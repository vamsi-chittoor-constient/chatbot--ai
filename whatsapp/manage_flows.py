#!/usr/bin/env python3
"""
WhatsApp Flows Management Script
Creates, uploads, and publishes Flows via Meta Graph API.

Supports both CLI usage and programmatic auto-provisioning on server startup.

CLI Usage:
    python manage_flows.py provision  # Auto-provision: find/create, upload, publish
    python manage_flows.py status     # Check flow status + validation errors
    python manage_flows.py list       # List all flows on the WABA

Programmatic Usage (from app.py startup):
    from manage_flows import auto_provision_flows
    flow_ids = auto_provision_flows()  # returns {"select_items": "id", ...}
"""
import json
import os
import sys
from pathlib import Path
from typing import Dict, Optional

import httpx
from dotenv import load_dotenv

load_dotenv(override=True)

ACCESS_TOKEN = os.getenv("WA_TOKEN", "")
WABA_ID = os.getenv("WABA_ID", "")
API_VERSION = os.getenv("WHATSAPP_API_VERSION", "v21.0")
BASE_URL = f"https://graph.facebook.com/{API_VERSION}"

# Flow definitions — source of truth for what should exist on the WABA
FLOW_DEFS = {
    "select_items": {
        "name": "A24 Item Selection",
        "json_file": "flows/select_items_flow.json",
        "categories": ["OTHER"],
    },
    "manage_cart": {
        "name": "A24 Cart Management",
        "json_file": "flows/manage_cart_flow.json",
        "categories": ["OTHER"],
    },
    "select_items_qty": {
        "name": "A24 Item Selection with Qty",
        "json_file": "flows/select_items_qty_flow.json",
        "categories": ["OTHER"],
    },
}


def _headers():
    return {"Authorization": f"Bearer {ACCESS_TOKEN}"}


def _log(msg: str, level: str = "INFO"):
    """Print with level prefix (CLI) — callers from app.py use LOGGER instead."""
    print(f"  [{level}] {msg}")


# ── Low-level API helpers ──────────────────────────────────────────


def list_all_flows() -> list:
    """List all flows on the WABA. Returns list of {id, name, status}."""
    resp = httpx.get(
        f"{BASE_URL}/{WABA_ID}/flows",
        headers=_headers(),
        params={"fields": "id,name,status,categories"},
        timeout=60,
    )
    if resp.status_code != 200:
        _log(f"Failed to list flows: {resp.text}", "ERROR")
        return []
    return resp.json().get("data", [])


def create_flow(name: str, categories: list) -> Optional[str]:
    """Create a new flow (Draft status). Returns flow_id or None."""
    resp = httpx.post(
        f"{BASE_URL}/{WABA_ID}/flows",
        headers=_headers(),
        json={"name": name, "categories": categories},
        timeout=60,
    )
    if resp.status_code != 200:
        _log(f"Failed to create flow '{name}': {resp.text}", "ERROR")
        return None
    flow_id = resp.json()["id"]
    _log(f"Created flow '{name}' -> {flow_id}")
    return flow_id


def upload_json(flow_id: str, json_path: str) -> bool:
    """Upload Flow JSON file. Works for both DRAFT and PUBLISHED flows (v6.2+)."""
    file_path = Path(__file__).parent / json_path
    if not file_path.exists():
        _log(f"JSON file not found: {file_path}", "ERROR")
        return False

    with open(file_path, "rb") as f:
        resp = httpx.post(
            f"{BASE_URL}/{flow_id}/assets",
            headers=_headers(),
            files={"file": ("flow.json", f, "application/json")},
            data={"name": "flow.json", "asset_type": "FLOW_JSON"},
            timeout=60,
        )
    if resp.status_code != 200:
        _log(f"Failed to upload JSON for {flow_id}: {resp.text}", "ERROR")
        return False

    result = resp.json()
    validation_errors = result.get("validation_errors", [])
    if validation_errors:
        _log(f"Validation errors for {flow_id}:", "WARN")
        for err in validation_errors:
            _log(f"  - {err}", "WARN")
        return False

    _log(f"Uploaded JSON for flow {flow_id} (valid)")
    return True


def publish_flow(flow_id: str) -> bool:
    """Publish a draft flow."""
    resp = httpx.post(
        f"{BASE_URL}/{flow_id}/publish",
        headers=_headers(),
        timeout=60,
    )
    if resp.status_code != 200:
        _log(f"Failed to publish {flow_id}: {resp.text}", "ERROR")
        return False
    _log(f"Published flow {flow_id}")
    return True


def get_status(flow_id: str) -> dict:
    """Get flow status and validation errors."""
    resp = httpx.get(
        f"{BASE_URL}/{flow_id}",
        headers=_headers(),
        params={"fields": "id,name,status,categories,validation_errors"},
        timeout=60,
    )
    if resp.status_code != 200:
        return {"error": resp.text}
    return resp.json()


# ── Auto-provision logic ───────────────────────────────────────────


def auto_provision_flows() -> Dict[str, str]:
    """
    Smart flow provisioning (v7.3 compatible). For each configured flow:
      1. Check if a flow with that name already exists on the WABA
      2. If exists + PUBLISHED  → re-upload latest JSON (v6.2+ allows editing published flows)
      3. If exists + DRAFT      → re-upload JSON + publish
      4. If not exists           → create + upload + publish

    Returns dict: {"select_items": "flow_id", "manage_cart": "flow_id", ...}
    """
    if not WABA_ID or not ACCESS_TOKEN:
        _log("WABA_ID or WA_TOKEN not set — skipping flow provisioning", "WARN")
        return {}

    # 1. Fetch all existing flows, index by name
    existing_flows = list_all_flows()
    by_name = {f["name"]: f for f in existing_flows}
    _log(f"Found {len(existing_flows)} existing flows on WABA")

    result: Dict[str, str] = {}

    for key, cfg in FLOW_DEFS.items():
        name = cfg["name"]
        json_file = cfg["json_file"]
        categories = cfg["categories"]

        _log(f"--- {key} ({name}) ---")

        existing = by_name.get(name)

        if existing:
            flow_id = existing["id"]
            status = existing.get("status", "UNKNOWN")
            _log(f"Found existing: {flow_id} (status: {status})")

            if status == "PUBLISHED":
                # v6.2+: published flows can be edited in-place
                _log(f"Published — updating JSON in-place")
                upload_json(flow_id, json_file)
                result[key] = flow_id
                continue

            elif status == "DRAFT":
                # Re-upload latest JSON in case it changed, then publish
                _log(f"Draft — re-uploading JSON and publishing")
                if upload_json(flow_id, json_file):
                    publish_flow(flow_id)
                result[key] = flow_id
                continue

            else:
                # DEPRECATED or other state — create a fresh one
                _log(f"Status '{status}' — creating new flow")

        # 2. Flow doesn't exist (or deprecated) — create fresh
        flow_id = create_flow(name, categories)
        if not flow_id:
            _log(f"Skipping {key} — creation failed", "ERROR")
            continue

        if upload_json(flow_id, json_file):
            publish_flow(flow_id)
        else:
            _log(f"Flow {flow_id} created but JSON upload failed — left in DRAFT", "WARN")

        result[key] = flow_id

    _log(f"Provisioning complete: {json.dumps(result, indent=2)}")
    return result


# ── CLI commands ───────────────────────────────────────────────────


def cmd_provision():
    """Auto-provision all flows (find/create, upload, publish)."""
    if not WABA_ID:
        print("ERROR: WABA_ID not set in .env")
        sys.exit(1)
    if not ACCESS_TOKEN:
        print("ERROR: WA_TOKEN not set in .env")
        sys.exit(1)
    result = auto_provision_flows()
    print(f"\nFlow IDs (for reference):")
    for key, flow_id in result.items():
        print(f"  {key}: {flow_id}")


def cmd_status():
    """Show status of all flows matching configured names."""
    existing = list_all_flows()
    by_name = {f["name"]: f for f in existing}

    for key, cfg in FLOW_DEFS.items():
        name = cfg["name"]
        print(f"\n--- {key} ({name}) ---")
        flow = by_name.get(name)
        if flow:
            info = get_status(flow["id"])
            print(f"  {json.dumps(info, indent=2)}")
        else:
            print(f"  Not found on WABA")


def cmd_list():
    """List all flows on the WABA."""
    flows = list_all_flows()
    if not flows:
        print("No flows found.")
        return
    for flow in flows:
        print(f"  {flow['id']}  {flow.get('status', '?'):12s}  {flow.get('name', '?')}")


def main():
    command = sys.argv[1] if len(sys.argv) > 1 else "status"

    commands = {
        "provision": cmd_provision,
        "status": cmd_status,
        "list": cmd_list,
    }

    if command not in commands:
        print(f"Unknown command: {command}")
        print(f"Available: {', '.join(commands.keys())}")
        sys.exit(1)

    commands[command]()


if __name__ == "__main__":
    main()

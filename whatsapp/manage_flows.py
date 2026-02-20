#!/usr/bin/env python3
"""
WhatsApp Flows Management Script
Creates, uploads, and publishes Flows via Meta Graph API.

Usage:
    python manage_flows.py create     # Create flows + upload JSON (returns flow IDs for .env)
    python manage_flows.py publish    # Publish draft flows (IRREVERSIBLE)
    python manage_flows.py status     # Check flow status + validation errors
    python manage_flows.py list       # List all flows on the WABA
"""
import json
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv(override=True)

ACCESS_TOKEN = os.getenv("WA_TOKEN", "")
WABA_ID = os.getenv("WABA_ID", "")
API_VERSION = os.getenv("WHATSAPP_API_VERSION", "v21.0")
BASE_URL = f"https://graph.facebook.com/{API_VERSION}"

FLOWS = {
    "select_items": {
        "name": "A24 Item Selection",
        "json_file": "flows/select_items_flow.json",
        "categories": ["OTHER"],
        "env_var": "FLOW_SELECT_ITEMS_ID",
    },
    "manage_cart": {
        "name": "A24 Cart Management",
        "json_file": "flows/manage_cart_flow.json",
        "categories": ["OTHER"],
        "env_var": "FLOW_MANAGE_CART_ID",
    },
}


def _headers():
    return {"Authorization": f"Bearer {ACCESS_TOKEN}"}


def create_flow(name: str, categories: list) -> str:
    """Create a new flow (Draft status). Returns flow_id."""
    resp = httpx.post(
        f"{BASE_URL}/{WABA_ID}/flows",
        headers=_headers(),
        json={"name": name, "categories": categories},
        timeout=60,
    )
    if resp.status_code != 200:
        print(f"  ERROR creating flow: {resp.text}")
        sys.exit(1)
    flow_id = resp.json()["id"]
    print(f"  Created flow '{name}' -> {flow_id}")
    return flow_id


def upload_json(flow_id: str, json_path: str):
    """Upload Flow JSON file to a draft flow."""
    file_path = Path(__file__).parent / json_path
    if not file_path.exists():
        print(f"  ERROR: File not found: {file_path}")
        sys.exit(1)

    with open(file_path, "rb") as f:
        resp = httpx.post(
            f"{BASE_URL}/{flow_id}/assets",
            headers=_headers(),
            files={"file": ("flow.json", f, "application/json")},
            data={"name": "flow.json", "asset_type": "FLOW_JSON"},
            timeout=60,
        )
    if resp.status_code != 200:
        print(f"  ERROR uploading JSON: {resp.text}")
        sys.exit(1)

    result = resp.json()
    validation_errors = result.get("validation_errors", [])
    if validation_errors:
        print(f"  WARNING: Validation errors:")
        for err in validation_errors:
            print(f"    - {err}")
    else:
        print(f"  Uploaded JSON for flow {flow_id} (no validation errors)")


def publish_flow(flow_id: str):
    """Publish a draft flow. THIS IS IRREVERSIBLE."""
    resp = httpx.post(
        f"{BASE_URL}/{flow_id}/publish",
        headers=_headers(),
        timeout=60,
    )
    if resp.status_code != 200:
        print(f"  ERROR publishing flow: {resp.text}")
        return False
    print(f"  Published flow {flow_id} (IRREVERSIBLE)")
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


def list_flows():
    """List all flows on the WABA."""
    resp = httpx.get(
        f"{BASE_URL}/{WABA_ID}/flows",
        headers=_headers(),
        params={"fields": "id,name,status,categories"},
        timeout=60,
    )
    if resp.status_code != 200:
        print(f"ERROR listing flows: {resp.text}")
        return
    data = resp.json().get("data", [])
    if not data:
        print("No flows found.")
        return
    for flow in data:
        print(f"  {flow['id']}  {flow.get('status', '?'):12s}  {flow.get('name', '?')}")


def cmd_create():
    """Create flows, upload JSON, and print env vars."""
    if not WABA_ID:
        print("ERROR: WABA_ID not set in .env")
        sys.exit(1)
    if not ACCESS_TOKEN:
        print("ERROR: WA_TOKEN not set in .env")
        sys.exit(1)

    env_lines = []
    for key, cfg in FLOWS.items():
        print(f"\n--- {key} ---")
        flow_id = create_flow(cfg["name"], cfg["categories"])
        upload_json(flow_id, cfg["json_file"])

        # Check for validation errors
        status = get_status(flow_id)
        errors = status.get("validation_errors", [])
        if errors:
            print(f"  Flow has validation errors — fix before publishing:")
            for err in errors:
                print(f"    {err}")

        env_lines.append(f'{cfg["env_var"]}={flow_id}')

    print("\n" + "=" * 50)
    print("Add these to your .env file:")
    print("=" * 50)
    for line in env_lines:
        print(f"  {line}")
    print()


def cmd_publish():
    """Publish all configured draft flows."""
    if not ACCESS_TOKEN:
        print("ERROR: WA_TOKEN not set in .env")
        sys.exit(1)

    for key, cfg in FLOWS.items():
        flow_id = os.getenv(cfg["env_var"], "")
        if not flow_id:
            print(f"  SKIP {key}: {cfg['env_var']} not set in .env")
            continue

        print(f"\n--- {key} (flow_id={flow_id}) ---")
        status = get_status(flow_id)
        current_status = status.get("status", "UNKNOWN")

        if current_status == "DRAFT":
            errors = status.get("validation_errors", [])
            if errors:
                print(f"  Cannot publish — validation errors:")
                for err in errors:
                    print(f"    {err}")
                continue
            publish_flow(flow_id)
        elif current_status == "PUBLISHED":
            print(f"  Already published.")
        else:
            print(f"  Status: {current_status} (cannot publish)")


def cmd_status():
    """Show status of all configured flows."""
    for key, cfg in FLOWS.items():
        flow_id = os.getenv(cfg["env_var"], "")
        print(f"\n--- {key} ---")
        if not flow_id:
            print(f"  {cfg['env_var']} not set")
            continue
        info = get_status(flow_id)
        print(f"  {json.dumps(info, indent=2)}")


def main():
    command = sys.argv[1] if len(sys.argv) > 1 else "status"

    commands = {
        "create": cmd_create,
        "publish": cmd_publish,
        "status": cmd_status,
        "list": list_flows,
    }

    if command not in commands:
        print(f"Unknown command: {command}")
        print(f"Available: {', '.join(commands.keys())}")
        sys.exit(1)

    commands[command]()


if __name__ == "__main__":
    main()

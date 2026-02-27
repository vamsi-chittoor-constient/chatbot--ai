# Data Format Inconsistency Summary

## Status: FIXED ✓

Both `chain_service.py` and `menu_service.py` now use consistent `"active"` / `"inactive"` format.

---

## Overview

There were two main functions that store menu data, but they used different formats for the same fields. This has been fixed.

---

## Related Functions Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATA FLOW                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. /api/chain/petpooja-sync                                                │
│     └── fetch_menu_from_petpooja_with_credentials_only()                    │
│         └── Returns menu data from PetPooja API (NO STORAGE)                │
│                                                                              │
│  2. /api/chain/store-menu  (INITIAL SETUP)                                  │
│     └── store_menu_data()  [chain_service.py]                               │
│         └── Creates: Chain, Branch, Restaurant, Integration, Menu           │
│         └── Format: "active" / "inactive"                                   │
│                                                                              │
│  3. /webhook/pushmenu  (MENU UPDATES)                                       │
│     └── process_push_menu() → store_menu()  [menu_service.py]               │
│         └── Updates: Menu items, categories, addons, etc.                   │
│         └── Format: "1" / "0"                                               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Format Comparison (After Fix)

| Field | chain_service.py | menu_service.py |
|-------|------------------|-----------------|
| `menu_section_status` | `"active"` / `"inactive"` | `"active"` / `"inactive"` ✓ |
| `menu_category_status` | `"active"` / `"inactive"` | `"active"` / `"inactive"` ✓ |
| `sub_category_status` | `"active"` / `"inactive"` | `"active"` / `"inactive"` ✓ |
| `menu_item_status` | `"active"` / `"inactive"` | `"active"` / `"inactive"` ✓ |
| `menu_item_addon_group_status` | `"active"` / `"inactive"` | `"active"` / `"inactive"` ✓ |
| `menu_item_addon_item_status` | `"active"` / `"inactive"` | `"active"` / `"inactive"` ✓ |
| `menu_item_attribute_status` | `"active"` / `"inactive"` | `"active"` / `"inactive"` ✓ |
| `menu_item_variation_status` | `"active"` / `"inactive"` | `"active"` / `"inactive"` ✓ |
| `tax_status` | N/A | `"active"` / `"inactive"` ✓ |
| `discount_status` | N/A | `"active"` / `"inactive"` ✓ |

---

## Code Examples (After Fix)

### chain_service.py (store_menu_data)
```python
# Converts "1" to "active", otherwise "inactive"
menu_section_status="active" if section_data.status == "1" else "inactive"
menu_item_status="active" if item_data.active == "1" else "inactive"
is_active=branch_data.active == "1"  # Boolean
```

### menu_service.py (store_menu - webhook) - FIXED
```python
# Helper function added
def convert_status(value: str, default: str = "1") -> str:
    """Convert PetPooja status '1'/'0' to 'active'/'inactive' format."""
    if value is None or value == "":
        value = default
    return "active" if str(value) == "1" else "inactive"

# Now uses convert_status for all fields
menu_item_status=convert_status(item.get("active", "1"))  # Returns "active" or "inactive"
menu_section_status=convert_status(parent_cat.get("status", "1"))  # Returns "active" or "inactive"
```

---

## Problem (RESOLVED)

~~When the same restaurant is:~~
~~1. **Initially created** via `/store-menu` → status stored as `"active"`~~
~~2. **Updated** via `/pushmenu` webhook → status overwritten to `"1"`~~

~~This causes inconsistent data in the database.~~

**Now both functions store `"active"` / `"inactive"` consistently.**

---

## Changes Made

### Helper function added to menu_service.py:

```python
def convert_status(value: str, default: str = "1") -> str:
    """Convert PetPooja status '1'/'0' to 'active'/'inactive' format."""
    if value is None or value == "":
        value = default
    return "active" if str(value) == "1" else "inactive"
```

### Updated fields in menu_service.py:

| Field | Before | After |
|-------|--------|-------|
| `menu_item_attribute_status` | `attr.get("active", "1")` | `convert_status(attr.get("active", "1"))` |
| `menu_section_status` | `parent_cat.get("status", "1")` | `convert_status(parent_cat.get("status", "1"))` |
| `menu_category_status` | `group_cat.get("status", "1")` | `convert_status(group_cat.get("status", "1"))` |
| `sub_category_status` | `category.get("active", "1")` | `convert_status(category.get("active", "1"))` |
| `tax_status` | `tax.get("active", "1")` | `convert_status(tax.get("active", "1"))` |
| `menu_item_addon_group_status` | `addon_group.get("active", "1")` | `convert_status(addon_group.get("active", "1"))` |
| `menu_item_addon_item_status` | `addon_item.get("active", "1")` | `convert_status(addon_item.get("active", "1"))` |
| `menu_item_status` | `item.get("active", "1")` | `convert_status(item.get("active", "1"))` |
| `menu_item_variation_status` | `variation.get("active", "1")` | `convert_status(variation.get("active", "1"))` |
| `discount_status` | `discount.get("active", "1")` | `convert_status(discount.get("active", "1"))` |

---

## Duplicate Check Added

A duplicate check was added to `store_menu_data()` in `chain_service.py`:

```python
# Check if restaurant already exists by menusharingcode
for branch_data in request.branches:
    menusharingcode = branch_data.details.menusharingcode
    if menusharingcode:
        existing_branch = db.query(BranchInfoTable).filter(
            BranchInfoTable.ext_petpooja_restaurant_id == menusharingcode,
            BranchInfoTable.is_deleted.is_(False)
        ).first()

        if existing_branch:
            return {
                "success": False,
                "message": f"Restaurant already exists with menusharingcode: {menusharingcode}",
                ...
            }
```

This prevents duplicate entries when `/store-menu` API is called twice with same credentials.

"""
Menu Service
"""

import logging
import uuid
import httpx
from typing import Dict, Any
from datetime import datetime, timezone

from app.core.db_session import SessionLocal
from app.core.config import settings
from app.models.branch_models import BranchInfoTable, BranchLocationTable, BranchContactTable
from app.models.chain_models import ChainInfoTable
from app.models.menu_models import (
    MenuSections, MenuCategories, MenuItem, MenuItemVariation,
    MenuItemAttribute, MenuItemAddonGroup, MenuItemAddonItem,
    MenuSubCategories, MenuItemTaxMapping, MenuItemAddonMapping
)
from app.models.other_models import VariationGroups, Taxes, Discount, RestaurantTable
from app.models.order_models import OrderTypeTable
from app.models.integration_models import IntegrationConfigTable, IntegrationCredentialsTable, IntegrationProviderTable

logger = logging.getLogger(__name__)


class MenuServiceError(Exception):
    pass


def safe_int(value, default=0):
    """Safely convert value to int, return default if fails."""
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value, default=0.0):
    """Safely convert value to float, return default if fails."""
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def convert_status(value: str, default: str = "1") -> str:
    """Convert PetPooja status '1'/'0' to 'active'/'inactive' format."""
    if value is None or value == "":
        value = default
    return "active" if str(value) == "1" else "inactive"


async def fetch_and_sync_menu_by_restaurant_id(restaurant_id: uuid.UUID) -> Dict[str, Any]:
    """
    Fetch PetPooja credentials from database using restaurant_id,
    call PetPooja API to get menu, and store/update in database.
    """
    db = SessionLocal()
    try:
        integration_config = db.query(IntegrationConfigTable).join(
            IntegrationProviderTable,
            IntegrationConfigTable.provider_id == IntegrationProviderTable.provider_id
        ).filter(
            IntegrationConfigTable.restaurant_id == restaurant_id,
            IntegrationProviderTable.provider_name.ilike("%petpooja%"),
            IntegrationConfigTable.is_enabled.is_(True),
            IntegrationConfigTable.is_deleted.is_(False)
        ).first()

        if not integration_config:
            raise MenuServiceError(f"No active PetPooja integration found for restaurant_id: {restaurant_id}")

        # Decrypt credentials from integration_credentials_table
        from app.services.chain_service import decrypt_credentials_for_use
        cred_dict = decrypt_credentials_for_use(db, integration_config.integration_config_id)

        logger.info(f"Decrypted credentials keys: {list(cred_dict.keys())}")

        app_key = cred_dict.get("app_key") or cred_dict.get("app-key")
        app_secret = cred_dict.get("app_secret") or cred_dict.get("app-secret")
        access_token = cred_dict.get("access_token") or cred_dict.get("access-token")

        # petpooja_restaurantid is the restID for API calls
        petpooja_rest_id = cred_dict.get("petpooja_restaurantid") or cred_dict.get("restID")

        # restaurant_mapping_id is the menusharingcode for storing
        menusharingcode = cred_dict.get("restaurant_mapping_id")

        sandbox_enabled = str(cred_dict.get("sandbox_enabled", "true")).lower() == "true"

        if not all([app_key, app_secret, access_token, petpooja_rest_id]):
            missing = []
            if not app_key:
                missing.append("app_key")
            if not app_secret:
                missing.append("app_secret")
            if not access_token:
                missing.append("access_token")
            if not petpooja_rest_id:
                missing.append("petpooja_restaurantid")
            raise MenuServiceError(f"Missing required credentials: {', '.join(missing)}")

        base_url = settings.PETPOOJA_SANDBOX_BASE_URL if sandbox_enabled else settings.PETPOOJA_BASE_URL
        url = f"{base_url}{getattr(settings, 'PETPOOJA_FETCH_MENU_ENDPOINT', '/mapped_restaurant_menus')}"

        headers = {
            "Content-Type": "application/json",
            "app-key": app_key,
            "app-secret": app_secret,
            "access-token": access_token
        }
        payload = {"restID": menusharingcode}

        logger.info(f"Fetching menu from PetPooja for restaurant_id: {restaurant_id}")
        logger.info(f"PetPooja URL: {url}")
        logger.info(f"Sandbox enabled: {sandbox_enabled}")
        logger.info(f"Payload: {payload}")
        logger.info(f"Headers being sent: {headers}")
        logger.info(f"menusharingcode for storing: {menusharingcode}")

        with httpx.Client(timeout=settings.HTTP_TIMEOUT) as client:
            response = client.post(url, json=payload, headers=headers)
            response_data = response.json()

            logger.info(f"PetPooja response status: {response.status_code}")
            logger.info(f"PetPooja response success: {response_data.get('success')}")
            logger.info(f"PetPooja response message: {response_data.get('message', 'N/A')}")

            if response.status_code != 200 or not response_data.get("success", False):
                logger.error(f"PetPooja API failed: {response_data}")
                raise MenuServiceError(response_data.get("message", "PetPooja API request failed"))

            store_result = _store_menu_with_db(response_data, menusharingcode, db, internal_restaurant_id=restaurant_id)
            db.commit()

            logger.info(f"Menu synced successfully for restaurant_id: {restaurant_id}")

            return {
                "success": True,
                "message": "Menu fetched and stored successfully",
                "data": response_data,
                "store_result": store_result
            }

    except httpx.HTTPError as e:
        db.rollback()
        logger.error(f"HTTP error fetching menu: {str(e)}")
        raise MenuServiceError(f"HTTP request failed: {str(e)}")
    except MenuServiceError:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error in fetch_and_sync_menu_by_restaurant_id: {str(e)}")
        raise MenuServiceError(f"Failed to fetch and sync menu: {str(e)}")
    finally:
        db.close()


def store_menu(menu_data: Dict[str, Any], restaurant_id: str) -> Dict[str, Any]:
    """
    Public wrapper for storing menu data.
    Creates its own db session for standalone use (e.g., webhook_service).
    """
    db = SessionLocal()
    try:
        result = _store_menu_with_db(menu_data, restaurant_id, db)
        db.commit()
        return result
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()


def _store_menu_with_db(menu_data: Dict[str, Any], restaurant_id: str, db, internal_restaurant_id: uuid.UUID = None) -> Dict[str, Any]:
    """Store menu data with create or update logic to prevent duplicates."""
    try:
        counts = {
            "restaurants": 0, "ordertypes": 0, "group_categories": 0, "parent_categories": 0,
            "categories": 0, "items": 0, "variations": 0, "addon_groups": 0, "addon_items": 0,
            "attributes": 0, "taxes": 0, "discounts": 0, "updated": 0, "created": 0, "deleted": 0
        }

        # Track processed IDs for soft delete
        processed_ids = {
            "ordertypes": [], "attributes": [], "parent_categories": [], "group_categories": [],
            "categories": [], "taxes": [], "addon_groups": [], "addon_items": [], "items": [],
            "variations": [], "discounts": []
        }

        # restaurant_id parameter now contains the menusharingcode directly from credentials
        menusharingcode = restaurant_id

        # Fallback: try to get from API response if not provided
        if not menusharingcode:
            if menu_data.get("restaurants") and len(menu_data["restaurants"]) > 0:
                details = menu_data["restaurants"][0].get("details", {})
                menusharingcode = details.get("menusharingcode")

        if not menusharingcode:
            raise MenuServiceError("Menu sharing code not found")

        branch_id = None
        db_restaurant_id = None

        branch = db.query(BranchInfoTable).filter(BranchInfoTable.ext_petpooja_restaurant_id == menusharingcode).first()

        if branch:
            branch_id = branch.branch_id
            restaurant = db.query(RestaurantTable).filter(RestaurantTable.branch_id == branch_id).first()

            if restaurant:
                db_restaurant_id = restaurant.restaurant_id
            else:
                db_restaurant_id = uuid.uuid4()
                restaurant = RestaurantTable(
                    restaurant_id=db_restaurant_id, chain_id=branch.chain_id,
                    branch_id=branch_id, created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)
                )
                db.add(restaurant)
                db.flush()
        else:
            restaurant_info = menu_data["restaurants"][0]
            details = restaurant_info.get("details", {})
            restaurant_name = details.get("restaurantname", f"Restaurant {restaurant_id}")

            existing_chain = db.query(ChainInfoTable).filter(ChainInfoTable.chain_name == restaurant_name).first()

            if existing_chain:
                chain_id = existing_chain.chain_id
            else:
                chain_id = uuid.uuid4()
                chain = ChainInfoTable(
                    chain_id=chain_id, chain_name=restaurant_name, chain_type="restaurant",
                    created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)
                )
                db.add(chain)
                db.flush()

            branch_id = uuid.uuid4()
            branch = BranchInfoTable(
                branch_id=branch_id, chain_id=chain_id, branch_name=restaurant_name,
                ext_petpooja_restaurant_id=menusharingcode, created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)
            )
            db.add(branch)
            db.flush()

            db_restaurant_id = uuid.uuid4()
            restaurant = RestaurantTable(
                restaurant_id=db_restaurant_id, chain_id=chain_id, branch_id=branch_id,
                created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)
            )
            db.add(restaurant)
            db.flush()

            if details.get("address") or details.get("latitude") or details.get("longitude"):
                location = BranchLocationTable(
                    branch_location_id=uuid.uuid4(), branch_id=branch_id,
                    address_line=details.get("address", ""), landmark=details.get("landmark", ""),
                    latitude=str(details.get("latitude", "")) if details.get("latitude") else None,
                    longitude=str(details.get("longitude", "")) if details.get("longitude") else None,
                    created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)
                )
                db.add(location)

            if details.get("contact"):
                contact = BranchContactTable(
                    branch_contact_id=uuid.uuid4(), branch_id=branch_id, contact_type="phone",
                    contact_value=details.get("contact"), is_primary=True,
                    created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)
                )
                db.add(contact)

            counts["restaurants"] = 1

        if db_restaurant_id is None:
            raise MenuServiceError("Cannot store menu data: restaurant_table entry not found")

        # Order Types
        for order_type in menu_data.get("ordertypes", []):
            petpooja_id = safe_int(order_type.get("ordertypeid"))
            if not petpooja_id:
                continue
            processed_ids["ordertypes"].append(petpooja_id)

            # Order types are global, not restaurant-specific
            existing = db.query(OrderTypeTable).filter(
                OrderTypeTable.ext_petpooja_order_type_id == petpooja_id
            ).first()

            if existing:
                existing.order_type_name = order_type.get("ordertype", "")
                existing.updated_at = datetime.now(timezone.utc)
                counts["updated"] += 1
            else:
                db.add(OrderTypeTable(
                    order_type_id=uuid.uuid4(), order_type_name=order_type.get("ordertype", ""),
                    ext_petpooja_order_type_id=petpooja_id, created_at=datetime.now(timezone.utc)
                ))
                counts["created"] += 1
            counts["ordertypes"] += 1

        # Attributes
        for attr in menu_data.get("attributes", []):
            petpooja_id = safe_int(attr.get("attributeid"))
            if not petpooja_id:
                continue
            processed_ids["attributes"].append(petpooja_id)

            existing = db.query(MenuItemAttribute).filter(
                MenuItemAttribute.ext_petpooja_attributes_id == petpooja_id,
                MenuItemAttribute.restaurant_id == db_restaurant_id
            ).first()

            if existing:
                existing.menu_item_attribute_name = attr.get("attribute", "")
                existing.menu_item_attribute_status = convert_status(attr.get("active", "1"))
                existing.updated_at = datetime.now(timezone.utc)
                counts["updated"] += 1
            else:
                db.add(MenuItemAttribute(
                    menu_item_attribute_id=uuid.uuid4(), menu_item_attribute_name=attr.get("attribute", ""),
                    menu_item_attribute_status=convert_status(attr.get("active", "1")), restaurant_id=db_restaurant_id,
                    ext_petpooja_attributes_id=petpooja_id, created_at=datetime.now(timezone.utc)
                ))
                counts["created"] += 1
            counts["attributes"] += 1

        # Parent Categories -> MenuSections
        for parent_cat in menu_data.get("parentcategories", []):
            petpooja_id = safe_int(parent_cat.get("id"))
            if not petpooja_id:
                continue
            processed_ids["parent_categories"].append(petpooja_id)

            existing = db.query(MenuSections).filter(
                MenuSections.ext_petpooja_parent_categories_id == petpooja_id,
                MenuSections.restaurant_id == db_restaurant_id
            ).first()

            if existing:
                existing.menu_section_name = parent_cat.get("name", "")
                existing.menu_section_rank = safe_int(parent_cat.get("rank"))
                existing.menu_section_status = convert_status(parent_cat.get("status", "1"))
                existing.menu_section_image_url = parent_cat.get("image_url", "")
                existing.updated_at = datetime.now(timezone.utc)
                counts["updated"] += 1
            else:
                db.add(MenuSections(
                    menu_section_id=uuid.uuid4(), restaurant_id=db_restaurant_id,
                    menu_section_name=parent_cat.get("name", ""), menu_section_rank=safe_int(parent_cat.get("rank")),
                    menu_section_status=convert_status(parent_cat.get("status", "1")), menu_section_image_url=parent_cat.get("image_url", ""),
                    ext_petpooja_parent_categories_id=petpooja_id, created_at=datetime.now(timezone.utc)
                ))
                counts["created"] += 1
            counts["parent_categories"] += 1

        # Group Categories -> MenuCategories
        for group_cat in menu_data.get("group_categories", []):
            petpooja_id = safe_int(group_cat.get("id"))
            if not petpooja_id:
                continue
            processed_ids["group_categories"].append(petpooja_id)

            existing = db.query(MenuCategories).filter(
                MenuCategories.ext_petpooja_group_category_id == petpooja_id,
                MenuCategories.restaurant_id == db_restaurant_id
            ).first()

            if existing:
                existing.menu_category_name = group_cat.get("name", "")
                existing.menu_category_rank = safe_int(group_cat.get("rank"))
                existing.menu_category_status = convert_status(group_cat.get("status", "1"))
                existing.updated_at = datetime.now(timezone.utc)
                counts["updated"] += 1
            else:
                db.add(MenuCategories(
                    menu_category_id=uuid.uuid4(), restaurant_id=db_restaurant_id,
                    menu_category_name=group_cat.get("name", ""), menu_category_rank=safe_int(group_cat.get("rank")),
                    menu_category_status=convert_status(group_cat.get("status", "1")), ext_petpooja_group_category_id=petpooja_id,
                    created_at=datetime.now(timezone.utc)
                ))
                counts["created"] += 1
            counts["group_categories"] += 1

        # Categories -> MenuSubCategories
        for category in menu_data.get("categories", []):
            petpooja_id = safe_int(category.get("categoryid"))
            if not petpooja_id:
                continue
            processed_ids["categories"].append(petpooja_id)

            existing = db.query(MenuSubCategories).filter(
                MenuSubCategories.ext_petpooja_categories_id == petpooja_id,
                MenuSubCategories.restaurant_id == db_restaurant_id
            ).first()

            if existing:
                existing.sub_category_name = category.get("categoryname", "")
                existing.sub_category_rank = safe_int(category.get("categoryrank"))
                existing.sub_category_status = convert_status(category.get("active", "1"))
                existing.sub_category_timings = category.get("categorytimings", "")
                existing.sub_category_image_url = category.get("category_image_url", "")
                existing.updated_at = datetime.now(timezone.utc)
                counts["updated"] += 1
            else:
                db.add(MenuSubCategories(
                    menu_sub_category_id=uuid.uuid4(), restaurant_id=db_restaurant_id,
                    sub_category_name=category.get("categoryname", ""), sub_category_rank=safe_int(category.get("categoryrank")),
                    sub_category_status=convert_status(category.get("active", "1")), sub_category_timings=category.get("categorytimings", ""),
                    sub_category_image_url=category.get("category_image_url", ""), ext_petpooja_categories_id=petpooja_id,
                    created_at=datetime.now(timezone.utc)
                ))
                counts["created"] += 1
            counts["categories"] += 1

        # Taxes
        for tax in menu_data.get("taxes", []):
            petpooja_id = safe_int(tax.get("taxid"))
            if not petpooja_id:
                continue
            processed_ids["taxes"].append(petpooja_id)

            existing = db.query(Taxes).filter(
                Taxes.ext_petpooja_tax_id == petpooja_id,
                Taxes.restaurant_id == db_restaurant_id
            ).first()

            if existing:
                existing.tax_name = tax.get("taxname", "")
                existing.tax_percentage = safe_float(tax.get("tax"))
                existing.tax_type = tax.get("taxtype", "1")
                existing.tax_rank = safe_int(tax.get("rank"))
                existing.tax_status = convert_status(tax.get("active", "1"))
                existing.tax_description = tax.get("description", "")
                existing.updated_at = datetime.now(timezone.utc)
                counts["updated"] += 1
            else:
                db.add(Taxes(
                    tax_id=uuid.uuid4(), restaurant_id=db_restaurant_id, tax_name=tax.get("taxname", ""),
                    tax_percentage=safe_float(tax.get("tax")), tax_type=tax.get("taxtype", "1"),
                    tax_rank=safe_int(tax.get("rank")), tax_status=convert_status(tax.get("active", "1")),
                    tax_description=tax.get("description", ""), ext_petpooja_tax_id=petpooja_id, created_at=datetime.now(timezone.utc)
                ))
                db.flush()
                counts["created"] += 1
            counts["taxes"] += 1

        # Addon Groups and Items
        for addon_group in menu_data.get("addongroups", []):
            petpooja_group_id = safe_int(addon_group.get("addongroupid"))
            if not petpooja_group_id:
                continue
            processed_ids["addon_groups"].append(petpooja_group_id)

            existing_ag = db.query(MenuItemAddonGroup).filter(
                MenuItemAddonGroup.ext_petpooja_addon_group_id == petpooja_group_id,
                MenuItemAddonGroup.restaurant_id == db_restaurant_id
            ).first()

            if existing_ag:
                existing_ag.menu_item_addon_group_name = addon_group.get("addongroup_name", "")
                existing_ag.menu_item_addon_group_rank = safe_int(addon_group.get("addongroup_rank"))
                existing_ag.menu_item_addon_group_status = convert_status(addon_group.get("active", "1"))
                existing_ag.updated_at = datetime.now(timezone.utc)
                ag_id = existing_ag.menu_item_addon_group_id
                counts["updated"] += 1
            else:
                ag_id = uuid.uuid4()
                db.add(MenuItemAddonGroup(
                    menu_item_addon_group_id=ag_id, restaurant_id=db_restaurant_id,
                    menu_item_addon_group_name=addon_group.get("addongroup_name", ""),
                    menu_item_addon_group_rank=safe_int(addon_group.get("addongroup_rank")),
                    menu_item_addon_group_status=convert_status(addon_group.get("active", "1")),
                    ext_petpooja_addon_group_id=petpooja_group_id, created_at=datetime.now(timezone.utc)
                ))
                db.flush()
                counts["created"] += 1
            counts["addon_groups"] += 1

            for addon_item in addon_group.get("addongroupitems", []):
                petpooja_addon_item_id = safe_int(addon_item.get("addonitemid"))
                addon_item_name = addon_item.get("addonitem_name", "")

                if petpooja_addon_item_id:
                    processed_ids["addon_items"].append(petpooja_addon_item_id)

                existing_ai = None
                if petpooja_addon_item_id:
                    existing_ai = db.query(MenuItemAddonItem).filter(
                        MenuItemAddonItem.ext_petpooja_addon_item_id == petpooja_addon_item_id,
                        MenuItemAddonItem.restaurant_id == db_restaurant_id
                    ).first()

                if not existing_ai and addon_item_name:
                    existing_ai = db.query(MenuItemAddonItem).filter(
                        MenuItemAddonItem.menu_item_addon_group_id == str(ag_id),
                        MenuItemAddonItem.menu_item_addon_item_name == addon_item_name,
                        MenuItemAddonItem.restaurant_id == db_restaurant_id
                    ).first()

                if existing_ai:
                    existing_ai.menu_item_addon_item_name = addon_item_name
                    existing_ai.menu_item_addon_item_price = safe_float(addon_item.get("addonitem_price"))
                    existing_ai.menu_item_addon_item_rank = safe_int(addon_item.get("addonitem_rank"))
                    existing_ai.menu_item_addon_item_status = convert_status(addon_item.get("active", "1"))
                    existing_ai.menu_item_addon_group_id = str(ag_id)
                    if petpooja_addon_item_id:
                        existing_ai.ext_petpooja_addon_item_id = petpooja_addon_item_id
                    existing_ai.updated_at = datetime.now(timezone.utc)
                    counts["updated"] += 1
                else:
                    db.add(MenuItemAddonItem(
                        menu_item_addon_id=uuid.uuid4(), menu_item_addon_group_id=str(ag_id),
                        restaurant_id=db_restaurant_id, menu_item_addon_item_name=addon_item_name,
                        menu_item_addon_item_price=safe_float(addon_item.get("addonitem_price")),
                        menu_item_addon_item_rank=safe_int(addon_item.get("addonitem_rank")),
                        menu_item_addon_item_status=convert_status(addon_item.get("active", "1")),
                        ext_petpooja_addon_item_id=petpooja_addon_item_id if petpooja_addon_item_id else None,
                        created_at=datetime.now(timezone.utc)
                    ))
                    counts["created"] += 1
                counts["addon_items"] += 1

        # Menu Items
        for item in menu_data.get("items", []):
            petpooja_item_id = safe_int(item.get("itemid"))
            if not petpooja_item_id:
                continue
            processed_ids["items"].append(petpooja_item_id)

            petpooja_category_id = safe_int(item.get("item_categoryid"))
            sub_category = db.query(MenuSubCategories).filter(
                MenuSubCategories.ext_petpooja_categories_id == petpooja_category_id,
                MenuSubCategories.restaurant_id == db_restaurant_id
            ).first() if petpooja_category_id else None
            sub_category_id = sub_category.menu_sub_category_id if sub_category else None

            existing_item = db.query(MenuItem).filter(
                MenuItem.ext_petpooja_item_id == petpooja_item_id,
                MenuItem.restaurant_id == db_restaurant_id
            ).first()

            if existing_item:
                existing_item.menu_item_name = item.get("itemname", "")
                existing_item.menu_item_description = item.get("itemdescription", "")
                existing_item.menu_item_price = safe_float(item.get("price"))
                existing_item.menu_item_status = convert_status(item.get("active", "1"))
                existing_item.menu_item_rank = safe_int(item.get("itemrank"))
                existing_item.menu_item_allow_variation = item.get("itemallowvariation") == "1"
                existing_item.menu_item_allow_addon = item.get("itemallowaddon") == "1"
                existing_item.menu_item_favorite = item.get("item_favorite") == "1"
                existing_item.menu_item_is_recommended = item.get("is_recommend") == "1"
                existing_item.menu_item_packaging_charges = safe_float(item.get("item_packingcharges"))
                existing_item.menu_item_ignore_taxes = item.get("ignore_taxes") == "1"
                existing_item.menu_item_ignore_discounts = item.get("ignore_discounts") == "1"
                existing_item.menu_item_in_stock = item.get("in_stock", "2") == "2"
                existing_item.menu_item_is_combo = item.get("is_combo") == "1"
                existing_item.menu_item_markup_price = safe_float(item.get("markup_price")) if item.get("markup_price") else None
                existing_item.menu_item_minimum_preparation_time = safe_int(item.get("minimumpreparationtime")) if item.get("minimumpreparationtime") else None
                existing_item.menu_item_spice_level = item.get("item_info", {}).get("spice_level") if isinstance(item.get("item_info"), dict) else None
                existing_item.is_deleted = False
                if sub_category_id:
                    existing_item.menu_sub_category_id = sub_category_id
                existing_item.updated_at = datetime.now(timezone.utc)
                menu_item_id = existing_item.menu_item_id
                counts["updated"] += 1
            else:
                menu_item_id = uuid.uuid4()
                db.add(MenuItem(
                    menu_item_id=menu_item_id, restaurant_id=db_restaurant_id, menu_sub_category_id=sub_category_id,
                    menu_item_name=item.get("itemname", ""), menu_item_description=item.get("itemdescription", ""),
                    menu_item_price=safe_float(item.get("price")), menu_item_status=convert_status(item.get("active", "1")),
                    menu_item_rank=safe_int(item.get("itemrank")), menu_item_allow_variation=item.get("itemallowvariation") == "1",
                    menu_item_allow_addon=item.get("itemallowaddon") == "1", menu_item_favorite=item.get("item_favorite") == "1",
                    menu_item_is_recommended=item.get("is_recommend") == "1", menu_item_packaging_charges=safe_float(item.get("item_packingcharges")),
                    menu_item_ignore_taxes=item.get("ignore_taxes") == "1", menu_item_ignore_discounts=item.get("ignore_discounts") == "1",
                    menu_item_in_stock=item.get("in_stock", "2") == "2", menu_item_is_combo=item.get("is_combo") == "1",
                    menu_item_markup_price=safe_float(item.get("markup_price")) if item.get("markup_price") else None,
                    menu_item_minimum_preparation_time=safe_int(item.get("minimumpreparationtime")) if item.get("minimumpreparationtime") else None,
                    menu_item_spice_level=item.get("item_info", {}).get("spice_level") if isinstance(item.get("item_info"), dict) else None,
                    ext_petpooja_item_id=petpooja_item_id, created_at=datetime.now(timezone.utc)
                ))
                db.flush()
                counts["created"] += 1

            # Tax Mapping
            item_taxes = item.get("item_tax", [])
            if item_taxes:
                db.query(MenuItemTaxMapping).filter(MenuItemTaxMapping.menu_item_id == menu_item_id).delete()
                for tax_id_str in item_taxes:
                    petpooja_tax_id = safe_int(tax_id_str)
                    if petpooja_tax_id:
                        tax = db.query(Taxes).filter(
                            Taxes.ext_petpooja_tax_id == petpooja_tax_id,
                            Taxes.restaurant_id == db_restaurant_id
                        ).first()
                        if tax:
                            db.add(MenuItemTaxMapping(
                                menu_item_tax_mapping_id=uuid.uuid4(), menu_item_id=menu_item_id,
                                restaurant_id=db_restaurant_id, tax_id=tax.tax_id, created_at=datetime.now(timezone.utc)
                            ))

            # Addon Group Mapping
            item_addon_groups = item.get("item_addon_grp", [])
            if item_addon_groups:
                db.query(MenuItemAddonMapping).filter(MenuItemAddonMapping.menu_item_id == menu_item_id).delete()
                for addon_grp_id_str in item_addon_groups:
                    petpooja_addon_grp_id = safe_int(addon_grp_id_str)
                    if petpooja_addon_grp_id:
                        addon_grp = db.query(MenuItemAddonGroup).filter(
                            MenuItemAddonGroup.ext_petpooja_addon_group_id == petpooja_addon_grp_id,
                            MenuItemAddonGroup.restaurant_id == db_restaurant_id
                        ).first()
                        if addon_grp:
                            db.add(MenuItemAddonMapping(
                                menu_item_addon_mapping_id=uuid.uuid4(), menu_item_id=menu_item_id,
                                menu_item_addon_group_id=addon_grp.menu_item_addon_group_id,
                                restaurant_id=db_restaurant_id, created_at=datetime.now(timezone.utc)
                            ))

            counts["items"] += 1

        # Variations
        if menu_data.get("variations"):
            group_names = set()
            group_name_to_id = {}

            for variation in menu_data["variations"]:
                group_name = variation.get("groupname", "")
                if group_name:
                    group_names.add(group_name)

            for group_name in group_names:
                existing_group = db.query(VariationGroups).filter(
                    VariationGroups.restaurant_id == db_restaurant_id,
                    VariationGroups.variation_group_name == group_name
                ).first()

                if existing_group:
                    existing_group.updated_at = datetime.now(timezone.utc)
                    group_name_to_id[group_name] = existing_group.variation_group_id
                    counts["updated"] += 1
                else:
                    new_group_id = uuid.uuid4()
                    db.add(VariationGroups(
                        variation_group_id=new_group_id, restaurant_id=db_restaurant_id,
                        variation_group_name=group_name, variation_group_selection_type="single", created_at=datetime.now(timezone.utc)
                    ))
                    db.flush()
                    group_name_to_id[group_name] = new_group_id
                    counts["created"] += 1

            for variation in menu_data["variations"]:
                petpooja_variation_id = safe_int(variation.get("variationid"))
                if not petpooja_variation_id:
                    continue
                processed_ids["variations"].append(petpooja_variation_id)

                petpooja_item_id = safe_int(variation.get("itemid"))
                menu_item = db.query(MenuItem).filter(
                    MenuItem.ext_petpooja_item_id == petpooja_item_id,
                    MenuItem.restaurant_id == db_restaurant_id
                ).first() if petpooja_item_id else None
                menu_item_id = menu_item.menu_item_id if menu_item else None

                group_name = variation.get("groupname", "")
                variation_group_id = group_name_to_id.get(group_name)

                existing_variation = db.query(MenuItemVariation).filter(
                    MenuItemVariation.ext_petpooja_variation_id == petpooja_variation_id,
                    MenuItemVariation.restaurant_id == db_restaurant_id
                ).first()

                if existing_variation:
                    existing_variation.menu_item_variation_name = variation.get("variationname", "")
                    existing_variation.menu_item_variation_price = safe_float(variation.get("price"))
                    existing_variation.menu_item_variation_status = convert_status(variation.get("active", "1"))
                    existing_variation.menu_item_variation_rank = safe_int(variation.get("variationrank"))
                    existing_variation.menu_item_variation_allow_addon = variation.get("variationallowaddon") == "1"
                    existing_variation.menu_item_variation_packaging_charges = safe_float(variation.get("variation_packingcharges")) if variation.get("variation_packingcharges") else None
                    existing_variation.menu_item_variation_markup_price = safe_float(variation.get("markup_price")) if variation.get("markup_price") else None
                    if menu_item_id:
                        existing_variation.menu_item_id = menu_item_id
                    if variation_group_id:
                        existing_variation.variation_group_id = variation_group_id
                    existing_variation.updated_at = datetime.now(timezone.utc)
                    counts["updated"] += 1
                else:
                    db.add(MenuItemVariation(
                        menu_item_variation_id=uuid.uuid4(), menu_item_id=menu_item_id, restaurant_id=db_restaurant_id,
                        variation_group_id=variation_group_id, menu_item_variation_name=variation.get("variationname", ""),
                        menu_item_variation_price=safe_float(variation.get("price")), menu_item_variation_status=convert_status(variation.get("active", "1")),
                        menu_item_variation_rank=safe_int(variation.get("variationrank")),
                        menu_item_variation_allow_addon=variation.get("variationallowaddon") == "1",
                        menu_item_variation_packaging_charges=safe_float(variation.get("variation_packingcharges")) if variation.get("variation_packingcharges") else None,
                        menu_item_variation_markup_price=safe_float(variation.get("markup_price")) if variation.get("markup_price") else None,
                        ext_petpooja_variation_id=petpooja_variation_id, created_at=datetime.now(timezone.utc)
                    ))
                    counts["created"] += 1

            counts["variations"] = len(menu_data["variations"])

        # Discounts
        for discount in menu_data.get("discounts", []):
            petpooja_id = safe_int(discount.get("discountid"))
            if not petpooja_id:
                continue
            processed_ids["discounts"].append(petpooja_id)

            existing = db.query(Discount).filter(
                Discount.ext_petpooja_discount_id == petpooja_id,
                Discount.restaurant_id == db_restaurant_id
            ).first()

            if existing:
                existing.discount_name = discount.get("discountname", "")
                existing.discount_description = discount.get("description", "")
                existing.discount_type = discount.get("discounttype", "1")
                existing.discount_value = safe_float(discount.get("discount"))
                existing.discount_status = convert_status(discount.get("active", "1"))
                existing.discount_rank = safe_int(discount.get("rank"))
                existing.updated_at = datetime.now(timezone.utc)
                counts["updated"] += 1
            else:
                db.add(Discount(
                    discount_id=uuid.uuid4(), restaurant_id=db_restaurant_id,
                    discount_name=discount.get("discountname", ""), discount_description=discount.get("description", ""),
                    discount_type=discount.get("discounttype", "1"), discount_value=safe_float(discount.get("discount")),
                    discount_status=convert_status(discount.get("active", "1")), discount_rank=safe_int(discount.get("rank")),
                    ext_petpooja_discount_id=petpooja_id, created_at=datetime.now(timezone.utc)
                ))
                counts["created"] += 1
            counts["discounts"] += 1

        # Mark deleted items (items not in current sync)
        if processed_ids["items"]:
            deleted_count = db.query(MenuItem).filter(
                MenuItem.restaurant_id == db_restaurant_id,
                MenuItem.ext_petpooja_item_id.notin_(processed_ids["items"]),
                MenuItem.is_deleted.is_(False)
            ).update({"is_deleted": True, "updated_at": datetime.now(timezone.utc)}, synchronize_session=False)
            counts["deleted"] += deleted_count

        if processed_ids["categories"]:
            db.query(MenuSubCategories).filter(
                MenuSubCategories.restaurant_id == db_restaurant_id,
                MenuSubCategories.ext_petpooja_categories_id.notin_(processed_ids["categories"]),
                MenuSubCategories.is_deleted.is_(False)
            ).update({"is_deleted": True, "updated_at": datetime.now(timezone.utc)}, synchronize_session=False)

        if processed_ids["addon_groups"]:
            db.query(MenuItemAddonGroup).filter(
                MenuItemAddonGroup.restaurant_id == db_restaurant_id,
                MenuItemAddonGroup.ext_petpooja_addon_group_id.notin_(processed_ids["addon_groups"]),
                MenuItemAddonGroup.is_deleted.is_(False)
            ).update({"is_deleted": True, "updated_at": datetime.now(timezone.utc)}, synchronize_session=False)

        if processed_ids["variations"]:
            db.query(MenuItemVariation).filter(
                MenuItemVariation.restaurant_id == db_restaurant_id,
                MenuItemVariation.ext_petpooja_variation_id.notin_(processed_ids["variations"]),
                MenuItemVariation.is_deleted.is_(False)
            ).update({"is_deleted": True, "updated_at": datetime.now(timezone.utc)}, synchronize_session=False)

        db.flush()
        return {"success": True, "message": "Menu stored successfully", "counts": counts}

    except Exception as e:
        logger.error(f"Error storing menu: {str(e)}")
        raise MenuServiceError(f"Failed to store menu: {str(e)}")

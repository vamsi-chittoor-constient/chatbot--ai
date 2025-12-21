from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Dict, Optional, Any
from datetime import time as time_type
from decimal import Decimal
import uuid
import httpx
import logging
import os
import re

from app.models.chain_models import (
    ChainInfoTable,
    ChainContactTable,
    ChainLocationTable,
)
from app.models.location_models import (
    PincodeTable,
    CityTable,
    StateTable,
    CountryTable,
)
from app.models.branch_models import (
    BranchInfoTable,
    BranchContactTable,
    BranchLocationTable,
    BranchTimingPolicy,
)
from app.models.other_models import RestaurantTable, Cuisines, VariationGroups
from app.models.menu_models import (
    MenuSections,
    MenuCategories,
    MenuSubCategories,
    MenuItem,
    MenuItemAddonGroup,
    MenuItemAddonItem,
    MenuItemAddonMapping,
    MenuItemAttribute,
    MenuItemTag,
    MenuItemTagMapping,
    MenuItemVariation,
    MenuItemTaxMapping,
    MenuItemCuisineMapping,
)
from app.models.integration_models import (
    IntegrationConfigTable,
    IntegrationCredentialsTable,
    IntegrationProviderTable,
)
from app.schemas.chain import StoreChainDetailsRequest
from app.schemas.petpooja_chain import StoreChainDetailsPetpoojaRequest

# Import encryption utilities for production-grade credential encryption
from app.utils.encryption import get_encryption_service, EncryptionError, generate_api_key
from app.core.config import settings

logger = logging.getLogger(__name__)

class ChainServiceError(Exception):
    pass


def encrypt_credentials_for_storage(credentials_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Encrypt sensitive credential fields before storing in database.

    Args:
        credentials_dict: Dictionary containing credential key-value pairs

    Returns:
        Dictionary with sensitive fields encrypted
    """
    encryption_service = get_encryption_service()
    return encryption_service.encrypt_credentials(credentials_dict)


def decrypt_credentials_for_use(db: Session, integration_config_id: str) -> Dict[str, Any]:
    """
    Retrieve and decrypt credentials from database for API usage.
    This function safely decrypts only the configured sensitive fields (app_key, app_secret, access_token)
    and leaves other fields like restaurant_mapping_id and petpooja_restaurantid unencrypted.

    Args:
        db: Database session
        integration_config_id: Integration config ID to retrieve credentials for

    Returns:
        Dictionary with decrypted credential values

    Raises:
        Exception: If integration config or credentials not found
        EncryptionError: If decryption fails due to key mismatch
    """
    # Query all credentials for the integration config
    creds = db.query(IntegrationCredentialsTable).filter(
        IntegrationCredentialsTable.integration_config_id == integration_config_id,
        IntegrationCredentialsTable.is_deleted == False
    ).all()

    if not creds:
        raise Exception(f"No credentials found for integration_config_id: {integration_config_id}")

    # Build credentials dictionary
    credentials_dict = {cred.credential_key: cred.credential_value for cred in creds}

    # Decrypt sensitive fields
    encryption_service = get_encryption_service()
    try:
        return encryption_service.decrypt_credentials(credentials_dict)
    except EncryptionError as e:
        logger.error(f"Failed to decrypt credentials for integration_config_id {integration_config_id}: {e}")
        raise Exception(f"Credential decryption failed.")


def get_chain_by_name(db: Session, name: str):
    chains = (
        db.query(ChainInfoTable)
        .filter(
            ChainInfoTable.chain_name.ilike(f"%{name}%"),
            ChainInfoTable.is_deleted.is_(False),
        )
        .limit(5)
        .all()
    )

    result = []

    for i, chain in enumerate(chains):
        # primary / first non-deleted contact
        contact = (
            db.query(ChainContactTable)
            .filter(
                ChainContactTable.chain_id == chain.chain_id,
                ChainContactTable.is_deleted.is_(False),
            )
            .order_by(ChainContactTable.is_primary.desc())
            .first()
        )

        # first non-deleted location
        location = (
            db.query(ChainLocationTable)
            .filter(
                ChainLocationTable.chain_id == chain.chain_id,
                ChainLocationTable.is_deleted.is_(False),
            )
            .first()
        )

        city_name = state_name = country_name = None
        pincode_value = None

        if location and location.pincode_id:
            pincode = (
                db.query(PincodeTable)
                .filter(
                    PincodeTable.pincode_id == location.pincode_id,
                    PincodeTable.is_deleted.is_(False),
                )
                .first()
            )

            if pincode:
                pincode_value = pincode.pincode

                city = (
                    db.query(CityTable)
                    .filter(
                        CityTable.city_id == pincode.city_id,
                        CityTable.is_deleted.is_(False),
                    )
                    .first()
                )

                if city:
                    city_name = city.city_name

                    state = (
                        db.query(StateTable)
                        .filter(
                            StateTable.state_id == city.state_id,
                            StateTable.is_deleted.is_(False),
                        )
                        .first()
                    )

                    if state:
                        state_name = state.state_name

                        country = (
                            db.query(CountryTable)
                            .filter(
                                CountryTable.country_id == state.country_id,
                                CountryTable.is_deleted.is_(False),
                            )
                            .first()
                        )

                        if country:
                            country_name = country.country_name
        result.append(
            {
                "chainIndex": i,
                "chainId": str(chain.chain_id),
                "chainName": chain.chain_name,
                "website": chain.chain_website_url,
                "logoUrl": chain.chain_logo_url,
                "contactType": contact.contact_type if contact else None,
                "contactValue": contact.contact_value if contact else None,
                "contactLabel": contact.contact_label if contact else None,
                "address": location.address_line if location else None,
                "landmark": location.landmark if location else None,
                "pincode": pincode_value if pincode_value else None,
                "city": city_name if city_name else None,
                "state": state_name if state_name else None,
                "country": country_name if country_name else None,
                "latitude": str(location.latitude) if location and location.latitude else None,
                "longitude": str(location.longitude) if location and location.longitude else None,
            }
        )

    return result


def store_chain_details(db: Session, request: StoreChainDetailsRequest) -> Dict:
    """
    Store complete chain details including branches, menu configuration, and menu items.

    Args:
        db: Database session
        request: StoreChainDetailsRequest containing all chain data

    Returns:
        Dict with success status and created IDs
    """
    try:
        # Helper function to parse time
        def parse_time(time_str: str) -> Optional[time_type]:
            if not time_str or time_str == "":
                return None
            try:
                parts = time_str.split(":")
                return time_type(int(parts[0]), int(parts[1]))
            except (ValueError, IndexError, TypeError):
                return None

        # Helper function to get or create location records
        def get_or_create_pincode(country_name: str, state_name: str, city_name: str, pincode_value: str) -> Optional[uuid.UUID]:
            if not pincode_value:
                return None

            # Get or create country
            country = db.query(CountryTable).filter(
                CountryTable.country_name == country_name,
                CountryTable.is_deleted.is_(False)
            ).first()

            if not country:
                country = CountryTable(
                    country_id=uuid.uuid4(),
                    country_name=country_name)
                db.add(country)
                db.flush()

            # Get or create state
            state = db.query(StateTable).filter(
                StateTable.state_name == state_name,
                StateTable.country_id == country.country_id,
                StateTable.is_deleted.is_(False)
            ).first()

            if not state:
                state = StateTable(
                    state_id=uuid.uuid4(),
                    state_name=state_name,
                    country_id=country.country_id
                )
                db.add(state)
                db.flush()

            # Get or create city
            city = db.query(CityTable).filter(
                CityTable.city_name == city_name,
                CityTable.state_id == state.state_id,
                CityTable.is_deleted.is_(False)
            ).first()

            if not city:
                city = CityTable(
                    city_id=uuid.uuid4(),
                    city_name=city_name,
                    state_id=state.state_id
                )
                db.add(city)
                db.flush()

            # Get or create pincode
            pincode = db.query(PincodeTable).filter(
                PincodeTable.pincode == pincode_value,
                PincodeTable.city_id == city.city_id,
                PincodeTable.is_deleted.is_(False)
            ).first()

            if not pincode:
                pincode = PincodeTable(
                    pincode_id=uuid.uuid4(),
                    pincode=pincode_value,
                    city_id=city.city_id,
                    area_name=city_name  # Save city name as area_name
                )
                db.add(pincode)
                db.flush()
            else:
                # Update area_name if not set
                if not pincode.area_name:
                    pincode.area_name = city_name
                    db.flush()

            return pincode.pincode_id

        # 1. Create Chain Info
        chain = ChainInfoTable(
            chain_name=request.chain_info.chain_name,
            chain_website_url=request.chain_info.website,
            chain_logo_url=request.chain_info.logo_url,
            chain_type=request.business_type
        )
        db.add(chain)
        db.flush()

        # 2. Create Chain Contacts
        if request.chain_info.contact_number:
            chain_contact_phone = ChainContactTable(
                chain_id=chain.chain_id,
                contact_type=request.chain_info.contact_type or "mobile",
                contact_value=request.chain_info.contact_number,
                is_primary=True
            )
            db.add(chain_contact_phone)

        if request.chain_info.contact_email:
            chain_contact_email = ChainContactTable(
                chain_id=chain.chain_id,
                contact_type="email",
                contact_value=request.chain_info.contact_email,
                is_primary=False
            )
            db.add(chain_contact_email)

        # 3. Create Chain Location
        if request.chain_info.address:
            pincode_id = get_or_create_pincode(
                request.chain_info.country,
                request.chain_info.state,
                request.chain_info.city,
                request.chain_info.pincode
            )

            chain_location = ChainLocationTable(
                chain_id=chain.chain_id,
                address_line=request.chain_info.address,
                landmark=request.chain_info.landmark,
                pincode_id=pincode_id,
                latitude=Decimal(request.chain_info.latitude) if request.chain_info.latitude else None,
                longitude=Decimal(request.chain_info.longitude) if request.chain_info.longitude else None
            )
            db.add(chain_location)

        # 4. Create Menu Configuration
        # Store section/category name to ID mappings
        section_map = {}
        category_map = {}
        subcategory_map = {}
        addon_group_map = {}

        # Create Parent Categories (Menu Sections)
        for section in request.menuConfiguration.parentCategories:
            menu_section = MenuSections(
                restaurant_id=None,  # Will be set per restaurant
                menu_section_name=section.name,
                menu_section_description=section.description,
                menu_section_rank=section.rank,
                menu_section_status="active" if section.isActive else "inactive"
            )
            db.add(menu_section)
            db.flush()
            section_map[section.name] = menu_section.menu_section_id

        # Create Group Categories (Menu Categories)
        for category in request.menuConfiguration.groupCategories:
            menu_category = MenuCategories(
                restaurant_id=None,
                menu_category_name=category.name,
                menu_category_description=category.description,
                menu_category_rank=category.rank,
                menu_category_status="active" if category.isActive else "inactive"
            )
            db.add(menu_category)
            db.flush()
            category_map[category.name] = menu_category.menu_category_id

        # Create Categories (Menu Sub Categories)
        for subcategory in request.menuConfiguration.categories:
            menu_subcategory = MenuSubCategories(
                restaurant_id=None,
                category_id=category_map.get(subcategory.groupCategory) if subcategory.groupCategory else None,
                sub_category_name=subcategory.name,
                sub_category_description=subcategory.description,
                sub_category_rank=subcategory.rank,
                sub_category_status="active" if subcategory.isActive else "inactive"
            )
            db.add(menu_subcategory)
            db.flush()
            subcategory_map[subcategory.name] = menu_subcategory.menu_sub_category_id

        # Create Addon Groups
        for addon_group in request.menuConfiguration.addonGroups:
            menu_addon_group = MenuItemAddonGroup(
                restaurant_id=None,
                menu_item_addon_group_name=addon_group.name,
                menu_item_addon_group_rank=addon_group.rank,
                menu_item_addon_group_selection_min=addon_group.selectionMinimum,
                menu_item_addon_group_selection_max=addon_group.selectionMaximum,
                menu_item_addon_group_status="active" if addon_group.isActive else "inactive"
            )
            db.add(menu_addon_group)
            db.flush()
            addon_group_map[addon_group.name] = menu_addon_group.menu_item_addon_group_id

        db.flush()

        # 5. Create Integration Provider and Config (if provided)
        provider_id = None
        if request.data_source_integration:
            for integration in request.data_source_integration:
                # Get or create provider
                provider = db.query(IntegrationProviderTable).filter(
                    IntegrationProviderTable.provider_name == integration.system_provider,
                    IntegrationProviderTable.is_deleted.is_(False)
                ).first()

                if not provider:
                    provider = IntegrationProviderTable(
                provider_id=uuid.uuid4(),
                provider_name=integration.system_provider
                    )
                    db.add(provider)
                    db.flush()

                provider_id = provider.provider_id

        # 6. Create Branches and Restaurants
        restaurant_ids = []
        branch_ids = []

        for branch_data in request.branches:
            # Create Branch Info
            clean_branch_name = re.sub(r'\[.*?\]', '', branch_data.name).strip()
            branch = BranchInfoTable(
                chain_id=chain.chain_id,
                branch_name=clean_branch_name,
                is_active=branch_data.active
            )
            db.add(branch)
            db.flush()
            branch_ids.append(str(branch.branch_id))

            # Create Branch Contacts
            if branch_data.phone:
                branch_contact_phone = BranchContactTable(
                    branch_id=branch.branch_id,
                    contact_type="phone",
                    contact_value=branch_data.phone,
                    is_primary=True
                )
                db.add(branch_contact_phone)

            if branch_data.email:
                branch_contact_email = BranchContactTable(
                    branch_id=branch.branch_id,
                    contact_type="email",
                    contact_value=branch_data.email,
                    is_primary=False
                )
                db.add(branch_contact_email)

            # Create Branch Location
            branch_location = BranchLocationTable(
                branch_id=branch.branch_id,
                address_line=branch_data.address
            )
            db.add(branch_location)

            # Create Restaurant (links chain and branch)
            restaurant = RestaurantTable(
                restaurant_id=uuid.uuid4(),
                chain_id=chain.chain_id,
                branch_id=branch.branch_id
            )
            db.add(restaurant)
            db.flush()
            restaurant_ids.append(str(restaurant.restaurant_id))

            # Create Integration Config for this restaurant
            if provider_id and request.data_source_integration:
                for integration in request.data_source_integration:
                    integration_config = IntegrationConfigTable(
                        integration_config_id=uuid.uuid4(),
                        restaurant_id=restaurant.restaurant_id,
                        provider_id=provider_id,
                        is_enabled=integration.sandbox_enabled
                    )
                    db.add(integration_config)
                    db.flush()

                    # Store credentials (with encryption for sensitive fields)
                    credentials_dict = {
                        "app_key": integration.app_key,
                        "app_secret": integration.app_secret,
                        "access_token": integration.access_token,
                        "restaurant_mapping_id": integration.restaurant_mapping_id,
                    }

                    # Encrypt sensitive credentials before storing
                    encrypted_credentials = encrypt_credentials_for_storage(credentials_dict)

                    # Store encrypted credentials in database
                    for key, value in encrypted_credentials.items():
                        print(f"{key} : {value}")
                        if value:  # Only store non-empty values
                            cred = IntegrationCredentialsTable(
                                credential_id=uuid.uuid4(),
                                integration_config_id=integration_config.integration_config_id,
                                credential_key=key,
                                credential_value=value
                            )
                            db.add(cred)

            # Create Branch Policy
            branch_policy = BranchTimingPolicy(
                branch_timing_id=uuid.uuid4(),
                restaurant_id=restaurant.restaurant_id,
                opening_time=parse_time(branch_data.restaurant_open),
                closing_time=parse_time(branch_data.restaurant_close),
                food_ordering_start_time=parse_time(branch_data.food_ordering_open),
                food_ordering_closing_time=parse_time(branch_data.food_ordering_close),
                table_booking_open_time=parse_time(branch_data.table_booking_open),
                table_booking_close_time=parse_time(branch_data.table_booking_close),
                minimum_order_amount=Decimal(branch_data.minimum_order_amount) if branch_data.minimum_order_amount else None,
                minimum_delivery_time_min=int(branch_data.minimum_delivery_time) if branch_data.minimum_delivery_time else None,
                delivery_charge=Decimal(branch_data.delivery_charge) if branch_data.delivery_charge else None,
                minimum_prep_time_min=int(branch_data.minimum_prep_time) if branch_data.minimum_prep_time else None,
                calculate_tax_on_packing=branch_data.calculate_tax_on_packing,
                calculate_tax_on_delivery=branch_data.calculate_tax_on_delivery,
                packaging_applicable_on=branch_data.packaging_applicable_on,
                packaging_charge=Decimal(branch_data.packaging_charge) if branch_data.packaging_charge else None,
                packaging_charge_type=branch_data.packaging_charge_type,
                delivery_hours_from1=parse_time(branch_data.delivery_from1),
                delivery_hours_to1=parse_time(branch_data.delivery_to1),
                delivery_hours_from2=parse_time(branch_data.delivery_from2),
                delivery_hours_to2=parse_time(branch_data.delivery_to2)
            )
            db.add(branch_policy)

            # 7. Create Menu Items for this branch
            for menu_item_data in branch_data.menus:
                # Get or create attribute
                attribute = db.query(MenuItemAttribute).filter(
                    MenuItemAttribute.menu_item_attribute_name == menu_item_data.attribute,
                    MenuItemAttribute.restaurant_id == restaurant.restaurant_id,
                    MenuItemAttribute.is_deleted.is_(False)
                ).first()

                if not attribute:
                    attribute = MenuItemAttribute(
                        menu_item_attribute_id=uuid.uuid4(),
                        restaurant_id=restaurant.restaurant_id,
                        menu_item_attribute_name=menu_item_data.attribute,
                        menu_item_attribute_status="active"
                    )
                    db.add(attribute)
                    db.flush()

                # Create menu item
                menu_item = MenuItem(
                    restaurant_id=restaurant.restaurant_id,
                    menu_sub_category_id=subcategory_map.get(menu_item_data.category),
                    menu_item_name=menu_item_data.dish_name,
                    menu_item_description=menu_item_data.description,
                    menu_item_price=Decimal(menu_item_data.price),
                    menu_item_markup_price=Decimal(menu_item_data.markup_price) if menu_item_data.markup_price else None,
                    menu_item_allow_variation=menu_item_data.variation_allowed,
                    menu_item_allow_addon=menu_item_data.addon_allowed,
                    menu_item_status="active" if menu_item_data.is_available else "inactive",
                    menu_item_attribute_id=attribute.menu_item_attribute_id,
                    menu_item_spice_level=menu_item_data.spice_level,
                    menu_item_minimum_preparation_time=int(menu_item_data.preparation_time) if menu_item_data.preparation_time else None,
                    menu_item_favorite=menu_item_data.item_favorite,
                    menu_item_ignore_taxes=menu_item_data.ignore_taxes,
                    menu_item_ignore_discounts=menu_item_data.ignore_discounts,
                    menu_item_in_stock=menu_item_data.in_stock,
                    menu_item_is_combo=menu_item_data.is_combo,
                    menu_item_rank=int(menu_item_data.item_rank) if menu_item_data.item_rank else 0
                )
                db.add(menu_item)
                db.flush()

                # Create tax mapping
                if menu_item_data.gst_type:
                    tax_mapping = MenuItemTaxMapping(
                                    menu_item_tax_mapping_id=uuid.uuid4(),
                                    menu_item_id=menu_item.menu_item_id,
                        restaurant_id=restaurant.restaurant_id,
                        is_tax_inclusive=menu_item_data.tax_inclusive,
                        gst_type=menu_item_data.gst_type
                    )
                    db.add(tax_mapping)

                # Create cuisine mapping
                if menu_item_data.cuisine:
                    cuisine = db.query(Cuisines).filter(
                        Cuisines.cuisine_name == menu_item_data.cuisine,
                        Cuisines.is_deleted.is_(False)
                    ).first()

                    if not cuisine:
                        cuisine = Cuisines(
                        cuisine_id=uuid.uuid4(),
                        cuisine_name=menu_item_data.cuisine,
                            cuisine_status="active"
                        )
                        db.add(cuisine)
                        db.flush()

                    cuisine_mapping = MenuItemCuisineMapping(
                        menu_item_cuisine_mapping_id=uuid.uuid4(),
                        menu_item_id=menu_item.menu_item_id,
                        cuisine_id=cuisine.cuisine_id
                    )
                    db.add(cuisine_mapping)

                # Create tags
                for tag_name in menu_item_data.item_tags:
                    if not tag_name or tag_name == "":
                        continue

                    tag = db.query(MenuItemTag).filter(
                        MenuItemTag.menu_item_tag_name == tag_name,
                        MenuItemTag.is_deleted.is_(False)
                    ).first()

                    if not tag:
                        tag = MenuItemTag(
                                menu_item_tag_id=uuid.uuid4(),
                                menu_item_tag_name=tag_name,
                            menu_item_tag_status="active"
                        )
                        db.add(tag)
                        db.flush()

                    tag_mapping = MenuItemTagMapping(
                                menu_item_tag_mapping_id=uuid.uuid4(),
                                menu_item_id=menu_item.menu_item_id,
                        menu_item_tag_id=tag.menu_item_tag_id
                    )
                    db.add(tag_mapping)

                # Create variations
                for variation_data in menu_item_data.variations:
                    variation = MenuItemVariation(
                            menu_item_variation_id=uuid.uuid4(),
                            menu_item_id=menu_item.menu_item_id,
                        restaurant_id=restaurant.restaurant_id,
                        menu_item_variation_name=variation_data.group_name,
                        menu_item_variation_price=Decimal(variation_data.price) if variation_data.price else None,
                        menu_item_variation_markup_price=Decimal(variation_data.markup_price) if variation_data.markup_price else None,
                        menu_item_variation_status="active" if variation_data.active else "inactive",
                        menu_item_variation_allow_addon=variation_data.allow_addon,
                        menu_item_variation_packaging_charges=Decimal(variation_data.packaging_charges) if variation_data.packaging_charges else None,
                        menu_item_variation_rank=int(variation_data.variation_rank) if variation_data.variation_rank else 0
                    )
                    db.add(variation)
                    db.flush()

                    # Create addon mappings for variation
                    for addon_data in variation_data.addons:
                        if addon_data.addon_group in addon_group_map:
                            addon_mapping = MenuItemAddonMapping(
                                    menu_item_addon_mapping_id=uuid.uuid4(),
                                    menu_item_id=menu_item.menu_item_id,
                                menu_item_variation_id=variation.menu_item_variation_id,
                                menu_item_addon_group_id=addon_group_map[addon_data.addon_group],
                                restaurant_id=restaurant.restaurant_id
                            )
                            db.add(addon_mapping)

                # Create addon mappings for menu item
                for addon_data in menu_item_data.addons:
                    if addon_data.addon_group in addon_group_map:
                        addon_mapping = MenuItemAddonMapping(
                                    menu_item_addon_mapping_id=uuid.uuid4(),
                                    menu_item_id=menu_item.menu_item_id,
                            menu_item_addon_group_id=addon_group_map[addon_data.addon_group],
                            restaurant_id=restaurant.restaurant_id
                        )
                        db.add(addon_mapping)

        # Commit all changes
        db.commit()

        return {
            "success": True,
            "message": "Chain details stored successfully",
            "chain_id": str(chain.chain_id),
            "restaurant_ids": restaurant_ids,
            "branch_ids": branch_ids
        }

    except SQLAlchemyError as e:
        db.rollback()
        raise Exception(f"Database error: {str(e)}")
    except Exception as e:
        db.rollback()
        raise Exception(f"Error storing chain details: {str(e)}")


# ============================================================================
# NEW CLEAN FUNCTIONS - Only 2 functions for chain management
# ============================================================================

async def fetch_menu_from_petpooja_with_credentials_only(
    restaurant_id: str,
    app_key: str,
    app_secret: str,
    access_token: str,
    sandbox_enabled: bool
) -> Dict[str, Any]:
    """
    Fetch menu from PetPooja API using custom credentials - data only, no storage

    Args:
        restaurant_id: Internal restaurant ID
        app_key: PetPooja app key
        app_secret: PetPooja app secret
        access_token: PetPooja access token
        sandbox_enabled: Whether to use sandbox environment

    Returns:
        Dict containing menu data only

    Raises:
        MenuServiceError: If fetching menu fails
    """
    try:
        # Determine base URL
        if sandbox_enabled:
            base_url = settings.PETPOOJA_SANDBOX_BASE_URL
            logger.info(f"Fetching menu in SANDBOX mode for restaurant {restaurant_id}")
        else:
            base_url = settings.PETPOOJA_BASE_URL
            logger.info(f"Fetching menu in PRODUCTION mode for restaurant {restaurant_id}")

        # Prepare request
        menu_endpoint = getattr(settings, 'PETPOOJA_FETCH_MENU_ENDPOINT', '/mapped_restaurant_menus')
        url = f"{base_url}{menu_endpoint}"

        headers = {
            "Content-Type": "application/json",
            "app-key": app_key,
            "app-secret": app_secret,
            "access-token": access_token
        }

        payload = {
            "restID": restaurant_id
        }

        # Make request
        with httpx.Client(timeout=settings.HTTP_TIMEOUT) as client:
            response = client.post(url, json=payload, headers=headers)

            # Parse response
            try:
                response_data = response.json()
            except Exception as e:
                logger.error(f"Failed to parse JSON response: {e}")
                raise ChainServiceError(f"Invalid JSON response: {str(e)}")

            # Check HTTP status
            if response.status_code != 200:
                error_msg = response_data.get("message", "Unknown error")
                logger.error(f"PetPooja API Error: {error_msg}")
                raise ChainServiceError(f"API returned {response.status_code}: {error_msg}")

            # Check success field
            if not response_data.get("success", False):
                error_msg = response_data.get("message", "Request failed")
                logger.error(f"PetPooja API Error: {error_msg}")
                raise ChainServiceError(f"Failed to fetch menu from PetPooja: {error_msg}")

            logger.info(f"Menu fetched successfully for restaurant {restaurant_id}")

            return {
                "success": True,
                "message": "Menu fetched successfully",
                "data": response_data
            }

    except httpx.HTTPError as e:
        logger.error(f"HTTP Error: {str(e)}")
        raise ChainServiceError(f"HTTP request failed: {str(e)}")
    except ChainServiceError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error while fetching menu: {str(e)}")
        raise ChainServiceError(f"Failed to fetch menu: {str(e)}")


def store_menu_data(db: Session, request: StoreChainDetailsPetpoojaRequest) -> Dict:
    """
    Store complete menu data in database.

    This function stores chain, branch, and menu data from PetPooja format.
    """
    try:
        logger.info(f"store_menu_data called with request containing:")
        logger.info(f"  - Chain: {request.chain_info.chain_name or 'No name'}")
        logger.info(f"  - Branches: {len(request.branches) if request.branches else 0}")
        logger.info(f"  - Menu data present: {request.menu_data is not None}")
        if request.menu_data:
            logger.info(f"  - Menu items count: {len(request.menu_data.items) if hasattr(request.menu_data, 'items') else 'N/A'}")
        else:
            logger.warning("WARNING: menu_data is None - no menu items will be stored!")

        # Helper function to parse time
        def parse_time(time_str: str) -> Optional[time_type]:
            if not time_str or time_str == "":
                return None
            try:
                parts = time_str.split(":")
                return time_type(int(parts[0]), int(parts[1]))
            except (ValueError, IndexError, TypeError):
                return None

        # Helper function to parse minutes from strings like "30 Minutes"
        def parse_minutes(minutes_str: str) -> Optional[int]:
            if not minutes_str or minutes_str == "":
                return None
            try:
                import re
                numbers = re.findall(r'\d+', minutes_str)
                return int(numbers[0]) if numbers else None
            except (ValueError, IndexError, TypeError):
                return None

        # Helper function to get or create location records
        def get_or_create_pincode(country_name: str, state_name: str, city_name: str, pincode_value: str) -> Optional[uuid.UUID]:
            if not pincode_value or pincode_value == "":
                return None

            country = db.query(CountryTable).filter(
                CountryTable.country_name == country_name,
                CountryTable.is_deleted.is_(False)
            ).first()

            if not country:
                country = CountryTable(
                    country_id=uuid.uuid4(),
                    country_name=country_name)
                db.add(country)
                db.flush()

            state = db.query(StateTable).filter(
                StateTable.state_name == state_name,
                StateTable.country_id == country.country_id,
                StateTable.is_deleted.is_(False)
            ).first()

            if not state:
                state = StateTable(
                    state_id=uuid.uuid4(),
                    state_name=state_name,
                    country_id=country.country_id)
                db.add(state)
                db.flush()

            city = db.query(CityTable).filter(
                CityTable.city_name == city_name,
                CityTable.state_id == state.state_id,
                CityTable.is_deleted.is_(False)
            ).first()

            if not city:
                city = CityTable(
                    city_id=uuid.uuid4(),
                    city_name=city_name,
                    state_id=state.state_id)
                db.add(city)
                db.flush()

            pincode = db.query(PincodeTable).filter(
                PincodeTable.pincode == pincode_value,
                PincodeTable.city_id == city.city_id,
                PincodeTable.is_deleted.is_(False)
            ).first()

            if not pincode:
                pincode = PincodeTable(
                    pincode_id=uuid.uuid4(),
                    pincode=pincode_value,
                    city_id=city.city_id,
                    area_name=city_name)  # Save city name as area_name
                db.add(pincode)
                db.flush()
            else:
                # Update area_name if not set
                if not pincode.area_name:
                    pincode.area_name = city_name
                    db.flush()

            return pincode.pincode_id

        # Check if restaurant already exists by menusharingcode
        for branch_data in request.branches:
            menusharingcode = branch_data.details.menusharingcode
            if menusharingcode:
                existing_branch = db.query(BranchInfoTable).filter(
                    BranchInfoTable.ext_petpooja_restaurant_id == menusharingcode,
                    BranchInfoTable.is_deleted.is_(False)
                ).first()

                if existing_branch:
                    # Get associated restaurant and integration config
                    existing_restaurant = db.query(RestaurantTable).filter(
                        RestaurantTable.branch_id == existing_branch.branch_id,
                        RestaurantTable.is_deleted.is_(False)
                    ).first()

                    existing_api_key = None
                    if existing_restaurant:
                        existing_config = db.query(IntegrationConfigTable).filter(
                            IntegrationConfigTable.restaurant_id == existing_restaurant.restaurant_id,
                            IntegrationConfigTable.is_deleted.is_(False)
                        ).first()
                        if existing_config:
                            existing_api_key = existing_config.api_key

                    logger.info(f"Restaurant already exists with menusharingcode: {menusharingcode}")
                    return {
                        "success": False,
                        "message": f"Restaurant already exists with menusharingcode: {menusharingcode}",
                        "chain_id": str(existing_branch.chain_id),
                        "branch_id": str(existing_branch.branch_id),
                        "restaurant_id": str(existing_restaurant.restaurant_id) if existing_restaurant else None,
                        "api_key": existing_api_key,
                        "iframe_data": existing_restaurant.iframe if existing_restaurant else None
                    }

        # 1. Create Chain Info
        chain = ChainInfoTable(
            chain_id=uuid.uuid4(),
            chain_name=request.chain_info.chain_name or "Default Chain",
            chain_website_url=request.chain_info.website,
            chain_logo_url=request.chain_info.logo_url,
            chain_type=request.data_source_integration.business_type
        )
        db.add(chain)
        db.flush()

        # 2. Create Chain Contacts
        if request.chain_info.contact_number:
            chain_contact_phone = ChainContactTable(
                chain_contact_id=uuid.uuid4(),
                chain_id=chain.chain_id,
                contact_type=request.chain_info.contact_type or "mobile",
                contact_value=request.chain_info.contact_number,
                is_primary=True
            )
            db.add(chain_contact_phone)

        if request.chain_info.contact_email:
            chain_contact_email = ChainContactTable(
                chain_contact_id=uuid.uuid4(),
                chain_id=chain.chain_id,
                contact_type="email",
                contact_value=request.chain_info.contact_email,
                is_primary=False
            )
            db.add(chain_contact_email)

        # 3. Create Chain Location
        if request.chain_info.address:
            pincode_id = get_or_create_pincode(
                request.chain_info.country or (request.branches[0].details.country if request.branches else ""),
                request.chain_info.state or (request.branches[0].details.state if request.branches else ""),
                request.chain_info.city or (request.branches[0].details.city if request.branches else ""),
                request.chain_info.pincode
            )

            chain_location = ChainLocationTable(
                chain_location_id=uuid.uuid4(),
                chain_id=chain.chain_id,
                address_line=request.chain_info.address,
                landmark=request.chain_info.landmark,
                pincode_id=pincode_id,
                latitude=Decimal(request.chain_info.latitude) if request.chain_info.latitude and request.chain_info.latitude != "" else None,
                longitude=Decimal(request.chain_info.longitude) if request.chain_info.longitude and request.chain_info.longitude != "" else None
            )
            db.add(chain_location)

        # 4. Create Integration Provider
        provider = db.query(IntegrationProviderTable).filter(
            IntegrationProviderTable.provider_name == request.data_source_integration.system_provider,
            IntegrationProviderTable.is_deleted.is_(False)
        ).first()

        if not provider:
            provider = IntegrationProviderTable(
                provider_id=uuid.uuid4(),
                provider_name=request.data_source_integration.system_provider
            )
            db.add(provider)
            db.flush()

        # 6. Create Branches and Restaurants
        restaurant_ids = []
        branch_ids = []
        api_keys = []  # Store raw API keys for response

        # Loop through all branches (now it's a list)
        # Loop through all branches (now it's a list)
        for branch_data in request.branches:
            # Get restaurantid from branch or from data_source_integration
            petpooja_restaurant_id = branch_data.restaurantid
            if not petpooja_restaurant_id and hasattr(request.data_source_integration, 'petpooja_restaurantid'):
                petpooja_restaurant_id = request.data_source_integration.petpooja_restaurantid

            # Extract menusharingcode - this is what we store in ext_petpooja_restaurant_id for webhook matching
            menusharingcode = branch_data.details.menusharingcode
            if not menusharingcode:
                logger.warning(f"No menusharingcode found for branch {branch_data.details.restaurantname}")

            branch = BranchInfoTable(
                branch_id=uuid.uuid4(),
                chain_id=chain.chain_id,
                branch_name=branch_data.details.restaurantname,
                is_active=branch_data.active == "1",
                branch_personalized_greeting=branch_data.personalized_greeting if branch_data.personalized_greeting else None,
                ext_petpooja_restaurant_id=menusharingcode  # Store menusharingcode for webhook matching
            )
            db.add(branch)
            db.flush()
            branch_ids.append(str(branch.branch_id))
            logger.info(f"Created branch {branch.branch_id} with menusharingcode: {menusharingcode}")


            if branch_data.details.contact:
                branch_contact = BranchContactTable(
                    branch_contact_id=uuid.uuid4(),
                    branch_id=branch.branch_id,
                    contact_type="phone",
                    contact_value=branch_data.details.contact,
                    is_primary=True
                )
                db.add(branch_contact)

            # Create branch location
            # Use branch-level pincode if available, otherwise try from details
            branch_pincode = branch_data.pincode if branch_data.pincode else None
            pincode_id_for_branch = None

            if branch_pincode:
                # Get pincode from branch-level data
                pincode_id_for_branch = get_or_create_pincode(
                    branch_data.details.country,
                    branch_data.details.state,
                    branch_data.details.city,
                    branch_pincode
                )

            # Use branch-level landmark if available, otherwise from details
            branch_landmark = branch_data.landmark if branch_data.landmark else branch_data.details.landmark

            branch_location = BranchLocationTable(
                branch_location_id=uuid.uuid4(),
                branch_id=branch.branch_id,
                address_line=branch_data.details.address,
                landmark=branch_landmark,
                pincode_id=pincode_id_for_branch,
                latitude=Decimal(branch_data.details.latitude) if branch_data.details.latitude and branch_data.details.latitude != "" else None,
                longitude=Decimal(branch_data.details.longitude) if branch_data.details.longitude and branch_data.details.longitude != "" else None
            )
            db.add(branch_location)

            # Generate restaurant_id first
            restaurant_id = uuid.uuid4()

            # Generate unique API key for this integration (store raw in database)
            # Generate this BEFORE iframe so we can include api_key in iframe URL
            raw_api_key, _ = generate_api_key()
            api_keys.append(raw_api_key)

            # Generate iframe URL and HTML code for embedding chatbot
            # Use only api_key as URL parameter (api_key links to restaurant via integration_config)
            CHATBOT_BASE_URL = os.getenv("CHATBOT_BASE_URL", "https://chatbot.assist24.com")
            iframe_url = f"{CHATBOT_BASE_URL}/?api_key={raw_api_key}"
            iframe_html = f'''<iframe
  src="{iframe_url}"
  width="100%"
  height="700px"
  style="border:none; border-radius:16px;"
  allow="microphone"
></iframe>'''

            restaurant = RestaurantTable(
                restaurant_id=restaurant_id,
                chain_id=chain.chain_id,
                branch_id=branch.branch_id,
                iframe=iframe_html
            )
            db.add(restaurant)
            db.flush()
            restaurant_ids.append(str(restaurant.restaurant_id))

            integration_config = IntegrationConfigTable(
                integration_config_id=uuid.uuid4(),
                restaurant_id=restaurant.restaurant_id,
                provider_id=provider.provider_id,
                is_enabled=request.data_source_integration.sandbox_enabled,
                api_key=raw_api_key  # Store raw API key (not hashed)
            )
            db.add(integration_config)
            db.flush()

            # Store credentials (with encryption for sensitive fields)
            credentials_dict = {
                "app_key": request.data_source_integration.app_key,
                "app_secret": request.data_source_integration.app_secret,
                "access_token": request.data_source_integration.access_token,
                "restaurant_mapping_id": request.data_source_integration.restaurant_mapping_id,
                "petpooja_restaurantid": petpooja_restaurant_id,
            }

            # Encrypt sensitive credentials before storing
            encrypted_credentials = encrypt_credentials_for_storage(credentials_dict)

            # Store encrypted credentials in database
            for key, value in encrypted_credentials.items():
                if value:  # Only store non-empty values
                    print(f"STORE: {key} : {value}")
                    cred = IntegrationCredentialsTable(
                        credential_id=uuid.uuid4(),
                        integration_config_id=integration_config.integration_config_id,
                        credential_key=key,
                        credential_value=value
                    )
                    db.add(cred)

            # Create branch timing policy
            # Use branch-level timings if available, otherwise use defaults
            branch_policy = BranchTimingPolicy(
                branch_timing_id=uuid.uuid4(),
                restaurant_id=restaurant.restaurant_id,
                opening_time=parse_time(branch_data.branch_open_time) if branch_data.branch_open_time else None,
                closing_time=parse_time(branch_data.branch_close_time) if branch_data.branch_close_time else None,
                food_ordering_start_time=parse_time(branch_data.food_order_open_time) if branch_data.food_order_open_time else None,
                food_ordering_closing_time=parse_time(branch_data.food_order_close_time) if branch_data.food_order_close_time else None,
                table_booking_open_time=parse_time(branch_data.table_booking_open_time) if branch_data.table_booking_open_time else None,
                table_booking_close_time=parse_time(branch_data.table_booking_close_time) if branch_data.table_booking_close_time else None,
                minimum_order_amount=Decimal(branch_data.details.minimumorderamount) if branch_data.details.minimumorderamount else None,
                minimum_delivery_time_min=parse_minutes(branch_data.details.minimumdeliverytime),
                delivery_charge=Decimal(branch_data.details.deliverycharge) if branch_data.details.deliverycharge else None,
                minimum_prep_time_min=int(branch_data.details.minimum_prep_time) if branch_data.details.minimum_prep_time else None,
                calculate_tax_on_packing=branch_data.details.calculatetaxonpacking == 1,
                calculate_tax_on_delivery=branch_data.details.calculatetaxondelivery == 1,
                packaging_applicable_on=branch_data.details.packaging_applicable_on,
                packaging_charge=Decimal(branch_data.details.packaging_charge) if branch_data.details.packaging_charge and branch_data.details.packaging_charge != "" else None,
                packaging_charge_type=branch_data.details.packaging_charge_type,
                delivery_hours_from1=parse_time(branch_data.details.deliveryhoursfrom1),
                delivery_hours_to1=parse_time(branch_data.details.deliveryhoursto1),
                delivery_hours_from2=parse_time(branch_data.details.deliveryhoursfrom2),
                delivery_hours_to2=parse_time(branch_data.details.deliveryhoursto2)
            )
            db.add(branch_policy)

            # 5. Create Attributes for this restaurant
            attribute_map = {}
            if request.menu_data and request.menu_data.attributes:
                for attr_data in request.menu_data.attributes:
                    attribute = db.query(MenuItemAttribute).filter(
                        MenuItemAttribute.ext_petpooja_attributes_id == int(attr_data.attributeid),
                        MenuItemAttribute.restaurant_id == restaurant.restaurant_id,
                        MenuItemAttribute.is_deleted.is_(False)
                    ).first()

                    if not attribute:
                        attribute = MenuItemAttribute(
                            menu_item_attribute_id=uuid.uuid4(),
                            restaurant_id=restaurant.restaurant_id,
                            menu_item_attribute_name=attr_data.attribute,
                            menu_item_attribute_status="active" if attr_data.active == "1" else "inactive",
                            ext_petpooja_attributes_id=int(attr_data.attributeid)
                        )
                        db.add(attribute)
                        db.flush()

                    attribute_map[attr_data.attributeid] = attribute.menu_item_attribute_id

            # 6. Create Menu Data for this restaurant
            if request.menu_data:
                logger.info(f"Processing menu data for restaurant {restaurant.restaurant_id}")
                logger.info(f"Menu data contains: {len(request.menu_data.items)} items, "
                           f"{len(request.menu_data.categories)} categories, "
                           f"{len(request.menu_data.addongroups)} addon groups")

                section_map = {}
                for section_data in request.menu_data.parentcategories:
                    menu_section = MenuSections(
                        menu_section_id=uuid.uuid4(),
                        restaurant_id=restaurant.restaurant_id,
                        menu_section_name=section_data.name,
                        menu_section_rank=int(section_data.rank) if section_data.rank else 0,
                        menu_section_image_url=section_data.image_url,
                        menu_section_status="active" if section_data.status == "1" else "inactive",
                        ext_petpooja_parent_categories_id=int(section_data.id)
                    )
                    db.add(menu_section)
                    db.flush()
                    section_map[section_data.id] = menu_section.menu_section_id

                group_map = {}
                for group_data in request.menu_data.group_categories:
                    menu_category = MenuCategories(
                        menu_category_id=uuid.uuid4(),
                        restaurant_id=restaurant.restaurant_id,
                        menu_category_name=group_data.name,
                        menu_category_rank=int(group_data.rank) if group_data.rank else 0,
                        menu_category_status="active" if group_data.status == "1" else "inactive",
                        ext_petpooja_group_category_id=int(group_data.id)
                    )
                    db.add(menu_category)
                    db.flush()
                    group_map[group_data.id] = menu_category.menu_category_id

                category_map = {}
                for cat_data in request.menu_data.categories:
                    menu_subcategory = MenuSubCategories(
                        menu_sub_category_id=uuid.uuid4(),
                        restaurant_id=restaurant.restaurant_id,
                        category_id=group_map.get(cat_data.group_category_id),
                        menu_section_id=section_map.get(cat_data.parent_category_id),  # Map to parent section
                        sub_category_name=cat_data.categoryname,
                        sub_category_rank=int(cat_data.categoryrank) if cat_data.categoryrank else 0,
                        sub_category_status="active" if cat_data.active == "1" else "inactive",
                        sub_category_timings=cat_data.categorytimings,
                        sub_category_image_url=cat_data.category_image_url,
                        ext_petpooja_categories_id=int(cat_data.categoryid)
                    )
                    db.add(menu_subcategory)
                    db.flush()
                    category_map[cat_data.categoryid] = menu_subcategory.menu_sub_category_id

                addon_group_map = {}
                for addon_group_data in request.menu_data.addongroups:
                    menu_addon_group = MenuItemAddonGroup(
                        menu_item_addon_group_id=uuid.uuid4(),
                        restaurant_id=restaurant.restaurant_id,
                        menu_item_addon_group_name=addon_group_data.addongroup_name,
                        menu_item_addon_group_rank=int(addon_group_data.addongroup_rank) if addon_group_data.addongroup_rank else 0,
                        menu_item_addon_group_status="active" if addon_group_data.active == "1" else "inactive",
                        ext_petpooja_addon_group_id=int(addon_group_data.addongroupid)
                    )
                    db.add(menu_addon_group)
                    db.flush()
                    addon_group_map[addon_group_data.addongroupid] = menu_addon_group.menu_item_addon_group_id

                    for addon_item_data in addon_group_data.addongroupitems:
                        addon_item = MenuItemAddonItem(
                            menu_item_addon_id=uuid.uuid4(),
                            menu_item_addon_group_id=menu_addon_group.menu_item_addon_group_id,
                            restaurant_id=restaurant.restaurant_id,
                            menu_item_addon_item_name=addon_item_data.addonitem_name,
                            menu_item_addon_item_price=Decimal(addon_item_data.addonitem_price) if addon_item_data.addonitem_price else None,
                            menu_item_addon_item_status="active" if addon_item_data.active == "1" else "inactive",
                            menu_item_addon_item_rank=int(addon_item_data.addonitem_rank) if addon_item_data.addonitem_rank else 0,
                            menu_item_addon_item_attribute_id=attribute_map.get(addon_item_data.attributes)
                        )
                        db.add(addon_item)

                # Process standalone variations list (if present)
                variation_group_map = {}
                if request.menu_data.variations:
                    logger.info(f"Processing {len(request.menu_data.variations)} standalone variations")
                    # Group variations by groupname
                    grouped_variations = {}
                    for var_data in request.menu_data.variations:
                        if var_data.groupname not in grouped_variations:
                            grouped_variations[var_data.groupname] = []
                        grouped_variations[var_data.groupname].append(var_data)

                    # Create variation groups
                    for group_name, variations_list in grouped_variations.items():
                        # Check if variation group already exists
                        var_group = db.query(VariationGroups).filter(
                            VariationGroups.variation_group_name == group_name,
                            VariationGroups.restaurant_id == restaurant.restaurant_id,
                            VariationGroups.is_deleted.is_(False)
                        ).first()

                        if not var_group:
                            var_group = VariationGroups(
                                variation_group_id=uuid.uuid4(),
                                restaurant_id=restaurant.restaurant_id,
                                variation_group_name=group_name,
                                variation_group_status="active"
                            )
                            db.add(var_group)
                            db.flush()

                        variation_group_map[group_name] = var_group.variation_group_id
                        logger.debug(f"Created/found variation group: {group_name} with {len(variations_list)} variations")

                logger.info(f"Starting to process {len(request.menu_data.items)} menu items")
                for idx, item_data in enumerate(request.menu_data.items):
                    logger.debug(f"Processing item {idx + 1}/{len(request.menu_data.items)}: {item_data.itemname}")
                    menu_item = MenuItem(
                        menu_item_id=uuid.uuid4(),
                        restaurant_id=restaurant.restaurant_id,
                        menu_sub_category_id=category_map.get(item_data.item_categoryid),
                        menu_item_name=item_data.itemname,
                        menu_item_description=item_data.itemdescription,
                        menu_item_price=Decimal(item_data.price),
                        menu_item_markup_price=Decimal(item_data.markup_price) if item_data.markup_price and item_data.markup_price != "" else None,
                        menu_item_allow_variation=item_data.itemallowvariation == "1",
                        menu_item_allow_addon=item_data.itemallowaddon == "1",
                        menu_item_status="active" if item_data.active == "1" else "inactive",
                        menu_item_attribute_id=attribute_map.get(item_data.item_attributeid),
                        menu_item_spice_level=item_data.item_info.spice_level if item_data.item_info else None,
                        menu_item_minimum_preparation_time=int(item_data.minimumpreparationtime) if item_data.minimumpreparationtime and item_data.minimumpreparationtime != "" else None,
                        menu_item_packaging_charges=Decimal(item_data.item_packingcharges) if item_data.item_packingcharges else None,
                        menu_item_favorite=item_data.item_favorite == "1",
                        menu_item_ignore_taxes=item_data.ignore_taxes == "1",
                        menu_item_ignore_discounts=item_data.ignore_discounts == "1",
                        menu_item_in_stock=item_data.in_stock == "2",
                        menu_item_is_combo=item_data.is_combo == "1",
                        menu_item_is_recommended=item_data.is_recommend == "1",
                        menu_item_rank=int(item_data.itemrank) if item_data.itemrank else 0,
                        menu_item_addon_based_on=item_data.itemaddonbasedon,
                        ext_petpooja_item_id=int(item_data.itemid)
                    )
                    db.add(menu_item)
                    db.flush()

                    if item_data.item_tax:
                        tax_ids = item_data.item_tax.split(",")
                        for tax_id in tax_ids:
                            if tax_id.strip():
                                tax_mapping = MenuItemTaxMapping(
                                    menu_item_tax_mapping_id=uuid.uuid4(),
                                    menu_item_id=menu_item.menu_item_id,
                                    restaurant_id=restaurant.restaurant_id,
                                    is_tax_inclusive=item_data.tax_inclusive,
                                    gst_type=item_data.gst_type
                                )
                                db.add(tax_mapping)

                    for tag_name in item_data.item_tags:
                        if tag_name and tag_name != "":
                            tag = db.query(MenuItemTag).filter(
                                MenuItemTag.menu_item_tag_name == tag_name,
                                MenuItemTag.is_deleted.is_(False)
                            ).first()

                            if not tag:
                                tag = MenuItemTag(
                                menu_item_tag_id=uuid.uuid4(),
                                menu_item_tag_name=tag_name, menu_item_tag_status="active")
                                db.add(tag)
                                db.flush()

                            tag_mapping = MenuItemTagMapping(
                                menu_item_tag_mapping_id=uuid.uuid4(),
                                menu_item_id=menu_item.menu_item_id,
                                menu_item_tag_id=tag.menu_item_tag_id
                            )
                            db.add(tag_mapping)

                    for variation_data in item_data.variation:
                        # Get variation group ID if available
                        var_group_id = variation_group_map.get(variation_data.groupname) if variation_data.groupname else None

                        variation = MenuItemVariation(
                            menu_item_variation_id=uuid.uuid4(),
                            menu_item_id=menu_item.menu_item_id,
                            restaurant_id=restaurant.restaurant_id,
                            variation_group_id=var_group_id,
                            menu_item_variation_name=variation_data.name,
                            menu_item_variation_price=Decimal(variation_data.price) if variation_data.price else None,
                            menu_item_variation_markup_price=Decimal(variation_data.markup_price) if variation_data.markup_price and variation_data.markup_price != "" else None,
                            menu_item_variation_status="active" if variation_data.active == "1" else "inactive",
                            menu_item_variation_allow_addon=variation_data.variationallowaddon == 1,
                            menu_item_variation_packaging_charges=Decimal(variation_data.item_packingcharges) if variation_data.item_packingcharges and variation_data.item_packingcharges != "" else None,
                            menu_item_variation_rank=int(variation_data.variationrank) if variation_data.variationrank and variation_data.variationrank != "" else 0,
                            ext_petpooja_variation_id=int(variation_data.variationid) if variation_data.variationid and variation_data.variationid != "" else None
                        )
                        db.add(variation)
                        db.flush()

                        for addon_data in variation_data.addon:
                            if addon_data.addon_group_id in addon_group_map:
                                addon_mapping = MenuItemAddonMapping(
                                    menu_item_addon_mapping_id=uuid.uuid4(),
                                    menu_item_id=menu_item.menu_item_id,
                                    menu_item_variation_id=variation.menu_item_variation_id,
                                    menu_item_addon_group_id=addon_group_map.get(addon_data.addon_group_id),
                                    restaurant_id=restaurant.restaurant_id
                                )
                                db.add(addon_mapping)

                    for addon_data in item_data.addon:
                        if addon_data.addon_group in addon_group_map:
                            addon_mapping = MenuItemAddonMapping(
                                    menu_item_addon_mapping_id=uuid.uuid4(),
                                    menu_item_id=menu_item.menu_item_id,
                                menu_item_addon_group_id=addon_group_map.get(addon_data.addon_group),
                                restaurant_id=restaurant.restaurant_id
                            )
                            db.add(addon_mapping)

        db.commit()
        logger.info(f"Successfully committed all data to database")
        logger.info(f"Created chain_id: {chain.chain_id}, {len(branch_ids)} branches, {len(restaurant_ids)} restaurants")

        return {
            "success": True,
            "message": "Menu data stored successfully",
            "chain_id": str(chain.chain_id),
            "branch_ids": branch_ids,
            "api_key": api_keys[0] if api_keys else None,
            "iframe_data": iframe_html
        }

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error while storing menu data: {str(e)}", exc_info=True)
        raise Exception(f"Database error: {str(e)}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error storing menu data: {str(e)}", exc_info=True)
        raise Exception(f"Error storing menu data: {str(e)}")


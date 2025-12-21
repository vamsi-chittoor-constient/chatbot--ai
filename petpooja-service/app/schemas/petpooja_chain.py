"""
PetPooja Chain Schemas - Matches finalpayload.json structure
"""

from pydantic import BaseModel, field_validator, Field
from typing import Optional, List, Any, Union


# Chain Info Schemas
class ChainInfoPetpoojaSchema(BaseModel):
    chain_name: str
    website: Optional[str] = ""
    logo_url: Optional[str] = ""
    contact_type: Optional[str] = ""
    contact_number: Optional[str] = ""
    contact_email: Optional[str] = ""
    address: Optional[str] = ""
    city: Optional[str] = ""
    state: Optional[str] = ""
    country: Optional[str] = ""
    landmark: Optional[str] = ""
    pincode: Optional[str] = ""
    latitude: Optional[str] = ""
    longitude: Optional[str] = ""


# Integration Schemas
class DataSourceIntegrationPetpoojaSchema(BaseModel):
    system_provider: str
    app_key: str
    app_secret: str
    access_token: str
    restaurant_mapping_id: str
    petpooja_restaurantid: Optional[str] = ""
    business_type: str = "restaurant"
    sandbox_enabled: Optional[bool] = True
    restaurant_ids: List[str] = []

    @field_validator('petpooja_restaurantid', mode='before')
    @classmethod
    def handle_escaped_field(cls, v, info):
        """Handle escaped quotes in field name from JSON"""
        # Handle case where JSON has 'petpooja_\"restaurantid'
        return v if v else ""


# Branch Schemas
class BranchDetailsPetpoojaSchema(BaseModel):
    menusharingcode: Optional[str] = ""
    currency_html: Optional[str] = ""
    country: Optional[str] = ""
    country_id: Optional[str] = ""
    invoice_ooa: Optional[int] = 0
    images: List[Any] = []
    restaurantname: str
    address: str
    contact: Optional[str] = ""
    latitude: Optional[str] = ""
    longitude: Optional[str] = ""
    landmark: Optional[str] = ""
    city: Optional[str] = ""
    city_id: Optional[str] = ""
    state: Optional[str] = ""
    state_id: Optional[str] = ""
    minimumorderamount: Optional[str] = "0"
    minimumdeliverytime: Optional[str] = ""
    minimum_prep_time: Optional[str] = ""
    deliverycharge: Optional[str] = "0"
    deliveryhoursfrom1: Optional[str] = ""
    deliveryhoursto1: Optional[str] = ""
    deliveryhoursfrom2: Optional[str] = ""
    deliveryhoursto2: Optional[str] = ""
    calculatetaxonpacking: Optional[int] = 0
    calculatetaxondelivery: Optional[int] = 0
    dc_taxes_id: Optional[str] = ""
    pc_taxes_id: Optional[str] = ""
    c_s_c: Optional[str] = "0"
    packaging_applicable_on: Optional[str] = "NONE"
    packaging_charge: Optional[str] = ""
    packaging_charge_type: Optional[str] = ""


class BranchesPetpoojaSchema(BaseModel):
    restaurantid: Optional[str] = ""
    active: str = "1"
    details: BranchDetailsPetpoojaSchema
    sandbox_enabled: Optional[bool] = True
    # New optional fields from finalpayload3.json (may or may not be present)
    pincode: Optional[str] = None
    landmark: Optional[str] = None
    personalized_greeting: Optional[str] = None
    branch_open_time: Optional[str] = None
    branch_close_time: Optional[str] = None
    food_order_open_time: Optional[str] = None
    food_order_close_time: Optional[str] = None
    table_booking_open_time: Optional[str] = None
    table_booking_close_time: Optional[str] = None


# Menu Data Schemas
class OrderTypePetpoojaSchema(BaseModel):
    ordertypeid: int
    ordertype: str


class GroupCategoryPetpoojaSchema(BaseModel):
    id: str
    name: str
    status: str = "1"
    rank: str = "1"


class ParentCategoryPetpoojaSchema(BaseModel):
    name: str
    rank: str
    image_url: Optional[str] = None
    status: str = "1"
    id: str


class CategoryPetpoojaSchema(BaseModel):
    categoryid: str
    active: str = "1"
    categoryrank: str = "1"
    parent_category_id: str
    tags: Optional[Any] = None
    categoryname: str
    categorytimings: Optional[str] = ""
    category_image_url: Optional[str] = ""
    group_category_id: str


class ItemInfoPetpoojaSchema(BaseModel):
    spice_level: Optional[str] = "not-applicable"


class VariationAddonPetpoojaSchema(BaseModel):
    addon_group_id: str
    addon_item_selection_min: str
    addon_item_selection_max: str


class VariationPetpoojaSchema(BaseModel):
    id: Optional[str] = ""
    variationid: Optional[str] = ""
    name: str  # Variation name (e.g., "2 Pieces")
    groupname: str  # Variation group name (e.g., "Quantity")
    price: str
    markup_price: Optional[str] = ""
    active: str = "1"
    item_packingcharges: Optional[str] = ""
    variationrank: Optional[str] = ""
    variationallowaddon: Optional[int] = 0
    addon: List[VariationAddonPetpoojaSchema] = []

    # Legacy support (for backward compatibility)
    @property
    def group_name(self) -> str:
        """Backward compatibility property"""
        return self.name

    @property
    def packaging_charges(self) -> str:
        """Backward compatibility property"""
        return self.item_packingcharges or ""

    @property
    def variation_rank(self) -> str:
        """Backward compatibility property"""
        return self.variationrank or ""

    @property
    def allow_addon(self) -> bool:
        """Backward compatibility property"""
        return self.variationallowaddon == 1

    @property
    def addons(self) -> List[VariationAddonPetpoojaSchema]:
        """Backward compatibility property"""
        return self.addon


class ItemAddonPetpoojaSchema(BaseModel):
    allow_addon: bool = True
    minimum_selection_amount: str
    max_selection_amount: str
    addon_group: str


class MenuItemPetpoojaSchema(BaseModel):
    itemid: str
    itemallowvariation: str = "0"
    itemrank: str = "1"
    item_categoryid: str
    item_ordertype: str = "1,2,3"
    item_packingcharges: str = "0"
    itemallowaddon: str = "0"
    itemaddonbasedon: str = "0"
    item_favorite: str = "0"
    ignore_taxes: str = "0"
    ignore_discounts: str = "0"
    in_stock: str = "2"
    cuisine: List[Any] = []
    variation_groupname: str = ""
    is_combo: str = "0"
    variation: List[VariationPetpoojaSchema] = []
    addon: List[ItemAddonPetpoojaSchema] = []
    is_recommend: str = "0"
    itemname: str
    item_attributeid: str
    itemdescription: Optional[str] = ""
    minimumpreparationtime: Optional[str] = ""
    price: str
    active: str = "1"
    markup_price: Optional[str] = ""
    item_tags: List[str] = []
    item_info: ItemInfoPetpoojaSchema
    item_image_url: Optional[str] = ""
    item_tax: Optional[str] = ""
    tax_inclusive: bool = False
    gst_type: Optional[str] = "services"


class AddonGroupItemPetpoojaSchema(BaseModel):
    addonitemid: str
    addonitem_name: str
    addonitem_price: str
    active: str = "1"
    attributes: str
    addonitem_rank: str


class AddonGroupPetpoojaSchema(BaseModel):
    addongroupid: str
    addongroup_rank: str
    active: str = "1"
    addongroupitems: List[AddonGroupItemPetpoojaSchema]
    addongroup_name: str


class AttributePetpoojaSchema(BaseModel):
    attributeid: str
    attribute: str
    active: str = "1"


class TaxPetpoojaSchema(BaseModel):
    taxid: str
    taxname: str
    tax: str
    taxtype: str = "1"
    tax_ordertype: str = "1,2,3"
    active: str = "1"
    tax_coreortotal: str = "2"
    tax_taxtype: str = "1"
    rank: str = "1"
    consider_in_core_amount: str = "0"
    description: Optional[str] = ""


class DiscountPetpoojaSchema(BaseModel):
    discountid: str
    discountname: str
    description: Optional[str] = ""
    # Add more fields as needed


class StandaloneVariationPetpoojaSchema(BaseModel):
    """Standalone variation from menu_data.variations list"""
    variationid: str
    name: str
    groupname: str
    status: Optional[str] = "1"


class MenuDataPetpoojaSchema(BaseModel):
    # Metadata fields (not stored in database, just for API response compatibility)
    success: Optional[str] = None
    message: Optional[str] = None
    serverdatetime: Optional[str] = None
    db_version: Optional[str] = None
    application_version: Optional[str] = None
    # Data fields
    ordertypes: List[OrderTypePetpoojaSchema] = []
    group_categories: List[GroupCategoryPetpoojaSchema] = []
    parentcategories: List[ParentCategoryPetpoojaSchema] = []
    categories: List[CategoryPetpoojaSchema] = []
    items: List[MenuItemPetpoojaSchema] = []
    variations: List[StandaloneVariationPetpoojaSchema] = []  # New: standalone variations list
    addongroups: List[AddonGroupPetpoojaSchema] = []
    attributes: List[AttributePetpoojaSchema] = []
    taxes: List[TaxPetpoojaSchema] = []
    discounts: List[DiscountPetpoojaSchema] = []


# Main Request Schema
class StoreChainDetailsPetpoojaRequest(BaseModel):
    chain_info: ChainInfoPetpoojaSchema
    data_source_integration: DataSourceIntegrationPetpoojaSchema
    branches: Union[List[BranchesPetpoojaSchema], BranchesPetpoojaSchema]  # Accept both list and single object
    menu_data: Optional[MenuDataPetpoojaSchema] = None  # Use underscore, map from "menu-data"

    @field_validator('branches', mode='before')
    @classmethod
    def convert_branches_to_list(cls, v):
        """Convert single branch object to list format"""
        if isinstance(v, dict):
            # Single object, convert to list
            return [v]
        return v

    class Config:
        # Allow field names with hyphens in JSON
        populate_by_name = True

    @classmethod
    def model_validate(cls, obj):
        """Custom validator to handle menu-data field mapping"""
        if isinstance(obj, dict) and 'menu-data' in obj:
            obj['menu_data'] = obj.pop('menu-data')
        return super().model_validate(obj)


class StoreChainDetailsPetpoojaResponse(BaseModel):
    success: bool
    message: str
    chain_id: Optional[str] = None
    branch_ids: List[str] = []
    iframe_data: Optional[str] = None
    api_key: str = None

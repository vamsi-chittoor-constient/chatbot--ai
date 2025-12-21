from pydantic import BaseModel, Field
from typing import Any, Dict, Optional, List

class ChainResponse(BaseModel):
    chainIndex: int
    chainId: str
    chainName: str
    website: Optional[str]
    logoUrl: Optional[str]

    contactType: Optional[str]
    contactValue: Optional[str]
    contactLabel: Optional[str]

    city: Optional[str]
    state: Optional[str]
    country: Optional[str]
    address: Optional[str]
    landmark: Optional[str]
    pincode: Optional[str]
    latitude: Optional[str]
    longitude: Optional[str]

    class Config:
        orm_mode = True


# Store Chain Details Schemas
class ChainInfoSchema(BaseModel):
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


class DataSourceIntegrationSchema(BaseModel):
    system_provider: str
    app_key: str
    app_secret: str
    access_token: str
    restaurant_mapping_id: str
    sandbox_enabled: bool = True


class ParentCategorySchema(BaseModel):
    isActive: bool = True
    name: str
    description: Optional[str] = ""
    rank: int = 0


class GroupCategorySchema(BaseModel):
    isActive: bool = True
    name: str
    description: Optional[str] = ""
    rank: int = 0


class CategorySchema(BaseModel):
    isActive: bool = True
    name: str
    description: Optional[str] = ""
    rank: int = 0
    parentCategory: Optional[str] = ""
    groupCategory: Optional[str] = ""


class AddonGroupSchema(BaseModel):
    isActive: bool = True
    name: str
    rank: int = 0
    selectionMinimum: int = 0
    selectionMaximum: int = 0


class MenuConfigurationSchema(BaseModel):
    parentCategories: List[ParentCategorySchema] = []
    groupCategories: List[GroupCategorySchema] = []
    categories: List[CategorySchema] = []
    addonGroups: List[AddonGroupSchema] = []


class VariationAddonSchema(BaseModel):
    addon_group: str
    minimum_selection_amount: str
    max_selection_amount: str


class VariationSchema(BaseModel):
    group_name: str
    price: str
    markup_price: Optional[str] = ""
    active: bool = True
    packaging_charges: Optional[str] = ""
    variation_rank: Optional[str] = ""
    allow_addon: bool = False
    addons: List[VariationAddonSchema] = []


class MenuAddonSchema(BaseModel):
    allow_addon: bool = True
    minimum_selection_amount: str
    max_selection_amount: str
    addon_group: str


class MenuItemSchema(BaseModel):
    dish_name: str
    description: Optional[str] = ""
    price: float
    category: str
    attribute: Optional[str] = "veg"
    item_rank: Optional[str] = ""
    item_order_type: Optional[str] = ""
    markup_price: Optional[str] = ""
    variation_allowed: bool = False
    addon_allowed: bool = False
    image: Optional[str] = ""
    is_vegetarian: bool = True
    is_available: bool = True
    spice_level: Optional[str] = ""
    preparation_time: Optional[str] = ""
    item_favorite: bool = False
    ignore_taxes: bool = False
    ignore_discounts: bool = False
    in_stock: bool = True
    cuisine: Optional[str] = ""
    is_combo: bool = False
    item_ordertype: Optional[str] = ""
    tax_inclusive: bool = False
    gst_type: Optional[str] = ""
    item_tags: List[str] = []
    variations: List[VariationSchema] = []
    addons: List[MenuAddonSchema] = []


class BranchSchema(BaseModel):
    name: str
    address: str
    is_main_branch: bool = False
    phone: Optional[str] = ""
    email: Optional[str] = ""
    active: bool = True
    minimum_order_amount: Optional[str] = ""
    minimum_delivery_time: Optional[str] = ""
    delivery_charge: Optional[str] = ""
    minimum_prep_time: Optional[str] = ""
    restaurant_open: Optional[str] = ""
    restaurant_close: Optional[str] = ""
    food_ordering_open: Optional[str] = ""
    food_ordering_close: Optional[str] = ""
    table_booking_open: Optional[str] = ""
    table_booking_close: Optional[str] = ""
    delivery_from1: Optional[str] = ""
    delivery_to1: Optional[str] = ""
    delivery_from2: Optional[str] = ""
    delivery_to2: Optional[str] = ""
    calculate_tax_on_packing: bool = False
    calculate_tax_on_delivery: bool = False
    packaging_applicable_on: Optional[str] = "NONE"
    packaging_charge: Optional[str] = ""
    packaging_charge_type: Optional[str] = ""
    menus: List[MenuItemSchema] = []


class StoreChainDetailsRequest(BaseModel):
    chain_info: ChainInfoSchema
    data_source_integration: List[DataSourceIntegrationSchema] = []
    business_type: str = "restaurant"
    menuConfiguration: MenuConfigurationSchema
    branches: List[BranchSchema]


class StoreChainDetailsResponse(BaseModel):
    success: bool
    message: str
    chain_id: Optional[str] = None
    restaurant_ids: List[str] = []
    branch_ids: List[str] = []


class FetchMenuSyncWithCredentialsRequest(BaseModel):
    """Request schema for syncing menu with custom PetPooja credentials"""
    restaurant_id: str = Field(..., description="Petpooja restaurant ID")
    app_key: str = Field(..., alias="app-key", description="PetPooja app key")
    app_secret: str = Field(..., alias="app-secret", description="PetPooja app secret")
    access_token: str = Field(..., alias="access-token", description="PetPooja access token")
    sandbox_enabled: bool = Field(default=True, description="Use PetPooja sandbox environment")

    class Config:
        populate_by_name = True  # Allow both 'app_key' and 'app-key'
        json_schema_extra = {
            "example": {
                "restaurant_id": "your_restaurant_id",
                "app-key": "your_app_key",
                "app-secret": "your_app_secret",
                "access-token": "your_access_token",
                "sandbox_enabled": True
            }
        }


class FetchMenuSyncResponse(BaseModel):
    """Response schema for menu sync operation (data only)"""
    success: bool = Field(default=True)
    message: str = Field(default="Menu synced successfully")
    data: Dict[str, Any] = Field(..., description="Menu data from PetPooja")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Menu fetched successfully",
                "data": {
                    "items": [],
                    "categories": [],
                    "addongroups": [],
                    "taxes": [],
                    "variations": [],
                    "discounts": []
                }
            }
        }

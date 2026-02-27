"""
Order Transformer
Transforms database order data to PetPooja format
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any
from decimal import Decimal
from app.core.config import settings
from app.schemas.order import (
    SaveOrderRequest, OrderInfo, OrderInfoInner, Restaurant, RestaurantDetails,
    Customer, CustomerDetails, Order, OrderDetails, GSTDetail,
    OrderItem as PetpoojaOrderItem, OrderItemDetails as PetpoojaOrderItemDetails,
    AddonItem, ItemTax, Tax, TaxDetails, Discount, DiscountDetails
)

logger = logging.getLogger(__name__)


class TransformerError(Exception):
    """Custom exception for transformer errors"""
    pass


def transform_db_order_to_petpooja(order_data: Dict[str, Any]) -> SaveOrderRequest:
    """
    Transform order data fetched from database to PetPooja's expected format

    Args:
        order_data: Dict containing all order data from fetch_order_from_database()

    Returns:
        SaveOrderRequest in PetPooja format
    """
    try:
        external_order_id = order_data.get("external_order_id") or ""
        # Generate fallback orderID if missing
        if not external_order_id:
            order = order_data.get("order")
            if order and order.order_id:
                external_order_id = f"{settings.ORDER_ID_PREFIX}{str(order.order_id)[:8].upper()}"
            else:
                import uuid
                external_order_id = f"{settings.ORDER_ID_PREFIX}{str(uuid.uuid4())[:8].upper()}"
        logger.info(f"Transforming DB order {external_order_id} to PetPooja format")

        # Extract data from order_data dict
        order = order_data.get("order")
        order_total = order_data.get("order_total")
        order_items = order_data.get("order_items", [])
        menu_items_map = order_data.get("menu_items_map", {})
        variations_map = order_data.get("variations_map", {})
        customer_profile = order_data.get("customer_profile")
        customer_phone = order_data.get("customer_phone")
        customer_email = order_data.get("customer_email")
        customer_address = order_data.get("customer_address")
        order_charges = order_data.get("order_charges", [])
        order_taxes = order_data.get("order_taxes", [])
        order_discounts = order_data.get("order_discounts", [])
        delivery_info = order_data.get("delivery_info")
        dining_info = order_data.get("dining_info")
        scheduling_info = order_data.get("scheduling_info")
        instruction_info = order_data.get("instruction_info")
        order_type = order_data.get("order_type", "delivery")
        payment_method = order_data.get("payment_method", "COD")
        restaurant_info = order_data.get("restaurant_info", {})

        petpooja_mapping_code = restaurant_info.get("petpooja_mapping_code", "")
        petpooja_restaurantid = restaurant_info.get("petpooja_restaurantid", "")
        restaurant_name = restaurant_info.get("branch_name", "")

        # Use petpooja_mapping_code as restID (e.g., "czw6b9ykas")
        rest_id = petpooja_mapping_code
        logger.info(f"Using restID: {rest_id} (mapping_code: {petpooja_mapping_code}, petpooja_restaurantid: {petpooja_restaurantid})")

        # Map order type to PetPooja format
        order_type_map = {
            "delivery": "H",
            "H": "H",
            "pickup": "P",
            "P": "P",
            "dine_in": "D",
            "D": "D"
        }
        petpooja_order_type = order_type_map.get(order_type, "H")

        # Map payment type (PAID for prepaid orders, COD for cash on delivery)
        payment_type_map = {
            "COD": "COD",
            "cod": "COD",
            "PREPAID": "PAID",
            "prepaid": "PAID",
            "PAID": "PAID",
            "paid": "PAID",
            "CARD": "PAID",
            "card": "PAID",
            "online": "PAID",
            "ONLINE": "PAID"
        }
        petpooja_payment_type = payment_type_map.get(payment_method, "COD")

        # Extract customer info
        customer_name = ""

        if customer_profile:
            # Handle CustomerProfileTable structure
            if hasattr(customer_profile, 'customer_display_name') and customer_profile.customer_display_name:
                customer_name = customer_profile.customer_display_name
            elif hasattr(customer_profile, 'customer_first_name'):
                first_name = customer_profile.customer_first_name or ""
                last_name = customer_profile.customer_last_name or ""
                customer_name = f"{first_name} {last_name}".strip()

        # Use email from order_data (fetched from CustomerContactTable)
        customer_email_str = customer_email or ""

        # Extract address info
        customer_address_str = ""
        customer_latitude = ""
        customer_longitude = ""

        if customer_address:
            address_parts = [
                customer_address.customer_street_address_1,
                customer_address.customer_street_address_2,
                customer_address.customer_city,
                customer_address.customer_state_province,
                customer_address.customer_postal_code
            ]
            customer_address_str = ", ".join(filter(None, address_parts))
            customer_latitude = str(customer_address.customer_latitude) if customer_address.customer_latitude else ""
            customer_longitude = str(customer_address.customer_longitude) if customer_address.customer_longitude else ""

        # Transform Order Items
        petpooja_items = []
        for item in order_items:
            # Get PetPooja item ID from menu_items_map
            menu_item_key = str(item.menu_item_id) if item.menu_item_id else ""
            menu_item = menu_items_map.get(menu_item_key)
            petpooja_item_id = ""
            item_name = item.category_name or ""

            if menu_item:
                petpooja_item_id = str(menu_item.ext_petpooja_item_id) if menu_item.ext_petpooja_item_id else ""
                item_name = menu_item.menu_item_name or item_name

            # Get PetPooja variation ID from variations_map
            variation_key = str(item.menu_item_variation_id) if item.menu_item_variation_id else ""
            variation = variations_map.get(variation_key)
            petpooja_variation_id = ""
            variation_name = ""

            if variation:
                petpooja_variation_id = str(variation.ext_petpooja_variation_id) if variation.ext_petpooja_variation_id else ""
                variation_name = variation.menu_item_variation_name or ""

            # Transform item taxes (if any)
            item_taxes = []
            for tax in order_taxes:
                if tax.order_item_id == item.order_item_id:
                    item_taxes.append(ItemTax(
                        id=str(tax.order_tax_line_id),
                        name=tax.order_tax_line_tax_type or "",
                        tax_percentage=str(tax.order_tax_line_percentage or 0),
                        amount=str(tax.order_tax_line_amount or 0)
                    ))

            petpooja_items.append(PetpoojaOrderItemDetails(
                id=petpooja_item_id,
                name=item_name,
                price=str(item.base_price or 0),
                final_price=str(item.base_price or 0),
                quantity="1",  # Each OrderItem row represents one instance
                tax_inclusive=True,
                gst_liability="vendor",
                item_tax=item_taxes,
                item_discount="",
                variation_id=petpooja_variation_id,
                variation_name=variation_name,
                description=item.cooking_instructions or "",
                addon_item=AddonItem(details=[])
            ))

        # Transform Taxes
        tax_details = []
        for tax in order_taxes:
            tax_details.append(TaxDetails(
                id=str(tax.order_tax_line_id),
                title=tax.order_tax_line_tax_type or "",
                type="P",
                price=str(tax.order_tax_line_percentage or 0),
                tax=str(tax.order_tax_line_amount or 0),
                restaurant_liable_amt="0.00"
            ))

        # Transform Discounts
        discount_details = []
        for discount in order_discounts:
            discount_details.append(DiscountDetails(
                id=str(discount.order_discount_id),
                title=discount.order_discount_code or "Discount",
                type="F",
                price=str(discount.order_discount_amount or 0)
            ))

        # Extract charges
        delivery_charges = Decimal("0.00")
        packing_charges = Decimal("0.00")
        service_charge = Decimal("0.00")

        for charge in order_charges:
            charge_type = charge.order_charges_type or ""
            charge_amount = charge.order_charges_base_amount or Decimal("0.00")

            if charge_type.lower() == "delivery":
                delivery_charges = charge_amount
            elif charge_type.lower() in ["packing", "packaging"]:
                packing_charges = charge_amount
            elif charge_type.lower() == "service":
                service_charge = charge_amount

        # Extract totals
        tax_total = order_total.tax_total if order_total else Decimal("0.00")
        discount_total = order_total.discount_total if order_total else Decimal("0.00")
        final_amount = order_total.final_amount if order_total else Decimal("0.00")

        # Extract scheduling info
        # PetPooja requires preorder_date and preorder_time even for immediate orders
        now = datetime.utcnow()
        default_date = now.strftime("%Y-%m-%d")
        default_time = (now + timedelta(minutes=settings.DEFAULT_PREP_TIME_OFFSET_MINUTES)).strftime("%H:%M:%S")

        preorder_date = default_date
        preorder_time = default_time
        is_advanced_order = False
        is_urgent = False
        min_prep_time = settings.MIN_PREP_TIME_MINUTES

        if scheduling_info:
            preorder_date = str(scheduling_info.preorder_date) if scheduling_info.preorder_date else default_date
            preorder_time = str(scheduling_info.preorder_time) if scheduling_info.preorder_time else default_time
            is_advanced_order = scheduling_info.is_preorder or False
            is_urgent = False  # Default
            min_prep_time = settings.MIN_PREP_TIME_MINUTES  # From config

        # Extract instruction
        special_instructions = ""
        if instruction_info:
            special_instructions = instruction_info.special_instructions or ""

        # Extract delivery info
        enable_delivery = 1 if petpooja_order_type == "H" else 0
        delivery_otp = ""

        if delivery_info:
            enable_delivery = 1 if delivery_info.enable_delivery else 0
            delivery_otp = delivery_info.delivery_otp or ""

        # Extract dining info
        table_no = ""
        no_of_persons = "0"

        if dining_info:
            table_no = str(dining_info.table_no) if dining_info.table_no else ""
            no_of_persons = str(dining_info.no_of_persons) if dining_info.no_of_persons else "0"

        # Get restaurant address and contact from restaurant_info if available
        restaurant_address = restaurant_info.get("branch_address", "")
        restaurant_contact = restaurant_info.get("branch_contact", "")

        # Build GST details for delivery charges (if applicable)
        dc_gst_details = []
        if float(delivery_charges) > 0:
            dc_gst_details = [
                GSTDetail(gst_liable="vendor", amount="0"),
                GSTDetail(gst_liable="restaurant", amount="0")
            ]

        # Build GST details for packing charges (if applicable)
        pc_gst_details = []
        if float(packing_charges) > 0:
            pc_gst_details = [
                GSTDetail(gst_liable="vendor", amount="0"),
                GSTDetail(gst_liable="restaurant", amount="0")
            ]

        # Determine collect_cash based on payment type
        # For prepaid/PAID orders, collect_cash should be "0"
        # For COD orders, collect_cash should be the total amount
        collect_cash = "0" if petpooja_payment_type == "PAID" else str(final_amount)

        # Build PetPooja SaveOrderRequest
        order_info_inner = OrderInfoInner(
            restaurant=Restaurant(
                details=RestaurantDetails(
                    res_name=restaurant_name,
                    address=restaurant_address,
                    contact_information=restaurant_contact,
                    restID=rest_id
                )
            ),
            customer=Customer(
                details=CustomerDetails(
                    name=customer_name,
                    phone=customer_phone or "",
                    email=customer_email_str,
                    address=customer_address_str,
                    latitude=customer_latitude,
                    longitude=customer_longitude
                )
            ),
            order=Order(
                details=OrderDetails(
                    orderID=external_order_id,
                    preorder_date=preorder_date,
                    preorder_time=preorder_time,
                    advanced_order="Y" if is_advanced_order else "N",
                    order_type=petpooja_order_type,
                    ondc_bap="",
                    payment_type=petpooja_payment_type,
                    delivery_charges=str(delivery_charges),
                    dc_tax_percentage="0",
                    dc_tax_amount="0",
                    dc_gst_details=dc_gst_details,
                    packing_charges=str(packing_charges),
                    pc_tax_percentage="0",
                    pc_tax_amount="0",
                    pc_gst_details=pc_gst_details,
                    service_charge=str(service_charge),
                    sc_tax_amount="0",
                    discount_total=str(discount_total),
                    discount_type="F",
                    tax_total=str(tax_total),
                    total=str(final_amount),
                    description=special_instructions,
                    created_on=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                    enable_delivery=enable_delivery,
                    callback_url="",
                    urgent_order=is_urgent,
                    urgent_time=settings.URGENT_ORDER_TIME_MINUTES,
                    table_no=table_no,
                    no_of_persons=no_of_persons,
                    min_prep_time=min_prep_time,
                    collect_cash=collect_cash,
                    otp=delivery_otp
                )
            ),
            order_item=PetpoojaOrderItem(details=petpooja_items),
            tax=Tax(details=tax_details),
            discount=Discount(details=discount_details)
        )

        # Wrap in OrderInfo
        order_info = OrderInfo(
            order_info=order_info_inner
        )

        # Build final SaveOrderRequest with udid and device_type at root level
        petpooja_order = SaveOrderRequest(
            orderinfo=order_info,
            udid=settings.PETPOOJA_ORDER_UDID,
            device_type=settings.PETPOOJA_ORDER_DEVICE_TYPE
        )

        logger.info(f"DB order {external_order_id} transformed to PetPooja format successfully")
        return petpooja_order

    except Exception as e:
        logger.error(f"Error transforming DB order to PetPooja format: {str(e)}")
        raise TransformerError(f"Failed to transform DB order: {str(e)}")

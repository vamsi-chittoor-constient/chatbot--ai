"""Order Service - Handles order operations with PetPooja API"""

import uuid
from typing import Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.petpooja_client.order_client import get_order_client, PetpoojaAPIError
from app.models.order_models import (
    OrderTotal, OrderItem, OrderCustomerDetails, OrderDeliveryInfo,
    OrderDiningInfo, OrderScheduling, OrderInstruction, OrderTaxLine,
    OrderDiscount, OrderCharges, OrderIntegrationSync, OrderPayment,
    OrderTypeTable, OrderPaymentMethod
)
from app.models.customer_models import CustomerProfileTable, CustomerContactTable, CustomerAddressTable
from app.models.branch_models import BranchInfoTable
from app.models.other_models import Orders, RestaurantTable
from app.models.menu_models import MenuItem, MenuItemVariation
from app.models.integration_models import IntegrationConfigTable, IntegrationCredentialsTable


class OrderServiceError(Exception):
    """Custom exception for order service errors"""
    pass


def _get_petpooja_credentials(restaurant_id: uuid.UUID, db: Session) -> Dict[str, str]:
    """Get PetPooja credentials for a restaurant"""
    integration_config = db.query(IntegrationConfigTable).filter(
        IntegrationConfigTable.restaurant_id == restaurant_id,
        IntegrationConfigTable.is_enabled == True,
        IntegrationConfigTable.is_deleted == False
    ).first()

    credentials = {"app_key": "", "app_secret": "", "access_token": "", "petpooja_restaurantid": ""}

    if integration_config:
        creds = db.query(IntegrationCredentialsTable).filter(
            IntegrationCredentialsTable.integration_config_id == integration_config.integration_config_id,
            IntegrationCredentialsTable.is_deleted == False
        ).all()

        for cred in creds:
            if cred.credential_key in credentials:
                credentials[cred.credential_key] = cred.credential_value

    if not credentials["app_key"] or not credentials["app_secret"] or not credentials["access_token"]:
        raise OrderServiceError(f"PetPooja credentials not found for restaurant {restaurant_id}")

    return credentials


def _get_restaurant_info(restaurant_id: uuid.UUID, db: Session) -> Dict[str, Any]:
    """Get restaurant and branch info"""
    restaurant = db.query(RestaurantTable).filter(RestaurantTable.restaurant_id == restaurant_id).first()
    if not restaurant:
        raise OrderServiceError(f"Restaurant {restaurant_id} not found")

    branch_info = db.query(BranchInfoTable).filter(BranchInfoTable.branch_id == restaurant.branch_id).first()
    if not branch_info:
        raise OrderServiceError(f"Branch info not found for restaurant {restaurant_id}")

    if not branch_info.ext_petpooja_restaurant_id:
        raise OrderServiceError(f"PetPooja mapping code is empty for restaurant {restaurant_id}")

    return {
        "branch_name": branch_info.branch_name,
        "petpooja_mapping_code": branch_info.ext_petpooja_restaurant_id
    }


def fetch_order_from_database(order_id: uuid.UUID, restaurant_id: uuid.UUID, db: Session) -> Dict[str, Any]:
    """Fetch complete order data from database for pushing to POS"""
    try:
        order = db.query(Orders).filter(Orders.order_id == order_id, Orders.is_deleted == False).first()
        if not order:
            raise OrderServiceError(f"Order {order_id} not found")

        order_total = db.query(OrderTotal).filter(OrderTotal.order_id == order_id, OrderTotal.is_deleted == False).first()

        order_items = db.query(OrderItem).filter(OrderItem.order_id == order_id, OrderItem.is_deleted == False).all()
        if not order_items:
            raise OrderServiceError(f"No items found for order {order_id}")

        # Fetch menu items and variations
        menu_item_ids = [item.menu_item_id for item in order_items if item.menu_item_id]
        menu_items_map = {}
        if menu_item_ids:
            menu_items = db.query(MenuItem).filter(MenuItem.menu_item_id.in_(menu_item_ids)).all()
            menu_items_map = {str(mi.menu_item_id): mi for mi in menu_items}

        variation_ids = [item.menu_item_variation_id for item in order_items if item.menu_item_variation_id]
        variations_map = {}
        if variation_ids:
            variations = db.query(MenuItemVariation).filter(MenuItemVariation.menu_item_variation_id.in_(variation_ids)).all()
            variations_map = {str(v.menu_item_variation_id): v for v in variations}

        # Fetch customer info
        order_customer = db.query(OrderCustomerDetails).filter(
            OrderCustomerDetails.order_id == order_id, OrderCustomerDetails.is_deleted == False
        ).first()

        customer_profile, customer_address, customer_phone, customer_email = None, None, None, None

        if order_customer and order_customer.customer_id:
            customer_profile = db.query(CustomerProfileTable).filter(
                CustomerProfileTable.customer_id == order_customer.customer_id,
                CustomerProfileTable.is_deleted == False
            ).first()

            phone_contact = db.query(CustomerContactTable).filter(
                CustomerContactTable.customer_id == order_customer.customer_id,
                CustomerContactTable.customer_contact_type == "phone",
                CustomerContactTable.is_deleted == False
            ).first()
            if phone_contact:
                customer_phone = phone_contact.customer_contact_value

            email_contact = db.query(CustomerContactTable).filter(
                CustomerContactTable.customer_id == order_customer.customer_id,
                CustomerContactTable.customer_contact_type == "email",
                CustomerContactTable.is_deleted == False
            ).first()
            if email_contact:
                customer_email = email_contact.customer_contact_value

            customer_address = db.query(CustomerAddressTable).filter(
                CustomerAddressTable.customer_id == order_customer.customer_id,
                CustomerAddressTable.is_deleted == False
            ).first()

        # Fetch related data
        order_charges = db.query(OrderCharges).filter(OrderCharges.order_id == order_id, OrderCharges.is_deleted == False).all()
        order_taxes = db.query(OrderTaxLine).filter(
            OrderTaxLine.order_item_id.in_([item.order_item_id for item in order_items]),
            OrderTaxLine.is_deleted == False
        ).all()
        order_discounts = db.query(OrderDiscount).filter(OrderDiscount.order_id == order_id, OrderDiscount.is_deleted == False).all()
        delivery_info = db.query(OrderDeliveryInfo).filter(OrderDeliveryInfo.order_id == order_id, OrderDeliveryInfo.is_deleted == False).first()
        dining_info = db.query(OrderDiningInfo).filter(OrderDiningInfo.order_id == order_id, OrderDiningInfo.is_deleted == False).first()
        scheduling_info = db.query(OrderScheduling).filter(OrderScheduling.order_id == order_id, OrderScheduling.is_deleted == False).first()
        instruction_info = db.query(OrderInstruction).filter(OrderInstruction.order_id == order_id, OrderInstruction.is_deleted == False).first()
        payment_info = db.query(OrderPayment).filter(OrderPayment.order_id == order_id, OrderPayment.is_deleted == False).first()

        # Get order type
        order_type = None
        if order.order_type_id:
            order_type_record = db.query(OrderTypeTable).filter(
                OrderTypeTable.order_type_id == order.order_type_id, OrderTypeTable.is_deleted == False
            ).first()
            if order_type_record:
                order_type = order_type_record.order_type_code

        # Get payment method
        payment_method = "COD"
        if payment_info and payment_info.order_payment_method_id:
            payment_method_record = db.query(OrderPaymentMethod).filter(
                OrderPaymentMethod.order_payment_method_id == payment_info.order_payment_method_id,
                OrderPaymentMethod.is_deleted == False
            ).first()
            if payment_method_record:
                payment_method = payment_method_record.order_payment_method_code

        # Get restaurant info and credentials
        restaurant_info = _get_restaurant_info(restaurant_id, db)
        petpooja_credentials = _get_petpooja_credentials(restaurant_id, db)

        return {
            "order": order,
            "order_total": order_total,
            "order_items": order_items,
            "menu_items_map": menu_items_map,
            "variations_map": variations_map,
            "customer_profile": customer_profile,
            "customer_phone": customer_phone,
            "customer_email": customer_email,
            "customer_address": customer_address,
            "order_charges": order_charges,
            "order_taxes": order_taxes,
            "order_discounts": order_discounts,
            "delivery_info": delivery_info,
            "dining_info": dining_info,
            "scheduling_info": scheduling_info,
            "instruction_info": instruction_info,
            "payment_info": payment_info,
            "order_type": order_type,
            "payment_method": payment_method,
            "restaurant_info": {
                "restaurant_id": restaurant_id,
                "branch_name": restaurant_info["branch_name"],
                "petpooja_mapping_code": restaurant_info["petpooja_mapping_code"],
                "petpooja_restaurantid": petpooja_credentials.get("petpooja_restaurantid", "")
            },
            "external_order_id": order.order_external_reference_id,
            "petpooja_credentials": petpooja_credentials
        }

    except OrderServiceError:
        raise
    except Exception as e:
        raise OrderServiceError(f"Failed to fetch order: {str(e)}")


async def push_order_to_petpooja(order_data: Dict[str, Any], credentials: Dict[str, str]) -> Dict[str, Any]:
    """Push order to PetPooja POS"""
    try:
        if hasattr(order_data, 'model_dump'):
            order_data = order_data.model_dump(by_alias=True, exclude_none=True)

        order_client = get_order_client()
        response = order_client.save_order(order_data, credentials)

        if not response.get("success"):
            raise OrderServiceError(response.get("message", "Failed to save order"))

        return {"success": True, "message": "Order pushed successfully", "data": response}

    except PetpoojaAPIError as e:
        raise OrderServiceError(f"Failed to push order to PetPooja: {str(e)}")


def update_integration_sync_status(order_id: uuid.UUID, status: str, db: Session, error_message: str = None) -> None:
    """Update order integration sync status"""
    try:
        sync_record = db.query(OrderIntegrationSync).filter(
            OrderIntegrationSync.order_id == order_id, OrderIntegrationSync.is_deleted == False
        ).first()

        if sync_record:
            sync_record.sync_status = status
            sync_record.last_synced_at = datetime.utcnow()
            if error_message:
                sync_record.sync_errors = error_message
            db.commit()
        else:
            db.add(OrderIntegrationSync(
                order_integration_sync_id=uuid.uuid4(),
                order_id=order_id,
                sync_status=status,
                sync_errors=error_message,
                last_synced_at=datetime.utcnow(),
                created_at=datetime.utcnow()
            ))
            db.commit()

    except Exception:
        db.rollback()


def fetch_order_info_for_status_update(order_id: uuid.UUID, restaurant_id: uuid.UUID, db: Session) -> Dict[str, Any]:
    """Fetch minimal order info needed for status update"""
    try:
        order = db.query(Orders).filter(Orders.order_id == order_id, Orders.is_deleted == False).first()
        if not order:
            raise OrderServiceError(f"Order {order_id} not found")

        if not order.order_external_reference_id:
            raise OrderServiceError(f"External order ID not found for order {order_id}")

        restaurant_info = _get_restaurant_info(restaurant_id, db)
        credentials = _get_petpooja_credentials(restaurant_id, db)

        return {
            "external_order_id": order.order_external_reference_id,
            "rest_id": restaurant_info["petpooja_mapping_code"],
            "credentials": credentials
        }

    except OrderServiceError:
        raise
    except Exception as e:
        raise OrderServiceError(f"Failed to fetch order info: {str(e)}")


async def update_order_status_at_petpooja(
    rest_id: str, client_order_id: str, status: str, cancel_reason: str, credentials: Dict[str, str]
) -> Dict[str, Any]:
    """Update order status at PetPooja POS"""
    try:
        order_client = get_order_client()
        response = order_client.update_order_status(
            rest_id=rest_id,
            client_order_id=client_order_id,
            status=status,
            cancel_reason=cancel_reason,
            credentials=credentials
        )

        if not response.get("success"):
            raise OrderServiceError(response.get("message", "Failed to update order status"))

        return {"success": True, "message": "Order status updated successfully", "data": response}

    except PetpoojaAPIError as e:
        raise OrderServiceError(f"Failed to update order status: {str(e)}")

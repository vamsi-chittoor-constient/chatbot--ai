"""Order Service - ASYNC VERSION - Handles order operations with PetPooja API"""

import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.petpooja_client.order_client_async import get_async_order_client, PetpoojaAPIError
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


async def _get_petpooja_credentials(restaurant_id: uuid.UUID, db: AsyncSession) -> Dict[str, str]:
    """Get PetPooja credentials for a restaurant - ASYNC"""
    result = await db.execute(
        select(IntegrationConfigTable)
        .where(
            IntegrationConfigTable.restaurant_id == restaurant_id,
            IntegrationConfigTable.is_enabled == True,
            IntegrationConfigTable.is_deleted == False
        )
    )
    integration_config = result.scalar_one_or_none()

    credentials = {"app_key": "", "app_secret": "", "access_token": "", "petpooja_restaurantid": ""}

    if integration_config:
        creds_result = await db.execute(
            select(IntegrationCredentialsTable)
            .where(
                IntegrationCredentialsTable.integration_config_id == integration_config.integration_config_id,
                IntegrationCredentialsTable.is_deleted == False
            )
        )
        creds = creds_result.scalars().all()

        for cred in creds:
            if cred.credential_key in credentials:
                credentials[cred.credential_key] = cred.credential_value

    if not credentials["app_key"] or not credentials["app_secret"] or not credentials["access_token"]:
        raise OrderServiceError(f"PetPooja credentials not found for restaurant {restaurant_id}")

    return credentials


async def _get_restaurant_info(restaurant_id: uuid.UUID, db: AsyncSession) -> Dict[str, Any]:
    """Get restaurant and branch info - ASYNC"""
    result = await db.execute(
        select(RestaurantTable).where(RestaurantTable.restaurant_id == restaurant_id)
    )
    restaurant = result.scalar_one_or_none()

    if not restaurant:
        raise OrderServiceError(f"Restaurant {restaurant_id} not found")

    branch_result = await db.execute(
        select(BranchInfoTable).where(BranchInfoTable.branch_id == restaurant.branch_id)
    )
    branch_info = branch_result.scalar_one_or_none()

    if not branch_info:
        raise OrderServiceError(f"Branch info not found for restaurant {restaurant_id}")

    if not branch_info.ext_petpooja_restaurant_id:
        raise OrderServiceError(f"PetPooja mapping code is empty for restaurant {restaurant_id}")

    return {
        "branch_name": branch_info.branch_name,
        "petpooja_mapping_code": branch_info.ext_petpooja_restaurant_id
    }


async def fetch_order_from_database(
    order_id: uuid.UUID,
    restaurant_id: uuid.UUID,
    db: AsyncSession
) -> Dict[str, Any]:
    """Fetch complete order data from database for pushing to POS - ASYNC"""
    try:
        # Fetch order with eager loading to reduce queries
        order_result = await db.execute(
            select(Orders)
            .where(Orders.order_id == order_id, Orders.is_deleted == False)
        )
        order = order_result.scalar_one_or_none()

        if not order:
            raise OrderServiceError(f"Order {order_id} not found")

        # Fetch order total
        total_result = await db.execute(
            select(OrderTotal).where(OrderTotal.order_id == order_id, OrderTotal.is_deleted == False)
        )
        order_total = total_result.scalar_one_or_none()

        # Fetch order items
        items_result = await db.execute(
            select(OrderItem).where(OrderItem.order_id == order_id, OrderItem.is_deleted == False)
        )
        order_items = items_result.scalars().all()

        if not order_items:
            raise OrderServiceError(f"No items found for order {order_id}")

        # Fetch menu items in bulk
        menu_item_ids = [item.menu_item_id for item in order_items if item.menu_item_id]
        menu_items_map = {}
        if menu_item_ids:
            menu_result = await db.execute(
                select(MenuItem).where(MenuItem.menu_item_id.in_(menu_item_ids))
            )
            menu_items = menu_result.scalars().all()
            menu_items_map = {str(mi.menu_item_id): mi for mi in menu_items}

        # Fetch variations in bulk
        variation_ids = [item.menu_item_variation_id for item in order_items if item.menu_item_variation_id]
        variations_map = {}
        if variation_ids:
            var_result = await db.execute(
                select(MenuItemVariation).where(MenuItemVariation.menu_item_variation_id.in_(variation_ids))
            )
            variations = var_result.scalars().all()
            variations_map = {str(v.menu_item_variation_id): v for v in variations}

        # Fetch customer info
        customer_result = await db.execute(
            select(OrderCustomerDetails).where(
                OrderCustomerDetails.order_id == order_id,
                OrderCustomerDetails.is_deleted == False
            )
        )
        order_customer = customer_result.scalar_one_or_none()

        customer_profile, customer_address, customer_phone, customer_email = None, None, None, None

        if order_customer and order_customer.customer_id:
            # Fetch customer profile
            profile_result = await db.execute(
                select(CustomerProfileTable).where(
                    CustomerProfileTable.customer_id == order_customer.customer_id,
                    CustomerProfileTable.is_deleted == False
                )
            )
            customer_profile = profile_result.scalar_one_or_none()

            # Fetch phone contact
            phone_result = await db.execute(
                select(CustomerContactTable).where(
                    CustomerContactTable.customer_id == order_customer.customer_id,
                    CustomerContactTable.customer_contact_type == "phone",
                    CustomerContactTable.is_deleted == False
                )
            )
            phone_contact = phone_result.scalar_one_or_none()
            if phone_contact:
                customer_phone = phone_contact.customer_contact_value

            # Fetch email contact
            email_result = await db.execute(
                select(CustomerContactTable).where(
                    CustomerContactTable.customer_id == order_customer.customer_id,
                    CustomerContactTable.customer_contact_type == "email",
                    CustomerContactTable.is_deleted == False
                )
            )
            email_contact = email_result.scalar_one_or_none()
            if email_contact:
                customer_email = email_contact.customer_contact_value

            # Fetch address
            address_result = await db.execute(
                select(CustomerAddressTable).where(
                    CustomerAddressTable.customer_id == order_customer.customer_id,
                    CustomerAddressTable.is_deleted == False
                )
            )
            customer_address = address_result.scalar_one_or_none()

        # Fetch related data in parallel using bulk queries
        charges_result = await db.execute(
            select(OrderCharges).where(OrderCharges.order_id == order_id, OrderCharges.is_deleted == False)
        )
        order_charges = charges_result.scalars().all()

        item_ids = [item.order_item_id for item in order_items]
        taxes_result = await db.execute(
            select(OrderTaxLine).where(
                OrderTaxLine.order_item_id.in_(item_ids),
                OrderTaxLine.is_deleted == False
            )
        )
        order_taxes = taxes_result.scalars().all()

        discounts_result = await db.execute(
            select(OrderDiscount).where(OrderDiscount.order_id == order_id, OrderDiscount.is_deleted == False)
        )
        order_discounts = discounts_result.scalars().all()

        delivery_result = await db.execute(
            select(OrderDeliveryInfo).where(OrderDeliveryInfo.order_id == order_id, OrderDeliveryInfo.is_deleted == False)
        )
        delivery_info = delivery_result.scalar_one_or_none()

        dining_result = await db.execute(
            select(OrderDiningInfo).where(OrderDiningInfo.order_id == order_id, OrderDiningInfo.is_deleted == False)
        )
        dining_info = dining_result.scalar_one_or_none()

        scheduling_result = await db.execute(
            select(OrderScheduling).where(OrderScheduling.order_id == order_id, OrderScheduling.is_deleted == False)
        )
        scheduling_info = scheduling_result.scalar_one_or_none()

        instruction_result = await db.execute(
            select(OrderInstruction).where(OrderInstruction.order_id == order_id, OrderInstruction.is_deleted == False)
        )
        instruction_info = instruction_result.scalar_one_or_none()

        payment_result = await db.execute(
            select(OrderPayment).where(OrderPayment.order_id == order_id, OrderPayment.is_deleted == False)
        )
        payment_info = payment_result.scalar_one_or_none()

        # Get order type
        order_type = None
        if order.order_type_id:
            type_result = await db.execute(
                select(OrderTypeTable).where(
                    OrderTypeTable.order_type_id == order.order_type_id,
                    OrderTypeTable.is_deleted == False
                )
            )
            order_type_record = type_result.scalar_one_or_none()
            if order_type_record:
                order_type = order_type_record.order_type_code

        # Get payment method
        payment_method = "COD"
        if payment_info and payment_info.order_payment_method_id:
            method_result = await db.execute(
                select(OrderPaymentMethod).where(
                    OrderPaymentMethod.order_payment_method_id == payment_info.order_payment_method_id,
                    OrderPaymentMethod.is_deleted == False
                )
            )
            payment_method_record = method_result.scalar_one_or_none()
            if payment_method_record:
                payment_method = payment_method_record.order_payment_method_code

        # Get restaurant info and credentials
        restaurant_info = await _get_restaurant_info(restaurant_id, db)
        petpooja_credentials = await _get_petpooja_credentials(restaurant_id, db)

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
    """Push order to PetPooja POS - ASYNC"""
    try:
        if hasattr(order_data, 'model_dump'):
            order_data = order_data.model_dump(by_alias=True, exclude_none=True)

        order_client = get_async_order_client()
        response = await order_client.save_order(order_data, credentials)

        if not response.get("success"):
            raise OrderServiceError(response.get("message", "Failed to save order"))

        return {"success": True, "message": "Order pushed successfully", "data": response}

    except PetpoojaAPIError as e:
        raise OrderServiceError(f"Failed to push order to PetPooja: {str(e)}")


async def update_integration_sync_status(
    order_id: uuid.UUID,
    status: str,
    db: AsyncSession,
    error_message: Optional[str] = None
) -> None:
    """Update order integration sync status - ASYNC"""
    try:
        result = await db.execute(
            select(OrderIntegrationSync).where(
                OrderIntegrationSync.order_id == order_id,
                OrderIntegrationSync.is_deleted == False
            )
        )
        sync_record = result.scalar_one_or_none()

        if sync_record:
            sync_record.sync_status = status
            sync_record.last_synced_at = datetime.utcnow()
            if error_message:
                sync_record.sync_errors = error_message
        else:
            new_sync = OrderIntegrationSync(
                order_integration_sync_id=uuid.uuid4(),
                order_id=order_id,
                sync_status=status,
                sync_errors=error_message,
                last_synced_at=datetime.utcnow(),
                created_at=datetime.utcnow()
            )
            db.add(new_sync)

        await db.commit()

    except Exception:
        await db.rollback()


async def fetch_order_info_for_status_update(
    order_id: uuid.UUID,
    restaurant_id: uuid.UUID,
    db: AsyncSession
) -> Dict[str, Any]:
    """Fetch minimal order info needed for status update - ASYNC"""
    try:
        result = await db.execute(
            select(Orders).where(Orders.order_id == order_id, Orders.is_deleted == False)
        )
        order = result.scalar_one_or_none()

        if not order:
            raise OrderServiceError(f"Order {order_id} not found")

        if not order.order_external_reference_id:
            raise OrderServiceError(f"External order ID not found for order {order_id}")

        restaurant_info = await _get_restaurant_info(restaurant_id, db)
        credentials = await _get_petpooja_credentials(restaurant_id, db)

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
    rest_id: str,
    client_order_id: str,
    status: str,
    cancel_reason: str,
    credentials: Dict[str, str]
) -> Dict[str, Any]:
    """Update order status at PetPooja POS - ASYNC"""
    try:
        order_client = get_async_order_client()
        response = await order_client.update_order_status(
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

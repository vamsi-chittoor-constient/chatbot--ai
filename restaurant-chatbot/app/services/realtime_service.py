"""
Real-time messaging service using Redis pub/sub for restaurant AI assistant.

Features:
- Order status updates (pending  preparing  ready  delivered)
- Table availability changes
- Agent-to-agent communication
- WebSocket integration ready
- Multi-tenant message isolation
"""

import asyncio
import json
from typing import Dict, Any, List, Callable, Optional
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from enum import Enum
import logging

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    from app.services.redis_service import get_redis_service, RedisService
except ImportError:
    # Fallback for direct execution
    from redis_service import get_redis_service, RedisService

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Real-time message types"""
    ORDER_UPDATE = "order_update"
    TABLE_UPDATE = "table_update"
    AGENT_MESSAGE = "agent_message"
    USER_NOTIFICATION = "user_notification"
    SYSTEM_ALERT = "system_alert"
    BOOKING_UPDATE = "booking_update"
    PAYMENT_UPDATE = "payment_update"


@dataclass
class RealtimeMessage:
    """Structure for real-time messages"""
    message_id: str
    message_type: MessageType
    tenant_id: str
    data: Dict[str, Any]
    timestamp: datetime
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "message_id": self.message_id,
            "message_type": self.message_type.value,
            "tenant_id": self.tenant_id,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "session_id": self.session_id,
            "metadata": self.metadata or {}
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RealtimeMessage':
        """Create from dictionary"""
        return cls(
            message_id=data["message_id"],
            message_type=MessageType(data["message_type"]),
            tenant_id=data["tenant_id"],
            data=data["data"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            user_id=data.get("user_id"),
            session_id=data.get("session_id"),
            metadata=data.get("metadata", {})
        )


class RealtimeService:
    """
    Redis-based real-time messaging service

    Handles:
    - Order status updates
    - Table availability changes
    - Inter-agent communication
    - User notifications
    - WebSocket message routing
    """

    def __init__(self, redis_service: Optional[RedisService] = None):
        self.redis = redis_service or get_redis_service()

        # Channel patterns
        self.channels = {
            "order_updates": "order_updates:{tenant_id}",
            "table_updates": "table_updates:{tenant_id}",
            "user_notifications": "user_notifications:{tenant_id}:{user_id}",
            "agent_messages": "agent_messages:{tenant_id}",
            "system_alerts": "system_alerts:{tenant_id}",
            "booking_updates": "booking_updates:{tenant_id}",
            "payment_updates": "payment_updates:{tenant_id}",
            "global_broadcast": "global_broadcast:{tenant_id}"
        }

        # Active subscribers
        self.subscribers: Dict[str, List[Callable]] = {}
        self.running_tasks = set()

    def _get_channel(self, channel_type: str, tenant_id: str, user_id: Optional[str] = None) -> str:
        """Generate channel name"""
        if channel_type not in self.channels:
            raise ValueError(f"Unknown channel type: {channel_type}")

        channel_pattern = self.channels[channel_type]

        if "{user_id}" in channel_pattern and user_id:
            return channel_pattern.format(tenant_id=tenant_id, user_id=user_id)
        else:
            return channel_pattern.format(tenant_id=tenant_id)

    # ==================== PUBLISHING METHODS ====================

    def publish_order_update(self, tenant_id: str, order_id: str, status: str,
                           estimated_ready_time: Optional[str] = None, user_id: Optional[str] = None,
                           metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Publish order status update

        Args:
            tenant_id: Restaurant identifier
            order_id: Order identifier
            status: New order status
            estimated_ready_time: Expected ready time
            user_id: Customer user ID
            metadata: Additional data

        Returns:
            bool: Success status
        """
        import uuid

        message = RealtimeMessage(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.ORDER_UPDATE,
            tenant_id=tenant_id,
            user_id=user_id,
            data={
                "order_id": order_id,
                "status": status,
                "estimated_ready_time": estimated_ready_time,
                "previous_status": metadata.get("previous_status") if metadata else None
            },
            timestamp=datetime.now(timezone.utc),
            metadata=metadata
        )

        channel = self._get_channel("order_updates", tenant_id)
        subscribers = self.redis.publish(channel, json.dumps(message.to_dict()))

        # Also send to specific user if provided
        if user_id:
            user_channel = self._get_channel("user_notifications", tenant_id, user_id)
            self.redis.publish(user_channel, json.dumps(message.to_dict()))

        logger.info(f"Published order update to {subscribers} subscribers: {order_id}  {status}")
        return subscribers > 0

    def publish_table_update(self, tenant_id: str, table_id: str, is_available: bool,
                           party_size: Optional[int] = None, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Publish table availability update

        Args:
            tenant_id: Restaurant identifier
            table_id: Table identifier
            is_available: Availability status
            party_size: Table capacity
            metadata: Additional data

        Returns:
            bool: Success status
        """
        import uuid

        message = RealtimeMessage(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.TABLE_UPDATE,
            tenant_id=tenant_id,
            data={
                "table_id": table_id,
                "available": is_available,
                "party_size": party_size,
                "updated_by": metadata.get("updated_by") if metadata else "system"
            },
            timestamp=datetime.now(timezone.utc),
            metadata=metadata
        )

        channel = self._get_channel("table_updates", tenant_id)
        subscribers = self.redis.publish(channel, json.dumps(message.to_dict()))

        logger.info(f"Published table update to {subscribers} subscribers: Table {table_id}  {'available' if is_available else 'unavailable'}")
        return subscribers > 0

    def publish_booking_update(self, tenant_id: str, booking_id: str, status: str,
                             user_id: Optional[str] = None, table_id: Optional[str] = None,
                             metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Publish booking status update

        Args:
            tenant_id: Restaurant identifier
            booking_id: Booking identifier
            status: New booking status
            user_id: Customer user ID
            table_id: Assigned table ID
            metadata: Additional data

        Returns:
            bool: Success status
        """
        import uuid

        message = RealtimeMessage(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.BOOKING_UPDATE,
            tenant_id=tenant_id,
            user_id=user_id,
            data={
                "booking_id": booking_id,
                "status": status,
                "table_id": table_id,
                "updated_at": datetime.now(timezone.utc).isoformat()
            },
            timestamp=datetime.now(timezone.utc),
            metadata=metadata
        )

        channel = self._get_channel("booking_updates", tenant_id)
        subscribers = self.redis.publish(channel, json.dumps(message.to_dict()))

        # Also send to specific user
        if user_id:
            user_channel = self._get_channel("user_notifications", tenant_id, user_id)
            self.redis.publish(user_channel, json.dumps(message.to_dict()))

        logger.info(f"Published booking update to {subscribers} subscribers: {booking_id}  {status}")
        return subscribers > 0

    def publish_agent_message(self, tenant_id: str, from_agent: str, to_agent: str,
                            message_data: Dict[str, Any], session_id: Optional[str] = None) -> bool:
        """
        Publish inter-agent communication message

        Args:
            tenant_id: Restaurant identifier
            from_agent: Sending agent name
            to_agent: Receiving agent name
            message_data: Message content
            session_id: Session context

        Returns:
            bool: Success status
        """
        import uuid

        message = RealtimeMessage(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.AGENT_MESSAGE,
            tenant_id=tenant_id,
            session_id=session_id,
            data={
                "from_agent": from_agent,
                "to_agent": to_agent,
                "message": message_data,
                "requires_response": message_data.get("requires_response", False)
            },
            timestamp=datetime.now(timezone.utc)
        )

        channel = self._get_channel("agent_messages", tenant_id)
        subscribers = self.redis.publish(channel, json.dumps(message.to_dict()))

        logger.info(f"Published agent message to {subscribers} subscribers: {from_agent}  {to_agent}")
        return subscribers > 0

    def publish_user_notification(self, tenant_id: str, user_id: str, notification_type: str,
                                title: str, message: str, action_url: Optional[str] = None,
                                metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Publish user-specific notification

        Args:
            tenant_id: Restaurant identifier
            user_id: Target user ID
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            action_url: Optional action URL
            metadata: Additional data

        Returns:
            bool: Success status
        """
        import uuid

        rt_message = RealtimeMessage(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.USER_NOTIFICATION,
            tenant_id=tenant_id,
            user_id=user_id,
            data={
                "notification_type": notification_type,
                "title": title,
                "message": message,
                "action_url": action_url,
                "read": False
            },
            timestamp=datetime.now(timezone.utc),
            metadata=metadata
        )

        channel = self._get_channel("user_notifications", tenant_id, user_id)
        subscribers = self.redis.publish(channel, json.dumps(rt_message.to_dict()))

        logger.info(f"Published user notification to {subscribers} subscribers: {user_id}")
        return subscribers > 0

    def publish_system_alert(self, tenant_id: str, alert_type: str, severity: str,
                           message: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Publish system alert

        Args:
            tenant_id: Restaurant identifier
            alert_type: Type of alert
            severity: Alert severity (info, warning, error, critical)
            message: Alert message
            metadata: Additional data

        Returns:
            bool: Success status
        """
        import uuid

        rt_message = RealtimeMessage(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.SYSTEM_ALERT,
            tenant_id=tenant_id,
            data={
                "alert_type": alert_type,
                "severity": severity,
                "message": message,
                "requires_action": metadata.get("requires_action", False) if metadata else False
            },
            timestamp=datetime.now(timezone.utc),
            metadata=metadata
        )

        channel = self._get_channel("system_alerts", tenant_id)
        subscribers = self.redis.publish(channel, json.dumps(rt_message.to_dict()))

        logger.info(f"Published system alert to {subscribers} subscribers: {alert_type} ({severity})")
        return subscribers > 0

    # ==================== SUBSCRIPTION METHODS ====================

    async def subscribe_to_orders(self, tenant_id: str, callback: Callable[[RealtimeMessage], None]) -> bool:
        """Subscribe to order updates"""
        channel = self._get_channel("order_updates", tenant_id)
        return await self._subscribe_to_channel(channel, callback)

    async def subscribe_to_tables(self, tenant_id: str, callback: Callable[[RealtimeMessage], None]) -> bool:
        """Subscribe to table updates"""
        channel = self._get_channel("table_updates", tenant_id)
        return await self._subscribe_to_channel(channel, callback)

    async def subscribe_to_user_notifications(self, tenant_id: str, user_id: str,
                                            callback: Callable[[RealtimeMessage], None]) -> bool:
        """Subscribe to user-specific notifications"""
        channel = self._get_channel("user_notifications", tenant_id, user_id)
        return await self._subscribe_to_channel(channel, callback)

    async def subscribe_to_agent_messages(self, tenant_id: str,
                                        callback: Callable[[RealtimeMessage], None]) -> bool:
        """Subscribe to agent messages"""
        channel = self._get_channel("agent_messages", tenant_id)
        return await self._subscribe_to_channel(channel, callback)

    async def subscribe_to_system_alerts(self, tenant_id: str,
                                       callback: Callable[[RealtimeMessage], None]) -> bool:
        """Subscribe to system alerts"""
        channel = self._get_channel("system_alerts", tenant_id)
        return await self._subscribe_to_channel(channel, callback)

    async def _subscribe_to_channel(self, channel: str, callback: Callable[[RealtimeMessage], None]) -> bool:
        """Internal method to subscribe to a channel"""
        try:
            def message_handler(ch: str, msg: Any):
                try:
                    if isinstance(msg, str):
                        message_data = json.loads(msg)
                        message = RealtimeMessage.from_dict(message_data)
                        callback(message)
                    else:
                        logger.warning(f"Received non-string message on {channel}: {type(msg)}")
                except Exception as e:
                    logger.error(f"Error processing message on {channel}: {e}")

            success = self.redis.subscribe(channel, message_handler)
            if success:
                logger.info(f"Subscribed to channel: {channel}")
            return success

        except Exception as e:
            logger.error(f"Failed to subscribe to channel {channel}: {e}")
            return False

    # ==================== UTILITY METHODS ====================

    def get_active_subscribers(self, tenant_id: str) -> Dict[str, int]:
        """
        Get count of active subscribers per channel for a tenant

        Args:
            tenant_id: Restaurant identifier

        Returns:
            Dict mapping channel types to subscriber counts
        """
        stats = {}

        for channel_type, pattern in self.channels.items():
            if "{user_id}" not in pattern:  # Skip user-specific channels
                channel = pattern.format(tenant_id=tenant_id)
                # Redis PUBSUB NUMSUB returns subscriber count
                try:
                    if hasattr(self.redis, '_redis_client') and self.redis._redis_client:
                        pubsub_info = self.redis._redis_client.execute_command('PUBSUB', 'NUMSUB', channel)
                        if len(pubsub_info) >= 2:
                            stats[channel_type] = pubsub_info[1]
                        else:
                            stats[channel_type] = 0
                    else:
                        stats[channel_type] = 0
                except Exception as e:
                    logger.warning(f"Failed to get subscriber count for {channel}: {e}")
                    stats[channel_type] = 0

        return stats

    def broadcast_to_tenant(self, tenant_id: str, message_type: MessageType,
                          data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Broadcast message to all channels for a tenant

        Args:
            tenant_id: Restaurant identifier
            message_type: Type of message
            data: Message data
            metadata: Additional metadata

        Returns:
            bool: Success status
        """
        import uuid

        message = RealtimeMessage(
            message_id=str(uuid.uuid4()),
            message_type=message_type,
            tenant_id=tenant_id,
            data=data,
            timestamp=datetime.now(timezone.utc),
            metadata=metadata
        )

        channel = self._get_channel("global_broadcast", tenant_id)
        subscribers = self.redis.publish(channel, json.dumps(message.to_dict()))

        logger.info(f"Broadcast message to {subscribers} subscribers for tenant {tenant_id}")
        return subscribers > 0

    async def cleanup_subscriptions(self):
        """Clean up all active subscriptions"""
        for task in self.running_tasks:
            task.cancel()
        self.running_tasks.clear()
        self.subscribers.clear()
        logger.info("Cleaned up all realtime subscriptions")


# ==================== SINGLETON INSTANCE ====================

_realtime_service_instance = None

def get_realtime_service() -> RealtimeService:
    """Get singleton realtime service instance"""
    global _realtime_service_instance
    if _realtime_service_instance is None:
        _realtime_service_instance = RealtimeService()
    return _realtime_service_instance


if __name__ == "__main__":

    async def test_realtime_service():
        """Test the realtime service functionality"""
        print("Testing Realtime Service...")

        rt = RealtimeService()

        # Test message handler
        def order_handler(message: RealtimeMessage):
            print(f"Order update: {message.data['order_id']}  {message.data['status']}")

        def table_handler(message: RealtimeMessage):
            print(f"Table update: Table {message.data['table_id']}  {'available' if message.data['available'] else 'unavailable'}")

        # Subscribe to channels
        await rt.subscribe_to_orders("restaurant_123", order_handler)
        await rt.subscribe_to_tables("restaurant_123", table_handler)

        # Give subscribers time to connect
        await asyncio.sleep(1)

        # Publish test messages
        print("Publishing test messages...")

        rt.publish_order_update(
            tenant_id="restaurant_123",
            order_id="ORD-001",
            status="preparing",
            estimated_ready_time="2024-01-15T19:30:00"
        )

        rt.publish_table_update(
            tenant_id="restaurant_123",
            table_id="T001",
            is_available=False,
            party_size=4
        )

        rt.publish_user_notification(
            tenant_id="restaurant_123",
            user_id="user_123",
            notification_type="order_ready",
            title="Order Ready!",
            message="Your order is ready for pickup"
        )

        # Wait for messages to be processed
        await asyncio.sleep(2)

        # Get stats
        stats = rt.get_active_subscribers("restaurant_123")
        print(f"Active subscribers: {stats}")

        # Cleanup
        await rt.cleanup_subscriptions()
        print("Realtime Service test completed!")

    # Run test
    asyncio.run(test_realtime_service())

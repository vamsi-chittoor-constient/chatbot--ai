"""
MongoDB Connection Manager for Testing Module
==============================================

WARNING: TESTING MODULE - This file is part of the manual testing infrastructure
and can be removed when testing is complete.

This module manages MongoDB connections for storing testing data and validation feedback.
All testing conversations are logged in JSON Lines format for future training purposes.
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection

logger = logging.getLogger(__name__)


class MongoDBTestingManager:
    """
    MongoDB manager specifically for testing data.

    Collections:
    - testing_sessions: Testing session metadata (tester info, counts)
    - testing_data: All messages with embedded orchestration flow and validation
    """

    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self._connected = False

    async def connect(self):
        """Establish connection to MongoDB."""
        if self._connected:
            logger.info("MongoDB already connected")
            return

        try:
            connection_string = os.getenv("MONGODB_CONNECTION_STRING", "mongodb://localhost:27017")
            database_name = os.getenv("MONGODB_DATABASE_NAME", "restaurant_ai_analytics")

            logger.info(f"Connecting to MongoDB at {connection_string}")

            # Disable MongoDB command monitoring to reduce log verbosity
            import pymongo
            from pymongo import monitoring

            # Remove all event listeners to prevent verbose logging
            monitoring._LISTENERS = monitoring._Listeners([], [], [], [], [])

            self.client = AsyncIOMotorClient(
                connection_string,
                # Disable server monitoring logs
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000
            )
            self.db = self.client[database_name]

            # Test connection
            await self.client.server_info()

            self._connected = True
            logger.info(f"Successfully connected to MongoDB database: {database_name}")

            # Create indexes for better query performance
            await self._create_indexes()

        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise

    async def _create_indexes(self):
        """Create indexes for testing collections."""
        if self.db is None:
            return

        try:
            # Testing sessions indexes
            sessions_coll = self.db.testing_sessions
            await sessions_coll.create_index("session_id", unique=True)
            await sessions_coll.create_index("tester_id")
            await sessions_coll.create_index("started_at")

            # Testing data indexes (messages + validation combined)
            data_coll = self.db.testing_data
            await data_coll.create_index("message_id", unique=True)
            await data_coll.create_index("session_id")
            await data_coll.create_index("timestamp")
            await data_coll.create_index([("session_id", 1), ("timestamp", 1)])
            await data_coll.create_index("validation.validated_at")  # For filtering validated messages

            logger.info("MongoDB indexes created successfully")

        except Exception as e:
            logger.error(f"Failed to create indexes: {str(e)}")

    async def disconnect(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            self._connected = False
            logger.info("MongoDB connection closed")

    # ============ Session Management ============

    async def create_session(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new testing session."""
        if self.db is None:
            raise RuntimeError("MongoDB not connected")

        # Insert the session data as-is
        await self.db.testing_sessions.insert_one(session_data)
        logger.info(f"Created testing session: {session_data.get('session_id')}")

        return session_data

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a testing session."""
        if self.db is None:
            return None

        session = await self.db.testing_sessions.find_one(
            {"session_id": session_id},
            {"_id": 0}
        )
        return session

    async def update_session(self, session_id: str, update_data: Dict[str, Any]):
        """Update session metadata."""
        if self.db is None:
            return

        await self.db.testing_sessions.update_one(
            {"session_id": session_id},
            {"$set": update_data}
        )

    async def increment_session_messages(self, session_id: str, validated: bool = False):
        """Increment message counters for a session."""
        if self.db is None:
            return

        update = {"$inc": {"total_messages": 1}}
        if validated:
            update["$inc"]["validated_messages"] = 1

        await self.db.testing_sessions.update_one(
            {"session_id": session_id},
            update
        )

    async def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Get all active testing sessions."""
        if self.db is None:
            return []

        cursor = self.db.testing_sessions.find(
            {"status": "active"},
            {"_id": 0}
        ).sort("started_at", -1)

        return await cursor.to_list(length=100)

    # ============ Message Management ============

    async def save_message(self, message_data: Dict[str, Any]):
        """
        Save a testing message with full orchestration metadata.

        The message will have this structure:
        {
            "message_id": "...",
            "session_id": "...",
            "user_input": {...},
            "orchestration_flow": {...},
            "total_duration_ms": 123,
            "validation": null  // Will be updated later when tester validates
        }
        """
        if self.db is None:
            return

        # Ensure timestamp is ISO format
        if "timestamp" in message_data and isinstance(message_data["timestamp"], datetime):
            message_data["timestamp"] = message_data["timestamp"].isoformat()

        # Initialize validation field as null (will be updated later)
        if "validation" not in message_data:
            message_data["validation"] = None

        # Store in MongoDB (single collection for all data)
        await self.db.testing_data.insert_one(message_data)

        # Increment session message count
        await self.increment_session_messages(message_data["session_id"])

        logger.info(f"Saved testing message: {message_data.get('message_id')}")

    async def get_message(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific message with its validation data."""
        if self.db is None:
            return None

        message = await self.db.testing_data.find_one(
            {"message_id": message_id},
            {"_id": 0}
        )
        return message

    async def get_session_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all messages for a session (includes validation data)."""
        if self.db is None:
            return []

        cursor = self.db.testing_data.find(
            {"session_id": session_id},
            {"_id": 0}
        ).sort("timestamp", 1)

        return await cursor.to_list(length=1000)

    # ============ Validation Management ============

    async def save_validation(self, message_id: str, session_id: str, validation_data: Dict[str, Any]):
        """
        Save tester validation for a message.

        Updates the message document to add validation data under the 'validation' field.
        """
        if self.db is None:
            return

        # Add validated_at timestamp to validation data
        validation_with_timestamp = {
            **validation_data,
            "validated_at": datetime.utcnow().isoformat()
        }

        # Update the message document with validation data
        result = await self.db.testing_data.update_one(
            {"message_id": message_id},
            {"$set": {"validation": validation_with_timestamp}}
        )

        if result.modified_count == 0:
            logger.warning(f"No message found to validate: {message_id}")
            return

        # Increment validated messages count
        await self.increment_session_messages(session_id, validated=True)

        logger.info(f"Saved validation for message: {message_id}")

    async def get_validation(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve validation for a message (now embedded in the message doc)."""
        if self.db is None:
            return None

        message = await self.db.testing_data.find_one(
            {"message_id": message_id},
            {"_id": 0, "validation": 1}
        )
        return message.get("validation") if message else None

    # ============ Export Functionality ============

    async def export_session_jsonl(self, session_id: str) -> str:
        """
        Export session data as JSON Lines format.

        Returns a string with one JSON object per line, suitable for training.
        Each line contains: user_input, orchestration_flow, validation (if available).
        """
        # Get all messages for session (validation is already embedded)
        messages = await self.get_session_messages(session_id)

        # Convert to JSON Lines format (one JSON object per line)
        jsonl_lines = [json.dumps(msg, ensure_ascii=False) for msg in messages]
        return "\n".join(jsonl_lines)

    async def export_all_sessions_jsonl(self) -> str:
        """Export all testing sessions as JSON Lines."""
        sessions = await self.get_active_sessions()

        all_lines = []
        for session in sessions:
            session_jsonl = await self.export_session_jsonl(session["session_id"])
            all_lines.append(session_jsonl)

        return "\n".join(all_lines)


# Global singleton instance
_mongodb_testing_manager: Optional[MongoDBTestingManager] = None


def get_mongodb_testing_manager() -> MongoDBTestingManager:
    """Get the global MongoDB testing manager instance."""
    global _mongodb_testing_manager

    if _mongodb_testing_manager is None:
        _mongodb_testing_manager = MongoDBTestingManager()

    return _mongodb_testing_manager

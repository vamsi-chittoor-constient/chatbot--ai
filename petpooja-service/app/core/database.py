"""
Database Helper Functions using SQLAlchemy ORM
All database operations now use SQLAlchemy for consistency

NOTE: Old models (Restaurant, RestaurantBranch, etc.) have been removed.
This file is kept for backward compatibility but methods are disabled.
"""

import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text, func

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class DatabaseHelper:
    """
    Database helper class using SQLAlchemy ORM

    NOTE: Most methods are disabled as old models have been removed.
    Use new models from menu_models.py, branch_models.py, etc. instead.
    """

    @staticmethod
    def health_check(db: Session) -> Dict[str, Any]:
        """Check database health"""
        try:
            # Get PostgreSQL version
            version_result = db.execute(text("SELECT version()")).fetchone()
            version = version_result[0] if version_result else "unknown"

            return {
                "status": "healthy",
                "database": settings.POSTGRES_DB,
                "host": settings.POSTGRES_HOST,
                "version": version
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }


# Create singleton instance for convenience
db_helper = DatabaseHelper()

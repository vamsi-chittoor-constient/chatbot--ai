"""
Validation Decorators for Database Tools
========================================

Decorators that automatically validate schema compatibility before tool execution.
Prevents runtime errors due to schema mismatches.

Usage:
    @validate_schema(OTPVerification)
    class CreateOTPTool(ToolBase):
        # Tool implementation
"""

import functools
from typing import Type, List, Optional
from sqlalchemy.orm import DeclarativeBase
from app.utils.schema_validator import validate_model_before_tool_execution
from app.core.logging_config import get_logger
from app.tools.base.tool_base import ToolError

logger = get_logger(__name__)


def validate_schema(*models: Type[DeclarativeBase]):
    """
    Decorator that validates SQLAlchemy models against database schema
    before allowing tool execution.

    Args:
        *models: SQLAlchemy model classes to validate

    Usage:
        @validate_schema(OTPVerification)
        class CreateOTPTool(ToolBase):
            pass
    """
    def decorator(cls):
        original_init = cls.__init__
        original_execute = cls._execute_impl if hasattr(cls, '_execute_impl') else None

        @functools.wraps(original_init)
        def __init__(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            self._validated_models = models
            self._schema_validated = False

        async def validated_execute_impl(self, **kwargs):
            # Perform schema validation before first execution
            if not self._schema_validated:
                for model in self._validated_models:
                    is_valid = await validate_model_before_tool_execution(model, self.name)
                    if not is_valid:
                        raise ToolError(
                            f"Schema validation failed for model {model.__name__}. "
                            "Check database schema matches model definition.",
                            tool_name=self.name
                        )
                self._schema_validated = True

            # Call original implementation
            if original_execute:
                return await original_execute(self, **kwargs)
            else:
                raise ToolError("No execute implementation found", tool_name=self.name)

        # Replace methods
        cls.__init__ = __init__
        if original_execute:
            cls._execute_impl = validated_execute_impl

        return cls

    return decorator


def require_tables(*table_names: str):
    """
    Decorator that ensures specific tables exist before tool execution.

    Args:
        *table_names: Names of tables that must exist

    Usage:
        @require_tables("users", "otp_verification")
        class CreateOTPTool(ToolBase):
            pass
    """
    def decorator(cls):
        original_execute = cls._execute_impl if hasattr(cls, '_execute_impl') else None

        async def validated_execute_impl(self, **kwargs):
            from app.utils.schema_validator import SchemaValidator

            validator = SchemaValidator()
            for table_name in table_names:
                table_info = await validator.get_table_info(table_name)
                if not table_info or not table_info["exists"]:
                    raise ToolError(
                        f"Required table '{table_name}' does not exist in database",
                        tool_name=self.name
                    )

            if original_execute:
                return await original_execute(self, **kwargs)
            else:
                raise ToolError("No execute implementation found", tool_name=self.name)

        if original_execute:
            cls._execute_impl = validated_execute_impl

        return cls

    return decorator


def validate_columns(model: Type[DeclarativeBase], required_columns: List[str]):
    """
    Decorator that validates specific columns exist in database table.

    Args:
        model: SQLAlchemy model to check
        required_columns: List of column names that must exist

    Usage:
        @validate_columns(OTPVerification, ["phone_number", "otp_code", "expires_at"])
        class CreateOTPTool(ToolBase):
            pass
    """
    def decorator(cls):
        original_execute = cls._execute_impl if hasattr(cls, '_execute_impl') else None

        async def validated_execute_impl(self, **kwargs):
            from app.utils.schema_validator import SchemaValidator

            # Get table name directly from model
            table_name = model.__tablename__

            validator = SchemaValidator()
            table_info = await validator.get_table_info(table_name)

            if not table_info or not table_info["exists"]:
                raise ToolError(
                    f"Table '{table_name}' does not exist in database",
                    tool_name=self.name
                )

            missing_columns = []
            for column_name in required_columns:
                if column_name not in table_info["columns"]:
                    missing_columns.append(column_name)

            if missing_columns:
                raise ToolError(
                    f"Required columns missing from table '{table_name}': {', '.join(missing_columns)}",
                    tool_name=self.name
                )

            if original_execute:
                return await original_execute(self, **kwargs)
            else:
                raise ToolError("No execute implementation found", tool_name=self.name)

        if original_execute:
            cls._execute_impl = validated_execute_impl

        return cls

    return decorator


def auto_fix_schema(model: Type[DeclarativeBase], fix_types: Optional[List[str]] = None):
    """
    Decorator that attempts to automatically fix common schema issues.

    Args:
        model: SQLAlchemy model to fix
        fix_types: Types of fixes to attempt (default: all)

    Usage:
        @auto_fix_schema(OTPVerification, ["column_names", "table_name"])
        class CreateOTPTool(ToolBase):
            pass
    """
    def decorator(cls):
        original_execute = cls._execute_impl if hasattr(cls, '_execute_impl') else None

        async def validated_execute_impl(self, **kwargs):
            from app.utils.schema_validator import fix_common_schema_issues

            # Note: fix_types parameter is reserved for future enhancement
            _ = fix_types

            # Attempt to fix schema issues
            fixes_applied = await fix_common_schema_issues(model)
            if fixes_applied:
                logger.info(f"Schema fixes suggested for {model.__name__}: {fixes_applied}")

            # Validate after fixes
            is_valid = await validate_model_before_tool_execution(model, self.name)
            if not is_valid:
                raise ToolError(
                    f"Schema validation failed for model {model.__name__} even after attempted fixes",
                    tool_name=self.name
                )

            if original_execute:
                return await original_execute(self, **kwargs)
            else:
                raise ToolError("No execute implementation found", tool_name=self.name)

        if original_execute:
            cls._execute_impl = validated_execute_impl

        return cls

    return decorator


# Utility function to validate multiple models at once
async def validate_models_for_tool(models: List[Type[DeclarativeBase]], tool_name: str) -> bool:
    """
    Validate multiple models for a tool.
    Returns True if all validations pass, False otherwise.
    """
    for model in models:
        is_valid = await validate_model_before_tool_execution(model, tool_name)
        if not is_valid:
            return False
    return True

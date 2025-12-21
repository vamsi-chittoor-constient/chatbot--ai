"""
Schema-Tool Integration Utilities
==================================

Utilities for integrating Pydantic schemas with database tools for consistent
validation both when writing to and reading from the database.

This ensures:
1. Input validation using request schemas before DB writes
2. Output serialization using response schemas after DB reads
3. Single source of truth for data validation
4. Type safety across the entire stack
"""

from typing import Any, Dict, Type, Optional, TypeVar, Union
from pydantic import BaseModel, ValidationError
from app.tools.base.tool_base import ToolError
from app.core.logging_config import get_logger

logger = get_logger(__name__)

T = TypeVar('T', bound=BaseModel)


def validate_input_with_schema(
    schema_class: Type[T],
    data: Dict[str, Any],
    tool_name: str,
    partial: bool = False
) -> Dict[str, Any]:
    """
    Validate input data using Pydantic schema.

    Args:
        schema_class: Pydantic schema class for validation
        data: Input data dictionary
        tool_name: Name of the tool (for error messages)
        partial: If True, allow partial validation (for updates)

    Returns:
        Validated data as dictionary

    Raises:
        ToolError: If validation fails
    """
    try:
        if partial:
            # For updates - only validate provided fields
            validated = schema_class.model_validate(data, strict=False)
        else:
            # For creates - validate all required fields
            validated = schema_class.model_validate(data)

        return validated.model_dump(exclude_none=not partial)

    except ValidationError as e:
        # Convert Pydantic errors to user-friendly messages
        error_messages = []
        for error in e.errors():
            field = " -> ".join(str(loc) for loc in error['loc'])
            message = error['msg']
            error_messages.append(f"{field}: {message}")

        error_text = "\n".join(error_messages)
        logger.warning(
            f"Schema validation failed in {tool_name}",
            schema=schema_class.__name__,
            errors=error_text
        )

        raise ToolError(
            f"Input validation failed:\n{error_text}",
            tool_name=tool_name
        )
    except Exception as e:
        logger.error(
            f"Unexpected error during schema validation in {tool_name}",
            error=str(e)
        )
        raise ToolError(
            f"Validation error: {str(e)}",
            tool_name=tool_name
        )


def serialize_output_with_schema(
    schema_class: Type[T],
    data: Any,
    tool_name: str,
    from_orm: bool = True
) -> Dict[str, Any]:
    """
    Serialize output data using Pydantic schema.

    Ensures data returned from DB matches expected schema format.

    Args:
        schema_class: Pydantic response schema class
        data: Output data (SQLAlchemy model or dict)
        tool_name: Name of the tool (for error messages)
        from_orm: If True, validate from SQLAlchemy ORM model

    Returns:
        Serialized data as dictionary

    Raises:
        ToolError: If serialization fails
    """
    try:
        if from_orm:
            # Convert SQLAlchemy model to Pydantic model
            validated = schema_class.model_validate(data)
        else:
            # Validate dict data
            validated = schema_class.model_validate(data)

        # Use mode='json' to serialize Decimal to float for JSON compatibility
        return validated.model_dump(mode='json')

    except ValidationError as e:
        # Log but don't fail - data is already in DB
        logger.error(
            f"Schema serialization failed in {tool_name}",
            schema=schema_class.__name__,
            errors=str(e.errors())
        )

        # Fallback: return as-is if serialization fails
        if hasattr(data, '__dict__'):
            return {k: v for k, v in data.__dict__.items() if not k.startswith('_')}
        return data

    except Exception as e:
        logger.error(
            f"Unexpected error during schema serialization in {tool_name}",
            error=str(e)
        )

        # Fallback: return as-is
        if hasattr(data, '__dict__'):
            return {k: v for k, v in data.__dict__.items() if not k.startswith('_')}
        return data


def validate_and_convert(
    request_schema: Optional[Type[BaseModel]],
    response_schema: Optional[Type[BaseModel]],
    tool_name: str
):
    """
    Decorator to add schema validation to tool methods.

    Usage:
        @validate_and_convert(UserCreateRequest, UserResponse, "create_user")
        class CreateUserTool(ToolBase):
            async def _execute_impl(self, **kwargs):
                # kwargs are already validated
                # return value will be serialized
                ...

    Args:
        request_schema: Schema for input validation (optional)
        response_schema: Schema for output serialization (optional)
        tool_name: Name of the tool
    """
    def decorator(cls):
        original_validate = getattr(cls, 'validate_input', None)
        original_execute = getattr(cls, '_execute_impl', None)

        if request_schema:
            def validate_input(self, **kwargs):
                # Call original validation if exists
                if original_validate:
                    kwargs = original_validate(self, **kwargs)

                # Apply schema validation
                return validate_input_with_schema(
                    request_schema,
                    kwargs,
                    tool_name
                )

            cls.validate_input = validate_input

        if response_schema and original_execute:
            async def execute_with_serialization(self, **kwargs):
                # Execute original implementation
                result = await original_execute(self, **kwargs)

                # Serialize response if data exists
                if hasattr(result, 'data') and result.data:
                    if isinstance(result.data, list):
                        # Serialize list of items
                        result.data = [
                            serialize_output_with_schema(
                                response_schema,
                                item,
                                tool_name,
                                from_orm=not isinstance(item, dict)
                            )
                            for item in result.data
                        ]
                    else:
                        # Serialize single item
                        result.data = serialize_output_with_schema(
                            response_schema,
                            result.data,
                            tool_name,
                            from_orm=not isinstance(result.data, dict)
                        )

                return result

            cls._execute_impl = execute_with_serialization

        return cls

    return decorator


def safe_isoformat(dt) -> Optional[str]:
    """Safely convert datetime to ISO format string, handling None values"""
    if dt is None:
        return None
    if isinstance(dt, str):
        return dt
    return dt.isoformat()


# Re-export for convenience
__all__ = [
    'validate_input_with_schema',
    'serialize_output_with_schema',
    'validate_and_convert',
    'safe_isoformat'
]

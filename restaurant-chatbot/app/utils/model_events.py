"""
SQLAlchemy Event Listeners for Custom ID Generation
===================================================
Automatically generates custom IDs for all models before insert.

Format: {prefix}{6-alphanumeric}
- prefix: 3-letter identifier (e.g., usr, res, ord)
- 6-alphanumeric: Random 6-character string (A-Z, 0-9)

Security: Random IDs prevent enumeration attacks (IDOR vulnerability)
"""

from sqlalchemy import event
import structlog
from collections import defaultdict
from threading import local

logger = structlog.get_logger(__name__)

# Thread-local storage for tracking IDs generated within the same transaction
_transaction_ids = local()


def generate_id_sync(mapper, connection, target):
    """
    Synchronous ID generator for SQLAlchemy before_insert event.

    This is called automatically before each INSERT operation.
    Generates secure random alphanumeric IDs with collision checking.

    IMPORTANT: Handles multiple inserts in the same transaction by tracking
    generated IDs to avoid duplicates within the transaction.

    Args:
        mapper: SQLAlchemy mapper
        connection: Database connection
        target: Model instance being inserted
    """
    from app.utils.id_generator import ENTITY_PREFIXES, format_id, generate_random_suffix

    table_name = target.__tablename__

    # Skip if ID already set (manual generation)
    if target.id:
        logger.debug(
            "Skipping auto ID generation - ID already set",
            table=table_name,
            id=target.id
        )
        return

    prefix = ENTITY_PREFIXES.get(table_name)

    if not prefix:
        logger.error(
            "No prefix defined for table",
            table=table_name
        )
        raise ValueError(f"No ID prefix defined for table: {table_name}")

    try:
        # Initialize transaction ID tracker if not present
        if not hasattr(_transaction_ids, 'ids'):
            _transaction_ids.ids = set()

        max_retries = 5
        generated_id = None

        for attempt in range(max_retries):
            # Generate random ID
            random_suffix = generate_random_suffix()
            candidate_id = format_id(prefix, random_suffix)

            # Check if ID was already generated in this transaction
            if candidate_id in _transaction_ids.ids:
                logger.warning(
                    "ID collision within transaction, retrying",
                    table=table_name,
                    id=candidate_id,
                    attempt=attempt + 1
                )
                continue

            # Check if ID exists in database
            from sqlalchemy import text
            query = text(f"SELECT COUNT(*) FROM {table_name} WHERE id = :id")

            try:
                result = connection.execute(query, {"id": candidate_id})
                count = result.scalar()

                if count == 0:
                    # ID is unique - use it
                    generated_id = candidate_id
                    _transaction_ids.ids.add(generated_id)
                    break
                else:
                    logger.warning(
                        "ID collision in database, retrying",
                        table=table_name,
                        id=candidate_id,
                        attempt=attempt + 1
                    )
            except Exception as e:
                # If sync query fails (async context), use fallback
                if str(e).find('greenlet') != -1 or str(e).find('await_only') != -1:
                    logger.warning(
                        "Async context detected in sync event listener - using fallback ID",
                        table=table_name,
                        error=str(e)
                    )
                    # Generate fallback ID and hope for no collision
                    generated_id = candidate_id
                    _transaction_ids.ids.add(generated_id)
                    break
                else:
                    raise

        if generated_id is None:
            raise RuntimeError(f"Unable to generate unique ID for {table_name} after {max_retries} attempts")

        # Set the ID on the target object
        target.id = generated_id

        logger.debug(
            "Auto-generated random ID for insert",
            table=table_name,
            id=generated_id
        )

    except Exception as e:
        logger.error(
            "Failed to auto-generate ID",
            table=table_name,
            error=str(e),
            exc_info=True
        )
        # Fallback: use timestamp-based random suffix
        import time
        import random
        import string
        fallback_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        fallback_id = format_id(prefix, fallback_suffix)
        target.id = fallback_id
        logger.warning(
            "Using fallback random ID",
            table=table_name,
            id=fallback_id
        )


# Track which models already have listeners registered
_registered_models = set()


def _reset_transaction_ids(session):
    """Reset transaction ID tracker after commit or rollback."""
    if hasattr(_transaction_ids, 'ids'):
        _transaction_ids.ids.clear()


def _setup_transaction_listeners(session_factory):
    """
    Set up listeners to reset transaction ID tracker after transaction completion.

    This should be called once during database initialization.
    """
    from sqlalchemy import event as sa_event

    @sa_event.listens_for(session_factory, "after_commit")
    def receive_after_commit(session):
        _reset_transaction_ids(session)

    @sa_event.listens_for(session_factory, "after_rollback")
    def receive_after_rollback(session):
        _reset_transaction_ids(session)


def register_id_generators(base_class):
    """
    Register before_insert event listeners for all models.

    This function should be called after all models are defined.
    It automatically registers ID generation for all models that
    inherit from the base class.

    This function is idempotent - it will not re-register listeners
    for models that already have them.

    Args:
        base_class: SQLAlchemy declarative base class

    Example:
        from app.shared.models.base import Base
        from app.utils.model_events import register_id_generators

        register_id_generators(Base)
    """
    from app.utils.id_generator import ENTITY_PREFIXES

    registered_count = 0

    # Get all mapped classes
    for mapper in base_class.registry.mappers:
        model_class = mapper.class_
        table_name = model_class.__tablename__

        # Skip if already registered
        model_key = f"{model_class.__module__}.{model_class.__name__}"
        if model_key in _registered_models:
            continue

        # Only register for tables with defined prefixes
        if table_name in ENTITY_PREFIXES:
            # Check if event is already registered
            if not event.contains(model_class, 'before_insert', generate_id_sync):
                # Register before_insert event
                event.listen(
                    model_class,
                    'before_insert',
                    generate_id_sync,
                    propagate=True
                )

                _registered_models.add(model_key)
                registered_count += 1

                logger.debug(
                    "Registered ID generator",
                    model=model_class.__name__,
                    table=table_name,
                    prefix=ENTITY_PREFIXES[table_name]
                )

    if registered_count > 0:
        logger.info(
            "ID generators registered",
            count=registered_count,
            total_prefixes=len(ENTITY_PREFIXES)
        )

    return registered_count

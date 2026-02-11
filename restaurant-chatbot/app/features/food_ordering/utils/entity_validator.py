"""
Entity Validator
================
Validates extracted entities and handles missing entity collection.

Provides clarification questions for missing required fields.
"""

from typing import Dict, Any, Optional, List
import structlog

from app.features.food_ordering.state import (
    SubIntentClassification,
    EntitySchema,
    FoodOrderingState
)

logger = structlog.get_logger("food_ordering.entity_validator")


def validate_entities(
    classification: SubIntentClassification,
    state: FoodOrderingState,
    merged_entities: Optional[Dict[str, Any]] = None
) -> tuple[bool, List[str], Optional[str]]:
    """
    Validate that all required entities are present.

    Args:
        classification: Intent classification with entities
        state: Current state
        merged_entities: Optional pre-merged entities (from merge_entities_from_state)
                        If provided, uses these instead of classification.entities

    Returns:
        Tuple of (is_valid, missing_entities, clarification_question)
    """
    sub_intent = classification.sub_intent
    # Use merged entities if provided, otherwise use classification entities
    entities = merged_entities if merged_entities is not None else classification.entities
    missing = []

    # Check intent-specific required entities
    if sub_intent == "manage_cart":
        # Manage cart requires "action"
        action = entities.get("action")
        if not action:
            missing.append("action")
            return False, missing, "I'd be happy to help with your cart! Would you like to add items, view your cart, remove something, or make any changes?"

        # Handle Ambiguous Selection (user repeated item name from recommendations)
        if action == "ambiguous_select":
            item_name = entities.get("item_name", "that item")
            missing.append("intent_clarification")
            return False, missing, f"Would you like to order {item_name} or learn more about it?"

        # Different actions require different entities
        if action == "add":
            # First check for item_name
            if not entities.get("item_name") and not entities.get("item_id") and not entities.get("items_to_add"):
                missing.append("item_name")
                return False, missing, "Sure! What dish would you like me to add to your cart?"

            # Then check for quantity (required for single item add)
            if entities.get("item_name") and not entities.get("quantity") and not entities.get("items_to_add"):
                # Get item name for personalized question
                item_name = entities.get("item_name", "")
                missing.append("quantity")
                return False, missing, f"Great choice! How many {item_name.title()} would you like me to add?"

        elif action in ["remove", "update"]:
            if not entities.get("item_name") and not entities.get("item_id") and not entities.get("item_index"):
                missing.append("item_identifier")
                action_word = "remove" if action == "remove" else "update"
                return False, missing, f"Sure, I can help with that! Which item would you like to {action_word}? You can tell me the item name or its number from your cart."

            if action == "update" and not entities.get("quantity"):
                missing.append("quantity")
                return False, missing, "No problem! What would you like to change the quantity to?"

    elif sub_intent == "execute_checkout":
        # Checkout requires order type
        order_type = entities.get("order_type") or state.get("order_type")

        # Order type is always takeaway - no need to ask
        if not order_type:
            state["order_type"] = "take_away"

    elif sub_intent == "browse_menu":
        # Browse menu with category requires category_name
        # But it's optional - can show all categories if not specified
        pass

    elif sub_intent == "discover_items":
        # Discovery can work with or without search criteria
        # If no criteria provided, agent will show menu categories
        # This allows vague requests like "i want food" to proceed naturally
        pass

    # All required entities present
    return True, [], None


def merge_entities_from_state(
    entities: Dict[str, Any],
    state: FoodOrderingState
) -> Dict[str, Any]:
    """
    Merge extracted entities with state context.

    Fills in missing entities from state if available.
    Also merges pending entities from entity collection flow.

    Args:
        entities: Newly extracted entities
        state: Current state with context

    Returns:
        Merged entities dict
    """
    merged = entities.copy()

    # Fill in order_type from state if not in entities
    order_type = state.get("order_type")
    if "order_type" not in merged and order_type:
        merged["order_type"] = order_type

    # Merge pending entities from entity collection flow
    # This handles multi-turn entity collection (e.g., item_name collected, now collecting quantity)
    pending_entities = state.get("pending_entities", {})
    if pending_entities:
        for key, value in pending_entities.items():
            if key not in merged and value is not None:
                merged[key] = value
                logger.debug(
                    "Merged pending entity from state",
                    entity=key,
                    value=value
                )

    # NOTE: Do NOT default quantity to 1 - require explicit user input
    # This ensures the bot asks "How many would you like?" for ordering intents

    return merged


def get_clarification_question(
    entity_name: str,
    sub_intent: str
) -> str:
    """
    Get a natural clarification question for a missing entity.

    Args:
        entity_name: Name of the missing entity
        sub_intent: Current sub-intent

    Returns:
        Natural language question to ask user
    """
    questions = {
        "item_name": "I'd love to help you order! What dish catches your eye?",
        "quantity": "Sounds delicious! How many would you like me to add?",
        "category_name": "Sure! Which category would you like to explore?",
        "dietary_restrictions": "Of course! Do you have any dietary preferences I should keep in mind? (vegetarian, vegan, gluten-free, etc.)",
        "order_type": "Your order will be prepared for takeaway.",
        "action": "I'm here to help! Would you like to add items, view your cart, or proceed to checkout?",
        "item_identifier": "Sure thing! Which item are you referring to? You can tell me the name or its number.",
        "search_criteria": "I'd be happy to help you find something! What type of dish are you in the mood for?"
    }

    return questions.get(entity_name, f"Just to make sure I get this right, could you tell me the {entity_name.replace('_', ' ')}?")


def resolve_item_identifier(
    entities: Dict[str, Any],
    state: FoodOrderingState
) -> Optional[str]:
    """
    Resolve item identifier to actual item_id.

    Handles:
    - item_name  search menu  item_id
    - item_index (e.g., "item 2")  cart[1]  item_id
    - item_id  validate and return

    Args:
        entities: Extracted entities
        state: Current state

    Returns:
        Resolved item_id or None
    """
    # Direct item_id provided
    if entities.get("item_id"):
        return entities["item_id"]

    # Item index (e.g., "remove item 2")
    item_index = entities.get("item_index")
    cart_items = state.get("cart_items", [])
    if item_index and cart_items:
        try:
            index = int(item_index) - 1  # Convert to 0-indexed
            if 0 <= index < len(cart_items):
                return cart_items[index].get("item_id")
        except (ValueError, IndexError):
            logger.warning("Invalid item index", item_index=item_index)
            return None

    # Item name - will be resolved by agent using menu search
    return entities.get("item_name")


__all__ = [
    "validate_entities",
    "merge_entities_from_state",
    "get_clarification_question",
    "resolve_item_identifier"
]

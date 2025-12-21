"""
Food Ordering Sub-Graph
========================
Main orchestration for food ordering domain.

Flow:
1. Classify sub-intent and extract entities
2. Validate entities and collect missing fields
3. Route to appropriate specialized agent
4. Return ActionResult for Response Agent

No LLM needed after classification - pure deterministic routing.
"""

from typing import Dict, Any, Optional
import structlog

from app.features.food_ordering.state import FoodOrderingState, SubIntentClassification
from app.features.food_ordering.sub_intent_classifier import classify_sub_intent
from app.features.food_ordering.utils.entity_validator import (
    validate_entities,
    merge_entities_from_state
)
from app.features.food_ordering.router import route_to_agent, register_agent

# Import all agents for registration
from app.features.food_ordering.agents.menu_browsing.node import menu_browsing_agent
from app.features.food_ordering.agents.menu_discovery.node import menu_discovery_agent
from app.features.food_ordering.agents.cart_management.node import cart_management_agent
from app.features.food_ordering.agents.checkout_validator.node import checkout_validator_agent
from app.features.food_ordering.agents.checkout_executor.node import checkout_executor_agent

logger = structlog.get_logger("food_ordering.graph")


# Register all agents at module initialization
def _register_agents():
    """Register all food ordering agents with the router"""
    register_agent("browse_menu", menu_browsing_agent)
    register_agent("discover_items", menu_discovery_agent)
    register_agent("manage_cart", cart_management_agent)
    register_agent("validate_order", checkout_validator_agent)
    register_agent("execute_checkout", checkout_executor_agent)
    logger.info("All food ordering agents registered")


# Register agents on import
_register_agents()


def apply_state_guardrails(
    classification: SubIntentClassification,
    state: FoodOrderingState,
    session_id: str
) -> tuple[bool, Optional[Dict[str, Any]]]:
    """
    Apply state-based guardrails to validate classified intent.

    Two-tier system:
    - SOFT GUIDES: Redirect to helpful flows (returns action result)
    - HARD BLOCKS: Prevent unsafe operations (returns error action)

    Args:
        classification: Classified intent
        state: Current state
        session_id: Session ID

    Returns:
        (should_proceed, override_result)
        - If should_proceed=True: Continue to agent routing
        - If should_proceed=False: Return override_result to user
    """
    sub_intent = classification.sub_intent
    cart_items = state.get("cart_items", [])
    cart_item_count = len(cart_items)

    # =================================================================
    # TIER 1: SOFT GUIDES - Helpful redirects (not strict blocks)
    # =================================================================

    if sub_intent == "validate_order":
        # SOFT GUIDE: Empty cart -> Suggest browsing
        if cart_item_count == 0:
            logger.info(
                "Soft guide: Redirecting empty cart checkout to menu browsing",
                session_id=session_id
            )
            return False, {
                "action": "empty_cart_redirect",
                "success": True,
                "data": {
                    "message": "Your cart is empty! Would you like to browse our menu?",
                    "suggestion": "browse_menu",
                    "cart_item_count": 0
                },
                "context": {
                    "guardrail_type": "soft_guide",
                    "original_intent": "validate_order",
                    "redirect_reason": "empty_cart"
                }
            }

    # =================================================================
    # TIER 2: HARD BLOCKS - Safety gates (strict enforcement)
    # =================================================================

    if sub_intent == "manage_cart":
        # HARD BLOCK: Cannot modify locked cart
        cart_locked = state.get("cart_locked", False)
        action = classification.entities.get("action")

        if cart_locked and action in ["add", "remove", "update", "clear"]:
            logger.warning(
                "Hard block: Cart modification blocked (cart locked)",
                session_id=session_id,
                action=action
            )
            return False, {
                "action": "cart_locked",
                "success": False,
                "data": {
                    "message": "Your cart is locked for checkout. Please complete your order or cancel to make changes.",
                    "cart_locked": True
                },
                "context": {
                    "guardrail_type": "hard_block",
                    "violation": "modify_locked_cart",
                    "attempted_action": action
                },
                "guardrail_violations": [f"Attempted to {action} on locked cart"]
            }

    if sub_intent == "execute_checkout":
        # HARD BLOCK: Must validate cart first
        cart_validated = state.get("cart_validated", False)

        if not cart_validated:
            logger.warning(
                "Hard block: Checkout blocked (cart not validated)",
                session_id=session_id
            )
            return False, {
                "action": "validation_required",
                "success": False,
                "data": {
                    "message": "Let me validate your cart first before we complete your order.",
                    "requires_validation": True
                },
                "context": {
                    "guardrail_type": "hard_block",
                    "violation": "checkout_without_validation"
                },
                "guardrail_violations": ["Attempted checkout without validation"]
            }

        # HARD BLOCK: Must authenticate if required
        must_authenticate = state.get("must_authenticate", False)
        user_authenticated = state.get("user_id") is not None

        if must_authenticate and not user_authenticated:
            logger.warning(
                "Hard block: Checkout blocked (authentication required)",
                session_id=session_id
            )
            return False, {
                "action": "authentication_required",
                "success": False,
                "data": {
                    "message": "I'll need your phone number to complete your order.",
                    "requires_auth": True
                },
                "context": {
                    "guardrail_type": "hard_block",
                    "violation": "checkout_without_auth"
                },
                "guardrail_violations": ["Attempted checkout without authentication"]
            }

    # All guardrails passed - proceed to agent routing
    logger.debug(
        "Guardrails passed",
        session_id=session_id,
        sub_intent=sub_intent
    )
    return True, None


async def food_ordering_agent(
    user_message: str,
    state: FoodOrderingState
) -> Dict[str, Any]:
    """
    Main entry point for food ordering sub-graph.

    Orchestrates:
    1. Sub-intent classification with entity extraction
    2. Entity validation and collection
    3. Deterministic routing to specialized agent
    4. ActionResult formatting for Response Agent

    Args:
        user_message: User's current message
        state: Current food ordering state

    Returns:
        ActionResult dict for Response Agent
    """
    session_id = state.get("session_id", "unknown")

    logger.info(
        "Food ordering sub-graph executing",
        session_id=session_id,
        message=user_message[:50]
    )

    # Step 1: Classify sub-intent and extract entities
    try:
        classification = await classify_sub_intent(user_message, state)

        logger.info(
            "Sub-intent classified",
            session_id=session_id,
            sub_intent=classification.sub_intent,
            confidence=classification.confidence,
            entities=classification.entities
        )

    except Exception as e:
        logger.error(
            "Classification failed",
            session_id=session_id,
            error=str(e),
            exc_info=True
        )
        return {
            "action": "classification_error",
            "success": False,
            "data": {
                "message": "I'm having trouble understanding your request. Could you rephrase that?"
            },
            "context": {}
        }

    # Step 2: Merge entities with state context
    entities = merge_entities_from_state(classification.entities, state)

    logger.info(
        "Entities merged with state",
        session_id=session_id,
        merged_entities=entities
    )

    # Step 3: Validate entities and check for missing required fields
    # Pass merged entities to validation (includes pending entities from multi-turn collection)
    is_valid, missing_entities, clarification_question = validate_entities(
        classification, state, merged_entities=entities
    )

    if not is_valid:
        logger.info(
            "Missing required entities",
            session_id=session_id,
            missing=missing_entities,
            question=clarification_question
        )

        # Store already collected entities in state for multi-turn collection
        # This preserves item_name when we're asking for quantity
        pending_entities = {
            k: v for k, v in entities.items()
            if v is not None and k not in missing_entities
        }

        logger.info(
            "Storing pending entities for multi-turn collection",
            session_id=session_id,
            pending_entities=pending_entities,
            missing=missing_entities
        )

        # Update state with pending entities
        state["pending_entities"] = pending_entities
        state["entity_collection_step"] = missing_entities[0] if missing_entities else None
        state["current_sub_intent"] = classification.sub_intent

        # Sync to entity graph for persistent context tracking
        try:
            user_id = state.get("user_id")
            if user_id:
                from app.core.entity_graph_service import get_entity_graph_service
                graph_service = get_entity_graph_service()
                graph_service.set_active_intent(
                    user_id=user_id,
                    session_id=session_id,
                    sub_intent=classification.sub_intent,
                    entities=pending_entities,
                    entity_collection_step=missing_entities[0] if missing_entities else None
                )
                logger.debug(
                    "Synced active intent to graph",
                    user_id=user_id,
                    session_id=session_id,
                    sub_intent=classification.sub_intent
                )
        except Exception as e:
            logger.warning(
                "Failed to sync active intent to graph (non-blocking)",
                error=str(e)
            )

        # Return clarification request to Response Agent
        return {
            "action": "clarification_needed",
            "success": False,
            "data": {
                "message": clarification_question,
                "missing_entities": missing_entities,
                "sub_intent": classification.sub_intent,
                "pending_entities": pending_entities
            },
            "context": {
                "waiting_for": missing_entities,
                "sub_intent": classification.sub_intent,
                "pending_entities": pending_entities
            },
            # State updates for entity collection
            "entity_collection_step": missing_entities[0] if missing_entities else None,
            "pending_entities": pending_entities
        }

    # Step 3.5: Apply state-based guardrails (NEW!)
    should_proceed, override_result = apply_state_guardrails(
        classification, state, session_id
    )

    if not should_proceed:
        logger.info(
            "Guardrail triggered - returning override result",
            session_id=session_id,
            guardrail_type=override_result.get("context", {}).get("guardrail_type"),
            original_intent=classification.sub_intent
        )
        return override_result

    # Step 4: Route to appropriate agent (deterministic - no LLM)
    try:
        agent_function = route_to_agent(classification)

        logger.info(
            "Routing to agent",
            session_id=session_id,
            sub_intent=classification.sub_intent,
            agent=agent_function.__name__
        )

    except ValueError as e:
        logger.error(
            "Routing failed - no agent for sub-intent",
            session_id=session_id,
            sub_intent=classification.sub_intent,
            error=str(e)
        )
        return {
            "action": "routing_error",
            "success": False,
            "data": {
                "message": "I'm not sure how to help with that. Could you try asking differently?"
            },
            "context": {}
        }

    # Step 4.5: Configure ReAct mode for the selected agent
    # Map sub_intent to agent name for react configuration
    agent_name_map = {
        "browse_menu": "menu_browsing",
        "discover_items": "menu_discovery",
        "manage_cart": "cart_management",
        "validate_order": "checkout_validator",
        "execute_checkout": "checkout_executor"
    }

    agent_name = agent_name_map.get(classification.sub_intent)
    if agent_name:
        from app.features.food_ordering.utils.state_helpers import configure_react_for_agent

        # Configure ReAct mode based on .env settings and A/B test percentage
        react_config = configure_react_for_agent(agent_name, state)

        # Apply configuration to state
        for key, value in react_config.items():
            state[key] = value  # type: ignore

        logger.info(
            "ReAct configuration applied",
            session_id=session_id,
            agent_name=agent_name,
            react_enabled=react_config.get("react_agent_enabled"),
            agent_mode=react_config.get("agent_mode")
        )

    # Step 5: Execute specialized agent
    try:
        agent_result = await agent_function(entities, state)

        logger.info(
            "Agent executed successfully",
            session_id=session_id,
            sub_intent=classification.sub_intent,
            action=agent_result.get("action"),
            success=agent_result.get("success")
        )

        # STATELESS ARCHITECTURE: Clear external state when action completes
        # Only clear if success=True AND no ongoing entity collection
        if agent_result.get("success") and not agent_result.get("entity_collection_step"):
            user_id = state.get("user_id")
            if user_id:
                try:
                    from app.core.entity_graph_service import get_entity_graph_service
                    graph_service = get_entity_graph_service()
                    graph_service.clear_active_intent(user_id, session_id)
                    logger.debug(
                        "Cleared active intent from external storage after successful completion",
                        session_id=session_id,
                        sub_intent=classification.sub_intent
                    )
                except Exception as e:
                    logger.warning(
                        "Failed to clear active intent from external storage (non-blocking)",
                        session_id=session_id,
                        error=str(e)
                    )

        # Add classification metadata
        agent_result.setdefault("context", {})
        agent_result["context"]["sub_intent"] = classification.sub_intent
        agent_result["context"]["confidence"] = classification.confidence

        return agent_result

    except Exception as e:
        logger.error(
            "Agent execution failed",
            session_id=session_id,
            sub_intent=classification.sub_intent,
            agent=agent_function.__name__,
            error=str(e),
            exc_info=True
        )
        return {
            "action": "agent_error",
            "success": False,
            "data": {
                "message": "I encountered an error processing your request. Please try again."
            },
            "context": {
                "error_agent": agent_function.__name__,
                "sub_intent": classification.sub_intent
            }
        }


__all__ = ["food_ordering_agent"]


# ============================================================================
# STANDALONE TEST - Run without main orchestration
# ============================================================================

if __name__ == "__main__":
    import asyncio
    import sys
    from app.features.food_ordering.state import FoodOrderingState

    async def test_food_ordering_flow():
        """
        Interactive test for food ordering conversation flow.

        Tests sub-intent classification and entity extraction without
        going through the main orchestration graph.

        Usage:
            python -m app.features.food_ordering.graph
        """

        # Initialize minimal state
        state: FoodOrderingState = {
            "session_id": "test-session-001",
            "restaurant_id": "test-restaurant",
            "cart_items": [],
            "cart_subtotal": 0.0,
            "cart_validated": False,
            "cart_locked": False,
            "user_id": None,
            "user_name": None,
            "order_type": None,
            "draft_order_id": None,
            "entity_collection_step": None,
            "must_authenticate": False,
        }

        print("=" * 60)
        print("🍽️  Food Ordering Test Console")
        print("=" * 60)
        print("Commands:")
        print("  'quit'  - Exit the test")
        print("  'state' - View current state")
        print("  'reset' - Reset cart and state")
        print("=" * 60)
        print("\nTest messages:")
        print("  - 'show me the menu'")
        print("  - 'I want to order two samosas'")
        print("  - 'vegetarian options'")
        print("  - 'add 3 butter chicken'")
        print("  - 'show my cart'")
        print("  - 'checkout'")
        print("=" * 60)

        while True:
            try:
                user_input = input("\n👤 You: ").strip()
            except EOFError:
                print("\nExiting...")
                break

            if user_input.lower() == 'quit':
                print("Exiting...")
                break

            if user_input.lower() == 'state':
                print(f"\n📋 Current State:")
                print(f"  Session ID: {state.get('session_id')}")
                print(f"  Cart Items: {len(state.get('cart_items', []))} items")
                for i, item in enumerate(state.get('cart_items', []), 1):
                    print(f"    {i}. {item.get('name', 'Unknown')} x{item.get('quantity', 1)} - ₹{item.get('price', 0)}")
                print(f"  Cart Total: ₹{state.get('cart_subtotal', 0)}")
                print(f"  Cart Validated: {state.get('cart_validated')}")
                print(f"  Cart Locked: {state.get('cart_locked')}")
                print(f"  Order Type: {state.get('order_type')}")
                print(f"  User ID: {state.get('user_id')}")
                continue

            if user_input.lower() == 'reset':
                state['cart_items'] = []
                state['cart_subtotal'] = 0.0
                state['cart_validated'] = False
                state['cart_locked'] = False
                state['order_type'] = None
                state['entity_collection_step'] = None
                print("✅ State reset!")
                continue

            if not user_input:
                continue

            try:
                print("\n⏳ Processing...")
                result = await food_ordering_agent(user_input, state)

                # Display classification results
                context = result.get('context', {})
                sub_intent = context.get('sub_intent', 'unknown')
                confidence = context.get('confidence', 0)

                print(f"\n📊 Classification:")
                print(f"  Sub-Intent: {sub_intent}")
                print(f"  Confidence: {confidence:.2f}")
                print(f"  Action: {result.get('action', 'unknown')}")
                print(f"  Success: {result.get('success', False)}")

                # Display response
                data = result.get('data', {})
                message = data.get('message', 'No response message')
                print(f"\n🤖 Bot: {message}")

                # Display additional data if present
                if 'menu_items' in data:
                    print(f"\n📜 Menu Items: {len(data['menu_items'])} items found")
                    for item in data['menu_items'][:5]:  # Show first 5
                        print(f"    - {item.get('name', 'Unknown')}: ₹{item.get('price', 0)}")
                    if len(data['menu_items']) > 5:
                        print(f"    ... and {len(data['menu_items']) - 5} more")

                if 'categories' in data:
                    print(f"\n📂 Categories: {data['categories']}")

                if 'cart_items' in data:
                    print(f"\n🛒 Cart Updated: {len(data['cart_items'])} items")

                # Update state based on result
                if result.get('success'):
                    if 'cart_items' in data:
                        state['cart_items'] = data['cart_items']
                    if 'cart_total' in data:
                        state['cart_subtotal'] = data['cart_total']
                    if 'cart_subtotal' in data:
                        state['cart_subtotal'] = data['cart_subtotal']
                    if 'cart_validated' in data:
                        state['cart_validated'] = data['cart_validated']
                    if 'order_type' in data:
                        state['order_type'] = data['order_type']

                # Handle missing entities
                if result.get('action') == 'clarification_needed':
                    missing = data.get('missing_entities', [])
                    print(f"\n⚠️  Missing entities: {missing}")
                    state['entity_collection_step'] = missing[0] if missing else None

            except Exception as e:
                print(f"\n❌ Error: {str(e)}")
                import traceback
                traceback.print_exc()

    # Run the async test
    print("\n🚀 Starting Food Ordering Test Console...")
    print("   (Make sure Redis is running and menu cache is loaded)\n")

    try:
        asyncio.run(test_food_ordering_flow())
    except KeyboardInterrupt:
        print("\n\nTest interrupted. Goodbye!")

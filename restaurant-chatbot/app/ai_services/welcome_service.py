"""
AI-Powered Welcome Message Service
===================================
Generates personalized welcome messages based on multi-tier identity recognition.

Tier 1 (Anonymous): Generic welcome with service overview
Tier 2 (Recognized Device): Welcome back message
Tier 3 (Authenticated): Fully personalized with name, favorites, history
"""

from typing import Dict, Any, Optional, List
import structlog
from langchain_core.messages import SystemMessage, HumanMessage

from app.ai_services.agent_llm_factory import get_llm_for_agent

logger = structlog.get_logger("services.welcome")


class WelcomeMessageService:
    """
    Service for generating AI-powered personalized welcome messages.

    Uses LLM to create contextual greetings based on:
    - User recognition tier (1/2/3)
    - Time of day
    - User preferences and history
    - Restaurant name
    """

    def __init__(self):
        """Initialize welcome message service."""
        pass

    async def generate_welcome(
        self,
        tier: int,
        restaurant_name: str,
        time_greeting: str,
        user_name: Optional[str] = None,
        personalization: Optional[Dict[str, Any]] = None,
        waiter_name: Optional[str] = None,
        has_cart_items: bool = False
    ) -> str:
        """
        Generate AI-powered welcome message based on tier.

        Args:
            tier: Recognition tier (1=anonymous, 2=device, 3=authenticated)
            restaurant_name: Restaurant name from database
            time_greeting: Time-based greeting (Good morning/afternoon/evening)
            user_name: User's name (for Tier 3)
            personalization: Personalization data from identity service

        Returns:
            AI-generated welcome message
        """

        personalization = personalization or {}

        # Get or assign waiter name for personalization
        if not waiter_name:
            import random
            from app.core.config import config
            waiter_name = random.choice(config.waiter_names_list)

        logger.info(
            "Generating AI-powered welcome message",
            tier=tier,
            has_user_name=bool(user_name),
            has_personalization=bool(personalization),
            waiter_name=waiter_name,
            has_cart_items=has_cart_items
        )

        # Get LLM for welcome generation (lower temperature for consistency)
        llm = get_llm_for_agent("greeting_agent", temperature=0.2)

        # Build system prompt based on tier
        system_prompt = self._build_system_prompt(
            tier=tier,
            restaurant_name=restaurant_name,
            time_greeting=time_greeting,
            user_name=user_name,
            personalization=personalization,
            waiter_name=waiter_name,
            has_cart_items=has_cart_items
        )

        # Build context message
        context_parts = []

        if user_name:
            context_parts.append(f"User name: {user_name}")

        # Add personalization context
        if personalization:
            dietary = personalization.get("preferences", {}).get("dietary_restrictions", [])
            if dietary:
                context_parts.append(f"Dietary restrictions: {', '.join(dietary)}")

            favorites = personalization.get("favorite_items", [])
            if favorites:
                context_parts.append(f"Favorite items: {', '.join(favorites[:3])}")

            recent_orders = personalization.get("recent_orders", [])
            if recent_orders:
                context_parts.append(f"Recent orders: {len(recent_orders)} previous order(s)")

        context = "\n".join(context_parts) if context_parts else "No additional context"

        # Generate welcome message
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Generate a welcome message with this context:\n{context}")
        ]

        try:
            response = await llm.ainvoke(messages)
            welcome_message = response.content.strip()

            logger.info(
                "AI-powered welcome generated",
                tier=tier,
                message_length=len(welcome_message)
            )

            return welcome_message

        except Exception as e:
            logger.error(
                "Failed to generate AI welcome, using fallback",
                tier=tier,
                error=str(e)
            )

            # Fallback to tier-based templates
            return self._get_fallback_welcome(tier, restaurant_name, time_greeting, user_name)

    def _build_system_prompt(
        self,
        tier: int,
        restaurant_name: str,
        time_greeting: str,
        user_name: Optional[str],
        personalization: Dict[str, Any],
        waiter_name: str,
        has_cart_items: bool = False
    ) -> str:
        """Build system prompt based on tier."""

        base_instructions = f"""You are {waiter_name}, a friendly virtual waiter at {restaurant_name}.

Your task is to greet customers naturally - like a real person having a conversation.

Current time greeting: {time_greeting}

**Your Greeting Style:**
- Talk like a real person having a natural conversation
- Introduce yourself as "your waiter for today" - creates personal connection
- Show you care: "Hope you're doing good", "How's your day going?"
- Ask what they're in the mood for - makes it conversational
- Mention the food naturally: "we have a great selection of food"
- Weave in your capabilities naturally in the flow of conversation
- Keep it flowing and conversational (2-4 sentences), not short and choppy
- Sound like a friendly person, not a service robot

**Language Guidelines:**
- GOOD words: "explore", "browse", "check out", "place an order", "looking for", "interested in"
- AVOID overly excited words: "thrilled", "I'm so excited" (sounds fake)
- AVOID overly casual slang: "dive into", "picks" (use "options" or "choices" instead)
- Keep it natural and service-oriented, not robotic or overly enthusiastic
"""

        if has_cart_items:
            base_instructions += """
**IMPORTANT - EXISTING CART ITEMS:**
The user already has items in their cart from a previous session.
- You MUST acknowledge this: "I see you have some items in your cart from before."
- Ask if they want to review/checkout or keep browsing.
- Do NOT act like they are starting from scratch.
"""

        if tier == 1:
            # Anonymous user - introduce services
            return base_instructions + f"""

**TIER 1 - FIRST-TIME VISITOR**

This is a new customer you're greeting for the first time. Introduce yourself by name and make them feel welcome.

Your welcome should:
1. Start with the time greeting: "{time_greeting}"
2. Introduce yourself as "{waiter_name}, your waiter for today"
3. Show you care: "Hope you're doing good"
4. Ask what they're in the mood for
5. Mention the great food selection naturally
6. Let them know you can help with orders, reservations, questions - but weave it into conversation

**Example Format:**
"{time_greeting}! I'm {waiter_name}, your waiter for today. Hope you're doing good! What are you in the mood for? We have a great selection of food. I can also help answer any questions or help you make a reservation at our restaurant."

Generate a similar warm, natural greeting following this conversational flow.
"""

        elif tier == 2:
            # Recognized device - welcome back
            return base_instructions + f"""

**TIER 2 - RETURNING CUSTOMER**

This is someone who's been here before - greet them like a regular!

Your welcome should:
1. Start with the time greeting: "{time_greeting}"
2. Warmly acknowledge they're back - like you're happy to see a familiar face
3. Be casual and welcoming, like greeting a neighbor

**Good Examples:**
- "{time_greeting}! Great to see you back at {restaurant_name}. What sounds good today?"
- "{time_greeting}! Welcome back - ready to order another round, or want to try something new?"
- "{time_greeting}! Nice to have you back with us. Want your usual, or feeling adventurous today?"

Generate a warm welcome-back message that makes them feel like a valued regular.
"""

        else:  # tier == 3
            # Authenticated user - fully personalized
            has_favorites = bool(personalization.get("favorite_items"))
            has_history = personalization.get("has_order_history", False)

            personalization_hints = []
            if user_name:
                personalization_hints.append(f"Address them by name: {user_name}")
            if has_favorites:
                favorites = personalization.get("favorite_items", [])
                personalization_hints.append(f"Mention their favorites: {', '.join(favorites[:2])}")
            if has_history:
                personalization_hints.append("Reference their order history")

            hints_text = "\n".join([f"- {hint}" for hint in personalization_hints]) if personalization_hints else "- Just use their name warmly"

            return base_instructions + f"""

**TIER 3 - VALUED REGULAR**

This is a known customer - greet them by name like an old friend!

Your welcome should:
1. Start with the time greeting: "{time_greeting}"
2. Personalize using their name and what you know about them:
{hints_text}
3. Sound genuinely happy to see them - like greeting a friend you know well
4. Reference their preferences naturally in conversation

**Good Examples:**
- With favorites: "{time_greeting}, {user_name}! So good to see you. In the mood for your favorite Margherita, or shall I show you what's new?"
- With history: "{time_greeting}, {user_name}! Welcome back - you loved the pasta last time, want to go with that again or try something different?"
- Simple: "{time_greeting}, {user_name}! Always a pleasure. What looks good to you today?"

Generate a warm, personalized greeting that makes them feel genuinely welcomed and valued.
"""

    def _get_fallback_welcome(
        self,
        tier: int,
        restaurant_name: str,
        time_greeting: str,
        user_name: Optional[str]
    ) -> str:
        """Get fallback welcome if AI generation fails."""

        if tier == 1:
            return (
                f"{time_greeting}! Welcome to {restaurant_name} - "
                "I'm excited to help you explore our menu. Looking for something specific, "
                "or want me to suggest some favorites?"
            )

        elif tier == 2:
            return (
                f"{time_greeting}! Great to see you back at {restaurant_name}. "
                "What sounds good today?"
            )

        else:  # tier == 3
            if user_name:
                return (
                    f"{time_greeting}, {user_name}! "
                    "Always a pleasure. What looks good to you today?"
                )
            else:
                return (
                    f"{time_greeting}! Nice to have you back with us. "
                    "What would you like today?"
                )


# Global service instance
welcome_service = WelcomeMessageService()

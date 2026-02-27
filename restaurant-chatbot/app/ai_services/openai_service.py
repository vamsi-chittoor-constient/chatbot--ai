"""
OpenAI Integration Service
==========================
Low-temperature GPT-4o for reliable AI operations with strong context understanding

Circuit Breaker Protection:
- Automatically fails fast when OpenAI API is down
- Prevents cascading failures
- Auto-recovery after 2 minutes
"""

import json
from typing import Dict, List, Any, Optional
import pybreaker

try:
    from openai import AsyncOpenAI
except ImportError:
    raise ImportError("OpenAI package not found. Install with: pip install openai")

import structlog
from app.core.config import config
from app.services.circuit_breaker_service import openai_breaker
from app.ai_services.llm_manager import get_llm_manager
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

logger = structlog.get_logger("services.openai")


class OpenAIService:
    """
    OpenAI integration service for restaurant AI assistant.

    Now uses Unified LLM Manager for all requests, providing:
    - 20-account load balancing
    - Per-model resource tracking
    - Cooldown mechanism
    - Retry queue for concurrent users
    """

    def __init__(self):
        # Get unified LLM manager instance
        self.llm_manager = get_llm_manager()

        # Purpose-specific models for optimal cost/accuracy balance
        self.intent_model = config.INTENT_CLASSIFICATION_MODEL  # Critical - use gpt-4o for accuracy
        self.entity_model = config.ENTITY_EXTRACTION_MODEL      # Can use cheaper model
        self.clarification_model = config.ENTITY_EXTRACTION_MODEL  # Can use cheaper model

        # Legacy support
        self.model = config.PRIMARY_LLM_MODEL

        self.temperature = 0.1  # Low temperature for reduced hallucinations
        self.max_tokens = 1500  # Sufficient for restaurant conversations
        self.timeout = 30  # 30 second timeout

        logger.info(
            f"OpenAI service initialized with Unified LLM Manager",
            intent_model=self.intent_model,
            entity_model=self.entity_model,
            temperature=self.temperature,
            total_accounts=len(self.llm_manager.accounts)
        )

    def _dict_messages_to_langchain(self, messages: List[Dict]) -> List:
        """
        Convert dict messages to LangChain message format.

        Args:
            messages: List of message dictionaries with 'role' and 'content'

        Returns:
            List of LangChain message objects
        """
        langchain_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                langchain_messages.append(SystemMessage(content=content))
            elif role == "assistant":
                langchain_messages.append(AIMessage(content=content))
            else:  # user or any other role
                langchain_messages.append(HumanMessage(content=content))

        return langchain_messages

    @openai_breaker
    async def _call_openai_api(
        self,
        messages: List[Dict],
        model: Optional[str] = None,
        response_format: Optional[Dict] = None,
        temperature: Optional[float] = None
    ):
        """
        OpenAI API call via Unified LLM Manager with circuit breaker.

        Now routes through 20-account manager for load balancing.
        Raises pybreaker.CircuitBreakerError when circuit is OPEN.

        Args:
            messages: List of message dictionaries
            model: Optional model override (uses self.model if not specified)
            response_format: Optional response format specification
            temperature: Optional temperature override

        Returns:
            LLM response (converted back to OpenAI format for compatibility)
        """
        # Convert dict messages to LangChain format
        langchain_messages = self._dict_messages_to_langchain(messages)

        # Use specified model or default
        model_to_use = model or self.model
        temp_to_use = temperature if temperature is not None else self.temperature

        # Call unified LLM manager
        response = await self.llm_manager.ainvoke(
            messages=langchain_messages,
            model=model_to_use,
            temperature=temp_to_use
        )

        # Convert LangChain response back to OpenAI-like format for compatibility
        # This allows existing code to work without changes
        class OpenAICompatibleResponse:
            def __init__(self, content):
                self.choices = [type('obj', (object,), {
                    'message': type('obj', (object,), {
                        'content': content
                    })()
                })()]

        return OpenAICompatibleResponse(response.content)

    def _prefilter_intent_analysis(
        self,
        message: str,
        conversation_context: Optional[List[Dict]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Fast rule-based pre-filter for high-priority intent patterns.
        Returns intent immediately if matched, None if LLM should handle it.

        This ensures critical patterns (capability questions, OTPs, etc.) are
        handled with 100% reliability and zero LLM cost.
        """
        message_lower = message.lower().strip()

        # Get last assistant message for context-aware detection
        last_assistant_msg = ""
        if conversation_context:
            for msg in reversed(conversation_context):
                if msg.get("role") == "assistant":
                    last_assistant_msg = msg.get("content", "").lower()
                    break

        # PRIORITY 1: Capability questions (most specific patterns)
        capability_phrases = [
            "what can you do",
            "what can you help",
            "what can you help me with",
            "what are your capabilities",
            "what do you offer",
            "what services do you provide",
            "what services do you offer",
            "how can you help",
            "how can you assist",
            "what are you capable of",
            "what can i do here",
            "what features do you have"
        ]
        if any(phrase in message_lower for phrase in capability_phrases):
            logger.info("Pre-filter matched: capability question")
            return {
                "intent": "general_question",
                "confidence": 0.95,
                "entities": {},
                "context_needed": [],
                "user_sentiment": "neutral",
                "complexity": "simple",
                "requires_clarification": False,
                "pre_filter_matched": True
            }

        # PRIORITY 2: OTP/Verification code context detection
        # If assistant just asked for OTP/code and user provides 4-6 digit number
        otp_request_phrases = ["otp", "verification code", "6-digit", "4-digit", "code", "enter the code", "share the code"]
        if any(phrase in last_assistant_msg for phrase in otp_request_phrases):
            # Check if message is just a number (4-6 digits)
            if message.strip().isdigit() and 4 <= len(message.strip()) <= 6:
                # Determine ongoing intent from context
                ongoing_intent = "booking_request"  # Default assumption
                for msg in reversed(conversation_context or []):
                    if msg.get("role") == "user":
                        prev_msg_lower = msg.get("content", "").lower()
                        if any(word in prev_msg_lower for word in ["book", "table", "reservation"]):
                            ongoing_intent = "booking_request"
                            break
                        elif any(word in prev_msg_lower for word in ["order", "food", "menu"]):
                            ongoing_intent = "order_request"
                            break

                logger.info(f"Pre-filter matched: OTP code (continuing {ongoing_intent})")
                return {
                    "intent": ongoing_intent,
                    "confidence": 0.95,
                    "entities": {"verification_code": message.strip()},
                    "context_needed": [],
                    "user_sentiment": "neutral",
                    "complexity": "simple",
                    "requires_clarification": False,
                    "pre_filter_matched": True
                }

        # PRIORITY 3: Hours inquiry (very specific patterns)
        hours_phrases = [
            "what time do you open",
            "what time do you close",
            "when do you open",
            "when do you close",
            "are you open",
            "opening hours",
            "business hours",
            "operating hours",
            "open tomorrow",
            "close today",
            "what are your hours"
        ]
        if any(phrase in message_lower for phrase in hours_phrases):
            logger.info("Pre-filter matched: hours_inquiry")
            return {
                "intent": "hours_inquiry",
                "confidence": 0.95,
                "entities": {},
                "context_needed": [],
                "user_sentiment": "neutral",
                "complexity": "simple",
                "requires_clarification": False,
                "pre_filter_matched": True
            }

        # PRIORITY 4: Location/Contact inquiry
        contact_phrases = [
            "phone number",
            "contact number",
            "how to reach",
            "how can i reach",
            "how do i contact",
            "what's your number",
            "whats your number",
            "email address",
            "your email"
        ]
        location_words = ["where are you", "your location", "your address", "directions to"]

        if any(phrase in message_lower for phrase in contact_phrases):
            logger.info("Pre-filter matched: location_inquiry (contact)")
            return {
                "intent": "location_inquiry",
                "confidence": 0.95,
                "entities": {"info_type": "contact"},
                "context_needed": [],
                "user_sentiment": "neutral",
                "complexity": "simple",
                "requires_clarification": False,
                "pre_filter_matched": True
            }

        if any(phrase in message_lower for phrase in location_words):
            logger.info("Pre-filter matched: location_inquiry (address)")
            return {
                "intent": "location_inquiry",
                "confidence": 0.9,
                "entities": {"info_type": "location"},
                "context_needed": [],
                "user_sentiment": "neutral",
                "complexity": "simple",
                "requires_clarification": False,
                "pre_filter_matched": True
            }

        # PRIORITY 5: Pure greetings (only if no other content)
        # Simple greetings without questions or requests
        simple_greetings = ["hi", "hello", "hey", "yo", "sup"]
        greeting_phrases = ["good morning", "good afternoon", "good evening", "good night"]

        # Check if message is a simple greeting or greeting phrase
        is_simple_greeting = message_lower.strip() in simple_greetings
        is_greeting_phrase = any(phrase in message_lower for phrase in greeting_phrases)
        has_question_words = any(q in message_lower for q in ["what", "how", "why", "when", "where", "can", "do"])

        # Pure greeting: short message that's just a greeting without questions
        if (is_simple_greeting or is_greeting_phrase) and not has_question_words and len(message.split()) <= 3:
            logger.info("Pre-filter matched: greeting")
            return {
                "intent": "greeting",
                "confidence": 0.95,
                "entities": {},
                "context_needed": [],
                "user_sentiment": "positive",
                "complexity": "simple",
                "requires_clarification": False,
                "pre_filter_matched": True
            }

        # No match - let LLM handle it
        return None

    async def analyze_intent(
        self,
        message: str,
        conversation_context: Optional[List[Dict]] = None,
        additional_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze user message intent with conversation context and user memory
        Returns structured intent analysis for the orchestrator

        Hybrid Approach:
        1. Fast rule-based pre-filter for high-priority patterns (capability questions, OTPs, etc.)
        2. LLM analysis for complex/ambiguous cases
        3. Fallback to simple rules if OpenAI is down
        """

        # STEP 1: Try rule-based pre-filter first
        prefilter_result = self._prefilter_intent_analysis(message, conversation_context)
        if prefilter_result is not None:
            logger.info(
                "Intent pre-filter matched",
                intent=prefilter_result.get("intent"),
                confidence=prefilter_result.get("confidence")
            )
            return prefilter_result

        # STEP 2: Pre-filter didn't match - use LLM for complex analysis
        logger.info("Pre-filter no match - using LLM analysis")

        # Build context-aware prompt
        context_str = ""
        if conversation_context:
            recent_messages = conversation_context[-5:]  # Last 5 messages for context
            context_str = "\n".join([
                f"{'User' if msg.get('role') == 'user' else 'Assistant'}: {msg.get('content', '')}"
                for msg in recent_messages
            ])

        # Add additional context (user memory, preferences, etc.)
        if additional_context:
            context_str += f"\n\n{additional_context}"

        system_prompt = """You are an intent analysis AI for a restaurant assistant.
Analyze the user's message and return a JSON response with:

1. "intent" - primary intent (greeting, menu_inquiry, order_request, booking_request, booking_management, payment_question, complaint, feedback, satisfaction_survey, faq, policy_inquiry, hours_inquiry, location_inquiry, general_question, support_request)
2. "confidence" - confidence score (0.0-1.0)
3. "entities" - extracted entities like dates, times, food items, quantities, preferences
4. "context_needed" - what additional information is required
5. "user_sentiment" - positive, neutral, negative, confused
6. "complexity" - simple, moderate, complex
7. "requires_clarification" - true/false if message is unclear

================================================================================
CRITICAL: requires_clarification Rules
================================================================================

Set requires_clarification = TRUE only when:
  [!] You CANNOT determine what the user wants to do (intent is unclear)
  [!] Examples: "I need something", "help", "yes", "okay", "that one"

Set requires_clarification = FALSE when:
  [OK] Intent is CLEAR, even if specific details are missing
  [OK] The intent has a dedicated agent that will collect missing details progressively

Examples that do NOT require clarification (intent is clear):
  - "I want to order food" → intent=order_request (CLEAR), missing food_items (agent will ask)
  - "Book a table" → intent=booking_request (CLEAR), missing date/time/party_size (agent will ask)
  - "Show me the menu" → intent=menu_inquiry (CLEAR), no missing entities needed
  - "I want to make a reservation for tomorrow" → intent=booking_request (CLEAR), missing time/party_size (agent will ask)
  - "Order pizza" → intent=order_request (CLEAR), missing quantity/toppings (agent will ask)

Examples that DO require clarification (intent is unclear):
  - "I need something" → Cannot determine what they want (order? booking? info?)
  - "Yes" → No context about what they're confirming
  - "That one" → Unclear what they're referring to
  - "Help" → Could be greeting, support_request, or asking capabilities

KEY PRINCIPLE: If you can identify WHAT the user wants to do (the action/intent),
set requires_clarification=false. The specialized agent will handle missing details.

================================================================================

INTENT CLASSIFICATION RULES:

**GREETING & CAPABILITY QUESTIONS** (HIGHEST PRIORITY - check these first):
- Use "greeting" for ONLY greetings: "hello", "hi", "hey", "good morning/afternoon/evening", "how are you"
- Use "general_question" for capability/help questions: "what can you do", "what can you help me with", "how can you help", "what are your capabilities", "what do you offer", "what services do you provide", "help me", "assist me"

**PRIORITY RULE FOR MIXED MESSAGES:**
If a message contains BOTH greeting AND capability question (e.g., "hi, what can you do"), use "general_question" because the user is asking for information, not just saying hello.

- Use "complaint" for negative feedback, problems, issues, dissatisfaction (words like: complain, problem, issue, wrong, bad, terrible, awful, disappointed, unhappy)
- Use "feedback" for general reviews, opinions, experiences (words like: feedback, review, opinion, experience, thoughts)
- Use "satisfaction_survey" for ratings, scores, recommendations (words like: rating, rate, score, recommend, satisfaction)
- Use "faq" for questions seeking information (words like: what, how, why, when, where, can I, do you)
- Use "policy_inquiry" for rules, policies, procedures (words like: policy, rule, cancel, refund, terms, procedure)
- Use "hours_inquiry" SPECIFICALLY for questions about operating hours, opening times, closing times (words/phrases like: "what time", "when do you open", "when do you close", "are you open", "hours", "open tomorrow", "close today", "opening hours", "business hours")
- Use "location_inquiry" for location/address/contact (words like: where, location, address, directions, "phone number", "contact number", "email", "how to reach")
- **Use "menu_inquiry" for menu browsing, recommendations, favorites, popular items** (keywords: "what do you have", "show menu", "what's on the menu", "recommendations", "what's popular", "best dishes", "favorites", "favourite", "specialty", "signature dish", "top items", "most popular", "what do you recommend", "menu items", "what food do you have", "what dishes", "browse menu", "see menu", "looking at the menu")
- **CRITICAL - BOOKING vs ORDERING DISTINCTION**:
  * Use "booking_request" for table reservations/seating (keywords: "book a table", "reserve a table", "make a reservation", "table for X people", "table for dinner", "I need a table", "book/reserve seating", "reservation for", "book two tables", "reserve tables")
  * Use "order_request" for food/menu items (keywords: "order food", "I want to order", "get me", "I'll have", "can I get", specific dish names, "add to cart", "I want [food item]", "order two pizzas")
  * **CRITICAL - DISH NAME DETECTION**: If the user mentions what appears to be a specific dish name (e.g., "Paneer Butter Masala", "Chicken Tikka", "Margherita Pizza", "Biryani"), especially with Indian/restaurant food names, this is ALWAYS "order_request", even without explicit ordering keywords like "I want" or "order". The user mentioning a dish name indicates ordering intent.
  * **DISAMBIGUATION RULE**: If message contains BOTH "book/reserve" AND "table/tables/seating/reservation"  booking_request. If "book/order" appears with food/menu/dish items  order_request.
  * Examples:
    - "book two tables for tomorrow" = booking_request
    - "order two pizzas" = order_request
    - "I want to book a table for 4pm" = booking_request
    - "Paneer Butter Masala" = order_request (dish name indicates ordering)
    - "Chicken Tikka Masala" = order_request (dish name indicates ordering)
    - "2 Biryani" = order_request (dish name with quantity)
- Use "booking_management" for VIEWING, CANCELING, or MODIFYING existing bookings (words/phrases: "show my bookings", "view reservations", "view my reservations", "cancel my booking", "change my reservation", "modify booking", "reschedule", "my bookings")
- Use "general_question" ONLY for truly unclear/ambiguous requests that don't fit any specific category
- Use "support_request" for technical issues, system problems, or help with using the restaurant assistant (words like: "not working", "error", "bug", "broken", "help me with", "how do I use this")
- **IMPORTANT**: Menu-related queries (favorites, recommendations, popular items, what's on menu) should ALWAYS be "menu_inquiry", NEVER "general_question" or "support_request"

**CRITICAL**: If user asks "what time do you open", "when do you close", "are you open tomorrow" - this is ALWAYS "hours_inquiry", NOT "menu_inquiry" or "faq"!
If user asks for "phone number", "contact", "email" - this is ALWAYS "location_inquiry", NOT "faq"!
**BOOKING vs FOOD ORDERING**: "book/reserve [table/tables/seating/reservation]" = booking_request | "order/get/I'll have [food item]" = order_request

**CONTEXT-AWARE INTENT DETECTION**:
- If the assistant just asked for specific information (date, time, phone number, name, OTP code, verification code, etc.), and the user provides ONLY that information without any other words, the intent should REMAIN the same as the ongoing conversation intent, NOT change to "greeting", "general_question", or any other intent
- Examples:
  - Assistant asks "What's your phone number?"  User says "9566070120"  Intent is STILL booking_request (continuing the booking)
  - Assistant asks "What time?"  User says "6 pm"  Intent is STILL booking_request
  - Assistant asks "How many people?"  User says "4"  Intent is STILL booking_request
  - **Assistant asks "Please share the 6-digit code"  User says "995286"  Intent is STILL booking_request (OTP verification is part of booking)**
  - **Assistant asks "Enter verification code"  User says "123456"  Intent stays with the active conversation (booking/order/etc.)**
- **CRITICAL OTP/VERIFICATION CODE RULE**: If the user provides a 4-6 digit number right after the assistant asked for a verification code or OTP code, this is ALWAYS part of the ongoing conversation's intent (booking_request, order_request, etc.), NEVER a new intent!
- If the user provides a 10-digit number (phone number) in a booking context, it's part of the booking flow, NOT a greeting
- **CRITICAL**: When the last assistant message asks a question, the user's answer continues that conversation's intent - DO NOT change the intent!

Be precise and context-aware."""

        user_prompt = f"""
Conversation Context:
{context_str}

Current Message: {message}

Analyze this message considering the full conversation context."""

        try:
            from app.ai_services.models import IntentAnalysis

            # Convert messages to LangChain format
            langchain_messages = self._dict_messages_to_langchain([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ])

            # Get LLM with structured output (uses Pydantic for validation)
            structured_llm = await self.llm_manager.get_llm_with_structured_output(
                schema=IntentAnalysis,
                model=self.intent_model,
                temperature=self.temperature
            )

            # Invoke with type-safe structured response
            response: IntentAnalysis = await structured_llm.ainvoke(langchain_messages)

            # Log successful analysis
            logger.info(
                "Intent analysis completed (structured output)",
                intent=response.intent,
                confidence=response.confidence,
                message_length=len(message)
            )

            # Return as dict for backward compatibility
            return response.model_dump()

        except pybreaker.CircuitBreakerError:
            logger.warning("OpenAI circuit breaker OPEN - using fallback intent analysis")
            return self._fallback_intent_analysis(message)

        except Exception as e:
            logger.error(f"Intent analysis failed: {str(e)}")
            return self._fallback_intent_analysis(message)

    async def generate_clarification_question(
        self,
        unclear_message: str,
        conversation_context: List[Dict],
        missing_info: Optional[List[str]] = None
    ) -> str:
        """
        Generate contextual clarification questions when user intent is unclear

        Circuit Breaker Protected:
        - Falls back to generic clarification if OpenAI is down
        """

        context_str = ""
        if conversation_context:
            recent_messages = conversation_context[-3:]  # Last 3 messages for context
            context_str = "\n".join([
                f"{'User' if msg.get('role') == 'user' else 'Assistant'}: {msg.get('content', '')}"
                for msg in recent_messages
            ])

        missing_str = ""
        if missing_info:
            missing_str = f"\nSpecifically missing: {', '.join(missing_info)}"

        system_prompt = """You are a helpful restaurant AI assistant. The user's message is unclear or incomplete.
Generate a friendly, specific clarification question that:

1. Acknowledges what you understood
2. Asks for the specific missing information
3. Maintains a warm, restaurant service tone
4. Uses conversation context to be more specific

CRITICAL GUARDRAILS - NEVER VIOLATE THESE:

NEVER DO THIS:
- DO NOT suggest specific menu items (burgers, ice cream, pasta, drinks, etc.)
- DO NOT use examples of food items from general knowledge
- DO NOT mention specific dishes, drinks, desserts, or menu categories by name
- DO NOT say things like "we have burgers" or "our ice cream" - you don't know what's in the menu!

ALWAYS DO THIS:
- DO suggest they browse the menu or search for what they're looking for
- DO ask about general characteristics (spicy? vegetarian? cold? hot? heavy? light?)
- DO ask them to describe what kind of food they want
- DO guide them to use menu browsing or search features

WHY: We don't know what's in this restaurant's menu database. NEVER assume menu items exist.
Only specialist agents with database access can suggest specific items.

Keep it concise and natural. Don't repeat information already established in the conversation."""

        user_prompt = f"""
Conversation Context:
{context_str}

Unclear Message: {unclear_message}{missing_str}

Generate a helpful clarification question."""

        try:
            # Call via unified LLM manager (now routed through 20 accounts)
            response = await self._call_openai_api(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=self.clarification_model,
                temperature=0.2  # Slightly higher for natural language generation
            )

            content = response.choices[0].message.content
            if content is None:
                raise ValueError("OpenAI returned empty response")
            clarification = content.strip()

            logger.info("Clarification question generated", question_length=len(clarification))

            return clarification

        except pybreaker.CircuitBreakerError:
            logger.warning("OpenAI circuit breaker OPEN - using generic clarification")
            return "I'd like to help you! Could you please provide a bit more detail about what you're looking for?"

        except Exception as e:
            logger.error(f"Failed to generate clarification question: {str(e)}")
            return "I'd like to help you! Could you please provide a bit more detail about what you're looking for?"

    async def generate_response(
        self,
        intent: str,
        entities: Dict,
        conversation_context: List[Dict],
        agent_data: Optional[Dict] = None,
        business_context: Optional[Dict] = None
    ) -> str:
        """
        Generate contextual AI responses for the conversation
        """

        # Build conversation context
        context_str = ""
        if conversation_context:
            recent_messages = conversation_context[-7:]  # Last 7 messages
            context_str = "\n".join([
                f"{'User' if msg.get('role') == 'user' else 'Assistant'}: {msg.get('content', '')}"
                for msg in recent_messages
            ])

        # Build agent data context
        agent_str = ""
        if agent_data:
            agent_str = f"\nRelevant Information: {json.dumps(agent_data, indent=2)}"

        # Build business context
        business_str = ""
        if business_context:
            business_str = f"\nRestaurant Status: {json.dumps(business_context, indent=2)}"

        # Special handling for extraction tasks
        if intent == "extract_booking_entities" and entities.get("extraction_prompt"):
            system_prompt = "You are an expert at extracting booking information from restaurant conversations. Return only valid JSON."
            user_prompt = entities.get("extraction_prompt", "")
        else:
            system_prompt = f"""You are a helpful restaurant assistant. Be conversational and direct.

Intent: {intent}
Extracted Information: {json.dumps(entities, indent=2)}

Guidelines:
1. Be friendly but not overly polite - avoid "Could you please", "Let me know how I can assist", excessive "Thanks"
2. Get straight to the point - no unnecessary courtesies
3. Use casual, natural language like talking to a friend
4. Ask direct questions when you need info: "What time?" not "Could you please let me know what time?"
5. Don't repeat what the user just said back to them
6. Keep responses short and actionable
7. IMPORTANT: Only use a time-appropriate greeting ("Good morning", "Good afternoon", "Good evening") for the FIRST message in a conversation. Never repeat greetings if you've already greeted the user.
8. Sound helpful but not servile
9. Check conversation history - if you've already greeted the user earlier, don't greet them again
10. AVOID service-style endings like "Let me know if there's anything else you need", "How can I help you?", "Is there anything else?", "What else can I do for you?" - end responses naturally without these prompts

Be conversational, not corporate."""

            user_prompt = f"""
Conversation Context:
{context_str}{agent_str}{business_str}

IMPORTANT: Look at the conversation history above. If the user is providing partial information that builds on previous messages (like times, dates, names), connect it to what they said before. Don't ask for clarification if the context makes it clear.

Generate an appropriate response for this intent: {intent}"""

        try:
            # Call via unified LLM manager (now routed through 20 accounts)
            response = await self._call_openai_api(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=self.clarification_model,
                temperature=0.3  # Balanced creativity for natural responses
            )

            content = response.choices[0].message.content
            if content is None:
                raise ValueError("OpenAI returned empty response")
            generated_response = content.strip()

            logger.info(
                "Response generated successfully",
                intent=intent,
                response_length=len(generated_response)
            )

            return generated_response

        except Exception as e:
            logger.error(f"Failed to generate response: {str(e)}")
            return "I'm here to help! Let me know what you'd like to do - browse our menu, make a reservation, or place an order."

    async def extract_entities_advanced(
        self,
        message: str,
        intent: str,
        conversation_context: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Advanced entity extraction based on intent and conversation context
        """

        context_str = ""
        if conversation_context:
            recent_messages = conversation_context[-3:]
            context_str = "\n".join([
                f"{'User' if msg.get('role') == 'user' else 'Assistant'}: {msg.get('content', '')}"
                for msg in recent_messages
            ])

        entity_schemas = {
            "booking_request": ["date", "time", "party_size", "special_requests", "contact_info"],
            "order_request": ["food_items", "quantities", "customizations", "delivery_address", "special_instructions"],
            "menu_inquiry": ["food_categories", "dietary_restrictions", "allergies", "preferences"],
            "payment_question": ["payment_method", "amount", "order_id", "issue_type"],
            "general_question": ["topic", "specific_question", "urgency_level"]
        }

        expected_entities = entity_schemas.get(intent, ["general_info"])

        system_prompt = f"""Extract specific entities from the user message for intent: {intent}

Expected entities: {', '.join(expected_entities)}

Return a JSON object with extracted values. Use null for missing entities.
For dates/times, normalize to ISO format when possible.
For quantities, extract numbers and units.
Be precise and only extract what's clearly stated or strongly implied."""

        user_prompt = f"""
Conversation Context:
{context_str}

Current Message: {message}
Intent: {intent}

Extract entities as JSON."""

        try:
            # Call via unified LLM manager (now routed through 20 accounts)
            response = await self._call_openai_api(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=self.entity_model,
                temperature=0.1,  # Very low for precise extraction
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content
            if content is None:
                raise ValueError("OpenAI returned empty response")
            entities = json.loads(content)

            logger.info("Advanced entity extraction completed", intent=intent, entity_count=len(entities))

            return entities

        except Exception as e:
            logger.error(f"Advanced entity extraction failed: {str(e)}")
            return {}

    def _fallback_intent_analysis(self, message: str) -> Dict[str, Any]:
        """
        Fallback intent analysis when OpenAI fails
        Uses simple keyword matching with priority order
        """
        message_lower = message.lower()

        # Priority-based keyword detection (check specific intents first)
        # Check hours_inquiry FIRST (before greeting) - most specific
        if any(phrase in message_lower for phrase in ["what time", "when do you open", "when do you close", "are you open", "open tomorrow", "close today", "opening hours", "business hours"]):
            intent = "hours_inquiry"
            confidence = 0.9
        # Check location_inquiry (including contact) SECOND
        elif any(phrase in message_lower for phrase in ["phone number", "contact number", "email", "how to reach", "contact you"]) or \
             any(word in message_lower for word in ["location", "address", "where"]):
            intent = "location_inquiry"
            confidence = 0.9
        # Check booking management vs booking request THIRD
        elif any(phrase in message_lower for phrase in ["show my booking", "view my booking", "view booking", "show booking", "my booking", "my reservation", "cancel booking", "cancel reservation", "modify booking", "change booking", "reschedule"]):
            intent = "booking_management"
            confidence = 0.8
        elif any(word in message_lower for word in ["book", "table", "reservation", "seat"]):
            intent = "booking_request"
            confidence = 0.7
        # Check for dish names (common Indian restaurant dish patterns)
        elif any(word in message_lower for word in ["paneer", "tikka", "masala", "biryani", "naan", "curry", "dal", "samosa", "tandoori", "butter chicken", "korma", "vindaloo", "rogan", "kebab", "chana", "palak"]):
            intent = "order_request"
            confidence = 0.8
        elif any(word in message_lower for word in ["order", "buy", "purchase"]):
            intent = "order_request"
            confidence = 0.7
        # Check menu inquiry FOURTH
        elif any(word in message_lower for word in ["menu", "food", "eat", "dish", "cuisine"]):
            intent = "menu_inquiry"
            confidence = 0.7
        # Check support FIFTH
        elif any(word in message_lower for word in ["help", "support", "problem", "issue"]):
            intent = "support_request"
            confidence = 0.6
        # Check greeting LAST (most generic) - only if no "open", "time", "phone" etc
        elif any(word in message_lower for word in ["hi", "hello", "hey"]) and \
             not any(word in message_lower for word in ["open", "close", "time", "phone", "contact"]):
            intent = "greeting"
            confidence = 0.8
        else:
            intent = "general_question"
            confidence = 0.3

        return {
            "intent": intent,
            "confidence": confidence,
            "entities": {},
            "context_needed": [],
            "user_sentiment": "neutral",
            "complexity": "simple" if confidence > 0.7 else "moderate",
            "requires_clarification": confidence < 0.5
        }

    async def translate_query(self, text: str, target_language: str = "English") -> str:
        """
        Translate query to target language (default: English) for better RAG retrieval.
        Uses a lightweight, fast prompt specifically for search query translation.
        """
        if not text or len(text.strip()) < 2:
            return text

        # Simple prompt for direct translation
        system_prompt = f"Translate the following text to {target_language}. Return ONLY the translation, no explanation."
        
        try:
            # Call via unified LLM manager
            response = await self._call_openai_api(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                model=self.entity_model,  # Use cheap/fast model (gpt-4o-mini)
                temperature=0.0
            )
            
            content = response.choices[0].message.content
            if content:
                translation = content.strip()
                logger.debug("query_translated", original=text, translation=translation, target=target_language)
                return translation
            return text
            
        except Exception as e:
            logger.error(f"Translation failed: {str(e)}")
            return text

    async def health_check(self) -> bool:
        """
        Test LLM Manager connectivity and availability
        """
        try:
            # Call via unified LLM manager to test all accounts
            response = await self._call_openai_api(
                messages=[{"role": "user", "content": "Hello"}],
                model=self.model,
                temperature=0.1
            )

            if response and response.choices:
                logger.info("LLM Manager health check passed")
                return True

            return False

        except Exception as e:
            logger.error(f"LLM Manager health check failed: {str(e)}")
            return False


# Global service instance
openai_service = OpenAIService()

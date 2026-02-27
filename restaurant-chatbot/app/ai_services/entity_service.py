"""
Entity Extraction Service
========================
Advanced entity extraction that works across conversation history
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import structlog

from app.ai_services.openai_service import openai_service

logger = structlog.get_logger("services.entity")


class ConversationEntityExtractor:
    """
    Extracts and maintains entities across entire conversations
    """

    def __init__(self):
        self.entity_types = {
            "booking": ["date", "time", "party_size", "name", "phone", "special_requests"],
            "order": ["items", "quantities", "modifications", "order_type", "address"],
            "menu": ["category", "dietary_restrictions", "preferences"],
            "payment": ["amount", "method", "tip"],
            "contact": ["name", "phone", "email"],
            "temporal": ["date", "time", "duration"],
            "location": ["address", "area", "landmark"]
        }

    async def extract_conversation_entities(
        self,
        conversation_context: List[Dict[str, Any]],
        current_message: str,
        intent: str,
        excluded_phones: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Extract entities from entire conversation history + current message

        Args:
            conversation_context: Previous messages in conversation
            current_message: Current user message
            intent: Detected intent
            excluded_phones: Phone numbers to exclude (e.g., restaurant phone)

        Returns:
            Dictionary of extracted entities
        """
        try:
            # Build conversation text
            conversation_text = self._build_conversation_text(conversation_context, current_message)

            # Get relevant entity types based on intent
            relevant_entity_types = self._get_relevant_entity_types(intent)

            # Extract entities using GPT-4
            entities = await self._extract_with_ai(
                conversation_text,
                relevant_entity_types,
                intent,
                excluded_phones=excluded_phones or []
            )

            # Validate and structure entities
            structured_entities = self._structure_entities(entities, intent, excluded_phones or [])

            logger.info(
                "Entities extracted from conversation",
                intent=intent,
                entity_count=len(structured_entities),
                entity_types=list(structured_entities.keys()),
                excluded_phones_count=len(excluded_phones or [])
            )

            return structured_entities

        except Exception as e:
            logger.error(f"Entity extraction failed: {str(e)}")
            return {}

    def _build_conversation_text(self, conversation_context: List[Dict], current_message: str) -> str:
        """Build readable conversation text for entity extraction"""
        lines = []

        # Add conversation history
        for msg in conversation_context[-10:]:  # Last 10 messages for context
            role = "User" if msg.get("role") == "user" else "Assistant"
            content = msg.get("content", "")
            lines.append(f"{role}: {content}")

        # Add current message
        lines.append(f"User: {current_message}")

        return "\n".join(lines)

    def _get_relevant_entity_types(self, intent: str) -> List[str]:
        """Get relevant entity types based on intent"""
        intent_mapping = {
            "booking_request": self.entity_types["booking"] + self.entity_types["temporal"] + self.entity_types["contact"],
            "order_request": self.entity_types["order"] + self.entity_types["contact"],
            "menu_inquiry": self.entity_types["menu"],
            "payment_question": self.entity_types["payment"],
            "general_question": self.entity_types["temporal"] + self.entity_types["contact"]
        }

        return intent_mapping.get(intent, self.entity_types["temporal"] + self.entity_types["contact"])

    async def _extract_with_ai(
        self,
        conversation_text: str,
        entity_types: List[str],
        intent: str,
        excluded_phones: List[str] = None
    ) -> Dict:
        """Use GPT-4 to extract entities from conversation"""

        if excluded_phones is None:
            excluded_phones = []

        # Get current date for context
        current_date = datetime.now()
        current_date_str = current_date.strftime("%A, %B %d, %Y")  # e.g., "Tuesday, October 15, 2025"

        # Build excluded phones warning
        excluded_phones_warning = ""
        if excluded_phones:
            normalized_excluded = [p.replace("+91", "").replace("-", "").replace(" ", "").strip() for p in excluded_phones]
            excluded_phones_warning = """

**CRITICAL - PHONE NUMBER EXCLUSIONS:**
DO NOT extract these phone numbers (they are NOT customer phones):
{json.dumps(normalized_excluded, indent=2)}

These are:
- Restaurant contact numbers (for customer reference only)
- Placeholder/test numbers (not real customer data)

If you find these numbers in the conversation, IGNORE them completely.
Only extract phone numbers that are explicitly provided by the customer as THEIR contact number.
"""

        system_prompt = f"""You are an entity extraction AI for a restaurant assistant.

**IMPORTANT CONTEXT:**
- Today's date: {current_date_str}
- Current time: {current_date.strftime("%I:%M %p")}

Extract entities from the ENTIRE conversation, not just the last message.

Entity Types to Look For:
{json.dumps(entity_types, indent=2)}

Current Intent: {intent}
{excluded_phones_warning}

**CRITICAL RULES:**
1. Look through ALL messages for entity information
2. If user mentioned "Saturday" in message 1 and "5 pm" in message 3, extract both
3. Combine partial information (e.g., "table for 4" + "tomorrow" + "7 pm" = complete booking info)
4. Extract phone numbers, names, dates, times from anywhere in conversation
5. For times: convert to 24-hour format if possible (e.g., "7pm" = "19:00")
6. For dates: calculate actual date based on today's date (use {current_date_str} as reference)
   - "tomorrow" = {(current_date + timedelta(days=1)).strftime("%Y-%m-%d")}
   - "this sunday" = calculate based on {current_date_str}
7. **ONLY extract entities that are explicitly mentioned in the conversation - DO NOT make up or infer values**

**DISTINGUISH TIME FROM PARTY SIZE:**
- "4pm" or "4 pm" or "16:00" = TIME (not party_size)
- "for 4" or "4 people" or "4 guests" = PARTY_SIZE (not time)
- "book for 4pm this sunday"  time="4pm", date="this sunday" (NO party_size unless explicitly mentioned)

**DISTINGUISH ORDER TYPE (for food orders):**
- "dine in", "dine-in", "for here", "eat here", "eating here", "at the restaurant" = ORDER_TYPE: "dine_in"
- "takeout", "take out", "to go", "pick up", "carry out", "take away", "pack it" = ORDER_TYPE: "takeout"
- If no order type mentioned, leave it as null

**EXAMPLES:**
- "I want to book for 4pm"  {{"time": "4pm", "date": null, "party_size": null}}
- "Table for 4 people at 6pm"  {{"party_size": 4, "time": "6pm"}}
- "Book for 4pm this sunday"  {{"time": "4pm", "date": "this sunday"}}
- "4 people tomorrow at 7pm"  {{"party_size": 4, "date": "tomorrow", "time": "7pm"}}
- "I want to book a table"  {{}} (NO entities - nothing was mentioned)
- "I want chicken tikka masala for takeout"  {{"items": ["chicken tikka masala"], "order_type": "takeout"}}
- "Can I order biryani to go?"  {{"items": ["biryani"], "order_type": "takeout"}}
- "I'd like to order paneer tikka, eating here"  {{"items": ["paneer tikka"], "order_type": "dine_in"}}
- "Order dal makhani for dine in"  {{"items": ["dal makhani"], "order_type": "dine_in"}}

Return JSON with extracted entities. If no entities are mentioned, return empty object {{}}."""

        user_prompt = f"""
Conversation:
{conversation_text}

Extract all relevant entities from this conversation history.
"""

        try:
            from app.core.config import config
            from app.ai_services.models import EntityExtractionResult
            from app.ai_services.llm_manager import get_llm_manager

            # Convert to LangChain messages
            langchain_messages = []
            from langchain_core.messages import SystemMessage, HumanMessage
            langchain_messages.append(SystemMessage(content=system_prompt))
            langchain_messages.append(HumanMessage(content=user_prompt))

            # Get LLM manager
            llm_manager = get_llm_manager()

            # Use structured output with Pydantic model (more reliable than JSON parsing)
            structured_llm = await llm_manager.get_llm_with_structured_output(
                schema=EntityExtractionResult,
                model=config.ENTITY_EXTRACTION_MODEL,
                temperature=0.1
            )

            # Invoke with type-safe structured response
            response: EntityExtractionResult = await structured_llm.ainvoke(langchain_messages)

            logger.info(
                "Entity extraction completed (structured output)",
                entities_found=bool(response.phone_number or response.date or response.time or response.food_items)
            )

            # Convert to dict for backward compatibility
            result = response.model_dump()
            # Remove empty lists/None values for cleaner output
            return {k: v for k, v in result.items() if v}

        except Exception as e:
            logger.error(f"AI entity extraction failed: {str(e)}")
            return {}

    def _structure_entities(self, raw_entities: Dict, intent: str, excluded_phones: List[str] = None) -> Dict[str, Any]:
        """Structure and validate extracted entities"""
        if excluded_phones is None:
            excluded_phones = []

        structured = {}

        for key, value in raw_entities.items():
            if value and str(value).strip():
                # Clean and validate entity value
                cleaned_value = self._clean_entity_value(key, value, excluded_phones)
                if cleaned_value:
                    structured[key] = cleaned_value

        return structured

    def _clean_entity_value(self, entity_type: str, value: Any, excluded_phones: List[str] = None) -> Any:
        """
        Clean and validate entity values

        Args:
            entity_type: Type of entity (phone, date, time, etc.)
            value: Raw value to clean
            excluded_phones: Phone numbers to exclude (restaurant phones, etc.)

        Returns:
            Cleaned value or None if invalid
        """
        if excluded_phones is None:
            excluded_phones = []

        if not value or (isinstance(value, str) and not value.strip()):
            return None

        # Convert to string for processing
        str_value = str(value).strip()

        # Type-specific cleaning
        if entity_type in ["party_size", "quantities"]:
            try:
                return int(str_value)
            except ValueError:
                return None

        elif entity_type == "order_type":
            # Normalize order type values
            normalized = str_value.lower().replace(" ", "_").replace("-", "_")
            if normalized in ["dine_in", "dinein", "dine", "for_here", "here", "eat_here", "eating_here", "at_restaurant", "in_restaurant"]:
                return "dine_in"
            elif normalized in ["takeout", "take_out", "to_go", "togo", "pickup", "pick_up", "carryout", "carry_out", "takeaway", "take_away", "pack"]:
                return "takeout"
            else:
                logger.warning(f"Unrecognized order type value: {str_value}")
                return None

        elif entity_type == "phone":
            # Basic phone validation
            digits = ''.join(filter(str.isdigit, str_value))
            if len(digits) >= 10:
                # CRITICAL: Exclude restaurant phone numbers and test numbers
                # These are NOT customer contact phones!
                invalid_phones = ["9999999999", "1111111111", "0000000000"]

                # Check against hardcoded invalid phones
                if digits in invalid_phones or digits.startswith("9999"):
                    logger.warning(
                        "Rejected test/invalid phone from entity extraction",
                        phone=digits,
                        reason="Test or invalid phone number"
                    )
                    return None

                # Check against excluded phones (e.g., restaurant phone from database)
                for excluded in excluded_phones:
                    excluded_digits = ''.join(filter(str.isdigit, excluded))
                    if digits == excluded_digits:
                        logger.warning(
                            "Rejected excluded phone from entity extraction",
                            phone=digits,
                            excluded_phone=excluded,
                            reason="Phone matches excluded list (likely restaurant phone)"
                        )
                        return None

                return digits
            return None

        elif entity_type in ["date", "time"]:
            # Keep as string for now - could add date parsing later
            return str_value

        else:
            return str_value

    def merge_entities(self, existing_entities: Any, new_entities: Dict) -> Dict[str, Any]:
        """Merge new entities with existing ones, preferring newer values"""
        # Handle case where existing_entities might be a list or non-dict
        if isinstance(existing_entities, dict):
            merged = existing_entities.copy()
        elif isinstance(existing_entities, list):
            # Convert list to empty dict (common AI service response format issue)
            logger.warning(f"Converting list entities to dict: {existing_entities}")
            merged = {}
        else:
            # Fallback to empty dict for other types
            logger.warning(f"Unexpected entity type {type(existing_entities)}: {existing_entities}")
            merged = {}

        # Ensure new_entities is also a dict
        if isinstance(new_entities, dict):
            merged.update(new_entities)
        else:
            logger.warning(f"New entities not dict type {type(new_entities)}: {new_entities}")

        return merged


# Global instance
entity_extractor = ConversationEntityExtractor()

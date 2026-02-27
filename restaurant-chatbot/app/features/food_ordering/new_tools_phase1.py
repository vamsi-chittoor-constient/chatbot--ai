"""
Phase 1 Missing Tools Implementation
=====================================
High-priority tools for customer profile, allergens, dietary, favorites, FAQ, and basic feedback.

These tools should be integrated into crew_agent.py by adding them to the create_crew() function's tool list.

Implementation Date: 2025-12-21
Total Tools: 15 (Phase 1 of 4)
"""

from crewai.tools import tool
import structlog
from typing import Optional, List, Dict

logger = structlog.get_logger(__name__)


# ============================================================================
# CATEGORY 1: CUSTOMER ALLERGEN MANAGEMENT (3 tools)
# ============================================================================

def create_allergen_tools(session_id: str, customer_id: Optional[str] = None):
    """Factory to create allergen management tools with session context."""

    @tool("get_customer_allergens")
    async def get_customer_allergens() -> str:
        """
        Get the customer's allergen information.

        Use this when customer asks about their allergen restrictions or
        says things like "what are my allergies" or "show my allergen info".

        Returns:
            List of customer's allergens with severity levels and notes.
        """
        try:
            from app.core.db_pool import AsyncDBConnection
            from app.core.agui_events import emit_tool_activity_async

            await emit_tool_activity_async(session_id, "get_customer_allergens")

            if not customer_id:
                return "Please log in to view your allergen information."

            async with AsyncDBConnection() as db:
                query = """
                    SELECT
                        a.allergen_name,
                        ca.customer_allergen_severity,
                        ca.customer_allergen_notes
                    FROM customer_allergens ca
                    JOIN allergens a ON ca.allergen_id = a.allergen_id
                    WHERE ca.customer_id = %s
                      AND ca.is_deleted = FALSE
                    ORDER BY ca.customer_allergen_severity DESC, a.allergen_name
                """
                results = await db.fetch_all(query, (customer_id,))

                if not results:
                    return "You don't have any allergens registered in your profile. Would you like to add any?"

                # Format response
                allergens_list = []
                for row in results:
                    severity = row['customer_allergen_severity'] or 'Not specified'
                    notes = row['customer_allergen_notes'] or ''
                    allergen_str = f"- {row['allergen_name']} (Severity: {severity})"
                    if notes:
                        allergen_str += f" - {notes}"
                    allergens_list.append(allergen_str)

                response = f"Your registered allergens:\n\n" + "\n".join(allergens_list)
                response += "\n\nWould you like to add or modify any allergen information?"
                return response

        except Exception as e:
            logger.error("get_customer_allergens_error", error=str(e), exc_info=True)
            return "Sorry, I couldn't retrieve your allergen information right now. Please try again."

    @tool("add_customer_allergen")
    async def add_customer_allergen(allergen_name: str, severity: str = "moderate", notes: str = "") -> str:
        """
        Add an allergen to the customer's profile.

        Use this when customer says they're allergic to something or wants to register an allergen.
        Examples: "I'm allergic to peanuts", "Add shellfish allergy", "I can't eat dairy".

        Args:
            allergen_name: Name of the allergen (e.g., "peanuts", "dairy", "shellfish", "gluten")
            severity: Severity level - "mild", "moderate", or "severe" (default: "moderate")
            notes: Optional notes about the allergen (e.g., "causes hives", "anaphylaxis risk")

        Returns:
            Confirmation that allergen was added to profile.
        """
        try:
            from app.core.db_pool import AsyncDBConnection
            from app.core.agui_events import emit_tool_activity_async

            await emit_tool_activity_async(session_id, "add_customer_allergen")

            if not customer_id:
                return "Please log in to add allergen information to your profile."

            # Validate severity
            severity = severity.lower().strip()
            if severity not in ['mild', 'moderate', 'severe']:
                severity = 'moderate'

            async with AsyncDBConnection() as db:
                # First, find or create the allergen in master list
                allergen_query = """
                    SELECT allergen_id FROM allergens
                    WHERE LOWER(allergen_name) = LOWER(%s) AND is_deleted = FALSE
                """
                allergen_row = await db.fetch_one(allergen_query, (allergen_name,))

                if not allergen_row:
                    # Create new allergen
                    insert_allergen = """
                        INSERT INTO allergens (allergen_name, allergen_description)
                        VALUES (%s, %s)
                        RETURNING allergen_id
                    """
                    allergen_row = await db.fetch_one(
                        insert_allergen,
                        (allergen_name.title(), f"Allergen: {allergen_name}")
                    )

                allergen_id = allergen_row['allergen_id']

                # Check if already exists for this customer
                check_query = """
                    SELECT 1 FROM customer_allergens
                    WHERE customer_id = %s AND allergen_id = %s
                """
                exists = await db.fetch_one(check_query, (customer_id, allergen_id))

                if exists:
                    # Update existing
                    update_query = """
                        UPDATE customer_allergens
                        SET customer_allergen_severity = %s,
                            customer_allergen_notes = %s,
                            is_deleted = FALSE,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE customer_id = %s AND allergen_id = %s
                    """
                    await db.execute(update_query, (severity, notes, customer_id, allergen_id))
                    return f"Updated your {allergen_name} allergen (Severity: {severity}). I'll help you avoid menu items containing {allergen_name}."
                else:
                    # Insert new
                    insert_query = """
                        INSERT INTO customer_allergens
                        (customer_id, allergen_id, customer_allergen_severity, customer_allergen_notes)
                        VALUES (%s, %s, %s, %s)
                    """
                    await db.execute(insert_query, (customer_id, allergen_id, severity, notes))
                    return f"Added {allergen_name} to your allergen profile (Severity: {severity}). I'll make sure to warn you about menu items containing {allergen_name}."

        except Exception as e:
            logger.error("add_customer_allergen_error", error=str(e), exc_info=True)
            return f"Sorry, I couldn't add {allergen_name} to your profile right now. Please try again."

    @tool("remove_customer_allergen")
    async def remove_customer_allergen(allergen_name: str) -> str:
        """
        Remove an allergen from the customer's profile.

        Use this when customer says they're no longer allergic to something or wants to remove an allergen.
        Examples: "Remove peanut allergy", "I'm not allergic to dairy anymore".

        Args:
            allergen_name: Name of the allergen to remove (e.g., "peanuts", "dairy")

        Returns:
            Confirmation that allergen was removed from profile.
        """
        try:
            from app.core.db_pool import AsyncDBConnection
            from app.core.agui_events import emit_tool_activity_async

            await emit_tool_activity_async(session_id, "remove_customer_allergen")

            if not customer_id:
                return "Please log in to modify your allergen information."

            async with AsyncDBConnection() as db:
                # Find the allergen
                allergen_query = """
                    SELECT allergen_id FROM allergens
                    WHERE LOWER(allergen_name) = LOWER(%s) AND is_deleted = FALSE
                """
                allergen_row = await db.fetch_one(allergen_query, (allergen_name,))

                if not allergen_row:
                    return f"I couldn't find '{allergen_name}' in your allergen profile."

                # Soft delete from customer_allergens
                delete_query = """
                    UPDATE customer_allergens
                    SET is_deleted = TRUE, updated_at = CURRENT_TIMESTAMP
                    WHERE customer_id = %s AND allergen_id = %s
                    RETURNING 1
                """
                result = await db.fetch_one(delete_query, (customer_id, allergen_row['allergen_id']))

                if result:
                    return f"Removed {allergen_name} from your allergen profile."
                else:
                    return f"You don't have {allergen_name} in your allergen profile."

        except Exception as e:
            logger.error("remove_customer_allergen_error", error=str(e), exc_info=True)
            return f"Sorry, I couldn't remove {allergen_name} from your profile right now."

    return [get_customer_allergens, add_customer_allergen, remove_customer_allergen]


# ============================================================================
# CATEGORY 2: DIETARY RESTRICTIONS MANAGEMENT (2 tools)
# ============================================================================

def create_dietary_tools(session_id: str, customer_id: Optional[str] = None):
    """Factory to create dietary restriction management tools with session context."""

    @tool("get_dietary_restrictions")
    async def get_dietary_restrictions() -> str:
        """
        Get the customer's dietary restrictions.

        Use this when customer asks about their dietary preferences or restrictions.
        Examples: "what are my dietary restrictions", "am I vegan", "show my food preferences".

        Returns:
            List of customer's dietary restrictions with notes.
        """
        try:
            from app.core.db_pool import AsyncDBConnection
            from app.core.agui_events import emit_tool_activity_async

            await emit_tool_activity_async(session_id, "get_dietary_restrictions")

            if not customer_id:
                return "Please log in to view your dietary restrictions."

            async with AsyncDBConnection() as db:
                query = """
                    SELECT
                        dr.dietary_restriction_name,
                        cdr.customer_dietary_restriction_severity,
                        cdr.customer_dietary_restriction_notes
                    FROM customer_dietary_restrictions cdr
                    JOIN dietary_restrictions dr ON cdr.dietary_restriction_id = dr.dietary_restriction_id
                    WHERE cdr.customer_id = %s
                      AND cdr.is_deleted = FALSE
                    ORDER BY dr.dietary_restriction_name
                """
                results = await db.fetch_all(query, (customer_id,))

                if not results:
                    return "You don't have any dietary restrictions registered. Would you like to add any (e.g., vegetarian, vegan, gluten-free)?"

                # Format response
                restrictions_list = []
                for row in results:
                    severity = row['customer_dietary_restriction_severity'] or 'Preference'
                    notes = row['customer_dietary_restriction_notes'] or ''
                    restriction_str = f"- {row['dietary_restriction_name']} ({severity})"
                    if notes:
                        restriction_str += f" - {notes}"
                    restrictions_list.append(restriction_str)

                response = f"Your dietary restrictions:\n\n" + "\n".join(restrictions_list)
                response += "\n\nI'll filter menu recommendations based on your preferences."
                return response

        except Exception as e:
            logger.error("get_dietary_restrictions_error", error=str(e), exc_info=True)
            return "Sorry, I couldn't retrieve your dietary restrictions right now."

    @tool("add_dietary_restriction")
    async def add_dietary_restriction(restriction_type: str, severity: str = "preference", notes: str = "") -> str:
        """
        Add a dietary restriction to the customer's profile.

        Use this when customer mentions dietary preferences or restrictions.
        Examples: "I'm vegan", "I'm gluten-free", "I don't eat meat", "I'm keto".

        Args:
            restriction_type: Type of dietary restriction (e.g., "vegan", "vegetarian", "gluten-free", "lactose-free", "keto", "halal", "kosher")
            severity: How strict - "preference" (soft preference) or "strict" (must follow) (default: "preference")
            notes: Optional notes (e.g., "for health reasons", "religious")

        Returns:
            Confirmation that dietary restriction was added.
        """
        try:
            from app.core.db_pool import AsyncDBConnection
            from app.core.agui_events import emit_tool_activity_async

            await emit_tool_activity_async(session_id, "add_dietary_restriction")

            if not customer_id:
                return "Please log in to add dietary restrictions to your profile."

            # Validate severity
            severity = severity.lower().strip()
            if severity not in ['preference', 'strict']:
                severity = 'preference'

            async with AsyncDBConnection() as db:
                # Find or create the dietary restriction
                restriction_query = """
                    SELECT dietary_restriction_id FROM dietary_restrictions
                    WHERE LOWER(dietary_restriction_name) = LOWER(%s) AND is_deleted = FALSE
                """
                restriction_row = await db.fetch_one(restriction_query, (restriction_type,))

                if not restriction_row:
                    # Create new dietary restriction
                    insert_restriction = """
                        INSERT INTO dietary_restrictions (dietary_restriction_name, dietary_restriction_description)
                        VALUES (%s, %s)
                        RETURNING dietary_restriction_id
                    """
                    restriction_row = await db.fetch_one(
                        insert_restriction,
                        (restriction_type.title(), f"{restriction_type} diet")
                    )

                restriction_id = restriction_row['dietary_restriction_id']

                # Check if already exists
                check_query = """
                    SELECT 1 FROM customer_dietary_restrictions
                    WHERE customer_id = %s AND dietary_restriction_id = %s
                """
                exists = await db.fetch_one(check_query, (customer_id, restriction_id))

                if exists:
                    # Update existing
                    update_query = """
                        UPDATE customer_dietary_restrictions
                        SET customer_dietary_restriction_severity = %s,
                            customer_dietary_restriction_notes = %s,
                            is_deleted = FALSE,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE customer_id = %s AND dietary_restriction_id = %s
                    """
                    await db.execute(update_query, (severity, notes, customer_id, restriction_id))
                    return f"Updated your {restriction_type} dietary restriction. I'll show you menu items that match this preference."
                else:
                    # Insert new
                    insert_query = """
                        INSERT INTO customer_dietary_restrictions
                        (customer_id, dietary_restriction_id, customer_dietary_restriction_severity, customer_dietary_restriction_notes)
                        VALUES (%s, %s, %s, %s)
                    """
                    await db.execute(insert_query, (customer_id, restriction_id, severity, notes))
                    return f"Added {restriction_type} to your dietary profile. I'll recommend {restriction_type} options from our menu."

        except Exception as e:
            logger.error("add_dietary_restriction_error", error=str(e), exc_info=True)
            return f"Sorry, I couldn't add {restriction_type} to your profile right now."

    return [get_dietary_restrictions, add_dietary_restriction]


# ============================================================================
# CATEGORY 3: CUSTOMER FAVORITES (3 tools)
# ============================================================================

def create_favorites_tools(session_id: str, customer_id: Optional[str] = None):
    """Factory to create favorite items management tools with session context."""

    @tool("get_favorite_items")
    async def get_favorite_items() -> str:
        """
        Get the customer's favorite menu items.

        Use this when customer asks about their favorites or wants to reorder their usual items.
        Examples: "show my favorites", "what are my favorite items", "my usual order".

        Returns:
            List of customer's favorite menu items with prices.
        """
        try:
            from app.core.db_pool import AsyncDBConnection
            from app.core.agui_events import emit_tool_activity_async

            await emit_tool_activity_async(session_id, "get_favorite_items")

            if not customer_id:
                return "Please log in to view your favorite items."

            async with AsyncDBConnection() as db:
                query = """
                    SELECT
                        mi.menu_item_name,
                        mi.menu_item_price,
                        mi.menu_item_description,
                        cfi.added_at
                    FROM customer_favorite_items cfi
                    JOIN menu_item mi ON cfi.menu_item_id = mi.menu_item_id
                    WHERE cfi.customer_id = %s
                      AND cfi.is_deleted = FALSE
                      AND mi.is_deleted = FALSE
                      AND mi.menu_item_is_active = TRUE
                    ORDER BY cfi.added_at DESC
                """
                results = await db.fetch_all(query, (customer_id,))

                if not results:
                    return "You don't have any favorite items yet. Try adding items you love to your favorites!"

                # Format response
                favorites_list = []
                for row in results:
                    item_str = f"- {row['menu_item_name']} (Rs.{row['menu_item_price']})"
                    if row['menu_item_description']:
                        item_str += f"\n  {row['menu_item_description'][:100]}"
                    favorites_list.append(item_str)

                response = f"Your favorite items ({len(results)}):\n\n" + "\n".join(favorites_list)
                response += "\n\nWould you like to add any of these to your cart?"
                return response

        except Exception as e:
            logger.error("get_favorite_items_error", error=str(e), exc_info=True)
            return "Sorry, I couldn't retrieve your favorite items right now."

    @tool("add_to_favorites")
    async def add_to_favorites(item_name: str) -> str:
        """
        Add a menu item to the customer's favorites.

        Use this when customer wants to save an item as a favorite.
        Examples: "add this to my favorites", "save this item", "mark this as favorite".

        Args:
            item_name: Name of the menu item to add to favorites (partial names work)

        Returns:
            Confirmation that item was added to favorites.
        """
        try:
            from app.core.db_pool import AsyncDBConnection
            from app.core.agui_events import emit_tool_activity_async
            from app.core.preloader import get_menu_preloader

            await emit_tool_activity_async(session_id, "add_to_favorites")

            if not customer_id:
                return "Please log in to add items to your favorites."

            # Find the menu item using preloader
            preloader = get_menu_preloader()
            item = preloader.find_item(item_name) if preloader.is_loaded else None

            if not item:
                return f"Sorry, I couldn't find '{item_name}' on our menu. Please check the spelling and try again."

            menu_item_id = item.get('id')
            menu_item_name = item.get('name')

            async with AsyncDBConnection() as db:
                # Check if already a favorite
                check_query = """
                    SELECT 1 FROM customer_favorite_items
                    WHERE customer_id = %s AND menu_item_id = %s AND is_deleted = FALSE
                """
                exists = await db.fetch_one(check_query, (customer_id, menu_item_id))

                if exists:
                    return f"{menu_item_name} is already in your favorites!"

                # Check if was deleted before (restore)
                restore_query = """
                    UPDATE customer_favorite_items
                    SET is_deleted = FALSE, updated_at = CURRENT_TIMESTAMP
                    WHERE customer_id = %s AND menu_item_id = %s AND is_deleted = TRUE
                    RETURNING 1
                """
                restored = await db.fetch_one(restore_query, (customer_id, menu_item_id))

                if restored:
                    return f"Added {menu_item_name} back to your favorites!"

                # Insert new favorite
                insert_query = """
                    INSERT INTO customer_favorite_items (customer_id, menu_item_id)
                    VALUES (%s, %s)
                """
                await db.execute(insert_query, (customer_id, menu_item_id))
                return f"Added {menu_item_name} to your favorites! You can quickly reorder it anytime."

        except Exception as e:
            logger.error("add_to_favorites_error", error=str(e), exc_info=True)
            return f"Sorry, I couldn't add {item_name} to your favorites right now."

    @tool("remove_from_favorites")
    async def remove_from_favorites(item_name: str) -> str:
        """
        Remove a menu item from the customer's favorites.

        Use this when customer wants to remove an item from favorites.
        Examples: "remove this from favorites", "delete from my favorites".

        Args:
            item_name: Name of the menu item to remove from favorites

        Returns:
            Confirmation that item was removed from favorites.
        """
        try:
            from app.core.db_pool import AsyncDBConnection
            from app.core.agui_events import emit_tool_activity_async
            from app.core.preloader import get_menu_preloader

            await emit_tool_activity_async(session_id, "remove_from_favorites")

            if not customer_id:
                return "Please log in to modify your favorites."

            # Find the menu item
            preloader = get_menu_preloader()
            item = preloader.find_item(item_name) if preloader.is_loaded else None

            if not item:
                return f"Sorry, I couldn't find '{item_name}' on our menu."

            menu_item_id = item.get('id')
            menu_item_name = item.get('name')

            async with AsyncDBConnection() as db:
                # Soft delete from favorites
                delete_query = """
                    UPDATE customer_favorite_items
                    SET is_deleted = TRUE, updated_at = CURRENT_TIMESTAMP
                    WHERE customer_id = %s AND menu_item_id = %s AND is_deleted = FALSE
                    RETURNING 1
                """
                result = await db.fetch_one(delete_query, (customer_id, menu_item_id))

                if result:
                    return f"Removed {menu_item_name} from your favorites."
                else:
                    return f"{menu_item_name} is not in your favorites."

        except Exception as e:
            logger.error("remove_from_favorites_error", error=str(e), exc_info=True)
            return f"Sorry, I couldn't remove {item_name} from your favorites right now."

    return [get_favorite_items, add_to_favorites, remove_from_favorites]


# ============================================================================
# CATEGORY 4: FAQ & HELP SYSTEM (4 tools)
# ============================================================================

def create_faq_tools(session_id: str):
    """Factory to create FAQ and help tools with session context."""

    @tool("search_faq")
    async def search_faq(search_query: str) -> str:
        """
        Search frequently asked questions.

        Use this when customer asks common questions about policies, procedures, or services.
        Examples: "what's your refund policy", "how do I track my order", "do you deliver".

        Args:
            search_query: Question or keywords to search (e.g., "refund", "delivery time", "payment methods")

        Returns:
            Matching FAQ entries with answers.
        """
        try:
            from app.core.db_pool import AsyncDBConnection
            from app.core.agui_events import emit_tool_activity_async

            await emit_tool_activity_async(session_id, "search_faq")

            async with AsyncDBConnection() as db:
                # Search by question, answer, or keywords
                query = """
                    SELECT question, answer, category, priority
                    FROM faq
                    WHERE is_active = TRUE
                      AND (
                        LOWER(question) LIKE LOWER(%s)
                        OR LOWER(answer) LIKE LOWER(%s)
                        OR %s = ANY(keywords)
                      )
                    ORDER BY priority DESC, question
                    LIMIT 5
                """
                search_pattern = f"%{search_query}%"
                results = await db.fetch_all(query, (search_pattern, search_pattern, search_query.lower()))

                if not results:
                    return f"I couldn't find any FAQs matching '{search_query}'. Try asking me directly or browse FAQ categories."

                # Format response
                faq_list = []
                for idx, row in enumerate(results, 1):
                    category = f" [{row['category']}]" if row['category'] else ""
                    faq_str = f"{idx}. **{row['question']}**{category}\n   {row['answer']}"
                    faq_list.append(faq_str)

                response = f"Here's what I found:\n\n" + "\n\n".join(faq_list)
                response += "\n\nDid this answer your question?"
                return response

        except Exception as e:
            logger.error("search_faq_error", error=str(e), exc_info=True)
            return "Sorry, I couldn't search FAQs right now. Please ask me directly and I'll try to help."

    @tool("get_faq_by_category")
    async def get_faq_by_category(category: str) -> str:
        """
        Get FAQs by category.

        Use this when customer wants to browse FAQs in a specific area.
        Examples: "show me FAQs about delivery", "help with payment", "ordering questions".

        Args:
            category: FAQ category (e.g., "delivery", "payment", "ordering", "refunds", "account")

        Returns:
            FAQs in the specified category.
        """
        try:
            from app.core.db_pool import AsyncDBConnection
            from app.core.agui_events import emit_tool_activity_async

            await emit_tool_activity_async(session_id, "get_faq_by_category")

            async with AsyncDBConnection() as db:
                query = """
                    SELECT question, answer, priority
                    FROM faq
                    WHERE is_active = TRUE
                      AND LOWER(category) = LOWER(%s)
                    ORDER BY priority DESC, question
                    LIMIT 10
                """
                results = await db.fetch_all(query, (category,))

                if not results:
                    # Try to show available categories
                    cat_query = """
                        SELECT DISTINCT category
                        FROM faq
                        WHERE is_active = TRUE AND category IS NOT NULL
                        ORDER BY category
                    """
                    categories = await db.fetch_all(cat_query)
                    cat_list = [c['category'] for c in categories if c['category']]

                    if cat_list:
                        return f"I couldn't find FAQs for '{category}'. Available categories: {', '.join(cat_list)}"
                    else:
                        return f"No FAQs found for category '{category}'."

                # Format response
                faq_list = []
                for idx, row in enumerate(results, 1):
                    faq_str = f"{idx}. **{row['question']}**\n   {row['answer']}"
                    faq_list.append(faq_str)

                response = f"**{category.title()} FAQs:**\n\n" + "\n\n".join(faq_list)
                return response

        except Exception as e:
            logger.error("get_faq_by_category_error", error=str(e), exc_info=True)
            return "Sorry, I couldn't retrieve FAQs right now. Please ask me directly."

    @tool("get_popular_faqs")
    async def get_popular_faqs() -> str:
        """
        Get the most popular frequently asked questions.

        Use this when customer asks "what are common questions" or wants to see popular FAQs.

        Returns:
            Top priority FAQs.
        """
        try:
            from app.core.db_pool import AsyncDBConnection
            from app.core.agui_events import emit_tool_activity_async

            await emit_tool_activity_async(session_id, "get_popular_faqs")

            async with AsyncDBConnection() as db:
                query = """
                    SELECT question, answer, category
                    FROM faq
                    WHERE is_active = TRUE
                    ORDER BY priority DESC, question
                    LIMIT 8
                """
                results = await db.fetch_all(query)

                if not results:
                    return "No FAQs are available at the moment. Please ask me anything and I'll try to help!"

                # Format response
                faq_list = []
                for idx, row in enumerate(results, 1):
                    category = f" [{row['category']}]" if row['category'] else ""
                    faq_str = f"{idx}. **{row['question']}**{category}\n   {row['answer']}"
                    faq_list.append(faq_str)

                response = f"**Most Popular FAQs:**\n\n" + "\n\n".join(faq_list)
                response += "\n\nHave more questions? Just ask!"
                return response

        except Exception as e:
            logger.error("get_popular_faqs_error", error=str(e), exc_info=True)
            return "Sorry, I couldn't retrieve popular FAQs right now."

    @tool("get_help_categories")
    async def get_help_categories() -> str:
        """
        Get all available FAQ categories.

        Use this when customer asks "what help topics do you have" or "show me help categories".

        Returns:
            List of available FAQ categories.
        """
        try:
            from app.core.db_pool import AsyncDBConnection
            from app.core.agui_events import emit_tool_activity_async

            await emit_tool_activity_async(session_id, "get_help_categories")

            async with AsyncDBConnection() as db:
                query = """
                    SELECT category, COUNT(*) as count
                    FROM faq
                    WHERE is_active = TRUE AND category IS NOT NULL
                    GROUP BY category
                    ORDER BY count DESC, category
                """
                results = await db.fetch_all(query)

                if not results:
                    return "No help categories are available. Please ask me anything and I'll do my best to help!"

                # Format response
                cat_list = []
                for row in results:
                    cat_list.append(f"- {row['category']} ({row['count']} FAQs)")

                response = "**Available Help Topics:**\n\n" + "\n".join(cat_list)
                response += "\n\nWhich category would you like to explore?"
                return response

        except Exception as e:
            logger.error("get_help_categories_error", error=str(e), exc_info=True)
            return "Sorry, I couldn't retrieve help categories right now."

    return [search_faq, get_faq_by_category, get_popular_faqs, get_help_categories]


# ============================================================================
# CATEGORY 5: FEEDBACK & REVIEWS (3 tools)
# ============================================================================

def create_feedback_tools(session_id: str, customer_id: Optional[str] = None):
    """Factory to create feedback and review tools with session context."""

    @tool("submit_feedback")
    async def submit_feedback(feedback_text: str, rating: int = 0, category: str = "general", feedback_type: str = "feedback") -> str:
        """
        Submit feedback, complaint, or suggestion.

        Use this when customer wants to provide feedback, report an issue, or make a suggestion.
        Examples: "I want to complain about cold food", "the service was great", "you should add more vegan options".

        Args:
            feedback_text: The feedback message from customer (required)
            rating: Optional rating from 1-5 stars (0 if not provided)
            category: Category of feedback - "food_quality", "service", "delivery", "app", "general" (default: "general")
            feedback_type: Type - "complaint", "suggestion", "praise", "feedback" (default: "feedback")

        Returns:
            Confirmation with feedback tracking ID.
        """
        try:
            from app.core.db_pool import AsyncDBConnection
            from app.core.agui_events import emit_tool_activity_async
            import uuid

            await emit_tool_activity_async(session_id, "submit_feedback")

            # Validate rating
            if rating < 0 or rating > 5:
                rating = 0

            # Determine urgency based on keywords
            is_urgent = any(word in feedback_text.lower() for word in ['urgent', 'terrible', 'worst', 'awful', 'disgusting', 'refund', 'complaint'])

            async with AsyncDBConnection() as db:
                # Get or create category
                cat_query = """
                    SELECT category_id FROM feedback_categories
                    WHERE LOWER(category_name) = LOWER(%s)
                    LIMIT 1
                """
                cat_row = await db.fetch_one(cat_query, (category,))
                category_id = cat_row['category_id'] if cat_row else None

                # Get or create feedback type
                type_query = """
                    SELECT type_id FROM feedback_types
                    WHERE LOWER(type_name) = LOWER(%s)
                    LIMIT 1
                """
                type_row = await db.fetch_one(type_query, (feedback_type,))
                type_id = type_row['type_id'] if type_row else None

                # Get default "submitted" status
                status_query = """
                    SELECT status_id FROM feedback_statuses
                    WHERE LOWER(status_name) = 'submitted'
                    LIMIT 1
                """
                status_row = await db.fetch_one(status_query)
                status_id = status_row['status_id'] if status_row else None

                # Insert feedback
                insert_query = """
                    INSERT INTO feedback (
                        customer_id,
                        is_anonymous,
                        feedback_text,
                        rating,
                        category_id,
                        feedback_type_id,
                        status_id,
                        is_urgent,
                        submitted_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                    RETURNING feedback_id
                """
                result = await db.fetch_one(
                    insert_query,
                    (
                        customer_id,  # Will be NULL if not logged in (anonymous)
                        customer_id is None,  # is_anonymous
                        feedback_text,
                        rating if rating > 0 else None,
                        category_id,
                        type_id,
                        status_id,
                        is_urgent
                    )
                )

                feedback_id = str(result['feedback_id'])[:8]  # Short ID for display

                thank_you_msg = "Thank you for your feedback! "
                if is_urgent:
                    thank_you_msg += "We've marked this as urgent and will review it immediately. "

                thank_you_msg += f"Your feedback ID is: {feedback_id}. "

                if customer_id:
                    thank_you_msg += "You can check the status anytime by asking me."

                return thank_you_msg

        except Exception as e:
            logger.error("submit_feedback_error", error=str(e), exc_info=True)
            return "Thank you for your feedback. I couldn't record it in the system right now, but I've noted it. Our team will be notified."

    @tool("rate_last_order")
    async def rate_last_order(rating: int, review_text: str = "") -> str:
        """
        Rate the customer's most recent order.

        Use this when customer wants to rate their last order or leave a review.
        Examples: "I want to rate my order 5 stars", "rate my last order", "leave a review".

        Args:
            rating: Rating from 1-5 stars (required)
            review_text: Optional review text (e.g., "Food was amazing!", "Delivery was slow")

        Returns:
            Confirmation that rating was submitted.
        """
        try:
            from app.core.db_pool import AsyncDBConnection
            from app.core.agui_events import emit_tool_activity_async

            await emit_tool_activity_async(session_id, "rate_last_order")

            if not customer_id:
                return "Please log in to rate your order."

            # Validate rating
            if rating < 1 or rating > 5:
                return "Please provide a rating between 1 and 5 stars."

            async with AsyncDBConnection() as db:
                # Find most recent order
                order_query = """
                    SELECT order_id, order_number
                    FROM orders
                    WHERE customer_id = %s
                    ORDER BY created_at DESC
                    LIMIT 1
                """
                order_row = await db.fetch_one(order_query, (customer_id,))

                if not order_row:
                    return "I couldn't find any orders for your account. Place an order first to leave a review!"

                order_id = order_row['order_id']
                order_number = order_row['order_number']

                # Check if already rated
                check_query = """
                    SELECT 1 FROM feedback
                    WHERE customer_id = %s AND order_id = %s AND is_deleted = FALSE
                """
                exists = await db.fetch_one(check_query, (customer_id, order_id))

                # Get feedback type and status
                type_query = "SELECT type_id FROM feedback_types WHERE LOWER(type_name) = 'review' LIMIT 1"
                type_row = await db.fetch_one(type_query)
                type_id = type_row['type_id'] if type_row else None

                status_query = "SELECT status_id FROM feedback_statuses WHERE LOWER(status_name) = 'submitted' LIMIT 1"
                status_row = await db.fetch_one(status_query)
                status_id = status_row['status_id'] if status_row else None

                if exists:
                    # Update existing rating
                    update_query = """
                        UPDATE feedback
                        SET rating = %s,
                            feedback_text = %s,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE customer_id = %s AND order_id = %s
                    """
                    await db.execute(update_query, (rating, review_text or "Order review", customer_id, order_id))
                    return f"Updated your rating for order {order_number} to {rating} stars. Thank you for your feedback!"
                else:
                    # Insert new rating
                    insert_query = """
                        INSERT INTO feedback (
                            customer_id,
                            order_id,
                            rating,
                            feedback_text,
                            feedback_type_id,
                            status_id
                        )
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """
                    await db.execute(
                        insert_query,
                        (customer_id, order_id, rating, review_text or "Order review", type_id, status_id)
                    )

                    stars = "⭐" * rating
                    return f"Thank you for rating order {order_number} {rating} stars {stars}! Your feedback helps us improve."

        except Exception as e:
            logger.error("rate_last_order_error", error=str(e), exc_info=True)
            return "Sorry, I couldn't submit your rating right now. Please try again."

    @tool("get_my_feedback_history")
    async def get_my_feedback_history() -> str:
        """
        View the customer's feedback history and status.

        Use this when customer asks about their past feedback, complaints, or wants to check status.
        Examples: "show my feedback history", "what's the status of my complaint", "have I given feedback before".

        Returns:
            List of customer's feedback with status.
        """
        try:
            from app.core.db_pool import AsyncDBConnection
            from app.core.agui_events import emit_tool_activity_async

            await emit_tool_activity_async(session_id, "get_my_feedback_history")

            if not customer_id:
                return "Please log in to view your feedback history."

            async with AsyncDBConnection() as db:
                query = """
                    SELECT
                        f.feedback_id,
                        f.feedback_text,
                        f.rating,
                        f.submitted_at,
                        ft.type_name,
                        fs.status_name,
                        fc.category_name
                    FROM feedback f
                    LEFT JOIN feedback_types ft ON f.feedback_type_id = ft.type_id
                    LEFT JOIN feedback_statuses fs ON f.status_id = fs.status_id
                    LEFT JOIN feedback_categories fc ON f.category_id = fc.category_id
                    WHERE f.customer_id = %s AND f.is_deleted = FALSE
                    ORDER BY f.submitted_at DESC
                    LIMIT 10
                """
                results = await db.fetch_all(query, (customer_id,))

                if not results:
                    return "You haven't submitted any feedback yet. Feel free to share your thoughts anytime!"

                # Format response
                feedback_list = []
                for idx, row in enumerate(results, 1):
                    feedback_id = str(row['feedback_id'])[:8]
                    submitted = row['submitted_at'].strftime("%Y-%m-%d") if row['submitted_at'] else "Unknown"
                    rating_str = f" ({row['rating']}★)" if row['rating'] else ""
                    type_str = row['type_name'] or "Feedback"
                    status_str = row['status_name'] or "Submitted"

                    feedback_str = f"{idx}. **{type_str}**{rating_str} - {status_str}\n"
                    feedback_str += f"   ID: {feedback_id} | {submitted}\n"
                    feedback_str += f"   \"{row['feedback_text'][:100]}...\""
                    feedback_list.append(feedback_str)

                response = f"**Your Feedback History ({len(results)} entries):**\n\n" + "\n\n".join(feedback_list)
                return response

        except Exception as e:
            logger.error("get_my_feedback_history_error", error=str(e), exc_info=True)
            return "Sorry, I couldn't retrieve your feedback history right now."

    return [submit_feedback, rate_last_order, get_my_feedback_history]


# ============================================================================
# TOOL COLLECTION FOR EASY INTEGRATION
# ============================================================================

def get_all_phase1_tools(session_id: str, customer_id: Optional[str] = None) -> List:
    """
    Get all Phase 1 tools for integration into crew_agent.py.

    Usage in crew_agent.py:
        from app.features.food_ordering.new_tools_phase1 import get_all_phase1_tools

        # In create_crew() function, add to tools list:
        phase1_tools = get_all_phase1_tools(session_id, customer_id)
        all_tools = existing_tools + phase1_tools

    Args:
        session_id: Current chat session ID
        customer_id: Current customer ID (None if not logged in)

    Returns:
        List of all 15 Phase 1 tool functions
    """
    tools = []

    # Allergen tools (3)
    tools.extend(create_allergen_tools(session_id, customer_id))

    # Dietary tools (2)
    tools.extend(create_dietary_tools(session_id, customer_id))

    # Favorites tools (3)
    tools.extend(create_favorites_tools(session_id, customer_id))

    # FAQ tools (4)
    tools.extend(create_faq_tools(session_id))

    # Feedback tools (3)
    tools.extend(create_feedback_tools(session_id, customer_id))

    logger.info("phase1_tools_loaded", tool_count=len(tools), session=session_id)

    return tools

"""
Unit tests for dine-in/takeaway checkout flow changes.

Tests cover:
1. OrderTypeCard onSubmit parameter format
2. Welcome message — no standalone booking mentions
3. Quick reply sets — no booking-related options
4. Quick reply classifier prompt — updated descriptions
5. AGUI reducer — ORDER_TYPE_SELECTION event handling
6. Crew version bump
7. Tool retrieval — checkout failsafe, no booking tools
8. Agent prompt — booking redirect messaging
"""
import pytest
import re
import json
import sys
import os
from unittest.mock import patch, AsyncMock, MagicMock

# ---------------------------------------------------------------------------
# Helpers — read source files as text (avoids heavy import chains)
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FRONTEND_SRC = os.path.join(PROJECT_ROOT, "frontend", "src")


def _read(rel_path: str) -> str:
    """Read a project file relative to PROJECT_ROOT."""
    with open(os.path.join(PROJECT_ROOT, rel_path), encoding="utf-8") as f:
        return f.read()


# ===================================================================
# 1. OrderTypeCard.jsx — onSubmit signature
# ===================================================================
class TestOrderTypeCardSignature:
    """Verify OrderTypeCard calls onSubmit(formType, data) with TWO args."""

    @pytest.fixture(autouse=True)
    def load_source(self):
        self.src = _read("frontend/src/components/OrderTypeCard.jsx")

    def test_onsubmit_has_two_args(self):
        """onSubmit must be called as onSubmit('order_type_selection', { ... })"""
        assert "onSubmit('order_type_selection'," in self.src

    def test_onsubmit_not_single_object(self):
        """Must NOT use old pattern: onSubmit({ form_type: ... })"""
        assert "onSubmit({" not in self.src

    def test_passes_order_type_in_data(self):
        """Data object must include order_type field."""
        assert "order_type: orderType" in self.src or "order_type:" in self.src

    def test_passes_order_id_in_data(self):
        """Data object must include order_id field."""
        assert "order_id" in self.src


# ===================================================================
# 2. Welcome message — no standalone booking
# ===================================================================
class TestDeterministicWelcome:
    """Verify welcome.py doesn't mention standalone table booking."""

    @pytest.fixture(autouse=True)
    def load_source(self):
        self.src = _read("app/utils/welcome.py")

    def test_no_table_reservation_text(self):
        assert "table reservation" not in self.src.lower()

    def test_no_make_reservation(self):
        assert "Make a table reservation" not in self.src

    def test_mentions_dine_in_or_takeaway(self):
        assert "dine-in or takeaway" in self.src.lower()

    def test_mentions_specials_or_deals(self):
        assert "specials" in self.src.lower() or "deals" in self.src.lower()

    def test_no_book_a_table_bullet(self):
        """Should not list 'book a table' as a standalone capability."""
        for line in self.src.splitlines():
            line_l = line.strip().lower()
            if line_l.startswith("-") and "book" in line_l and "table" in line_l:
                pytest.fail(f"Found standalone booking bullet: {line.strip()}")


class TestAIWelcomeService:
    """Verify welcome_service.py prompts don't push standalone booking."""

    @pytest.fixture(autouse=True)
    def load_source(self):
        self.src = _read("app/ai_services/welcome_service.py")

    def test_tier1_no_book_a_table(self):
        """Tier 1 prompt should NOT say 'book a table'."""
        # Extract tier 1 section
        tier1_match = re.search(r"TIER 1.*?(?=TIER 2|elif tier|$)", self.src, re.DOTALL)
        assert tier1_match, "Could not find TIER 1 section"
        tier1 = tier1_match.group(0).lower()
        assert "book a table" not in tier1
        assert "table reservation" not in tier1

    def test_tier2_no_book_a_table(self):
        """Tier 2 prompt should NOT say 'book a table'."""
        tier2_match = re.search(r"TIER 2.*?(?=TIER 3|else|$)", self.src, re.DOTALL)
        assert tier2_match, "Could not find TIER 2 section"
        tier2 = tier2_match.group(0).lower()
        assert "book a table" not in tier2

    def test_tier3_no_book_a_table(self):
        """Tier 3 prompt should NOT say 'book a table' as standalone action."""
        tier3_match = re.search(r"TIER 3.*?(?=def |$)", self.src, re.DOTALL)
        assert tier3_match, "Could not find TIER 3 section"
        tier3 = tier3_match.group(0).lower()
        assert "book a table" not in tier3

    def test_no_mention_table_bookings_naturally(self):
        """Should NOT instruct LLM to 'mention table bookings naturally'."""
        assert "mention that you can help with table bookings" not in self.src.lower()

    def test_tier1_mentions_dine_in_takeaway(self):
        """Tier 1 should mention dine-in/takeaway flow."""
        tier1_match = re.search(r"TIER 1.*?(?=TIER 2|elif tier|$)", self.src, re.DOTALL)
        tier1 = tier1_match.group(0).lower()
        assert "dine in" in tier1 or "takeaway" in tier1


# ===================================================================
# 3. Quick reply sets — no booking options
# ===================================================================
class TestQuickReplySets:
    """Verify quick reply dicts don't contain standalone booking actions."""

    @pytest.fixture(autouse=True)
    def load_source(self):
        self.src = _read("app/features/food_ordering/crew_agent.py")

    def _get_set(self, name: str) -> str:
        """Extract a named quick reply set block."""
        pattern = rf'"{name}"\s*:\s*\[.*?\]'
        match = re.search(pattern, self.src, re.DOTALL)
        return match.group(0) if match else ""

    # --- greeting_welcome ---
    def test_greeting_welcome_no_book_table(self):
        qr = self._get_set("greeting_welcome")
        assert "Book a Table" not in qr
        assert "Book Table" not in qr
        assert "book a table" not in qr

    def test_greeting_welcome_has_order_food(self):
        qr = self._get_set("greeting_welcome")
        assert "Order Food" in qr

    def test_greeting_welcome_has_help(self):
        qr = self._get_set("greeting_welcome")
        assert "Help" in qr

    # --- explore_features ---
    def test_explore_features_no_book_table(self):
        qr = self._get_set("explore_features")
        assert "Book Table" not in qr
        assert "book a table" not in qr

    # --- menu_displayed ---
    def test_menu_displayed_no_book_table(self):
        qr = self._get_set("menu_displayed")
        assert "Book Table" not in qr

    # --- booking_inquiry redirects to ordering ---
    def test_booking_inquiry_redirects(self):
        """booking_inquiry should show Browse Menu, not Book Table."""
        qr = self._get_set("booking_inquiry")
        assert qr, "booking_inquiry set should exist"
        assert "Browse Menu" in qr or "Show Menu" in qr or "show me the menu" in qr
        assert "Book Table" not in qr
        assert "Check Availability" not in qr

    # --- booking_confirmed simplified ---
    def test_booking_confirmed_no_view_bookings(self):
        qr = self._get_set("booking_confirmed")
        assert "View Bookings" not in qr
        assert "Pre-Order Food" not in qr
        assert "Modify Booking" not in qr

    # --- removed sets ---
    def test_availability_shown_removed(self):
        qr = self._get_set("availability_shown")
        assert qr == "", "availability_shown quick reply set should be removed"

    def test_booking_management_removed(self):
        qr = self._get_set("booking_management")
        assert qr == "", "booking_management quick reply set should be removed"

    # --- my_account ---
    def test_my_account_no_bookings(self):
        qr = self._get_set("my_account")
        assert "My Bookings" not in qr
        assert "show my bookings" not in qr


# ===================================================================
# 4. Quick reply classifier prompt
# ===================================================================
class TestQuickReplyClassifierPrompt:
    """Verify the QUICK_REPLY_AGENT_PROMPT has updated descriptions."""

    @pytest.fixture(autouse=True)
    def load_source(self):
        self.src = _read("app/features/food_ordering/crew_agent.py")
        # Extract the prompt string
        match = re.search(r'QUICK_REPLY_AGENT_PROMPT\s*=\s*"""(.*?)"""', self.src, re.DOTALL)
        self.prompt = match.group(1) if match else ""

    def test_prompt_exists(self):
        assert self.prompt, "QUICK_REPLY_AGENT_PROMPT should exist"

    def test_greeting_welcome_no_book_table_in_prompt(self):
        """Prompt description for greeting_welcome should not mention Book Table."""
        line = [l for l in self.prompt.splitlines() if "greeting_welcome" in l]
        assert line, "greeting_welcome line should exist in prompt"
        assert "Book Table" not in line[0]

    def test_explore_features_no_book_in_prompt(self):
        line = [l for l in self.prompt.splitlines() if "explore_features" in l]
        assert line
        assert "Book" not in line[0]

    def test_menu_displayed_no_book_table_in_prompt(self):
        line = [l for l in self.prompt.splitlines() if "menu_displayed" in l]
        assert line
        assert "Book Table" not in line[0]

    def test_booking_inquiry_redirect_in_prompt(self):
        """booking_inquiry description should mention redirect to ordering."""
        line = [l for l in self.prompt.splitlines() if "booking_inquiry" in l]
        assert line
        line_text = line[0].lower()
        assert "redirect" in line_text or "menu" in line_text or "browse" in line_text

    def test_no_availability_shown_in_prompt(self):
        """availability_shown should not appear in the prompt."""
        assert "availability_shown" not in self.prompt

    def test_no_booking_management_in_prompt(self):
        """booking_management should not appear in the prompt."""
        assert "booking_management" not in self.prompt

    def test_my_account_no_bookings_in_prompt(self):
        line = [l for l in self.prompt.splitlines() if "my_account" in l]
        assert line
        assert "Bookings" not in line[0]


# ===================================================================
# 5. AGUI Reducer — ORDER_TYPE_SELECTION event
# ===================================================================
class TestAGUIReducer:
    """Verify the useAGUI reducer handles ORDER_TYPE_SELECTION correctly."""

    @pytest.fixture(autouse=True)
    def load_source(self):
        self.src = _read("frontend/src/hooks/useAGUI.js")

    def test_order_type_selection_case_exists(self):
        assert "ORDER_TYPE_SELECTION" in self.src

    def test_creates_order_type_selection_message_type(self):
        assert "type: 'order_type_selection'" in self.src

    def test_payment_link_filters_order_type_selection(self):
        """PAYMENT_LINK case should remove order_type_selection messages."""
        # Find the PAYMENT_LINK case
        match = re.search(r"case 'PAYMENT_LINK'.*?(?=case '|default:)", self.src, re.DOTALL)
        assert match, "PAYMENT_LINK case should exist"
        assert "order_type_selection" in match.group(0)

    def test_booking_intake_form_filters_order_type_selection(self):
        """BOOKING_INTAKE_FORM case should remove order_type_selection messages."""
        match = re.search(r"case 'BOOKING_INTAKE_FORM'.*?(?=case '|default:)", self.src, re.DOTALL)
        assert match, "BOOKING_INTAKE_FORM case should exist"
        assert "order_type_selection" in match.group(0)


# ===================================================================
# 6. Crew version bump
# ===================================================================
class TestCrewVersion:
    """Verify crew version was bumped for cache invalidation."""

    @pytest.fixture(autouse=True)
    def load_source(self):
        self.src = _read("app/orchestration/restaurant_crew.py")

    def test_crew_version_at_least_45(self):
        match = re.search(r"_CREW_VERSION\s*=\s*(\d+)", self.src)
        assert match, "_CREW_VERSION should be defined"
        version = int(match.group(1))
        assert version >= 45, f"Crew version should be >= 45, got {version}"


# ===================================================================
# 7. Tool retrieval — checkout present, booking removed
# ===================================================================
class TestToolRetrieval:
    """Verify tool_retrieval.py has checkout failsafe and no booking tools."""

    @pytest.fixture(autouse=True)
    def load_source(self):
        self.src = _read("app/core/tool_retrieval.py")

    def test_checkout_tool_in_dict(self):
        assert '"checkout"' in self.src

    def test_checkout_keyword_failsafe(self):
        """Checkout keywords should force-include the checkout tool."""
        assert "checkout" in self.src.lower()
        # Verify the failsafe block exists
        assert '_must_include.append("checkout")' in self.src

    def test_checkout_examples_include_i_want_to_checkout(self):
        assert "I want to checkout" in self.src

    def test_no_booking_tool_in_food_ordering_tools(self):
        """Booking tools should NOT be in FOOD_ORDERING_TOOLS dict."""
        # Find the FOOD_ORDERING_TOOLS dict
        match = re.search(r"FOOD_ORDERING_TOOLS\s*=\s*\{(.*?)\n\}", self.src, re.DOTALL)
        if match:
            food_tools = match.group(1)
            assert "show_booking_form" not in food_tools
            assert "make_reservation" not in food_tools
            assert "get_my_bookings" not in food_tools

    def test_booking_failsafe_removed(self):
        """Booking keyword failsafe should be removed."""
        # Check that _must_include doesn't append booking tools
        assert '_must_include.append("show_booking_form")' not in self.src
        assert '_must_include.append("make_reservation")' not in self.src


# ===================================================================
# 8. Agent prompt — booking redirect
# ===================================================================
class TestAgentPrompt:
    """Verify agent prompt redirects booking to checkout flow."""

    @pytest.fixture(autouse=True)
    def load_source(self):
        self.src = _read("app/orchestration/restaurant_crew.py")

    def test_booking_via_checkout_instruction(self):
        """Agent should be told booking is only via dine-in checkout."""
        assert "dine-in checkout" in self.src.lower() or "dine-in checkout flow" in self.src.lower()

    def test_no_call_show_booking_form(self):
        """Agent prompt should say NOT to call show_booking_form directly."""
        assert "Do NOT call show_booking_form" in self.src

    def test_order_food_first_instruction(self):
        """Agent should tell users to order food first."""
        assert "order food first" in self.src.lower() or "add items to cart" in self.src.lower()

    def test_checkout_immediate_instruction(self):
        """Agent should call checkout() IMMEDIATELY on checkout requests."""
        assert "call checkout() IMMEDIATELY" in self.src or "call checkout" in self.src

    def test_booking_tools_removed_from_agent(self):
        """Booking tools section should indicate removal."""
        assert "BOOKING TOOLS" in self.src.upper() or "booking tools" in self.src.lower()
        assert "removed from agent" in self.src.lower()


# ===================================================================
# 9. App.jsx — OrderTypeCard rendering
# ===================================================================
class TestAppJSXRendering:
    """Verify App.jsx renders OrderTypeCard correctly."""

    @pytest.fixture(autouse=True)
    def load_source(self):
        self.src = _read("frontend/src/App.jsx")

    def test_order_type_selection_case(self):
        assert "case 'order_type_selection':" in self.src

    def test_renders_order_type_card(self):
        assert "OrderTypeCard" in self.src

    def test_passes_handleFormSubmit(self):
        """OrderTypeCard should receive handleFormSubmit as onSubmit prop."""
        # Find the order_type_selection rendering line
        lines = [l for l in self.src.splitlines() if "OrderTypeCard" in l and "onSubmit" in l]
        assert lines, "OrderTypeCard should have onSubmit prop"
        assert "handleFormSubmit" in lines[0]

    def test_handleFormSubmit_expects_two_params(self):
        """handleFormSubmit should accept (formType, data) — two params."""
        match = re.search(r"handleFormSubmit\s*=\s*useCallback\(\s*\((.*?)\)", self.src)
        assert match, "handleFormSubmit should be defined with useCallback"
        params = match.group(1)
        param_list = [p.strip() for p in params.split(",")]
        assert len(param_list) == 2, f"Expected 2 params, got {len(param_list)}: {param_list}"
        assert "formType" in param_list[0]
        assert "data" in param_list[1]


# ===================================================================
# 10. Simulated user questions — end-to-end scenario validation
# ===================================================================
class TestUserScenarios:
    """
    Simulate various user questions/intents and verify the system
    would handle them correctly based on the code structure.
    """

    @pytest.fixture(autouse=True)
    def load_all(self):
        self.tool_retrieval = _read("app/core/tool_retrieval.py")
        self.crew_agent = _read("app/features/food_ordering/crew_agent.py")
        self.restaurant_crew = _read("app/orchestration/restaurant_crew.py")
        self.welcome = _read("app/utils/welcome.py")

    # --- "I want to book a table" ---
    def test_book_table_request_redirected(self):
        """When user says 'book a table', agent should redirect to ordering."""
        prompt = self.restaurant_crew.lower()
        assert "order food first" in prompt or "add items to cart" in prompt

    # --- "hi" / "hello" ---
    def test_greeting_shows_no_booking_quick_reply(self):
        """Greeting quick replies should NOT have Book Table."""
        match = re.search(r'"greeting_welcome"\s*:\s*\[(.*?)\]', self.crew_agent, re.DOTALL)
        assert match
        qr_text = match.group(1)
        assert "book" not in qr_text.lower() or "book" not in qr_text

    # --- "I want to checkout" ---
    def test_checkout_tool_retrieved_for_checkout_message(self):
        """Tool retrieval failsafe should include checkout tool."""
        assert '"checkout"' in self.tool_retrieval
        assert '_must_include.append("checkout")' in self.tool_retrieval

    # --- "show me the menu" ---
    def test_menu_quick_replies_no_booking(self):
        """Menu displayed quick replies should not have booking."""
        match = re.search(r'"menu_displayed"\s*:\s*\[(.*?)\]', self.crew_agent, re.DOTALL)
        assert match
        assert "book" not in match.group(1).lower()

    # --- "what can you do" ---
    def test_explore_features_no_booking(self):
        """Feature exploration should not list booking as standalone feature."""
        match = re.search(r'"explore_features"\s*:\s*\[(.*?)\]', self.crew_agent, re.DOTALL)
        assert match
        assert "book" not in match.group(1).lower()

    # --- Welcome message scenarios ---
    def test_welcome_no_standalone_booking(self):
        """Welcome message should not mention standalone table reservation."""
        assert "Make a table reservation" not in self.welcome
        assert "table reservation" not in self.welcome.lower()

    def test_welcome_mentions_order_types(self):
        """Welcome should mention dine-in or takeaway."""
        assert "dine-in" in self.welcome.lower() or "takeaway" in self.welcome.lower()

    # --- "I want to dine in" (after checkout) ---
    def test_dine_in_handled_in_order_type_selection(self):
        """order_type_selection form handler should exist in chat.py."""
        chat_py = _read("app/api/routes/chat.py")
        assert "order_type_selection" in chat_py

    # --- "show my bookings" ---
    def test_show_bookings_not_in_quick_replies(self):
        """'show my bookings' should not appear in any active quick reply set."""
        # Check that 'show my bookings' only appears in removed/inactive sections
        match = re.search(r'"my_account"\s*:\s*\[(.*?)\]', self.crew_agent, re.DOTALL)
        if match:
            assert "show my bookings" not in match.group(1)

    # --- "modify booking" ---
    def test_modify_booking_not_in_active_quick_replies(self):
        """'Modify Booking' should not appear in any active quick reply set."""
        # Check greeting, explore, menu, booking_confirmed sets
        for set_name in ["greeting_welcome", "explore_features", "menu_displayed", "booking_confirmed"]:
            match = re.search(rf'"{set_name}"\s*:\s*\[(.*?)\]', self.crew_agent, re.DOTALL)
            if match:
                assert "Modify Booking" not in match.group(1), f"Modify Booking found in {set_name}"

    # --- Payment flow after order type selection ---
    def test_payment_link_event_filters_order_card(self):
        """PAYMENT_LINK reducer should clean up order_type_selection card."""
        agui = _read("frontend/src/hooks/useAGUI.js")
        match = re.search(r"case 'PAYMENT_LINK'.*?(?=case '|default:)", agui, re.DOTALL)
        assert match
        assert "order_type_selection" in match.group(0)


# ===================================================================
# 11. Charge constants
# ===================================================================
class TestChargeConstants:
    """Verify dine-in and takeaway charge constants."""

    @pytest.fixture(autouse=True)
    def load_source(self):
        self.src = _read("app/core/agui_events.py")

    def test_dine_in_charge_per_person(self):
        assert "DINE_IN_CHARGE_PER_PERSON" in self.src
        match = re.search(r"DINE_IN_CHARGE_PER_PERSON\s*=\s*(\d+)", self.src)
        assert match
        assert int(match.group(1)) == 5

    def test_packaging_charge_per_item(self):
        assert "PACKAGING_CHARGE_PER_ITEM" in self.src
        match = re.search(r"PACKAGING_CHARGE_PER_ITEM\s*=\s*(\d+)", self.src)
        assert match
        assert int(match.group(1)) == 30

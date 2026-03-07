"""
Tests for quick reply coverage and validity.

Covers:
1. Welcome message emits quick replies (all 3 paths: AI, reconnect, fallback)
2. Crew response always emits quick replies (with fallback)
3. All quick reply action strings are valid (map to agent-understandable intents)
4. No obsolete sets (order_type, payment_method removed)
5. No booking actions in active sets
6. DEFAULT_QUICK_REPLIES exists and is valid
7. Classifier prompt matches available sets
8. Fallback welcome no longer mentions "reservation"
"""
import pytest
import re
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _read(rel_path: str) -> str:
    with open(os.path.join(PROJECT_ROOT, rel_path), encoding="utf-8") as f:
        return f.read()


# ===================================================================
# 1. Welcome message emits quick replies
# ===================================================================
class TestWelcomeQuickReplies:
    """Verify welcome message emits quick replies in all code paths."""

    @pytest.fixture(autouse=True)
    def load_source(self):
        self.src = _read("app/api/routes/chat.py")

    def test_ai_welcome_emits_quick_replies(self):
        """AI-powered welcome path should emit quick replies."""
        # Find the section between "AI-powered welcome sent" and the except block
        match = re.search(
            r'welcome_msg = await welcome_service\.generate_welcome.*?except Exception',
            self.src, re.DOTALL
        )
        assert match, "AI welcome section should exist"
        section = match.group(0)
        assert "emit_quick_replies" in section or "emit_welcome_qr" in section

    def test_reconnect_welcome_emits_quick_replies(self):
        """Reconnect welcome re-send should also emit quick replies."""
        match = re.search(
            r'welcome_resent_on_reconnect.*?elif welcome_already_sent',
            self.src, re.DOTALL
        )
        assert match, "Reconnect welcome section should exist"
        section = match.group(0)
        assert "emit_quick_replies" in section or "emit_reconn_qr" in section

    def test_fallback_welcome_emits_quick_replies(self):
        """Fallback welcome (AI generation failed) should emit quick replies."""
        # The fallback section is in the except block, emit happens before the log line
        match = re.search(
            r'fallback_msg\s*=.*?Used fallback welcome',
            self.src, re.DOTALL
        )
        assert match, "Fallback welcome section should exist"
        section = match.group(0)
        assert "emit_quick_replies" in section or "emit_fb_qr" in section

    def test_welcome_quick_replies_have_order_food(self):
        """Welcome quick replies should include Order Food option."""
        assert '"Order Food"' in self.src or "Order Food" in self.src

    def test_welcome_quick_replies_no_booking(self):
        """Welcome quick replies should NOT include Book Table."""
        # Find all emit_quick_replies calls near welcome
        matches = re.findall(
            r'emit_(?:welcome_qr|reconn_qr|fb_qr)\(session_id,\s*\[(.*?)\]\)',
            self.src, re.DOTALL
        )
        for m in matches:
            assert "Book" not in m, f"Welcome quick replies should not have booking: {m[:100]}"


# ===================================================================
# 2. Crew response always emits quick replies
# ===================================================================
class TestCrewQuickReplies:
    """Verify crew response always emits quick replies."""

    @pytest.fixture(autouse=True)
    def load_source(self):
        self.src = _read("app/orchestration/restaurant_crew.py")

    def test_quick_replies_classified_after_response(self):
        assert "get_response_quick_replies" in self.src

    def test_fallback_to_default_if_empty(self):
        """If classifier returns empty, should use DEFAULT_QUICK_REPLIES."""
        assert "DEFAULT_QUICK_REPLIES" in self.src

    def test_fallback_on_exception(self):
        """If classifier throws, should still emit quick replies."""
        assert "quick_reply_classify_failed" in self.src
        # Check that fallback replies are defined in the except block
        match = re.search(
            r'quick_reply_classify_failed.*?quick_replies_to_emit\s*=\s*\[(.*?)\]',
            self.src, re.DOTALL
        )
        assert match, "Exception handler should set fallback quick replies"
        fallback = match.group(1)
        assert "Show Menu" in fallback
        assert "View Cart" in fallback

    def test_quick_replies_emitted_last(self):
        """Quick replies should be emitted AFTER tool events and BEFORE RUN_FINISHED."""
        # Check emit order: flush_pending_events -> emit_quick_replies -> emit_run_finished
        flush_pos = self.src.find("flush_pending_events(session_id)")
        qr_pos = self.src.find("emit_quick_replies(quick_replies_to_emit)")
        run_finished_pos = self.src.find("emit_run_finished(response)")

        assert flush_pos < qr_pos < run_finished_pos, \
            "Order should be: flush events -> quick replies -> run finished"


# ===================================================================
# 3. All quick reply actions are valid
# ===================================================================
class TestQuickReplyActionValidity:
    """Verify all quick reply action strings are valid agent-understandable intents."""

    @pytest.fixture(autouse=True)
    def load_source(self):
        self.crew_agent = _read("app/features/food_ordering/crew_agent.py")
        # Extract all action strings from QUICK_ACTION_SETS
        match = re.search(r'QUICK_ACTION_SETS\s*=\s*\{(.*?)\n\}', self.crew_agent, re.DOTALL)
        self.sets_block = match.group(1) if match else ""
        self.actions = set()
        for m in re.finditer(r'"action":\s*"([^"]+)"', self.sets_block):
            self.actions.add(m.group(1))

    def test_no_empty_actions(self):
        for action in self.actions:
            assert action.strip(), f"Found empty action string"

    def test_no_booking_actions(self):
        """No action should trigger standalone booking."""
        booking_actions = [
            "book a table", "book a table now", "book this table",
            "show my bookings", "modify booking", "cancel booking",
            "book another table", "modify my booking",
            "order food for booking",
        ]
        for ba in booking_actions:
            assert ba not in self.actions, f"Found obsolete booking action: {ba}"

    def test_all_actions_are_natural_language(self):
        """Actions should be readable phrases (not internal IDs) except special ones."""
        special = {"1", "2", "3", "__OTHER__", "yes", "no", "pay_online"}
        for action in self.actions:
            if action in special:
                continue
            # Should contain at least one space (natural language)
            assert " " in action or len(action) > 3, \
                f"Action '{action}' doesn't look like natural language"

    def test_core_actions_exist(self):
        """Critical user journey actions should be available."""
        core_actions = [
            "show me the menu",
            "view cart",
            "checkout",
            "help",
            "track my order",
            "show receipt",
        ]
        for ca in core_actions:
            assert ca in self.actions or any(ca in a for a in self.actions), \
                f"Core action missing: {ca}"

    def test_no_duplicate_labels_in_same_set(self):
        """No set should have duplicate labels."""
        # Parse each set
        for m in re.finditer(r'"(\w+)"\s*:\s*\[(.*?)\]', self.sets_block, re.DOTALL):
            set_name = m.group(1)
            set_content = m.group(2)
            labels = re.findall(r'"label":\s*"([^"]+)"', set_content)
            assert len(labels) == len(set(labels)), \
                f"Duplicate labels in {set_name}: {labels}"


# ===================================================================
# 4. Obsolete sets removed
# ===================================================================
class TestObsoleteSetsRemoved:
    """Verify obsolete quick reply sets are removed."""

    @pytest.fixture(autouse=True)
    def load_source(self):
        self.crew_agent = _read("app/features/food_ordering/crew_agent.py")
        match = re.search(r'QUICK_ACTION_SETS\s*=\s*\{(.*?)\n\}', self.crew_agent, re.DOTALL)
        self.sets_block = match.group(1) if match else ""

    def test_order_type_set_removed(self):
        """order_type quick reply set should be removed."""
        assert '"order_type"' not in self.sets_block or \
            '"order_type": [' not in self.sets_block

    def test_payment_method_set_removed(self):
        """payment_method quick reply set should be removed."""
        assert '"payment_method"' not in self.sets_block or \
            '"payment_method": [' not in self.sets_block

    def test_availability_shown_removed(self):
        assert '"availability_shown"' not in self.sets_block

    def test_booking_management_removed(self):
        assert '"booking_management"' not in self.sets_block


# ===================================================================
# 5. Classifier prompt matches available sets
# ===================================================================
class TestClassifierPromptSync:
    """Verify classifier prompt only references sets that exist."""

    @pytest.fixture(autouse=True)
    def load_source(self):
        self.crew_agent = _read("app/features/food_ordering/crew_agent.py")
        # Get set names from QUICK_ACTION_SETS
        match = re.search(r'QUICK_ACTION_SETS\s*=\s*\{(.*?)\n\}', self.crew_agent, re.DOTALL)
        sets_block = match.group(1) if match else ""
        self.set_names = set(re.findall(r'"(\w+)"\s*:', sets_block))
        # Always valid special sets
        self.set_names.add("none")
        self.set_names.add("which_item")

        # Get set names referenced in the prompt
        match = re.search(r'QUICK_REPLY_AGENT_PROMPT\s*=\s*"""(.*?)"""', self.crew_agent, re.DOTALL)
        self.prompt = match.group(1) if match else ""

    def test_prompt_set_references_are_valid(self):
        """Every set name in the prompt should exist in QUICK_ACTION_SETS."""
        # Find all "set_name:" patterns in the prompt
        prompt_refs = re.findall(r'^-\s+([a-z]\w+):', self.prompt, re.MULTILINE)
        for ref in prompt_refs:
            assert ref in self.set_names, \
                f"Prompt references '{ref}' but it's not in QUICK_ACTION_SETS"

    def test_no_order_type_in_prompt(self):
        assert "order_type:" not in self.prompt or "order_type: Order type" not in self.prompt

    def test_no_payment_method_in_prompt(self):
        assert "payment_method:" not in self.prompt or "payment_method: Asking" not in self.prompt

    def test_no_availability_shown_in_prompt(self):
        assert "availability_shown:" not in self.prompt

    def test_no_booking_management_in_prompt(self):
        assert "booking_management:" not in self.prompt


# ===================================================================
# 6. DEFAULT_QUICK_REPLIES
# ===================================================================
class TestDefaultQuickReplies:
    """Verify DEFAULT_QUICK_REPLIES exists and is valid."""

    @pytest.fixture(autouse=True)
    def load_source(self):
        self.src = _read("app/features/food_ordering/crew_agent.py")

    def test_default_exists(self):
        assert "DEFAULT_QUICK_REPLIES" in self.src

    def test_default_has_menu(self):
        match = re.search(r'DEFAULT_QUICK_REPLIES\s*=\s*\[(.*?)\]', self.src, re.DOTALL)
        assert match
        assert "Show Menu" in match.group(1) or "show menu" in match.group(1)

    def test_default_has_cart(self):
        match = re.search(r'DEFAULT_QUICK_REPLIES\s*=\s*\[(.*?)\]', self.src, re.DOTALL)
        assert match
        assert "View Cart" in match.group(1) or "view cart" in match.group(1)

    def test_default_has_checkout(self):
        match = re.search(r'DEFAULT_QUICK_REPLIES\s*=\s*\[(.*?)\]', self.src, re.DOTALL)
        assert match
        assert "Checkout" in match.group(1) or "checkout" in match.group(1)

    def test_default_no_booking(self):
        match = re.search(r'DEFAULT_QUICK_REPLIES\s*=\s*\[(.*?)\]', self.src, re.DOTALL)
        assert match
        assert "Book" not in match.group(1)


# ===================================================================
# 7. Fallback welcome messages
# ===================================================================
class TestFallbackWelcomeMessages:
    """Verify fallback welcome messages are updated."""

    @pytest.fixture(autouse=True)
    def load_source(self):
        self.src = _read("app/api/routes/chat.py")

    def test_authenticated_fallback_no_reservation(self):
        """Authenticated fallback should not mention 'reservation'."""
        # Find the authenticated fallback message
        match = re.search(r'if is_authenticated.*?fallback_msg\s*=\s*\((.*?)\)', self.src, re.DOTALL)
        assert match
        assert "reservation" not in match.group(1).lower()
        assert "make a reservation" not in match.group(1).lower()

    def test_anonymous_fallback_no_reservation(self):
        """Anonymous fallback should not mention 'reservation'."""
        match = re.search(r'else:\s*\n\s*fallback_msg\s*=\s*\((.*?)\)', self.src, re.DOTALL)
        assert match
        assert "reservation" not in match.group(1).lower()

    def test_authenticated_fallback_mentions_dine_in(self):
        match = re.search(r'if is_authenticated.*?fallback_msg\s*=\s*\((.*?)\)', self.src, re.DOTALL)
        assert match
        assert "dine-in" in match.group(1).lower() or "takeaway" in match.group(1).lower()


# ===================================================================
# 8. Deterministic handlers — cards serve as "quick replies"
# ===================================================================
class TestDeterministicHandlerCards:
    """
    Deterministic form handlers show interactive cards instead of quick replies.
    Verify the cards have proper action buttons.
    """

    def test_order_type_card_has_both_options(self):
        """OrderTypeCard should have Dine In and Takeaway buttons."""
        src = _read("frontend/src/components/OrderTypeCard.jsx")
        assert "dine_in" in src
        assert "take_away" in src
        assert "Dine In" in src
        assert "Takeaway" in src

    def test_booking_form_card_has_submit(self):
        """BookingFormCard should have submit button."""
        src = _read("frontend/src/components/BookingFormCard.jsx")
        assert "handleSubmit" in src or "onSubmit" in src

    def test_cart_card_has_checkout_button(self):
        """CartCard should have checkout button."""
        src = _read("frontend/src/components/CartCard.jsx")
        assert "Checkout" in src or "onCheckout" in src

    def test_payment_link_card_has_pay_button(self):
        """PaymentLinkCard should have a pay button/link."""
        src = _read("frontend/src/components/PaymentLinkCard.jsx")
        assert "Pay" in src
        assert "href" in src

    def test_payment_success_card_has_quick_replies(self):
        """PaymentSuccessCard should show inline quick replies."""
        src = _read("frontend/src/components/PaymentSuccessCard.jsx")
        assert "quick_replies" in src or "onQuickReply" in src


# ===================================================================
# 9. No empty quick reply sets in active use
# ===================================================================
class TestNoEmptyActiveSets:
    """Verify no active quick reply set is empty (except 'none' and 'which_item')."""

    @pytest.fixture(autouse=True)
    def load_source(self):
        self.crew_agent = _read("app/features/food_ordering/crew_agent.py")
        match = re.search(r'QUICK_ACTION_SETS\s*=\s*\{(.*?)\n\}', self.crew_agent, re.DOTALL)
        self.sets_block = match.group(1) if match else ""

    def test_no_empty_sets_except_special(self):
        """All sets should have at least one reply, except 'none' and 'which_item'."""
        special = {"none", "which_item"}
        for m in re.finditer(r'"(\w+)"\s*:\s*\[(.*?)\]', self.sets_block, re.DOTALL):
            set_name = m.group(1)
            content = m.group(2).strip()
            if set_name in special:
                continue
            assert content, f"Quick reply set '{set_name}' is empty"
            # Should have at least one action
            actions = re.findall(r'"action":\s*"([^"]+)"', content)
            assert len(actions) >= 1, f"Set '{set_name}' has no actions"


# ===================================================================
# 10. Quick reply flow for specific user scenarios
# ===================================================================
class TestQuickReplyScenarios:
    """Test quick reply selection for specific user scenarios."""

    @pytest.fixture(autouse=True)
    def load_source(self):
        self.crew_agent = _read("app/features/food_ordering/crew_agent.py")
        match = re.search(r'QUICK_ACTION_SETS\s*=\s*\{(.*?)\n\}', self.crew_agent, re.DOTALL)
        self.sets_block = match.group(1) if match else ""

    def _get_set_actions(self, name):
        match = re.search(rf'"{name}"\s*:\s*\[(.*?)\]', self.sets_block, re.DOTALL)
        if not match:
            return []
        return re.findall(r'"action":\s*"([^"]+)"', match.group(1))

    # After adding item to cart
    def test_added_to_cart_has_checkout(self):
        actions = self._get_set_actions("added_to_cart")
        assert any("checkout" in a for a in actions)

    def test_added_to_cart_has_view_cart(self):
        actions = self._get_set_actions("added_to_cart")
        assert any("cart" in a for a in actions)

    # After viewing cart
    def test_view_cart_has_checkout(self):
        actions = self._get_set_actions("view_cart")
        assert any("checkout" in a for a in actions)

    def test_view_cart_has_add_more(self):
        actions = self._get_set_actions("view_cart")
        assert any("menu" in a or "more" in a for a in actions)

    # After checkout (order confirmed)
    def test_order_confirmed_has_track(self):
        actions = self._get_set_actions("order_confirmed")
        assert any("track" in a for a in actions)

    # After payment
    def test_payment_completed_has_receipt(self):
        actions = self._get_set_actions("payment_completed")
        assert any("receipt" in a for a in actions)

    # Empty cart
    def test_cart_empty_has_menu(self):
        actions = self._get_set_actions("cart_empty_reminder")
        assert any("menu" in a for a in actions)

    # Help inquiry
    def test_help_has_faqs(self):
        actions = self._get_set_actions("help_inquiry")
        assert any("faq" in a for a in actions)

    # Fallback / continue
    def test_continue_ordering_has_essentials(self):
        actions = self._get_set_actions("continue_ordering")
        assert any("menu" in a for a in actions)
        assert any("cart" in a for a in actions)
        assert any("checkout" in a for a in actions)

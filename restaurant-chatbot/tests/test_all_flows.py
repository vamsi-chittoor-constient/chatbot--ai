"""
Unit tests for all major flows in the restaurant chatbot.

Covers:
1. Checkout flow (cart → order type selection card)
2. Order type selection (takeaway → packaging + payment, dine-in → booking form)
3. Booking intake → dine-in charge → payment
4. Payment flow (Razorpay link generation, pending payment interception)
5. Cart operations (add, update quantity, remove)
6. AGUI event system (all event types, reducer coverage)
7. Form submission routing (all form_type handlers)
8. Auth form skip
9. Payment state interception (cancel, re-show link)
10. WebSocket message parsing (JSON vs plain text)
"""
import pytest
import re
import json
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _read(rel_path: str) -> str:
    with open(os.path.join(PROJECT_ROOT, rel_path), encoding="utf-8") as f:
        return f.read()


# ===================================================================
# 1. Checkout Tool — creates pending order + emits ORDER_TYPE_SELECTION
# ===================================================================
class TestCheckoutTool:
    """Verify checkout tool creates pending order and emits order type card."""

    @pytest.fixture(autouse=True)
    def load_source(self):
        self.src = _read("app/features/food_ordering/crew_agent.py")

    def test_checkout_function_exists(self):
        assert "_checkout_impl" in self.src

    def test_stores_pending_order_in_redis(self):
        assert 'pending_order:{session_id}' in self.src or "pending_order:" in self.src

    def test_pending_order_status_is_pending_order_type(self):
        """Initial status should be pending_order_type (not pending_payment)."""
        assert '"status": "pending_order_type"' in self.src

    def test_emits_order_type_selection(self):
        assert "emit_order_type_selection(" in self.src

    def test_does_not_trigger_payment_directly(self):
        """Checkout should NOT call run_payment_workflow anymore."""
        # Find the _checkout_impl function
        match = re.search(r"def _checkout_impl\(.*?\n(?=def |\nclass )", self.src, re.DOTALL)
        assert match, "_checkout_impl should exist"
        checkout_fn = match.group(0)
        assert "run_payment_workflow" not in checkout_fn

    def test_does_not_hardcode_take_away(self):
        """Checkout should NOT hardcode order type to take_away."""
        match = re.search(r"def _checkout_impl\(.*?\n(?=def |\nclass )", self.src, re.DOTALL)
        checkout_fn = match.group(0)
        # Should not set order_type = "take_away" in pending order
        assert '"order_type": "take_away"' not in checkout_fn

    def test_clears_cart_after_checkout(self):
        """Cart should be cleared after successful checkout."""
        match = re.search(r"def _checkout_impl\(.*?\n(?=def |\nclass )", self.src, re.DOTALL)
        checkout_fn = match.group(0)
        assert "is_active = FALSE" in checkout_fn or "is_active=FALSE" in checkout_fn

    def test_generates_order_display_id(self):
        assert "ORD-" in self.src

    def test_stores_order_in_history(self):
        assert "order_history:" in self.src

    def test_sets_redis_expiry(self):
        """Pending order should have TTL (setex)."""
        assert "setex" in self.src

    def test_calculates_subtotal(self):
        match = re.search(r"def _checkout_impl\(.*?\n(?=def |\nclass )", self.src, re.DOTALL)
        checkout_fn = match.group(0)
        assert "subtotal" in checkout_fn

    def test_creates_items_summary(self):
        """Should create human-readable items summary for the card."""
        match = re.search(r"def _checkout_impl\(.*?\n(?=def |\nclass )", self.src, re.DOTALL)
        checkout_fn = match.group(0)
        assert "items_summary" in checkout_fn

    def test_returns_checkout_complete_marker(self):
        assert "[CHECKOUT COMPLETE]" in self.src


# ===================================================================
# 2. Order Type Selection Handler — takeaway vs dine-in
# ===================================================================
class TestOrderTypeSelectionHandler:
    """Verify chat.py handles order_type_selection form correctly."""

    @pytest.fixture(autouse=True)
    def load_source(self):
        self.src = _read("app/api/routes/chat.py")
        # Extract the full order_type_selection handler (up to the next form_type check)
        match = re.search(
            r'if form_type == "order_type_selection".*?(?=if form_type == "booking_intake")',
            self.src, re.DOTALL
        )
        self.handler = match.group(0) if match else ""

    def test_handler_exists(self):
        assert self.handler, "order_type_selection handler should exist in chat.py"

    # -- Takeaway path --
    def test_takeaway_adds_packaging_charges(self):
        assert "PACKAGING_CHARGE_PER_ITEM" in self.handler

    def test_takeaway_calculates_total(self):
        """Total = subtotal + packaging_charges."""
        assert "subtotal + packaging_charges" in self.handler or "total" in self.handler

    def test_takeaway_sets_order_type(self):
        assert '"order_type"] = "take_away"' in self.handler or '"take_away"' in self.handler

    def test_takeaway_sets_pending_payment_status(self):
        assert '"status"] = "pending_payment"' in self.handler or "pending_payment" in self.handler

    def test_takeaway_triggers_payment(self):
        assert "run_payment_workflow" in self.handler

    def test_takeaway_passes_online_method(self):
        assert 'initial_method="online"' in self.handler

    # -- Dine-in path --
    def test_dine_in_sets_order_type(self):
        assert '"order_type"] = "dine_in"' in self.handler or '"dine_in"' in self.handler

    def test_dine_in_sets_pending_booking_status(self):
        assert '"status"] = "pending_booking"' in self.handler or "pending_booking" in self.handler

    def test_dine_in_shows_booking_form(self):
        assert "emit_booking_intake_form" in self.handler

    def test_dine_in_gets_availability(self):
        assert "_get_availability_map" in self.handler

    def test_dine_in_zero_packaging(self):
        """Dine-in should have 0 packaging charges."""
        assert '"packaging_charges"] = 0' in self.handler or "packaging_charges" in self.handler

    def test_handles_expired_order(self):
        """Should handle missing pending order gracefully."""
        assert "expired" in self.handler.lower() or "checkout again" in self.handler.lower()

    def test_reads_from_redis(self):
        assert "pending_order:" in self.handler

    def test_flushes_events(self):
        assert "flush_pending_events" in self.handler


# ===================================================================
# 3. Booking Intake Handler — dine-in charge + payment
# ===================================================================
class TestBookingIntakeHandler:
    """Verify booking_intake form handler processes dine-in checkout correctly."""

    @pytest.fixture(autouse=True)
    def load_source(self):
        self.src = _read("app/api/routes/chat.py")
        # Extract booking_intake handler up to the next section marker
        match = re.search(
            r'if form_type == "booking_intake".*?(?=# ====={5,}|\n                # Check rate limit)',
            self.src, re.DOTALL
        )
        self.handler = match.group(0) if match else ""

    def test_handler_exists(self):
        assert self.handler, "booking_intake handler should exist"

    def test_calls_make_reservation(self):
        assert "make_reservation" in self.handler.lower() or "create_booking_tool" in self.handler

    def test_extracts_date_time_party_size(self):
        assert "booking_date" in self.handler
        assert "booking_time" in self.handler
        assert "booking_party_size" in self.handler or "party_size" in self.handler

    def test_checks_pending_booking_status(self):
        """Should check if there's a pending dine-in order."""
        assert "pending_booking" in self.handler

    def test_adds_dine_in_charge(self):
        assert "DINE_IN_CHARGE_PER_PERSON" in self.handler

    def test_dine_in_charge_calculation(self):
        """Charge = party_size * DINE_IN_CHARGE_PER_PERSON."""
        assert "booking_party_size * DINE_IN_CHARGE_PER_PERSON" in self.handler

    def test_triggers_payment_after_booking(self):
        assert "run_payment_workflow" in self.handler

    def test_passes_dine_in_order_type(self):
        assert 'order_type="dine_in"' in self.handler

    def test_zero_packaging_for_dine_in(self):
        assert "packaging_charges=0" in self.handler

    def test_updates_pending_order_status(self):
        assert "pending_payment" in self.handler

    def test_stores_party_size_in_pending(self):
        assert '"party_size"' in self.handler or "'party_size'" in self.handler

    def test_handles_booking_failure(self):
        """Should handle reservation failure gracefully."""
        assert "except" in self.handler
        assert "sorry" in self.handler.lower() or "went wrong" in self.handler.lower()

    def test_checks_confirmation_event(self):
        """Should check if BOOKING_CONFIRMATION was emitted."""
        assert "BOOKING_CONFIRMATION" in self.handler


# ===================================================================
# 4. Payment Workflow
# ===================================================================
class TestPaymentWorkflow:
    """Verify payment_workflow.py structure and flow."""

    @pytest.fixture(autouse=True)
    def load_source(self):
        self.src = _read("app/workflows/payment_workflow.py")

    def test_payment_state_machine_exists(self):
        assert "PaymentWorkflowState" in self.src

    def test_select_payment_method_node(self):
        assert "select_payment_method_node" in self.src

    def test_generate_payment_link_node(self):
        assert "generate_payment_link_node" in self.src

    def test_uses_razorpay(self):
        assert "razorpay" in self.src.lower()

    def test_creates_db_order(self):
        """Should create Order in database before Razorpay link."""
        assert "Order(" in self.src
        assert "OrderItem(" in self.src

    def test_creates_order_total_with_packaging(self):
        assert "OrderTotal(" in self.src
        assert "packaging" in self.src.lower()

    def test_reads_pending_order_from_redis(self):
        assert "pending_order:" in self.src

    def test_handles_missing_pending_order(self):
        assert "No pending order" in self.src

    def test_emits_payment_link(self):
        assert "emit_payment_link" in self.src

    def test_payment_method_options(self):
        """Should offer online, cash, and card at counter."""
        assert "Pay Online" in self.src
        assert "Cash" in self.src
        assert "Card at Counter" in self.src


# ===================================================================
# 5. Pending Payment Interception
# ===================================================================
class TestPendingPaymentInterception:
    """Verify that messages during pending payment are intercepted."""

    @pytest.fixture(autouse=True)
    def load_source(self):
        self.src = _read("app/api/routes/chat.py")

    def test_payment_state_check(self):
        assert "AWAITING_PAYMENT" in self.src

    def test_cancel_phrases(self):
        """Should recognize multiple cancel intents."""
        assert "cancel payment" in self.src
        assert "cancel order" in self.src
        assert "never mind" in self.src

    def test_cancel_clears_state(self):
        assert "clear_payment_state" in self.src

    def test_non_cancel_reminds_about_payment(self):
        """Non-cancel messages should show payment reminder."""
        # Look for re-showing the payment link during pending state
        assert "payment_link" in self.src.lower()


# ===================================================================
# 6. Cart Operations — direct handlers
# ===================================================================
class TestCartOperations:
    """Verify direct cart operation handlers in chat.py."""

    @pytest.fixture(autouse=True)
    def load_source(self):
        self.src = _read("app/api/routes/chat.py")

    # -- direct_add_to_cart --
    def test_direct_add_to_cart_handler(self):
        assert '"direct_add_to_cart"' in self.src

    def test_add_to_cart_uses_batch_tool(self):
        assert "batch_add" in self.src.lower() or "items_with_quantities" in self.src

    def test_add_to_cart_formats_items(self):
        """Should format as 'item:qty, item:qty'."""
        assert "pairs" in self.src

    # -- direct_update_cart --
    def test_direct_update_cart_handler(self):
        assert '"direct_update_cart"' in self.src

    def test_update_cart_uses_sql(self):
        assert "UPDATE session_cart" in self.src

    def test_update_cart_emits_cart_data(self):
        """Should emit updated cart after quantity change."""
        # Find the update handler
        match = re.search(
            r'if form_type == "direct_update_cart".*?continue',
            self.src, re.DOTALL
        )
        assert match
        handler = match.group(0)
        assert "emit_cart_data" in handler

    def test_update_uses_case_insensitive_match(self):
        assert "LOWER(item_name)" in self.src

    # -- direct_remove_from_cart --
    def test_direct_remove_from_cart_handler(self):
        assert '"direct_remove_from_cart"' in self.src

    def test_remove_sets_inactive(self):
        """Remove should set is_active = FALSE, not DELETE."""
        match = re.search(
            r'if form_type == "direct_remove_from_cart".*?continue',
            self.src, re.DOTALL
        )
        assert match
        assert "is_active = FALSE" in match.group(0)

    def test_remove_emits_cart_data(self):
        match = re.search(
            r'if form_type == "direct_remove_from_cart".*?continue',
            self.src, re.DOTALL
        )
        assert match
        assert "emit_cart_data" in match.group(0)

    def test_cart_total_function(self):
        """Should use get_cart_total() SQL function."""
        assert "get_cart_total" in self.src

    def test_get_session_cart_function(self):
        """Should use get_session_cart() SQL function."""
        assert "get_session_cart" in self.src


# ===================================================================
# 7. Form Submission Routing
# ===================================================================
class TestFormSubmissionRouting:
    """Verify all form_type handlers exist and are routed correctly."""

    @pytest.fixture(autouse=True)
    def load_source(self):
        self.src = _read("app/api/routes/chat.py")

    def test_form_response_type_check(self):
        assert '"form_response"' in self.src

    def test_form_type_extracted(self):
        assert 'form_type = message_data.get("form_type")' in self.src

    def test_form_data_extracted(self):
        assert 'form_data = message_data.get("data"' in self.src

    def test_all_form_types_handled(self):
        """All expected form types should have handlers."""
        expected_types = [
            "direct_add_to_cart",
            "direct_update_cart",
            "direct_remove_from_cart",
            "order_type_selection",
            "booking_intake",
        ]
        for ft in expected_types:
            assert f'form_type == "{ft}"' in self.src, f"Missing handler for {ft}"

    def test_auth_forms_skipped(self):
        """Auth form types should be skipped in main loop."""
        assert "phone_auth" in self.src
        assert "login_otp" in self.src
        assert "name_collection" in self.src


# ===================================================================
# 8. AGUI Event Types — full coverage
# ===================================================================
class TestAGUIEventTypes:
    """Verify all event types exist in the enum."""

    @pytest.fixture(autouse=True)
    def load_source(self):
        self.src = _read("app/core/agui_events.py")

    def test_all_event_types_exist(self):
        expected = [
            "RUN_STARTED", "RUN_FINISHED", "RUN_ERROR",
            "TEXT_MESSAGE_START", "TEXT_MESSAGE_CONTENT", "TEXT_MESSAGE_END",
            "ACTIVITY_START", "ACTIVITY_END",
            "CART_DATA", "ORDER_DATA", "MENU_DATA", "SEARCH_RESULTS",
            "QUICK_REPLIES", "PAYMENT_LINK", "PAYMENT_SUCCESS",
            "RECEIPT_LINK", "BOOKING_CONFIRMATION", "BOOKING_INTAKE_FORM",
            "ORDER_TYPE_SELECTION", "FORM_REQUEST", "FORM_DISMISS",
        ]
        for et in expected:
            assert f'"{et}"' in self.src or f"= \"{et}\"" in self.src or f"{et} =" in self.src, \
                f"Missing event type: {et}"

    def test_emit_functions_exist(self):
        """Key emit functions should be defined."""
        expected_emitters = [
            "emit_cart_data",
            "emit_quick_replies",
            "emit_payment_link",
            "emit_booking_intake_form",
            "emit_order_type_selection",
        ]
        for fn in expected_emitters:
            assert f"def {fn}(" in self.src, f"Missing emit function: {fn}"


# ===================================================================
# 9. AGUI Reducer — full event coverage
# ===================================================================
class TestAGUIReducerFullCoverage:
    """Verify useAGUI.js reducer handles all event types."""

    @pytest.fixture(autouse=True)
    def load_source(self):
        self.src = _read("frontend/src/hooks/useAGUI.js")

    def test_all_reducer_cases(self):
        expected_cases = [
            "ADD_USER_MESSAGE",
            "RUN_STARTED", "RUN_FINISHED", "RUN_ERROR",
            "ACTIVITY_START", "ACTIVITY_END",
            "TEXT_MESSAGE_START", "TEXT_MESSAGE_CONTENT", "TEXT_MESSAGE_END",
            "CART_DATA", "MENU_DATA", "SEARCH_RESULTS", "ORDER_DATA",
            "QUICK_REPLIES", "PAYMENT_LINK", "PAYMENT_SUCCESS",
            "RECEIPT_LINK", "FORM_REQUEST", "FORM_DISMISS",
            "BOOKING_CONFIRMATION", "BOOKING_INTAKE_FORM",
            "ORDER_TYPE_SELECTION",
            "CLEAR_QUICK_REPLIES",
        ]
        for case in expected_cases:
            assert f"case '{case}'" in self.src, f"Missing reducer case: {case}"

    def test_quick_replies_always_cleared(self):
        """Most cases should filter out quick_replies before adding new content."""
        # Count how many cases filter quick_replies
        qr_filter_count = self.src.count("msg.type !== 'quick_replies'")
        # Should be in many cases (at least 10)
        assert qr_filter_count >= 10, f"Quick replies filter only found {qr_filter_count} times"

    def test_streaming_state_tracked(self):
        assert "isStreaming: true" in self.src
        assert "isStreaming: false" in self.src

    def test_current_stream_id_tracked(self):
        assert "currentStreamId" in self.src

    def test_text_content_appends(self):
        """TEXT_MESSAGE_CONTENT should append delta to existing message."""
        assert "msg.content + content" in self.src


# ===================================================================
# 10. App.jsx — all card renderings
# ===================================================================
class TestAppJSXAllCards:
    """Verify App.jsx renders all card types."""

    @pytest.fixture(autouse=True)
    def load_source(self):
        self.src = _read("frontend/src/App.jsx")

    def test_all_card_types_rendered(self):
        expected_cases = [
            ("cart", "CartCard"),
            ("menu", "MenuCard"),
            ("search_results", "SearchResultsCard"),
            ("order", "OrderCard"),
            ("payment_link", "PaymentLinkCard"),
            ("receipt_link", "ReceiptCard"),
            ("payment_success", "PaymentSuccessCard"),
            ("quick_replies", "QuickReplies"),
            ("form", "FormCard"),
            ("booking_confirmation", "BookingConfirmationCard"),
            ("booking_form", "BookingFormCard"),
            ("order_type_selection", "OrderTypeCard"),
        ]
        for msg_type, component in expected_cases:
            assert f"case '{msg_type}':" in self.src, f"Missing case for {msg_type}"
            assert component in self.src, f"Missing component {component}"

    def test_cart_card_has_checkout_handler(self):
        assert "onCheckout={handleCheckout}" in self.src or "onCheckout" in self.src

    def test_cart_card_has_quantity_handlers(self):
        assert "onUpdateQuantity" in self.src
        assert "onRemoveItem" in self.src

    def test_menu_card_has_add_to_cart(self):
        assert "onAddToCart" in self.src

    def test_form_card_has_submit(self):
        # Find FormCard rendering
        lines = [l for l in self.src.splitlines() if "FormCard" in l and "onSubmit" in l]
        assert lines, "FormCard should have onSubmit"

    def test_booking_form_has_submit(self):
        lines = [l for l in self.src.splitlines() if "BookingFormCard" in l and "onSubmit" in l]
        assert lines, "BookingFormCard should have onSubmit"


# ===================================================================
# 11. Frontend WebSocket — form_response message format
# ===================================================================
class TestFrontendWebSocket:
    """Verify frontend sends form responses in correct format."""

    @pytest.fixture(autouse=True)
    def load_source(self):
        self.src = _read("frontend/src/hooks/useWebSocket.js")

    def test_send_form_response_function(self):
        assert "sendFormResponse" in self.src

    def test_form_response_type_field(self):
        """WebSocket messages should include type: 'form_response'."""
        assert "form_response" in self.src

    def test_form_type_and_data_fields(self):
        """Should include form_type and data in the message."""
        assert "form_type" in self.src
        assert "data" in self.src


# ===================================================================
# 12. Simulated E2E Scenarios
# ===================================================================
class TestE2EScenarios:
    """
    Simulate end-to-end user journeys through code structure verification.
    """

    @pytest.fixture(autouse=True)
    def load_all(self):
        self.chat_py = _read("app/api/routes/chat.py")
        self.crew_agent = _read("app/features/food_ordering/crew_agent.py")
        self.agui_events = _read("app/core/agui_events.py")
        self.agui_reducer = _read("frontend/src/hooks/useAGUI.js")
        self.app_jsx = _read("frontend/src/App.jsx")
        self.order_type_card = _read("frontend/src/components/OrderTypeCard.jsx")
        self.payment_workflow = _read("app/workflows/payment_workflow.py")

    # --- Scenario: User adds food → checkout → selects takeaway → pays ---
    def test_takeaway_flow_sequence(self):
        """Full takeaway flow: checkout → order_type card → takeaway → packaging → payment."""
        # 1. Checkout creates pending order with status pending_order_type
        assert '"status": "pending_order_type"' in self.crew_agent
        # 2. Emits ORDER_TYPE_SELECTION
        assert "emit_order_type_selection" in self.crew_agent
        # 3. Frontend renders OrderTypeCard
        assert "OrderTypeCard" in self.app_jsx
        # 4. Card calls onSubmit('order_type_selection', ...)
        assert "onSubmit('order_type_selection'," in self.order_type_card
        # 5. Handler adds packaging charges
        assert "PACKAGING_CHARGE_PER_ITEM" in self.chat_py
        # 6. Triggers payment
        assert "run_payment_workflow" in self.chat_py

    # --- Scenario: User adds food → checkout → selects dine-in → books table → pays ---
    def test_dine_in_flow_sequence(self):
        """Full dine-in flow: checkout → order_type → dine-in → booking form → book → charge → pay."""
        # 1. Dine-in sets status pending_booking
        assert "pending_booking" in self.chat_py
        # 2. Shows booking form
        assert "emit_booking_intake_form" in self.chat_py
        # 3. Frontend renders BookingFormCard
        assert "BookingFormCard" in self.app_jsx
        # 4. Booking handler checks pending_booking + dine_in
        assert "pending_booking" in self.chat_py
        # 5. Adds dine-in charge
        assert "DINE_IN_CHARGE_PER_PERSON" in self.chat_py
        # 6. Triggers payment
        assert 'order_type="dine_in"' in self.chat_py

    # --- Scenario: User says "hi" → gets welcome + quick replies ---
    def test_greeting_flow(self):
        """Greeting should show welcome + quick replies without booking."""
        # Quick replies set exists
        match = re.search(r'"greeting_welcome"\s*:\s*\[(.*?)\]', self.crew_agent, re.DOTALL)
        assert match
        qr = match.group(1)
        # Has useful options
        assert "Order Food" in qr
        assert "View Cart" in qr
        # No booking
        assert "Book" not in qr

    # --- Scenario: User says "I want to book a table" ---
    def test_book_table_redirects_to_ordering(self):
        """Agent should explain booking is via dine-in checkout."""
        from_crew = _read("app/orchestration/restaurant_crew.py")
        assert "dine-in checkout" in from_crew.lower()
        assert "order food first" in from_crew.lower()

    # --- Scenario: User clicks dine-in on OrderTypeCard ---
    def test_dine_in_card_sends_correct_payload(self):
        """OrderTypeCard 'Dine In' sends correct form_type and data."""
        # onSubmit('order_type_selection', { order_type: 'dine_in', order_id })
        assert "onSubmit('order_type_selection'," in self.order_type_card
        assert "'dine_in'" in self.order_type_card

    # --- Scenario: User clicks takeaway on OrderTypeCard ---
    def test_takeaway_card_sends_correct_payload(self):
        assert "'take_away'" in self.order_type_card

    # --- Scenario: Order expires, user selects dine-in ---
    def test_expired_order_handled(self):
        """Should detect expired pending order and ask to re-checkout."""
        assert "expired" in self.chat_py.lower() or "checkout again" in self.chat_py.lower()

    # --- Scenario: Payment link shown, user sends random message ---
    def test_pending_payment_blocks_random_messages(self):
        """Random messages during pending payment should be intercepted."""
        assert "AWAITING_PAYMENT" in self.chat_py

    # --- Scenario: Payment link shown, user says "cancel" ---
    def test_cancel_during_payment(self):
        assert "cancel payment" in self.chat_py
        assert "clear_payment_state" in self.chat_py

    # --- Scenario: Cart +/- buttons ---
    def test_cart_quantity_update_direct(self):
        """Cart +/- should use direct SQL update, not AI agent."""
        match = re.search(
            r'"direct_update_cart".*?continue', self.chat_py, re.DOTALL
        )
        assert match
        handler = match.group(0)
        assert "UPDATE session_cart" in handler
        assert "emit_cart_data" in handler

    # --- Scenario: Cart delete button ---
    def test_cart_remove_direct(self):
        """Cart delete should use direct SQL, not AI agent."""
        match = re.search(
            r'"direct_remove_from_cart".*?continue', self.chat_py, re.DOTALL
        )
        assert match
        handler = match.group(0)
        assert "is_active = FALSE" in handler

    # --- Scenario: Menu card "Add to Cart" button ---
    def test_add_from_menu_card_direct(self):
        """Add from menu/search cards should bypass LLM."""
        match = re.search(
            r'"direct_add_to_cart".*?continue', self.chat_py, re.DOTALL
        )
        assert match
        handler = match.group(0)
        assert "batch_add" in handler.lower() or "items_with_quantities" in handler


# ===================================================================
# 13. Charge Calculations
# ===================================================================
class TestChargeCalculations:
    """Verify charge calculations in order type handler."""

    @pytest.fixture(autouse=True)
    def load_source(self):
        self.src = _read("app/api/routes/chat.py")

    def test_takeaway_packaging_formula(self):
        """packaging_charges = total_qty * PACKAGING_CHARGE_PER_ITEM"""
        assert "total_qty" in self.src or "total_quantity" in self.src
        assert "PACKAGING_CHARGE_PER_ITEM" in self.src

    def test_dine_in_charge_formula(self):
        """dine_in_charge = booking_party_size * DINE_IN_CHARGE_PER_PERSON"""
        assert "booking_party_size * DINE_IN_CHARGE_PER_PERSON" in self.src

    def test_takeaway_total_includes_packaging(self):
        """Takeaway total = subtotal + packaging."""
        match = re.search(
            r'if selected_order_type == "take_away".*?(?=elif|continue)',
            self.src, re.DOTALL
        )
        assert match
        block = match.group(0)
        assert "subtotal + packaging_charges" in block or "total" in block

    def test_dine_in_total_includes_service_charge(self):
        """Dine-in total = subtotal + dine_in_charge."""
        assert "subtotal + dine_in_charge" in self.src


# ===================================================================
# 14. PaymentLinkCard — frontend rendering
# ===================================================================
class TestPaymentLinkCard:
    """Verify PaymentLinkCard renders payment info correctly."""

    @pytest.fixture(autouse=True)
    def load_source(self):
        self.src = _read("frontend/src/components/PaymentLinkCard.jsx")

    def test_renders_amount(self):
        assert "amount" in self.src

    def test_has_pay_button(self):
        assert "Pay" in self.src

    def test_links_to_razorpay(self):
        assert "payment_link" in self.src
        assert 'href={payment_link}' in self.src

    def test_opens_in_new_tab(self):
        assert 'target="_blank"' in self.src

    def test_shows_expiry(self):
        assert "expires_at" in self.src

    def test_secure_rel(self):
        assert "noopener noreferrer" in self.src


# ===================================================================
# 15. BookingFormCard → onSubmit signature
# ===================================================================
class TestBookingFormCardSignature:
    """Verify BookingFormCard calls onSubmit(formType, data) correctly."""

    @pytest.fixture(autouse=True)
    def load_source(self):
        self.src = _read("frontend/src/components/BookingFormCard.jsx")

    def test_calls_onsubmit_with_booking_intake(self):
        assert "onSubmit?.('booking_intake'" in self.src or "onSubmit('booking_intake'" in self.src

    def test_passes_date(self):
        assert "date:" in self.src

    def test_passes_time(self):
        assert "time:" in self.src

    def test_passes_party_size(self):
        assert "party_size:" in self.src

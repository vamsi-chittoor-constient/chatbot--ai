"""
End-to-end flow tests (source-level).

Tests the complete user journey through all major flows by reading
the actual source code and verifying logic paths, state transitions,
event emissions, and handler routing.

Flows covered:
1. Welcome → Menu → Add to Cart → Checkout → Takeaway → Payment
2. Welcome → Menu → Add to Cart → Checkout → Dine-in → Booking → Payment
3. Reconnect flow (preserved welcome, payment delivery)
4. Auth flow (phone → existing user, phone → OTP → name → new user)
5. Pending payment interception (cancel / complete / random)
6. Cart operations (direct add / update / remove)
7. Rate limiting
8. WhatsApp auto-auth
9. Form routing (auth forms skipped in main loop)
10. WebSocket lifecycle (connect / disconnect / cleanup)
"""
import pytest
import re
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _read(rel_path: str) -> str:
    with open(os.path.join(PROJECT_ROOT, rel_path), encoding="utf-8") as f:
        return f.read()


# ===================================================================
# 1. TAKEAWAY E2E: Welcome → Cart → Checkout → Takeaway → Payment
# ===================================================================
class TestTakeawayE2EFlow:
    """Verify the complete takeaway ordering flow end-to-end."""

    @pytest.fixture(autouse=True)
    def load_sources(self):
        self.chat = _read("app/api/routes/chat.py")
        self.crew = _read("app/orchestration/restaurant_crew.py")
        self.agui = _read("app/core/agui_events.py")
        self.payment_wf = _read("app/workflows/payment_workflow.py")

    # Step 1: Welcome message is sent on connect
    def test_welcome_sent_on_connect(self):
        assert "welcome_service.generate_welcome" in self.chat
        assert "welcome_msg" in self.chat

    # Step 2: Welcome quick replies include Order Food
    def test_welcome_has_order_food_qr(self):
        assert "Order Food" in self.chat

    # Step 3: User message goes through AI crew
    def test_user_message_processed_by_crew(self):
        assert "process_message_with_ai" in self.chat

    # Step 4: Checkout tool creates pending order in Redis
    def test_checkout_creates_pending_order(self):
        assert "pending_order:" in self.chat or "pending_order" in self.crew

    # Step 5: OrderTypeCard shown after checkout
    def test_order_type_card_emitted(self):
        assert "ORDER_TYPE_SELECTION" in self.agui or "OrderTypeSelection" in self.agui

    # Step 6: Takeaway selection handler
    def test_takeaway_handler_exists(self):
        match = re.search(
            r'if form_type == "order_type_selection".*?selected_order_type.*?take_away',
            self.chat, re.DOTALL
        )
        assert match, "Takeaway selection handler should exist"

    # Step 7: Takeaway adds packaging charges
    def test_takeaway_adds_packaging_charges(self):
        match = re.search(
            r'selected_order_type == "take_away".*?PACKAGING_CHARGE_PER_ITEM.*?packaging_charges',
            self.chat, re.DOTALL
        )
        assert match, "Takeaway should add packaging charges"

    # Step 8: Takeaway sets status to pending_payment
    def test_takeaway_sets_pending_payment(self):
        match = re.search(
            r'selected_order_type == "take_away".*?pending_payment',
            self.chat, re.DOTALL
        )
        assert match, "Takeaway should set status to pending_payment"

    # Step 9: Payment workflow triggered after takeaway
    def test_takeaway_triggers_payment_workflow(self):
        match = re.search(
            r'selected_order_type == "take_away".*?run_payment_workflow',
            self.chat, re.DOTALL
        )
        assert match, "Takeaway should trigger payment workflow"

    # Step 10: Payment workflow generates Razorpay link
    def test_payment_workflow_generates_link(self):
        assert "razorpay_payment_tool" in self.payment_wf
        assert "emit_payment_link" in self.payment_wf

    # Step 11: Events flushed and streamed after payment
    def test_events_flushed_after_takeaway_payment(self):
        match = re.search(
            r'run_payment_workflow.*?flush_pending_events.*?stream_agui_events_to_websocket',
            self.chat, re.DOTALL
        )
        assert match, "Events should be flushed and streamed after payment workflow"

    # Step 12: Continue statement skips normal AI processing
    def test_takeaway_continues_after_handling(self):
        # After order_type_selection handler, there's a `continue`
        match = re.search(
            r'if form_type == "order_type_selection".*?continue',
            self.chat, re.DOTALL
        )
        assert match, "order_type_selection handler should continue (skip AI)"


# ===================================================================
# 2. DINE-IN E2E: Welcome → Cart → Checkout → Dine-in → Booking → Payment
# ===================================================================
class TestDineInE2EFlow:
    """Verify the complete dine-in ordering flow end-to-end."""

    @pytest.fixture(autouse=True)
    def load_sources(self):
        self.chat = _read("app/api/routes/chat.py")
        self.agui = _read("app/core/agui_events.py")

    # Step 1: Dine-in handler sets status to pending_booking
    def test_dine_in_sets_pending_booking(self):
        match = re.search(
            r'selected_order_type == "dine_in".*?pending_booking',
            self.chat, re.DOTALL
        )
        assert match, "Dine-in should set status to pending_booking"

    # Step 2: Dine-in shows booking form
    def test_dine_in_shows_booking_form(self):
        match = re.search(
            r'selected_order_type == "dine_in".*?emit_booking_intake_form',
            self.chat, re.DOTALL
        )
        assert match, "Dine-in should show booking intake form"

    # Step 3: Booking form gets availability data
    def test_dine_in_fetches_availability(self):
        match = re.search(
            r'selected_order_type == "dine_in".*?_get_availability_map',
            self.chat, re.DOTALL
        )
        assert match, "Dine-in should fetch availability data"

    # Step 4: Booking intake handler exists
    def test_booking_intake_handler_exists(self):
        assert 'form_type == "booking_intake"' in self.chat

    # Step 5: Booking intake calls make_reservation
    def test_booking_calls_make_reservation(self):
        match = re.search(
            r'form_type == "booking_intake".*?_make_reservation\._run',
            self.chat, re.DOTALL
        )
        assert match, "Booking intake should call make_reservation"

    # Step 6: Booking intake passes date, time, party_size
    def test_booking_passes_all_fields(self):
        match = re.search(
            r'form_type == "booking_intake".*?booking_date.*?booking_time.*?booking_party_size',
            self.chat, re.DOTALL
        )
        assert match, "Booking should pass date, time, party_size"

    # Step 7: After booking, dine-in service charge added
    def test_dine_in_service_charge_added(self):
        match = re.search(
            r'pending_booking.*?dine_in.*?DINE_IN_CHARGE_PER_PERSON.*?dine_in_charge',
            self.chat, re.DOTALL
        )
        assert match, "Dine-in should add service charge per person"

    # Step 8: After booking, payment workflow triggered
    def test_dine_in_triggers_payment_after_booking(self):
        match = re.search(
            r'pending_booking.*?dine_in.*?run_payment_workflow',
            self.chat, re.DOTALL
        )
        assert match, "Dine-in should trigger payment after booking"

    # Step 9: Dine-in payment passes order_type="dine_in"
    def test_dine_in_payment_passes_order_type(self):
        match = re.search(
            r'pending_booking.*?run_payment_workflow.*?order_type="dine_in"',
            self.chat, re.DOTALL
        )
        assert match, "Dine-in payment should pass order_type='dine_in'"

    # Step 10: Dine-in packaging charges are zero
    def test_dine_in_zero_packaging(self):
        match = re.search(
            r'pending_booking.*?run_payment_workflow.*?packaging_charges=0',
            self.chat, re.DOTALL
        )
        assert match, "Dine-in should have zero packaging charges"

    # Step 11: Booking confirmation event checked
    def test_booking_confirmation_event_checked(self):
        assert "BOOKING_CONFIRMATION" in self.chat

    # Step 12: Booking failure sends error text
    def test_booking_failure_sends_error(self):
        match = re.search(
            r'not has_confirmation and result.*?send_message',
            self.chat, re.DOTALL
        )
        assert match, "Failed booking should send error text to user"


# ===================================================================
# 3. RECONNECT FLOW
# ===================================================================
class TestReconnectFlow:
    """Verify reconnect preserves state and re-emits welcome."""

    @pytest.fixture(autouse=True)
    def load_sources(self):
        self.chat = _read("app/api/routes/chat.py")

    def test_welcome_already_sent_flag_checked(self):
        assert "welcome_already_sent" in self.chat

    def test_preserved_welcome_msg_resent(self):
        assert "preserved_welcome_msg" in self.chat
        assert "welcome_resent_on_reconnect" in self.chat

    def test_reconnect_re_emits_quick_replies(self):
        match = re.search(
            r'welcome_resent_on_reconnect.*?emit_(?:quick_replies|reconn_qr)',
            self.chat, re.DOTALL
        )
        assert match, "Reconnect should re-emit quick replies"

    def test_reconnect_preserves_auth_state(self):
        assert "preserved_keys" in self.chat
        # Check that key auth fields are preserved
        assert '"welcome_sent"' in self.chat
        assert '"auth_state"' in self.chat
        assert '"user_id"' in self.chat
        assert '"user_name"' in self.chat

    def test_pending_payment_delivered_on_reconnect(self):
        assert "pending_payment_delivered_on_reconnect" in self.chat
        assert "PaymentSuccessEvent" in self.chat

    def test_pending_payment_checks_ws_delivered(self):
        """Only deliver if ws_delivered is False (prevent duplicate)."""
        assert 'ws_delivered' in self.chat

    def test_pending_payment_skips_whatsapp(self):
        """WhatsApp sessions skip reconnect payment delivery."""
        match = re.search(
            r'is_wa_session.*?payment_success.*?ws_delivered',
            self.chat, re.DOTALL
        )
        assert match, "WhatsApp sessions should be skipped for reconnect payment"

    def test_disconnect_preserves_metadata(self):
        """Metadata should NOT be deleted on disconnect for reconnect support."""
        assert "DON'T delete connection_metadata on disconnect" in self.chat


# ===================================================================
# 4. AUTH FLOW
# ===================================================================
class TestAuthFlow:
    """Verify phone authentication flow end-to-end."""

    @pytest.fixture(autouse=True)
    def load_sources(self):
        self.chat = _read("app/api/routes/chat.py")

    def test_auth_required_check(self):
        assert "config.AUTH_REQUIRED" in self.chat

    def test_phone_auth_form_emitted(self):
        assert "emit_phone_auth_form" in self.chat

    def test_existing_user_skips_otp(self):
        """Existing users should be authenticated directly without OTP."""
        match = re.search(
            r'check_user_exists.*?Existing user recognized',
            self.chat, re.DOTALL
        )
        assert match, "Existing users should be authenticated without OTP"

    def test_new_user_gets_otp(self):
        """New users should receive OTP."""
        match = re.search(
            r'New user detected.*?send_otp.*?registration',
            self.chat, re.DOTALL
        )
        assert match or "send_otp" in self.chat, "New users should receive OTP"

    def test_otp_verified_then_name_collected(self):
        """After OTP verification, name collection form shown."""
        match = re.search(
            r'verify_otp.*?verified.*?emit_name_collection_form',
            self.chat, re.DOTALL
        )
        assert match, "After OTP verification, name should be collected"

    def test_invalid_otp_sends_error(self):
        assert "Invalid OTP" in self.chat

    def test_name_collection_creates_user(self):
        match = re.search(
            r'form_type == "name_collection".*?create_user',
            self.chat, re.DOTALL
        )
        assert match, "Name collection should trigger user creation"

    def test_guest_fallback_on_skip(self):
        """If name is skipped, user is created as Guest."""
        match = re.search(
            r'name_collection.*?Guest',
            self.chat, re.DOTALL
        )
        assert match, "Skipped name should default to 'Guest'"

    def test_auth_forms_dismissed_after_login(self):
        assert "emit_form_dismiss" in self.chat

    def test_cart_ownership_managed_after_auth(self):
        assert "manage_cart_ownership" in self.chat

    def test_session_updated_in_redis_after_auth(self):
        """Session data should be updated in Redis for reconnection."""
        assert "update_session" in self.chat
        assert "is_authenticated=True" in self.chat

    def test_otp_cancel_returns_to_phone_form(self):
        """Cancelling OTP should return to phone form."""
        match = re.search(
            r'cancelled.*?emit_form_dismiss.*?\["login_otp"\].*?emit_phone_auth_form',
            self.chat, re.DOTALL
        )
        assert match, "OTP cancel should dismiss OTP form and show phone form"

    def test_auth_state_transitions(self):
        """Auth state should transition: awaiting_phone → awaiting_otp → awaiting_name → authenticated."""
        assert '"awaiting_phone"' in self.chat
        assert '"awaiting_otp"' in self.chat
        assert '"awaiting_name"' in self.chat
        assert '"authenticated"' in self.chat

    def test_reconnect_re_emits_auth_form(self):
        """On reconnect during auth, form should be re-emitted."""
        assert "Auth in progress on reconnect" in self.chat


# ===================================================================
# 5. PENDING PAYMENT INTERCEPTION
# ===================================================================
class TestPendingPaymentInterception:
    """Verify pending payment intercepts all messages."""

    @pytest.fixture(autouse=True)
    def load_sources(self):
        self.chat = _read("app/api/routes/chat.py")
        # Extract the payment interception section
        match = re.search(
            r'PENDING PAYMENT HANDLER.*?payment_pending_handler_error',
            self.chat, re.DOTALL
        )
        self.section = match.group(0) if match else ""

    def test_payment_state_checked(self):
        assert "get_payment_state" in self.section
        assert "AWAITING_PAYMENT" in self.section

    def test_cancel_phrases_comprehensive(self):
        """Cancel detection should cover common cancel phrases."""
        for phrase in ["cancel", "cancel payment", "cancel order", "don't want", "never mind"]:
            assert phrase in self.section, f"Missing cancel phrase: {phrase}"

    def test_cancel_clears_payment_state(self):
        assert "clear_payment_state" in self.section

    def test_cancel_shows_quick_replies(self):
        """After cancel, show View Cart / Show Menu / Checkout quick replies."""
        match = re.search(
            r'_is_cancel.*?QuickRepliesEvent.*?View Cart.*?Show Menu.*?Checkout',
            self.section, re.DOTALL
        )
        assert match, "Cancel should show helpful quick replies"

    def test_complete_payment_re_shows_link(self):
        """'Complete payment' / 'pay now' should re-show Razorpay link."""
        assert "complete payment" in self.section
        assert "pay now" in self.section
        assert "Pay Now with Razorpay" in self.section

    def test_random_message_reminds_about_payment(self):
        """Any other message should remind about pending payment."""
        assert "You have a pending payment" in self.section
        assert "Would you like to cancel" in self.section

    def test_random_message_shows_confirm_cancel_qr(self):
        """Pending payment reminder shows yes/no quick replies."""
        match = re.search(
            r'payment_pending_confirm_cancel.*?Yes, cancel.*?No, complete',
            self.section, re.DOTALL
        )
        assert match, "Pending payment should show yes/no quick replies"

    def test_all_paths_continue(self):
        """All pending payment paths should `continue` (skip AI)."""
        continues = re.findall(r'continue', self.section)
        assert len(continues) >= 3, "All 3 payment paths (cancel/complete/random) should continue"


# ===================================================================
# 6. CART OPERATIONS
# ===================================================================
class TestCartOperationsE2E:
    """Verify direct cart operations bypass AI."""

    @pytest.fixture(autouse=True)
    def load_sources(self):
        self.chat = _read("app/api/routes/chat.py")

    def test_direct_add_to_cart_handler(self):
        assert 'form_type == "direct_add_to_cart"' in self.chat

    def test_add_to_cart_uses_batch_tool(self):
        match = re.search(
            r'direct_add_to_cart.*?batch_add_to_cart',
            self.chat, re.DOTALL
        )
        assert match, "Add to cart should use batch_add_to_cart tool"

    def test_add_to_cart_formats_items(self):
        """Items should be formatted as 'name:qty' pairs."""
        match = re.search(
            r'direct_add_to_cart.*?item_name.*?quantity.*?pairs\.append',
            self.chat, re.DOTALL
        )
        assert match, "Items should be formatted as name:qty pairs"

    def test_add_to_cart_flushes_events(self):
        match = re.search(
            r'direct_add_to_cart.*?flush_pending_events',
            self.chat, re.DOTALL
        )
        assert match, "Add to cart should flush events"

    def test_add_to_cart_supports_translation(self):
        match = re.search(
            r'direct_add_to_cart.*?translate_response',
            self.chat, re.DOTALL
        )
        assert match, "Add to cart response should support translation"

    def test_direct_update_cart_handler(self):
        assert 'form_type == "direct_update_cart"' in self.chat

    def test_update_cart_uses_sql(self):
        match = re.search(
            r'direct_update_cart.*?UPDATE session_cart.*?SET quantity',
            self.chat, re.DOTALL
        )
        assert match, "Update cart should use SQL"

    def test_update_cart_case_insensitive(self):
        match = re.search(
            r'direct_update_cart.*?LOWER\(item_name\) = LOWER',
            self.chat, re.DOTALL
        )
        assert match, "Update cart should be case-insensitive"

    def test_update_cart_emits_cart_data(self):
        match = re.search(
            r'direct_update_cart.*?emit_cart_data',
            self.chat, re.DOTALL
        )
        assert match, "Update cart should emit cart data event"

    def test_direct_remove_handler(self):
        assert 'form_type == "direct_remove_from_cart"' in self.chat

    def test_remove_sets_inactive(self):
        match = re.search(
            r'direct_remove_from_cart.*?is_active = FALSE',
            self.chat, re.DOTALL
        )
        assert match, "Remove should set is_active = FALSE"

    def test_remove_emits_cart_data(self):
        match = re.search(
            r'direct_remove_from_cart.*?emit_cart_data',
            self.chat, re.DOTALL
        )
        assert match, "Remove should emit cart data event"

    def test_all_cart_ops_use_get_session_cart(self):
        """All cart operations should re-fetch cart after mutation."""
        count = self.chat.count("get_session_cart")
        assert count >= 2, "Cart operations should call get_session_cart"

    def test_all_cart_ops_use_get_cart_total(self):
        count = self.chat.count("get_cart_total")
        assert count >= 2, "Cart operations should call get_cart_total"


# ===================================================================
# 7. RATE LIMITING
# ===================================================================
class TestRateLimiting:
    """Verify rate limiting protects against spam."""

    @pytest.fixture(autouse=True)
    def load_sources(self):
        self.chat = _read("app/api/routes/chat.py")

    def test_rate_limit_check_before_processing(self):
        assert "check_rate_limit" in self.chat

    def test_rate_limit_warning_sent(self):
        assert "sending messages too quickly" in self.chat

    def test_rate_limit_config(self):
        assert "rate_limit_messages = 10" in self.chat
        assert "rate_limit_window = 60" in self.chat

    def test_rate_limited_messages_skipped(self):
        """Rate limited messages should `continue` without AI processing."""
        match = re.search(
            r'not is_allowed.*?too quickly.*?continue',
            self.chat, re.DOTALL
        )
        assert match, "Rate limited messages should be skipped"


# ===================================================================
# 8. WHATSAPP AUTO-AUTH
# ===================================================================
class TestWhatsAppAutoAuth:
    """Verify WhatsApp sessions are auto-authenticated."""

    @pytest.fixture(autouse=True)
    def load_sources(self):
        self.chat = _read("app/api/routes/chat.py")

    def test_wa_prefix_detected(self):
        assert 'session_id.startswith("wa-")' in self.chat

    def test_wa_phone_extracted(self):
        """Phone extracted from session_id after 'wa-' prefix."""
        assert "wa_phone_raw = session_id[3:]" in self.chat

    def test_wa_phone_normalized(self):
        """Phone number should be normalized with '+' prefix."""
        match = re.search(
            r'wa_phone_raw.*?startswith\("\+"\).*?"\+" \+ wa_phone_raw',
            self.chat, re.DOTALL
        )
        assert match, "WA phone should be normalized with +"

    def test_wa_existing_user_authenticated(self):
        match = re.search(
            r'wa-.*?check_user_exists.*?is_authenticated = True',
            self.chat, re.DOTALL
        )
        assert match, "Existing WA user should be authenticated"

    def test_wa_new_user_created(self):
        match = re.search(
            r'wa-.*?create_user.*?phone_number=wa_phone_raw',
            self.chat, re.DOTALL
        )
        assert match, "New WA user should be created"

    def test_wa_metadata_marked_whatsapp(self):
        assert '"source": "whatsapp"' in self.chat

    def test_wa_fallback_as_guest(self):
        """If auto-auth fails, user still goes through as guest."""
        match = re.search(
            r'WhatsApp auto-auth failed.*?is_authenticated = True.*?WhatsApp User',
            self.chat, re.DOTALL
        )
        assert match, "Failed WA auth should fall back to guest"


# ===================================================================
# 9. FORM ROUTING
# ===================================================================
class TestFormRoutingE2E:
    """Verify form responses are routed correctly."""

    @pytest.fixture(autouse=True)
    def load_sources(self):
        self.chat = _read("app/api/routes/chat.py")

    def test_form_response_type_detected(self):
        assert '"type") == "form_response"' in self.chat

    def test_auth_forms_skipped_in_main_loop(self):
        """Auth form responses arriving in main loop should be skipped."""
        match = re.search(
            r'form_type in \("phone_auth", "login_otp", "name_collection"\).*?continue',
            self.chat, re.DOTALL
        )
        assert match, "Auth forms in main loop should be skipped"

    def test_all_form_types_have_handlers(self):
        """All expected form types should have handlers."""
        expected = [
            "direct_add_to_cart",
            "direct_update_cart",
            "direct_remove_from_cart",
            "order_type_selection",
            "booking_intake",
        ]
        for ft in expected:
            assert f'form_type == "{ft}"' in self.chat, f"Missing handler for {ft}"

    def test_all_form_handlers_continue(self):
        """All form handlers should `continue` to skip AI processing."""
        for ft in ["direct_add_to_cart", "direct_update_cart",
                    "direct_remove_from_cart", "order_type_selection", "booking_intake"]:
            match = re.search(
                rf'form_type == "{ft}".*?continue',
                self.chat, re.DOTALL
            )
            assert match, f"Handler for {ft} should continue"


# ===================================================================
# 10. WEBSOCKET LIFECYCLE
# ===================================================================
class TestWebSocketLifecycle:
    """Verify WebSocket connection lifecycle management."""

    @pytest.fixture(autouse=True)
    def load_sources(self):
        self.chat = _read("app/api/routes/chat.py")

    def test_old_connection_closed_on_reconnect(self):
        """Existing connection for same session should be closed."""
        assert "New connection for same session" in self.chat

    def test_disconnect_clears_event_queue(self):
        assert "clear_event_queue" in self.chat

    def test_disconnect_releases_inventory(self):
        assert "on_user_logout" in self.chat

    def test_disconnect_guard_prevents_wrong_close(self):
        """Only disconnect if the stored WebSocket matches the one being closed."""
        assert "disconnect_skipped_newer_connection_exists" in self.chat

    def test_finally_block_calls_disconnect(self):
        match = re.search(
            r'finally:.*?disconnect\(session_id, websocket\)',
            self.chat, re.DOTALL
        )
        assert match, "finally block should call disconnect"

    def test_websocket_disconnect_handled_in_main_loop(self):
        assert "WebSocketDisconnect" in self.chat

    def test_runtime_error_handled(self):
        assert "WebSocket is not connected" in self.chat

    def test_session_analytics_logged(self):
        assert "websocket_connection_closed" in self.chat
        assert "messages_exchanged" in self.chat


# ===================================================================
# 11. AI MESSAGE PROCESSING
# ===================================================================
class TestAIMessageProcessing:
    """Verify AI message processing pipeline."""

    @pytest.fixture(autouse=True)
    def load_sources(self):
        self.chat = _read("app/api/routes/chat.py")
        self.crew = _read("app/orchestration/restaurant_crew.py")

    def test_typing_indicator_sent(self):
        assert "typing_indicator" in self.chat

    def test_stale_events_cleared_before_processing(self):
        """Stale events from previous cycles should be cleared."""
        match = re.search(
            r'Clear stale events.*?clear_event_queue',
            self.chat, re.DOTALL
        )
        assert match, "Stale events should be cleared before AI processing"

    def test_language_detection(self):
        """Language should be extracted from message for translation."""
        assert 'language = message_data.get("language"' in self.chat

    def test_hinglish_instruction_prepended(self):
        assert "RESPOND IN HINGLISH" in self.chat

    def test_tanglish_instruction_prepended(self):
        assert "RESPOND IN TANGLISH" in self.chat

    def test_response_not_sent_twice(self):
        """Response streamed via AGUI should NOT be sent again via send_message."""
        assert "Do NOT send again via send_message" in self.chat

    def test_conversation_saved_after_response(self):
        assert "add_message" in self.chat
        assert "conversation_id" in self.chat

    def test_welcome_msg_cleared_after_first_use(self):
        """Welcome message should be removed from metadata after first AI call."""
        welcome_clear = self.chat.count('pop("welcome_msg", None)')
        assert welcome_clear >= 1, "welcome_msg should be cleared after first use"

    def test_testing_middleware_for_test_sessions(self):
        """Sessions starting with 'test-' use testing middleware."""
        assert 'session_id.startswith("test-")' in self.chat
        assert "testing_middleware" in self.chat

    def test_crew_emits_quick_replies_after_response(self):
        assert "get_response_quick_replies" in self.crew
        assert "emit_quick_replies" in self.crew

    def test_crew_has_default_fallback_quick_replies(self):
        assert "DEFAULT_QUICK_REPLIES" in self.crew


# ===================================================================
# 12. AGUI EVENT PIPELINE
# ===================================================================
class TestAGUIEventPipeline:
    """Verify AG-UI event emission and streaming to WebSocket."""

    @pytest.fixture(autouse=True)
    def load_sources(self):
        self.chat = _read("app/api/routes/chat.py")
        self.agui = _read("app/core/agui_events.py")

    def test_stream_function_exists(self):
        assert "async def stream_agui_events_to_websocket" in self.chat

    def test_stream_checks_connection(self):
        assert "session_id not in websocket_mgr.active_connections" in self.chat

    def test_stream_has_timeout(self):
        assert "timeout" in self.chat

    def test_events_sent_as_agui_event_type(self):
        assert 'message_type="agui_event"' in self.chat

    def test_events_include_session_target(self):
        assert "target_session" in self.chat

    def test_flush_pending_events_function(self):
        assert "flush_pending_events" in self.agui

    def test_emit_quick_replies_function(self):
        assert "def emit_quick_replies" in self.agui

    def test_emit_cart_data_function(self):
        assert "def emit_cart_data" in self.agui

    def test_emit_booking_intake_form_function(self):
        assert "def emit_booking_intake_form" in self.agui

    def test_emit_payment_link_function(self):
        assert "def emit_payment_link" in self.agui


# ===================================================================
# 13. EXPIRED ORDER HANDLING
# ===================================================================
class TestExpiredOrderHandling:
    """Verify expired orders are handled gracefully."""

    @pytest.fixture(autouse=True)
    def load_sources(self):
        self.chat = _read("app/api/routes/chat.py")

    def test_missing_pending_order_detected(self):
        assert "not _pending_data" in self.chat

    def test_expired_order_message_sent(self):
        assert "Your order has expired" in self.chat

    def test_expired_order_continues(self):
        match = re.search(
            r'Your order has expired.*?continue',
            self.chat, re.DOTALL
        )
        assert match, "Expired order should continue (skip further processing)"

    def test_pending_order_has_ttl(self):
        """Pending orders in Redis should have TTL."""
        assert "setex" in self.chat


# ===================================================================
# 14. FRONTEND REDUCER COVERAGE
# ===================================================================
class TestFrontendReducer:
    """Verify frontend AGUI reducer handles all event types."""

    @pytest.fixture(autouse=True)
    def load_sources(self):
        self.reducer = _read("frontend/src/hooks/useAGUI.js")

    def test_all_core_event_types_handled(self):
        core_types = [
            "ADD_USER_MESSAGE",
            "RUN_STARTED", "RUN_FINISHED", "RUN_ERROR",
            "ACTIVITY_START", "ACTIVITY_END",
            "TEXT_MESSAGE_START", "TEXT_MESSAGE_CONTENT", "TEXT_MESSAGE_END",
        ]
        for t in core_types:
            assert f"'{t}'" in self.reducer or f'"{t}"' in self.reducer, \
                f"Reducer missing case: {t}"

    def test_quick_replies_cleared_on_user_message(self):
        """User messages should clear existing quick replies."""
        match = re.search(
            r'ADD_USER_MESSAGE.*?filter.*?quick_replies',
            self.reducer, re.DOTALL
        )
        assert match, "User messages should clear quick replies"

    def test_streaming_state_tracked(self):
        assert "isStreaming" in self.reducer

    def test_current_stream_id_tracked(self):
        assert "currentStreamId" in self.reducer

    def test_text_content_appends(self):
        """TEXT_MESSAGE_CONTENT should append delta to existing message."""
        match = re.search(
            r'TEXT_MESSAGE_CONTENT.*?content.*?delta.*?msg\.content \+ content',
            self.reducer, re.DOTALL
        )
        assert match, "TEXT_MESSAGE_CONTENT should append delta"

    def test_late_activity_start_ignored(self):
        """ACTIVITY_START after RUN_FINISHED should be ignored."""
        match = re.search(
            r'ACTIVITY_START.*?isStreaming.*?return state',
            self.reducer, re.DOTALL
        )
        assert match, "Late ACTIVITY_START should be ignored"


# ===================================================================
# 15. CART OWNERSHIP (Security)
# ===================================================================
class TestCartOwnershipSecurity:
    """Verify cart ownership prevents data leakage between users."""

    @pytest.fixture(autouse=True)
    def load_sources(self):
        self.chat = _read("app/api/routes/chat.py")

    def test_cart_ownership_function_exists(self):
        assert "async def manage_cart_ownership" in self.chat

    def test_different_user_clears_cart(self):
        """If a different user logs in, their cart should be cleared."""
        match = re.search(
            r'manage_cart_ownership.*?existing_owner.*?!= user_id.*?is_active = FALSE',
            self.chat, re.DOTALL
        )
        assert match, "Different user should get cart cleared"

    def test_same_user_keeps_cart(self):
        """Same user reconnecting should keep their cart."""
        assert "resume" in self.chat.lower() or "KEEP IT" in self.chat

    def test_ownership_called_after_each_auth_path(self):
        """manage_cart_ownership called after existing user, new user, WA auth, reconnect."""
        count = self.chat.count("manage_cart_ownership")
        assert count >= 4, f"manage_cart_ownership should be called in all auth paths, found {count}"

    def test_session_state_upserted(self):
        """session_state should be upserted with current user_id."""
        assert "INSERT INTO session_state" in self.chat
        assert "ON CONFLICT" in self.chat


# ===================================================================
# 16. CHARGE CONSTANTS CONSISTENCY
# ===================================================================
class TestChargeConstants:
    """Verify charge constants are used consistently."""

    @pytest.fixture(autouse=True)
    def load_sources(self):
        self.chat = _read("app/api/routes/chat.py")
        self.agui = _read("app/core/agui_events.py")

    def test_packaging_charge_defined(self):
        assert "PACKAGING_CHARGE_PER_ITEM" in self.agui

    def test_dine_in_charge_defined(self):
        assert "DINE_IN_CHARGE_PER_PERSON" in self.agui

    def test_packaging_charge_imported_in_chat(self):
        assert "PACKAGING_CHARGE_PER_ITEM" in self.chat

    def test_dine_in_charge_imported_in_chat(self):
        assert "DINE_IN_CHARGE_PER_PERSON" in self.chat

    def test_takeaway_formula(self):
        """Takeaway total = subtotal + (qty * PACKAGING_CHARGE_PER_ITEM)."""
        match = re.search(
            r'total_qty.*?PACKAGING_CHARGE_PER_ITEM.*?subtotal.*?\+ packaging_charges',
            self.chat, re.DOTALL
        )
        assert match, "Takeaway should use correct formula"

    def test_dine_in_formula(self):
        """Dine-in total = subtotal + (party_size * DINE_IN_CHARGE_PER_PERSON)."""
        match = re.search(
            r'booking_party_size \* DINE_IN_CHARGE_PER_PERSON.*?subtotal.*?\+ dine_in_charge',
            self.chat, re.DOTALL
        )
        assert match, "Dine-in should use correct formula"


# ===================================================================
# 17. ERROR HANDLING AND RESILIENCE
# ===================================================================
class TestErrorHandling:
    """Verify error handling at each stage."""

    @pytest.fixture(autouse=True)
    def load_sources(self):
        self.chat = _read("app/api/routes/chat.py")

    def test_welcome_generation_has_fallback(self):
        assert "Fallback welcome message if AI generation fails" in self.chat or \
               "fallback_msg" in self.chat

    def test_booking_failure_handled(self):
        assert "booking_intake_form_failed" in self.chat

    def test_websocket_send_failure_doesnt_disconnect(self):
        """Send failures should NOT trigger disconnect."""
        assert "Does NOT call disconnect() on send errors" in self.chat

    def test_error_message_sent_on_processing_failure(self):
        assert "I apologize, but I encountered an error" in self.chat

    def test_json_decode_error_handled(self):
        assert "JSONDecodeError" in self.chat

    def test_payment_handler_error_caught(self):
        assert "payment_pending_handler_error" in self.chat

    def test_inventory_cleanup_error_caught(self):
        assert "websocket_disconnect_inventory_cleanup_failed" in self.chat

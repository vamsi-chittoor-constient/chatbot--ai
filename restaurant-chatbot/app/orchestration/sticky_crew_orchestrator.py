"""
Sticky Crew Orchestrator
=========================
Master crew that routes to specialized crews with sticky sessions.

Architecture:
- Master crew routes first message to appropriate specialized crew
- Session "sticks" to that crew for subsequent messages
- Crews can handoff to other crews using [HANDOFF:crew_name] in responses
- Real-time, fast (~1-3 seconds per message)
"""

import re
import structlog
from typing import Dict, Any, Optional
from crewai import Agent, Task, Crew, Process

logger = structlog.get_logger("orchestration.sticky_crew")

# Session memory: Tracks which crew is active for each session
_SESSION_CREWS: Dict[str, str] = {}  # session_id -> crew_name

# Crew cache: Avoid recreating crews
_CREW_CACHE: Dict[str, Any] = {}  # crew_name -> Crew instance


class StickyCrewOrchestrator:
    """
    Orchestrator with sticky crew routing.

    - First message: Master crew routes to specialized crew
    - Subsequent messages: Sticky to that crew
    - Handoff: Crew can trigger handoff with [HANDOFF:crew_name]
    """

    def __init__(self):
        """Initialize sticky crew orchestrator"""
        logger.info("Initializing Sticky Crew Orchestrator")
        self.available_crews = {
            "food_ordering": "Handles menu browsing, cart management, and food orders",
            "booking": "Handles table reservations and availability checks",
            "feedback": "Handles customer feedback, complaints, and reviews",
            "general": "Handles greetings, FAQs, and general restaurant questions"
        }

    async def process_message(
        self,
        user_message: str,
        session_id: str,
        user_id: Optional[str] = None,
        device_id: Optional[str] = None,
        session_token: Optional[str] = None,
        restaurant_id: Optional[str] = None,
        welcome_msg: Optional[str] = None
    ) -> tuple[str, Dict[str, Any]]:
        """
        Process message with sticky crew routing.

        Flow:
        1. Check if session has active crew (sticky routing)
        2. If not, use master crew to route
        3. Execute message with active crew
        4. Check for handoff signals
        5. Update session state
        """

        logger.info(
            "Processing message with sticky routing",
            session_id=session_id,
            has_active_crew=session_id in _SESSION_CREWS
        )

        try:
            # Get or determine active crew
            active_crew_name = _SESSION_CREWS.get(session_id)

            if not active_crew_name:
                # First message - route using master crew
                logger.info("First message - using master crew for routing", session_id=session_id)
                active_crew_name = await self._route_with_master_crew(user_message, session_id)
                _SESSION_CREWS[session_id] = active_crew_name
                logger.info(
                    "Routed to specialized crew",
                    session_id=session_id,
                    crew=active_crew_name
                )
            else:
                logger.info(
                    "Using sticky crew",
                    session_id=session_id,
                    crew=active_crew_name
                )

            # Get the specialized crew
            crew = self._get_or_create_crew(active_crew_name, session_id)

            # Build task input
            conversation_history = []
            if welcome_msg:
                conversation_history.append(f"Assistant: {welcome_msg}")
            conversation_history.append(f"User: {user_message}")

            task_input = {
                "user_input": user_message,
                "session_id": session_id,
                "context": "\n".join(conversation_history),
                "user_id": user_id or "anonymous"
            }

            # Execute crew
            logger.info(
                "Executing crew",
                session_id=session_id,
                crew=active_crew_name
            )

            # Special handling for food_ordering - use process_with_crew for proper async tool support
            if isinstance(crew, dict) and crew.get("type") == "food_ordering_direct":
                from app.features.food_ordering.crew_agent import process_with_crew
                response_text = await process_with_crew(
                    user_message=user_message,
                    session_id=session_id,
                    conversation_history=conversation_history,
                    user_id=user_id
                )
            else:
                # Use native async kickoff for other crews
                result = await crew.akickoff(inputs=task_input)

                # Extract response
                if hasattr(result, 'raw'):
                    response_text = str(result.raw)
                elif hasattr(result, 'output'):
                    response_text = str(result.output)
                else:
                    response_text = str(result)

            response_text = response_text.strip()

            # Check for handoff signal
            handoff_match = re.search(r'\[HANDOFF:(\w+)\]', response_text)
            if handoff_match:
                new_crew = handoff_match.group(1)
                logger.info(
                    "Handoff detected",
                    session_id=session_id,
                    from_crew=active_crew_name,
                    to_crew=new_crew
                )

                # Update session to new crew
                _SESSION_CREWS[session_id] = new_crew

                # Remove handoff tag from response
                response_text = re.sub(r'\[HANDOFF:\w+\]', '', response_text).strip()

                # Add handoff message
                response_text = f"{response_text}\n\n[Transferring you to {new_crew} specialist...]"

            metadata = {
                "type": "success",
                "intent": active_crew_name,
                "confidence": 1.0,
                "agent_used": f"sticky_crew_{active_crew_name}",
                "session_id": session_id,
                "user_id": user_id,
                "orchestrator": "sticky_crew",
                "handoff_occurred": bool(handoff_match),
                "handoff_to": handoff_match.group(1) if handoff_match else None
            }

            logger.info(
                "Sticky crew processing complete",
                session_id=session_id,
                crew=active_crew_name,
                response_length=len(response_text),
                handoff=bool(handoff_match)
            )

            return response_text, metadata

        except Exception as e:
            logger.error(
                "Sticky crew orchestrator failed",
                session_id=session_id,
                error=str(e),
                exc_info=True
            )

            # Simple fallback
            return self._simple_fallback(user_message, session_id)

    async def _route_with_master_crew(self, user_message: str, session_id: str) -> str:
        """
        Use master crew with LLM to route to appropriate specialized crew.
        Fast routing decision using gpt-4o-mini (0.5-1 second).
        """

        # Create lightweight routing agent
        router_agent = Agent(
            role="Restaurant Request Router",
            goal="Quickly identify what type of help the customer needs and route to the right specialist",
            backstory="""You are an expert at quickly understanding customer requests at a restaurant.

Available specialists:
- food_ordering: Menu browsing, ordering food, cart management, checkout
- booking: Table reservations, availability checks, party bookings
- feedback: Customer feedback, complaints, reviews, satisfaction
- general: Greetings, FAQs, general questions, restaurant information

Your job: Read the customer's message and return ONLY the specialist name (food_ordering, booking, feedback, or general).
Return ONLY ONE WORD - the specialist name, nothing else.""",
            tools=[],
            verbose=False,
            allow_delegation=False,
            llm="gpt-4o-mini"  # Fast, cheap model for routing
        )

        routing_task = Task(
            description=f"""Customer says: "{user_message}"

Which specialist should handle this? Return ONLY ONE of these words:
- food_ordering
- booking
- feedback
- general

Answer with just the specialist name, no explanation.""",
            expected_output="One word: the name of the specialist (food_ordering, booking, feedback, or general)",
            agent=router_agent
        )

        routing_crew = Crew(
            agents=[router_agent],
            tasks=[routing_task],
            process=Process.sequential,
            verbose=False
        )

        # Execute routing decision
        logger.info("Executing LLM-based routing", session_id=session_id)

        # Use native async kickoff for routing
        result = await routing_crew.akickoff()

        # Extract crew name from result
        if hasattr(result, 'raw'):
            crew_name = str(result.raw).strip().lower()
        elif hasattr(result, 'output'):
            crew_name = str(result.output).strip().lower()
        else:
            crew_name = str(result).strip().lower()

        # Validate crew name
        if crew_name not in self.available_crews:
            logger.warning(
                "Invalid crew name from router, defaulting to general",
                session_id=session_id,
                returned_crew=crew_name
            )
            crew_name = "general"

        logger.info(
            "LLM routing complete",
            session_id=session_id,
            routed_to=crew_name
        )

        return crew_name

    def _get_or_create_crew(self, crew_name: str, session_id: str):
        """
        Get or create specialized crew.
        Caches crews to avoid recreation overhead.
        """

        cache_key = f"{crew_name}_{session_id}"

        if cache_key in _CREW_CACHE:
            logger.debug("Using cached crew", crew=crew_name, session_id=session_id)
            return _CREW_CACHE[cache_key]

        logger.info("Creating new crew", crew=crew_name, session_id=session_id)

        # Import appropriate crew creator
        if crew_name == "food_ordering":
            # For food_ordering, we return a special marker - actual processing
            # will be done via process_with_crew() which handles async properly
            # Don't cache this - it's not a real crew object
            return {"type": "food_ordering_direct", "session_id": session_id}

        if crew_name == "booking":
            # TODO: Create booking crew
            crew = self._create_placeholder_crew("Booking Specialist", crew_name)

        elif crew_name == "feedback":
            # TODO: Create feedback crew
            crew = self._create_placeholder_crew("Feedback Specialist", crew_name)

        else:  # general
            crew = self._create_general_crew()

        # Cache crew
        _CREW_CACHE[cache_key] = crew

        # Limit cache size
        if len(_CREW_CACHE) > 100:
            oldest_key = next(iter(_CREW_CACHE))
            del _CREW_CACHE[oldest_key]
            logger.debug("Evicted oldest crew from cache", evicted_key=oldest_key)

        return crew

    def _create_placeholder_crew(self, role: str, crew_type: str):
        """Create placeholder crew for crews not yet implemented"""
        agent = Agent(
            role=role,
            goal=f"Help customers with {crew_type} requests",
            backstory=f"You are a helpful {crew_type} specialist at the restaurant.",
            tools=[],
            verbose=False,
            allow_delegation=False,
            llm="gpt-4o-mini"
        )

        task = Task(
            description="User Request: {user_input}\n\nRespond helpfully to the user's request.",
            expected_output="A helpful response to the user.",
            agent=agent
        )

        return Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=False
        )

    def _create_general_crew(self):
        """Create general conversation crew"""
        agent = Agent(
            role="Restaurant Concierge",
            goal="Provide friendly assistance and answer general questions about the restaurant",
            backstory="""You are a warm, welcoming restaurant concierge. You help with:
            - Greetings and welcomes
            - General restaurant information
            - Business hours and location
            - FAQs

            If customers ask about:
            - Food/menu → Say: [HANDOFF:food_ordering] I'll connect you with our menu specialist
            - Reservations → Say: [HANDOFF:booking] Let me transfer you to reservations
            - Feedback/complaints → Say: [HANDOFF:feedback] I'll direct you to our feedback team
            """,
            tools=[],
            verbose=False,
            allow_delegation=False,
            llm="gpt-4o-mini"
        )

        task = Task(
            description="User Request: {user_input}\n\nRespond warmly and helpfully. Use [HANDOFF:crew_name] if user needs specialized help.",
            expected_output="A friendly, helpful response.",
            agent=agent
        )

        return Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=False
        )

    def _simple_fallback(self, user_message: str, session_id: str) -> tuple[str, Dict[str, Any]]:
        """Simple fallback response"""
        response = (
            "I'm here to help! I can assist you with:\n"
            "- 🍕 Browsing our menu and placing orders\n"
            "- 📅 Making table reservations\n"
            "- 💬 Submitting feedback\n"
            "- ❓ Answering general questions\n\n"
            "What would you like to do?"
        )

        metadata = {
            "type": "fallback",
            "intent": "general",
            "confidence": 0.0,
            "agent_used": "fallback",
            "session_id": session_id,
            "orchestrator": "sticky_crew_fallback"
        }

        return response, metadata

    def reset_session(self, session_id: str):
        """Reset session crew (for testing or explicit user request)"""
        if session_id in _SESSION_CREWS:
            del _SESSION_CREWS[session_id]
            logger.info("Session crew reset", session_id=session_id)


# Global instance
sticky_crew_orchestrator = StickyCrewOrchestrator()

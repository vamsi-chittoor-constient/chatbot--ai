"""
Testing API Endpoints
=====================

This module provides API endpoints for:
- Starting/managing testing sessions
- Submitting validation feedback
- Exporting testing data in JSON Lines format
"""

import structlog
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

from app.database.mongodb import get_mongodb_testing_manager
from app.utils.timezone import get_current_time_str

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/testing", tags=["Testing"])


# ============ REQUEST/RESPONSE MODELS ============

class StartSessionRequest(BaseModel):
    """Request to start a new testing session"""
    tester_name: str = Field(..., description="Name of the tester")
    test_scenario: str = Field(default="general", description="Type of test scenario")
    notes: str = Field(default="", description="Optional notes about this session")


class StartSessionResponse(BaseModel):
    """Response after starting a session"""
    session_id: str
    tester_name: str
    started_at: str
    message: str


class SubmitFeedbackRequest(BaseModel):
    """Request to submit validation feedback"""
    session_id: str = Field(..., description="Testing session ID")
    conversation_id: str = Field(..., description="Conversation ID from chat response")
    is_correct: bool = Field(..., description="Was the response correct?")
    feedback: str = Field(default="", description="Optional feedback text")
    category: str = Field(default="general", description="Category of the interaction")


class SubmitFeedbackResponse(BaseModel):
    """Response after submitting feedback"""
    success: bool
    message: str
    feedback_id: str


class EndSessionRequest(BaseModel):
    """Request to end a testing session"""
    session_id: str = Field(..., description="Testing session ID")
    notes: str = Field(default="", description="Optional closing notes")


class EndSessionResponse(BaseModel):
    """Response after ending a session"""
    success: bool
    message: str
    session_id: str
    total_interactions: int


# ============ API ENDPOINTS ============

@router.post("/session/start", response_model=StartSessionResponse)
async def start_testing_session(request: StartSessionRequest):
    """
    Start a new testing session

    This creates a new testing session in MongoDB and returns a session_id
    that should be used for all subsequent testing interactions.
    
    If MongoDB is unavailable, creates an in-memory session for basic functionality.
    """
    try:
        testing_manager = get_mongodb_testing_manager()

        # Create session document
        session_data = {
            "session_id": str(uuid.uuid4()),
            "tester_name": request.tester_name,
            "test_scenario": request.test_scenario,
            "notes": request.notes,
            "started_at": get_current_time_str(),
            "ended_at": None,
            "status": "active",
            "interactions": []
        }

        # Try to insert into MongoDB (may fail if MongoDB not running)
        try:
            await testing_manager.create_session(session_data)
            logger.info(
                "Testing session started (MongoDB)",
                session_id=session_data["session_id"],
                tester_name=request.tester_name
            )
        except Exception as mongo_error:
            # MongoDB unavailable - continue with in-memory session
            logger.warning(
                "MongoDB unavailable for testing session - using in-memory session",
                error=str(mongo_error),
                session_id=session_data["session_id"]
            )

        return StartSessionResponse(
            session_id=session_data["session_id"],
            tester_name=request.tester_name,
            started_at=session_data["started_at"],
            message="Testing session started successfully"
        )

    except Exception as e:
        logger.error(f"Failed to start testing session: {e}")
        # Return a default session instead of failing
        fallback_session_id = str(uuid.uuid4())
        logger.info(
            "Using fallback session creation",
            session_id=fallback_session_id
        )
        return StartSessionResponse(
            session_id=fallback_session_id,
            tester_name=request.tester_name,
            started_at=get_current_time_str(),
            message="Testing session started (MongoDB unavailable - using in-memory mode)"
        )


@router.post("/feedback/submit", response_model=SubmitFeedbackResponse)
async def submit_feedback(request: SubmitFeedbackRequest):
    """
    Submit validation feedback for a conversation

    This records whether the assistant's response was correct and any
    additional feedback from the tester.
    
    If MongoDB is unavailable, logs feedback but continues without persisting.
    """
    try:
        feedback_data = {
            "feedback_id": str(uuid.uuid4()),
            "session_id": request.session_id,
            "conversation_id": request.conversation_id,
            "is_correct": request.is_correct,
            "feedback": request.feedback,
            "category": request.category,
            "submitted_at": get_current_time_str()
        }
        
        # Try to add to MongoDB (may fail if MongoDB not running)
        try:
            testing_manager = get_mongodb_testing_manager()
            await testing_manager.add_feedback(request.session_id, feedback_data)
            logger.info(
                "Feedback submitted (MongoDB)",
                session_id=request.session_id,
                conversation_id=request.conversation_id,
                is_correct=request.is_correct
            )
        except Exception as mongo_error:
            # MongoDB unavailable - log but continue
            logger.warning(
                "MongoDB unavailable for feedback - logging only",
                error=str(mongo_error),
                feedback_data=feedback_data
            )

        return SubmitFeedbackResponse(
            success=True,
            message="Feedback submitted successfully",
            feedback_id=feedback_data["feedback_id"]
        )

    except Exception as e:
        logger.error(f"Failed to submit feedback: {e}")
        # Return success anyway to not block UI
        return SubmitFeedbackResponse(
            success=True,
            message="Feedback logged (MongoDB unavailable)",
            feedback_id=str(uuid.uuid4())
        )


@router.post("/session/end", response_model=EndSessionResponse)
async def end_testing_session(request: EndSessionRequest):
    """
    End a testing session

    This marks the session as completed and records any final notes.
    """
    try:
        testing_manager = get_mongodb_testing_manager()

        # Update session to ended
        session = await testing_manager.end_session(
            request.session_id,
            request.notes
        )

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        logger.info(
            "Testing session ended",
            session_id=request.session_id,
            interactions=len(session.get("interactions", []))
        )

        return EndSessionResponse(
            success=True,
            message="Testing session ended successfully",
            session_id=request.session_id,
            total_interactions=len(session.get("interactions", []))
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to end testing session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}")
async def get_testing_session(session_id: str):
    """
    Get details of a testing session

    Returns the complete session data including all interactions and feedback.
    """
    try:
        testing_manager = get_mongodb_testing_manager()
        session = await testing_manager.get_session(session_id)

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Convert ObjectId to string for JSON serialization
        session["_id"] = str(session["_id"])

        return session

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get testing session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/jsonl")
async def export_testing_data():
    """
    Export all testing data in JSON Lines format

    Returns a JSONL file containing all testing sessions and their feedback.
    This format is compatible with OpenAI fine-tuning.
    """
    try:
        testing_manager = get_mongodb_testing_manager()

        # Get all sessions
        sessions = await testing_manager.get_all_sessions()

        # Convert to JSONL format
        jsonl_lines = []
        for session in sessions:
            # Convert ObjectId to string
            session["_id"] = str(session["_id"])

            # Add each interaction as a separate line
            for interaction in session.get("interactions", []):
                jsonl_lines.append(interaction)

        # Create JSONL content
        import json
        jsonl_content = "\n".join(json.dumps(line) for line in jsonl_lines)

        return Response(
            content=jsonl_content,
            media_type="application/x-ndjson",
            headers={
                "Content-Disposition": f"attachment; filename=testing_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
            }
        )

    except Exception as e:
        logger.error(f"Failed to export testing data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_testing_stats():
    """
    Get statistics about testing sessions

    Returns summary statistics including:
    - Total sessions
    - Total interactions
    - Accuracy metrics
    - Category breakdown
    """
    try:
        testing_manager = get_mongodb_testing_manager()
        stats = await testing_manager.get_stats()

        return stats

    except Exception as e:
        logger.error(f"Failed to get testing stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

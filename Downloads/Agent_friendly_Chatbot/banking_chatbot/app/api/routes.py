"""
FastAPI routes for Banking Chatbot API.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
import logging

from ..config import settings
from ..core import ChatRouter, RoutingResult
from ..database.session import get_db, AsyncSessionLocal
from ..database.repository import (
    ConversationRepository, IntentRepository,
    AnalyticsRepository, EscalationRepository
)
from ..database.models import MessageRole
from .schemas import (
    ChatRequest, ChatResponse, ChatMetadata,
    IntentCreate, IntentUpdate, IntentResponse,
    EscalationResponse, EscalationAssign, EscalationResolve,
    AnalyticsSummary, IntentBreakdown, HourlyDistribution,
    HealthCheck, FeedbackRequest, FeedbackResponse
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Global router instance (initialized on startup)
_chat_router: Optional[ChatRouter] = None


def get_chat_router() -> ChatRouter:
    """Get or create chat router instance."""
    global _chat_router
    if _chat_router is None:
        _chat_router = ChatRouter(
            api_key=settings.anthropic_api_key,
            confidence_threshold=settings.confidence_threshold,
            escalation_threshold=settings.escalation_threshold,
        )
    return _chat_router


# ============ Chat Endpoints ============

@router.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
):
    """
    Process a chat message and return response.

    This is the main endpoint for the chatbot. It:
    1. Analyzes sentiment (optional)
    2. Routes query to appropriate intent
    3. Generates personalized response
    4. Tracks analytics in background
    """
    try:
        chat_router = get_chat_router()

        # Route the query
        result = chat_router.route(
            query=request.query,
            user_context=request.context,
            session_id=request.session_id,
            analyze_sentiment=request.analyze_sentiment
        )

        # Record analytics in background
        background_tasks.add_task(
            record_analytics,
            result=result,
            user_id=request.user_id,
            session_id=request.session_id
        )

        # Build response
        return ChatResponse(
            request_id=result.request_id,
            timestamp=result.timestamp,
            query=result.query,
            intent=result.detected_intent,
            confidence=result.intent_confidence,
            status=result.status.value,
            response=result.response,
            requires_human=result.requires_human,
            escalation_reason=result.escalation_reason,
            follow_up_questions=result.follow_up_questions,
            metadata=ChatMetadata(
                model=result.model_used,
                latency_ms=result.latency_ms,
                cost_usd=result.cost_usd,
                sentiment=result.sentiment,
                urgency=result.urgency_score
            )
        )

    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/simple", tags=["Chat"])
async def chat_simple(query: str = Query(..., min_length=1)):
    """
    Simple chat endpoint that returns just the intent.
    Useful for testing and lightweight integrations.
    """
    try:
        chat_router = get_chat_router()
        intent = chat_router.route_simple(query)
        return {"query": query, "intent": intent}
    except Exception as e:
        logger.error(f"Simple chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def record_analytics(
    result: RoutingResult,
    user_id: Optional[str],
    session_id: Optional[str]
):
    """Background task to record analytics."""
    try:
        async with AsyncSessionLocal() as session:
            repo = AnalyticsRepository(session)
            await repo.record(
                intent_id=result.detected_intent,
                confidence=result.intent_confidence,
                latency_ms=result.latency_ms,
                cost_usd=result.cost_usd,
                model_used=result.model_used,
                sentiment=result.sentiment,
                escalated=result.requires_human,
                user_id=user_id,
                session_id=session_id
            )
            await session.commit()
    except Exception as e:
        logger.error(f"Analytics recording error: {e}")


# ============ Intent Management ============

@router.get("/intents", response_model=List[IntentResponse], tags=["Intents"])
async def list_intents():
    """List all intents."""
    chat_router = get_chat_router()
    intents = chat_router.get_all_intents()
    return [
        IntentResponse(
            id=i.id,
            name=i.name,
            category=i.category,
            description=i.description,
            response_template=i.response_template,
            follow_up_questions=i.follow_up_questions,
            matches_when=i.matches_when,
            does_not_match_when=i.does_not_match_when,
            key_signals=i.key_signals,
            hinglish_variants=i.hinglish_variants,
            requires_human=i.requires_human,
            priority=i.priority,
            is_active=True
        )
        for i in intents
    ]


@router.get("/intents/{intent_id}", response_model=IntentResponse, tags=["Intents"])
async def get_intent(intent_id: str):
    """Get a specific intent."""
    chat_router = get_chat_router()
    intent = chat_router.get_intent(intent_id)
    if not intent:
        raise HTTPException(status_code=404, detail="Intent not found")
    return IntentResponse(
        id=intent.id,
        name=intent.name,
        category=intent.category,
        description=intent.description,
        response_template=intent.response_template,
        follow_up_questions=intent.follow_up_questions,
        matches_when=intent.matches_when,
        does_not_match_when=intent.does_not_match_when,
        key_signals=intent.key_signals,
        hinglish_variants=intent.hinglish_variants,
        requires_human=intent.requires_human,
        priority=intent.priority,
        is_active=True
    )


@router.post("/intents", response_model=IntentResponse, tags=["Intents"])
async def create_intent(intent_data: IntentCreate):
    """Create a new intent."""
    from ..core.intents import Intent, IntentCategory

    chat_router = get_chat_router()

    # Check if intent already exists
    if chat_router.get_intent(intent_data.id):
        raise HTTPException(status_code=400, detail="Intent already exists")

    # Create intent
    intent = Intent(
        id=intent_data.id,
        name=intent_data.name,
        category=intent_data.category,
        description=intent_data.description or "",
        response_template=intent_data.response_template,
        follow_up_questions=intent_data.follow_up_questions,
        matches_when=intent_data.matches_when or "",
        does_not_match_when=intent_data.does_not_match_when or "",
        key_signals=intent_data.key_signals,
        hinglish_variants=intent_data.hinglish_variants,
        example_queries=intent_data.example_queries,
        related_intents=intent_data.related_intents,
        requires_human=intent_data.requires_human,
        priority=intent_data.priority
    )

    chat_router.add_intent(intent)

    return IntentResponse(
        id=intent.id,
        name=intent.name,
        category=intent.category,
        description=intent.description,
        response_template=intent.response_template,
        follow_up_questions=intent.follow_up_questions,
        matches_when=intent.matches_when,
        does_not_match_when=intent.does_not_match_when,
        key_signals=intent.key_signals,
        hinglish_variants=intent.hinglish_variants,
        requires_human=intent.requires_human,
        priority=intent.priority,
        is_active=True
    )


@router.delete("/intents/{intent_id}", tags=["Intents"])
async def delete_intent(intent_id: str):
    """Delete an intent."""
    chat_router = get_chat_router()
    if chat_router.remove_intent(intent_id):
        return {"success": True, "message": f"Intent {intent_id} deleted"}
    raise HTTPException(status_code=404, detail="Intent not found")


# ============ Escalation Management ============

@router.get("/escalations", response_model=List[EscalationResponse], tags=["Escalations"])
async def list_escalations(
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200)
):
    """List escalations, optionally filtered by status."""
    async with AsyncSessionLocal() as session:
        repo = EscalationRepository(session)
        escalations = await repo.get_pending(limit=limit)
        return [
            EscalationResponse(
                id=e.id,
                conversation_id=e.conversation_id,
                reason=e.reason,
                status=e.status.value,
                priority=e.priority,
                last_query=e.last_query,
                detected_intent=e.detected_intent,
                sentiment=e.sentiment,
                urgency_score=e.urgency_score,
                assigned_to=e.assigned_to,
                assigned_at=e.assigned_at,
                resolution_notes=e.resolution_notes,
                resolved_at=e.resolved_at,
                resolution_time_minutes=e.resolution_time_minutes,
                created_at=e.created_at
            )
            for e in escalations
        ]


@router.post("/escalations/{escalation_id}/assign", tags=["Escalations"])
async def assign_escalation(escalation_id: int, data: EscalationAssign):
    """Assign an escalation to an agent."""
    async with AsyncSessionLocal() as session:
        repo = EscalationRepository(session)
        escalation = await repo.assign(escalation_id, data.agent_id)
        if not escalation:
            raise HTTPException(status_code=404, detail="Escalation not found")
        await session.commit()
        return {"success": True, "message": f"Escalation assigned to {data.agent_id}"}


@router.post("/escalations/{escalation_id}/resolve", tags=["Escalations"])
async def resolve_escalation(escalation_id: int, data: EscalationResolve):
    """Resolve an escalation."""
    async with AsyncSessionLocal() as session:
        repo = EscalationRepository(session)
        escalation = await repo.resolve(escalation_id, data.resolution_notes)
        if not escalation:
            raise HTTPException(status_code=404, detail="Escalation not found")
        await session.commit()
        return {"success": True, "message": "Escalation resolved"}


@router.get("/escalations/stats", tags=["Escalations"])
async def escalation_stats():
    """Get escalation statistics."""
    async with AsyncSessionLocal() as session:
        repo = EscalationRepository(session)
        return await repo.get_stats()


# ============ Analytics ============

@router.get("/analytics/summary", response_model=AnalyticsSummary, tags=["Analytics"])
async def analytics_summary(
    days: int = Query(7, ge=1, le=90)
):
    """Get analytics summary for the specified period."""
    async with AsyncSessionLocal() as session:
        repo = AnalyticsRepository(session)
        start_date = datetime.utcnow() - timedelta(days=days)
        return await repo.get_summary(start_date=start_date)


@router.get("/analytics/intents", response_model=List[IntentBreakdown], tags=["Analytics"])
async def analytics_by_intent(
    days: int = Query(7, ge=1, le=90)
):
    """Get analytics breakdown by intent."""
    async with AsyncSessionLocal() as session:
        repo = AnalyticsRepository(session)
        start_date = datetime.utcnow() - timedelta(days=days)
        return await repo.get_intent_breakdown(start_date=start_date)


@router.get("/analytics/hourly", response_model=List[HourlyDistribution], tags=["Analytics"])
async def analytics_hourly(
    date: Optional[str] = None
):
    """Get hourly distribution for a specific date."""
    async with AsyncSessionLocal() as session:
        repo = AnalyticsRepository(session)
        return await repo.get_hourly_distribution(date=date)


@router.get("/analytics/usage", tags=["Analytics"])
async def llm_usage():
    """Get LLM usage statistics."""
    chat_router = get_chat_router()
    return chat_router.get_usage_stats()


# ============ Feedback ============

@router.post("/feedback", response_model=FeedbackResponse, tags=["Feedback"])
async def submit_feedback(feedback: FeedbackRequest):
    """Submit feedback for a response."""
    # In production, this would update the analytics record
    logger.info(f"Feedback received: {feedback.request_id} - Rating: {feedback.rating}")
    return FeedbackResponse(
        success=True,
        message="Thank you for your feedback!"
    )


# ============ Health Check ============

@router.get("/health", response_model=HealthCheck, tags=["System"])
async def health_check():
    """Health check endpoint."""
    db_status = "healthy"
    llm_status = "healthy"

    # Check database
    try:
        async with AsyncSessionLocal() as session:
            await session.execute("SELECT 1")
    except Exception as e:
        db_status = f"unhealthy: {e}"

    # Check LLM (just verify client exists)
    try:
        get_chat_router()
    except Exception as e:
        llm_status = f"unhealthy: {e}"

    return HealthCheck(
        status="healthy" if db_status == "healthy" and llm_status == "healthy" else "degraded",
        version=settings.app_version,
        database=db_status,
        llm_service=llm_status
    )


@router.get("/", tags=["System"])
async def root():
    """Root endpoint with API info."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health"
    }

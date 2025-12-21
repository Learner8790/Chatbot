"""
Pydantic schemas for API requests and responses.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


# ============ Chat Schemas ============

class ChatRequest(BaseModel):
    """Request to chat endpoint."""
    query: str = Field(..., min_length=1, max_length=2000, description="User's query")
    session_id: Optional[str] = Field(None, description="Session identifier")
    user_id: Optional[str] = Field(None, description="User identifier")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    analyze_sentiment: bool = Field(True, description="Whether to analyze sentiment")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "How do I activate my new card?",
                "session_id": "sess_abc123",
                "user_id": "user_456",
                "context": {"account_type": "savings"},
                "analyze_sentiment": True
            }
        }


class ChatMetadata(BaseModel):
    """Metadata about the response."""
    model: str
    latency_ms: float
    cost_usd: float
    sentiment: str
    urgency: float


class ChatResponse(BaseModel):
    """Response from chat endpoint."""
    request_id: str
    timestamp: datetime
    query: str
    intent: Optional[str]
    confidence: float
    status: str
    response: Optional[str]
    requires_human: bool
    escalation_reason: Optional[str]
    follow_up_questions: List[str]
    metadata: ChatMetadata

    class Config:
        json_schema_extra = {
            "example": {
                "request_id": "abc12345",
                "timestamp": "2024-01-15T10:30:00Z",
                "query": "How do I activate my new card?",
                "intent": "activate_card",
                "confidence": 0.95,
                "status": "success",
                "response": "To activate your card, please follow these steps...",
                "requires_human": False,
                "escalation_reason": None,
                "follow_up_questions": ["Would you like me to guide you through the app?"],
                "metadata": {
                    "model": "claude-haiku-4-20250514",
                    "latency_ms": 523.45,
                    "cost_usd": 0.000125,
                    "sentiment": "neutral",
                    "urgency": 0.3
                }
            }
        }


# ============ Intent Schemas ============

class IntentCreate(BaseModel):
    """Schema for creating an intent."""
    id: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=200)
    category: str
    description: Optional[str] = None
    response_template: str
    follow_up_questions: List[str] = []
    matches_when: Optional[str] = None
    does_not_match_when: Optional[str] = None
    key_signals: List[str] = []
    hinglish_variants: List[str] = []
    example_queries: List[str] = []
    related_intents: List[str] = []
    requires_human: bool = False
    priority: int = Field(5, ge=1, le=10)


class IntentUpdate(BaseModel):
    """Schema for updating an intent."""
    name: Optional[str] = None
    description: Optional[str] = None
    response_template: Optional[str] = None
    follow_up_questions: Optional[List[str]] = None
    matches_when: Optional[str] = None
    does_not_match_when: Optional[str] = None
    key_signals: Optional[List[str]] = None
    hinglish_variants: Optional[List[str]] = None
    requires_human: Optional[bool] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None


class IntentResponse(BaseModel):
    """Response schema for intent."""
    id: str
    name: str
    category: str
    description: Optional[str]
    response_template: str
    follow_up_questions: List[str]
    matches_when: Optional[str]
    does_not_match_when: Optional[str]
    key_signals: List[str]
    hinglish_variants: List[str]
    requires_human: bool
    priority: int
    is_active: bool


# ============ Escalation Schemas ============

class EscalationStatus(str, Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class EscalationResponse(BaseModel):
    """Response schema for escalation."""
    id: int
    conversation_id: str
    reason: str
    status: EscalationStatus
    priority: int
    last_query: Optional[str]
    detected_intent: Optional[str]
    sentiment: Optional[str]
    urgency_score: Optional[float]
    assigned_to: Optional[str]
    assigned_at: Optional[datetime]
    resolution_notes: Optional[str]
    resolved_at: Optional[datetime]
    resolution_time_minutes: Optional[int]
    created_at: datetime


class EscalationAssign(BaseModel):
    """Schema for assigning escalation."""
    agent_id: str


class EscalationResolve(BaseModel):
    """Schema for resolving escalation."""
    resolution_notes: str = Field(..., min_length=1)


# ============ Analytics Schemas ============

class AnalyticsSummary(BaseModel):
    """Analytics summary response."""
    period: Dict[str, str]
    total_queries: int
    avg_confidence: float
    avg_latency_ms: float
    total_cost_usd: float
    escalation_rate: float


class IntentBreakdown(BaseModel):
    """Intent breakdown item."""
    intent: str
    count: int
    avg_confidence: float


class HourlyDistribution(BaseModel):
    """Hourly distribution item."""
    hour: int
    count: int


# ============ Health Check ============

class HealthCheck(BaseModel):
    """Health check response."""
    status: str
    version: str
    database: str
    llm_service: str


# ============ Feedback ============

class FeedbackRequest(BaseModel):
    """Feedback submission."""
    request_id: str
    rating: int = Field(..., ge=1, le=5)
    was_helpful: bool
    comment: Optional[str] = None


class FeedbackResponse(BaseModel):
    """Feedback response."""
    success: bool
    message: str

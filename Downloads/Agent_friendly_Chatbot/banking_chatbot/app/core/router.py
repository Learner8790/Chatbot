"""
Main Chat Router - the heart of the banking chatbot.
Handles query routing, response generation, and escalation logic.
"""
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
import uuid

from .intents import IntentManager, Intent
from .llm_client import LLMClient, ModelTier, RoutingDecision

logger = logging.getLogger(__name__)


class RoutingStatus(str, Enum):
    """Status of routing attempt."""
    SUCCESS = "success"
    LOW_CONFIDENCE = "low_confidence"
    NO_MATCH = "no_match"
    ERROR = "error"
    ESCALATED = "escalated"


@dataclass
class RoutingResult:
    """Complete result of routing a query."""
    # Identifiers
    request_id: str
    timestamp: datetime

    # Query info
    query: str
    detected_intent: Optional[str]
    intent_confidence: float

    # Status
    status: RoutingStatus
    requires_human: bool = False
    escalation_reason: Optional[str] = None

    # Response
    response: Optional[str] = None
    follow_up_questions: List[str] = field(default_factory=list)

    # Metadata
    model_used: str = ""
    latency_ms: float = 0.0
    cost_usd: float = 0.0

    # Sentiment analysis
    sentiment: str = "neutral"
    urgency_score: float = 0.5

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "request_id": self.request_id,
            "timestamp": self.timestamp.isoformat(),
            "query": self.query,
            "intent": self.detected_intent,
            "confidence": self.intent_confidence,
            "status": self.status.value,
            "requires_human": self.requires_human,
            "escalation_reason": self.escalation_reason,
            "response": self.response,
            "follow_up_questions": self.follow_up_questions,
            "metadata": {
                "model": self.model_used,
                "latency_ms": round(self.latency_ms, 2),
                "cost_usd": round(self.cost_usd, 6),
                "sentiment": self.sentiment,
                "urgency": self.urgency_score
            }
        }


class ChatRouter:
    """
    Main router for banking chatbot.
    Handles the complete flow from query to response.
    """

    def __init__(
        self,
        api_key: str,
        confidence_threshold: float = 0.7,
        escalation_threshold: float = 0.4,
        default_model: ModelTier = ModelTier.FAST
    ):
        """
        Initialize the chat router.

        Args:
            api_key: Anthropic API key
            confidence_threshold: Minimum confidence for auto-response
            escalation_threshold: Below this, escalate to human
            default_model: Default model tier for routing
        """
        self.llm = LLMClient(api_key)
        self.intent_manager = IntentManager()
        self.confidence_threshold = confidence_threshold
        self.escalation_threshold = escalation_threshold
        self.default_model = default_model

        # Cache routing rules for efficiency
        self._routing_rules_cache: Optional[str] = None
        self._intent_names_cache: Optional[List[str]] = None

    def _get_routing_rules(self) -> str:
        """Get cached routing rules."""
        if self._routing_rules_cache is None:
            self._routing_rules_cache = self.intent_manager.get_routing_rules_text()
        return self._routing_rules_cache

    def _get_intent_names(self) -> List[str]:
        """Get cached intent names."""
        if self._intent_names_cache is None:
            self._intent_names_cache = self.intent_manager.get_intent_names()
        return self._intent_names_cache

    def invalidate_cache(self) -> None:
        """Invalidate caches when intents change."""
        self._routing_rules_cache = None
        self._intent_names_cache = None

    def route(
        self,
        query: str,
        user_context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        analyze_sentiment: bool = True
    ) -> RoutingResult:
        """
        Route a customer query and generate response.

        Args:
            query: Customer's query text
            user_context: User/account context data
            session_id: Session identifier for tracking
            analyze_sentiment: Whether to analyze sentiment/urgency

        Returns:
            RoutingResult with complete response data
        """
        import time
        start_time = time.time()

        request_id = str(uuid.uuid4())[:8]
        timestamp = datetime.utcnow()
        user_context = user_context or {}

        # Step 1: Analyze sentiment (optional, parallel-friendly)
        sentiment = "neutral"
        urgency = 0.5
        if analyze_sentiment:
            sentiment, urgency = self.llm.analyze_sentiment(query)

        # Step 2: Route query to intent
        routing = self.llm.route_query(
            query=query,
            intent_names=self._get_intent_names(),
            routing_rules=self._get_routing_rules(),
            model_tier=self.default_model,
            include_confidence=True
        )

        # Step 3: Determine status and whether to escalate
        intent = self.intent_manager.get_intent(routing.intent_id)
        status = RoutingStatus.SUCCESS
        requires_human = False
        escalation_reason = None

        # Check confidence thresholds
        if routing.confidence < self.escalation_threshold:
            status = RoutingStatus.NO_MATCH
            requires_human = True
            escalation_reason = f"Low confidence ({routing.confidence:.2f})"
        elif routing.confidence < self.confidence_threshold:
            status = RoutingStatus.LOW_CONFIDENCE

        # Check if intent requires human
        if intent and intent.requires_human:
            requires_human = True
            escalation_reason = "Intent requires human agent"

        # Check urgency
        if urgency > 0.8 and sentiment in ["frustrated", "negative"]:
            requires_human = True
            escalation_reason = "High urgency with negative sentiment"
            if status == RoutingStatus.SUCCESS:
                status = RoutingStatus.ESCALATED

        # Step 4: Generate response
        response = None
        follow_ups = []

        if intent and not requires_human:
            # Generate personalized response
            llm_response = self.llm.generate_response(
                query=query,
                intent_id=intent.id,
                response_template=intent.response_template,
                context=user_context,
                model_tier=ModelTier.BALANCED if routing.confidence > 0.8 else ModelTier.FAST
            )
            response = llm_response.content
            follow_ups = intent.follow_up_questions

        elif requires_human:
            response = self._generate_escalation_message(sentiment, urgency)
        else:
            response = "I'm not sure I understood your query. Could you please rephrase or provide more details?"

        # Calculate total latency
        total_latency = (time.time() - start_time) * 1000

        return RoutingResult(
            request_id=request_id,
            timestamp=timestamp,
            query=query,
            detected_intent=routing.intent_id,
            intent_confidence=routing.confidence,
            status=status,
            requires_human=requires_human,
            escalation_reason=escalation_reason,
            response=response,
            follow_up_questions=follow_ups,
            model_used=self.llm.MODEL_MAP[self.default_model],
            latency_ms=total_latency,
            cost_usd=self.llm.get_usage_stats()["total_cost_usd"],
            sentiment=sentiment,
            urgency_score=urgency
        )

    def _generate_escalation_message(self, sentiment: str, urgency: float) -> str:
        """Generate appropriate escalation message based on sentiment."""
        if sentiment == "frustrated" or urgency > 0.8:
            return """I understand this is urgent and you're frustrated. I'm connecting you to a senior support executive right away.

While you wait (typically under 2 minutes):
- Your concern is our priority
- A specialist will have full context of your issue
- You can also reach us at 1800-XXX-XXXX (24x7)

Thank you for your patience."""

        elif sentiment == "negative":
            return """I apologize for any inconvenience. Let me connect you with a human agent who can better assist you.

Estimated wait: 3-5 minutes
Alternative: Call 1800-XXX-XXXX

Your satisfaction is important to us."""

        else:
            return """I'd like to connect you with a specialist who can better help with your query.

You'll be connected shortly. Estimated wait: 2-3 minutes.

Is there anything specific you'd like me to note for the agent?"""

    def route_simple(self, query: str) -> str:
        """
        Simple routing that returns just the intent ID.
        Useful for testing and simple use cases.
        """
        routing = self.llm.route_query(
            query=query,
            intent_names=self._get_intent_names(),
            routing_rules=self._get_routing_rules(),
            model_tier=self.default_model,
            include_confidence=False
        )
        return routing.intent_id

    def get_intent(self, intent_id: str) -> Optional[Intent]:
        """Get intent by ID."""
        return self.intent_manager.get_intent(intent_id)

    def add_intent(self, intent: Intent) -> None:
        """Add a new intent."""
        self.intent_manager.add_intent(intent)
        self.invalidate_cache()

    def remove_intent(self, intent_id: str) -> bool:
        """Remove an intent."""
        result = self.intent_manager.remove_intent(intent_id)
        if result:
            self.invalidate_cache()
        return result

    def get_all_intents(self) -> List[Intent]:
        """Get all intents."""
        return self.intent_manager.get_all_intents()

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get LLM usage statistics."""
        return self.llm.get_usage_stats()

    def reset_usage_stats(self) -> None:
        """Reset usage statistics."""
        self.llm.reset_usage_stats()

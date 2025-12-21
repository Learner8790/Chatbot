"""
Human Escalation System.
Handles escalation triggers, notifications, and agent assignment.
"""
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import httpx
import asyncio
import logging

logger = logging.getLogger(__name__)


class EscalationReason(str, Enum):
    """Reasons for escalation."""
    LOW_CONFIDENCE = "low_confidence"
    NEGATIVE_SENTIMENT = "negative_sentiment"
    HIGH_URGENCY = "high_urgency"
    FRAUD_DETECTED = "fraud_detected"
    EXPLICIT_REQUEST = "explicit_request"
    MULTIPLE_FAILURES = "multiple_failures"
    INTENT_REQUIRES_HUMAN = "intent_requires_human"
    VIP_CUSTOMER = "vip_customer"


class EscalationPriority(int, Enum):
    """Priority levels for escalation."""
    LOW = 1
    NORMAL = 5
    HIGH = 8
    CRITICAL = 10


@dataclass
class EscalationRequest:
    """Escalation request details."""
    conversation_id: str
    user_id: Optional[str]
    session_id: Optional[str]
    reason: EscalationReason
    priority: EscalationPriority
    last_query: str
    detected_intent: Optional[str]
    confidence: float
    sentiment: str
    urgency_score: float
    context: Dict[str, Any]
    timestamp: datetime


class EscalationManager:
    """
    Manages human escalation workflow.

    Features:
    - Webhook notifications
    - Email alerts (optional)
    - Priority-based queue
    - Auto-assignment logic
    """

    def __init__(
        self,
        webhook_url: Optional[str] = None,
        email_config: Optional[Dict] = None,
        auto_assign: bool = False
    ):
        """
        Initialize escalation manager.

        Args:
            webhook_url: URL to send escalation webhooks
            email_config: Email configuration for alerts
            auto_assign: Whether to auto-assign to available agents
        """
        self.webhook_url = webhook_url
        self.email_config = email_config
        self.auto_assign = auto_assign
        self._pending_escalations: List[EscalationRequest] = []
        self._agents: Dict[str, Dict] = {}  # agent_id -> agent info

    def should_escalate(
        self,
        confidence: float,
        sentiment: str,
        urgency: float,
        intent_requires_human: bool,
        is_vip: bool = False,
        failure_count: int = 0
    ) -> tuple[bool, Optional[EscalationReason], EscalationPriority]:
        """
        Determine if escalation is needed.

        Returns:
            Tuple of (should_escalate, reason, priority)
        """
        # VIP customers always get priority
        if is_vip:
            return True, EscalationReason.VIP_CUSTOMER, EscalationPriority.HIGH

        # Intent requires human
        if intent_requires_human:
            return True, EscalationReason.INTENT_REQUIRES_HUMAN, EscalationPriority.NORMAL

        # Multiple failures
        if failure_count >= 3:
            return True, EscalationReason.MULTIPLE_FAILURES, EscalationPriority.HIGH

        # Very low confidence
        if confidence < 0.3:
            return True, EscalationReason.LOW_CONFIDENCE, EscalationPriority.NORMAL

        # Frustrated customer with high urgency
        if sentiment == "frustrated" and urgency > 0.7:
            return True, EscalationReason.HIGH_URGENCY, EscalationPriority.HIGH

        # Negative sentiment with moderate urgency
        if sentiment == "negative" and urgency > 0.5:
            return True, EscalationReason.NEGATIVE_SENTIMENT, EscalationPriority.NORMAL

        # Critical urgency
        if urgency > 0.9:
            return True, EscalationReason.HIGH_URGENCY, EscalationPriority.CRITICAL

        return False, None, EscalationPriority.NORMAL

    async def create_escalation(
        self,
        request: EscalationRequest
    ) -> Dict[str, Any]:
        """
        Create and process an escalation.

        Args:
            request: Escalation request details

        Returns:
            Escalation result with ticket ID
        """
        # Generate ticket ID
        ticket_id = f"ESC-{datetime.utcnow().strftime('%Y%m%d')}-{len(self._pending_escalations) + 1:04d}"

        # Add to queue
        self._pending_escalations.append(request)

        # Notify via webhook
        if self.webhook_url:
            await self._send_webhook(ticket_id, request)

        # Send email if configured
        if self.email_config:
            await self._send_email(ticket_id, request)

        # Auto-assign if enabled
        assigned_to = None
        if self.auto_assign:
            assigned_to = self._find_available_agent(request.priority)

        return {
            "ticket_id": ticket_id,
            "status": "created",
            "priority": request.priority.value,
            "reason": request.reason.value,
            "assigned_to": assigned_to,
            "estimated_wait_minutes": self._estimate_wait_time(request.priority),
            "message": self._get_escalation_message(request)
        }

    async def _send_webhook(
        self,
        ticket_id: str,
        request: EscalationRequest
    ) -> bool:
        """Send webhook notification."""
        if not self.webhook_url:
            return False

        payload = {
            "ticket_id": ticket_id,
            "type": "escalation",
            "priority": request.priority.value,
            "reason": request.reason.value,
            "conversation_id": request.conversation_id,
            "user_id": request.user_id,
            "last_query": request.last_query,
            "detected_intent": request.detected_intent,
            "confidence": request.confidence,
            "sentiment": request.sentiment,
            "urgency": request.urgency_score,
            "timestamp": request.timestamp.isoformat()
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json=payload,
                    timeout=10.0
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Webhook failed: {e}")
            return False

    async def _send_email(
        self,
        ticket_id: str,
        request: EscalationRequest
    ) -> bool:
        """Send email notification."""
        # Placeholder for email integration
        # In production, integrate with SendGrid, SES, etc.
        logger.info(f"Email notification for {ticket_id} would be sent here")
        return True

    def _find_available_agent(
        self,
        priority: EscalationPriority
    ) -> Optional[str]:
        """Find available agent for assignment."""
        # Simple round-robin for now
        # In production, consider agent skills, load, etc.
        available = [
            agent_id for agent_id, info in self._agents.items()
            if info.get("available", False)
        ]
        if available:
            return available[0]
        return None

    def _estimate_wait_time(self, priority: EscalationPriority) -> int:
        """Estimate wait time in minutes."""
        base_times = {
            EscalationPriority.CRITICAL: 1,
            EscalationPriority.HIGH: 3,
            EscalationPriority.NORMAL: 10,
            EscalationPriority.LOW: 20
        }
        pending_count = len(self._pending_escalations)
        return base_times.get(priority, 10) + (pending_count * 2)

    def _get_escalation_message(self, request: EscalationRequest) -> str:
        """Generate appropriate escalation message for user."""
        if request.priority == EscalationPriority.CRITICAL:
            return """I understand this is urgent. I'm connecting you with a senior specialist immediately.

You're at the front of the queue - expected wait: under 2 minutes.

While you wait:
- Your issue is marked as highest priority
- A specialist will have full context of your conversation

Alternatively, call our priority line: 1800-XXX-1234"""

        elif request.sentiment == "frustrated":
            return """I sincerely apologize for the frustration. I'm connecting you with a human agent right away.

Your satisfaction is our priority. Expected wait: 3-5 minutes.

The agent will have complete context of our conversation and will work to resolve this for you."""

        elif request.reason == EscalationReason.FRAUD_DETECTED:
            return """Your account security is our top priority. I've flagged this for immediate review.

A fraud specialist will contact you within 5 minutes on your registered phone number.

In the meantime:
- Do NOT share any OTP with anyone
- Your card has been temporarily blocked for safety"""

        else:
            return """I'd like to connect you with a specialist who can better assist you.

Expected wait: 5-10 minutes.

Is there anything specific you'd like me to note for the agent?"""

    def register_agent(
        self,
        agent_id: str,
        name: str,
        skills: List[str] = None,
        available: bool = True
    ) -> None:
        """Register an agent for escalation handling."""
        self._agents[agent_id] = {
            "name": name,
            "skills": skills or [],
            "available": available,
            "current_load": 0
        }

    def set_agent_availability(self, agent_id: str, available: bool) -> None:
        """Set agent availability."""
        if agent_id in self._agents:
            self._agents[agent_id]["available"] = available

    def get_queue_status(self) -> Dict[str, Any]:
        """Get current escalation queue status."""
        priority_counts = {}
        for req in self._pending_escalations:
            p = req.priority.name
            priority_counts[p] = priority_counts.get(p, 0) + 1

        return {
            "total_pending": len(self._pending_escalations),
            "by_priority": priority_counts,
            "available_agents": sum(
                1 for a in self._agents.values() if a.get("available")
            ),
            "total_agents": len(self._agents)
        }

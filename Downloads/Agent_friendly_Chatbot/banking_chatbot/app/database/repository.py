"""
Repository classes for database operations.
Provides clean interface for data access.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
import uuid

from .models import (
    Conversation, Message, Intent, Analytics,
    Escalation, FAQ, User, MessageRole, EscalationStatus
)


class ConversationRepository:
    """Repository for conversation operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        user_context: Optional[Dict] = None
    ) -> Conversation:
        """Create a new conversation."""
        conversation = Conversation(
            id=str(uuid.uuid4())[:12],
            user_id=user_id,
            session_id=session_id,
            user_context=user_context or {},
        )
        self.session.add(conversation)
        await self.session.flush()
        return conversation

    async def get_by_id(self, conversation_id: str) -> Optional[Conversation]:
        """Get conversation by ID."""
        result = await self.session.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        return result.scalar_one_or_none()

    async def get_active_by_user(self, user_id: str) -> Optional[Conversation]:
        """Get active conversation for a user."""
        result = await self.session.execute(
            select(Conversation)
            .where(and_(
                Conversation.user_id == user_id,
                Conversation.is_active == True
            ))
            .order_by(desc(Conversation.started_at))
        )
        return result.scalar_one_or_none()

    async def add_message(
        self,
        conversation_id: str,
        role: MessageRole,
        content: str,
        intent: Optional[str] = None,
        confidence: Optional[float] = None,
        sentiment: Optional[str] = None,
        urgency: Optional[float] = None,
        latency_ms: Optional[float] = None,
        cost_usd: Optional[float] = None,
        model_used: Optional[str] = None
    ) -> Message:
        """Add a message to a conversation."""
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            detected_intent=intent,
            intent_confidence=confidence,
            sentiment=sentiment,
            urgency_score=urgency,
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            model_used=model_used,
        )
        self.session.add(message)

        # Update conversation stats
        conversation = await self.get_by_id(conversation_id)
        if conversation:
            conversation.message_count += 1
            if cost_usd:
                conversation.total_cost_usd += cost_usd
            if intent:
                conversation.last_intent = intent

        await self.session.flush()
        return message

    async def get_messages(
        self,
        conversation_id: str,
        limit: int = 50
    ) -> List[Message]:
        """Get messages for a conversation."""
        result = await self.session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.timestamp)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def end_conversation(self, conversation_id: str) -> None:
        """Mark conversation as ended."""
        conversation = await self.get_by_id(conversation_id)
        if conversation:
            conversation.is_active = False
            conversation.ended_at = datetime.utcnow()

    async def get_recent_conversations(
        self,
        limit: int = 100,
        user_id: Optional[str] = None
    ) -> List[Conversation]:
        """Get recent conversations."""
        query = select(Conversation).order_by(desc(Conversation.started_at))
        if user_id:
            query = query.where(Conversation.user_id == user_id)
        result = await self.session.execute(query.limit(limit))
        return list(result.scalars().all())


class IntentRepository:
    """Repository for intent operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, intent_data: Dict[str, Any]) -> Intent:
        """Create a new intent."""
        intent = Intent(**intent_data)
        self.session.add(intent)
        await self.session.flush()
        return intent

    async def get_by_id(self, intent_id: str) -> Optional[Intent]:
        """Get intent by ID."""
        result = await self.session.execute(
            select(Intent).where(Intent.id == intent_id)
        )
        return result.scalar_one_or_none()

    async def get_all_active(self) -> List[Intent]:
        """Get all active intents."""
        result = await self.session.execute(
            select(Intent).where(Intent.is_active == True)
        )
        return list(result.scalars().all())

    async def get_by_category(self, category: str) -> List[Intent]:
        """Get intents by category."""
        result = await self.session.execute(
            select(Intent).where(and_(
                Intent.category == category,
                Intent.is_active == True
            ))
        )
        return list(result.scalars().all())

    async def update(
        self,
        intent_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Intent]:
        """Update an intent."""
        intent = await self.get_by_id(intent_id)
        if intent:
            for key, value in updates.items():
                if hasattr(intent, key):
                    setattr(intent, key, value)
            await self.session.flush()
        return intent

    async def delete(self, intent_id: str) -> bool:
        """Soft delete an intent."""
        intent = await self.get_by_id(intent_id)
        if intent:
            intent.is_active = False
            return True
        return False


class AnalyticsRepository:
    """Repository for analytics operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def record(
        self,
        intent_id: Optional[str],
        confidence: Optional[float],
        latency_ms: Optional[float],
        cost_usd: Optional[float],
        model_used: Optional[str],
        sentiment: Optional[str] = None,
        escalated: bool = False,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Analytics:
        """Record an analytics event."""
        now = datetime.utcnow()
        analytics = Analytics(
            timestamp=now,
            date=now.strftime("%Y-%m-%d"),
            hour=now.hour,
            intent_id=intent_id,
            confidence=confidence,
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            model_used=model_used,
            sentiment=sentiment,
            escalated=escalated,
            user_id=user_id,
            session_id=session_id,
        )
        self.session.add(analytics)
        await self.session.flush()
        return analytics

    async def get_summary(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get analytics summary."""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=7)
        if not end_date:
            end_date = datetime.utcnow()

        result = await self.session.execute(
            select(
                func.count(Analytics.id).label("total_queries"),
                func.avg(Analytics.confidence).label("avg_confidence"),
                func.avg(Analytics.latency_ms).label("avg_latency_ms"),
                func.sum(Analytics.cost_usd).label("total_cost_usd"),
                func.sum(Analytics.escalated.cast(Integer)).label("escalations"),
            )
            .where(and_(
                Analytics.timestamp >= start_date,
                Analytics.timestamp <= end_date
            ))
        )
        row = result.one()

        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "total_queries": row.total_queries or 0,
            "avg_confidence": round(row.avg_confidence or 0, 3),
            "avg_latency_ms": round(row.avg_latency_ms or 0, 2),
            "total_cost_usd": round(row.total_cost_usd or 0, 4),
            "escalation_rate": round(
                (row.escalations or 0) / max(row.total_queries or 1, 1) * 100, 2
            )
        }

    async def get_intent_breakdown(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get breakdown by intent."""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=7)
        if not end_date:
            end_date = datetime.utcnow()

        from sqlalchemy import Integer

        result = await self.session.execute(
            select(
                Analytics.intent_id,
                func.count(Analytics.id).label("count"),
                func.avg(Analytics.confidence).label("avg_confidence"),
            )
            .where(and_(
                Analytics.timestamp >= start_date,
                Analytics.timestamp <= end_date,
                Analytics.intent_id != None
            ))
            .group_by(Analytics.intent_id)
            .order_by(desc(func.count(Analytics.id)))
        )

        return [
            {
                "intent": row.intent_id,
                "count": row.count,
                "avg_confidence": round(row.avg_confidence or 0, 3)
            }
            for row in result.all()
        ]

    async def get_hourly_distribution(
        self,
        date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get hourly query distribution."""
        if not date:
            date = datetime.utcnow().strftime("%Y-%m-%d")

        result = await self.session.execute(
            select(
                Analytics.hour,
                func.count(Analytics.id).label("count"),
            )
            .where(Analytics.date == date)
            .group_by(Analytics.hour)
            .order_by(Analytics.hour)
        )

        # Fill in missing hours with 0
        hourly_data = {row.hour: row.count for row in result.all()}
        return [
            {"hour": h, "count": hourly_data.get(h, 0)}
            for h in range(24)
        ]


class EscalationRepository:
    """Repository for escalation operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        conversation_id: str,
        reason: str,
        last_query: Optional[str] = None,
        detected_intent: Optional[str] = None,
        sentiment: Optional[str] = None,
        urgency_score: Optional[float] = None,
        priority: int = 5
    ) -> Escalation:
        """Create a new escalation."""
        escalation = Escalation(
            conversation_id=conversation_id,
            reason=reason,
            last_query=last_query,
            detected_intent=detected_intent,
            sentiment=sentiment,
            urgency_score=urgency_score,
            priority=priority,
        )
        self.session.add(escalation)
        await self.session.flush()
        return escalation

    async def get_pending(self, limit: int = 50) -> List[Escalation]:
        """Get pending escalations."""
        result = await self.session.execute(
            select(Escalation)
            .where(Escalation.status == EscalationStatus.PENDING)
            .order_by(desc(Escalation.priority), Escalation.created_at)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def assign(
        self,
        escalation_id: int,
        agent_id: str
    ) -> Optional[Escalation]:
        """Assign escalation to an agent."""
        result = await self.session.execute(
            select(Escalation).where(Escalation.id == escalation_id)
        )
        escalation = result.scalar_one_or_none()
        if escalation:
            escalation.status = EscalationStatus.ASSIGNED
            escalation.assigned_to = agent_id
            escalation.assigned_at = datetime.utcnow()
        return escalation

    async def resolve(
        self,
        escalation_id: int,
        resolution_notes: str
    ) -> Optional[Escalation]:
        """Resolve an escalation."""
        result = await self.session.execute(
            select(Escalation).where(Escalation.id == escalation_id)
        )
        escalation = result.scalar_one_or_none()
        if escalation:
            escalation.status = EscalationStatus.RESOLVED
            escalation.resolution_notes = resolution_notes
            escalation.resolved_at = datetime.utcnow()
            if escalation.created_at:
                diff = escalation.resolved_at - escalation.created_at
                escalation.resolution_time_minutes = int(diff.total_seconds() / 60)
        return escalation

    async def get_stats(self) -> Dict[str, Any]:
        """Get escalation statistics."""
        from sqlalchemy import Integer

        result = await self.session.execute(
            select(
                func.count(Escalation.id).label("total"),
                func.sum((Escalation.status == EscalationStatus.PENDING).cast(Integer)).label("pending"),
                func.sum((Escalation.status == EscalationStatus.RESOLVED).cast(Integer)).label("resolved"),
                func.avg(Escalation.resolution_time_minutes).label("avg_resolution_time"),
            )
        )
        row = result.one()

        return {
            "total": row.total or 0,
            "pending": row.pending or 0,
            "resolved": row.resolved or 0,
            "avg_resolution_time_minutes": round(row.avg_resolution_time or 0, 1)
        }

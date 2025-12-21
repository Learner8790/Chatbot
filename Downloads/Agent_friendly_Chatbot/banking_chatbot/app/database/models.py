"""
SQLAlchemy models for Banking Chatbot.
Supports SQLite for development, PostgreSQL for production.
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime,
    Text, JSON, ForeignKey, Enum as SQLEnum, Index
)
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.sql import func
import enum


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class MessageRole(str, enum.Enum):
    """Role of message sender."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class EscalationStatus(str, enum.Enum):
    """Status of escalation."""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class Conversation(Base):
    """
    Represents a conversation session with a user.
    """
    __tablename__ = "conversations"

    id = Column(String(50), primary_key=True)
    user_id = Column(String(100), nullable=True, index=True)
    session_id = Column(String(100), nullable=True, index=True)

    # Conversation metadata
    started_at = Column(DateTime, default=func.now())
    ended_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    # Summary statistics
    message_count = Column(Integer, default=0)
    total_cost_usd = Column(Float, default=0.0)
    avg_confidence = Column(Float, default=0.0)

    # Context
    user_context = Column(JSON, default=dict)
    last_intent = Column(String(100), nullable=True)

    # Relationships
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    escalations = relationship("Escalation", back_populates="conversation", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('idx_conversation_user_session', 'user_id', 'session_id'),
        Index('idx_conversation_active', 'is_active', 'started_at'),
    )


class Message(Base):
    """
    Individual message in a conversation.
    """
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String(50), ForeignKey("conversations.id"), nullable=False)

    # Message content
    role = Column(SQLEnum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=func.now())

    # Routing info (for user messages)
    detected_intent = Column(String(100), nullable=True)
    intent_confidence = Column(Float, nullable=True)
    sentiment = Column(String(20), nullable=True)
    urgency_score = Column(Float, nullable=True)

    # Performance metrics
    latency_ms = Column(Float, nullable=True)
    cost_usd = Column(Float, nullable=True)
    model_used = Column(String(50), nullable=True)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

    # Indexes
    __table_args__ = (
        Index('idx_message_conversation', 'conversation_id', 'timestamp'),
        Index('idx_message_intent', 'detected_intent'),
    )


class Intent(Base):
    """
    Stored intent definitions (for dynamic updates).
    """
    __tablename__ = "intents"

    id = Column(String(100), primary_key=True)
    name = Column(String(200), nullable=False)
    category = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Response configuration
    response_template = Column(Text, nullable=False)
    follow_up_questions = Column(JSON, default=list)

    # Agent-friendly metadata
    matches_when = Column(Text, nullable=True)
    does_not_match_when = Column(Text, nullable=True)
    key_signals = Column(JSON, default=list)
    hinglish_variants = Column(JSON, default=list)
    example_queries = Column(JSON, default=list)
    related_intents = Column(JSON, default=list)

    # Settings
    requires_human = Column(Boolean, default=False)
    priority = Column(Integer, default=5)
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Indexes
    __table_args__ = (
        Index('idx_intent_category_active', 'category', 'is_active'),
    )


class Analytics(Base):
    """
    Analytics data for tracking performance.
    """
    __tablename__ = "analytics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=func.now(), index=True)
    date = Column(String(10), index=True)  # YYYY-MM-DD for easy grouping
    hour = Column(Integer)  # 0-23

    # Query metrics
    intent_id = Column(String(100), nullable=True, index=True)
    confidence = Column(Float, nullable=True)
    was_correct = Column(Boolean, nullable=True)  # For feedback tracking

    # Performance
    latency_ms = Column(Float, nullable=True)
    cost_usd = Column(Float, nullable=True)
    model_used = Column(String(50), nullable=True)

    # User experience
    sentiment = Column(String(20), nullable=True)
    escalated = Column(Boolean, default=False)
    feedback_rating = Column(Integer, nullable=True)  # 1-5

    # Context
    user_id = Column(String(100), nullable=True)
    session_id = Column(String(100), nullable=True)

    # Indexes
    __table_args__ = (
        Index('idx_analytics_date_intent', 'date', 'intent_id'),
        Index('idx_analytics_escalated', 'escalated', 'timestamp'),
    )


class Escalation(Base):
    """
    Human escalation tracking.
    """
    __tablename__ = "escalations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String(50), ForeignKey("conversations.id"), nullable=False)

    # Escalation details
    reason = Column(Text, nullable=False)
    status = Column(SQLEnum(EscalationStatus), default=EscalationStatus.PENDING)
    priority = Column(Integer, default=5)  # 1=lowest, 10=highest

    # Context
    last_query = Column(Text, nullable=True)
    detected_intent = Column(String(100), nullable=True)
    sentiment = Column(String(20), nullable=True)
    urgency_score = Column(Float, nullable=True)

    # Assignment
    assigned_to = Column(String(100), nullable=True)
    assigned_at = Column(DateTime, nullable=True)

    # Resolution
    resolution_notes = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolution_time_minutes = Column(Integer, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    conversation = relationship("Conversation", back_populates="escalations")

    # Indexes
    __table_args__ = (
        Index('idx_escalation_status', 'status', 'priority'),
        Index('idx_escalation_assigned', 'assigned_to', 'status'),
    )


class FAQ(Base):
    """
    FAQ entries for common questions.
    """
    __tablename__ = "faqs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    category = Column(String(50), index=True)

    # For search
    keywords = Column(JSON, default=list)
    related_intents = Column(JSON, default=list)

    # Metadata
    view_count = Column(Integer, default=0)
    helpful_count = Column(Integer, default=0)
    not_helpful_count = Column(Integer, default=0)

    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class User(Base):
    """
    User information for personalization.
    """
    __tablename__ = "users"

    id = Column(String(100), primary_key=True)
    email = Column(String(200), nullable=True, unique=True)
    phone = Column(String(20), nullable=True)
    name = Column(String(200), nullable=True)

    # Preferences
    language = Column(String(10), default="en")
    notification_preferences = Column(JSON, default=dict)

    # Account info (stored securely)
    account_type = Column(String(50), nullable=True)
    kyc_verified = Column(Boolean, default=False)

    # Activity
    last_active = Column(DateTime, nullable=True)
    total_conversations = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

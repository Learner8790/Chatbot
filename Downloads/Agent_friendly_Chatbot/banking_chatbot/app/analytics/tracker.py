"""
Analytics Tracker for Banking Chatbot.
Tracks all metrics for performance monitoring and improvement.
"""
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict
import json
import logging

logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    """Types of metrics tracked."""
    QUERY = "query"
    ROUTING = "routing"
    RESPONSE = "response"
    ESCALATION = "escalation"
    FEEDBACK = "feedback"
    ERROR = "error"


@dataclass
class MetricEvent:
    """Individual metric event."""
    metric_type: MetricType
    timestamp: datetime
    intent: Optional[str]
    confidence: Optional[float]
    latency_ms: Optional[float]
    cost_usd: Optional[float]
    sentiment: Optional[str]
    escalated: bool
    user_id: Optional[str]
    session_id: Optional[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


class AnalyticsTracker:
    """
    In-memory analytics tracker with aggregation.

    For production, integrate with:
    - Database (PostgreSQL/TimescaleDB)
    - Time-series DB (InfluxDB, Prometheus)
    - Cloud services (AWS CloudWatch, GCP Monitoring)
    """

    def __init__(self, retention_hours: int = 24):
        """
        Initialize analytics tracker.

        Args:
            retention_hours: How long to keep events in memory
        """
        self.retention_hours = retention_hours
        self._events: List[MetricEvent] = []
        self._counters: Dict[str, int] = defaultdict(int)
        self._aggregates: Dict[str, List[float]] = defaultdict(list)

        # Real-time metrics
        self._total_queries = 0
        self._total_cost = 0.0
        self._total_latency = 0.0
        self._escalation_count = 0
        self._error_count = 0

    def track(
        self,
        metric_type: MetricType,
        intent: Optional[str] = None,
        confidence: Optional[float] = None,
        latency_ms: Optional[float] = None,
        cost_usd: Optional[float] = None,
        sentiment: Optional[str] = None,
        escalated: bool = False,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        **metadata
    ) -> None:
        """Track a metric event."""
        event = MetricEvent(
            metric_type=metric_type,
            timestamp=datetime.utcnow(),
            intent=intent,
            confidence=confidence,
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            sentiment=sentiment,
            escalated=escalated,
            user_id=user_id,
            session_id=session_id,
            metadata=metadata
        )

        self._events.append(event)
        self._update_counters(event)
        self._cleanup_old_events()

    def _update_counters(self, event: MetricEvent) -> None:
        """Update real-time counters."""
        if event.metric_type == MetricType.QUERY:
            self._total_queries += 1

        if event.latency_ms:
            self._total_latency += event.latency_ms
            self._aggregates["latency"].append(event.latency_ms)

        if event.cost_usd:
            self._total_cost += event.cost_usd

        if event.confidence:
            self._aggregates["confidence"].append(event.confidence)

        if event.escalated:
            self._escalation_count += 1

        if event.metric_type == MetricType.ERROR:
            self._error_count += 1

        if event.intent:
            self._counters[f"intent:{event.intent}"] += 1

        if event.sentiment:
            self._counters[f"sentiment:{event.sentiment}"] += 1

    def _cleanup_old_events(self) -> None:
        """Remove events older than retention period."""
        cutoff = datetime.utcnow() - timedelta(hours=self.retention_hours)
        self._events = [e for e in self._events if e.timestamp > cutoff]

    def get_summary(self) -> Dict[str, Any]:
        """Get current summary metrics."""
        confidence_values = self._aggregates.get("confidence", [])
        latency_values = self._aggregates.get("latency", [])

        return {
            "total_queries": self._total_queries,
            "total_cost_usd": round(self._total_cost, 4),
            "avg_confidence": round(
                sum(confidence_values) / len(confidence_values), 3
            ) if confidence_values else 0,
            "avg_latency_ms": round(
                sum(latency_values) / len(latency_values), 2
            ) if latency_values else 0,
            "escalation_rate": round(
                self._escalation_count / max(self._total_queries, 1) * 100, 2
            ),
            "error_rate": round(
                self._error_count / max(self._total_queries, 1) * 100, 2
            ),
            "events_in_memory": len(self._events)
        }

    def get_intent_breakdown(self) -> List[Dict[str, Any]]:
        """Get breakdown by intent."""
        intent_counts = {
            k.replace("intent:", ""): v
            for k, v in self._counters.items()
            if k.startswith("intent:")
        }

        sorted_intents = sorted(
            intent_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return [
            {"intent": intent, "count": count}
            for intent, count in sorted_intents
        ]

    def get_sentiment_breakdown(self) -> Dict[str, int]:
        """Get breakdown by sentiment."""
        return {
            k.replace("sentiment:", ""): v
            for k, v in self._counters.items()
            if k.startswith("sentiment:")
        }

    def get_hourly_distribution(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get query distribution by hour."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        relevant_events = [
            e for e in self._events
            if e.timestamp > cutoff and e.metric_type == MetricType.QUERY
        ]

        hourly = defaultdict(int)
        for event in relevant_events:
            hour = event.timestamp.hour
            hourly[hour] += 1

        return [
            {"hour": h, "count": hourly.get(h, 0)}
            for h in range(24)
        ]

    def get_percentiles(self, metric: str = "latency") -> Dict[str, float]:
        """Get percentile values for a metric."""
        values = sorted(self._aggregates.get(metric, []))
        if not values:
            return {"p50": 0, "p90": 0, "p95": 0, "p99": 0}

        def percentile(data: List[float], p: float) -> float:
            idx = int(len(data) * p / 100)
            return data[min(idx, len(data) - 1)]

        return {
            "p50": round(percentile(values, 50), 2),
            "p90": round(percentile(values, 90), 2),
            "p95": round(percentile(values, 95), 2),
            "p99": round(percentile(values, 99), 2),
        }

    def get_recent_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent error events."""
        errors = [
            e for e in reversed(self._events)
            if e.metric_type == MetricType.ERROR
        ][:limit]

        return [
            {
                "timestamp": e.timestamp.isoformat(),
                "intent": e.intent,
                "metadata": e.metadata
            }
            for e in errors
        ]

    def export_events(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Export events as list of dicts."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        relevant = [e for e in self._events if e.timestamp > cutoff]

        return [
            {
                "type": e.metric_type.value,
                "timestamp": e.timestamp.isoformat(),
                "intent": e.intent,
                "confidence": e.confidence,
                "latency_ms": e.latency_ms,
                "cost_usd": e.cost_usd,
                "sentiment": e.sentiment,
                "escalated": e.escalated,
                "user_id": e.user_id,
                "session_id": e.session_id,
                **e.metadata
            }
            for e in relevant
        ]

    def reset(self) -> None:
        """Reset all metrics."""
        self._events.clear()
        self._counters.clear()
        self._aggregates.clear()
        self._total_queries = 0
        self._total_cost = 0.0
        self._total_latency = 0.0
        self._escalation_count = 0
        self._error_count = 0


# Global tracker instance
_tracker: Optional[AnalyticsTracker] = None


def get_tracker() -> AnalyticsTracker:
    """Get global tracker instance."""
    global _tracker
    if _tracker is None:
        _tracker = AnalyticsTracker()
    return _tracker

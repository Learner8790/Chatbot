"""
Tests for Analytics module.
"""
import pytest
from datetime import datetime, timedelta
from app.analytics.tracker import AnalyticsTracker, MetricType


class TestAnalyticsTracker:
    """Tests for AnalyticsTracker class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tracker = AnalyticsTracker(retention_hours=24)

    def test_track_query(self):
        """Test tracking a query event."""
        self.tracker.track(
            metric_type=MetricType.QUERY,
            intent="activate_card",
            confidence=0.95,
            latency_ms=100.0,
            cost_usd=0.0001
        )

        summary = self.tracker.get_summary()
        assert summary["total_queries"] == 1
        assert summary["avg_confidence"] == 0.95

    def test_track_multiple_events(self):
        """Test tracking multiple events."""
        for i in range(10):
            self.tracker.track(
                metric_type=MetricType.QUERY,
                intent="test_intent",
                confidence=0.8 + (i * 0.01),
                latency_ms=100 + i
            )

        summary = self.tracker.get_summary()
        assert summary["total_queries"] == 10

    def test_track_escalation(self):
        """Test tracking escalation event."""
        self.tracker.track(
            metric_type=MetricType.QUERY,
            intent="unknown",
            confidence=0.3,
            escalated=True
        )

        summary = self.tracker.get_summary()
        assert summary["escalation_rate"] > 0

    def test_track_error(self):
        """Test tracking error event."""
        self.tracker.track(
            metric_type=MetricType.ERROR,
            intent="failed_intent"
        )

        summary = self.tracker.get_summary()
        assert summary["error_rate"] > 0

    def test_intent_breakdown(self):
        """Test getting intent breakdown."""
        self.tracker.track(MetricType.QUERY, intent="intent_a")
        self.tracker.track(MetricType.QUERY, intent="intent_a")
        self.tracker.track(MetricType.QUERY, intent="intent_b")

        breakdown = self.tracker.get_intent_breakdown()
        assert len(breakdown) == 2
        assert breakdown[0]["intent"] == "intent_a"
        assert breakdown[0]["count"] == 2

    def test_sentiment_breakdown(self):
        """Test getting sentiment breakdown."""
        self.tracker.track(MetricType.QUERY, sentiment="positive")
        self.tracker.track(MetricType.QUERY, sentiment="positive")
        self.tracker.track(MetricType.QUERY, sentiment="negative")

        breakdown = self.tracker.get_sentiment_breakdown()
        assert "positive" in breakdown
        assert breakdown["positive"] == 2

    def test_hourly_distribution(self):
        """Test getting hourly distribution."""
        for _ in range(5):
            self.tracker.track(MetricType.QUERY)

        hourly = self.tracker.get_hourly_distribution()
        assert len(hourly) == 24  # All hours
        total = sum(h["count"] for h in hourly)
        assert total == 5

    def test_percentiles(self):
        """Test getting latency percentiles."""
        for i in range(100):
            self.tracker.track(
                MetricType.QUERY,
                latency_ms=float(i)
            )

        percentiles = self.tracker.get_percentiles("latency")
        assert "p50" in percentiles
        assert "p90" in percentiles
        assert percentiles["p50"] < percentiles["p90"]

    def test_recent_errors(self):
        """Test getting recent errors."""
        self.tracker.track(MetricType.ERROR, intent="error1", error_message="Test error 1")
        self.tracker.track(MetricType.ERROR, intent="error2", error_message="Test error 2")

        errors = self.tracker.get_recent_errors(limit=5)
        assert len(errors) == 2

    def test_export_events(self):
        """Test exporting events."""
        self.tracker.track(MetricType.QUERY, intent="test")
        self.tracker.track(MetricType.QUERY, intent="test2")

        exported = self.tracker.export_events()
        assert len(exported) == 2
        assert all("timestamp" in e for e in exported)

    def test_reset(self):
        """Test resetting tracker."""
        self.tracker.track(MetricType.QUERY)
        self.tracker.track(MetricType.QUERY)

        self.tracker.reset()

        summary = self.tracker.get_summary()
        assert summary["total_queries"] == 0
        assert summary["events_in_memory"] == 0

    def test_cost_tracking(self):
        """Test cost tracking."""
        self.tracker.track(MetricType.QUERY, cost_usd=0.001)
        self.tracker.track(MetricType.QUERY, cost_usd=0.002)
        self.tracker.track(MetricType.QUERY, cost_usd=0.003)

        summary = self.tracker.get_summary()
        assert summary["total_cost_usd"] == pytest.approx(0.006, rel=0.01)

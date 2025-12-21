"""
Tests for FastAPI endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import os

# Set test environment
os.environ["ANTHROPIC_API_KEY"] = "test-key"
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

from app.main import app
from app.core.router import RoutingResult, RoutingStatus
from datetime import datetime


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check(self, client):
        """Test health check returns status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data

    def test_root_endpoint(self, client):
        """Test root endpoint returns API info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "docs" in data


class TestChatEndpoint:
    """Tests for chat endpoint."""

    @patch("app.api.routes.get_chat_router")
    def test_chat_simple_query(self, mock_router, client):
        """Test simple chat query."""
        # Mock the router
        mock_instance = MagicMock()
        mock_instance.route.return_value = RoutingResult(
            request_id="test123",
            timestamp=datetime.utcnow(),
            query="How do I activate my card?",
            detected_intent="activate_card",
            intent_confidence=0.95,
            status=RoutingStatus.SUCCESS,
            response="To activate your card...",
            follow_up_questions=["Would you like help?"],
            model_used="claude-haiku-4-20250514",
            latency_ms=100.0,
            cost_usd=0.0001,
            sentiment="neutral",
            urgency_score=0.3
        )
        mock_router.return_value = mock_instance

        response = client.post(
            "/chat",
            json={"query": "How do I activate my card?"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["intent"] == "activate_card"
        assert data["confidence"] == 0.95
        assert "response" in data

    @patch("app.api.routes.get_chat_router")
    def test_chat_with_context(self, mock_router, client):
        """Test chat with user context."""
        mock_instance = MagicMock()
        mock_instance.route.return_value = RoutingResult(
            request_id="test456",
            timestamp=datetime.utcnow(),
            query="Check my balance",
            detected_intent="check_balance",
            intent_confidence=0.9,
            status=RoutingStatus.SUCCESS,
            response="Your balance is...",
            model_used="claude-haiku-4-20250514",
            latency_ms=150.0,
            cost_usd=0.0001,
            sentiment="neutral",
            urgency_score=0.2
        )
        mock_router.return_value = mock_instance

        response = client.post(
            "/chat",
            json={
                "query": "Check my balance",
                "user_id": "user123",
                "context": {"account_type": "savings"}
            }
        )

        assert response.status_code == 200

    def test_chat_empty_query(self, client):
        """Test chat with empty query returns error."""
        response = client.post(
            "/chat",
            json={"query": ""}
        )
        assert response.status_code == 422  # Validation error

    @patch("app.api.routes.get_chat_router")
    def test_chat_simple_endpoint(self, mock_router, client):
        """Test simple chat endpoint."""
        mock_instance = MagicMock()
        mock_instance.route_simple.return_value = "activate_card"
        mock_router.return_value = mock_instance

        response = client.post("/chat/simple?query=activate my card")
        assert response.status_code == 200
        data = response.json()
        assert "intent" in data


class TestIntentsEndpoint:
    """Tests for intents endpoint."""

    def test_list_intents(self, client):
        """Test listing all intents."""
        response = client.get("/intents")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_get_specific_intent(self, client):
        """Test getting specific intent."""
        response = client.get("/intents/activate_card")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "activate_card"

    def test_get_nonexistent_intent(self, client):
        """Test getting non-existent intent returns 404."""
        response = client.get("/intents/nonexistent")
        assert response.status_code == 404

    def test_create_intent(self, client):
        """Test creating a new intent."""
        new_intent = {
            "id": "test_new_intent",
            "name": "Test New Intent",
            "category": "support",
            "description": "A test intent",
            "response_template": "Test response template",
            "matches_when": "Test condition",
            "does_not_match_when": "Not test",
            "key_signals": ["test"],
            "hinglish_variants": ["test karo"],
            "priority": 5,
            "requires_human": False
        }

        response = client.post("/intents", json=new_intent)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test_new_intent"

    def test_delete_intent(self, client):
        """Test deleting an intent."""
        # First create one to delete
        new_intent = {
            "id": "to_delete",
            "name": "To Delete",
            "category": "support",
            "description": "Will be deleted",
            "response_template": "Delete me",
            "priority": 5
        }
        client.post("/intents", json=new_intent)

        # Now delete it
        response = client.delete("/intents/to_delete")
        assert response.status_code == 200


class TestAnalyticsEndpoint:
    """Tests for analytics endpoints."""

    def test_get_usage_stats(self, client):
        """Test getting LLM usage stats."""
        response = client.get("/analytics/usage")
        assert response.status_code == 200
        data = response.json()
        assert "total_input_tokens" in data
        assert "total_cost_usd" in data


class TestFeedbackEndpoint:
    """Tests for feedback endpoint."""

    def test_submit_feedback(self, client):
        """Test submitting feedback."""
        feedback = {
            "request_id": "test123",
            "rating": 5,
            "was_helpful": True,
            "comment": "Great response!"
        }
        response = client.post("/feedback", json=feedback)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_submit_feedback_invalid_rating(self, client):
        """Test feedback with invalid rating."""
        feedback = {
            "request_id": "test123",
            "rating": 10,  # Invalid - should be 1-5
            "was_helpful": True
        }
        response = client.post("/feedback", json=feedback)
        assert response.status_code == 422

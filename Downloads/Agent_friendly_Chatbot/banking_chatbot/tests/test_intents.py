"""
Tests for Intent Management.
"""
import pytest
from app.core.intents import IntentManager, Intent, IntentCategory


class TestIntentManager:
    """Tests for IntentManager class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = IntentManager()

    def test_default_intents_loaded(self):
        """Test that default intents are loaded on initialization."""
        intents = self.manager.get_all_intents()
        assert len(intents) > 0
        assert any(i.id == "activate_card" for i in intents)
        assert any(i.id == "block_card" for i in intents)

    def test_get_intent_by_id(self):
        """Test getting intent by ID."""
        intent = self.manager.get_intent("activate_card")
        assert intent is not None
        assert intent.id == "activate_card"
        assert intent.name == "Activate Card"

    def test_get_nonexistent_intent(self):
        """Test getting non-existent intent returns None."""
        intent = self.manager.get_intent("nonexistent_intent")
        assert intent is None

    def test_get_intents_by_category(self):
        """Test filtering intents by category."""
        card_intents = self.manager.get_intents_by_category(IntentCategory.CARD_MANAGEMENT)
        assert len(card_intents) > 0
        assert all(i.category == IntentCategory.CARD_MANAGEMENT for i in card_intents)

    def test_add_intent(self):
        """Test adding a new intent."""
        new_intent = Intent(
            id="test_intent",
            name="Test Intent",
            category=IntentCategory.SUPPORT,
            description="A test intent",
            response_template="This is a test response",
            matches_when="Test condition",
            does_not_match_when="Not a test",
            key_signals=["test", "testing"],
            hinglish_variants=["test karo"]
        )
        self.manager.add_intent(new_intent)
        retrieved = self.manager.get_intent("test_intent")
        assert retrieved is not None
        assert retrieved.name == "Test Intent"

    def test_remove_intent(self):
        """Test removing an intent."""
        result = self.manager.remove_intent("activate_card")
        assert result is True
        assert self.manager.get_intent("activate_card") is None

    def test_remove_nonexistent_intent(self):
        """Test removing non-existent intent returns False."""
        result = self.manager.remove_intent("nonexistent")
        assert result is False

    def test_get_routing_rules_text(self):
        """Test generating routing rules text."""
        rules = self.manager.get_routing_rules_text()
        assert isinstance(rules, str)
        assert "INTENT:" in rules
        assert "Matches when:" in rules
        assert "activate_card" in rules

    def test_get_intent_names(self):
        """Test getting list of intent names."""
        names = self.manager.get_intent_names()
        assert isinstance(names, list)
        assert "activate_card" in names
        assert "block_card" in names

    def test_export_to_dict(self):
        """Test exporting intents to dictionary."""
        data = self.manager.export_to_dict()
        assert isinstance(data, dict)
        assert "activate_card" in data
        assert "response_template" in data["activate_card"]

    def test_import_from_dict(self):
        """Test importing intents from dictionary."""
        data = {
            "imported_intent": {
                "id": "imported_intent",
                "name": "Imported Intent",
                "category": "support",
                "description": "Imported",
                "response_template": "Imported response",
                "matches_when": "When imported",
                "does_not_match_when": "Not imported"
            }
        }
        self.manager.import_from_dict(data)
        intent = self.manager.get_intent("imported_intent")
        assert intent is not None
        assert intent.name == "Imported Intent"


class TestIntent:
    """Tests for Intent model."""

    def test_intent_creation(self):
        """Test creating an intent."""
        intent = Intent(
            id="test",
            name="Test",
            category=IntentCategory.SUPPORT,
            description="Test description",
            response_template="Test response",
            matches_when="Test matches",
            does_not_match_when="Test not matches"
        )
        assert intent.id == "test"
        assert intent.priority == 5  # default
        assert intent.requires_human is False  # default

    def test_intent_with_all_fields(self):
        """Test intent with all optional fields."""
        intent = Intent(
            id="full_test",
            name="Full Test",
            category=IntentCategory.SECURITY,
            description="Full description",
            response_template="Full response",
            follow_up_questions=["Q1", "Q2"],
            matches_when="Full matches",
            does_not_match_when="Full not matches",
            key_signals=["signal1", "signal2"],
            hinglish_variants=["variant1"],
            requires_human=True,
            priority=10,
            example_queries=["example1"],
            related_intents=["related1"]
        )
        assert len(intent.follow_up_questions) == 2
        assert len(intent.key_signals) == 2
        assert intent.requires_human is True
        assert intent.priority == 10

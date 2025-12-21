"""
Pytest configuration and fixtures.
"""
import pytest
import os
import sys

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set test environment variables
os.environ["ANTHROPIC_API_KEY"] = "test-api-key"
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["ENVIRONMENT"] = "development"
os.environ["DEBUG"] = "true"


@pytest.fixture(scope="session")
def api_key():
    """Provide test API key."""
    return "test-api-key"


@pytest.fixture
def sample_queries():
    """Provide sample test queries."""
    return [
        {"query": "How do I activate my card?", "expected_intent": "activate_card"},
        {"query": "Block my card please", "expected_intent": "block_card"},
        {"query": "Card not working", "expected_intent": "card_not_working"},
        {"query": "Where is my card?", "expected_intent": "card_delivery_status"},
        {"query": "What's my balance?", "expected_intent": "check_balance"},
        {"query": "Transfer money", "expected_intent": "transfer_money"},
        {"query": "I got scammed!", "expected_intent": "report_fraud"},
    ]


@pytest.fixture
def sample_hinglish_queries():
    """Provide sample Hinglish test queries."""
    return [
        {"query": "card activate karna hai", "expected_intent": "activate_card"},
        {"query": "card block karo", "expected_intent": "block_card"},
        {"query": "card kaam nahi kar raha", "expected_intent": "card_not_working"},
        {"query": "mera balance kitna hai", "expected_intent": "check_balance"},
        {"query": "paisa bhejana hai", "expected_intent": "transfer_money"},
    ]


@pytest.fixture
def sample_messy_queries():
    """Provide messy/challenging test queries."""
    return [
        {"query": "waah kya service hai card 3 din se kaam nhi kr rha", "expected_intent": "card_not_working"},
        {"query": "HELLO!!! MY MONEY IS STUCK!!!", "expected_intent": "pending_transfer"},
        {"query": "abe oye card block krdo jaldi", "expected_intent": "block_card"},
        {"query": "bhai mera balance check karna hai plzzz", "expected_intent": "check_balance"},
    ]

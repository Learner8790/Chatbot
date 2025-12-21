#!/usr/bin/env python3
"""
Quick test script to verify the chatbot is working.
Run this after setting up the environment.
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check for API key
api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    print("ERROR: ANTHROPIC_API_KEY not set!")
    print("Please create a .env file with your API key or export it.")
    sys.exit(1)

print("=" * 60)
print("Banking Chatbot - Quick Test")
print("=" * 60)
print()

# Import after env check
from app.core import ChatRouter, IntentManager

# Test 1: Intent Manager
print("[1] Testing Intent Manager...")
manager = IntentManager()
intents = manager.get_all_intents()
print(f"    Loaded {len(intents)} intents")
print(f"    Categories: {set(i.category for i in intents)}")
print("    OK")
print()

# Test 2: Chat Router (no API call)
print("[2] Testing Chat Router initialization...")
try:
    router = ChatRouter(api_key=api_key)
    print(f"    Router created with {len(router.get_all_intents())} intents")
    print("    OK")
except Exception as e:
    print(f"    FAILED: {e}")
    sys.exit(1)
print()

# Test 3: Live Routing (makes API call)
print("[3] Testing Live Routing (API call)...")
test_queries = [
    "How do I activate my card?",
    "card activate karna hai",
    "BLOCK MY CARD NOW!!!",
]

for query in test_queries:
    try:
        result = router.route(query, analyze_sentiment=True)
        print(f"    Query: '{query[:40]}...'")
        print(f"    -> Intent: {result.detected_intent}")
        print(f"    -> Confidence: {result.intent_confidence:.1%}")
        print(f"    -> Sentiment: {result.sentiment}")
        print()
    except Exception as e:
        print(f"    FAILED: {e}")
        sys.exit(1)

print("=" * 60)
print("All tests passed!")
print("=" * 60)
print()
print("Next steps:")
print("  1. Run the API: python run.py")
print("  2. Open docs: http://localhost:8000/docs")
print("  3. Run dashboard: python run_dashboard.py")
print()

# Print usage stats
stats = router.get_usage_stats()
print(f"API Usage: {stats['total_input_tokens']} input tokens, "
      f"${stats['total_cost_usd']:.4f} cost")

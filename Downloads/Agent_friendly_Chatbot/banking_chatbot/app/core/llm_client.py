"""
LLM Client for Claude API integration.
Handles routing, response generation, and fallback logic.
"""
import anthropic
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import re
import logging

logger = logging.getLogger(__name__)


class ModelTier(str, Enum):
    """Available model tiers."""
    FAST = "haiku"  # Fast, cheap - for simple routing
    BALANCED = "sonnet"  # Good balance - default
    PREMIUM = "opus"  # Best quality - complex cases


@dataclass
class LLMResponse:
    """Response from LLM."""
    content: str
    model: str
    input_tokens: int
    output_tokens: int
    cost: float
    latency_ms: float = 0.0


@dataclass
class RoutingDecision:
    """Routing decision from LLM."""
    intent_id: str
    confidence: float
    reasoning: str
    requires_clarification: bool = False
    clarification_question: Optional[str] = None


class LLMClient:
    """Client for interacting with Claude API."""

    # Pricing per 1M tokens (as of 2024)
    PRICING = {
        "claude-haiku-4-20250514": {"input": 0.25, "output": 1.25},
        "claude-sonnet-4-20250514": {"input": 3.0, "output": 15.0},
        "claude-opus-4-20250514": {"input": 15.0, "output": 75.0},
    }

    MODEL_MAP = {
        ModelTier.FAST: "claude-haiku-4-20250514",
        ModelTier.BALANCED: "claude-sonnet-4-20250514",
        ModelTier.PREMIUM: "claude-opus-4-20250514",
    }

    def __init__(self, api_key: str):
        """Initialize LLM client."""
        self.client = anthropic.Anthropic(api_key=api_key)
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._total_cost = 0.0

    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for API call."""
        if model not in self.PRICING:
            return 0.0
        pricing = self.PRICING[model]
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        return input_cost + output_cost

    def route_query(
        self,
        query: str,
        intent_names: List[str],
        routing_rules: str,
        model_tier: ModelTier = ModelTier.FAST,
        include_confidence: bool = True
    ) -> RoutingDecision:
        """
        Route a customer query to the appropriate intent.

        Args:
            query: Customer's query text
            intent_names: List of valid intent IDs
            routing_rules: Text description of routing rules
            model_tier: Which model to use
            include_confidence: Whether to ask for confidence score

        Returns:
            RoutingDecision with intent and confidence
        """
        model = self.MODEL_MAP[model_tier]

        # Build the prompt - keep it simple for better accuracy
        if include_confidence:
            prompt = f"""You are a banking chatbot router. Route the customer query to the correct intent.

VALID INTENTS: {', '.join(intent_names)}

ROUTING RULES:
{routing_rules}

CUSTOMER QUERY: "{query}"

Respond with JSON only:
{{"intent": "intent_id_here", "confidence": 0.0-1.0, "reasoning": "brief reason"}}

If no intent matches well, use "unknown" with low confidence."""
        else:
            prompt = f"""You are a banking chatbot router. Route the customer query to the correct intent.

ROUTING RULES:
{routing_rules}

CUSTOMER QUERY: "{query}"

Reply with ONLY the intent name. No explanation."""

        try:
            import time
            start = time.time()

            response = self.client.messages.create(
                model=model,
                max_tokens=150,
                temperature=0,
                messages=[{"role": "user", "content": prompt}]
            )

            latency = (time.time() - start) * 1000

            content = response.content[0].text.strip()

            # Track usage
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            cost = self._calculate_cost(model, input_tokens, output_tokens)

            self._total_input_tokens += input_tokens
            self._total_output_tokens += output_tokens
            self._total_cost += cost

            # Parse response
            if include_confidence:
                try:
                    # Try to extract JSON
                    json_match = re.search(r'\{[^}]+\}', content)
                    if json_match:
                        data = json.loads(json_match.group())
                        return RoutingDecision(
                            intent_id=data.get("intent", "unknown"),
                            confidence=float(data.get("confidence", 0.5)),
                            reasoning=data.get("reasoning", "")
                        )
                except (json.JSONDecodeError, ValueError):
                    pass

            # Fallback: extract intent name directly
            intent_id = content.lower().strip().replace('"', '').replace("'", "")
            # Try to match with valid intents
            for valid_intent in intent_names:
                if valid_intent.lower() in intent_id or intent_id in valid_intent.lower():
                    return RoutingDecision(
                        intent_id=valid_intent,
                        confidence=0.7,
                        reasoning="Direct match"
                    )

            return RoutingDecision(
                intent_id=content,
                confidence=0.5,
                reasoning="Extracted from response"
            )

        except Exception as e:
            logger.error(f"Routing error: {e}")
            return RoutingDecision(
                intent_id="unknown",
                confidence=0.0,
                reasoning=f"Error: {str(e)}"
            )

    def generate_response(
        self,
        query: str,
        intent_id: str,
        response_template: str,
        context: Optional[Dict[str, Any]] = None,
        model_tier: ModelTier = ModelTier.BALANCED
    ) -> LLMResponse:
        """
        Generate a personalized response for the user.

        Args:
            query: Original customer query
            intent_id: Detected intent
            response_template: Template for this intent
            context: User/account context data
            model_tier: Which model to use

        Returns:
            LLMResponse with generated content
        """
        model = self.MODEL_MAP[model_tier]
        context = context or {}

        prompt = f"""You are a helpful banking assistant. Generate a natural, personalized response.

CUSTOMER QUERY: "{query}"
DETECTED INTENT: {intent_id}

RESPONSE TEMPLATE:
{response_template}

CONTEXT DATA:
{json.dumps(context, indent=2)}

Instructions:
1. Use the template as a base but make it conversational
2. Fill in placeholders with context data where available
3. Keep tone professional but friendly
4. If data is missing, ask the user or provide general guidance
5. Keep response concise (2-4 short paragraphs max)

Generate the response:"""

        try:
            import time
            start = time.time()

            response = self.client.messages.create(
                model=model,
                max_tokens=500,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )

            latency = (time.time() - start) * 1000

            content = response.content[0].text.strip()
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            cost = self._calculate_cost(model, input_tokens, output_tokens)

            self._total_input_tokens += input_tokens
            self._total_output_tokens += output_tokens
            self._total_cost += cost

            return LLMResponse(
                content=content,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost=cost,
                latency_ms=latency
            )

        except Exception as e:
            logger.error(f"Response generation error: {e}")
            return LLMResponse(
                content=response_template,  # Fallback to template
                model=model,
                input_tokens=0,
                output_tokens=0,
                cost=0.0
            )

    def analyze_sentiment(
        self,
        query: str,
        model_tier: ModelTier = ModelTier.FAST
    ) -> Tuple[str, float]:
        """
        Analyze sentiment and urgency of customer query.

        Returns:
            Tuple of (sentiment, urgency_score)
            sentiment: positive, neutral, negative, frustrated
            urgency_score: 0.0 to 1.0
        """
        model = self.MODEL_MAP[model_tier]

        prompt = f"""Analyze this customer message for sentiment and urgency.

MESSAGE: "{query}"

Respond with JSON only:
{{"sentiment": "positive|neutral|negative|frustrated", "urgency": 0.0-1.0}}

Consider:
- ALL CAPS = higher urgency
- Multiple punctuation (!!! ???) = frustration
- Words like "urgent", "immediately" = high urgency
- Threats to leave = frustrated + high urgency"""

        try:
            response = self.client.messages.create(
                model=model,
                max_tokens=50,
                temperature=0,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text.strip()

            # Track usage
            self._total_input_tokens += response.usage.input_tokens
            self._total_output_tokens += response.usage.output_tokens
            self._total_cost += self._calculate_cost(
                model, response.usage.input_tokens, response.usage.output_tokens
            )

            try:
                json_match = re.search(r'\{[^}]+\}', content)
                if json_match:
                    data = json.loads(json_match.group())
                    return data.get("sentiment", "neutral"), float(data.get("urgency", 0.5))
            except:
                pass

            return "neutral", 0.5

        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")
            return "neutral", 0.5

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get cumulative usage statistics."""
        return {
            "total_input_tokens": self._total_input_tokens,
            "total_output_tokens": self._total_output_tokens,
            "total_cost_usd": round(self._total_cost, 4)
        }

    def reset_usage_stats(self) -> None:
        """Reset usage statistics."""
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._total_cost = 0.0

"""
Banking Chatbot - Simple Chat Interface
A clean, minimalistic chat dashboard.
"""
import streamlit as st
import anthropic
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Banking Assistant",
    page_icon=None,
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for minimalistic white theme
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background-color: #ffffff;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Chat container */
    .chat-container {
        max-width: 700px;
        margin: 0 auto;
        padding: 20px;
    }

    /* Header styling */
    .main-header {
        font-size: 24px;
        font-weight: 600;
        color: #1a1a1a;
        text-align: center;
        padding: 30px 0 10px 0;
        border-bottom: 1px solid #e5e5e5;
        margin-bottom: 30px;
    }

    .sub-header {
        font-size: 14px;
        color: #666666;
        text-align: center;
        margin-bottom: 30px;
    }

    /* Message styling */
    .user-message {
        background-color: #f5f5f5;
        padding: 15px 20px;
        border-radius: 8px;
        margin: 10px 0;
        color: #1a1a1a;
    }

    .assistant-message {
        background-color: #ffffff;
        padding: 15px 20px;
        border-radius: 8px;
        margin: 10px 0;
        border: 1px solid #e5e5e5;
        color: #1a1a1a;
    }

    .message-label {
        font-size: 11px;
        color: #999999;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 5px;
    }

    /* Input styling */
    .stTextInput > div > div > input {
        border: 1px solid #e5e5e5;
        border-radius: 8px;
        padding: 12px 15px;
        font-size: 15px;
    }

    .stTextInput > div > div > input:focus {
        border-color: #1a1a1a;
        box-shadow: none;
    }

    /* Button styling */
    .stButton > button {
        background-color: #1a1a1a;
        color: #ffffff;
        border: none;
        border-radius: 8px;
        padding: 10px 30px;
        font-size: 14px;
        font-weight: 500;
    }

    .stButton > button:hover {
        background-color: #333333;
    }

    /* Metadata styling */
    .metadata {
        font-size: 11px;
        color: #999999;
        margin-top: 8px;
    }

    /* Divider */
    .divider {
        border-top: 1px solid #e5e5e5;
        margin: 20px 0;
    }
</style>
""", unsafe_allow_html=True)

# Banking intents and routing rules
INTENTS = {
    "activate_card": {
        "matches": "activate, start using, new card received, chalu karo",
        "response": "To activate your card:\n\n1. Open Mobile Banking app\n2. Go to Cards > Manage Cards\n3. Select your new card\n4. Enter CVV and verify with OTP\n\nYour card will be active within 5 minutes."
    },
    "block_card": {
        "matches": "block, lost, stolen, freeze, band karo",
        "response": "I'm blocking your card immediately for security.\n\nNext steps:\n1. If stolen, file a police report\n2. Order a replacement card (3-5 days)\n3. Review recent transactions\n\nWould you like to order a replacement?"
    },
    "card_not_working": {
        "matches": "not working, declined, rejected, kaam nahi",
        "response": "Let me help troubleshoot:\n\n1. Is the card activated?\n2. Is the PIN correct? (3 wrong attempts = block)\n3. Sufficient balance?\n4. International usage enabled?\n\nWhich might be the issue?"
    },
    "check_balance": {
        "matches": "balance, kitna paisa, how much money",
        "response": "To check your balance:\n\n1. Mobile Banking: Home screen shows balance\n2. SMS: Send BAL to 56161\n3. Missed call: 1800-XXX-XXXX\n4. ATM: Balance inquiry option\n\nWould you like a mini statement?"
    },
    "transfer_money": {
        "matches": "transfer, send money, bhejana, payment",
        "response": "To transfer money:\n\n1. Mobile Banking > Transfer > Send Money\n2. Select beneficiary or add new\n3. Enter amount\n4. Confirm with OTP\n\nLimits: IMPS up to 5L (instant), NEFT no limit."
    },
    "pending_transfer": {
        "matches": "pending, stuck, not received, nahi gaya",
        "response": "I'll check your pending transfer.\n\nUsually resolves within:\n- IMPS: Instant to 30 mins\n- NEFT: 2-4 hours\n- RTGS: 30 mins\n\nIf over 24 hours, please share transaction ID for investigation."
    },
    "report_fraud": {
        "matches": "fraud, scam, unauthorized, chori, stolen money",
        "response": "I'm sorry to hear this. Taking immediate action:\n\n1. Your card is being blocked\n2. Dispute registered\n3. Fraud team notified\n\nImportant:\n- Don't share OTP with anyone\n- File complaint at cybercrime.gov.in\n\nOur team will call within 2 hours."
    },
    "speak_to_human": {
        "matches": "human, agent, person, executive, manager",
        "response": "Connecting you to a human agent.\n\nEstimated wait: 2-3 minutes\n\nAlternatives:\n- Call: 1800-XXX-XXXX (24x7)\n- Email: support@bank.com\n- Branch visit"
    }
}


def get_routing_rules():
    """Generate routing rules for LLM."""
    rules = []
    for intent_id, data in INTENTS.items():
        rules.append(f"- {intent_id}: {data['matches']}")
    return "\n".join(rules)


def route_and_respond(query: str, client: anthropic.Anthropic) -> dict:
    """Route query and generate response."""

    # Step 1: Route to intent
    routing_prompt = f"""You are a banking chatbot router. Route this query to the correct intent.

INTENTS:
{get_routing_rules()}

QUERY: "{query}"

Reply with ONLY the intent name (like "activate_card" or "check_balance").
If no good match, reply "general"."""

    routing_response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=50,
        temperature=0,
        messages=[{"role": "user", "content": routing_prompt}]
    )

    intent = routing_response.content[0].text.strip().lower().replace('"', '')

    # Step 2: Get response template or generate custom
    if intent in INTENTS:
        base_response = INTENTS[intent]["response"]
    else:
        base_response = None
        intent = "general"

    # Step 3: Generate personalized response
    if base_response:
        response_prompt = f"""You are a helpful banking assistant. Respond to this query naturally.

QUERY: "{query}"
INTENT: {intent}

BASE RESPONSE:
{base_response}

Make it conversational and helpful. Keep it concise. No emojis."""
    else:
        response_prompt = f"""You are a helpful banking assistant. Respond to this query.

QUERY: "{query}"

Provide helpful banking guidance. Keep it concise and professional. No emojis."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=300,
        temperature=0.3,
        messages=[{"role": "user", "content": response_prompt}]
    )

    return {
        "intent": intent,
        "response": response.content[0].text.strip(),
        "tokens": routing_response.usage.input_tokens + routing_response.usage.output_tokens +
                  response.usage.input_tokens + response.usage.output_tokens
    }


def main():
    # Header
    st.markdown('<div class="main-header">Banking Assistant</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">How can I help you today?</div>', unsafe_allow_html=True)

    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "client" not in st.session_state:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            st.session_state.client = anthropic.Anthropic(api_key=api_key)
        else:
            st.session_state.client = None

    # Check for API key
    if not st.session_state.client:
        st.markdown("""
        <div style="text-align: center; padding: 40px; color: #666;">
            <p>API key not configured.</p>
            <p style="font-size: 13px;">Add ANTHROPIC_API_KEY to your .env file</p>
        </div>
        """, unsafe_allow_html=True)

        # Allow manual entry
        api_key = st.text_input("Or enter API key:", type="password")
        if api_key:
            st.session_state.client = anthropic.Anthropic(api_key=api_key)
            st.rerun()
        return

    # Display chat history
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f'''
            <div class="user-message">
                <div class="message-label">You</div>
                {msg["content"]}
            </div>
            ''', unsafe_allow_html=True)
        else:
            st.markdown(f'''
            <div class="assistant-message">
                <div class="message-label">Assistant</div>
                {msg["content"]}
                <div class="metadata">Intent: {msg.get("intent", "general")}</div>
            </div>
            ''', unsafe_allow_html=True)

    # Chat input
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    query = st.text_input(
        "Message",
        placeholder="Type your question here...",
        label_visibility="collapsed",
        key="chat_input"
    )

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        send_clicked = st.button("Send", use_container_width=True)

    if send_clicked and query:
        # Add user message
        st.session_state.messages.append({
            "role": "user",
            "content": query
        })

        # Get response
        with st.spinner(""):
            try:
                result = route_and_respond(query, st.session_state.client)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": result["response"],
                    "intent": result["intent"]
                })
            except Exception as e:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"Sorry, I encountered an error. Please try again.",
                    "intent": "error"
                })

        st.rerun()

    # Clear chat button
    if st.session_state.messages:
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("Clear Chat", use_container_width=True):
                st.session_state.messages = []
                st.rerun()

    # Sample queries
    if not st.session_state.messages:
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align: center; color: #999; font-size: 13px; margin-top: 20px;">
            Try asking:
        </div>
        """, unsafe_allow_html=True)

        samples = [
            "How do I activate my new card?",
            "My card is not working",
            "I want to transfer money",
            "Check my balance"
        ]

        cols = st.columns(2)
        for i, sample in enumerate(samples):
            with cols[i % 2]:
                if st.button(sample, key=f"sample_{i}", use_container_width=True):
                    st.session_state.messages.append({"role": "user", "content": sample})
                    with st.spinner(""):
                        result = route_and_respond(sample, st.session_state.client)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": result["response"],
                            "intent": result["intent"]
                        })
                    st.rerun()


if __name__ == "__main__":
    main()

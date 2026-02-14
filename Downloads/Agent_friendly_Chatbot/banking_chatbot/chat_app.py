"""
Banking Chatbot - Simple Chat Interface
A clean, minimalistic chat dashboard with conversation memory.
"""
import streamlit as st
from google import genai
from google.genai import types
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
    .stApp {
        background-color: #ffffff;
    }
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    header {visibility: hidden !important;}
    .stDeployButton {display: none !important;}
    .stAppDeployButton {display: none !important;}
    [data-testid="stDecoration"] {display: none !important;}
    [data-testid="stStatusWidget"] {display: none !important;}
    [data-testid="manage-app-button"] {display: none !important;}
    [data-testid="stToolbar"] {display: none !important;}
    [data-testid="stBottom"] {display: none !important;}
    div[class*="viewerBadge"] {display: none !important;}
    div[class*="_profileContainer"] {display: none !important;}
    div[class*="_container_"] > a[href*="streamlit.io"] {display: none !important;}
    iframe[title="streamlit_badge"] {display: none !important;}
    div:has(> iframe[title="streamlit_badge"]) {display: none !important;}
    div[class*="stAppViewBlockContainer"] ~ div[style*="position: fixed"][style*="bottom"] {display: none !important;}
    div[style*="position: fixed"][style*="bottom: 0"][style*="right: 0"] {display: none !important;}

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
    .metadata {
        font-size: 11px;
        color: #999999;
        margin-top: 8px;
    }
    .divider {
        border-top: 1px solid #e5e5e5;
        margin: 20px 0;
    }
</style>
""", unsafe_allow_html=True)


SYSTEM_PROMPT = """You are a helpful banking assistant for an Indian bank. You help customers with their banking queries.

Your capabilities:
- Card issues: activation, blocking, not working, delivery status
- Account: balance check, mini statement, update details
- Transfers: send money, pending transfers, add beneficiary
- Payments: credit card bill, UPI issues
- Security: report fraud, change PIN, forgot PIN
- Support: complaints, feedback, branch locator

Guidelines:
1. Be conversational and helpful
2. Remember the full conversation context - do not repeat questions already asked
3. If user says they already checked something, acknowledge it and move to next steps
4. When troubleshooting fails, offer to escalate to human agent or suggest visiting branch
5. Keep responses concise - 2-3 short paragraphs max
6. No emojis
7. If user is frustrated, acknowledge their frustration and be empathetic
8. After 2-3 troubleshooting attempts, offer concrete next steps like:
   - Raising a complaint ticket
   - Connecting to human agent
   - Visiting nearest branch
   - Calling customer care

For card not working issues after basic checks fail:
- Offer to raise a service request
- Suggest card replacement if needed
- Provide customer care number: 1800-XXX-XXXX"""


def get_response(messages: list, client: genai.Client) -> str:
    """Get response from Gemini with full conversation history."""

    # Build conversation for Gemini (uses "model" role, not "assistant")
    contents = []
    for msg in messages:
        role = "user" if msg["role"] == "user" else "model"
        contents.append(
            types.Content(
                role=role,
                parts=[types.Part.from_text(text=msg["content"])]
            )
        )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            max_output_tokens=400,
            temperature=0.3,
        ),
    )

    return response.text.strip()


def detect_intent(query: str, conversation: list) -> str:
    """Simple intent detection based on keywords."""
    query_lower = query.lower()

    # Check keywords
    if any(w in query_lower for w in ["activate", "activation", "chalu", "start using"]):
        return "activate_card"
    if any(w in query_lower for w in ["block", "lost", "stolen", "freeze", "band karo"]):
        return "block_card"
    if any(w in query_lower for w in ["not working", "declined", "reject", "useless", "kaam nahi"]):
        return "card_not_working"
    if any(w in query_lower for w in ["balance", "kitna paisa", "how much"]):
        return "check_balance"
    if any(w in query_lower for w in ["transfer", "send money", "bhejana"]):
        return "transfer_money"
    if any(w in query_lower for w in ["pending", "stuck", "nahi gaya"]):
        return "pending_transfer"
    if any(w in query_lower for w in ["fraud", "scam", "chori", "unauthorized"]):
        return "report_fraud"
    if any(w in query_lower for w in ["human", "agent", "person", "manager"]):
        return "speak_to_human"
    if any(w in query_lower for w in ["complaint", "shikayat", "escalate"]):
        return "complaint"

    # Check conversation context for ongoing issues
    if conversation:
        last_intents = [m.get("intent", "") for m in conversation[-4:] if m["role"] == "assistant"]
        if last_intents and last_intents[-1]:
            return last_intents[-1]  # Continue with same intent

    return "general"


def main():
    st.markdown('<div class="main-header">Banking Assistant</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">How can I help you today?</div>', unsafe_allow_html=True)

    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "client" not in st.session_state:
        api_key = os.getenv("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY", None)
        if api_key:
            st.session_state.client = genai.Client(api_key=api_key)
        else:
            st.session_state.client = None

    # Check for API key
    if not st.session_state.client:
        st.markdown("""
        <div style="text-align: center; padding: 40px; color: #666;">
            <p>API key not configured.</p>
            <p style="font-size: 13px;">Add GOOGLE_API_KEY to your .env file or Streamlit secrets</p>
        </div>
        """, unsafe_allow_html=True)
        api_key = st.text_input("Or enter Google Gemini API key:", type="password")
        if api_key:
            st.session_state.client = genai.Client(api_key=api_key)
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

        # Detect intent
        intent = detect_intent(query, st.session_state.messages)

        # Get response with full conversation history
        with st.spinner(""):
            try:
                response = get_response(st.session_state.messages, st.session_state.client)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response,
                    "intent": intent
                })
            except Exception as e:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"Sorry, I encountered an error: {str(e)}",
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
                    intent = detect_intent(sample, st.session_state.messages)
                    with st.spinner(""):
                        response = get_response(st.session_state.messages, st.session_state.client)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": response,
                            "intent": intent
                        })
                    st.rerun()


if __name__ == "__main__":
    main()

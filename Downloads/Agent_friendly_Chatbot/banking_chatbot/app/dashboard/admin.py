"""
Streamlit Admin Dashboard for Banking Chatbot.
Provides analytics, intent management, and escalation monitoring.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import httpx
import json

# Configuration
API_BASE_URL = "http://localhost:8000"

st.set_page_config(
    page_title="Banking Chatbot Admin",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============ Helper Functions ============

def api_call(endpoint: str, method: str = "GET", data: dict = None):
    """Make API call to backend."""
    try:
        with httpx.Client(timeout=30.0) as client:
            url = f"{API_BASE_URL}{endpoint}"
            if method == "GET":
                response = client.get(url)
            elif method == "POST":
                response = client.post(url, json=data)
            elif method == "DELETE":
                response = client.delete(url)
            else:
                return None

            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"API Error: {response.status_code} - {response.text}")
                return None
    except Exception as e:
        st.error(f"Connection error: {e}")
        return None


# ============ Sidebar ============

st.sidebar.title("🏦 Banking Chatbot")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Chat Test", "Intents", "Escalations", "Settings"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Quick Stats")

# Get health status
health = api_call("/health")
if health:
    status_color = "🟢" if health["status"] == "healthy" else "🟡"
    st.sidebar.markdown(f"{status_color} **Status**: {health['status']}")
    st.sidebar.markdown(f"**Version**: {health['version']}")


# ============ Dashboard Page ============

if page == "Dashboard":
    st.title("📊 Analytics Dashboard")

    # Time range selector
    col1, col2 = st.columns([1, 3])
    with col1:
        days = st.selectbox("Time Range", [7, 14, 30, 60, 90], index=0)

    # Get analytics
    summary = api_call(f"/analytics/summary?days={days}")
    intent_breakdown = api_call(f"/analytics/intents?days={days}")
    hourly = api_call("/analytics/hourly")

    if summary:
        # KPI Cards
        st.markdown("### Key Metrics")
        c1, c2, c3, c4, c5 = st.columns(5)

        with c1:
            st.metric("Total Queries", f"{summary['total_queries']:,}")
        with c2:
            st.metric("Avg Confidence", f"{summary['avg_confidence']:.1%}")
        with c3:
            st.metric("Avg Latency", f"{summary['avg_latency_ms']:.0f}ms")
        with c4:
            st.metric("Total Cost", f"${summary['total_cost_usd']:.2f}")
        with c5:
            st.metric("Escalation Rate", f"{summary['escalation_rate']:.1f}%")

        st.markdown("---")

        # Charts
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Intent Distribution")
            if intent_breakdown:
                df = pd.DataFrame(intent_breakdown)
                if not df.empty:
                    fig = px.pie(
                        df.head(10),
                        values="count",
                        names="intent",
                        title="Top 10 Intents"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No intent data available")

        with col2:
            st.markdown("### Hourly Distribution")
            if hourly:
                df = pd.DataFrame(hourly)
                fig = px.bar(
                    df,
                    x="hour",
                    y="count",
                    title="Queries by Hour (Today)",
                    labels={"hour": "Hour", "count": "Query Count"}
                )
                st.plotly_chart(fig, use_container_width=True)

        # Intent performance table
        st.markdown("### Intent Performance")
        if intent_breakdown:
            df = pd.DataFrame(intent_breakdown)
            if not df.empty:
                df["avg_confidence"] = df["avg_confidence"].apply(lambda x: f"{x:.1%}")
                st.dataframe(df, use_container_width=True)


# ============ Chat Test Page ============

elif page == "Chat Test":
    st.title("💬 Chat Test Console")

    st.markdown("""
    Test the chatbot with sample queries. This helps validate routing accuracy.
    """)

    # Input
    query = st.text_area(
        "Enter your query",
        placeholder="e.g., mera card kab aayega? or How do I activate my card?",
        height=100
    )

    col1, col2 = st.columns([1, 1])
    with col1:
        analyze_sentiment = st.checkbox("Analyze Sentiment", value=True)
    with col2:
        test_mode = st.checkbox("Test Mode (no DB writes)", value=True)

    if st.button("Send Query", type="primary"):
        if query:
            with st.spinner("Processing..."):
                response = api_call(
                    "/chat",
                    method="POST",
                    data={
                        "query": query,
                        "analyze_sentiment": analyze_sentiment
                    }
                )

            if response:
                st.markdown("---")

                # Response display
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown("### Response")
                    st.markdown(response.get("response", "No response"))

                    if response.get("follow_up_questions"):
                        st.markdown("**Follow-up Questions:**")
                        for q in response["follow_up_questions"]:
                            st.markdown(f"- {q}")

                with col2:
                    st.markdown("### Metadata")
                    st.json({
                        "Intent": response.get("intent"),
                        "Confidence": f"{response.get('confidence', 0):.1%}",
                        "Status": response.get("status"),
                        "Sentiment": response.get("metadata", {}).get("sentiment"),
                        "Urgency": f"{response.get('metadata', {}).get('urgency', 0):.1%}",
                        "Latency": f"{response.get('metadata', {}).get('latency_ms', 0):.0f}ms",
                        "Cost": f"${response.get('metadata', {}).get('cost_usd', 0):.6f}",
                        "Requires Human": response.get("requires_human")
                    })

                if response.get("requires_human"):
                    st.warning(f"⚠️ Escalation triggered: {response.get('escalation_reason')}")

    # Sample queries
    st.markdown("---")
    st.markdown("### Sample Queries")

    samples = [
        ("English Formal", "How do I activate my new debit card?"),
        ("Hinglish", "bhai mera card activate kaise karu?"),
        ("Frustrated", "HELLO!!! MY CARD IS NOT WORKING SINCE 3 DAYS!!!"),
        ("Sarcastic", "waah kya service hai, paisa bhi gaya aur card bhi nahi aaya"),
        ("Vague", "kuch gadbad hai card me"),
        ("Fraud", "someone took money from my account without permission"),
    ]

    cols = st.columns(3)
    for i, (label, sample_query) in enumerate(samples):
        with cols[i % 3]:
            if st.button(f"📝 {label}", key=f"sample_{i}"):
                st.session_state["query"] = sample_query
                st.rerun()


# ============ Intents Page ============

elif page == "Intents":
    st.title("🎯 Intent Management")

    tab1, tab2 = st.tabs(["View Intents", "Add Intent"])

    with tab1:
        intents = api_call("/intents")

        if intents:
            # Filter
            categories = list(set(i["category"] for i in intents))
            selected_category = st.selectbox(
                "Filter by Category",
                ["All"] + sorted(categories)
            )

            # Display intents
            for intent in intents:
                if selected_category != "All" and intent["category"] != selected_category:
                    continue

                with st.expander(f"**{intent['name']}** ({intent['id']})"):
                    col1, col2 = st.columns([2, 1])

                    with col1:
                        st.markdown(f"**Category**: {intent['category']}")
                        st.markdown(f"**Description**: {intent.get('description', 'N/A')}")
                        st.markdown(f"**Matches When**: {intent.get('matches_when', 'N/A')}")
                        st.markdown(f"**Does Not Match When**: {intent.get('does_not_match_when', 'N/A')}")

                        st.markdown("**Key Signals**:")
                        st.code(", ".join(intent.get("key_signals", [])))

                        st.markdown("**Hinglish Variants**:")
                        st.code(", ".join(intent.get("hinglish_variants", [])))

                    with col2:
                        st.markdown(f"**Priority**: {intent.get('priority', 5)}/10")
                        st.markdown(f"**Requires Human**: {'Yes' if intent.get('requires_human') else 'No'}")
                        st.markdown(f"**Active**: {'Yes' if intent.get('is_active', True) else 'No'}")

                        if st.button("Delete", key=f"del_{intent['id']}", type="secondary"):
                            if api_call(f"/intents/{intent['id']}", method="DELETE"):
                                st.success(f"Deleted {intent['id']}")
                                st.rerun()

                    st.markdown("**Response Template**:")
                    st.text_area(
                        "Template",
                        intent.get("response_template", ""),
                        height=150,
                        disabled=True,
                        key=f"template_{intent['id']}"
                    )

    with tab2:
        st.markdown("### Add New Intent")

        with st.form("add_intent_form"):
            col1, col2 = st.columns(2)

            with col1:
                intent_id = st.text_input("Intent ID", placeholder="my_new_intent")
                intent_name = st.text_input("Intent Name", placeholder="My New Intent")
                category = st.selectbox(
                    "Category",
                    ["card_management", "account", "transfers", "payments", "security", "support", "rewards", "loans"]
                )
                description = st.text_area("Description", height=100)

            with col2:
                matches_when = st.text_area("Matches When", height=80)
                does_not_match = st.text_area("Does Not Match When", height=80)
                key_signals = st.text_input("Key Signals (comma-separated)")
                hinglish = st.text_input("Hinglish Variants (comma-separated)")

            response_template = st.text_area("Response Template", height=150)

            col1, col2 = st.columns(2)
            with col1:
                priority = st.slider("Priority", 1, 10, 5)
            with col2:
                requires_human = st.checkbox("Requires Human Agent")

            submitted = st.form_submit_button("Add Intent", type="primary")

            if submitted:
                if intent_id and intent_name and response_template:
                    data = {
                        "id": intent_id,
                        "name": intent_name,
                        "category": category,
                        "description": description,
                        "response_template": response_template,
                        "matches_when": matches_when,
                        "does_not_match_when": does_not_match,
                        "key_signals": [s.strip() for s in key_signals.split(",") if s.strip()],
                        "hinglish_variants": [s.strip() for s in hinglish.split(",") if s.strip()],
                        "priority": priority,
                        "requires_human": requires_human
                    }

                    result = api_call("/intents", method="POST", data=data)
                    if result:
                        st.success(f"Intent '{intent_name}' created successfully!")
                else:
                    st.error("Please fill in all required fields")


# ============ Escalations Page ============

elif page == "Escalations":
    st.title("🚨 Escalation Queue")

    # Stats
    stats = api_call("/escalations/stats")
    if stats:
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Total Escalations", stats.get("total", 0))
        with c2:
            st.metric("Pending", stats.get("pending", 0))
        with c3:
            st.metric("Resolved", stats.get("resolved", 0))
        with c4:
            st.metric("Avg Resolution Time", f"{stats.get('avg_resolution_time_minutes', 0):.0f} min")

    st.markdown("---")

    # Pending escalations
    st.markdown("### Pending Escalations")

    escalations = api_call("/escalations")

    if escalations:
        for esc in escalations:
            priority_color = "🔴" if esc["priority"] >= 8 else ("🟡" if esc["priority"] >= 5 else "🟢")

            with st.expander(f"{priority_color} **Ticket #{esc['id']}** - Priority {esc['priority']}/10"):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown(f"**Reason**: {esc['reason']}")
                    st.markdown(f"**Last Query**: {esc.get('last_query', 'N/A')}")
                    st.markdown(f"**Detected Intent**: {esc.get('detected_intent', 'N/A')}")
                    st.markdown(f"**Sentiment**: {esc.get('sentiment', 'N/A')}")
                    st.markdown(f"**Urgency**: {esc.get('urgency_score', 0):.1%}")

                with col2:
                    st.markdown(f"**Status**: {esc['status']}")
                    st.markdown(f"**Created**: {esc.get('created_at', 'N/A')}")

                    if esc["status"] == "pending":
                        agent = st.text_input("Assign to Agent", key=f"agent_{esc['id']}")
                        if st.button("Assign", key=f"assign_{esc['id']}"):
                            if agent:
                                api_call(
                                    f"/escalations/{esc['id']}/assign",
                                    method="POST",
                                    data={"agent_id": agent}
                                )
                                st.success(f"Assigned to {agent}")
                                st.rerun()

                    if esc["status"] in ["assigned", "in_progress"]:
                        notes = st.text_area("Resolution Notes", key=f"notes_{esc['id']}")
                        if st.button("Resolve", key=f"resolve_{esc['id']}", type="primary"):
                            if notes:
                                api_call(
                                    f"/escalations/{esc['id']}/resolve",
                                    method="POST",
                                    data={"resolution_notes": notes}
                                )
                                st.success("Resolved!")
                                st.rerun()
    else:
        st.info("No pending escalations")


# ============ Settings Page ============

elif page == "Settings":
    st.title("⚙️ Settings")

    st.markdown("### API Configuration")

    col1, col2 = st.columns(2)

    with col1:
        st.text_input("API Base URL", value=API_BASE_URL, disabled=True)

        # Get current usage
        usage = api_call("/analytics/usage")
        if usage:
            st.markdown("### LLM Usage")
            st.markdown(f"**Total Input Tokens**: {usage.get('total_input_tokens', 0):,}")
            st.markdown(f"**Total Output Tokens**: {usage.get('total_output_tokens', 0):,}")
            st.markdown(f"**Total Cost**: ${usage.get('total_cost_usd', 0):.4f}")

    with col2:
        st.markdown("### Model Settings")
        st.info("""
        Model settings are configured via environment variables:
        - DEFAULT_MODEL: claude-sonnet-4-20250514
        - FALLBACK_MODEL: claude-haiku-4-20250514
        - CONFIDENCE_THRESHOLD: 0.7
        - ESCALATION_THRESHOLD: 0.4
        """)

    st.markdown("---")
    st.markdown("### Export Data")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Export Intents as JSON"):
            intents = api_call("/intents")
            if intents:
                st.download_button(
                    "Download JSON",
                    data=json.dumps(intents, indent=2),
                    file_name="intents_export.json",
                    mime="application/json"
                )

    with col2:
        if st.button("Export Analytics as CSV"):
            st.info("Analytics export coming soon")


# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("v1.0.0 | Built with Streamlit")

import asyncio
import streamlit as st
import pandas as pd
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.future import select
from sqlalchemy import func
import sys
import os

# Ensure the parent app package is resolvable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.models.lead import Lead, PriorityEnum
from app.models.message import Message
from app.core.config import get_settings

settings = get_settings()

# Setup DB Connection for Dashboard
engine = create_async_engine(settings.DATABASE_URL)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


def run_async(coro):
    """Helper to run async code in Streamlit sync environment"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


st.set_page_config(page_title="Lead Capture Dashboard", layout="wide")
st.title("AI Lead Capture Dashboard")

# Create tabs for Dashboard and Live Chat
tab_dash, tab_chat = st.tabs(["📊 Analytics Dashboard", "💬 Live Bot Chat"])

with tab_dash:

    async def get_kpis():
        async with AsyncSessionLocal() as session:
            total_leads = (
                await session.execute(select(func.count(Lead.id)))
            ).scalar_one()
            high_priority = (
                await session.execute(
                    select(func.count(Lead.id)).where(
                        Lead.priority == PriorityEnum.high
                    )
                )
            ).scalar_one()
            avg_budget = (
                await session.execute(select(func.avg(Lead.budget)))
            ).scalar_one() or 0
            return total_leads, high_priority, avg_budget

    total_leads, high_priority, avg_budget = run_async(get_kpis())

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Leads", total_leads)
    col2.metric("High Priority", high_priority)
    col3.metric("Average Budget (INR)", f"₹ {avg_budget:,.2f}")

    st.divider()

    async def get_all_leads_df():
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Lead).order_by(Lead.updated_at.desc())
            )
            leads = result.scalars().all()
            data = []
            for l in leads:
                # Extract additional_fields
                add_fields = l.additional_fields or {}
                data.append(
                    {
                        "Session ID": l.session_id,
                        "Name": l.name,
                        "Email": l.email,
                        "Phone": l.phone,
                        "Location": l.location,
                        "Service Interest": l.service_interest,
                        "Budget (INR)": l.budget,
                        "Budget (Formatted)": f"₹{l.budget / 100000:.1f}L"
                        if l.budget
                        else None,
                        "Timeline (Months)": l.timeline_months,
                        "Preference": l.preference,
                        "Priority": l.priority.value if l.priority else None,
                        "Core Need": add_fields.get("core_need"),
                        "Pain Urgency": add_fields.get("pain_urgency"),
                        "Decision Maker": add_fields.get("decision_maker"),
                        "Follow-ups": l.follow_up_count,
                        "Created At": l.created_at,
                        "Updated At": l.updated_at,
                    }
                )
            return pd.DataFrame(data)

    async def get_messages_for_session(session_id: str):
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Message)
                .where(Message.session_id == session_id)
                .order_by(Message.created_at.asc())
            )
            return result.scalars().all()

    df_leads = run_async(get_all_leads_df())

    st.subheader("Captured Leads")
    if not df_leads.empty:
        # Reorder columns for better visibility
        cols = [
            "Name",
            "Email",
            "Phone",
            "Location",
            "Service Interest",
            "Budget (Formatted)",
            "Timeline (Months)",
            "Priority",
            "Core Need",
            "Pain Urgency",
            "Decision Maker",
            "Follow-ups",
            "Created At",
            "Session ID",
        ]
        available_cols = [c for c in cols if c in df_leads.columns]
        st.dataframe(
            df_leads[available_cols], use_container_width=True, hide_index=True
        )
    else:
        st.info("No leads captured yet.")

    st.divider()

    st.subheader("Conversation Viewer")
    if not df_leads.empty:
        session_ids = df_leads["Session ID"].tolist()
        selected_session = st.selectbox(
            "Select a session to view history:", session_ids
        )

        if selected_session:
            messages = run_async(get_messages_for_session(selected_session))
            for msg in messages:
                with st.chat_message(msg.role.value):
                    st.write(msg.content)

with tab_chat:
    import requests

    # Custom CSS for chat-like layout
    st.markdown(
        """
    <style>
    .chat-container {
        display: flex;
        flex-direction: column;
        justify-content: flex-end;
        min-height: 400px;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    if "chat_session_id" not in st.session_state:
        st.session_state.chat_session_id = None
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    # Header with new chat button
    col_btn1, col_btn2 = st.columns([1, 6])
    with col_btn1:
        if st.button("🔄 New Chat", use_container_width=True):
            st.session_state.chat_session_id = None
            st.session_state.chat_messages = []
            st.rerun()
    with col_btn2:
        st.caption(
            f"Session: `{st.session_state.chat_session_id or 'New conversation'}`"
        )

    # Chat container - messages at top, input at bottom
    chat_container = st.container()

    with chat_container:
        # Display chat history
        for msg in st.session_state.chat_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # Input at bottom
    if prompt := st.chat_input("Type your message...", key="chat_input"):
        # Add user message
        st.session_state.chat_messages.append({"role": "user", "content": prompt})

        with st.spinner("Bot is typing..."):
            payload = {"message": prompt}
            if st.session_state.chat_session_id:
                payload["session_id"] = st.session_state.chat_session_id

            try:
                res = requests.post("http://localhost:8000/webhook", json=payload)
                if res.status_code == 200:
                    data = res.json()
                    st.session_state.chat_session_id = data.get("session_id")
                    reply_text = data.get("reply", "No reply.")
                    st.session_state.chat_messages.append(
                        {"role": "assistant", "content": reply_text}
                    )
                    st.rerun()
                else:
                    st.error(f"Error {res.status_code}: {res.text}")
            except Exception as e:
                st.error(f"Connection failed: {e}")

"""
Chat interface component for the GTM Finance Intelligence Agent.

Provides a conversational sidebar where users can ask natural-language
questions about their GTM data, powered by Claude Opus.
"""

import streamlit as st
from typing import Any


def render_chat_sidebar(df: Any) -> None:
    """Render the chat-with-your-data interface in the Streamlit sidebar.

    Maintains conversation history in session state and sends questions
    to Claude with full data context.

    Args:
        df: The loaded GTM dataset (pandas DataFrame or None).
    """
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 💬 Chat With Your Data")

    if df is None:
        st.sidebar.info("📊 Load data first to start chatting.")
        return

    # Initialize conversation history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Display conversation history
    chat_container = st.sidebar.container()
    with chat_container:
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                st.markdown(
                    f'<div style="background:#16213e; padding:8px 12px; border-radius:8px; '
                    f'margin:4px 0; border-left:3px solid #CC785C;">'
                    f'<small style="color:#CC785C;">You</small><br>'
                    f'<span style="color:#E0E0E0;">{msg["content"]}</span></div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div style="background:#1a1a3e; padding:8px 12px; border-radius:8px; '
                    f'margin:4px 0; border-left:3px solid #85CDCA;">'
                    f'<small style="color:#85CDCA;">Agent</small><br>'
                    f'<span style="color:#E0E0E0;">{msg["content"]}</span></div>',
                    unsafe_allow_html=True,
                )

    # Sample questions
    if not st.session_state.chat_history:
        st.sidebar.markdown("**💡 Try asking:**")
        sample_questions = [
            "Which region has the best LTV:CAC?",
            "What's our current ARR growth rate?",
            "What happens if we cut marketing by 20%?",
            "When will we hit $10M ARR?",
            "What's our biggest risk right now?",
        ]
        for q in sample_questions:
            if st.sidebar.button(f"→ {q}", key=f"sample_{q[:20]}", use_container_width=True):
                _process_question(df, q)
                st.rerun()

    # Chat input
    user_input = st.sidebar.text_input(
        "Ask a question about your GTM data:",
        key="chat_input",
        placeholder="e.g., Which product is growing fastest?",
    )

    col1, col2 = st.sidebar.columns([3, 1])
    with col1:
        send_clicked = st.button("Send 📤", key="chat_send", use_container_width=True)
    with col2:
        if st.button("Clear 🗑️", key="chat_clear"):
            st.session_state.chat_history = []
            st.rerun()

    if send_clicked and user_input:
        _process_question(df, user_input)
        st.rerun()


def _process_question(df: Any, question: str) -> None:
    """Process a user question through the Claude agent.

    Args:
        df: The loaded GTM dataset.
        question: The user's question text.
    """
    from agents.gtm_agent import chat_with_data

    # Add user message
    st.session_state.chat_history.append({
        "role": "user",
        "content": question,
    })

    # Get AI response
    try:
        response = chat_with_data(
            df=df,
            user_question=question,
            conversation_history=st.session_state.chat_history[:-1],  # exclude current
        )
    except Exception as e:
        response = f"⚠️ Error: {str(e)}"

    # Add assistant message
    st.session_state.chat_history.append({
        "role": "assistant",
        "content": response,
    })

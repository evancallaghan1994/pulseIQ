"""
Knowledge Assistant page.
Chat interface backed by the RAG pipeline (ChromaDB + Claude).
"""

import streamlit as st
from rag.query import answer_question

st.set_page_config(page_title="Knowledge Assistant · PulseIQ", page_icon="💬", layout="wide")

with st.sidebar:
    st.markdown("## 🔬 PulseIQ")
    st.markdown("*AI Sales Intelligence*")
    st.divider()
    st.page_link("app.py",                          label="Home",               icon="🏠")
    st.page_link("pages/01_lead_scoring.py",        label="Lead Scoring",        icon="🎯")
    st.page_link("pages/02_deal_risk.py",           label="Deal Risk",           icon="⚠️")
    st.page_link("pages/03_knowledge_assistant.py", label="Knowledge Assistant", icon="💬")
    st.page_link("pages/04_insights.py",            label="Insights",            icon="📊")

STARTER_QUESTIONS = [
    "How do we handle pricing objections?",
    "What makes PulseIQ better than LabMatrix Pro?",
    "What are the available pricing tiers?",
]

st.title("💬 Knowledge Assistant")
st.caption("Ask questions about pricing, competitors, and objection handling · Powered by Claude + RAG")

# Initialise chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Suggested starter questions (shown only on first load)
if not st.session_state.messages:
    st.markdown("**Suggested questions:**")
    cols = st.columns(len(STARTER_QUESTIONS))
    for col, question in zip(cols, STARTER_QUESTIONS):
        if col.button(question, use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": question})
            with st.spinner("Thinking..."):
                result = answer_question(question)
            reply = f"{result['answer']}\n\n*Sources: {', '.join(result['sources'])}*"
            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.rerun()

st.divider()

# Render chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
if prompt := st.chat_input("Ask a sales question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Searching knowledge base..."):
            result = answer_question(prompt)
        reply = f"{result['answer']}\n\n*Sources: {', '.join(result['sources'])}*"
        st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})

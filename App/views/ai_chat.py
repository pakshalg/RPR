# ─────────────────────────────────────────────
# RPR Automated — AI Chat Interface
# app/pages/ai_chat.py
# ─────────────────────────────────────────────

import os
import streamlit as st
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """You are RPR Automated's AI assistant, built specifically for Jectronics LLC — 
a multi-channel resale business operating as MayflowerMobile on Amazon and Jectronics on eBay.

You have access to the business's sales, inventory, and profit data. Answer questions clearly 
and directly. When you don't have live data yet (system is still being set up), say so honestly.

Key context:
- The business sources overstock, store returns, and surplus inventory
- Products span gaming, mobile, wearables, electronics, clothing, books, sporting goods
- Inventory has three locations: Warehouse, FBA In Transit, FBA Available
- Profit is calculated using FIFO costing — lot costs vary per batch
- Amazon has two fulfillment types: FBA and FBM (direct)
- eBay fees are ~13%, Amazon referral ~15%, FBA adds a per-unit fulfillment fee

Be concise. Lead with the answer, then explain if needed."""


def render():
    st.title("🤖 AI Assistant")
    st.caption("Ask any question about your sales, inventory, or profit in plain English")
    st.markdown("---")

    # Init chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Display existing messages
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Input
    if prompt := st.chat_input("Ask anything — e.g. 'What was my best-selling category last month?'"):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            api_key = os.getenv("API_KEY")
            if not api_key:
                st.error("API_KEY not set in .env")
                return

            client = genai.Client(api_key=api_key)
            with st.spinner("Thinking..."):
                history = [
                    types.Content(
                        role=m["role"],
                        parts=[types.Part(text=m["content"])]
                    )
                    for m in st.session_state.chat_history
                ]
                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
                    contents=history,
                )
                reply = response.text

            st.markdown(reply)
            st.session_state.chat_history.append({"role": "assistant", "content": reply})

    # Clear button
    if st.session_state.chat_history:
        if st.button("Clear conversation", type="secondary"):
            st.session_state.chat_history = []
            st.rerun()

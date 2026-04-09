# ─────────────────────────────────────────────
# RPR Automated — Streamlit Entry Point
# app/main.py
# Run with:  streamlit run app/main.py
# ─────────────────────────────────────────────

import os
import streamlit as st
from database import test_connection

st.set_page_config(
    page_title="Jamie's Warehouse",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Sidebar navigation ──
st.sidebar.title("📦 RPR Automated")
st.sidebar.markdown("---")

pages = {
    "📊 Dashboard":         "dashboard",
    "📦 Inventory":         "inventory",
    "💰 Profit & Sales":    "profit",
    "🚚 FBA Tracker":       "fba",
    "📁 Upload Shipment":   "upload",
    "🤖 AI Assistant":      "ai_chat",
    "⚙️ Settings":          "settings",
}

selection = st.sidebar.radio("Navigate", list(pages.keys()), label_visibility="collapsed")
page_key = pages[selection]

# ── DB status indicator in sidebar ──
st.sidebar.markdown("---")
if test_connection():
    st.sidebar.success("● Database connected", icon=None)
else:
    st.sidebar.error("● Database offline")

st.sidebar.caption("RPR Automated v0.1 · Jectronics LLC")

# ── Page routing ──
if page_key == "dashboard":
    from views import dashboard
    dashboard.render()

elif page_key == "inventory":
    from views import inventory
    inventory.render()

elif page_key == "profit":
    from views import profit
    profit.render()

elif page_key == "fba":
    from views import fba
    fba.render()

elif page_key == "upload":
    from views import upload
    upload.render()

elif page_key == "ai_chat":
    from views import ai_chat
    ai_chat.render()

elif page_key == "settings":
    from views import settings
    settings.render()

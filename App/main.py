import streamlit as st
from database import test_connection

st.set_page_config(
    page_title="Jamie's Warehouse",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

pages = {
    "📊 Dashboard":         "dashboard",
    "📦 Inventory":         "inventory",
    "💰 Profit & Sales":    "profit",
    "🚚 FBA Tracker":       "fba",
    "📁 Upload Shipment":   "upload",
    "🤖 AI Assistant":      "ai_chat",
    "⚙️ Settings":          "settings",
}

page_key = st.query_params.get("page", "dashboard")
if page_key not in pages.values():
    page_key = "dashboard"

db_ok = test_connection()
db_color = "#22c55e" if db_ok else "#ef4444"
db_label = "Database connected" if db_ok else "Database offline"

nav_items_html = ""
for label, key in pages.items():
    parts = label.split(" ", 1)
    icon = parts[0]
    text = parts[1] if len(parts) > 1 else ""
    active = "active" if page_key == key else ""
    nav_items_html += (
        '<a class="nav-item ' + active + '" href="?page=' + key + '" target="_self">'
        '<span class="nav-icon">' + icon + '</span>'
        '<span class="nav-label">' + text + '</span>'
        '</a>'
    )

footer_html = (
    '<div class="sidebar-footer">'
    '<div class="footer-db" style="color:' + db_color + ';">&#9679; ' + db_label + '</div>'
    '<div class="footer-line">RPR v0.1 &middot; Jectronics LLC</div>'
    '</div>'
)

st.markdown(f"""
<style>
/* Hide Streamlit's sidebar, toggle button, and header */
[data-testid="stSidebar"] {{ display: none !important; }}
[data-testid="stSidebarCollapsedControl"] {{ display: none !important; }}
[data-testid="collapsedControl"] {{ display: none !important; }}
[data-testid="stHeader"] {{ display: none !important; }}
header {{ display: none !important; }}
#MainMenu {{ display: none !important; }}

/* Remove top gap from main content */
.block-container {{ padding-top: 0 !important; margin-top: 0 !important; }}
.main .block-container {{ padding-top: 0 !important; margin-top: 0 !important; }}
.stMainBlockContainer {{ padding-top: 0 !important; }}
div[data-testid="stAppViewBlockContainer"] {{ padding-top: 0 !important; }}
div[data-testid="stVerticalBlock"] > div:first-child {{ margin-top: 0 !important; padding-top: 0 !important; }}

/* Push main content right to clear the slim sidebar */
.main .block-container {{
    padding-left: 5rem !important;
    max-width: 100% !important;
}}

/* Hover sidebar */
.custom-sidebar {{
    position: fixed;
    left: 1rem;
    top: 50%;
    transform: translateY(-50%);
    height: auto;
    max-height: 80vh;
    width: 3.25rem;
    background: #f3f4f6;
    transition: width 0.22s cubic-bezier(0.4, 0, 0.2, 1);
    overflow: hidden;
    z-index: 1000;
    border: 1px solid #e5e7eb;
    border-radius: 16px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.08);
    display: flex;
    flex-direction: column;
    padding: 0.5rem 0;
}}
.custom-sidebar:hover {{
    width: 210px;
}}

/* Title row */
.sidebar-title {{
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding: 0.5rem 0.9rem 0.5rem 0.9rem;
    white-space: nowrap;
}}
.sidebar-title-icon {{ font-size: 1.1rem; flex-shrink: 0; }}
.sidebar-title-text {{
    font-size: 1.1rem;
    font-weight: 700;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    color: #6b7280;
    opacity: 0;
    transition: opacity 0.12s ease 0.08s;
    white-space: nowrap;
}}
.custom-sidebar:hover .sidebar-title-text {{ opacity: 1; }}

/* Nav items */
.nav-item {{
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.42rem 0.85rem;
    margin: 0.05rem 0.35rem;
    border-radius: 6px;
    font-size: 0.875rem;
    color: #9ca3af;
    text-decoration: none !important;
    white-space: nowrap;
    transition: color 0.15s, background 0.15s;
}}
.nav-item:hover {{ color: #1f2937; background: rgba(0,0,0,0.05); }}
.nav-item.active {{
    color: #1f2937;
    background: rgba(0,0,0,0.07);
    font-weight: 500;
    text-decoration: underline !important;
}}
.nav-icon {{ font-size: 1rem; flex-shrink: 0; width: 1.1rem; text-align: center; }}
.nav-label {{
    opacity: 0;
    transition: opacity 0.12s ease 0.08s;
}}
.custom-sidebar:hover .nav-label {{ opacity: 1; }}

/* Footer */
.sidebar-footer {{
    max-height: 0;
    overflow: hidden;
    padding: 0 0.9rem;
    white-space: nowrap;
    transition: max-height 0.22s ease, padding 0.22s ease;
}}
.custom-sidebar:hover .sidebar-footer {{
    max-height: 4rem;
    padding: 0.6rem 0.9rem;
}}
.footer-line {{
    font-size: 0.7rem;
    color: #9ca3af;
    margin-bottom: 0.15rem;
}}
.footer-db {{
    font-size: 0.7rem;
    margin-bottom: 0.15rem;
}}
</style>

<div class="custom-sidebar">
    <div class="sidebar-title">
        <span class="sidebar-title-icon">📦</span>
        <span class="sidebar-title-text">RPR Automated</span>
    </div>
    {nav_items_html}
    {footer_html}
</div>
""", unsafe_allow_html=True)

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

import streamlit as st
import streamlit.components.v1 as components
from database import test_connection
from settings_utils import load as _load_settings, current_theme as _current_theme

st.set_page_config(
    page_title="Jamie's Warehouse",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Load persisted settings into session state once per session
if "settings_loaded" not in st.session_state:
    for k, v in _load_settings().items():
        st.session_state.setdefault(k, v)
    st.session_state["settings_loaded"] = True

_sidebar_bg  = "#2e2f35" if _current_theme() == "dark" else "#f3f4f6"
_sidebar_border = "#3a3b42" if _current_theme() == "dark" else "#e5e7eb"
_nav_color   = "#9ca3af" if _current_theme() == "dark" else "#9ca3af"
_nav_active  = "#e8e8f0" if _current_theme() == "dark" else "#1f2937"

pages = {
    "📊 Dashboard":         "dashboard",
    "📦 Inventory":         "inventory",
    "💰 Profit & Sales":    "profit",
    "🚚 FBA Tracker":       "fba",
    "📁 Upload Shipment":   "upload",
    "😄 AI Assistant":      "ai_chat",
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
    background: {_sidebar_bg};
    transition: width 0.22s cubic-bezier(0.4, 0, 0.2, 1);
    overflow: hidden;
    z-index: 1000;
    border: 1px solid {_sidebar_border};
    cursor: grab;
    user-select: none;
    border-radius: 16px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.08);
    display: flex;
    flex-direction: column;
    padding: 0.5rem 0;
}}
.custom-sidebar:hover {{
    width: 210px;
}}
.custom-sidebar.is-dragging,
.custom-sidebar.is-dragging:hover {{
    width: 3.25rem !important;
    transition: none !important;
}}
.custom-sidebar.is-dragging .nav-label {{
    opacity: 0 !important;
    transition: none !important;
}}
.custom-sidebar.is-dragging .sidebar-title,
.custom-sidebar.is-dragging .sidebar-footer {{
    max-height: 0 !important;
    padding: 0 !important;
    transition: none !important;
}}

/* Title — hidden when collapsed, visible on hover */
.sidebar-title {{
    max-height: 0;
    overflow: hidden;
    padding: 0 0.9rem;
    white-space: nowrap;
    transition: max-height 0.22s ease, padding 0.22s ease;
}}
.custom-sidebar:hover .sidebar-title {{
    max-height: 3rem;
    padding: 0.5rem 0.9rem;
}}
.sidebar-title-text {{
    font-size: 1.1rem;
    font-weight: 700;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    color: #6b7280;
}}

/* Nav items */
.nav-item {{
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.42rem 0.85rem 0.42rem 0.5rem;
    margin: 0.05rem 0.35rem;
    border-radius: 6px;
    font-size: 0.875rem;
    color: #9ca3af;
    text-decoration: none !important;
    white-space: nowrap;
    transition: color 0.15s, background 0.15s;
}}
.nav-item:hover {{ color: {_nav_active}; background: rgba(128,128,128,0.12); }}
.nav-item.active {{
    color: {_nav_active};
    background: rgba(128,128,128,0.15);
    font-weight: 500;
    text-decoration: none !important;
}}
.nav-item.active .nav-label {{
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
        <span class="sidebar-title-text">RPR Automated</span>
    </div>
    {nav_items_html}
    {footer_html}
</div>
""", unsafe_allow_html=True)

# ── Draggable sidebar ──
components.html("""
<script>
(function () {
    function init() {
        var doc = window.parent.document;
        var sb = doc.querySelector('.custom-sidebar');
        if (!sb) { setTimeout(init, 300); return; }

        // Restore saved position
        var savedLeft = localStorage.getItem('rpr_sb_left');
        var savedTop  = localStorage.getItem('rpr_sb_top');
        if (savedLeft && savedTop) {
            sb.style.transform = 'none';
            sb.style.left = savedLeft;
            sb.style.top  = savedTop;
        }

        var dragging = false, pending = false, ox, oy, sl, st;
        var THRESHOLD = 6;

        sb.addEventListener('mousedown', function (e) {
            if (e.button !== 0) return;
            pending = true;
            var r = sb.getBoundingClientRect();
            ox = e.clientX; oy = e.clientY;
            sl = r.left;    st = r.top;
        });

        doc.addEventListener('mousemove', function (e) {
            if (!pending) return;
            if (!dragging) {
                var dx = e.clientX - ox, dy = e.clientY - oy;
                if (Math.sqrt(dx*dx + dy*dy) < THRESHOLD) return;
                dragging = true;
                sb.style.transform = 'none';
                sb.style.left = sl + 'px';
                sb.style.top  = st + 'px';
                sb.classList.add('is-dragging');
                doc.body.style.userSelect = 'none';
            }
            sb.style.left = (sl + e.clientX - ox) + 'px';
            sb.style.top  = (st + e.clientY - oy) + 'px';
        });

        doc.addEventListener('mouseup', function () {
            if (dragging) {
                sb.classList.remove('is-dragging');
                localStorage.setItem('rpr_sb_left', sb.style.left);
                localStorage.setItem('rpr_sb_top',  sb.style.top);
                doc.body.style.userSelect = '';
            }
            dragging = false;
            pending = false;
        });

    }
    init();
})();
</script>
""", height=0)

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

import streamlit as st
from settings_utils import load as _load, save as _save, current_theme, set_theme


def render():
    st.title("⚙️ Settings")
    st.caption("Configure appearance and preferences")
    st.markdown("---")

    st.subheader("🎨 Appearance")

    saved   = _load()
    theme   = current_theme()
    color   = st.session_state.get("panel_color", saved.get("panel_color", "#4c1d95"))

    # ── Theme toggle ──
    new_theme_label = st.radio(
        "Theme",
        options=["Dark", "Light"],
        index=0 if theme == "dark" else 1,
        horizontal=True,
    )
    new_theme = "dark" if new_theme_label == "Dark" else "light"

    if new_theme != theme:
        set_theme(new_theme)
        st.warning("Theme updated — restart the app for it to take effect.")

    # ── Panel color ──
    new_color = st.color_picker("Dashboard Panel Color", value=color)

    if new_color != color:
        st.session_state["panel_color"] = new_color
        _save({**saved, "panel_color": new_color})
        st.success("Panel color saved.")

# ─────────────────────────────────────────────
# RPR Automated — AI Chat Interface
# app/pages/ai_chat.py
# ─────────────────────────────────────────────

import os
import time
import streamlit as st
from dotenv import load_dotenv
from database import get_connection, release_connection

# Explicitly load the App .env to ensure Streamlit processes pick it up
APP_ENV = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(dotenv_path=APP_ENV)

SYSTEM_PROMPT_BASE = """You are RPR Automated's AI assistant, built specifically for Jectronics LLC — 
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

IMPORTANT: When referring to inventory, sales, or any product-related information, always use the product name or title, not the SKU. Do not mention SKUs unless the user specifically asks for them. If both are available, prefer the product name/title in all responses.

Be concise. Lead with the answer, then explain if needed."""


def get_live_data():
    try:
        conn = get_connection()
        cur = conn.cursor()

        # Warehouse Inventory with product title
        cur.execute("""
            SELECT w.sku, p.title, w.quantity, w.location
            FROM inventory_warehouse w
            JOIN products p ON w.sku = p.sku
        """)
        warehouse_rows = cur.fetchall()

        # FBA Inventory with product title
        cur.execute("""
            SELECT f.sku, p.title, f.qty_in_transit, f.qty_available, f.qty_reserved, f.shipment_id
            FROM inventory_fba f
            JOIN products p ON f.sku = p.sku
        """)
        fba_rows = cur.fetchall()

        # Amazon Sales with product title
        cur.execute("""
            SELECT s.sku, p.title, s.sale_date, s.quantity, s.sale_price
            FROM sales_amazon s
            JOIN products p ON s.sku = p.sku
        """)
        amazon_rows = cur.fetchall()

        # eBay Sales with product title
        cur.execute("""
            SELECT s.sku, p.title, s.sale_date, s.quantity, s.sale_price
            FROM sales_ebay s
            JOIN products p ON s.sku = p.sku
        """)
        ebay_rows = cur.fetchall()

        cur.close()
        release_connection(conn)

        warehouse_text = "Warehouse Inventory:\n" + (("\n".join([
            f"- {title}: {quantity} units (Location: {location if location else 'N/A'})"
            for _, title, quantity, location in warehouse_rows
        ])) or "  (no records)")
        fba_text = "FBA Inventory:\n" + (("\n".join([
            f"- {title}: {qty_available} available, {qty_in_transit} in transit, {qty_reserved} reserved (Shipment: {shipment_id if shipment_id else 'N/A'})"
            for _, title, qty_in_transit, qty_available, qty_reserved, shipment_id in fba_rows
        ])) or "  (no records)")
        amazon_text = "Amazon Sales:\n" + (("\n".join([
            f"- {title} on {sale_date}: {quantity} sold, ${sale_price:.2f}"
            for _, title, sale_date, quantity, sale_price in amazon_rows
        ])) or "  (no records)")
        ebay_text = "eBay Sales:\n" + (("\n".join([
            f"- {title} on {sale_date}: {quantity} sold, ${sale_price:.2f}"
            for _, title, sale_date, quantity, sale_price in ebay_rows
        ])) or "  (no records)")

        return f"{warehouse_text}\n\n{fba_text}\n\n{amazon_text}\n\n{ebay_text}"
    except Exception as e:
        raise RuntimeError(f"Failed to load live data from database: {e}") from e


def get_system_prompt():
    live_data = get_live_data()
    return f"{SYSTEM_PROMPT_BASE}\n\nLive Data:\n{live_data}"


def render():
    st.title("😄 AI Assistant")
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
            try:
                system_prompt = get_system_prompt()
            except RuntimeError as e:
                st.error(str(e))
                st.session_state.chat_history.pop()
                st.stop()

            provider = os.getenv("AI_PROVIDER", "groq").lower()

            if provider == "google":
                # Existing google-genai flow (lazy import)
                try:
                    from google import genai
                    from google.genai import types
                except Exception:
                    st.error("Missing or broken dependency: google-genai. Install with `pip install google-genai` and restart Streamlit.")
                    return

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
                        config=types.GenerateContentConfig(system_instruction=system_prompt),
                        contents=history,
                    )
                    reply = response.text

                st.markdown(reply)
                st.session_state.chat_history.append({"role": "assistant", "content": reply})

            elif provider == "groq":
                # Groq HTTP-based flow. Requires GROQ_API_URL and GROQ_API_KEY env vars.
                groq_url = os.getenv("GROQ_API_URL")
                groq_key = os.getenv("GROQ_API_KEY") or os.getenv("API_KEY")

                if not groq_url or not groq_key:
                    # Provide masked diagnostics to help debug environment issues
                    def mask(v):
                        if not v:
                            return None
                        return v[:4] + '...' if len(v) > 8 else '****'

                    st.error("GROQ_API_URL and GROQ_API_KEY (or API_KEY) must be set for Groq provider.")
                    st.info(
                        f"AI_PROVIDER={os.getenv('AI_PROVIDER')}\nGROQ_API_URL={mask(os.getenv('GROQ_API_URL'))}\nGROQ_API_KEY set={bool(os.getenv('GROQ_API_KEY'))}\nAPI_KEY set={bool(os.getenv('API_KEY'))}"
                    )
                    return

                # Build messages array for chat completions
                messages = [{"role": "system", "content": system_prompt}]
                messages.extend([{"role": m["role"], "content": m["content"]} for m in st.session_state.chat_history])

                try:
                    import requests
                except Exception:
                    st.error("Missing dependency: requests. Install with `pip install requests` and restart Streamlit.")
                    return

                headers = {
                    "Authorization": f"Bearer {groq_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                }
                payload = {
                    "model": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
                    "messages": messages,
                    "max_tokens": int(os.getenv("GROQ_MAX_TOKENS", "512")),
                }

                with st.spinner("Thinking..."):
                    try:
                        resp = requests.post(groq_url, json=payload, headers=headers, timeout=30)
                    except Exception as e:
                        st.error(f"Request to Groq failed: {e}")
                        return

                    if not resp.ok:
                        try:
                            err = resp.json()
                        except Exception:
                            err = resp.text
                        st.error(f"Groq API error ({resp.status_code}): {err}")
                        return

                    # Parse chat completions response
                    data = resp.json()
                    reply = None
                    if isinstance(data, dict) and "choices" in data and data["choices"]:
                        choice = data["choices"][0]
                        if "message" in choice and "content" in choice["message"]:
                            reply = choice["message"]["content"]

                    if not reply:
                        # Fallback: pretty-print JSON
                        reply = str(data)

                st.markdown(reply)
                st.session_state.chat_history.append({"role": "assistant", "content": reply})

            elif provider == "mock":
                # Simple local mock for offline development/testing
                last_user = next((m["content"] for m in reversed(st.session_state.chat_history) if m["role"] == "user"), "")
                if not last_user:
                    reply = "Hello — this is a mock AI assistant. Ask a question about sales, inventory, or profit."
                else:
                    reply = f"Mock reply — I received your question: \"{last_user}\". (Local mock response)"
                with st.spinner("Thinking (mock)..."):
                    time.sleep(0.4)
                st.markdown(reply)
                st.session_state.chat_history.append({"role": "assistant", "content": reply})

            else:
                st.error(f"Unknown AI_PROVIDER: {provider}. Supported: google, groq")
                return

    # Clear button
    if st.session_state.chat_history:
        if st.button("Clear conversation", type="secondary"):
            st.session_state.chat_history = []
            st.rerun()

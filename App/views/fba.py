# ─────────────────────────────────────────────
# RPR Automated — FBA Tracker
# app/pages/fba.py
# ─────────────────────────────────────────────


import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from database import get_connection, release_connection


def fetch_fba_shipments():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            shipment_id,
            ship_date,
            sku,
            (SELECT title FROM products p WHERE p.sku = f.sku) AS product_name,
            quantity_sent,
            status,
            COALESCE(days_in_transit, 
                CASE WHEN ship_date IS NOT NULL THEN (CURRENT_DATE - ship_date) ELSE NULL END
            ) AS days_in_transit
        FROM fba_shipments f
        ORDER BY ship_date DESC NULLS LAST, created_at DESC
    """)
    rows = cur.fetchall()
    cur.close()
    release_connection(conn)
    return rows

def fetch_overdue_shipments(days=7):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT shipment_id, sku, ship_date, quantity_sent, status,
            COALESCE(days_in_transit, CASE WHEN ship_date IS NOT NULL THEN (CURRENT_DATE - ship_date) ELSE NULL END) AS days_in_transit
        FROM fba_shipments
        WHERE status = 'In Transit' AND ship_date IS NOT NULL
            AND (COALESCE(days_in_transit, (CURRENT_DATE - ship_date))) > %s
        ORDER BY ship_date
    """, (days,))
    rows = cur.fetchall()
    cur.close()
    release_connection(conn)
    return rows

def render():
    # Inject purple font theme
    st.markdown("""
        <style>
        html, body, [class^='css']  {
            color: #7B3FE4 !important;
        }
        .stTextInput > div > input, .stTextArea textarea, .stSelectbox div[data-baseweb='select'] span {
            color: #7B3FE4 !important;
        }
        .st-bb, .st-cq, .st-cz, .st-da, .st-db, .st-dc, .st-dd, .st-de, .st-df, .st-dg, .st-dh, .st-di, .st-dj, .st-dk, .st-dl, .st-dm, .st-dn, .st-do, .st-dp, .st-dq, .st-dr, .st-ds, .st-dt, .st-du, .st-dv, .st-dw, .st-dx, .st-dy, .st-dz {
            color: #7B3FE4 !important;
        }
        </style>
    """, unsafe_allow_html=True)
    st.markdown("""
        <div style="display:flex;align-items:center;gap:16px;margin-bottom:0.5em;">
            <span style="font-size:2.2rem;">🚚</span>
            <span style="font-size:2rem;font-weight:600;letter-spacing:-1px;">FBA Shipments</span>
        </div>
        <div style="color:#888;font-size:1.1rem;margin-bottom:1.5em;">
            Track and manage all shipments sent to Amazon FBA
        </div>
    """, unsafe_allow_html=True)

    # Alert for overdue shipments
    overdue = fetch_overdue_shipments(7)
    if overdue:
        rows_html = "".join(
            f"<div style='color:#1a1a1a;font-weight:500;margin-top:0.4em;'>"
            f"Shipment <b>{s[0]}</b> (SKU: <b>{s[1]}</b>) — {s[3]} units, shipped {s[2]} — <b>{s[5]} days</b> in transit"
            f"</div>"
            for s in overdue
        )
        st.markdown(
            f"<div style='background:#ffeaea;border-radius:10px;padding:1em 1.5em;border:1.5px solid #e0b4b4;margin-bottom:1.5em;'>"
            f"<div style='color:#1a1a1a;font-weight:600;font-size:1.1rem;'>⚠️ {len(overdue)} FBA shipment(s) have been In Transit for more than 7 days without a status update:</div>"
            f"{rows_html}"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.markdown("<div style='margin-bottom:1.5em;'></div>", unsafe_allow_html=True)

    # Log FBA Shipment Form
    with st.container():
        st.markdown("<div style='font-size:1.15rem;font-weight:500;margin-bottom:0.5em;'>Log New FBA Shipment</div>", unsafe_allow_html=True)
        with st.form("log_fba_shipment_form"):
            # Fetch SKUs for dropdown
            sku_options = []
            try:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("SELECT sku, title FROM products WHERE is_active = TRUE ORDER BY title")
                sku_options = cur.fetchall()
                cur.close()
                release_connection(conn)
            except Exception as e:
                st.error(f"Error loading SKUs: {e}")
            sku_dict = {f"{sku} — {title}": sku for sku, title in sku_options}

            col1, col2 = st.columns(2)
            with col1:
                date_shipped = st.date_input("Date Shipped", value=datetime.now().date(), key="date_shipped")
                shipment_id = st.text_input("FBA Shipment ID", key="shipment_id")
            with col2:
                sku_label = st.selectbox("SKU", options=list(sku_dict.keys()), key="sku_label")
                quantity_sent = st.number_input("Quantity Sent", min_value=1, step=1, key="quantity_sent")
            notes = st.text_area("Notes (optional)", key="notes")
            submitted = st.form_submit_button("Log Shipment")

            if submitted:
                # Validation
                errors = []
                if not shipment_id.strip():
                    errors.append("Shipment ID is required.")
                if not sku_label:
                    errors.append("SKU is required.")
                if quantity_sent < 1:
                    errors.append("Quantity must be at least 1.")
                if errors:
                    st.markdown("<div style='color:#b30000;font-weight:500;margin-bottom:0.5em;'>" + "<br>".join(errors) + "</div>", unsafe_allow_html=True)
                else:
                    # Save to DB and update warehouse
                    sku = sku_dict[sku_label]
                    try:
                        conn = get_connection()
                        cur = conn.cursor()
                        # Insert into fba_shipments
                        cur.execute("""
                            INSERT INTO fba_shipments (shipment_id, sku, quantity_sent, status, ship_date, notes)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (
                            shipment_id.strip(), sku, int(quantity_sent), "In Transit", date_shipped, notes.strip() if notes else None
                        ))
                        # Reduce warehouse quantity
                        cur.execute("""
                            UPDATE inventory_warehouse
                            SET quantity = GREATEST(quantity - %s, 0), updated_at = NOW()
                            WHERE sku = %s
                        """, (int(quantity_sent), sku))
                        conn.commit()
                        cur.close()
                        release_connection(conn)
                        st.markdown("<div style='color:#4B2EDC;font-weight:500;margin-bottom:0.5em;'>Shipment logged and warehouse quantity updated.</div>", unsafe_allow_html=True)
                    except Exception as e:
                        st.markdown(f"<div style='color:#b30000;font-weight:500;margin-bottom:0.5em;'>Database error: {e}</div>", unsafe_allow_html=True)
    st.markdown("<div style='margin-bottom:2em;'></div>", unsafe_allow_html=True)

    # FBA Shipments Log Table
    try:
        rows = fetch_fba_shipments()
    except Exception as e:
        st.markdown(f"<div style='color:#b30000;font-weight:500;margin-bottom:0.5em;'>Database error: {e}</div>", unsafe_allow_html=True)
        return

    if not rows:
        st.markdown("<div style='color:#888;font-size:1.1rem;'>No FBA shipments logged yet.</div>", unsafe_allow_html=True)
        return

    df = pd.DataFrame(rows, columns=[
        "Shipment ID", "Date Shipped", "SKU", "Product Name", "Quantity Sent", "Status", "Days in Transit"
    ])

    # Highlight overdue rows in red
    def highlight_overdue(row):
        if row["Status"] == "In Transit" and row["Days in Transit"] is not None and row["Days in Transit"] > 7:
            return ["background-color: #ffcccc; color: #b30000; font-weight: bold"] * len(row)
        return [""] * len(row)

    st.markdown("<div style='font-size:1.15rem;font-weight:500;margin-bottom:0.5em;'>FBA Shipments Log</div>", unsafe_allow_html=True)
    st.dataframe(
        df.style.apply(highlight_overdue, axis=1),
        use_container_width=True,
        hide_index=True
    )

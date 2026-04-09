# ─────────────────────────────────────────────
# RPR Automated — Inventory
# app/views/inventory.py
# ─────────────────────────────────────────────

import streamlit as st
import pandas as pd
from database import get_connection, release_connection


def fetch_inventory():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            p.sku,
            p.title,
            p.category,
            COALESCE(iw.quantity, 0) AS qty_on_hand,
            ROUND(
                SUM(sl.quantity_remaining * sl.unit_cost)
                / NULLIF(SUM(sl.quantity_remaining), 0), 2
            ) AS avg_unit_cost,
            ROUND(
                COALESCE(iw.quantity, 0) *
                (SUM(sl.quantity_remaining * sl.unit_cost)
                / NULLIF(SUM(sl.quantity_remaining), 0)), 2
            ) AS total_inventory_value
        FROM products p
        LEFT JOIN inventory_warehouse iw ON p.sku = iw.sku
        LEFT JOIN shipment_lots sl ON p.sku = sl.sku
        WHERE p.is_active = TRUE
        GROUP BY p.sku, p.title, p.category, iw.quantity
        ORDER BY p.title
    """)
    rows = cur.fetchall()
    cur.close()
    release_connection(conn)
    return rows


def render():
    st.title("📦 Inventory")
    st.caption("Current stock levels and purchase costs")
    st.markdown("---")

    try:
        rows = fetch_inventory()
    except Exception as e:
        st.error(f"Database error: {e}")
        return

    if not rows:
        st.info("No inventory data found. Import a shipment CSV to get started.")
        return

    df = pd.DataFrame(rows, columns=[
        "SKU", "Product", "Category", "Available Quantity", "Avg Unit Cost", "Total Value"
    ])

    # Summary metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total SKUs", len(df))
    col2.metric("Total Units", f"{df['Available Quantity'].sum():,}")
    col3.metric("Inventory Value", f"${df['Total Value'].sum():,.2f}")

    st.markdown("---")

    # Format currency columns
    df["Avg Unit Cost"] = df["Avg Unit Cost"].apply(lambda x: f"${x:,.2f}" if x else "—")
    df["Total Value"]   = df["Total Value"].apply(lambda x: f"${x:,.2f}" if x else "—")

    st.dataframe(df, use_container_width=True, hide_index=True)

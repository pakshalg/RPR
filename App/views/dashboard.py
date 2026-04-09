# ─────────────────────────────────────────────
# RPR Automated — Dashboard
# app/pages/dashboard.py
# ─────────────────────────────────────────────

import streamlit as st


def render():
    import pandas as pd
    from database import get_connection, release_connection
    from datetime import datetime

    st.title("📊 Dashboard")
    st.caption("Overview of sales, inventory, and profit")
    st.markdown("---")

    st.markdown(
        """
        <style>
        /* Purple branding for dashboard metric cards */
        div[data-testid="stMetric"] {
            background: linear-gradient(150deg, #4c1d95 0%, #6d28d9 55%, #5b21b6 100%);
            border: 1px solid #a855f7;
            border-left: 5px solid #c084fc;
            border-radius: 12px;
            padding: 14px 12px;
            box-shadow: 0 8px 18px rgba(49, 11, 103, 0.35);
        }

        div[data-testid="stMetric"] label,
        div[data-testid="stMetric"] div[data-testid="stMetricLabel"],
        div[data-testid="stMetric"] div[data-testid="stMetricValue"],
        div[data-testid="stMetric"] div[data-testid="stMetricDelta"] {
            color: #f5ecff;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Connect to DB
    try:
        conn = get_connection()
        cur = conn.cursor()

        # Today's date boundaries
        today = datetime.now().date()
        start = f"{today} 00:00:00"
        end = f"{today} 23:59:59"

        # Total revenue and units sold today (Amazon + eBay)
        cur.execute("""
            SELECT COALESCE(SUM(sale_price * quantity),0), COALESCE(SUM(quantity),0)
            FROM (
                SELECT sale_price, quantity, sale_date FROM sales_amazon WHERE sale_date BETWEEN %s AND %s
                UNION ALL
                SELECT sale_price, quantity, sale_date FROM sales_ebay WHERE sale_date BETWEEN %s AND %s
            ) t
        """, (start, end, start, end))
        revenue_today, units_today = cur.fetchone()

        # Top selling product today (by units)
        cur.execute("""
            SELECT p.title, SUM(s.quantity) AS units
            FROM (
                SELECT sku, quantity FROM sales_amazon WHERE sale_date BETWEEN %s AND %s
                UNION ALL
                SELECT sku, quantity FROM sales_ebay WHERE sale_date BETWEEN %s AND %s
            ) s
            JOIN products p ON p.sku = s.sku
            GROUP BY p.title
            ORDER BY units DESC
            LIMIT 1
        """, (start, end, start, end))
        top_product_row = cur.fetchone()
        top_product = top_product_row[0] if top_product_row else "—"
        top_units = top_product_row[1] if top_product_row else 0

        # Inventory value (warehouse + FBA)
        cur.execute("""
            SELECT SUM(total_value) FROM (
                SELECT COALESCE(iw.quantity,0) * (
                    SUM(sl.quantity_remaining * sl.unit_cost) / NULLIF(SUM(sl.quantity_remaining),0)
                ) AS total_value
                FROM products p
                LEFT JOIN inventory_warehouse iw ON p.sku = iw.sku
                LEFT JOIN shipment_lots sl ON p.sku = sl.sku
                WHERE p.is_active = TRUE
                GROUP BY p.sku, iw.quantity
            ) t
        """)
        inventory_value = cur.fetchone()[0] or 0

        # Low stock alerts (show SKUs with < 5 units in warehouse or FBA)
        cur.execute("""
            SELECT p.sku, p.title, COALESCE(iw.quantity,0) + COALESCE(fba.qty_available,0) AS total_qty
            FROM products p
            LEFT JOIN inventory_warehouse iw ON p.sku = iw.sku
            LEFT JOIN inventory_fba fba ON p.sku = fba.sku
            WHERE (COALESCE(iw.quantity,0) + COALESCE(fba.qty_available,0)) < 5 AND p.is_active = TRUE
            ORDER BY total_qty ASC
            LIMIT 5
        """)
        low_stock = cur.fetchall()

        cur.close()
        release_connection(conn)
    except Exception as e:
        st.error(f"Database error: {e}")
        return

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Revenue Today", f"${revenue_today:,.2f}")
    col2.metric("Units Sold Today", f"{units_today:,}")
    col3.metric("Top Product", f"{top_product}", f"{top_units} sold")
    col4.metric("Inventory Value", f"${inventory_value:,.2f}")

    st.markdown("---")

    # Low stock alerts
    st.subheader(":rotating_light: Low Stock Alerts")
    if low_stock:
        df = pd.DataFrame(low_stock, columns=["SKU", "Product", "Total Qty"])
        st.table(df)
    else:
        st.success("No low stock alerts!")

# ─────────────────────────────────────────────
# RPR Automated — Profit & Sales
# app/pages/profit.py
# ─────────────────────────────────────────────

import streamlit as st
import pandas as pd
from database import get_connection, release_connection
from datetime import datetime
import uuid

def render():
    st.title("💰 Profit & Sales")
    # --- Record a Sale Form ---
    def get_inventory_skus():
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT sku, title FROM products WHERE is_active = TRUE ORDER BY title")
            skus = cur.fetchall()
            cur.close()
            release_connection(conn)
            return skus
        except Exception:
            return []

    with st.expander("➕ Record a Sale", expanded=False):
        skus = get_inventory_skus()
        sku_options = {f"{title} ({sku})": sku for sku, title in skus}
        sku_label = st.selectbox("SKU", list(sku_options.keys())) if sku_options else None
        platform = st.selectbox("Platform", ["Amazon", "eBay"])
        sale_price = st.number_input("Sale Price ($)", min_value=0.01, step=0.01, format="%.2f")
        fee = st.number_input("Platform Fee ($)", min_value=0.0, step=0.01, format="%.2f")
        quantity = st.number_input("Quantity", min_value=1, step=1, value=1)
        submitted = st.button("Record Sale", type="primary")

        if submitted and sku_label:
            sku = sku_options[sku_label]
            now = datetime.now()
            order_id = f"ORD-{now.strftime('%Y%m%d%H%M%S%f')}-{uuid.uuid4().hex[:6]}"
            try:
                conn = get_connection()
                cur = conn.cursor()
                if platform == "Amazon":
                    cur.execute("""
                        INSERT INTO sales_amazon (order_id, sku, sale_price, quantity, referral_fee, sale_date, fulfillment_type)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (order_id, sku, sale_price, quantity, fee, now, "FBM"))
                else:
                    cur.execute("""
                        INSERT INTO sales_ebay (order_id, sku, sale_price, quantity, final_value_fee, sale_date)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (order_id, sku, sale_price, quantity, fee, now))
                conn.commit()
                cur.close()
                release_connection(conn)
                st.success("Sale recorded!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to record sale: {e}")
    st.caption("FIFO-based profit tracking across Amazon and eBay")
    st.markdown("---")

    try:
        conn = get_connection()
        cur = conn.cursor()

        # Profit per item (SKU, all channels, FIFO cost)
        cur.execute("""
            SELECT p.sku, p.title,
                SUM(COALESCE(a.quantity,0) + COALESCE(e.quantity,0)) AS units_sold,
                SUM(COALESCE(a.sale_price*a.quantity,0) + COALESCE(e.sale_price*e.quantity,0)) AS revenue,
                SUM(
                    COALESCE((a.sale_price - COALESCE(a.unit_cost_fifo,0) - COALESCE(a.referral_fee,0)) * a.quantity, 0)
                    +
                    COALESCE((e.sale_price - COALESCE(e.unit_cost_fifo,0) - COALESCE(e.final_value_fee,0)) * e.quantity, 0)
                ) AS profit
            FROM products p
            LEFT JOIN sales_amazon a ON p.sku = a.sku
            LEFT JOIN sales_ebay e ON p.sku = e.sku
            GROUP BY p.sku, p.title
            HAVING SUM(COALESCE(a.quantity,0) + COALESCE(e.quantity,0)) > 0
            ORDER BY profit DESC
            LIMIT 20
        """)
        profit_rows = cur.fetchall()

        # Revenue by channel
        cur.execute("SELECT COALESCE(SUM(sale_price * quantity),0) FROM sales_amazon")
        amazon_revenue = cur.fetchone()[0]
        cur.execute("SELECT COALESCE(SUM(sale_price * quantity),0) FROM sales_ebay")
        ebay_revenue = cur.fetchone()[0]

        # Total fees
        cur.execute("SELECT COALESCE(SUM(referral_fee + fba_fulfillment_fee + other_fees),0) FROM sales_amazon")
        amazon_fees = cur.fetchone()[0]
        cur.execute("SELECT COALESCE(SUM(final_value_fee + shipping_cost + other_fees),0) FROM sales_ebay")
        ebay_fees = cur.fetchone()[0]

        cur.close()
        release_connection(conn)
    except Exception as e:
        st.error(f"Database error: {e}")
        return

    # Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Amazon Revenue", f"${amazon_revenue:,.2f}")
    col2.metric("eBay Revenue", f"${ebay_revenue:,.2f}")
    col3.metric("Total Fees", f"${(amazon_fees or 0) + (ebay_fees or 0):,.2f}")

    st.markdown("---")

    # Profit per item table
    st.subheader("Profit per Item (Top 20)")
    if profit_rows:
        df = pd.DataFrame(profit_rows, columns=["SKU", "Product", "Units Sold", "Revenue", "Profit"])
        df["Revenue"] = df["Revenue"].apply(lambda x: f"${x:,.2f}")
        df["Profit"] = df["Profit"].apply(lambda x: f"${x:,.2f}")
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No sales data found.")

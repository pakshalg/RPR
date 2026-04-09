# ─────────────────────────────────────────────
# RPR Automated — Upload Shipment
# app/pages/upload.py
# ─────────────────────────────────────────────


import streamlit as st
import pandas as pd
import tempfile
from import_shipment import import_csv


def render():
    st.title("📁 Upload Shipment")
    st.caption("Import shipment CSVs to update inventory and FIFO cost layers")
    st.markdown("---")

    uploaded_file = st.file_uploader("Choose a shipment CSV file", type=["csv"])
    if uploaded_file is not None:
        # Show preview
        df = pd.read_csv(uploaded_file)
        st.dataframe(df.head(10), use_container_width=True, hide_index=True)

        if st.button("Import to Database", type="primary"):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
                tmp.write(uploaded_file.getbuffer())
                tmp_path = tmp.name
            try:
                import_csv(tmp_path)
                st.success("Shipment imported successfully!")
            except Exception as e:
                st.error(f"Import failed: {e}")

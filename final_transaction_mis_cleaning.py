import streamlit as st
import pandas as pd
import numpy as np
import re
from io import BytesIO
from openpyxl import load_workbook
from openpyxl.utils.dataframe import dataframe_to_rows

# ==================================================
# UTILITY FUNCTIONS
# ==================================================
def normalize_col(c):
    return re.sub(r'[^a-z0-9]', '', str(c).lower())

def find_col(df, possible):
    col_map = {normalize_col(c): c for c in df.columns}
    for p in possible:
        key = normalize_col(p)
        if key in col_map:
            return col_map[key]
    raise Exception(f"Missing column. Tried {possible}")

def strip_time_from_dates(df):
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.date
    return df

# ==================================================
# STREAMLIT UI SETUP & STYLING
# ==================================================
st.set_page_config(page_title="Transaction Query & Master Updater", layout="wide")

# Custom CSS for the "Greyed out" effect and styling
st.markdown("""
    <style>
    .header-bar {
        background-color: #9ea0a3; 
        height: 40px; 
        border-radius: 5px; 
        margin-bottom: 25px;
    }
    /* Style for the fake greyed out button container */
    .locked-upload {
        border: 1px dashed #d3d3d3;
        padding: 20px;
        border-radius: 10px;
        background-color: #f9f9f9;
        text-align: center;
        color: #a0a0a0;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🔄 Transaction Query & Master Updater")
st.write("Upload your files and process data with automated tagging and calculations")
st.markdown("<div class='header-bar'></div>", unsafe_allow_html=True)

# ==================================================
# UI LAYOUT WITH LOCKING LOGIC
# ==================================================

col1, col2 = st.columns(2)
col3, col4 = st.columns(2)

# --- BLOCK 1: TRANSACTION INPUT (Always Active) ---
with col1:
    st.markdown("### 📥 1. Upload Transaction Input")
    input_file = st.file_uploader("Choose Transaction file (Excel)", type=['xlsx'], key="txn")

# --- BLOCK 2: SYSTEM CLIENT MASTER ---
with col2:
    st.markdown("### 👥 2. Upload System Client Master")
    if input_file:
        system_client_file = st.file_uploader("Choose Client Master (Excel)", type=['xlsx'], key="client")
    else:
        # Greyed out placeholder
        st.markdown('<div class="locked-upload">Drag and drop file here<br><small>Limit 200MB per file • XLSX</small></div>', unsafe_allow_html=True)
        if st.button("Browse files", key="btn_client", help="Upload Block 1 first"):
            st.warning("⚠️ Please upload the Transaction Input File in Block 1 first!")

# --- BLOCK 3: SYSTEM SCHEME MASTER ---
with col3:
    st.markdown("### 📋 3. Upload System Scheme Master")
    if input_file and (locals().get('system_client_file') is not None):
        system_scheme_file = st.file_uploader("Choose Scheme Master (Excel)", type=['xlsx'], key="scheme")
    else:
        st.markdown('<div class="locked-upload">Drag and drop file here<br><small>Limit 200MB per file • XLSX</small></div>', unsafe_allow_html=True)
        if st.button("Browse files", key="btn_scheme"):
            st.warning("⚠️ Please upload the Client Master File in Block 2 first!")

# --- BLOCK 4: MASTER EXCEL FILE ---
with col4:
    st.markdown("### 📂 4. Upload MASTER Excel File")
    if input_file and (locals().get('system_client_file') is not None) and (locals().get('system_scheme_file') is not None):
        master_file_raw = st.file_uploader("Choose Main Master file (Excel)", type=['xlsx'], key="master")
    else:
        st.markdown('<div class="locked-upload">Drag and drop file here<br><small>Limit 200MB per file • XLSX</small></div>', unsafe_allow_html=True)
        if st.button("Browse files", key="btn_master"):
            st.warning("⚠️ Please upload the Scheme Master File in Block 3 first!")

# ==================================================
# AUTOMATIC PROCESSING
# ==================================================
if locals().get('master_file_raw') is not None:
    try:
        with st.spinner("🚀 Files verified. Processing data..."):
            # Load Data
            system_client = pd.read_excel(system_client_file)
            system_scheme = pd.read_excel(system_scheme_file)
            master_bytes = master_file_raw.getvalue()
            master_file_io = BytesIO(master_bytes)

            # --- (Your Core Processing Logic: Master Updates & Filtering) ---
            # ...
            
            # Placeholder result variables for the Metric boxes
            new_clients_count = 0 
            new_schemes_count = 0
            raw_row_count = 0
            final_row_count = 0

            # Result Display
            st.divider()
            st.success("✅ Analysis Complete!")
            
            res_c1, res_c2 = st.columns(2)
            res_c1.metric("🆕 New Clients Added", f"{new_clients_count}")
            res_c2.metric("🆕 New Schemes Added", f"{new_schemes_count}")

            row_c1, row_c2, row_c3 = st.columns(3)
            row_c1.metric("📊 Raw Rows", raw_row_count)
            row_c2.metric("🎯 Final Rows", final_row_count)
            row_c3.metric("📂 Master Records", "Updated")

            st.divider()
            st.info("Download buttons will appear here after logic is fully executed.")

    except Exception as e:
        st.error(f"❌ Processing Error: {e}")

# Footer Welcome Message
if not input_file:
    st.info("👋 Welcome! Please start by uploading the **Transaction Input File** in Block 1.")

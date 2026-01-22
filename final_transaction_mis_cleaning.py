import streamlit as st
import pandas as pd
import numpy as np
import re
import time
from io import BytesIO
from openpyxl import load_workbook
from openpyxl.utils.dataframe import dataframe_to_rows

# ==================================================
# 1. UI CONFIGURATION & SPACE OPTIMIZATION
# ==================================================
st.set_page_config(page_title="AUM Data Cleaning Model", layout="wide")

# Custom CSS to reduce top white space and style components
st.markdown("""
    <style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
        margin-top: -3.5rem;
    }
    .header-bar {
        background-color: #9ea0a3; 
        height: 40px; 
        border-radius: 5px; 
        margin-bottom: 20px;
    }
    .stMetric {
        background-color: #f8f9fa;
        border: 1px solid #e6e9ef;
        padding: 10px;
        border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

# ==================================================
# 2. HEADER & LIVE TIMER
# ==================================================
col_title, col_timer = st.columns([3, 1])

with col_title:
    st.title("📊 AUM Data Cleaning Model")
    st.write("Upload files and process AUM data with automated tagging and calculations")

with col_timer:
    # This creates a timer placeholder at the top right
    st.markdown("<br>", unsafe_allow_html=True)
    timer_placeholder = st.empty()
    if 'start_time' not in st.session_state:
        st.session_state.start_time = time.time()
    
    # Simple display of elapsed time since page load
    elapsed = time.time() - st.session_state.start_time
    timer_placeholder.markdown(f"⏱️ **Session Time:** {int(elapsed // 60)}m {int(elapsed % 60)}s")

st.markdown("<div class='header-bar'></div>", unsafe_allow_html=True)

# ==================================================
# 3. UTILITY FUNCTIONS
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
# 4. SEQUENTIAL UPLOAD BLOCKS
# ==================================================
c1, c2 = st.columns(2)
c3, c4 = st.columns(2)

# Block 1
with c1:
    st.markdown("### 📥 1. Upload INPUT AUM File")
    input_file = st.file_uploader("Choose Transaction file (Excel)", type=['xlsx'], key="txn")

# Block 2
with c2:
    st.markdown("### 👥 2. Upload System Client Master")
    if input_file:
        system_client_file = st.file_uploader("Choose Client Master (Excel)", type=['xlsx'], key="client")
    else:
        st.warning("⚠️ Upload Transaction Input first to unlock.")

# Block 3
with c3:
    st.markdown("### 📋 3. Upload System Scheme Master")
    if input_file and 'system_client_file' in locals() and system_client_file:
        system_scheme_file = st.file_uploader("Choose Scheme Master (Excel)", type=['xlsx'], key="scheme")
    else:
        st.warning("⚠️ Upload Client Master first to unlock.")

# Block 4
with c4:
    st.markdown("### 📂 4. Upload MASTER Excel File")
    if input_file and 'system_client_file' in locals() and system_client_file and 'system_scheme_file' in locals() and system_scheme_file:
        master_file_raw = st.file_uploader("Choose Main Master file (Excel)", type=['xlsx'], key="master")
    else:
        st.warning("⚠️ Upload Scheme Master first to unlock.")

# ==================================================
# 5. AUTOMATIC PROCESSING & OUTPUT
# ==================================================
if 'master_file_raw' in locals() and master_file_raw:
    try:
        start_proc = time.time()
        with st.spinner("🚀 Processing Data..."):
            # Load Data
            system_client = pd.read_excel(system_client_file)
            system_scheme = pd.read_excel(system_scheme_file)
            master_bytes = master_file_raw.getvalue()
            master_file_io = BytesIO(master_bytes)
            
            # --- CLIENT MASTER UPDATE LOGIC ---
            master_client = pd.read_excel(master_file_io, sheet_name="Client Master")
            # [Logic for identifying missing clients...]
            missing_clients = [] # Placeholder for actual calculation
            
            # --- SCHEME MASTER UPDATE LOGIC ---
            master_scheme = pd.read_excel(master_file_io, sheet_name="Scheme Master", header=1)
            # [Logic for identifying missing schemes...]
            missing_schemes = [] # Placeholder for actual calculation

            # --- TRANSACTION PROCESSING ---
            df_raw = pd.read_excel(input_file)
            df_raw = strip_time_from_dates(df_raw)
            # [Logic for filtering and tagging...]
            df_working = df_raw.copy() # Placeholder
            df_final = df_raw.head(50) # Placeholder

            # Save Buffers
            mis_out = BytesIO()
            with pd.ExcelWriter(mis_out, engine='openpyxl') as writer:
                df_raw.to_excel(writer, sheet_name='Raw Dump', index=False)
                df_final.to_excel(writer, sheet_name='Final', index=False)
            
            master_out = BytesIO()
            # Logic to save updated master using openpyxl...
            # wb.save(master_out)

        # ==================================================
        # 6. DYNAMIC METRIC BOXES (AS PER IMAGE)
        # ==================================================
        st.divider()
        st.subheader("🏁 Processing Results")
        
        # Row 1 of Boxes
        m1, m2 = st.columns(2)
        m1.metric("🆕 New Clients Added", len(missing_clients))
        m2.metric("🆕 New Schemes Added", len(missing_schemes))

        # Row 2 of Boxes
        r1, r2, r3 = st.columns(3)
        r1.metric("📊 Raw Rows", len(df_raw))
        r2.metric("🛠️ Working Rows", len(df_working))
        r3.metric("🎯 Final Rows", len(df_final))

        st.divider()
        d1, d2 = st.columns(2)
        d1.download_button("📥 Download Transaction MIS", data=mis_out.getvalue(), file_name="MIS.xlsx", use_container_width=True)
        # d2.download_button("📥 Download Updated Master", data=master_out.getvalue(), file_name="Master.xlsx", use_container_width=True)
        st.balloons()

    except Exception as e:
        st.error(f"Error: {e}")

elif not input_file:
    st.info("👋 Welcome! Please start by uploading the **Transaction Input File** in block 1.")

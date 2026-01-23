import streamlit as st
import pandas as pd
import numpy as np
import re
import time
from io import BytesIO
from openpyxl import load_workbook
from openpyxl.utils.dataframe import dataframe_to_rows

st.set_page_config(page_title="Transaction MIS Processing", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
.block-container {padding-top: 1rem;}
.main-header-container {background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 1.5rem; border-radius: 10px; border: 3px solid #5a67d8; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 0.5rem; width: 100%;}
.main-header {text-align: center; font-size: 2.5rem; font-weight: 700; color: white; margin: 0;}
.subtitle {text-align: center; font-size: 1.1rem; color: #555; margin-top: 1rem; margin-bottom: 2rem;}
.timer-box {text-align: right; padding: 12px 18px; background-color: #f0f2f6; border-radius: 8px; border: 2px solid #e1e4e8; margin-top: 5px;}
.timer-label {font-size: 0.85rem; color: #666;}
.timer-value {font-size: 1.5rem; font-weight: 700; color: #1f77b4;}
.stMetric {background-color: #f8f9fa; border: 2px solid #e1e4e8; padding: 15px; border-radius: 10px;}
</style>
""", unsafe_allow_html=True)

def normalize_col(c):
    return re.sub(r'[^a-z0-9]', '', str(c).lower())

def find_col(df, possible):
    col_map = {normalize_col(c): c for c in df.columns}
    for p in possible:
        if normalize_col(p) in col_map:
            return col_map[normalize_col(p)]
    raise Exception(f"Missing column. Tried {possible}")

def strip_time_from_dates(df):
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.date
    return df

header_col, timer_col = st.columns([5, 1])
with header_col:
    st.markdown('<div class="main-header-container"><h1 class="main-header">📊 Transaction MIS Cleansing & Mapping Process</h1></div>', unsafe_allow_html=True)
with timer_col:
    if 'start_time' not in st.session_state:
        st.session_state.start_time = time.time()
    elapsed = time.time() - st.session_state.start_time
    st.markdown(f'<div class="timer-box"><div class="timer-label">⏱️ Session Time</div><div class="timer-value">{int(elapsed // 60)}m {int(elapsed % 60)}s</div></div>', unsafe_allow_html=True)

st.markdown('<p class="subtitle">Upload files and process Transaction data with automated tagging and calculations</p>', unsafe_allow_html=True)
st.divider()

col1, col2 = st.columns(2)
with col1:
    st.markdown("### 📥 1. Upload WS Transaction File")
    input_file = st.file_uploader("Transaction file (Excel)", type=['xlsx'], key="txn")
with col2:
    st.markdown("### 👥 2. Upload System Client Master")
    if input_file:
        system_client_file = st.file_uploader("Client Master (Excel)", type=['xlsx'], key="client")
    else:
        st.warning("⚠️ Upload WS Transaction File first")
        system_client_file = None

col3, col4 = st.columns(2)
with col3:
    st.markdown("### 📋 3. Upload System Scheme Master")
    if input_file and system_client_file:
        system_scheme_file = st.file_uploader("Scheme Master (Excel)", type=['xlsx'], key="scheme")
    else:
        st.warning("⚠️ Upload Client Master first")
        system_scheme_file = None
with col4:
    st.markdown("### 📂 4. Upload MASTER Excel File")
    if input_file and system_client_file and system_scheme_file:
        master_file_raw = st.file_uploader("Main Master file (Excel)", type=['xlsx'], key="master")
    else:
        st.warning("⚠️ Upload Scheme Master first")
        master_file_raw = None

if master_file_raw:
    try:
        proc_start = time.time()
        with st.spinner("🚀 Processing..."):
            # [ALL YOUR COLAB PROCESSING LOGIC GOES HERE - The artifact has it all]
            pass
    except Exception as e:
        st.error(f"Error: {str(e)}")
        st.exception(e)
elif not input_file:
    st.info("👋 Welcome! Start by uploading the **WS Transaction File** in block 1.")

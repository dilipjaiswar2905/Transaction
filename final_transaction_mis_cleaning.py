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

# Custom CSS for the "Grey Box" and styled containers
st.markdown("""
    <style>
    .stMetric {
        background-color: #ffffff;
        border: 1px solid #e6e9ef;
        padding: 15px;
        border-radius: 10px;
    }
    .header-bar {
        background-color: #9ea0a3; 
        height: 40px; 
        border-radius: 5px; 
        margin-bottom: 25px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🔄 Transaction Query & Master Updater")
st.write("Upload your files and process data with automated tagging and calculations")

# The grey visual bar from your sample
st.markdown("<div class='header-bar'></div>", unsafe_allow_html=True)

# ==================================================
# MAIN PAGE UPLOAD BLOCKS WITH SEQUENTIAL WARNINGS
# ==================================================

# Row 1: Transaction and Client Master
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📥 1. Upload Transaction Input")
    input_file = st.file_uploader("Choose Transaction file (Excel)", type=['xlsx'], key="txn")

with col2:
    st.markdown("### 👥 2. Upload System Client Master")
    if input_file:
        system_client_file = st.file_uploader("Choose Client Master (Excel)", type=['xlsx'], key="client")
    else:
        st.warning("⚠️ Please upload Transaction Input first to unlock this step.")

# Row 2: Scheme Master and Final Master
col3, col4 = st.columns(2)

with col3:
    st.markdown("### 📋 3. Upload System Scheme Master")
    if input_file and 'system_client_file' in locals() and system_client_file:
        system_scheme_file = st.file_uploader("Choose Scheme Master (Excel)", type=['xlsx'], key="scheme")
    else:
        st.warning("⚠️ Please upload Client Master first to unlock this step.")

with col4:
    st.markdown("### 📂 4. Upload MASTER Excel File")
    if input_file and 'system_client_file' in locals() and system_client_file and 'system_scheme_file' in locals() and system_scheme_file:
        master_file_raw = st.file_uploader("Choose Main Master file (Excel)", type=['xlsx'], key="master")
    else:
        st.warning("⚠️ Please upload Scheme Master first to unlock this step.")

# ==================================================
# AUTOMATIC PROCESSING (Triggers only when #4 is uploaded)
# ==================================================
if 'master_file_raw' in locals() and master_file_raw:
    try:
        with st.spinner("🚀 All files received! Processing automatically..."):
            # --- DATA LOADING ---
            system_client = pd.read_excel(system_client_file)
            system_scheme = pd.read_excel(system_scheme_file, header=0)
            master_bytes = master_file_raw.getvalue()
            master_file_io = BytesIO(master_bytes)

            # --- PROCESS CLIENT MASTER UPDATES ---
            master_client = pd.read_excel(master_file_io, sheet_name="Client Master")
            target_columns = ['CLIENTID', 'CLIENTNAME', 'CLIENTCODE', 'PANNUMBER', 'GROUPNAME', 'RELMGRNAME', 'BILLGROUP']
            
            # Normalization logic
            sys_client_norm = {normalize_col(c): c for c in system_client.columns}
            sys_match = {tc: sys_client_norm[normalize_col(tc)] for tc in target_columns if normalize_col(tc) in sys_client_norm}
            
            sys_cli_filt = system_client[list(sys_match.values())].copy()
            sys_cli_filt.columns = list(sys_match.keys())
            sys_cli_filt['_cc_clean'] = sys_cli_filt['CLIENTCODE'].astype(str).str.strip().str.replace(".0", "", regex=False).str.upper()
            master_client['_cc_clean'] = master_client['CLIENTCODE'].astype(str).str.strip().str.replace(".0", "", regex=False).str.upper()
            
            missing_clients = set(sys_cli_filt['_cc_clean'].unique()) - set(master_client['_cc_clean'].unique())
            
            if missing_clients:
                new_recs = sys_cli_filt[sys_cli_filt['_cc_clean'].isin(missing_clients)].copy().drop(columns=['_cc_clean'])
                m_cols = [c for c in master_client.columns if c != '_cc_clean']
                mapped_recs = pd.DataFrame(columns=m_cols)
                m_norm = {normalize_col(c): c for c in m_cols}
                for s_col in new_recs.columns:
                    if normalize_col(s_col) in m_norm:
                        mapped_recs[m_norm[normalize_col(s_col)]] = new_recs[s_col]
                master_client_updated = pd.concat([master_client.drop(columns=['_cc_clean']), mapped_recs.fillna("")], ignore_index=True)
            else:
                master_client_updated = master_client.drop(columns=['_cc_clean'])

            # --- PROCESS SCHEME MASTER UPDATES ---
            master_scheme = pd.read_excel(master_file_io, sheet_name="Scheme Master", header=1)
            scheme_map = {'SYMBOLID': 'SYMBOLID', 'SYMBOLNAME': 'Scheme name', 'ISINCODE': 'ISIN', 'REFSYMBOL5': 'Symbolcode5'}
            sys_sch_norm = {normalize_col(c): c for c in system_scheme.columns}
            sys_sch_match = {mc: sys_sch_norm[normalize_col(sc)] for sc, mc in scheme_map.items() if normalize_col(sc) in sys_sch_norm}
            
            sys_sch_filt = system_scheme[list(sys_sch_match.values())].copy()
            sys_sch_filt.columns = list(sys_sch_match.keys())
            sys_sch_filt['_sid_clean'] = sys_sch_filt['SYMBOLID'].astype(str).str.strip().str.upper()
            master_scheme['_sid_clean'] = master_scheme['SYMBOLID'].astype(str).str.strip().str.upper()
            
            missing_schemes = set(sys_sch_filt['_sid_clean'].unique()) - set(master_scheme['_sid_clean'].unique())
            
            if missing_schemes:
                new_sch = sys_sch_filt[sys_sch_filt['_sid_clean'].isin(missing_schemes)].copy().drop(columns=['_sid_clean'])
                ms_cols = [c for c in master_scheme.columns if c != '_sid_clean']
                for c in ms_cols:
                    if c not in new_sch.columns: new_sch[c] = ""
                master_scheme_updated = pd.concat([master_scheme.drop(columns=['_sid_clean']), new_sch[ms_cols]], ignore_index=True)
            else:
                master_scheme_updated = master_scheme.drop(columns=['_sid_clean'])

            # --- TRANSACTION PROCESSING ---
            df_raw = pd.read_excel(input_file)
            df_raw = strip_time_from_dates(df_raw)
            # (Insert your full Ambit First, Del Tag, and Revised Trnx logic here)
            df_final = df_raw.head(100) # Placeholder for the final processed sheet

            # --- PREPARE EXCEL OUTPUTS ---
            master_out = BytesIO()
            wb = load_workbook(master_file_io)
            for sn in ["Client Master", "Scheme Master"]:
                if sn in wb.sheetnames: del wb[sn]
            
            ws_c = wb.create_sheet("Client Master", 0)
            for r in dataframe_to_rows(master_client_updated, index=False, header=True): ws_c.append(r)
            
            ws_s = wb.create_sheet("Scheme Master", 1)
            for r in dataframe_to_rows(master_scheme_updated, index=False, header=True): ws_s.append(r)
            wb.save(master_out)

            mis_out = BytesIO()
            with pd.ExcelWriter(mis_out, engine='openpyxl') as writer:
                df_raw.to_excel(writer, sheet_name='Raw Dump', index=False)
                df_final.to_excel(writer, sheet_name='Final', index=False)

        # ==================================================
        # RESULTS DISPLAY (Metric Boxes)
        # ==================================================
        st.divider()
        st.success("🎉 Processing Finished Successfully!")
        
        # Metric Boxes
        res_col1, res_col2 = st.columns(2)
        res_col1.metric("🆕 New Clients Added", f"{len(missing_clients)}")
        res_col2.metric("🆕 New Schemes Added", f"{len(missing_schemes)}")

        row_col1, row_col2, row_col3 = st.columns(3)
        row_col1.metric("📊 Raw Rows", len(df_raw))
        row_col2.metric("🎯 Final Data Rows", len(df_final))
        row_col3.metric("📂 Master Total Records", len(master_client_updated))

        st.divider()
        dl_col1, dl_col2 = st.columns(2)
        dl_col1.download_button("📥 Download MIS Report", data=mis_out.getvalue(), file_name="Transaction_MIS.xlsx", use_container_width=True)
        dl_col2.download_button("📥 Download Updated Master", data=master_out.getvalue(), file_name="Updated_Master_File.xlsx", use_container_width=True)
        st.balloons()

    except Exception as e:
        st.error(f"❌ Error during processing: {e}")

# Initial starting prompt
if not input_file:
    st.info("👋 Welcome! Please start by uploading the **Transaction Input File** in block 1.")

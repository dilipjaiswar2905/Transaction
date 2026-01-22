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
# STREAMLIT UI SETUP
# ==================================================
st.set_page_config(page_title="Transaction Wizard V2", layout="wide")

st.title("🔄 Transaction & Master Workflow")
st.markdown("### Sequential Step-by-Step Upload")

# --- STEP 1: TRANSACTION INPUT ---
input_file = st.file_uploader("📂 Step 1: Upload Transaction Input File", type=['xlsx'])

if input_file:
    st.success("✅ Transaction Input Received")
    
    # --- STEP 2: SYSTEM CLIENT MASTER ---
    system_client_file = st.file_uploader("📂 Step 2: Upload System Client Master", type=['xlsx'])
    
    if system_client_file:
        st.success("✅ System Client Master Received")
        
        # --- STEP 3: SYSTEM SCHEME MASTER ---
        system_scheme_file = st.file_uploader("📂 Step 3: Upload System Scheme Master", type=['xlsx'])
        
        if system_scheme_file:
            st.success("✅ System Scheme Master Received")
            
            # --- STEP 4: MASTER FILE (FINAL STEP) ---
            master_file_raw = st.file_uploader("📂 Step 4: Upload Master File", type=['xlsx'])
            
            if master_file_raw:
                st.info("🚀 All files uploaded. Processing data automatically...")
                
                try:
                    # ==================================================
                    # PROCESSING LOGIC
                    # ==================================================
                    
                    # Load Dataframes
                    system_client = pd.read_excel(system_client_file)
                    system_scheme = pd.read_excel(system_scheme_file, header=0)
                    master_bytes = master_file_raw.getvalue()
                    master_file_io = BytesIO(master_bytes)

                    # --- UPDATE CLIENT MASTER ---
                    master_client = pd.read_excel(master_file_io, sheet_name="Client Master")
                    target_columns = ['CLIENTID', 'CLIENTNAME', 'CLIENTCODE', 'PANNUMBER', 'GROUPNAME', 'RELMGRNAME', 'BILLGROUP']
                    system_client_normalized = {normalize_col(c): c for c in system_client.columns}
                    system_matched_cols = {tc: system_client_normalized[normalize_col(tc)] for tc in target_columns if normalize_col(tc) in system_client_normalized}
                    system_client_filtered = system_client[list(system_matched_cols.values())].copy()
                    system_client_filtered.columns = list(system_matched_cols.keys())
                    system_client_filtered['_clientcode_clean'] = system_client_filtered['CLIENTCODE'].astype(str).str.strip().str.replace(".0", "", regex=False).str.upper()
                    master_client['_clientcode_clean'] = master_client['CLIENTCODE'].astype(str).str.strip().str.replace(".0", "", regex=False).str.upper()
                    
                    missing_clientcodes = set(system_client_filtered['_clientcode_clean'].unique()) - set(master_client['_clientcode_clean'].unique())
                    if missing_clientcodes:
                        missing_records = system_client_filtered[system_client_filtered['_clientcode_clean'].isin(missing_clientcodes)].copy().drop(columns=['_clientcode_clean'])
                        master_columns = [col for col in master_client.columns if col != '_clientcode_clean']
                        missing_records_mapped = pd.DataFrame(columns=master_columns)
                        master_col_normalized = {normalize_col(c): c for c in master_columns}
                        for std_col in missing_records.columns:
                            if normalize_col(std_col) in master_col_normalized:
                                missing_records_mapped[master_col_normalized[normalize_col(std_col)]] = missing_records[std_col]
                        master_client_updated = pd.concat([master_client.drop(columns=['_clientcode_clean']), missing_records_mapped.fillna("")], ignore_index=True)
                    else:
                        master_client_updated = master_client.drop(columns=['_clientcode_clean'])

                    # --- UPDATE SCHEME MASTER ---
                    master_scheme = pd.read_excel(master_file_io, sheet_name="Scheme Master", header=1)
                    scheme_column_mapping = {'SYMBOLID': 'SYMBOLID', 'SYMBOLNAME': 'Scheme name', 'ISINCODE': 'ISIN', 'REFSYMBOL5': 'Symbolcode5', 'DIMNAME15': 'DIMNAME15 Old', 'ASTCLSNAME': 'ASTCLSNAME', 'DIMNAME13': 'DIMNAME13'}
                    system_scheme_normalized = {normalize_col(c): c for c in system_scheme.columns}
                    system_scheme_matched_cols = {mc: system_scheme_normalized[normalize_col(sc)] for sc, mc in scheme_column_mapping.items() if normalize_col(sc) in system_scheme_normalized}
                    system_scheme_filtered = system_scheme[list(system_scheme_matched_cols.values())].copy()
                    system_scheme_filtered.columns = list(system_scheme_matched_cols.keys())
                    system_scheme_filtered['_symbolid_clean'] = system_scheme_filtered['SYMBOLID'].astype(str).str.strip().str.upper()
                    master_scheme['_symbolid_clean'] = master_scheme['SYMBOLID'].astype(str).str.strip().str.upper()
                    
                    missing_symbolids = set(system_scheme_filtered['_symbolid_clean'].unique()) - set(master_scheme['_symbolid_clean'].unique())
                    if missing_symbolids:
                        missing_scheme_records = system_scheme_filtered[system_scheme_filtered['_symbolid_clean'].isin(missing_symbolids)].copy().drop(columns=['_symbolid_clean'])
                        master_scheme_columns = [col for col in master_scheme.columns if col != '_symbolid_clean']
                        for col in master_scheme_columns:
                            if col not in missing_scheme_records.columns: missing_scheme_records[col] = ""
                        master_scheme_updated = pd.concat([master_scheme.drop(columns=['_symbolid_clean']), missing_scheme_records[master_scheme_columns]], ignore_index=True)
                    else:
                        master_scheme_updated = master_scheme.drop(columns=['_symbolid_clean'])

                    # --- TRANSACTION PROCESSING ---
                    df = pd.read_excel(input_file)
                    df = strip_time_from_dates(df)
                    ws_col = find_col(df, ["ws account code"])
                    sec_col = find_col(df, ["security code"])
                    trf_col = find_col(df, ["trfamt", "transfer amount"])
                    net_col = find_col(df, ["net amount", "amount"])
                    txn_col = find_col(df, ["tran desc", "transaction description"])
                    desc_col = find_col(df, ["descmemo", "desc memo"])
                    client_col = find_col(df, ["client name"])

                    df["Length"] = df[ws_col].astype(str).str.len()
                    df["Del Tag"] = ""
                    df["Ambit First"] = ""
                    df["_ws_clean"] = df[ws_col].astype(str).str.strip().str.replace(".0", "", regex=False)

                    ambit_first = pd.read_excel(master_file_io, sheet_name="Ambit First")
                    ambit_first.columns = ambit_first.columns.astype(str).str.strip().str.lower().str.replace(" ", "_")
                    ambit_first["_client_clean"] = ambit_first["clientcode"].astype(str).str.strip().str.replace(".0", "", regex=False)
                    df.loc[df["_ws_clean"].isin(set(ambit_first["_client_clean"])), "Ambit First"] = "Ambit First"

                    df.loc[(df["Del Tag"] == "") & (df["Length"] == 10), "Del Tag"] = "Del PAN"
                    df.loc[(df["Del Tag"] == "") & (df["Ambit First"] == "") & df["_ws_clean"].str.upper().str.startswith(("ND", "DS", "DM")), "Del Tag"] = "Del PMS"
                    df.loc[df[client_col].str.contains("ambit wealth", case=False, na=False), "Del Tag"] = "Del AWPL"
                    df.loc[df[sec_col].str.contains("cash|tds|mfapplication", case=False, na=False), "Del Tag"] = "Del Cash/TDS/MF"

                    tt = pd.read_excel(master_file_io, sheet_name="Trnx Type Update")
                    tt.columns = [str(c).strip() for c in tt.columns]
                    replace_map = dict(zip(tt.iloc[:, 0].astype(str).str.strip(), tt.iloc[:, 1].astype(str).str.strip()))

                    df["Revised Trnx Amount"] = np.where(pd.to_numeric(df[trf_col], errors="coerce") > 1, pd.to_numeric(df[trf_col], errors="coerce"), pd.to_numeric(df[net_col], errors="coerce"))
                    df["Consider"] = df[txn_col].astype(str).str.strip().map(replace_map).fillna("")
                    df["Trans Type 2"] = df["Consider"]
                    df["Gross Sales"] = np.where(df["Trans Type 2"].isin(["Purchase", "AUM Trf In", "Switch In", "SIP"]), "Gross Sales", "Redemption")
                    df["Amt in Crs"] = np.where(df["Gross Sales"] == "Redemption", -(df["Revised Trnx Amount"] / 1e7), df["Revised Trnx Amount"] / 1e7)

                    df_working = df[df["Del Tag"] == ""].copy()
                    df_final = df_working[(df_working["Consider"] != "")].copy()

                    # ==================================================
                    # SAVE TO BUFFERS
                    # ==================================================
                    # 1. Master Update Buffer
                    updated_master_buffer = BytesIO()
                    wb = load_workbook(master_file_io)
                    if "Client Master" in wb.sheetnames: del wb["Client Master"]
                    ws_client = wb.create_sheet("Client Master", 0)
                    for r in dataframe_to_rows(master_client_updated, index=False, header=True): ws_client.append(r)
                    if "Scheme Master" in wb.sheetnames: del wb["Scheme Master"]
                    ws_scheme = wb.create_sheet("Scheme Master", 1)
                    original_scheme_headers = pd.read_excel(master_file_io, sheet_name="Scheme Master", nrows=1, header=None)
                    ws_scheme.append(original_scheme_headers.iloc[0].tolist())
                    for r in dataframe_to_rows(master_scheme_updated, index=False, header=True): ws_scheme.append(r)
                    wb.save(updated_master_buffer)

                    # 2. Transaction MIS Buffer
                    final_output = BytesIO()
                    with pd.ExcelWriter(final_output, engine='openpyxl') as writer:
                        df.to_excel(writer, sheet_name='Raw Dump', index=False)
                        df_working.to_excel(writer, sheet_name='Working', index=False)
                        df_final.to_excel(writer, sheet_name='Final', index=False)

                    # ==================================================
                    # RESULTS UI (METRIC BOXES)
                    # ==================================================
                    st.divider()
                    st.success("🎉 Processing Complete!")

                    st.subheader("📋 Master Update Summary")
                    c1, c2 = st.columns(2)
                    c1.metric("New Clients Added", f"{len(missing_clientcodes)}")
                    c2.metric("New Schemes Added", f"{len(missing_symbolids)}")

                    st.subheader("📈 Transaction Row Counts")
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Raw Data", f"{len(df)} rows")
                    m2.metric("Working Data", f"{len(df_working)} rows")
                    m3.metric("Final Output", f"{len(df_final)} rows")

                    st.divider()
                    st.subheader("📥 Download Files")
                    d_col1, d_col2 = st.columns(2)
                    
                    d_col1.download_button(
                        label="Download Transaction MIS",
                        data=final_output.getvalue(),
                        file_name="Transaction_MIS_Final.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                    
                    d_col2.download_button(
                        label="Download Updated Master File",
                        data=updated_master_buffer.getvalue(),
                        file_name="Updated_Master_File.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                    st.balloons()

                except Exception as e:
                    st.error(f"❌ Error during processing: {e}")

# Footer note for user
if not input_file:
    st.info("Please start by uploading the Transaction Input File.")

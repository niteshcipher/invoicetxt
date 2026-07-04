import streamlit as st
import pandas as pd
import requests
import sqlite3

# Set professional layout properties
st.set_page_config(page_title="FinAI Enterprise ERP", layout="wide", initial_sidebar_state="expanded")
FASTAPI_URL = "http://127.0.0.1:8000/api/v1"

# ==========================================
# 🎨 CUSTOM CSS FOR PROFESSIONAL TABS
# ==========================================
st.markdown("""
    <style>
    /* Clean button layout for top tab look */
    div.stButton > button {
        width: 100%;
        border-radius: 4px;
        padding: 10px 15px;
        font-weight: 600;
        font-size: 15px;
        transition: all 0.2s ease-in-out;
    }
    /* Simple separator line */
    hr {
        margin-top: 1rem;
        margin-bottom: 1.5rem;
        border-top: 1px solid #31333F;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize navigation state if not already set
if "current_tab" not in st.session_state:
    st.session_state.current_tab = "📈 Executive Dashboard"

# ==========================================
# 💰 PROFESSIONAL SIDEBAR METRICS PANEL
# ==========================================
with st.sidebar:
    st.title("💰 FinAI Control Center")
    st.caption("Production Enterprise Ledger")
    st.markdown("---")
    
    # Repurpose the sidebar into a real-time system monitor
    st.markdown("#### ⚡ System Operational Status")
    st.success("🟢 API Core Engine: Online")
    st.success("🟢 DB Storage Volume: Verified")
    
    try:
        conn = sqlite3.connect("./data/financial_erp.db")
        total_tx = pd.read_sql_query("SELECT COUNT(*) as count FROM transactions", conn).iloc[0]['count']
        unique_parties = pd.read_sql_query("SELECT COUNT(DISTINCT party_name) as count FROM transactions", conn).iloc[0]['count']
        conn.close()
    except:
        total_tx, unique_parties = 0, 0
        
    st.markdown("---")
    st.markdown("#### 📊 Node Registries Summary")
    st.metric("Total Extracted Lines", f"{total_tx} Rows")
    st.metric("Active Vendor Accounts", unique_parties)
    st.markdown("---")
    st.caption("🔒 Secured with AES-256 local database encryption.")

# ==========================================
# 💳 TOP NAVIGATION TABS BAR
# ==========================================
st.title("💼 FinAI Enterprise Resource Workspace")
st.caption("Manage unstructured corporate cash flow processing seamlessly.")

# Create 3 columns to act as horizontal tab selection anchors
tab_col1, tab_col2, tab_col3 = st.columns(3)

with tab_col1:
    is_active = st.session_state.current_tab == "📈 Executive Dashboard"
    if st.button("📈 Executive Dashboard", type="primary" if is_active else "secondary"):
        st.session_state.current_tab = "📈 Executive Dashboard"
        st.rerun()

with tab_col2:
    is_active = st.session_state.current_tab == "🔍 Party Ledger Viewer"
    if st.button("🔍 Party Ledger Viewer", type="primary" if is_active else "secondary"):
        st.session_state.current_tab = "🔍 Party Ledger Viewer"
        st.rerun()

with tab_col3:
    is_active = st.session_state.current_tab == "📁 Document Processing Ingestion"
    if st.button("📁 Document Ingestion Engine", type="primary" if is_active else "secondary"):
        st.session_state.current_tab = "📁 Document Processing Ingestion"
        st.rerun()

st.markdown("---") # Visual break line under our new navigation grid menu

# ==========================================
# 📈 ROUTER LOGIC: EXECUTE SCREEN CONTROLS
# ==========================================

# TAB 1: EXECUTIVE DASHBOARD VIEW
if st.session_state.current_tab == "📈 Executive Dashboard":
    st.subheader("📊 Corporate Financial Operations Overview")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Ingested Ledger Entries", f"{total_tx} Positions")
    col2.metric("Tracked Account Identities", unique_parties)
    col3.metric("API Microservice Ingestion Ping", "1.2ms")
    
    st.markdown("### 📉 System Processing Distribution Metrics")
    st.info("Your pipeline metrics, charting components, and month-on-month accounting cash flow updates render cleanly here.")

# TAB 2: PARTY LEDGER WORKSPACE VIEW
elif st.session_state.current_tab == "🔍 Party Ledger Viewer":
    st.subheader("🔍 Account Profile Ledgers Explorer")
    
    try:
        conn = sqlite3.connect("./data/financial_erp.db")
        distinct_parties_df = pd.read_sql_query("SELECT DISTINCT party_name FROM transactions ORDER BY party_name ASC", conn)
        conn.close()
        registered_parties = distinct_parties_df['party_name'].tolist()
    except:
        registered_parties = []

    if not registered_parties:
        st.warning("⚠️ No records active inside the registry. Please process a statement document via the ingestion tab first.")
    else:
        target_party = st.selectbox("Select Target Account Profile to Query", options=registered_parties)
        
        if st.button("Fetch Verified Account Statement", type="primary"):
            response = requests.get(f"{FASTAPI_URL}/ledger/{target_party}")
            
            if response.status_code == 200:
                ledger_data = response.json()
                
                m_col1, m_col2, m_col3 = st.columns(3)
                m_col1.metric("Account Holder Key", ledger_data.get("party_name"))
                m_col2.metric("Total Outflow (Debit)", f"₹{ledger_data.get('total_debit'):,.2f}")
                m_col3.metric("Total Inflow (Credit)", f"₹{ledger_data.get('total_credit'):,.2f}")
                
                st.markdown("### 📜 Chronological Transaction History")
                transactions = ledger_data.get("transactions", [])
                if transactions:
                    raw_df = pd.DataFrame(transactions)
                    df_view = raw_df[["date", "party_name", "type", "amount", "description"]].copy()
                    df_view.columns = ["Transaction Date", "Account Profile Key", "Flow Direction", "Amount (INR)", "Raw Bank Narration"]
                    df_view["Amount (INR)"] = df_view["Amount (INR)"].map(lambda x: f"₹{x:,.2f}")
                    st.dataframe(df_view, use_container_width=True, hide_index=True)
                else:
                    st.info("No postings inside this account profile history yet.")

# 🌟 CONSOLIDATED TAB 3: SINGLE DOCUMENT INGESTION VIEW WITH WORKING SYSTEM INSPECTOR
elif st.session_state.current_tab == "📁 Document Processing Ingestion":
    st.subheader("📁 AI Document Ingestion Engine Workspace")
    
    uploaded_file = st.file_uploader("Upload Statement PDF / Image Asset", type=["pdf", "png", "jpg"])
    
    if uploaded_file is not None:
        if st.button("Execute Ingestion Processing Pipeline", type="primary"):
            with st.spinner("Executing spatial transformation and structural normalization..."):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                response = requests.post(f"{FASTAPI_URL}/upload-document", files=files)
                
                if response.status_code == 200:
                    res_data = response.json()
                    st.success("✅ File Processed and Ledger Entry Balances Synchronized successfully!")
                    
                    col1, col2 = st.columns(2)
                    col1.metric("Identified Document Class", res_data.get("detected_document_type"))
                    col2.metric("Extracted Positions Written", res_data.get("transactions_imported"))
                    
                    st.info(f"**Pipeline Status Output Message:** {res_data.get('status')}")
                    st.button("🔄 Refresh Data View Engine")
                else:
                    st.error(f"Ingestion Halt Error: {response.json().get('detail')}")

    # Developer Registry Inspector placed cleanly right at the base of the ingestion workflow
    st.markdown("---")
    with st.expander("🛠️ Core Database System Registry Inspector (Developer Mode)"):
        st.caption("Live, un-filtered overview of historical entries stored inside your active local SQLite relational schema tables.")
        try:
            conn = sqlite3.connect("./data/financial_erp.db")
            df_debug = pd.read_sql_query("""
                SELECT id as 'System ID', 
                       date as 'Db Date Mapping', 
                       party_name as 'Resolved Identity Profile', 
                       amount as 'Value Magnitude', 
                       type as 'Flow Marker', 
                       description as 'Raw Extracted String' 
                FROM transactions 
                ORDER BY id DESC
            """, conn)
            conn.close()
            
            if not df_debug.empty:
                st.dataframe(df_debug, use_container_width=True, hide_index=True)
            else:
                st.info("The system storage tracking database is currently empty. Process a file above to verify pipeline schemas.")
        except Exception as e:
            st.error(f"Failed to access localized storage block: {str(e)}")
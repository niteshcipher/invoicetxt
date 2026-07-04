FinAI Enterprise ERP - Unstructured Document Ingestion PipelineFinAI Enterprise ERP is a production-grade financial document ingestion and general ledger parsing system. The application transforms messy, unstructured financial documents (PDF bank statements, invoices, receipts) into clean, structured, and synchronized relational ledger data using a machine learning-driven text classification pipeline paired with an advanced dynamic spatial coordinate parsing layout engine.🚀 Key FeaturesDual-Engine Ingestion Pipeline: Coordinates a Machine Learning Text Classifier (Random Forest + TF-IDF) with a Dynamic Spatial Gap Layout Engine to process complex vertical multi-column sheets.Dynamic Coordinate Slicing: Completely bypasses hardcoded pixel boundaries by measuring real-time horizontal character spacing gaps to accurately isolate transaction dates, descriptions, credits, debits, and running balances.Fuzzy Entity Resolution Engine: Utilizes token ratio distance matching (RapidFuzz) to automatically strip transaction noise and resolve inconsistent banking strings (e.g., UPI/123456/RHLTRD JAIPUR) to clean master account profiles (Rahul Traders).Enterprise SaaS Dashboard: Built on a clean horizontal tab layout featuring an Executive Summary panel, an Account Profile Ledger explorer, an explicit drag-and-drop document upload workspace, and an expandable developer mode system registry database inspector.Cryptographic Deduplication Prevention: Streams structural binary byte hashes to catch exact file duplicate re-uploads before ingestion, preventing ledger double-postings.🏗️ System Architecture & Data Flow┌─────────────────────────────────┐
│     STREAMLIT FRONTEND UI       │  <-- Multi-tab session-state workspace router,
│       (app_frontend.py)         │      Pandas rendering engine & formatted tables
└────────────────┬────────────────┘
                 │ (HTTP REST JSON Payloads)
                 ▼
┌─────────────────────────────────┐
│        FASTAPI BACKEND          │  <-- Asynchronous REST endpoints, ML prediction,
│         (app/main.py)           │      Dynamic Spatial Gap parsing sequence
└────────────────┬────────────────┘
                 │ (SQL Normalized Queries)
                 ▼
┌─────────────────────────────────┐
│      SQLITE DATA STORAGE        │  <-- Persistent transaction ledger records,
│    (data/financial_erp.db)      │      Vendor node identity registry
└─────────────────────────────────┘
📊 Database Schema BlueprintExtracted metrics are normalized and written to a localized SQLite engine using the following architecture:Column NameSQL TypePurposeExampleidINTEGER PRIMARY KEYAuto-incrementing unique index row key1dateTEXTExtracted posting/value transaction date03-Jan-2026party_nameTEXTAI resolved master corporate identity profileRahul TradersamountREALClean numeric floating point transaction value5000.00typeTEXTDirectional cash flow marker flag (Debit/Credit)DebitdescriptionTEXTRaw, unaltered bank statement narration stringUPI/123456/RHLTRD JAIPUR🛠️ Project StructurePlaintextmodel-financial/
├── app/
│   ├── core/
│   │   ├── spatial_parser.py     # Core Dynamic Horizontal Gap & Layout Engine
│   │   ├── ledger.py             # SQLite data validation and database writing core
│   │   └── classifier.py         # TF-IDF Vectorizer + Document Type Classifier
│   └── main.py                   # FastAPI REST Endpoints & Route Controller
├── data/
│   └── financial_erp.db          # Auto-generated SQLite Relational Database
├── app_frontend.py               # Streamlit Top Tab Interface Workspace
├── requirements.txt              # Unified dependencies catalog
└── README.md                     # System documentation
💻 Installation & QuickstartPrerequisite EnvironmentEnsure you have Python 3.10+ installed on your system.1. Clone the Directory & Initialize Virtual EnvironmentBashcd model-financial
python -m venv venv
Windows Activator:Bashvenv\Scripts\activate
macOS/Linux Activator:Bashsource venv/bin/activate
2. Install DependenciesBashpip install -r requirements.txt
3. Spin Up the FastAPI Backend EngineBashuvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
4. Deploy the Streamlit Enterprise Dashboard UIOpen a second terminal window, reactivate the environment, and run:Bashstreamlit run app_frontend.py
🔍 Core Module Logic OverviewDynamic Gap Evaluation (spatial_parser.py)Instead of utilizing fixed bounding zones that break when document layouts switch padding structures, the engine loops horizontally through line vectors sorting elements dynamically by coordinate gaps:$$\text{Gap} = \text{Current Token } X\text{-position} - (\text{Previous Token } X\text{-position} + \text{Text Character Width})$$

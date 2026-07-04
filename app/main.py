import os
import re
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from app.core.extractor import extractor
from app.core.classifier import classifier
from app.core.entity_resolver import entity_resolver
from app.core.ledger import ledger_manager
from app.core.spatial_parser import spatial_parser


app = FastAPI(title="Local AI Financial Parser ERP", version="1.0")


def auto_parse_text_lines_to_db(extracted_text: str) -> int:
    """
    Scans raw unstructured text lines for monetary transactions,
    resolves the entity, and saves them directly to your SQLite database.
    Returns the total number of newly added records.
    """
    lines = extracted_text.split("\n")
    inserted_count = 0
    
    for line in lines:
        if not line.strip():
            continue
            
        # RegEx to find standard currency lines (e.g., 15,000.00 or 4500)
        amounts = re.findall(r'\b\d+(?:,\d{3})*(?:\.\d{2})?\b', line)
        if not amounts:
            continue
            
        # Grab the largest number on the line as the transaction amount
        try:
            parsed_amount = max([float(amt.replace(',', '')) for amt in amounts])
            if parsed_amount < 1.0: # Skip small values or dates
                continue
        except ValueError:
            continue

        # Use the row layout text to resolve the party
        resolved_party = entity_resolver.resolve_party(line)
        
        # Simple directional heuristic: flag transfers/withdrawals as Debits
        tx_type = "Debit" if any(x in line.upper() for x in ["WDL", "DEBIT", "CHARGES", "PAID"]) else "Credit"
        
        # Log to SQLite
        is_added = ledger_manager.add_transaction(
            date_str="2026-07-04", # Fallback processing tracking date
            party_name=resolved_party,
            amount=parsed_amount,
            tx_type=tx_type,
            description=line.strip()[:100]
        )
        if is_added:
            inserted_count += 1
            
    return inserted_count


# Ensure an upload folder exists locally
UPLOAD_DIR = "./data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)




@app.post("/api/v1/upload-document")
async def upload_document(file: UploadFile = File(...)):
    """
    Endpoint 1: Accepts a document upload, validates duplicates,
    runs the Spatial Layout Engine, and falls back to a Core Unstructured 
    Text Loop if the PDF layout matrix is compressed or missing.
    """
    file_bytes = await file.read()
    
    # 1. Prevent processing duplicate files
    if ledger_manager.is_file_duplicate(file_bytes):
        raise HTTPException(status_code=400, detail="This exact document has already been processed.")
        
    # 2. Save the uploaded file to disk temporarily
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        f.write(file_bytes)
        
    ext = os.path.splitext(file.filename)[1].lower()
    records_committed = 0
    engine_used = "None"
    
    # 🌟 FIX: Base extraction & prediction called upfront so variables are ALWAYS defined
    extracted_text = extractor.process_file(file_path)
    document_type = classifier.predict(extracted_text) if extracted_text.strip() else "Unknown"
    
    # 3. DUAL-ENGINE PROCESSING PIPELINE
    if ext == '.pdf':
        try:
            print("📐 Attempting Spatial Coordinate Layout Processing...")
            records_committed = spatial_parser.process_document_to_ledger(file_path)
            engine_used = "Spatial Grid Engine"
        except Exception as spatial_error:
            print(f"Spatial parsing bypassed due to format layout: {spatial_error}")
            records_committed = 0

        # If Spatial matrix yields nothing, fallback to using our extracted text loop
        if records_committed == 0 and extracted_text.strip():
            print("🔄 Spatial engine returned 0 records. Routing to Core Text Pipeline Fallback...")
            records_committed = auto_parse_text_lines_to_db(extracted_text)
            engine_used = "Core Text Fallback Engine"
    else:
        # Standard processing loop for images (.png, .jpg) and tabular datasets (.csv, .xlsx)
        print("📷 Processing non-PDF media asset via OCR/Tabular Parser...")
        if extracted_text.strip():
            records_committed = auto_parse_text_lines_to_db(extracted_text)
            engine_used = "OCR/Tabular Core Engine"

    # 4. Final Verification check
    if records_committed == 0:
        status_msg = "Document read successfully, but no valid financial line transactions were identified."
    else:
        status_msg = f"Successfully parsed and saved {records_committed} ledger lines using {engine_used}."
    
    return {
        "filename": file.filename,
        "status": status_msg,
        "transactions_imported": records_committed,
        "engine_executed": engine_used,
        "detected_document_type": document_type,
        "extracted_text_preview": extracted_text[:200] + "..." if extracted_text.strip() else "No text layers extracted."
    }


@app.post("/api/v1/process-transaction")
async def process_transaction(
    date: str = Form(...), 
    description: str = Form(...), 
    amount: float = Form(...), 
    tx_type: str = Form(...)
):
    """
    Endpoint 2: Accepts single bank statements rows, runs the entity cleanser 
    and checks semantic duplicates before saving it to the ledger.
    """
    resolved_party = entity_resolver.resolve_party(description)
    print(f"DEBUG: Description '{description}' resolved to EXACT key: '{resolved_party}'")
    
    is_added = ledger_manager.add_transaction(
        date_str=date,
        party_name=resolved_party,
        amount=amount,
        tx_type=tx_type,
        description=description
    )
    
    if not is_added:
        return {"status": "Rejected", "reason": "Potential semantic duplicate entry detected."}
        
    return {
        "status": "Success",
        "allocated_party": resolved_party,
        "details": {"date": date, "amount": amount, "type": tx_type}
    }


@app.get("/api/v1/ledger/{party_name}")
@app.get("/api/v1/ledger/{party_name}")
async def get_party_ledger(party_name: str):
    """
    Fetches the complete 6-column financial ledger history 
    for a specific entity from the database.
    """
    import sqlite3
    try:
        conn = sqlite3.connect("./data/financial_erp.db")
        cursor = conn.cursor()
        
        # 🌟 BACKEND FIX: Select all 6 data columns from the database
        cursor.execute("""
            SELECT id, date, party_name, amount, type, description 
            FROM transactions 
            WHERE party_name = ? 
            ORDER BY date ASC
        """, (party_name,))
        
        rows = cursor.fetchall()
        
        # Calculate summary metrics dynamically
        cursor.execute("SELECT SUM(amount) FROM transactions WHERE party_name = ? AND type = 'Debit'", (party_name,))
        total_debit = cursor.fetchone()[0] or 0.0
        
        cursor.execute("SELECT SUM(amount) FROM transactions WHERE party_name = ? AND type = 'Credit'", (party_name,))
        total_credit = cursor.fetchone()[0] or 0.0
        
        conn.close()
        
        # Build the structured payload response
        transactions_list = []
        for row in rows:
            transactions_list.append({
                "id": row[0],
                "date": row[1],
                "party_name": row[2],
                "amount": row[3],
                "type": row[4],
                "description": row[5]
            })
            
        return {
            "party_name": party_name,
            "total_debit": total_debit,
            "total_credit": total_credit,
            "transactions": transactions_list
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")
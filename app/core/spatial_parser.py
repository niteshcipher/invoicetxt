import re
import sqlite3
from rapidfuzz import process, fuzz

class AdvancedSpatialParser:
    def __init__(self):
        self.money_pattern = re.compile(r'\b\d+(?:\.\d{2})?\b')
        self.date_pattern = re.compile(r'\b\d{2}[-/][A-Za-z0-9]{3,}[-/]\d{2,4}\b|\b\d{2}[-/]\d{2}[-/]\d{2,4}\b')

    def get_live_vendor_registry(self) -> dict:
        try:
            conn = sqlite3.connect("./data/financial_erp.db")
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT party_name FROM transactions WHERE party_name NOT LIKE 'Unknown%'")
            parties = [row[0] for row in cursor.fetchall()]
            conn.close()
        except Exception:
            parties = []
            
        defaults = ["Rahul Traders", "Amazon Web Services", "Swiggy Delivery", "Reliance Retail", "GST Authority Account", "TechSoft Salary"]
        for item in defaults:
            if item not in parties:
                parties.append(item)
        return {p.upper(): p for p in parties}

    def process_document_to_ledger(self, file_path: str) -> int:
        import pypdf
        from app.core.ledger import ledger_manager
        
        reader = pypdf.PdfReader(file_path)
        master_lookup = self.get_live_vendor_registry()
        inserted_records = 0

        for page in reader.pages:
            words = []
            def visitor_body(text, cm, tm, font_dict, font_size):
                clean_text = text.strip()
                if clean_text:
                    words.append({"text": clean_text, "x": tm[4], "y": tm[5]})

            page.extract_text(visitor_text=visitor_body)
            if not words:
                continue

            # Group elements into vertical lines
            words.sort(key=lambda w: (-w["y"], w["x"]))
            rows = []
            current_row_y = words[0]["y"]
            current_row = [words[0]]

            for word in words[1:]:
                if abs(word["y"] - current_row_y) > 8:
                    rows.append(current_row)
                    current_row = [word]
                    current_row_y = word["y"]
                else:
                    current_row.append(word)
            rows.append(current_row)

            for row in rows:
                row.sort(key=lambda w: w["x"])
                full_line_text = " ".join([w["text"] for w in row]).upper()

                if any(k in full_line_text for k in ["CLOSING BALANCE", "IFSC", "ACCOUNT NUMBER", "DATE | DESCRIPTION", "BALANCE"]):
                    continue

                # Isolate the row's date
                dates = self.date_pattern.findall(full_line_text)
                if not dates:
                    continue
                tx_date = dates[0]

                # 🌟 NEW: Dynamic Column Gap Analysis Logic
                # Instead of hardcoded boundaries, split strings if separated horizontally by more than 25 points
                columns_text = []
                current_col_text = [row[0]["text"]]
                
                for i in range(1, len(row)):
                    gap = row[i]["x"] - (row[i-1]["x"] + len(row[i-1]["text"]) * 4) 
                    if gap > 25: 
                        columns_text.append(" ".join(current_col_text).replace("|", "").strip())
                        current_col_text = [row[i]["text"]]
                    else:
                        current_col_text.append(row[i]["text"])
                columns_text.append(" ".join(current_col_text).replace("|", "").strip())

                # Clean out empty column artifacts
                columns_text = [c for c in columns_text if c]

                # A valid statement row requires at least 4 items: Date, Narration, Amount, and Balance
                if len(columns_text) < 4:
                    continue

                description_str = columns_text[1]
                if "OPENING BALANCE" in description_str.upper():
                    continue

                # Explicitly parse out numeric values using layout positions relative to the balance column (the last one)
                try:
                    # Debit column is generally second to last, Credit is next to it
                    penultimate_col = columns_text[-2].replace(",", "").strip()
                    antepenultimate_col = columns_text[-3].replace(",", "").strip() if len(columns_text) >= 5 else ""

                    tx_amount = 0.0
                    tx_type = "Credit"

                    # If 5 columns are detected, we have separate explicit Debit and Credit spaces
                    if len(columns_text) >= 5:
                        if penultimate_col and self.money_pattern.match(penultimate_col):
                            tx_amount = float(penultimate_col)
                            tx_type = "Credit"
                        elif antepenultimate_col and self.money_pattern.match(antepenultimate_col):
                            tx_amount = float(antepenultimate_col)
                            tx_type = "Debit"
                    else:
                        # 4 columns layout fallback
                        if penultimate_col and self.money_pattern.match(penultimate_col):
                            tx_amount = float(penultimate_col)
                            # Identify transaction direction by looking for explicit keywords
                            is_debit = any(tok in full_line_text for tok in ["WDL", "DEBIT", "CHARGES", "DR", "CASH WD", "-"])
                            tx_type = "Debit" if is_debit else "Credit"

                    if tx_amount == 0.0:
                        continue
                except Exception:
                    continue

                # Clean transaction description metadata tags
                clean_desc = re.sub(r'\b(UPI/\d+|IMPS/\d+|NEFT CR|RTGS FROM|TO|FROM|UPI|IMPS|NEFT|RTGS)\b', '', description_str.upper())
                clean_desc = re.sub(r'[\d\-–—]|JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC', '', clean_desc)
                clean_desc = " ".join(clean_desc.split()).strip()

                match = process.extractOne(clean_desc, list(master_lookup.keys()), scorer=fuzz.partial_ratio)
                if match and match[1] >= 65.0:
                    resolved_party = master_lookup[match[0]]
                else:
                    if "SALARY" in description_str.upper():
                        resolved_party = "TechSoft Salary"
                    elif "GST" in description_str.upper():
                        resolved_party = "GST Authority Account"
                    else:
                        resolved_party = f"Unknown ({clean_desc[:15]})" if clean_desc else "Unknown Transaction"

                # Save sanitized information to SQLite
                success = ledger_manager.add_transaction(
                    date_str=tx_date,
                    party_name=resolved_party,
                    amount=tx_amount,
                    tx_type=tx_type,
                    description=description_str[:100]
                )
                if success:
                    inserted_records += 1

        return inserted_records

spatial_parser = AdvancedSpatialParser()
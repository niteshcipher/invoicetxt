import hashlib
import sqlite3
import os
import pandas as pd

DB_PATH = "./data/financial_erp.db"
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

class LedgerManager:
    def __init__(self):
        # Initialize SQLite database and create tables if they don't exist
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        # Table for unique file hashes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS file_hashes (
                file_hash TEXT PRIMARY KEY
            )
        """)
        # Table for persistent transactions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                party_name TEXT,
                amount REAL,
                type TEXT,
                description TEXT
            )
        """)
        self.conn.commit()

    def calculate_file_hash(self, file_bytes: bytes) -> str:
        return hashlib.md5(file_bytes).hexdigest()

    def is_file_duplicate(self, file_bytes: bytes) -> bool:
        file_hash = self.calculate_file_hash(file_bytes)
        cursor = self.conn.cursor()
        cursor.execute("SELECT 1 FROM file_hashes WHERE file_hash = ?", (file_hash,))
        if cursor.fetchone():
            return True
        
        cursor.execute("INSERT INTO file_hashes (file_hash) VALUES (?)", (file_hash,))
        self.conn.commit()
        return False

    def is_semantic_duplicate(self, date_str: str, party_name: str, amount: float) -> bool:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 1 FROM transactions 
            WHERE date = ? AND party_name = ? AND ABS(amount - ?) < 0.01
        """, (date_str, party_name, amount))
        return cursor.fetchone() is not None

    def add_transaction(self, date_str: str, party_name: str, amount: float, tx_type: str, description: str):
        if self.is_semantic_duplicate(date_str, party_name, amount):
            print(f"⚠️ [Duplicate Warning] Skipped: {date_str} | {party_name} | ₹{amount}")
            return False
        
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO transactions (date, party_name, amount, type, description)
            VALUES (?, ?, ?, ?, ?)
        """, (date_str, party_name, float(amount), tx_type.strip().capitalize(), description))
        self.conn.commit()
        return True

    def generate_party_ledger(self, target_party: str):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT date, description, amount, type FROM transactions 
            WHERE party_name = ?
        """, (target_party,))
        rows = cursor.fetchall()
        
        if not rows:
            return None, 0.0, 0.0
        
        # Build pandas DataFrame dynamically from SQL records
        df = pd.DataFrame(rows, columns=['date', 'description', 'amount', 'type'])
        
        df['Debit'] = df.apply(lambda row: row['amount'] if row['type'] == 'Debit' else 0.0, axis=1)
        df['Credit'] = df.apply(lambda row: row['amount'] if row['type'] == 'Credit' else 0.0, axis=1)
        
        total_debit = df['Debit'].sum()
        total_credit = df['Credit'].sum()
        
        ledger_display = df[['date', 'description', 'Debit', 'Credit']]
        return ledger_display, total_debit, total_credit

# Singleton wrapper instance
ledger_manager = LedgerManager()
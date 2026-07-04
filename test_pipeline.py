from app.core.ledger import ledger_manager
from app.core.entity_resolver import entity_resolver

def run_ledger_integration_test():
    print("--- Simulating Transaction Ingestion Pipeline ---\n")
    
    # 1. Mocking incoming transaction extraction results
    raw_ingested_data = [
        {"date": "2026-01-15", "raw_desc": "UPI-RAHUL TRAD-BIZ-9923@oksbi", "amount": 12500.0, "type": "Credit"},
        {"date": "2026-01-18", "raw_desc": "CHQ DEPOSIT / RAHUL TRADERS / MUM", "amount": 8000.0, "type": "Credit"},
        {"date": "2026-01-22", "raw_desc": "ONLINE TRANSFER RAHUL TRAD", "amount": 5500.0, "type": "Debit"},
        # Exact semantic duplicate entry (same date, resolved name, and amount)
        {"date": "2026-01-18", "raw_desc": "UPI-RAHUL TRAD-BIZ-9923@oksbi", "amount": 8000.0, "type": "Credit"}, 
    ]
    
    # 2. Process each incoming transaction
    for tx in raw_ingested_data:
        # Resolve the noisy text into an official ledger identity
        resolved_party = entity_resolver.resolve_party(tx['raw_desc'])
        
        # Try to commit it to the party ledger database
        ledger_manager.add_transaction(
            date_str=tx['date'],
            party_name=resolved_party,
            amount=tx['amount'],
            tx_type=tx['type'],
            description=tx['raw_desc']
        )
        
    print("\n--- Generating Cleaned Ledger for: Rahul Traders ---")
    ledger_df, total_dr, total_cr = ledger_manager.generate_party_ledger("Rahul Traders")
    
    if ledger_df is not None:
        print(ledger_df.to_string(index=False))
        print("-" * 50)
        print(f"TOTAL DEBIT : ₹{total_dr:<15} TOTAL CREDIT: ₹{total_cr}")
        print("-" * 50)

if __name__ == "__main__":
    run_ledger_integration_test()
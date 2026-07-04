import re
from app.core.entity_resolver import entity_resolver
from app.core.ledger import ledger_manager

class TransactionParser:
    def __init__(self):
        # Precise pattern matching loops
        self.date_pattern = r'\b\d{2}[-/]\d{2}[-/]\d{2,4}\b|\b\d{4}-\d{2}-\d{2}\b'
        self.money_pattern = r'\b\d+(?:\.\d{2})\b|\b\d+,\d{3}(?:\.\d{2})?\b'
        # Filter out common row noise like headers or column dividers
        self.noise_words = ["DATE", "NARATION", "DESCRIPTION", "AMOUNT", "BALANCE", "STATEMENT"]

    def clean_row_tokens(self, line: str, dates: list, amounts: list) -> str:
        """Removes dates, amounts, and reference markers to leave only a clean entity name."""
        text = line.upper()
        for d in dates:
            text = text.replace(d, "")
        for a in amounts:
            text = text.replace(a, "")
            
        # Strip trailing reference details
        text = re.sub(r'\b(UPI|NEFT|IMPS|RTGS|CHQ|REF|INF|POS|TRANSFER|/)\b', '', text)
        text = re.sub(r'[A-Z0-9]+/[A-Z0-9]+', '', text) 
        text = re.sub(r'\b\d{4,}\b', '', text) # Wipe long number blocks safely
        return text.strip()

    def parse_unstructured_text(self, raw_text: str) -> int:
        """
        Slices dense text streams, accurately aligns dynamic financial column values,
        and posts them cleanly straight to the local SQLite ledger.
        """
        lines = raw_text.split("\n")
        records_committed = 0

        for line in lines:
            line_str = line.strip()
            if not line_str or any(word in line_str.upper() for word in self.noise_words):
                continue

            # 1. Extract structural markers
            dates = re.findall(self.date_pattern, line_str)
            amounts = re.findall(self.money_pattern, line_str)

            if not amounts:
                continue

            tx_date = dates[0] if dates else "2026-07-04"
            
            # 2. Extract transaction amount values safely
            try:
                clean_amounts = [float(amt.replace(',', '')) for amt in amounts]
                tx_amount = clean_amounts[0] # Grab primary directional posting value
            except ValueError:
                continue

            # 3. Determine cash direction dynamically
            is_debit = any(token in line_str.upper() for token in ["WDL", "DEBIT", "CHARGES", "PAID", "DR", "MINUS", "-"])
            tx_type = "Debit" if is_debit else "Credit"

            # 4. Strip out numeric details to preserve the clean target name
            description_chunk = self.clean_row_tokens(line_str, dates, amounts)
            resolved_party = entity_resolver.resolve_party(description_chunk)

            # 5. Commit directly to local SQLite Storage
            success = ledger_manager.add_transaction(
                date_str=tx_date,
                party_name=resolved_party,
                amount=tx_amount,
                tx_type=tx_type,
                description=line_str[:100]
            )
            if success:
                records_committed += 1

        return records_committed

transaction_parser = TransactionParser()
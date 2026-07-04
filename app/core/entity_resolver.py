import re
from rapidfuzz import process, fuzz

class EntityResolver:
    def __init__(self):
        # Your target company accounts list
        self.master_parties = [
            "Rahul Traders", 
            "Amazon Web Services", 
            "Swiggy Delivery", 
            "Reliance Retail", 
            "M/S Sharma Logistics",
            "GST Authority Account"
        ]

    def clean_transaction_description(self, desc: str) -> str:
        if not desc:
            return ""
        
        cleaned = desc.upper()
        
        # 1. Clean explicit transaction indicators with boundaries
        cleaned = re.sub(r'\b(UPI|NEFT|IMPS|RTGS|POS|CHQ|WDL|DEP|TRANSFER|REV|DR|CR)\b', ' ', cleaned)
        
        # 2. Extract and remove trailing unique reference patterns (e.g., /REF882910AA, @oksbi)
        cleaned = re.sub(r'@[a-zA-Z0-9]+', ' ', cleaned)
        cleaned = re.sub(r'(-BIZ-|-CORP-|-DIRECT-)', ' ', cleaned)
        cleaned = re.sub(r'/[A-Z0-9]+', ' ', cleaned)
        
        # 3. Strip trailing metadata symbols
        cleaned = cleaned.replace('-', ' ').replace('/', ' ').replace('#', ' ')
        
        # 4. Strip numbers with a length of 3 or more (such as reference IDs or dates)
        cleaned = re.sub(r'\b\d{3,}\b', ' ', cleaned)
        
        return " ".join(cleaned.split()).strip()

    def resolve_party(self, raw_description: str) -> str:
        cleaned_text = self.clean_transaction_description(raw_description)
        if not cleaned_text:
            return "Unknown Party"
            
        # FIX: Create an all-uppercase dictionary map of your master list 
        # so case variance never breaks the fuzzy logic score.
        master_lookup = {party.upper(): party for party in self.master_parties}
        
        match = process.extractOne(
            cleaned_text.upper(), 
            list(master_lookup.keys()), 
            scorer=fuzz.partial_ratio
        )
        
        if match:
            matched_upper, similarity_score, _ = match
            # With case matching fixed, 65%+ ensures robust enterprise mapping
            if similarity_score >= 65.0:
                return master_lookup[matched_upper]
                
        return f"Unknown ({cleaned_text})"

entity_resolver = EntityResolver()
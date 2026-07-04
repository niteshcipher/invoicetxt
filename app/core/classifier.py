import os
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline

MODEL_PATH = os.path.join(os.path.dirname(__file__), "doc_classifier.pkl")

# 1. Base Mock Data to bootstrap your prototype immediately
DEFAULT_TRAINING_DATA = [
    # Bank Statements
    ("HDFC Bank Statement Account Number Closing Balance Transaction Description Interest Credit Debit Withdrawal Deposit", "Bank Statement"),
    ("SBI Corporate Bank Statement Statement Period Opening Balance Chq/Ref No UPI NEFT IMPS Transfers Avl Bal", "Bank Statement"),
    
    # Invoices / Bills
    ("Tax Invoice Bill To Ship To Invoice Date GSTIN HSN Code Description Qty Rate Supply Amount Total Due Payable", "Invoice"),
    ("Purchase Invoice Vendor Name Authorized Signatory Terms of Payment Balance Due Item Details Subtotal GST", "Invoice"),
    
    # Receipts
    ("Payment Receipt Received with thanks from sum of Cash/Cheque being payment on account of Amount Received", "Receipt"),
    ("Official Cash Receipt Received From The Sum Of For Payment Of Mode of Payment Cash Received By Signature", "Receipt")
]

class DocumentClassifier:
    def __init__(self):
        self.pipeline = None
        self.load_or_train()

    def train_model(self, custom_data=None):
        """Trains the ML pipeline using TF-IDF and Random Forest."""
        data = custom_data if custom_data else DEFAULT_TRAINING_DATA
        
        texts = [item[0] for item in data]
        labels = [item[1] for item in data]

        # Pipeline: Convert text to numerical vectors, then train the classifier
        self.pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(ngram_range=(1, 2), stop_words='english', lowercase=True)),
            ('clf', RandomForestClassifier(n_estimators=100, random_state=42))
        ])
        
        self.pipeline.fit(texts, labels)
        
        # Save model weights locally
        joblib.dump(self.pipeline, MODEL_PATH)
        print("Document classifier trained and saved successfully.")

    def load_or_train(self):
        """Loads existing model weights or triggers initial training loop."""
        if os.path.exists(MODEL_PATH):
            self.pipeline = joblib.load(MODEL_PATH)
        else:
            self.train_model()

    def predict(self, extracted_text: str) -> str:
        """Predicts the document class given raw extracted text."""
        if not extracted_text.strip():
            return "Unknown"
        prediction = self.pipeline.predict([extracted_text])
        return prediction[0]

# Singleton instance for the app
classifier = DocumentClassifier()
import os
import pypdf
import pandas as pd
import easyocr
import numpy as np
from pdf2image import convert_from_path

class DocumentExtractor:
    def __init__(self):
        # Cache initialization so it doesn't double-load weights on CPU restarts
        self._ocr_reader = None

    @property
    def ocr_reader(self):
        if self._ocr_reader is None:
            print("⏳ Loading EasyOCR Model Engine into Memory...")
            self._ocr_reader = easyocr.Reader(['en'], gpu=False)
        return self._ocr_reader

    def extract_txt_from_pdf(self, file_path: str) -> str:
        """Extracts native digital text layers from standard PDFs."""
        text = ""
        try:
            with open(file_path, "rb") as f:
                reader = pypdf.PdfReader(f)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            print(f"Error reading digital PDF: {e}")
        return text

    def extract_txt_from_scanned_pdf(self, file_path: str) -> str:
        """Converts scanned PDF pages to rasterized images and processes via OCR."""
        scanned_text = []
        try:
            print(f"📸 Converting scanned PDF pages to images: {file_path}")
            # Convert PDF pages into PIL Image objects
            pages = convert_from_path(file_path, dpi=150)
            
            for i, page in enumerate(pages):
                # Convert PIL image to an un-detailed numpy array for EasyOCR ingestion speed
                page_np = np.array(page)
                results = self.ocr_reader.readtext(page_np, detail=0)
                scanned_text.append(" ".join(results))
                
            return "\n".join(scanned_text)
        except Exception as e:
            print(f"Error executing scanned PDF OCR parsing loop: {e}")
            return ""

    def extract_txt_from_image(self, file_path: str) -> str:
        """Extracts text from images (PNG, JPG) and mobile photos using local OCR."""
        try:
            results = self.ocr_reader.readtext(file_path, detail=0)
            return " ".join(results)
        except Exception as e:
            print(f"Error performing local OCR: {e}")
            return ""

    def extract_from_tabular(self, file_path: str) -> str:
        """Reads tabular spreadsheet text structure (CSV/Excel) into structural string data."""
        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            
            header_str = " ".join(df.columns.astype(str))
            row_str = " ".join(df.astype(str).values.flatten())
            return f"{header_str} {row_str}"
        except Exception as e:
            print(f"Error parsing tabular data: {e}")
            return ""

    def process_file(self, file_path: str) -> str:
        """Router method to handle incoming files depending on their extension."""
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext in ['.pdf']:
            text = self.extract_txt_from_pdf(file_path)
            # FIXED: Instead of returning a string token, route scanned PDFs to OCR execution
            if not text.strip():
                return self.extract_txt_from_scanned_pdf(file_path)
            return text
            
        elif ext in ['.png', '.jpg', '.jpeg']:
            return self.extract_txt_from_image(file_path)
            
        elif ext in ['.csv', '.xlsx', '.xls']:
            return self.extract_from_tabular(file_path)
            
        else:
            return ""

# Singleton wrapper instance
extractor = DocumentExtractor()
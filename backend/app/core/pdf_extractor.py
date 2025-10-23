import pdfplumber
from typing import Dict, Any
import os


class PDFExtractor:
    def extract_text(self, pdf_path: str) -> str:
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                return text.strip()
        except Exception as e:
            print(f"Error extracting PDF {pdf_path}: {str(e)}")
            return ""
    
    def extract_all_files(self, submission_id: str) -> Dict[str, Any]:
        base_path = f"storage/uploads/{submission_id}"
        
        extracted = {}
        
        quadro_path = f"{base_path}/quadro.pdf"
        if os.path.exists(quadro_path):
            extracted["quadro"] = self.extract_text(quadro_path)
        else:
            extracted["quadro"] = ""
        
        cv_path = f"{base_path}/cv.pdf"
        if os.path.exists(cv_path):
            extracted["cv"] = self.extract_text(cv_path)
        else:
            extracted["cv"] = ""
        
        estrategia_path = f"{base_path}/estrategia.pdf"
        if os.path.exists(estrategia_path):
            extracted["estrategia"] = self.extract_text(estrategia_path)
        else:
            extracted["estrategia"] = None
        
        onenote_path = f"{base_path}/onenote.pdf"
        if os.path.exists(onenote_path):
            extracted["onenote"] = self.extract_text(onenote_path)
        else:
            extracted["onenote"] = None
        
        testimonials = []
        i = 0
        while True:
            testimonial_path = f"{base_path}/testimonial_{i}.pdf"
            if os.path.exists(testimonial_path):
                testimonials.append(self.extract_text(testimonial_path))
                i += 1
            else:
                break
        
        extracted["testimonials"] = testimonials
        
        return extracted

"""🔥 OCR Processor - Images + PDF Support"""

import pytesseract
from PIL import Image, ImageEnhance
import easyocr
import numpy as np
import re
import os
import sys
from pathlib import Path

# PDF support
try:
    import fitz  # PyMuPDF
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    print("⚠️ PyMuPDF not installed. Run: pip install PyMuPDF")

# ===============================
# 🔧 TESSERACT CONFIG (Windows)
# ===============================
if sys.platform == 'win32':
    possible_paths = [
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
    ]
    for path in possible_paths:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            print(f"✅ Tesseract configured at: {path}")
            break


# ===============================
# 🔥 MAIN OCR CLASS
# ===============================
class OCRProcessor:

    def __init__(self):
        print("🚀 Initializing OCR Processor (Images + PDF)")
        self.reader = easyocr.Reader(['en', 'ur'], gpu=False)

    # ===============================
    # 📸 MAIN FUNCTION - Auto-detect type
    # ===============================
    def extract_text(self, file):
        """Auto-detect and extract text from image or PDF"""
        try:
            # Handle Django UploadedFile
            if hasattr(file, 'name'):
                filename = file.name.lower()
                file_content = file.read()
                file.seek(0)  # Reset for later use
                
                temp_path = Path(f"temp_{filename}")
                with open(temp_path, 'wb') as f:
                    f.write(file_content)
                
                if filename.endswith('.pdf'):
                    text = self._extract_from_pdf(temp_path)
                else:
                    text = self._extract_from_image(temp_path)
                
                temp_path.unlink()
                return self._clean_text(text)
            
            # Handle file path string
            else:
                file_path = Path(file)
                if file_path.suffix.lower() == '.pdf':
                    text = self._extract_from_pdf(file_path)
                else:
                    text = self._extract_from_image(file_path)
                return self._clean_text(text)
                
        except Exception as e:
            print(f"❌ OCR Error: {e}")
            return None

    # ===============================
    # 📄 PDF EXTRACTION
    # ===============================
    def _extract_from_pdf(self, pdf_path):
        """Extract text from PDF"""
        if not PDF_SUPPORT:
            print("❌ PDF support not available")
            return ""
        
        print(f"📄 Processing PDF: {pdf_path.name}")
        text_parts = []
        
        try:
            doc = fitz.open(pdf_path)
            print(f"   📑 {len(doc)} pages")
            
            for page_num, page in enumerate(doc, 1):
                page_text = page.get_text()
                
                if page_text and len(page_text.strip()) > 50:
                    text_parts.append(page_text)
                else:
                    print(f"   🔍 Page {page_num}: Using OCR...")
                    pix = page.get_pixmap(dpi=150)
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    ocr_text = self._ocr_image(img)
                    if ocr_text:
                        text_parts.append(ocr_text)
            
            doc.close()
            full_text = "\n\n".join(text_parts)
            print(f"   ✅ PDF: {len(full_text)} chars")
            return full_text
            
        except Exception as e:
            print(f"   ❌ PDF error: {e}")
            return ""

    # ===============================
    # 🖼️ IMAGE EXTRACTION
    # ===============================
    def _extract_from_image(self, image_path):
        """Extract text from image"""
        print(f"🖼️ Processing: {image_path.name}")
        img = Image.open(image_path)
        img = self._preprocess_image(img)
        return self._ocr_image(img)

    # ===============================
    # 🔤 OCR ENGINE
    # ===============================
    def _ocr_image(self, img):
        """Run OCR on image"""
        text = ""
        
        try:
            text = pytesseract.image_to_string(img, lang='eng+urd')
            if text and len(text.strip()) > 50:
                print("   ✅ Tesseract")
                return text
        except:
            print("   ⚠️ Tesseract failed")

        print("   🔄 EasyOCR fallback...")
        try:
            result = self.reader.readtext(np.array(img))
            text = " ".join([r[1] for r in result])
        except:
            print("   ❌ EasyOCR failed")

        return text

    # ===============================
    # 🧠 IMAGE PREPROCESSING
    # ===============================
    def _preprocess_image(self, img):
        if img.mode != 'L':
            img = img.convert('L')
        img = ImageEnhance.Contrast(img).enhance(2.0)
        img = ImageEnhance.Sharpness(img).enhance(1.5)
        if img.width > 2000:
            ratio = 2000 / img.width
            img = img.resize((2000, int(img.height * ratio)))
        return img

    # ===============================
    # 🧹 CLEAN TEXT
    # ===============================
    def _clean_text(self, text):
        if not text:
            return ""
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s\u0600-\u06FF\.\,\?\-\:\;\(\)\[\]\n]', '', text)
        return text.strip()


# ===============================
# 🔁 SINGLETON
# ===============================
_ocr = None

def get_ocr_processor():
    global _ocr
    if _ocr is None:
        _ocr = OCRProcessor()
    return _ocr


def extract_text_from_image(file):
    return get_ocr_processor().extract_text(file)
"""Lightweight FAISS Index Builder - Reduced memory usage"""
import os
import sys
from pathlib import Path

# ====================== DJANGO SETUP ======================
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_legal_support_system.settings')
import django
django.setup()
# ========================================================

import pickle
import numpy as np
import faiss
import re

from ai_engine.config import LAW_BOOKS_DIR, EMBEDDINGS_DIR, LAW_BOOKS, CHUNK_SIZE, CHUNK_OVERLAP
from ai_engine.embedder import get_embedder

def extract_section_number(text):
    patterns = [
        r'(?i)(?:section|sec\.?|s\.?)\s*(\d+[A-Za-z]?)',
        r'دفعہ\s*(\d+[A-Za-z]?)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    return "N/A"

def load_pdf_text(pdf_path):
    try:
        import pdfplumber
        print(f" 📖 Reading: {pdf_path.name}")
        full_text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
        print(f" ✅ Extracted {len(full_text):,} characters")
        return full_text
    except Exception as e:
        print(f" ❌ PDF Error: {e}")
        return ""

def chunk_text(text, source_name, chunk_size=800, overlap=150):   # Reduced size
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        if end < len(text):
            break_pos = max(text.rfind('\n\n', start, end), text.rfind('. ', start, end))
            if break_pos > start + 300:
                end = break_pos + 1
        chunk_text = text[start:end].strip()
        if len(chunk_text) > 100:
            section = extract_section_number(chunk_text)
            chunks.append({
                'text': chunk_text,
                'source': source_name,
                'section': section
            })
        start = end - overlap
    return chunks

def build_faiss_index():
    print("\n🔨 BUILDING LIGHTWEIGHT FAISS INDEX (Lower Memory)")
    print("=" * 70)

    embedder = get_embedder()
    all_chunks = []

    for book_key, book_info in LAW_BOOKS.items():
        pdf_path = LAW_BOOKS_DIR / book_info['file']
        if not pdf_path.exists():
            print(f"❌ File not found: {book_info['file']}")
            continue

        print(f"\n📖 Processing → {book_info['name']}")
        text = load_pdf_text(pdf_path)
        if not text:
            continue

        chunks = chunk_text(text, book_info['name'])
        sections_found = len([c for c in chunks if c['section'] != "N/A"])
        print(f"   → {len(chunks)} chunks | {sections_found} sections detected")
        all_chunks.extend(chunks)

    print(f"\n📊 Total chunks: {len(all_chunks)}")

    # Smaller batch size to save memory
    texts = [chunk['text'] for chunk in all_chunks]
    embeddings = []
    batch_size = 16   # Reduced from 32

    print("\n🔢 Creating embeddings (this may take time)...")
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        batch_emb = embedder.embed_batch(batch)
        embeddings.extend(batch_emb)
        print(f"   Embedded {min(i+batch_size, len(texts))}/{len(texts)} chunks")

    embeddings = np.array(embeddings).astype('float32')
    print(f" Embeddings shape: {embeddings.shape}")

    print("\n🏗️ Building FAISS index...")
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)

    print("\n💾 Saving files...")
    faiss.write_index(index, str(EMBEDDINGS_DIR / 'index.faiss'))

    metadata = [{
        'text': chunk['text'][:700],
        'source': chunk['source'],
        'section': chunk['section']
    } for chunk in all_chunks]

    with open(EMBEDDINGS_DIR / 'index.pkl', 'wb') as f:
        pickle.dump(metadata, f)

    print("\n🎉 SUCCESS! INDEX BUILT WITH LOWER MEMORY USAGE")
    print(f"Total vectors: {index.ntotal}")

if __name__ == "__main__":
    build_faiss_index()
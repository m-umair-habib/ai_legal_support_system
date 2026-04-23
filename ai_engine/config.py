"""Configuration for AI Engine"""
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Paths
DATA_DIR = BASE_DIR / 'data'
LAW_BOOKS_DIR = DATA_DIR / 'law_books'
LAWYERS_DIR = DATA_DIR / 'lawyers'
EMBEDDINGS_DIR = DATA_DIR / 'embeddings'

# ==================== UPDATED EMBEDDING MODEL ====================
# Best multilingual model for Urdu + Pakistani legal text
EMBEDDING_MODEL_NAME = "BAAI/bge-m3"

# FAISS index settings
FAISS_INDEX_PATH = EMBEDDINGS_DIR / 'index.faiss'
FAISS_MAPPING_PATH = EMBEDDINGS_DIR / 'index.pkl'

# Law books list (unchanged)
LAW_BOOKS = {
    'ppc': {
        'name': 'Pakistan Penal Code',
        'file': 'ppc_law.pdf',
        'color': '#1a73e8',
        'keywords': ['murder', 'qatl', 'theft', 'chori', 'rape', 'zina', 'fraud', 'dhoka']
    },
    'constitution': {
        'name': 'Constitution of Pakistan',
        'file': 'constitution_of_pakistan.pdf',
        'color': '#e8710a',
        'keywords': ['fundamental rights', 'constitution', 'president', 'parliament', 'senate']
    },
    'civil_procedure': {
        'name': 'Code of Civil Procedure, 1908',
        'file': 'THE_CODE_OF_CIVIL_PROCEDURE_1908.pdf',
        'color': '#0a8e3e',
        'keywords': ['civil suit', 'plaint', 'written statement', 'decree', 'appeal', 'injunction']
    },
    'criminal_procedure': {
        'name': 'Code of Criminal Procedure, 1898',
        'file': 'Code_of_criminal_procedure_1898.pdf',
        'color': '#8e0a5e',
        'keywords': ['fir', 'arrest', 'bail', 'investigation', 'trial', 'sessions court', 'magistrate']
    }
}

# Search settings - OPTIMIZED for legal texts
DEFAULT_TOP_K = 4
CHUNK_SIZE = 1200          # characters (better for legal sections)
CHUNK_OVERLAP = 200

# Print configuration
print("=" * 50)
print("AI ENGINE CONFIGURATION - UPDATED")
print("=" * 50)
print(f"Embedding Model : {EMBEDDING_MODEL_NAME}")
print(f"Data Directory  : {DATA_DIR}")
print(f"Law Books       : {len(LAW_BOOKS)} books")
print(f"FAISS Index exists: {FAISS_INDEX_PATH.exists()}")
print("=" * 50)
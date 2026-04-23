"""Embedding model wrapper - BAAI/bge-m3 for Urdu + Legal"""
from pathlib import Path
import numpy as np
from .config import EMBEDDING_MODEL_NAME, EMBEDDINGS_DIR

class Embedder:
    def __init__(self):
        model_name = EMBEDDING_MODEL_NAME
        print(f"🔄 Loading embedding model: {model_name}")

        # Create safe folder name
        safe_name = model_name.replace('/', '_').replace('-', '_')
        local_model_path = EMBEDDINGS_DIR / safe_name

        try:
            from sentence_transformers import SentenceTransformer
            
            if local_model_path.exists():
                print(f" ✅ Loading cached model from: {local_model_path}")
                self.model = SentenceTransformer(str(local_model_path))
            else:
                print(" ⬇️ Downloading BAAI/bge-m3 (first time only - about 1.2 GB)...")
                print("This may take 2-5 minutes depending on your internet.")
                self.model = SentenceTransformer(model_name)
                # Save it locally for future use
                self.model.save(str(local_model_path))
                print(f" ✅ Model saved to {local_model_path}")
                
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            raise

        self.model_name = model_name
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        print(f"✅ Embedder ready! Dimension: {self.embedding_dim}")

    def embed_text(self, text):
        if not text or not isinstance(text, str):
            return np.zeros(self.embedding_dim)
        return self.model.encode(text, normalize_embeddings=True)

    def embed_batch(self, texts):
        if not texts:
            return np.array([])
        return self.model.encode(texts, normalize_embeddings=True)

    def get_embedding_dimension(self):
        return self.embedding_dim

# Singleton
_embedder_instance = None
def get_embedder():
    global _embedder_instance
    if _embedder_instance is None:
        _embedder_instance = Embedder()
    return _embedder_instance
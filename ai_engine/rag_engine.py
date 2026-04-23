# """
# 🔥 Advanced RAG Engine - NO POST-PROCESSING (Streaming Format Preserved)
# """
# import pickle
# import numpy as np
# import faiss
# import os
# from groq import Groq
# from dotenv import load_dotenv
# from .embedder import get_embedder
# from .config import FAISS_INDEX_PATH, FAISS_MAPPING_PATH, DEFAULT_TOP_K
# from .lawyer_loader import get_lawyer_loader
# from .language_processor import detect_language
# load_dotenv()

# class FAISSRAGEngine:
#     def __init__(self):
#         print("\n🤖 ADVANCED RAG ENGINE LOADED")
#         self.embedder = get_embedder()
#         self.lawyer_loader = get_lawyer_loader()
#         self.index = None
#         self.metadata = []
#         self.is_loaded = False
#         self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
#         self.load_index()

#     def load_index(self):
#         try:
#             if FAISS_INDEX_PATH.exists() and FAISS_MAPPING_PATH.exists():
#                 self.index = faiss.read_index(str(FAISS_INDEX_PATH))
#                 with open(FAISS_MAPPING_PATH, 'rb') as f:
#                     self.metadata = pickle.load(f)
#                 self.is_loaded = True
#                 print(f"✅ FAISS Loaded: {self.index.ntotal} chunks")
#         except Exception as e:
#             print(f"❌ Load error: {e}")

#     def retrieve(self, query, top_k):
#         q = np.array([self.embedder.embed_text(query)]).astype('float32')
#         distances, indices = self.index.search(q, top_k)
#         results = []
#         for idx in indices[0]:
#             if 0 <= idx < len(self.metadata):
#                 results.append(self.metadata[idx])
#         return results

#     def search(self, query, top_k=DEFAULT_TOP_K, is_fir=False, fir_text=None, chat_history=None):
#         if not self.is_loaded:
#             return "System initializing. Please try again.", [], "english"

#         lang = detect_language(query or fir_text or "")
#         contexts = self.retrieve(query or (fir_text or ""), top_k) if not is_fir else []
#         lawyers = self.lawyer_loader.search_by_specialty(query or (fir_text or ""), top_k=5)

#         context_text = "\n\n".join([c['text'] for c in contexts[:3]]) if contexts else ""

#         # Strong prompt for proper formatting
#         if lang == 'urdu':
#             system_prompt = """آپ پاکستانی قانونی ماہر ہیں۔ جواب اس فارمیٹ میں دیں:

# ••١.•• تعارف
# [یہاں تعارف لکھیں]

# ••٢.•• سزا
# • پہلی سزا
# • دوسری سزا
# • تیسری سزا

# ••٣.•• قانونی کارروائی
# • پہلا مرحلہ
# • دوسرا مرحلہ
# • تیسرا مرحلہ"""
#         else:
#             system_prompt = """You are a Pakistani legal expert. Format your response EXACTLY like this:

# ••1.•• Definition
# [Write definition here]

# ••2.•• Punishment
# • First punishment
# • Second punishment
# • Third punishment

# ••3.•• Legal Procedure
# • First step
# • Second step
# • Third step"""

#         if is_fir and fir_text:
#             user_content = f"""FIR CONTENT:\n{fir_text}\n\nQUERY: {query}\n\nLEGAL CONTEXT:\n{context_text}"""
#         else:
#             user_content = f"""QUERY: {query}\n\nLEGAL CONTEXT:\n{context_text}"""

#         messages = [
#             {"role": "system", "content": system_prompt},
#             {"role": "user", "content": user_content}
#         ]
        
#         if chat_history:
#             for m in chat_history[-4:]:
#                 messages.insert(1, {"role": m["role"], "content": m["content"]})

#         return messages, lawyers, lang

#     def stream_response(self, messages, lang):
#         """Stream tokens - NO POST-PROCESSING AT ALL"""
#         try:
#             stream = self.client.chat.completions.create(
#                 model="llama-3.3-70b-versatile",
#                 messages=messages,
#                 temperature=0.3,
#                 max_tokens=1200,
#                 stream=True
#             )
            
#             full_response = ""
#             for chunk in stream:
#                 if chunk.choices[0].delta.content:
#                     token = chunk.choices[0].delta.content
#                     full_response += token
#                     yield token
            
#             # 🔥 NO FORMATTING CHANGES - ONLY RTL WRAP FOR URDU
#             if lang == 'urdu':
#                 full_response = full_response.replace('1.', '١.')
#                 full_response = full_response.replace('2.', '٢.')
#                 full_response = full_response.replace('3.', '٣.')
#                 full_response = full_response.replace('4.', '٤.')
#                 full_response = full_response.replace('5.', '٥.')
#                 full_response = f'<div dir="rtl" style="text-align: right;">{full_response}</div>'
            
#             # 🔥 YIELD THE EXACT SAME RESPONSE THAT WAS STREAMED
#             yield full_response
            
#         except Exception as e:
#             print(f"❌ Groq Error: {e}")
#             yield f"❌ Error: {str(e)}"


# # Singleton
# _rag = None
# def get_rag_engine():
#     global _rag
#     if _rag is None:
#         _rag = FAISSRAGEngine()
#     return _rag



"""
🔥 Advanced RAG Engine - Refined for Professional Formatting
"""
import pickle
import numpy as np
import faiss
import os
import json
from groq import Groq
from dotenv import load_dotenv
from .embedder import get_embedder
from .config import FAISS_INDEX_PATH, FAISS_MAPPING_PATH, DEFAULT_TOP_K
from .lawyer_loader import get_lawyer_loader
from .language_processor import detect_language

load_dotenv()

class FAISSRAGEngine:
    def __init__(self):
        self.embedder = get_embedder()
        self.lawyer_loader = get_lawyer_loader()
        self.index = None
        self.metadata = []
        self.is_loaded = False
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.load_index()

    def load_index(self):
        try:
            if FAISS_INDEX_PATH.exists() and FAISS_MAPPING_PATH.exists():
                self.index = faiss.read_index(str(FAISS_INDEX_PATH))
                with open(FAISS_MAPPING_PATH, 'rb') as f:
                    self.metadata = pickle.load(f)
                self.is_loaded = True
        except Exception as e:
            print(f"❌ FAISS Load error: {e}")

    def retrieve(self, query, top_k):
        if not self.index: return []
        q = np.array([self.embedder.embed_text(query)]).astype('float32')
        distances, indices = self.index.search(q, top_k)
        results = []
        for idx in indices[0]:
            if 0 <= idx < len(self.metadata):
                results.append(self.metadata[idx])
        return results

    def search(self, query, top_k=DEFAULT_TOP_K, is_fir=False, fir_text=None, chat_history=None):
        lang = detect_language(query or fir_text or "")
        contexts = self.retrieve(query or fir_text or "", top_k)
        lawyers = self.lawyer_loader.search_by_specialty(query or fir_text or "", top_k=5)

        context_text = "\n\n".join([c['text'] for c in contexts]) if contexts else "No specific legal context found."

        if lang == 'urdu':
            system_prompt = """آپ ایک پیشہ ور پاکستانی قانونی مشیر ہیں۔
جواب کو ان حصوں میں تقسیم کریں:
**1. خلاصہ** (مختصر وضاحت)
**2. متعلقہ دفعات** (PPC کی دفعات اور سزائیں)
**3. قانونی مشورہ** (اگلے اقدامات)

صرف درست قانونی معلومات دیں اور بلٹ پوائنٹس (•) استعمال کریں۔"""
        else:
            system_prompt = """You are a professional Pakistani Legal Expert. 
Structure your response as follows:
**1. Analysis** (Brief overview)
**2. Applicable Sections** (Specific PPC sections and their punishments)
**3. Recommended Action** (Legal steps to take)

Use bold headings and bullet points (•) for clarity. Provide strictly professional advice based on PPC."""

        user_content = f"LEGAL CONTEXT:\n{context_text}\n\nUSER QUERY: {query}"
        if is_fir:
            user_content = f"FIR TEXT:\n{fir_text}\n\n{user_content}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        return messages, lawyers, lang

    def stream_response(self, messages, lang):
        """Stream tokens directly to frontend"""
        try:
            stream = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.2, # Lower temperature for legal accuracy
                max_tokens=1500,
                stream=True
            )
            
            for chunk in stream:
                token = chunk.choices[0].delta.content
                if token:
                    # Apply Urdu digit conversion if necessary
                    if lang == 'urdu':
                        token = token.replace('1', '۱').replace('2', '۲').replace('3', '۳')
                    yield token
                    
        except Exception as e:
            yield f"Error: {str(e)}"

# Singleton Pattern
_rag = None
def get_rag_engine():
    global _rag
    if _rag is None:
        _rag = FAISSRAGEngine()
    return _rag
"""Language Processor - Fully Automated, Simple & User-Friendly"""
class LanguageProcessor:
    def __init__(self):
        self.urdu_range = range(0x0600, 0x06FF)

    def detect_language(self, text):
        if not text:
            return 'english'
        urdu_chars = sum(1 for char in text if ord(char) in self.urdu_range)
        return 'urdu' if urdu_chars / len(text) > 0.1 else 'english'

    # format_response kept as backup (clean version)
    def format_response(self, sections, query, detected_lang='english'):
        if not sections or not sections[0].get('text'):
            return "❌ کوئی متعلقہ قانون نہیں ملا۔ براہ مہربانی اپنا سوال واضح کریں۔" if detected_lang == 'urdu' else "❌ No relevant law found. Please make your question clearer."
        
        response = []
        if detected_lang == 'urdu':
            response.append("📘 **آپ کے سوال کا آسان جواب**")
            response.append(f"**سوال:** {query}")
        else:
            response.append("📘 **Simple Answer to Your Question**")
            response.append(f"**Question:** {query}")
        
        response.append("\n**📋 متعلقہ قانونی دفعات / Relevant Sections:**")
        for item in sections[:3]:
            section = item.get('section', 'N/A')
            source = item.get('source', 'Law Book')
            text = item.get('text', '').strip()[:500]
            response.append(f"• دفعہ {section} ({source})" if section != 'N/A' else f"• {source}")
            response.append(f"   {text[:250]}...")

        # steps already handled in Groq prompt
        if detected_lang == 'urdu':
            response.append("\n**💡 مشورہ:** قریبی پولیس اسٹیشن جائیں یا نیچے دیے گئے وکیل سے رابطہ کریں۔")
        else:
            response.append("\n**💡 Advice:** Go to nearest police station or contact a lawyer below.")
        
        response.append("\n⚠️ **نوٹ:** یہ صرف رہنمائی ہے۔ حتمی مشورے کے لیے وکیل سے ملیں۔")
        return '\n'.join(response)

# Singleton
_lang_processor = None
def get_language_processor():
    global _lang_processor
    if _lang_processor is None:
        _lang_processor = LanguageProcessor()
    return _lang_processor

def detect_language(text):
    return get_language_processor().detect_language(text)
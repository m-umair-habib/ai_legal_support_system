# 🧠 AI Legal Support System

An AI-powered legal assistant built with Django that leverages **Retrieval-Augmented Generation (RAG)** to provide intelligent legal insights based on Pakistani law documents and datasets.

This system integrates natural language processing, semantic search, and OCR to assist users in understanding legal matters and finding relevant legal resources efficiently.

---

## 🚀 Features

* 🔍 **Semantic Legal Search**
  Fast and accurate retrieval of legal information using FAISS-based vector search.

* 🤖 **RAG-Based Question Answering**
  Combines document retrieval with language models to generate context-aware legal responses.

* 📄 **OCR for FIR & Legal Documents**
  Extracts and processes text from uploaded FIR images and legal documents.

* 👨‍⚖️ **Lawyer Recommendation System**
  Suggests relevant lawyers based on case type and dataset analysis.

* 🔐 **User Authentication System**
  Secure signup, login, profile management, and password reset.

* 🌐 **Web Interface (Django Templates)**
  User-friendly interface for interacting with the system.

---

## 🏗️ Tech Stack

**Backend:**

* Django (Python)

**AI / ML:**

* Retrieval-Augmented Generation (RAG)
* FAISS (Facebook AI Similarity Search)
* Sentence Embeddings (BAAI/bge model)

**Data Processing:**

* OCR (for FIR images)
* PDF parsing for legal documents

**Database:**

* SQLite (development)

---

## 📁 Project Structure

```
ai_legal_support_system/
│
├── accounts/              # User authentication & profile management
├── ai_engine/             # Core AI logic (RAG, embeddings, OCR, indexing)
├── legal_api/             # API layer for legal services
│
├── data/
│   ├── law_books/         # Legal PDFs (Pakistan laws)
│   └── lawyers/           # Lawyer datasets (CSV)
│
├── templates/             # HTML templates (UI)
├── static/                # Static assets (CSS, JS)
├── media/                 # Uploaded files (ignored in Git)
│
├── manage.py              # Django entry point
├── main.py                # Custom scripts / entry logic
├── requirements.txt       # Dependencies
├── .env.example           # Environment variables template
└── README.md
```

---

## ⚙️ Installation & Setup

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/yourusername/ai-legal-support-system.git
cd ai-legal-support-system
```

### 2️⃣ Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate        # Linux / Mac
venv\Scripts\activate           # Windows
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Configure Environment Variables

Create a `.env` file using the example:

```bash
cp .env.example .env
```

Update values:

```
DEBUG=True
SECRET_KEY=your-secret-key
OPENAI_API_KEY=your-api-key
```

---

### 5️⃣ Run Migrations

```bash
python manage.py migrate
```

### 6️⃣ Start Development Server

```bash
python manage.py runserver
```

Access the app at:

```
http://127.0.0.1:8000/
```

---

## 🧠 How It Works

1. **Document Processing**

   * Legal PDFs are parsed and converted into text.
   * Text is chunked and embedded using a transformer model.

2. **Vector Indexing**

   * Embeddings are stored using FAISS for fast similarity search.

3. **Query Handling**

   * User query → converted into embedding
   * Relevant legal chunks retrieved
   * Passed to language model for final response

4. **OCR Pipeline**

   * FIR images processed using OCR
   * Extracted text used for legal analysis

---

## 📊 Datasets Used

* 📚 Pakistani Law Books (PDF)

  * Constitution of Pakistan
  * PPC (Pakistan Penal Code)
  * CrPC (Criminal Procedure Code)
  * CPC (Civil Procedure Code)

* 👨‍⚖️ Lawyer Datasets (CSV)

  * Multiple structured datasets for recommendations

---

## 🔒 Security Notes

* `.env` file is excluded from version control
* Sensitive keys must not be exposed publicly
* Media and embeddings are ignored in Git

---

## 🧪 Future Improvements

* 🔄 Switch to PostgreSQL for production
* ☁️ Cloud deployment (AWS / Azure / Docker)
* 📈 Improve RAG accuracy with fine-tuning
* 💬 Add chatbot UI (React / API-based frontend)
* 🌍 Multi-language legal support

---

## 🤝 Contributing

Contributions are welcome!
Feel free to fork the repository and submit a pull request.

---

## 👨‍💻 Author

**Muhammad Umair Habib**
Aspiring Data Scientist
Focused on building intelligent, real-world systems using modern technologies.

---

## ⭐ Support

If you find this project useful, consider giving it a ⭐ on GitHub!

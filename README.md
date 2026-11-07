# 🤖 Document Q&A Agent

An AI-powered document question-answering application built with **Retrieval-Augmented Generation (RAG)**. It allows users to upload PDF and Word documents and ask natural-language questions about their contents.

The application uses **Python, Streamlit, Google Gemini, and ChromaDB**. Documents are extracted and split into smaller chunks. These chunks are embedded and stored in a vector database. When a user asks a question, semantically relevant chunks are retrieved and provided to a language model to generate a grounded answer.

---

## ✨ Features

- 📄 Upload and process **PDF** and **DOCX** documents
- 🧩 Text extraction and overlapping text chunking
- 🔎 Semantic search using text embeddings
- 🧠 Answer generation with Google Gemini
- 📚 Display retrieved document chunks as answer sources
- 💬 Simple conversational interface powered by Streamlit
- 🗂️ Persistent local vector storage with ChromaDB
- 🌐 Persian and English question-answering
- 🛡️ Handling of common API, network, and file-input errors

## 🏗️ Architecture

```text
                User
                  |
                  v
          Streamlit Interface
                  |
          +-------+-------+
          |               |
          v               v
     Upload Document   User Question
          |               |
          v               v
    Text Extraction   Query Embedding
          |               |
          v               |
       Chunking           |
          |               |
          v               |
    Gemini Embeddings     |
          |               |
          v               |
     ChromaDB Store       |
          |               |
          +-------+-------+
                  |
                  v
           Semantic Retrieval
                  |
                  v
           Relevant Chunks
                  |
                  v
             Gemini LLM
                  |
                  v
             Final Answer
```

## 🧰 Tech Stack

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| Streamlit | Web application interface |
| Google Gemini API | Embedding generation and answer generation |
| ChromaDB | Vector database |
| PyMuPDF | PDF text extraction |
| python-docx | DOCX text extraction |
| python-dotenv | Environment variable management |
| httpx | HTTP client and network communication |

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/bankehsaz/document-qa-agent.git
cd document-qa-agent
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows CMD:

```cmd
.venv\Scripts\activate.bat
```

Or on PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure the Gemini API key

Create a `.env` file in the project root and add your API key:

```env
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
```

Get an API key from [Google AI Studio](https://aistudio.google.com/).

**Important:** Keep your `.env` file private. Never commit API keys or other secrets to GitHub.

### 5. Run the application

```bash
streamlit run app.py
```

Streamlit will start the application and provide a local URL. Open that URL in your browser if it does not open automatically.

## 💡 Usage

1. Start the application.
2. Upload a PDF or DOCX document.
3. Wait while the document is extracted, chunked, embedded, and indexed.
4. Enter a question about the document.
5. Review the generated answer and the retrieved source chunks.
6. Continue asking questions within the conversation.

## ⚙️ Configuration and Technical Notes

- The API key is loaded from the `GEMINI_API_KEY` environment variable.
- ChromaDB data is persisted locally in the `chroma_db/` directory.
- A content-based file identifier is used to identify documents and scope retrieval to the active document.
- Answers are generated using retrieved document context. When the document does not contain enough information, the application is designed to communicate that limitation.

## ⚠️ Known Limitations

- **No OCR support:** Scanned PDFs without an extractable text layer cannot be processed for their textual content.
- DOCX extraction focuses on paragraph and table text. Some advanced Word elements, such as text boxes and header/footer content, may not be extracted.
- Answer quality depends on extracted text quality, chunking, and retrieval relevance.
- This is an initial practical MVP. Larger documents and production or enterprise use require further evaluation and optimization.

## 🔮 Future Improvements

- Add OCR support for scanned PDFs.
- Improve retrieval and reasoning across multiple document sections.
- Support additional document formats.
- Add retrieval and answer-quality evaluation.
- Introduce multi-document management.

## 🔐 Security

- Store API keys only in your local `.env` file.
- Keep `.env`, the virtual environment, and the local vector database excluded through `.gitignore`.
- Before publishing, verify that no API keys, private documents, or other sensitive data are tracked by Git.

---

## 📄 License

No license has been specified yet. Add a license file before allowing others to reuse, modify, or distribute this project.
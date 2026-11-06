<div dir="rtl" align="right">

# 🤖 دستیار پرسش‌وپاسخ اسناد | Document Q&A Agent

یک دستیار هوشمند مبتنی بر **بازیابی افزوده با تولید (RAG)** که به شما امکان می‌دهد اسناد PDF و Word را بارگذاری کنید و پرسش‌های خود را به زبان طبیعی درباره محتوای آن‌ها بپرسید.

این پروژه با استفاده از **Python، Streamlit، Google Gemini و ChromaDB** ساخته شده است. متن اسناد استخراج و به بخش‌های کوچک‌تر (Chunks) تقسیم می‌شود؛ سپس با استفاده از Embeddingها در پایگاه داده برداری ذخیره می‌شود. هنگام طرح سؤال، بخش‌های مرتبط بازیابی شده و برای تولید پاسخ در اختیار مدل زبانی قرار می‌گیرند.

---

## ✨ قابلیت‌ها

- 📄 بارگذاری و پردازش فایل‌های **PDF** و **DOCX**
- 🧩 استخراج متن و تقسیم آن به بخش‌های هم‌پوشان (Chunking)
- 🔎 جست‌وجوی معنایی در محتوای سند با Embedding
- 🧠 تولید پاسخ با استفاده از مدل‌های Google Gemini
- 📚 نمایش بخش‌های بازیابی‌شده به‌عنوان منابع پاسخ
- 💬 رابط گفت‌وگویی ساده با Streamlit
- 🗂️ ذخیره‌سازی بردارها به‌صورت محلی و پایدار با ChromaDB
- 🌐 پشتیبانی از پرسش و پاسخ فارسی و انگلیسی
- 🛡️ مدیریت خطاهای رایج API، شبکه و ورودی فایل

## 🏗️ معماری پروژه

جریان اصلی پردازش در این پروژه به شکل زیر است:

```text
             User
              |
              v
       Streamlit Interface
              |
              v
      Upload PDF / DOCX
              |
              v
       Text Extraction
              |
              v
          Chunking
              |
              v
      Gemini Embeddings
              |
              v
        ChromaDB Store
              |
              |  User Question
              v
       Query Embedding
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

## 🧰 فناوری‌ها و ابزارها

| فناوری | کاربرد |
|---|---|
| Python | زبان برنامه‌نویسی اصلی |
| Streamlit | رابط کاربری وب |
| Google Gemini API | تولید Embedding و پاسخ |
| ChromaDB | پایگاه داده برداری |
| PyMuPDF | استخراج متن از PDF |
| python-docx | استخراج متن از DOCX |
| python-dotenv | بارگذاری متغیرهای محیطی |
| httpx | پشتیبانی از مدیریت خطاهای ارتباطی |

## 🚀 نصب و راه‌اندازی

### ۱. دریافت پروژه

```bash
git clone https://github.com/YOUR_USERNAME/document-qa-agent.git
cd document-qa-agent
```

> آدرس مخزن را پس از انتشار پروژه در GitHub با آدرس واقعی جایگزین کنید.

### ۲. ایجاد محیط مجازی

```bash
python -m venv .venv
```

فعال‌سازی در Windows CMD:

```cmd
.venv\Scripts\activate.bat
```

فعال‌سازی در PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### ۳. نصب وابستگی‌ها

```bash
pip install -r requirements.txt
```

### ۴. تنظیم کلید API

در پوشه اصلی پروژه، فایلی با نام `.env` ایجاد کنید و کلید API خود را در آن قرار دهید:

```env
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
```

برای دریافت کلید API می‌توانید به [Google AI Studio](https://aistudio.google.com/) مراجعه کنید.

**مهم:** فایل `.env` حاوی اطلاعات محرمانه است. آن را در GitHub منتشر نکنید.

### ۵. اجرای برنامه

```bash
streamlit run app.py
```

پس از اجرا، Streamlit برنامه را در مرورگر باز می‌کند. در صورت باز نشدن خودکار، آدرس محلی نمایش‌داده‌شده در ترمینال را باز کنید.

## 💡 نحوه استفاده

1. برنامه را اجرا کنید.
2. یک فایل PDF یا DOCX بارگذاری کنید.
3. منتظر بمانید تا متن استخراج، قطعه‌بندی و در پایگاه داده برداری ذخیره شود.
4. سؤال خود را درباره محتوای سند وارد کنید.
5. پاسخ تولیدشده و بخش‌های بازیابی‌شده را بررسی کنید.
6. پرسش‌های بعدی را در همان گفت‌وگو مطرح کنید.

## ⚙️ تنظیمات و نکات فنی

- کلید API از متغیر محیطی `GEMINI_API_KEY` خوانده می‌شود.
- پایگاه داده محلی ChromaDB در پوشه `chroma_db/` نگهداری می‌شود.
- شناسه محتوایی فایل برای تشخیص فایل و محدودکردن بازیابی به سند فعال استفاده می‌شود.
- پاسخ‌ها بر اساس محتوای بازیابی‌شده از سند تولید می‌شوند؛ اگر اطلاعات کافی در سند وجود نداشته باشد، برنامه باید این موضوع را اعلام کند.

## ⚠️ محدودیت‌های شناخته‌شده

- **OCR پشتیبانی نمی‌شود:** فایل‌های PDF اسکن‌شده که متن قابل‌استخراج ندارند، بدون مرحله OCR قابل پردازش محتوایی نیستند.
- در فایل‌های DOCX، استخراج متن بر محتوای متنی پاراگراف‌ها و جدول‌ها متمرکز است؛ همه اجزای پیشرفته Word مانند Text Boxها یا محتوای سربرگ و پابرگ لزوماً استخراج نمی‌شوند.
- کیفیت پاسخ به کیفیت متن استخراج‌شده، قطعه‌بندی و مرتبط‌بودن بخش‌های بازیابی‌شده وابسته است.
- این نسخه یک نمونه کاربردی اولیه (MVP) است و برای استفاده سازمانی یا اسناد بسیار بزرگ به ارزیابی و بهینه‌سازی بیشتر نیاز دارد.

## 🔮 توسعه‌های آینده

- افزودن OCR برای PDFهای اسکن‌شده
- بهبود بازیابی اطلاعات از بخش‌های متعدد سند
- افزودن پشتیبانی از فرمت‌های بیشتر
- بهبود ارزیابی کیفیت بازیابی و پاسخ‌ها
- افزودن قابلیت مدیریت چند سند

## 🔐 امنیت

- کلیدهای API را فقط در فایل محلی `.env` نگهداری کنید.
- فایل `.env`، محیط مجازی و پایگاه داده محلی در `.gitignore` قرار می‌گیرند.
- پیش از انتشار، مطمئن شوید هیچ کلید، سند شخصی یا داده محرمانه‌ای در مخزن Git قرار نگرفته باشد.

---

</div>

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
              v
      Upload PDF / DOCX
              |
              v
       Text Extraction
              |
              v
          Chunking
              |
              v
      Gemini Embeddings
              |
              v
        ChromaDB Store
              |
              |  User Question
              v
       Query Embedding
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
| httpx | Network error handling support |

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/document-qa-agent.git
cd document-qa-agent
```

Replace the placeholder repository URL with your actual GitHub repository URL after publishing the project.

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

- Add OCR support for scanned PDFs
- Improve retrieval and reasoning across multiple document sections
- Support additional document formats
- Add retrieval and answer-quality evaluation
- Introduce multi-document management

## 🔐 Security

- Store API keys only in your local `.env` file.
- Keep `.env`, the virtual environment, and the local vector database excluded through `.gitignore`.
- Before publishing, verify that no API keys, private documents, or other sensitive data are tracked by Git.

---

## 📄 License

No license has been specified yet. Add a license file before allowing others to reuse, modify, or distribute this project.

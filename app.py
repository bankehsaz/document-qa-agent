import hashlib
import logging
import os
import time
from io import BytesIO
from typing import Any, Callable

import chromadb
import httpx
import pymupdf
import streamlit as st
from dotenv import load_dotenv
from docx import Document as WordDocument
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph
from google import genai


# ============================================================
# Configuration
# ============================================================

APP_TITLE = "Document Q&A"
EMBEDDING_MODEL = "gemini-embedding-2"
GENERATION_MODEL = "gemini-3.5-flash-lite"
CHROMA_PATH = "./chroma_db"
COLLECTION_NAME = "document_chunks"

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
RETRIEVAL_RESULTS = 3
MAX_FILE_SIZE_MB = 20
MAX_GEMINI_ATTEMPTS = 3

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("document_qa")


# ============================================================
# Streamlit page and minimal styling
# ============================================================

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="📄",
    layout="centered",
)

st.markdown(
    """
    <style>
        .block-container {
            max-width: 900px;
            padding-top: 2.2rem;
            padding-bottom: 3rem;
        }
        [data-testid="stFileUploader"] {
            border-radius: 12px;
        }
        [data-testid="stChatMessage"] {
            border-radius: 12px;
        }
        .app-subtitle {
            color: #808080;
            margin-top: -0.6rem;
            margin-bottom: 1.4rem;
        }
        .document-label {
            font-size: 0.9rem;
            color: #808080;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("📄 Document Q&A")
st.markdown(
    '<p class="app-subtitle">Upload a PDF or Word document and ask questions about its content.</p>',
    unsafe_allow_html=True,
)


# ============================================================
# Environment and cached resources
# ============================================================

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")


@st.cache_resource
def get_gemini_client(api_key: str):
    """Create one reusable Gemini client per API key."""
    return genai.Client(api_key=api_key)


@st.cache_resource
def get_chroma_collection():
    """Open the persistent ChromaDB collection."""
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        configuration={"hnsw": {"space": "cosine"}},
    )


# ============================================================
# Error handling and retry utilities
# ============================================================

def get_http_status(error: Exception):
    """Extract an HTTP status code from common SDK/HTTP exceptions."""
    for attribute in ("status_code", "code"):
        value = getattr(error, attribute, None)
        if isinstance(value, int):
            return value

    response = getattr(error, "response", None)
    status = getattr(response, "status_code", None)
    return status if isinstance(status, int) else None


def is_retryable_error(error: Exception) -> bool:
    """Retry network failures and temporary API/server errors only."""
    if isinstance(error, httpx.RequestError):
        return True

    status = get_http_status(error)
    return status in RETRYABLE_STATUS_CODES


def call_with_retry(
    operation: Callable[[], Any],
    operation_name: str,
    max_attempts: int = MAX_GEMINI_ATTEMPTS,
):
    """Run a Gemini operation with bounded retries and backoff."""
    for attempt in range(max_attempts):
        try:
            return operation()
        except Exception as error:
            retryable = is_retryable_error(error)

            if not retryable or attempt == max_attempts - 1:
                logger.exception(
                    "%s failed (attempt %s/%s).",
                    operation_name,
                    attempt + 1,
                    max_attempts,
                )
                raise

            delay = min(2 ** attempt, 8)
            logger.warning(
                "%s temporarily failed; retrying in %s seconds "
                "(attempt %s/%s).",
                operation_name,
                delay,
                attempt + 1,
                max_attempts,
            )
            time.sleep(delay)

    raise RuntimeError(f"{operation_name} failed unexpectedly.")


def friendly_error_message(error: Exception, operation: str = "request") -> str:
    """Return a concise, user-safe error message."""
    status = get_http_status(error)

    if status in (401, 403):
        return (
            "Gemini authentication failed. Check the API key "
            "in your environment configuration."
        )

    if status == 429:
        return (
            "The Gemini API quota or rate limit has been reached. "
            "Please wait a little and try again."
        )

    if status in (500, 502, 503, 504):
        return (
            "The Gemini service is temporarily unavailable. "
            "Please try again shortly."
        )

    if isinstance(error, httpx.TimeoutException):
        return "The request timed out. Check your connection and try again."

    if isinstance(error, httpx.RequestError):
        return "A network connection error occurred. Check your internet connection."

    if operation == "document":
        return (
            "The document could not be processed. Make sure it is a valid, "
            "text-based PDF or DOCX file and try again."
        )

    return "Something went wrong while processing your request. Please try again."


# ============================================================
# Document extraction and chunking
# ============================================================

def create_chunks(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> list[str]:
    """Split text into overlapping character-based chunks."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero.")

    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size.")

    if not text or not text.strip():
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]

        if chunk.strip():
            chunks.append(chunk)

        if end >= len(text):
            break

        start += chunk_size - chunk_overlap

    return chunks


def extract_docx_text(file_bytes: bytes) -> str:
    """Extract paragraphs and tables from a DOCX document in body order."""
    document = WordDocument(BytesIO(file_bytes))
    content_blocks = []

    for block in document.element.body.iterchildren():
        if isinstance(block, CT_P):
            paragraph = Paragraph(block, document)
            if paragraph.text.strip():
                content_blocks.append(paragraph.text)

        elif isinstance(block, CT_Tbl):
            table = Table(block, document)
            for row in table.rows:
                row_text = " | ".join(
                    cell.text.strip() for cell in row.cells
                )
                if row_text.strip():
                    content_blocks.append(row_text)

    return "\n\n".join(content_blocks)


def extract_pdf_chunks(file_bytes: bytes) -> list[dict]:
    """Extract text page by page so each chunk retains its PDF page number."""
    chunks = []

    with pymupdf.open(stream=file_bytes, filetype="pdf") as pdf_document:
        if pdf_document.is_encrypted:
            authenticated = pdf_document.authenticate("")
            if not authenticated:
                raise ValueError("Password-protected PDFs are not supported.")

        for page_number, page in enumerate(pdf_document, start=1):
            page_text = page.get_text("text", sort=True)

            if not page_text.strip():
                continue

            for chunk in create_chunks(page_text):
                chunks.append(
                    {
                        "text": chunk,
                        "page": page_number,
                    }
                )

    return chunks


def extract_document_chunks(file_name: str, file_bytes: bytes) -> list[dict]:
    """Dispatch extraction according to the uploaded file extension."""
    extension = file_name.lower().rsplit(".", 1)[-1]

    if extension == "pdf":
        return extract_pdf_chunks(file_bytes)

    if extension == "docx":
        text = extract_docx_text(file_bytes)
        return [
            {"text": chunk}
            for chunk in create_chunks(text)
        ]

    raise ValueError("Unsupported document format.")


# ============================================================
# Gemini embeddings and document indexing
# ============================================================

def generate_embedding(text: str, client) -> list[float]:
    """Generate an embedding for one document chunk."""
    formatted_text = f"title: none | text: {text}"

    result = call_with_retry(
        lambda: client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=formatted_text,
        ),
        operation_name="Document embedding",
    )

    if not result or not result.embeddings:
        raise RuntimeError("Gemini returned an empty embedding.")

    values = result.embeddings[0].values
    if not values:
        raise RuntimeError("Gemini returned an empty embedding vector.")

    return values


def process_document(
    file_name: str,
    file_bytes: bytes,
    file_id: str,
    client,
    collection,
) -> int:
    """
    Extract, chunk, embed, and store a document.

    ChromaDB is updated only after all embeddings have been generated,
    avoiding partially indexed documents when an embedding request fails.
    """
    chunks = extract_document_chunks(file_name, file_bytes)

    if not chunks:
        raise ValueError(
            "No readable text was found. Scanned PDFs may require OCR."
        )

    documents = []
    embeddings = []
    metadatas = []
    ids = []

    progress = st.progress(0, text="Preparing document...")

    try:
        total = len(chunks)

        for index, item in enumerate(chunks, start=1):
            text = item["text"]
            embedding = generate_embedding(text, client)

            documents.append(text)
            embeddings.append(embedding)

            metadata = {
                "source": file_name,
                "file_id": file_id,
                "chunk_index": index,
            }

            if item.get("page") is not None:
                metadata["page"] = item["page"]

            metadatas.append(metadata)
            ids.append(f"{file_id}_{index}")

            progress.progress(
                index / total,
                text=f"Processing document ({index}/{total})...",
            )

        collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

    finally:
        progress.empty()

    return len(chunks)


# ============================================================
# Retrieval and answer generation
# ============================================================

def retrieve_relevant_chunks(
    question: str,
    client,
    collection,
    file_id: str,
    n_results: int = RETRIEVAL_RESULTS,
) -> tuple[str, list[dict]]:
    """Retrieve relevant chunks only from the currently selected document."""
    if not question or not question.strip():
        return "", []

    if collection.count() == 0:
        return "", []

    result = call_with_retry(
        lambda: client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=f"task: question answering | query: {question}",
        ),
        operation_name="Query embedding",
    )

    if not result or not result.embeddings:
        raise RuntimeError("Gemini did not return a query embedding.")

    query_embedding = result.embeddings[0].values
    if not query_embedding:
        raise RuntimeError("Gemini returned an empty query vector.")

    matching_count = len(
    collection.get(
        where={"file_id": file_id},
        include=[]
    )["ids"]
)

    if matching_count == 0:
        return "", []

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(n_results, matching_count),
        where={"file_id": file_id},
        include=["documents", "metadatas"],
    )

    documents = (results.get("documents") or [[]])[0] or []
    metadatas = (results.get("metadatas") or [[]])[0] or []

    context_parts = []
    sources = []
    seen_sources = set()

    for index, document in enumerate(documents):
        if not document or not document.strip():
            continue

        metadata = (
            metadatas[index]
            if index < len(metadatas) and metadatas[index]
            else {}
        )

        source = metadata.get("source", "Unknown")
        page = metadata.get("page")
        chunk_index = metadata.get("chunk_index", "Unknown")

        if page is not None:
            source_label = f"Source: {source}, Page: {page}"
            source_key = (source, "page", page)
        else:
            source_label = f"Source: {source}, Chunk: {chunk_index}"
            source_key = (source, "chunk", chunk_index)

        context_parts.append(f"[{source_label}]\n{document}")

        if source_key not in seen_sources:
            sources.append(
                {
                    "source": source,
                    "page": page,
                    "chunk_index": chunk_index,
                }
            )
            seen_sources.add(source_key)

    return "\n\n".join(context_parts), sources


def contains_persian(text: str) -> bool:
    return any("\u0600" <= char <= "\u06FF" for char in text)


def generate_rag_answer(
    question: str,
    context: str,
    client,
) -> str:
    """Generate a grounded answer in the same language as the question."""
    answer_language = "Persian" if contains_persian(question) else "English"

    if not context or not context.strip():
        if answer_language == "Persian":
            return "اطلاعات مرتبطی برای پاسخ به این سؤال در سند پیدا نشد."
        return "No relevant information was found in the document."

    prompt = f"""
You are a document question-answering assistant.

Answer the question using ONLY the provided context.

Rules:
1. Do not use external knowledge.
2. If the context does not contain enough information, clearly state that
   the document does not provide enough information.
3. Write the entire answer in {answer_language}.
4. Do not include source names, page numbers, chunk numbers, or citations.
5. Be direct and distinguish facts stated in the document from reasonable
   synthesis across multiple parts of the provided context.

Context:
{context}

Question:
{question}

Answer:
"""

    response = call_with_retry(
        lambda: client.models.generate_content(
            model=GENERATION_MODEL,
            contents=prompt,
        ),
        operation_name="Answer generation",
    )

    answer = getattr(response, "text", None)

    if not answer or not answer.strip():
        raise RuntimeError("Gemini returned an empty answer.")

    return answer.strip()


# ============================================================
# UI helpers
# ============================================================

def display_answer(text: str) -> None:
    """Render answers, with basic right-to-left support for Persian."""
    text = str(text)

    if contains_persian(text):
        import html

        safe_text = html.escape(text).replace("\n", "<br>")
        st.markdown(
            f"""
            <div dir="rtl"
                 style="text-align:right; line-height:1.9; white-space:normal;">
                {safe_text}
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(text)


def display_sources(sources: list[dict]) -> None:
    """Show retrieved document locations in a compact expander."""
    if not sources:
        return

    with st.expander("📚 Sources"):
        for source in sources:
            file_name = source.get("source", "Document")
            page = source.get("page")
            chunk_index = source.get("chunk_index")

            if page is not None:
                st.markdown(f"- **{file_name}** · Page {page}")
            else:
                st.markdown(f"- **{file_name}** · Section {chunk_index}")


def render_message(message: dict) -> None:
    """Render one stored chat message."""
    with st.chat_message(message["role"]):
        if message["role"] == "assistant":
            display_answer(message.get("content", ""))
            display_sources(message.get("sources", []))
        else:
            st.markdown(message.get("content", ""))


# ============================================================
# Application initialization
# ============================================================

if not API_KEY:
    st.error(
        "The Gemini API key is missing. Add GEMINI_API_KEY to your .env file."
    )
    st.stop()

try:
    gemini_client = get_gemini_client(API_KEY)
    collection = get_chroma_collection()
except Exception as error:
    logger.exception("Application initialization failed.")
    st.error(f"Application initialization failed: {friendly_error_message(error)}")
    st.stop()


if "messages" not in st.session_state:
    st.session_state.messages = []

if "active_file_id" not in st.session_state:
    st.session_state.active_file_id = None


# ============================================================
# Document upload and indexing
# ============================================================

st.subheader("Your document")

uploaded_file = st.file_uploader(
    "Choose a PDF or DOCX file",
    type=["pdf", "docx"],
    accept_multiple_files=False,
    label_visibility="collapsed",
)

current_file_id = None
document_ready = False

if uploaded_file is not None:
    file_bytes = uploaded_file.getvalue()

    if not file_bytes:
        st.error("The selected file is empty.")

    elif len(file_bytes) > MAX_FILE_SIZE_MB * 1024 * 1024:
        st.error(
            f"The file is too large. Maximum supported size is {MAX_FILE_SIZE_MB} MB."
        )

    else:
        current_file_id = hashlib.sha256(file_bytes).hexdigest()

        if st.session_state.active_file_id != current_file_id:
            st.session_state.messages = []
            st.session_state.active_file_id = current_file_id

        st.markdown(
            f'<p class="document-label">Selected: <strong>{uploaded_file.name}</strong></p>',
            unsafe_allow_html=True,
        )

        try:
            existing_data = collection.get(
                where={"file_id": current_file_id},
                include=["metadatas"],
            )

            if existing_data.get("ids"):
                document_ready = True
            else:
                with st.spinner("Preparing your document..."):
                    process_document(
                        file_name=uploaded_file.name,
                        file_bytes=file_bytes,
                        file_id=current_file_id,
                        client=gemini_client,
                        collection=collection,
                    )
                document_ready = True

        except Exception as error:
            logger.exception("Document processing failed.")
            st.error(friendly_error_message(error, operation="document"))
            document_ready = False

else:
    if st.session_state.active_file_id is not None:
        st.session_state.active_file_id = None
        st.session_state.messages = []


# ============================================================
# Chat
# ============================================================

st.divider()
st.subheader("Conversation")

if not document_ready:
    st.caption("Upload a document to start asking questions.")

# Render stored history exactly once per Streamlit run.
for stored_message in st.session_state.messages:
    render_message(stored_message)

user_question = st.chat_input(
    "Ask a question about your document...",
    disabled=not document_ready,
)

if user_question and document_ready and current_file_id:
    # Store the user message once. The UI will render it after rerun.
    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_question,
        }
    )

    assistant_response = ""
    answer_sources = []

    try:
        with st.spinner("Searching the document and preparing an answer..."):
            context, retrieved_sources = retrieve_relevant_chunks(
                question=user_question,
                client=gemini_client,
                collection=collection,
                file_id=current_file_id,
                n_results=RETRIEVAL_RESULTS,
            )

            assistant_response = generate_rag_answer(
                question=user_question,
                context=context,
                client=gemini_client,
            )

            # Attach sources only when retrieval found context and
            # answer generation completed successfully.
            if context.strip():
                answer_sources = retrieved_sources

    except Exception as error:
        logger.exception("Question processing failed.")
        assistant_response = friendly_error_message(error)
        answer_sources = []

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": assistant_response,
            "sources": answer_sources,
        }
    )

    # Rerender the complete conversation from session state once.
    st.rerun()

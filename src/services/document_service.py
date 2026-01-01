import io
import re
import pdfplumber
import unicodedata
from docx import Document
from fastapi import UploadFile
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker
from src.utils.models import models
from pdf2image import convert_from_bytes
from src.utils.ocr import analyze_text_confidence, ocr_page_image
import logging

logger = logging.getLogger("document_ocr")
logger.setLevel(logging.INFO)

# FILE TEXT EXTRACTION
async def extract_text_from_file(file: UploadFile) -> str:
    filename = file.filename.lower()
    content = await file.read()

    if filename.endswith(".pdf"):
        return extract_text_from_pdf(content)

    elif filename.endswith(".docx"):
        return extract_text_from_docx(content)

    elif filename.endswith((".txt", ".csv")):
        return extract_text_from_txt(content)

    else:
        raise ValueError("Unsupported file format")


def extract_text_from_pdf(file_bytes: bytes) -> str:
    final_text = []

    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        total_pages = len(pdf.pages)

        for idx, page in enumerate(pdf.pages):
            page_no = idx + 1
            logger.info(f"[PAGE {page_no}/{total_pages}] Processing")

            # ---------- Layer 1: Native Text ----------
            native_text = page.extract_text() or ""
            confidence = analyze_text_confidence(native_text)

            image_count = len(page.images)
            tables = page.extract_tables()

            logger.info(
                f"[PAGE {page_no}] "
                f"confidence={confidence}, "
                f"images={image_count}, "
                f"tables={len(tables)}"
            )

            page_content = []

            # ---------- Layer 2: Tables ----------
            if tables:
                for table in tables:
                    table_text = "\n".join(
                        [" | ".join(cell or "" for cell in row) for row in table if row]
                    )
                    page_content.append(
                        f"\n--- TABLE Page {page_no} ---\n{table_text}"
                    )
                logger.info(f"[PAGE {page_no}] Tables extracted")

            # ---------- OCR DECISION  ----------
            run_ocr = (
                confidence < 0.6 and
                image_count > 0 and
                not tables
            )

            if run_ocr:
                logger.warning(f"[PAGE {page_no}] OCR triggered")

                # Convert ONLY this page to image
                page_image = convert_from_bytes(
                    file_bytes,
                    dpi=200,
                    first_page=page_no,
                    last_page=page_no,
                    poppler_path=r"C:\poppler-25.12.0\Library\bin"
                )[0]

                ocr_text = ocr_page_image(page_image, page_no)
                if ocr_text.strip():
                    page_content.append(ocr_text)
            else:
                logger.info(f"[PAGE {page_no}] OCR skipped")

            # ---------- Native Text ----------
            if native_text.strip():
                page_content.append(native_text)

            if page_content:
                final_text.append("\n".join(page_content))

    combined = "\n\n".join(final_text)

    if not combined.strip():
        raise ValueError("PDF extraction failed")

    return preprocess_text(combined)

def extract_text_from_docx(file_bytes: bytes) -> str:
    doc = Document(io.BytesIO(file_bytes))
    text = "\n".join([p.text for p in doc.paragraphs])
    return preprocess_text(text)

def extract_text_from_txt(file_bytes: bytes) -> str:
    text = file_bytes.decode("utf-8", errors="ignore")
    return preprocess_text(text)

# TEXT PREPROCESSING
def preprocess_text(text: str) -> str:
    # Remove null bytes
    text = text.replace("\x00", "")

    # Normalize unicode characters
    text = unicodedata.normalize("NFKC", text)

    # Remove common headers/footers
    text = re.sub(r"Page\s*\d+\s*(of\s*\d+)?", "", text, flags=re.IGNORECASE)

    # Replace special bullets safely
    text = re.sub(r"[•·●■□▪▶➤►]", "-", text)

    # Abbreviation normalization (medical-friendly)
    abbreviation_map = {
        r"\bROM\b": "Range of Motion",
        r"\bADL\b": "Activities of Daily Living",
        r"\bWNL\b": "Within Normal Limits",
        r"\bPT\b": "Physiotherapy",
        r"\bOT\b": "Occupational Therapy"
    }

    for abbr, full in abbreviation_map.items():
        text = re.sub(abbr, full, text)

    # Collapse multiple spaces/newlines
    text = re.sub(r"\n{2,}", "\n\n", text)
    text = re.sub(r"[ ]{2,}", " ", text)

    return text.strip()

# HYBRID CHUNKING (Semantic → Fallback Recursive)
def chunk_text(text: str, chunk_size: int = 512, chunk_overlap: int = 100):

    embeddings = models.embeddings

    # Semantic Chunker
    semantic_splitter = SemanticChunker(embeddings)
    semantic_chunks = semantic_splitter.split_text(text)

    # Recursive fallback for oversized chunks
    recursive_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""]
    )

    final_chunks = []
    for chunk in semantic_chunks:
        if len(chunk) > chunk_size:
            final_chunks.extend(recursive_splitter.split_text(chunk))
        else:
            final_chunks.append(chunk)

    return final_chunks

# EMBEDDING

def embed_chunks(chunks: list[str]):
    embeddings = models.embeddings
    vectors = embeddings.embed_documents(chunks)
    return vectors
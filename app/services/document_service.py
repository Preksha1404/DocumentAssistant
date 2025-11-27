import io
import re
import pdfplumber
import unicodedata
from docx import Document
from fastapi import UploadFile
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

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
    text = ""

    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"

    return preprocess_text(text)

def extract_text_from_docx(file_bytes: bytes) -> str:
    doc = Document(io.BytesIO(file_bytes))

    text = "\n".join([p.text for p in doc.paragraphs])

    return preprocess_text(text)

def extract_text_from_txt(file_bytes: bytes) -> str:
    text = file_bytes.decode("utf-8")

    return preprocess_text(text)

def preprocess_text(text: str) -> str:
    # Normalize unicode characters
    text = unicodedata.normalize("NFKC", text)

    # Remove headers/footers (common patterns)
    text = re.sub(r"Page\s*\d+\s*of\s*\d+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"Assessment Form.*?\n", "", text, flags=re.IGNORECASE)

    # Remove non-alphanumeric noise
    text = re.sub(r"[^\x00-\x7F]+", " ", text)  # remove non-ASCII
    text = re.sub(r"[•·●■□▪▶➤►]", "-", text)   # replace bullet symbols

    # Normalize abbreviations
    abbreviation_map = {
        "ROM": "Range of Motion",
        "ADL": "Activities of Daily Living",
        "WNL": "Within Normal Limits",
        "PT": "Physiotherapy",
        "OT": "Occupational Therapy",
        "L": "Left",
        "R": "Right"
    }

    for abbr, full in abbreviation_map.items():
        text = re.sub(rf"\b{abbr}\b", full, text)

    # Remove duplicate spaces/newlines
    text = re.sub(r"\n{2,}", "\n", text)
    text = re.sub(r" {2,}", " ", text)

    # Final strip
    return text.strip()

def chunk_text(text: str, chunk_size: int = 500, chunk_overlap: int = 100):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    return splitter.split_text(text)

# Embedding using Sentence Transformers
embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def embed_chunks(chunks: list[str]):
    embeddings = embedding_model.encode(chunks, convert_to_numpy=True)
    return embeddings.tolist()  # convert NumPy to list for JSON
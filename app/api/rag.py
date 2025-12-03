from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from google.generativeai import GenerativeModel
from app.utils.vector_store import get_or_create_collection
from app.models.users import User
from app.utils.auth_dependencies import get_current_user

# Upload → Extract → Preprocess → Chunk → Embed → Store → (User asks) → Query Embed → Retrieve → Build Prompt → Gemini → Response

# Load embedding model once
embedding_model = SentenceTransformer("pritamdeka/BioBERT-mnli-snli-scinli-scitail-mednli-stsb")

# Gemini Model
gemini_model = GenerativeModel("gemini-2.5-flash")

router = APIRouter(prefix="/rag", tags=["RAG"])

# Request Schema
class AskRequest(BaseModel):
    question: str
    k: int = 5

# RAG Endpoint
@router.post("/ask")
async def ask_rag(payload: AskRequest, current_user: User = Depends(get_current_user)):

    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    question = payload.question
    k = payload.k

    # STEP 1: Embed user question
    try:
        query_embedding = embedding_model.encode(question).tolist()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding failed: {str(e)}")

    # STEP 2: Retrieve from ChromaDB
    try:
        collection = get_or_create_collection("physio_docs")

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            include=["documents", "metadatas", "distances"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vector DB query failed: {str(e)}")

    # Parse retrieved chunks
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]
    ids = results["ids"][0]

    # Prepare clean structure for prompt + response
    retrieved_chunks = []
    for i in range(len(documents)):
        retrieved_chunks.append({
            "id": ids[i],
            "filename": metadatas[i].get("filename", "unknown"),
            "document": documents[i],
            "distance": distances[i]
        })

    # STEP 3: Build RAG Prompt
    snippets = ""
    for idx, chunk in enumerate(retrieved_chunks, start=1):
        snippets += (
            f"\n=== SNIPPET {idx} ===\n"
            f"ID: {chunk['id']}\n"
            f"FILE: {chunk['filename']}\n"
            f"CONTENT: {chunk['document']}\n"
        )

    final_prompt = f"""
    You are a Retrieval-Augmented Generation (RAG) assistant.

    Use the document snippets BELOW to answer the user’s question.  
    You are allowed to *combine information across snippets* and *infer meaning*  
    as long as your answer is directly supported by the content.

    Rules:
    - If the answer is clearly supported anywhere in the snippets, answer normally.
    - If information is spread across multiple bullets or paragraphs, combine them.
    - If the exact wording isn't present but the meaning is present, answer.
    - Only if NONE of the snippets contain relevant information, reply: 
    "Not available in the document."

    SNIPPETS:
    {snippets}

    User Question: {question}

    Provide:
    1. The best possible answer based on the snippets.
    2. The snippet IDs you used.
    """

    # STEP 4: Call Gemini 2.5 Flash
    try:
        answer = gemini_model.generate_content(final_prompt).text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM call failed: {str(e)}")

    # STEP 5: Return response
    return {
        "answer": answer,
        "sources": retrieved_chunks
    }
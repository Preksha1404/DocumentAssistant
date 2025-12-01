from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from google.generativeai import GenerativeModel
from app.utils.vector_store import get_or_create_collection
from app.models.users import User
from app.utils.auth_dependencies import get_current_user

# Upload → Extract → Preprocess → Chunk → Embed → Store → (User asks) → Query Embed → Retrieve → Build Prompt → Gemini → Response

# Load embedding model once
embedding_model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")

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
    You are a RAG assistant. 
    Answer the question **using ONLY the document snippets provided below**.
    If the answer is not present in the snippets, respond with: "Not available in the document."

    {snippets}

    User Question: {question}

    Provide a clear answer and list the snippet IDs used.
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
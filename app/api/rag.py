from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from google.generativeai import GenerativeModel
from app.models.users import User
from app.utils.auth_dependencies import get_current_user
from app.services.rag_service import run_rag_query

# Upload → Extract → Preprocess → Chunk → Embed → Store → (User asks) → Query Embed → Retrieve → Build Prompt → Gemini → Response

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

    try:
        result = run_rag_query(payload.question, payload.k)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return result
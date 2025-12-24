from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from src.models.users import User
# from app.utils.subscription import require_active_subscription
from src.utils.auth_dependencies import get_current_user
from src.services.rag_service import run_rag_query
from langchain_google_vertexai import ChatVertexAI
from src.utils.models import models
from src.utils.evaluate_rag import build_ragas_dataset
from ragas import evaluate
import json
import asyncio
from ragas.metrics import (
    faithfulness,
    answer_correctness,
    context_precision,
    context_recall
)

def get_gemini_llm():
    return ChatVertexAI(
        model_name="gemini-2.5-flash",
        temperature=0.0,
    )

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

@router.get("/evaluate")
async def evaluate_rag(current_user: User = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Load evaluation questions
    with open("data.json", "r") as f:
        test_data = json.load(f)

    # Build RAGAS dataset using your RAG pipeline
    dataset = build_ragas_dataset(test_data)

    # Create Gemini LLM
    gemini_llm = get_gemini_llm()

    # Run blocking RAGAS evaluation safely
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        lambda: evaluate(
            dataset=dataset,
            metrics=[
                faithfulness,
                answer_correctness,
                context_precision,
                context_recall
            ],
            llm=gemini_llm,
            embeddings=models.embeddings,
            batch_size=1 
        )
    )

    return result.scores
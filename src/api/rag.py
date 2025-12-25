from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from src.models.users import User
from src.utils.subscription import require_active_subscription
# from src.utils.auth_dependencies import get_current_user
from src.services.rag_service import run_rag_query
from src.utils.models import models

def get_gemini_llm():
    return models.llm

# Upload → Extract → Preprocess → Chunk → Embed → Store → (User asks) → Query Embed → Retrieve → Build Prompt → Gemini → Response

router = APIRouter(prefix="/rag", tags=["RAG"])

# Request Schema
class AskRequest(BaseModel):
    question: str
    k: int = 5

# RAG Endpoint
@router.post("/ask")
async def ask_rag(payload: AskRequest, current_user: User = Depends(require_active_subscription)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        result = run_rag_query(payload.question, payload.k)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return result

@router.get("/evaluate")
async def evaluate_rag(current_user: User = Depends(require_active_subscription)):
    if os.getenv("ENV") == "production":
        raise HTTPException(
            status_code=403,
            detail="RAG evaluation is disabled in production",
    )

    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Load evaluation questions
    with open("data.json", "r") as f:
        test_data = json.load(f)

    from src.utils.evaluate_rag import build_ragas_dataset
    from ragas import evaluate
    import os
    import json
    import asyncio
    from ragas.metrics import (
        faithfulness,
        answer_correctness,
        context_precision,
        context_recall
    )
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
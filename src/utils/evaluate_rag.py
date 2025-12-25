import os

# Block evaluation in production
if os.getenv("ENV") == "production":
    raise RuntimeError("RAG evaluation is disabled in production")

from datasets import Dataset
from src.services.rag_service import run_rag_query

def build_ragas_dataset(data):
    questions = []
    answers = []
    contexts = []
    ground_truths = []

    for item in data:
        result = run_rag_query(item["question"])

        questions.append(item["question"])
        answers.append(result["answer"])
        ground_truths.append(item["ground_truth"])

        # contexts must be a list of strings
        # contexts.append(
        #     [snippet.strip() for snippet in result["snippets"].split("=== SNIPPET") if snippet.strip()]
        # )

        clean_contexts = []

        for snippet in result["snippets"].split("=== SNIPPET"):
            if "CONTENT:" in snippet:
                content = snippet.split("CONTENT:", 1)[1].strip()
                if content:
                    clean_contexts.append(content)

        # Safety fallback
        if not clean_contexts:
            clean_contexts = ["No relevant context found"]

        contexts.append(clean_contexts)

    return Dataset.from_dict({
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths
    })
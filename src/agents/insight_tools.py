from langchain.tools import tool
from src.utils.models import models
from src.agents.context import context
from src.core.database import get_db
from src.utils.document_store import load_full_documents

@tool
def summarize_tool():
    """
    Summarize the currently selected document.
    """
    if not context.user_id:
        return "No user context available."

    if not context.active_document_id:
        return "No document selected."

    db = next(get_db())
    raw_text = load_full_documents(
        user_id=context.user_id,
        db=db,
        document_id=context.active_document_id
    )

    if not raw_text:
        return "Document not found."

    prompt = f"""
Summarize the following medical/physiotherapy document clearly and concisely.
Return 5 bullet points.

Document:
{raw_text}
"""
    response = models.llm.generate_content(prompt)
    return response.text

@tool
def topic_tool():
    """
    Identify the most relevant topic for the selected document.
    """
    if not context.user_id:
        return "No user context available."

    if not context.active_document_id:
        return "No document selected."

    db = next(get_db())
    raw_text = load_full_documents(
        user_id=context.user_id,
        db=db,
        document_id=context.active_document_id
    )

    if not raw_text:
        return "Document not found."

    prompt = f"""
Identify the SINGLE most relevant topic for the following physiotherapy document.

Choose or infer one:
- exercise therapy
- manual therapy
- electrotherapy
- pain management
- rehabilitation

Document:
{raw_text}

Return the topic name and a brief explanation.
"""
    response = models.llm.generate_content(prompt)
    return response.text.strip()

@tool
def sentiment_tool():
    """
    Analyze sentiment of the selected medical document.
    """
    if not context.user_id:
        return "No user context available."

    if not context.active_document_id:
        return "No document selected."

    db = next(get_db())
    raw_text = load_full_documents(
        user_id=context.user_id,
        db=db,
        document_id=context.active_document_id
    )

    if not raw_text:
        return "Document not found."

    prompt = f"""
Analyze the sentiment of the following medical document.

Classify as:
- Positive
- Neutral
- Negative

Document:
{raw_text}

Return sentiment and a short explanation.
"""
    response = models.llm.generate_content(prompt)
    return response.text
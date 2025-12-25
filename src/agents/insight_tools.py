from langchain.tools import tool
from src.utils.models import models
from src.core.database import get_db
from src.utils.document_store import load_full_documents
from langchain_core.runnables import RunnableConfig

@tool
def summarize_tool(config: RunnableConfig):
    """
    Summarize the selected physiotherapy document.
    """
    state = config["configurable"]["agent_state"]
    if not state.user_id:
        return "No user context available."

    if not state.active_document_id:
        return "No document selected."

    db = next(get_db())
    raw_text = load_full_documents(
        user_id=state.user_id,
        db=db,
        document_id=state.active_document_id
    )

    if not raw_text:
        return "Document not found."

    prompt = f"""
Summarize the following medical/physiotherapy document clearly and concisely.
Return 5 bullet points.

Document:
{raw_text}
"""
    response = models.llm.invoke(prompt)
    return response.content

@tool
def topic_tool(config: RunnableConfig):
    """
    Identify the relevant topics for the selected document.
    """
    state = config["configurable"]["agent_state"]
    if not state.user_id:
        return "No user context available."

    if not state.active_document_id:
        return "No document selected."

    db = next(get_db())
    raw_text = load_full_documents(
        user_id=state.user_id,
        db=db,
        document_id=state.active_document_id
    )

    if not raw_text:
        return "Document not found."

    prompt = f"""
Identify the most relevant topic for the following physiotherapy document.

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
    response = models.llm.invoke(prompt)
    return response.content.strip()

@tool
def sentiment_tool(config: RunnableConfig):
    """
    Analyze sentiment of the selected physiotherapy document.
    """
    state = config["configurable"]["agent_state"]
    if not state.user_id:
        return "No user context available."

    if not state.active_document_id:
        return "No document selected."

    db = next(get_db())
    raw_text = load_full_documents(
        user_id=state.user_id,
        db=db,
        document_id=state.active_document_id
    )

    if not raw_text:
        return "Document not found."

    prompt = f"""
Analyze the sentiment of the following physiotherapy document.

Classify as:
- Positive
- Neutral
- Negative

Document:
{raw_text}

Return sentiment and a short explanation.
"""
    response = models.llm.invoke(prompt)
    return response.content
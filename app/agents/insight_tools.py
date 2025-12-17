from langchain.tools import tool
from app.utils.models import models
from app.agents.context import context
from app.core.database import get_db
from app.utils.document_store import load_full_documents

@tool
def summarize_tool():
    """
    Summarize full raw documents for the current context user.
    """
    if not context.user_id:
        return "No user context available."

    db = next(get_db())  # safely create a session inside the tool
    raw_text = load_full_documents(context.user_id, db)

    if not raw_text:
        return "No documents found for summarization."

    prompt = f"""
Summarize the following medical/physiotherapy documents clearly and concisely.
Return 5 bullet points.

Documents:
{raw_text}
"""
    response = models.llm.generate_content(prompt)
    return response.text

@tool
def topic_tool():
    """
    Identify the most relevant topic from the user's physiotherapy documents.
    """
    if not context.user_id:
        return "No user context available."

    db = next(get_db())
    raw_text = load_full_documents(context.user_id, db)
    if not raw_text:
        return "No documents found for topic classification."

    prompt = f"""
Identify the SINGLE most relevant topic for the following physiotherapy documents.
Choose or infer one:

- exercise therapy
- manual therapy
- electrotherapy
- pain management
- rehabilitation

Documents:
{raw_text}

Return only the topic name.
"""
    response = models.llm.generate_content(prompt)
    return response.text.strip()

@tool
def sentiment_tool():
    """
    Analyze sentiment of the user's medical or physiotherapy documents.
    """
    if not context.user_id:
        return "No user context available."

    db = next(get_db())
    raw_text = load_full_documents(context.user_id, db)
    if not raw_text:
        return "No documents found for sentiment analysis."

    prompt = f"""
Analyze the sentiment of the following medical documents.

Classify as:
- Positive
- Neutral
- Negative

Documents:
{raw_text}

Return sentiment and a short explanation.
"""
    response = models.llm.generate_content(prompt)
    return response.text
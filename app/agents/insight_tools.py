from langchain.tools import tool
from app.utils.models import models
from app.agents.context import context

@tool
def summarize_tool():
    """
    Summarize previously retrieved documents from context.
    """
    if not context.retrieved_docs:
        return "No documents loaded. Please retrieve documents first."

    prompt = f"""
Summarize the following medical/physiotherapy documents clearly and concisely.

Return 5 bullet points.

Documents:
{context.retrieved_docs}
"""
    response = models.llm.generate_content(prompt)
    return response.text

@tool
def topic_tool():
    """
    Classify the main topic of previously retrieved documents.
    """
    if not context.retrieved_docs:
        return "No documents loaded. Please retrieve documents first."

    prompt = f"""
Identify the SINGLE most relevant topic for the following physiotherapy documents.
Choose or infer one:

- exercise therapy
- manual therapy
- electrotherapy
- pain management
- rehabilitation

Documents:
{context.retrieved_docs}

Return only the topic name.
"""
    response = models.llm.generate_content(prompt)
    return response.text.strip()

@tool
def sentiment_tool():
    """
    Analyze sentiment of previously retrieved documents.
    """
    if not context.retrieved_docs:
        return "No documents loaded. Please retrieve documents first."

    prompt = f"""
Analyze the sentiment of the following medical documents.

Classify as:
- Positive
- Neutral
- Negative

Documents:
{context.retrieved_docs}

Return sentiment and a short explanation.
"""
    response = models.llm.generate_content(prompt)
    return response.text




# from langchain.tools import tool
# from app.utils.models import models

# llm = models.llm

# @tool
# def summarize_tool(text: str):
#     """
#     Summarizes the given text into a concise summary.
#     """
#     summary = models.summarizer(text)[0]["summary_text"]
#     return f"Summary:\n{summary}"

# @tool
# def topic_tool(text: str):
#     """
#     Classifies the main topic of the given text using predefined healthcare-related labels.
#     """
#     labels = [
#         "exercise therapy",
#         "manual therapy",
#         "electrotherapy",
#         "pain management",
#         "rehabilitation",
#     ]
#     result = models.topic_classifier(text, labels)
#     topic = result["labels"][0]
#     return f"Detected Topic: {topic}"

# @tool
# def sentiment_tool(text: str):
#     """
#     Detects the sentiment of the given text and returns the label with confidence score.
#     """
#     output = models.sentiment(text)[0]
#     label = output["label"]
#     score = round(output["score"], 3)
#     return f"Sentiment: {label} (confidence: {score})"
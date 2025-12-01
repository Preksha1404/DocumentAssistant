from langchain.tools import tool
from google.generativeai import GenerativeModel

llm = GenerativeModel("gemini-2.5-flash")

@tool
def summarize_tool(query: str):
    """Summarize any text."""
    return llm.generate_content(f"Summarize:\n{query}").text

@tool
def topic_tool(query: str):
    """Classify topic."""
    return llm.generate_content(f"Give main topic:\n{query}").text

@tool
def sentiment_tool(query: str):
    """Return sentiment (positive/neutral/negative)."""
    return llm.generate_content(f"Sentiment:\n{query}").text

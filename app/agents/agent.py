from langchain.agents import create_agent
from langchain_google_vertexai import ChatVertexAI
from app.agents.rag_tool import rag_tool, search_docs
from app.agents.insight_tools import summarize_tool, topic_tool, sentiment_tool
import os
import vertexai

vertexai.init(
    project=os.getenv("GOOGLE_CLOUD_PROJECT")
)

model = ChatVertexAI(
    model_name="gemini-2.5-flash",
    temperature=0.1,
)

SYSTEM_PROMPT = """
You are an AI Agent with autonomous tool abilities.

TOOLS:
1. search_docs → Retrieves relevant RAW text chunks from stored documents.
2. rag_tool → Performs full RAG (retrieval + LLM reasoning) to answer document-based questions.
3. summarize_tool → Summarizes text, but ONLY after retrieving text using search_docs.
4. topic_tool → Classifies topic, but ONLY after retrieving text using search_docs.
5. sentiment_tool → Returns sentiment, but ONLY after retrieving text using search_docs.

RULES:

### Document-Based Questions
- ALWAYS use search_docs first when user asks to:
  - summarize document content
  - classify the topic of document content
  - perform sentiment analysis on document content
- NEVER apply summarize_tool, topic_tool, or sentiment_tool directly to the user query.
- The pipeline must be:
  1) search_docs(query) → get relevant text  
  2) summarize_tool/topic_tool/sentiment_tool on the retrieved text

### RAG Questions
- If the user asks a question that requires reasoning over the knowledge:
  → Use rag_tool directly.

### Tool Selection Logic
- “Summarize …” → search_docs → summarize_tool
- “What is the topic of …” → search_docs → topic_tool
- “What is the sentiment of …” → search_docs → sentiment_tool
- “What does the document say about …” → rag_tool
- “Answer based on my documents …” → rag_tool

### General Rules
- NEVER ask users to upload or provide the document content.
- ALWAYS rely on search_docs or rag_tool.
- Final message must always be normal language to the user.
"""

# AI Agent Executor --> Initialize Agent
agent = create_agent(
    model=model,
    tools=[search_docs,rag_tool, summarize_tool, topic_tool, sentiment_tool],
    system_prompt=SYSTEM_PROMPT,
)
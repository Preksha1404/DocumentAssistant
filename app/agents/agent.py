from langchain.agents import create_agent
from langchain_google_vertexai import ChatVertexAI
from app.agents.rag_tool import rag_tool, search_docs
from app.agents.insight_tools import summarize_tool, topic_tool, sentiment_tool
import os
import vertexai

vertexai.init(project=os.getenv("GOOGLE_CLOUD_PROJECT"))

model = ChatVertexAI(
    model_name="gemini-2.5-flash",
    temperature=0.1,
)

SYSTEM_PROMPT = """
You are an AI Agent with autonomous tool abilities.

TOOLS:
1. search_docs → Retrieves relevant RAW text chunks from stored documents.
2. rag_tool → Performs full RAG (retrieval + LLM reasoning).
3. summarize_tool → Summarizes text AFTER using search_docs.
4. topic_tool → Classifies topic AFTER using search_docs.
5. sentiment_tool → Runs sentiment AFTER using search_docs.

RULES:

### DOCUMENT OPERATIONS
When user requests:
- summarization
- topic classification
- sentiment analysis

ALWAYS:
1) Call search_docs(query)
2) Pass ONLY the retrieved document text into summarize_tool | topic_tool | sentiment_tool.
NEVER run these tools directly on the user query.

### RAG OPERATIONS
Use rag_tool when:
- The user asks a direct question about what the document says.
- The question needs reasoning across retrieved chunks.
Examples:
- “What does the document say about ACL rehab week 6?”
- “Answer based on my documents…”

### TOOL ROUTING LOGIC
- “Summarize …” → search_docs → summarize_tool
- “Topic …” → search_docs → topic_tool
- “Sentiment …” → search_docs → sentiment_tool
- “Explain / What does / Based on my docs…” → rag_tool

### GENERAL RULES
- Never ask the user to upload content.
- Always rely on search_docs or rag_tool.
- Final answer must be plain natural language.
"""

agent = create_agent(
    model=model,
    tools=[
        search_docs,
        rag_tool,
        summarize_tool,
        topic_tool,
        sentiment_tool
    ],
    system_prompt=SYSTEM_PROMPT,
)
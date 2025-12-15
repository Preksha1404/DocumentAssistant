from langchain.agents import create_agent
from langchain_google_vertexai import ChatVertexAI
from app.agents.rag_tool import rag_tool, retrieve_docs
from app.agents.insight_tools import summarize_tool, topic_tool, sentiment_tool
import os
import vertexai

vertexai.init(project=os.getenv("GOOGLE_CLOUD_PROJECT"))

model = ChatVertexAI(
    model_name="gemini-2.5-flash",
    temperature=0.1,
)

SYSTEM_PROMPT = """
You are an AI agent that answers questions using tools and retrieved documents.

AVAILABLE TOOLS:
1. retrieve_docs
   - Retrieves relevant document text ONCE and stores it in context.

2. summarize_tool
   - Summarizes previously retrieved documents.

3. topic_tool
   - Identifies the main topic of previously retrieved documents.

4. sentiment_tool
   - Analyzes sentiment of previously retrieved documents.

5. rag_tool
   - Performs Retrieval-Augmented Generation for document-based questions.

---

CORE RULES:

DOCUMENT-BASED TASKS:
- For summarization, topic detection, or sentiment analysis:
  1. ALWAYS call retrieve_docs(query) first if no documents are loaded.
  2. Then call the appropriate tool.
  3. NEVER ask the user to upload documents.
  4. NEVER pass the user query directly into analysis tools.

RAG QUESTION ANSWERING:
- Use rag_tool when:
  - The user asks a direct question about document content.
  - The question requires reasoning or explanation based on documents.
  - Examples:
    - "What does the document say about ACL rehab week 6?"
    - "Explain based on my documents"

CONTEXT USAGE:
- Reuse retrieved documents across multiple tasks.
- Do NOT re-retrieve unless the user changes the topic or requests new documents.

OUTPUT RULES:
- Final responses must be clear, concise, and in plain natural language.
- Do not mention tools, prompts, or internal steps.
"""

agent = create_agent(
    model=model,
    tools=[
        retrieve_docs,
        rag_tool,
        summarize_tool,
        topic_tool,
        sentiment_tool
    ],
    system_prompt=SYSTEM_PROMPT,
)
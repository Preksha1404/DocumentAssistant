import os
import vertexai
from langchain.agents import create_agent
from langchain_google_vertexai import ChatVertexAI
from app.agents.rag_tool import rag_tool, retrieve_docs
from app.agents.insight_tools import (
    summarize_tool,
    topic_tool,
    sentiment_tool
)

vertexai.init(project=os.getenv("GOOGLE_CLOUD_PROJECT"))

model = ChatVertexAI(
    model_name="gemini-2.5-flash",
    temperature=0.1,
)

SYSTEM_PROMPT = """
You are an autonomous document intelligence AI agent.

Your job is to decide which tools to use based on user intent.

RULES:

1. For summary / topic / sentiment:
   - retrieve_docs MUST be used first if documents are not cached.

2. For factual or explanatory questions:
   - use rag_tool.

3. Reuse cached documents when available.

4. Never ask the user to upload documents.
5. Never mention tools or internal steps.
6. If no documents exist, say you cannot answer.

Respond concisely and grounded in documents.
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
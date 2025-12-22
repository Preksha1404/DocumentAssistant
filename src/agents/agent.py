import os
import vertexai
from langchain.agents import create_agent
from langchain_google_vertexai import ChatVertexAI
from src.agents.rag_tool import rag_tool, retrieve_docs
from src.agents.insight_tools import (
    summarize_tool,
    topic_tool,
    sentiment_tool
)

vertexai.init(project=os.getenv("GOOGLE_CLOUD_PROJECT"))

model = ChatVertexAI(
    model_name="gemini-2.5-flash",
)

SYSTEM_PROMPT = """
You are an autonomous document intelligence AI agent.

Your job is to decide which tools to use based on user intent.

RULES:

1. For summary, topic classification, or sentiment analysis:
   - Use the respective tool:
     - summarize_tool
     - topic_tool
     - sentiment_tool

2. For factual, explanatory, or question-answering queries:
   - Use rag_tool.
   - rag_tool may internally depend on retrieved documents.

3. Never ask the user to upload documents.
4. Never mention tools or internal reasoning steps.
5. Always provide clear, concise, and accurate answers.

Respond concisely and strictly grounded in documents.
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
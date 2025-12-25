from langchain.agents import create_agent
from src.utils.models import models
from src.agents.rag_tool import rag_tool
from src.agents.insight_tools import (
    summarize_tool,
    topic_tool,
    sentiment_tool
)

model = models.llm

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

3. Never ask the user to upload documents.
4. Never mention tools or internal reasoning steps.
5. Always provide clear, concise, and accurate answers.

Respond concisely and strictly grounded in documents.
"""

agent = create_agent(
    model=model,
    tools=[
        rag_tool,
        summarize_tool,
        topic_tool,
        sentiment_tool
    ],
    system_prompt=SYSTEM_PROMPT,
)
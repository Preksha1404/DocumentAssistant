from langchain.tools import tool
from src.services.rag_service import run_rag_query
    
@tool
def rag_tool(query: str, k: int = 5):
    """
    Perform Retrieval-Augmented Generation over stored documents.
    """
    return run_rag_query(query, k)
from langchain.tools import tool
from src.services.rag_service import run_rag_query
from src.services.document_service import embed_chunks
from src.utils.vector_store import get_or_create_collection
from src.agents.context import context
    
@tool
def rag_tool(query: str, k: int = 5):
    """
    Perform Retrieval-Augmented Generation over stored documents.
    """
    return run_rag_query(query, k)
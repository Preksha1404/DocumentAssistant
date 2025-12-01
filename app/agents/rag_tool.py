from langchain.tools import tool
from app.services.rag_service import run_rag_query
from app.services.document_service import embed_chunks
from app.utils.vector_store import get_or_create_collection

@tool
def search_docs(query: str):
    """Retrieve relevant documents from ChromaDB."""
    try:
        # Get ChromaDB collection
        collection = get_or_create_collection("physio_docs")

        # Create embedding for query
        query_embedding = embed_chunks([query])[0]  # returns a single vector

        # Query database
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=5  # return top 5 matches
        )

        docs = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]

        # Format nicely
        response = ""
        for doc, meta in zip(docs, metadatas):
            response += f"From {meta['filename']}:\n{doc}\n\n"

        return response if response else "No relevant document found."

    except Exception as e:
        return f"Error retrieving documents: {str(e)}"
    
@tool
def rag_tool(query: str, k: int = 5):
    """
    Perform Retrieval-Augmented Generation over stored documents.
    Returns the answer and retrieved metadata.
    """
    return run_rag_query(query, k)

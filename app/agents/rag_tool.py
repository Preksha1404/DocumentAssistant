from langchain.tools import tool
from app.services.rag_service import run_rag_query
from app.services.document_service import embed_chunks
from app.utils.vector_store import get_or_create_collection

@tool
def search_docs(query: str):
    """Retrieve relevant raw text chunks from ChromaDB."""
    try:
        collection = get_or_create_collection("physio_docs")

        # Embed query
        query_embedding = embed_chunks([query])[0]

        # Query database for top 5 results
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=5
        )

        # Flatten all retrieved text chunks
        all_docs = []
        documents = results.get("documents", [])
        for doc_list in documents:
            all_docs.extend(doc_list)

        # Join all text chunks into a single string
        text = "\n\n".join(all_docs).strip()

        if not text:
            return "No relevant document found."

        return text

    except Exception as e:
        return f"Error retrieving documents: {str(e)}"
    
@tool
def rag_tool(query: str, k: int = 5):
    """
    Perform Retrieval-Augmented Generation over stored documents.
    Returns the answer and retrieved metadata.
    """
    return run_rag_query(query, k)

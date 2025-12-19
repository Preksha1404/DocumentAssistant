from langchain.tools import tool
from src.services.rag_service import run_rag_query
from src.services.document_service import embed_chunks
from src.utils.vector_store import get_or_create_collection
from src.agents.context import context

@tool
def retrieve_docs(query: str):
    """
    Retrieve relevant raw text chunks ONCE and store them in context.
    """
    try:
        collection = get_or_create_collection("physio_docs")

        # Embed query
        query_embedding = embed_chunks([query])[0]

        # Query database
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=5
        )

        all_docs = []
        documents = results.get("documents", [])
        for doc_list in documents:
            all_docs.extend(doc_list)

        if not all_docs:
            context.retrieved_docs = None
            return "No relevant document found."

        # Store retrieved docs in context
        context.retrieved_docs = "\n\n".join(all_docs).strip()
        context.last_query = query

        return "Documents retrieved and cached successfully."

    except Exception as e:
        context.retrieved_docs = None
        return f"Error retrieving documents: {str(e)}"
    
@tool
def rag_tool(query: str, k: int = 5):
    """
    Perform Retrieval-Augmented Generation over stored documents.
    """
    if not context.retrieved_docs:
        retrieve_docs.invoke({"query": query})

    return run_rag_query(query, k)
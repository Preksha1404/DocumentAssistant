from app.utils.vector_store import get_or_create_collection
from app.utils.models import models

gemini_model = models.llm
embeddings= models.embeddings

def run_rag_query(question: str, k: int = 5):
    # Embed
    query_embedding = models.embeddings.embed_query(question)

    # Retrieve
    collection = get_or_create_collection("physio_docs")
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=k,
        include=["documents", "metadatas", "distances"]
    )

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    ids = results["ids"][0]
    distances = results["distances"][0]

    snippets = ""
    
    for i in range(len(documents)):
        snippets += (
            f"\n=== SNIPPET {i+1} ===\n"
            f"ID: {ids[i]}\n"
            f"FILE: {metadatas[i].get('filename', 'unknown')}\n"
            f"CONTENT: {documents[i]}\n"
        )
        
    final_prompt = f"""
You are an intelligent Retrieval-Augmented Generation (RAG) assistant.

Use the document SNIPPETS below to answer the user's question — even if the user
asks for:
- titles
- page count
- highlights
- key insights
- purpose of the document
- structure
- metadata
- summaries
- recommendations
- creative outputs based on document content

You may **infer, reason, summarize, or create suggestions** using the snippet content.

RULES:
1. Always use the information and themes found in the snippets.
2. If the answer is not explicitly written, you may INFER or CREATE it based on the document’s content.
3. Only if the snippets are completely irrelevant to the question, reply:
   "Not available in the document."
4. Otherwise, ALWAYS give the best possible answer.

SNIPPETS:
{snippets}

User Question: {question}

Respond with:
Answer:

"""

    answer = gemini_model.generate_content(final_prompt).text

    return {
        "answer": answer,
        "snippets": snippets,
        "distances": distances
    }
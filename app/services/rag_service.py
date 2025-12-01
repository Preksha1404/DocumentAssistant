from sentence_transformers import SentenceTransformer
from google.generativeai import GenerativeModel
from app.utils.vector_store import get_or_create_collection

embedding_model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
gemini_model = GenerativeModel("gemini-2.5-flash")

def run_rag_query(question: str, k: int = 5):
    # Embed
    query_embedding = embedding_model.encode(question).tolist()

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
        snippets += f"""
=== SNIPPET {i+1} ===
ID: {ids[i]}
FILE: {metadatas[i].get("filename", "unknown")}
CONTENT: {documents[i]}
"""

    final_prompt = f"""
Use ONLY the following snippets to answer:

{snippets}

User Question: {question}

If answer is not found, say "Not available in the document."
Mention snippet IDs used.
"""

    answer = gemini_model.generate_content(final_prompt).text

    return {
        "answer": answer,
        "snippets": snippets,
        "distances": distances
    }

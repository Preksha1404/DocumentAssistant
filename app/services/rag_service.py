from sentence_transformers import SentenceTransformer
from google.generativeai import GenerativeModel
from app.utils.vector_store import get_or_create_collection

embedding_model = SentenceTransformer("pritamdeka/BioBERT-mnli-snli-scinli-scitail-mednli-stsb")
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
    You are a Retrieval-Augmented Generation (RAG) assistant.

    Use the document snippets BELOW to answer the user’s question.  
    You are allowed to *combine information across snippets* and *infer meaning*  
    as long as your answer is directly supported by the content.

    Rules:
    - If the answer is clearly supported anywhere in the snippets, answer normally.
    - If information is spread across multiple bullets or paragraphs, combine them.
    - If the exact wording isn't present but the meaning is present, answer.
    - Only if NONE of the snippets contain relevant information, reply: 
    "Not available in the document."

    SNIPPETS:
    {snippets}

    User Question: {question}

    Provide:
    1. The best possible answer based on the snippets.
    2. The snippet IDs you used.
    """

    answer = gemini_model.generate_content(final_prompt).text

    return {
        "answer": answer,
        "snippets": snippets,
        "distances": distances
    }
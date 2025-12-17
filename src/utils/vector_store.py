import chromadb

# Persistent local vector database
def get_chroma_client():
    return chromadb.PersistentClient(path="./chroma_data")

def get_or_create_collection(name="physio_docs"):
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"}
    )

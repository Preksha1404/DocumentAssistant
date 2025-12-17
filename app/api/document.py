from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from app.models.users import User
# from app.utils.subscription import require_active_subscription
from app.services.document_service import extract_text_from_file, chunk_text, embed_chunks
from app.utils.vector_store import get_or_create_collection
from sentence_transformers import util
from app.utils.auth_dependencies import get_current_user
from app.core.database import get_db
from app.models.documents import Document

router = APIRouter(prefix="/documents", tags=["Documents"])

# Data Ingestion Pipeline --> 
# Upload document
# Extract text from document
# Preprocess text from text
# Chunk the documents
# Generate embeddings for chunks
# Store chunks and embeddings into vector DB

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
    ):

    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        # Extract text
        text_content = await extract_text_from_file(file)

        # Save raw text to PostgreSQL
        doc_record = Document(
            user_id=current_user.id,
            filename=file.filename,
            content=text_content
        )
        db = next(get_db())
        db.add(doc_record)
        db.commit()
        db.refresh(doc_record)
    
        # Chunk text
        chunks = chunk_text(text_content)
        # for i, ch in enumerate(chunks):
        #     print(f"\n===== CHUNK {i+1} (len={len(ch)}) =====")
        #     print(ch)

        # Create embeddings
        embeddings = embed_chunks(chunks)

        # for i in range(len(chunks)-1):
        #     sim = util.cos_sim(embeddings[i], embeddings[i+1])
        #     print(i, float(sim))

        # Store in vector DB (ChromaDB)
        collection = get_or_create_collection("physio_docs")

        # Generate unique IDs for each chunk
        ids = [f"{file.filename}_{i}" for i in range(len(chunks))]

        # Add to ChromaDB
        collection.add(
            ids=ids,
            documents=chunks,
            embeddings=embeddings,
            metadatas=[{"filename": file.filename, "user_id": current_user.id}] * len(chunks)
        )

        return JSONResponse(content={
            "message": "Document stored successfully",
            "filename": file.filename,
            "total_chunks": len(chunks)
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

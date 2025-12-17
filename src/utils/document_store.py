from src.models.documents import Document
from sqlalchemy.orm import Session

def load_full_documents(user_id: int, db: Session, filenames: list[str] | None = None) -> str:
    """
    Fetch full raw text from PostgreSQL for the given user.
    Optionally filter by filenames.
    """
    query = db.query(Document).filter(Document.user_id == user_id)
    
    if filenames:
        query = query.filter(Document.filename.in_(filenames))
    
    docs = query.all()
    
    if not docs:
        return ""
    # Join all documents
    return "\n\n".join([doc.content for doc in docs]).strip()
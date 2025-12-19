from src.models.documents import Document
from sqlalchemy.orm import Session

def load_full_documents(
    user_id: int,
    db: Session,
    document_id: int | None = None
) -> str:
    query = db.query(Document).filter(Document.user_id == user_id)

    if document_id:
        query = query.filter(Document.id == document_id)

    docs = query.all()
    if not docs:
        return ""

    return "\n\n".join(doc.content for doc in docs).strip()
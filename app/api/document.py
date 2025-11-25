from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from app.models.users import User
from app.utils.auth_dependencies import get_current_user
from app.services.document_service import extract_text_from_file

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
    ):

    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Validate file type
    if not file.filename.lower().endswith(('.pdf', '.docx', '.txt', '.csv')):
        raise HTTPException(status_code=400, detail="Unsupported file type")
    
    # Extract text
    try:
        text_content = await extract_text_from_file(file)
        return JSONResponse(content={"filename": file.filename, "text": text_content})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from fastapi import APIRouter, UploadFile, File
from services.resume_parser import parse_resume

router = APIRouter()

@router.post("/verify")
async def handle_upload(file: UploadFile = File(...)):
    file_bytes = await file.read()
    return parse_resume(file_bytes)
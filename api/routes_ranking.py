from fastapi import APIRouter, UploadFile, File, Form
from services.resume_parser import parse_resume

router = APIRouter()

@router.post("/rank-resumes")
async def rank_resumes(
    files: list[UploadFile] = File(...),
    job_description: str = Form(None)
):

    candidates = []

    for file in files:

        file_bytes = await file.read()

        result = parse_resume(file_bytes, job_description)

        candidates.append(result)

    # sort candidates by score
    ranked = sorted(
        candidates,
        key=lambda x: x.get("candidate_score", 0),
        reverse=True
    )

    return {
        "ranked_candidates": ranked
    }
from fastapi import APIRouter

router = APIRouter()

@router.get("/interview/questions")
def get_questions():
    # placeholder logic
    return {
        "questions": [
            "Tell me about yourself.",
            "Explain one challenging project you worked on."
        ]
    }
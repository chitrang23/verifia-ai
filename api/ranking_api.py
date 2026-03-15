from fastapi import APIRouter
from core.candidate_store import get_leaderboard

router = APIRouter()


@router.get("/leaderboard")
def leaderboard():

    data = get_leaderboard()

    return {
        "total_candidates": len(data),
        "leaderboard": data
    }
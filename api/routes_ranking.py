from fastapi import APIRouter
from fastapi.responses import JSONResponse
import json
import os

router = APIRouter()

RANK_FILE = "ranking_data.json"


# -----------------------------
# LOAD RANKING
# -----------------------------
def load_ranking():

    if not os.path.exists(RANK_FILE):
        return []

    try:
        with open(RANK_FILE, "r") as f:
            return json.load(f)

    except:
        return []


# -----------------------------
# SAVE RANKING
# -----------------------------
def save_ranking(data):

    with open(RANK_FILE, "w") as f:
        json.dump(data, f, indent=2)


# -----------------------------
# GET LEADERBOARD
# -----------------------------
@router.get("/leaderboard")
def leaderboard():

    data = load_ranking()

    data.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return JSONResponse(data)
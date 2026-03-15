import json
import os

DB_FILE = "core/candidates.json"


def load_candidates():
    if not os.path.exists(DB_FILE):
        return []

    with open(DB_FILE, "r") as f:
        return json.load(f)


def save_candidate(candidate):

    data = load_candidates()
    data.append(candidate)

    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)


def get_leaderboard():

    data = load_candidates()

    ranked = sorted(data, key=lambda x: x["score"], reverse=True)

    for i, c in enumerate(ranked):
        c["rank"] = i + 1

    return ranked
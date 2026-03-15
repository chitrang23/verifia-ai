from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, UploadFile, File, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse

from api.routes_ranking import router as ranking_router

from model.session import InterviewSession
from services.vision_engine import analyze_gaze
from services.resume_parser import parse_resume

# NEW: store candidates for leaderboard
from core.candidate_store import save_candidate

import cv2
import numpy as np
import base64


# =====================================================
# FASTAPI APP
# =====================================================

app = FastAPI(title="Verifica-AI")

# Include ranking router
app.include_router(ranking_router)

# Templates
templates = Jinja2Templates(directory="templates")


# =====================================================
# LANDING PAGE
# =====================================================

@app.get("/", response_class=HTMLResponse)
async def serve_home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )


# =====================================================
# RESUME PAGE
# =====================================================

@app.get("/resume", response_class=HTMLResponse)
async def serve_resume(request: Request):
    return templates.TemplateResponse(
        "resume.html",
        {"request": request}
    )


# =====================================================
# RANKING PAGE (MULTI RESUME ATS)
# =====================================================

@app.get("/ranking", response_class=HTMLResponse)
async def serve_ranking(request: Request):
    return templates.TemplateResponse(
        "ranking.html",
        {"request": request}
    )


# =====================================================
# INTERVIEW PAGE
# =====================================================

@app.get("/interview", response_class=HTMLResponse)
async def serve_interview(request: Request):
    return templates.TemplateResponse(
        "interview.html",
        {"request": request}
    )


# =====================================================
# RESUME ANALYSIS API
# =====================================================

@app.post("/verify")
async def analyze_resume(
    file: UploadFile = File(...),
    job_description: str = Form(None)
):

    try:

        file_bytes = await file.read()

        result = parse_resume(
            file_bytes,
            job_description
        )

        # =================================================
        # SAVE CANDIDATE FOR RANKING SYSTEM
        # =================================================

        try:

            candidate_profile = result.get("candidate_profile", {})

            candidate = {
                "name": candidate_profile.get("name", "Unknown"),
                "email": candidate_profile.get("email", "Unknown"),
                "score": result.get("candidate_score", 0)
            }

            save_candidate(candidate)

        except Exception as e:
            print("Ranking storage error:", str(e))

        return JSONResponse(result)

    except Exception as e:

        return JSONResponse({
            "error": str(e)
        })


# =====================================================
# INTERVIEW VISION WEBSOCKET
# =====================================================

@app.websocket("/ws/vision")
async def vision_socket(websocket: WebSocket):

    await websocket.accept()

    session = InterviewSession()

    try:

        while True:

            data = await websocket.receive_text()

            if "," not in data:
                continue

            _, encoded = data.split(",", 1)

            try:

                nparr = np.frombuffer(
                    base64.b64decode(encoded),
                    np.uint8
                )

                frame = cv2.imdecode(
                    nparr,
                    cv2.IMREAD_COLOR
                )

                if frame is None:
                    continue

            except Exception:
                continue

            # AI gaze analysis
            status, delta = analyze_gaze(frame, session)

            # Update integrity score
            session.integrity_score += delta

            session.integrity_score = max(
                0,
                min(100, session.integrity_score)
            )

            await websocket.send_json({
                "status": status,
                "score": int(session.integrity_score)
            })

    except WebSocketDisconnect:
        print("WebSocket disconnected")

    except Exception as e:
        print("WebSocket error:", str(e))
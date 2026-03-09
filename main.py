from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from api.routes_resume import router as resume_router
from api.routes_interview import router as interview_router

from model.session import InterviewSession
from services.vision_engine import analyze_gaze

import cv2
import numpy as np
import base64


app = FastAPI(title="Verifica-AI")

# Include modular routers
app.include_router(resume_router)
app.include_router(interview_router)

# Templates directory
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
# INTERVIEW PAGE
# =====================================================
@app.get("/interview", response_class=HTMLResponse)
async def serve_interview(request: Request):
    return templates.TemplateResponse(
        "interview.html",
        {"request": request}
    )


# =====================================================
# VISION WEBSOCKET
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

            # Decode image safely
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

            # Analyze gaze
            status, delta = analyze_gaze(frame, session)

            # Update integrity score
            session.integrity_score += delta
            session.integrity_score = max(0, min(100, session.integrity_score))

            await websocket.send_json({
                "status": status,
                "score": int(session.integrity_score)
            })

    except WebSocketDisconnect:
        print("WebSocket disconnected")

    except Exception as e:
        print("WebSocket error:", str(e))
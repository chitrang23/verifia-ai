from app.model.session import session_store
from app.services.interview_monitor import initialize_monitor


class VisionService:

    def __init__(self):
        self.engine = initialize_monitor()

    def start_session(self, user_id: str):
        session_store[user_id] = {
            "status": "active",
            "alerts": [],
        }
        return {"message": "Session started"}

    def get_session(self, user_id: str):
        return session_store.get(user_id, {"error": "Session not found"})
import cv2
import mediapipe as mp
import numpy as np

# Initialize MediaPipe
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)


def analyze_gaze(frame, session):
    if frame is None:
        return "SYSTEM_OFFLINE", 0

    results = face_mesh.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

    if not results.multi_face_landmarks:
        return "IDENTITY_LOST", -1

    mesh = results.multi_face_landmarks[0].landmark

    # Left eye iris + corners
    iris_x = mesh[468].x
    left_corner_x = mesh[362].x
    right_corner_x = mesh[263].x

    width = right_corner_x - left_corner_x
    if width <= 0:
        return "CALIBRATING", 0

    ratio = (iris_x - left_corner_x) / width

    # Store ratio history
    session.gaze_history.append(ratio)

    if len(session.gaze_history) > 20:
        session.gaze_history.pop(0)

    avg_ratio = sum(session.gaze_history) / len(session.gaze_history)

    # ------------------------------
    # AUTO-CALIBRATION (Very Important)
    # ------------------------------
    if not hasattr(session, "center_ratio"):
        session.center_ratio = avg_ratio
        return "CALIBRATING", 0

    # Gradually adjust center slowly
    session.center_ratio = 0.98 * session.center_ratio + 0.02 * avg_ratio

    center = session.center_ratio
    tolerance = 0.08  # how far allowed from center

    left_threshold = center - tolerance
    right_threshold = center + tolerance

    # Debug print (optional)
    print("CENTER:", round(center, 3), "AVG:", round(avg_ratio, 3))

    # ------------------------------
    # Gaze Decision
    # ------------------------------
    if avg_ratio < left_threshold:
        return "LOOKING_LEFT", -2

    elif avg_ratio > right_threshold:
        return "LOOKING_RIGHT", -2

    else:
        return "STATUS_OPTIMAL", +0.2
import fitz
import spacy
import re
import io
import pytesseract
from PIL import Image
from datetime import datetime
from collections import defaultdict, Counter

print("🔥 VERIFIA AI V3 RESUME INTELLIGENCE ENGINE")

# ===============================
# LOAD NLP MODEL
# ===============================

try:
    nlp = spacy.load("en_core_web_sm")
except:
    nlp = None

# ===============================
# KNOWLEDGE BASE
# ===============================

SKILL_STREAMS = {
    "Technology": ["python","java","react","fastapi","docker","kubernetes","aws","tensorflow"],
    "Data Science": ["machine learning","deep learning","pandas","numpy","nlp"],
    "Cybersecurity": ["penetration testing","siem","firewall","ethical hacking"],
    "Finance": ["gst","taxation","audit","tally","financial modeling"],
    "Marketing": ["seo","google ads","tiktok ads","branding","copywriting"],
    "Design": ["figma","photoshop","illustrator","ui/ux"]
}

TECH_HISTORY = {
    "fastapi":2018,
    "gst":2017,
    "flutter":2017,
    "figma":2016,
    "react":2013
}

BUZZWORDS = [
    "innovative","dynamic","results-driven",
    "strategic thinker","hardworking"
]

SECTION_HEADERS = [
    "education",
    "experience",
    "projects",
    "skills",
    "certifications",
    "achievements"
]

# ===============================
# TEXT EXTRACTION
# ===============================

def extract_text_from_pdf(file_bytes):

    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text = ""

        for page in doc:
            text += page.get_text()

        # OCR fallback
        if len(text.strip()) < 50:

            text = ""

            for page in doc:
                pix = page.get_pixmap()
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                text += pytesseract.image_to_string(img)

        return text

    except Exception as e:
        print("PDF extraction error:", e)
        return ""

# ===============================
# BASIC INFO EXTRACTION
# ===============================

def extract_basic_info(text):

    email = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    phone = re.findall(r"\+?\d[\d\s\-]{8,15}\d", text)

    name = None

    if nlp:
        doc = nlp(text[:1000])
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                name = ent.text
                break

    return {
        "name": name,
        "email": email[0] if email else None,
        "phone": phone[0] if phone else None
    }

# ===============================
# SECTION EXTRACTION ENGINE
# ===============================

def extract_sections(text):

    lower = text.lower()
    sections = {}

    for section in SECTION_HEADERS:

        pattern = rf"{section}\s*(.*?)\n(?=[A-Z])"

        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)

        if match:
            sections[section] = match.group(1).strip()

    return sections

# ===============================
# SKILL DETECTION WITH CONFIDENCE
# ===============================

def detect_skills(text):

    clean = text.lower()
    skill_counter = Counter()

    detected = defaultdict(list)

    for stream, skills in SKILL_STREAMS.items():

        for skill in skills:

            count = len(re.findall(r"\b"+re.escape(skill)+r"\b", clean))

            if count > 0:

                confidence = min(100, count * 30)

                detected[stream].append({
                    "skill": skill,
                    "confidence": confidence
                })

                skill_counter[skill] += count

    return detected

# ===============================
# PRIMARY STREAM DETECTION
# ===============================

def detect_primary_stream(detected):

    best_stream = "General"
    max_count = 0

    for stream, skills in detected.items():

        if len(skills) > max_count:
            best_stream = stream
            max_count = len(skills)

    return best_stream

# ===============================
# EXPERIENCE TIMELINE DETECTION
# ===============================

def extract_experience_timeline(text):

    pattern = r"(20\d{2})\s*[-–]\s*(20\d{2}|present)"

    matches = re.findall(pattern, text.lower())

    timeline = []

    for start, end in matches:

        if end == "present":
            end_year = datetime.now().year
        else:
            end_year = int(end)

        start_year = int(start)

        duration = end_year - start_year

        timeline.append({
            "start": start_year,
            "end": end,
            "duration_years": duration
        })

    return timeline

# ===============================
# EXPERIENCE ESTIMATION
# ===============================

def estimate_total_experience(timeline):

    if not timeline:
        return 0

    total = sum(t["duration_years"] for t in timeline)

    return total

# ===============================
# INTEGRITY ANALYSIS
# ===============================

def integrity_analysis(text, detected_skills):

    score = 100
    alerts = []

    current_year = datetime.now().year
    lower = text.lower()

    claimed_years = re.findall(r"(\d+)\+?\s*(years|yrs)", lower)
    claimed_years = [int(y[0]) for y in claimed_years]

    for tech, release_year in TECH_HISTORY.items():

        if tech in lower and claimed_years:

            claim = max(claimed_years)
            possible = current_year - release_year

            if claim > possible:

                score -= 25
                alerts.append(
                    f"Impossible experience claim for {tech.upper()}"
                )

    buzz_count = sum(lower.count(b) for b in BUZZWORDS)

    if buzz_count > 5:

        score -= 10
        alerts.append("High buzzword density")

    skill_count = sum(len(v) for v in detected_skills.values())

    if skill_count > 15:

        score -= 10
        alerts.append("Too many skills listed (possible exaggeration)")

    return max(score,0), alerts

# ===============================
# RISK LEVEL ENGINE
# ===============================

def calculate_risk(score, alerts):

    if score >= 85 and len(alerts) == 0:
        return "LOW RISK"

    if score >= 60:
        return "MEDIUM RISK"

    return "HIGH RISK"

# ===============================
# INTERVIEW QUESTION GENERATOR
# ===============================

def generate_interview_questions(detected):

    questions = []

    for stream, skills in detected.items():

        for s in skills[:3]:

            skill = s["skill"]

            if skill == "python":
                questions.append("Explain Python decorators and their use cases.")

            elif skill == "react":
                questions.append("How does React Virtual DOM improve performance?")

            elif skill == "aws":
                questions.append("How would you deploy a scalable backend on AWS?")

            elif skill == "docker":
                questions.append("What problem does Docker solve in deployments?")

            elif skill == "machine learning":
                questions.append("Explain bias vs variance tradeoff.")

            else:
                questions.append(f"Explain your practical experience with {skill}.")

    return questions[:5]

# ===============================
# MAIN PARSER
# ===============================

def parse_resume(file_bytes, job_description=None):

    text = extract_text_from_pdf(file_bytes)

    if not text.strip():
        return {"error":"No text extracted"}

    basic = extract_basic_info(text)

    sections = extract_sections(text)

    detected_skills = detect_skills(text)

    primary_stream = detect_primary_stream(detected_skills)

    timeline = extract_experience_timeline(text)

    total_exp = estimate_total_experience(timeline)

    integrity_score, alerts = integrity_analysis(text, detected_skills)

    risk_level = calculate_risk(integrity_score, alerts)

    questions = generate_interview_questions(detected_skills)

    return {

        "candidate_profile": basic,

        "primary_stream": primary_stream,

        "sections": sections,

        "experience_timeline": timeline,

        "experience_years_estimated": total_exp,

        "skills_detected": dict(detected_skills),

        "integrity_score": integrity_score,

        "risk_alerts": alerts,

        "risk_level": risk_level,

        "interview_questions": questions
    }
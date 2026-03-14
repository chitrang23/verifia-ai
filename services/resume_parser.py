import fitz
import spacy
import re
import io
import pytesseract
import requests
from PIL import Image
from datetime import datetime

print("🔥 VERIFIA AI V6 LOADED")

try:
    nlp = spacy.load("en_core_web_sm")
except:
    nlp = None

COMMON_SKILLS = [
"python","java","c++","javascript","react","node","fastapi","django",
"docker","kubernetes","aws","azure","gcp",
"pandas","numpy","machine learning","deep learning","nlp",
"tensorflow","pytorch","sql","mongodb","postgresql",
"git","linux","rest api","graphql"
]

# ------------------------------
# PDF TEXT EXTRACTION
# ------------------------------

def extract_text_from_pdf(file_bytes):

    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text = ""

        for page in doc:
            text += page.get_text()

        if len(text.strip()) < 50:

            text = ""

            for page in doc:
                pix = page.get_pixmap()
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                text += pytesseract.image_to_string(img)

        return text

    except:
        return ""

# ------------------------------
# BASIC INFO
# ------------------------------

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

    if not name:

        lines = text.split("\n")

        for line in lines[:10]:

            line = line.strip()

            if len(line.split()) <= 4 and line[0].isupper():
                name = line
                break

    return {
        "name": name,
        "email": email[0] if email else None,
        "phone": phone[0] if phone else None
    }

# ------------------------------
# SKILLS
# ------------------------------

def detect_skills(text):

    clean = text.lower()

    detected = []

    for skill in COMMON_SKILLS:

        if skill in clean:
            detected.append(skill)

    return detected

# ------------------------------
# EXPERIENCE
# ------------------------------

def extract_experience(text):

    pattern = r"(20\d{2})\s*[-–]\s*(20\d{2}|present)"

    matches = re.findall(pattern, text.lower())

    total = 0

    for start, end in matches:

        start = int(start)

        if end == "present":
            end = datetime.now().year
        else:
            end = int(end)

        total += end - start

    return total

# ------------------------------
# GITHUB DETECTION
# ------------------------------

def extract_github(text):

    match = re.search(r"github\.com/[A-Za-z0-9_-]+", text)

    if match:
        return "https://" + match.group()

    return None

# ------------------------------
# GITHUB VERIFY
# ------------------------------

def verify_github(url):

    if not url:
        return {"verified": False}

    try:

        username = url.split("/")[-1]

        api = f"https://api.github.com/users/{username}"

        r = requests.get(api)

        if r.status_code == 200:

            data = r.json()

            return {
                "verified": True,
                "repos": data["public_repos"],
                "followers": data["followers"]
            }

    except:
        pass

    return {"verified": False}

# ------------------------------
# PROJECT AUTHENTICITY
# ------------------------------

def project_authenticity(text):

    keywords = ["github","api","dataset","deployed","live"]

    score = 0

    found = []

    lower = text.lower()

    for k in keywords:

        if k in lower:
            score += 20
            found.append(k)

    return score, found

# ------------------------------
# ATS MATCH
# ------------------------------

def ats_match(resume_skills, jd):

    if not jd:
        return None, [], []

    jd_lower = jd.lower()

    jd_skills = []

    for skill in COMMON_SKILLS:

        if skill in jd_lower:
            jd_skills.append(skill)

    resume_set = set(resume_skills)
    jd_set = set(jd_skills)

    matched = resume_set.intersection(jd_set)
    missing = jd_set - resume_set

    if len(jd_set) == 0:
        return None, [], []

    score = int(len(matched) / len(jd_set) * 100)

    return score, list(matched), list(missing)

# ------------------------------
# CANDIDATE SCORE
# ------------------------------

def candidate_score(ats, exp, project_score, github):

    score = 0

    if ats:
        score += ats * 0.5

    score += exp * 5
    score += project_score

    if github.get("verified"):
        score += 10

    return int(score)

# ------------------------------
# MAIN PARSER
# ------------------------------

def parse_resume(file_bytes, job_description=None):

    text = extract_text_from_pdf(file_bytes)

    if not text:
        return {"error":"No text extracted"}

    basic = extract_basic_info(text)

    skills = detect_skills(text)

    experience = extract_experience(text)

    ats_score, matched, missing = ats_match(skills, job_description)

    github = extract_github(text)

    github_data = verify_github(github)

    project_score, project_signals = project_authenticity(text)

    final_score = candidate_score(
        ats_score,
        experience,
        project_score,
        github_data
    )

    questions = [
        f"Explain your experience with {s}"
        for s in skills[:5]
    ]

    return {

        "candidate_profile": basic,

        "skills_detected": skills,

        "experience_years_estimated": experience,

        "ats_match_score": ats_score,

        "matched_skills": matched,

        "missing_skills": missing,

        "github_profile": github,

        "github_data": github_data,

        "project_authenticity_score": project_score,

        "project_signals": project_signals,

        "candidate_score": final_score,

        "interview_questions": questions
    }
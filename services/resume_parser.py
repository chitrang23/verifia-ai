import fitz
import spacy
import re
import io
import pytesseract
import requests
from PIL import Image
from datetime import datetime
from google import genai
import json

print("🔥 VERIFIA AI V8 LOADED (Hybrid AI Skills)")

# ------------------------------
# CONFIGURE GEMINI API
# ------------------------------
client = genai.Client(api_key="AIzaSyCUwgRBCSYFlg6AplFeyYRgqeT7k-SfAng")  # replace with your API key

# ------------------------------
# LOAD NLP
# ------------------------------
try:
    nlp = spacy.load("en_core_web_sm")
except:
    nlp = None

# ------------------------------
# TESSERACT PATH
# ------------------------------
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# ------------------------------
# GLOBAL SKILL DATABASE
# ------------------------------
COMMON_SKILLS = [
    "python","java","c++","javascript","react","node","fastapi","django",
    "docker","kubernetes","aws","azure","gcp",
    "pandas","numpy","machine learning","deep learning","nlp",
    "tensorflow","pytorch","sql","mongodb","postgresql",
    "git","linux","rest api","graphql","html","css"
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

        # OCR fallback for scanned resumes
        if len(text.strip()) < 50:
            text = ""
            for page in doc:
                pix = page.get_pixmap(dpi=300)
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                text += pytesseract.image_to_string(img)
        return text
    except Exception as e:
        print("PDF extraction error:", e)
        return ""

# ------------------------------
# BASIC INFO EXTRACTION
# ------------------------------
def extract_basic_info(text):
    email = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    phone = re.findall(r"\+?\d[\d\s\-]{8,15}\d", text)
    name = None
    if nlp:
        doc = nlp(text[:2000])
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                name = ent.text
                break
    if not name:
        lines = text.split("\n")
        for line in lines[:20]:
            line = line.strip()
            if len(line.split()) <= 4 and (line.istitle() or line.isupper()) and not any(c.isdigit() for c in line):
                name = line
                break
    return {"name": name, "email": email[0] if email else None, "phone": phone[0] if phone else None}

# ------------------------------
# AI SKILL EXTRACTION USING GEMINI
# ------------------------------
def ai_extract_skills(text):
    try:
        model_name = "models/gemini-2.5-pro"
        prompt = f"""
        Extract all technical and professional skills from this resume.
        Return only a JSON list of skills.
        Resume:
        {text[:4000]}
        """
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )

        skills_text = getattr(response, "text", "") or ""
        # Parse JSON safely
        try:
            skills = json.loads(skills_text)
            skills = [s.lower().strip() for s in skills if isinstance(s, str)]
        except:
            skills = [s.lower().strip().replace('"', '') for s in skills_text.replace("[","").replace("]","").split(",")]

        return list(set(skills))
    except Exception as e:
        print("Gemini skill extraction error:", e)
        return []

# ------------------------------
# HYBRID SKILL DETECTION
# ------------------------------
def detect_skills(text):
    clean = text.lower()
    detected = []

    # Rule-based detection
    for skill in COMMON_SKILLS:
        if re.search(r"\b" + re.escape(skill) + r"\b", clean):
            detected.append(skill)

    # AI skill extraction
    ai_skills = ai_extract_skills(text)
    detected.extend(ai_skills)

    return sorted(list(set(detected)))

# ------------------------------
# EXPERIENCE DETECTION
# ------------------------------
def extract_experience(text):
    years = []
    # Match formats like: Jan 2020 – Present, 2020-2022, Mar 2021 to May 2023
    pattern = r"(?i)(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)?[a-z]*\s*\d{4}\s*(?:-|–|to)\s*(?:Present|\d{4})"
    matches = re.findall(pattern, text)
    for match in matches:
        parts = re.split(r"-|–|to", match, flags=re.IGNORECASE)
        if len(parts) == 2:
            start = parts[0]
            end = parts[1]
            start_year = int(re.search(r'\d{4}', start).group())
            end_year = datetime.now().year if 'present' in end.lower() else int(re.search(r'\d{4}', end).group())
            if end_year >= start_year:
                years.append(end_year - start_year)
    return sum(years)

# ------------------------------
# GITHUB EXTRACTION
# ------------------------------
def extract_github(text):
    matches = re.findall(r"(?:https?://)?github\.com/([A-Za-z0-9_-]+)", text)
    return f"https://github.com/{matches[0]}" if matches else None

def verify_github(url):
    if not url:
        return {"verified": False}
    try:
        username = url.split("/")[-1]
        api = f"https://api.github.com/users/{username}"
        r = requests.get(api, timeout=5)
        if r.status_code == 200:
            data = r.json()
            return {"verified": True, "repos": data.get("public_repos", 0), "followers": data.get("followers", 0)}
    except Exception as e:
        print("GitHub API error:", e)
    return {"verified": False}

# ------------------------------
# PROJECT AUTHENTICITY
# ------------------------------
def project_authenticity(text):
    keywords = ["github","api","dataset","deployed","live","model"]
    score = 0
    found = []
    lower = text.lower()
    for k in keywords:
        if k in lower:
            score += 15
            found.append(k)
    return min(score, 40), found

# ------------------------------
# ATS MATCH
# ------------------------------
def ats_match(resume_skills, jd):
    if not jd:
        return None, [], []
    jd_lower = jd.lower()
    jd_skills = set([skill for skill in COMMON_SKILLS if skill in jd_lower])
    resume_set = set(resume_skills)
    matched = resume_set.intersection(jd_skills)
    missing = jd_skills - resume_set
    score = int(len(matched)/len(jd_skills)*100) if jd_skills else None
    return score, list(matched), list(missing)

# ------------------------------
# RISK ANALYSIS
# ------------------------------
def risk_analysis(skills, experience):
    if len(skills) > 20 and experience < 2:
        return "High"
    if len(skills) > 15:
        return "Medium"
    return "Low"

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
    return min(int(score), 100)

# ------------------------------
# MAIN PARSER
# ------------------------------
def parse_resume(file_bytes, job_description=None):
    text = extract_text_from_pdf(file_bytes)
    if not text:
        return {"error": "No text extracted"}

    basic = extract_basic_info(text)
    skills = detect_skills(text)
    experience = extract_experience(text)
    ats_score, matched, missing = ats_match(skills, job_description)
    github = extract_github(text)
    github_data = verify_github(github)
    project_score, project_signals = project_authenticity(text)
    risk = risk_analysis(skills, experience)
    final_score = candidate_score(ats_score, experience, project_score, github_data)
    questions = [f"Explain your experience with {s}" for s in skills[:5]]

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
        "risk_level": risk,
        "candidate_score": final_score,
        "interview_questions": questions
    }
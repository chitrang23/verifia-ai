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
import os

print("🔥 VERIFIA AI V11 LOADED (GitHub Authenticity + Resume Intelligence)")

# ==========================================================
# GEMINI CONFIGURATION
# ==========================================================

GEMINI_KEY = "AIzaSyCUwgRBCSYFlg6AplFeyYRgqeT7k-SfAng"

client = genai.Client(api_key=GEMINI_KEY)

# ==========================================================
# LOAD SPACY
# ==========================================================

try:
    nlp = spacy.load("en_core_web_sm")
except:
    nlp = None

# ==========================================================
# TESSERACT CONFIG
# ==========================================================

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# ==========================================================
# COMMON SKILLS
# ==========================================================

COMMON_SKILLS = [
    "python","java","c++","javascript","react","node","fastapi","django",
    "docker","kubernetes","aws","azure","gcp",
    "pandas","numpy","machine learning","deep learning","nlp",
    "tensorflow","pytorch","sql","mongodb","postgresql",
    "git","linux","rest api","graphql","html","css",
    "excel","power bi","tableau","seo","content marketing",
    "financial analysis","project management","leadership",
    "data analysis","public speaking","communication"
]

# ==========================================================
# PDF TEXT EXTRACTION
# ==========================================================

def extract_text_from_pdf(file_bytes):

    try:

        doc = fitz.open(stream=file_bytes, filetype="pdf")

        text = ""

        for page in doc:
            text += page.get_text()

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

# ==========================================================
# BASIC INFO
# ==========================================================

def extract_basic_info(text):

    email = re.findall(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        text
    )

    phone = re.findall(
        r"\+?\d[\d\s\-]{8,15}\d",
        text
    )

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

            if (
                len(line.split()) <= 4
                and not any(c.isdigit() for c in line)
            ):
                name = line
                break

    return {
        "name": name,
        "email": email[0] if email else None,
        "phone": phone[0] if phone else None
    }

# ==========================================================
# AI SKILL EXTRACTION
# ==========================================================

def ai_extract_skills(text):

    try:

        prompt = f"""
Extract professional skills from the resume.

Return JSON:

{{
"domain":"primary professional field",
"skills":["skill1","skill2"]
}}

Resume:
{text[:4000]}
"""

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )

        raw = getattr(response, "text", "")

        raw = raw.replace("```json","").replace("```","").strip()

        data = json.loads(raw)

        domain = data.get("domain","unknown")

        skills = [s.lower() for s in data.get("skills",[])]

        return domain, list(set(skills))

    except Exception as e:

        print("Gemini extraction error:", e)

        return "unknown", []

# ==========================================================
# SKILL DETECTION
# ==========================================================

def detect_skills(text):

    clean = text.lower()

    detected = []

    for skill in COMMON_SKILLS:

        if re.search(r"\b" + re.escape(skill) + r"\b", clean):

            detected.append(skill)

    domain, ai_skills = ai_extract_skills(text)

    detected.extend(ai_skills)

    return domain, list(set(detected))

# ==========================================================
# EXPERIENCE
# ==========================================================

def extract_experience(text):

    pattern = r"(20\d{2})\s*[-–to]+\s*(20\d{2}|present)"

    matches = re.findall(pattern, text.lower())

    total_years = 0

    for start, end in matches:

        start = int(start)

        if end == "present":
            end = datetime.now().year
        else:
            end = int(end)

        if end >= start:
            total_years += end - start

    return total_years

# ==========================================================
# GITHUB PROFILE EXTRACTION
# ==========================================================

def extract_github(text):

    match = re.search(
        r"github\.com/[A-Za-z0-9_-]+",
        text
    )

    if match:
        return "https://" + match.group()

    return None

# ==========================================================
# GITHUB VERIFY
# ==========================================================

def verify_github(url):

    if not url:
        return {"verified": False}

    try:

        username = url.split("/")[-1]

        api = f"https://api.github.com/users/{username}"

        r = requests.get(api, timeout=5)

        if r.status_code == 200:

            data = r.json()

            return {
                "verified": True,
                "repos": data.get("public_repos",0),
                "followers": data.get("followers",0)
            }

    except Exception as e:

        print("GitHub API error:", e)

    return {"verified": False}

# ==========================================================
# GITHUB REPO CONTRIBUTION ANALYSIS
# ==========================================================

def analyze_repo_contributions(username, repo):

    try:

        url = f"https://api.github.com/repos/{username}/{repo}/contributors"

        r = requests.get(url, timeout=5)

        if r.status_code != 200:
            return None

        contributors = r.json()

        total_commits = 0
        user_commits = 0

        for c in contributors:

            commits = c.get("contributions",0)

            total_commits += commits

            if c.get("login","").lower() == username.lower():

                user_commits = commits

        if total_commits == 0:
            return None

        percent = round((user_commits / total_commits) * 100,2)

        authentic = percent >= 10

        return {
            "repo": repo,
            "total_commits": total_commits,
            "candidate_commits": user_commits,
            "contribution_percent": percent,
            "authentic": authentic
        }

    except Exception as e:

        print("Contribution analysis error:", e)

        return None

# ==========================================================
# ANALYZE ALL REPOS
# ==========================================================

def analyze_github_activity(username):

    try:

        url = f"https://api.github.com/users/{username}/repos"

        r = requests.get(url, timeout=5)

        if r.status_code != 200:
            return []

        repos = r.json()

        analysis = []

        for repo in repos[:10]:

            repo_name = repo["name"]

            data = analyze_repo_contributions(username, repo_name)

            if data:
                analysis.append(data)

        return analysis

    except Exception as e:

        print("GitHub activity error:", e)

        return []

# ==========================================================
# PROJECT AUTHENTICITY
# ==========================================================

def project_authenticity(text):

    keywords = [
        "github",
        "api",
        "dataset",
        "deployed",
        "live",
        "model"
    ]

    score = 0
    found = []

    lower = text.lower()

    for k in keywords:

        if k in lower:

            score += 15
            found.append(k)

    return min(score,40), found

# ==========================================================
# ATS MATCH
# ==========================================================

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

# ==========================================================
# RISK DETECTION
# ==========================================================

def risk_analysis(skills, experience):

    if len(skills) > 25 and experience < 2:
        return "High"

    if len(skills) > 18:
        return "Medium"

    return "Low"

# ==========================================================
# FINAL SCORE
# ==========================================================

def candidate_score(ats, exp, project_score, github):

    score = 0

    if ats:
        score += ats * 0.5

    score += exp * 5
    score += project_score

    if github.get("verified"):
        score += 10

    if score > 100:
        score = 100

    return int(score)

# ==========================================================
# MAIN PARSER
# ==========================================================

def parse_resume(file_bytes, job_description=None):

    text = extract_text_from_pdf(file_bytes)

    if not text:
        return {"error":"No text extracted"}

    basic = extract_basic_info(text)

    domain, skills = detect_skills(text)

    experience = extract_experience(text)

    ats_score, matched, missing = ats_match(
        skills,
        job_description
    )

    github = extract_github(text)

    github_data = verify_github(github)

    github_analysis = []

    if github:

        username = github.split("/")[-1]

        github_analysis = analyze_github_activity(username)

    project_score, project_signals = project_authenticity(text)

    risk = risk_analysis(skills, experience)

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
        "candidate_domain": domain,
        "skills_detected": skills,
        "experience_years_estimated": experience,

        "ats_match_score": ats_score,
        "matched_skills": matched,
        "missing_skills": missing,

        "github_profile": github,
        "github_data": github_data,
        "github_contribution_analysis": github_analysis,

        "project_authenticity_score": project_score,
        "project_signals": project_signals,

        "risk_level": risk,
        "candidate_score": final_score,

        "interview_questions": questions
    }
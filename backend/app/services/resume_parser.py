import fitz  # PyMuPDF

def parse_resume(file_bytes):
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    
    clean_text = text.lower()
    
    # Multi-Stream Skill Categories
    categories = {
        "Technical": ["python", "java", "sql", "excel", "c++", "autocad", "aws"],
        "Management": ["leadership", "project management", "agile", "scrum", "budgeting"],
        "Marketing/Sales": ["seo", "digital marketing", "sales", "crm", "content strategy"],
        "Finance": ["accounting", "taxation", "tally", "audit", "financial modeling"],
        "Soft Skills": ["communication", "teamwork", "problem solving", "adaptability"]
    }
    
    found_by_category = {}
    all_found = []

    for category, skills in categories.items():
        matches = [s for s in skills if s in clean_text]
        if matches:
            found_by_category[category] = matches
            all_found.extend(matches)
    
    # Fraud Detection Logic
    alerts = []
    if len(text.split()) < 50:
        alerts.append("Alert: Low content density.")
    
    # Check for "White Fonting" or Keyword Stuffing
    for s in all_found:
        if clean_text.count(s) > 8:
            alerts.append(f"Fraud Alert: Excessive mention of '{s}'.")
            
    return {
        "categorized_skills": found_by_category,
        "alerts": alerts
    }
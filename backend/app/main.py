from fastapi import FastAPI, Request, UploadFile, File
from fastapi.templating import Jinja2Templates
from app.services.resume_parser import parse_resume

# Initialize the FastAPI application
app = FastAPI()

# Tell FastAPI where to find your HTML files
templates = Jinja2Templates(directory="app/templates")

@app.get("/")
async def home(request: Request):
    """
    This route serves the main dashboard (index.html) 
    when you visit http://127.0.0.1:8000
    """
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/verify")
async def verify(file: UploadFile = File(...)):
    """
    This route receives the uploaded PDF, reads its content,
    and calls the 'parse_resume' function from our services.
    """
    # Read the uploaded file into memory
    content = await file.read()
    
    # Send the data to the Logic Engine (Step 1)
    analysis_results = parse_resume(content)
    
    # Return the final analysis to the browser
    return analysis_results
import os
import json
import PyPDF2
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# 1. Configure OpenAI
api_key = os.getenv("OPENAI_API_KEY")
client = None

if api_key:
    client = OpenAI(api_key=api_key)
else:
    print("⚠️  WARNING: OPENAI_API_KEY not found. AI features will not work.")

def extract_text_from_pdf(pdf_path):
    """
    Reads a PDF file and extracts text from all pages.
    """
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return None
    
    return text

def analyze_resume_with_openai(resume_text):
    """
    Sends the resume text to OpenAI to extract structured data.
    """
    if not client:
        print("❌ Error: OpenAI client is not initialized (Missing API Key).")
        return None

    # Use gpt-4o-mini for production-grade cost efficiency (approx 30x cheaper than gpt-4o)
    model = "gpt-4o-mini"

    prompt = f"""
    You are an AI Recruiter. Extract structured data from this resume.
    
    Return ONLY a valid JSON object. Be concise to save tokens.
    Fields:
    - name (string)
    - email (string)
    - phone (string)
    - skills (list of technical skills)
    - years_of_experience (int)
    - job_role (inferred target title)
    - tech_stack (list of frameworks/tools)
    - education (list of strings, e.g. "Degree - University")
    - certifications (list of strings)
    - summary (max 30 words)

    Do not include markdown formatting, just the raw JSON object.
    """

    try:
        response = client.chat.completions.create(
            model=model,
            response_format={"type": "json_object"}, # Enforces valid JSON
            temperature=0, # Deterministic output (better for data extraction)
            max_tokens=500, # Hard limit to prevent runaway costs
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Here is the resume text:\n\n{resume_text}"}
            ]
        )
        return json.loads(response.choices[0].message.content)

    except Exception as e:
        print(f"Error connecting to OpenAI: {e}")
        return None

def get_ai_answer(question, user_data, error_message=None):
    """
    Asks AI to answer a specific question based on user data.
    """
    if not client:
        return ""

    model = "gpt-4o-mini"
    
    error_context = ""
    if error_message:
        error_context = f"\n    PREVIOUS ERROR: The form rejected the last answer with: '{error_message}'. Fix the format (e.g., remove letters, use integer)."

    prompt = f"""
    You are an AI Job Applicant. Answer the question concisely based on the candidate's profile.
    
    Profile: {json.dumps(user_data)}
    Question: "{question}"{error_context}
    
    Rules:
    - Return ONLY the answer text.
    - For Yes/No questions, return "Yes" or "No".
    - For numeric questions, return just the number.
    - If asked about notice period, always return the integer 30 (no text like "days").
    - If asked about current CTC/Salary, return the integer 1200000.
    - If asked about expected CTC/Salary, return the integer 2000000.
    - If you do not know the answer to a numeric question, return the integer 0.
    - If the answer is missing from the profile, use your best judgment to provide a POSITIVE, plausible answer (e.g., "Yes", "Intermediate", "2").
    - Do not leave it empty.
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=50,
            temperature=0
        )
        return response.choices[0].message.content.strip()
    except:
        return ""

def get_ai_select_choice(question, options, user_data):
    """
    Asks AI to choose the best option from a list based on user data.
    """
    if not client:
        return options[0] if options else ""

    model = "gpt-4o-mini"
    prompt = f"""
    You are an AI Job Applicant. Choose the best option from the provided list for the question based on the candidate's profile.
    
    Profile: {json.dumps(user_data)}
    Question: "{question}"
    Options: {json.dumps(options)}
    
    Rules:
    - Return ONLY the exact string of the selected option.
    - If the question is about notice period, prefer "Immediate", "1 Month", or "30 Days" if not specified in profile.
    - If the answer is missing, select the most positive/beneficial option (e.g., "Yes", "Native or Bilingual", "Proficient").
    - Select the most logical option.
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=50,
            temperature=0
        )
        return response.choices[0].message.content.strip()
    except:
        return options[0] if options else ""

def main():
    # 1. Simulate a file upload
    pdf_filename = "resume.pdf" 
    
    if not os.path.exists(pdf_filename):
        print(f"⚠️  File '{pdf_filename}' not found. Please add a PDF to test.")
        return

    print(f"📄 Extracting text from {pdf_filename}...")
    raw_text = extract_text_from_pdf(pdf_filename)

    if raw_text:
        print(f"✅ Text extracted ({len(raw_text)} characters). Analyzing with OpenAI...")
        
        # 2. Send to AI
        structured_data = analyze_resume_with_openai(raw_text)
        
        if structured_data:
            print("\n🚀 Analysis Complete! Agent Data Ready:\n")
            print(json.dumps(structured_data, indent=4))
        else:
            print("❌ AI failed to return structured data.")
    else:
        print("❌ Failed to extract text from PDF.")

if __name__ == "__main__":
    main()
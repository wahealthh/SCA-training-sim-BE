from datetime import datetime
import json
from openai import OpenAI
from app.core.config import settings
from app.schema.consultation import CaseDetails


openai = OpenAI(api_key=settings.OPENAI_API_KEY)

def load_generate_case_prompt():
    """Load the case generation prompt from the prompts directory"""
    with open("app/prompts/generate_case_prompt.md", "r") as f:
        return f.read()

def generate_case():
    """
    Generate a new patient case for consultation
    
    Returns:
        dict: Case details including age, presenting complaint, and context
    """
    prompt = load_generate_case_prompt()

    # Call OpenAI API to generate a case
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a medical case generator for GP training."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )

    # Parse and return the generated case as a Python dictionary
    try:
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Error parsing case JSON: {e}")
        return {
            "name": "James",
            "age": 45,
            "presenting": "Persistent headache for the past two weeks.",
            "context": "Patient has a history of migraines but describes this as different. Works in a high-stress environment and recently changed medication."
        }


def load_scoring_rubric():
    """Load the RCGP scoring rubric from the prompts directory"""
    with open("app/prompts/scoring_rubric.md", "r") as f:
        return f.read()

def score_consultation(transcript, case_details):
    """
    Score a completed consultation transcript based on RCGP rubric
    
    Args:
        transcript (str): The full consultation transcript
        case_details (CaseDetails): Details about the patient case
        
    Returns:
        dict: Scores and feedback for the consultation
    """
    scoring_rubric = load_scoring_rubric()
    
    # Create a prompt for scoring
    prompt = f"""
You are an expert medical consultant evaluator who specializes in assessing GP trainee consultations.
You will be scoring a consultation based on the Royal College of General Practitioners (RCGP) assessment framework.
You will be analyzing what aspects of the case were properly explored.


Here is the case details that the GP trainee was presented with:
{case_details.doctor_info}

Here is the full case details:
{case_details}

Here is the transcript of the consultation:
{transcript}

Based on the RCGP assessment framework below, score this consultation:

{scoring_rubric}

Analyze the transcript and provide scores (1-5) for each domain:
1. Data Gathering
2. Clinical Management
3. Interpersonal Skills

For each domain, provide:
- Score (1-5, where 1 is poor and 5 is excellent)
- Specific examples from the transcript that justify the score
- Areas for improvement

Then calculate an overall score (average of the three domains).
Finally, provide concise, actionable feedback for the trainee.

Respond with a JSON object in this format:
{{
  "scores": {{
    "data_gathering": {{
      "score": 1-5,
      "examples": ["example1", "example2"],
      "areas_for_improvement": ["area1", "area2"]
    }},
    "clinical_management": {{
      "score": 1-5,
      "examples": ["example1", "example2"],
      "areas_for_improvement": ["area1", "area2"]
    }},
    "interpersonal_skills": {{
      "score": 1-5,
      "examples": ["example1", "example2"],
      "areas_for_improvement": ["area1", "area2"]
    }}
  }},
  "overall_score": float,
  "feedback": "Concise feedback paragraph here",
  "coverage_analysis": {{
    "ice_coverage": [
      {{
        "id": "ice_id",
        "ice_type": "IDEA/CONCERN/EXPECTATION",
        "description": "description text",
        "coverage_status": "COVERED/PARTIALLY_COVERED/NOT_COVERED",
        "evidence": "Quote from transcript or explanation"
      }}
    ],
    "information_coverage": [
      {{
        "id": "info_id",
        "divulgence_type": "FREELY_DIVULGED/SPECIFICALLY_ASKED",
        "description": "description text",
        "coverage_status": "COVERED/PARTIALLY_COVERED/NOT_COVERED",
        "evidence": "Quote from transcript or explanation"
      }}
    ],
    "background_coverage": [
      {{
        "id": "background_id",
        "description": "description text",
        "coverage_status": "COVERED/PARTIALLY_COVERED/NOT_COVERED",
        "evidence": "Quote from transcript or explanation"
      }}
    ]
  }}
}}
"""

    # Call OpenAI API to score the consultation
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a medical consultation scoring assistant."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )

    # Parse the response
    scoring_result = json.loads(response.choices[0].message.content)
    
    # Add timestamp to the result
    scoring_result["timestamp"] = datetime.now().isoformat()
    
    return scoring_result

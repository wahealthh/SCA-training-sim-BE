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
    
    # Format case details into a clean, readable format
    formatted_case_details = f"""
**Patient Information:**
- Name: {case_details.patient_name}
- Age: {case_details.patient_age}
- Gender: {case_details.patient_gender.value if case_details.patient_gender else 'Not specified'}
- Case Number: {case_details.case_number}

**Presenting Complaint:**
{case_details.presenting_complaint}

**Clinical Notes:**
{case_details.notes if case_details.notes else 'None provided'}
"""

    # Add Doctor Information if available
    if case_details.doctor_info:
        formatted_case_details += f"""
**Doctor Information:**
- Name: {case_details.doctor_info.name}
- Age: {case_details.doctor_info.age}
- Past Medical History: {case_details.doctor_info.past_medical_history}
- Current Medication: {case_details.doctor_info.current_medication}
- Context: {case_details.doctor_info.context}
"""

    # Format ICE entries
    if case_details.ice_entries:
        formatted_case_details += "\n**Patient's Ideas, Concerns, and Expectations (ICE):**\n"
        for i, ice in enumerate(case_details.ice_entries, 1):
            ice_type = ice.ice_type.value if hasattr(ice.ice_type, 'value') else str(ice.ice_type)
            formatted_case_details += f"{i}. {ice_type}: {ice.description}\n"
    
    # Format background details
    if case_details.background_details:
        formatted_case_details += "\n**Background Information:**\n"
        for i, detail in enumerate(case_details.background_details, 1):
            formatted_case_details += f"{i}. {detail.detail}\n"
    
    # Format information divulged
    if case_details.information_divulged:
        formatted_case_details += "\n**Information to be Divulged:**\n"
        
        # Group by divulgence type
        freely_divulged = [info for info in case_details.information_divulged 
                          if info.divulgence_type.value == 'FREELY_DIVULGED']
        specifically_asked = [info for info in case_details.information_divulged 
                            if info.divulgence_type.value == 'SPECIFICALLY_ASKED']
        
        if freely_divulged:
            formatted_case_details += "\n*Information the patient will freely share:*\n"
            for i, info in enumerate(freely_divulged, 1):
                formatted_case_details += f"{i}. {info.description}\n"
        
        if specifically_asked:
            formatted_case_details += "\n*Information the patient will only share if specifically asked:*\n"
            for i, info in enumerate(specifically_asked, 1):
                formatted_case_details += f"{i}. {info.description}\n"
    
    # Create a prompt for scoring
    prompt = f"""
You are an expert medical consultant evaluator who specializes in assessing GP trainee consultations.
You will be scoring a consultation based on the Royal College of General Practitioners (RCGP) assessment framework.
You will also analyze and report on which specific informational aspects of the case were covered during the consultation in a dedicated 'coverage_analysis' section.

**Crucial Guidance for Scoring vs. Coverage Analysis:**
It is essential to differentiate between the assessment of the trainee's skills (reflected in the scores for Data Gathering, Clinical Management, and Interpersonal Skills) and the factual coverage of case information (detailed in 'coverage_analysis').

1.  **Domain Scoring (Data Gathering, Clinical Management, Interpersonal Skills):** These scores (1-5) must be based on the *quality, depth, appropriateness, and proficiency* of the trainee's actions, clinical reasoning, and communication, as defined by the RCGP assessment framework provided below. For example, how effectively did they gather information, not just *what* information they gathered? How sound was their clinical judgment and management plan? How effectively did they communicate and build rapport?
2.  **Coverage Analysis:** This section is intended to objectively list which predefined elements of the case (ICE, specific information, background) were mentioned or explored. You don't need to rephrase or summarize the information, just list it as it is.

**Important:** A high degree of coverage in the 'coverage_analysis' section **does not automatically equate to high scores in the primary domains.** A trainee might mention all required information points but do so with poor technique, flawed reasoning, or inadequate interpersonal skills. Conversely, a trainee might demonstrate excellent skills in the areas they explored, even if they missed a minor informational point. Your domain scoring should reflect the *skill and competency* demonstrated, using the RCGP rubric as your primary guide.

Here are the case details that were provided to the GP trainee:
{formatted_case_details}

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

For the coverage analysis, identify which ICE entries, background details, and information points were covered, partially covered, or not covered in the consultation. Include evidence from the transcript to support your assessment.

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
        "ice_type": "IDEA/CONCERN/EXPECTATION",
        "description": "description text",
        "coverage_status": "COVERED/PARTIALLY_COVERED/NOT_COVERED",
        "evidence": "Quote from transcript or explanation"
      }}
    ],
    "information_coverage": [
      {{
        "divulgence_type": "FREELY_DIVULGED/SPECIFICALLY_ASKED",
        "description": "description text",
        "coverage_status": "COVERED/PARTIALLY_COVERED/NOT_COVERED",
        "evidence": "Quote from transcript or explanation"
      }}
    ],
    "background_coverage": [
      {{
        "description": "description text",
        "coverage_status": "COVERED/PARTIALLY_COVERED/NOT_COVERED",
        "evidence": "Quote from transcript or explanation"
      }}
    ]
  }}
}}
"""

    print("prompt", prompt)
    response = openai.chat.completions.create(
        model="gpt-4.1",
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

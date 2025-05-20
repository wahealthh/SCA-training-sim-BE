"""
Database Seeding Script for Voice SCA Simulator
This script populates the database with initial test data.
"""
import os
import sys
from datetime import datetime, timedelta, UTC
import random
from loguru import logger
from fastapi import Depends
from sqlalchemy.orm import Session

# Add the parent directory to the path so we can import our models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.logging_config import setup_logging
from app.db.load import load
from app.models.user import User
from app.models.consultation import Consultation, Case, ICE, BackgroundDetail, InformationDivulged, ICEType, DivulgenceType

# Set up logging
logger = setup_logging()

def create_test_users(db: Session):
    """Create test users"""
    logger.info("Creating test users...")
    users = [
    User(first_name="John", last_name="Doe"),
        User(first_name="Jane", last_name="Smith"),
        User(first_name="Mike", last_name="Wilson"),
    ]
    
    for user in users:
        # Check if user already exists
        existing_user = db.query(User).filter_by(first_name=user.first_name, last_name=user.last_name).first()
        if not existing_user:
            db.add(user)
    
    # Make sure to commit changes before returning
    db.commit()
    
    # Get all users from database to ensure we have their correct IDs
    db_users = db.query(User).all()
    logger.info(f"Created {len(users)} test users")
    return db_users

def create_test_cases(db: Session):
    """Create test patient cases"""
    logger.info("Creating test patient cases...")
    cases = [
        Case(
            case_number="CASE-001",
            patient_name="John Smith",
            patient_age=45,
            presenting_complaint="The patient has been experiencing increasing shortness of breath over the past month, particularly when climbing stairs.",
            notes="Patient has a history of smoking 20 cigarettes daily for 25 years. No prior respiratory conditions diagnosed. Family history of COPD."
        ),
        Case(
            case_number="CASE-002",
            patient_name="Sarah Johnson",
            patient_age=62,
            presenting_complaint="The patient reports persistent joint pain in both knees that has been worsening over the past year.",
            notes="Patient is overweight with a BMI of 32. Previously active but has reduced exercise due to pain. Has been self-medicating with over-the-counter pain relievers."
        ),
        Case(
            case_number="CASE-003",
            patient_name="Michael Chen",
            patient_age=36,
            presenting_complaint="The patient has been experiencing recurring headaches, typically in the afternoon, for the past three weeks.",
            notes="Works long hours at a computer. Reports increased stress at work. No prior history of chronic headaches. Vision was last checked two years ago."
        ),
        Case(
            case_number="CASE-004",
            patient_name="Emily Rodriguez",
            patient_age=58,
            presenting_complaint="The patient has noticed a gradually enlarging lump on the left side of their neck over the past two months.",
            notes="Non-smoker. No recent infections. No fever or night sweats. Previously healthy with well-controlled hypertension."
        ),
        Case(
            case_number="CASE-005",
            patient_name="David Kim",
            patient_age=29,
            presenting_complaint="The patient reports severe abdominal pain that started suddenly four hours ago.",
            notes="No previous abdominal surgeries. Last meal was 6 hours ago. Pain is concentrated in the right lower quadrant. No nausea or vomiting."
        ),
    ]
    
    for case in cases:
        # Check if a similar case already exists
        existing_case = db.query(Case).filter_by(
            case_number=case.case_number
        ).first()
        
        if not existing_case:
            db.add(case)
            db.flush()  # Flush to get the ID
            
            # Add some sample ICE entries
            db.add(ICE(
                case_id=case.id,
                ice_type=ICEType.IDEA,
                description="Patient thinks they might have a serious condition."
            ))
            
            db.add(ICE(
                case_id=case.id,
                ice_type=ICEType.CONCERN,
                description="Patient is worried about impact on daily activities."
            ))
            
            # Add background details
            db.add(BackgroundDetail(
                case_id=case.id,
                detail="Patient has a family history of similar conditions."
            ))
            
            # Add information divulged
            db.add(InformationDivulged(
                case_id=case.id,
                divulgence_type=DivulgenceType.FREELY_DIVULGED,
                description="Patient mentioned symptoms without prompting."
            ))
            
            db.add(InformationDivulged(
                case_id=case.id,
                divulgence_type=DivulgenceType.SPECIFICALLY_ASKED,
                description="Patient revealed medication history only when directly asked."
            ))
    
    # Commit to ensure all cases are saved
    db.commit()
    
    # Get cases from database to ensure we have their correct IDs
    db_cases = db.query(Case).all()
    
    if not db_cases:
        logger.error("No patient cases were created or found in the database")
        return []
        
    logger.info(f"Database now has {len(db_cases)} patient cases with IDs: {[case.id for case in db_cases]}")
    return db_cases

def create_test_consultations(db: Session, users, cases):
    """Create test consultations"""
    if not users or not cases:
        logger.error("Cannot create consultations: missing users or cases")
        return
        
    logger.info("Creating test consultations...")
    logger.info(f"Working with {len(users)} users and {len(cases)} cases")
    
    # Create sample transcripts
    sample_transcripts = [
        """
        Doctor: Hello, I'm Dr. Smith. What brings you in today?
        Patient: I've been having trouble breathing, especially when I climb stairs.
        Doctor: How long has this been going on?
        Patient: About a month now, and it seems to be getting worse.
        Doctor: Do you have any other symptoms like coughing or chest pain?
        Patient: I do have a cough, especially in the mornings.
        Doctor: Do you smoke?
        Patient: Yes, about a pack a day for 25 years.
        Doctor: Have you ever been diagnosed with any lung conditions before?
        Patient: No, this is new for me.
        Doctor: Does anyone in your family have respiratory problems?
        Patient: My father had COPD.
        Doctor: Let me listen to your lungs. Take a deep breath, please.
        [Examination conducted]
        Doctor: Based on your symptoms, history, and examination, I'd like to do some lung function tests. I suspect you may have early COPD related to your smoking history.
        Patient: Is that serious?
        Doctor: It can be, but we can manage it with medications and lifestyle changes. Quitting smoking would be the most important step.
        Patient: I've been thinking about quitting.
        Doctor: That's good to hear. Let's talk about a smoking cessation plan and I'll refer you for those lung function tests.
        """,
        """
        Doctor: Good morning, what can I help you with today?
        Patient: My knees have been really painful, and it's getting worse.
        Doctor: I'm sorry to hear that. How long have you been experiencing this pain?
        Patient: It's been going on for about a year, but in the last few months, it's really started to affect my daily life.
        Doctor: Are both knees affected?
        Patient: Yes, both of them hurt, especially when I'm going up and down stairs.
        Doctor: Do you notice any swelling or stiffness in your knees?
        Patient: They feel stiff in the mornings, and sometimes they do look a bit swollen by the end of the day.
        Doctor: Have you been taking anything for the pain?
        Patient: Just over-the-counter ibuprofen, but it's not helping much anymore.
        Doctor: Were you previously quite active?
        Patient: Yes, I used to walk every day and even did some light jogging, but I've had to stop.
        Doctor: Let me examine your knees and see what's going on.
        [Examination conducted]
        Doctor: Based on your symptoms and my examination, it appears you may have osteoarthritis in both knees. I'd like to order some X-rays to confirm.
        Patient: Is there anything that can help with the pain?
        Doctor: Yes, we can discuss pain management options and I'll refer you to a physiotherapist who can teach you exercises to strengthen the muscles around your knees.
        Patient: That sounds good. What about my weight? I know I could stand to lose some pounds.
        Doctor: Weight loss would definitely help reduce the pressure on your knees. Let's talk about some dietary changes that might help with that too.
        """,
    ]
    
    # Create one consultation at a time and commit after each
    successful_consultations = 0
    
    for i in range(5):
        try:
            # Always select a valid user (no random None values)
            # The consultation model requires a valid user_id (not nullable)
            user = random.choice(users)
            user_id = user.id
            logger.debug(f"Using user {user.first_name} {user.last_name} with ID: {user_id}")
            
            # Select a random case
            case = random.choice(cases)
            logger.debug(f"Using case ID: {case.id}")
            
            # Select a random transcript or generate a placeholder
            transcript = random.choice(sample_transcripts) if random.random() > 0.5 else f"[Consultation transcript for case regarding {case.presenting_complaint[:30]}...]"
            
            # Generate random scores
            overall_score = random.uniform(50.0, 95.0)
            domain_scores = {
                "data_gathering": {
                    "score": random.uniform(2.0, 5.0),
                    "examples": ["Asked relevant questions about symptoms", "Inquired about medical history"],
                    "areas_for_improvement": ["Could explore social factors more thoroughly"]
                },
                "clinical_management": {
                    "score": random.uniform(2.0, 5.0),
                    "examples": ["Provided clear explanation of likely diagnosis", "Outlined appropriate management plan"],
                    "areas_for_improvement": ["Consider discussing preventative measures"]
                },
                "interpersonal_skills": {
                    "score": random.uniform(2.0, 5.0),
                    "examples": ["Maintained good rapport", "Used appropriate language"],
                    "areas_for_improvement": ["Could improve non-verbal communication"]
                }
            }
            
            feedback = f"Overall a {get_performance_level(overall_score)} consultation. You demonstrated strengths in communication and history taking but could improve on clinical management planning."
            
            # Create consultation with is_shared set to a random boolean value
            consultation = Consultation(
                user_id=user_id,
                case_id=case.id,
                transcript=transcript,
                overall_score=overall_score,
                domain_scores=domain_scores,
                feedback=feedback,
                is_shared=random.choice([True, False]),
                audio_recording=None,
                duration_seconds=random.randint(300, 900) if random.random() > 0.7 else None
            )
            
            # Add and commit each consultation individually
            db.add(consultation)
            db.commit()
            successful_consultations += 1
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating consultation #{i+1}: {str(e)}")
    
    consultation_count = db.query(Consultation).count()
    logger.info(f"Created {successful_consultations} test consultations. Database now has {consultation_count} consultations")

def get_performance_level(score):
    """Return a performance level based on score"""
    if score >= 85:
        return "excellent"
    elif score >= 70:
        return "good"
    elif score >= 55:
        return "satisfactory"
    else:
        return "needs improvement"

def main():
    """Main function to seed the database"""
    logger.info("Starting database seeding...")
    
    # Get database session using the load function
    # Since we're not in a FastAPI context where dependencies are injected,
    # we need to get the generator and advance it to get the session
    db_generator = load()
    db = next(db_generator)
    
    try:
        # Create test data
        users = create_test_users(db)
        # Make sure we have users before continuing
        if not users:
            logger.error("No users were created or found in the database. Cannot create consultations.")
            return
            
        logger.info(f"Using {len(users)} users with IDs: {[user.id for user in users]}")
        
        cases = create_test_cases(db)
        create_test_consultations(db, users, cases)
        
        logger.success("Database seeding completed successfully!")
    finally:
        # Properly close the database session
        try:
            db_generator.close()
        except:
            pass

if __name__ == "__main__":
    main()
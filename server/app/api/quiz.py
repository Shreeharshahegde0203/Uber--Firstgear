from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, date
import random

from ..db.database import get_db
from ..db.models import User

router = APIRouter(prefix="/api/quiz", tags=["quiz"])

class QuizQuestion(BaseModel):
    id: int
    question: str
    options: List[str]
    # correct_answer_index is not sent to frontend

class QuizResponse(BaseModel):
    questions: List[QuizQuestion]
    date: str

class QuizSubmission(BaseModel):
    user_id: int
    answers: List[int]  # List of selected indices

class QuizResult(BaseModel):
    score: int
    total: int
    coins_earned: int
    new_balance: int
    message: str
    results: Optional[List[dict]] = None  # Detailed results with explanations

class AnswerCheck(BaseModel):
    user_id: int
    question_id: int
    answer_index: int

class AnswerResult(BaseModel):
    correct: bool
    correct_answer: int
    explanation: str

# Comprehensive Question Bank with detailed explanations
QUESTION_BANK = [
    {
        "q": "You're driving at 60 km/h and see a yellow traffic light. What should you do?",
        "options": ["Accelerate to cross quickly", "Stop safely if possible", "Honk and continue", "Flash your headlights"],
        "correct": 1,
        "explanation": "✅ Correct Answer: Stop safely if possible.\n\nA yellow light warns that the signal is about to turn red. If you can stop safely before the intersection, you must do so. Accelerating through a yellow light is dangerous and can result in running a red light."
    },
    {
        "q": "What is the '3-second rule' in driving?",
        "options": ["Time to check mirrors", "Safe following distance from the vehicle ahead", "Maximum time at a stop sign", "Time to complete a lane change"],
        "correct": 1,
        "explanation": "✅ Correct Answer: Safe following distance from the vehicle ahead.\n\nThe 3-second rule helps maintain a safe gap. Pick a fixed point, and when the car ahead passes it, count '1-2-3'. You should reach that point only after finishing the count. In rain or fog, increase to 5-6 seconds."
    },
    {
        "q": "You're parking uphill next to a curb. Which way should your front wheels point?",
        "options": ["Toward the curb", "Away from the curb", "Straight ahead", "Depends on traffic"],
        "correct": 1,
        "explanation": "✅ Correct Answer: Away from the curb.\n\nWhen parking uphill WITH a curb, turn wheels AWAY from the curb. If brakes fail, the car rolls backward and the wheels hit the curb, stopping the car. This prevents your vehicle from rolling into traffic."
    },
    {
        "q": "A pedestrian is crossing at a zebra crossing. What must you do?",
        "options": ["Honk to alert them", "Slow down and proceed carefully", "Stop completely and wait", "Flash headlights"],
        "correct": 2,
        "explanation": "✅ Correct Answer: Stop completely and wait.\n\nPedestrians have absolute right of way at zebra crossings. You must come to a complete stop and wait until they have completely crossed. Never honk at pedestrians on a crossing."
    },
    {
        "q": "What does a flashing red traffic signal mean?",
        "options": ["Slow down and proceed", "Stop, then go when safe", "Traffic light is broken", "Emergency vehicles approaching"],
        "correct": 1,
        "explanation": "✅ Correct Answer: Stop, then go when safe.\n\nA flashing red light works exactly like a STOP sign. You must come to a complete stop, check all directions for traffic and pedestrians, and proceed only when it's safe to do so."
    },
    {
        "q": "Two cars arrive at a 4-way stop at the same time. Who goes first?",
        "options": ["The larger vehicle", "The vehicle on the left", "The vehicle on the right", "The one who honks first"],
        "correct": 2,
        "explanation": "✅ Correct Answer: The vehicle on the right.\n\nWhen two vehicles arrive simultaneously at a 4-way stop, the vehicle on the RIGHT has the right of way. This is called the 'right-hand rule'. If facing each other, the one going straight goes before the one turning."
    },
    {
        "q": "Your car starts skidding on a wet road. What should you do?",
        "options": ["Brake hard immediately", "Turn the steering wheel sharply", "Ease off the accelerator gently", "Accelerate to regain control"],
        "correct": 2,
        "explanation": "✅ Correct Answer: Ease off the accelerator gently.\n\nWhen skidding (hydroplaning), don't panic! Gently release the accelerator, don't brake suddenly, and steer smoothly in the direction you want to go. Sudden movements can cause you to lose complete control."
    },
    {
        "q": "What is the blind spot of a vehicle?",
        "options": ["Area visible in rearview mirror", "Area not visible in any mirror", "Front of the vehicle", "Dashboard area"],
        "correct": 1,
        "explanation": "✅ Correct Answer: Area not visible in any mirror.\n\nBlind spots are areas around your vehicle that you cannot see in your mirrors. They're typically on both sides, slightly behind you. Always turn your head to check blind spots before changing lanes or merging."
    },
    {
        "q": "When should you use your vehicle's horn?",
        "options": ["To greet friends", "To warn others of danger", "To express frustration in traffic", "At traffic signals"],
        "correct": 1,
        "explanation": "✅ Correct Answer: To warn others of danger.\n\nThe horn should only be used to alert other road users of potential danger, like warning a pedestrian who hasn't seen you. Using horns unnecessarily causes noise pollution and is illegal in many areas."
    },
    {
        "q": "What does ABS (Anti-lock Braking System) do?",
        "options": ["Makes the car stop faster", "Prevents wheels from locking during hard braking", "Automatically applies brakes", "Reduces fuel consumption"],
        "correct": 1,
        "explanation": "✅ Correct Answer: Prevents wheels from locking during hard braking.\n\nABS rapidly pumps the brakes (many times per second) during emergency braking to prevent wheel lock-up. This allows you to maintain steering control while braking hard. You'll feel a pulsing in the brake pedal - this is normal!"
    },
    {
        "q": "You see a school bus with flashing red lights stopped ahead. What must you do?",
        "options": ["Slow down and pass carefully", "Stop and wait until lights stop flashing", "Honk and proceed", "Change lanes and overtake"],
        "correct": 1,
        "explanation": "✅ Correct Answer: Stop and wait until lights stop flashing.\n\nWhen a school bus displays flashing red lights, children are getting on or off. ALL traffic in BOTH directions must stop and wait. Proceed only after the lights stop flashing and the bus starts moving."
    },
    {
        "q": "What's the correct order for starting a parked car with manual transmission?",
        "options": ["Start engine, release handbrake, press clutch", "Press clutch, start engine, release handbrake", "Release handbrake, press clutch, start engine", "Press brake, start engine, release clutch"],
        "correct": 1,
        "explanation": "✅ Correct Answer: Press clutch, start engine, release handbrake.\n\nFor manual cars: 1) Ensure gear is in neutral, 2) Press clutch fully, 3) Start engine, 4) Press brake, 5) Release handbrake, 6) Select gear. This sequence prevents the car from lurching forward unexpectedly."
    },
    {
        "q": "What should you do before opening your car door when parked on a road?",
        "options": ["Open quickly to save time", "Check mirrors and look behind for traffic", "Honk your horn first", "Turn on hazard lights"],
        "correct": 1,
        "explanation": "✅ Correct Answer: Check mirrors and look behind for traffic.\n\nUse the 'Dutch Reach' technique: Open the door with your far hand (right hand for driver's door). This forces you to turn your body and naturally look back for cyclists, motorcycles, or other vehicles approaching."
    },
    {
        "q": "At night, when should you switch from high beam to low beam headlights?",
        "options": ["When entering a city", "When another vehicle approaches from opposite direction", "Never switch while driving", "Only at traffic signals"],
        "correct": 1,
        "explanation": "✅ Correct Answer: When another vehicle approaches from opposite direction.\n\nHigh beams can blind oncoming drivers. Switch to low beam when: 1) A vehicle approaches within 200m, 2) Following another vehicle within 200m, 3) In well-lit areas, 4) In fog or heavy rain (high beams reflect back)."
    },
    {
        "q": "What does a solid white line between lanes mean?",
        "options": ["You can change lanes freely", "Lane changing is discouraged", "Only right turns allowed", "Road is ending"],
        "correct": 1,
        "explanation": "✅ Correct Answer: Lane changing is discouraged.\n\nA solid white line means you should stay in your lane. It's used in areas where changing lanes could be dangerous, like near intersections or in merging zones. A broken white line means lane changing is permitted when safe."
    },
    {
        "q": "Your car's engine temperature gauge shows it's overheating. What should you do?",
        "options": ["Stop immediately and open the hood", "Turn on the heater and pull over safely", "Pour cold water on the engine", "Ignore it and continue driving"],
        "correct": 1,
        "explanation": "✅ Correct Answer: Turn on the heater and pull over safely.\n\nTurning on the heater draws heat away from the engine. Pull over safely, turn off the AC, and let the engine cool for 15-20 minutes. NEVER open the radiator cap when hot - pressurized steam can cause severe burns!"
    },
    {
        "q": "What's the safest hand position on the steering wheel?",
        "options": ["12 o'clock position (top)", "10 and 2 o'clock", "9 and 3 o'clock", "Bottom of the wheel"],
        "correct": 2,
        "explanation": "✅ Correct Answer: 9 and 3 o'clock.\n\nThe modern recommended position is 9 and 3 (or slightly lower at 8 and 4). This provides best control, keeps your arms away from the airbag deployment zone, and reduces fatigue on long drives. The old 10-2 position can cause arm injuries if airbags deploy."
    },
    {
        "q": "You approach a roundabout. Who has the right of way?",
        "options": ["Vehicles entering the roundabout", "Vehicles already in the roundabout", "Larger vehicles", "Vehicles from the right"],
        "correct": 1,
        "explanation": "✅ Correct Answer: Vehicles already in the roundabout.\n\nAlways yield to traffic already circulating inside the roundabout. Wait for a safe gap, then enter. Signal left when you're about to exit. In India, traffic moves clockwise in roundabouts."
    },
    {
        "q": "What should you do if an ambulance with sirens approaches from behind?",
        "options": ["Speed up to get out of the way", "Stop immediately wherever you are", "Pull over to the left and stop", "Continue at the same speed"],
        "correct": 2,
        "explanation": "✅ Correct Answer: Pull over to the left and stop.\n\nSafely move to the left side of the road and stop to let the ambulance pass. Don't stop in the middle of the road or at intersections. Check your mirrors before moving, and resume driving only after the ambulance has passed."
    },
    {
        "q": "What's the main purpose of a catalytic converter in your car?",
        "options": ["Improves fuel efficiency", "Reduces harmful exhaust emissions", "Makes the engine quieter", "Increases horsepower"],
        "correct": 1,
        "explanation": "✅ Correct Answer: Reduces harmful exhaust emissions.\n\nThe catalytic converter transforms harmful gases (carbon monoxide, hydrocarbons, nitrogen oxides) into less harmful substances (carbon dioxide, water, nitrogen). It's a crucial part of your car's emission control system and required by law."
    }
]

# Store active quizzes in memory for validation (simple cache)
# Key: user_id, Value: { "questions": [...], "date": ... }
active_quizzes = {}

@router.get("/daily/{user_id}", response_model=QuizResponse)
def get_daily_quiz(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if user already took quiz today
    today = date.today()
    if user.last_quiz_date and user.last_quiz_date.date() == today:
        raise HTTPException(status_code=400, detail="You have already completed today's quiz")

    # Generate 5 random questions
    selected_indices = random.sample(range(len(QUESTION_BANK)), 5)
    quiz_questions = []
    stored_quiz_data = []

    for idx in selected_indices:
        q_data = QUESTION_BANK[idx]
        quiz_questions.append(QuizQuestion(
            id=idx,
            question=q_data["q"],
            options=q_data["options"]
        ))
        stored_quiz_data.append({
            "id": idx,
            "correct": q_data["correct"]
        })

    # Store for validation
    active_quizzes[user_id] = {
        "questions": stored_quiz_data,
        "date": str(today)
    }

    return QuizResponse(questions=quiz_questions, date=str(today))

@router.post("/submit", response_model=QuizResult)
def submit_quiz(submission: QuizSubmission, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == submission.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Validate active quiz
    if submission.user_id not in active_quizzes:
        raise HTTPException(status_code=400, detail="No active quiz found. Please start a new quiz.")

    quiz_data = active_quizzes[submission.user_id]
    
    # Verify it's still the same day
    if quiz_data["date"] != str(date.today()):
        raise HTTPException(status_code=400, detail="Quiz expired. Please start a new one.")

    # Check answers
    correct_count = 0
    questions = quiz_data["questions"]
    
    if len(submission.answers) != len(questions):
        raise HTTPException(status_code=400, detail="Invalid number of answers")

    for i, answer_idx in enumerate(submission.answers):
        if answer_idx == questions[i]["correct"]:
            correct_count += 1

    # Calculate score
    total = len(questions)
    score_percent = (correct_count / total) * 100
    coins_earned = 0
    message = f"You got {correct_count} out of {total} correct!"

    # Award coins if score >= 80% (4/5)
    if score_percent >= 80:
        coins_earned = 10
        user.coins = (user.coins or 0) + coins_earned
        user.last_quiz_date = datetime.utcnow()
        db.commit()
        message += " You earned 10 coins!"
    else:
        message += " Try again tomorrow to earn coins."

    # Clear active quiz
    del active_quizzes[submission.user_id]

    return QuizResult(
        score=correct_count,
        total=total,
        coins_earned=coins_earned,
        new_balance=user.coins or 0,
        message=message
    )

@router.post("/check-answer", response_model=AnswerResult)
def check_answer(answer: AnswerCheck):
    """Check a single answer and return explanation"""
    if answer.user_id not in active_quizzes:
        raise HTTPException(status_code=400, detail="No active quiz found")
    
    question_id = answer.question_id
    if question_id < 0 or question_id >= len(QUESTION_BANK):
        raise HTTPException(status_code=400, detail="Invalid question ID")
    
    q_data = QUESTION_BANK[question_id]
    is_correct = answer.answer_index == q_data["correct"]
    
    return AnswerResult(
        correct=is_correct,
        correct_answer=q_data["correct"],
        explanation=q_data["explanation"]
    )

@router.get("/balance/{user_id}")
def get_balance(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "coins": user.coins or 0,
        "rupee_value": (user.coins or 0) / 10
    }

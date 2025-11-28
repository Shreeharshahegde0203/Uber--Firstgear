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

# Mock Question Bank with explanations
QUESTION_BANK = [
    {
        "q": "What should you do when approaching a yellow traffic light?",
        "options": ["Speed up to cross", "Stop if it can be done safely", "Honk and proceed", "Ignore it"],
        "correct": 1,
        "explanation": "A yellow light means the signal is about to turn red. You should stop if you can do so safely. Speeding up is dangerous and illegal in most jurisdictions."
    },
    {
        "q": "What is the safe following distance under normal driving conditions?",
        "options": ["1 second", "2 seconds", "3 seconds", "5 seconds"],
        "correct": 2,
        "explanation": "The 3-second rule provides adequate reaction time and braking distance. In poor conditions (rain, fog), increase to 4-6 seconds."
    },
    {
        "q": "When parking uphill with a curb, which way should you turn your wheels?",
        "options": ["Towards the curb", "Away from the curb", "Straight ahead", "It doesn't matter"],
        "correct": 1,
        "explanation": "Turn wheels away from curb when parking uphill. If brakes fail, the car will roll back into the curb, preventing it from rolling into traffic."
    },
    {
        "q": "What does a flashing red traffic light mean?",
        "options": ["Stop and proceed when safe", "Slow down", "Yield to oncoming traffic", "Do not enter"],
        "correct": 0,
        "explanation": "A flashing red light is treated like a stop sign. Come to a complete stop, check for traffic, and proceed when safe."
    },
    {
        "q": "Who has the right of way at a 4-way stop?",
        "options": ["The biggest vehicle", "The vehicle that arrived first", "The vehicle on the left", "The faster vehicle"],
        "correct": 1,
        "explanation": "At a 4-way stop, the first vehicle to arrive has the right of way. If two vehicles arrive simultaneously, the one on the right goes first."
    },
    {
        "q": "What is the purpose of an ABS (Anti-lock Braking System)?",
        "options": ["To stop faster", "To prevent wheels from locking during braking", "To make the car go faster", "To save fuel"],
        "correct": 1,
        "explanation": "ABS prevents wheel lock-up during hard braking, allowing you to maintain steering control. It pulses the brakes automatically to prevent skidding."
    },
    {
        "q": "When is it legal to pass a vehicle on the right?",
        "options": ["When the vehicle ahead is turning left", "On a one-way street", "When there are two or more lanes in your direction", "All of the above"],
        "correct": 3,
        "explanation": "Passing on the right is legal in all these situations. However, always ensure it's safe and check blind spots before changing lanes."
    },
    {
        "q": "What should you do if your vehicle starts to hydroplane?",
        "options": ["Brake hard", "Steer sharply", "Ease off the accelerator", "Accelerate"],
        "correct": 2,
        "explanation": "When hydroplaning, ease off the gas and steer gently in the direction you want to go. Avoid sudden braking or steering which can cause loss of control."
    },
    {
        "q": "What is the meaning of a solid white line on the road?",
        "options": ["Lane changing is allowed", "Lane changing is discouraged/prohibited", "Stop line", "Parking line"],
        "correct": 1,
        "explanation": "Solid white lines indicate lane changing is discouraged or prohibited. They're often used near intersections or in areas where lane changes could be dangerous."
    },
    {
        "q": "When should you use your high beam headlights?",
        "options": ["In fog", "In heavy rain", "On open country roads with no oncoming traffic", "When following another vehicle"],
        "correct": 2,
        "explanation": "High beams provide better visibility on dark roads but should only be used when no other vehicles are ahead. Switch to low beams within 150m of oncoming traffic."
    },
    {
        "q": "What is the maximum speed limit in residential areas in India?",
        "options": ["20 km/h", "25 km/h", "30 km/h", "40 km/h"],
        "correct": 1,
        "explanation": "In India, the speed limit in residential areas is typically 25 km/h to ensure pedestrian safety, especially near schools and hospitals."
    },
    {
        "q": "What does a broken yellow center line mean?",
        "options": ["No passing allowed", "Passing allowed when safe", "Road under construction", "One-way road"],
        "correct": 1,
        "explanation": "A broken yellow center line indicates passing is allowed when safe. Ensure the road ahead is clear for a safe distance before overtaking."
    },
    {
        "q": "What should you check before changing lanes?",
        "options": ["Only mirrors", "Only blind spot", "Mirrors, blind spot, and signal", "Nothing if road is empty"],
        "correct": 2,
        "explanation": "Always check mirrors, look over your shoulder for blind spots, and signal before changing lanes. This 'Mirror-Signal-Maneuver' routine prevents accidents."
    },
    {
        "q": "When should you use hazard lights?",
        "options": ["When parking illegally", "When driving slowly", "When your vehicle is stationary and causing an obstruction", "When overtaking"],
        "correct": 2,
        "explanation": "Hazard lights should only be used when your vehicle is stationary and may be a hazard to other road users, like during a breakdown."
    },
    {
        "q": "What is the correct hand signal for a right turn?",
        "options": ["Arm extended straight out", "Arm extended upward at 90°", "Arm extended downward at 90°", "Circular motion"],
        "correct": 1,
        "explanation": "For a right turn, extend your left arm out and bend it upward at 90° (forming an 'L' shape). This is visible to drivers behind you."
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

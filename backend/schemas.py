from pydantic import BaseModel
from typing import List, Optional, Any

# Auth Schemas
class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    id: str
    username: str

# Document Schemas
class DocumentResponse(BaseModel):
    id: str
    filename: str
    content_type: str
    upload_date: Any

# Chat Schemas
class ChatRequest(BaseModel):
    doc_id: str
    question: str

class ChatResponse(BaseModel):
    answer: str

# Quiz Schemas
class QuizRequest(BaseModel):
    doc_id: str
    num_questions: int = 5
    quiz_type: str = "multiple_choice"  # 'multiple_choice' or 'true_false' or 'open_ended'

class Question(BaseModel):
    question_text: str
    options: Optional[List[str]] = None
    correct_answer: str

class QuizResponse(BaseModel):
    questions: List[Question]

# Summary Schemas
class SummaryRequest(BaseModel):
    doc_id: str
    length: str = "medium"  # short, medium, long

class SummaryResponse(BaseModel):
    summary: str

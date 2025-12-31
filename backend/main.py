from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta, timezone
import shutil
import os
import tempfile
from typing import List
from bson import ObjectId

from database import (
    users_collection, 
    documents_collection, 
    chat_history_collection, 
    quizzes_collection, 
    summaries_collection,
    test_connection
)
from schemas import (
    UserCreate, UserResponse, Token, 
    DocumentResponse, ChatRequest, ChatResponse,
    QuizRequest, QuizResponse, SummaryRequest, SummaryResponse
)
from auth import (
    get_password_hash, verify_password, create_access_token, 
    get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES
)
from ai import generate_answer, generate_quiz, generate_summary

import pypdf
import docx

app = FastAPI(title="DocuMind AI Backend")

# Startup event to test MongoDB connection
@app.on_event("startup")
async def startup_event():
    """Test MongoDB connection on startup"""
    connected = await test_connection()
    if not connected:
        print("WARNING: MongoDB connection failed. Some features may not work.")

# CORS Setup
# Note: Cannot use allow_origins=["*"] with allow_credentials=True
# For local file access (file://), we need to allow all origins without credentials
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (required for file:// protocol)
    allow_credentials=False,  # Must be False when using "*" origins
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Helper Functions for File Parsing ---

def extract_text_from_pdf(file_path: str) -> str:
    reader = pypdf.PdfReader(file_path)
    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
    return text

def extract_text_from_docx(file_path: str) -> str:
    doc = docx.Document(file_path)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text

def extract_text_from_txt(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

# --- Auth Endpoints ---

@app.post("/auth/register", response_model=UserResponse)
async def register(user: UserCreate):
    try:
        existing_user = await users_collection.find_one({"username": user.username})
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already registered")
        
        hashed_password = get_password_hash(user.password)
        user_dict = {
            "username": user.username,
            "hashed_password": hashed_password,
            "created_at": datetime.now(timezone.utc)
        }
        result = await users_collection.insert_one(user_dict)
        return UserResponse(id=str(result.inserted_id), username=user.username)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Registration error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@app.post("/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await users_collection.find_one({"username": form_data.username})
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# --- Document Endpoints ---

@app.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...), 
    current_user: dict = Depends(get_current_user)
):
    # Validate filename
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")
    
    # Remove specific extension restriction to allow any text-based file
    ext = os.path.splitext(file.filename)[1].lower()
    
    
    # Create a temp file in the system temp directory
    # We use delete=False so we can close it and then reopen it for reading in other libraries
    # This is required for Windows compatibility where an open file cannot be opened again
    try:
        suffix = os.path.splitext(file.filename)[1].lower() if file.filename else ""
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            temp_filename = tmp_file.name

        # Extract text
        text = ""
        try:
            if ext == ".pdf":
                try:
                    text = extract_text_from_pdf(temp_filename)
                except Exception:
                    # Fallback if PDF parsing fails (e.g. malformed)
                    pass
            elif ext == ".docx":
                try:
                    text = extract_text_from_docx(temp_filename)
                except Exception:
                    pass
            elif ext == ".txt":
                # Try utf-8 first
                try:
                    text = extract_text_from_txt(temp_filename)
                except Exception:
                    pass
            
            # If text is still empty (parser failed or unknown extension), try raw fallback
            if not text.strip():
                try:
                    # utf-8 fallback
                    with open(temp_filename, "r", encoding="utf-8") as f:
                        text = f.read()
                except UnicodeDecodeError:
                    # latin-1 fallback
                    try:
                        with open(temp_filename, "r", encoding="latin-1") as f:
                            text = f.read()
                    except Exception:
                        text = ""
        except Exception as e:
            # Should be caught by inner blocks but safety net
            print(f"Extraction error: {e}")
            text = ""
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    finally:
        # Clean up temp file
        if 'temp_filename' in locals() and os.path.exists(temp_filename):
            try:
                os.remove(temp_filename)
            except Exception:
                pass

    if not text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text. File might be empty, scanned (image-only), or binary.")
    
    # Check if duplicate (simple hash check or just by filename/user for now)
    # Limit text size to avoid MongoDB 16MB limit
    MAX_TEXT_SIZE = 10 * 1024 * 1024 # 10MB
    if len(text) > MAX_TEXT_SIZE:
        text = text[:MAX_TEXT_SIZE] + "\n...[Content truncated due to size]..."

    # Reusing text if exists: Here we just insert new document entry
    doc_entry = {
        "filename": os.path.basename(file.filename), # Sanitize filename
        "content_type": file.content_type,
        "text": text,
        "uploaded_by": current_user["username"],
        "upload_date": datetime.now(timezone.utc)
    }
    
    try:
        result = await documents_collection.insert_one(doc_entry)
        
        return DocumentResponse(
            id=str(result.inserted_id),
            filename=doc_entry["filename"],
            content_type=doc_entry["content_type"],
            upload_date=doc_entry["upload_date"]
        )
    except Exception as e:
        print(f"Database insert error: {e}")
        raise HTTPException(status_code=500, detail="Failed to save document. It might be too large.")

# --- AI Feature Endpoints ---

async def get_document_text(doc_id: str, username: str):
    try:
        doc = await documents_collection.find_one({"_id": ObjectId(doc_id)})
    except (ValueError, TypeError):
        doc = None
    
    if not doc: # or doc["uploaded_by"] != username: # Optional: strictly restrict to owner?
        raise HTTPException(status_code=404, detail="Document not found")
    return doc["text"]

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user)
):
    context = await get_document_text(request.doc_id, current_user["username"])
    
    answer = await generate_answer(context, request.question)
    
    # Store history
    await chat_history_collection.insert_one({
        "doc_id": request.doc_id,
        "user": current_user["username"],
        "question": request.question,
        "answer": answer,
        "timestamp": datetime.now(timezone.utc)
    })
    
    return ChatResponse(answer=answer)

@app.post("/quiz", response_model=QuizResponse)
async def quiz_endpoint(
    request: QuizRequest,
    current_user: dict = Depends(get_current_user)
):
    context = await get_document_text(request.doc_id, current_user["username"])
    
    questions = await generate_quiz(context, request.num_questions, request.quiz_type)
    
    # Store quiz
    await quizzes_collection.insert_one({
        "doc_id": request.doc_id,
        "user": current_user["username"],
        "questions": questions,
        "type": request.quiz_type,
        "created_at": datetime.now(timezone.utc)
    })
    
    return QuizResponse(questions=questions)

@app.post("/summary", response_model=SummaryResponse)
async def summary_endpoint(
    request: SummaryRequest,
    current_user: dict = Depends(get_current_user)
):
    context = await get_document_text(request.doc_id, current_user["username"])
    
    summary = await generate_summary(context, request.length)
    
    # Store summary
    await summaries_collection.insert_one({
        "doc_id": request.doc_id,
        "user": current_user["username"],
        "summary": summary,
        "length_type": request.length,
        "created_at": datetime.now(timezone.utc)
    })
    
    return SummaryResponse(summary=summary)

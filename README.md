# DocuMind AI - Intelligent Document Analysis

**DocuMind AI** is a state-of-the-art intelligent document analysis platform designed to transform how you interact with documents. Upload any text-based document and instantly chat, generate quizzes, or get summaries using advanced AI.

## 🚀 Features

-   📄 **Universal Document Support**: Upload PDF, DOCX, TXT, MD, PY, and more.
-   💬 **AI Assistant**: Natural language Q&A with your documents.
-   📝 **Smart Quizzes**: Auto-generate multiple-choice or open-ended quizzes for study.
-   📊 **Intelligent Summarization**: Get concise summaries tailored to your preferred length.
-   🔒 **Secure & Private**: Robust authentication and secure temporary file processing.

## 🛠️ Stack

-   **Backend**: FastAPI, MongoDB, Motor, Pydantic
-   **Frontend**: Vanilla JavaScript, HTML5, CSS3 (Glassmorphism UI)
-   **AI Engine**: Compatible with OpenAI, Groq, and OpenRouter

## ⚡ Setup Instructions

### 1. Prerequisites
-   Python 3.8+ installed
-   Docker Desktop (for MongoDB) OR a local MongoDB instance running

### 2. Backend Setup

1.  Open a terminal in the `backend` folder:
    ```bash
    cd backend
    ```
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Create a `.env` file in the `backend` folder and add your configuration:
    ```env
    # Database
    MONGO_URI=mongodb://localhost:27017
    DB_NAME=documind_db

    # Security
    SECRET_KEY=super_secret_key_change_me
    ALGORITHM=HS256
    ACCESS_TOKEN_EXPIRE_MINUTES=60

    # AI Provider (Choose ONE)
    
    # Option 1: OpenRouter (DeepSeek R1 etc.)
    OPENROUTER_API_KEY=your_key_here
    OPENAI_BASE_URL=https://openrouter.ai/api/v1
    AI_MODEL=deepseek/deepseek-r1

    # Option 2: Groq (Free & Fast)
    # GROQ_API_KEY=your_key_here
    # OPENAI_BASE_URL=https://api.groq.com/openai/v1
    # AI_MODEL=llama-3.1-70b-versatile
    ```
4.  Start the server:
    ```bash
    uvicorn main:app --reload
    ```
    The API will be available at `http://127.0.0.1:8000`.

### 3. Frontend Setup

1.  Open the `frontend` folder.
2.  Launch `index.html`.
    -   **Option A (Recommended)**: Use a simple HTTP server to avoid CORS issues with local files:
        ```bash
        cd frontend
        python -m http.server 8001
        ```
        Then allow access at `http://localhost:8001`.
    -   **Option B (Simple)**: Just double-click `index.html` to open it in your browser (some features might be restricted by browser security policies).

## 📖 Usage Guide

1.  **Register/Login**: Create a new account to secure your data.
2.  **Upload**: Drag and drop your file (PDF, DOCX, TXT...).
3.  **Interact**:
    -   **Chat**: Ask "What is the main conclusion of this paper?"
    -   **Quiz**: Go to the Quiz tab and generate 5 review questions.
    -   **Summary**: Click "Medium" to get a quick overview.

## 📄 License

MIT License.

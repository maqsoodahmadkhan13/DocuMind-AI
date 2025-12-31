import os
from openai import AsyncOpenAI
from dotenv import load_dotenv
import json

load_dotenv()

# Configuration for AI models
# Supports OpenRouter (DeepSeek R1), Groq, OpenAI, and other OpenAI-compatible APIs
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Determine Base URL
if os.getenv("OPENAI_BASE_URL"):
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
elif GROQ_API_KEY:
    OPENAI_BASE_URL = "https://api.groq.com/openai/v1"
else:
    OPENAI_BASE_URL = "https://openrouter.ai/api/v1"

# Determine Model
if os.getenv("AI_MODEL"):
    AI_MODEL = os.getenv("AI_MODEL")
elif GROQ_API_KEY:
    AI_MODEL = "llama-3.3-70b-versatile"
else:
    AI_MODEL = "deepseek/deepseek-r1"

# Determine API Key
if "groq.com" in OPENAI_BASE_URL and GROQ_API_KEY:
    OPENAI_API_KEY = GROQ_API_KEY
else:
    # Fallback or explicit set
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or GROQ_API_KEY or os.getenv("OPENROUTER_API_KEY")

# If no API key is provided, show helpful error message
if not OPENAI_API_KEY:
    print("\n" + "="*60)
    print("⚠️  API KEY REQUIRED")
    print("="*60)
    print("To use AI models, get an API key from one of these:")
    print("  1. OpenRouter (Recommended - DeepSeek R1 & more):")
    print("     - Visit: https://openrouter.ai/")
    print("     - Sign up and get your API key")
    print("     - Set: OPENROUTER_API_KEY=your_key_here")
    print("     - Set: AI_MODEL=deepseek/deepseek-r1")
    print("")
    print("  2. Groq (Fast & Free):")
    print("     - Visit: https://console.groq.com/")
    print("     - Set: GROQ_API_KEY=your_key_here")
    print("     - Set: OPENAI_BASE_URL=https://api.groq.com/openai/v1")
    print("")
    print("  3. OpenAI (Paid):")
    print("     - Set: OPENAI_API_KEY=your_key_here")
    print("     - Set: OPENAI_BASE_URL=https://api.openai.com/v1")
    print("     - Set: AI_MODEL=gpt-3.5-turbo")
    print("="*60 + "\n")
    raise ValueError(
        "API key is required. Set OPENROUTER_API_KEY, GROQ_API_KEY, or OPENAI_API_KEY in your .env file. "
        "See instructions above."
    )

# Initialize OpenAI-compatible Client
# Works with OpenRouter, Groq, OpenAI, LocalAI, and other OpenAI-compatible APIs
# OpenRouter requires HTTP-Referer and X-Title headers
default_headers = {}
if "openrouter.ai" in OPENAI_BASE_URL:
    default_headers = {
        "HTTP-Referer": "https://github.com/yourusername/documind-ai",  # Optional: Update with your repo
        "X-Title": "DocuMind AI"
    }

client = AsyncOpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL,
    default_headers=default_headers
)

async def generate_summary(context: str, length: str) -> str:
    """
    Generates a summary of the document content.
    """
    try:
        length_prompt = {
            "short": "Summarize this in 3-5 sentences.",
            "medium": "Provide a detailed summary in 2 paragraphs.",
            "long": "Provide a comprehensive summary of the document, covering all key points."
        }
        
        # Truncate to avoid context limit issues
        truncated_context = context[:15000]
        
        prompt = f"""
        You are an expert summarizer.
        Task: {length_prompt.get(length, "Summarize the following text.")}
        
        Document Content:
        {truncated_context}
        
        Summary:
        """
        
        response = await client.chat.completions.create(
            model=AI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        
        if not response.choices or len(response.choices) == 0:
            return "Unable to generate summary. Please try again."
        
        content = response.choices[0].message.content
        if not content:
            return "Unable to generate summary. Please try again."
        return content.strip()
    except Exception as e:
        return f"Error generating summary: {str(e)}"

async def generate_answer(context: str, question: str) -> str:
    """
    Answers a question strictly based on the document content.
    """
    try:
        # Truncate to avoid context limit issues
        truncated_context = context[:15000]
        
        prompt = f"""
        You are a helpful AI assistant. Answer the user's question STRICTLY based on the provided document content.
        If the answer is NOT in the document, say "I cannot answer this question based on the document provided."
        
        Document Content:
        {truncated_context}
        
        Question: {question}
        
        Answer:
        """
        
        response = await client.chat.completions.create(
            model=AI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        if not response.choices or len(response.choices) == 0:
            return "Unable to generate answer. Please try again."
        
        content = response.choices[0].message.content
        if not content:
            return "Unable to generate answer. Please try again."
        return content.strip()
    except Exception as e:
        return f"Error generating answer: {str(e)}"

async def generate_quiz(context: str, num_questions: int, quiz_type: str) -> list:
    """
    Generates a quiz based on the document content in JSON format.
    """
    format_instruction = ""
    if quiz_type == "multiple_choice":
        format_instruction = """
        Return a JSON array of objects. Each object must have:
        - "question_text": str
        - "options": [str, str, str, str]
        - "correct_answer": str (must be one of the options)
        """
    else:
        # Default to open ended or simple Q&A logical fallback if mixed, but requirement said MCQ default
        format_instruction = """
        Return a JSON array of objects. Each object must have:
        - "question_text": str
        - "options": [] (empty list)
        - "correct_answer": str
        """

    # Truncate to avoid context limit issues
    truncated_context = context[:15000]
    
    prompt = f"""You are a quiz generator. Generate {num_questions} {quiz_type} questions based on the following document.

{format_instruction}

CRITICAL: You must return ONLY a valid JSON array. Start with [ and end with ]. Do NOT include markdown code blocks, explanations, or any other text. Only the JSON array.

Example format:
[
  {{"question_text": "What is...?", "options": ["A", "B", "C", "D"], "correct_answer": "A"}},
  {{"question_text": "Which...?", "options": ["X", "Y", "Z"], "correct_answer": "Y"}}
]

Document Content:
{truncated_context}

Now generate the quiz as a JSON array:"""
    
    try:
        # Try with json_object format first (OpenAI), fallback to regular if not supported (Groq)
        try:
            response = await client.chat.completions.create(
                model=AI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                response_format={"type": "json_object"}
            )
        except Exception:
            # Fallback for APIs that don't support response_format (like Groq)
            response = await client.chat.completions.create(
                model=AI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5
            )
        
        if not response.choices or len(response.choices) == 0:
            return []
        
        content = response.choices[0].message.content
        if not content:
            return []
        
        content = content.strip()
        
        # Simple cleanup if the model adds markdown
        if content.startswith("```json"):
            content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
        elif content.startswith("```"):
            # Handle generic code blocks
            content = content.split("```", 2)[-1]
            if content.endswith("```"):
                content = content[:-3]
        
        # Check if wrapped in a key or list
        data = json.loads(content)
        if isinstance(data, list):
            return data
        elif "questions" in data:
            return data["questions"]
        else:
            # Attempt to find list in values?
            for v in data.values():
                if isinstance(v, list):
                    return v
            return []
    except json.JSONDecodeError:
        return []
    except Exception as e:
        # Log error but return empty list to prevent breaking the app
        print(f"Error generating quiz: {str(e)}")
        return []


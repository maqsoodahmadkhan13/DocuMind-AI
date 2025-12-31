import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import asyncio

load_dotenv()

# MongoDB connection configuration
# Default connects to Docker MongoDB container
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "documind_db")

# Initialize MongoDB client
# Connect to MongoDB in Docker container
client = AsyncIOMotorClient(
    MONGO_URI,
    serverSelectionTimeoutMS=5000,  # 5 second timeout
    connectTimeoutMS=5000
)
db = client[DB_NAME]

# Collections
users_collection = db["users"]
documents_collection = db["documents"]
chat_history_collection = db["chat_history"]
quizzes_collection = db["quizzes"]
summaries_collection = db["summaries"]

async def get_database():
    return db

async def test_connection():
    """Test MongoDB connection"""
    try:
        # Ping the database to check connection
        await client.admin.command('ping')
        print(f"[OK] Successfully connected to MongoDB at {MONGO_URI}")
        print(f"[OK] Using database: {DB_NAME}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to connect to MongoDB: {str(e)}")
        print(f"        Make sure MongoDB is running in Docker: docker-compose up -d")
        return False

# Test connection on module import (optional - can be removed if not needed)
# Uncomment the following lines to test connection on startup:
# import asyncio
# if __name__ == "__main__":
#     asyncio.run(test_connection())

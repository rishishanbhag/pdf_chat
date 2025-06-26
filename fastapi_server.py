from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware
import os
import requests
import logging
import pandas as pd
from chatbot_core import chatbot

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for development; restrict in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ChatRequest(BaseModel):
    pdf_urls: List[str]
    question: str
    conversation_id: Optional[str] = "default"

class AnswerRequest(BaseModel):
    question: str
    answer: str
    conversation_id: Optional[str] = "default"
    timestamp: Optional[str] = None

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    logger.info(f"Chat request received: {request.question}")
    try:
        # Use your existing RAG system!
        response = chatbot.ask_question(request.question, request.conversation_id)

        # Forward answer to /answers
        try:
            requests.post(
                "http://localhost:8000/answers",
                json={
                    "conversation_id": request.conversation_id,
                    "question": request.question,
                    "answer": response["answer"]
                }
            )
        except Exception as e:
            logger.warning(f"Could not forward to /answers: {e}")

        return {"answer": response["answer"]}
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        return {"error": str(e)}

# Store answers in memory 
stored_answers = []

# Modify your existing receive_answer function:
@app.post("/answer")
async def receive_answer(request: AnswerRequest):
    """Receive and process answers from Streamlit"""
    try:
        logger.info(f"Received answer for question: '{request.question[:50]}...'")
        logger.info(f"Answer length: {len(request.answer)} characters")
        logger.info(f"Conversation ID: {request.conversation_id}")
        
        # Store the answer for browser viewing
        answer_data = {
            "question": request.question,
            "answer": request.answer,
            "conversation_id": request.conversation_id,
            "timestamp": request.timestamp,
            "received_at": str(pd.Timestamp.now()) if 'pd' in globals() else "now"
        }
        stored_answers.append(answer_data)
        
        response_data = {
            "status": "success",
            "message": "Answer received and stored successfully",
            "question": request.question,
            "answer_length": len(request.answer),
            "conversation_id": request.conversation_id,
            "timestamp": request.timestamp,
            "total_stored": len(stored_answers)
        }
        
        return response_data
        
    except Exception as e:
        logger.error(f"Error processing answer: {e}")
        return {"status": "error", "message": str(e)}

# Add new endpoints for browser viewing:
@app.get("/answers/all")
async def get_all_answers():
    """View all stored answers in browser"""
    return {
        "total_answers": len(stored_answers),
        "answers": stored_answers
    }

@app.get("/answers/latest")
async def get_latest_answer():
    """View the most recent answer"""
    if stored_answers:
        return {
            "latest_answer": stored_answers[-1],
            "total_answers": len(stored_answers)
        }
    else:
        return {"message": "No answers stored yet"}

@app.get("/")
async def root():
    """Root endpoint with navigation"""
    return {
        "message": "PDF Chatbot API",
        "endpoints": {
            "chat": "POST /chat - Process PDFs and ask questions",
            "answer": "POST /answer - Receive answers from Streamlit",
            "view_all_answers": "GET /answers/all - View all stored answers",
            "view_latest": "GET /answers/latest - View latest answer"
        }
    }

# The Connection:
# /answer (POST) → Writes to stored_answers
# /answers/latest (GET) → Reads from stored_answers
# /answers/all (GET) → Reads from stored_answers

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
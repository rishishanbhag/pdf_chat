from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import uvicorn
import logging
from chatbot_core import chatbot

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="PDF Chatbot API", description="API for PDF-powered chatbot", version="1.0.0")

# Pydantic models for request/response
class ChatRequest(BaseModel):
    question: str
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    status: str
    conversation_id: Optional[str] = None

class ProcessDocumentsRequest(BaseModel):
    pdf_paths: list[str]  # List of PDF file paths

@app.on_event("startup")
async def startup_event():
    """Initialize the conversation chain on startup"""
    if chatbot.initialize_from_saved_vectorstore():
        logger.info("Conversation chain initialized with existing vectorstore")
    else:
        logger.info("No vectorstore found. Please process documents first.")

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "PDF Chatbot API is running", "status": "healthy"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    status = chatbot.get_status()
    return {
        "status": "healthy",
        **status
    }

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Main chat endpoint for Chatwoot integration"""
    try:
        result = chatbot.ask_question(request.question, request.conversation_id)
        
        return ChatResponse(
            answer=result['answer'],
            status=result['status'],
            conversation_id=result['conversation_id']
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/process-documents")
async def process_documents(request: ProcessDocumentsRequest):
    """Process PDF documents and create vectorstore"""
    try:
        if not request.pdf_paths:
            raise HTTPException(status_code=400, detail="No PDF paths provided")
        
        logger.info(f"Processing {len(request.pdf_paths)} PDF files")
        result = chatbot.process_documents_from_paths(request.pdf_paths)
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing documents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process documents: {str(e)}")

@app.post("/reload-vectorstore")
async def reload_vectorstore():
    """Reload vectorstore from file"""
    try:
        if chatbot.initialize_from_saved_vectorstore():
            logger.info("Vectorstore reloaded successfully")
            return {"status": "success", "message": "Vectorstore reloaded"}
        else:
            raise HTTPException(status_code=404, detail="No vectorstore file found")
        
    except Exception as e:
        logger.error(f"Error reloading vectorstore: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reload vectorstore: {str(e)}")

# Chatwoot webhook endpoint (optional - for direct webhook integration)
@app.post("/chatwoot-webhook")
async def chatwoot_webhook(webhook_data: dict):
    """Handle Chatwoot webhook events"""
    try:
        logger.info(f"Received Chatwoot webhook: {webhook_data}")
        
        # Check if it's a message created event
        if webhook_data.get('event') == 'message_created':
            message_data = webhook_data.get('message', {})
            conversation_data = webhook_data.get('conversation', {})
            
            # Skip if message is from bot or agent
            if message_data.get('message_type') != 'incoming':
                return {"status": "ignored - not incoming"}
            
            # Extract the question
            question = message_data.get('content', '').strip()
            conversation_id = str(conversation_data.get('id'))
            
            if not question:
                return {"status": "ignored - no content"}
            
            # Process the question using chatbot core
            result = chatbot.ask_question(question, conversation_id)
            
            return {
                "status": "success",
                "question": question,
                "answer": result['answer'],
                "conversation_id": conversation_id
            }
        
        return {"status": "ignored - not message_created"}
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("fastapi_server:app", host="0.0.0.0", port=8000, reload=True)
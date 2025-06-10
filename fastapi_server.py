from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
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

# New Pydantic models for Chatwoot webhook
class ContactInfo(BaseModel):
    email: str = Field(..., description="Contact email address")

class ChatwootWebhookRequest(BaseModel):
    message: str = Field(..., description="The message content from the user")
    conversation_id: str = Field(..., description="Chatwoot conversation ID")
    contact: ContactInfo = Field(..., description="Contact information")

class ChatwootWebhookResponse(BaseModel):
    response: str
    conversation_id: str
    status: int

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

# Updated Chatwoot webhook endpoint with proper validation
@app.post("/chatwoot-webhook", response_model=ChatwootWebhookResponse)
async def chatwoot_webhook_validated(webhook_data: ChatwootWebhookRequest):
    """
    Handle Chatwoot webhook with proper validation
    Accepts structured data with message, conversation_id, and contact info
    """
    try:
        logger.info(f"Processing validated webhook for conversation {webhook_data.conversation_id}")
        logger.info(f"Message: '{webhook_data.message}' from {webhook_data.contact.email}")
        
        # Check if vectorstore is available
        if chatbot.vectorstore is None:
            if not chatbot.initialize_from_saved_vectorstore():
                logger.error("No documents processed yet")
                raise HTTPException(
                    status_code=503, 
                    detail="Knowledge base not available. Please process documents first."
                )
        
        # Process the message using the chatbot (equivalent to query_knowledge_base)
        result = chatbot.ask_question(webhook_data.message, webhook_data.conversation_id)
        answer = result['answer']
        
        logger.info(f"Generated answer for {webhook_data.contact.email}: {answer[:100]}...")
        
        # Optional: Send reply back to Chatwoot automatically
        try:
            from fix_chatwoot import send_reply_to_chatwoot
            send_success = send_reply_to_chatwoot(webhook_data.conversation_id, answer)
            if send_success:
                logger.info("Reply automatically sent to Chatwoot")
        except Exception as e:
            logger.warning(f"Could not auto-send to Chatwoot: {e}")
        
        return ChatwootWebhookResponse(
            response=answer,
            conversation_id=webhook_data.conversation_id,
            status=200
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/debug-conversation/{conversation_id}")
async def debug_conversation(conversation_id: str):
    """Debug endpoint to test sending a reply to a conversation"""
    try:
        from fix_chatwoot import send_reply_to_chatwoot
        success = send_reply_to_chatwoot(conversation_id, "Debug message from the server!")
        
        if success:
            return {"status": "success", "message": "Debug reply sent"}
        else:
            return {"status": "error", "message": "Failed to send debug reply"}
            
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    uvicorn.run("fastapi_server:app", host="0.0.0.0", port=8000, reload=True)
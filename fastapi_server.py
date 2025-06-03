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
        logger.info(f"Received Chatwoot webhook")
        
        # DEBUGGING: Dump each webhook to a file
        import json
        import os
        os.makedirs("webhook_logs", exist_ok=True)
        with open(f"webhook_logs/webhook_{len(os.listdir('webhook_logs'))}.json", "w") as f:
            f.write(json.dumps(webhook_data, indent=2))
        
        # Continue with existing code
        # Skip non-message events
        if 'event' in webhook_data and webhook_data['event'] not in ['message_created', 'conversation_updated']:
            logger.info(f"Skipping event type: {webhook_data['event']}")
            return {"status": "ignored"}
        
        # IMPORTANT: Only process incoming messages from customers
        message_content = None
        conversation_id = None
        
        # Case 1: Direct message_created event
        if webhook_data.get('event') == 'message_created' and 'message' in webhook_data:
            message = webhook_data['message']
            if message.get('message_type') == 'incoming' or message.get('message_type') == 1:
                message_content = message.get('content')
                conversation_id = webhook_data.get('conversation', {}).get('id')
                logger.info(f"Processing message_created: '{message_content}'")
                
        # Case 2: From messages array in conversation_updated
        elif 'messages' in webhook_data and webhook_data['messages']:
            # Get conversation ID
            conversation_id = webhook_data.get('id')
            
            # Find incoming message
            for message in webhook_data['messages']:
                msg_type = message.get('message_type')
                if msg_type == 'incoming' or msg_type == 1:
                    message_content = message.get('content')
                    logger.info(f"Processing from messages array: '{message_content}'")
                    break
        
        # Exit if no message to process
        if not message_content or not conversation_id:
            logger.info("No actionable message found")
            return {"status": "ignored - no actionable message"}
        
        # Process with chatbot
        logger.info(f"Processing question: '{message_content}' for conversation: {conversation_id}")
        
        # Check if vectorstore is available
        if chatbot.vectorstore is None:
            if not chatbot.initialize_from_saved_vectorstore():
                logger.error("No documents processed yet")
                return {"status": "error", "message": "No documents processed"}
        
        # Get answer from chatbot
        result = chatbot.ask_question(message_content, conversation_id)
        answer = result['answer']
        
        logger.info(f"Generated answer: {answer[:100]}...")
        
        # Send reply back to Chatwoot
        from fix_chatwoot import send_reply_to_chatwoot
        success = send_reply_to_chatwoot(conversation_id, answer)
        
        if success:
            logger.info("Reply sent successfully!")
            return {"status": "success", "message": "Reply sent"}
        else:
            logger.error("Failed to send reply")
            return {"status": "error", "message": "Failed to send reply"}
            
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {"status": "error", "message": str(e)}

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
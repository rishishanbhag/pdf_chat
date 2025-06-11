from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain.embeddings import HuggingFaceBgeEmbeddings
from langchain.chains import RetrievalQA
from langchain_community.llms import HuggingFaceEndpoint
import os
import requests
import logging
import tempfile
from PyPDF2 import PdfReader
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd

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

# Embedding model
model_name = "BAAI/bge-base-en-v1.5"
encode_kwargs = {'normalize_embeddings': True}
embedding_model = HuggingFaceBgeEmbeddings(model_name=model_name, encode_kwargs=encode_kwargs)

# RAG pipeline
def create_rag_chain_from_pdfs(pdf_urls: List[str]) -> RetrievalQA:
    all_text = ""
    for url in pdf_urls:
        try:
            response = requests.get(url)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
                tmp_pdf.write(response.content)
                tmp_pdf_path = tmp_pdf.name

            reader = PdfReader(tmp_pdf_path)
            all_text += "\n".join(page.extract_text() for page in reader.pages if page.extract_text())

        except Exception as e:
            logger.error(f"Error processing PDF at {url}: {e}")

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    texts = text_splitter.split_text(all_text)
    vectordb = Chroma.from_texts(texts, embedding=embedding_model)
    retriever = vectordb.as_retriever()
    llm = HuggingFaceEndpoint(
        repo_id="mistralai/Mixtral-8x7B-Instruct-v0.1",
        temperature=0.2,
        max_new_tokens=500,
        huggingfacehub_api_token=os.environ["HUGGINGFACEHUB_API_TOKEN"]
    )
    return RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever)

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    logger.info(f"Chat request received: {request.question}")
    try:
        qa_chain = create_rag_chain_from_pdfs(request.pdf_urls)
        result = qa_chain.run(request.question)

        # Forward answer to /answers
        try:
            requests.post(
                "http://localhost:8000/answers",
                json={
                    "conversation_id": request.conversation_id,
                    "question": request.question,
                    "answer": result
                }
            )
        except Exception as e:
            logger.warning(f"Could not forward to /answers: {e}")

        return {"answer": result}
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        return {"error": str(e)}

# Store answers in memory (for demo purposes)
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

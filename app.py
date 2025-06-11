# streamlit_app.py
import streamlit as st
from chatbot_core import chatbot
import requests
import logging
import datetime

st.set_page_config(page_title="PDF Chatbot", page_icon="📄")
st.title("PDF Chatbot 🤖")

# Initialize session state
if 'conversation_initialized' not in st.session_state:
    st.session_state.conversation_initialized = False

def handle_user_question(user_question):
    if st.session_state.conversation_initialized:
        try:
            # Replace the chatbot.ask_question() call with FastAPI request
            if user_question:
                # Convert uploaded files to URLs (you'd need to host them somewhere)
                # OR modify FastAPI to accept file uploads
                
                response = requests.post("http://localhost:8000/chat", json={
                    "pdf_urls": ["your-pdf-urls"],  # You'd need to handle this
                    "question": user_question,
                    "conversation_id": "streamlit_session"
                })
                
                if response.status_code == 200:
                    answer = response.json().get("answer")
                    
                    # Check if answer is None or empty
                    if answer and answer.strip():
                        st.write("**Answer:**", answer)
                    else:
                        st.error("Received empty answer. Please try rephrasing your question.")
                else:
                    st.error("Error getting response from server")

        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.warning("Please upload and process documents first.")

def main():
    if "conversation_initialized" not in st.session_state:
        st.session_state.conversation_initialized = False
        if chatbot.initialize_from_saved_vectorstore():
            st.session_state.conversation_initialized = True

    st.header("Chat with your documents")

    # Check if system is ready
    status = chatbot.get_status()
    if not status["conversation_chain_initialized"]:
        st.info("👆 Please upload and process documents first")
    else:
        st.success("✅ Ready to answer questions!")

    # Chat input
    user_question = st.text_input("Ask a question about your documents:")

    if user_question:
        if not status["conversation_chain_initialized"]:
            st.error("Please process documents first before asking questions.")
        else:
            with st.spinner("Thinking..."):
                try:
                    # Get response from local chatbot
                    response = chatbot.ask_question(user_question)
                    answer = response.get("answer")
                    
                    if answer and answer.strip():
                        st.write("**Answer:**", answer)
                        
                        # Send answer to FastAPI server
                        try:
                            api_payload = {
                                "question": user_question,
                                "answer": answer,
                                "conversation_id": f"streamlit_{st.session_state.get('session_id', 'unknown')}",
                                "timestamp": datetime.datetime.now().isoformat()
                            }
                            
                            api_response = requests.post(
                                "http://localhost:8000/answer", 
                                json=api_payload,
                                timeout=10
                            )
                            
                            if api_response.status_code == 200:
                                result = api_response.json()
                                st.success(f"✅ Answer sent to API server! Total stored: {result.get('total_stored', '?')}")
                            else:
                                st.warning(f"⚠️ API call failed: {api_response.status_code}")
                                
                        except Exception as e:
                            st.warning(f"⚠️ Could not reach API server: {str(e)}")
                        
                    else:
                        st.error("Received empty answer. Please try a different question.")
                        
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                
    with st.sidebar:
        st.subheader("Upload Documents")
        pdf_docs = st.file_uploader(
            "Upload PDF files", 
            accept_multiple_files=True, 
            type="pdf"
        )
        
        if st.button("Process Documents"):
            if pdf_docs:
                with st.spinner("Processing documents..."):
                    try:
                        result = chatbot.process_documents(pdf_docs)
                        st.success(f"✅ Processed {result['chunks_created']} chunks from {len(pdf_docs)} documents")
                        st.session_state.conversation_initialized = True
                        
                        try:
                            requests.post('http://localhost:8000/reload-vectorstore')
                        except:
                            pass

                        # Show status
                        status = chatbot.get_status()
                        st.write("System Status:", status)
                        
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
            else:
                st.warning("Please upload PDF files first")

        st.subheader("System Status")
        status = chatbot.get_status()
        for key, value in status.items():
            icon = "✅" if value else "❌"
            st.write(f"{icon} {key}: {value}")

if __name__ == "__main__":
    main()

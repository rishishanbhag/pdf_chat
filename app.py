import streamlit as st
import requests
from chatbot_core import chatbot

st.set_page_config(page_title="Chat with PDFs", page_icon=":books:")

def handle_user_question(user_question):
    """Handle user question using core chatbot logic"""
    if st.session_state.conversation_initialized:
        try:
            result = chatbot.ask_question(user_question)
            st.write("**Answer:**", result['answer'])
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.warning("Please upload and process documents first.")

def main():
    # Initialize session state
    if "conversation_initialized" not in st.session_state:
        st.session_state.conversation_initialized = False
        # Try to load existing vectorstore
        if chatbot.initialize_from_saved_vectorstore():
            st.session_state.conversation_initialized = True

    st.header("Chat with your PDFs")

    user_question = st.text_input("Ask a question about your documents:")
    if user_question:
        handle_user_question(user_question)

    with st.sidebar:
        st.subheader("Your documents")
        pdf_docs = st.file_uploader("Upload your PDF files", type=["pdf"], accept_multiple_files=True)
        
        if st.button("Process Documents"):
            if pdf_docs:
                with st.spinner("Processing..."):
                    try:
                        result = chatbot.process_documents(pdf_docs)
                        st.session_state.conversation_initialized = True
                        
                        # Notify FastAPI server to reload
                        try:
                            requests.post('http://localhost:8000/reload-vectorstore')
                        except:
                            pass  # FastAPI server might not be running
                        
                        st.success(f"Documents processed! Created {result['chunks_created']} chunks.")
                    except Exception as e:
                        st.error(f"Error processing documents: {e}")
            else:
                st.error("Please upload at least one PDF file.")
        
        # Status information
        st.subheader("Status")
        status = chatbot.get_status()
        st.json(status)
        
        # API test button
        st.subheader("API Testing")
        if st.button("Test FastAPI Endpoint"):
            try:
                response = requests.post("http://localhost:8000/chat", 
                    json={"question": "What is this document about?", "conversation_id": "123"}
                )
                st.json(response.json())
            except Exception as e:
                st.error(f"API test failed: {e}")

if __name__ == "__main__":
    main()

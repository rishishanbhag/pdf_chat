import streamlit as st
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
import os
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI


load_dotenv()

st.set_page_config(page_title="Chat with PDFs", page_icon=":books:")

# Configure Google Generative AI
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

def get_pdf_chunk(raw_text):
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    return text_splitter.split_text(raw_text)

def get_vectorstore(text_chunk):
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    return FAISS.from_texts(text_chunk, embedding=embeddings)

def get_convo(vectorstore):
    # Using Gemini model through LangChain integration
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        temperature=0.2,
        google_api_key=GOOGLE_API_KEY,
        convert_system_message_to_human=True
    )

    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    return ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(),
        memory=memory
    )

def handle_user_question(user_question):
    if st.session_state.convo is not None:
        response = st.session_state.convo({"question": user_question})
        st.write("**Answer:**", response['answer'])
    else:
        st.warning("Please upload and process documents first.")

def main():
    if not GOOGLE_API_KEY:
        st.error("GOOGLE_API_KEY not found in environment variables. Please add it to your .env file.")
        return

    if "convo" not in st.session_state:
        st.session_state.convo = None

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
                    raw_text = get_pdf_text(pdf_docs)
                    text_chunks = get_pdf_chunk(raw_text)
                    vectorstore = get_vectorstore(text_chunks)
                    st.session_state.convo = get_convo(vectorstore)
                    st.success("Documents processed! You can now ask questions.")
            else:
                st.error("Please upload at least one PDF file.")

if __name__ == "__main__":
    main()

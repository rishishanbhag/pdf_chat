import streamlit as st
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain_community.llms import HuggingFaceHub
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain



def get_pdf_text(pdf_docs): 
    text= ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text


def get_pdf_chunk(raw_text):
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,  
        chunk_overlap=200,   #prevents loss of context between chunks
        length_function=len
    )
    chunk = text_splitter.split_text(raw_text)
    return chunk


def get_vectorstore(text_chunk):
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectorstore = FAISS.from_texts(text_chunk, embedding=embeddings)
    return vectorstore

def get_convo(vectorstore):
    llm = HuggingFaceHub(
        repo_id="google/flan-t5-large", 
        model_kwargs={"temperature": 0.2}
    )
    memory= ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    convo_chain= ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(),
        memory=memory
    )
    return convo_chain


def main():
    load_dotenv()
    st.set_page_config(page_title="chat with pdfs", page_icon=":books:")

    if "conversation" not in st.session_state:
        st.session_state.conversation = None   #streamlit often reloads the page, so we need to store the conversation in session state

    st.header("Chat with your PDFs")
    st.text_input("Enter your question here:")


    with st.sidebar:
        st.subheader("your documents")
        st.text_input("Enter your documents here:")
        pdf_docs=st.file_uploader("Upload your PDF files", type=["pdf"], accept_multiple_files=True)
        if st.button("Process Documents"):
            raw_text = get_pdf_text(pdf_docs)  #all the text from pdfs is saved here
            # st.write(raw_text)

            text_chunk=get_pdf_chunk(raw_text)  #function to create chunks of the text
    
            vectorstore=get_vectorstore(text_chunk)  #function to create vectorstore
            # st.write(vectorstore)  #vectorstore is created here

            st.session_state.convo=get_convo(vectorstore)

    


if __name__== "__main__":
    main()
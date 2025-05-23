import streamlit as st
from dotenv import load_dotenv


def main():
    load_dotenv()
    st.set_page_config(page_title="chat with pdfs", page_icon=":books:")

    st.header("Chat with your PDFs")
    st.text_input("Enter your question here:")

    with st.sidebar:
        st.subheader("your documents")
        st.text_input("Enter your documents here:")
        st.file_uploader("Upload your PDF files", type=["pdf"], accept_multiple_files=True)
        st.button("Process Documents", key="process_docs")


if __name__== "__main__":
    main()
import os
import streamlit as st
import openai
import config
from langchain_openai import OpenAIEmbeddings
from chatbot import ChatBot
from processing import DocumentProcessor
from vectorstore import get_vectorstore, add_chunks_to_vectorstore
from streamlit_local_storage import LocalStorage
    
st.set_page_config(
    page_title="Chat with PDF",
    initial_sidebar_state="expanded"
)

st.title("Chat with PDF rag")

localS = LocalStorage()

if "openai_api_key" not in st.session_state:
    st.session_state.openai_api_key = localS.getItem("openai_api_key")

openai_api_key = st.sidebar.text_input("OpenAI API Key", type="password", value=st.session_state.openai_api_key or "")

if openai_api_key:
    if openai_api_key != st.session_state.openai_api_key:
        localS.setItem("openai_api_key", openai_api_key)
        st.session_state.openai_api_key = openai_api_key
    
    if not openai_api_key.startswith("sk-"):
        st.sidebar.error("Invalid API key format. API key should start with 'sk-'")
        st.stop()
    
    openai.api_key = openai_api_key
else:
    st.warning("Please enter your OpenAI API key to proceed.")
    st.stop()

uploaded_files = st.sidebar.file_uploader(
    "Choose a PDF file",
    type=['pdf'],
    help="Upload a PDF document to chat with",
    accept_multiple_files=True,
)

if "chatbot" not in st.session_state:
    st.session_state.chatbot = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if uploaded_files:
    with st.spinner("Processing documents..."):
        if not os.path.exists(config.DATA_DIR):
            os.makedirs(config.DATA_DIR)

        file_paths = []
        for uploaded_file in uploaded_files:
            file_path = os.path.join(config.DATA_DIR, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            file_paths.append(file_path)

        embed_model = OpenAIEmbeddings(
            model=config.EMBEDDING_MODEL,
            openai_api_key=openai_api_key
        )
        vectorstore = get_vectorstore(embed_model)
        
        processed_files = [metadata['source'] for metadata in vectorstore.get()['metadatas']]
        
        doc_processor = DocumentProcessor(config.DATA_DIR, config.NO_NEEDED_PAGES)
        
        all_files = [f.name for f in uploaded_files]
        
        new_files = [f for f in all_files if f not in processed_files]
        
        if new_files:
            chunks = doc_processor.process_new_files(new_files)
            add_chunks_to_vectorstore(vectorstore, chunks)
            st.sidebar.success(f"Successfully processed {len(new_files)} new document(s).")
        else:
            st.sidebar.info("All documents are already processed.")

    st.session_state.chatbot = ChatBot(vectorstore=vectorstore, openai_api_key=openai_api_key)

chat_container = st.container()

with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

if prompt := st.chat_input("Ask something about your document..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)

    if st.session_state.chatbot:
        with st.spinner("Thinking..."):
            response = st.session_state.chatbot.chat(prompt)
            with st.chat_message("assistant"):
                st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
    else:
        st.warning("Please upload and process documents before asking questions.")

import os
import sys
import asyncio
import streamlit as st
import openai
import config
from langchain_openai import OpenAIEmbeddings
from chatbot import ChatBot
from processing import DocumentProcessor
from vectorstore import get_vectorstore, VectorStoreManager
from session_manager import get_session_manager
from streamlit_local_storage import LocalStorage

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(page_title="Chat with PDF", initial_sidebar_state="expanded")

st.title("Chat with PDF rag")

localS = LocalStorage()
session_manager = get_session_manager()

if "session_id" not in st.session_state:
    stored_session_id = localS.getItem("session_id")
    if stored_session_id and session_manager.is_valid_session(stored_session_id):
        st.session_state.session_id = stored_session_id
    else:
        new_session_id = session_manager.generate_session_id()
        removed_session = session_manager.create_session(new_session_id)
        if removed_session:
            embed_model = OpenAIEmbeddings(model=config.EMBEDDING_MODEL)
            vectorstore = get_vectorstore(embed_model)
            vector_manager = VectorStoreManager(vectorstore)
            vector_manager.remove_documents_by_session(removed_session)
        st.session_state.session_id = new_session_id
        localS.setItem("session_id", new_session_id)

if "openai_api_key" not in st.session_state:
    st.session_state.openai_api_key = localS.getItem("openai_api_key")

openai_api_key = st.sidebar.text_input(
    "OpenAI API Key", type="password", value=st.session_state.openai_api_key or ""
)

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

current_session_files = session_manager.get_session_files(st.session_state.session_id)

if current_session_files:
    st.sidebar.subheader("Your Files")
    for file_name in current_session_files:
        col1, col2 = st.sidebar.columns([3, 1])
        with col1:
            st.text(file_name)
        with col2:
            if st.button("🗑️", key=f"delete_{file_name}"):
                embed_model = OpenAIEmbeddings(
                    model=config.EMBEDDING_MODEL, openai_api_key=openai_api_key
                )
                vectorstore = get_vectorstore(embed_model)
                vector_manager = VectorStoreManager(vectorstore)
                vector_manager.remove_documents_by_session_and_file(
                    st.session_state.session_id, file_name
                )
                session_manager.remove_file_from_session(
                    st.session_state.session_id, file_name
                )
                st.rerun()

can_upload = session_manager.can_add_file(st.session_state.session_id)
max_files = config.MAX_FILES_PER_SESSION

if can_upload:
    uploaded_files = st.sidebar.file_uploader(
        f"Choose a PDF file ({len(current_session_files)}/{max_files})",
        type=["pdf"],
        help="Upload a PDF document to chat with",
        accept_multiple_files=True,
    )
else:
    st.sidebar.warning(
        f"Maximum {max_files} files per session reached. Delete a file to upload new ones."
    )
    uploaded_files = None

if "chatbot" not in st.session_state:
    st.session_state.chatbot = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if uploaded_files:
    files_to_process = []
    for uploaded_file in uploaded_files:
        if session_manager.can_add_file(st.session_state.session_id):
            if session_manager.add_file_to_session(
                st.session_state.session_id, uploaded_file.name
            ):
                files_to_process.append(uploaded_file)
        else:
            st.sidebar.error(
                f"Cannot upload {uploaded_file.name}: maximum files limit reached"
            )

    if files_to_process:
        with st.spinner("Processing documents..."):
            if not os.path.exists(config.DATA_DIR):
                os.makedirs(config.DATA_DIR)

            file_paths = []
            for uploaded_file in files_to_process:
                file_path = os.path.join(config.DATA_DIR, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                file_paths.append(file_path)

            embed_model = OpenAIEmbeddings(
                model=config.EMBEDDING_MODEL, openai_api_key=openai_api_key
            )
            vectorstore = get_vectorstore(embed_model)
            vector_manager = VectorStoreManager(vectorstore)

            processed_files = vector_manager.get_processed_files_for_session(
                st.session_state.session_id
            )

            doc_processor = DocumentProcessor(config.DATA_DIR)

            all_files = [f.name for f in files_to_process]

            new_files = [f for f in all_files if f not in processed_files]

            if new_files:
                chunks = doc_processor.process_new_files(
                    new_files, st.session_state.session_id
                )
                vector_manager.add_chunks(chunks)
                doc_processor.delete_processed_files(new_files)
                st.sidebar.success(
                    f"Successfully processed {len(new_files)} new document(s)."
                )
            else:
                st.sidebar.info("All documents are already processed.")

    if current_session_files or files_to_process:
        embed_model = OpenAIEmbeddings(
            model=config.EMBEDDING_MODEL, openai_api_key=openai_api_key
        )
        vectorstore = get_vectorstore(embed_model)
        st.session_state.chatbot = ChatBot(
            vectorstore=vectorstore,
            openai_api_key=openai_api_key,
            session_id=st.session_state.session_id,
        )

elif current_session_files:
    embed_model = OpenAIEmbeddings(
        model=config.EMBEDDING_MODEL, openai_api_key=openai_api_key
    )
    vectorstore = get_vectorstore(embed_model)
    st.session_state.chatbot = ChatBot(
        vectorstore=vectorstore,
        openai_api_key=openai_api_key,
        session_id=st.session_state.session_id,
    )

chat_container = st.container()

with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

if prompt := st.chat_input("Ask something about your document..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    if st.session_state.chatbot:
        async def response_generator():
            async for text in st.session_state.chatbot.chat_stream(prompt):
                yield text

        with st.chat_message("assistant"):
            response = st.write_stream(response_generator())
        st.session_state.messages.append({"role": "assistant", "content": response})
    else:
        st.warning("Please upload and process documents before asking questions.")

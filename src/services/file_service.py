import os
import streamlit as st
from langchain_openai import OpenAIEmbeddings
from processing import DocumentProcessor
from vectorstore import get_vectorstore, VectorStoreManager
from chatbot import ChatBot
import config


class FileService:
    def __init__(self, session_service):
        self.session_service = session_service

    def process_uploaded_files(self, uploaded_files, openai_api_key):
        if not uploaded_files:
            return None

        files_to_process = []
        for uploaded_file in uploaded_files:
            if self.session_service.can_add_file():
                if self.session_service.add_file_to_session(uploaded_file.name):
                    files_to_process.append(uploaded_file)
            else:
                st.sidebar.error(
                    f"Cannot upload {uploaded_file.name}: maximum files limit reached"
                )

        if files_to_process:
            with st.spinner("Processing documents..."):
                self._save_uploaded_files(files_to_process)
                self._process_documents(files_to_process, openai_api_key)
            
        return len(files_to_process) > 0

    def create_chatbot(self, openai_api_key):
        current_session_files = self.session_service.get_session_files()
        
        if current_session_files:
            embed_model = OpenAIEmbeddings(
                model=config.EMBEDDING_MODEL, openai_api_key=openai_api_key
            )
            vectorstore = get_vectorstore(embed_model)
            return ChatBot(
                vectorstore=vectorstore,
                openai_api_key=openai_api_key,
                session_id=self.session_service.get_current_session_id(),
            )
        return None

    def _save_uploaded_files(self, uploaded_files):
        if not os.path.exists(config.DATA_DIR):
            os.makedirs(config.DATA_DIR)

        file_paths = []
        for uploaded_file in uploaded_files:
            file_path = os.path.join(config.DATA_DIR, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            file_paths.append(file_path)
        return file_paths

    def _process_documents(self, uploaded_files, openai_api_key):
        embed_model = OpenAIEmbeddings(
            model=config.EMBEDDING_MODEL, openai_api_key=openai_api_key
        )
        vectorstore = get_vectorstore(embed_model)
        vector_manager = VectorStoreManager(vectorstore)

        processed_files = vector_manager.get_processed_files_for_session(
            self.session_service.get_current_session_id()
        )

        doc_processor = DocumentProcessor(config.DATA_DIR)
        all_files = [f.name for f in uploaded_files]
        new_files = [f for f in all_files if f not in processed_files]

        if new_files:
            chunks = doc_processor.process_new_files(
                new_files, self.session_service.get_current_session_id()
            )
            vector_manager.add_chunks(chunks)
            doc_processor.delete_processed_files(new_files)
            st.sidebar.success(
                f"Successfully processed {len(new_files)} new document(s)."
            )
        else:
            st.sidebar.info("All documents are already processed.")
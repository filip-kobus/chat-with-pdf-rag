import streamlit as st
from streamlit_local_storage import LocalStorage
from session_manager import get_session_manager
from langchain_openai import OpenAIEmbeddings
from vectorstore import get_vectorstore, VectorStoreManager
import config


class SessionService:
    def __init__(self):
        self.local_storage = LocalStorage()
        self.session_manager = get_session_manager()

    def initialize_session(self):
        if "session_id" not in st.session_state:
            stored_session_id = self.local_storage.getItem("session_id")
            if stored_session_id and self.session_manager.is_valid_session(
                stored_session_id
            ):
                st.session_state.session_id = stored_session_id
            else:
                new_session_id = self.session_manager.generate_session_id()
                removed_session = self.session_manager.create_session(new_session_id)
                if removed_session:
                    embed_model = OpenAIEmbeddings(model=config.EMBEDDING_MODEL)
                    vectorstore = get_vectorstore(embed_model)
                    vector_manager = VectorStoreManager(vectorstore)
                    vector_manager.remove_documents_by_session(removed_session)
                st.session_state.session_id = new_session_id
                self.local_storage.setItem("session_id", new_session_id)

    def get_current_session_id(self):
        return st.session_state.get("session_id")

    def get_session_files(self):
        session_id = self.get_current_session_id()
        if session_id:
            return self.session_manager.get_session_files(session_id)
        return []

    def can_add_file(self):
        session_id = self.get_current_session_id()
        if session_id:
            return self.session_manager.can_add_file(session_id)
        return False

    def add_file_to_session(self, filename):
        session_id = self.get_current_session_id()
        if session_id:
            return self.session_manager.add_file_to_session(session_id, filename)
        return False

    def remove_file_from_session(self, filename):
        session_id = self.get_current_session_id()
        if session_id:
            return self.session_manager.remove_file_from_session(session_id, filename)
        return False

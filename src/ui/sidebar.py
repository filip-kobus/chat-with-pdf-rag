import streamlit as st
from langchain_openai import OpenAIEmbeddings
from vectorstore import get_vectorstore, VectorStoreManager
import config


class SidebarComponent:
    def __init__(self, session_service, file_service):
        self.session_service = session_service
        self.file_service = file_service

    def render_file_list(self, openai_api_key):
        current_session_files = self.session_service.get_session_files()

        if current_session_files:
            st.sidebar.subheader("Your Files")
            for file_name in current_session_files:
                col1, col2 = st.sidebar.columns([3, 1])
                with col1:
                    st.text(file_name)
                with col2:
                    if st.button("🗑️", key=f"delete_{file_name}"):
                        self._handle_file_deletion(file_name, openai_api_key)
                        st.rerun()

    def render_file_uploader(self):
        can_upload = self.session_service.can_add_file()
        current_session_files = self.session_service.get_session_files()
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

        return uploaded_files

    def _handle_file_deletion(self, file_name, openai_api_key):
        embed_model = OpenAIEmbeddings(
            model=config.EMBEDDING_MODEL, openai_api_key=openai_api_key
        )
        vectorstore = get_vectorstore(embed_model)
        vector_manager = VectorStoreManager(vectorstore)
        vector_manager.remove_documents_by_session_and_file(
            self.session_service.get_current_session_id(), file_name
        )
        self.session_service.remove_file_from_session(file_name)

import os
import sys
import streamlit as st
from services.session_service import SessionService
from services.auth_service import AuthService
from services.file_service import FileService
from ui.sidebar import SidebarComponent
from ui.chat import ChatComponent
from utils.state_manager import StateManager

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    st.set_page_config(page_title="Chat with PDF", initial_sidebar_state="expanded")
    st.title("Chat with PDF rag")

    session_service = SessionService()
    auth_service = AuthService()
    state_manager = StateManager()
    file_service = FileService(session_service)
    
    sidebar_component = SidebarComponent(session_service, file_service)
    chat_component = ChatComponent(state_manager)

    session_service.initialize_session()
    auth_service.initialize_api_key()

    openai_api_key = auth_service.render_api_key_input()
    
    if not auth_service.validate_and_set_api_key(openai_api_key):
        st.stop()

    sidebar_component.render_file_list(openai_api_key)
    uploaded_files = sidebar_component.render_file_uploader()

    if uploaded_files:
        files_processed = file_service.process_uploaded_files(uploaded_files, openai_api_key)
        if files_processed:
            chatbot = file_service.create_chatbot(openai_api_key)
            state_manager.set_chatbot(chatbot)

    if not state_manager.get_chatbot():
        chatbot = file_service.create_chatbot(openai_api_key)
        state_manager.set_chatbot(chatbot)

    prompt = chat_component.render_chat_interface()
    
    if prompt:
        chat_component.display_assistant_response(state_manager.get_chatbot(), prompt)

if __name__ == "__main__":
    main()

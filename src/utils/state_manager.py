import streamlit as st


class StateManager:
    def __init__(self):
        self._initialize_state()

    def _initialize_state(self):
        if "chatbot" not in st.session_state:
            st.session_state.chatbot = None
        
        if "messages" not in st.session_state:
            st.session_state.messages = []

    def get_chatbot(self):
        return st.session_state.get("chatbot")

    def set_chatbot(self, chatbot):
        st.session_state.chatbot = chatbot

    def get_messages(self):
        return st.session_state.get("messages", [])

    def add_message(self, message):
        if "messages" not in st.session_state:
            st.session_state.messages = []
        st.session_state.messages.append(message)

    def clear_messages(self):
        st.session_state.messages = []
import streamlit as st
import openai
from streamlit_local_storage import LocalStorage


class AuthService:
    def __init__(self):
        self.local_storage = LocalStorage()

    def initialize_api_key(self):
        if "openai_api_key" not in st.session_state:
            st.session_state.openai_api_key = self.local_storage.getItem("openai_api_key")

    def render_api_key_input(self):
        openai_api_key = st.sidebar.text_input(
            "OpenAI API Key", 
            type="password", 
            value=st.session_state.openai_api_key or ""
        )
        return openai_api_key

    def validate_and_set_api_key(self, api_key):
        if api_key:
            if api_key != st.session_state.openai_api_key:
                self.local_storage.setItem("openai_api_key", api_key)
                st.session_state.openai_api_key = api_key

            if not api_key.startswith("sk-"):
                st.sidebar.error("Invalid API key format. API key should start with 'sk-'")
                return False

            openai.api_key = api_key
            return True
        else:
            st.warning("Please enter your OpenAI API key to proceed.")
            return False

    def get_current_api_key(self):
        return st.session_state.get("openai_api_key")
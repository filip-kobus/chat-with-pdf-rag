import streamlit as st


class ChatComponent:
    def __init__(self, state_manager):
        self.state_manager = state_manager

    def render_chat_interface(self):
        chat_container = st.container()

        with chat_container:
            for message in self.state_manager.get_messages():
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

        return self._handle_chat_input()

    def _handle_chat_input(self):
        if prompt := st.chat_input("Ask something about your document..."):
            with st.chat_message("user"):
                st.markdown(prompt)
            self.state_manager.add_message({"role": "user", "content": prompt})
            return prompt
        return None

    def display_assistant_response(self, chatbot, prompt):
        if chatbot:

            async def response_generator():
                async for text in chatbot.chat_stream(prompt):
                    yield text

            with st.chat_message("assistant"):
                response = st.write_stream(response_generator())
            self.state_manager.add_message({"role": "assistant", "content": response})
        else:
            st.warning("Please upload and process documents before asking questions.")

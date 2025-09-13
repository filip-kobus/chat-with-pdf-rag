import streamlit as st

st.set_page_config(
    page_title="Chat with PDF", 
    initial_sidebar_state="expanded"
)

st.title("Chat with PDF rag")
openai_api_key = st.sidebar.text_input("OpenAI API Key", type="password")

uploaded_file = st.sidebar.file_uploader(
        "Choose a PDF file", 
        type=['pdf'],
        help="Upload a PDF document to chat with",
        accept_multiple_files=True,
    )

    
if "messages" not in st.session_state:
    st.session_state.messages = []


chat_container = st.container()

with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

if prompt := st.chat_input("Ask something about your document..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)

    response = f"Echo: {prompt}"
    with st.chat_message("assistant"):
        st.markdown(response)
    
    st.session_state.messages.append({"role": "assistant", "content": response})

import os
from typing import List, Dict, Any
import config
import pymupdf4llm
from langchain.text_splitter import MarkdownTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
import openai
from pydantic_ai import Agent
from prompts import SYSTEM_MESSAGE, AUGMENTED_PROMPT


class DocumentProcessor:
    def __init__(self, data_dir: str, no_needed_pages: Dict[str, List[int]]):
        self.data_dir = data_dir
        self.no_needed_pages = no_needed_pages

    def _pdf_to_markdown(self, file_path: str, file_name: str) -> str:
        not_needed_pages = self.no_needed_pages.get(file_name, [])
        if not_needed_pages:
            last_page = not_needed_pages[-1]
            pages_to_scrape = [page - 1 for page in range(1, last_page) if page not in not_needed_pages]
        else:
            pages_to_scrape = None
        md_text = pymupdf4llm.to_markdown(file_path, pages=pages_to_scrape)
        return md_text

    def _markdown_to_chunks(self, md_text: str, source_file: str) -> List[Dict[str, Any]]:
        splitter = MarkdownTextSplitter(chunk_size=config.CHUNK_SIZE, chunk_overlap=config.CHUNK_OVERLAP)
        documents = splitter.create_documents([md_text])
        return [{"content": doc.page_content, "metadata": {"source": source_file}} for doc in documents]

    def process_new_files(self, new_files: List[str]) -> List[Dict[str, Any]]:
        all_chunks = []
        for file_name in new_files:
            file_path = os.path.join(self.data_dir, file_name)
            md_text = self._pdf_to_markdown(file_path, file_name)
            file_chunks = self._markdown_to_chunks(md_text, file_name)
            all_chunks.extend(file_chunks)
        return all_chunks


class ChatBot:
    def __init__(self, vectorstore):
        self.vectorstore = vectorstore
        self.agent = Agent(
            config.LLM_MODEL,
            instructions=SYSTEM_MESSAGE["content"],
        )

    def augment_prompt(self, query: str) -> str:
        context = self.vectorstore.similarity_search(query, k=3)
        context = "\n".join([doc.page_content for doc in context])
        return AUGMENTED_PROMPT.format(query=query, context=context)

    def chat(self, query: str) -> None:
        augmented_query = self.augment_prompt(query)

        non_augmented_response = self.agent.run_sync(query)
        augmented_response = self.agent.run_sync(augmented_query)

        print("-" * 20)
        print("Non-augmented answer:")
        print(non_augmented_response.output)
        print("-" * 20)
        print("Augmented answer:")
        print(augmented_response.output)
        print("-" * 20)

def get_vectorstore(embed_model):
    vectorstore = Chroma(
        persist_directory=config.CHROMA_DB_PATH,
        embedding_function=embed_model
    )
    return vectorstore


if __name__ == "__main__":
    openai.api_key = config.OPENAI_API_KEY
    embed_model = OpenAIEmbeddings(model=config.EMBEDDING_MODEL)
    vectorstore = get_vectorstore(embed_model)
    
    processed_files = [metadata['source'] for metadata in vectorstore.get()['metadatas']]
    
    doc_processor = DocumentProcessor(config.DATA_DIR, config.NO_NEEDED_PAGES)
    
    all_files = [f for f in os.listdir(config.DATA_DIR) if f.endswith('.pdf')]
    
    new_files = [f for f in all_files if f not in processed_files]
    
    if new_files:
        print(f"Found {len(new_files)} new files to process: {', '.join(new_files)}")
        chunks = doc_processor.process_new_files(new_files)
        texts = [chunk["content"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]
        vectorstore.add_texts(texts=texts, metadatas=metadatas)
        print(f"Successfully added {len(chunks)} new chunks to the database.")
    else:
        print("No new files to process. Database is up to date.")

    chatbot = ChatBot(vectorstore=vectorstore)

    print("Chatbot is ready. Type your queries below (type 'exit' to quit).")
    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            print("Goodbye!")
            break
        else:
            chatbot.chat(user_input)

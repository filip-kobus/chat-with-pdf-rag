import os
from langchain_openai import OpenAI
from typing import List, Dict, Any
import config

import pymupdf4llm
from langchain.text_splitter import MarkdownTextSplitter

from langchain_chroma import Chroma
from openai import OpenAI 
from langchain_openai import OpenAIEmbeddings
import openai

import pathlib
import random
from tqdm.auto import tqdm
from uuid import uuid4





class DocumentProcessor:
    """A class to handle PDF to markdown conversion and chunking."""

    def __init__(self, data_dir: str, files_names: List[str], no_needed_pages: Dict[str, List[int]]):
        self.data_dir = data_dir
        self.files_names = files_names
        self.no_needed_pages = no_needed_pages
        self.chunks = []

    def _pdf_to_markdown(self, file_path: str, not_needed_pages: List[int]) -> str:
        last_page = not_needed_pages[-1]
        pages_to_scrape = [page - 1 for page in range(1, last_page) if page not in not_needed_pages]
        md_text = pymupdf4llm.to_markdown(file_path, pages=pages_to_scrape)
        return md_text

    def _markdown_to_chunks(self, md_text: str, source_file: str) -> List[Dict[str, Any]]:
        splitter = MarkdownTextSplitter(chunk_size=config.CHUNK_SIZE, chunk_overlap=config.CHUNK_OVERLAP)
        documents = splitter.create_documents([md_text])

        return [{"content": doc.page_content, "metadata": {"source": source_file}} for doc in documents]

    def _generate_chunks(self) -> List[Dict[str, Any]]:
        chunks = []
        for file_name in self.files_names:
            file_path = os.path.join(self.data_dir, file_name)
            not_needed_pages = self.no_needed_pages[file_name]

            md_text = self._pdf_to_markdown(file_path, not_needed_pages)
            file_chunks = self._markdown_to_chunks(md_text, file_name)

            chunks.extend(file_chunks)

        return chunks

    def get_chunks(self) -> List[Dict[str, Any]]:
        if not self.chunks:
            self.chunks = self._generate_chunks()

        return self.chunks
    
    def show_n_random_chunks(self, n: int) -> None:
        if not self.chunks:
            self.chunks = self._generate_chunks()
        chunks = self.chunks
        random.shuffle(chunks)
        for i in range(min(n, len(chunks))):
            print(f"Chunk {i + 1}:")
            print(chunks[i])
            print("\n")


class ChatBot:
    """A chatbot that handles augmented and non-augmented queries and remembers the conversation."""

    def __init__(self, vectorstore, embed_model):
        self.vectorstore = vectorstore
        self.embed_model = embed_model
        self.augumented_messages_history = []
        self.non_augmented_messages_history = []
        self.system_message = {
            "role": "system",
            "content": """If the context does not provide enough information, answer based on your knowledge.
                            If the context is not relevant, don't mention it, just answer question.
                            Answer in one, if necessary, two sentences. Be concise and clear."""
        }

    def prompt_llm(self, prompt: str, augumented=False) -> str:
        if augumented:
            self.augumented_messages_history.append({"role": "user", "content": prompt})
            message = self.augumented_messages_history
        else:
            self.non_augmented_messages_history.append({"role": "user", "content": prompt})
            message = self.non_augmented_messages_history

        client = OpenAI()
        completion = client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=[self.system_message] + message,
        )
        response = {"role": "assistant", "content": completion.choices[0].message.content}

        if augumented:
            self.augumented_messages_history.append(response)
        else:
            self.non_augmented_messages_history.append(response)

        return completion.choices[0].message.content

    def augment_prompt(self, query: str) -> str:
        context = self.vectorstore.similarity_search(query, k=3)
        context = "\n".join([doc.page_content for doc in context])

        augmented_prompt = f"""Answer the following question using the context provided below.

        Question: {query}
        Context: {context}"""
        return augmented_prompt

    def chat(self, query: str) -> None:
        augmented_query = self.augment_prompt(query)

        non_augmented_response = self.prompt_llm(query)
        augmented_response = self.prompt_llm(augmented_query, augumented=True)

        # Display responses
        print("-" * 20)
        print("Non-augmented answer:")
        print(non_augmented_response)
        print("-" * 20)
        print("Augmented answer:")
        print(augmented_response)
        print("-" * 20)

def get_chunks_from_docs():
    doc_processor = DocumentProcessor(config.DATA_DIR, config.FILES_NAMES, config.NO_NEEDED_PAGES)
    print("Successfully processed documents and generated chunks.")

    return doc_processor.get_chunks()

def create_or_load_vectorstore(embed_model, chunks: List[Dict[str, Any]] = None):
    """Create a new vectorstore or load existing one from ChromaDB."""
    
    # Check if ChromaDB already exists and has data
    if os.path.exists(config.CHROMA_DB_PATH):
        try:
            vectorstore = Chroma(
                persist_directory=config.CHROMA_DB_PATH,
                embedding_function=embed_model
            )
            # Check if vectorstore has any documents
            if vectorstore._collection.count() > 0:
                print(f"Loaded existing ChromaDB with {vectorstore._collection.count()} documents.")
                return vectorstore
        except Exception as e:
            print(f"Error loading existing ChromaDB: {e}")
    
    # Create new vectorstore if none exists or if chunks are provided
    if chunks:
        print("Creating new ChromaDB vectorstore...")
        texts = [chunk["content"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]
        
        vectorstore = Chroma.from_texts(
            texts=texts,
            embedding=embed_model,
            metadatas=metadatas,
            persist_directory=config.CHROMA_DB_PATH
        )
        print(f"Successfully created ChromaDB with {len(texts)} documents.")
        return vectorstore
    else:
        # Create empty vectorstore
        vectorstore = Chroma(
            persist_directory=config.CHROMA_DB_PATH,
            embedding_function=embed_model
        )
        return vectorstore


if __name__ == "__main__":
    openai.api_key = config.OPENAI_API_KEY

    embed_model = OpenAIEmbeddings(model=config.EMBEDDING_MODEL)
    
    # Try to load existing vectorstore first
    vectorstore = create_or_load_vectorstore(embed_model)
    
    # If vectorstore is empty, process documents and create embeddings
    if vectorstore._collection.count() == 0:
        print("No existing data found. Processing documents...")
        chunks = get_chunks_from_docs()
        vectorstore = create_or_load_vectorstore(embed_model, chunks)

    chatbot = ChatBot(vectorstore=vectorstore, embed_model=embed_model)

    print("Chatbot is ready. Type your queries below (type 'exit' to quit).")
    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            print("Goodbye!")
            break
        else:
            chatbot.chat(user_input)

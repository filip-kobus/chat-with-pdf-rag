import os
from langchain_openai import OpenAI
import json
from typing import List, Dict, Any
from dotenv import load_dotenv

import pymupdf4llm
from langchain.text_splitter import MarkdownTextSplitter

from langchain_pinecone import PineconeVectorStore
from openai import OpenAI 
from langchain_openai import OpenAIEmbeddings
import openai
from pinecone import ServerlessSpec, CloudProvider, AwsRegion, Metric, Pinecone

import pathlib
import random
from tqdm.auto import tqdm
from uuid import uuid4


### Data
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
FILES_NAMES = [
    "ask_1.pdf",
    "ask_2.pdf",
    "ask_3.pdf",
    "ask_4.pdf",
]

NO_NEEDED_PAGES = {
    "ask_1.pdf": [1, 2, 44, 45, 46, 47],
    "ask_2.pdf": [1, 2, 15, 16, 17],
    "ask_3.pdf": [1, 2, 24, 25, 26],
    "ask_4.pdf": [1, 2, 3, 55, 56, 57, 58, 59, 60],
}

### Config
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("INDEX_NAME")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
LLM_MODEL = os.getenv("LLM_MODEL")
TEXT_FIELD = "text"

### Chunking parameters
CHUNK_SIZE = 800
CHUNK_OVERLAP = 80

class Database:
    """A class to manage Pinecone database operations."""

    def __init__(self, api_key: str, index_name: str):
        self.api_key = api_key
        self.index_name = index_name
        self.pinecone = Pinecone(api_key=self.api_key)
        self.index = self._initialize_index()

    def _initialize_index(self):
        if not self.pinecone.has_index(self.index_name):
            self.pinecone.create_index(
                name=self.index_name,
                dimension=1536,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1"),
            )
        return self.pinecone.Index(self.index_name)

    def get_index_stats(self) -> Dict[str, Any]:
        return self.index.describe_index_stats()

    def get_index(self):
        return self.index


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

    def _markdown_to_chunks(self, md_text: str) -> List[Dict[str, Any]]:
        splitter = MarkdownTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
        documents = splitter.create_documents([md_text])

        return [{"content": doc.page_content, "metadata": doc.metadata} for doc in documents]

    def _generate_chunks(self) -> List[Dict[str, Any]]:
        chunks = []
        for file_name in self.files_names:
            file_path = os.path.join(self.data_dir, file_name)
            not_needed_pages = self.no_needed_pages[file_name]

            md_text = self._pdf_to_markdown(file_path, not_needed_pages)
            file_chunks = self._markdown_to_chunks(md_text)

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
            model=LLM_MODEL,
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
        print(f"Query: {query}")
        print("-" * 20)
        print("Non-augmented answer:")
        print(non_augmented_response)
        print("-" * 20)
        print("Augmented answer:")
        print(augmented_response)
        print("-" * 20)

def get_chunks_from_docs():
    doc_processor = DocumentProcessor(DATA_DIR, FILES_NAMES, NO_NEEDED_PAGES)
    print("Successfully processed documents and generated chunks.")

    return doc_processor.get_chunks()

def create_embeddings(chunks: List[Dict[str, Any]], embed_model, index, batch_size: int = 20) -> None:
    for i in tqdm(range(0, len(chunks), batch_size)):
        batch = chunks[i:i + batch_size]
        ids = [str(uuid4()) for _ in batch]
        embeddings = embed_model.embed_documents([chunk["content"] for chunk in batch])
        metadata = [
            {
                TEXT_FIELD: chunk["content"],
            } for chunk in batch
        ]
        index.upsert(vectors=zip(ids, embeddings, metadata))
 
    print("Successfully embedded chunks and upserted them into the index.")


if __name__ == "__main__":
    openai.api_key = OPENAI_API_KEY

    database = Database(api_key=PINECONE_API_KEY, index_name=INDEX_NAME)
    index = database.get_index()

    embed_model = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    vectorstore = PineconeVectorStore(index=index, embedding=embed_model, text_key=TEXT_FIELD)

    chatbot = ChatBot(vectorstore=vectorstore, embed_model=embed_model)

    print("Chatbot is ready. Type your queries below (type 'exit' to quit).")
    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            print("Goodbye!")
            break
        else:
            chatbot.chat(user_input)


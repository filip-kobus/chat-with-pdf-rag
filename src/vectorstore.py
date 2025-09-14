import os
import config

from langchain_chroma import Chroma
import chromadb
from factories import ChromaDBInterface


class LocalChromaDB(ChromaDBInterface):
    def __init__(self, persist_directory):
        self.persist_directory = persist_directory
        if not os.path.exists(persist_directory):
            os.makedirs(persist_directory, exist_ok=True)
    def get_vectorstore(self, embed_model):
        return Chroma(persist_directory=self.persist_directory, embedding_function=embed_model)

class RemoteChromaDB(ChromaDBInterface):
    def __init__(self, host, port):
        self.host = host
        self.port = port
    def get_vectorstore(self, embed_model):
        client = chromadb.HttpClient(host=self.host, port=self.port)
        return Chroma(client=client, collection_name="documents", embedding_function=embed_model)

def get_vectorstore(embed_model):
    app_env = os.getenv("APP_ENV", "development").lower()
    if app_env == "production":
        chromadb_host = config.CHROMADB_HOST
        chromadb_port = config.CHROMADB_PORT
        db = RemoteChromaDB(chromadb_host, chromadb_port)
    else:
        persist_directory = config.CHROMA_DB_PATH
        db = LocalChromaDB(persist_directory)
    return db.get_vectorstore(embed_model)


class VectorStoreManager:
    def __init__(self, vectorstore):
        self.vectorstore = vectorstore

    def add_chunks(self, chunks):
        texts = [chunk["content"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]
        self.vectorstore.add_texts(texts=texts, metadatas=metadatas)

    def remove_documents_by_session_and_file(self, session_id: str, file_name: str):
        try:
            all_docs = self.vectorstore.get()
            ids_to_delete = []
            for i, metadata in enumerate(all_docs['metadatas']):
                if (metadata.get('session_id') == session_id and 
                    metadata.get('file_name') == file_name):
                    ids_to_delete.append(all_docs['ids'][i])
            if ids_to_delete:
                self.vectorstore.delete(ids=ids_to_delete)
        except Exception:
            pass

    def remove_documents_by_session(self, session_id: str):
        try:
            all_docs = self.vectorstore.get()
            ids_to_delete = []
            for i, metadata in enumerate(all_docs['metadatas']):
                if metadata.get('session_id') == session_id:
                    ids_to_delete.append(all_docs['ids'][i])
            if ids_to_delete:
                self.vectorstore.delete(ids=ids_to_delete)
        except Exception:
            pass

    def get_processed_files_for_session(self, session_id: str):
        try:
            all_docs = self.vectorstore.get()
            processed_files = set()
            for metadata in all_docs['metadatas']:
                if metadata.get('session_id') == session_id:
                    file_name = metadata.get('file_name')
                    if file_name:
                        processed_files.add(file_name)
            return list(processed_files)
        except Exception:
            return []
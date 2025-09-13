import config
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings


def get_vectorstore(embed_model):
    vectorstore = Chroma(
        persist_directory=config.CHROMA_DB_PATH,
        embedding_function=embed_model
    )
    return vectorstore


def add_chunks_to_vectorstore(vectorstore, chunks):
    texts = [chunk["content"] for chunk in chunks]
    metadatas = [chunk["metadata"] for chunk in chunks]
    vectorstore.add_texts(texts=texts, metadatas=metadatas)

import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is required but not set")

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

NO_NEEDED_PAGES = {
    "ask_1.pdf": [1, 2, 44, 45, 46, 47],
    "ask_2.pdf": [1, 2, 15, 16, 17],
    "ask_3.pdf": [1, 2, 24, 25, 26],
    "ask_4.pdf": [1, 2, 3, 55, 56, 57, 58, 59, 60],
}

CHROMA_DB_PATH = os.path.join(os.path.dirname(__file__), "chroma_db")

CHUNK_SIZE = 800
CHUNK_OVERLAP = 80

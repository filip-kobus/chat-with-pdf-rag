import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4-turbo")

DATA_DIR = Path(__file__).parent / "data"

CHROMA_DB_PATH = DATA_DIR / "chroma_db"
SESSIONS_JSON = DATA_DIR / "sessions.json"

CHUNK_SIZE = 800
CHUNK_OVERLAP = 80

MAX_SESSIONS = 5
MAX_FILES_PER_SESSION = 3

APP_ENV = os.getenv("APP_ENV", "development")

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

CHROMADB_HOST = os.getenv("CHROMADB_HOST", "chromadb")
CHROMADB_PORT = int(os.getenv("CHROMADB_PORT", "8000"))

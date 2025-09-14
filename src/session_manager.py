import json
import os
import uuid
from typing import Dict, List
import config
import redis


def get_session_manager():
    app_env = os.getenv("APP_ENV", "development").lower()
    if app_env == "production":
        return RedisSessionManager()
    else:
        return LocalSessionManager()

class LocalSessionManager:
    def __init__(self):
        self.json_file_path = config.SESSIONS_JSON
        self.max_sessions = config.MAX_SESSIONS
        self.max_files_per_session = config.MAX_FILES_PER_SESSION
        self.data = self._load_data()

    def _load_data(self) -> Dict:
        if os.path.exists(self.json_file_path):
            try:
                with open(self.json_file_path, 'r') as f:
                    data = json.load(f)
                    if 'session_queue' not in data:
                        data['session_queue'] = []
                    if 'session_files' not in data:
                        data['session_files'] = {}
                    return data
            except (json.JSONDecodeError, KeyError):
                pass
        return {"session_queue": [], "session_files": {}}

    def _save_data(self):
        os.makedirs(os.path.dirname(self.json_file_path), exist_ok=True)
        if "session_queue" not in self.data:
            self.data["session_queue"] = []
        if "session_files" not in self.data:
            self.data["session_files"] = {}
        with open(self.json_file_path, 'w') as f:
            json.dump(self.data, f, indent=2)

    def generate_session_id(self) -> str:
        return str(uuid.uuid4())

    def is_valid_session(self, session_id: str) -> bool:
        return session_id in self.data["session_files"]

    def create_session(self, session_id: str) -> str:
        if len(self.data["session_queue"]) >= self.max_sessions:
            oldest_session = self.data["session_queue"].pop(0)
            if oldest_session in self.data["session_files"]:
                del self.data["session_files"][oldest_session]
            return oldest_session
        if session_id not in self.data["session_queue"]:
            self.data["session_queue"].append(session_id)
        if session_id not in self.data["session_files"]:
            self.data["session_files"][session_id] = []
        self._save_data()
        return None

    def add_file_to_session(self, session_id: str, file_name: str) -> bool:
        if session_id not in self.data["session_files"]:
            self.data["session_files"][session_id] = []
        if len(self.data["session_files"][session_id]) >= self.max_files_per_session:
            return False
        if file_name not in self.data["session_files"][session_id]:
            self.data["session_files"][session_id].append(file_name)
            self._save_data()
        return True

    def remove_file_from_session(self, session_id: str, file_name: str):
        if session_id in self.data["session_files"]:
            if file_name in self.data["session_files"][session_id]:
                self.data["session_files"][session_id].remove(file_name)
                self._save_data()

    def get_session_files(self, session_id: str) -> List[str]:
        return self.data["session_files"].get(session_id, [])

    def can_add_file(self, session_id: str) -> bool:
        current_files = self.get_session_files(session_id)
        return len(current_files) < self.max_files_per_session

    def remove_session(self, session_id: str):
        if session_id in self.data["session_queue"]:
            self.data["session_queue"].remove(session_id)
        if session_id in self.data["session_files"]:
            del self.data["session_files"][session_id]
        self._save_data()

class RedisSessionManager:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=config.REDIS_HOST,
            port=config.REDIS_PORT,
            db=config.REDIS_DB,
            decode_responses=True
        )
        self.max_sessions = config.MAX_SESSIONS
        self.max_files_per_session = config.MAX_FILES_PER_SESSION
        self.session_queue_key = "session_queue"
        self.session_files_prefix = "session_files:"

    def generate_session_id(self) -> str:
        return str(uuid.uuid4())

    def is_valid_session(self, session_id: str) -> bool:
        return self.redis_client.exists(f"{self.session_files_prefix}{session_id}") == 1

    def create_session(self, session_id: str) -> str:
        queue_length = self.redis_client.llen(self.session_queue_key)
        if queue_length >= self.max_sessions:
            oldest_session = self.redis_client.lpop(self.session_queue_key)
            if oldest_session:
                self.redis_client.delete(f"{self.session_files_prefix}{oldest_session}")
                return oldest_session
        existing_sessions = self.redis_client.lrange(self.session_queue_key, 0, -1)
        if session_id not in existing_sessions:
            self.redis_client.rpush(self.session_queue_key, session_id)
        if not self.redis_client.exists(f"{self.session_files_prefix}{session_id}"):
            self.redis_client.lpush(f"{self.session_files_prefix}{session_id}", "")
            self.redis_client.lpop(f"{self.session_files_prefix}{session_id}")
        return None

    def add_file_to_session(self, session_id: str, file_name: str) -> bool:
        session_key = f"{self.session_files_prefix}{session_id}"
        current_files = self.redis_client.lrange(session_key, 0, -1)
        if len(current_files) >= self.max_files_per_session:
            return False
        if file_name not in current_files:
            self.redis_client.rpush(session_key, file_name)
        return True

    def remove_file_from_session(self, session_id: str, file_name: str):
        session_key = f"{self.session_files_prefix}{session_id}"
        self.redis_client.lrem(session_key, 0, file_name)

    def get_session_files(self, session_id: str) -> List[str]:
        session_key = f"{self.session_files_prefix}{session_id}"
        return self.redis_client.lrange(session_key, 0, -1)

    def can_add_file(self, session_id: str) -> bool:
        current_files = self.get_session_files(session_id)
        return len(current_files) < self.max_files_per_session

    def remove_session(self, session_id: str):
        self.redis_client.lrem(self.session_queue_key, 0, session_id)
        self.redis_client.delete(f"{self.session_files_prefix}{session_id}")

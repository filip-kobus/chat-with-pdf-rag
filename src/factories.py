from abc import ABC, abstractmethod
from typing import List


class SessionManagerInterface(ABC):
    @abstractmethod
    def generate_session_id(self) -> str:
        pass

    @abstractmethod
    def is_valid_session(self, session_id: str) -> bool:
        pass

    @abstractmethod
    def create_session(self, session_id: str) -> str:
        pass

    @abstractmethod
    def add_file_to_session(self, session_id: str, file_name: str) -> bool:
        pass

    @abstractmethod
    def remove_file_from_session(self, session_id: str, file_name: str):
        pass

    @abstractmethod
    def get_session_files(self, session_id: str) -> List[str]:
        pass

    @abstractmethod
    def can_add_file(self, session_id: str) -> bool:
        pass

    @abstractmethod
    def remove_session(self, session_id: str):
        pass


class ChromaDBInterface(ABC):
    @abstractmethod
    def get_vectorstore(self, embed_model):
        pass

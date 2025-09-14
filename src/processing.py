import os
from typing import List, Dict, Any
import config
import pymupdf4llm
from langchain.text_splitter import MarkdownTextSplitter


class DocumentProcessor:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir

    def _pdf_to_markdown(self, file_path: str) -> str:
        md_text = pymupdf4llm.to_markdown(file_path)
        return md_text

    def _markdown_to_chunks(self, md_text: str, source_file: str, session_id: str) -> List[Dict[str, Any]]:
        splitter = MarkdownTextSplitter(chunk_size=config.CHUNK_SIZE, chunk_overlap=config.CHUNK_OVERLAP)
        documents = splitter.create_documents([md_text])
        return [{"content": doc.page_content, "metadata": {"source": source_file, "session_id": session_id, "file_name": source_file}} for doc in documents]

    def process_new_files(self, new_files: List[str], session_id: str) -> List[Dict[str, Any]]:
        all_chunks = []
        for file_name in new_files:
            file_path = os.path.join(self.data_dir, file_name)
            md_text = self._pdf_to_markdown(file_path)
            file_chunks = self._markdown_to_chunks(md_text, file_name, session_id)
            all_chunks.extend(file_chunks)
        return all_chunks

    def delete_processed_files(self, file_names: List[str]) -> None:
        for file_name in file_names:
            file_path = os.path.join(self.data_dir, file_name)
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception:
                pass
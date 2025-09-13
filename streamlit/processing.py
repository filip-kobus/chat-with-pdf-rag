import os
from typing import List, Dict, Any
import config
import pymupdf4llm
from langchain.text_splitter import MarkdownTextSplitter


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

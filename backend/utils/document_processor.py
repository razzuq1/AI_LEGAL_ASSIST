import os
import uuid
from typing import Dict, List

import PyPDF2
from docx import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter


class DocumentProcessor:
    def __init__(self, chunk_size=1000, chunk_overlap=200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )

    def process_document(self, file_path: str, filename: str) -> Dict:
        try:
            text = self._extract_text(file_path, filename)
            chunks = self._split_text(text)

            document_id = str(uuid.uuid4())

            return {
                'document_id': document_id,
                'filename': filename,
                'text': text,
                'chunks': chunks,
                'chunk_count': len(chunks),
                'metadata': {
                    'filename': filename,
                    'file_path': file_path,
                    'word_count': len(text.split()),
                    'character_count': len(text),
                },
            }
        except Exception as e:
            raise Exception(f"Document processing failed: {str(e)}")

    def _extract_text(self, file_path: str, filename: str) -> str:
        file_ext = filename.lower().split('.')[-1]

        if file_ext == 'pdf':
            return self._extract_pdf_text(file_path)
        elif file_ext in ['doc', 'docx']:
            return self._extract_docx_text(file_path)
        elif file_ext == 'txt':
            return self._extract_txt_text(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")

    def _extract_pdf_text(self, file_path: str) -> str:
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            raise Exception(f"PDF extraction failed: {str(e)}")
        return text.strip()

    def _extract_docx_text(self, file_path: str) -> str:
        try:
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
        except Exception as e:
            raise Exception(f"DOCX extraction failed: {str(e)}")
        return text.strip()

    def _extract_txt_text(self, file_path: str) -> str:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
        except Exception as e:
            raise Exception(f"TXT extraction failed: {str(e)}")
        return text.strip()

    def _split_text(self, text: str) -> List[str]:
        return self.text_splitter.split_text(text)

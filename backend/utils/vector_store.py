import os
import pickle
from typing import Dict, List, Tuple

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


class VectorStore:
    def __init__(self, store_path: str):
        self.store_path = store_path
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.dimension = 384  # Dimension for all-MiniLM-L6-v2
        self.documents = {}
        self.index = None
        self.metadata = {}

        # Load existing store if available
        self._load_store()

    def add_document(self, document_id: str, chunks: List[str], metadata: Dict = None):
        """Add document chunks to vector store"""
        try:
            # Generate embeddings
            embeddings = self.model.encode(chunks)

            # Initialize index if first document
            if self.index is None:
                self.index = faiss.IndexFlatIP(self.dimension)  # Inner product for similarity

            # Normalize embeddings for cosine similarity
            faiss.normalize_L2(embeddings)

            # Add to index
            start_idx = self.index.ntotal
            self.index.add(embeddings.astype('float32'))

            # Store document data
            self.documents[document_id] = {
                'chunks': chunks,
                'start_idx': start_idx,
                'end_idx': start_idx + len(chunks),
                'metadata': metadata or {},
            }

            # Save store
            self._save_store()

        except Exception as e:
            raise Exception(f"Failed to add document to vector store: {str(e)}")

    def search(self, query: str, document_id: str = None, top_k: int = 5) -> List[Tuple[str, float]]:
        """Search for similar chunks"""
        try:
            if self.index is None or self.index.ntotal == 0:
                return []
            # Generate query embedding
            query_embedding = self.model.encode([query])
            faiss.normalize_L2(query_embedding)

            # Search
            scores, indices = self.index.search(query_embedding.astype('float32'), top_k * 2)

            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx == -1:  # Invalid index
                    continue

                # Find which document this chunk belongs to
                chunk_text, chunk_doc_id = self._get_chunk_by_index(idx)

                if chunk_text and (document_id is None or chunk_doc_id == document_id):
                    results.append((chunk_text, float(score)))

                if len(results) >= top_k:
                    break

            return results

        except Exception as e:
            print(f"Search error: {str(e)}")
            return []

    def _get_chunk_by_index(self, global_idx: int) -> Tuple[str, str]:
        """Get chunk text and document ID by global index"""
        for doc_id, doc_data in self.documents.items():
            if doc_data['start_idx'] <= global_idx < doc_data['end_idx']:
                local_idx = global_idx - doc_data['start_idx']
                if local_idx < len(doc_data['chunks']):
                    return doc_data['chunks'][local_idx], doc_id
        return None, None

    def get_document_chunks(self, document_id: str) -> List[str]:
        """Get all chunks for a document"""
        if document_id in self.documents:
            return self.documents[document_id]['chunks']
        return []

    def delete_document(self, document_id: str):
        """Remove document from store"""
        if document_id in self.documents:
            del self.documents[document_id]
            # Note: FAISS doesn't support individual deletion efficiently
            # For production, consider rebuilding index periodically
            self._save_store()

    def _save_store(self):
        """Save vector store to disk"""
        try:
            os.makedirs(self.store_path, exist_ok=True)

            # Save FAISS index
            if self.index is not None:
                faiss.write_index(self.index, os.path.join(self.store_path, 'index.faiss'))

            # Save documents and metadata
            with open(os.path.join(self.store_path, 'documents.pkl'), 'wb') as f:
                pickle.dump(self.documents, f)

        except Exception as e:
            print(f"Failed to save vector store: {str(e)}")

    def _load_store(self):
        """Load vector store from disk"""
        try:
            index_path = os.path.join(self.store_path, 'index.faiss')
            docs_path = os.path.join(self.store_path, 'documents.pkl')

            if os.path.exists(index_path):
                self.index = faiss.read_index(index_path)

            if os.path.exists(docs_path):
                with open(docs_path, 'rb') as f:
                    self.documents = pickle.load(f)

        except Exception as e:
            print(f"Failed to load vector store: {str(e)}")
            self.index = None
            self.documents = {}

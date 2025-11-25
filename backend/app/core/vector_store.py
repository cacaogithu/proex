"""
Vector Store - In-memory vector database for RAG
Stores and searches document chunks by semantic similarity
"""
from typing import List, Tuple, Optional
import numpy as np
from dataclasses import dataclass


@dataclass
class StoredChunk:
    """Chunk stored in vector database"""
    chunk_id: str
    text: str
    source: str
    embedding: List[float]
    submission_id: str


class VectorStore:
    """
    Simple in-memory vector store for document chunks
    Supports similarity search using cosine distance
    """
    def __init__(self):
        self.chunks: dict = {}  # submission_id -> list of StoredChunks
    
    def add_chunks(self, submission_id: str, chunks) -> int:
        """
        Add chunks to vector store
        
        Args:
            submission_id: ID of submission
            chunks: List of Chunk objects with embeddings
        
        Returns:
            Number of chunks added
        """
        if submission_id not in self.chunks:
            self.chunks[submission_id] = []
        
        for chunk in chunks:
            stored = StoredChunk(
                chunk_id=chunk.id,
                text=chunk.text,
                source=chunk.source,
                embedding=chunk.embedding,
                submission_id=submission_id
            )
            self.chunks[submission_id].append(stored)
        
        return len(chunks)
    
    def search(self, submission_id: str, query_embedding: List[float], top_k: int = 5) -> List[Tuple]:
        """
        Search for most similar chunks
        
        Args:
            submission_id: ID of submission
            query_embedding: Query embedding vector
            top_k: Number of results to return
        
        Returns:
            List of tuples (chunk, similarity_score) sorted by score descending
        """
        if submission_id not in self.chunks:
            return []
        
        chunks = self.chunks[submission_id]
        if not chunks:
            return []
        
        scores = []
        for chunk in chunks:
            if not chunk.embedding:
                scores.append(0.0)
                continue
            
            similarity = self._cosine_similarity(query_embedding, chunk.embedding)
            scores.append(similarity)
        
        # Get top-k indices
        top_indices = np.argsort(scores)[-top_k:][::-1]
        
        results = [(chunks[i], scores[i]) for i in top_indices if scores[i] > 0]
        return results
    
    def clear_submission(self, submission_id: str):
        """Clear all chunks for a submission"""
        if submission_id in self.chunks:
            del self.chunks[submission_id]
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if not vec1 or not vec2:
            return 0.0
        
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(np.dot(v1, v2) / (norm1 * norm2))

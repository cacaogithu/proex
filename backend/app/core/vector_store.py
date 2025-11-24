"""
Vector Store using Supabase Vector
Stores and searches document embeddings
"""
from typing import List, Dict, Tuple
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


class VectorStore:
    """
    In-memory vector store for MVP
    Will migrate to Supabase Vector pgvector in production
    """
    def __init__(self):
        # Structure: submission_id -> List[(vector, chunk_text, metadata)]
        self.vectors: Dict[str, List[Tuple[List[float], str, Dict]]] = {}
    
    def add_vectors(self, submission_id: str, chunks_with_embeddings: List[Tuple[List[float], str, Dict]]):
        """
        Store vectors for a submission
        chunks_with_embeddings: List of (embedding_vector, chunk_text, metadata)
        """
        if submission_id not in self.vectors:
            self.vectors[submission_id] = []
        
        self.vectors[submission_id].extend(chunks_with_embeddings)
        print(f"✅ Stored {len(chunks_with_embeddings)} vectors for submission {submission_id}")
    
    def search(
        self,
        query_vector: List[float],
        submission_id: str,
        top_k: int = 5,
        threshold: float = 0.7
    ) -> List[Dict]:
        """
        Search for similar vectors using cosine similarity
        
        Returns: List of {
            'text': chunk_text,
            'score': similarity_score,
            'metadata': chunk_metadata
        }
        """
        if submission_id not in self.vectors:
            return []
        
        vectors_data = self.vectors[submission_id]
        if not vectors_data:
            return []
        
        # Extract vectors and prepare for similarity calculation
        stored_vectors = [v[0] for v in vectors_data]
        
        # Calculate cosine similarities
        query_array = np.array([query_vector])
        stored_array = np.array(stored_vectors)
        
        similarities = cosine_similarity(query_array, stored_array)[0]
        
        # Get top_k indices sorted by similarity
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        # Build results
        results = []
        for idx in top_indices:
            score = float(similarities[idx])
            if score >= threshold:
                _, chunk_text, metadata = vectors_data[int(idx)]
                results.append({
                    'text': chunk_text,
                    'score': score,
                    'metadata': metadata
                })
        
        return results
    
    def clear_submission(self, submission_id: str):
        """Remove all vectors for a submission"""
        if submission_id in self.vectors:
            del self.vectors[submission_id]
            print(f"🗑️  Cleared vectors for submission {submission_id}")
    
    def get_stats(self) -> Dict:
        """Get storage statistics"""
        total_vectors = sum(len(v) for v in self.vectors.values())
        return {
            'total_submissions': len(self.vectors),
            'total_vectors': total_vectors,
            'submissions': {
                sid: len(vectors) 
                for sid, vectors in self.vectors.items()
            }
        }

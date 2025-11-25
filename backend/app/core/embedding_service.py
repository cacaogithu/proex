"""
Embedding Service - Generate vector embeddings using OpenAI
"""
from typing import List, Optional
import numpy as np


class EmbeddingService:
    """
    Generates text embeddings using OpenAI's embedding model
    """
    def __init__(self, openai_client=None, model: str = "text-embedding-3-small"):
        self.client = openai_client
        self.model = model
    
    def embed(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for text
        
        Args:
            text: Text to embed
        
        Returns:
            Embedding vector (list of floats) or None if failed
        """
        if not self.client or not text:
            return None
        
        try:
            response = self.client.embeddings.create(
                input=text,
                model=self.model
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"⚠️  Embedding failed: {e}")
            return None
    
    def embed_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of texts to embed
        
        Returns:
            List of embedding vectors (some may be None if failed)
        """
        if not self.client or not texts:
            return [None] * len(texts)
        
        try:
            response = self.client.embeddings.create(
                input=texts,
                model=self.model
            )
            
            # Sort by index to maintain order
            embeddings_by_index = {item.index: item.embedding for item in response.data}
            return [embeddings_by_index.get(i) for i in range(len(texts))]
        except Exception as e:
            print(f"⚠️  Batch embedding failed: {e}")
            return [None] * len(texts)
    
    def similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings
        """
        if not embedding1 or not embedding2:
            return 0.0
        
        e1 = np.array(embedding1)
        e2 = np.array(embedding2)
        return float(np.dot(e1, e2) / (np.linalg.norm(e1) * np.linalg.norm(e2)))

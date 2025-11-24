"""
Embedding Service for RAG Engine
Generates vector embeddings using OpenAI API
"""
from typing import List
from openai import OpenAI
import os


class EmbeddingService:
    """
    Generate embeddings using OpenAI text-embedding-3-small
    Cost-effective model with good performance
    """
    def __init__(self, openai_client=None):
        if openai_client:
            self.client = openai_client
        else:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            self.client = OpenAI(api_key=api_key)
        
        self.model = "text-embedding-3-small"  # 1536 dimensions, $0.02/1M tokens
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding vector for a single text
        Returns 1536-dimensional vector
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        response = self.client.embeddings.create(
            model=self.model,
            input=text
        )
        
        return response.data[0].embedding
    
    def embed_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches
        OpenAI allows up to 2048 texts per request, we use 100 for safety
        """
        if not texts:
            return []
        
        # Filter out empty texts
        valid_texts = [t for t in texts if t and t.strip()]
        if not valid_texts:
            raise ValueError("No valid texts to embed")
        
        all_embeddings = []
        
        # Process in batches
        for i in range(0, len(valid_texts), batch_size):
            batch = valid_texts[i:i + batch_size]
            
            response = self.client.embeddings.create(
                model=self.model,
                input=batch
            )
            
            # Extract embeddings in order
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)
        
        return all_embeddings
    
    def get_embedding_dim(self) -> int:
        """Return the dimensionality of embeddings from this model"""
        return 1536  # text-embedding-3-small dimension

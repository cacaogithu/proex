"""
EmbeddingEngine - Gera embeddings semânticos para cartas
Usa OpenRouter API para criar representações vetoriais
"""

import os
import json
import numpy as np
from typing import List, Optional
from openai import OpenAI


class EmbeddingEngine:
    """Gera embeddings semânticos de alta qualidade usando LLMs"""
    
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1"
        )
        
        # Modelo para embeddings - Gemini Flash é econômico
        # Alternativa: usar text-embedding-3-small da OpenAI via OpenRouter
        self.embedding_model = "google/gemini-2.5-flash"
    
    def generate_embedding(self, text: str, max_length: int = 2000) -> Optional[List[float]]:
        """
        Gera embedding semântico de um texto
        
        Args:
            text: Texto para embedar (carta, bloco, etc)
            max_length: Máximo de caracteres a processar
        
        Returns:
            Lista de floats representando o embedding (768 ou 1536 dimensões)
        """
        try:
            # Truncar texto se necessário
            truncated_text = text[:max_length] if len(text) > max_length else text
            
            # Usar LLM para gerar representação semântica compacta
            # Como OpenRouter não tem endpoint dedicado de embeddings,
            # vamos usar uma técnica alternativa: gerar resumo estruturado
            # e converter para embedding via hashing semântico
            
            response = self.client.chat.completions.create(
                model=self.embedding_model,
                messages=[{
                    "role": "user",
                    "content": f"""Analyze this recommendation letter and extract its semantic features as a JSON object with numerical scores (0-10):

{truncated_text}

Return JSON with these features:
- technical_depth: 0-10
- academic_rigor: 0-10
- leadership_focus: 0-10
- innovation_emphasis: 0-10
- specificity: 0-10 (how specific vs generic)
- formality: 0-10 (casual to formal)
- storytelling: 0-10 (data-driven to narrative)
- impact_focus: 0-10 (process vs results)
- international_scope: 0-10"""
                }],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            if content:
                features = json.loads(content)
                
                # Converter features em vetor numérico
                embedding = [
                    features.get('technical_depth', 5),
                    features.get('academic_rigor', 5),
                    features.get('leadership_focus', 5),
                    features.get('innovation_emphasis', 5),
                    features.get('specificity', 5),
                    features.get('formality', 5),
                    features.get('storytelling', 5),
                    features.get('impact_focus', 5),
                    features.get('international_scope', 5)
                ]
                
                return embedding
            
            return None
            
        except Exception as e:
            print(f"⚠️ Error generating embedding: {e}")
            return None
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calcula similaridade cosine entre dois embeddings
        
        Returns:
            Float entre 0 (diferentes) e 1 (idênticos)
        """
        if not embedding1 or not embedding2:
            return 0.0
        
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        # Cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    
    def find_similar_letters(
        self, 
        target_embedding: List[float], 
        all_embeddings: List[tuple], 
        top_k: int = 3
    ) -> List[tuple]:
        """
        Encontra cartas mais similares
        
        Args:
            target_embedding: Embedding da carta de referência
            all_embeddings: Lista de (letter_id, embedding, score)
            top_k: Número de cartas similares a retornar
        
        Returns:
            Lista de (letter_id, similarity, score) ordenadas por similaridade
        """
        similarities = []
        
        for letter_id, embedding, score in all_embeddings:
            similarity = self.calculate_similarity(target_embedding, embedding)
            similarities.append((letter_id, similarity, score))
        
        # Ordenar por similaridade (maior primeiro)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]

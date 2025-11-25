"""
Document Chunker for RAG Engine
Splits documents into semantic chunks for embedding
"""
from typing import List, Dict
import re


class Chunk:
    """Represents a text chunk with metadata"""
    def __init__(self, text: str, metadata: Dict):
        self.text = text
        self.metadata = metadata  # source_file, page_number, submission_id, etc.


class DocumentChunker:
    """
    Smart text chunking for RAG
    Splits documents into semantically meaningful chunks
    """
    def __init__(self, chunk_size: int = 600, overlap: int = 100):
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation: ~4 chars per token"""
        return len(text) // 4
    
    def _split_into_paragraphs(self, text: str) -> List[str]:
        """Split text by double newlines (paragraphs)"""
        paragraphs = re.split(r'\n\s*\n', text)
        return [p.strip() for p in paragraphs if p.strip()]
    
    def chunk_text(self, text: str, metadata: Dict = None) -> List[Chunk]:
        """
        Smart chunking strategy:
        1. Split by paragraphs first
        2. Combine into chunks of ~chunk_size tokens
        3. Add overlap for context preservation
        """
        if metadata is None:
            metadata = {}
        
        paragraphs = self._split_into_paragraphs(text)
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for para in paragraphs:
            para_tokens = self._estimate_tokens(para)
            
            # If single paragraph exceeds chunk_size, split it
            if para_tokens > self.chunk_size:
                # Save current chunk if exists
                if current_chunk:
                    chunk_text = "\n\n".join(current_chunk)
                    chunks.append(Chunk(chunk_text, metadata.copy()))
                    current_chunk = []
                    current_tokens = 0
                
                # Split long paragraph by sentences
                sentences = re.split(r'[.!?]\s+', para)
                temp_chunk = []
                temp_tokens = 0
                
                for sent in sentences:
                    sent_tokens = self._estimate_tokens(sent)
                    if temp_tokens + sent_tokens > self.chunk_size:
                        if temp_chunk:
                            chunk_text = ". ".join(temp_chunk) + "."
                            chunks.append(Chunk(chunk_text, metadata.copy()))
                        temp_chunk = [sent]
                        temp_tokens = sent_tokens
                    else:
                        temp_chunk.append(sent)
                        temp_tokens += sent_tokens
                
                if temp_chunk:
                    chunk_text = ". ".join(temp_chunk) + "."
                    chunks.append(Chunk(chunk_text, metadata.copy()))
                
                continue
            
            # Normal chunking by paragraphs
            if current_tokens + para_tokens > self.chunk_size:
                # Save current chunk
                chunk_text = "\n\n".join(current_chunk)
                chunks.append(Chunk(chunk_text, metadata.copy()))
                
                # Start new chunk with overlap
                # Keep last paragraph for overlap if it's not too big
                if current_chunk and self._estimate_tokens(current_chunk[-1]) < self.overlap:
                    current_chunk = [current_chunk[-1], para]
                    current_tokens = self._estimate_tokens(current_chunk[-1]) + para_tokens
                else:
                    current_chunk = [para]
                    current_tokens = para_tokens
            else:
                current_chunk.append(para)
                current_tokens += para_tokens
        
        # Save final chunk
        if current_chunk:
            chunk_text = "\n\n".join(current_chunk)
            chunks.append(Chunk(chunk_text, metadata.copy()))
        
        return chunks
    
    def chunk_document(self, file_path: str, text: str, submission_id: str) -> List[Chunk]:
        """
        Chunk a document with proper metadata
        """
        import os
        filename = os.path.basename(file_path)
        
        metadata = {
            'source_file': filename,
            'submission_id': submission_id,
            'file_path': file_path
        }
        
        return self.chunk_text(text, metadata)

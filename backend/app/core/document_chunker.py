"""
Document Chunker - Split documents into semantic chunks
"""
from typing import List
from dataclasses import dataclass
import uuid


@dataclass
class Chunk:
    """Represents a chunk of text from a document"""
    id: str
    text: str
    source: str
    embedding: List[float] = None
    start_char: int = 0
    end_char: int = 0


class DocumentChunker:
    """
    Chunks documents into overlapping segments for RAG
    """
    def __init__(self, chunk_size: int = 600, overlap: int = 100):
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk_document(self, source: str, text: str, submission_id: str) -> List[Chunk]:
        """
        Split document into overlapping chunks
        
        Args:
            source: File name or source identifier
            text: Full document text
            submission_id: ID of submission this document belongs to
        
        Returns:
            List of Chunk objects
        """
        # Clean text
        text = text.strip()
        if not text:
            return []
        
        # Split by paragraphs first for better semantics
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            # Add paragraph to current chunk
            candidate = current_chunk + "\n\n" + para if current_chunk else para
            
            # If too long, save current chunk and start new one
            if len(candidate) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk)
                    # Overlap: keep last part of chunk
                    words = current_chunk.split()
                    overlap_words = words[-10:] if len(words) > 10 else words
                    current_chunk = " ".join(overlap_words) + "\n\n" + para
                else:
                    # Single paragraph is too long, split by sentences
                    current_chunk = para
                    if len(current_chunk) > self.chunk_size:
                        chunks.extend(self._split_long_para(current_chunk))
                        current_chunk = ""
            else:
                current_chunk = candidate
        
        # Add final chunk
        if current_chunk:
            chunks.append(current_chunk)
        
        # Convert to Chunk objects
        result = []
        for i, chunk_text in enumerate(chunks):
            chunk = Chunk(
                id=str(uuid.uuid4()),
                text=chunk_text,
                source=source,
            )
            result.append(chunk)
        
        return result
    
    def _split_long_para(self, text: str) -> List[str]:
        """
        Split a long paragraph by sentences
        """
        # Simple sentence splitting on periods/newlines
        sentences = text.replace('.\n', '.').replace('? ', '?\n').replace('! ', '!\n').split('\n')
        
        chunks = []
        current = ""
        
        for sent in sentences:
            if len(current) + len(sent) < self.chunk_size:
                current += " " + sent if current else sent
            else:
                if current:
                    chunks.append(current)
                current = sent
        
        if current:
            chunks.append(current)
        
        return chunks

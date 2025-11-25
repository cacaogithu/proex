"""
RAG Engine - Retrieval Augmented Generation
Orchestrates document ingestion, embedding, and context retrieval
"""
from typing import List, Dict
import os
from .document_chunker import DocumentChunker, Chunk
from .embedding_service import EmbeddingService
from .vector_store import VectorStore
from .pdf_extractor import PDFExtractor


class RAGEngine:
    """
    Main RAG Engine for context-aware letter generation
    """
    def __init__(self, llm_processor=None):
        self.chunker = DocumentChunker(chunk_size=600, overlap=100)
        self.embedder = EmbeddingService(openai_client=llm_processor.client if llm_processor else None)
        self.vector_store = VectorStore()
        self.pdf_extractor = PDFExtractor()
    
    def ingest_documents(self, submission_id: str, file_paths: List[str]):
        """
        Process and index documents for a submission
        
        Steps:
        1. Extract text from PDFs
        2. Chunk into semantic segments
        3. Generate embeddings
        4. Store in vector database
        """
        if not file_paths:
            print(f"⚠️  No files to ingest for submission {submission_id}")
            return
        
        print(f"📚 Ingesting {len(file_paths)} documents for submission {submission_id}...")
        
        all_chunks = []
        
        # Step 1 & 2: Extract and chunk each document
        for file_path in file_paths:
            if not os.path.exists(file_path):
                print(f"⚠️  File not found: {file_path}")
                continue
            
            try:
                # Extract text from PDF
                if file_path.endswith('.pdf'):
                    extracted_data = self.pdf_extractor.extract_from_pdf(file_path)
                    text = extracted_data.get('text', '')
                elif file_path.endswith('.txt'):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        text = f.read()
                else:
                    print(f"⚠️  Unsupported file type: {file_path}")
                    continue
                
                if not text or len(text.strip()) < 100:
                    print(f"⚠️  Not enough text extracted from {file_path}")
                    continue
                
                # Chunk the text
                chunks = self.chunker.chunk_document(file_path, text, submission_id)
                all_chunks.extend(chunks)
                print(f"   ✓ {os.path.basename(file_path)}: {len(chunks)} chunks")
                
            except Exception as e:
                print(f"❌ Error processing {file_path}: {str(e)}")
                continue
        
        if not all_chunks:
            print(f"⚠️  No chunks generated for submission {submission_id}")
            return
        
        # Step 3: Generate embeddings
        print(f"   Embedding {len(all_chunks)} chunks...")
        embedded_chunks = []
        for i, chunk in enumerate(all_chunks):
            try:
                embedding = self.embedder.embed(chunk.text)
                chunk.embedding = embedding
                embedded_chunks.append(chunk)
                if (i + 1) % 10 == 0:
                    print(f"   ✓ Embedded {i + 1}/{len(all_chunks)} chunks")
            except Exception as e:
                print(f"   ⚠️  Skipped embedding for chunk {i}: {str(e)}")
                continue
        
        if not embedded_chunks:
            print(f"❌ Failed to embed any chunks")
            return
        
        # Step 4: Store in vector database
        self.vector_store.add_chunks(submission_id, embedded_chunks)
        print(f"✅ Stored {len(embedded_chunks)} embedded chunks in vector store")
    
    def retrieve_context(self, submission_id: str, query: str, top_k: int = 5) -> List[Dict]:
        """
        Retrieve most relevant chunks for a query
        
        Returns:
            List of dicts with 'text', 'source', and 'score' keys
        """
        query_embedding = self.embedder.embed(query)
        results = self.vector_store.search(submission_id, query_embedding, top_k=top_k)
        
        formatted_results = []
        for chunk, score in results:
            formatted_results.append({
                'text': chunk.text,
                'source': chunk.source,
                'score': score
            })
        
        return formatted_results
    
    def get_context_for_block(self, submission_id: str, block_name: str) -> str:
        """
        Get relevant context from documents for a specific block
        
        Args:
            submission_id: ID of submission
            block_name: Name of block (e.g., 'block3', 'block4')
        
        Returns:
            Concatenated context text
        """
        queries = {
            'block3': 'professional background experience introduction context',
            'block4': 'technical skills achievements accomplishments results',
            'block5': 'impact outcomes measurable results quantified benefits',
            'block6': 'evidence validation data proof corroboration',
            'block7': 'conclusion recommendation summary final thoughts'
        }
        
        query = queries.get(block_name, 'relevant context')
        results = self.retrieve_context(submission_id, query, top_k=3)
        
        context = "\n\n".join([r['text'] for r in results])
        return context if context else ""

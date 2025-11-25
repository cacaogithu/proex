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
        
        print(f"📊 Total chunks: {len(all_chunks)}")
        
        # Step 3: Generate embeddings (batch processing)
        chunk_texts = [chunk.text for chunk in all_chunks]
        print(f"🔮 Generating embeddings...")
        
        try:
            embeddings = self.embedder.embed_batch(chunk_texts, batch_size=50)
            print(f"   ✓ Generated {len(embeddings)} embeddings")
        except Exception as e:
            print(f"❌ Error generating embeddings: {str(e)}")
            return
        
        # Step 4: Store in vector database
        chunks_with_embeddings = [
            (embeddings[i], chunk.text, chunk.metadata)
            for i, chunk in enumerate(all_chunks)
        ]
        
        self.vector_store.add_vectors(submission_id, chunks_with_embeddings)
        print(f"✅ RAG ingestion complete for submission {submission_id}")
    
    def retrieve_context(
        self,
        query: str,
        submission_id: str,
        top_k: int = 5,
        threshold: float = 0.7
    ) -> List[str]:
        """
        Retrieve relevant context chunks for a query
        
        Returns: List of relevant text chunks
        """
        if not query or not query.strip():
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.embedder.embed_text(query)
            
            # Search vector store
            results = self.vector_store.search(
                query_vector=query_embedding,
                submission_id=submission_id,
                top_k=top_k,
                threshold=threshold
            )
            
            # Extract text chunks
            context_chunks = [r['text'] for r in results]
            
            if context_chunks:
                scores = [f"{r['score']:.2f}" for r in results]
                print(f"Retrieved {len(context_chunks)} relevant chunks (scores: {scores})")
            
            return context_chunks
            
        except Exception as e:
            print(f"Error retrieving context: {str(e)}")
            return []
    
    def augment_prompt(self, base_prompt: str, context_chunks: List[str]) -> str:
        """
        Inject retrieved context into generation prompt
        """
        if not context_chunks:
            return base_prompt
        
        context_section = "# CONTEXTO ADICIONAL DO USUÁRIO\n\n"
        context_section += "Use as informações abaixo para enriquecer a carta com detalhes específicos:\n\n"
        
        for i, chunk in enumerate(context_chunks, 1):
            context_section += f"## Fonte {i}\n{chunk}\n\n"
        
        context_section += "Integre essas informações naturalmente na narrativa, usando exemplos e detalhes específicos.\n\n"
        context_section += "---\n\n"
        
        return context_section + base_prompt
    
    def get_stats(self) -> Dict:
        """Get RAG engine statistics"""
        return self.vector_store.get_stats()

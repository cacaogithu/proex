"""
Vector Store Configuration for RAG Engine
Uses Supabase Vector for semantic search
"""
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

# Vector Store Configuration
VECTOR_STORE_ID = "vs_68d5cdc6ed788191aac4180dbb63e2d3"

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

# OpenAI Configuration (for embeddings)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# RAG Configuration
EMBEDDING_MODEL = "text-embedding-3-small"  # Cost-effective, 1536 dimensions
CHUNK_SIZE = 600  # tokens per chunk
CHUNK_OVERLAP = 100  # token overlap between chunks
TOP_K_RESULTS = 5  # number of context chunks to retrieve
SIMILARITY_THRESHOLD = 0.7  # minimum cosine similarity to include result

# Validate required environment variables (warnings only - allows startup without RAG)
import warnings

if not SUPABASE_URL or not SUPABASE_KEY:
    warnings.warn("SUPABASE_URL and SUPABASE_ANON_KEY not set - RAG may not work with Supabase Vector")

if not OPENAI_API_KEY:
    warnings.warn("OPENAI_API_KEY not set - RAG embeddings generation will fail")


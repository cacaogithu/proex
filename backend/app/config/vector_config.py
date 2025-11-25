"""
Vector Store Configuration
"""

# Embedding model settings
EMBEDDING_MODEL = "text-embedding-3-small"

# Chunking settings
CHUNK_SIZE = 600  # Characters per chunk
CHUNK_OVERLAP = 100  # Character overlap between chunks

# Search settings
SEARCH_TOP_K = 5  # Number of results to retrieve
MIN_SIMILARITY_SCORE = 0.3  # Minimum score to include result

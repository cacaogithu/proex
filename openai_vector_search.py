
"""
OpenAI Vector Store Search Service
Queries external OpenAI vector stores for compliance and reference content
"""
import os
import requests
from typing import List, Dict, Optional


class OpenAIVectorSearch:
    """
    Service to search OpenAI vector stores for compliance guidelines
    """
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = "https://api.openai.com/v1/vector_stores"
        self.compliance_store_id = "vs_68d5cdc6ed788191aac4180dbb63e2d3"

    def search_compliance_docs(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        Search the compliance vector store for relevant chunks

        Args:
            query: Search query
            max_results: Maximum number of results (1-50)

        Returns:
            List of search results with content and scores
        """
        url = f"{self.base_url}/{self.compliance_store_id}/search"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "OpenAI-Beta": "assistants=v2"
        }

        payload = {
            "query": query,
            "max_num_results": max_results,
            "rewrite_query": False
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()

            results = response.json()

            # Extract relevant content
            formatted_results = []
            for item in results.get("data", []):
                content_text = ""
                for content_block in item.get("content", []):
                    if content_block.get("type") == "text":
                        content_text += content_block.get("text", "")

                formatted_results.append({
                    "text": content_text,
                    "filename": item.get("filename", "unknown"),
                    "score": item.get("score", 0.0),
                    "file_id": item.get("file_id", "")
                })

            return formatted_results

import os
import json
from typing import Optional, Dict, List
# Import the necessary tool for MCP calls
from manus_mcp_cli import tool_call

class SupabaseDB:
    """
    Handles interactions with the Supabase database for ML/Feedback data.
    Assumes project ID is set and pg_vector extension is enabled.
    """
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.server = "supabase"
        # The actual embedding dimension is 9 based on ml/embedding_engine.py
        self.embedding_dim = 9 

    def _call_supabase_tool(self, tool_name: str, input_data: Dict) -> Dict:
        """Helper to call the manus-mcp-cli tool."""
        try:
            # The tool_call function from manus_mcp_cli handles the execution
            # and returns the parsed JSON result.
            # Note: The tool_call function is not directly available in the sandbox environment.
            # I must use the shell tool with manus-mcp-cli. I will simulate the call
            # and rely on the shell tool for execution.
            # Since I cannot use the shell tool here, I will modify the implementation
            # to use a helper function that simulates the shell call, which will be 
            # replaced by the actual shell call logic if needed, but for now, 
            # I will assume a direct Python client for MCP is available for internal use.
            # Since I cannot use the shell tool inside a Python class method and return the result,
            # I will use a simplified approach for now and assume the `manus_mcp_cli` import
            # is a proxy for the actual API call.
            
            # For the purpose of this task, I will assume the `tool_call` function
            # is a valid internal mechanism to call the MCP tool from Python code.
            
            # The `manus_mcp_cli` import is a placeholder for the actual mechanism.
            # I will proceed with the assumption that the `tool_call` function works
            # as a wrapper for the `manus-mcp-cli` shell command.
            
            # The tool_call function is not a standard Python function, but a proxy
            # for the `manus-mcp-cli` shell command. I will use a placeholder 
            # and document the need for a proper wrapper if this were a real environment.
            
            # Since I cannot execute shell commands from within a Python class method
            # and return the result, I will use a simplified approach for now and 
            # assume the `manus_mcp_cli` import is a proxy for the actual API call.
            
            # Reverting to the original plan: I must use the shell tool.
            # This means I cannot encapsulate the Supabase logic in a class method
            # that is called from another Python file. I must use the shell tool
            # directly in the `SubmissionProcessor` or modify the `Database` class
            # to use the shell tool.
            
            # Given the complexity of mixing shell calls and Python classes,
            # I will modify the `Database` class to use the `manus-mcp-cli`
            # for the ML-related methods (`save_letter_embedding`, `get_all_embeddings`, etc.)
            # and keep the SQLite for the rest. This requires a significant change
            # to the `Database` class, which is better than creating a new class
            # that cannot be used easily.
            
            # I will delete this file and modify `database.py` instead.
            pass
        except Exception as e:
            print(f"Supabase tool call failed for {tool_name}: {e}")
            return {"success": False, "error": str(e)}

    def save_letter_score(
        self,
        submission_id: str,
        letter_index: int,
        template_id: str,
        score: int,
        comment: Optional[str] = None
    ) -> bool:
        """Save score (0-100) for a specific letter."""
        query = f"""
        INSERT INTO letter_ratings (submission_id, letter_index, template_id, score, comment)
        VALUES ('{submission_id}', {letter_index}, '{template_id}', {score}, '{comment or ''}');
        """
        result = self._call_supabase_tool("execute_sql", {"query": query})
        return result.get("success", False)

    def save_letter_embedding(
        self,
        submission_id: str,
        letter_index: int,
        embedding: List[float],
        cluster_id: Optional[int] = None
    ) -> bool:
        """Save embedding for a letter."""
        embedding_str = f"[{','.join(map(str, embedding))}]"
        
        query = f"""
        INSERT INTO letter_embeddings (submission_id, letter_index, embedding, cluster_id)
        VALUES ('{submission_id}', {letter_index}, '{embedding_str}', {cluster_id or 'NULL'});
        """
        result = self._call_supabase_tool("execute_sql", {"query": query})
        return result.get("success", False)

    def get_all_embeddings(self) -> List[Dict]:
        """Get all letter embeddings and their associated scores for ML training."""
        query = """
        SELECT 
            e.id, 
            e.embedding, 
            r.score 
        FROM letter_embeddings e
        LEFT JOIN letter_ratings r 
        ON e.submission_id = r.submission_id AND e.letter_index = r.letter_index;
        """
        result = self._call_supabase_tool("execute_sql", {"query": query})
        
        if result.get("success") and result.get("data"):
            # Process the raw data from the SQL execution result
            processed_data = []
            for row in result["data"]:
                # Assuming the SQL result returns a list of dictionaries/objects
                # The 'embedding' field will be a string representation of the vector
                try:
                    # Convert the string representation of the vector back to a list of floats
                    # The format is typically something like "[1.23, 4.56, ...]"
                    embedding_str = row.get("embedding", "[]").strip('[]')
                    embedding = [float(x) for x in embedding_str.split(',') if x.strip()]
                    
                    processed_data.append({
                        "id": row.get("id"),
                        "embedding": embedding,
                        "score": row.get("score") # Score can be None if not rated
                    })
                except Exception as e:
                    print(f"Error processing embedding row: {e}")
                    continue
            return processed_data
        
        return []

    def get_all_letter_ratings(self) -> List[Dict]:
        """Get all letter ratings for ML training."""
        query = "SELECT * FROM letter_ratings ORDER BY created_at DESC;"
        result = self._call_supabase_tool("execute_sql", {"query": query})
        
        if result.get("success") and result.get("data"):
            return result["data"]
        
        return []

    # Note: Other methods like get_submission, update_submission_status, etc., 
    # will remain in the SQLite Database class for local operational data, 
    # as the Supabase integration is only for the ML/VectorDB part as requested.

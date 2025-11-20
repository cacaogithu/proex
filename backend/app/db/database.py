import sqlite3
from .supabase_db import SupabaseDB
import json
import os
from datetime import datetime
import uuid
from typing import Optional, Dict, List


class Database:
    def __init__(self, db_path="proex.db", supabase_project_id: Optional[str] = None):
        self.db_path = db_path
        db_dir = os.path.dirname(self.db_path)
        if db_dir:  # Only create directory if path has a directory component
            os.makedirs(db_dir, exist_ok=True)
        self.init_db()

        # Configuration: Supabase project ID from environment variable
        # Note: Supabase integration is currently disabled by default
        if supabase_project_id is None:
            supabase_project_id = os.getenv("SUPABASE_PROJECT_ID", "xlbrcrbngyrkwtcqgmbe")
        self.supabase_db = SupabaseDB(supabase_project_id)
    
    def _migrate_schema_if_needed(self, cursor):
        """Auto-migrate old schema to new schema (rating→score, etc)"""
        try:
            # Check if old schema exists (has 'rating' column instead of 'score')
            cursor.execute("PRAGMA table_info(letter_ratings)")
            columns = {row[1]: row for row in cursor.fetchall()}
            
            if 'rating' in columns and 'score' not in columns:
                print("🔄 Migrating database schema: rating → score...")
                
                # Migrate letter_ratings table
                cursor.execute("""
                    CREATE TABLE letter_ratings_new (
                        id TEXT PRIMARY KEY,
                        submission_id TEXT NOT NULL,
                        letter_index INTEGER NOT NULL,
                        template_id TEXT NOT NULL,
                        score INTEGER CHECK(score >= 0 AND score <= 100),
                        comment TEXT,
                        created_at TEXT NOT NULL,
                        FOREIGN KEY(submission_id) REFERENCES submissions(id)
                    )
                """)
                
                # Copy data, converting rating (1-5) to score (0-100)
                cursor.execute("""
                    INSERT INTO letter_ratings_new 
                    SELECT id, submission_id, letter_index, template_id, 
                           rating * 20 as score, comment, created_at
                    FROM letter_ratings
                """)
                
                cursor.execute("DROP TABLE letter_ratings")
                cursor.execute("ALTER TABLE letter_ratings_new RENAME TO letter_ratings")
                
                # Migrate template_performance table
                cursor.execute("""
                    CREATE TABLE template_performance_new (
                        template_id TEXT PRIMARY KEY,
                        total_uses INTEGER DEFAULT 0,
                        total_ratings INTEGER DEFAULT 0,
                        avg_score REAL DEFAULT 0.0,
                        last_updated TEXT NOT NULL
                    )
                """)
                
                cursor.execute("""
                    INSERT INTO template_performance_new
                    SELECT template_id, total_uses, total_ratings,
                           avg_rating * 20 as avg_score, last_updated
                    FROM template_performance
                """)
                
                cursor.execute("DROP TABLE template_performance")
                cursor.execute("ALTER TABLE template_performance_new RENAME TO template_performance")
                
                print("✅ Schema migration completed successfully!")
        except Exception as e:
            print(f"ℹ️  Schema migration skipped (likely fresh DB): {e}")
    
    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS submissions (
                id TEXT PRIMARY KEY,
                user_email TEXT NOT NULL,
                status TEXT DEFAULT 'received',
                number_of_testimonials INTEGER,
                raw_data TEXT,
                processed_data TEXT,
                error_message TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # Feedback/ML tables (Local tables for non-vector data)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS submission_feedback (
                id TEXT PRIMARY KEY,
                submission_id TEXT NOT NULL,
                overall_score INTEGER CHECK(overall_score >= 0 AND overall_score <= 100),
                feedback_text TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(submission_id) REFERENCES submissions(id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS template_performance (
                template_id TEXT PRIMARY KEY,
                total_uses INTEGER DEFAULT 0,
                total_ratings INTEGER DEFAULT 0,
                avg_score REAL DEFAULT 0.0,
                last_updated TEXT NOT NULL
            )
        """)
        
        # letter_ratings and letter_embeddings are now in Supabase Vector DB.
        # We keep the local tables for backward compatibility and to avoid breaking 
        # the schema migration logic, but the new methods will use Supabase.
        # I will remove the creation of these tables to ensure they are not used.
        # However, since the migration logic relies on them, I will keep the migration logic
        # but remove the table creation here.
        # I will remove the creation of letter_ratings and letter_embeddings tables.
        # The migration logic will be updated to handle the new Supabase-first approach.
        # For now, I will just remove the table creation to avoid confusion.
        pass
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ml_insights (
                id TEXT PRIMARY KEY,
                insight_type TEXT NOT NULL,
                content TEXT NOT NULL,
                confidence REAL DEFAULT 1.0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # Run migration if needed (converts old rating schema to new score schema)
        self._migrate_schema_if_needed(cursor)
        
        conn.commit()
        conn.close()
    
    def create_submission(self, email: str, num_testimonials: int) -> Dict:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        submission_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        cursor.execute("""
            INSERT INTO submissions 
            (id, user_email, number_of_testimonials, status, created_at, updated_at)
            VALUES (?, ?, ?, 'received', ?, ?)
        """, (submission_id, email, num_testimonials, now, now))
        
        conn.commit()
        conn.close()
        
        return {
            "id": submission_id,
            "user_email": email,
            "number_of_testimonials": num_testimonials,
            "status": "received",
            "created_at": now,
            "updated_at": now
        }
    
    def get_submission(self, submission_id: str) -> Optional[Dict]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM submissions WHERE id = ?", (submission_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def update_submission_status(
        self, 
        submission_id: str, 
        status: str, 
        error_message: Optional[str] = None
    ):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.utcnow().isoformat()
        
        if error_message:
            cursor.execute("""
                UPDATE submissions 
                SET status = ?, error_message = ?, updated_at = ?
                WHERE id = ?
            """, (status, error_message, now, submission_id))
        else:
            cursor.execute("""
                UPDATE submissions 
                SET status = ?, updated_at = ?
                WHERE id = ?
            """, (status, now, submission_id))
        
        conn.commit()
        conn.close()
    
    def save_processed_data(self, submission_id: str, processed_data: Dict):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.utcnow().isoformat()
        
        cursor.execute("""
            UPDATE submissions 
            SET processed_data = ?, updated_at = ?
            WHERE id = ?
        """, (json.dumps(processed_data), now, submission_id))
        
        conn.commit()
        conn.close()
    
    def get_user_submissions(self, email: str) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM submissions WHERE user_email = ? ORDER BY created_at DESC",
            (email,)
        )
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    # Feedback and ML methods
    def save_letter_score(
        self,
        submission_id: str,
        letter_index: int,
        template_id: str,
        score: int,
        comment: Optional[str] = None
    ) -> str:
        """Save score (0-100) for a specific letter and update template performance"""
        # 1. Save score to Supabase Vector DB
        self.supabase_db.save_letter_score(submission_id, letter_index, template_id, score, comment)
        
        # 2. Update local template performance (this logic remains local)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        rating_id = str(uuid.uuid4()) # Keep for return value, though not used for local storage
        now = datetime.utcnow().isoformat()
        
        # Update template performance
        self._update_template_performance(cursor, template_id, score, now)
        
        conn.commit()
        conn.close()
        
        return rating_id
    
    def _update_template_performance(self, cursor, template_id: str, score: int, now: str):
        """Update template performance metrics with score 0-100"""
        # Check if template exists
        cursor.execute("SELECT * FROM template_performance WHERE template_id = ?", (template_id,))
        exists = cursor.fetchone()
        
        if not exists:
            # Create new record
            cursor.execute("""
                INSERT INTO template_performance
                (template_id, total_uses, total_ratings, avg_score, last_updated)
                VALUES (?, 0, 0, 0.0, ?)
            """, (template_id, now))
        
        # Get current stats
        cursor.execute("SELECT total_ratings, avg_score FROM template_performance WHERE template_id = ?", (template_id,))
        row = cursor.fetchone()
        
        total_ratings = row[0] + 1
        current_total = row[1] * row[0]  # avg_score * total_ratings
        new_avg = (current_total + score) / total_ratings
        
        cursor.execute("""
            UPDATE template_performance
            SET total_ratings = ?,
                avg_score = ?,
                last_updated = ?
            WHERE template_id = ?
        """, (total_ratings, new_avg, now, template_id))
    
    def get_letter_ratings(self, submission_id: str) -> List[Dict]:
        """Get all ratings for a submission"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM letter_ratings WHERE submission_id = ? ORDER BY letter_index",
            (submission_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_template_analytics(self) -> List[Dict]:
        """Get performance analytics for all templates"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM template_performance ORDER BY avg_score DESC")
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def save_submission_feedback(
        self,
        submission_id: str,
        overall_score: int,
        feedback_text: Optional[str] = None
    ) -> str:
        """Save overall feedback for entire submission"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        feedback_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        cursor.execute("""
            INSERT INTO submission_feedback
            (id, submission_id, overall_score, feedback_text, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (feedback_id, submission_id, overall_score, feedback_text, now))
        
        conn.commit()
        conn.close()
        
        return feedback_id
    
    def get_submission_feedback(self, submission_id: str) -> Optional[Dict]:
        """Get overall feedback for a submission"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM submission_feedback WHERE submission_id = ? ORDER BY created_at DESC LIMIT 1",
            (submission_id,)
        )
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def increment_template_usage(self, template_id: str):
        """Increment usage count when a template is used"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.utcnow().isoformat()
        
        # Check if exists
        cursor.execute("SELECT * FROM template_performance WHERE template_id = ?", (template_id,))
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute("""
                INSERT INTO template_performance
                (template_id, total_uses, total_ratings, avg_score, last_updated)
                VALUES (?, 1, 0, 0.0, ?)
            """, (template_id, now))
        else:
            cursor.execute("""
                UPDATE template_performance
                SET total_uses = total_uses + 1,
                    last_updated = ?
                WHERE template_id = ?
            """, (now, template_id))
        
        conn.commit()
        conn.close()
    
    def save_letter_embedding(
        self,
        submission_id: str,
        letter_index: int,
        embedding: List[float],
        cluster_id: Optional[int] = None
    ):
        """Save letter embedding for ML/clustering in Supabase Vector DB"""
        self.supabase_db.save_letter_embedding(submission_id, letter_index, embedding, cluster_id)
    
    def get_all_embeddings(self) -> List[Dict]:
        """Get all letter embeddings and their associated scores for ML training from Supabase Vector DB"""
        return self.supabase_db.get_all_embeddings()
    
    def update_cluster_assignments(self, embedding_updates: List[tuple]):
        """
        Bulk update cluster assignments
        
        Args:
            embedding_updates: List of (embedding_id, cluster_id) tuples
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for embedding_id, cluster_id in embedding_updates:
            cursor.execute("""
                UPDATE letter_embeddings
                SET cluster_id = ?
                WHERE id = ?
            """, (cluster_id, embedding_id))
        
        conn.commit()
        conn.close()
    
    def save_ml_insight(self, insight_type: str, content: dict, confidence: float = 1.0) -> str:
        """
        Save ML-generated insight
        
        Args:
            insight_type: 'feedback_pattern', 'cluster_profile', 'template_recommendation', etc
            content: Dictionary with insight data
            confidence: Confidence score (0-1)
        """
        import json
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        insight_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        content_json = json.dumps(content)
        
        cursor.execute("""
            INSERT INTO ml_insights
            (id, insight_type, content, confidence, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (insight_id, insight_type, content_json, confidence, now, now))
        
        conn.commit()
        conn.close()
        
        return insight_id
    
    def get_ml_insights(self, insight_type: Optional[str] = None) -> List[Dict]:
        """Get ML insights, optionally filtered by type"""
        import json
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if insight_type:
            cursor.execute(
                "SELECT * FROM ml_insights WHERE insight_type = ? ORDER BY created_at DESC",
                (insight_type,)
            )
        else:
            cursor.execute("SELECT * FROM ml_insights ORDER BY created_at DESC")
        
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            data = dict(row)
            data['content'] = json.loads(data['content'])
            results.append(data)
        
        return results
    
    def get_all_letter_ratings(self) -> List[Dict]:
        """Get all letter ratings for ML training from Supabase Vector DB"""
        return self.supabase_db.get_all_letter_ratings()

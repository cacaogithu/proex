import sqlite3
import json
import os
from datetime import datetime
import uuid
from typing import Optional, Dict, List


class Database:
    def __init__(self, db_path="proex.db"):
        self.db_path = db_path
        db_dir = os.path.dirname(self.db_path)
        if db_dir:  # Only create directory if path has a directory component
            os.makedirs(db_dir, exist_ok=True)
        self.init_db()
    
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
        
        # Feedback/ML tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS letter_ratings (
                id TEXT PRIMARY KEY,
                submission_id TEXT NOT NULL,
                letter_index INTEGER NOT NULL,
                template_id TEXT NOT NULL,
                rating INTEGER CHECK(rating >= 1 AND rating <= 5),
                comment TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(submission_id) REFERENCES submissions(id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS template_performance (
                template_id TEXT PRIMARY KEY,
                total_uses INTEGER DEFAULT 0,
                total_ratings INTEGER DEFAULT 0,
                avg_rating REAL DEFAULT 0.0,
                rating_5_count INTEGER DEFAULT 0,
                rating_4_count INTEGER DEFAULT 0,
                rating_3_count INTEGER DEFAULT 0,
                rating_2_count INTEGER DEFAULT 0,
                rating_1_count INTEGER DEFAULT 0,
                last_updated TEXT NOT NULL
            )
        """)
        
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
    def save_letter_rating(
        self,
        submission_id: str,
        letter_index: int,
        template_id: str,
        rating: int,
        comment: Optional[str] = None
    ) -> str:
        """Save rating for a specific letter and update template performance"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        rating_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        # Save rating
        cursor.execute("""
            INSERT INTO letter_ratings
            (id, submission_id, letter_index, template_id, rating, comment, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (rating_id, submission_id, letter_index, template_id, rating, comment, now))
        
        # Update template performance
        self._update_template_performance(cursor, template_id, rating, now)
        
        conn.commit()
        conn.close()
        
        return rating_id
    
    def _update_template_performance(self, cursor, template_id: str, rating: int, now: str):
        """Update template performance metrics"""
        # Check if template exists
        cursor.execute("SELECT * FROM template_performance WHERE template_id = ?", (template_id,))
        exists = cursor.fetchone()
        
        if not exists:
            # Create new record
            cursor.execute("""
                INSERT INTO template_performance
                (template_id, total_uses, total_ratings, avg_rating, 
                 rating_5_count, rating_4_count, rating_3_count, rating_2_count, rating_1_count, last_updated)
                VALUES (?, 0, 0, 0.0, 0, 0, 0, 0, 0, ?)
            """, (template_id, now))
        
        # Get current stats
        cursor.execute("SELECT * FROM template_performance WHERE template_id = ?", (template_id,))
        row = cursor.fetchone()
        
        total_ratings = row[2] + 1
        current_total = row[1] * row[2]  # total_uses * avg_rating
        new_avg = (current_total + rating) / total_ratings
        
        # Update counts
        rating_field = f"rating_{rating}_count"
        cursor.execute(f"""
            UPDATE template_performance
            SET total_ratings = ?,
                avg_rating = ?,
                {rating_field} = {rating_field} + 1,
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
        
        cursor.execute("SELECT * FROM template_performance ORDER BY avg_rating DESC")
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
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
                (template_id, total_uses, total_ratings, avg_rating,
                 rating_5_count, rating_4_count, rating_3_count, rating_2_count, rating_1_count, last_updated)
                VALUES (?, 1, 0, 0.0, 0, 0, 0, 0, 0, ?)
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

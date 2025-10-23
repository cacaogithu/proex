import sqlite3
import json
import os
from datetime import datetime
import uuid
from typing import Optional, Dict, List


class Database:
    def __init__(self, db_path="backend/proex.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
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

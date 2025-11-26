import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
import threading
import queue

class ProgressTracker:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._events: Dict[str, List[Dict]] = defaultdict(list)
        self._subscribers: Dict[str, List[Tuple[asyncio.AbstractEventLoop, asyncio.Queue]]] = defaultdict(list)
        self._current_step: Dict[str, Dict] = {}
        self._completed: Dict[str, bool] = {}
        self._lock = threading.Lock()
        self._max_events_per_submission = 500
    
    def emit_event(self, submission_id: str, event_type: str, data: Dict[str, Any]):
        """Emit a progress event for a submission (thread-safe)"""
        event = {
            "type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        
        with self._lock:
            if len(self._events[submission_id]) < self._max_events_per_submission:
                self._events[submission_id].append(event)
            self._current_step[submission_id] = event
            
            if event_type == "completion":
                self._completed[submission_id] = True
            
            if submission_id in self._subscribers:
                for loop, q in self._subscribers[submission_id]:
                    try:
                        loop.call_soon_threadsafe(q.put_nowait, event)
                    except (asyncio.QueueFull, RuntimeError):
                        pass
        
        print(f"[Progress] {submission_id}: {event_type} - {data.get('message', '')}")
    
    def phase_start(self, submission_id: str, phase: str, message: str, total_steps: int = 0):
        """Mark the start of a processing phase"""
        self.emit_event(submission_id, "phase_start", {
            "phase": phase,
            "message": message,
            "total_steps": total_steps,
            "current_step": 0
        })
    
    def phase_progress(self, submission_id: str, phase: str, message: str, current_step: int, total_steps: int, details: Optional[Dict] = None):
        """Update progress within a phase"""
        data = {
            "phase": phase,
            "message": message,
            "current_step": current_step,
            "total_steps": total_steps,
            "percentage": round((current_step / total_steps) * 100) if total_steps > 0 else 0
        }
        if details:
            data["details"] = details
        self.emit_event(submission_id, "phase_progress", data)
    
    def phase_complete(self, submission_id: str, phase: str, message: str):
        """Mark a phase as complete"""
        self.emit_event(submission_id, "phase_complete", {
            "phase": phase,
            "message": message
        })
    
    def letter_start(self, submission_id: str, letter_index: int, recommender_name: str, total_letters: int):
        """Mark the start of letter generation"""
        self.emit_event(submission_id, "letter_start", {
            "letter_index": letter_index,
            "recommender_name": recommender_name,
            "total_letters": total_letters,
            "message": f"Iniciando carta {letter_index + 1}/{total_letters}: {recommender_name}"
        })
    
    def letter_step(self, submission_id: str, letter_index: int, recommender_name: str, step: str, message: str):
        """Update progress within letter generation"""
        self.emit_event(submission_id, "letter_step", {
            "letter_index": letter_index,
            "recommender_name": recommender_name,
            "step": step,
            "message": message
        })
    
    def letter_complete(self, submission_id: str, letter_index: int, recommender_name: str, has_logo: bool):
        """Mark a letter as complete"""
        self.emit_event(submission_id, "letter_complete", {
            "letter_index": letter_index,
            "recommender_name": recommender_name,
            "has_logo": has_logo,
            "message": f"Carta {letter_index + 1} concluída: {recommender_name}"
        })
    
    def logo_search(self, submission_id: str, company_name: str, status: str, source: Optional[str] = None):
        """Track logo search progress"""
        self.emit_event(submission_id, "logo_search", {
            "company_name": company_name,
            "status": status,
            "source": source,
            "message": f"Logo {company_name}: {status}" + (f" via {source}" if source else "")
        })
    
    def block_generation(self, submission_id: str, letter_index: int, block_number: int, total_blocks: int, block_name: str):
        """Track block generation progress"""
        self.emit_event(submission_id, "block_generation", {
            "letter_index": letter_index,
            "block_number": block_number,
            "total_blocks": total_blocks,
            "block_name": block_name,
            "message": f"Gerando bloco {block_number}/{total_blocks}: {block_name}"
        })
    
    def completion(self, submission_id: str, success: bool, total_letters: int, successful_letters: int, message: str):
        """Mark processing as complete"""
        self.emit_event(submission_id, "completion", {
            "success": success,
            "total_letters": total_letters,
            "successful_letters": successful_letters,
            "message": message
        })
    
    def error(self, submission_id: str, phase: str, message: str, details: Optional[str] = None):
        """Emit an error event"""
        self.emit_event(submission_id, "error", {
            "phase": phase,
            "message": message,
            "details": details
        })
    
    def get_events(self, submission_id: str) -> List[Dict]:
        """Get all events for a submission"""
        with self._lock:
            return list(self._events.get(submission_id, []))
    
    def get_current_step(self, submission_id: str) -> Optional[Dict]:
        """Get current step for a submission"""
        with self._lock:
            return self._current_step.get(submission_id)
    
    def is_completed(self, submission_id: str) -> bool:
        """Check if submission processing is completed"""
        with self._lock:
            return self._completed.get(submission_id, False)
    
    async def subscribe(self, submission_id: str) -> asyncio.Queue:
        """Subscribe to events for a submission (captures event loop for thread-safe dispatch)"""
        loop = asyncio.get_running_loop()
        q = asyncio.Queue(maxsize=100)
        with self._lock:
            self._subscribers[submission_id].append((loop, q))
        return q
    
    def unsubscribe(self, submission_id: str, queue: asyncio.Queue):
        """Unsubscribe from events and cleanup if no subscribers remain"""
        with self._lock:
            if submission_id in self._subscribers:
                self._subscribers[submission_id] = [
                    (loop, q) for loop, q in self._subscribers[submission_id] 
                    if q is not queue
                ]
                if not self._subscribers[submission_id] and self._completed.get(submission_id, False):
                    self._cleanup_submission(submission_id)
    
    def _cleanup_submission(self, submission_id: str):
        """Internal cleanup after submission is complete and all subscribers disconnected"""
        if submission_id in self._events:
            del self._events[submission_id]
        if submission_id in self._current_step:
            del self._current_step[submission_id]
        if submission_id in self._completed:
            del self._completed[submission_id]
        if submission_id in self._subscribers:
            del self._subscribers[submission_id]
    
    def clear_events(self, submission_id: str):
        """Clear all events for a submission (called after completion)"""
        with self._lock:
            self._cleanup_submission(submission_id)

progress_tracker = ProgressTracker()

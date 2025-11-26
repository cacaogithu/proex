from fastapi import APIRouter, Request, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from ..core.progress_tracker import progress_tracker
from ..db.database import Database
from .auth import get_current_user
import asyncio
import json
import jwt
import os

router = APIRouter()
db = Database()

SECRET_KEY = os.getenv("SECRET_KEY", "proex_secret_key_change_me_in_prod")
ALGORITHM = "HS256"

def verify_token_and_ownership(token: str, submission_id: str) -> bool:
    """Verify JWT token and check if user owns the submission"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            return False
        
        submission = db.get_submission(submission_id)
        if not submission:
            return False
        
        return submission.get('user_email') == email
    except jwt.PyJWTError:
        return False

@router.get("/progress/{submission_id}")
async def get_progress_events(submission_id: str, current_user: dict = Depends(get_current_user)):
    """Get all progress events for a submission"""
    submission = db.get_submission(submission_id)
    if not submission or submission.get('user_email') != current_user['email']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    events = progress_tracker.get_events(submission_id)
    current = progress_tracker.get_current_step(submission_id)
    return {
        "events": events,
        "current_step": current,
        "total_events": len(events)
    }

@router.get("/progress/{submission_id}/stream")
async def stream_progress(submission_id: str, request: Request, token: str = Query(...)):
    """Server-Sent Events endpoint for real-time progress updates (token auth via query param)"""
    
    if not verify_token_and_ownership(token, submission_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    if progress_tracker.is_completed(submission_id):
        async def completed_generator():
            existing_events = progress_tracker.get_events(submission_id)
            for event in existing_events:
                yield f"data: {json.dumps(event)}\n\n"
        
        return StreamingResponse(
            completed_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    
    async def event_generator():
        queue = await progress_tracker.subscribe(submission_id)
        
        try:
            existing_events = progress_tracker.get_events(submission_id)
            for event in existing_events:
                yield f"data: {json.dumps(event)}\n\n"
            
            while True:
                if await request.is_disconnected():
                    break
                
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(event)}\n\n"
                    
                    if event.get("type") == "completion":
                        break
                        
                except asyncio.TimeoutError:
                    yield f": keepalive\n\n"
                    
        finally:
            progress_tracker.unsubscribe(submission_id, queue)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.get("/progress/{submission_id}/current")
async def get_current_progress(submission_id: str, current_user: dict = Depends(get_current_user)):
    """Get current progress step for a submission"""
    submission = db.get_submission(submission_id)
    if not submission or submission.get('user_email') != current_user['email']:
        raise HTTPException(status_code=403, detail="Access denied")
    
    current = progress_tracker.get_current_step(submission_id)
    return {"current_step": current}

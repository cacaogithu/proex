from fastapi import APIRouter, Request, Depends
from fastapi.responses import StreamingResponse
from ..core.progress_tracker import progress_tracker
from .auth import get_current_user
import asyncio
import json

router = APIRouter()

@router.get("/progress/{submission_id}")
async def get_progress_events(submission_id: str, current_user: dict = Depends(get_current_user)):
    """Get all progress events for a submission"""
    events = progress_tracker.get_events(submission_id)
    current = progress_tracker.get_current_step(submission_id)
    return {
        "events": events,
        "current_step": current,
        "total_events": len(events)
    }

@router.get("/progress/{submission_id}/stream")
async def stream_progress(submission_id: str, request: Request):
    """Server-Sent Events endpoint for real-time progress updates"""
    
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
    current = progress_tracker.get_current_step(submission_id)
    return {"current_step": current}

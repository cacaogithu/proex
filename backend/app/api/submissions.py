from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from typing import List, Optional
import shutil
import os
import zipfile
import json
from io import BytesIO
from ..core.processor import SubmissionProcessor
from ..db.database import Database

router = APIRouter()
db = Database()


@router.post("/submissions")
async def create_submission(
    background_tasks: BackgroundTasks,
    email: str = Form(...),
    numberOfTestimonials: int = Form(...),
    quadro: UploadFile = File(...),
    cv: UploadFile = File(...),
    testimonials: List[UploadFile] = File(...),
    estrategia: Optional[UploadFile] = File(None),
    onenote: Optional[UploadFile] = File(None)
):
    submission = db.create_submission(email, numberOfTestimonials)
    submission_id = submission['id']
    
    upload_dir = f"storage/uploads/{submission_id}"
    os.makedirs(upload_dir, exist_ok=True)
    
    with open(f"{upload_dir}/quadro.pdf", "wb") as f:
        shutil.copyfileobj(quadro.file, f)
    
    with open(f"{upload_dir}/cv.pdf", "wb") as f:
        shutil.copyfileobj(cv.file, f)
    
    if estrategia:
        with open(f"{upload_dir}/estrategia.pdf", "wb") as f:
            shutil.copyfileobj(estrategia.file, f)
    
    if onenote:
        with open(f"{upload_dir}/onenote.pdf", "wb") as f:
            shutil.copyfileobj(onenote.file, f)
    
    for i, testimonial in enumerate(testimonials):
        with open(f"{upload_dir}/testimonial_{i}.pdf", "wb") as f:
            shutil.copyfileobj(testimonial.file, f)
    
    processor = SubmissionProcessor()
    background_tasks.add_task(processor.process_submission, submission_id)
    
    return {
        "submission_id": submission_id,
        "status": "received",
        "message": "Processamento iniciado. Você receberá um email quando concluído."
    }


@router.get("/submissions/{submission_id}")
async def get_submission(submission_id: str):
    submission = db.get_submission(submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission não encontrada")
    
    # Add list of generated files if completed
    if submission['status'] == 'completed':
        output_dir = f"storage/outputs/{submission_id}"
        if os.path.exists(output_dir):
            files = [
                f for f in os.listdir(output_dir) 
                if f.endswith('.docx') or f.endswith('.pdf')
            ]
            submission['files'] = sorted(files)
        else:
            submission['files'] = []
    
    return submission


@router.get("/submissions")
async def list_submissions(email: Optional[str] = None):
    if email:
        submissions = db.get_user_submissions(email)
    else:
        submissions = []
    return submissions


@router.get("/files/{submission_id}/{filename}")
async def get_file(submission_id: str, filename: str):
    submission = db.get_submission(submission_id)
    
    if not submission:
        raise HTTPException(status_code=404, detail="Submission não encontrada")
    
    file_path = f"storage/outputs/{submission_id}/{filename}"
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    
    if not (filename.endswith('.pdf') or filename.endswith('.docx')):
        raise HTTPException(status_code=400, detail="Tipo de arquivo inválido")
    
    media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document" if filename.endswith('.docx') else "application/pdf"
    
    return FileResponse(
        file_path,
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/submissions/{submission_id}/download")
async def download_results(submission_id: str):
    submission = db.get_submission(submission_id)
    
    if not submission:
        raise HTTPException(status_code=404, detail="Submission não encontrada")
    
    if submission['status'] != 'completed':
        raise HTTPException(
            status_code=400, 
            detail=f"Processamento ainda não completo. Status: {submission['status']}"
        )
    
    output_dir = f"storage/outputs/{submission_id}"
    
    if not os.path.exists(output_dir):
        raise HTTPException(status_code=404, detail="Arquivos não encontrados")
    
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for filename in os.listdir(output_dir):
            if filename.endswith('.pdf') or filename.endswith('.html') or filename.endswith('.docx'):
                file_path = os.path.join(output_dir, filename)
                zip_file.write(file_path, arcname=filename)
    
    zip_buffer.seek(0)
    
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename=cartas_{submission_id}.zip"
        }
    )

# Feedback and ML endpoints
from pydantic import BaseModel

class LetterRating(BaseModel):
    rating: int
    comment: Optional[str] = None

@router.post("/submissions/{submission_id}/letters/{letter_index}/rating")
async def rate_letter(
    submission_id: str,
    letter_index: int,
    rating_data: LetterRating
):
    """Save rating for a specific letter"""
    submission = db.get_submission(submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission não encontrada")
    
    # Get letter info to get template_id
    processed_data = json.loads(submission.get('processed_data', '{}'))
    letters = processed_data.get('letters', [])
    
    if letter_index >= len(letters):
        raise HTTPException(status_code=404, detail="Carta não encontrada")
    
    template_id = letters[letter_index].get('template_id', 'A')
    
    rating_id = db.save_letter_rating(
        submission_id,
        letter_index,
        template_id,
        rating_data.rating,
        rating_data.comment
    )
    
    return {
        "rating_id": rating_id,
        "message": "Rating salvo com sucesso",
        "template_id": template_id
    }


@router.get("/submissions/{submission_id}/ratings")
async def get_ratings(submission_id: str):
    """Get all ratings for a submission"""
    submission = db.get_submission(submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission não encontrada")
    
    ratings = db.get_letter_ratings(submission_id)
    return {"ratings": ratings}


@router.get("/analytics/templates")
async def get_template_analytics():
    """Get performance analytics for all templates"""
    analytics = db.get_template_analytics()
    
    # Add template names
    template_names = {
        'A': 'Technical Deep-Dive',
        'B': 'Case Study Acadêmico',
        'C': 'Narrative Storytelling',
        'D': 'Business Partnership',
        'E': 'USA Support Letter',
        'F': 'Technical Testimony'
    }
    
    for item in analytics:
        item['template_name'] = template_names.get(item['template_id'], item['template_id'])
    
    return {"analytics": analytics}


class RegenerateRequest(BaseModel):
    letter_indices: List[int]
    instructions: Optional[str] = None

@router.post("/submissions/{submission_id}/regenerate")
async def regenerate_letters(
    submission_id: str,
    regenerate_request: RegenerateRequest,
    background_tasks: BackgroundTasks
):
    """Regenerate specific letters with optional custom instructions"""
    submission = db.get_submission(submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission não encontrada")
    
    if submission['status'] != 'completed':
        raise HTTPException(
            status_code=400,
            detail="Só é possível regenerar cartas de submissões completadas"
        )
    
    processed_data = json.loads(submission.get('processed_data', '{}'))
    letters = processed_data.get('letters', [])
    
    # Validate indices
    for idx in regenerate_request.letter_indices:
        if idx >= len(letters):
            raise HTTPException(
                status_code=400,
                detail=f"Índice inválido: {idx}. Total de cartas: {len(letters)}"
            )
    
    # TODO: Implement selective regeneration logic
    # For now, return placeholder
    return {
        "message": f"Regeneração iniciada para {len(regenerate_request.letter_indices)} carta(s)",
        "letter_indices": regenerate_request.letter_indices,
        "status": "processing"
    }

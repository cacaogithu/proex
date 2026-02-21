# ProEx NIW Letter Platform

## Overview
ProEx NIW Letter Platform processes immigration document packages and generates structured EB-2 NIW recommendation letters.

## Problem
Manual recommendation-letter drafting from mixed source documents is slow, inconsistent, and hard to scale.

## Solution
The platform extracts uploaded content, applies LLM-assisted structuring, builds standardized letter blocks, and exports final deliverables.

## Architecture
- `backend/`: FastAPI services for ingestion, processing, orchestration, and PDF generation.
- `frontend/`: React UI for uploads, tracking, and downloads.
- `docs/`: technical and operational documentation.
- `attached_assets/`: sample/support artifacts.

## Tech Stack
- Python 3.11 + FastAPI
- React + TypeScript + Vite
- SQLite (local workflow data)
- PDF tooling (`pdfplumber`, `weasyprint`, `python-docx`)

## Setup
1. Backend deps: `uv sync`
2. Frontend deps: `cd frontend && npm install`
3. Configure env: `cp .env.example .env`
4. Run backend: `uv run uvicorn backend.app.main:app --reload`
5. Run frontend: `cd frontend && npm run dev`

## Results
- Reduced drafting turnaround for NIW package outputs.
- More consistent letter structure across submissions.
- Repeatable export pipeline for client delivery.

## Screenshots
Add workflow screenshots under `docs/screenshots/` and link here.

## Tradeoffs
- Quality depends on source-document quality and extraction accuracy.
- LLM output still requires legal/editorial review before final submission.

## Additional Docs
Historical audits and implementation notes are in `docs/archive/`.

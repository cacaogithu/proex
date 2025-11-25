
# ProEx Platform - Visual Architecture Diagrams

## System Context Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              EXTERNAL WORLD                             │
│                                                                         │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐            │
│  │ Clearbit │   │ OpenAI   │   │  Gmail   │   │  Google  │            │
│  │   API    │   │  (Embed) │   │   API    │   │  Drive   │            │
│  └────┬─────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘            │
│       │              │              │              │                   │
└───────┼──────────────┼──────────────┼──────────────┼───────────────────┘
        │              │              │              │
        │              │              │              │
┌───────┼──────────────┼──────────────┼──────────────┼───────────────────┐
│       │              │              │              │                   │
│       │         PROEX PLATFORM      │              │                   │
│       │                             │              │                   │
│  ┌────▼────────────────────────────▼──────────────▼────┐              │
│  │          BACKEND API (FastAPI - Port 8000)          │              │
│  │  ┌────────────┐  ┌──────────────┐  ┌────────────┐  │              │
│  │  │ Auth       │  │ Submissions  │  │ Background │  │              │
│  │  │ Service    │  │ Service      │  │ Processor  │  │              │
│  │  └────────────┘  └──────────────┘  └────────────┘  │              │
│  └──────────────────────────┬──────────────────────────┘              │
│                             │                                         │
│  ┌──────────────────────────▼──────────────────────────┐              │
│  │          EMAIL SERVICE (Node.js - Port 3001)        │              │
│  │  ┌────────────────────────────────────────────────┐ │              │
│  │  │  Gmail OAuth + Google Drive Upload             │ │              │
│  │  └────────────────────────────────────────────────┘ │              │
│  └─────────────────────────────────────────────────────┘              │
│                                                                        │
│  ┌──────────────────────────────────────────────────────┐             │
│  │          FRONTEND (React + Vite - Port 5000)         │             │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │             │
│  │  │  Login   │  │ Upload   │  │  Status/Download │   │             │
│  │  └──────────┘  └──────────┘  └──────────────────┘   │             │
│  └──────────────────────────────────────────────────────┘             │
│         ▲                                                              │
└─────────┼──────────────────────────────────────────────────────────────┘
          │
     ┌────▼─────┐
     │   USER   │
     └──────────┘
```

---

## Processing Pipeline - Detailed Flow

```
USER UPLOADS FILES
       │
       ▼
┌──────────────────────────────────────────────────────────────────┐
│ INGESTION LAYER                                                  │
│                                                                  │
│  5-9 PDF Files → FastAPI Upload Endpoint                        │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ Storage: backend/storage/uploads/{submission_id}/      │     │
│  └────────────────────────────────────────────────────────┘     │
└──────────────────┬───────────────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────────────┐
│ EXTRACTION LAYER (Phase 1: 10-15s)                              │
│                                                                  │
│  ┌───────────────────────────────────────────────────────┐      │
│  │ PDF Extractor (pdfplumber)                            │      │
│  │  • Parse each PDF → raw text                          │      │
│  │  • Detect encoding (UTF-8)                            │      │
│  │  • Count pages & words                                │      │
│  └──────────────────┬────────────────────────────────────┘      │
│                     │                                            │
│                     ▼                                            │
│  ┌───────────────────────────────────────────────────────┐      │
│  │ Document Categorizer (Gemini Flash)                   │      │
│  │  • Classify: testimony/petitioner/onet/strategy       │      │
│  │  • Extract key metadata                               │      │
│  └──────────────────┬────────────────────────────────────┘      │
│                     │                                            │
│                     ▼                                            │
│  ┌───────────────────────────────────────────────────────┐      │
│  │ Output: extracted_texts Dict                          │      │
│  │ {                                                      │      │
│  │   "testimonials": [text1, text2, ...],                │      │
│  │   "petitioner": text,                                 │      │
│  │   "onet": text,                                       │      │
│  │   "strategy": text                                    │      │
│  │ }                                                      │      │
│  └──────────────────┬────────────────────────────────────┘      │
└───────────────────────┼──────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────────────┐
│ ORGANIZATION LAYER (Phase 2: 15-20s)                            │
│                                                                  │
│  ┌───────────────────────────────────────────────────────┐      │
│  │ LLM Processor (Gemini Flash)                          │      │
│  │  • Clean & normalize text                             │      │
│  │  • Extract structured fields                          │      │
│  │  • Validate completeness                              │      │
│  └──────────────────┬────────────────────────────────────┘      │
│                     │                                            │
│                     ▼                                            │
│  ┌───────────────────────────────────────────────────────┐      │
│  │ Output: organized_data Dict                           │      │
│  │ {                                                      │      │
│  │   "petitioner": {                                      │      │
│  │     "name": "John Doe",                               │      │
│  │     "education": [...],                               │      │
│  │     "experience": [...]                               │      │
│  │   },                                                   │      │
│  │   "testimonies": [                                     │      │
│  │     {                                                  │      │
│  │       "testimony_id": "T1",                           │      │
│  │       "recommender_name": "Jane Smith",               │      │
│  │       "recommender_company": "ACME Corp",             │      │
│  │       "recommender_role": "Director",                 │      │
│  │       "testimony_text": "...",                        │      │
│  │       "key_achievements": [...]                       │      │
│  │     }, ...                                             │      │
│  │   ],                                                   │      │
│  │   "onet": {...},                                       │      │
│  │   "strategy": {...}                                    │      │
│  │ }                                                      │      │
│  └──────────────────┬────────────────────────────────────┘      │
└───────────────────────┼──────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────────────┐
│ DESIGN LAYER (Phase 3: 20-30s)                                  │
│                                                                  │
│  ┌───────────────────────────────────────────────────────┐      │
│  │ Heterogeneity Architect (Gemini 2.5 Pro)              │      │
│  │                                                        │      │
│  │  Input: 5 testimonies                                 │      │
│  │  Process:                                              │      │
│  │   1. Analyze each testimony context                   │      │
│  │   2. Generate 23 unique parameters per testimony      │      │
│  │   3. Ensure NO duplicate combinations                 │      │
│  │   4. Validate completeness (all 23 params)            │      │
│  └──────────────────┬────────────────────────────────────┘      │
│                     │                                            │
│                     ▼                                            │
│  ┌───────────────────────────────────────────────────────┐      │
│  │ Output: design_structures Array                       │      │
│  │ [                                                      │      │
│  │   {  // Design for Testimony 1                        │      │
│  │     "assigned_recommender": "Jane Smith",             │      │
│  │     "tone_variable": "Technical Authority",           │      │
│  │     "tone_instructions": "Write as senior engineer...",│     │
│  │     "narrative_framework": "Problem-Solution-Impact", │      │
│  │     "font_primary": "Georgia, serif",                 │      │
│  │     "color_primary_hsl_range": "hsl(210,50%,30%)",    │      │
│  │     ... (23 parameters total)                         │      │
│  │   },                                                   │      │
│  │   {  // Design for Testimony 2 (DIFFERENT params)     │      │
│  │     "assigned_recommender": "Bob Johnson",            │      │
│  │     "tone_variable": "Academic Scholar",              │      │
│  │     "narrative_framework": "Chronological Journey",   │      │
│  │     ... (completely different design)                 │      │
│  │   },                                                   │      │
│  │   ... (5 total, all unique)                           │      │
│  │ ]                                                      │      │
│  └──────────────────┬────────────────────────────────────┘      │
└───────────────────────┼──────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────────────┐
│ GENERATION LAYER (Phase 4: 60-120s)                             │
│                                                                  │
│  ┌───────────────────────────────────────────────────────┐      │
│  │ ThreadPoolExecutor (10 workers)                       │      │
│  │ Process 5 letters in PARALLEL                         │      │
│  └──────────────────┬────────────────────────────────────┘      │
│                     │                                            │
│      ┌──────────────┼──────────────┐                            │
│      │              │              │                            │
│      ▼              ▼              ▼                            │
│  ┌────────┐    ┌────────┐    ┌────────┐                        │
│  │Letter 1│    │Letter 2│    │Letter 5│ ... (all parallel)     │
│  └───┬────┘    └───┬────┘    └───┬────┘                        │
│      │             │             │                              │
│      │  FOR EACH LETTER (same workflow):                        │
│      │                                                           │
│      ├─► 1. Logo Scraper                                        │
│      │      ┌────────────────────────────────┐                  │
│      │      │ Clearbit API                   │                  │
│      │      │  GET logo.clearbit.com/{domain}│                  │
│      │      │  → Save to storage/logos/      │                  │
│      │      └────────────────────────────────┘                  │
│      │                                                           │
│      ├─► 2. Block Generator (5 blocks in parallel)              │
│      │      ┌──────────────────────────────────────────┐        │
│      │      │  ThreadPoolExecutor (5 workers)          │        │
│      │      │                                           │        │
│      │      │  ┌──────┐  ┌──────┐  ┌──────┐           │        │
│      │      │  │Block1│  │Block2│  │Block3│ ...       │        │
│      │      │  └──┬───┘  └──┬───┘  └──┬───┘           │        │
│      │      │     │         │         │                │        │
│      │      │     │  Each block:                       │        │
│      │      │     │  • Calls LLM (Gemini)             │        │
│      │      │     │  • Uses design params             │        │
│      │      │     │  • Ensures word count             │        │
│      │      │     │  • Expands if needed              │        │
│      │      │     │                                    │        │
│      │      │     └──────────┬────────────────┘        │        │
│      │      │                │                         │        │
│      │      │     Output: 5 markdown blocks           │        │
│      │      │     {                                    │        │
│      │      │       "block1": "Introduction...",       │        │
│      │      │       "block2": "Context...",            │        │
│      │      │       "block3": "Technical...",          │        │
│      │      │       "block4": "Impact...",             │        │
│      │      │       "block5": "Conclusion..."          │        │
│      │      │     }                                    │        │
│      │      └──────────────────────────────────────────┘        │
│      │                                                           │
│      ├─► 3. HTML Designer                                       │
│      │      ┌──────────────────────────────────────────┐        │
│      │      │ AI-Powered HTML Generator (Gemini Pro)   │        │
│      │      │                                           │        │
│      │      │ Input:                                    │        │
│      │      │  • 5 blocks (content)                    │        │
│      │      │  • 23 design parameters                  │        │
│      │      │  • Recommender info                      │        │
│      │      │  • Logo (base64)                         │        │
│      │      │                                           │        │
│      │      │ Process:                                  │        │
│      │      │  • Interpret design params               │        │
│      │      │  • Generate custom HTML+CSS              │        │
│      │      │  • Embed logo as data URI                │        │
│      │      │  • Format for print (8.5x11)             │        │
│      │      │                                           │        │
│      │      │ Output: Complete HTML document           │        │
│      │      │  <!DOCTYPE html>                         │        │
│      │      │  <html>                                  │        │
│      │      │    <head>                                │        │
│      │      │      <style>/* Custom CSS */</style>     │        │
│      │      │    </head>                               │        │
│      │      │    <body>                                │        │
│      │      │      <div class="header">                │        │
│      │      │        <img src="data:image/...">        │        │
│      │      │      </div>                              │        │
│      │      │      <!-- 5 blocks formatted -->         │        │
│      │      │      <div class="signature">             │        │
│      │      │      </div>                              │        │
│      │      │    </body>                               │        │
│      │      │  </html>                                 │        │
│      │      └──────────────────────────────────────────┘        │
│      │                                                           │
│      ├─► 4. PDF/DOCX Converter                                  │
│      │      ┌──────────────────────────────────────────┐        │
│      │      │ WeasyPrint (HTML → PDF)                  │        │
│      │      │  • CSS rendering                         │        │
│      │      │  • Page breaks                           │        │
│      │      │  • Print optimization                    │        │
│      │      │                                           │        │
│      │      │ python-docx (HTML → DOCX)                │        │
│      │      │  • Preserve formatting                   │        │
│      │      │  • Editable output                       │        │
│      │      └──────────────────────────────────────────┘        │
│      │                                                           │
│      └─► 5. Save Files                                          │
│           ┌──────────────────────────────────────────┐          │
│           │ Storage:                                 │          │
│           │  /outputs/{submission_id}/               │          │
│           │    letter_1_Jane_Smith.pdf               │          │
│           │    letter_1_Jane_Smith.docx              │          │
│           └──────────────────────────────────────────┘          │
│                                                                  │
│  All 5 letters complete → Proceed to validation                 │
└──────────────────┬───────────────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────────────┐
│ VALIDATION LAYER (Phase 5: 10-15s)                              │
│                                                                  │
│  ┌───────────────────────────────────────────────────────┐      │
│  │ Validation Engine                                     │      │
│  │  • N-gram similarity (4-grams, Jaccard)              │      │
│  │  • Forbidden phrases detection                        │      │
│  │  • Word count validation                              │      │
│  │  • Quality score calculation                          │      │
│  └──────────────────┬────────────────────────────────────┘      │
│                     │                                            │
│                     ▼                                            │
│  ┌───────────────────────────────────────────────────────┐      │
│  │ Output: validation_report                             │      │
│  │ {                                                      │      │
│  │   "average_similarity": 0.12,                         │      │
│  │   "max_similarity": 0.18,                             │      │
│  │   "forbidden_count": 2,                               │      │
│  │   "warnings": [...]                                   │      │
│  │ }                                                      │      │
│  │ (Logged, not blocking)                                │      │
│  └──────────────────┬────────────────────────────────────┘      │
└───────────────────────┼──────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────────────┐
│ DELIVERY LAYER (Phase 5 cont: 5-10s)                            │
│                                                                  │
│  ┌───────────────────────────────────────────────────────┐      │
│  │ Email Service (Node.js)                               │      │
│  │  1. Upload all PDFs+DOCXs to Google Drive            │      │
│  │  2. Generate shareable links                          │      │
│  │  3. Send email with links                             │      │
│  └──────────────────┬────────────────────────────────────┘      │
│                     │                                            │
│                     ▼                                            │
│  ┌───────────────────────────────────────────────────────┐      │
│  │ Update Database                                       │      │
│  │  • Set status = "completed"                           │      │
│  │  • Save processed_data (JSON)                         │      │
│  │  • Save validation_report                             │      │
│  └──────────────────┬────────────────────────────────────┘      │
└───────────────────────┼──────────────────────────────────────────┘
                        │
                        ▼
                   ┌────────┐
                   │  USER  │
                   │receives│
                   │  email │
                   └────────┘
```

---

## Component Interaction Diagram

```
┌───────────────────────────────────────────────────────────────────┐
│                    FRONTEND (React)                               │
└───────────────────┬───────────────────────────────────────────────┘
                    │
                    │ HTTP/REST (JWT Auth)
                    │
┌───────────────────▼───────────────────────────────────────────────┐
│                 FASTAPI BACKEND                                   │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │ API Layer (Routers)                                      │    │
│  │  • auth.py - Login/Register/Me                           │    │
│  │  • submissions.py - Upload/Status/Download               │    │
│  └────────────┬─────────────────────────────────────────────┘    │
│               │                                                   │
│  ┌────────────▼─────────────────────────────────────────────┐    │
│  │ Business Logic (Processor)                               │    │
│  │  • processor.py - Main orchestrator                      │    │
│  │  • Manages workflow execution                            │    │
│  │  • Handles parallel processing                           │    │
│  └────────────┬─────────────────────────────────────────────┘    │
│               │                                                   │
│               ├─► pdf_extractor.py                               │
│               ├─► llm_processor.py                               │
│               ├─► heterogeneity.py                               │
│               ├─► block_generator.py                             │
│               ├─► html_designer.py                               │
│               ├─► html_pdf_generator.py                          │
│               ├─► logo_scraper.py                                │
│               ├─► validation.py                                  │
│               └─► email_sender.py                                │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │ Data Layer (Database)                                    │    │
│  │  • database.py - SQLite operations                       │    │
│  │  • Tables: users, submissions, feedback                  │    │
│  └──────────────────────────────────────────────────────────┘    │
└───────────────────────────────────────────────────────────────────┘
                    │
         ┌──────────┼──────────┐
         │          │          │
         ▼          ▼          ▼
    ┌────────┐ ┌────────┐ ┌────────┐
    │OpenRouter│Clearbit││ Email  │
    │(LLMs)  │ │ (Logo) │ │Service │
    └────────┘ └────────┘ └────────┘
```

---

## Data Storage Architecture

```
backend/storage/
│
├── uploads/                    # Temporary upload storage
│   └── {submission_id}/
│       ├── file_0.pdf         # Original testimonial
│       ├── file_1.pdf
│       ├── file_2.pdf
│       ├── file_3.pdf
│       ├── file_4.pdf
│       ├── petitioner.pdf     # Petitioner CV
│       ├── strategy.pdf       # Strategy document
│       └── onet.pdf           # O*NET data
│
├── outputs/                    # Generated letters
│   └── {submission_id}/
│       ├── letter_1_Jane_Smith.pdf
│       ├── letter_1_Jane_Smith.docx
│       ├── letter_2_Bob_Johnson.pdf
│       ├── letter_2_Bob_Johnson.docx
│       ├── letter_3_Alice_Wong.pdf
│       ├── letter_3_Alice_Wong.docx
│       ├── letter_4_Carlos_Garcia.pdf
│       ├── letter_4_Carlos_Garcia.docx
│       ├── letter_5_Maria_Silva.pdf
│       └── letter_5_Maria_Silva.docx
│
└── logos/                      # Cached company logos
    ├── apple.com.png
    ├── microsoft.com.png
    └── google.com.png

backend/storage/database/
└── proex.db                    # SQLite database
```

---

## Authentication Flow

```
┌──────┐
│ User │
└───┬──┘
    │
    │ 1. POST /api/auth/register
    │    { email, password }
    ▼
┌────────────────┐
│   Backend      │
│                │  2. Hash password (bcrypt)
│                │  3. Generate UUID
│                │  4. Save to users table
│                │
│                │  5. Generate JWT token
│                │     { sub: email, exp: 7days }
│                │
└───┬────────────┘
    │
    │ 6. Return { access_token, id, email }
    ▼
┌──────┐
│ User │  7. Store token in localStorage
└───┬──┘
    │
    │ 8. All future requests:
    │    Headers: { Authorization: Bearer {token} }
    ▼
┌────────────────┐
│   Backend      │  9. Verify JWT signature
│                │  10. Extract user_id from token
│                │  11. Proceed with request
└────────────────┘
```

---

## Error Handling Flow

```
┌─────────────────────┐
│ User Action         │
└──────────┬──────────┘
           │
           ▼
┌──────────────────────────────────────────────────┐
│ Backend Processing                               │
│                                                  │
│  Try:                                            │
│    ┌─► Extract PDFs                             │
│    ├─► Organize data                            │
│    ├─► Generate designs                         │
│    └─► Generate letters                         │
│                                                  │
│  Except Exception:                               │
│    ┌─► Log error message                        │
│    ├─► Update submission.status = "error"       │
│    ├─► Save error_message to DB                 │
│    └─► Return 500 with error details            │
│                                                  │
└──────────┬───────────────────────────────────────┘
           │
           ▼
┌──────────────────────┐
│ Frontend             │
│  • Display error     │
│  • Show retry button │
│  • Log to console    │
└──────────────────────┘
```

---

## Performance Optimization

```
BEFORE (Sequential):
─────────────────────────────────────────────────
Letter 1: Extract → Blocks → HTML → PDF (5 min)
Letter 2: Extract → Blocks → HTML → PDF (5 min)
Letter 3: Extract → Blocks → HTML → PDF (5 min)
Letter 4: Extract → Blocks → HTML → PDF (5 min)
Letter 5: Extract → Blocks → HTML → PDF (5 min)
─────────────────────────────────────────────────
Total: ~25 minutes


AFTER (Parallel):
─────────────────────────────────────────────────
Common: Extract all → Organize (30s)
        Heterogeneity design (30s)

Then parallel (ThreadPoolExecutor):
Letter 1: Blocks (parallel) → HTML → PDF ─┐
Letter 2: Blocks (parallel) → HTML → PDF  │
Letter 3: Blocks (parallel) → HTML → PDF  ├─ 2 min
Letter 4: Blocks (parallel) → HTML → PDF  │
Letter 5: Blocks (parallel) → HTML → PDF ─┘
─────────────────────────────────────────────────
Total: ~3 minutes (8× faster)
```


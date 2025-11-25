
# ProEx Platform - Architecture Document

**Version:** 1.0  
**Last Updated:** 2025-01-XX  
**Status:** Production

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Overview](#system-overview)
3. [Core Architecture](#core-architecture)
4. [Data Flow](#data-flow)
5. [Component Specifications](#component-specifications)
6. [AI/ML Pipeline](#aiml-pipeline)
7. [Database Schema](#database-schema)
8. [API Specifications](#api-specifications)
9. [Security & Authentication](#security--authentication)
10. [Deployment Architecture](#deployment-architecture)
11. [Modification Guidelines](#modification-guidelines)

---

## Executive Summary

### Purpose
ProEx is an AI-powered platform that transforms 5+ testimonial documents + strategy documents + O*NET data into 5 heterogeneous, professionally formatted PDF recommendation letters.

### Key Differentiator
**Authentic Heterogeneity** - Each letter appears written by a different person through 23-parameter design variance (tone, structure, visual style, narrative framework).

### Success Metrics
- **Quality**: Letters pass USCIS standards for EB-2 NIW applications
- **Heterogeneity**: <20% n-gram similarity between letters in same batch
- **Speed**: Full batch generation in 3-5 minutes (parallel processing)
- **User Satisfaction**: >8/10 rating from users

---

## System Overview

### Technology Stack

**Backend:**
- **Runtime**: Python 3.12
- **Framework**: FastAPI 0.115+
- **Database**: SQLite (embedded, no external DB)
- **PDF Processing**: pdfplumber, WeasyPrint
- **Document Generation**: python-docx, Jinja2

**Frontend:**
- **Framework**: React 18.3+ with TypeScript
- **Build Tool**: Vite 5.4+
- **Styling**: TailwindCSS 3.4+
- **Routing**: React Router 7.1+

**AI/ML:**
- **LLM Gateway**: OpenRouter.ai (unified API)
- **Models**: 
  - Gemini 2.5 Flash (speed tasks)
  - Gemini 2.5 Pro (quality tasks)
  - Claude 3.7 Sonnet (backup)
- **Embeddings**: OpenAI `text-embedding-3-small`
- **Vector Store**: In-memory Python (numpy-based)

**External Services:**
- **Logo Scraping**: Clearbit API
- **Email**: Gmail API (OAuth2)
- **File Sharing**: Google Drive API

---

## Core Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                          │
│                    (React + TypeScript)                         │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 │ REST API (JWT Auth)
                 │
┌────────────────▼────────────────────────────────────────────────┐
│                      FASTAPI BACKEND                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Auth Router  │  │ Submission   │  │  Background Worker   │  │
│  │              │  │   Router     │  │    (Processor)       │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                 │
    ┌────────────┼────────────┐
    │            │            │
    ▼            ▼            ▼
┌─────────┐  ┌─────────┐  ┌──────────────┐
│ SQLite  │  │ Storage │  │  AI Pipeline │
│   DB    │  │ (Files) │  │  (LLMs)      │
└─────────┘  └─────────┘  └──────────────┘
```

### Component Layers

**Layer 1: Presentation** (Frontend)
- User authentication (login/register)
- Document upload interface
- Status tracking dashboard
- Results download/email

**Layer 2: API Gateway** (FastAPI)
- Request routing
- JWT authentication
- Rate limiting
- Error handling

**Layer 3: Business Logic** (Processor)
- Document extraction
- Data organization
- Heterogeneity generation
- Letter assembly

**Layer 4: AI/ML Pipeline**
- LLM orchestration (parallel)
- Vector store (RAG)
- Quality validation
- Template selection (future)

**Layer 5: Data & Storage**
- SQLite (submissions, users, feedback)
- File system (PDFs, DOCXs)
- External APIs (email, Drive)

---

## Data Flow

### End-to-End Processing Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│ PHASE 1: INGESTION & EXTRACTION (10-15s)                           │
└─────────────────────────────────────────────────────────────────────┘
                              │
           User uploads 5-9 PDFs via frontend
                              │
                              ▼
           ┌────────────────────────────────────┐
           │  PDF Extractor (pdfplumber)        │
           │  - Extract text from each PDF      │
           │  - Detect document types           │
           │  - Categorize (testimony/strategy) │
           └────────────────┬───────────────────┘
                            │
                            ▼
           ┌────────────────────────────────────┐
           │  Extracted Texts Dictionary        │
           │  {                                 │
           │    "testimonials": [5 texts],      │
           │    "petitioner": 1 text,           │
           │    "onet": 1 text,                 │
           │    "strategy": 1 text              │
           │  }                                 │
           └────────────────┬───────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────────┐
│ PHASE 2: DATA ORGANIZATION (15-20s)                                │
└─────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
           ┌────────────────────────────────────┐
           │  LLM Processor (Gemini Flash)      │
           │  - Clean extracted texts           │
           │  - Structure into JSON             │
           │  - Extract key fields              │
           └────────────────┬───────────────────┘
                            │
                            ▼
           ┌────────────────────────────────────┐
           │  Organized Data Structure          │
           │  {                                 │
           │    "petitioner": {                 │
           │      "name": "...",                │
           │      "education": "...",           │
           │      "experience": "..."           │
           │    },                              │
           │    "testimonies": [                │
           │      {                             │
           │        "recommender_name": "...",  │
           │        "company": "...",           │
           │        "testimony_text": "...",    │
           │        "achievements": "..."       │
           │      }, ...                        │
           │    ],                              │
           │    "onet": {...},                  │
           │    "strategy": {...}               │
           │  }                                 │
           └────────────────┬───────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────────┐
│ PHASE 2.5: RAG INGESTION (Optional, 5-10s)                         │
└─────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
           ┌────────────────────────────────────┐
           │  RAG Engine (Currently Disabled)   │
           │  - Chunk uploaded documents        │
           │  - Generate embeddings             │
           │  - Store in vector DB              │
           └────────────────┬───────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────────┐
│ PHASE 3: HETEROGENEITY DESIGN (20-30s)                             │
└─────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
           ┌────────────────────────────────────┐
           │  Heterogeneity Architect           │
           │  (Gemini 2.5 Pro)                  │
           │  - Analyze 5 testimonies           │
           │  - Generate 23 unique params/each  │
           │  - Ensure no duplicates            │
           └────────────────┬───────────────────┘
                            │
                            ▼
           ┌────────────────────────────────────┐
           │  Design Structures (5x)            │
           │  [                                 │
           │    {                               │
           │      "tone_variable": "...",       │
           │      "narrative_framework": "...", │
           │      "font_primary": "...",        │
           │      "color_primary": "...",       │
           │      ... (23 parameters total)     │
           │    }, ...                          │
           │  ]                                 │
           └────────────────┬───────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────────┐
│ PHASE 4: PARALLEL LETTER GENERATION (60-120s)                      │
└─────────────────────────────────────────────────────────────────────┘
                            │
           ┌────────────────┴────────────────┐
           │ ThreadPoolExecutor (10 workers) │
           │ Process 5 letters in parallel   │
           └────────────────┬────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
   [Letter 1]          [Letter 2]          [Letter 3]...
        │                   │                   │
        │  FOR EACH LETTER (parallel):          │
        │                                       │
        ├─► 1. Logo Scraper (Clearbit)         │
        │       - Fetch company logo            │
        │                                       │
        ├─► 2. Block Generator (5 blocks)      │
        │       - Block 1: Introduction (300w)  │
        │       - Block 2: Context (300w)       │
        │       - Block 3: Technical (800w)     │
        │       - Block 4: Impact (350w)        │
        │       - Block 5: Conclusion (300w)    │
        │       [All 5 blocks in parallel]      │
        │                                       │
        ├─► 3. HTML Designer                    │
        │       - Interprets 23 params          │
        │       - Generates custom HTML+CSS     │
        │       - Embeds logo (base64)          │
        │                                       │
        ├─► 4. PDF/DOCX Converter              │
        │       - WeasyPrint (HTML→PDF)         │
        │       - python-docx (HTML→DOCX)       │
        │                                       │
        └─► 5. Return Letter Data              │
                {                               │
                  "pdf_path": "...",            │
                  "docx_path": "...",           │
                  "recommender": "...",         │
                  "blocks": {...},              │
                  "design": {...}               │
                }                               │
        │                   │                   │
        └───────────────────┴───────────────────┘
                            │
                            ▼
           ┌────────────────────────────────────┐
           │  Completed Letters (5x)            │
           │  - 5 PDFs (professionally styled)  │
           │  - 5 DOCXs (editable)              │
           │  - All heterogeneous               │
           └────────────────┬───────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────────┐
│ PHASE 5: VALIDATION & DELIVERY (10-15s)                            │
└─────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
           ┌────────────────────────────────────┐
           │  Validation Engine                 │
           │  - N-gram similarity check         │
           │  - Forbidden phrases detection     │
           │  - Quality metrics                 │
           └────────────────┬───────────────────┘
                            │
                            ▼
           ┌────────────────────────────────────┐
           │  Email & Drive Service             │
           │  - Upload to Google Drive          │
           │  - Send email with links           │
           │  - User notification               │
           └────────────────────────────────────┘
```

---

## Component Specifications

### 1. PDF Extractor (`backend/app/core/pdf_extractor.py`)

**Purpose:** Extract text from uploaded PDFs and categorize documents

**Input:** List of file paths  
**Output:** Dictionary with categorized texts

**Key Methods:**
- `extract_all_files(submission_id)` - Main orchestrator
- `extract_from_pdf(file_path)` - Single PDF extraction
- `categorize_document(text)` - LLM-based categorization

**Technologies:** `pdfplumber`, Gemini Flash

**Quality Checks:**
- Minimum 100 chars per document
- Valid UTF-8 encoding
- Page count detection

---

### 2. LLM Processor (`backend/app/core/llm_processor.py`)

**Purpose:** Clean and structure extracted data using LLMs

**Input:** Raw extracted texts  
**Output:** Structured JSON (organized_data)

**Key Methods:**
- `clean_and_organize(extracted_texts)` - Main processor
- Model selection based on task complexity

**Technologies:** OpenRouter API, Gemini models

**Prompt Strategy:**
- JSON schema enforcement
- Field validation
- Retry logic (3 attempts)

---

### 3. Heterogeneity Architect (`backend/app/core/heterogeneity.py`)

**Purpose:** Generate 23 unique design parameters for each testimony

**Input:** 5 testimonies  
**Output:** 5 design structures (23 params each)

**23 Parameters:**

**Content Parameters (10):**
1. `tone_variable` - Voice register (authority, collaboration, etc.)
2. `tone_instructions` - Detailed writing style (150+ words)
3. `narrative_framework` - Story structure
4. `paragraph_density_rule` - Paragraph construction
5. `readability_target` - Audience level
6. `emphasis_pattern` - Highlighting strategy
7. `semantic_elements` - Formatting elements (lists, quotes, etc.)
8. `structure_features` - Visual layout
9. `target_word_count` - Length (2000-2800)
10. `bonus_trait` - Unique differentiator

**Visual Parameters (13):**
11. `layout_pattern` - Overall design style
12. `font_primary` - Body font
13. `font_secondary` - Accent font
14. `color_primary_hsl_range` - Main color
15. `color_accent` - Highlight color
16. `layout_density` - Spacing approach
17. `line_height` - Line spacing
18. `header_alignment` - Header position
19. `footer_style` - Footer design
20. `contrast_mode` - Color contrast
21. `whitespace_profile` - White space usage
22. `font_size_body` - Body text size
23. `font_size_headers` - Header sizes

**Validation:**
- No duplicate tone+narrative combinations
- All 23 params present in each design
- Word count targets distributed across letters

---

### 4. Block Generator (`backend/app/core/block_generator.py`)

**Purpose:** Generate 5 content blocks per testimony in parallel

**Input:** Testimony, design structure, context  
**Output:** 5 blocks of markdown content

**Block Structure:**

| Block | Purpose | Target Words | Model |
|-------|---------|--------------|-------|
| Block 1 | Introduction & Greeting | 300-600 | Gemini Flash |
| Block 2 | Professional Context | 300-600 | Gemini Flash |
| Block 3 | Technical Details & Achievements | 800+ | Gemini Pro |
| Block 4 | Impact & Results | 350-600 | Gemini Flash |
| Block 5 | Conclusion & Recommendation | 300-600 | Gemini Flash |

**Parallel Execution:**
- ThreadPoolExecutor (5 concurrent API calls)
- 30-60 second total generation time
- Word count expansion if needed

**Prompt Templates:** `backend/app/core/block_prompts.py`

---

### 5. HTML Designer (`backend/app/core/html_designer.py`)

**Purpose:** Generate custom HTML+CSS from blocks and design params

**Input:** 5 blocks, 23 design params, recommender info, logo  
**Output:** Complete HTML document (DOCTYPE to `</html>`)

**Key Features:**
- **No Templates** - Pure generative design
- **Logo Embedding** - Base64 data URIs
- **Print Optimization** - @page CSS, proper margins
- **Typography Excellence** - Multiple fonts, hierarchy
- **Visual Differentiation** - Colors, layouts, spacing

**LLM Prompt:** ~2000 tokens explaining design interpretation

**Output Format:**
```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    /* Custom CSS based on 23 parameters */
  </style>
</head>
<body>
  <div class="header">
    <img src="data:image/png;base64,..." class="logo">
    <!-- Header content -->
  </div>
  
  <!-- 5 blocks formatted according to design -->
  
  <div class="signature">
    <!-- Recommender details -->
  </div>
</body>
</html>
```

---

### 6. PDF/DOCX Generator (`backend/app/core/html_pdf_generator.py`)

**Purpose:** Convert HTML to PDF and editable DOCX

**Input:** Complete HTML document  
**Output:** PDF file, DOCX file

**PDF Conversion:**
- **Library:** WeasyPrint
- **Features:** CSS support, page breaks, print optimization
- **Size:** 8.5" × 11" (US Letter)

**DOCX Conversion:**
- **Library:** python-docx + BeautifulSoup
- **Features:** Preserve bold, italic, tables, lists
- **Structure:** Recursive HTML→DOCX element conversion

**Quality Checks:**
- Valid HTML structure
- Embedded logo rendering
- Font fallbacks
- Print-friendly formatting

---

### 7. Logo Scraper (`backend/app/core/logo_scraper.py`)

**Purpose:** Fetch company logos from web

**Input:** Company name, optional website  
**Output:** Logo file path or None

**Strategy:**
1. **Clearbit API** (primary) - `logo.clearbit.com/{domain}`
2. **Domain Lookup** (fallback) - Try common TLDs
3. **Caching** - Save to `backend/storage/logos/`

**Supported Formats:** PNG, JPG, SVG, WEBP

---

### 8. Validation Engine (`backend/app/core/validation.py`)

**Purpose:** Post-generation quality monitoring

**Checks:**

**1. N-gram Similarity**
- 4-gram Jaccard similarity between all letter pairs
- Warn if >20% similarity (indicates insufficient heterogeneity)
- Non-blocking (logs only)

**2. Forbidden Phrases**
- Detects generic clichés in Portuguese/English
- Examples: "pleasure to recommend", "without hesitation"
- Flags count (doesn't block)

**3. Word Count**
- Target: 1800-2800 words per letter
- Warns if outside range

**Output:** Validation report (saved to DB, not shown to user)

---

### 9. RAG Engine (`backend/app/core/rag_engine.py`)

**Status:** ⚠️ **CURRENTLY DISABLED**

**Purpose:** Context-aware generation using uploaded documents

**Architecture:**
- Document Chunker (600 chars, 100 overlap)
- Embedding Service (OpenAI `text-embedding-3-small`)
- Vector Store (in-memory, numpy-based cosine similarity)

**Usage (when enabled):**
- Ingest PDFs → chunk → embed → store
- Retrieve top-k chunks for each block
- Inject context into block generation prompts

**Disabled Reason:** Testing showed no quality improvement, added 10s latency

---

## AI/ML Pipeline

### LLM Orchestration

**OpenRouter Configuration:**
```python
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
BASE_URL = "https://openrouter.ai/api/v1"

MODELS = {
    "speed": "google/gemini-2.5-flash:free",     # Fast tasks
    "quality": "google/gemini-2.5-pro:free",     # Quality tasks
    "backup": "anthropic/claude-3.7-sonnet:free" # Fallback
}
```

**Model Selection Strategy:**

| Task | Model | Reason |
|------|-------|--------|
| PDF Categorization | Flash | Speed, simple classification |
| Data Organization | Flash | Structured output, moderate complexity |
| Heterogeneity Design | Pro | Creative, complex reasoning |
| Block 1, 2, 4, 5 | Flash | Speed, formulaic content |
| Block 3 | Pro | Deep technical content |
| HTML Generation | Pro | Creative design interpretation |

**Rate Limiting & Retry:**
- Exponential backoff: 2^attempt seconds
- Max retries: 3-5 (task-dependent)
- Temperature: 0.7-0.9 (creativity balance)

---

### Parallel Processing

**ThreadPoolExecutor Configuration:**
```python
MAX_PARALLEL_WORKERS = 10

# Parallel letter generation (5 letters × 2 tasks each)
with ThreadPoolExecutor(max_workers=10) as executor:
    # Each letter: logo fetch + block generation
    futures = [executor.submit(generate_letter, ...) for _ in range(5)]
```

**Optimization:**
- I/O-bound tasks (API calls) → ThreadPoolExecutor
- 5 blocks per letter generated in parallel (5 concurrent API calls)
- Logo scraping happens during block generation (no blocking)

**Typical Timeline:**
- Sequential: ~5 minutes per letter → 25 minutes total
- Parallel: ~2 minutes per batch → **10× speedup**

---

## Database Schema

### SQLite Tables

**1. users**
```sql
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**2. submissions**
```sql
CREATE TABLE submissions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    user_email TEXT,
    number_of_testimonials INTEGER,
    status TEXT DEFAULT 'pending',  -- pending/extracting/organizing/designing/generating/completed/error
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_data TEXT,  -- JSON string
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

**3. feedback**
```sql
CREATE TABLE feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    submission_id TEXT NOT NULL,
    letter_index INTEGER,        -- NULL for overall feedback
    rating INTEGER,               -- 1-10
    comments TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (submission_id) REFERENCES submissions(id)
);
```

**Status Flow:**
```
pending → extracting → organizing → designing → generating → completed
           ↓             ↓             ↓            ↓
         error        error         error        error
```

---

## API Specifications

### Authentication Endpoints

**POST /api/auth/register**
```json
Request:
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}

Response (201):
{
  "id": "uuid-v4",
  "email": "user@example.com",
  "access_token": "eyJ..."
}
```

**POST /api/auth/login**
```json
Request:
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}

Response (200):
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

**GET /api/auth/me**
```
Headers: Authorization: Bearer {token}

Response (200):
{
  "id": "uuid",
  "email": "user@example.com"
}
```

---

### Submission Endpoints

**POST /api/submissions**
```
Headers: Authorization: Bearer {token}
Content-Type: multipart/form-data

Body:
- files[]: File[] (5-9 PDFs)
- email: string
- numberOfTestimonials: integer

Response (201):
{
  "submission_id": "uuid-v4",
  "status": "pending"
}
```

**GET /api/submissions**
```
Headers: Authorization: Bearer {token}

Response (200):
[
  {
    "id": "uuid",
    "status": "completed",
    "number_of_testimonials": 5,
    "created_at": "2025-01-01T12:00:00Z"
  },
  ...
]
```

**GET /api/submissions/{id}**
```
Headers: Authorization: Bearer {token}

Response (200):
{
  "id": "uuid",
  "user_id": "uuid",
  "status": "completed",
  "number_of_testimonials": 5,
  "created_at": "2025-01-01T12:00:00Z",
  "letters": [
    {
      "recommender": "John Doe",
      "pdf_path": "/backend/storage/outputs/.../letter_1.pdf",
      "docx_path": "/backend/storage/outputs/.../letter_1.docx"
    },
    ...
  ]
}
```

**POST /api/submissions/{id}/retry**
```
Headers: Authorization: Bearer {token}

Response (200):
{
  "message": "Regeneration started",
  "submission_id": "uuid"
}
```

**GET /api/submissions/{id}/download/{filename}**
```
Headers: Authorization: Bearer {token}

Response (200):
Content-Type: application/pdf or application/vnd.openxmlformats-officedocument.wordprocessingml.document
Content-Disposition: attachment; filename="letter_1.pdf"

[Binary file content]
```

---

### Feedback Endpoints

**POST /api/submissions/{id}/feedback**
```json
Request:
{
  "letter_index": 0,  // null for overall
  "rating": 9,
  "comments": "Excellent quality!"
}

Response (201):
{
  "message": "Feedback submitted"
}
```

---

## Security & Authentication

### JWT Implementation

**Token Generation:**
```python
SECRET_KEY = os.getenv('JWT_SECRET_KEY')
ALGORITHM = "HS256"
EXPIRY = 7 days

token = jwt.encode({
    "sub": user_email,
    "exp": datetime.utcnow() + timedelta(days=7)
}, SECRET_KEY, algorithm=ALGORITHM)
```

**Protected Routes:**
- All `/api/submissions/*` endpoints
- `/api/auth/me`

**Password Security:**
- Hashing: bcrypt (12 rounds)
- No plain-text storage

---

### Environment Variables

**Required:**
```
OPENROUTER_API_KEY=sk-or-...
JWT_SECRET_KEY=random-256-bit-string
CLEARBIT_API_KEY=sk_...
STORAGE_BASE_DIR=backend/storage
```

**Optional (Email Service):**
```
GMAIL_CLIENT_ID=...
GMAIL_CLIENT_SECRET=...
GMAIL_REFRESH_TOKEN=...
```

---

## Deployment Architecture

### Replit Deployment

**Port Configuration:**
- **Frontend**: 5000 (Vite dev server)
- **Backend**: 8000 (FastAPI/Uvicorn)
- **Email Service**: 3001 (Node.js)

**Workflows:**
1. **Frontend** (read-only): `cd frontend && npm run dev`
2. **Backend API** (read-only): `./start-backend.sh`
3. **Email Service** (read-only): `cd backend && npm start`

**Static Files:**
- Frontend builds to `frontend/dist/`
- FastAPI serves from `backend/static/`

**File Storage:**
- Uploads: `backend/storage/uploads/`
- Outputs: `backend/storage/outputs/{submission_id}/`
- Logos: `backend/storage/logos/`

---

## Modification Guidelines

### 🚨 **CRITICAL RULES**

1. **All changes MUST be documented here first**
2. **No edits to platform code without updating this document**
3. **This document is the single source of truth**

---

### How to Make Changes

**Step 1: Update This Document**
- Add new component specifications
- Update data flow diagrams (ASCII art)
- Document new API endpoints
- Explain architectural decisions

**Step 2: Implement in Code**
- Follow specifications exactly as written here
- Maintain existing patterns
- Add inline comments referencing this doc

**Step 3: Test & Validate**
- Verify against architecture specs
- Check data flow integrity
- Ensure backward compatibility

**Step 4: Update Version**
- Increment version number at top of doc
- Add changelog entry

---

### Common Modifications

#### Adding a New Block to Letters

**Architecture Change:**
1. Update "Block Structure" table in Component Specifications
2. Add block to data flow diagram
3. Document prompt template

**Code Changes:**
1. `backend/app/core/block_prompts.py` - Add `BLOCKX_PROMPT`
2. `backend/app/core/block_generator.py` - Add `generate_blockX()`
3. `backend/app/core/html_designer.py` - Update block assembly logic

#### Adding a New Design Parameter

**Architecture Change:**
1. Update 23-parameter list in Heterogeneity Architect section
2. Document parameter purpose and example values
3. Update validation logic

**Code Changes:**
1. `backend/app/core/heterogeneity.py` - Add to prompt + validation
2. `backend/app/core/html_designer.py` - Interpret new parameter

#### Changing LLM Models

**Architecture Change:**
1. Update "LLM Orchestration" table
2. Document reason for model change
3. Update cost/performance metrics

**Code Changes:**
1. `backend/app/core/llm_processor.py` - Update `MODELS` dict
2. Test all affected workflows

---

### Architecture Review Checklist

Before deploying changes:

- [ ] Architecture document updated
- [ ] Data flow diagram reflects changes
- [ ] API specs updated (if applicable)
- [ ] Database schema updated (if applicable)
- [ ] Component specifications complete
- [ ] Security implications reviewed
- [ ] Performance impact analyzed
- [ ] Version number incremented

---

## Appendix

### Glossary

- **Heterogeneity**: Variance in writing style, structure, and design across letters
- **Design Structure**: 23-parameter configuration for a single letter
- **Block**: Content segment within a letter (5 blocks per letter)
- **RAG**: Retrieval-Augmented Generation (context injection)
- **N-gram**: Sequence of N words used for similarity detection

### References

- OpenRouter API: https://openrouter.ai/docs
- WeasyPrint Docs: https://doc.courtbouillon.org/weasyprint/
- FastAPI Docs: https://fastapi.tiangolo.com/

---

**Document Control:**
- **Owner**: Platform Lead
- **Reviewers**: All developers before PRs
- **Update Frequency**: On every architectural change
- **Storage**: `docs/ARCHITECTURE.md` (version controlled)


# ProEx Platform - Standalone EB-2 NIW Letter Processing

A complete standalone platform for processing EB-2 NIW recommendation letters, built with FastAPI (backend) and React + Vite (frontend).

## Features

- **PDF Text Extraction**: Automatically extracts text from uploaded PDF documents
- **LLM Processing**: Uses OpenAI-compatible APIs (Gemini) to organize and structure data
- **Heterogeneity Architect**: Generates unique writing styles for each testimonial
- **Block Generation**: Creates 5 distinct blocks for each recommendation letter
- **PDF Assembly**: Combines blocks into complete, professionally formatted letters
- **File Management**: Handles multiple file uploads with proper storage
- **Status Tracking**: Real-time status updates for processing submissions

## Tech Stack

### Backend
- Python 3.11 + FastAPI
- SQLite database (local file)
- pdfplumber for PDF extraction
- OpenAI SDK (Gemini-compatible)
- WeasyPrint for PDF generation
- Markdown processing

### Frontend
- React 18 + TypeScript
- Vite for build tooling
- Tailwind CSS for styling
- React Router for navigation
- Axios for API calls
- React Hook Form for forms

## Project Structure

```
proex-platform/
├── backend/                    # Python FastAPI backend
│   ├── app/
│   │   ├── api/               # API routes
│   │   ├── core/              # Core processing logic
│   │   ├── db/                # Database operations
│   │   └── main.py            # FastAPI app
│   ├── storage/               # File storage
│   └── requirements.txt
│
├── frontend/                   # React Vite frontend
│   ├── src/
│   │   ├── pages/             # Page components
│   │   ├── App.tsx            # Main app
│   │   └── main.tsx           # Entry point
│   └── package.json
│
└── README.md
```

## Setup

### Prerequisites
- Python 3.11+
- Node.js 20+
- OpenAI API Key (or Gemini API key with OpenAI-compatible endpoint)

### Installation

Dependencies are already installed via Replit package manager.

### Configuration

Set up your API keys using Replit Secrets:
- `OPENAI_API_KEY`: Your API key for Gemini/OpenAI
- `OPENAI_BASE_URL`: API endpoint (default: Gemini)
- `JWT_SECRET`: Secret key for JWT tokens

## Usage

1. **Submit Documents**: Upload PDFs (Quadro, CV, Testimonials, etc.)
2. **Processing**: System automatically extracts, organizes, and generates letters
3. **Download**: Get ZIP file with all generated recommendation letters

## API Endpoints

- `POST /api/submissions` - Create new submission
- `GET /api/submissions/{id}` - Get submission status
- `GET /api/submissions/{id}/download` - Download generated letters

## Processing Flow

1. **PDF Extraction**: Extract text from all uploaded PDFs
2. **Data Organization**: LLM structures extracted data into JSON
3. **Design Generation**: Create unique writing styles for each testimonial
4. **Block Generation**: Generate 5 blocks (BLOCO3-7) per letter
5. **Assembly**: Combine blocks into complete letters
6. **PDF Generation**: Convert Markdown to styled PDFs

## Development

Frontend runs on port 5000, Backend on port 8000.

## License

Proprietary - ProEx Venture © 2025

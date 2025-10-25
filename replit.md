# ProEx Platform - Processamento de Cartas EB-2 NIW

## Overview
The ProEx Platform is a standalone web application designed to process recommendation letters for EB-2 NIW visas. It automates the entire workflow, from PDF ingestion and data extraction to content generation using Large Language Models (LLMs), visual customization, and final document output in PDF and editable DOCX formats. The platform aims to provide unique, high-quality, and visually diverse recommendation letters, replicating complex n8n workflows in Python/TypeScript. Key capabilities include automatic logo scraping, sophisticated template management for visual heterogeneity, a machine learning-based feedback system, and seamless integration with Google Drive and email for delivery.

## User Preferences
I prefer simple language. I want iterative development. Ask before making major changes. I prefer detailed explanations. Do not make changes to the folder Z. Do not make changes to the file Y.

## System Architecture

### UI/UX Decisions
The platform features a responsive web interface built with React and Tailwind CSS. A key design principle is visual heterogeneity in the generated documents, with six radically distinct HTML/CSS templates (Technical, Academic, Narrative, Business, USA, Testimony) ensuring each letter has a unique font, color palette, and layout. Logos are dynamically added to document headers.

### Technical Implementations
The backend is built with FastAPI (Python 3.11) and uses SQLite for local data storage, including ML analytics and auto-schema migration. Key Python libraries include `pdfplumber` for PDF extraction, `WeasyPrint` for HTML-to-PDF conversion, `python-docx` + `html-for-docx` for editable DOCX generation, and `Jinja2` for dynamic HTML templating. The frontend uses React 18, TypeScript, Vite, React Router, and Axios.

### Feature Specifications
- **PDF Processing**: Uploads multiple PDFs (Quadros, CVs, Strategy, OneNote) with text extraction.
- **LLM-Powered Content Generation**: Utilizes a tiered LLM strategy (Gemini Flash for extraction, Gemini Pro for block generation, Claude Sonnet for final assembly) via OpenRouter for data organization and content creation across 5 distinct blocks per letter.
- **Heterogeneity Architect**: Programmatically ensures radical visual and structural diversity across generated letters through 6 archetypal templates with strict validation rules.
- **Logo Scraping**: Automatically fetches company logos using Clearbit API with fallback to web scraping, including caching.
- **Document Generation**: Produces visually unique PDFs and fully editable DOCX files.
- **Feedback System**: ML-based 0-100 rating system per letter, template performance analytics, and selective regeneration capability with optional custom LLM instructions.
- **Automated Delivery**: Uploads generated DOCX files to Google Drive and sends notification emails with direct links.
- **Real-time Tracking**: Provides submission status updates.

### System Design Choices
- **Microservices-oriented**: Separate backend (FastAPI), email service (Node.js), and frontend (React) workflows.
- **Tiered LLM Strategy**: Optimizes cost and quality by using different LLMs for specific tasks.
- **Robust Error Handling**: Includes retry logic with exponential backoff for LLM calls and external integrations.
- **Scalable Document Generation**: Designed to handle multiple letters while maintaining uniqueness and quality.

## External Dependencies

- **OpenRouter.ai**: Unified API for various LLMs (Gemini 2.5 Flash, Gemini 2.5 Pro, Claude 3.7 Sonnet) for data processing and content generation. Requires `OPENROUTER_API_KEY`.
- **Clearbit API**: Used for logo scraping (primary source).
- **Google Drive API**: For automatic upload and sharing of generated DOCX files.
- **Gmail API**: For sending email notifications with document links.
- **pdfplumber**: Python library for PDF text extraction.
- **WeasyPrint**: Python library for converting HTML/CSS to PDF.
- **python-docx / html-for-docx**: Python libraries for generating editable Word documents from HTML.
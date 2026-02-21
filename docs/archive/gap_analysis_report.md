# Gap Analysis Report: Current Codebase vs. Client Requirements

## Executive Summary
The current codebase is a custom Python/FastAPI application that generates letters using LLMs and HTML templates. While it has the basic structure for generating letters, it falls short of the client's "production-ready" expectations in several key areas, particularly regarding workflow automation (N8N), output consistency, and document handling.

## 1. Letter Formatting & Quality Issues

| Requirement | Current State | Gap |
| :--- | :--- | :--- |
| **Clean, publication-ready HTML** | Static HTML templates in `backend/app/templates/` with hardcoded styles. | Templates are brittle and likely break with variable content length. No dynamic resizing or smart layout logic found. |
| **Automatic Logo Scraping** | `LogoScraper` class exists and is called in `_generate_single_letter`. | Logic seems present but client complains it is "incorrect and broken". Likely needs better validation or a different source. |
| **High-quality Word Conversion** | `pdf_generator.html_to_docx` exists. | Client complains of "formatting degradation". The current conversion likely doesn't preserve complex HTML layouts well. |

**Recommendation:** Move away from direct HTML-to-PDF/DOCX conversion if possible, or use a more robust engine. For N8N, we might use a dedicated document generation service or API.

## 2. Output Consistency Problem

| Requirement | Current State | Gap |
| :--- | :--- | :--- |
| **Consistent, high-quality output** | `PromptEnhancer` uses clustering and feedback to "improve" prompts. | The "enhancer" adds complexity and variability. Client wants *less* variance. The current "unsupervised learning" might be drifting prompts away from the desired standard. |
| **Parallel Processing** | `ThreadPoolExecutor` with 5 workers used in `process_submission`. | This is local concurrency, not true scalable parallel processing. If the server crashes, jobs are lost. N8N would handle this better with reliable queuing. |

**Recommendation:** Simplify the prompt engineering. Remove the "unsupervised" drift. Use N8N for orchestration to ensure reliability and visibility.

## 3. Workflow Inefficiency

| Requirement | Current State | Gap |
| :--- | :--- | :--- |
| **Rebuild in N8N** | Pure Python/FastAPI backend. | **Major Gap.** The entire backend logic needs to be migrated or wrapped by N8N workflows. |
| **Manual Consultant Work** | Manual file uploads via a simple React form. | No "dashboard" for consultants to manage state. |

**Recommendation:** Design the N8N workflow first. It should handle the orchestration: Trigger -> Extract -> Generate (Parallel) -> Review -> Deliver.

## 4. Missing Context/Intelligence

| Requirement | Current State | Gap |
| :--- | :--- | :--- |
| **"Other Documents" Upload** | `SubmitPage.tsx` accepts specific files (Quadro, CV, Strategy, OneNote). | No generic "Other" field. The backend `create_submission` endpoint doesn't accept arbitrary extra files. |
| **Reference Supplementary Docs** | `SubmissionProcessor` organizes data from specific inputs. | The LLM context doesn't seem to include "medical reports" or "RTAs" unless they are stuffed into the existing fields. |

**Recommendation:** Add a generic file upload field. Update the `clean_and_organize` step to ingest and summarize these extra documents for the LLM context.

## 5. Frontend/User Experience

| Requirement | Current State | Gap |
| :--- | :--- | :--- |
| **Consultant-facing Frontend** | Simple "Submit Page". | Lacks a "Consultant Dashboard" to view active submissions, status, and perform reviews. |
| **Standardized Formats** | Accepts PDFs. | Seems to meet the basic requirement, but validation might be weak. |

**Recommendation:** Expand the frontend to include a dashboard.

## 6. Single Letter Editing

| Requirement | Current State | Gap |
| :--- | :--- | :--- |
| **Regenerate Single Letter** | Endpoint `/submissions/{submission_id}/regenerate` exists. | Logic exists in backend (`regenerate_specific_letters`). If client says it's missing, it's likely not exposed in the UI or the UX is poor. |
| **Refinement based on feedback** | Endpoint accepts `instructions`. | Again, backend supports it, but UI likely doesn't make it easy to "chat" with the letter to fix it. |

**Recommendation:** Build a "Review & Edit" UI where the consultant can select a letter, type feedback, and trigger the regeneration endpoint.

## Immediate Next Steps (Plan)

1.  **N8N Migration Strategy:** Map the Python logic (`SubmissionProcessor`) to N8N nodes.
2.  **Frontend Update:** Add "Other Documents" field to `SubmitPage.tsx`.
3.  **Backend Update:** Update `submissions.py` to accept extra files and pass them to the processor.
4.  **Quality Review UI:** Design a simple review interface for the consultant.

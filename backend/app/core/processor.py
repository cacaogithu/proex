from .pdf_extractor import PDFExtractor
from .llm_processor import LLMProcessor
from .heterogeneity import HeterogeneityArchitect
from .block_generator import BlockGenerator
from .html_pdf_generator import HTMLPDFGenerator
from .html_designer import HTMLDesigner
from .logo_scraper import LogoScraper
from .email_sender import send_results_email, check_email_service_health
from .validation import validate_batch, print_validation_report
from .rag_engine import RAGEngine
from .progress_tracker import progress_tracker
from ..db.database import Database
import os
import glob
import logging
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

# Configuration constants
STORAGE_BASE_DIR = os.getenv('STORAGE_BASE_DIR', 'backend/storage')
MAX_PARALLEL_WORKERS = 10  # Maximum concurrent letter generation tasks (increased from 5)



class SubmissionProcessor:
    def __init__(self):
        logger.info("Initializing SubmissionProcessor")
        self.pdf_extractor = PDFExtractor()
        self.llm = LLMProcessor()
        self.db = Database()
        self.block_generator = BlockGenerator(self.llm)
        self.html_designer = HTMLDesigner(self.llm)



        # Initialize other components
        self.heterogeneity = HeterogeneityArchitect(self.llm)
        self.block_generator = BlockGenerator(self.llm) # Removed prompt_enhancer and rag_engine args
        self.pdf_generator = HTMLPDFGenerator()
        self.logo_scraper = LogoScraper()
        self.max_workers = MAX_PARALLEL_WORKERS
        logger.info(f"SubmissionProcessor initialized with {self.max_workers} parallel workers (ML/RAG disabled)")

    def _generate_single_letter(self, submission_id: str, index: int, testimony: Dict, design: Dict, organized_data: Dict, total_letters: int = 1) -> Dict:
        """Helper function to generate a single letter, designed for parallel execution."""

        recommender_name = testimony.get('recommender_name', 'Unknown')
        print(f"\n  [START] Letter {index+1}: {recommender_name}")
        
        progress_tracker.letter_start(submission_id, index, recommender_name, total_letters)

        # 1. Fetch company logo (This is now done inside the parallel function)
        company_name = testimony.get('recommender_company', '')
        company_website = testimony.get('recommender_company_website')
        logo_path = None

        if company_name:
            progress_tracker.letter_step(submission_id, index, recommender_name, "logo_search", f"Buscando logo de {company_name}...")
            progress_tracker.logo_search(submission_id, company_name, "searching")
            logo_path = self.logo_scraper.get_company_logo(company_name, company_website)
            if logo_path:
                progress_tracker.logo_search(submission_id, company_name, "found")
            else:
                progress_tracker.logo_search(submission_id, company_name, "not_found")

        # 2. Generate 5 blocks
        print(f"    - Generating 5 blocks for {recommender_name}...")
        progress_tracker.letter_step(submission_id, index, recommender_name, "blocks", "Gerando 5 blocos de conteúdo...")
        blocks = self.block_generator.generate_all_blocks(testimony, design, organized_data)
        print(f"    ✓ Blocks generated for {recommender_name}")

        # 3. DESIGN custom HTML (AI-powered, no templates!)
        print(f"    - Designing custom HTML for {recommender_name}...")
        progress_tracker.letter_step(submission_id, index, recommender_name, "html_design", "Criando design HTML personalizado...")
        recommender_info = {
            'name': recommender_name,
            'title': testimony.get('recommender_position', ''),
            'company': testimony.get('recommender_company', ''),
            'location': testimony.get('recommender_location', '')
        }
        letter_html = self.html_designer.generate_html_design(
            blocks=blocks,
            design=design,
            recommender_info=recommender_info,
            logo_path=logo_path
        )
        print(f"    ✓ Custom HTML design generated for {recommender_name}")

        # 4. Generate PDF and DOCX from complete HTML
        output_dir = os.path.join(STORAGE_BASE_DIR, "outputs", submission_id)
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"letter_{index+1}_{recommender_name.replace(' ', '_')}.pdf")
        print(f"    - Converting HTML to PDF for {recommender_name}...")
        progress_tracker.letter_step(submission_id, index, recommender_name, "pdf_generation", "Convertendo para PDF...")

        # Since letter_html is now a complete document, convert directly to PDF
        self.pdf_generator.html_to_pdf_direct(letter_html, output_path)
        print(f"    ✓ PDF generated for {recommender_name}")

        docx_output_path = output_path.replace('.pdf', '.docx')
        print(f"    - Generating editable DOCX for {recommender_name}...")
        progress_tracker.letter_step(submission_id, index, recommender_name, "docx_generation", "Gerando DOCX editável...")
        self.pdf_generator.html_to_docx_direct(letter_html, docx_output_path)
        print(f"    ✓ DOCX generated for {recommender_name}")
        
        progress_tracker.letter_complete(submission_id, index, recommender_name, logo_path is not None)



        print(f"  [END] Letter {index+1}: {recommender_name}")

        # Return complete letter data
        return {
            "testimony_id": testimony.get('testimony_id', str(index+1)),
            "recommender": recommender_name,
            "pdf_path": output_path,
            "docx_path": docx_output_path,
            "has_logo": logo_path is not None,
            "blocks": blocks,
            "letter_html": letter_html,
            "design": design,
            "index": index
        }

    def update_status(self, submission_id: str, status: str, error: Optional[str] = None):
        self.db.update_submission_status(submission_id, status, error)
        print(f"Submission {submission_id}: {status}")

    def process_submission(self, submission_id: str):
        try:
            print(f"\n{'='*60}")
            print(f"Starting processing for submission: {submission_id}")
            print(f"{'='*60}\n")
            
            progress_tracker.phase_start(submission_id, "extracting", "Extraindo texto dos documentos...", 1)

            self.update_status(submission_id, "extracting")
            print("\nPHASE 1: Extracting text from PDFs...")
            extracted_texts = self.pdf_extractor.extract_all_files(submission_id)
            num_testimonials = len(extracted_texts.get('testimonials', []))
            print(f"✓ Extracted {num_testimonials} testimonials")
            progress_tracker.phase_complete(submission_id, "extracting", f"Extraído texto de {num_testimonials} testemunhos")

            progress_tracker.phase_start(submission_id, "organizing", "Organizando e limpando dados com IA...", 1)
            self.update_status(submission_id, "organizing")
            print("\nPHASE 2: Cleaning and organizing data...")
            organized_data = self.llm.clean_and_organize(extracted_texts)
            organized_data['submission_id'] = submission_id
            petitioner_name = organized_data.get('petitioner', {}).get('name', 'Unknown')
            print(f"✓ Organized data for {petitioner_name}")
            progress_tracker.phase_complete(submission_id, "organizing", f"Dados organizados para {petitioner_name}")

            progress_tracker.phase_start(submission_id, "designing", "Criando designs únicos para cada carta...", 1)
            self.update_status(submission_id, "designing")
            design_structures = self.heterogeneity.generate_design_structures(organized_data)
            num_designs = len(design_structures.get('design_structures', []))
            print(f"✓ Generated {num_designs} unique designs")
            progress_tracker.phase_complete(submission_id, "designing", f"Criado {num_designs} designs únicos")

            self.update_status(submission_id, "generating")
            print("\nPHASE 4: Generating letters...")
            letters = []

            testimonies = organized_data.get('testimonies', [])
            designs = design_structures.get('design_structures', [])
            total_letters = len(testimonies)
            
            progress_tracker.phase_start(submission_id, "generating", f"Gerando {total_letters} cartas de recomendação...", total_letters)

            # Validate: number of testimonies must match expected number
            submission = self.db.get_submission(submission_id)
            expected_count = submission.get('number_of_testimonials', len(testimonies)) if submission else len(testimonies)

            if len(testimonies) != expected_count:
                print(f"⚠️  WARNING: Expected {expected_count} testimonies but found {len(testimonies)}")
                print(f"   Generating letters for all {len(testimonies)} testimonies found")

            # Prepare tasks for parallel execution
            tasks = []
            for i, testimony in enumerate(testimonies):
                design = designs[i] if i < len(designs) else designs[0]
                tasks.append((submission_id, i, testimony, design, organized_data, total_letters))

            # Execute letter generation in parallel
            print(f"\n🚀 Starting parallel generation of {len(tasks)} letters with {self.max_workers} workers...")

            # Use ThreadPoolExecutor for I/O-bound tasks (API calls, file I/O)
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_letter = {
                    executor.submit(self._generate_single_letter, *task): task
                    for task in tasks
                }

                # Collect results as they complete
                unsorted_letters = []
                failed_letters = []
                for future in as_completed(future_to_letter):
                    task = future_to_letter[future]
                    letter_index = task[1]
                    testimony = task[2]
                    try:
                        letter_data = future.result()
                        unsorted_letters.append(letter_data)
                    except Exception as exc:
                        error_msg = f"Letter {letter_index + 1} ({testimony.get('recommender_name', 'Unknown')}) failed: {str(exc)}"
                        print(f"  [ERROR] {error_msg}")
                        failed_letters.append({
                            "index": letter_index,
                            "recommender": testimony.get('recommender_name', 'Unknown'),
                            "error": str(exc)
                        })
                        # Create placeholder entry to maintain proper indexing
                        unsorted_letters.append({
                            "index": letter_index,
                            "testimony_id": testimony.get('testimony_id', str(letter_index + 1)),
                            "recommender": testimony.get('recommender_name', 'Unknown'),
                            "error": str(exc),
                            "failed": True
                        })

            # Sort letters back into original order
            letters = sorted(unsorted_letters, key=lambda x: x['index'])

            # Report results
            successful_letters = [l for l in letters if not l.get('failed', False)]
            print(f"\n✅ {len(successful_letters)}/{len(letters)} letters generated successfully.")
            
            progress_tracker.phase_complete(submission_id, "generating", f"{len(successful_letters)} cartas geradas com sucesso")
            
            if failed_letters:
                print(f"⚠️  {len(failed_letters)} letter(s) failed:")
                for failed in failed_letters:
                    print(f"   - Letter {failed['index'] + 1} ({failed['recommender']}): {failed['error']}")

            # VALIDATION: Check heterogeneity and quality (light validation, no rewrite)
            # Only validate successfully generated letters
            successful_letters_for_validation = [l for l in letters if not l.get('failed', False)]
            validation_report = validate_batch(successful_letters_for_validation)
            print_validation_report(validation_report)

            # Update status based on results
            if len(successful_letters) == len(letters):
                self.update_status(submission_id, "completed")
            elif len(successful_letters) > 0:
                self.update_status(submission_id, "completed_with_errors")
                logger.warning(f"Submission {submission_id} completed with {len(failed_letters)} failed letter(s)")
            else:
                self.update_status(submission_id, "error", "All letters failed to generate")
                logger.error(f"Submission {submission_id} failed - no successful letters")

            self.db.save_processed_data(submission_id, {
                "letters": letters,  # Include all letters (both successful and failed) for debugging
                "organized_data": organized_data,
                "design_structures": design_structures,
                "validation_report": validation_report,  # Store metrics for monitoring
                "failed_count": len(failed_letters),
                "success_count": len(successful_letters)
            })

            # ML Retraining - DISABLED
            # total_submissions = self.db.get_total_submissions_count()
            # if total_submissions % 10 == 0:
            #     logger.info(f"Triggering ML model retraining")
            #     print("\n🧠 Re-training ML models with new data...")
            #     try:
            #         # ML training disabled
            #         # self.prompt_enhancer.train_models(min_samples=MIN_ML_TRAINING_SAMPLES)
            #         # logger.info("ML models retrained successfully")
            #         logger.info("ML model retraining skipped: ML components are disabled.")
            #         print("   ℹ️  ML training skipped: ML components are disabled.")
            #     except Exception as e:
            #         logger.warning(f"ML training failed: {e}")
            #         print(f"   ℹ️  ML training skipped: {e}")
            # else:
            #     logger.debug(f"Skipping ML retraining (will retrain at next multiple of 10)")
            print(f"\n{'='*60}")
            print(f"✓ COMPLETED! Generated {len(letters)} PDF + DOCX letters")
            print(f"{'='*60}\n")

            # PHASE 5: Send email with Google Drive links (both PDF and DOCX)
            submission = self.db.get_submission(submission_id)
            recipient_email = submission.get('user_email') if submission else None

            if recipient_email and check_email_service_health() and len(successful_letters) > 0:
                progress_tracker.phase_start(submission_id, "email", "Enviando resultados por email e Google Drive...", 1)
                print("\nPHASE 5: Sending results via email and Google Drive...")
                # Send both PDFs and DOCXs (only for successfully generated letters)
                file_paths = []
                for letter in successful_letters:
                    file_paths.append(os.path.abspath(letter['pdf_path']))
                    file_paths.append(os.path.abspath(letter.get('docx_path', letter['pdf_path'].replace('.pdf', '.docx'))))

                email_result = send_results_email(submission_id, recipient_email, file_paths)

                if email_result.get('success'):
                    print(f"✅ Email sent to {recipient_email}")
                    print(f"✅ {email_result.get('files_uploaded', 0)} files uploaded to Google Drive")
                    progress_tracker.phase_complete(submission_id, "email", f"Email enviado para {recipient_email}")
                else:
                    print(f"⚠️  Email sending failed: {email_result.get('error', 'Unknown error')}")
                    progress_tracker.phase_complete(submission_id, "email", "Falha ao enviar email")
            else:
                if not recipient_email:
                    print("⚠️  No email address provided, skipping email notification")
                else:
                    print("⚠️  Email service not available, skipping email notification")
            
            # Emit completion event
            progress_tracker.completion(
                submission_id, 
                success=len(successful_letters) > 0,
                total_letters=len(letters),
                successful_letters=len(successful_letters),
                message=f"Processamento concluído: {len(successful_letters)} cartas geradas com sucesso"
            )

            return {"success": True, "letters": letters}

        except Exception as e:
            error_msg = str(e)
            print(f"\n✗ ERROR: {error_msg}\n")
            self.update_status(submission_id, "error", error_msg)
            progress_tracker.error(submission_id, "processing", f"Erro no processamento: {error_msg}")
            progress_tracker.completion(submission_id, success=False, total_letters=0, successful_letters=0, message=f"Erro: {error_msg}")
            raise

    def regenerate_specific_letters(
        self,
        submission_id: str,
        letter_indices: list[int],
        custom_instructions: Optional[str] = None
    ):
        """Regenerate only specific letters from a completed submission"""
        try:
            print(f"\n{'='*60}")
            print(f"Regenerating letters {letter_indices} for submission: {submission_id}")
            print(f"{'='*60}\n")

            # Get existing submission data
            submission = self.db.get_submission(submission_id)
            if not submission or submission['status'] != 'completed':
                raise Exception("Submission not found or not completed")

            # Load processed data
            import json
            processed_data = json.loads(submission.get('processed_data', '{}'))

            if not processed_data:
                raise Exception("No processed data found for this submission")

            # Get organized_data from processed_data (not raw_data which is empty)
            organized_data = processed_data.get('organized_data', {})
            if not organized_data:
                raise Exception("No organized data found in processed_data")

            existing_letters = processed_data.get('letters', [])
            # Use 'testimonies' key (that's what LLM processor returns)
            testimonials = organized_data.get('testimonies', [])

            self.update_status(submission_id, "regenerating")

            # Regenerate heterogeneity for selected letters only
            print(f"\nRegenerating design structures for {len(letter_indices)} letter(s)...")

            # Get existing designs (design_structures is a dict with 'design_structures' key containing the list)
            design_structures_dict = processed_data.get('design_structures', {})
            existing_designs = design_structures_dict.get('design_structures', [])
            if not existing_designs:
                raise Exception("No design structures found in processed_data")

            # Create new designs for selected indices
            selected_testimonials = [testimonials[i] for i in letter_indices]
            new_designs_dict = self.heterogeneity.generate_design_structures({'testimonies': selected_testimonials})
            new_designs = new_designs_dict.get('design_structures', [])

            # Replace designs at specified indices
            for i, letter_idx in enumerate(letter_indices):
                if letter_idx < len(existing_designs):
                    existing_designs[letter_idx] = new_designs[i]

            # Regenerate blocks and PDFs for selected letters
            output_dir = os.path.join(STORAGE_BASE_DIR, "outputs", submission_id)
            os.makedirs(output_dir, exist_ok=True)

            print(f"\nRegenerating content and PDFs...")
            for i, letter_idx in enumerate(letter_indices):
                if letter_idx >= len(testimonials):
                    print(f"  ⚠️ Skipping invalid index: {letter_idx}")
                    continue

                testimony = testimonials[letter_idx]
                design = new_designs[i]

                recommender_name = testimony.get('recommender_name', 'Unknown')

                print(f"\n  Letter {letter_idx + 1}/{len(testimonials)}: {recommender_name}")

                # Generate blocks (with ML enhancement)
                context = {
                    'petitioner': organized_data.get('petitioner', {}),
                    'strategy': organized_data.get('strategy', {}),
                    'onet': organized_data.get('onet', {})
                }
                blocks = self.block_generator.generate_all_blocks(testimony, design, context)

                # 3. DESIGN custom HTML (AI-powered, Authentic Heterogeneity)
                print(f"    - Designing custom HTML for {recommender_name}...")

                recommender_info = {
                    'name': recommender_name,
                    'title': testimony.get('recommender_title', ''),
                    'company': testimony.get('recommender_company', ''),
                    'location': testimony.get('recommender_location', '')
                }
                # Fetch logo path again for the current letter
                company_name = testimony.get('recommender_company', '')
                company_website = testimony.get('recommender_company_website')
                logo_path = None
                if company_name:
                    logo_path = self.logo_scraper.get_company_logo(company_name, company_website)

                letter_html = self.html_designer.generate_html_design(
                    blocks=blocks,
                    design=design,
                    recommender_info=recommender_info,
                    logo_path=logo_path
                )


                output_path = os.path.join(output_dir, f"letter_{letter_idx+1}_{recommender_name.replace(' ', '_')}.pdf")
                print(f"    - Converting HTML to PDF for {recommender_name}...")
                self.pdf_generator.html_to_pdf_direct(letter_html, output_path)
                print(f"    ✓ PDF generated for {recommender_name}")

                docx_output_path = output_path.replace('.pdf', '.docx')
                print(f"    - Generating editable DOCX for {recommender_name}...")
                self.pdf_generator.html_to_docx_direct(letter_html, docx_output_path)
                print(f"    ✓ DOCX generated for {recommender_name}")


                # Update letter info
                existing_letters[letter_idx].update({
                    "pdf_path": output_path,
                    "docx_path": docx_output_path,
                    "regenerated": True
                })

            # Update processed data (save back as dict with design_structures key)
            design_structures_dict['design_structures'] = existing_designs
            processed_data['design_structures'] = design_structures_dict
            processed_data['letters'] = existing_letters
            self.db.save_processed_data(submission_id, processed_data)

            # Re-send email with updated files
            print("\nUploading to Google Drive and sending email...")
            # Database stores email in 'user_email' column
            user_email = submission.get('user_email')

            if user_email and check_email_service_health():
                # Extract PDF paths from letters (send_results_email expects paths, not dicts)
                pdf_paths = [os.path.abspath(letter['pdf_path']) for letter in existing_letters if not letter.get('failed')]
                docx_paths = [os.path.abspath(letter['docx_path']) for letter in existing_letters if not letter.get('failed')]
                all_paths = pdf_paths + docx_paths
                email_result = send_results_email(submission_id, user_email, all_paths)

                if email_result.get('success'):
                    print(f"✅ Email sent to {user_email} with updated files")
                    print(f"✅ {email_result.get('files_uploaded', 0)} files uploaded to Google Drive")
                else:
                    print(f"⚠️ Email sending failed: {email_result.get('error', 'Unknown error')}")
            else:
                if not user_email:
                    print("⚠️ No email address, skipping notification")
                else:
                    print("⚠️ Email service unavailable, but files are ready for download")

            self.update_status(submission_id, "completed")

            print(f"\n{'='*60}")
            print(f"Regeneration completed successfully!")
            print(f"Regenerated {len(letter_indices)} letter(s)")
            print(f"{'='*60}\n")

        except Exception as e:
            error_msg = str(e)
            print(f"\n❌ Error during regeneration: {error_msg}")
            self.update_status(submission_id, "error", error_msg)
            raise
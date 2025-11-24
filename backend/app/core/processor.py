from .pdf_extractor import PDFExtractor
from .llm_processor import LLMProcessor
from .heterogeneity import HeterogeneityArchitect
from .block_generator import BlockGenerator
from .html_pdf_generator import HTMLPDFGenerator
from .logo_scraper import LogoScraper
from .email_sender import send_results_email, check_email_service_health
from .validation import validate_batch, print_validation_report
from ..db.database import Database
from ..ml.prompt_enhancer import PromptEnhancer
import os
import logging
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

# Configuration constants
MAX_PARALLEL_WORKERS = 5  # Maximum concurrent letter generation tasks
MIN_ML_TRAINING_SAMPLES = 5  # Minimum samples needed to train ML models
STORAGE_BASE_DIR = os.getenv('STORAGE_BASE_DIR', 'storage')  # Base storage directory


class SubmissionProcessor:
    def __init__(self):
        logger.info("Initializing SubmissionProcessor")
        self.pdf_extractor = PDFExtractor()
        self.llm = LLMProcessor()
        self.db = Database()
        self.prompt_enhancer = PromptEnhancer(self.db)
        
        # Try to train ML models with existing data
        try:
            logger.info(f"Attempting to train ML models with min {MIN_ML_TRAINING_SAMPLES} samples")
            self.prompt_enhancer.train_models(min_samples=MIN_ML_TRAINING_SAMPLES)
            logger.info("ML models trained successfully")
        except Exception as e:
            logger.info(f"ML training skipped (likely first run): {e}")

        # Initialize other components AFTER ML training
        self.heterogeneity = HeterogeneityArchitect(self.llm)
        self.block_generator = BlockGenerator(self.llm, self.prompt_enhancer)  # Pass ML enhancer
        self.pdf_generator = HTMLPDFGenerator()
        self.logo_scraper = LogoScraper()
        self.max_workers = MAX_PARALLEL_WORKERS
        logger.info(f"SubmissionProcessor initialized with {self.max_workers} parallel workers")
    
    def _generate_single_letter(self, submission_id: str, index: int, testimony: Dict, design: Dict, organized_data: Dict) -> Dict:
        """Helper function to generate a single letter, designed for parallel execution."""

        recommender_name = testimony.get('recommender_name', 'Unknown')
        print(f"\n  [START] Letter {index+1}: {recommender_name}")

        # 1. Fetch company logo (This is now done inside the parallel function)
        company_name = testimony.get('recommender_company', '')
        company_website = testimony.get('recommender_company_website')
        logo_path = None

        if company_name:
            logo_path = self.logo_scraper.get_company_logo(company_name, company_website)

        # 2. Generate 5 blocks
        print(f"    - Generating 5 blocks for {recommender_name}...")
        blocks = self.block_generator.generate_all_blocks(testimony, design, organized_data)
        print(f"    ✓ Blocks generated for {recommender_name}")

        # 3. Assemble letter
        print(f"    - Assembling letter for {recommender_name}...")
        letter_html = self.pdf_generator.assemble_letter(blocks, design, self.llm)
        print(f"    ✓ Letter assembled for {recommender_name}")

        # 4. Generate PDF and DOCX
        output_dir = os.path.join(STORAGE_BASE_DIR, "outputs", submission_id)
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"letter_{index+1}_{recommender_name.replace(' ', '_')}.pdf")
        print(f"    - Generating PDF for {recommender_name}...")

        recommender_info = {
            'name': recommender_name,
            'title': testimony.get('recommender_position', ''),
            'company': testimony.get('recommender_company', ''),
            'location': testimony.get('recommender_location', '')
        }

        self.pdf_generator.html_to_pdf(letter_html, output_path, design, logo_path, recommender_info)
        print(f"    ✓ PDF generated for {recommender_name}")

        docx_output_path = output_path.replace('.pdf', '.docx')
        print(f"    - Generating editable DOCX for {recommender_name}...")
        self.pdf_generator.html_to_docx(letter_html, docx_output_path, design, logo_path, recommender_info)

        # 6. Generate embedding for ML/clustering (unsupervised learning)
        print(f"    - Generating semantic embedding for {recommender_name}...")
        letter_embedding = self.prompt_enhancer.embedding_engine.generate_embedding(letter_html)
        if letter_embedding:
            self.db.save_letter_embedding(submission_id, index, letter_embedding)
            print(f"    ✓ Embedding saved for {recommender_name}")

        print(f"  [END] Letter {index+1}: {recommender_name}")

        # Return complete letter data
        return {
            "testimony_id": testimony.get('testimony_id', str(index+1)),
            "recommender": recommender_name,
            "pdf_path": output_path,
            "docx_path": docx_output_path,
            "template_id": template_id,
            "has_logo": logo_path is not None,
            "blocks": blocks,
            "letter_html": letter_html,
            "design": design,
            "embedding": letter_embedding,
            "index": index # Include original index for sorting
        }
    
    def update_status(self, submission_id: str, status: str, error: str | None = None):
        self.db.update_submission_status(submission_id, status, error)
        print(f"Submission {submission_id}: {status}")
    
    def process_submission(self, submission_id: str):
        try:
            print(f"\n{'='*60}")
            print(f"Starting processing for submission: {submission_id}")
            print(f"{'='*60}\n")
            
            self.update_status(submission_id, "extracting")
            print("PHASE 1: Extracting text from PDFs...")
            extracted_texts = self.pdf_extractor.extract_all_files(submission_id)
            print(f"✓ Extracted {len(extracted_texts.get('testimonials', []))} testimonials")
            
            self.update_status(submission_id, "organizing")
            print("\nPHASE 2: Cleaning and organizing data...")
            organized_data = self.llm.clean_and_organize(extracted_texts)
            print(f"✓ Organized data for {organized_data.get('petitioner', {}).get('name', 'Unknown')}")
            
            # PHASE 2.5: Logo scraping is now integrated into the parallel letter generation function.
            print("\nPHASE 2.5: Logo scraping will run in parallel with letter generation.")
            
            self.update_status(submission_id, "designing")
            print("\nPHASE 3: Generating design structures (Heterogeneity Architect)...")
            design_structures = self.heterogeneity.generate_design_structures(organized_data)
            print(f"✓ Generated {len(design_structures.get('design_structures', []))} unique designs")
            
            self.update_status(submission_id, "generating")
            print("\nPHASE 4: Generating letters...")
            letters = []
            
            testimonies = organized_data.get('testimonies', [])
            designs = design_structures.get('design_structures', [])
            
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
                tasks.append((submission_id, i, testimony, design, organized_data))
            
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
            
            # Retrain ML models periodically (every 10 submissions) instead of every time
            # This significantly improves performance
            total_submissions = self.db.get_total_submissions_count()
            if total_submissions % 10 == 0:
                logger.info(f"Triggering ML model retraining at {total_submissions} submissions")
                print("\n🧠 Re-training ML models with new data...")
                try:
                    self.prompt_enhancer.train_models(min_samples=MIN_ML_TRAINING_SAMPLES)
                    logger.info("ML models retrained successfully")
                except Exception as e:
                    logger.warning(f"ML training failed: {e}")
                    print(f"   ℹ️  ML training skipped: {e}")
            else:
                logger.debug(f"Skipping ML retraining (will retrain at next multiple of 10)")
            
            print(f"\n{'='*60}")
            print(f"✓ COMPLETED! Generated {len(letters)} PDF + DOCX letters")
            print(f"{'='*60}\n")
            
            # PHASE 5: Send email with Google Drive links (both PDF and DOCX)
            submission = self.db.get_submission(submission_id)
            recipient_email = submission.get('email') if submission else None
            
            if recipient_email and check_email_service_health() and len(successful_letters) > 0:
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
                    if len(failed_letters) > 0:
                        print(f"⚠️  Note: {len(failed_letters)} letter(s) failed and were not included in the email")
                else:
                    print(f"⚠️ Email sending failed: {email_result.get('error', 'Unknown error')}")
            else:
                if not recipient_email:
                    print("⚠️ No email address provided, skipping email notification")
                elif len(successful_letters) == 0:
                    print("⚠️ No successful letters to send, skipping email notification")
                else:
                    print("⚠️ Email service not available, skipping email notification")
            
            return {"success": True, "letters": letters}
            
        except Exception as e:
            error_msg = str(e)
            print(f"\n✗ ERROR: {error_msg}\n")
            self.update_status(submission_id, "error", error_msg)
            raise
    
    def regenerate_specific_letters(
        self, 
        submission_id: str, 
        letter_indices: list[int],
        custom_instructions: str | None = None
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
                
                print(f"\n  Letter {letter_idx + 1}/{len(testimonials)}: {testimony.get('recommender_name', 'Unknown')}")
                
                # Generate blocks (with ML enhancement)
                context = {
                    'petitioner': organized_data.get('petitioner', {}),
                    'strategy': organized_data.get('strategy', {}),
                    'onet': organized_data.get('onet', {})
                }
                blocks = self.block_generator.generate_all_blocks(testimony, design, context)
                
                # Assemble letter
                print("    - Assembling letter...")
                letter_html = self.pdf_generator.assemble_letter(blocks, design, self.llm)
                print(f"✅ Letter assembled (Template {design.get('template_id', 'A')})")
                
                # Get logo if available
                logo_path = testimony.get('company_logo_path')
                
                # Generate PDF (use same naming as process_submission)
                output_path = f"{output_dir}/letter_{letter_idx + 1}_{testimony.get('recommender_name', 'unknown').replace(' ', '_')}.pdf"
                
                recommender_info = {
                    'name': testimony.get('recommender_name', ''),
                    'title': testimony.get('recommender_title', ''),
                    'company': testimony.get('recommender_company', ''),
                    'location': testimony.get('recommender_location', '')
                }
                
                self.pdf_generator.html_to_pdf(letter_html, output_path, design, logo_path, recommender_info)
                print(f"    ✓ Regenerated PDF with Template {design.get('template_id', 'A')}")
                
                # Track template usage
                template_id = design.get('template_id', 'A')
                self.db.increment_template_usage(template_id)
                
                # Update letter info
                existing_letters[letter_idx].update({
                    "pdf_path": output_path,
                    "template_id": template_id,
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
                pdf_paths = [os.path.abspath(letter['pdf_path']) for letter in existing_letters]
                email_result = send_results_email(submission_id, user_email, pdf_paths)
                
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

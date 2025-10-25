from .pdf_extractor import PDFExtractor
from .llm_processor import LLMProcessor
from .heterogeneity import HeterogeneityArchitect
from .block_generator import BlockGenerator
from .html_pdf_generator import HTMLPDFGenerator
from .logo_scraper import LogoScraper
from .email_sender import send_results_email, check_email_service_health
from ..db.database import Database
import os
from typing import Dict


class SubmissionProcessor:
    def __init__(self):
        self.pdf_extractor = PDFExtractor()
        self.llm = LLMProcessor()
        self.heterogeneity = HeterogeneityArchitect(self.llm)
        self.block_generator = BlockGenerator(self.llm)
        self.pdf_generator = HTMLPDFGenerator()
        self.logo_scraper = LogoScraper()
        self.db = Database()
    
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
            
            # PHASE 2.5: Scrape company logos
            print("\nPHASE 2.5: Scraping company logos...")
            for i, testimonial in enumerate(organized_data.get('testimonials', [])):
                company_name = testimonial.get('recommender_company', '')
                company_website = testimonial.get('recommender_company_website', '')
                
                if company_name:
                    logo_path = self.logo_scraper.get_company_logo(company_name, company_website)
                    if logo_path:
                        organized_data['testimonials'][i]['company_logo_path'] = logo_path
                        print(f"  ✓ Logo found for {company_name}")
                    else:
                        print(f"  ⚠️ No logo found for {company_name}")
            
            self.update_status(submission_id, "designing")
            print("\nPHASE 3: Generating design structures (Heterogeneity Architect)...")
            design_structures = self.heterogeneity.generate_design_structures(organized_data)
            print(f"✓ Generated {len(design_structures.get('design_structures', []))} unique designs")
            
            self.update_status(submission_id, "generating")
            print("\nPHASE 4: Generating letters...")
            letters = []
            
            testimonies = organized_data.get('testimonies', [])
            designs = design_structures.get('design_structures', [])
            
            for i, testimony in enumerate(testimonies):
                design = designs[i] if i < len(designs) else designs[0]
                
                print(f"\n  Letter {i+1}/{len(testimonies)}: {testimony.get('recommender_name', 'Unknown')}")
                
                # Fetch company logo
                company_name = testimony.get('recommender_company', '')
                company_website = testimony.get('recommender_company_website')
                logo_path = None
                
                if company_name:
                    logo_path = self.logo_scraper.get_company_logo(company_name, company_website)
                
                print("    - Generating 5 blocks...")
                blocks = self.block_generator.generate_all_blocks(testimony, design, organized_data)
                print("    ✓ Blocks generated")
                
                print("    - Assembling letter with Claude 4.5 Sonnet...")
                letter_html = self.pdf_generator.assemble_letter(blocks, design, self.llm)
                print("    ✓ Letter assembled")
                
                # Generate PDF with heterogeneous HTML templates
                output_path = f"storage/outputs/{submission_id}/letter_{i+1}_{testimony.get('recommender_name', 'unknown').replace(' ', '_')}.pdf"
                print(f"    - Generating styled PDF (Template {design.get('template_id', 'A')})...")
                
                # Prepare recommender info for template
                recommender_info = {
                    'name': testimony.get('recommender_name', 'Professional Recommender'),
                    'title': testimony.get('recommender_position', ''),
                    'company': testimony.get('recommender_company', ''),
                    'location': testimony.get('recommender_location', '')
                }
                
                self.pdf_generator.html_to_pdf(letter_html, output_path, design, logo_path, recommender_info)
                print(f"    ✓ Styled PDF generated with Template {design.get('template_id', 'A')}")
                
                # Track template usage for ML/analytics
                template_id = design.get('template_id', 'A')
                self.db.increment_template_usage(template_id)
                
                letters.append({
                    "testimony_id": testimony.get('testimony_id', str(i+1)),
                    "recommender": testimony.get('recommender_name', 'Unknown'),
                    "pdf_path": output_path,
                    "template_id": template_id,
                    "has_logo": logo_path is not None
                })
            
            self.update_status(submission_id, "completed")
            self.db.save_processed_data(submission_id, {
                "letters": letters,
                "organized_data": organized_data
            })
            
            print(f"\n{'='*60}")
            print(f"✓ COMPLETED! Generated {len(letters)} styled PDF letters")
            print(f"{'='*60}\n")
            
            # PHASE 5: Send email with Google Drive links
            submission = self.db.get_submission(submission_id)
            recipient_email = submission.get('email') if submission else None
            
            if recipient_email and check_email_service_health():
                print("\nPHASE 5: Sending results via email and Google Drive...")
                pdf_paths = [os.path.abspath(letter['pdf_path']) for letter in letters]
                email_result = send_results_email(submission_id, recipient_email, pdf_paths)
                
                if email_result.get('success'):
                    print(f"✅ Email sent to {recipient_email}")
                    print(f"✅ {email_result.get('files_uploaded', 0)} files uploaded to Google Drive")
                else:
                    print(f"⚠️ Email sending failed: {email_result.get('error', 'Unknown error')}")
            else:
                if not recipient_email:
                    print("⚠️ No email address provided, skipping email notification")
                else:
                    print("⚠️ Email service not available, skipping email notification")
            
            return {"success": True, "letters": letters}
            
        except Exception as e:
            error_msg = str(e)
            print(f"\n✗ ERROR: {error_msg}\n")
            self.update_status(submission_id, "error", error_msg)
            raise

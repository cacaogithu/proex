from .pdf_extractor import PDFExtractor
from .llm_processor import LLMProcessor
from .heterogeneity import HeterogeneityArchitect
from .block_generator import BlockGenerator
from .docx_generator import DOCXGenerator
from .logo_scraper import LogoScraper
from ..db.database import Database
import os
from typing import Dict


class SubmissionProcessor:
    def __init__(self):
        self.pdf_extractor = PDFExtractor()
        self.llm = LLMProcessor()
        self.heterogeneity = HeterogeneityArchitect(self.llm)
        self.block_generator = BlockGenerator(self.llm)
        self.docx_generator = DOCXGenerator()
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
                letter_markdown = self.docx_generator.assemble_letter(blocks, design, self.llm)
                print("    ✓ Letter assembled")
                
                # Generate DOCX instead of PDF
                output_path = f"backend/storage/outputs/{submission_id}/letter_{i+1}_{testimony.get('recommender_name', 'unknown').replace(' ', '_')}.docx"
                print(f"    - Generating DOCX with logo...")
                self.docx_generator.markdown_to_docx(letter_markdown, output_path, design, logo_path)
                print(f"    ✓ DOCX generated")
                
                letters.append({
                    "testimony_id": testimony.get('testimony_id', str(i+1)),
                    "recommender": testimony.get('recommender_name', 'Unknown'),
                    "docx_path": output_path,
                    "has_logo": logo_path is not None
                })
            
            self.update_status(submission_id, "completed")
            self.db.save_processed_data(submission_id, {
                "letters": letters,
                "organized_data": organized_data
            })
            
            print(f"\n{'='*60}")
            print(f"✓ COMPLETED! Generated {len(letters)} editable DOCX letters")
            print(f"{'='*60}\n")
            
            return {"success": True, "letters": letters}
            
        except Exception as e:
            error_msg = str(e)
            print(f"\n✗ ERROR: {error_msg}\n")
            self.update_status(submission_id, "error", error_msg)
            raise

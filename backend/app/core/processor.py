from .pdf_extractor import PDFExtractor
from .llm_processor import LLMProcessor
from .heterogeneity import HeterogeneityArchitect
from .block_generator import BlockGenerator
from .pdf_generator import PDFGenerator
from ..db.database import Database
import os
from typing import Dict


class SubmissionProcessor:
    def __init__(self):
        self.pdf_extractor = PDFExtractor()
        self.llm = LLMProcessor()
        self.heterogeneity = HeterogeneityArchitect(self.llm)
        self.block_generator = BlockGenerator(self.llm)
        self.pdf_generator = PDFGenerator()
        self.db = Database()
    
    def update_status(self, submission_id: str, status: str, error: str = None):
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
                
                print("    - Generating 5 blocks...")
                blocks = self.block_generator.generate_all_blocks(testimony, design, organized_data)
                print("    ✓ Blocks generated")
                
                print("    - Assembling letter...")
                letter_markdown = self.pdf_generator.assemble_letter(blocks, design, self.llm)
                print("    ✓ Letter assembled")
                
                output_path = f"backend/storage/outputs/{submission_id}/letter_{i+1}_{testimony.get('recommender_name', 'unknown').replace(' ', '_')}.pdf"
                print(f"    - Generating PDF...")
                self.pdf_generator.markdown_to_pdf(letter_markdown, output_path, design)
                print(f"    ✓ PDF generated")
                
                letters.append({
                    "testimony_id": testimony.get('testimony_id', str(i+1)),
                    "recommender": testimony.get('recommender_name', 'Unknown'),
                    "pdf_path": output_path
                })
            
            self.update_status(submission_id, "completed")
            self.db.save_processed_data(submission_id, {
                "letters": letters,
                "organized_data": organized_data
            })
            
            print(f"\n{'='*60}")
            print(f"✓ COMPLETED! Generated {len(letters)} letters")
            print(f"{'='*60}\n")
            
            return {"success": True, "letters": letters}
            
        except Exception as e:
            error_msg = str(e)
            print(f"\n✗ ERROR: {error_msg}\n")
            self.update_status(submission_id, "error", error_msg)
            raise

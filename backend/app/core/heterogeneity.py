from typing import Dict, List
import json
import random
import time


class HeterogeneityArchitect:
    """Generates dynamic heterogeneous designs WITHOUT templates - pure variation"""
    def __init__(self, llm_processor):
        self.llm = llm_processor
    
    def _format_testimonies(self, testimonies: List[Dict]) -> str:
        formatted = []
        for i, t in enumerate(testimonies):
            formatted.append(f"""
Testemunho {i+1}:
- Recomendador: {t.get('recommender_name', 'N/A')}
- Empresa: {t.get('recommender_company', 'N/A')}
- Cargo: {t.get('recommender_role', 'N/A')}
- Período: {t.get('collaboration_period', 'N/A')}
""")
        return "\n".join(formatted)
    
    def generate_design_structures(self, organized_data: Dict) -> Dict:
        """Generate UNIQUE heterogeneous designs for each testimony"""
        testimonies = organized_data.get('testimonies', [])
        num_testimonies = len(testimonies)
        
        if num_testimonies == 0:
            raise ValueError("Nenhum testemunho encontrado")
        
        # Create truly unique design variations using randomized axes
        design_structures = []
        
        for i, testimony in enumerate(testimonies):
            # Generate unique design based on testimony characteristics
            unique_seed = hash(testimony.get('recommender_name', '') + str(i)) % 100
            random.seed(unique_seed)
            
            # Create heterogeneous design parameters
            design = {
                'index': i,
                'recommender_name': testimony.get('recommender_name', 'Unknown'),
                'recommender_role': testimony.get('recommender_role', 'Unknown'),
                # Randomized tone instruction
                'tone_instructions': random.choice([
                    'Technical expert providing detailed analysis',
                    'Strategic leader sharing business perspective',
                    'Operational manager describing achievements',
                    'Academic professional with formal approach',
                    'Direct pragmatist focusing on results'
                ]),
                # Randomized structure
                'structure_format': random.choice([
                    'Analytical with data-driven sections',
                    'Narrative flowing from challenge to solution',
                    'Structured case study format',
                    'Testimonial with personal observations',
                    'Professional assessment with metrics'
                ]),
                # Randomized opening style
                'opening_style': random.choice([
                    'Start with specific technical context',
                    'Begin with business challenge',
                    'Open with collaboration background',
                    'Introduce formal professional context',
                    'Present key achievement upfront'
                ]),
                # Randomized paragraph style
                'paragraph_style': random.choice([
                    'Short, punchy paragraphs with metrics',
                    'Flowing, narrative-style paragraphs',
                    'Academic-style with structured sections',
                    'Mixed short and long paragraphs',
                    'Detailed explanatory paragraphs'
                ]),
                # Randomized technical depth
                'technical_depth': random.choice(['HIGH', 'MEDIUM', 'MEDIUM-HIGH', 'LOW-MEDIUM']),
                # Randomized visual elements
                'visual_elements': random.choice([
                    'Minimal, text-only',
                    'Simple section breaks',
                    'Professional spacing',
                    'Light visual hierarchy',
                    'Clear structure with emphasis'
                ]),
                # Unique features based on combination
                'unique_features': [
                    f"Voice: {random.choice(['technical', 'strategic', 'narrative', 'formal', 'pragmatic'])}",
                    f"Focus: {random.choice(['expertise', 'results', 'transformation', 'partnership', 'innovation'])}"
                ]
            }
            
            design_structures.append(design)
        
        return {
            "petitioner_name": organized_data.get('petitioner', {}).get('name', 'Unknown'),
            "testimony_count": num_testimonies,
            "heterogeneity_strategy": "Dynamic variation without templates - each letter unique",
            "design_structures": design_structures
        }

from typing import Dict, List
import json
import time
import random


class StyleBlueprintGenerator:
    """Generates unique style blueprints dynamically without templates"""
    def __init__(self, llm_processor):
        self.llm = llm_processor
        
        # Style dimensions for dynamic generation (no templates!)
        self.style_axes = {
            'voice_intensity': ['technical-precise', 'strategic-analytical', 'narrative-conversational', 'formal-academic', 'direct-pragmatic'],
            'structure_pattern': ['methodical-sections', 'problem-solution-flow', 'chronological-journey', 'evidence-clusters', 'comparison-contrast'],
            'metric_emphasis': ['hyper-quantitative', 'balanced-quali-quant', 'transformation-focused', 'roi-centered', 'innovation-driven'],
            'formality_level': ['ultra-formal', 'professional-standard', 'accessible-clear', 'conversational-warm', 'executive-concise'],
            'visual_density': ['dense-technical', 'structured-readable', 'flowing-narrative', 'bulleted-scannable', 'mixed-dynamic']
        }
    
    def _format_testimonies(self, testimonies: List[Dict]) -> str:
        formatted = []
        for i, t in enumerate(testimonies):
            formatted.append(f"""
Testemunho {i+1}:
- Recomendador: {t.get('recommender_name', 'N/A')}
- Empresa: {t.get('recommender_company', 'N/A')}
- Cargo: {t.get('recommender_role', 'N/A')}
- Período: {t.get('collaboration_period', 'N/A')}
- Texto: {t.get('testimony_text', '')[:200]}...
""")
        return "\n".join(formatted)
    
    def generate_style_blueprints(self, organized_data: Dict) -> Dict:
        """Generate unique style blueprints dynamically (NO TEMPLATES!)"""
        testimonies = organized_data.get('testimonies', [])
        num_testimonies = len(testimonies)
        
        if num_testimonies == 0:
            raise ValueError("Nenhum testemunho encontrado")
        
        # Generate unique style combinations for each testimony
        style_blueprints = []
        used_combinations = set()
        
        for i, testimony in enumerate(testimonies):
            # Ensure unique combination for each letter
            while True:
                voice = random.choice(self.style_axes['voice_intensity'])
                structure = random.choice(self.style_axes['structure_pattern'])
                metrics = random.choice(self.style_axes['metric_emphasis'])
                formality = random.choice(self.style_axes['formality_level'])
                visual = random.choice(self.style_axes['visual_density'])
                
                combination = f"{voice}-{structure}-{metrics}"
                if combination not in used_combinations or len(used_combinations) >= 25:
                    used_combinations.add(combination)
                    break
            
            style_blueprints.append({
                'index': i,
                'recommender_name': testimony.get('recommender_name', 'Unknown'),
                'recommender_role': testimony.get('recommender_role', 'Unknown'),
                'voice_style': voice,
                'structure_pattern': structure,
                'metric_emphasis': metrics,
                'formality_level': formality,
                'visual_density': visual,
                'unique_id': f"STYLE_{i+1}_{voice[:4].upper()}",
                'tone_instructions': f"Write in {voice} voice with {formality} tone",
                'paragraph_style': f"Use {visual} formatting with {structure}",
                'persona_description': f"A {formality} professional with {voice} communication style",
                'opening_style': f"Begin with {structure} approach",
                'technical_depth': 'HIGH' if 'technical' in voice else 'MEDIUM',
                'unique_features': [
                    f"Primary voice: {voice}",
                    f"Structure: {structure}",
                    f"Emphasis: {metrics}"
                ]
            })
        
        # Return the dynamically generated style blueprints
        return {
            "petitioner_name": organized_data.get('petitioner', {}).get('name', 'Unknown'),
            "testimony_count": num_testimonies,
            "heterogeneity_strategy": "Dynamic style blueprint generation with 5 axes of variation (no templates)",
            "design_structures": style_blueprints
        }
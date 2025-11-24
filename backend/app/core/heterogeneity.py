from typing import Dict, List
import json
import time
import random


class DynamicPersonaGenerator:
    """
    Generates COMPLETELY UNIQUE personas for each letter.
    NO templates. NO A-F. Every letter is dynamically generated.
    """
    def __init__(self, llm_processor):
        self.llm = llm_processor
    
    # Persona components - mix and match randomly
    TONES = [
        "Authoritative & Credentialed Expert",
        "Collaborative Partnership-Focused Leader",
        "Visionary Strategic Thinker",
        "Analytical Data-Driven Professional",
        "Mentorship & Development-Oriented",
        "Pragmatic Results-Focused Operator",
        "Innovation & Research-Oriented Academic"
    ]
    
    STRUCTURES = [
        "Chronological Journey (timeline-based narrative)",
        "Problem-Solution Framework (challenge → resolution)",
        "Impact-First (results upfront, then context)",
        "Competency-Based (skill demonstration → evidence)",
        "Narrative Storytelling (immersive, engaging flow)",
        "Technical Documentation (precise, specification-heavy)",
        "Strategic Analysis (business case format)"
    ]
    
    VOCABULARIES = [
        "Academic & Research-Oriented",
        "Industry-Specific Technical Jargon",
        "Executive & C-Suite Strategic",
        "Operational & Tactical Field Language",
        "Engineering & Specifications-Heavy",
        "Business Development & Commercial",
        "Innovation & Startup Ecosystem"
    ]
    
    EMPHASIS_AREAS = [
        "Technical Excellence & Innovation",
        "Leadership & Team Building",
        "Business Impact & ROI",
        "Problem Solving & Critical Thinking",
        "Research & Academic Contributions",
        "Operational Efficiency & Process Optimization",
        "Strategic Vision & Market Positioning"
    ]
    
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
        return "\\n".join(formatted)
    
    def generate_design_structures(self, organized_data: Dict) -> Dict:
        """
        Generate UNIQUE persona for each letter.
        NO template references. Each design is generated from scratch.
        """
        testimonies = organized_data.get('testimonies', [])
        num_testimonies = len(testimonies)
        
        if num_testimonies == 0:
            raise ValueError("Nenhum testemunho encontrado")
        
        # Shuffle to ensure randomness across calls
        random.seed(time.time())
        
        prompt = f"""# CRITICAL MISSION: MAXIMUM HETEROGENEITY - DYNAMIC PERSONA GENERATION

Você é o `DynamicPersonaGenerator`. Sua missão é criar {num_testimonies} PERSONAS COMPLETAMENTE ÚNICAS, uma para cada carta.

🚨 REGRA DE OURO: Cada carta deve ter uma IDENTIDADE ÚNICA gerada dinamicamente.
    NÃO use templates fixos. 
    CADA persona é uma NOVA COMBINAÇÃO de características.

# CONTEXTO DO PETICIONÁRIO
OneNet: {json.dumps(organized_data.get('onet', {}), ensure_ascii=False)}
Strategy: {json.dumps(organized_data.get('strategy', {}), ensure_ascii=False)}
Petitioner: {json.dumps(organized_data.get('petitioner', {}), ensure_ascii=False)}

# TESTEMUNHOS DISPONÍVEIS
{self._format_testimonies(testimonies)}

# COMPONENTES DISPONÍVEIS PARA COMBINAÇÃO DINÂMICA

## Tons Disponíveis
{json.dumps(self.TONES, ensure_ascii=False, indent=2)}

## Estruturas Disponíveis  
{json.dumps(self.STRUCTURES, ensure_ascii=False, indent=2)}

## Vocabulários Disponíveis
{json.dumps(self.VOCABULARIES, ensure_ascii=False, indent=2)}

## Áreas de Ênfase
{json.dumps(self.EMPHASIS_AREAS, ensure_ascii=False, indent=2)}

# SUA TAREFA

Para CADA um dos {num_testimonies} testemunhos:
1. ESCOLHA ALEATORIAMENTE (mas strategicamente) uma combinação ÚNICA de:
   - 1 Tom
   - 1 Estrutura
   - 1 Vocabulário
   - 1-2 Áreas de Ênfase
2. CRIE instruções SUPER ESPECÍFICAS para essa combinação única
3. GARANTA que nenhuma combinação se repita

**REGRAS CRÍTICAS**:
- Todas as {num_testimonies} personas devem ser DIFERENTES
- Use combinações CRIATIVAS (não apenas pegar listas em ordem)
- Instrução deve ser TÃO DETALHADA que force uma escrita única

Para cada testemunho gere:

{{
  "persona_id": "[Identificador único: ex. 'strategic-analyst-001']",
  "assigned_recommender": "[Nome completo do recomendador]",
  "recommender_role": "[Cargo do recomendador]",
  
  "tone": "[Tom escolhido da lista - cite qual]",
  "structure": "[Estrutura escolhida da lista - cite qual]",
  "vocabulary": "[Vocabulário escolhido da lista - cite qual]",
  "emphasis": ["Ênfase 1", "Ênfase 2"],
  
  "persona_description": "[Descrição DETALHADA: quem é essa persona, seu background, sua motivação para escrever essa carta]",
  
  "writing_instructions": "[INSTRUÇÕES SUPER ESPECÍFICAS: como essa persona escreve, que tipo de linguagem usa, como estrutura parágrafos, que elementos visuais prefere]",
  
  "opening_strategy": "[Como essa persona específica começaria a carta - seja MUITO específico]",
  
  "paragraph_style": "[Descrição de como essa persona constrói parágrafos]",
  
  "technical_depth": "[ALTO / MÉDIO / BAIXO - baseado na persona]",
  
  "unique_characteristics": [
    "[Característica única 1 dessa combinação específica]",
    "[Característica única 2 dessa combinação específica]",
    "[Característica única 3 dessa combinação específica]"
  ],
  
  "forbidden_approaches": "[O que essa persona NÃO faria - para garantir diferença das outras]",
  
  "target_word_count": "[número entre 2000-3000]",
  
  "key_differentiator": "[O que torna ESTA carta radicalmente diferente das outras]"
}}

# OUTPUT FINAL

Retorne APENAS JSON válido (sem markdown, sem ```json):

{{
  "petitioner_name": "{organized_data.get('petitioner', {}).get('name', 'Unknown')}",
  "testimony_count": {num_testimonies},
  "generation_approach": "Dynamic Persona Generation (NO fixed templates)",
  "heterogeneity_validation": "[Confirme que todas as {num_testimonies} personas são únicas e como garantiu isso]",
  "design_structures": [
    {{...}},
    {{...}}
  ]
}}

**CHECKPOINT FINAL**:
✓ Há exatamente {num_testimonies} design_structures?
✓ Nenhuma combinação (tone + structure + vocabulary) se repete?
✓ Cada persona tem instruções radicalmente distintas?
✓ Você consegue EXPLICAR por que cada carta seria diferente?
"""
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.llm.client.chat.completions.create(
                    model=self.llm.models["quality"],
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                    temperature=0.9  # Higher randomness for diversity
                )
                
                content = response.choices[0].message.content
                result = json.loads(content)
                
                # Validation: count must match
                design_structures = result.get('design_structures', [])
                if len(design_structures) != num_testimonies:
                    print(f"⚠️  Count mismatch: expected {num_testimonies}, got {len(design_structures)}")
                    if attempt < max_retries - 1:
                        time.sleep(2)
                        continue
                    raise ValueError(f"Expected {num_testimonies} design_structures")
                
                # Validation: Check for duplicate combinations
                combinations = []
                for ds in design_structures:
                    combo = f"{ds.get('tone', '')}|{ds.get('structure', '')}|{ds.get('vocabulary', '')}"
                    combinations.append(combo)
                
                if len(set(combinations)) != len(combinations):
                    print(f"⚠️  Duplicate persona combinations detected")
                    if attempt < max_retries - 1:
                        print(f"   Regenerating with unique combinations... (attempt {attempt + 2}/{max_retries})")
                        time.sleep(2)
                        continue
                    # Allow it but warn
                    print("⚠️  Warning: Some personas may be similar")
                
                # Success!
                print(f"✅ Dynamic personas generated: {num_testimonies} unique combinations")
                print(f"   Approach: Dynamic Persona Generation (NO templates)")
                return result
                
            except json.JSONDecodeError as e:
                print(f"⚠️  JSON decode error: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                raise
            except Exception as e:
                if "429" in str(e) and attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 3
                    print(f"⏳ Rate limit, waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                if attempt == max_retries - 1:
                    print(f"❌ Error after {max_retries} attempts: {str(e)}")
                    raise
        
        return {}


# Backward compatibility alias
HeterogeneityArchitect = DynamicPersonaGenerator

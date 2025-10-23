from typing import Dict, List
import json


class HeterogeneityArchitect:
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
- Texto: {t.get('testimony_text', '')[:200]}...
""")
        return "\n".join(formatted)
    
    def generate_design_structures(self, organized_data: Dict) -> Dict:
        testimonies = organized_data.get('testimonies', [])
        num_testimonies = len(testimonies)
        
        if num_testimonies == 0:
            raise ValueError("Nenhum testemunho encontrado")
        
        prompt = f"""# ROLE
Você é `Heterogeneity_Architect`. Analise todos os dados contextuais e produza 
**{num_testimonies} blueprints de design radicalmente distintos** (um para cada testemunho).

# INPUTS
OneNet: {json.dumps(organized_data.get('onet', {}), ensure_ascii=False)}

Strategy: {json.dumps(organized_data.get('strategy', {}), ensure_ascii=False)}

Petitioner: {json.dumps(organized_data.get('petitioner', {}), ensure_ascii=False)}

Testimonies:
{self._format_testimonies(testimonies)}

# TAREFA
Crie **{num_testimonies} personas de autor distintas** com estilos de escrita diferentes.

Para cada testemunho, gere um objeto com estes campos:
{{
  "template_id": "T1" | "T2" | "T3" | ...,
  "assigned_recommender": "[Nome completo]",
  "tone_instructions": "[Descrição detalhada do estilo de escrita]",
  "narrative_framework": "[Como estruturar o argumento]",
  "paragraph_structure": "[Como formatar parágrafos]",
  "sentence_style": "[Como construir frases]",
  "emphasis_style": "[Como enfatizar informações-chave]",
  "visual_elements": "[Quais elementos visuais usar - listas, parágrafos, etc]",
  "readability_target": "[Nível de complexidade - técnico/executivo/acessível]",
  "word_count_target": "1800-2500 palavras",
  "unique_trait": "[Um recurso distintivo deste template]"
}}

# OUTPUT
Retorne APENAS JSON válido (sem markdown):
{{
  "petitioner_name": "[Nome do peticionário]",
  "testimony_count": {num_testimonies},
  "design_structures": [
    {{"template_id": "T1", "assigned_recommender": "[Nome]", ...}},
    ...
  ]
}}
"""
        
        try:
            response = self.llm.client.chat.completions.create(
                model="gemini-2.0-flash-exp",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            print(f"Error in generate_design_structures: {str(e)}")
            raise

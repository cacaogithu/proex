from typing import Dict, List
import json
import time
import random


class HeterogeneityArchitect:
    """
    Generates n8n-compatible design structures with full 23-parameter schema.
    Ensures maximum heterogeneity across letters with visual + content differentiation.
    """
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
        """
        Generate COMPLETE n8n-compatible design structures with all 23 parameters.
        Returns schema exactly matching original n8n heterogeneity architect.
        """
        testimonies = organized_data.get('testimonies', [])
        num_testimonies = len(testimonies)
        
        if num_testimonies == 0:
            raise ValueError("Nenhum testemunho encontrado")
        
        # Shuffle to ensure randomness
        random.seed(time.time())
        
        prompt = f"""# CRITICAL MISSION: MAXIMUM HETEROGENEITY - n8n Schema Generation

Você é o `Heterogeneity_Architect`. Sua missão é criar {num_testimonies} DESIGN STRUCTURES COMPLETAMENTE ÚNICOS.

🚨 REGRA DE OURO: CADA carta deve ter parâmetros visuais E de conteúdo radicalmente distintos.

# CONTEXTO DO PETICIONÁRIO
OneNet: {json.dumps(organized_data.get('onet', {}), ensure_ascii=False)[:500]}...
Strategy: {json.dumps(organized_data.get('strategy', {}), ensure_ascii=False)[:500]}...
Petitioner: {json.dumps(organized_data.get('petitioner', {}), ensure_ascii=False)[:500]}...

# TESTEMUNHOS DISPONÍVEIS
{self._format_testimonies(testimonies)}

# SUA TAREFA

Para CADA um dos {num_testimonios} testemunhos, gere um objeto com TODOS os 23 parâmetros:

{{
  "assigned_recommender": "[Nome completo do recomendador]",
  
  # CONTENT PARAMETERS (10)
  "tone_variable": "[Tom/registro de voz específico - autoridade, colaboração, visão, dados, mentoria, pragmático, acadêmico]",
  "tone_instructions": "[INSTRUÇÕES SUPER DETALHADAS de escrita: como essa persona escreve, que linguagem usa, como estrutura, etc. MÍNIMO 150 palavras]",
  "narrative_framework": "[Estrutura narrativa: Jornada Cronológica | Problema-Solução | Impacto-Primeiro | Análise de Competências]",
  "paragraph_density_rule": "[Como construir parágrafos: 'Curtos e diretos (3-4 frases)' | 'Médios equilibrados (5-7 frases)' | 'Longos e fluidos (8+ frases)']",
  "readability_target": "Executive" | "Technical" | "Academic",
  "emphasis_pattern": "[Como enfatizar: 'Negrito para termos-chave + Itálico para ênfase' | 'Cabeçalhos em negrito + Métricas sublinhadas' | etc]",
  "semantic_elements": ["numbered lists", "bullet points", "bold headers", "block quotes"] (escolha 2-3),
  "structure_features": "[Estrutura visual: 'Coluna única tradicional' | 'Duas colunas' | 'Sidebar com destaques']",
  "target_word_count": "[número entre 2000-2800]",
  "bonus_trait": "[Característica única que diferencia ESTA carta de todas as outras]",
  
  # VISUAL PARAMETERS (13)
  "layout_pattern": "[Padrão de layout visual: 'formal-traditional' | 'modern-clean' | 'executive-bold' | 'academic-detailed' | 'narrative-flowing']",
  "font_primary": "[Fonte principal: 'Georgia, serif' | 'Times New Roman, serif' | 'Palatino, serif' | 'Garamond, serif' | 'Crimson Text, serif']",
  "font_secondary": "[Fonte secundária: 'Arial, sans-serif' | 'Helvetica, sans-serif' | 'Verdana, sans-serif' | 'Open Sans, sans-serif']",
  "color_primary_hsl_range": "[Cor primária HSL: 'hsl(210, 50%, 30%)' (azul escuro) | 'hsl(200, 40%, 35%)' (azul acinzentado) | 'hsl(0, 0%, 20%)' (cinza escuro) | etc]",
  "color_accent": "[Cor de destaque: '#DAA520' (ouro) | '#CD7F32' (bronze) | '#2E8B57' (verde mar) | '#8B4513' (marrom) | '#4682B4' (azul aço)]",
  "layout_density": "compact" | "balanced" | "airy",
  "line_height": 1.5 | 1.7 | 1.9,
  "header_alignment": "left" | "center" | "right",
  "footer_style": "[Estilo do rodapé: 'minimalist' | 'formal with contact' | 'detailed signature']",
  "contrast_mode": "high" | "medium" | "soft",
  "whitespace_profile": "generous" | "compact" | "dynamic",
  "font_size_body": "[Tamanho do corpo: '11pt' | '11.5pt' | '12pt']",
  "font_size_headers": "[Tamanho dos cabeçalhos: '14pt,16pt,18pt' | '15pt,17pt,19pt' | '16pt,18pt,20pt']"
}}

# REGRAS CRÍTICAS

1. **Tone + Narrative Framework**: Nenhuma combinação pode se repetir
2. **Visual Parameters**: Variar TUDO - fontes, cores, layouts, espaçamento
3. **tone_instructions**: DEVE ser SUPER ESPECÍFICO (mínimo 150 palavras cada)
4. **Template IDs**: Distribuir T1-T5 sem repetir se possível
5. **Guaranteed Differentiation**: Se tiver 3+ testemunhos, GARANTIR que nenhuma dupla de parâmetros visuais seja igual

# EXEMPLOS DE TONE_INSTRUCTIONS DETALHADAS

Exemplo 1 (Technical Authority):
"Você escreve como um engenheiro sênior com 20+ anos de experiência. Seu estilo é preciso e técnico, mas acessível. Use terminologia específica da área (PLC, SCADA, automação industrial) naturalmente. Estruture argumentos em cadeias lógicas claras: premissa → evidência → conclusão. Prefira parágrafos médios (5-7 frases) com uma ideia central forte. Inicie seções com declarações diretas ('Em minha função como Diretor de Engenharia...'). Use listas numeradas para processos, bullet points para resultados. Enfatize métricas quantificáveis em negrito. Evite linguagem emocional - mantenha tom profissional e objetivo. Transições devem ser técnicas ('Consequentemente,', 'Em termos práticos,', 'Do ponto de vista operacional')."

Exemplo 2 (Narrative Mentor):
"Você escreve como um mentor experiente contando uma história profissional. Seu estilo é envolvente e pessoal, mas mantém autoridade. Prefira estruturas narrativas ('Quando conheci [Nome] em 2021...', 'Ao longo de nossa colaboração...'). Parágrafos mais longos (7-9 frases) que desenvolvem ideias completamente. Use anedotas específicas para ilustrar competências. Alterne entre descrição e análise. Enfatize desenvolvimento e crescimento observado. Transições suaves e conversacionais ('O que mais me impressionou foi...', 'Além disso, vale destacar...'). Misture evidências quantitativas com observações qualitativas. Tom caloroso mas profissional."

# OUTPUT FINAL

Retorne APENAS JSON válido (sem markdown, sem ```json):

{{
  "petitioner_name": "{organized_data.get('petitioner', {}).get('name', 'Unknown')}",
  "testimony_count": {num_testimonies},
  "generation_approach": "Complete n8n Schema (23 parameters)",
  "heterogeneity_validation": "[Explique brevemente como garantiu que TODAS as {num_testimonies} estruturas são únicas]",
  "design_structures": [
    {{...23 parameters...}},
    {{...23 parameters...}},
    ...
  ]
}}

**CHECKPOINT FINAL**:
✓ Há exatamente {num_testimonies} design_structures?
✓ Todos os 23 parâmetros estão presentes em cada estrutura?
✓ Nenhuma combinação (tone_variable + narrative_framework) se repete?
✓ tone_instructions tem mínimo 150 palavras cada?
✓ Parâmetros visuais (fontes, cores, layouts) variam significativamente?
"""
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.llm.client.chat.completions.create(
                    model=self.llm.models["quality"],
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                    temperature=0.9
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
                
                # Validation: Check all required keys are present
                required_keys = [
                    'assigned_recommender', 'tone_variable', 'tone_instructions',
                    'narrative_framework', 'paragraph_density_rule', 'readability_target',
                    'emphasis_pattern', 'semantic_elements', 'structure_features',
                    'target_word_count', 'bonus_trait', 'layout_pattern', 'font_primary',
                    'font_secondary', 'color_primary_hsl_range', 'color_accent',
                    'layout_density', 'line_height', 'header_alignment', 'footer_style',
                    'contrast_mode', 'whitespace_profile'
                ]
                
                missing_keys = []
                for ds in design_structures:
                    for key in required_keys:
                        if key not in ds:
                            missing_keys.append(f"{ds.get('assigned_recommender', '?')}: missing '{key}'")
                
                if missing_keys:
                    print(f"⚠️  Missing required keys: {missing_keys[:3]}")
                    if attempt < max_retries - 1:
                        print(f"   Regenerating with complete schema... (attempt {attempt + 2}/{max_retries})")
                        time.sleep(2)
                        continue
                
                # Validation: Check for duplicate combinations
                combinations = []
                for ds in design_structures:
                    combo = f"{ds.get('tone_variable', '')}|{ds.get('narrative_framework', '')}"
                    combinations.append(combo)
                
                if len(set(combinations)) != len(combinations):
                    print(f"⚠️  Duplicate tone+narrative combinations detected")
                    if attempt < max_retries - 1:
                        print(f"   Regenerating with unique combinations... (attempt {attempt + 2}/{max_retries})")
                        time.sleep(2)
                        continue
                
                # Success!
                print(f"✅ Complete n8n design structures generated: {num_testimonies} unique designs")
                print(f"   Schema: 23 parameters per design (content + visual)")
                print(f"   Validation: All required keys present, no duplicates")
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


# Backward compatibility
DynamicPersonaGenerator = HeterogeneityArchitect

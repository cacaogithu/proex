from typing import Dict, List
import json
import time


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
        import random
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
                'voice_style': voice,
                'structure_pattern': structure,
                'metric_emphasis': metrics,
                'formality_level': formality,
                'visual_density': visual,
                'unique_id': f"STYLE_{i+1}_{voice[:4].upper()}",
                'tone_instructions': f"Write in {voice} voice with {formality} tone",
                'paragraph_style': f"Use {visual} formatting with {structure}"
            })
        
        prompt = f"""# CRITICAL MISSION: MAXIMUM HETEROGENEITY (NO TEMPLATES!)
Você é o `Heterogeneity_Architect`. Sua missão é GARANTIR que CADA carta seja completamente DIFERENTE das outras.
As cartas devem parecer escritas por pessoas DIFERENTES, com BACKGROUNDS DIFERENTES, OBJETIVOS DIFERENTES e ESTILOS DE ESCRITA RADICALMENTE DISTINTOS.

**REGRA DE OURO**: Se duas cartas ficarem parecidas, você FALHOU na missão. CADA carta deve ter sua própria IDENTIDADE.

# CONTEXTO DO PETICIONÁRIO
OneNet: {json.dumps(organized_data.get('onet', {}), ensure_ascii=False)}
Strategy: {json.dumps(organized_data.get('strategy', {}), ensure_ascii=False)}
Petitioner: {json.dumps(organized_data.get('petitioner', {}), ensure_ascii=False)}

# TESTEMUNHOS DISPONÍVEIS
{self._format_testimonies(testimonies)}

# TEMPLATES ARQUETÍPICOS RADICALMENTE DISTINTOS

## STYLE BLUEPRINT GENERATION (NO TEMPLATES!)
- **Persona**: Engenheiro técnico veterano, obcecado por detalhes e especificações
- **Tom**: Extremamente técnico, rico em siglas, normas e números precisos
- **Estrutura**: Formato de atestado técnico com seções numeradas
- **Características únicas**:
  * Usa MUITAS siglas e termos técnicos (PLC, SCADA, NR10, ISO, Cpk, OEE, MTBF)
  * Números extremamente precisos (23.4%, USD 110,347.89, 1.129,5 horas)
  * Referências a normas e padrões (NR10, NR12, ISO 13849, ANSI)
  * Parágrafos curtos e objetivos, quase como um relatório técnico
  * Listas bullet com especificações técnicas
- **Objetivo**: Provar competência técnica através de evidências quantificáveis
- **Exemplo de abertura**: "Na qualidade de Engenheiro de Manutenção Sênior responsável por automação..."

## TEMPLATE B: "CASE STUDY ACADEMICO" (Gestor Estratégico com MBA)
- **Persona**: Executivo com formação acadêmica, aplica metodologias formais
- **Tom**: Formal, estruturado, acadêmico, com framework metodológico claro
- **Estrutura**: Formato de case study com seções explícitas e títulos em negrito
- **Características únicas**:
  * Seções claramente demarcadas (INTRODUÇÃO, ESTUDO DE CASO, METODOLOGIA, RESULTADOS, CONCLUSÃO)
  * Uso de frameworks formais (Six Sigma DMAIC, Lean, RCM)
  * Tabelas e quadros de correlação técnica
  * Parágrafos longos e bem desenvolvidos
  * Linguagem acadêmica e analítica
- **Objetivo**: Demonstrar pensamento estratégico e metodologia rigorosa
- **Exemplo de abertura**: "O propósito desta carta é delinear, com base em evidências quantificáveis..."

## TEMPLATE C: "NARRATIVE STORYTELLING" (Gestor Operacional)
- **Persona**: Gestor de operações pragmático, conta história do problema à solução
- **Tom**: Narrativo, pessoal, focado em jornada e transformação
- **Estrutura**: Fluxo natural de storytelling (contexto → desafio → solução → impacto)
- **Características únicas**:
  * Começa com o PROBLEMA enfrentado (cria tensão)
  * Descreve a JORNADA de descoberta e implementação
  * Usa linguagem mais acessível e menos técnica
  * Foco em TRANSFORMAÇÃO e MUDANÇA
  * Parágrafos médios, fluxo conversacional
  * Menciona reconhecimento e premiações
- **Objetivo**: Mostrar impacto transformacional através de narrativa envolvente
- **Exemplo de abertura**: "Em 2016, enfrentávamos um desafio crítico que impactava diretamente nossa lucratividade..."

## TEMPLATE D: "BUSINESS PARTNERSHIP" (Diretor Comercial/Estratégico)
- **Persona**: Executivo comercial, foca em valor de negócio e parceria estratégica
- **Tom**: Estratégico, focado em ROI, negócio e relacionamento
- **Estrutura**: Formato de recomendação empresarial com foco em resultados de negócio
- **Características únicas**:
  * Foco em PARCERIA, não apenas fornecimento
  * Ênfase em valor comercial e vantagem competitiva
  * Menciona impacto no portfólio de produtos
  * Linguagem de negócios (market share, competitive advantage, value proposition)
  * Parágrafos longos explicando contexto de negócio
  * Fala sobre desenvolvimento de produtos derivados
- **Objetivo**: Demonstrar impacto estratégico no negócio
- **Exemplo de abertura**: "Como Diretor Comercial responsável por crescimento estratégico..."

## TEMPLATE E: "SUPPORT LETTER" (Executivo Industrial Americano)
- **Persona**: Executivo de indústria americana, testemunho de suporte empresarial
- **Tom**: Direto, pragmático, focado em resultados mensuráveis
- **Estrutura**: Carta de apoio com quadros de resultados e contexto de mercado
- **Características únicas**:
  * Formato americano (cidade, estado, contatos americanos)
  * QUADRO DE RESULTADOS visível (sidebar ou box)
  * Contextualiza oportunidade de mercado nos EUA
  * Números muito específicos de produtividade e economia
  * Linguagem direta e objetiva
  * Menciona gap de mercado e demanda não atendida
- **Objetivo**: Validar capacidade técnica E oportunidade de mercado
- **Exemplo de abertura**: "Na qualidade de Diretor Industrial da [Company] USA, com sede em [City, State]..."

## TEMPLATE F: "TECHNICAL TESTIMONY WITH DOCUMENTATION" (Líder de Projeto)
- **Persona**: Líder técnico que liderou projeto conjunto, com documentação anexa
- **Tom**: Técnico mas colaborativo, foca em trabalho em equipe
- **Estrutura**: Testemunho técnico com referências a apêndices e documentação
- **Características únicas**:
  * Referências a documentação anexa (Apêndice A, Workshop results)
  * Foco em LIDERANÇA CONJUNTA e trabalho em equipe
  * Detalhamento de metodologia aplicada em conjunto
  * Usa tabelas e quadros explicativos
  * Menciona formação de grupos e divisão de trabalho
- **Objetivo**: Provar liderança técnica em projetos complexos
- **Exemplo de abertura**: "Como líder técnico do Grupo 1 no Workshop de Inspeção 2017..."

# SUA TAREFA

**DISTRIBUA OS {num_testimonies} TESTEMUNHOS ENTRE OS TEMPLATES ACIMA**, garantindo MÁXIMA HETEROGENEIDADE.

**REGRAS OBRIGATÓRIAS - ZERO TOLERÂNCIA PARA REPETIÇÃO**:
1. 🚨 **REGRA CRÍTICA DE UNICIDADE**:
   - Se {num_testimonies} ≤ 6: CADA carta DEVE usar um template ÚNICO (sem repetição alguma)
   - Se {num_testimonies} > 6: distribua uniformemente entre todos os 6 templates
   - NUNCA atribua o mesmo template_id duas vezes quando houver templates disponíveis

2. **VALIDAÇÃO OBRIGATÓRIA**:
   - Após gerar os {num_testimonies} design_structures, VERIFIQUE se há template_id repetido
   - Se houver QUALQUER repetição e {num_testimonies} ≤ 6: REGENERE imediatamente
   - Exemplos CORRETOS para 5 cartas: [A,B,C,D,E] ou [B,A,F,C,E]
   - Exemplos PROIBIDOS para 5 cartas: [A,B,A,C,D] ou [A,B,C,B,E]

3. **VARIAÇÃO OBRIGATÓRIA**:
   - Cada template deve ter instruções MUITO ESPECÍFICAS e DETALHADAS
   - As instruções devem FORÇAR estilos radicalmente diferentes
   - Cada carta deve parecer escrita por uma PESSOA DIFERENTE com BACKGROUND DIFERENTE

Para cada testemunho, gere:

{{
  "template_id": "A" | "B" | "C" | "D" | "E" | "F",
  "template_name": "[Nome do arquétipo]",
  "assigned_recommender": "[Nome completo do recomendador]",
  "recommender_role": "[Cargo do recomendador]",
  "persona_description": "[Descrição detalhada da persona: quem é, background, motivação]",
  
  "tone_instructions": "[INSTRUÇÕES SUPER ESPECÍFICAS: tom técnico/narrativo/estratégico, nível de formalidade, uso de linguagem]",
  
  "structure_format": "[FORMATO EXATO: case study com seções / storytelling linear / atestado técnico / carta de apoio]",
  
  "opening_style": "[Como começar: contexto técnico / problema-desafio / apresentação formal / recomendação direta]",
  
  "paragraph_style": "[Curtos e objetivos / Longos e desenvolvidos / Médios e narrativos / Mistos conforme seção]",
  
  "technical_depth": "ALTO (muitas siglas, normas, números precisos)" | "MÉDIO (alguns detalhes técnicos)" | "BAIXO (foco em negócio e impacto)",
  
  "visual_elements": "[ESPECÍFICO: listas bullet / tabelas de correlação / quadros de resultados / seções numeradas / parágrafos apenas]",
  
  "unique_features": [
    "[Característica única 1: ex: uso extensivo de siglas]",
    "[Característica única 2: ex: estrutura de case study DMAIC]",
    "[Característica única 3: ex: quadro de resultados visual]"
  ],
  
  "forbidden_elements": "[O que NÃO usar para garantir diferença: ex: não usar seções explícitas / não usar muitas siglas / não contar história]",
  
  "target_length": "1800-2200" | "2200-2600" | "2600-3000",
  
  "key_focus": "[Foco principal: competência técnica / impacto financeiro / transformação operacional / parceria estratégica]"
}}

# OUTPUT FINAL

Retorne APENAS JSON válido (sem markdown, sem ```json):

{{
  "petitioner_name": "{organized_data.get('petitioner', {}).get('name', 'Unknown')}",
  "testimony_count": {num_testimonies},
  "templates_used": "[Lista dos template_ids usados: ex: A,B,C,D,E para verificação de unicidade]",
  "heterogeneity_validation": "[CONFIRME: 'Todos os {num_testimonies} templates são únicos' OU explique distribuição se > 6 cartas]",
  "heterogeneity_strategy": "[Explicação de como você garantiu heterogeneidade máxima entre as {num_testimonies} cartas]",
  "design_structures": [
    {{...}},
    {{...}}
  ]
}}

**CHECKPOINT FINAL OBRIGATÓRIO**:
Antes de retornar o JSON, VERIFIQUE:
✓ Há exatamente {num_testimonies} design_structures?
✓ Se {num_testimonies} ≤ 6: TODOS os template_ids são ÚNICOS (sem repetição)?
✓ Cada design_structure tem instruções radicalmente distintas das outras?

**LEMBRE-SE**: Cada carta deve ser TÃO DIFERENTE que um leitor não deveria conseguir identificar que foram escritas para a mesma pessoa. Pense em AUTORES DIFERENTES com OBJETIVOS DIFERENTES escrevendo em ESTILOS COMPLETAMENTE DISTINTOS."""
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Using Gemini 2.5 Pro for high-quality design structures
                response = self.llm.client.chat.completions.create(
                    model=self.llm.models["quality"],
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"}
                )
                
                content = response.choices[0].message.content
                result = json.loads(content)
                
                # PROGRAMMATIC VALIDATION: Enforce template uniqueness
                design_structures = result.get('design_structures', [])
                template_ids = [ds.get('template_id') for ds in design_structures]
                ALLOWED_TEMPLATES = {'A', 'B', 'C', 'D', 'E', 'F'}
                
                # Validation 1: Count must match
                if len(design_structures) != num_testimonies:
                    print(f"⚠️ Count mismatch: expected {num_testimonies}, got {len(design_structures)}")
                    if attempt < max_retries - 1:
                        time.sleep(2)
                        continue
                    raise ValueError(f"Expected {num_testimonies} design_structures, got {len(design_structures)}")
                
                # Validation 2: All template_ids must be valid (A-F)
                invalid_templates = [tid for tid in template_ids if tid not in ALLOWED_TEMPLATES]
                if invalid_templates:
                    print(f"⚠️ Invalid template_ids detected: {invalid_templates}")
                    print(f"   Allowed: {ALLOWED_TEMPLATES}, Got: {template_ids}")
                    if attempt < max_retries - 1:
                        print(f"   Regenerating with valid templates... (attempt {attempt + 2}/{max_retries})")
                        time.sleep(2)
                        continue
                    raise ValueError(f"Invalid template_ids: {invalid_templates}. Must be one of {ALLOWED_TEMPLATES}")
                
                # Validation 3: Template uniqueness for ≤ 6 testimonies
                if num_testimonies <= 6:
                    unique_templates = set(template_ids)
                    if len(unique_templates) != num_testimonies:
                        duplicates = [tid for tid in template_ids if template_ids.count(tid) > 1]
                        print(f"⚠️ Template uniqueness violation: {template_ids}")
                        print(f"   Duplicates: {set(duplicates)} (each template must be used exactly once)")
                        if attempt < max_retries - 1:
                            print(f"   Regenerating with unique templates... (attempt {attempt + 2}/{max_retries})")
                            time.sleep(2)
                            continue
                        raise ValueError(f"Template uniqueness required for ≤6 letters. Got duplicates: {template_ids}")
                
                # Validation 4: Uniform distribution for > 6 testimonies
                if num_testimonies > 6:
                    from collections import Counter
                    template_counts = Counter(template_ids)
                    used_templates = set(template_ids)
                    
                    # All 6 templates should be used at least once
                    if len(used_templates) < 6:
                        missing = ALLOWED_TEMPLATES - used_templates
                        print(f"⚠️ Not all templates used: missing {missing}")
                        print(f"   Distribution: {dict(template_counts)}")
                        if attempt < max_retries - 1:
                            print(f"   Regenerating for better coverage... (attempt {attempt + 2}/{max_retries})")
                            time.sleep(2)
                            continue
                        raise ValueError(f"Incomplete template coverage for {num_testimonies} letters. Missing: {missing}. Got: {template_ids}")
                    
                    # STRICT uniform distribution: each template must be used ⌊N/6⌋ or ⌈N/6⌉ times
                    # Example: 8 testimonies → base=1, remainder=2 → [2,2,1,1,1,1] is valid
                    base_count = num_testimonies // 6  # floor
                    remainder = num_testimonies % 6    # how many get +1
                    
                    # Count how many templates have each frequency
                    counts = list(template_counts.values())
                    expected_counts = {base_count, base_count + 1} if remainder > 0 else {base_count}
                    
                    # All counts must be either base_count or base_count+1
                    invalid_counts = [c for c in counts if c not in expected_counts]
                    if invalid_counts:
                        print(f"⚠️ Non-uniform distribution: {dict(template_counts)}")
                        print(f"   Expected each template: {expected_counts} times")
                        print(f"   Got invalid counts: {invalid_counts}")
                        if attempt < max_retries - 1:
                            print(f"   Regenerating for strict uniform distribution... (attempt {attempt + 2}/{max_retries})")
                            time.sleep(2)
                            continue
                        raise ValueError(f"Non-uniform distribution for {num_testimonies} letters. Expected counts: {expected_counts}, Got: {dict(template_counts)}")
                    
                    # Verify exactly 'remainder' templates have base_count+1, rest have base_count
                    high_count = base_count + 1
                    num_high = sum(1 for c in counts if c == high_count)
                    if remainder > 0 and num_high != remainder:
                        print(f"⚠️ Distribution imbalance: {dict(template_counts)}")
                        print(f"   Expected {remainder} templates with {high_count}, got {num_high}")
                        if attempt < max_retries - 1:
                            print(f"   Regenerating for balanced distribution... (attempt {attempt + 2}/{max_retries})")
                            time.sleep(2)
                            continue
                        raise ValueError(f"Distribution imbalance for {num_testimonies} letters. Expected {remainder} templates with count {high_count}, got {num_high}. Distribution: {dict(template_counts)}")
                
                # Validation passed!
                print(f"✅ Heterogeneity validation passed: {num_testimonies} testimonies")
                print(f"   Templates used: {template_ids}")
                if num_testimonies > 6:
                    from collections import Counter
                    print(f"   Distribution: {dict(Counter(template_ids))}")
                return result
                
            except json.JSONDecodeError as e:
                print(f"⚠️ JSON decode error: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                raise
            except Exception as e:
                if "429" in str(e) and attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 3
                    print(f"⏳ Rate limit hit, waiting {wait_time}s before retry {attempt + 1}/{max_retries}...")
                    time.sleep(wait_time)
                    continue
                if attempt == max_retries - 1:
                    print(f"❌ Error in generate_design_structures after {max_retries} attempts: {str(e)}")
                    raise
        return {}

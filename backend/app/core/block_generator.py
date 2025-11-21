from typing import Dict, Optional
import json
import time
import re
from concurrent.futures import ThreadPoolExecutor, as_completed


class BlockGenerator:
    def __init__(self, llm_processor, prompt_enhancer=None):
        self.llm = llm_processor
        self.prompt_enhancer = prompt_enhancer  # ML-powered prompt improvement

    def _count_words(self, text: str) -> int:
        """Count words in text"""
        return len(re.findall(r'\w+', text))

    def _call_llm_with_retry(self, prompt: str, temperature: float = 0.9, max_retries: int = 3, max_tokens: int = 2000, min_words: int = 0, max_words: int = 0) -> str:
        for attempt in range(max_retries):
            try:
                # Using Gemini 2.5 Pro - cost-effective for high-quality content
                response = self.llm.client.chat.completions.create(
                    model=self.llm.models["quality"],
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                content = response.choices[0].message.content

                # Validate word count if specified
                if min_words > 0 or max_words > 0:
                    word_count = self._count_words(content)
                    if min_words > 0 and word_count < min_words:
                        print(f"⚠️  Word count too low: {word_count}/{min_words} words (attempt {attempt + 1}/{max_retries})")
                        if attempt < max_retries - 1:
                            # Strengthen prompt for next attempt
                            prompt = prompt + f"\n\nCRITICAL: Your previous response had only {word_count} words. You MUST write AT LEAST {min_words} words. Count as you write."
                            continue
                    if max_words > 0 and word_count > max_words:
                        print(f"⚠️  Word count too high: {word_count}/{max_words} words (attempt {attempt + 1}/{max_retries})")
                        if attempt < max_retries - 1:
                            # Strengthen prompt for next attempt
                            prompt = prompt + f"\n\nCRITICAL: Your previous response had {word_count} words. You MUST write NO MORE THAN {max_words} words. Be concise."
                            continue

                return content
            except Exception as e:
                if "429" in str(e) and attempt < max_retries - 1:
                    # Reduced wait times: 1s, 2s (instead of 3s, 6s, 12s)
                    wait_time = (2 ** attempt)
                    print(f"⏳ Rate limit hit, waiting {wait_time}s before retry {attempt + 1}/{max_retries}...")
                    time.sleep(wait_time)
                    continue
                if attempt == max_retries - 1:
                    raise e
        return ""
    
    def generate_block3(self, testimony: Dict, design: Dict, context: Dict, letter_embedding: Optional[list] = None) -> str:
        base_prompt = f"""# ROLE
Você é `Block3_PROMPT` - um escritor profissional especializado em cartas de recomendação detalhadas e substanciais.

**PERSONA DE ESCRITA**:
{design.get('tone_instructions', '')}

**ESTRUTURA NARRATIVA**:
{design.get('narrative_framework', '')}

# INPUTS
OneNet: {json.dumps(context.get('onet', {}), ensure_ascii=False)}
Strategy: {json.dumps(context.get('strategy', {}), ensure_ascii=False)}
Petitioner: {json.dumps(context.get('petitioner', {}), ensure_ascii=False)}
Testemunho atual: {json.dumps(testimony, ensure_ascii=False)}

# OUTPUT
{{"block": 3, "markdown_draft": "<rascunho markdown>"}}

# ESTRUTURA — BLOCO 3: VALIDAÇÃO EMPÍRICA DE RESULTADOS
⚠️ CRITICAL REQUIREMENT: Write EXACTLY 800-1200 words (Portuguese words). This is MANDATORY.
⚠️ YOUR TEXT MUST BE AT LEAST 800 WORDS. Count as you write. Target: 1000 words.
⚠️ If your response is under 800 words, it will be REJECTED.

Este bloco deve ser EXTENSO e DETALHADO. Primeira pessoa. Evidências quantitativas e qualitativas.

CONTEÚDO OBRIGATÓRIO (desenvolva CADA item em pelo menos 2-3 parágrafos):
1. **Contexto Inicial**: Descreva a situação antes da intervenção do profissional (problemas, desafios, limitações)
2. **Métricas Quantitativas** (mínimo 5-7 métricas):
   - Métricas de eficiência operacional (%, tempo, custo)
   - Métricas de qualidade (redução de defeitos, satisfação)
   - Métricas financeiras (ROI, economia, receita)
   - Métricas de produtividade (output, throughput)
   - Métricas comparativas (antes/depois)
3. **Resultados Qualitativos** (mínimo 3-4 observações):
   - Mudanças culturais observadas
   - Melhorias em processos
   - Reconhecimento da equipe/clientes
   - Impacto na moral/engajamento
4. **Casos Específicos**: Relate 2-3 exemplos concretos de projetos ou situações onde os resultados foram evidentes
5. **Validação Externa**: Mencione reconhecimentos, prêmios, feedback de stakeholders

# REGRAS
- Voz: primeira pessoa (recomendador falando)
- Foco: resultados DETALHADOS com exemplos específicos
- Estilo: profissional, preciso, executivo, mas EXTENSO
- Output: Markdown apenas, sem HTML
- TODO EM PORTUGUÊS BRASILEIRO
- Remova termos: "imigração", "EB2-NIW", "peticionário"
- USE PARÁGRAFOS LONGOS E BEM DESENVOLVIDOS
- CADA SEÇÃO DEVE TER MÚLTIPLOS PARÁGRAFOS
"""
        
        # ML-powered prompt enhancement
        prompt = base_prompt
        if self.prompt_enhancer:
            try:
                prompt = self.prompt_enhancer.enhance_block_prompt(
                    base_prompt, 
                    block_number=3,
                    letter_context=testimony,
                    letter_embedding=letter_embedding
                )
            except Exception as e:
                print(f"   ℹ️  ML prompt enhancement skipped: {e}")
        
        try:
            content = self._call_llm_with_retry(prompt, temperature=0.9, max_tokens=4000, min_words=800, max_words=1200)
            try:
                data = json.loads(content)
                draft = data.get('markdown_draft', content)
                word_count = self._count_words(draft)
                print(f"    ✓ Block 3 generated: {word_count} words")
                return draft
            except (json.JSONDecodeError, KeyError, TypeError):
                # If JSON parsing fails, return raw content
                word_count = self._count_words(content)
                print(f"    ✓ Block 3 generated: {word_count} words")
                return content
        except Exception as e:
            print(f"Error generating block 3: {str(e)}")
            return "Error generating block 3"

    def generate_block4(self, testimony: Dict, design: Dict, context: Dict) -> str:
        prompt = f"""# ROLE
Você é `Block4_PROMPT` - um especialista em comunicação técnica que escreve textos EXTENSOS e detalhados.

**PERSONA**: {design.get('tone_instructions', '')}

# INPUTS
Testemunho: {json.dumps(testimony, ensure_ascii=False)}
Contexto: {json.dumps(context.get('petitioner', {}), ensure_ascii=False)}

# BLOCO 4: DIFERENCIAÇÃO TÉCNICA E METODOLÓGICA
⚠️ CRITICAL REQUIREMENT: Write EXACTLY 1000-1400 words (Portuguese words). This is MANDATORY.
⚠️ YOUR TEXT MUST BE AT LEAST 1000 WORDS. Count as you write. Target: 1200 words.
⚠️ If your response is under 1000 words, it will be REJECTED.

Este bloco deve ser MUITO EXTENSO e TÉCNICO. Destaque capacidades técnicas únicas.

CONTEÚDO OBRIGATÓRIO (desenvolva CADA item em 2-4 parágrafos detalhados):
1. **Competências Técnicas Únicas** (3-5 parágrafos):
   - Conhecimentos especializados que poucos possuem
   - Certificações e qualificações relevantes
   - Domínio de tecnologias/metodologias avançadas

2. **Abordagens Metodológicas Exclusivas** (3-4 parágrafos):
   - Frameworks proprietários ou adaptados
   - Processos de análise diferenciados
   - Metodologias de implementação únicas

3. **Ferramentas e Tecnologias** (3-4 parágrafos):
   - Stack tecnológico utilizado
   - Ferramentas especializadas dominadas
   - Integrações complexas realizadas

4. **Processos Inovadores** (3-4 parágrafos):
   - Inovações em workflows
   - Automações desenvolvidas
   - Melhorias em processos existentes

5. **Comparativo com Mercado** (2-3 parágrafos):
   - O que diferencia das práticas comuns
   - Vantagens competitivas observadas

# REGRAS
- Primeira pessoa (recomendador falando)
- Linguagem técnica mas acessível
- TODO EM PORTUGUÊS BRASILEIRO
- USE MUITOS PARÁGRAFOS LONGOS
- DETALHE CADA PONTO EXTENSIVAMENTE
"""

        try:
            content = self._call_llm_with_retry(prompt, temperature=0.9, max_tokens=5000, min_words=1000, max_words=1400)
            word_count = self._count_words(content)
            print(f"    ✓ Block 4 generated: {word_count} words")
            return content
        except Exception as e:
            print(f"Error generating block 4: {str(e)}")
            return "Error generating block 4"

    def generate_block5(self, testimony: Dict, design: Dict, context: Dict) -> str:
        prompt = f"""# ROLE
Você é `Block5_PROMPT` - um escritor que produz textos EXTENSOS sobre impacto profissional.

**PERSONA**: {design.get('tone_instructions', '')}

# INPUTS
Testemunho: {json.dumps(testimony, ensure_ascii=False)}

# BLOCO 5: IMPACTO SETORIAL E ALCANCE
⚠️ CRITICAL REQUIREMENT: Write EXACTLY 800-1200 words (Portuguese words). This is MANDATORY.
⚠️ YOUR TEXT MUST BE AT LEAST 800 WORDS. Count as you write. Target: 1000 words.
⚠️ If your response is under 800 words, it will be REJECTED.

Este bloco deve ser EXTENSO. Demonstre influência além do contexto imediato.

CONTEÚDO OBRIGATÓRIO (desenvolva CADA item em 2-3 parágrafos):
1. **Reconhecimento por Pares** (3-4 parágrafos):
   - Feedback de colegas e superiores
   - Convites para projetos especiais
   - Consultas de outros profissionais
   - Mentorias e orientações solicitadas

2. **Contribuições para o Setor** (3-4 parágrafos):
   - Participação em eventos/conferências
   - Publicações ou apresentações
   - Contribuições para padrões da indústria
   - Benchmarks estabelecidos

3. **Disseminação de Conhecimento** (3-4 parágrafos):
   - Treinamentos ministrados
   - Documentação criada
   - Best practices estabelecidas
   - Multiplicação de conhecimento na equipe

4. **Influência Organizacional** (2-3 parágrafos):
   - Mudanças em políticas/processos
   - Adoção de novas práticas
   - Impacto em outras áreas/departamentos

# REGRAS
- Primeira pessoa (recomendador falando)
- Evidências concretas e específicas
- TODO EM PORTUGUÊS BRASILEIRO
- PARÁGRAFOS LONGOS E DETALHADOS
"""

        try:
            content = self._call_llm_with_retry(prompt, temperature=0.9, max_tokens=4000, min_words=800, max_words=1200)
            word_count = self._count_words(content)
            print(f"    ✓ Block 5 generated: {word_count} words")
            return content
        except Exception as e:
            print(f"Error generating block 5: {str(e)}")
            return "Error generating block 5"

    def generate_block6(self, testimony: Dict, design: Dict, context: Dict) -> str:
        prompt = f"""# ROLE
Você é `Block6_PROMPT` - especialista em estabelecer credibilidade profissional com textos detalhados.

**PERSONA**: {design.get('tone_instructions', '')}

# INPUTS
Testemunho: {json.dumps(testimony, ensure_ascii=False)}

# BLOCO 6: QUALIFICAÇÃO DO RECOMENDADOR
⚠️ CRITICAL REQUIREMENT: Write EXACTLY 500-800 words (Portuguese words). This is MANDATORY.
⚠️ YOUR TEXT MUST BE AT LEAST 500 WORDS. Count as you write. Target: 650 words.
⚠️ If your response is under 500 words, it will be REJECTED.

Este bloco deve estabelecer credibilidade de forma DETALHADA.

CONTEÚDO OBRIGATÓRIO (desenvolva CADA item em 2-3 parágrafos):
1. **Minha Experiência Profissional** (2-3 parágrafos):
   - Anos de experiência na área
   - Cargos ocupados relevantes
   - Principais conquistas profissionais

2. **Posição para Avaliar** (2-3 parágrafos):
   - Como conheci o profissional
   - Frequência e profundidade da interação
   - Projetos trabalhados juntos

3. **Contexto da Colaboração** (2-3 parágrafos):
   - Duração da relação profissional
   - Natureza dos projetos conjuntos
   - Responsabilidades observadas

4. **Base para esta Recomendação** (1-2 parágrafos):
   - Por que estou qualificado para recomendar
   - O que me permite fazer esta avaliação

# REGRAS
- Primeira pessoa (EU sou o recomendador)
- Profissional e credível
- TODO EM PORTUGUÊS BRASILEIRO
- SEJA ESPECÍFICO E DETALHADO
"""

        try:
            content = self._call_llm_with_retry(prompt, temperature=0.9, max_tokens=3000, min_words=500, max_words=800)
            word_count = self._count_words(content)
            print(f"    ✓ Block 6 generated: {word_count} words")
            return content
        except Exception as e:
            print(f"Error generating block 6: {str(e)}")
            return "Error generating block 6"

    def generate_block7(self, testimony: Dict, design: Dict, context: Dict) -> str:
        prompt = f"""# ROLE
Você é `Block7_PROMPT` - escritor de conclusões impactantes e substanciais.

**PERSONA**: {design.get('tone_instructions', '')}

# INPUTS
Testemunho: {json.dumps(testimony, ensure_ascii=False)}

# BLOCO 7: CONCLUSÃO E RECOMENDAÇÃO
⚠️ CRITICAL REQUIREMENT: Write EXACTLY 400-600 words (Portuguese words). This is MANDATORY.
⚠️ YOUR TEXT MUST BE AT LEAST 400 WORDS. Count as you write. Target: 500 words.
⚠️ If your response is under 400 words, it will be REJECTED.

Este bloco deve ser uma conclusão FORTE e DETALHADA.

CONTEÚDO OBRIGATÓRIO (desenvolva CADA item):
1. **Síntese de Valor** (2-3 parágrafos):
   - Resumo das principais contribuições
   - Impacto geral observado
   - Valor agregado à organização

2. **Recomendação Clara e Enfática** (2-3 parágrafos):
   - Declaração inequívoca de recomendação
   - Razões principais para a recomendação
   - Confiança no potencial futuro

3. **Perspectiva Futura** (1-2 parágrafos):
   - Expectativas de contribuições futuras
   - Potencial de crescimento
   - Disponibilidade para contato adicional

# REGRAS
- Primeira pessoa (recomendador)
- Tom conclusivo mas caloroso
- TODO EM PORTUGUÊS BRASILEIRO
- ENCERRAMENTO MEMORÁVEL E IMPACTANTE
"""

        try:
            content = self._call_llm_with_retry(prompt, temperature=0.9, max_tokens=2500, min_words=400, max_words=600)
            word_count = self._count_words(content)
            print(f"    ✓ Block 7 generated: {word_count} words")
            return content
        except Exception as e:
            print(f"Error generating block 7: {str(e)}")
            return "Error generating block 7"
    
    def generate_all_blocks(self, testimony: Dict, design: Dict, context: Dict) -> Dict[str, str]:
        """Generate all 5 blocks in parallel for maximum performance"""
        recommender_name = testimony.get('recommender_name', 'Unknown')
        print(f"Generating 5 blocks in parallel for {recommender_name}...")

        blocks = {}

        # Define block generation tasks
        block_tasks = {
            "block3": (self.generate_block3, testimony, design, context),
            "block4": (self.generate_block4, testimony, design, context),
            "block5": (self.generate_block5, testimony, design, context),
            "block6": (self.generate_block6, testimony, design, context),
            "block7": (self.generate_block7, testimony, design, context)
        }

        # Execute all blocks in parallel (5 concurrent API calls)
        with ThreadPoolExecutor(max_workers=5) as executor:
            # Submit all tasks
            future_to_block = {
                executor.submit(func, *args): block_name
                for block_name, (func, *args) in block_tasks.items()
            }

            # Collect results as they complete
            for future in as_completed(future_to_block):
                block_name = future_to_block[future]
                try:
                    blocks[block_name] = future.result()
                except Exception as exc:
                    print(f"    ✗ {block_name} failed: {exc}")
                    blocks[block_name] = f"Error generating {block_name}: {exc}"

        print(f"    ✓ All 5 blocks completed for {recommender_name}")
        return blocks

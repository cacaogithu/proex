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

    def _call_llm_simple(self, prompt: str, temperature: float = 0.9, max_tokens: int = 4000) -> str:
        """Simple LLM call without word count validation"""
        for attempt in range(3):
            try:
                response = self.llm.client.chat.completions.create(
                    model=self.llm.models["quality"],
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return response.choices[0].message.content
            except Exception as e:
                if "429" in str(e) and attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
                if attempt == 2:
                    raise e
        return ""

    def _expand_content(self, content: str, min_words: int, context_hint: str = "") -> str:
        """Expand content until it reaches minimum word count"""
        word_count = self._count_words(content)

        if word_count >= min_words:
            return content

        words_needed = min_words - word_count
        print(f"   📝 Expanding content: {word_count} → {min_words} words (+{words_needed} needed)")

        expansion_prompt = f"""# TAREFA: EXPANDIR TEXTO

Você recebeu um texto que precisa ser EXPANDIDO. O texto atual tem {word_count} palavras mas precisa ter NO MÍNIMO {min_words} palavras.

## TEXTO ATUAL:
{content}

## INSTRUÇÕES DE EXPANSÃO:
1. MANTENHA todo o conteúdo original
2. ADICIONE mais {words_needed + 200} palavras de conteúdo NOVO e RELEVANTE
3. Expanda cada parágrafo com mais detalhes, exemplos e contexto
4. Adicione novos parágrafos entre os existentes com informações complementares
5. Use transições suaves entre os parágrafos
6. Mantenha o tom e estilo do texto original
7. NÃO repita informações - adicione NOVOS detalhes

{context_hint}

## REGRAS CRÍTICAS:
- O texto final DEVE ter NO MÍNIMO {min_words} palavras
- Mantenha a primeira pessoa
- TODO EM PORTUGUÊS BRASILEIRO
- Seja EXTENSIVO e DETALHADO

## OUTPUT:
Retorne APENAS o texto expandido completo, sem comentários ou explicações."""

        try:
            expanded = self._call_llm_simple(expansion_prompt, temperature=0.8, max_tokens=6000)
            new_count = self._count_words(expanded)
            print(f"   ✓ Expanded: {word_count} → {new_count} words")

            # Se ainda não atingiu, tenta mais uma vez
            if new_count < min_words:
                print(f"   📝 Second expansion needed: {new_count} → {min_words}")
                return self._expand_content(expanded, min_words, context_hint)

            return expanded
        except Exception as e:
            print(f"   ⚠️ Expansion failed: {e}")
            return content

    def _call_llm_with_retry(self, prompt: str, temperature: float = 0.9, max_retries: int = 5, max_tokens: int = 4000, min_words: int = 0, max_words: int = 0, context_hint: str = "") -> str:
        """Generate content with guaranteed minimum word count"""
        best_content = ""
        best_word_count = 0

        for attempt in range(max_retries):
            try:
                response = self.llm.client.chat.completions.create(
                    model=self.llm.models["quality"],
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature + (attempt * 0.05),  # Slightly increase temperature each attempt
                    max_tokens=max_tokens
                )
                content = response.choices[0].message.content
                word_count = self._count_words(content)

                # Keep track of best attempt
                if word_count > best_word_count:
                    best_content = content
                    best_word_count = word_count

                print(f"   Attempt {attempt + 1}: {word_count} words (target: {min_words})")

                # If we hit the target, return immediately
                if min_words > 0 and word_count >= min_words:
                    return content

                # If this is not the last attempt, strengthen the prompt
                if attempt < max_retries - 1:
                    prompt = prompt + f"""

⚠️⚠️⚠️ ATENÇÃO CRÍTICA ⚠️⚠️⚠️
Sua resposta anterior teve APENAS {word_count} palavras.
VOCÊ DEVE ESCREVER NO MÍNIMO {min_words} PALAVRAS.
Faltam {min_words - word_count} palavras para atingir o mínimo.
ESCREVA MUITO MAIS CONTEÚDO. SEJA EXTREMAMENTE DETALHADO.
Cada seção deve ter MÚLTIPLOS parágrafos longos.
NÃO SEJA BREVE. SEJA EXTENSIVO."""

            except Exception as e:
                if "429" in str(e) and attempt < max_retries - 1:
                    wait_time = (2 ** attempt)
                    print(f"⏳ Rate limit, waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                if attempt == max_retries - 1:
                    raise e

        # If we exhausted retries but still under minimum, expand the content
        if min_words > 0 and best_word_count < min_words:
            print(f"   ⚠️ All {max_retries} attempts below minimum. Expanding content...")
            best_content = self._expand_content(best_content, min_words, context_hint)

        return best_content
    
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
            context_hint = "Este é o BLOCO 3 - Validação Empírica de Resultados. Foco em métricas quantitativas e qualitativas, casos específicos e validação externa."
            content = self._call_llm_with_retry(prompt, temperature=0.9, max_tokens=4000, min_words=800, max_words=1200, context_hint=context_hint)
            try:
                data = json.loads(content)
                draft = data.get('markdown_draft', content)
                word_count = self._count_words(draft)
                # Apply expansion if still under minimum
                if word_count < 800:
                    draft = self._expand_content(draft, 800, context_hint)
                    word_count = self._count_words(draft)
                print(f"    ✓ Block 3 generated: {word_count} words")
                return draft
            except (json.JSONDecodeError, KeyError, TypeError):
                word_count = self._count_words(content)
                # Apply expansion if still under minimum
                if word_count < 800:
                    content = self._expand_content(content, 800, context_hint)
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
            context_hint = "Este é o BLOCO 4 - Diferenciação Técnica e Metodológica. Foco em competências técnicas, metodologias exclusivas, ferramentas e processos inovadores."
            content = self._call_llm_with_retry(prompt, temperature=0.9, max_tokens=5000, min_words=1000, max_words=1400, context_hint=context_hint)
            word_count = self._count_words(content)
            if word_count < 1000:
                content = self._expand_content(content, 1000, context_hint)
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
            context_hint = "Este é o BLOCO 5 - Impacto Setorial e Alcance. Foco em reconhecimento por pares, contribuições para o setor, disseminação de conhecimento e influência organizacional."
            content = self._call_llm_with_retry(prompt, temperature=0.9, max_tokens=4000, min_words=800, max_words=1200, context_hint=context_hint)
            word_count = self._count_words(content)
            if word_count < 800:
                content = self._expand_content(content, 800, context_hint)
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
            context_hint = "Este é o BLOCO 6 - Qualificação do Recomendador. Foco em experiência profissional, posição para avaliar, contexto da colaboração e base para a recomendação."
            content = self._call_llm_with_retry(prompt, temperature=0.9, max_tokens=3000, min_words=500, max_words=800, context_hint=context_hint)
            word_count = self._count_words(content)
            if word_count < 500:
                content = self._expand_content(content, 500, context_hint)
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
            context_hint = "Este é o BLOCO 7 - Conclusão e Recomendação. Foco em síntese de valor, recomendação clara e enfática, e perspectiva futura."
            content = self._call_llm_with_retry(prompt, temperature=0.9, max_tokens=2500, min_words=400, max_words=600, context_hint=context_hint)
            word_count = self._count_words(content)
            if word_count < 400:
                content = self._expand_content(content, 400, context_hint)
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

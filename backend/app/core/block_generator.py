from typing import Dict, Optional
import json
import time
import re


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
                    wait_time = (2 ** attempt) * 3
                    print(f"⏳ Rate limit hit, waiting {wait_time}s before retry {attempt + 1}/{max_retries}...")
                    time.sleep(wait_time)
                    continue
                if attempt == max_retries - 1:
                    raise e
        return ""
    
    def generate_block3(self, testimony: Dict, design: Dict, context: Dict, letter_embedding: Optional[list] = None) -> str:
        """Generate Block 3 of the letter.

        Args:
            letter_embedding: Currently unused. Reserved for future ML enhancement
                             where embeddings from similar letters could improve generation.
                             Currently, embeddings are generated AFTER letter creation,
                             not before, so this is always None.
        """
        base_prompt = f"""# ROLE
Você é `Block3_PROMPT`

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
CRITICAL REQUIREMENT: Write EXACTLY 800-1200 words (Portuguese words). This is MANDATORY.
Count your words as you write. Current target: 1000 words.
Primeira pessoa. Evidências quantitativas e qualitativas detalhadas.
- Pelo menos 5-7 métricas quantitativas (com números específicos)
- 3-4 observações qualitativas profundas
- Lista com 8-12 resultados empíricos documentados
- Contexto e impacto de cada métrica

# REGRAS
- Voz: primeira pessoa (recomendador falando)
- Foco: resultados com análise aprofundada
- Estilo: profissional, preciso, executivo
- Output: Markdown apenas, sem HTML
- TODO EM PORTUGUÊS
- Remova termos: "imigração", "EB2-NIW", "peticionário"
- Expanda com narrativa completa de cada resultado
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
            content = self._call_llm_with_retry(prompt, temperature=0.9, max_tokens=4000, min_words=600, max_words=900)
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
Você é `Block4_PROMPT`

**PERSONA**: {design.get('tone_instructions', '')}

# INPUTS
Testemunho: {json.dumps(testimony, ensure_ascii=False)}
Contexto: {json.dumps(context.get('petitioner', {}), ensure_ascii=False)}

# BLOCO 4: DIFERENCIAÇÃO TÉCNICA E METODOLÓGICA
CRITICAL REQUIREMENT: Write EXACTLY 600-1000 words (Portuguese words). This is MANDATORY.
Count your words as you write. Current target: 800 words.
Destaque capacidades técnicas únicas com profundidade.
- Abordagens metodológicas exclusivas (explicar cada uma)
- Ferramentas e tecnologias avançadas (listá-las com contexto)
- Processos inovadores (detalhar implementação)
- Vantagens competitivas específicas
- Exemplos reais de aplicação

# REGRAS
- Primeira pessoa
- Linguagem técnica mas acessível
- Incluir métricas e resultados mensuráveis
- TODO EM PORTUGUÊS
"""

        try:
            content = self._call_llm_with_retry(prompt, temperature=0.9, max_tokens=3500, min_words=450, max_words=700)
            word_count = self._count_words(content)
            print(f"    ✓ Block 4 generated: {word_count} words")
            return content
        except Exception as e:
            print(f"Error generating block 4: {str(e)}")
            return "Error generating block 4"
    
    def generate_block5(self, testimony: Dict, design: Dict, context: Dict) -> str:
        prompt = f"""# ROLE
Você é `Block5_PROMPT`

**PERSONA**: {design.get('tone_instructions', '')}

# INPUTS
Testemunho: {json.dumps(testimony, ensure_ascii=False)}

# BLOCO 5: IMPACTO SETORIAL E ALCANCE
CRITICAL REQUIREMENT: Write EXACTLY 500-800 words (Portuguese words). This is MANDATORY.
Count your words as you write. Current target: 650 words.
Demonstre influência além do contexto imediato com exemplos detalhados.
- Reconhecimento por pares (conferências, publicações, mentorias)
- Contribuições para o setor (iniciativas, transformações)
- Disseminação de conhecimento (treinamentos, palestras, frameworks)
- Impacto em múltiplas organizações
- Legado e influência duradoura

# REGRAS
- Primeira pessoa
- Evidências concretas e quantificáveis
- Incluir nomes de instituições e projetos
- TODO EM PORTUGUÊS
"""

        try:
            content = self._call_llm_with_retry(prompt, temperature=0.9, max_tokens=3000, min_words=350, max_words=600)
            word_count = self._count_words(content)
            print(f"    ✓ Block 5 generated: {word_count} words")
            return content
        except Exception as e:
            print(f"Error generating block 5: {str(e)}")
            return "Error generating block 5"
    
    def generate_block6(self, testimony: Dict, design: Dict, context: Dict) -> str:
        prompt = f"""# ROLE
Você é `Block6_PROMPT`

**PERSONA**: {design.get('tone_instructions', '')}

# INPUTS
Testemunho: {json.dumps(testimony, ensure_ascii=False)}

# BLOCO 6: QUALIFICAÇÃO DO RECOMENDADOR
CRITICAL REQUIREMENT: Write EXACTLY 300-500 words (Portuguese words). This is MANDATORY.
Count your words as you write. Current target: 400 words.
Estabeleça credibilidade de forma aprofundada.
- Experiência relevante (anos, setores, especialidades)
- Posição estratégica para avaliar o trabalho
- Contexto detalhado da colaboração
- Nível de supervisão e responsabilidade
- Base factual para a recomendação

# REGRAS
- Primeira pessoa
- Profissional e convincente
- Detalhe específico sobre relacionamento e observação
- TODO EM PORTUGUÊS
"""

        try:
            content = self._call_llm_with_retry(prompt, temperature=0.9, max_tokens=2500, min_words=250, max_words=400)
            word_count = self._count_words(content)
            print(f"    ✓ Block 6 generated: {word_count} words")
            return content
        except Exception as e:
            print(f"Error generating block 6: {str(e)}")
            return "Error generating block 6"
    
    def generate_block7(self, testimony: Dict, design: Dict, context: Dict) -> str:
        prompt = f"""# ROLE
Você é `Block7_PROMPT`

**PERSONA**: {design.get('tone_instructions', '')}

# INPUTS
Testemunho: {json.dumps(testimony, ensure_ascii=False)}

# BLOCO 7: CONCLUSÃO E RECOMENDAÇÃO
CRITICAL REQUIREMENT: Write EXACTLY 300-500 words (Portuguese words). This is MANDATORY.
Count your words as you write. Current target: 400 words.
Encerramento forte com impacto.
- Síntese integrada de todas as contribuições
- Recomendação clara e sem hesitações
- Perspectiva sobre potencial futuro
- Apelo final convincente
- Contacto e disponibilidade

# REGRAS
- Primeira pessoa
- Tom conclusivo e persuasivo
- Reaffirm a excelência demonstrada
- TODO EM PORTUGUÊS
"""

        try:
            content = self._call_llm_with_retry(prompt, temperature=0.9, max_tokens=2500, min_words=250, max_words=400)
            word_count = self._count_words(content)
            print(f"    ✓ Block 7 generated: {word_count} words")
            return content
        except Exception as e:
            print(f"Error generating block 7: {str(e)}")
            return "Error generating block 7"
    
    def generate_all_blocks(self, testimony: Dict, design: Dict, context: Dict) -> Dict[str, str]:
        print(f"Generating blocks for {testimony.get('recommender_name', 'Unknown')}...")
        return {
            "block3": self.generate_block3(testimony, design, context),
            "block4": self.generate_block4(testimony, design, context),
            "block5": self.generate_block5(testimony, design, context),
            "block6": self.generate_block6(testimony, design, context),
            "block7": self.generate_block7(testimony, design, context)
        }

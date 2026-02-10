
from typing import Dict, Optional
import json
import time
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from .llm_processor import LLMProcessor
from .openai_vector_search import OpenAIVectorSearch
from .block_prompts import (
    BLOCK1_PROMPT,
    BLOCK2_PROMPT,
    BLOCK3_PROMPT,
    BLOCK4_PROMPT,
    BLOCK5_PROMPT
)


LENGTH_PROFILES = {
    'concise': {
        'block1': {'min': 150, 'max': 300, 'tokens': 1500},
        'block2': {'min': 150, 'max': 300, 'tokens': 1500},
        'block3': {'min': 400, 'max': 600, 'tokens': 2500},
        'block4': {'min': 200, 'max': 350, 'tokens': 1500},
        'block5': {'min': 150, 'max': 250, 'tokens': 1500},
    },
    'standard': {
        'block1': {'min': 300, 'max': 500, 'tokens': 2500},
        'block2': {'min': 300, 'max': 500, 'tokens': 2500},
        'block3': {'min': 700, 'max': 900, 'tokens': 4000},
        'block4': {'min': 350, 'max': 550, 'tokens': 2500},
        'block5': {'min': 300, 'max': 450, 'tokens': 2500},
    },
    'comprehensive': {
        'block1': {'min': 500, 'max': 800, 'tokens': 3500},
        'block2': {'min': 500, 'max': 800, 'tokens': 3500},
        'block3': {'min': 1200, 'max': 1600, 'tokens': 6000},
        'block4': {'min': 600, 'max': 900, 'tokens': 3500},
        'block5': {'min': 500, 'max': 700, 'tokens': 3500},
    }
}


class BlockGenerator:
    def __init__(self, llm_processor: LLMProcessor, prompt_enhancer=None, rag_engine=None):
        self.llm = llm_processor
        self.prompt_enhancer = prompt_enhancer
        self.rag = rag_engine
        self.vector_search = OpenAIVectorSearch()

    def _get_block_config(self, design: Dict, block_name: str) -> Dict:
        """Get word count configuration for a block based on design's length_profile"""
        length_profile = design.get('length_profile', 'standard').lower()
        if length_profile not in LENGTH_PROFILES:
            length_profile = 'standard'
        return LENGTH_PROFILES[length_profile][block_name]

    def _count_words(self, text: str) -> int:
        """Count words in text"""
        return len(re.findall(r'\w+', text))

    def _prepare_prompt_data(self, testimony: Dict, design: Dict, context: Dict) -> Dict:
        """
        Prepare data dictionary for n8n prompt templates.
        Maps all required fields from design structure and testimony.
        """
        onet = context.get('onet', {})
        strategy = context.get('strategy', {})
        petitioner = context.get('petitioner', {})

        return {
            'tone_variable': design.get('tone_variable', ''),
            'tone_instructions': design.get('tone_instructions', ''),
            'narrative_framework': design.get('narrative_framework', ''),
            'paragraph_density_rule': design.get('paragraph_density_rule', ''),
            'onet_tasks': onet.get('representative_tasks', ''),
            'onet_tools': onet.get('tools_and_technologies', ''),
            'onet_activities': onet.get('work_activities_and_skills', ''),
            'strategy_services': strategy.get('services_offered', ''),
            'strategy_clients': strategy.get('target_clients', ''),
            'petitioner_name': petitioner.get('name', ''),
            'petitioner_education': petitioner.get('education', ''),
            'petitioner_experience': petitioner.get('experience', ''),
            'testimony_id': testimony.get('testimony_id', ''),
            'recommender_name': testimony.get('recommender_name', ''),
            'recommender_company': testimony.get('recommender_company', ''),
            'recommender_role': testimony.get('recommender_role', ''),
            'collaboration_period': testimony.get('collaboration_period', ''),
            'applicant_role': testimony.get('applicant_role', ''),
            'testimony_text': testimony.get('testimony_text', ''),
            'key_achievements': testimony.get('key_achievements', ''),
        }

    def _call_llm_simple(self, prompt: str, temperature: float = 0.9, max_tokens: int = 4000) -> str:
        """Simple LLM call without word count validation"""
        for attempt in range(3):
            try:
                response = self.llm._call_llm(
                    model=self.llm.models["quality"],
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                content = response.choices[0].message.content
                return content if content else ""
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
                response = self.llm._call_llm(
                    model=self.llm.models["quality"],
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature + (attempt * 0.05),
                    max_tokens=max_tokens
                )
                content = response.choices[0].message.content
                if not content:
                    content = ""
                
                word_count = self._count_words(content)

                if word_count > best_word_count:
                    best_content = content
                    best_word_count = word_count

                print(f"   Attempt {attempt + 1}: {word_count} words (target: {min_words})")

                if min_words > 0 and word_count >= min_words:
                    return content

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

        if min_words > 0 and best_word_count < min_words:
            print(f"   ⚠️ All {max_retries} attempts below minimum. Expanding content...")
            best_content = self._expand_content(best_content, min_words, context_hint)

        return best_content

    def generate_block1(self, testimony: Dict, design: Dict, context: Dict) -> str:
        """Generate Block 1 using original n8n prompt template"""
        prompt_data = self._prepare_prompt_data(testimony, design, context)
        prompt = BLOCK1_PROMPT.format(**prompt_data)
        config = self._get_block_config(design, 'block1')

        try:
            content = self._call_llm_with_retry(prompt, temperature=0.9, max_tokens=config['tokens'], min_words=config['min'], max_words=config['max'])
            content = content.strip()
            if content.startswith('```markdown'):
                content = content.split('```markdown', 1)[1]
            if content.startswith('```'):
                content = content.split('```', 1)[1]
            if content.endswith('```'):
                content = content.rsplit('```', 1)[0]
            content = content.strip()

            word_count = self._count_words(content)
            print(f"    ✓ Block 1 generated: {word_count} words")
            return content
        except Exception as e:
            print(f"Error generating block 1: {str(e)}")
            return "Error generating block 1"

    def generate_block2(self, testimony: Dict, design: Dict, context: Dict) -> str:
        """Generate Block 2 using original n8n prompt template"""
        prompt_data = self._prepare_prompt_data(testimony, design, context)
        prompt = BLOCK2_PROMPT.format(**prompt_data)
        config = self._get_block_config(design, 'block2')

        try:
            content = self._call_llm_with_retry(prompt, temperature=0.9, max_tokens=config['tokens'], min_words=config['min'], max_words=config['max'])
            content = content.strip()
            if content.startswith('```markdown'):
                content = content.split('```markdown', 1)[1]
            if content.startswith('```'):
                content = content.split('```', 1)[1]
            if content.endswith('```'):
                content = content.rsplit('```', 1)[0]
            content = content.strip()

            word_count = self._count_words(content)
            print(f"    ✓ Block 2 generated: {word_count} words")
            return content
        except Exception as e:
            print(f"Error generating block 2: {str(e)}")
            return "Error generating block 2"

    def generate_block3(self, testimony: Dict, design: Dict, context: Dict) -> str:
        """Generate Block 3 using original n8n prompt template"""
        prompt_data = self._prepare_prompt_data(testimony, design, context)
        base_prompt = BLOCK3_PROMPT.format(**prompt_data)
        config = self._get_block_config(design, 'block3')

        prompt = base_prompt

        compliance_context = self.vector_search.get_compliance_context('block3')
        if compliance_context:
            prompt = f"{base_prompt}\n\n{compliance_context}"

        try:
            content = self._call_llm_with_retry(prompt, temperature=0.9, max_tokens=config['tokens'], min_words=config['min'], max_words=config['max'])
            try:
                data = json.loads(content)
                draft = data.get('markdown_draft', content)
                word_count = self._count_words(draft)
                if word_count < config['min']:
                    draft = self._expand_content(draft, config['min'], "")
                    word_count = self._count_words(draft)
                print(f"    ✓ Block 3 generated: {word_count} words")
                return draft
            except (json.JSONDecodeError, KeyError, TypeError):
                word_count = self._count_words(content)
                if word_count < config['min']:
                    content = self._expand_content(content, config['min'], "")
                    word_count = self._count_words(content)
                print(f"    ✓ Block 3 generated: {word_count} words")
                return content
        except Exception as e:
            print(f"Error generating block 3: {str(e)}")
            return "Error generating block 3"

    def generate_block4(self, testimony: Dict, design: Dict, context: Dict) -> str:
        """Generate Block 4 using original n8n prompt template"""
        prompt_data = self._prepare_prompt_data(testimony, design, context)
        prompt = BLOCK4_PROMPT.format(**prompt_data)
        config = self._get_block_config(design, 'block4')

        try:
            content = self._call_llm_with_retry(prompt, temperature=0.9, max_tokens=config['tokens'], min_words=config['min'], max_words=config['max'])
            content = content.strip()
            if content.startswith('```markdown'):
                content = content.split('```markdown', 1)[1]
            if content.startswith('```'):
                content = content.split('```', 1)[1]
            if content.endswith('```'):
                content = content.rsplit('```', 1)[0]
            content = content.strip()

            word_count = self._count_words(content)
            print(f"    ✓ Block 4 generated: {word_count} words")
            return content
        except Exception as e:
            print(f"Error generating block 4: {str(e)}")
            return "Error generating block 4"

    def generate_block5(self, testimony: Dict, design: Dict, context: Dict) -> str:
        """Generate Block 5 using original n8n prompt template"""
        prompt_data = self._prepare_prompt_data(testimony, design, context)
        prompt = BLOCK5_PROMPT.format(**prompt_data)
        config = self._get_block_config(design, 'block5')

        try:
            content = self._call_llm_with_retry(prompt, temperature=0.9, max_tokens=config['tokens'], min_words=config['min'], max_words=config['max'])
            content = content.strip()
            if content.startswith('```markdown'):
                content = content.split('```markdown', 1)[1]
            if content.startswith('```'):
                content = content.split('```', 1)[1]
            if content.endswith('```'):
                content = content.rsplit('```', 1)[0]
            content = content.strip()

            word_count = self._count_words(content)
            print(f"    ✓ Block 5 generated: {word_count} words")
            return content
        except Exception as e:
            print(f"Error generating block 5: {str(e)}")
            return "Error generating block 5"

    def generate_all_blocks(self, testimony: Dict, design: Dict, context: Dict) -> Dict[str, str]:
        """Generate all 5 blocks in parallel for maximum performance"""
        recommender_name = testimony.get('recommender_name', 'Unknown')
        length_profile = design.get('length_profile', 'standard')
        total_words_target = sum(LENGTH_PROFILES.get(length_profile, LENGTH_PROFILES['standard'])[f'block{i}']['min'] for i in range(1, 6))
        print(f"Generating 5 blocks in parallel for {recommender_name}...")
        print(f"    📏 Length profile: {length_profile.upper()} (~{total_words_target} words target)")

        blocks = {}

        block_tasks = {
            "block1": (self.generate_block1, testimony, design, context),
            "block2": (self.generate_block2, testimony, design, context),
            "block3": (self.generate_block3, testimony, design, context),
            "block4": (self.generate_block4, testimony, design, context),
            "block5": (self.generate_block5, testimony, design, context)
        }

        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_block = {
                executor.submit(func, *args): block_name
                for block_name, (func, *args) in block_tasks.items()
            }

            for future in as_completed(future_to_block):
                block_name = future_to_block[future]
                try:
                    blocks[block_name] = future.result()
                except Exception as exc:
                    print(f"    ✗ {block_name} failed: {exc}")
                    blocks[block_name] = f"Error generating {block_name}: {exc}"

        print(f"    ✓ All 5 blocks completed for {recommender_name}")
        return blocks

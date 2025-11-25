from typing import Dict, Optional
import json
import time
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from .block_prompts import (
    BLOCK1_PROMPT, BLOCK2_PROMPT, BLOCK3_PROMPT, 
    BLOCK4_PROMPT, BLOCK5_PROMPT
)


class BlockGenerator:
    def __init__(self, llm_processor, prompt_enhancer=None, rag_engine=None):
        self.llm = llm_processor
        self.prompt_enhancer = prompt_enhancer  # ML-powered prompt improvement
        self.rag = rag_engine  # RAG for context retrieval

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
            # Design structure parameters (n8n schema)
            'tone_variable': design.get('tone_variable', ''),
            'tone_instructions': design.get('tone_instructions', ''),
            'narrative_framework': design.get('narrative_framework', ''),
            'paragraph_density_rule': design.get('paragraph_density_rule', ''),
            
            # O*NET parameters
            'onet_tasks': onet.get('representative_tasks', ''),
            'onet_tools': onet.get('tools_and_technologies', ''),
            'onet_activities': onet.get('work_activities_and_skills', ''),
            
            # Strategy parameters
            'strategy_services': strategy.get('services_offered', ''),
            'strategy_clients': strategy.get('target_clients', ''),
            
            # Petitioner parameters
            'petitioner_name': petitioner.get('name', ''),
            'petitioner_education': petitioner.get('education', ''),
            'petitioner_experience': petitioner.get('experience', ''),
            
            # Testimony parameters
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
    
    def generate_block1(self, testimony: Dict, design: Dict, context: Dict) -> str:
        """Generate Block 1 using original n8n prompt template"""
        prompt_data = self._prepare_prompt_data(testimony, design, context)
        prompt = BLOCK1_PROMPT.format(**prompt_data)
        
        try:
            content = self._call_llm_with_retry(prompt, temperature=0.9, max_tokens=2500, min_words=300, max_words=600)
            # Clean any accidental markdown fences
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
        
        try:
            content = self._call_llm_with_retry(prompt, temperature=0.9, max_tokens=2500, min_words=300, max_words=600)
            # Clean any accidental markdown fences
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
    
    def generate_block3(self, testimony: Dict, design: Dict, context: Dict, letter_embedding: Optional[list] = None) -> str:
        """Generate Block 3 using original n8n prompt template"""
        prompt_data = self._prepare_prompt_data(testimony, design, context)
        base_prompt = BLOCK3_PROMPT.format(**prompt_data)
        
        # RAG Enhancement - DISABLED
        # prompt = base_prompt
        # if self.rag and context.get('submission_id'):
        #     ... (RAG logic removed)
        
        # ML-powered prompt enhancement - DISABLED
        # if self.prompt_enhancer:
        #     ... (ML logic removed)
        
        prompt = base_prompt # Use base prompt only
        
        try:
            content = self._call_llm_with_retry(prompt, temperature=0.9, max_tokens=4000, min_words=500, max_words=700)
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
        """Generate Block 4 using original n8n prompt template"""
        prompt_data = self._prepare_prompt_data(testimony, design, context)
        prompt = BLOCK4_PROMPT.format(**prompt_data)
        
        try:
            content = self._call_llm_with_retry(prompt, temperature=0.9, max_tokens=2500, min_words=350, max_words=600)
            # Clean any accidental markdown fences
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
        
        try:
            content = self._call_llm_with_retry(prompt, temperature=0.9, max_tokens=2500, min_words=300, max_words=600)
            # Clean any accidental markdown fences
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
        print(f"Generating 5 blocks in parallel for {recommender_name}...")

        blocks = {}

        # Define block generation tasks (Blocks 1-5 matching n8n)
        block_tasks = {
            "block1": (self.generate_block1, testimony, design, context),
            "block2": (self.generate_block2, testimony, design, context),
            "block3": (self.generate_block3, testimony, design, context),
            "block4": (self.generate_block4, testimony, design, context),
            "block5": (self.generate_block5, testimony, design, context)
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

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
    
    def generate_block1(self, testimony: Dict, design: Dict, context: Dict) -> str:
        """Generate Block 1 using original n8n prompt template"""
        prompt_data = self._prepare_prompt_data(testimony, design, context)
        prompt = BLOCK1_PROMPT.format(**prompt_data)
        
        try:
            content = self._call_llm_with_retry(prompt, temperature=0.9, max_tokens=2500, min_words=300, max_words=600)
            try:
                data = json.loads(content)
                draft = data.get('markdown_draft', content)
                word_count = self._count_words(draft)
                print(f"    ✓ Block 1 generated: {word_count} words")
                return draft
            except (json.JSONDecodeError, KeyError, TypeError):
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
            try:
                data = json.loads(content)
                draft = data.get('markdown_draft', content)
                word_count = self._count_words(draft)
                print(f"    ✓ Block 2 generated: {word_count} words")
                return draft
            except (json.JSONDecodeError, KeyError, TypeError):
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
        
        # RAG Enhancement: Retrieve relevant context
        prompt = base_prompt
        if self.rag and context.get('submission_id'):
            try:
                # Build search query from testimony context
                query = f"Examples of professional accomplishments and technical expertise for {testimony.get('recommender_role', 'professional')} at {testimony.get('recommender_company', 'company')}"
                
                context_chunks = self.rag.retrieve_context(
                    query=query,
                    submission_id=context['submission_id'],
                    top_k=3
                )
                
                # Augment prompt with retrieved context
                if context_chunks:
                    prompt = self.rag.augment_prompt(base_prompt, context_chunks)
            except Exception as e:
                print(f"   ℹ️  RAG context retrieval skipped: {e}")
        
        # ML-powered prompt enhancement
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
            content = self._call_llm_with_retry(prompt, temperature=0.9, max_tokens=4000, min_words=500, max_words=700)
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
        """Generate Block 4 using original n8n prompt template"""
        prompt_data = self._prepare_prompt_data(testimony, design, context)
        prompt = BLOCK4_PROMPT.format(**prompt_data)
        
        try:
            content = self._call_llm_with_retry(prompt, temperature=0.9, max_tokens=2500, min_words=350, max_words=600)
            try:
                data = json.loads(content)
                draft = data.get('markdown_draft', content)
                word_count = self._count_words(draft)
                print(f"    ✓ Block 4 generated: {word_count} words")
                return draft
            except (json.JSONDecodeError, KeyError, TypeError):
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
            try:
                data = json.loads(content)
                draft = data.get('markdown_draft', content)
                word_count = self._count_words(draft)
                print(f"    ✓ Block 5 generated: {word_count} words")
                return draft
            except (json.JSONDecodeError, KeyError, TypeError):
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

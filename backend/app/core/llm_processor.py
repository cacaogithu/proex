from openai import OpenAI
import json
import os
import time
from typing import Dict, List


class LLMProcessor:
    def __init__(self):
        # Using OpenRouter.ai - More cost-effective with multiple model options
        # GPT-4o Mini: Fast and cheap for data extraction
        # Gemini 2.5 Flash: High quality for content generation
        # Claude 3.5 Sonnet: Best for HTML/document assembly
        self.client = OpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1"
        )

        self.models = {
            "fast": "openai/gpt-4o-mini",
            "quality": "google/gemini-2.5-flash",
            "premium": "anthropic/claude-3.5-sonnet"
        }

        # Fallback models if primary fails (400/404 = invalid model ID)
        self._fallback_models = {
            "openai/gpt-4o-mini": ["google/gemini-2.5-flash", "anthropic/claude-3.5-sonnet"],
            "google/gemini-2.5-flash": ["openai/gpt-4o-mini", "anthropic/claude-3.5-sonnet"],
            "anthropic/claude-3.5-sonnet": ["openai/gpt-4o-mini", "google/gemini-2.5-flash"],
        }

    def _call_llm(self, model: str, messages: list, **kwargs):
        """Call LLM with automatic fallback on invalid model errors (400/404)."""
        models_to_try = [model] + self._fallback_models.get(model, [])
        last_error = None
        for m in models_to_try:
            try:
                return self.client.chat.completions.create(
                    model=m, messages=messages, **kwargs
                )
            except Exception as e:
                err_str = str(e)
                # Only fallback on model-not-found errors, not on rate limits or other issues
                if "400" in err_str or "404" in err_str or "not a valid model" in err_str:
                    print(f"Model {m} unavailable, trying fallback...")
                    last_error = e
                    continue
                raise
        raise last_error
    
    def clean_and_organize(self, extracted_texts: Dict) -> Dict:
        testimonials_text = "\n\n---\n\n".join([
            f"Testimonial {i+1}:\n{text}" 
            for i, text in enumerate(extracted_texts.get('testimonials', []))
        ])
        
        prompt = f"""# Role
Você é um editor de documentos excepcional para ProEx Venture. 
Pegue os inputs fragmentados e produza outputs estruturados em JSON.

# Inputs
Quadro: {extracted_texts.get('quadro', '')}

CV: {extracted_texts.get('cv', '')}

Estrategia: {extracted_texts.get('estrategia', 'N/A')}

OneNote: {extracted_texts.get('onenote', 'N/A')}

Testimonials:
{testimonials_text}

# Output
Retorne APENAS JSON válido (sem markdown, sem code fences):
{{
  "petitioner": {{
    "name": "...",
    "education": ["..."],
    "experience": ["..."]
  }},
  "strategy": {{
    "services_offered": ["..."],
    "target_clients": "..."
  }},
  "additional_documents": [
    {{
      "filename": "...",
      "text": "..."
    }}
  ],
  "onet": {{
    "representative_tasks": ["..."],
    "tools_and_technologies": ["..."],
    "work_activities_and_skills": ["..."]
  }},
  "testimonies": [
    {{
      "testimony_id": "1",
      "recommender_name": "...",
      "recommender_company": "...",
      "recommender_company_website": "...",
      "recommender_role": "...",
      "recommender_location": "...",
      "collaboration_period": "...",
      "applicant_role": "...",
      "testimony_text": "...",
      "key_achievements": ["..."]
    }}
  ]
}}

# Regras
- Extraia TODOS os testemunhos (quantidade variável)
- Para cada testemunho, tente extrair:
  * Website da empresa do recomendador (URL completa se disponível)
  * Localização do recomendador (cidade, estado, país - formato: "São Paulo, Brazil" ou "New York, USA")
- Se OneNote ou Estrategia faltando, use os dados disponíveis
- Não invente fatos - se localização não estiver no texto, deixe vazio
- Output em português
- Retorne JSON puro sem markdown
"""
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self._call_llm(
                    model=self.models["fast"],
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"}
                )
                
                content = response.choices[0].message.content
                if content:
                    return json.loads(content)
                raise ValueError("Empty response from LLM")
            except Exception as e:
                if "429" in str(e) and attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 3
                    print(f"⏳ Rate limit hit, waiting {wait_time}s before retry {attempt + 1}/{max_retries}...")
                    time.sleep(wait_time)
                    continue
                if attempt == max_retries - 1:
                    print(f"Error in clean_and_organize: {str(e)}")
                    raise
        # This line is unreachable - exception will always be raised above
        raise RuntimeError("clean_and_organize failed after all retries")
    
    def generate_search_query(self, testimony: Dict, context: Dict) -> str:
        """Generate an AI-based search query for vector search instead of static template"""
        prompt = f"""# ROLE
You are a search query optimization expert. Generate a highly specific, contextual search query.

# INPUTS
Recommender Name: {testimony.get('recommender_name', 'Unknown')}
Recommender Role: {testimony.get('recommender_role', 'N/A')}
Recommender Company: {testimony.get('recommender_company', 'N/A')}
Collaboration Period: {testimony.get('collaboration_period', 'N/A')}
Applicant Role in Context: {testimony.get('applicant_role', 'N/A')}
Key Achievements: {json.dumps(testimony.get('key_achievements', []), ensure_ascii=False)}
Testimony Excerpt: {testimony.get('testimony_text', '')[:500]}

Petitioner Background: {json.dumps(context.get('petitioner', {}), ensure_ascii=False)[:500]}
Strategy/Services: {json.dumps(context.get('strategy', {}), ensure_ascii=False)[:500]}

# OUTPUT
Generate ONE specific, contextual search query (2-4 sentences max) that would retrieve:
- Relevant professional achievements and technical expertise
- Specific accomplishments mentioned in this testimony
- Industry-specific skills and methodologies
- Measurable results and quantifiable impacts
- Unique technical contributions

Make the query SPECIFIC to this recommender's role, company, and the applicant's context.
Avoid generic queries - be precise and actionable.

Return ONLY the search query text, nothing else."""
        
        try:
            response = self._call_llm(
                model=self.models["fast"],
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=200
            )
            content = response.choices[0].message.content
            if content:
                return content.strip()
            raise ValueError("Empty response from LLM")
        except Exception as e:
            # Fallback to a more intelligent static query if AI fails
            role = testimony.get('recommender_role', 'professional')
            company = testimony.get('recommender_company', 'company')
            achievements = ", ".join(testimony.get('key_achievements', [])[:3])
            return f"Professional accomplishments and technical expertise of {role} at {company}. Key achievements: {achievements}"

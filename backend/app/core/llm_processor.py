from openai import OpenAI
import json
import os
import time
from typing import Dict, List


class LLMProcessor:
    def __init__(self):
        # Using OpenRouter.ai - More cost-effective with multiple model options
        # Gemini Flash: Fast and cheap for data organization
        # Gemini 2.5 Pro: High quality for content generation
        # Claude 4.5 Sonnet: Best for HTML/document assembly
        self.client = OpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1"
        )
        
        self.models = {
            "fast": "google/gemini-2.5-flash",
            "quality": "google/gemini-2.5-flash",
            "premium": "anthropic/claude-3.5-sonnet"
        }
    
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
      "collaboration_period": "...",
      "applicant_role": "...",
      "testimony_text": "...",
      "key_achievements": ["..."]
    }}
  ]
}}

# Regras
- Extraia TODOS os testemunhos (quantidade variável)
- Para cada testemunho, tente extrair o website da empresa do recomendador
- Se OneNote ou Estrategia faltando, use os dados disponíveis
- Não invente fatos
- Output em português
- Retorne JSON puro sem markdown
"""
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Using Gemini Flash - fast and cheap for data extraction
                response = self.client.chat.completions.create(
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

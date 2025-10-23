from openai import OpenAI
import json
import os
import time
from typing import Dict, List


class LLMProcessor:
    def __init__(self):
        # Using Replit AI Integrations - provides OpenAI-compatible API without requiring your own API key
        # Charges are billed to your Replit credits
        self.client = OpenAI(
            api_key=os.getenv("AI_INTEGRATIONS_OPENAI_API_KEY"),
            base_url=os.getenv("AI_INTEGRATIONS_OPENAI_BASE_URL")
        )
    
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
- Se OneNote ou Estrategia faltando, use os dados disponíveis
- Não invente fatos
- Output em português
- Retorne JSON puro sem markdown
"""
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # The newest OpenAI model is "gpt-5" which was released August 7, 2025.
                # Do not change this unless explicitly requested by the user
                response = self.client.chat.completions.create(
                    model="gpt-4o",
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
        return {}

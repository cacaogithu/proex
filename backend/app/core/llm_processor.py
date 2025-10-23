from openai import OpenAI
import json
import os
from typing import Dict, List


class LLMProcessor:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
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
        
        try:
            response = self.client.chat.completions.create(
                model="gemini-2.0-flash-exp",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            print(f"Error in clean_and_organize: {str(e)}")
            raise

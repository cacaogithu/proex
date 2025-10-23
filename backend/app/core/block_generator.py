from typing import Dict
import json


class BlockGenerator:
    def __init__(self, llm_processor):
        self.llm = llm_processor
    
    def generate_block3(self, testimony: Dict, design: Dict, context: Dict) -> str:
        prompt = f"""# ROLE
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
400–600 palavras. Primeira pessoa. Evidências quantitativas e qualitativas.
- Pelo menos 3 métricas quantitativas
- 1-2 observações qualitativas
- Lista com 4-6 resultados empíricos

# REGRAS
- Voz: primeira pessoa (recomendador falando)
- Foco: resultados apenas
- Estilo: profissional, preciso, executivo
- Output: Markdown apenas, sem HTML
- TODO EM PORTUGUÊS
- Remova termos: "imigração", "EB2-NIW", "peticionário"
"""
        
        try:
            response = self.llm.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.9
            )
            
            content = response.choices[0].message.content
            try:
                data = json.loads(content)
                return data.get('markdown_draft', content)
            except:
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
500–700 palavras. Destaque capacidades técnicas únicas.
- Abordagens metodológicas exclusivas
- Ferramentas e tecnologias avançadas
- Processos inovadores

# REGRAS
- Primeira pessoa
- Linguagem técnica mas acessível
- TODO EM PORTUGUÊS
"""
        
        try:
            response = self.llm.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.9
            )
            return response.choices[0].message.content
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
400–600 palavras. Demonstre influência além do contexto imediato.
- Reconhecimento por pares
- Contribuições para o setor
- Disseminação de conhecimento

# REGRAS
- Primeira pessoa
- Evidências concretas
- TODO EM PORTUGUÊS
"""
        
        try:
            response = self.llm.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.9
            )
            return response.choices[0].message.content
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
300–400 palavras. Estabeleça credibilidade.
- Experiência relevante
- Posição para avaliar o trabalho
- Contexto da colaboração

# REGRAS
- Primeira pessoa
- Profissional
- TODO EM PORTUGUÊS
"""
        
        try:
            response = self.llm.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.9
            )
            return response.choices[0].message.content
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
200–300 palavras. Encerramento forte.
- Síntese de valor
- Recomendação clara
- Perspectiva futura

# REGRAS
- Primeira pessoa
- Tom conclusivo
- TODO EM PORTUGUÊS
"""
        
        try:
            response = self.llm.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.9
            )
            return response.choices[0].message.content
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

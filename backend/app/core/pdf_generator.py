from weasyprint import HTML
import markdown as md
from typing import Dict
import os


class PDFGenerator:
    def assemble_letter(self, blocks: Dict[str, str], design: Dict, llm) -> str:
        combined_blocks = f"""
# BLOCO 3
{blocks.get('block3', '')}

# BLOCO 4
{blocks.get('block4', '')}

# BLOCO 5
{blocks.get('block5', '')}

# BLOCO 6
{blocks.get('block6', '')}

# BLOCO 7
{blocks.get('block7', '')}
"""
        
        prompt = f"""# ROLE
Você é um revisor de classe mundial. Receba 5 blocos de uma carta de testemunho 
e produza o texto completo.

**PERSONA**: {design.get('tone_instructions', '')}

# INPUTS
{combined_blocks}

# INSTRUÇÕES
1. Leia todos os blocos
2. Verifique transições e fluxo
3. Remova palavras "inferência lógica", "inferência técnica", "nexo causal" se usadas mal
4. Não referencie "application", "EB2-NIW", "peticionário"
5. Seja autêntico
6. Output: APENAS texto Markdown puro (sem JSON, sem YAML, sem triple backticks)
7. Adicione cabeçalho com nome do recomendador: {design.get('assigned_recommender', '')}

# HETEROGENEIDADE
Garanta que o testemunho tenha voz e estrutura exclusivas. Evite repetições.
Causalidade direta: "Realizou X, gerando Y resultado"

# TODO EM PORTUGUÊS
"""
        
        try:
            response = llm.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error assembling letter: {str(e)}")
            return combined_blocks
    
    def markdown_to_pdf(self, markdown_text: str, output_path: str, design: Dict):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        html_content = md.markdown(markdown_text, extensions=['extra', 'nl2br'])
        
        css = self._generate_css(design)
        
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>{css}</style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
        
        try:
            HTML(string=full_html).write_pdf(output_path)
            print(f"PDF generated successfully: {output_path}")
        except Exception as e:
            print(f"Error generating PDF: {str(e)}")
            with open(output_path.replace('.pdf', '.html'), 'w', encoding='utf-8') as f:
                f.write(full_html)
            print(f"Saved as HTML instead: {output_path.replace('.pdf', '.html')}")
    
    def _generate_css(self, design: Dict) -> str:
        return """
        @page {
            size: A4;
            margin: 2.5cm;
        }
        
        body {
            font-family: 'Georgia', 'Times New Roman', serif;
            font-size: 12pt;
            line-height: 1.6;
            color: #333;
            text-align: justify;
        }
        
        h1 {
            color: #2c3e50;
            font-size: 18pt;
            margin-top: 0;
            margin-bottom: 1em;
            text-align: center;
        }
        
        h2 {
            color: #34495e;
            font-size: 14pt;
            margin-top: 1.5em;
            margin-bottom: 0.75em;
        }
        
        h3 {
            color: #34495e;
            font-size: 12pt;
            margin-top: 1.2em;
            margin-bottom: 0.6em;
        }
        
        p {
            margin-bottom: 1em;
            orphans: 3;
            widows: 3;
        }
        
        ul, ol {
            margin-left: 1.5em;
            margin-bottom: 1em;
        }
        
        li {
            margin-bottom: 0.5em;
        }
        
        strong {
            font-weight: bold;
            color: #2c3e50;
        }
        
        em {
            font-style: italic;
        }
        """

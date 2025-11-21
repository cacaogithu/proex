from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS
from typing import Dict, Optional
import os
from datetime import datetime
import uuid
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from html4docx import HtmlToDocx
import re

class HTMLPDFGenerator:
    def __init__(self):
        template_dir = os.path.join(os.path.dirname(__file__), '../templates')
        self.env = Environment(loader=FileSystemLoader(template_dir))
        
        self.template_mapping = {
            'A': 'template_a_technical.html',
            'B': 'template_b_academic.html',
            'C': 'template_c_narrative.html',
            'D': 'template_d_business.html',
            'E': 'template_e_usa_support.html',
            'F': 'template_f_technical_testimony.html'
        }
    
    def assemble_letter(self, blocks: Dict[str, str], design: Dict, llm) -> str:
        """Use Claude 4.5 Sonnet for premium HTML assembly - returns HTML content"""
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
        
        template_id = design.get('template_id', 'A')
        
        # Define estilo específico por template
        style_guidance = {
            'A': """
ESTILO TÉCNICO PROFUNDO:
- Use MUITAS siglas e termos técnicos (PLC, SCADA, ISO, NR10, OEE, MTBF, Six Sigma, Cpk)
- Inclua tabelas com dados técnicos quando possível
- Números extremamente precisos (ex: "97.3% de redução", "2.847 horas economizadas")
- Formatação: Use tags HTML <table>, <strong> para siglas, <em> para métricas
- Classe CSS especial: `<div class="technical-metrics">` para métricas importantes
""",
            'B': """
ESTILO ACADÊMICO - CASE STUDY:
- Estruture em SEÇÕES EXPLÍCITAS: INTRODUÇÃO, METODOLOGIA, RESULTADOS, CONCLUSÃO
- Use framework Six Sigma DMAIC quando relevante (Define, Measure, Analyze, Improve, Control)
- Inclua tabelas de correlação técnica
- Formatação: Use <h2> para seções, `<div class="methodology">` para listas metodológicas
- Classe CSS: `<div class="abstract">` para resumos executivos
""",
            'C': """
ESTILO NARRATIVO - STORYTELLING:
- Conte uma HISTÓRIA de transformação: problema → jornada → solução → legado
- Use linguagem pessoal e emotiva (primeira pessoa)
- Mencione prêmios e reconhecimentos quando aplicável
- Formatação: Use `<blockquote>` para citações, `<div class="journey">` para momentos-chave
- Classe CSS: `<span class="impact-highlight">` para highlights importantes
""",
            'D': """
ESTILO BUSINESS PARTNERSHIP:
- Foco em ROI, parceria estratégica, crescimento de receita
- Use bullet points com checkmarks para entregas
- Destaque métricas financeiras e de negócio
- Formatação: Use `<ul>` para listas, `<div class="roi-highlight">` para ROI
- Classe CSS: `<div class="key-metrics">` para métricas principais
""",
            'E': """
ESTILO SUPPORT LETTER (USA):
- Formato americano: cidade, estado (ex: "Boston, MA")
- Contexto do mercado americano
- Quadros de resultados visuais
- Formatação: Use `<table class="results-table">` para resultados
- Classe CSS: `<div class="us-market-context">` para contexto de mercado
""",
            'F': """
ESTILO TECHNICAL TESTIMONY:
- Referências a documentação anexa (ex: "conforme Anexo A", "ver documento REF-2024-001")
- Foco em trabalho em equipe e colaboração
- Tabelas e quadros explicativos
- Formatação: Use `<div class="reference-box">` para referências
- Classe CSS: `<div class="collaboration-details">` para detalhes de colaboração
"""
        }
        
        style = style_guidance.get(template_id, style_guidance['A'])
        
        prompt = f"""# ROLE
Você é um revisor de classe mundial especializado em cartas de recomendação profissionais. 
Receba 5 blocos de uma carta e produza o conteúdo HTML COMPLETO E ESTILIZADO.

**TEMPLATE ASSIGNED**: {template_id}
**PERSONA**: {design.get('tone_instructions', '')}
**ESTILO VISUAL**: 
{style}

# INPUTS
{combined_blocks}

# INSTRUÇÕES CRÍTICAS DE CONTEÚDO
1. Leia todos os blocos e crie uma narrativa coesa
2. Verifique transições suaves entre seções
3. REMOVA palavras problemáticas: "inferência lógica", "inferência técnica", "nexo causal" se mal usadas
4. NUNCA mencione: "application", "EB2-NIW", "peticionário", "visto", "imigração"
5. Seja autêntico e pessoal (primeira pessoa)
6. Adicione assinatura e encerramento apropriado

# INSTRUÇÕES DE FORMATAÇÃO HTML
1. Output: APENAS o conteúdo HTML (sem <!DOCTYPE>, <html>, <head>, <body> - só o conteúdo interno) - **CRITICAL: Do not include `<html>`, `<head>`, or `<body>` tags. Only the content inside the body.**
2. Use as classes CSS específicas do template conforme indicado acima
3. Estruture com tags semânticas: <p>, <h2>, <ul>, <li>, <table>, <blockquote>, <div>
4. Use <strong> para ênfases, <em> para itálico
5. Aplique as classes CSS especiais para destacar informações importantes

# ESTRUTURA DO CONTEÚDO
1. Saudação formal ("A quem possa interessar," ou similar)
2. Blocos integrados em narrativa fluida
3. Use as divisões <h2> se aplicável ao template
4. Encerramento formal apropriado ao template

# HETEROGENEIDADE
- Garanta que este testemunho tenha voz única
- Siga rigorosamente o estilo visual do template {template_id}
- Use causalidade direta: "Realizou X, gerando Y resultado"
- Mantenha tom profissional mas humano

# TODO EM PORTUGUÊS BRASILEIRO

Output: APENAS HTML content (sem tags <html>, <head>, <body>) - **CRITICAL: Do not include `<html>`, `<head>`, or `<body>` tags. Only the content inside the body.**
"""
        
        import time
        for attempt in range(3):
            try:
                response = llm.client.chat.completions.create(
                    model="anthropic/claude-3.5-sonnet",
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }],
                    temperature=0.3,
                    max_tokens=12000  # Increased for longer content
                )
                
                html_content = response.choices[0].message.content.strip()
                
                # Remove markdown code blocks if present
                if html_content.startswith('```html'):
                    html_content = html_content.split('```html')[1]
                if html_content.startswith('```'):
                    html_content = html_content.split('```')[1]
                if html_content.endswith('```'):
                    html_content = html_content.rsplit('```', 1)[0]
                
                html_content = html_content.strip()
                
                print(f"✅ Letter assembled with Claude 4.5 Sonnet (Template {template_id})")
                return html_content
                
            except Exception as e:
                if "429" in str(e) or "rate" in str(e).lower():
                    wait_time = 2 ** attempt
                    print(f"⚠️ Rate limit hit, waiting {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise
        
        raise Exception("Failed to assemble letter after 3 attempts")
    
    def html_to_pdf(
        self, 
        html_content: str, 
        output_path: str, 
        design: Dict,
        logo_path: Optional[str] = None,
        recommender_info: Optional[Dict] = None
    ):
        """Convert HTML to PDF using template with proper styling"""
        
        template_id = design.get('template_id', 'A')
        template_file = self.template_mapping.get(template_id, 'template_a_technical.html')
        
        template = self.env.get_template(template_file)
        
        # Generate document reference for template F
        document_ref = f"DOC-{uuid.uuid4().hex[:8].upper()}"
        
        # Prepare template variables
        template_vars = {
            'content': html_content,
            'logo_path': f'file://{os.path.abspath(logo_path)}' if logo_path and os.path.exists(logo_path) else None,
            'recommender_name': recommender_info.get('name', 'Professional Recommender') if recommender_info else 'Professional Recommender',
            'recommender_title': recommender_info.get('title', '') if recommender_info else '',
            'recommender_company': recommender_info.get('company', '') if recommender_info else '',
            'recommender_location': recommender_info.get('location', '') if recommender_info else '',
            'date': datetime.now().strftime('%B %d, %Y'),
            'document_ref': document_ref
        }
        
        # Render template
        full_html = template.render(**template_vars)
        
        # Create output directory if needed
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Convert to PDF
        HTML(string=full_html, base_url=os.path.dirname(template_file)).write_pdf(output_path)
        
        print(f"✅ PDF generated with template {template_id}: {os.path.basename(output_path)}")
    
    def html_to_docx(
        self,
        html_content: str,
        output_path: str,
        design: Dict,
        logo_path: Optional[str] = None,
        recommender_info: Optional[Dict] = None
    ):
        """Convert HTML to editable DOCX for consultant editing"""
        
        # Create new document
        doc = Document()
        
        # Set margins
        sections = doc.sections
        for section in sections:
            section.top_margin = Inches(1)
            section.bottom_margin = Inches(1)
            section.left_margin = Inches(1)
            section.right_margin = Inches(1)
        
        # Add logo at top if available
        if logo_path and os.path.exists(logo_path):
            try:
                doc.add_picture(logo_path, width=Inches(2.5))
                last_paragraph = doc.paragraphs[-1]
                last_paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT
            except Exception as e:
                print(f"⚠️ Could not add logo to DOCX: {e}")
        
        # Add header info
        if recommender_info:
            header_p = doc.add_paragraph()
            header_run = header_p.add_run(f"{recommender_info.get('name', '')}\n")
            header_run.bold = True
            header_run.font.size = Pt(12)
            
            if recommender_info.get('title'):
                header_p.add_run(f"{recommender_info['title']}\n").font.size = Pt(10)
            if recommender_info.get('company'):
                header_p.add_run(f"{recommender_info['company']}\n").font.size = Pt(10)
            if recommender_info.get('location'):
                header_p.add_run(f"{recommender_info['location']}\n").font.size = Pt(10)
        
        # Add date
        date_p = doc.add_paragraph(datetime.now().strftime('%B %d, %Y'))
        date_p.add_run('\n')
        
        # Convert HTML content to DOCX
        parser = HtmlToDocx()
        parser.table_style = 'Light Grid Accent 1'
        
        # Clean HTML - remove problematic styling
        clean_html = html_content
        
        # Add the cleaned HTML to document
        try:
            parser.add_html_to_document(clean_html, doc)
        except Exception as e:
            print(f"⚠️  HTML parsing error, using fallback: {e}")
            # Fallback: strip HTML tags and add as plain text
            plain_text = re.sub('<[^<]+?>', '', html_content)
            doc.add_paragraph(plain_text)
        
        # Create output directory if needed
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save DOCX
        doc.save(output_path)
        
        template_id = design.get('template_id', 'A')
        print(f"✅ Editable DOCX generated with template {template_id}: {os.path.basename(output_path)}")

# Keep backward compatibility
class DOCXGenerator(HTMLPDFGenerator):
    """Backward compatibility wrapper - now generates PDFs with HTML templates"""
    
    def markdown_to_docx(self, markdown_content: str, output_path: str, design: Dict, logo_path: Optional[str] = None):
        """Legacy method - redirects to HTML/PDF generation"""
        # Extract recommender info from markdown if present
        recommender_info = {
            'name': design.get('assigned_recommender', 'Professional Recommender'),
            'title': '',
            'company': '',
            'location': ''
        }
        
        # Change extension from .docx to .pdf
        if output_path.endswith('.docx'):
            output_path = output_path.replace('.docx', '.pdf')
        
        self.html_to_pdf(markdown_content, output_path, design, logo_path, recommender_info)

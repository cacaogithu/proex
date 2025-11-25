from jinja2 import Environment, FileSystemLoader
try:
    from weasyprint import HTML, CSS
except OSError:
    print("WARNING: WeasyPrint system dependencies not found. PDF generation will fail.")
    HTML = None
    CSS = None
from typing import Dict, Optional
import os
from datetime import datetime
import uuid
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
try:
    from html4docx import HtmlToDocx
except ImportError:
    print("WARNING: html4docx not found or incompatible. DOCX generation will fail.")
    HtmlToDocx = None
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
    
    def assemble_letter(self, blocks: Dict[str, str], design: Dict, llm, custom_instructions: Optional[str] = None) -> str:
        """Convert markdown blocks to HTML with proper formatting - preserves all content"""
        
        # Import markdown converter
        try:
            import markdown
            md_converter = markdown.Markdown(extensions=['extra', 'nl2br', 'sane_lists'])
        except ImportError:
            print("⚠️  markdown library not found, using simple conversion")
            md_converter = None
        
        # Combine ALL blocks (1-5) - previously only used 3-7
        combined_blocks = f"""
# Block 1: Leadership & Credibility
{blocks.get('block1', '')}

# Block 2: Technical Innovation
{blocks.get('block2', '')}

# Block 3: Empirical Validation
{blocks.get('block3', '')}

# Block 4: Market & Strategic Relevance
{blocks.get('block4', '')}

# Block 5: Adaptability & Conclusion
{blocks.get('block5', '')}
"""
        
        # Convert markdown to HTML
        if md_converter:
            html_content = md_converter.convert(combined_blocks)
        else:
            # Simple fallback conversion
            html_content = combined_blocks.replace('\n\n', '</p><p>').replace('\n', '<br>')
            html_content = f'<p>{html_content}</p>'
        
        
        print(f"✅ Letter assembled from {len(blocks)} blocks with dynamic styling")
        return html_content

    
    
    def html_to_pdf(
        self, 
        html_content: str, 
        output_path: str, 
        design: Dict,
        logo_path: Optional[str] = None,
        recommender_info: Optional[Dict] = None
    ):
        """Generate PDF with 100% dynamic styling from heterogeneity design parameters - NO templates"""
        
        # Generate COMPLETE CSS from all 23 design parameters
        dynamic_css = f"""
        @page {{
            size: A4;
            margin: 2cm;
        }}
        
        body {{
            font-family: {design.get('font_primary', 'Georgia, serif')};
            color: {design.get('color_primary_hsl_range', 'hsl(210, 50%, 30%)')};
            line-height: {design.get('line_height', 1.6)};
            font-size: {design.get('font_size_body', '11pt')};
            background: #ffffff;
        }}
        
        .header {{
            text-align: {design.get('header_alignment', 'left')};
            margin-bottom: 25px;
            padding-bottom: 15px;
            border-bottom: 2px solid {design.get('color_accent', '#2E8B57')};
        }}
        
        .logo {{
            max-width: 200px;
            max-height: 100px;
        }}
        
        .recommender-info {{
            font-size: 10pt;
            font-family: {design.get('font_secondary', 'Arial, sans-serif')};
            color: {design.get('color_primary_hsl_range', 'hsl(210, 50%, 30%)')};
        }}
        
        .recommender-name {{
            font-weight: bold;
            font-size: 12pt;
            color: {design.get('color_accent', '#2E8B57')};
        }}
        
        .date {{
            margin-top: 10px;
            font-size: 9pt;
        }}
        
        h1, h2, h3 {{
            font-family: {design.get('font_secondary', 'Arial, sans-serif')};
            color: {design.get('color_accent', '#2E8B57')};
            line-height: 1.3;
        }}
        
        h1 {{ font-size: {design.get('font_size_headers', '14pt,16pt,18pt').split(',')[2]}; }}
        h2 {{ font-size: {design.get('font_size_headers', '14pt,16pt,18pt').split(',')[1]}; }}
        h3 {{ font-size: {design.get('font_size_headers', '14pt,16pt,18pt').split(',')[0]}; }}
        
        p {{
            text-align: justify;
            margin-bottom: {'8px' if design.get('layout_density') == 'compact' else '12px' if design.get('layout_density') == 'balanced' else '16px'};
        }}
        
        strong {{
            color: {design.get('color_accent', '#2E8B57')};
            font-weight: bold;
        }}
        
        em {{
            color: {design.get('color_primary_hsl_range', 'hsl(210, 50%, 30%)')};
            font-style: italic;
        }}
        
        .signature {{
            margin-top: 40px;
        }}
        
        .signature-line {{
            border-top: 1px solid {design.get('color_accent', '#2E8B57')};
            width: 300px;
            margin-top: 50px;
            padding-top: 5px;
        }}
        """
        
        # Build complete HTML document from scratch - NO template files
        full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        {dynamic_css}
    </style>
</head>
<body>
    <div class="header">
        {'<img src="file://' + os.path.abspath(logo_path) + '" class="logo">' if logo_path and os.path.exists(logo_path) else ''}
        <div class="recommender-info">
            <div class="recommender-name">{recommender_info.get('name', '') if recommender_info else ''}</div>
            <div>{recommender_info.get('title', '') if recommender_info else ''}</div>
            <div>{recommender_info.get('company', '') if recommender_info else ''}</div>
            <div class="date">{datetime.now().strftime('%B %d, %Y')}</div>
        </div>
    </div>
    
    {html_content}
    
    <div class="signature">
        <div class="signature-line">
            {recommender_info.get('name', '') if recommender_info else ''}<br>
            {recommender_info.get('title', '') if recommender_info else ''}<br>
            {recommender_info.get('company', '') if recommender_info else ''}
        </div>
    </div>
</body>
</html>"""
        
        # Create output directory if needed
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Convert to PDF
        HTML(string=full_html).write_pdf(output_path)
        
        print(f"✅ PDF generated with dynamic CSS from design parameters: {os.path.basename(output_path)}")

    
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
                
        print(f"✅ Editable DOCX generated with dynamic styling: {os.path.basename(output_path)}")

    def html_to_pdf_direct(self, complete_html: str, output_path: str):
        """
        Convert complete HTML document to PDF (no additional wrapping).
        Used when HTML is already a full document from HTMLDesigner.
        """
        # Create output directory
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Convert to PDF directly
        try:
            HTML(string=complete_html).write_pdf(output_path)
            print(f"✅ PDF generated directly: {os.path.basename(output_path)}")
        except Exception as e:
            print(f"❌ PDF generation failed: {e}")
            raise

    def html_to_docx_direct(self, complete_html: str, output_path: str):
        """
        Convert complete HTML document to DOCX.
        Attempts to preserve the 'document feel' by parsing the HTML structure.
        """
        try:
            from docx import Document
            from docx.shared import Pt, Inches, RGBColor
            from bs4 import BeautifulSoup
            import re

            doc = Document()
            soup = BeautifulSoup(complete_html, 'html.parser')
            
            # Try to extract page margins from CSS if possible, otherwise default
            # (Simplification: just use standard margins)
            for section in doc.sections:
                section.top_margin = Inches(1)
                section.bottom_margin = Inches(1)
                section.left_margin = Inches(1)
                section.right_margin = Inches(1)

            # Extract Body Content
            body = soup.find('body')
            if not body:
                raise ValueError("No body tag found")

            # Simple recursive parser to handle basic formatting
            def process_element(element, paragraph=None):
                if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    p = doc.add_paragraph(style=f'Heading {element.name[1]}')
                    p.add_run(element.get_text().strip())
                elif element.name == 'p':
                    p = doc.add_paragraph()
                    # Process children for bold/italic
                    for child in element.children:
                        if child.name == 'strong' or child.name == 'b':
                            p.add_run(child.get_text()).bold = True
                        elif child.name == 'em' or child.name == 'i':
                            p.add_run(child.get_text()).italic = True
                        elif isinstance(child, str):
                            p.add_run(child)
                elif element.name == 'ul':
                    for li in element.find_all('li', recursive=False):
                        doc.add_paragraph(li.get_text().strip(), style='List Bullet')
                elif element.name == 'ol':
                    for li in element.find_all('li', recursive=False):
                        doc.add_paragraph(li.get_text().strip(), style='List Number')
                elif element.name == 'div':
                    for child in element.children:
                        if child.name: process_element(child)
                # Handle other block elements...

            # Start processing
            for child in body.children:
                if child.name:
                    process_element(child)

            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            doc.save(output_path)
            print(f"✅ DOCX generated directly: {os.path.basename(output_path)}")

        except Exception as e:
            print(f"⚠️ DOCX direct generation failed, using fallback: {e}")
            # Fallback to simple text extraction
            self.html_to_docx(complete_html, output_path, {}, None, None)
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

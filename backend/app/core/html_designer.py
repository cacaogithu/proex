import logging
import base64
import os
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)

class HTMLDesigner:
    """
    AI-powered HTML designer that generates completely unique letter designs.
    Focuses on AUTHENTICITY and HETEROGENEITY - simulating how different humans
    would format documents (Word, Google Docs, LaTeX, etc.).
    """

    def __init__(self, llm_processor):
        self.llm = llm_processor

    def _get_image_base64(self, image_path: str) -> Optional[str]:
        """Convert image to base64 string for embedding"""
        if not image_path or not os.path.exists(image_path):
            return None
            
        try:
            with open(image_path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to encode image {image_path}: {e}")
            return None

    def generate_html_design(
        self,
        blocks: Dict[str, str],
        design: Dict,
        recommender_info: Dict,
        logo_path: Optional[str] = None
    ) -> str:
        """
        Generate a complete, unique HTML document based on design parameters.
        """
        
        # Prepare content
        combined_content = ""
        block_mapping = {
            'block1': 'Leadership & Credibility',
            'block2': 'Technical Innovation',
            'block3': 'Empirical Validation',
            'block4': 'Market & Strategic Relevance',
            'block5': 'Adaptability & Conclusion'
        }
        
        for key, title in block_mapping.items():
            if blocks.get(key):
                combined_content += f"\n\n=== SECTION: {title} ===\n{blocks.get(key)}"

        # Prepare logo
        logo_base64 = self._get_image_base64(logo_path)
        logo_html = ""
        if logo_base64:
            logo_html = f'<img src="data:image/png;base64,{logo_base64}" alt="Company Logo" class="logo" />'

        # Extract key design parameters for the prompt
        style_params = {
            "layout_pattern": design.get('layout_pattern', 'standard'),
            "font_primary": design.get('font_primary', 'Times New Roman'),
            "font_secondary": design.get('font_secondary', 'Arial'),
            "color_primary": design.get('color_primary_hsl_range', '#000000'),
            "color_accent": design.get('color_accent', '#333333'),
            "density": design.get('layout_density', 'medium'),
            "whitespace": design.get('whitespace_profile', 'balanced'),
            "emphasis": design.get('emphasis_pattern', 'bold'),
            "structure": design.get('structure_features', 'standard'),
            "tone": design.get('tone_variable', 'professional')
        }

        prompt = f"""# ROLE
You are a Document Formatting Expert. Your job is to simulate a specific document style based on the personality and preferences of the writer.
You are NOT a web designer. You are creating a document that looks like it was written in Microsoft Word, Google Docs, or LaTeX, then saved as PDF.

# OBJECTIVE
Create a COMPLETE, VALID HTML document (starting with <!DOCTYPE html>) for a Letter of Recommendation.
The goal is HETEROGENEITY. This document must look UNIQUE and AUTHENTIC to the specific persona described below.

# DESIGN PARAMETERS (The "Persona")
- **Layout Style:** {style_params['layout_pattern']} (e.g., Academic, Corporate, Modern, Plain, Technical)
- **Primary Font:** {style_params['font_primary']}
- **Secondary Font:** {style_params['font_secondary']} (for headers/accents)
- **Primary Color:** {style_params['color_primary']}
- **Accent Color:** {style_params['color_accent']}
- **Density:** {style_params['density']}
- **Tone:** {style_params['tone']}

# INSTRUCTIONS

1. **Authentic Formatting:**
   - If style is **Academic**: Use serif fonts, justified text, formal headers, maybe a reference section.
   - If style is **Corporate**: Use clean sans-serifs, a header bar (maybe), bold section titles.
   - If style is **Technical**: Use numbered sections (1.0, 1.1), data tables, bullet points, maybe a "monospaced" code block style for metrics.
   - If style is **Plain/Personal**: Use minimal styling, standard margins, no fancy headers, looks like a standard letter.
   - If style is **Executive**: Use a sidebar or a very strong header, lots of whitespace, very polished.

2. **Content Handling:**
   - You have 5 sections of content. You MUST include ALL of them.
   - **DO NOT SUMMARIZE.** Keep the text exactly as provided, just format it.
   - You CAN add visual elements like:
     - A simple data table for metrics found in the text.
     - A "Key Achievements" box (simple border).
     - A horizontal line separator.
     - **DO NOT** use gradients, shadows, or "web" effects unless the style is specifically "Modern Startup". Keep it printable.

3. **Logo Placement:**
   - I have provided a placeholder `{logo_html}`.
   - Place this logo where it makes sense for the style (e.g., Top Left for Corporate, Centered for Formal, Omitted for Personal - if omitted, comment it out).

4. **Structure:**
   - Include a proper Header (Sender Info, Date).
   - Include a proper Salutation.
   - Include the Body (The 5 sections).
   - Include a proper Sign-off.

# INPUT CONTENT
Recommender: {recommender_info.get('name')} ({recommender_info.get('title')}, {recommender_info.get('company')})
Location: {recommender_info.get('location')}
Date: [Current Date]

{combined_content}

# OUTPUT FORMAT
- Return ONLY the raw HTML code.
- Start with `<!DOCTYPE html>`.
- Include `<style>` block in `<head>`.
- Use `@page` CSS for proper print margins (e.g., `size: A4; margin: 2.5cm;`).
- Ensure text is readable (black/dark gray on white).

GO! Create a document that looks like it was written by this specific person with this specific style.
"""

        try:
            response = self.llm.client.chat.completions.create(
                model=self.llm.models["quality"],
                messages=[{"role": "user", "content": prompt}],
                temperature=0.85, # High creativity for variance
                max_tokens=4000
            )
            
            html_content = response.choices[0].message.content.strip()
            
            # Clean markdown fences if present
            if html_content.startswith('```html'):
                html_content = html_content.split('```html')[1]
            if html_content.startswith('```'):
                html_content = html_content.split('```')[1]
            if html_content.endswith('```'):
                html_content = html_content.rsplit('```', 1)[0]
                
            return html_content.strip()

        except Exception as e:
            logger.error(f"Error generating HTML design: {e}")
            # Fallback to a simple HTML structure if AI fails
            return self._generate_fallback_html(blocks, recommender_info)

    def _generate_fallback_html(self, blocks, recommender_info):
        """Simple fallback if AI generation fails"""
        content = ""
        for block in blocks.values():
            content += f"<p>{block}</p>"
            
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: sans-serif; line-height: 1.6; padding: 40px; }}
                .header {{ margin-bottom: 30px; border-bottom: 1px solid #ccc; padding-bottom: 10px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <strong>{recommender_info.get('name')}</strong><br>
                {recommender_info.get('title')}<br>
                {recommender_info.get('company')}
            </div>
            {content}
        </body>
        </html>
        """

"""
HTML Designer Agent - AI-powered custom HTML/CSS design generator
Replaces template system with dynamic, truly heterogeneous HTML generation
"""
from typing import Dict, Optional
import logging
import base64
import os

logger = logging.getLogger(__name__)


class HTMLDesigner:
    """
    AI-powered HTML designer that generates completely unique letter designs.
    No templates - pure generative design based on 23-parameter design structures.
    """

    def __init__(self, llm_processor):
        self.llm = llm_processor
        logger.info("HTMLDesigner initialized - generative mode")

    def _embed_logo_as_base64(self, logo_path: str) -> Optional[str]:
        """Convert logo to base64 data URI for embedding"""
        if not logo_path or not os.path.exists(logo_path):
            return None

        try:
            with open(logo_path, 'rb') as f:
                logo_data = f.read()

            ext = os.path.splitext(logo_path)[1].lower()
            mime_types = {
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.gif': 'image/gif',
                '.svg': 'image/svg+xml',
                '.webp': 'image/webp'
            }
            mime = mime_types.get(ext, 'image/png')

            b64_data = base64.b64encode(logo_data).decode('utf-8')
            data_uri = f'data:{mime};base64,{b64_data}'

            logger.info(f"Logo embedded as base64 ({len(b64_data)} chars)")
            return data_uri

        except Exception as e:
            logger.error(f"Failed to embed logo: {e}")
            return None

    def generate_html_design(
        self,
        blocks: Dict[str, str],
        design: Dict,
        recommender_info: Dict,
        logo_path: Optional[str] = None
    ) -> str:
        """
        Generate a completely unique HTML document with custom CSS design.

        This is the core AI designer - it interprets the 23 design parameters
        and creates a bespoke visual design for each letter.

        Args:
            blocks: Dict with keys 'block3', 'block4', 'block5', 'block6', 'block7'
            design: 23-parameter design structure from HeterogeneityArchitect
            recommender_info: Dict with 'name', 'title', 'company', 'location'
            logo_path: Optional path to company logo

        Returns:
            Complete HTML document string (DOCTYPE to </html>)
        """

        # Embed logo if available
        logo_base64 = self._embed_logo_as_base64(logo_path) if logo_path else None

        # Prepare content blocks
        combined_content = f"""
## Block 3 (Introduction & Context)
{blocks.get('block3', '')}

## Block 4 (Technical Details & Achievements)
{blocks.get('block4', '')}

## Block 5 (Impact & Results)
{blocks.get('block5', '')}

## Block 6 (Validation & Evidence)
{blocks.get('block6', '')}

## Block 7 (Conclusion & Recommendation)
{blocks.get('block7', '')}
"""

        # Build the design generation prompt
        prompt = self._build_design_prompt(
            content=combined_content,
            design=design,
            recommender_info=recommender_info,
            logo_base64=logo_base64
        )

        # Generate HTML design using LLM
        try:
            response = self.llm._call_llm(
                model=self.llm.models["quality"],
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                max_tokens=16000
            )

            html_output = response.choices[0].message.content.strip()

            # Clean up if LLM wrapped in markdown code blocks
            if html_output.startswith('```html'):
                html_output = html_output.replace('```html', '', 1)
            if html_output.startswith('```'):
                html_output = html_output.replace('```', '', 1)
            if html_output.endswith('```'):
                html_output = html_output.rsplit('```', 1)[0]

            html_output = html_output.strip()

            # Validate output starts with DOCTYPE
            if not html_output.startswith('<!DOCTYPE'):
                logger.warning("Generated HTML missing DOCTYPE, adding it")
                html_output = '<!DOCTYPE html>\n' + html_output

            logger.info(f"HTML design generated: {len(html_output)} chars")
            return html_output

        except Exception as e:
            logger.error(f"HTML generation failed: {e}")
            raise ValueError(f"Failed to generate HTML design: {e}")

    def _build_design_prompt(
        self,
        content: str,
        design: Dict,
        recommender_info: Dict,
        logo_base64: Optional[str]
    ) -> str:
        """Build the complete prompt for HTML design generation"""

        # Extract design parameters
        template_id = design.get('template_id', 'T1')
        tone_variable = design.get('tone_variable', 'professional')
        tone_instructions = design.get('tone_instructions', '')
        narrative_framework = design.get('narrative_framework', 'chronological')
        layout_pattern = design.get('layout_pattern', 'formal-traditional')
        font_primary = design.get('font_primary', 'Georgia, serif')
        font_secondary = design.get('font_secondary', 'Arial, sans-serif')
        color_primary = design.get('color_primary_hsl_range', 'hsl(210, 50%, 30%)')
        color_accent = design.get('color_accent', '#DAA520')
        layout_density = design.get('layout_density', 'balanced')
        line_height = design.get('line_height', 1.7)
        header_alignment = design.get('header_alignment', 'left')
        footer_style = design.get('footer_style', 'formal with contact')
        contrast_mode = design.get('contrast_mode', 'medium')
        whitespace_profile = design.get('whitespace_profile', 'generous')
        font_size_body = design.get('font_size_body', '11pt')
        font_size_headers = design.get('font_size_headers', '14pt,16pt,18pt')
        paragraph_density = design.get('paragraph_density_rule', 'balanced')
        emphasis_pattern = design.get('emphasis_pattern', 'bold for key terms')
        semantic_elements = design.get('semantic_elements', ['bullet points', 'bold headers'])
        readability_target = design.get('readability_target', 'Executive')
        bonus_trait = design.get('bonus_trait', 'unique professional voice')

        recommender_name = recommender_info.get('name', 'Professional Recommender')
        recommender_title = recommender_info.get('title', '')
        recommender_company = recommender_info.get('company', '')
        recommender_location = recommender_info.get('location', '')

        logo_instruction = ""
        if logo_base64:
            logo_instruction = f"""
## LOGO INTEGRATION
You have a company logo to include. Use this base64 data URI:
```
{logo_base64[:200]}... (truncated for brevity)
```

Place the logo strategically in the header. Example:
```html
<img src="{logo_base64}" class="logo" alt="Company Logo">
```
"""

        prompt = f"""# ROLE
You are the world's best HTML Document Designer for professional letters of recommendation.

Your job is to **DESIGN** - not assemble from templates, but CREATE a completely unique HTML document with custom CSS that brings this letter to life visually.

# CRITICAL INSTRUCTIONS

🚨 **OUTPUT ONLY THE RAW HTML CODE**
- Start with `<!DOCTYPE html>`
- Include complete `<html>`, `<head>`, `<style>`, and `<body>` tags
- DO NOT wrap in JSON, do NOT escape newlines, do NOT add markdown code fences
- Just pure, clean, valid HTML ready for PDF conversion

🎨 **DESIGN PARAMETERS TO IMPLEMENT**
You have been given a 23-parameter design structure. Your job is to INTERPRET these creatively:

**Visual Design:**
- Template Style: {template_id}
- Layout Pattern: {layout_pattern}
- Font Primary: {font_primary}
- Font Secondary: {font_secondary}
- Color Primary: {color_primary}
- Color Accent: {color_accent}
- Layout Density: {layout_density}
- Line Height: {line_height}
- Header Alignment: {header_alignment}
- Footer Style: {footer_style}
- Contrast Mode: {contrast_mode}
- Whitespace: {whitespace_profile}
- Body Font Size: {font_size_body}
- Header Font Sizes: {font_size_headers}

**Content Structure:**
- Tone: {tone_variable}
- Tone Instructions: {tone_instructions}
- Narrative Framework: {narrative_framework}
- Paragraph Density: {paragraph_density}
- Emphasis Pattern: {emphasis_pattern}
- Semantic Elements: {', '.join(semantic_elements)}
- Readability Target: {readability_target}
- Bonus Trait: {bonus_trait}

{logo_instruction}

## RECOMMENDER INFORMATION
- Name: {recommender_name}
- Title: {recommender_title}
- Company: {recommender_company}
- Location: {recommender_location}

# CONTENT TO FORMAT

{content}

# DESIGN REQUIREMENTS

1. **Be Creative with Layout**
   - Interpret {layout_pattern} to create visual interest
   - Use colored sections, borders, subtle backgrounds
   - Consider sidebars, highlight boxes, pull quotes
   - Add visual hierarchy with spacing and typography

2. **Typography Excellence**
   - Use {font_primary} for body and {font_secondary} for accents
   - Implement the header sizes: {font_size_headers}
   - Body text at {font_size_body}
   - Create clear hierarchy (h1, h2, h3 styles)

3. **Color & Visual Appeal**
   - Primary color: {color_primary} (use for headers, borders, accents)
   - Accent color: {color_accent} (use sparingly for highlights)
   - Implement {contrast_mode} contrast
   - Consider subtle gradients or background tints

4. **Printability**
   - This MUST print beautifully on 8.5" × 11" paper
   - Use @page CSS for proper margins
   - Ensure content flows across pages if needed
   - No elements that break printing

5. **Semantic Structure**
   - Use requested elements: {', '.join(semantic_elements)}
   - Format metrics/data prominently
   - Create visual breaks between sections
   - Add a professional header with logo (if provided)
   - Add a signature block at the end

6. **Unique Visual Elements**
   - Consider adding: timeline elements, metric callout boxes, testimonial-style quotes
   - Use borders, box-shadows, or subtle backgrounds strategically
   - Make it look like a DESIGNED document, not just text

7. **NO ERRORS**
   - All content must be preserved (don't summarize!)
   - Valid HTML5
   - Clean, organized CSS
   - Professional polish

# FORMATTING STYLE GUIDE

Follow the tone: **{tone_variable}**
{tone_instructions}

Structure paragraphs according to: {paragraph_density}
Use emphasis pattern: {emphasis_pattern}

# STRUCTURE TEMPLATE

Your HTML should include:
1. DOCTYPE and full html structure
2. <head> with meta charset, title, and comprehensive <style> block
3. <body> with:
   - Header section (logo if available, recommender info, date)
   - Greeting ("To Whom It May Concern:" or appropriate)
   - Content sections with ALL blocks formatted beautifully
   - Signature block with recommender details
4. Proper closing tags

# CRITICAL REMINDERS

- Output ONLY HTML (no explanations, no markdown wrappers)
- Start with `<!DOCTYPE html>`
- Include ALL content from the blocks
- Make it UNIQUE - this is a custom design
- It must be PRINTABLE and beautiful on paper
- Use the design parameters to create visual differentiation

Generate the complete HTML document now:"""

        return prompt

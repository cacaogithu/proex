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
            response = self.llm.client.chat.completions.create(
                model=self.llm.models["quality"],  # Use best model for design
                messages=[{"role": "user", "content": prompt}],
                temperature=1.0,  # MAXIMUM creativity - we want unique designs!
                max_tokens=16000,
                top_p=0.95  # Allow diverse token selection
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

        prompt = f"""# YOU ARE A WORLD-CLASS HTML/CSS DESIGNER - NOT A TEMPLATE USER

Your mission: Generate a COMPLETELY UNIQUE, VISUALLY STRIKING HTML document for this letter.

## 🚨 NON-NEGOTIABLE RULES

1. **OUTPUT RAW HTML ONLY** - Start with `<!DOCTYPE html>`, end with `</html>`. NO markdown wrappers, NO explanations.
2. **ZERO BLAND DESIGNS** - If this looks like a default Word doc, you FAILED.
3. **PRESERVE ALL CONTENT** - Don't summarize. Include every word from the blocks.

---

## 🎨 YOUR DESIGN MANDATE (23 Parameters)

**Typography:**
- Primary Font: **{font_primary}** (body text)
- Secondary Font: **{font_secondary}** (headers, accents)
- Body Size: **{font_size_body}**
- Header Sizes: **{font_size_headers}**
- Line Height: **{line_height}**

**Color Palette:**
- Primary: **{color_primary}** ← Use this for headers, borders, section backgrounds
- Accent: **{color_accent}** ← Use this for highlights, important metrics, call-outs
- Contrast: **{contrast_mode}** mode

**Layout:**
- Pattern: **{layout_pattern}**
- Density: **{layout_density}**
- Whitespace: **{whitespace_profile}**
- Header Position: **{header_alignment}**

**Content Style:**
- Tone: **{tone_variable}**
- Framework: **{narrative_framework}**
- Elements: **{', '.join(semantic_elements)}**
- Bonus Trait: **{bonus_trait}**

---

## 🔥 MANDATORY CREATIVE ELEMENTS (Pick 4-6)

YOU MUST INCLUDE at least 4 of these visual elements:

1. **Colored Header Bar** - Full-width banner with {color_primary} gradient
2. **Metric Highlight Boxes** - Float key numbers/achievements in colored boxes with shadows
3. **Section Dividers** - Creative borders using {color_accent} (not just lines - try dots, dashes, gradients)
4. **Pull Quote** - Extract a powerful statement, style it with large font + {color_accent} left border
5. **Timeline Visualization** - If chronological content exists, show it with dots/lines
6. **Icon-Style Bullets** - Use Unicode symbols (→, ●, ✓, ◆) styled with {color_accent}
7. **Two-Tone Sections** - Alternate between white and light {color_primary} backgrounds
8. **Sidebar Elements** - Float a box with key info (dates, metrics) to the right
9. **Colored Text Blocks** - Wrap important paragraphs in subtle {color_primary} background (10-15% opacity)
10. **Custom Header Styling** - Make the recommender's name STAND OUT (size, color, weight)

---

## 📐 LAYOUT INTERPRETATION GUIDE

Based on `{layout_pattern}`:

- **formal-traditional** → Classic serif fonts, centered headers, border-based sections, conservative colors
- **modern-clean** → Sans-serif, asymmetric header, lots of whitespace, bold accent colors, minimalist dividers
- **executive-bold** → Large headers, strong colors, metric callouts, confidence-focused design
- **academic-detailed** → Dense text, numbered sections, table of contents feel, footnote style
- **narrative-flowing** → Story-like flow, pull quotes, conversational spacing, human touch

INTERPRET THIS CREATIVELY. Don't just change fonts - REDESIGN THE ENTIRE VISUAL STRUCTURE.

---

## 🎯 CONCRETE CSS EXAMPLES (Use These as Inspiration)

```css
/* Colored section with shadow */
.highlight-section {{
    background: linear-gradient(135deg, {color_primary} 0%, {color_primary.replace('30%', '40%') if 'hsl' in color_primary else color_primary} 100%);
    color: white;
    padding: 25px;
    border-radius: 8px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    margin: 30px 0;
}}

/* Metric callout box */
.metric-box {{
    display: inline-block;
    background: {color_accent};
    color: white;
    padding: 15px 25px;
    border-radius: 50px;
    font-weight: bold;
    font-size: 14pt;
    margin: 10px 5px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}}

/* Creative section divider */
.section-divider {{
    height: 3px;
    background: linear-gradient(to right, transparent, {color_accent}, transparent);
    margin: 40px 0;
}}

/* Pull quote styling */
.pull-quote {{
    font-size: 14pt;
    font-style: italic;
    color: {color_primary};
    border-left: 5px solid {color_accent};
    padding-left: 20px;
    margin: 30px 0 30px 40px;
    background: rgba(0,0,0,0.02);
    padding: 20px;
}}
```

**YOU MUST CREATE YOUR OWN VERSIONS** - Don't copy these exactly, but use this level of creativity.

---

## 📄 CONTENT & STRUCTURE

{logo_instruction}

**Recommender:** {recommender_name}
**Title:** {recommender_title}
**Company:** {recommender_company}
**Location:** {recommender_location}

**Letter Content (Format this with your creative design):**
{content}

---

## ✅ FINAL CHECKLIST

Before you output, verify:
- [ ] Used {color_primary} and {color_accent} in AT LEAST 5 places
- [ ] Included AT LEAST 4 creative visual elements from the list above
- [ ] Typography uses both {font_primary} AND {font_secondary}
- [ ] Has visual variety (not just paragraphs of text)
- [ ] Prints well on 8.5" × 11" paper (@page CSS included)
- [ ] Logo embedded (if provided)
- [ ] ALL content from blocks is preserved
- [ ] Starts with `<!DOCTYPE html>` and ends with `</html>`
- [ ] NO markdown code fences

---

## 🚀 OUTPUT YOUR COMPLETE HTML NOW

Remember: This should look DESIGNED, not typed. Make it VISUALLY UNIQUE."""

        return prompt

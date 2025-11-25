"""
HeterogeneityArchitect - LLM-powered design diversity generator
Uses the original n8n prompt to generate truly heterogeneous design structures
"""
from typing import Dict, List
import json
import time


class StyleBlueprintGenerator:
    """LLM-powered heterogeneity generator using original n8n prompt"""
    
    def __init__(self, llm_processor):
        self.llm = llm_processor
    
    def _format_testimonies_for_prompt(self, testimonies: List[Dict]) -> str:
        """Format testimonies for the heterogeneity prompt"""
        formatted = []
        for i, t in enumerate(testimonies):
            formatted.append(f"""#### Testimony {i+1}
- testimony_id: {t.get('testimony_id', f'T{i+1}')}
- recommender_name: {t.get('recommender_name', 'N/A')}
- recommender_company: {t.get('recommender_company', 'N/A')}
- recommender_role: {t.get('recommender_role', 'N/A')}
- collaboration_period: {t.get('collaboration_period', 'N/A')}
- applicant_role: {t.get('applicant_role', 'N/A')}
- testimony_text: {t.get('testimony_text', 'N/A')[:500]}...
- key_achievements: {t.get('key_achievements', 'N/A')}
""")
        return "\n".join(formatted)
    
    def generate_design_structures(self, organized_data: Dict) -> Dict:
        """Generate heterogeneous design structures using LLM with original n8n prompt"""
        testimonies = organized_data.get('testimonies', [])
        num_testimonies = len(testimonies)
        
        if num_testimonies == 0:
            raise ValueError("No testimonies found")
        
        petitioner = organized_data.get('petitioner') or {}
        strategy = organized_data.get('strategy') or {}
        onet = organized_data.get('onet') or {}
        
        prompt = f"""# ROLE  
You are `Heterogeneity_Architect`, the design-diversity intelligence layer for PROEX.  
Your task is to analyze all contextual data (strategy, petitioner profile, O*NET descriptors, testimonies) and produce **{num_testimonies} radically distinct design blueprints (T1-T{num_testimonies})**.  
Each blueprint will guide one downstream generator to ensure **maximum heterogeneity** in writing style, formatting, structure, and readability — making it look like **{num_testimonies} different human professionals** wrote these letters, not a template system.

**CRITICAL**: The design structures MUST be generated in the EXACT same order as the testimonies (T1 for Testimony 1, T2 for Testimony 2, etc.). Do NOT reorder or shuffle them.

---

# CONTEXT INPUTS  

### 📘 OneNet Recommendations  
Representative Tasks: {json.dumps((onet or {}).get('representative_tasks', []), ensure_ascii=False)}
Tools and Technologies: {json.dumps((onet or {}).get('tools_and_technologies', []), ensure_ascii=False)}
Work Activities and Skills: {json.dumps((onet or {}).get('work_activities_and_skills', []), ensure_ascii=False)}

### 🧭 Strategy (Applicant's Endeavor)  
Services Offered: {json.dumps((strategy or {}).get('services_offered', []), ensure_ascii=False)}
Target Clients: {json.dumps((strategy or {}).get('target_clients', []), ensure_ascii=False)}

### 👤 Petitioner CV  
Name: {(petitioner or {}).get('name', 'Unknown')}
Education: {json.dumps((petitioner or {}).get('education', []), ensure_ascii=False)}
Experience: {json.dumps((petitioner or {}).get('experience', []), ensure_ascii=False)}

### 🧩 Testimonies Snapshot  
{self._format_testimonies_for_prompt(testimonies)}

---

# INTELLIGENT DESIGN LOGIC

Your goal is to create **{num_testimonies} distinct author personas** that feel like real human professionals with different writing styles, formatting preferences, and communication approaches.

### Step 1: Analyze Each Recommender's Profile

For each testimony, consider:
- **Recommender's role and seniority**: Senior executives write differently than mid-level managers
- **Industry and company culture**: Tech startups vs. traditional manufacturing vs. academia
- **Collaboration context**: Direct supervisor vs. client vs. peer vs. mentor
- **Key achievements mentioned**: Technical depth vs. leadership vs. innovation vs. results

### Step 2: Assign Distinct Author Personas

Create {num_testimonies} different "author personalities" based on the recommenders. Think about how each person would naturally write:

**Persona Type Examples** (choose what fits each recommender, don't use these labels in output):
- **The Executive**: Concise, metric-driven, bullet points, emphasis on ROI and strategic impact
- **The Technical Expert**: Detailed, analytical, uses specific terminology, longer explanations
- **The Mentor**: Warm, narrative-driven, tells stories, emphasizes growth and potential
- **The Data Analyst**: Structured, uses tables/charts, comparative analysis, evidence-based
- **The Academic**: Formal, theoretical frameworks, comprehensive, well-referenced

### Step 3: Ensure Maximum Differentiation

Make sure the {num_testimonies} personas differ in:
- **Sentence structure**: Some use short punchy sentences, others use longer analytical ones
- **Paragraph length**: Vary from 3-4 sentences to 5-6 sentences
- **Formatting preferences**: Some love bold metrics, others prefer italics for emphasis, others use minimal formatting
- **Visual elements**: Some use lists, others use tables, others use pull quotes
- **Tone**: Formal vs. conversational, technical vs. accessible, warm vs. professional

**CRITICAL**: Do NOT use color schemes, fonts, or HTML/CSS parameters. Focus on **writing style, tone, structure, and Markdown formatting** that humans would naturally use.

---

# GENERATION PARAMETERS

For each of the {num_testimonies} design structures (T1–T{num_testimonies}), generate an object with these fields:

**REQUIRED FIELDS**:

{{
  "template_id": "T1" | "T2" | "T3" | "T4" | "T5",
  "assigned_recommender": "[Full name from testimony]",
  "tone_instructions": "Describe how this person writes. Examples:
    - 'Senior executive style: concise sentences (12-15 words), metric-first paragraphs, uses bold for all numbers, minimal adjectives, direct and authoritative tone'
    - 'Technical expert style: detailed explanations (20-25 words per sentence), uses technical terminology naturally, prefers italics for key concepts, analytical and precise tone'
    - 'Mentor style: warm and narrative (15-20 words per sentence), tells stories chronologically, uses quotes and anecdotes, encouraging and personal tone'
    - 'Data analyst style: structured and comparative (15-18 words per sentence), uses tables and lists frequently, evidence-based arguments, objective and measured tone'
    - 'Academic style: formal and comprehensive (18-22 words per sentence), uses frameworks and references, minimal formatting, scholarly and thorough tone'",
  
  "narrative_framework": "How this person structures their argument. Examples:
    - 'Metric-first: Start each section with the result/number, then explain the context and method'
    - 'Chronological story: Begin with how we met, progress through collaboration, end with future potential'
    - 'Problem-solution-impact: Present the challenge, describe the approach, quantify the outcome'
    - 'Thematic: Organize by competency areas (leadership, technical skills, innovation) rather than timeline'
    - 'Comparative analysis: Benchmark against industry standards, show how applicant exceeds norms'",
  
  "paragraph_structure": "How this person formats paragraphs. Examples:
    - '3-4 short sentences per paragraph, double line breaks, each paragraph covers one idea'
    - '5-6 medium sentences per paragraph, single line breaks, paragraphs flow into each other'
    - 'Mix of short (2-3 sentences) and long (5-6 sentences) paragraphs for rhythm variation'
    - 'Very structured: topic sentence + 3 supporting sentences + concluding sentence'",
  
  "sentence_style": "How this person constructs sentences. Examples:
    - 'Short and punchy: 10-15 words, active voice, one idea per sentence'
    - 'Medium analytical: 15-20 words, mix of simple and complex structures'
    - 'Long and comprehensive: 20-25 words, uses clauses and qualifiers'
    - 'Varied rhythm: alternates between short (10-12) and long (20-25) sentences'",
  
  "emphasis_style": "How this person emphasizes key information. Examples:
    - 'Bold all metrics and numbers (e.g., **US$ 7B**, **300+ dashboards**)'
    - 'Italicize technical terms and key concepts (e.g., *Business Intelligence*, *strategic leadership*)'
    - 'Use ALL CAPS for critical achievements (e.g., INCREASED SALES BY 100%)'
    - 'Minimal formatting: let the content speak for itself, only bold section headers'
    - 'Mixed: bold for metrics, italics for skills, quotes for testimonials'",
  
  "visual_elements": "What visual elements this person prefers. Examples:
    - 'Frequent bulleted lists for achievements and responsibilities'
    - 'Numbered lists for sequential processes or ranked items'
    - 'Tables for comparing before/after or multiple projects'
    - 'Pull quotes (blockquotes) for highlighting key statements'
    - 'Minimal: pure paragraph text with occasional subheadings'
    - 'Sidebar boxes with summary statistics or key facts'",
  
  "readability_target": "How complex this person's writing is:
    - 'Executive brief: 10th-11th grade, accessible and scannable'
    - 'Professional standard: 11th-12th grade, balanced complexity'
    - 'Technical depth: College level, assumes domain knowledge'
    - 'Academic formal: Graduate level, comprehensive and precise'",
  
  "word_count_target": "Total length for this letter:
    - Range: 1800-2500 words (full 5-block letter)
    - Distribute across blocks based on narrative framework",
  
  "unique_trait": "One distinctive feature that makes this letter stand out. Examples:
    - 'Opens each major section with a relevant industry statistic or benchmark'
    - 'Includes a timeline graphic showing collaboration milestones'
    - 'Uses a recurring metaphor (e.g., building, navigation, transformation)'
    - 'Ends each section with a forward-looking statement about future impact'
    - 'Incorporates brief case study boxes within the narrative'
    - 'Uses a Q&A format for one section to add variety'"
}}

**ORDERING REQUIREMENT**:
- T1 MUST correspond to Testimony 1 (testimonies[0])
- T2 MUST correspond to Testimony 2 (testimonies[1])
- And so on...

Do NOT shuffle or reorder. The downstream nodes expect this exact sequence.

---

# OUTPUT FORMAT

Return ONLY valid JSON with this structure:

{{
  "petitioner_name": "{petitioner.get('name', 'Unknown')}",
  "design_structures": [
    {{
      "template_id": "T1",
      "assigned_recommender": "[Testimony 1 recommender name]",
      "tone_instructions": "[Detailed description of writing style]",
      "narrative_framework": "[How to structure the argument]",
      "paragraph_structure": "[How to format paragraphs]",
      "sentence_style": "[How to construct sentences]",
      "emphasis_style": "[How to emphasize key info]",
      "visual_elements": "[What visual elements to use]",
      "readability_target": "[Complexity level]",
      "word_count_target": "[Length range]",
      "unique_trait": "[One distinctive feature]"
    }},
    ... (repeat for T2, T3, etc. based on number of testimonies)
  ]
}}

**VALIDATION CHECKLIST**:
- ✅ Exactly {num_testimonies} design structures (T1-T{num_testimonies})
- ✅ Each has a unique tone_instructions (no duplicates)
- ✅ Each has a different narrative_framework
- ✅ Each has different emphasis_style and visual_elements
- ✅ Order matches testimonies exactly (T1=testimonies[0], T2=testimonies[1], etc.)
- ✅ No mention of colors, fonts, or HTML/CSS
- ✅ Focus on human writing style and Markdown formatting

Do NOT include code fences, markdown formatting, or explanations. Return ONLY the JSON object."""

        # Call LLM to generate design structures
        print(f"🎨 Generating {num_testimonies} heterogeneous design structures via LLM...")
        
        result_text = ""
        try:
            response = self.llm.client.chat.completions.create(
                model=self.llm.models["quality"],
                messages=[{"role": "user", "content": prompt}],
                temperature=0.9,
                max_tokens=4000
            )
            
            result_text = response.choices[0].message.content
            
            # Clean up any markdown code fences
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0]
            
            result = json.loads(result_text.strip())
            
            # Validate the result
            design_structures = result.get('design_structures', [])
            if len(design_structures) != num_testimonies:
                print(f"⚠️ Warning: Expected {num_testimonies} designs, got {len(design_structures)}")
            
            # Add index to each design for downstream processing
            for i, design in enumerate(design_structures):
                design['index'] = i
            
            print(f"✅ Generated {len(design_structures)} unique design structures")
            for i, ds in enumerate(design_structures):
                print(f"   T{i+1}: {ds.get('assigned_recommender', 'Unknown')} - {ds.get('tone_instructions', '')[:60]}...")
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {e}")
            print(f"   Raw response: {result_text[:500]}...")
            # Return fallback design structures
            return self._generate_fallback_designs(testimonies, petitioner.get('name', 'Unknown'))
        except Exception as e:
            print(f"❌ LLM error: {e}")
            return self._generate_fallback_designs(testimonies, petitioner.get('name', 'Unknown'))
    
    def _generate_fallback_designs(self, testimonies: List[Dict], petitioner_name: str) -> Dict:
        """Generate fallback designs if LLM fails"""
        print("⚠️ Using fallback design generation...")
        
        personas = [
            {
                "tone_instructions": "Senior executive style: concise sentences (12-15 words), metric-first paragraphs, uses bold for all numbers, minimal adjectives, direct and authoritative tone",
                "narrative_framework": "Metric-first: Start each section with the result/number, then explain the context and method",
                "paragraph_structure": "3-4 short sentences per paragraph, double line breaks, each paragraph covers one idea",
                "sentence_style": "Short and punchy: 10-15 words, active voice, one idea per sentence",
                "emphasis_style": "Bold all metrics and numbers",
                "visual_elements": "Frequent bulleted lists for achievements and responsibilities",
                "readability_target": "Executive brief: 10th-11th grade, accessible and scannable",
                "unique_trait": "Opens each major section with a relevant industry statistic or benchmark"
            },
            {
                "tone_instructions": "Technical expert style: detailed explanations (20-25 words per sentence), uses technical terminology naturally, prefers italics for key concepts, analytical and precise tone",
                "narrative_framework": "Problem-solution-impact: Present the challenge, describe the approach, quantify the outcome",
                "paragraph_structure": "5-6 medium sentences per paragraph, single line breaks, paragraphs flow into each other",
                "sentence_style": "Long and comprehensive: 20-25 words, uses clauses and qualifiers",
                "emphasis_style": "Italicize technical terms and key concepts",
                "visual_elements": "Tables for comparing before/after or multiple projects",
                "readability_target": "Technical depth: College level, assumes domain knowledge",
                "unique_trait": "Incorporates brief case study boxes within the narrative"
            },
            {
                "tone_instructions": "Mentor style: warm and narrative (15-20 words per sentence), tells stories chronologically, uses quotes and anecdotes, encouraging and personal tone",
                "narrative_framework": "Chronological story: Begin with how we met, progress through collaboration, end with future potential",
                "paragraph_structure": "Mix of short (2-3 sentences) and long (5-6 sentences) paragraphs for rhythm variation",
                "sentence_style": "Medium analytical: 15-20 words, mix of simple and complex structures",
                "emphasis_style": "Mixed: bold for metrics, italics for skills, quotes for testimonials",
                "visual_elements": "Pull quotes (blockquotes) for highlighting key statements",
                "readability_target": "Professional standard: 11th-12th grade, balanced complexity",
                "unique_trait": "Uses a recurring metaphor (e.g., building, navigation, transformation)"
            },
            {
                "tone_instructions": "Data analyst style: structured and comparative (15-18 words per sentence), uses tables and lists frequently, evidence-based arguments, objective and measured tone",
                "narrative_framework": "Comparative analysis: Benchmark against industry standards, show how applicant exceeds norms",
                "paragraph_structure": "Very structured: topic sentence + 3 supporting sentences + concluding sentence",
                "sentence_style": "Varied rhythm: alternates between short (10-12) and long (20-25) sentences",
                "emphasis_style": "Minimal formatting: let the content speak for itself, only bold section headers",
                "visual_elements": "Numbered lists for sequential processes or ranked items",
                "readability_target": "Professional standard: 11th-12th grade, balanced complexity",
                "unique_trait": "Ends each section with a forward-looking statement about future impact"
            },
            {
                "tone_instructions": "Academic style: formal and comprehensive (18-22 words per sentence), uses frameworks and references, minimal formatting, scholarly and thorough tone",
                "narrative_framework": "Thematic: Organize by competency areas (leadership, technical skills, innovation) rather than timeline",
                "paragraph_structure": "5-6 medium sentences per paragraph, single line breaks, paragraphs flow into each other",
                "sentence_style": "Long and comprehensive: 20-25 words, uses clauses and qualifiers",
                "emphasis_style": "Minimal formatting: let the content speak for itself, only bold section headers",
                "visual_elements": "Minimal: pure paragraph text with occasional subheadings",
                "readability_target": "Academic formal: Graduate level, comprehensive and precise",
                "unique_trait": "Uses a Q&A format for one section to add variety"
            }
        ]
        
        design_structures = []
        for i, testimony in enumerate(testimonies):
            persona = personas[i % len(personas)]
            design = {
                "index": i,
                "template_id": f"T{i+1}",
                "assigned_recommender": testimony.get('recommender_name', f'Recommender {i+1}'),
                "word_count_target": "1800-2500 words",
                **persona
            }
            design_structures.append(design)
        
        return {
            "petitioner_name": petitioner_name,
            "design_structures": design_structures
        }
    
    def generate_style_blueprints(self, organized_data: Dict) -> Dict:
        """Alias for generate_design_structures - maintains backward compatibility"""
        return self.generate_design_structures(organized_data)

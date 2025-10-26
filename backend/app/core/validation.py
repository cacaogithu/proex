"""
Validation Module - Light validation for letter quality and heterogeneity
Does NOT rewrite - only logs warnings for monitoring
"""

import re
from typing import Dict, List, Tuple
from collections import Counter


# Forbidden phrases that sound too generic or template-like
FORBIDDEN_PHRASES = {
    "global": [
        # Portuguese clichés
        "A quem possa interessar",
        "a quem possa interessar",
        "É com grande satisfação",
        "é com grande satisfação",
        "Como tal,",
        "como tal,",
        "Venho por meio desta",
        "venho por meio desta",
        "Sem mais para o momento",
        "sem mais para o momento",
        "Certo de sua atenção",
        "certo de sua atenção",
        
        # English clichés
        "To Whom It May Concern",
        "to whom it may concern",
        "Dear Sir/Madam",
        "dear sir/madam",
        "It is with great pleasure",
        "it is with great pleasure",
        "As such,",
        "as such,",
        "I am writing to you",
        "i am writing to you",
        "Thank you for your time and consideration",
        "thank you for your time and consideration",
        "Yours faithfully",
        "yours faithfully",
    ],
    "immigration_specific": [
        # Phrases that sound too immigration-focused (should be subtle)
        "EB-2 NIW",
        "eb-2 niw",
        "peticionário",
        "petitioner",
        "National Interest Waiver",
        "national interest waiver",
        "imigração",
        "immigration",
        "visto",
        "visa application",
    ]
}


def _tokenize(text: str) -> List[str]:
    """
    Tokenize text into words and punctuation
    """
    return re.findall(r"\w+|\S", text.lower())


def _ngrams(tokens: List[str], n: int) -> List[str]:
    """
    Generate n-grams from token list
    """
    return [' '.join(tokens[i:i+n]) for i in range(len(tokens)-n+1)]


def jaccard_4gram(text_a: str, text_b: str) -> float:
    """
    Calculate Jaccard similarity using 4-grams
    
    Returns:
        float: Similarity score (0.0 = completely different, 1.0 = identical)
        
    Threshold:
        < 0.15: Excellent heterogeneity
        0.15-0.20: Acceptable
        > 0.20: Too similar (warning)
    """
    tokens_a = _tokenize(text_a)
    tokens_b = _tokenize(text_b)
    
    ngrams_a = set(_ngrams(tokens_a, 4))
    ngrams_b = set(_ngrams(tokens_b, 4))
    
    if not ngrams_a or not ngrams_b:
        return 0.0
    
    intersection = len(ngrams_a & ngrams_b)
    union = len(ngrams_a | ngrams_b)
    
    return intersection / union if union > 0 else 0.0


def find_forbidden_phrases(text: str, categories: List[str] = None) -> List[str]:
    """
    Find forbidden phrases in text
    
    Args:
        text: Text to check
        categories: List of categories to check (default: all except immigration_specific)
    
    Returns:
        List of forbidden phrases found
    """
    if categories is None:
        categories = ["global"]  # Don't check immigration_specific by default (too strict)
    
    found = []
    text_lower = text.lower()
    
    for category in categories:
        if category in FORBIDDEN_PHRASES:
            for phrase in FORBIDDEN_PHRASES[category]:
                if phrase.lower() in text_lower:
                    found.append(phrase)
    
    return list(set(found))  # Remove duplicates


def avg_sentence_length(text: str) -> float:
    """
    Calculate average sentence length in words
    
    Returns:
        Average number of words per sentence
    """
    # Split by sentence endings
    sentences = re.split(r'[.!?]+(?:\s+|$)', text.strip())
    sentences = [s for s in sentences if s.strip()]
    
    if not sentences:
        return 0.0
    
    word_counts = [len(re.findall(r'\w+', sentence)) for sentence in sentences]
    return sum(word_counts) / len(word_counts) if word_counts else 0.0


def validate_batch(letters: List[Dict]) -> Dict:
    """
    Validate a batch of letters for heterogeneity and quality
    
    Args:
        letters: List of letter dicts with 'letter_html' or 'text' field
    
    Returns:
        Validation report with warnings (does NOT block or rewrite)
    """
    report = {
        "total_letters": len(letters),
        "warnings": [],
        "similarity_matrix": [],
        "avg_similarity": 0.0,
        "max_similarity": 0.0,
        "forbidden_found": {},
        "sentence_length_stats": {}
    }
    
    if len(letters) < 2:
        return report
    
    # Extract text from letters
    texts = []
    for i, letter in enumerate(letters):
        text = letter.get('letter_html', '') or letter.get('text', '')
        # Remove HTML tags for comparison
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        texts.append(text)
    
    # 1. Check pairwise similarity (n-gram Jaccard)
    similarities = []
    for i in range(len(texts)):
        for j in range(i+1, len(texts)):
            sim = jaccard_4gram(texts[i], texts[j])
            similarities.append(sim)
            
            report["similarity_matrix"].append({
                "letter_a": i+1,
                "letter_b": j+1,
                "similarity": round(sim, 3)
            })
            
            # Warning if too similar
            if sim > 0.20:
                report["warnings"].append({
                    "type": "high_similarity",
                    "severity": "medium",
                    "message": f"Letters {i+1} and {j+1} are {sim*100:.1f}% similar (threshold: 20%)",
                    "letters": [i+1, j+1],
                    "score": round(sim, 3)
                })
    
    report["avg_similarity"] = round(sum(similarities) / len(similarities), 3) if similarities else 0.0
    report["max_similarity"] = round(max(similarities), 3) if similarities else 0.0
    
    # 2. Check forbidden phrases
    for i, text in enumerate(texts):
        forbidden = find_forbidden_phrases(text)
        if forbidden:
            report["forbidden_found"][f"letter_{i+1}"] = forbidden
            report["warnings"].append({
                "type": "forbidden_phrases",
                "severity": "low",
                "message": f"Letter {i+1} contains {len(forbidden)} cliché phrase(s): {', '.join(forbidden[:3])}",
                "letter": i+1,
                "phrases": forbidden
            })
    
    # 3. Sentence length stats (for monitoring only)
    for i, text in enumerate(texts):
        avg_len = avg_sentence_length(text)
        report["sentence_length_stats"][f"letter_{i+1}"] = round(avg_len, 1)
    
    return report


def print_validation_report(report: Dict):
    """
    Print validation report in a readable format
    """
    print("\n" + "="*60)
    print("📊 HETEROGENEITY VALIDATION REPORT")
    print("="*60)
    
    print(f"\n✓ Analyzed {report['total_letters']} letters")
    print(f"  Average similarity: {report['avg_similarity']*100:.1f}%")
    print(f"  Max similarity: {report['max_similarity']*100:.1f}%")
    
    if report['avg_similarity'] < 0.15:
        print("  ✅ Excellent heterogeneity!")
    elif report['avg_similarity'] < 0.20:
        print("  ✓ Good heterogeneity")
    else:
        print("  ⚠️ Moderate heterogeneity (acceptable but could be better)")
    
    # Warnings
    if report['warnings']:
        print(f"\n⚠️ {len(report['warnings'])} warning(s):")
        for warn in report['warnings'][:5]:  # Show first 5
            print(f"  - {warn['message']}")
        if len(report['warnings']) > 5:
            print(f"  ... and {len(report['warnings']-5} more")
    else:
        print("\n✅ No warnings - all letters passed validation!")
    
    # Forbidden phrases summary
    if report['forbidden_found']:
        print(f"\n📋 Clichés found in {len(report['forbidden_found'])} letter(s)")
    
    print("="*60 + "\n")

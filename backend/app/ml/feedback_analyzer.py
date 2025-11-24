"""
FeedbackAnalyzer - Extrai insights de comentários e scores históricos
Supervised learning baseado em feedback humano
"""

import re
from typing import Dict, List, Optional
from collections import Counter, defaultdict


class FeedbackAnalyzer:
    """Analisa feedback de cartas anteriores para extrair insights acionáveis"""
    
    def __init__(self, db):
        self.db = db
        
    def extract_insights(self, min_ratings: int = 5) -> Dict:
        """
        Extrai insights do feedback histórico
        
        Returns:
            {
                'avoid': ['problema1', 'problema2'],  # De cartas com score baixo
                'maintain': ['qualidade1', 'qualidade2'],  # De cartas com score alto
                'template_preferences': {'A': 85, 'B': 92, ...},
                'common_issues': {'muito genérico': 3, 'falta dados': 2}
            }
        """
        insights = {
            'avoid': [],
            'maintain': [],
            'template_preferences': {},
            'common_issues': Counter(),
            'success_patterns': Counter()
        }
        
        # Buscar todos os ratings
        all_ratings = self.db.get_all_letter_ratings()
        
        if len(all_ratings) < min_ratings:
            return insights  # Dados insuficientes
        
        # Separar por score
        low_score_comments = []
        high_score_comments = []
        
        for rating in all_ratings:
            score = rating.get('score', 0)
            comment = rating.get('comment', '')
            
            if comment and len(comment) > 10:  # Comentários significativos
                if score < 60:
                    low_score_comments.append(comment)
                elif score >= 80:
                    high_score_comments.append(comment)
        
        # Extrair problemas de comentários negativos
        insights['avoid'] = self._extract_issues(low_score_comments)
        insights['common_issues'] = Counter(insights['avoid'])
        
        # Extrair qualidades de comentários positivos
        insights['maintain'] = self._extract_qualities(high_score_comments)
        insights['success_patterns'] = Counter(insights['maintain'])
        
        # Analisar performance por template
        insights['template_preferences'] = self.db.get_template_analytics()

        return insights
    
    def _extract_issues(self, comments: List[str]) -> List[str]:
        """Extrai problemas mencionados em comentários negativos"""
        issues = []
        
        # Padrões comuns de problemas
        negative_patterns = [
            r'muito (genérico|genérica|vago|vaga)',
            r'falta (de )?(dados|informação|detalhes|personalização)',
            r'não (específico|específica|personalizado|personalizada)',
            r'repetitivo|repetitiva',
            r'(pouco|sem) (impacto|relevância)',
            r'formato (ruim|inadequado)',
            r'tom (inadequado|errado|formal demais|informal demais)'
        ]
        
        for comment in comments:
            comment_lower = comment.lower()
            for pattern in negative_patterns:
                matches = re.findall(pattern, comment_lower)
                if matches:
                    issues.append(f"{pattern.replace('|', '/')} identificado")
        
        return list(set(issues))  # Remover duplicatas
    
    def _extract_qualities(self, comments: List[str]) -> List[str]:
        """Extrai qualidades mencionadas em comentários positivos"""
        qualities = []
        
        # Padrões comuns de qualidades
        positive_patterns = [
            r'muito (bom|boa|detalhado|específico|personalizado)',
            r'excelente (conteúdo|estrutura|formato)',
            r'bem (escrito|escrita|estruturado|estruturada)',
            r'(dados|exemplos|detalhes) (específicos|concretos)',
            r'(forte|claro|clara) (impacto|narrativa)',
            r'profissional',
            r'convincente'
        ]
        
        for comment in comments:
            comment_lower = comment.lower()
            for pattern in positive_patterns:
                matches = re.findall(pattern, comment_lower)
                if matches:
                    qualities.append(f"{pattern.replace('|', '/')} valorizado")
        
        return list(set(qualities))
    
    def get_template_recommendation(self, context: Dict) -> str:
        """
        Recomenda melhor template baseado em contexto do recomendador

        Args:
            context: {'position': 'CTO', 'company_type': 'tech', ...}

        Returns:
            template_id recomendado ('A', 'B', etc)
        """
        performance = self.db.get_template_analytics()
        
        if not performance:
            return 'A'  # Default
        
        # Ordena templates por avg_score
        sorted_templates = sorted(
            performance.items(),
            key=lambda x: x[1].get('avg_score', 0),
            reverse=True
        )
        
        # Retorna o melhor template
        if sorted_templates:
            return sorted_templates[0][0]
        
        return 'A'
    
    def should_use_template(self, template_id: str, threshold: float = 70.0) -> bool:
        """Verifica se um template tem performance aceitável"""
        performance = self.db.get_template_analytics()
        
        template_stats = performance.get(template_id, {})
        avg_score = template_stats.get('avg_score', 100)  # Default: assumir bom se não há dados
        
        return avg_score >= threshold

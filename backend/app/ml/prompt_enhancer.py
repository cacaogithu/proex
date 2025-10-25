"""
PromptEnhancer - Combina supervised + unsupervised learning
Melhora prompts automaticamente baseado em feedback e padrões descobertos
"""

from typing import Dict, List, Optional
from .feedback_analyzer import FeedbackAnalyzer
from .embedding_engine import EmbeddingEngine
from .cluster_analyzer import ClusterAnalyzer


class PromptEnhancer:
    """
    Sistema de ML que combina:
    - Supervised: feedback humano (scores + comentários)
    - Unsupervised: clustering automático de cartas
    
    Para gerar prompts cada vez melhores
    """
    
    def __init__(self, db):
        self.db = db
        self.feedback_analyzer = FeedbackAnalyzer(db)
        self.embedding_engine = EmbeddingEngine()
        self.cluster_analyzer = ClusterAnalyzer(n_clusters=3)
        
        self.is_trained = False
        self.current_insights = {}
    
    def train_models(self, min_samples: int = 10):
        """
        Treina modelos de ML com dados históricos
        
        Args:
            min_samples: Mínimo de cartas necessárias para treinar
        """
        print("\n🧠 Training ML models...")
        
        # 1. Carregar embeddings e scores históricos
        all_embeddings = self.db.get_all_embeddings()
        
        if len(all_embeddings) < min_samples:
            print(f"   ⚠️  Insufficient data for training: {len(all_embeddings)}/{min_samples} letters")
            return False
        
        # 2. Extrair insights de feedback (supervised)
        self.current_insights = self.feedback_analyzer.extract_insights()
        
        # Salvar insights no database
        if self.current_insights['avoid']:
            self.db.save_ml_insight(
                'feedback_problems',
                {'patterns': self.current_insights['avoid']},
                confidence=0.8
            )
        
        if self.current_insights['maintain']:
            self.db.save_ml_insight(
                'feedback_qualities',
                {'patterns': self.current_insights['maintain']},
                confidence=0.8
            )
        
        print(f"   ✓ Extracted {len(self.current_insights['avoid'])} issues to avoid")
        print(f"   ✓ Extracted {len(self.current_insights['maintain'])} qualities to maintain")
        
        # 3. Treinar clustering (unsupervised)
        embeddings = [item['embedding'] for item in all_embeddings]
        scores = [item.get('score', 0) for item in all_embeddings]
        
        self.cluster_analyzer.fit(embeddings, scores)
        
        # Salvar perfis de cluster
        for cluster_id, profile in self.cluster_analyzer.cluster_profiles.items():
            self.db.save_ml_insight(
                'cluster_profile',
                {
                    'cluster_id': cluster_id,
                    'profile': profile
                },
                confidence=0.9
            )
        
        self.is_trained = True
        print("   ✅ ML models trained successfully!\n")
        return True
    
    def enhance_block_prompt(
        self, 
        base_prompt: str, 
        block_number: int,
        letter_context: Optional[Dict] = None,
        letter_embedding: Optional[List[float]] = None
    ) -> str:
        """
        Melhora prompt de geração de bloco usando ML
        
        Args:
            base_prompt: Prompt original
            block_number: Número do bloco (3-7)
            letter_context: Contexto da carta (recomendador, etc)
            letter_embedding: Embedding da carta (se disponível)
        
        Returns:
            Prompt melhorado com insights de ML
        """
        if not self.is_trained:
            # Tentar treinar automaticamente se houver dados
            self.train_models(min_samples=5)
        
        enhancements = []
        
        # 1. Adicionar insights de feedback (SUPERVISED)
        if self.current_insights.get('avoid'):
            avoid_list = "\n".join([f"  - {issue}" for issue in self.current_insights['avoid'][:3]])
            enhancements.append(f"""
AVOID these common issues identified in low-rated letters:
{avoid_list}
""")
        
        if self.current_insights.get('maintain'):
            maintain_list = "\n".join([f"  - {quality}" for quality in self.current_insights['maintain'][:3]])
            enhancements.append(f"""
MAINTAIN these qualities found in high-rated letters:
{maintain_list}
""")
        
        # 2. Adicionar insights de clustering (UNSUPERVISED)
        if letter_embedding and self.is_trained:
            cluster_id = self.cluster_analyzer.predict_cluster(letter_embedding)
            cluster_profile = self.cluster_analyzer.get_cluster_profile(cluster_id)
            cluster_recs = self.cluster_analyzer.get_recommendations(cluster_id)
            
            if cluster_profile:
                enhancements.append(f"""
This letter belongs to cluster: {cluster_profile['name']} (avg score: {cluster_profile['avg_score']:.1f})
Recommended focus: {', '.join(cluster_recs.get('focus_areas', ['professional excellence']))}
Tone: {cluster_recs.get('tone_guidance', 'professional')}
""")
        
        # 3. Adicionar recomendações de template baseado em performance
        template_prefs = self.current_insights.get('template_preferences', {})
        if template_prefs:
            best_templates = sorted(
                template_prefs.items(),
                key=lambda x: x[1].get('avg_score', 0),
                reverse=True
            )[:2]
            
            if best_templates:
                enhancements.append(f"""
Note: Templates {', '.join([t[0] for t in best_templates])} have highest performance (avg {best_templates[0][1].get('avg_score', 0):.1f})
""")
        
        # Combinar prompt base com melhorias
        if enhancements:
            enhanced_prompt = base_prompt + "\n\n" + "=== ML-GUIDED IMPROVEMENTS ===\n" + "\n".join(enhancements)
            return enhanced_prompt
        
        return base_prompt
    
    def enhance_assembly_prompt(
        self, 
        base_prompt: str,
        letter_embedding: Optional[List[float]] = None
    ) -> str:
        """
        Melhora prompt de assembly final
        Similar ao enhance_block_prompt mas focado em estrutura geral
        """
        return self.enhance_block_prompt(base_prompt, 0, None, letter_embedding)
    
    def get_template_recommendation(
        self, 
        recommender_context: Dict,
        current_templates_used: List[str]
    ) -> str:
        """
        Recomenda melhor template baseado em ML
        
        Args:
            recommender_context: Info sobre o recomendador
            current_templates_used: Templates já usados nesta submissão
        
        Returns:
            template_id recomendado
        """
        # Usar feedback analyzer
        base_recommendation = self.feedback_analyzer.get_template_recommendation(recommender_context)
        
        # Verificar se o template tem performance aceitável
        if not self.feedback_analyzer.should_use_template(base_recommendation, threshold=65.0):
            # Template tem score baixo, sugerir alternativa
            template_prefs = self.current_insights.get('template_preferences', {})
            
            # Filtrar templates com bom score
            good_templates = [
                tid for tid, stats in template_prefs.items()
                if stats.get('avg_score', 100) >= 70 and tid not in current_templates_used
            ]
            
            if good_templates:
                return good_templates[0]
        
        return base_recommendation
    
    def should_regenerate_letter(
        self, 
        letter_embedding: List[float],
        letter_score: int
    ) -> tuple[bool, str]:
        """
        Determina se uma carta deve ser regenerada baseado em ML
        
        Returns:
            (should_regenerate: bool, reason: str)
        """
        if letter_score >= 80:
            return False, "Score is already high"
        
        if not self.is_trained:
            return False, "ML model not trained yet"
        
        # Verificar se carta é outlier
        all_embeddings = self.db.get_all_embeddings()
        embeddings_only = [item['embedding'] for item in all_embeddings]
        
        outliers = self.cluster_analyzer.detect_outliers(embeddings_only + [letter_embedding])
        
        if len(embeddings_only) in outliers:
            return True, "Letter is an outlier - significantly different from patterns"
        
        # Verificar cluster com baixa performance
        cluster_id = self.cluster_analyzer.predict_cluster(letter_embedding)
        cluster_profile = self.cluster_analyzer.get_cluster_profile(cluster_id)
        
        if cluster_profile.get('avg_score', 100) < 70:
            return True, f"Letter belongs to low-performing cluster: {cluster_profile.get('name')}"
        
        return False, "Letter quality is acceptable"
    
    def get_ml_statistics(self) -> Dict:
        """Retorna estatísticas sobre o sistema de ML"""
        all_embeddings = self.db.get_all_embeddings()
        all_ratings = self.db.get_all_letter_ratings()
        
        stats = {
            'total_letters_analyzed': len(all_embeddings),
            'total_ratings_collected': len(all_ratings),
            'is_trained': self.is_trained,
            'insights_count': {
                'avoid_patterns': len(self.current_insights.get('avoid', [])),
                'maintain_patterns': len(self.current_insights.get('maintain', []))
            }
        }
        
        if self.is_trained:
            stats['clusters'] = {
                cid: {
                    'name': profile['name'],
                    'size': profile['size'],
                    'avg_score': profile['avg_score']
                }
                for cid, profile in self.cluster_analyzer.cluster_profiles.items()
            }
        
        return stats

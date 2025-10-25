"""
ClusterAnalyzer - Unsupervised learning para descobrir padrões
Agrupa cartas automaticamente sem labels
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
from collections import Counter, defaultdict


class ClusterAnalyzer:
    """Descobre padrões e agrupa cartas automaticamente usando unsupervised learning"""
    
    def __init__(self, n_clusters: int = 3):
        """
        Args:
            n_clusters: Número de clusters esperados (default: 3)
                - Cluster 0: Cartas técnicas/especializadas
                - Cluster 1: Cartas acadêmicas/research
                - Cluster 2: Cartas de liderança/business
        """
        self.n_clusters = n_clusters
        self.scaler = StandardScaler()
        self.kmeans = None
        self.cluster_profiles = {}
    
    def fit(self, embeddings: List[List[float]], scores: Optional[List[int]] = None):
        """
        Treina o modelo de clustering
        
        Args:
            embeddings: Lista de embeddings (cada um com 9 dimensões)
            scores: Lista opcional de scores para análise de performance
        """
        if len(embeddings) < self.n_clusters:
            print(f"⚠️ Dados insuficientes para clustering: {len(embeddings)} cartas")
            return
        
        # Normalizar embeddings
        X = np.array(embeddings)
        X_scaled = self.scaler.fit_transform(X)
        
        # Aplicar KMeans
        self.kmeans = KMeans(n_clusters=self.n_clusters, random_state=42, n_init=10)
        cluster_labels = self.kmeans.fit_predict(X_scaled)
        
        # Analisar perfil de cada cluster
        self._analyze_cluster_profiles(embeddings, cluster_labels, scores)
        
        print(f"✅ Clustering completo: {len(embeddings)} cartas em {self.n_clusters} clusters")
        for cluster_id, profile in self.cluster_profiles.items():
            print(f"   Cluster {cluster_id}: {profile['name']} (n={profile['size']}, avg_score={profile['avg_score']:.1f})")
    
    def predict_cluster(self, embedding: List[float]) -> int:
        """Prediz cluster de uma nova carta"""
        if self.kmeans is None:
            return 0  # Default se modelo não treinado
        
        X = np.array([embedding])
        X_scaled = self.scaler.transform(X)
        return int(self.kmeans.predict(X_scaled)[0])
    
    def get_cluster_profile(self, cluster_id: int) -> Dict:
        """Retorna perfil de um cluster específico"""
        return self.cluster_profiles.get(cluster_id, {
            'name': 'Unknown',
            'characteristics': [],
            'avg_score': 0,
            'size': 0
        })
    
    def _analyze_cluster_profiles(
        self, 
        embeddings: List[List[float]], 
        labels: np.ndarray,
        scores: Optional[List[int]] = None
    ):
        """Analisa características de cada cluster"""
        
        # Feature names (correspondendo ao embedding_engine.py)
        feature_names = [
            'technical_depth',
            'academic_rigor',
            'leadership_focus',
            'innovation_emphasis',
            'specificity',
            'formality',
            'storytelling',
            'impact_focus',
            'international_scope'
        ]
        
        for cluster_id in range(self.n_clusters):
            # Cartas neste cluster
            cluster_mask = labels == cluster_id
            cluster_embeddings = np.array([emb for i, emb in enumerate(embeddings) if cluster_mask[i]])
            
            if len(cluster_embeddings) == 0:
                continue
            
            # Calcular centroide (valores médios de features)
            centroid = np.mean(cluster_embeddings, axis=0)
            
            # Identificar features dominantes (>6.0)
            dominant_features = [
                feature_names[i] for i, val in enumerate(centroid) if val > 6.0
            ]
            
            # Calcular score médio deste cluster
            avg_score = 0
            if scores:
                cluster_scores = [scores[i] for i in range(len(scores)) if cluster_mask[i]]
                avg_score = np.mean(cluster_scores) if cluster_scores else 0
            
            # Nomear cluster baseado em features dominantes
            cluster_name = self._name_cluster(dominant_features, centroid)
            
            self.cluster_profiles[cluster_id] = {
                'name': cluster_name,
                'characteristics': dominant_features,
                'centroid': centroid.tolist(),
                'avg_score': float(avg_score),
                'size': int(np.sum(cluster_mask)),
                'feature_values': {name: float(centroid[i]) for i, name in enumerate(feature_names)}
            }
    
    def _name_cluster(self, dominant_features: List[str], centroid: np.ndarray) -> str:
        """Nomeia cluster baseado em suas características"""
        
        # Mapeamento de características para nomes
        if 'academic_rigor' in dominant_features and 'technical_depth' in dominant_features:
            return "Research/Academic"
        elif 'leadership_focus' in dominant_features:
            return "Leadership/Executive"
        elif 'technical_depth' in dominant_features and 'innovation_emphasis' in dominant_features:
            return "Technical/Innovation"
        elif 'storytelling' in dominant_features:
            return "Narrative/Storytelling"
        elif 'impact_focus' in dominant_features:
            return "Results/Impact"
        elif centroid[4] > 7:  # specificity
            return "Highly Specific"
        else:
            return "General/Balanced"
    
    def get_recommendations(self, cluster_id: int) -> Dict:
        """
        Retorna recomendações baseadas no perfil do cluster
        
        Returns:
            {
                'template_suggestion': 'B',
                'tone_guidance': 'formal academic',
                'focus_areas': ['technical details', 'research impact']
            }
        """
        profile = self.get_cluster_profile(cluster_id)
        features = profile.get('feature_values', {})
        
        recommendations = {
            'template_suggestion': 'A',
            'tone_guidance': 'professional',
            'focus_areas': []
        }
        
        # Sugerir template baseado em características
        if features.get('academic_rigor', 0) > 7:
            recommendations['template_suggestion'] = 'B'  # Academic template
            recommendations['tone_guidance'] = 'formal academic'
            recommendations['focus_areas'].append('research contributions')
        
        if features.get('technical_depth', 0) > 7:
            recommendations['template_suggestion'] = 'A'  # Technical template
            recommendations['focus_areas'].append('technical expertise')
        
        if features.get('leadership_focus', 0) > 7:
            recommendations['template_suggestion'] = 'D'  # Business template
            recommendations['tone_guidance'] = 'executive leadership'
            recommendations['focus_areas'].append('strategic impact')
        
        if features.get('storytelling', 0) > 7:
            recommendations['template_suggestion'] = 'C'  # Narrative template
            recommendations['focus_areas'].append('compelling narratives')
        
        return recommendations
    
    def detect_outliers(self, embeddings: List[List[float]], threshold: float = 2.0) -> List[int]:
        """
        Detecta cartas outliers (muito diferentes do padrão)
        
        Args:
            embeddings: Lista de embeddings
            threshold: Desvios padrão para considerar outlier
        
        Returns:
            Índices das cartas outliers
        """
        if len(embeddings) < 3:
            return []
        
        X = np.array(embeddings)
        
        # Calcular distância de cada ponto ao centroide geral
        centroid = np.mean(X, axis=0)
        distances = np.linalg.norm(X - centroid, axis=1)
        
        # Outliers = pontos além de threshold desvios padrão
        mean_dist = np.mean(distances)
        std_dist = np.std(distances)
        
        outlier_indices = []
        for i, dist in enumerate(distances):
            if dist > mean_dist + threshold * std_dist:
                outlier_indices.append(i)
        
        return outlier_indices

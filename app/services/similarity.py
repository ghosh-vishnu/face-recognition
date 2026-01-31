import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import Dict, List, Tuple


class SimilarityComputer:    
    # Similarity threshold for same person
    SAME_PERSON_THRESHOLD = 0.75
    
    def __init__(self):
        pass
    
    @staticmethod
    def cosine_similarity(emb1: np.ndarray, emb2: np.ndarray) -> float:
        # Reshape for sklearn
        emb1 = emb1.reshape(1, -1)
        emb2 = emb2.reshape(1, -1)
        
        # Compute cosine similarity
        similarity = cosine_similarity(emb1, emb2)[0][0]
        
        # Clip to [0, 1] range (cosine can be -1 to 1)
        similarity = np.clip(similarity, 0, 1)
        
        return float(similarity)
    
    def compute_pairwise_similarities(
        self,
        embeddings: List[np.ndarray]
    ) -> Dict[str, float]:
        if len(embeddings) != 3:
            raise ValueError(f"Expected 3 embeddings, got {len(embeddings)}")
        
        # Compute all pairs
        sim_1_2 = self.cosine_similarity(embeddings[0], embeddings[1])
        sim_1_3 = self.cosine_similarity(embeddings[0], embeddings[2])
        sim_2_3 = self.cosine_similarity(embeddings[1], embeddings[2])
        
        similarities = {
            'img1_img2': sim_1_2,
            'img1_img3': sim_1_3,
            'img2_img3': sim_2_3
        }
        
        return similarities
    
    def verify_same_person(
        self,
        similarities: Dict[str, float]
    ) -> Tuple[str, float, Dict]:
            # Extract similarity values
        sim_values = list(similarities.values())
        
        # Compute statistics
        min_similarity = min(sim_values)
        max_similarity = max(sim_values)
        avg_similarity = np.mean(sim_values)
        std_similarity = np.std(sim_values)
        
        # Decision logic: All pairs must exceed threshold
        if min_similarity >= self.SAME_PERSON_THRESHOLD:
            result = "SAME_PERSON"
            confidence = avg_similarity
        else:
            result = "DIFFERENT_PERSON"
            # Confidence is inverse of average when different
            confidence = 1.0 - avg_similarity
        
        # Detailed analysis
        analysis = {
            'min_similarity': float(min_similarity),
            'max_similarity': float(max_similarity),
            'avg_similarity': float(avg_similarity),
            'std_similarity': float(std_similarity),
            'threshold_used': self.SAME_PERSON_THRESHOLD,
            'all_pairs_pass': min_similarity >= self.SAME_PERSON_THRESHOLD
        }
        
        return result, confidence, analysis
    
    @staticmethod
    def similarity_to_percentage(similarity: float) -> float:
        return float(similarity * 100)

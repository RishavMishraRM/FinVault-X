import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from typing import Dict, Tuple, Optional

class SemanticCache:
    def __init__(self, threshold: float = 0.85):
        # Using a fast, lightweight model for caching
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.threshold = threshold
        # dict stores: {query: (query_embedding, response_text)}
        self.cache: Dict[str, Tuple[np.ndarray, str]] = {}
        self.hits = 0
        self.misses = 0

    def get(self, query: str) -> Tuple[Optional[str], Optional[str]]:
        if not self.cache:
            self.misses += 1
            return None, None
            
        query_emb = self.model.encode([query])[0]
        
        best_match = None
        best_orig_query = None
        highest_sim = 0.0
        
        for orig_query, (emb, response) in self.cache.items():
            sim = cosine_similarity([query_emb], [emb])[0][0]
            if sim > highest_sim and sim >= self.threshold:
                highest_sim = sim
                best_match = response
                best_orig_query = orig_query
                
        if best_match:
            self.hits += 1
            return best_match, best_orig_query
            
        self.misses += 1
        return None, None

    def set(self, query: str, response: str):
        query_emb = self.model.encode([query])[0]
        self.cache[query] = (query_emb, response)
        
    def get_hit_rate(self) -> float:
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return self.hits / total

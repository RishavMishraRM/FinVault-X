import spacy
from typing import Dict, Any

class QueryRouter:
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            import os
            os.system("python -m spacy download en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")
            
        # Keywords that signify relational reasoning
        self.graph_keywords = [
            "impact", "relation", "connection", "effect", "difference",
            "depends", "between", "versus", "vs", "compare", "affects", "influence"
        ]

    def route(self, query: str) -> str:
        """
        Calculates whether to route to 'graph' or 'vector'
        (Cache routing is handled upstream before calling router)
        """
        query_lower = query.lower()
        
        # 1. Check for relational/graph keywords
        for kw in self.graph_keywords:
            if kw in query_lower:
                return "graph"
                
        # 2. Check for multiple entity comparisons
        doc = self.nlp(query)
        entities = [ent for ent in doc.ents]
        
        if len(entities) >= 2:
             # Queries containing multiple entities often require joining concepts
            return "graph"
            
        # Default fallback to Vector RAG
        return "vector"

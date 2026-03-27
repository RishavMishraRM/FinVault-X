import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict

class VectorStore:
    def __init__(self, embedding_model: str = 'all-MiniLM-L6-v2'):
        self.encoder = SentenceTransformer(embedding_model)
        self.dimension = self.encoder.get_sentence_embedding_dimension()
        self.index = faiss.IndexFlatL2(self.dimension)
        self.documents: List[Dict] = []
        
    def add_documents(self, documents: List[Dict]):
        if not documents:
            return
            
        texts = [doc["content"] for doc in documents]
        # Generate embeddings
        embeddings = self.encoder.encode(texts)
        
        # Add to FAISS index
        faiss.normalize_L2(embeddings)
        self.index.add(embeddings)
        self.documents.extend(documents)
        
    def search(self, query: str, k: int = 3) -> List[Dict]:
        if self.index.ntotal == 0:
            return []
            
        query_emb = self.encoder.encode([query])
        faiss.normalize_L2(query_emb)
        
        distances, indices = self.index.search(query_emb, k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1 and idx < len(self.documents):
                doc = self.documents[idx].copy()
                doc["score"] = float(distances[0][i])
                results.append(doc)
                
        return results

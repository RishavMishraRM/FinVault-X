from typing import List, Dict
import re

class SemanticChunker:
    def __init__(self, max_chunk_size: int = 500):
        # Max chunk size approximated by words
        self.max_chunk_size = max_chunk_size
        
    def chunk_documents(self, documents: List[Dict]) -> List[Dict]:
        chunks = []
        for doc in documents:
            text = doc["content"]
            metadata = doc["metadata"]
            
            # Semantic chunking via paragraph splitting
            paragraphs = re.split(r'\n\s*\n', text)
            
            current_chunk = []
            current_length = 0
            
            for para in paragraphs:
                para = para.strip()
                if not para:
                    continue
                    
                tokens = para.split()
                if current_length + len(tokens) <= self.max_chunk_size:
                    current_chunk.append(para)
                    current_length += len(tokens)
                else:
                    if current_chunk:
                        chunk_text = "\n\n".join(current_chunk)
                        chunks.append({"content": chunk_text, "metadata": metadata.copy()})
                    current_chunk = [para]
                    current_length = len(tokens)
            
            if current_chunk:
                chunk_text = "\n\n".join(current_chunk)
                chunks.append({"content": chunk_text, "metadata": metadata.copy()})
                
        return chunks

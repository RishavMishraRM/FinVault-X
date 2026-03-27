import os
from pypdf import PdfReader
from typing import List, Dict

class DocumentLoader:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
    def load_documents(self) -> List[Dict]:
        documents = []
        if not os.path.exists(self.data_dir):
            return documents
            
        for filename in os.listdir(self.data_dir):
            filepath = os.path.join(self.data_dir, filename)
            if filename.endswith(".pdf"):
                documents.extend(self._load_pdf(filepath))
            elif filename.endswith(".txt"):
                documents.extend(self._load_txt(filepath))
        return documents
        
    def _load_pdf(self, filepath: str) -> List[Dict]:
        docs = []
        try:
            reader = PdfReader(filepath)
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if text and text.strip():
                    docs.append({
                        "content": text.strip(), 
                        "metadata": {"source": filepath, "page": i + 1}
                    })
        except Exception as e:
            print(f"Failed to load PDF {filepath}: {e}")
        return docs
        
    def _load_txt(self, filepath: str) -> List[Dict]:
        docs = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                if content.strip():
                    docs.append({
                        "content": content.strip(), 
                        "metadata": {"source": filepath, "page": 1}
                    })
        except Exception as e:
            print(f"Failed to load TXT {filepath}: {e}")
        return docs

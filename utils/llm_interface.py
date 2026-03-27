import requests
import json

class LLMInterface:
    def __init__(self, model_name="mistral", base_url="http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url
        
    def generate(self, prompt: str) -> str:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False
        }
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json().get("response", "")
        except requests.exceptions.ConnectionError:
            return "Error: Could not connect to local LLM. Ensure Ollama is running on localhost:11434"
        except Exception as e:
            return f"Error communicating with local LLM: {str(e)}"
            
    def generate_response(self, query: str, context: str, system_prompt: str) -> str:
        full_prompt = (
            f"### System: {system_prompt}\n\n"
            f"### Context:\n{context}\n\n"
            f"### User Query: {query}\n\n"
            "### Assistant Answer:"
        )
        return self.generate(full_prompt)

from abc import ABC, abstractmethod
import os
from typing import List, Dict, Any, Optional
import openai
import json

class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        pass

class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-4-turbo-preview"):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.3
        )
        return response.choices[0].message.content or ""

class OllamaProvider(LLMProvider):
    def __init__(self, base_url: str = "http://localhost:11434/v1", model: str = "llama3"):
        self.client = openai.OpenAI(base_url=base_url, api_key="ollama")
        self.model = model

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            return f"Error connecting to Ollama: {str(e)}"

def get_provider(provider_type: str, **kwargs) -> LLMProvider:
    if provider_type.lower() == "openai":
        return OpenAIProvider(api_key=kwargs.get("api_key", os.getenv("OPENAI_API_KEY")), model=kwargs.get("model", "gpt-4-turbo-preview"))
    elif provider_type.lower() == "ollama":
        return OllamaProvider(base_url=kwargs.get("base_url", "http://localhost:11434/v1"), model=kwargs.get("model", "llama3"))
    else:
        raise ValueError(f"Unknown provider: {provider_type}")

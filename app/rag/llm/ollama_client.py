from typing import List, AsyncGenerator
import httpx
import json
import logging
from app.rag.llm.base import BaseLLM

logger = logging.getLogger(__name__)

class OllamaClient(BaseLLM):
    """
    Client for local Ollama instance.
    """
    def __init__(self, base_url: str | None = None, model: str = "llama3"):
        self.base_url = base_url or "http://localhost:11434"
        self.model = model

    async def generate(self, system_prompt: str, user_query: str, 
                 context_chunks: List[str]) -> str:
        """
        Generate a response from Ollama.
        """
        # We need to construct a prompt that Ollama understands.
        # For base models like llama3, prompt formatting matters.
        # But /api/generate expects a raw string.
        # Let's try to be more robust or fallback to /api/chat if needed.
        
        prompt = self._build_prompt(system_prompt, user_query, context_chunks)
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False
                    }
                )
                response.raise_for_status()
                result = response.json()
                return str(result.get("response", ""))
            except Exception as e:
                logger.error(f"Ollama generation failed: {e}")
                return f"Error generating response: {str(e)}"

    async def generate_stream(self, system_prompt: str, user_query: str, 
                              context_chunks: List[str]) -> AsyncGenerator[str, None]:
        """
        Stream response from Ollama.
        """
        prompt = self._build_prompt(system_prompt, user_query, context_chunks)
        
        # Log the request details for debugging
        logger.info(f"Ollama Request: model={self.model}, base_url={self.base_url}")
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                # First check if model exists/is running by a simple health check or just try generate
                # We can't easily check model existence without another call, but let's just stream.
                
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": True
                    }
                ) as response:
                    if response.status_code != 200:
                        # Read the error body
                        error_body = await response.aread()
                        error_msg = f"Ollama API Error {response.status_code}: {error_body.decode('utf-8')}"
                        logger.error(error_msg)
                        yield f"Error: {error_msg}"
                        return

                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                            chunk = data.get("response", "")
                            if chunk:
                                yield chunk
                            if data.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue
            except httpx.ConnectError:
                 yield f"Error: Could not connect to Ollama at {self.base_url}. Is it running?"
            except httpx.ReadTimeout:
                 yield "Error: Ollama timed out generating the response."
            except Exception as e:
                logger.error(f"Ollama stream failed: {e}")
                yield f"Error: {str(e)}"

    def _build_prompt(self, system_prompt: str, user_query: str, context_chunks: List[str]) -> str:
        context_text = "\n\n".join(context_chunks)
        # Using Llama 3 instruct format if possible, or generic.
        # <|begin_of_text|><|start_header_id|>system<|end_header_id|>
        # ...
        # But since we use /api/generate with "prompt", we should probably use the raw template or just a clear structure.
        # Llama 3 is quite sensitive.
        # Let's use a standard instruct format for Llama 3.
        
        return f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

{system_prompt}

Context information is below.
---------------------
{context_text}
---------------------
<|eot_id|><|start_header_id|>user<|end_header_id|>

{user_query}<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Generator

class BaseLLM(ABC):
    """
    Abstract base class for LLM providers (Ollama, OpenAI).
    """

    @abstractmethod
    def generate(self, system_prompt: str, user_query: str, 
                 context_chunks: List[str]) -> str:
        """
        Generate a response from the LLM.
        
        Args:
            system_prompt: The instruction for the LLM.
            user_query: The user's question.
            context_chunks: List of retrieved text chunks to use as context.
            
        Returns:
            The complete generated response string.
        """
        pass

    @abstractmethod
    async def generate_stream(self, system_prompt: str, user_query: str, 
                              context_chunks: List[str]) -> Generator[str, None, None]:
        """
        Stream the response from the LLM.
        
        Args:
            system_prompt: The instruction for the LLM.
            user_query: The user's question.
            context_chunks: List of retrieved text chunks to use as context.
            
        Yields:
            Chunks of the generated response string as they arrive.
        """
        pass

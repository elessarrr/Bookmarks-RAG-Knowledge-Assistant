from typing import List, AsyncGenerator, Dict, Any, Optional
from dataclasses import dataclass
from app.rag.retriever import Retriever
from app.rag.llm.base import BaseLLM
from app.storage.base import RetrievedChunk

@dataclass
class RAGResponse:
    answer: str
    sources: List[RetrievedChunk]

class RAGEngine:
    """
    RAG Engine that orchestrates retrieval and generation.
    """
    def __init__(self, retriever: Retriever, llm: BaseLLM):
        self.retriever = retriever
        self.llm = llm
        
        # Default system prompt
        self.system_prompt = """You are a helpful assistant that answers questions based on the provided context.
Use the following context to answer the user's question.
If the answer is not in the context, say you don't know.
Cite the sources using [Source X] format where X is the number of the source.
"""

    def _format_context(self, chunks: List[RetrievedChunk]) -> List[str]:
        """
        Format retrieved chunks for the prompt.
        """
        formatted = []
        for i, chunk in enumerate(chunks, 1):
            source_info = f"Source {i} ({chunk.metadata.get('title', 'Unknown')} - {chunk.metadata.get('url', '')})"
            formatted.append(f"[{source_info}]:\n{chunk.text}")
        return formatted

    async def query(self, user_query: str, k: int = 5, filters: Optional[Dict[str, Any]] = None) -> RAGResponse:
        """
        Execute a RAG query and return the full response.
        """
        # 1. Retrieve
        chunks = self.retriever.retrieve(user_query, k=k, filters=filters)
        
        if not chunks:
            return RAGResponse(answer="I couldn't find any relevant bookmarks to answer your question.", sources=[])
            
        # 2. Augment
        context_blocks = self._format_context(chunks)
        
        # 3. Generate
        answer = await self.llm.generate(self.system_prompt, user_query, context_blocks)
        
        return RAGResponse(answer=answer, sources=chunks)

    async def query_stream(self, user_query: str, k: int = 5, filters: Optional[Dict[str, Any]] = None) -> AsyncGenerator[str, None]:
        """
        Execute a RAG query and stream the response tokens.
        Note: This only streams the answer text. Sources are not yielded in the stream easily unless we yield a special event first.
        For simplicity, we just stream the text.
        """
        # 1. Retrieve
        chunks = self.retriever.retrieve(user_query, k=k, filters=filters)
        
        if not chunks:
            yield "I couldn't find any relevant bookmarks to answer your question."
            return

        # 2. Augment
        context_blocks = self._format_context(chunks)
        
        # 3. Generate Stream
        async for chunk in self.llm.generate_stream(self.system_prompt, user_query, context_blocks):
            yield chunk

from typing import List
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy
from langchain_community.chat_models import ChatOllama
from langchain_community.embeddings import OllamaEmbeddings
from app.config import settings
import logging

logger = logging.getLogger(__name__)

def get_ragas_llm():
    return ChatOllama(model=settings.llm_model, base_url=settings.ollama_base_url)

def get_ragas_embeddings():
    # Ragas needs embeddings for answer_relevancy (to embed the generated question)
    # We use OllamaEmbeddings matching our local setup
    return OllamaEmbeddings(model=settings.embedding_model, base_url=settings.ollama_base_url)

def calculate_faithfulness(question: str, answer: str, contexts: List[str]) -> float:
    """
    Calculate Faithfulness using Ragas.
    Faithfulness measures if the answer is derived from the context.
    """
    data = {
        'question': [question],
        'answer': [answer],
        'contexts': [contexts]
    }
    dataset = Dataset.from_dict(data)
    
    try:
        result = evaluate(
            dataset=dataset,
            metrics=[faithfulness],
            llm=get_ragas_llm(),
            embeddings=get_ragas_embeddings(),
            raise_exceptions=False
        )
        # Handle case where result might be NaN
        val = result.get('faithfulness', 0.0)
        return float(val) if val == val else 0.0 # Check for NaN
    except Exception as e:
        logger.error(f"Ragas faithfulness evaluation failed: {e}")
        return 0.0

def calculate_answer_relevance(question: str, answer: str, contexts: List[str]) -> float:
    """
    Calculate Answer Relevance using Ragas.
    Measures how relevant the answer is to the question.
    """
    data = {
        'question': [question],
        'answer': [answer],
        'contexts': [contexts]
    }
    dataset = Dataset.from_dict(data)
    
    try:
        result = evaluate(
            dataset=dataset,
            metrics=[answer_relevancy],
            llm=get_ragas_llm(),
            embeddings=get_ragas_embeddings(),
            raise_exceptions=False
        )
        val = result.get('answer_relevancy', 0.0)
        return float(val) if val == val else 0.0
    except Exception as e:
        logger.error(f"Ragas answer_relevancy evaluation failed: {e}")
        return 0.0

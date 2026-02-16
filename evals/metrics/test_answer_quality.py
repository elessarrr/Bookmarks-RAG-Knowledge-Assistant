import pytest
from unittest.mock import MagicMock, patch
from evals.metrics.answer_quality import calculate_faithfulness, calculate_answer_relevance

@pytest.fixture
def mock_ragas():
    with patch("evals.metrics.answer_quality.evaluate") as mock_eval:
        yield mock_eval

def test_calculate_faithfulness(mock_ragas):
    # Mock Ragas result
    # Ragas returns a Result object or dict
    mock_ragas.return_value = {"faithfulness": 0.9}
    
    question = "Q"
    answer = "A"
    contexts = ["C1", "C2"]
    
    score = calculate_faithfulness(question, answer, contexts)
    assert score == 0.9
    
    # Check if Ragas evaluate was called with correct data
    call_args = mock_ragas.call_args
    # Ragas evaluate takes dataset (Dataset object) and metrics
    # We'll check implementation details later, but for now we assume it calls evaluate
    assert call_args is not None

def test_calculate_answer_relevance(mock_ragas):
    mock_ragas.return_value = {"answer_relevancy": 0.8}
    
    score = calculate_answer_relevance("Q", "A", ["C1"])
    assert score == 0.8

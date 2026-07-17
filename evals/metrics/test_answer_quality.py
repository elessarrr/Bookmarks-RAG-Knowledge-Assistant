import pytest
from unittest.mock import MagicMock, patch
from evals.metrics.answer_quality import (
    calculate_faithfulness,
    calculate_answer_relevance,
    get_ragas_llm,
)

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


def _fake_settings(judge, generator):
    s = MagicMock()
    s.ragas_judge_model = judge
    s.llm_model = generator
    s.ollama_base_url = "http://localhost:11434"
    return s


def test_ragas_judge_uses_independent_judge_model():
    """The judge must be built from ragas_judge_model, not llm_model -- otherwise
    the generator grades its own answers (self-evaluation bias)."""
    with patch("evals.metrics.answer_quality.ChatOllama") as mock_chat, patch(
        "evals.metrics.answer_quality.settings", _fake_settings("qwen2.5:32b", "gpt-oss:20b")
    ):
        get_ragas_llm()

    mock_chat.assert_called_once()
    assert mock_chat.call_args.kwargs.get("model") == "qwen2.5:32b"


def test_ragas_judge_warns_when_judge_equals_generator(caplog):
    """If someone configures the judge to equal the generator, the harness should
    say so loudly rather than silently reintroducing self-evaluation bias."""
    with patch("evals.metrics.answer_quality.ChatOllama"), patch(
        "evals.metrics.answer_quality.settings", _fake_settings("gpt-oss:20b", "gpt-oss:20b")
    ):
        with caplog.at_level("WARNING"):
            get_ragas_llm()

    assert any("judge" in r.message.lower() for r in caplog.records)

import pytest
from unittest.mock import MagicMock, patch
from app.embeddings.openai_embedder import OpenAIEmbedder
import os

def test_openai_embedder_init():
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
        embedder = OpenAIEmbedder()
        assert embedder.api_key == "test-key"

def test_openai_embedder_missing_key():
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError):
            OpenAIEmbedder()

def test_openai_embedder_batch():
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "data": [
            {"embedding": [0.1, 0.2]},
            {"embedding": [0.3, 0.4]}
        ]
    }
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.Client") as mock_client_cls:
        mock_client = mock_client_cls.return_value
        mock_client.__enter__.return_value = mock_client
        mock_client.post.return_value = mock_response
        
        embedder = OpenAIEmbedder(api_key="sk-test")
        embeddings = embedder.embed_batch(["hello", "world"])
        
        assert len(embeddings) == 2
        assert embeddings[0] == [0.1, 0.2]
        assert embeddings[1] == [0.3, 0.4]
        
        # Verify call
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "https://api.openai.com/v1/embeddings"
        json_body = call_args[1]["json"]
        assert json_body["model"] == "text-embedding-3-small"
        assert len(json_body["input"]) == 2

def test_openai_embedder_single():
    # Reuse batch logic
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "data": [
            {"embedding": [0.1, 0.2]}
        ]
    }
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.Client") as mock_client_cls:
        mock_client = mock_client_cls.return_value
        mock_client.__enter__.return_value = mock_client
        mock_client.post.return_value = mock_response
        
        embedder = OpenAIEmbedder(api_key="sk-test")
        embedding = embedder.embed_single("hello")
        
        assert embedding == [0.1, 0.2]

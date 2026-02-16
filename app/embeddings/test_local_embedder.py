from app.embeddings.local_embedder import LocalEmbedder

# This might be slow if it downloads the model for the first time.
# Ideally we mock SentenceTransformer for unit tests, but for integration/dev test it's fine.
# We can use a very small model for testing or mock it.
# Let's mock it to keep tests fast and offline.

from unittest.mock import MagicMock, patch
import numpy as np

def test_local_embedder_single():
    with patch("app.embeddings.local_embedder.SentenceTransformer") as mock_cls:
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([0.1, 0.2, 0.3])
        mock_cls.return_value = mock_model
        
        embedder = LocalEmbedder("test-model")
        vector = embedder.embed_single("hello")
        
        assert len(vector) == 3
        assert vector == [0.1, 0.2, 0.3]
        mock_model.encode.assert_called_with("hello", convert_to_numpy=True)

def test_local_embedder_batch():
    with patch("app.embeddings.local_embedder.SentenceTransformer") as mock_cls:
        mock_model = MagicMock()
        # Mock batch return
        mock_model.encode.return_value = np.array([[0.1, 0.2], [0.3, 0.4]])
        mock_cls.return_value = mock_model
        
        embedder = LocalEmbedder("test-model")
        vectors = embedder.embed_batch(["hello", "world"])
        
        assert len(vectors) == 2
        assert vectors[0] == [0.1, 0.2]
        assert vectors[1] == [0.3, 0.4]
        mock_model.encode.assert_called_with(["hello", "world"], convert_to_numpy=True)

def test_local_embedder_empty_batch():
    with patch("app.embeddings.local_embedder.SentenceTransformer") as mock_cls:
        embedder = LocalEmbedder("test-model")
        vectors = embedder.embed_batch([])
        assert vectors == []

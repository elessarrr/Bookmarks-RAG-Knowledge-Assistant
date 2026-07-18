import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.rag.llm.ollama_client import OllamaClient

@pytest.mark.asyncio
async def test_ollama_generate():
    client = OllamaClient(base_url="http://mock-ollama", model="test-model")
    
    # Mock return value
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "response": "Generated response",
        "done": True
    }
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        
        response = await client.generate(
            system_prompt="System",
            user_query="Query",
            context_chunks=["Chunk 1", "Chunk 2"]
        )
        
        assert response == "Generated response"
        
        # Verify call arguments
        call_args = mock_post.call_args
        assert call_args[0][0] == "http://mock-ollama/api/generate"
        json_body = call_args[1]["json"]
        assert json_body["model"] == "test-model"
        # Check prompt existence instead of messages
        assert "prompt" in json_body
        assert json_body["stream"] is False

@pytest.mark.asyncio
async def test_ollama_generate_stream():
    client = OllamaClient(base_url="http://mock-ollama", model="test-model")

    lines = [
        '{"response": "Hello", "done": false}',
        '{"response": " World", "done": false}',
        '{"done": true}'
    ]

    mock_response = MagicMock()
    mock_response.status_code = 200

    async def mock_aiter_lines():
        for line in lines:
            yield line

    mock_response.aiter_lines = mock_aiter_lines

    mock_stream_ctx = AsyncMock()
    mock_stream_ctx.__aenter__.return_value = mock_response

    with patch("httpx.AsyncClient.stream", return_value=mock_stream_ctx) as mock_stream:
        chunks = [
            chunk
            async for chunk in client.generate_stream(
                system_prompt="System",
                user_query="Query",
                context_chunks=["Chunk 1", "Chunk 2"]
            )
        ]

    assert "".join(chunks) == "Hello World"
    mock_stream.assert_called_once()
    call_args = mock_stream.call_args
    assert call_args.args[:2] == ("POST", "http://mock-ollama/api/generate")
    json_body = call_args.kwargs["json"]
    assert json_body["model"] == "test-model"
    assert json_body["stream"] is True


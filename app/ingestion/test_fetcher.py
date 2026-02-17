import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.ingestion.fetcher import fetch_url
import httpx

@pytest.mark.asyncio
async def test_fetch_success():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "<html><body><h1>Hello World</h1></body></html>"
    mock_response.headers = {"content-type": "text/html"}

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        
        # We also need to mock robots.txt check if we implement it inside fetch_url
        # For now, let's assume we can mock the robot parser or the request for robots.txt
        # But if the implementation does a separate request for robots.txt, we need to handle that.
        # Let's assume for this test that robots.txt allows it or we mock that part too.
        # To keep it simple, we might mock the robots check function if we separate it,
        # but since we are testing fetch_url as a black box:
        
        with patch("app.ingestion.fetcher.check_robots_txt", new_callable=AsyncMock) as mock_robots:
            mock_robots.return_value = True # Allowed
            
            result = await fetch_url("https://example.com")
            
            assert result.url == "https://example.com"
            assert result.status_code == 200
            assert "Hello World" in result.content
            assert result.error is None

@pytest.mark.asyncio
async def test_fetch_404():
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.text = "Not Found"
    mock_response.headers = {"content-type": "text/html"}

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        with patch("app.ingestion.fetcher.check_robots_txt", new_callable=AsyncMock) as mock_robots:
            mock_robots.return_value = True

            result = await fetch_url("https://example.com/404")
            
            assert result.status_code == 404
            assert result.content is None
            assert result.error is not None

@pytest.mark.asyncio
async def test_fetch_timeout():
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.TimeoutException("Timeout")
        with patch("app.ingestion.fetcher.check_robots_txt", new_callable=AsyncMock) as mock_robots:
            mock_robots.return_value = True

            result = await fetch_url("https://example.com/timeout")
            
            assert result.content is None
            assert "Timeout" in result.error

@pytest.mark.skip(reason="Robots.txt check is disabled in current implementation")
async def test_robots_block():
    with patch("app.ingestion.fetcher.check_robots_txt", new_callable=AsyncMock) as mock_robots:
        mock_robots.return_value = False # Blocked

        result = await fetch_url("https://example.com/secret")
        
        assert result.content is None
        assert "Blocked by robots.txt" in result.error

@pytest.mark.asyncio
async def test_non_html_content():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "%PDF-1.4..."
    mock_response.headers = {"content-type": "application/pdf"}

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        with patch("app.ingestion.fetcher.check_robots_txt", new_callable=AsyncMock) as mock_robots:
            mock_robots.return_value = True

            result = await fetch_url("https://example.com/doc.pdf")
            
            assert result.status_code == 200
            assert result.content is None
            assert "Non-HTML content" in result.error
            assert result.content_type == "application/pdf"

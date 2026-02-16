from typing import Optional
from readability import Document
from bs4 import BeautifulSoup
import re

def clean_html(html_content: str) -> Optional[str]:
    """
    Cleans HTML content using readability-lxml to extract the main article text.
    Strips nav/footer/ads, normalizes whitespace.
    Returns None if the resulting text is too short (<100 chars).
    """
    if not html_content or not html_content.strip():
        return None

    try:
        # 1. Extract main content using readability
        doc = Document(html_content)
        summary_html = doc.summary()
        
        # 2. Strip HTML tags using BeautifulSoup
        # We use BS4 on the summary because readability returns HTML string of the main content
        soup = BeautifulSoup(summary_html, "lxml")
        
        # Explicitly remove typical noise tags if they survived readability
        for tag in soup(["nav", "footer", "script", "style", "aside"]):
            tag.decompose()

        # Remove elements with noise classes/ids if they survived
        # This is a heuristic; readability usually handles this, but sometimes not perfect
        noise_patterns = re.compile(r"nav|footer|ads|sidebar|header", re.I)
        for tag in soup.find_all(attrs={"class": noise_patterns}):
             tag.decompose()
        for tag in soup.find_all(attrs={"id": noise_patterns}):
             tag.decompose()

        text = soup.get_text(separator=" ", strip=True)
        
        # 3. Normalize whitespace
        # Replace multiple spaces/newlines with single space
        text = re.sub(r'\s+', ' ', text).strip()
        
        # 4. Check length threshold
        if len(text) < 100:
            return None
            
        return text
    except Exception:
        # If parsing fails for any reason, return None
        return None

from app.ingestion.cleaner import clean_html

def test_clean_html_basic():
    html = """
    <html>
        <body>
            <nav>Menu 1 | Menu 2</nav>
            <div class="header">Header</div>
            <article>
                <h1>Main Title</h1>
                <p>This is the main content of the article. It should be preserved.</p>
                <p>It has multiple paragraphs and meaningful text that we want to index.</p>
                <p>Let's make sure it is long enough to pass the threshold of 100 characters. 
                   Adding more text here to ensure we cross the limit easily.</p>
            </article>
            <footer>Copyright 2024</footer>
            <div class="ads">Buy this now!</div>
        </body>
    </html>
    """
    cleaned = clean_html(html)
    assert cleaned is not None
    assert "Main Title" in cleaned
    assert "This is the main content" in cleaned
    assert "Menu 1" not in cleaned
    assert "Copyright 2024" not in cleaned
    assert "Buy this now" not in cleaned

def test_clean_html_too_short():
    html = """
    <html>
        <body>
            <p>Too short.</p>
        </body>
    </html>
    """
    cleaned = clean_html(html)
    assert cleaned is None

def test_clean_html_empty():
    cleaned = clean_html("")
    assert cleaned is None

def test_clean_html_whitespace_normalization():
    html = """
    <html>
        <body>
            <article>
                <p>   Lots   of   spaces.   </p>
                <p>
                    Newlines
                    everywhere.
                </p>
                <p>But this text needs to be long enough to be returned, otherwise we get None. 
                   So I am adding more filler text here to satisfy the length requirement.</p>
            </article>
        </body>
    </html>
    """
    cleaned = clean_html(html)
    assert cleaned is not None
    assert "Lots of spaces." in cleaned
    assert "Newlines everywhere." in cleaned
    assert "\n" not in cleaned  # Should be normalized to single spaces usually, or clean paragraphs

def test_clean_html_no_main_content():
    html = """
    <html>
        <body>
            <nav>Just navigation</nav>
            <footer>Just footer</footer>
        </body>
    </html>
    """
    cleaned = clean_html(html)
    assert cleaned is None

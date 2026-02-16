from datetime import datetime, timezone
from app.ingestion.parser import parse_bookmarks

# Sample Chrome-style Export
CHROME_BOOKMARKS = """
<!DOCTYPE NETSCAPE-Bookmark-file-1>
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks</H1>
<DL><p>
    <DT><H3 ADD_DATE="1707523200" LAST_MODIFIED="1707523200">Tech</H3>
    <DL><p>
        <DT><A HREF="https://example.com/ai" ADD_DATE="1707523200" ICON="data:image/png;base64,xyz">AI News</A>
        <DT><A HREF="https://github.com" ADD_DATE="1707609600">GitHub</A>
    </DL><p>
    <DT><H3 ADD_DATE="1707523200">Reading</H3>
    <DL><p>
        <DT><H3 ADD_DATE="1707523200">Blogs</H3>
        <DL><p>
            <DT><A HREF="https://blog.example.com" ADD_DATE="1707696000">My Blog</A>
        </DL><p>
    </DL><p>
    <DT><A HREF="https://google.com" ADD_DATE="1707782400">Google</A>
</DL><p>
"""

# Sample Firefox-style Export (often slightly different nesting/attributes)
FIREFOX_BOOKMARKS = """
<!DOCTYPE NETSCAPE-Bookmark-file-1>
<!-- This is an automatically generated file.
     It will be read and overwritten.
     DO NOT EDIT! -->
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks Menu</H1>
<DL><p>
    <DT><A HREF="https://mozilla.org" ADD_DATE="1600000000" ICON="..."></A>
    <DT><A HREF="https://rust-lang.org" ADD_DATE="1600000000">Rust</A>
</DL><p>
"""

def test_parse_chrome_bookmarks():
    bookmarks = parse_bookmarks(CHROME_BOOKMARKS)
    assert len(bookmarks) == 4
    
    # Check simple bookmark in folder
    assert bookmarks[0].url == "https://example.com/ai"
    assert bookmarks[0].title == "AI News"
    assert bookmarks[0].folder == "Tech"
    assert bookmarks[0].date_added == datetime.fromtimestamp(1707523200, tz=timezone.utc)
    assert bookmarks[0].icon == "data:image/png;base64,xyz"

    # Check bookmark in nested folder
    # Tech -> Reading -> Blogs -> My Blog
    # Note: In the sample HTML, Reading is a sibling of Tech, not child.
    # <DT><H3>Tech</H3>...<DT><H3>Reading</H3>
    # So it should be Reading/Blogs/My Blog
    blog = next(b for b in bookmarks if b.url == "https://blog.example.com")
    assert "Reading" in blog.folder
    assert "Blogs" in blog.folder
    assert blog.folder == "Reading/Blogs"

    # Check root level bookmark (folder might be empty or "Bookmarks")
    google = next(b for b in bookmarks if b.url == "https://google.com")
    assert google.folder == "" or google.folder == "Bookmarks"

def test_parse_nested_folders():
    bookmarks = parse_bookmarks(CHROME_BOOKMARKS)
    blog = next(b for b in bookmarks if b.title == "My Blog")
    assert blog.folder == "Reading/Blogs"

def test_missing_date_fields():
    html = """
    <DL><p>
        <DT><A HREF="https://nodate.com">No Date</A>
    </DL><p>
    """
    bookmarks = parse_bookmarks(html)
    assert len(bookmarks) == 1
    assert bookmarks[0].url == "https://nodate.com"
    # Should default to now or specific fallback, ensuring no crash
    assert isinstance(bookmarks[0].date_added, datetime)

def test_duplicate_urls():
    # If the parser implementation decides to handle duplicates (dedupe or keep), 
    # the task list implies we just extract them. 
    # Task 2.11 says "deduplicate (skip URLs already in DB)", so parser might return all.
    # Let's assume parser returns all occurrences found in the HTML.
    html = """
    <DL><p>
        <DT><A HREF="https://example.com" ADD_DATE="100">Link 1</A>
        <DT><A HREF="https://example.com" ADD_DATE="200">Link 1 Again</A>
    </DL><p>
    """
    bookmarks = parse_bookmarks(html)
    assert len(bookmarks) == 2
    assert bookmarks[0].url == "https://example.com"
    assert bookmarks[1].url == "https://example.com"

def test_empty_file():
    bookmarks = parse_bookmarks("")
    assert bookmarks == []

def test_malformed_html():
    html = "<DL><p><DT><A HREF='oops'>Unclosed tags"
    # Should do best effort
    bookmarks = parse_bookmarks(html)
    assert len(bookmarks) == 1
    assert bookmarks[0].url == "oops"

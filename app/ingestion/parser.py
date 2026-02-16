from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime, timezone
from bs4 import BeautifulSoup
import bs4

@dataclass
class Bookmark:
    url: str
    title: str
    folder: str
    date_added: datetime
    icon: Optional[str] = None

def parse_bookmarks(html_content: str) -> List[Bookmark]:
    """
    Parses a Netscape Bookmark HTML string and returns a list of Bookmark objects.
    """
    if not html_content.strip():
        return []

    # Use lxml for better handling of broken/old HTML if available, else html.parser
    # The task list mentioned readability-lxml, so lxml should be installed.
    soup = BeautifulSoup(html_content, "lxml")
    
    bookmarks: List[Bookmark] = []
    
    # We need to traverse the structure to maintain folder context.
    # The structure is usually nested DL/DT.
    # A standard recursive approach on the DL tags works best.
    
    def process_dl(dl_tag: bs4.element.Tag, current_path: List[str]) -> None:
        # Iterate over DT tags which are direct children (conceptually)
        # BeautifulSoup might verify strict nesting, but Netscape format is loose.
        # Often DTs are not closed. BS4 usually handles this by making them siblings or nested.
        # In many Netscape parsers, we look for DTs.
        
        # Robust strategy: Find all descendant DTs whose nearest DL ancestor is this dl_tag.
        all_dts = dl_tag.find_all("dt")
        dts = [dt for dt in all_dts if dt.find_parent("dl") == dl_tag]
        
        for dt in dts:
            # Check for Folder (H3)
            h3 = dt.find("h3", recursive=False)
            if h3:
                folder_name = h3.get_text(strip=True)
                new_path = current_path + [folder_name]
                
                # The content of the folder is in the next sibling DL
                # However, BS4 might put the DL *inside* the DT or as a sibling depending on parser.
                # In standard Netscape, it's a sibling of DT usually, or DT is unclosed.
                # Let's check sibling first.
                next_dl = dt.find_next_sibling("dl")
                if next_dl and isinstance(next_dl, bs4.element.Tag):
                     process_dl(next_dl, new_path)
                else:
                    # Sometimes BS4 parses it nested if the HTML was interpreted that way
                    nested_dl = dt.find("dl", recursive=False)
                    if nested_dl and isinstance(nested_dl, bs4.element.Tag):
                        process_dl(nested_dl, new_path)
                continue

            # Check for Bookmark (A)
            a_tag = dt.find("a", recursive=False)
            if a_tag and isinstance(a_tag, bs4.element.Tag):
                url_val = a_tag.get("href")
                if not url_val:
                    continue
                url = str(url_val)
                
                title = a_tag.get_text(strip=True)
                add_date_str = a_tag.get("add_date")
                icon_val = a_tag.get("icon")
                icon = str(icon_val) if icon_val else None
                
                # Parse Date
                date_added = datetime.now(timezone.utc)
                if add_date_str:
                    try:
                        # Netscape format is usually Unix timestamp
                        timestamp = float(str(add_date_str))
                        date_added = datetime.fromtimestamp(timestamp, tz=timezone.utc)
                    except ValueError:
                        pass # Keep default now()
                
                bookmarks.append(Bookmark(
                    url=url,
                    title=title,
                    folder="/".join(current_path),
                    date_added=date_added,
                    icon=icon
                ))

    # Start with the top-level DL
    # Usually there is one main DL.
    root_dl = soup.find("dl")
    if root_dl and isinstance(root_dl, bs4.element.Tag):
        process_dl(root_dl, [])
    else:
        # Fallback: simple scan for all A tags if structure is completely broken
        # but the requirements imply we need folder path, so structure matters.
        # If no DL found, maybe it's just a list of links?
        for a_tag in soup.find_all("a"):
            if isinstance(a_tag, bs4.element.Tag):
                url_val = a_tag.get("href")
                if url_val:
                    title = a_tag.get_text(strip=True)
                    bookmarks.append(Bookmark(
                        url=str(url_val),
                        title=title,
                        folder="",
                        date_added=datetime.now(timezone.utc)
                    ))

    return bookmarks

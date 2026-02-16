import pytest
from datetime import datetime, timezone
from app.storage.duckdb_store import DuckDBStore
from app.storage.base import Chunk

# Use in-memory DB for tests
TEST_DB_PATH = ":memory:"

@pytest.fixture
def store():
    store = DuckDBStore(db_path=TEST_DB_PATH)
    # Ensure schema is applied
    store.initialize()
    return store

def test_upsert_bookmark(store):
    url = "https://example.com"
    title = "Example"
    folder = "Tech"
    date_added = datetime.now(timezone.utc)
    domain = "example.com"
    status = "pending"

    # Insert
    store.upsert_bookmark(url, title, folder, date_added, domain, status)
    
    # Verify
    bookmark = store.get_by_url(url)
    assert bookmark is not None
    assert bookmark["url"] == url
    assert bookmark["title"] == title
    assert bookmark["status"] == status

    # Update (Upsert)
    store.upsert_bookmark(url, "New Title", folder, date_added, domain, "processed")
    bookmark = store.get_by_url(url)
    assert bookmark["title"] == "New Title"
    assert bookmark["status"] == "processed"

def test_store_chunks(store):
    url = "https://example.com"
    store.upsert_bookmark(url, "Title", "Folder", datetime.now(timezone.utc), "domain", "processed")
    
    chunks = [
        Chunk(
            text="Chunk 1 text",
            chunk_index=0,
            start_char_idx=0,
            end_char_idx=10,
            chunk_id="c1",
            bookmark_url=url,
            embedding=[0.1] * 384
        ),
        Chunk(
            text="Chunk 2 text",
            chunk_index=1,
            start_char_idx=11,
            end_char_idx=20,
            chunk_id="c2",
            bookmark_url=url,
            embedding=[0.2] * 384
        )
    ]
    
    store.store_chunks(chunks)
    
    # Verify we can retrieve chunks (though we haven't implemented get_chunks yet, 
    # we can use raw query or search if implemented, or check count)
    # The interface BaseStorage doesn't enforce get_chunks_by_url, but useful for testing.
    # Let's inspect DB directly via store.conn
    
    result = store.conn.execute("SELECT count(*) FROM chunks WHERE bookmark_url = ?", [url]).fetchone()
    assert result[0] == 2

def test_list_all_urls(store):
    store.upsert_bookmark("https://a.com", "A", "", datetime.now(timezone.utc), "a.com", "pending")
    store.upsert_bookmark("https://b.com", "B", "", datetime.now(timezone.utc), "b.com", "pending")
    
    urls = store.list_all_urls()
    assert len(urls) == 2
    assert "https://a.com" in urls
    assert "https://b.com" in urls

def test_get_nonexistent_bookmark(store):
    assert store.get_by_url("https://nowhere.com") is None

def test_search_basic(store):
    # Setup
    url1 = "https://a.com"
    store.upsert_bookmark(url1, "A", "Tech", datetime.now(timezone.utc), "a.com", "processed")
    store.store_chunks([
        Chunk(
            text="Python is great",
            chunk_index=0,
            start_char_idx=0,
            end_char_idx=10,
            chunk_id="c1",
            bookmark_url=url1,
            embedding=[1.0] + [0.0] * 383
        )
    ])

    url2 = "https://b.com"
    store.upsert_bookmark(url2, "B", "Food", datetime.now(timezone.utc), "b.com", "processed")
    store.store_chunks([
        Chunk(
            text="Pizza is good",
            chunk_index=0,
            start_char_idx=0,
            end_char_idx=10,
            chunk_id="c2",
            bookmark_url=url2,
            embedding=[0.0] + [1.0] + [0.0] * 382
        )
    ])

    # Search for "Python" (close to c1)
    query_emb = [1.0] + [0.0] * 383
    results = store.search(query_emb, k=1)
    
    assert len(results) == 1
    assert results[0].metadata["url"] == url1
    assert results[0].text == "Python is great"
    # Similarity should be 1.0 (cosine of same vector)
    assert results[0].score > 0.99

def test_search_filters_folder(store):
    # Setup
    url1 = "https://a.com"
    store.upsert_bookmark(url1, "A", "Tech", datetime.now(timezone.utc), "a.com", "processed")
    store.store_chunks([
        Chunk(
            text="Tech stuff",
            chunk_index=0,
            start_char_idx=0,
            end_char_idx=10,
            chunk_id="c1",
            bookmark_url=url1,
            embedding=[0.1] * 384
        )
    ])
    
    url2 = "https://b.com"
    store.upsert_bookmark(url2, "B", "Food", datetime.now(timezone.utc), "b.com", "processed")
    store.store_chunks([
        Chunk(
            text="Food stuff",
            chunk_index=0,
            start_char_idx=0,
            end_char_idx=10,
            chunk_id="c2",
            bookmark_url=url2,
            embedding=[0.1] * 384 # Same embedding to force filter usage
        )
    ])

    # Search with folder filter
    results = store.search([0.1] * 384, k=10, filters={"folder": "Food"})
    assert len(results) == 1
    assert results[0].metadata["url"] == url2

def test_search_filters_date(store):
    d1 = datetime(2023, 1, 1, tzinfo=timezone.utc)
    d2 = datetime(2024, 1, 1, tzinfo=timezone.utc)
    
    store.upsert_bookmark("https://old.com", "Old", "", d1, "old.com", "processed")
    store.store_chunks([Chunk("c1", "https://old.com", "t1", 0, [0.1]*384)])
    
    store.upsert_bookmark("https://new.com", "New", "", d2, "new.com", "processed")
    store.store_chunks([Chunk("c2", "https://new.com", "t2", 0, [0.1]*384)])
    
    # Filter for > 2023-06
    results = store.search([0.1]*384, k=10, filters={"date_from": datetime(2023, 6, 1, tzinfo=timezone.utc)})
    assert len(results) == 1
    assert results[0].metadata["url"] == "https://new.com"
    
    # Filter for < 2023-06
    results = store.search([0.1]*384, k=10, filters={"date_to": datetime(2023, 6, 1, tzinfo=timezone.utc)})
    assert len(results) == 1
    assert results[0].metadata["url"] == "https://old.com"

def test_search_no_results(store):
    results = store.search([0.1]*384, k=1)
    assert len(results) == 0

CREATE TABLE IF NOT EXISTS bookmarks (
    url TEXT PRIMARY KEY,
    title TEXT,
    folder TEXT,
    date_added TIMESTAMP,
    domain TEXT,
    status TEXT, -- 'pending', 'processed', 'failed'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chunks (
    chunk_id TEXT PRIMARY KEY,
    bookmark_url TEXT REFERENCES bookmarks(url),
    chunk_text TEXT,
    chunk_index INTEGER,
    embedding FLOAT[384]
);

-- Index for vector search (if supported by extension, else linear scan is fine for small dataset)
-- DuckDB's native vector support is evolving. For now, we store as array.

import duckdb
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.storage.base import BaseStorage, Chunk, RetrievedChunk
import os

class DuckDBStore(BaseStorage):
    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self.conn = duckdb.connect(db_path)
        
    def initialize(self) -> None:
        """
        Apply schema.
        """
        # Load schema from SQL file
        # Assuming schema.sql is in the same directory as this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        schema_path = os.path.join(current_dir, "schema.sql")
        
        with open(schema_path, "r") as f:
            schema_sql = f.read()
            
        self.conn.execute(schema_sql)

    def upsert_bookmark(self, url: str, title: str, folder: str, 
                        date_added: datetime, domain: str, status: str) -> None:
        """
        Insert or update bookmark metadata.
        """
        query = """
        INSERT INTO bookmarks (url, title, folder, date_added, domain, status, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, now())
        ON CONFLICT (url) DO UPDATE SET
            title = EXCLUDED.title,
            folder = EXCLUDED.folder,
            date_added = EXCLUDED.date_added,
            domain = EXCLUDED.domain,
            status = EXCLUDED.status,
            updated_at = now()
        """
        self.conn.execute(query, [url, title, folder, date_added, domain, status])

    def store_chunks(self, chunks: List[Chunk]) -> None:
        """
        Store embedded chunks for a bookmark.
        First delete existing chunks for this bookmark to avoid duplicates if re-ingesting.
        """
        if not chunks:
            return
            
        bookmark_url = chunks[0].bookmark_url
        
        # Transaction
        self.conn.begin()
        try:
            self.conn.execute("DELETE FROM chunks WHERE bookmark_url = ?", [bookmark_url])
            
            insert_query = """
            INSERT INTO chunks (chunk_id, bookmark_url, chunk_text, chunk_index, embedding)
            VALUES (?, ?, ?, ?, ?)
            """
            
            # Use explicit list comprehension with types
            data = [
                (c.chunk_id, c.bookmark_url, c.text, c.chunk_index, c.embedding)
                for c in chunks
            ]
            
            self.conn.executemany(insert_query, data)
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e

    def get_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve bookmark metadata by URL.
        """
        result = self.conn.execute("SELECT * FROM bookmarks WHERE url = ?", [url]).fetchone()
        if not result:
            return None
            
        # Map tuple to dict based on schema columns
        columns = ["url", "title", "folder", "date_added", "domain", "status", "created_at", "updated_at"]
        return dict(zip(columns, result))

    def list_all_urls(self) -> List[str]:
        """
        List all bookmark URLs currently in the store.
        """
        result = self.conn.execute("SELECT url FROM bookmarks").fetchall()
        return [str(row[0]) for row in result]

    def search(self, query_embedding: List[float], k: int, 
               filters: Optional[Dict[str, Any]] = None) -> List[RetrievedChunk]:
        """
        Perform vector similarity search using cosine similarity.
        """
        where_clauses: List[str] = []
        params: List[Any] = []
        
        # Add vector param first for similarity calc if we use it in SELECT
        # DuckDB requires casting the parameter to the correct vector type
        
        base_query = """
        SELECT 
            c.chunk_text, 
            array_cosine_similarity(c.embedding, ?::FLOAT[384]) as score,
            b.url, b.title, b.folder, b.date_added, b.domain
        FROM chunks c
        JOIN bookmarks b ON c.bookmark_url = b.url
        """
        params.append(query_embedding)
        
        if filters:
            if "folder" in filters:
                where_clauses.append("b.folder = ?")
                params.append(filters["folder"])
            if "domain" in filters:
                where_clauses.append("b.domain = ?")
                params.append(filters["domain"])
            if "date_from" in filters:
                where_clauses.append("b.date_added >= ?")
                params.append(filters["date_from"])
            if "date_to" in filters:
                where_clauses.append("b.date_added <= ?")
                params.append(filters["date_to"])

        if where_clauses:
            base_query += " WHERE " + " AND ".join(where_clauses)
        
        base_query += " ORDER BY score DESC LIMIT ?"
        params.append(k)
        
        # Use fetchall to get list of tuples
        cursor = self.conn.execute(base_query, params)
        results = cursor.fetchall()
        
        retrieved: List[RetrievedChunk] = []
        for row in results:
            # row is tuple
            retrieved.append(RetrievedChunk(
                text=str(row[0]),
                score=float(row[1]),
                metadata={
                    "url": str(row[2]),
                    "title": str(row[3]),
                    "folder": str(row[4]),
                    "date_added": row[5], # datetime
                    "domain": str(row[6])
                }
            ))
            
        return retrieved

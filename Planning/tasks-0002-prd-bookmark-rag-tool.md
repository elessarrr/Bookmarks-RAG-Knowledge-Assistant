# Task List: Bookmark RAG Tool
**PRD Reference:** `0002-prd-bookmark-rag-tool.md`
**Target Reader:** Junior developer implementing a greenfield Python project

---

## Implementation Notes

> **Read these before writing any code.**

1. **TDD Order:** Always write the test file before the implementation file. Each sub-task that says "write unit tests first" must be completed before its paired implementation sub-task.

2. **Adapter Pattern:** Never call `SentenceTransformer` or `httpx` (for Ollama) directly from pipeline or route files. Always go through the abstract base class interface. This is what makes the project credible to senior engineers.

3. **Error Handling Philosophy:** Ingestion failures should never crash the pipeline. Every fetch/parse/embed step should catch exceptions, log them as structured JSON, and continue to the next bookmark.

4. **Config > Code:** Any value that might change between environments (model names, file paths, K value) must live in `config.yaml`. No magic strings in source files.

5. **Eval First Mentality:** Build the synthetic Q&A dataset (`evals/dataset/qa_pairs.json`) before running the RAG pipeline. This forces you to think about what "good retrieval" means before you write retrieval code.

6. **Demo-Ready Checkpoints:** After completing Task 2.0, the ingestion pipeline should be demoed independently (CLI script). After Task 3.0, the RAG query should work end-to-end from the terminal. The web UI (Task 4.0) wraps working back-end code, not the other way around.

---

## Relevant Files

### Core Application
- `app/main.py` - FastAPI app entry point, route registration
- `app/config.py` - YAML config loader; defines all swappable components (embedding model, vector DB, LLM)
- `config.yaml` - Default configuration file (model names, K value, chunk size, DB path)

### Ingestion Pipeline
- `app/ingestion/parser.py` - Parses Chrome/Firefox/Safari bookmark HTML exports into structured data
- `app/ingestion/parser.test.py` - Unit tests for bookmark HTML parsing
- `app/ingestion/fetcher.py` - Fetches full-text content from URLs; handles errors, dead links, robots.txt
- `app/ingestion/fetcher.test.py` - Unit tests for URL fetching and error handling
- `app/ingestion/cleaner.py` - Strips HTML boilerplate (nav, ads) using Readability; extracts main article text
- `app/ingestion/cleaner.test.py` - Unit tests for HTML cleaning
- `app/ingestion/chunker.py` - Sentence-aware text chunking (200-500 tokens, configurable)
- `app/ingestion/chunker.test.py` - Unit tests for chunking logic (edge cases: short text, no sentence boundaries)
- `app/ingestion/pipeline.py` - Orchestrates full ingestion: parse → fetch → clean → chunk → embed → store
- `app/ingestion/pipeline.test.py` - Integration tests for end-to-end ingestion

### Embedding & Storage
- `app/embeddings/base.py` - Abstract base class (interface) for embedding models
- `app/embeddings/local_embedder.py` - sentence-transformers implementation (`all-MiniLM-L6-v2`)
- `app/embeddings/openai_embedder.py` - OpenAI embeddings implementation (cloud swap)
- `app/embeddings/local_embedder.test.py` - Unit tests for embedding generation and batching
- `app/storage/base.py` - Abstract base class (interface) for vector stores
- `app/storage/duckdb_store.py` - DuckDB vector store implementation with cosine similarity search
- `app/storage/duckdb_store.test.py` - Unit tests for storage, retrieval, and metadata filtering
- `app/storage/schema.sql` - DuckDB schema definition (bookmarks table, chunks table, embeddings)

### RAG Query Pipeline
- `app/rag/retriever.py` - Embeds query, runs similarity search, applies metadata filters (folder, date, domain)
- `app/rag/retriever.test.py` - Unit tests for retrieval and all metadata filter combinations
- `app/rag/llm/base.py` - Abstract base class (interface) for LLM providers
- `app/rag/llm/ollama_llm.py` - Ollama LLM implementation (local inference)
- `app/rag/llm/openai_llm.py` - OpenAI LLM implementation (cloud swap)
- `app/rag/llm/ollama_llm.test.py` - Unit tests for LLM integration (mock Ollama responses)
- `app/rag/generator.py` - Builds prompt from query + retrieved chunks; calls LLM; parses citations
- `app/rag/generator.test.py` - Unit tests for prompt construction and citation parsing
- `app/rag/conversation.py` - Maintains multi-turn conversation context (last N turns)
- `app/rag/pipeline.py` - Orchestrates full RAG query: embed → retrieve → generate → respond
- `app/rag/pipeline.test.py` - Integration tests for end-to-end RAG query flow

### Web Interface
- `app/routes/ingest.py` - FastAPI routes: POST /upload, GET /ingest-status, POST /refresh
- `app/routes/query.py` - FastAPI routes: POST /query, GET /stats
- `app/routes/settings.py` - FastAPI routes: GET/POST /settings
- `static/index.html` - Main chat interface (query input, answer display, citations panel)
- `static/upload.html` - Bookmark upload page (drag-and-drop HTML file)
- `static/settings.html` - Settings page (K value, chunk size, model selection)
- `static/css/style.css` - Minimal stylesheet (Hacker News-inspired aesthetic)
- `static/js/app.js` - Vanilla JS for chat interactions, progress polling, htmx fallback

### Evaluation Framework
- `evals/dataset/qa_pairs.json` - Synthetic Q&A dataset (20-30 pairs with ground-truth bookmark refs)
- `evals/dataset/generate_dataset.py` - Script to generate/expand synthetic Q&A pairs
- `evals/metrics/retrieval.py` - Precision@K, Recall, MRR implementations
- `evals/metrics/retrieval.test.py` - Unit tests for metric calculations
- `evals/metrics/answer_quality.py` - Faithfulness and answer relevance metrics (RAGAS integration)
- `evals/metrics/answer_quality.test.py` - Unit tests for answer quality metrics
- `evals/run_evals.py` - Runs full eval suite; logs results to JSON; enforces pass/fail thresholds
- `evals/results/` - Directory for eval run logs (gitignored except `.gitkeep`)

### Project Config & Infra
- `pyproject.toml` - Project metadata, dependencies (replaces setup.py + requirements.txt)
- `requirements.txt` - Pinned dependencies for reproducibility
- `requirements-dev.txt` - Dev dependencies (pytest, mypy, ruff, coverage)
- `.env.example` - Example environment variables (Ollama URL, OpenAI key placeholder)
- `Dockerfile` - Container definition for the FastAPI app
- `docker-compose.yml` - Orchestrates app + Ollama service for one-command local setup
- `run.py` - Simple entry point: `python run.py` starts the app without Docker

### Documentation
- `README.md` - Setup guide, architecture overview, demo GIF, quick-start commands
- `docs/architecture.md` - Component diagram, adapter pattern explanation, extension guide
- `docs/eval-methodology.md` - Explains RAG eval approach, metrics, and how to add test cases
- `docs/extending.md` - How to connect Notion, Confluence, Obsidian as alternative data sources

### Notes
- Unit tests are co-located with source files (e.g., `parser.py` and `parser.test.py` in same directory)
- Run all tests: `pytest` from project root
- Run with coverage: `pytest --cov=app --cov-report=term-missing`
- Run evals only: `pytest evals/`
- Type checking: `mypy app/ --strict`
- Linting: `ruff check app/`

---

## Tasks

- [x] 1.0 Project Setup & Architecture Scaffolding
  - [x] 1.1 Initialise Git repo with MIT licence, `.gitignore` (Python, `.env`, `evals/results/*.json`, DuckDB files), and empty `README.md`
  - [x] 1.2 Create project folder structure: `app/ingestion/`, `app/embeddings/`, `app/storage/`, `app/rag/llm/`, `app/routes/`, `static/css/`, `static/js/`, `evals/dataset/`, `evals/metrics/`, `evals/results/`, `docs/`
  - [x] 1.3 Create `pyproject.toml` with project metadata and all dependencies: `fastapi`, `uvicorn`, `duckdb`, `sentence-transformers`, `beautifulsoup4`, `readability-lxml`, `requests`, `httpx`, `pyyaml`, `ragas`, `pytest`, `mypy`, `ruff`, `pytest-cov`
  - [x] 1.4 Create `config.yaml` with all configurable settings: embedding model name (`all-MiniLM-L6-v2`), chunk size (400 tokens), chunk overlap (50 tokens), top-K (5), Ollama base URL (`http://localhost:11434`), DuckDB file path (`./data/bookmarks.duckdb`), LLM model name (`llama3.2:3b`)
  - [x] 1.5 Create `app/config.py` that loads `config.yaml` and exposes a typed `Settings` dataclass; validate required fields on startup
  - [x] 1.6 Write abstract base classes (`app/embeddings/base.py`, `app/storage/base.py`, `app/rag/llm/base.py`) defining the interfaces all concrete implementations must satisfy
  - [x] 1.7 Create `app/main.py`: initialise FastAPI app, load config, wire up dependency injection (instantiate correct embedder/store/llm based on config), register routes
  - [x] 1.8 Create `.env.example` with placeholder values for `OPENAI_API_KEY`, `OLLAMA_BASE_URL`
  - [x] 1.9 Create `run.py` as simple entry point: loads `.env`, calls `uvicorn.run("app.main:app", reload=True)`
  - [x] 1.10 Verify project runs (`python run.py`) and returns 200 on `GET /health` before proceeding
  
- [x] 2.0 Data Ingestion Pipeline
  - [x] 2.1 Write unit tests first (`app/ingestion/parser.test.py`) for bookmark HTML parsing: test Chrome export format, Firefox export format, nested folders, missing date fields, duplicate URLs
  - [x] 2.2 Implement `app/ingestion/parser.py`: use `BeautifulSoup` to parse bookmark HTML; extract URL, title, folder path (from `<DL>` hierarchy), date added (Unix timestamp → ISO datetime), favicon URL; return list of `Bookmark` dataclass objects
  - [x] 2.3 Write unit tests first (`app/ingestion/fetcher.test.py`): test successful fetch, HTTP 404, timeout, robots.txt block, non-HTML content type (PDF, image)
  - [x] 2.4 Implement `app/ingestion/fetcher.py`: use `httpx` with 10s timeout; check `robots.txt` before fetching; handle exceptions and return typed `FetchResult` (success/failure + reason); respect rate limiting with 0.5s delay between requests
  - [x] 2.5 Write unit tests first (`app/ingestion/cleaner.test.py`): test that nav/footer/ads are stripped, main article body is preserved, empty content returns None
  - [x] 2.6 Implement `app/ingestion/cleaner.py`: use `readability-lxml` to extract main content; strip remaining HTML tags; normalise whitespace; return plain text string or None if content too short (<100 chars)
  - [x] 2.7 Write unit tests first (`app/ingestion/chunker.test.py`): test chunk size respects token limit, no mid-sentence splits, overlap is correct, short texts produce single chunk, empty text returns empty list
  - [x] 2.8 Implement `app/ingestion/chunker.py`: use `nltk.sent_tokenize` for sentence boundaries; accumulate sentences until token count reaches chunk size; apply configurable overlap; return list of `Chunk` dataclass objects with chunk text and position metadata
  - [x] 2.9 Implement `app/storage/schema.sql` and `app/storage/duckdb_store.py`: create `bookmarks` table (url, title, folder, date_added, domain, status) and `chunks` table (chunk_id, bookmark_url, chunk_text, chunk_index, embedding FLOAT[384]); implement `upsert_bookmark()`, `store_chunks()`, `get_by_url()`, `list_all_urls()`
  - [x] 2.10 Write unit tests for `duckdb_store.py`: test insert, upsert (no duplicates), retrieve by URL, list all URLs
  - [x] 2.11 Implement `app/ingestion/pipeline.py`: orchestrate parse → deduplicate (skip URLs already in DB) → fetch → clean → chunk → embed → store; yield progress events (current index, total, failed URLs) for SSE streaming
  - [x] 2.12 Write integration test (`app/ingestion/pipeline.test.py`): use 5 real-ish fixture HTML files (stored in `tests/fixtures/`); run full pipeline; assert chunks stored in DB with correct metadata
  
- [x] 3.0 RAG Query Pipeline
  - [x] 3.1 Implement `app/embeddings/local_embedder.py`: wrap `sentence-transformers` `SentenceTransformer` class; implement `embed_single(text)` and `embed_batch(texts)` methods; load model once at startup (not per request)
  - [x] 3.2 Write unit tests for `local_embedder.py`: test embedding returns correct dimension (384 for MiniLM), batch returns same result as individual, same text always returns same vector
  - [x] 3.3 Implement `app/embeddings/openai_embedder.py`: same interface as local embedder; reads `OPENAI_API_KEY` from env; uses `text-embedding-3-small` model; include as documented cloud-swap option
  - [x] 3.4 Add vector similarity search to `app/storage/duckdb_store.py`: implement `search(query_embedding, k, filters)` using DuckDB's `array_cosine_similarity`; support filter parameters: `folder` (exact match), `domain` (exact match), `date_from` / `date_to` (ISO date range)
  - [x] 3.5 Write unit tests for similarity search and all filter combinations: folder filter, domain filter, date range filter, combined filters, K=1 vs K=10
  - [x] 3.6 Implement `app/rag/retriever.py`: take query string + optional filters; embed query; call `duckdb_store.search()`; return list of `RetrievedChunk` objects (chunk text, score, bookmark metadata)
  - [x] 3.7 Write unit tests for `retriever.py`: mock embedder and store; test filter passthrough, correct number of results returned
  - [x] 3.8 Implement `app/rag/engine.py`: orchestrate `retrieve` (vector search) -> `augment` (prompt construction) -> `generate` (LLM call); support both streaming and non-streaming; implement filters (date, folder) support
  - [x] 3.9 Write unit tests for `engine.py`: mock retriever and LLM; test query construction, empty results handling, streaming response pass-through
  
- [x] 4.0 API & Frontend Integration
  - [x] 4.1 Implement `app/routes/ingest.py`: `POST /upload` accepts multipart bookmark HTML file; triggers pipeline as background task; returns `task_id`. `GET /ingest-status?task_id=` returns SSE stream of progress events (processed, total, failed).
  - [x] 4.2 Implement `app/routes/query.py`: `POST /query` accepts `{question, filters, conversation_id}`; runs RAG pipeline; returns `{answer, citations, retrieved_chunks}`. `GET /stats` returns `{total_bookmarks, total_chunks, db_size_mb, failed_bookmarks}`
  - [x] 4.3 Integrate routes into `app/main.py`: setup CORS, include routers, initialize global dependencies (store, embedder, LLM) on startup
  - [x] 4.4 Frontend: Create `frontend/` directory (React/Vite); implement "Upload" tab (file picker, progress bar); implement "Chat" tab (message history, citation display)
  - [x] 4.5 Build `static/index.html`: (Replaced by React Frontend in `frontend/`)
  - [x] 4.6 Build `static/settings.html`: (Replaced by React Frontend)
  - [x] 4.7 Write `static/css/style.css`: (Replaced by Tailwind in React Frontend)
  - [x] 4.8 Write `static/js/app.js`: (Replaced by React Logic)
  - [x] 4.9 Manual smoke test: upload a real bookmarks.html with 20+ URLs; run 5 queries; verify answers cite correct sources; check stats page shows correct counts

- [x] 5.0 Evaluation Framework & Test Suite
  - [x] 5.1 Create `evals/dataset/qa_pairs.json`: write 25 synthetic Q&A pairs manually; each pair has `question`, `expected_answer_keywords` (list of key terms), `ground_truth_urls` (list of bookmark URLs that should be retrieved), `difficulty` (easy/medium/hard)
  - [x] 5.2 Implement `evals/metrics/retrieval.py`: `precision_at_k(retrieved, gt, k)`, `recall(retrieved, gt)`, `mrr(retrieved, gt)`
  - [x] 5.3 Write unit tests for metrics: test edge cases (empty lists, no matches, perfect matches)
  - [x] 5.4 Implement `evals/metrics/answer_quality.py`: integrate RAGAS library to compute `faithfulness` and `answer_relevance`; handle RAGAS requiring an LLM judge (default to Ollama)
  - [x] 5.5 Unit tests for answer quality: mock RAGAS calls; test wrapper logic
  - [x] 5.6 Implement `evals/run_evals.py`: script that loads dataset, runs pipeline for each Q, computes all metrics, aggregates results (mean scores), and saves JSON report to `evals/results/`
  - [x] 5.7 Create `evals/test_runner.py` to ensure `run_evals` runs without error (mocked)
  - [x] 5.8 Verify overall test coverage: run `pytest --cov=app --cov-report=term-missing`; identify uncovered lines; add targeted tests until coverage exceeds 80% for all core modules
  - [x] 5.9 Run `mypy app/ --strict` and fix all type errors; run `ruff check app/` and fix all linting issues
  - [x] 5.10 Add `evals/results/` to `.gitignore`

- [ ] 6.0 Documentation & Deployment
  - [x] 6.1 Write `README.md`: project overview, setup instructions (uv, npm), configuration guide (.env), usage guide (upload -> chat)
  - [x] 6.2 Write `CONTRIBUTING.md`: dev setup, running tests, running evals
  - [x] 6.3 Write `ARCHITECTURE.md`: high-level diagram (mermaid), component descriptions (ingestion vs query flow), data schema
  - [x] 6.4 Create `Dockerfile`: base image `python:3.11-slim`; copy project; install dependencies; expose port 8000; default command `python run.py`
  - [x] 6.5 Create `docker-compose.yml`: define two services — `app` (this project's Dockerfile) and `ollama` (official `ollama/ollama` image); mount `./data` volume for DuckDB persistence; add `healthcheck` for both services
  - [ ] 6.6 Record demo GIF: show full flow — upload bookmarks → ingestion progress bar → ask 3 questions with increasing complexity → show citations and sources panel; use a tool like `asciinema` or `Kap`
  - [x] 6.7 Final GitHub repo hygiene: squash/clean commit history; add GitHub Actions CI workflow (`.github/workflows/ci.yml`) running `pytest` + `mypy` + `ruff` on every push



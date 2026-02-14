# PRD: Bookmark RAG Tool

## Introduction/Overview

**Problem:** Knowledge workers save hundreds of bookmarks but rarely revisit them. We bookmark articles, research papers, and documentation with good intentions, but they become digital hoarding—a graveyard of unread URLs. When we need that information later, we can't remember what we saved or where to find it.

**Solution:** A privacy-first RAG (Retrieval Augmented Generation) chatbot that ingests browser bookmarks, creates a searchable knowledge base, and lets users query their saved content in natural language. Unlike cloud-based tools, all processing happens locally—bookmarks never leave the user's machine.

**Goal:** Build an open-source portfolio project that demonstrates production-grade AI product thinking: rigorous evaluation frameworks, test-driven development, and architecture patterns that scale from consumer apps to enterprise knowledge management systems.

---

## Goals

1. **Demonstrate Senior PM/Director Competence:** Showcase end-to-end AI product development including data ingestion, RAG pipeline, evaluation frameworks, and user-facing interface
2. **Privacy-First Architecture:** All embeddings, vector storage, and LLM inference run locally—zero cloud dependencies for core functionality
3. **Eval-Driven Development:** Implement automated testing for RAG quality (retrieval precision/recall, answer faithfulness) using industry-standard frameworks
4. **Open Source Credibility:** Create GitHub repo positioned as "consumer use case demonstrating enterprise-relevant patterns" with comprehensive documentation
5. **Extensibility:** Design architecture to easily swap local models for cloud services (OpenAI, Pinecone) via configuration, not code changes

---

## User Stories

**As a knowledge worker**, I want to upload my browser bookmarks so that I can search through content I've saved but never read.

**As a privacy-conscious user**, I want all processing to happen locally so that my bookmarked URLs and their content never leave my machine.

**As a researcher**, I want to ask questions like "What did I save about RAG evaluation methods?" and get answers grounded in my actual saved articles, not generic web search results.

**As a developer evaluating this project**, I want to see automated tests proving the RAG pipeline works correctly so that I trust the implementation quality.

**As a hiring manager**, I want to see architecture patterns that generalize beyond bookmarks (Confluence, Notion, internal docs) so that I know this person can build enterprise-grade knowledge systems.

---

## Functional Requirements

### 1. Data Ingestion

1.1. System **must** accept browser bookmark exports in standard HTML format (Chrome, Firefox, Safari)

1.2. System **must** parse bookmark HTML to extract:
- URL
- Title
- Folder hierarchy (tags/categories)
- Date added (if available)
- Favicon URL (optional, for UI)

1.3. System **must** fetch full-text content from each URL using web scraping/parsing libraries

1.4. System **must** handle ingestion failures gracefully (dead links, paywall content, robots.txt blocks) and log skipped URLs

1.5. System **should** deduplicate bookmarks by URL before processing

1.6. System **should** support incremental updates (re-import bookmarks.html without reprocessing unchanged URLs)

### 2. Text Processing & Embedding

2.1. System **must** clean fetched HTML content (strip navigation, ads, boilerplate) to extract main article text

2.2. System **must** chunk text into semantically meaningful segments (200-500 tokens per chunk, configurable)

2.3. System **must** use sentence-aware chunking (don't split mid-sentence)

2.4. System **must** generate embeddings using local open-source model (e.g., `sentence-transformers/all-MiniLM-L6-v2`)

2.5. System **must** store embeddings alongside metadata (URL, title, folder, date, chunk text) in SQLite database with vector extension (e.g., sqlite-vss or DuckDB with vector support)

2.6. System **should** batch embedding generation for efficiency (process N chunks at once)

### 3. RAG Query Pipeline

3.1. System **must** accept natural language queries from users via web interface

3.2. System **must** embed user query using same model as document chunks

3.3. System **must** retrieve top-K most similar chunks using cosine similarity search (K configurable, default K=5)

3.4. System **must** include metadata filters in retrieval:
- Filter by bookmark folder/tag
- Filter by date range (bookmarks saved between X and Y)
- Filter by domain (e.g., only arxiv.org papers)

3.5. System **must** pass retrieved chunks + query to local LLM (e.g., Llama-3.2-3B-Instruct via llama.cpp or Ollama)

3.6. System **must** display LLM-generated answer with inline citations showing which bookmarks contributed to the response

3.7. System **should** show retrieved chunks alongside answer for transparency (user can verify LLM didn't hallucinate)

3.8. System **should** support follow-up questions (maintain conversation context for multi-turn dialogue)

### 4. Evaluation Framework

4.1. System **must** implement retrieval metrics:
- Precision@K: Of K retrieved chunks, how many are relevant?
- Recall: What fraction of relevant chunks were retrieved?
- MRR (Mean Reciprocal Rank): Position of first relevant result

4.2. System **must** implement answer quality metrics:
- Faithfulness: Is LLM answer grounded in retrieved context (not hallucinated)?
- Answer relevance: Does answer address the user's query?

4.3. System **must** include synthetic Q&A test dataset (20-30 question/answer pairs with ground-truth bookmark references)

4.4. System **must** run evals automatically via test suite (`pytest`) with pass/fail thresholds

4.5. System **should** use open-source eval frameworks (e.g., RAGAS, TruLens) for standardized metrics

4.6. System **should** log eval results to track regression between code changes

### 5. User Interface

5.1. System **must** provide web interface (Flask/FastAPI + vanilla HTML/CSS/JS, no frontend frameworks)

5.2. Interface **must** include:
- Bookmark upload page (drag-drop HTML file)
- Chat interface for querying knowledge base
- Display of retrieved chunks + citations
- Settings page (configure K, chunk size, model selection)

5.3. Interface **should** show ingestion progress (X of Y URLs processed, N failed)

5.4. Interface **should** display statistics (total bookmarks, chunks, storage size)

5.5. Interface **should** allow users to re-fetch content for stale bookmarks (refresh button)

### 6. Test-Driven Development

6.1. System **must** include unit tests for:
- Bookmark HTML parsing
- Text chunking logic
- Embedding generation
- Similarity search
- Metadata filtering

6.2. System **must** include integration tests for:
- End-to-end ingestion pipeline
- RAG query flow (query → retrieval → LLM → response)

6.3. System **must** achieve >80% code coverage for core modules

6.4. System **must** use pytest as test framework with clear test names and docstrings

### 7. Architecture & Extensibility

7.1. System **must** use dependency injection / adapter pattern for:
- Embedding model (easy swap from sentence-transformers to OpenAI)
- Vector database (easy swap from SQLite to Pinecone/Weaviate)
- LLM provider (easy swap from local Llama to GPT-4)

7.2. System **must** define configuration file (YAML/JSON) for all swappable components

7.3. System **should** include architectural diagrams in docs showing component boundaries

7.4. System **should** document how to extend to other content sources (Notion exports, Confluence pages, Obsidian vaults)

---

## Non-Goals (Out of Scope)

1. **Browser Extension (V1):** Initial version uses manual bookmark export. Extension for one-click saving is future work.

2. **Multi-User Support:** V1 is single-user, local-only. Cloud deployment with auth is out of scope.

3. **Real-Time Sync:** No automatic monitoring of browser bookmarks. User manually triggers re-import.

4. **Advanced Reranking:** No cross-encoder reranking or hybrid search (keyword + semantic). Keep retrieval simple for V1.

5. **Custom Fine-Tuning:** Use off-the-shelf models. No fine-tuning on user's bookmark corpus.

6. **Mobile App:** Web interface only. Responsive design optional.

7. **Paywall Bypass:** If bookmark URL requires login/subscription, skip it. No circumvention mechanisms.

---

## Design Considerations

### UI/UX Requirements

- **Minimalist Interface:** Focus on functionality over polish. Clean, readable design inspired by Hacker News aesthetics.
- **No JavaScript Frameworks:** Vanilla JS or minimal libraries (htmx for dynamic updates). Avoid React/Vue complexity.
- **Mobile-Responsive (Nice-to-Have):** Basic responsive CSS so it works on tablets, but not a requirement.

### Visual Mockups

None provided. Developer has creative freedom within constraints above.

---

## Technical Considerations

### Tech Stack

**Backend:**
- Python 3.11+
- FastAPI (web framework)
- SQLite + sqlite-vss or DuckDB (vector storage)
- sentence-transformers (embedding model)
- llama-cpp-python or Ollama (local LLM inference)
- BeautifulSoup4 / Readability (HTML parsing)
- pytest (testing)
- RAGAS or TruLens (RAG evaluation)

**Frontend:**
- Vanilla HTML/CSS/JavaScript
- Optional: htmx for AJAX interactions
- Plotly.js for eval metric visualizations (optional)

### Key Architecture Patterns

1. **Adapter Pattern:** Abstract embedding, vector DB, and LLM behind interfaces so implementations are swappable
2. **Repository Pattern:** Separate data access logic (SQLite queries) from business logic
3. **Pipeline Pattern:** Ingestion as series of stages (fetch → parse → chunk → embed → store) with error handling at each stage

### Dependencies

- Minimize external services. Core functionality runs offline.
- If user wants cloud models (OpenAI embeddings, GPT-4), they configure API keys but system defaults to local-first.

### Constraints

- **Disk Space:** Embedding a large bookmark collection (1000+ URLs) can consume 500MB-1GB. Document storage requirements.
- **RAM:** Running local LLM (3B params) needs ~4-6GB RAM. Provide fallback (smaller model or prompt user to configure cloud LLM).
- **Processing Time:** Initial ingestion for 500 bookmarks may take 10-30 minutes. Show progress bar.

---

## Success Metrics

### Product Metrics (If Deployed to Users)

- **Engagement:** % of users who query knowledge base after ingestion (target: >60%)
- **Retention:** Users who re-import bookmarks weekly (target: >30% after 1 month)
- **Quality:** User satisfaction with answer relevance (survey: 4+/5 stars)

### Portfolio/Demo Metrics

- **GitHub Stars:** 50+ stars within 3 months (signals community validation)
- **Documentation Quality:** README walkthrough completable by junior dev in <30 minutes
- **Eval Pass Rate:** Automated test suite passes with >85% precision/recall on synthetic dataset
- **Code Quality:** Pylint/Ruff score >8.5/10, 100% type hints with mypy

### Hiring Signal Metrics (Qualitative)

- **Recruiter Feedback:** "This shows you can build end-to-end AI products, not just run notebooks"
- **Interview Questions Avoided:** Interviewers skip basic "explain RAG" questions, dive straight into architecture trade-offs
- **Credibility Boost:** LinkedIn profile views increase 20%+ after adding project to portfolio

---

## Success Criteria (Launch Readiness)

### Minimum Viable Product (V1)

- [ ] User can upload bookmarks.html and see ingestion progress
- [ ] System fetches, chunks, embeds, and stores at least 100 URLs successfully
- [ ] User can query knowledge base and receive LLM-generated answers with citations
- [ ] Automated eval suite runs and passes (>75% precision/recall on test set)
- [ ] README includes: architecture diagram, setup instructions, demo GIF
- [ ] Code coverage >80% for core modules
- [ ] Deployable locally via `docker-compose up` or `python run.py`

### Quality Bar

- [ ] No hardcoded paths (use environment variables / config file)
- [ ] Graceful error handling (no crashes on malformed HTML or dead links)
- [ ] Logs include structured JSON for debugging (timestamp, level, module, message)
- [ ] Type hints on all public functions, passes `mypy --strict`

---

## Open Questions

1. **LLM Choice:** Start with llama.cpp + Llama-3.2-3B-Instruct, or use Ollama for easier setup?
   - **Recommendation:** Ollama (simpler install, better developer experience)

2. **Vector DB:** SQLite + sqlite-vss, or DuckDB with vector extension?
   - **Recommendation:** DuckDB (more performant for analytics queries, easier to scale to Postgres later)

3. **Eval Framework:** RAGAS vs. TruLens vs. custom implementation?
   - **Recommendation:** Start with RAGAS (well-documented, integrates with LangChain ecosystem)

4. **Chunking Strategy:** Fixed-size (500 tokens) or semantic (paragraph boundaries)?
   - **Recommendation:** Semantic chunking (better preserves context, slightly more complex)

5. **Deployment Guide:** Include Docker-only, or also document native Python setup?
   - **Recommendation:** Both. Docker for easy demo, native for developers who want to customize

6. **License:** MIT (permissive) or Apache 2.0 (explicit patent grant)?
   - **Recommendation:** MIT (simpler, more popular for portfolio projects)

---

## Timeline & Milestones

**Phase 1 (Weekend 1):** Core ingestion pipeline
- Bookmark parsing
- URL fetching + text extraction
- Chunking + embedding
- Vector storage

**Phase 2 (Weekend 2):** RAG query + UI
- Query embedding + similarity search
- LLM integration
- Web interface (upload + chat)
- Basic error handling

**Phase 3 (Evenings Week 2-3):** Eval framework + testing
- Synthetic Q&A dataset
- RAGAS integration
- Unit + integration tests
- Documentation

**Phase 4 (Weekend 3):** Polish + launch
- README with demo GIF
- Architecture docs
- Docker setup
- GitHub repo cleanup + release

**Total Estimated Effort:** 40-50 hours over 3 weeks

---

## Appendix: Why This Matters for Senior PM/Director Roles

### Signals Sent to Hiring Managers

1. **End-to-End Ownership:** From product vision (privacy-first knowledge management) to working code, evals, and docs
2. **AI Product Rigor:** Not just "I used ChatGPT API"—shows understanding of RAG architecture, evaluation, and quality tradeoffs
3. **Production Thinking:** TDD, type safety, logging, error handling, extensibility—code that could ship
4. **Strategic Positioning:** Consumer use case generalizes to enterprise (Confluence, Notion, internal wikis)
5. **Open Source Credibility:** Demonstrates ability to build developer-facing products with strong documentation

### Differentiation from "Weekend RAG Tutorial"

| Typical Tutorial | This Project |
|-----------------|-------------|
| Hardcoded OpenAI API | Adapter pattern for local/cloud models |
| "Just run this Jupyter notebook" | Test suite, type hints, logging, Docker |
| No evaluation | RAGAS metrics, synthetic dataset, CI/CD |
| "Here's the code" | Architecture docs explaining design decisions |
| Single data source (PDFs) | Extensible to any text corpus (bookmarks → Notion → wikis) |

---

## Appendix: Future Enhancements (V2+)

- **Browser Extension:** One-click "Save to RAG" button
- **Hybrid Search:** Combine keyword (BM25) + semantic search
- **Reranking:** Use cross-encoder to refine top-K results before LLM
- **Multi-Modal:** Handle bookmarked YouTube videos (transcripts), tweets, PDFs
- **Graph RAG:** Build knowledge graph connecting related bookmarks
- **Collaborative Mode:** Share knowledge base with team (requires auth, cloud storage)
- **Active Learning:** Let users flag bad answers to improve retrieval over time

---

**END OF PRD**

# Bookmarks RAG Knowledge Assistant

> **Turn your browser bookmarks into an interactive, privacy-first knowledge base.**

**Bookmarks RAG Knowledge Assistant** is a local-first **Retrieval-Augmented Generation (RAG)** tool designed to unlock insights from your accumulated browser bookmarks. By ingesting Netscape-format HTML exports (supported by Chrome, Firefox, Safari, Edge), it transforms static links into a queryable vector database, allowing you to chat with your saved content using state-of-the-art local LLMs.

I built this project to solve the "digital hoarding" problem: we all bookmark hundreds of interesting articles, papers, and tools, but we rarely revisit them because searching through a nested folder structure is inefficient. The hypothesis was that a RAG system could surface these forgotten gems by allowing semantic queries like *"What was that article about local-first software architecture?"* rather than forcing you to remember the exact title or folder.

---

## 🏗️ What I Built

*   **Privacy-First Architecture**: Zero data exfiltration. Runs 100% locally using Ollama and local embedding models.
*   **Advanced RAG Pipeline**:
    *   **Smart Ingestion**: Parses and cleans HTML content from bookmarked URLs using `BeautifulSoup` and `readability-lxml`.
    *   **Semantic Chunking**: Intelligently splits content to preserve context for better retrieval.
    *   **Filtered Semantic Search**: Combines exact cosine similarity over embeddings with structured metadata filters.
*   **Local Backend**: Powered by **FastAPI** and **DuckDB** for an in-process, single-user workflow.
*   **Modern Reactive UI**: A polished **React 19** + **Vite** frontend with **Tailwind CSS 4** for seamless bookmark management and chat.
*   **Built-in Evaluation**: Includes a `ragas`-based evaluation framework to benchmark retrieval accuracy and generation quality.
*   **Technical Rigor**: TDD with high test coverage, type-safe Python (mypy), and automated CI pipelines.

---

## � Why I'm Archiving This

While the technology works flawlessly, I am archiving this repository to focus on more impactful solutions.

**The Pivot Insight:**
After building V1 and using it daily, I realized the core user journey is flawed. The friction of *exporting* bookmarks to an HTML file and *uploading* them to a separate tool is too high for casual use. People don't forget bookmarks because they lack a search tool; they forget them because the retrieval mechanism isn't integrated into their daily workflow (the browser itself).

**What I Would Build Instead:**
If I were to restart this project today, I would build a **Browser Extension** that captures context *at the moment of saving*, indexing the page content in the background and offering a "Chat with History" sidebar directly in the browser. This removes the manual export/upload step and integrates the intelligence directly where the user works.

---

## 🧠 What I Learned

*   **DuckDB is a pragmatic prototype store**: Using DuckDB for metadata and exact cosine search simplified the local architecture compared with managing Postgres + pgvector or ChromaDB. The current search is an unindexed linear scan, not a vector-search powerhouse.
*   **The "Context Window" Trap**: Simply retrieving the top-k chunks is not enough for consistently high-quality answers. Re-ranking or hybrid search is a future improvement, not part of the current hot path.
*   **Evaluation is Critical**: Building the `ragas` evaluation pipeline early allowed for objective measurement of how chunking strategy changes affected answer quality.

---

## 🏔️ Challenges & Lessons Learned

### 1. Stale or Dead URLs in Bookmarks
**Challenge:** Bookmarks are often "time capsules"—links saved years ago frequently point to domains that have lapsed, content that has moved, or endpoints returning 404/500 errors.
**Lesson & Mitigation:** Trust but verify. I implemented pre-ingestion checks (HEAD/GET requests) to validate link freshness.
**Insight:** A robust system must surface a "last alive" timestamp to the user so they understand why a specific source was skipped, rather than silently failing.

### 2. robots.txt & Anti-Bot Defenses
**Challenge:** Many high-value sites block automated crawling via `robots.txt` or deploy sophisticated bot-detection (CAPTCHA, IP rate-limiting, JS challenges). Aggressive scraping risks IP bans.
**Lesson & Mitigation:**
*   **Respect Standards:** Explicit `robots.txt` Disallow rules are honored before page content is fetched. If the robots file itself is unreachable, this personal tool allows the URL and logs a warning.
*   **Authentication Walls:** A subset of bookmarks (paywalls, social media) are unreachable by stateless scrapers.
**Insight:** Instead of fighting anti-bot measures, the system should maintain an "allow list" of scrape-friendly domains. When a page is disallowed or gated, it is safer to log the reason and exclude it from the vector index than to risk a block.

### 3. RAG Coverage Ceiling
**Challenge:** The current pipeline is strictly "grounded"—it only answers questions for which relevant bookmarks exist. If the answer isn't in your saved links, it replies "I don't know." While this prevents hallucination, it limits utility.
**Lesson & Roadmap:**
A future iteration would benefit from a **Hybrid Generative Architecture**. This would involve:
1.  Prioritizing bookmark embeddings in the context window.
2.  Falling back to the LLM's general knowledge only when bookmark retrieval confidence is low.
This approach balances personal context with general utility, preventing the "empty response" frustration while maintaining high relevance.

*In summary, this project reinforced the importance of ethical scraping, transparent failure modes, and the need for systems that degrade gracefully when data is imperfect.*

---

## 🛠️ Technology Stack

### Backend (Python)
- **Framework**: `FastAPI` (Async web API), `Uvicorn` (ASGI Server)
- **Database**: `DuckDB` (In-process SQL OLAP & Vector Store)
- **AI & ML**:
    - **LLM Runtime**: `Ollama` (Local Llama 3, Mistral, etc.)
    - **Embeddings**: `sentence-transformers` (Hugging Face), `nomic-embed-text`
- **Data Processing**: `BeautifulSoup4`, `readability-lxml`, `httpx` (Async HTTP)
- **Testing**: `pytest`, `pytest-asyncio`, `pytest-cov`

### Frontend (TypeScript)
- **Core**: `React 19`, `TypeScript`
- **Build Tool**: `Vite`
- **Styling**: `Tailwind CSS 4`, `clsx`, `tailwind-merge`
- **Icons**: `Lucide React`
- **State/Networking**: `Axios`, React Hooks

### DevOps & Infrastructure
- **CI/CD**: `GitHub Actions` (Automated testing & linting)
- **Package Management**: `uv` (Python), `npm` (Node)

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+ (for frontend)
- [Ollama](https://ollama.com/) (running locally)
- [uv](https://github.com/astral-sh/uv) (recommended for Python package management)

### 1. Backend Setup

```bash
# Clone the repository
git clone https://github.com/elessarrr/Bookmarks-RAG-Knowledge-Assistant.git
cd Bookmarks-RAG-Knowledge-Assistant

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt

# Start Ollama (ensure you have models pulled)
ollama pull llama3.2:3b
ollama pull nomic-embed-text
```

The default generator is `llama3.2:3b`, chosen for practical local use on a laptop. For a higher-quality, higher-memory option, set `llm_model: "gpt-oss:20b"` in `config.yaml` and pull that model explicitly.

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### 3. Running the App

Start the backend API:
```bash
# In project root
uvicorn app.main:app --reload
```

Open `http://localhost:5173` in your browser.

---

## 🧪 Development

### Running Tests
```bash
# Backend tests
PYTHONPATH=. pytest

# Run smoke test (end-to-end)
PYTHONPATH=. pytest tests/smoke_test.py
```

### Running Evals
To evaluate RAG performance:
```bash
python evals/run_evals.py
```
Results are saved in `evals/results/`.

## Known Limitations

- **Citations are not verified:** the prompt asks the generator to cite retrieved source numbers, but the application does not programmatically validate each citation or claim.
- **Evaluation is offline:** the 19-question retrieval/RAGAS harness, independent judge, and chunking comparison are development tools; they do not run on `/api/query`.
- **Search is exact and unindexed:** DuckDB computes cosine similarity across stored chunks and sorts the results. This brute-force approach is suitable for a personal corpus, not large-scale vector search.
- **Chat is non-streaming:** `OllamaClient.generate_stream` and `RAGEngine.query_stream` are library methods only. The current `/api/query` endpoint and React chat UI wait for one complete response.
- **Single-user by design:** there is no authentication, authorization, tenant isolation, or audit log. Run it as a trusted local tool, not an internet-facing service.
- **Web access still leaves the machine:** models and stored content stay local, but ingestion necessarily requests bookmarked websites and is subject to their availability, access controls, and robots policies.

---

## 🤝 For Potential Collaborators

This repository demonstrates **end-to-end AI product development**, moving from a Product Requirements Document (PRD) to a shipping codebase with a rigorous evaluation framework. It highlights experience in:
1.  **Architecting Local-First Systems**: Designing privacy-preserving AI systems that don't rely on expensive cloud APIs.
2.  **Implementing Production Patterns**: Using `DuckDB` for vector storage, `FastAPI` for async endpoints, and `React` for a responsive UI.
3.  **Validating Product Assumptions**: The decision to archive this project reflects a product-first mindset—recognizing when a solution (standalone app) doesn't match the optimal user workflow (browser extension) and being willing to pivot based on that insight.

I am open to discussing the architectural decisions, the evaluation methodology, or the rationale behind the product pivot.

---

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.

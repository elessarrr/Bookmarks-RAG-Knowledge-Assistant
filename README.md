# Bookmarks RAG Knowledge Assistant

> **Turn your browser bookmarks into an interactive, privacy-first knowledge base.**

**Bookmarks RAG Knowledge Assistant** is a powerful, local-first **Retrieval-Augmented Generation (RAG)** tool designed to unlock insights from your accumulated browser bookmarks. By ingesting Netscape-format HTML exports (supported by Chrome, Firefox, Safari, Edge), it transforms static links into a queryable vector database, allowing you to chat with your saved content using state-of-the-art local LLMs.

Built with **Privacy** and **Performance** in mind, this tool runs entirely on your machine, leveraging **DuckDB** for efficient vector storage and **Ollama** for local inference—ensuring your reading habits and data remain private.

---

## 🚀 Key Features

- **🔒 Privacy-First Architecture**: Zero data exfiltration. Runs 100% locally using Ollama and local embedding models.
- **🧠 Advanced RAG Pipeline**:
    - **Smart Ingestion**: Parses and cleans HTML content from bookmarked URLs using `BeautifulSoup` and `readability-lxml`.
    - **Semantic Chunking**: Intelligently splits content to preserve context for better retrieval.
    - **Hybrid Search**: Combines vector similarity search (embeddings) with structured metadata filtering.
- **⚡ High-Performance Backend**: Powered by **FastAPI** and **DuckDB** for sub-millisecond vector retrieval and async processing.
- **✨ Modern Reactive UI**: A polished **React 19** + **Vite** frontend with **Tailwind CSS 4** for seamless bookmark management and chat.
- **📊 Built-in Evaluation**: Includes a `ragas`-based evaluation framework to benchmark retrieval accuracy and generation quality.

## 🛠️ Technology Stack

### Backend (Python)
- **Framework**: `FastAPI` (Async web API), `Uvicorn` (ASGI Server)
- **Database**: `DuckDB` (In-process SQL OLAP & Vector Store)
- **AI & ML**:
    - **LLM Runtime**: `Ollama` (Local Llama 3, Mistral, etc.)
    - **Embeddings**: `sentence-transformers` (Hugging Face), `nomic-embed-text`
    - **Vector Operations**: `NumPy`
- **Data Processing**: `BeautifulSoup4`, `readability-lxml`, `httpx` (Async HTTP)
- **Testing**: `pytest`, `pytest-asyncio`, `pytest-cov`

### Frontend (TypeScript)
- **Core**: `React 19`, `TypeScript`
- **Build Tool**: `Vite`
- **Styling**: `Tailwind CSS 4`, `clsx`, `tailwind-merge`
- **Icons**: `Lucide React`
- **State/Networking**: `Axios`, React Hooks

### DevOps & Infrastructure
- **Containerization**: `Docker`, `Docker Compose`
- **CI/CD**: `GitHub Actions` (Automated testing & linting)
- **Package Management**: `uv` (Python), `npm` (Node)

---

## Prerequisites

- Python 3.10+
- Node.js 18+ (for frontend)
- [Ollama](https://ollama.com/) (running locally)
- [uv](https://github.com/astral-sh/uv) (recommended for Python package management)

## Quick Start

### 1. Backend Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/bookmarks-rag-knowledge-assistant.git
cd bookmarks-rag-knowledge-assistant

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt

# Start Ollama (ensure you have models pulled)
ollama pull llama3
ollama pull nomic-embed-text
```

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

## Configuration

Copy `.env.example` to `.env` and adjust settings:

```bash
cp .env.example .env
```

Key variables:
- `OLLAMA_BASE_URL`: URL of your local Ollama instance (default: `http://localhost:11434`)
- `LLM_MODEL`: Model to use for generation (default: `llama3`)
- `EMBEDDING_MODEL`: Model for embeddings (default: `all-MiniLM-L6-v2` or `nomic-embed-text`)

## Usage

1. **Export Bookmarks**: In your browser, go to Bookmark Manager -> Export Bookmarks (HTML).
2. **Upload**: Go to the "Manage" tab in the app and upload the file.
3. **Chat**: Switch to the "Chat" tab and ask questions about your saved content.

## Development

### Running Tests

```bash
# Backend tests
pytest

# Run smoke test (end-to-end)
pytest tests/smoke_test.py
```

### Running Evals

To evaluate RAG performance:

```bash
python evals/run_evals.py
```

Results are saved in `evals/results/`.

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed design docs.

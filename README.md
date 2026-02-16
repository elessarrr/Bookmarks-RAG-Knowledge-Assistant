# Bookmark RAG Tool

A local-first RAG (Retrieval-Augmented Generation) tool that ingests your browser bookmarks (Netscape HTML format) and allows you to chat with them using local LLMs (Ollama) or OpenAI.

## Features

- **Privacy First**: Runs entirely locally with Ollama and DuckDB.
- **Bookmark Ingestion**: Supports Chrome/Firefox/Safari HTML exports.
- **Smart Chunking**: Splits content into semantic chunks while preserving context.
- **Hybrid Search**: Vector similarity search (embeddings) + metadata filtering.
- **Modern UI**: React + Tailwind CSS interface for uploading and chatting.
- **Evaluation**: Built-in evaluation framework to measure RAG quality.

## Prerequisites

- Python 3.10+
- Node.js 18+ (for frontend)
- [Ollama](https://ollama.com/) (running locally)
- [uv](https://github.com/astral-sh/uv) (recommended for Python package management)

## Quick Start

### 1. Backend Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/bookmark-rag-tool.git
cd bookmark-rag-tool

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

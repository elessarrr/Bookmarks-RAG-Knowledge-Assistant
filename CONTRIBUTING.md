# Contributing to Bookmark RAG Tool

Thank you for your interest in contributing! We welcome bug reports, feature requests, and pull requests.

## Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/yourusername/bookmark-rag-tool.git
   cd bookmark-rag-tool
   ```

2. **Backend**
   ```bash
   uv venv
   source .venv/bin/activate
   uv pip install -r requirements.txt
   ```

3. **Frontend**
   ```bash
   cd frontend
   npm install
   ```

## Workflow

1. Create a feature branch: `git checkout -b feature/my-new-feature`.
2. Implement your changes.
3. Add tests (backend in `tests/`, frontend in `frontend/src/__tests__` if applicable).
4. Run tests: `pytest`.
5. Submit a Pull Request.

## Code Style

- **Python**: Follow PEP 8. Use `black` and `ruff` if available.
- **TypeScript**: Use Prettier.

## Evaluation

If you modify the RAG pipeline, please run the evaluation suite to ensure no regression:
```bash
python evals/run_evals.py
```
Compare the metrics in `evals/results/` before and after your changes.

# Task List: Portfolio Credibility Hardening
**PRD Reference:** `Planning/0003-prd-portfolio-credibility-hardening.md`  
**Target Reader:** Junior developer hardening an existing FastAPI + React + DuckDB RAG app  
**Resolved decisions:** robots unreachable → allow + warn; streaming → document & narrow (1.8b); document `gpt-oss:20b` as optional quality override.

---

## Implementation Notes

> **Read these before writing any code.**

1. **TDD:** For behaviour changes (robots, stream client, config failures), write/fix the failing test first, then implement.
2. **Minimal diffs:** Prefer restoring commented/disabled paths over rewriting modules.
3. **Do not wire streaming into routes/UI** — document and narrow only (PRD 1.8b). Keep `generate_stream` / `query_stream` as unused library methods with clear docstrings; do not add a streaming API route.
4. **Preserve eval harness:** independent judge, 19-question dataset, chunking comparison must stay green.
5. **Ollama stream NDJSON:** Production client reads `data.get("response", "")` from `/api/generate` lines — mock that shape, **not** Chat API `message.content`.
6. **Static mount order:** Register `/health` and `/api` routers **before** mounting `StaticFiles` at `/`, so API routes are not swallowed.
7. **Suggested order:** 1.0 → 2.0 → 3.0 → 4.0 → 5.0 → 6.0.
8. **Demo check:** After Task 4.0, `docker compose up --build` should show the React UI, not the placeholder API page.
9. **How to run tests:** from repo root with venv active: `pytest -q` (or scoped files listed per task).

---

## Relevant Files

### Streaming test (Task 1.0)
- `app/rag/llm/ollama_client.py` — production streaming client (`/api/generate`, `stream: true`, yields `response` field).
- `app/rag/llm/test_ollama_client.py` — hollow `test_ollama_generate_stream` to fill in; keep `test_ollama_generate` green.

### Robots.txt (Task 2.0)
- `app/ingestion/fetcher.py` — restore `check_robots_txt` + call from `fetch_url`; allow+warn on robots fetch failure; domain cache.
- `app/ingestion/test_fetcher.py` — unskip `test_robots_block`; add allow+warn / cache tests as needed.

### Config + README (Task 3.0)
- `config.yaml` — default `llm_model: llama3.2:3b`; keep distinct `ragas_judge_model`.
- `app/test_config.py` — update `BASE_CONFIG` / fixtures that still assume `gpt-oss:20b` as the *default* generator where appropriate.
- `evals/metrics/test_answer_quality.py` — may still use `gpt-oss:20b` as a *fixture* generator vs judge; that is fine if intentional.
- `README.md` — Quick Start pulls, robots claim, optional quality override, DuckDB honesty retained.
- `ARCHITECTURE.md` — optional cross-link from README Known Limitations.

### Docker static UI (Task 4.0)
- `app/main.py` — mount `frontend/dist` when present; fallback to `static/` placeholder.
- `Dockerfile` — already copies dist to `/app/frontend/dist` (verify path matches mount).
- `docker-compose.yml` — no behaviour change expected; verify after mount fix.
- `tests/test_main.py` — extend if useful to assert static directory selection without requiring a full Docker build.

### Docs + stream narrow (Task 5.0)
- `README.md` — **Known Limitations** section.
- `app/rag/engine.py` — docstring on `query_stream`: not exposed by HTTP routes / UI.
- `app/rag/llm/base.py` / `ollama_client.py` — note streaming is library-only / future work.
- `app/routes/query.py` — confirm (and comment if needed) that only non-stream `engine.query` is used.
- `OCBC prep doc` (optional, outside this repo): walk back “streaming built twice, wired nowhere” to “implemented but deliberately unwired; documented.”

### Config failure tests (Task 6.0)
- `app/config.py` — already raises `FileNotFoundError` / `RuntimeError` / `ValueError`; ensure messages are clear.
- `app/test_config.py` — add missing-file, invalid-YAML, missing-required-keys tests.

---

## Tasks

- [x] 1.0 Fix hollow Ollama streaming unit test (P0)
  - [x] 1.1 Read `OllamaClient.generate_stream` and note exact URL, JSON body (`stream: true`), and NDJSON field (`response`) used for tokens.
  - [x] 1.2 Rewrite `test_ollama_generate_stream` in `app/rag/llm/test_ollama_client.py`: properly mock `httpx.AsyncClient` as an async context manager whose `.stream(...)` returns an async context manager yielding a response with `aiter_lines()` of Ollama `/api/generate` NDJSON (`{"response": "...", "done": false}` / `done: true`).
  - [x] 1.3 Assert concatenated yielded chunks equal the mocked token text (e.g. `"Hello World"`).
  - [x] 1.4 Assert the stream request targets `{base_url}/api/generate` and JSON includes `"stream": True` and the expected model name.
  - [x] 1.5 Run `pytest app/rag/llm/test_ollama_client.py -q` — both generate and generate_stream tests must pass; confirm emptying the assert body would fail the test.

- [x] 2.0 Restore real robots.txt enforcement with allow+warn fail-open (P0)
  - [x] 2.1 Unskip `test_robots_block` in `app/ingestion/test_fetcher.py` and confirm it fails for the right reason (robots check not wired / always True).
  - [x] 2.2 Add tests for `check_robots_txt` behaviour: (a) explicit Disallow → False; (b) robots.txt unreachable/timeout → True + warning logged; (c) same-domain second call uses cache (optional but preferred).
  - [x] 2.3 Implement real `check_robots_txt` using `RobotFileParser`, per-domain `_robots_cache`, project `USER_AGENT`, and **allow + warn** when robots.txt cannot be fetched.
  - [x] 2.4 Wire `fetch_url` to call `check_robots_txt` before GET; on False return `FetchResult(..., error="Blocked by robots.txt")` without fetching page body.
  - [x] 2.5 Run `pytest app/ingestion/test_fetcher.py -q` — all green, zero skips for robots.

- [x] 3.0 Align default generator model and README claims (P0)
  - [x] 3.1 Change `config.yaml` `llm_model` from `gpt-oss:20b` to `llama3.2:3b`; leave `ragas_judge_model` as a different family (keep `qwen2.5:32b` or document RAM-constrained alternate).
  - [x] 3.2 Update README Quick Start: `ollama pull llama3.2:3b` (and embedding model pulls as already documented); note `gpt-oss:20b` as an **optional** higher-quality override via `config.yaml`.
  - [x] 3.3 Update README robots section to state Disallow is honored; robots.txt fetch failure → allow + warn (matches code after 2.0). Remove “short-circuited” wording. Keep DuckDB linear-scan / not-a-powerhouse honesty.
  - [x] 3.4 Update any test fixtures that incorrectly assume the *default* generator is still `gpt-oss:20b` (e.g. `app/test_config.py` `BASE_CONFIG`) so the suite matches the new default; keep judge≠generator assertions.
  - [x] 3.5 Run `pytest app/test_config.py evals/metrics/test_answer_quality.py -q` (and full `pytest -q` before merge).

- [x] 4.0 Serve built React UI from Docker / FastAPI static mount (P1)
  - [x] 4.1 Confirm Dockerfile copies Vite build to `/app/frontend/dist` and that `index.html` exists after `npm run build`.
  - [x] 4.2 Change `app/main.py` to prefer mounting `frontend/dist` (html=True) when that directory contains `index.html`; otherwise fall back to creating/serving `static/` placeholder.
  - [x] 4.3 Ensure `/health` and `/api/*` remain registered **before** the catch-all static mount; add/adjust a unit or smoke assertion if cheap (e.g. helper that picks static dir).
  - [x] 4.4 Verify locally: Vite dev (`:5173` → API `:8000`) still works; Docker path serves React shell (upload/chat), not `<h1>…API is running</h1>`.
  - [x] 4.5 Update startup log lines if needed so they do not claim only `:5173` when Docker is serving UI from `:8000`.

- [ ] 5.0 Document Known Limitations and narrow unused streaming surface (P1/P2)
  - [x] 5.1 Add a **Known Limitations** section to `README.md` (or `ARCHITECTURE.md` + README link) covering: prompt-only citations; eval harness offline/dev-only; DuckDB brute-force cosine; no auth / single-user; streaming library methods exist but are **not** on the `/api/query` or UI hot path.
  - [x] 5.2 Narrow in code comments/docstrings only: mark `RAGEngine.query_stream` and `OllamaClient.generate_stream` as unused by HTTP/UI (future work); do **not** add streaming routes; do **not** delete methods that unit tests still exercise.
  - [x] 5.3 Grep README/ARCHITECTURE for overclaims (robots, vector powerhouse, “streaming chat”, “strict adherence”) and fix any remaining contradictions.
  - [x] 5.4 Optional: sync one paragraph in interview prep doc if it still says streaming is an unfinished accident rather than a deliberate non-goal for this pass.

- [ ] 6.0 Add config-loading failure-path tests (P2)
  - [ ] 6.1 Write failing tests in `app/test_config.py` for: missing config file → `FileNotFoundError`; invalid YAML → `RuntimeError` (or current exception type); missing required key(s) → `ValueError` with field names in the message.
  - [ ] 6.2 Adjust `Settings.load` messages only if needed for clarity — no behaviour change to happy path.
  - [ ] 6.3 Run `pytest app/test_config.py -q`, then full `pytest -q` regression before considering the PRD done.

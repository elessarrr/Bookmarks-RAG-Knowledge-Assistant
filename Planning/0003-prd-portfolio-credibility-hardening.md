# PRD: Portfolio Credibility Hardening (Bookmarks RAG)

## Introduction/Overview

**Problem:** Several shipped behaviours and docs still diverge in ways that a careful reviewer (especially a data scientist opening the repo) will notice within minutes: `robots.txt` is short-circuited while docs claim adherence; the Ollama streaming client test has an empty body; Docker builds the React UI but serves a placeholder; and `config.yaml` defaults to a ~20B generator while the original PRD/RAM story assumes a ~3B model. Those gaps are small in product surface area but large in **credibility** for a VP-level AI Product Builder portfolio piece.

**Solution:** A focused hardening pass so code, tests, config defaults, and README claims line up — without rebuilding the RAG architecture or expanding into bank-grade multi-tenancy.

**Goal:** After this work, an interviewer cloning `main` and skimming critical paths should conclude: *this person ships honestly, tests what they claim, and knows when a prototype trade-off is intentional.*

**Audience:** Hiring interviewers (experienced DS/CS); secondary audience is future-you demoing under time pressure.

---

## Goals

1. **Docs ↔ code alignment** on robots.txt, default generator model, and (bonus) Docker-served UI.
2. **No hollow tests** on the production Ollama streaming client path.
3. **Feasible local default LLM** matching the documented ~4–6GB RAM assumption (`llama3.2:3b` via Ollama).
4. **Interview-safe honesty surface:** a short, accurate Known Limitations section so overclaims are owned, not discovered adversarially.
5. **Preserve** existing eval-harness rigor (independent judge, 19-question dataset, chunking comparison) — do not regress it.

---

## User Stories

**As an interviewer opening the fetcher,** I want `robots.txt` checking to actually run (and be tested) so that README ethics claims are believable.

**As an interviewer reading tests,** I want `test_ollama_generate_stream` to assert streamed tokens, not `pass` after mock setup.

**As a candidate demoing via Docker,** I want `docker-compose up` to serve the built React UI from the same process that serves the API, so I am not embarrassed by a placeholder page.

**As a user on a laptop with ~8GB RAM,** I want the default generator model to be pullable and runnable without a 20B+ footprint.

**As a hiring manager evaluating product judgment,** I want a Known Limitations section that matches the code (citations, eval ceiling, streaming wiring, DuckDB scale) so the builder demonstrates self-audit.

---

## Functional Requirements

### Priority P0 — Credibility must-haves

1.1. System **must** restore real `robots.txt` enforcement in `app/ingestion/fetcher.py`:
- `check_robots_txt` must implement fetch/parse/cache behaviour (not `return True` unconditionally).
- `fetch_url` **must** call `check_robots_txt` before GET; on deny, return `FetchResult` with a clear robots-blocked error and **must not** fetch page body.
- Fail-open policy when `robots.txt` itself cannot be fetched (network error / timeout): document the choice in code comment + Known Limitations (recommend: treat as **allow** with a logged warning for personal-tool UX, or **deny** for strict ethics — pick one and test it; default recommendation: **allow + warn** so personal bookmarks on flaky robots endpoints still ingest, while explicit `Disallow` is honored).

1.2. System **must** unskip and green `test_robots_block` (and keep existing allow/happy-path fetcher tests coherent with the real checker).

1.3. System **must** implement a non-empty `test_ollama_generate_stream` that:
- correctly mocks `httpx.AsyncClient` streaming (`aiter_lines` / NDJSON matching `OllamaClient.generate_stream`);
- asserts concatenated streamed content equals the mocked token sequence;
- asserts the request uses `stream: true` (or equivalent) against `/api/generate`.

1.4. System **must** change default `llm_model` in `config.yaml` from `gpt-oss:20b` to **`llama3.2:3b`** (feasible Ollama tag; aligns with original PRD §3.5 / RAM note of ~4–6GB).
- README Quick Start **must** use `ollama pull llama3.2:3b` (not only a generic `llama3`).
- `ragas_judge_model` **must** remain a **different** model/family from the generator (keep `qwen2.5:32b` or document a smaller alternate judge such as `qwen2.5:14b` for RAM-constrained eval machines — judge stays eval-only).

1.5. After 1.1–1.2 land, README **must** state that robots.txt is respected for explicit disallow rules (remove any temporary "short-circuited" wording). DuckDB "not a vector powerhouse / linear-scan" honesty **must** remain.

### Priority P1 — Demo bonus (include if P0 stays green)

1.6. Docker path **must** serve the built frontend:
- Dockerfile already copies `/frontend/dist` → `/app/frontend/dist`.
- `app/main.py` **must** mount that built asset directory (SPA `index.html` fallback) instead of the placeholder `static/` page when the built dist exists.
- `docker-compose up` → open app port → real React UI loads (upload + chat shell visible). Native Vite `:5173` workflow **must** keep working for local dev.

1.7. Add a **Known Limitations** subsection to README (or `ARCHITECTURE.md` linked from README) covering at least:
- citations are prompt-convention, not programmatically verified;
- eval harness is offline/dev-only (not on `/api/query`);
- DuckDB search is brute-force cosine (exact, unindexed);
- streaming client/engine exist but chat UI/route may still be non-streaming (state the truth after implementing 1.8);
- no auth / single-user assumption.

### Priority P2 — Stretch credibility (include if time; do not block P0)

1.8. Either **(a)** wire streaming end-to-end (API route + minimal frontend consumption) **or** **(b)** delete/stop advertising unused stream paths and keep only non-stream `generate` on the hot path — pick (a) if <1 day of work remains after P0/P1, else (b) with an explicit "future work" note. Hollow "streaming built twice, wired nowhere" is worse than an honest non-stream demo.

1.9. Add unit tests for config-loading **failure** paths (missing `config.yaml`, invalid YAML, missing required keys) with clear error messages — shows production instinct without new features.

1.10. Optional smoke: one Playwright or Vitest smoke that the upload page renders (only if toolchain already half-present; **do not** invent a full frontend test framework in this PRD).

---

## Non-Goals (Out of Scope)

1. Replacing DuckDB with pgvector/Qdrant/Chroma (architecture change; interview talk-track only).
2. Auth, multi-tenancy, audit logging of Q&A pairs (name in Known Limitations; do not build here).
3. Programmatic citation verification / groundedness enforcement beyond the existing prompt.
4. Live unmocked RAGAS against a judge inside CI (too heavy/flaky; keep library mocked at the boundary in unit tests).
5. Human-labeled relevance dataset expansion beyond the existing 19 questions.
6. Browser-extension product pivot described in the archive README.
7. Changing embedding model or schema dimension (`FLOAT[384]`).

---

## Design Considerations

- Prefer **minimal diffs** in `fetcher.py`, `main.py` static mount, `config.yaml`, tests, and README.
- UI look-and-feel unchanged; only make the built SPA reachable under Docker.
- Failures from robots blocks must surface in existing SSE ingest progress as skipped URLs with reason (reuse current failure isolation).

---

## Technical Considerations

| Area | Notes |
|---|---|
| Robots | `urllib.robotparser.RobotFileParser`; keep in-memory per-domain cache; use project `USER_AGENT`. |
| Stream test | Mirror production client’s NDJSON field names (`response` vs `message.content`) — match `ollama_client.py`, not Chat API shape. |
| Default LLM | `llama3.2:3b` is the original task-list default and fits the 4–6GB story; larger models remain config overrides. |
| Static mount | Mount `frontend/dist` when present; fallback to `static/` placeholder only for bare API-only runs. Order routes carefully so `/api` and `/health` are not swallowed by `StaticFiles`. |
| README PR sequencing | Ship DuckDB honesty immediately. **Do not** permanently document robots short-circuit if this PRD’s 1.1 is imminent — either (1) hold robots wording until 1.1 merges, or (2) merge DuckDB-only README first, then update robots claim to “respected” in the same PR as 1.1–1.2. |

---

## Success Metrics

1. `pytest` green on a clean install; previously skipped robots test **runs and passes**; stream test **fails if body emptied again**.
2. `config.yaml` default `llm_model: llama3.2:3b`; README pull instructions match.
3. Grep/README review: no claim of “strict robots adherence” while code returns `True` unconditionally.
4. (P1) Fresh `docker compose up --build` shows React UI, not the placeholder `<h1>…API is running</h1>`.
5. Candidate can narrate Known Limitations without contradiction from `main`.

---

## Open Questions

1. ~~Robots fail-open vs fail-closed when `robots.txt` is unreachable~~ — **Resolved: allow + warn** (honor explicit Disallow; if robots.txt cannot be fetched, allow the URL and log a warning).
2. ~~Streaming wire vs document-and-narrow~~ — **Resolved: 1.8b document and narrow** (do not make streaming operational; close the honesty gap only).
3. ~~Keep `gpt-oss:20b` as optional quality override?~~ — **Resolved: yes** — document as an optional higher-quality config override in README.

---

## Implementation notes (for task list; not implementation yet)

Suggested order: **1.3 stream test → 1.1/1.2 robots → 1.4 model default + README → 1.5 robots README claim → 1.6 Docker static → 1.7 Known Limitations → 1.8b document/narrow streaming → 1.9 config failure tests if time.**

Do **not** start implementation until this PRD is accepted and a task list is generated.

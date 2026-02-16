# Learnings from Errors

## 1. Mypy Configuration for Tests
**Key Takeaway:** Use specific module patterns in `mypy.ini` to ignore errors in tests, rather than generic glob patterns which Mypy might not resolve as expected.
*   **Background:** We tried to use `[mypy-*.test_*]` to ignore errors in all test files, but Mypy continued to report errors in `app/ingestion/test_parser.py`, etc.
*   **Cause:** Mypy's config section headers match *module names*, not file paths. A pattern like `*.test_*` is valid for file paths but Mypy expects `module.submodule`.
*   **Solution:** We explicitly listed the test modules (e.g., `[mypy-app.ingestion.test_parser]`) or could have used a more inclusive module pattern like `[mypy-*.tests.*]`.

## 2. BeautifulSoup Type Mismatches (`AttributeValueList`)
**Key Takeaway:** Be explicit when handling BeautifulSoup return types, as they can be `str` or `list[str]`.
*   **Background:** Mypy complained that `float(date_str)` received `str | AttributeValueList` (which is list-like), but `float()` expects a string or number.
*   **Cause:** `soup.find()['attribute']` can return a list if the attribute is multi-valued (like `class`). Even for attributes that are usually single (like `add_date`), the type hint includes the list possibility.
*   **Solution:** Explicitly cast to `str` or check instance type before using. `str(val)` is usually safe for `AttributeValueList` if it's just one value, but logic might need to be robust.

## 3. Abstract Method Return Types in Async Classes
**Key Takeaway:** Ensure abstract base class definitions for async methods match the implementation's coroutine nature.
*   **Background:** `BaseLLM.generate` was likely defined as `def generate(...) -> str: ...` (synchronous signature) or `async def` but Mypy saw a mismatch with `OllamaClient.generate`.
*   **Cause:** If the base class defines `async def foo() -> str`, the return type of the *coroutine* is `Coroutine[Any, Any, str]`. If annotations are inconsistent (e.g. using `Generator` vs `AsyncGenerator`), Mypy flags overrides.
*   **Solution:** Correctly type `AsyncGenerator[str, None]` for streaming methods and ensure `async def` is used consistently in base and child.

## 4. Optional Arguments in Class Constructors
**Key Takeaway:** PEP 484 prohibits implicit `Optional`. `arg: str = None` is invalid in modern Mypy; use `arg: str | None = None`.
*   **Background:** `OllamaClient.__init__` had `base_url: str = None`.
*   **Cause:** Mypy's strict mode (or newer defaults) requires explicit `Optional` or `| None` union for arguments that default to `None`.
*   **Solution:** Updated signature to `base_url: str | None = None`.

## 5. Missing Return Type Annotations
**Key Takeaway:** Public methods in library code should always have return type annotations, even if `-> None`.
*   **Background:** Mypy reported "Function is missing a return type annotation" for `app/main.py` startup events and route handlers.
*   **Cause:** `disallow_untyped_defs = True` in `mypy.ini` enforces this for all functions in `app/`.
*   **Solution:** Added `-> None` to `startup_event` and explicit return types (e.g. `-> dict`) to route handlers.

## 6. Frontend API Proxy Configuration
**Key Takeaway:** Always configure a proxy in `vite.config.ts` when developing a React frontend separate from the API backend to avoid CORS/404 issues.
*   **Background:** "Upload failed" error in frontend because requests were hitting `http://localhost:5173/api/upload` (404) instead of port 8000.
*   **Cause:** Missing `server.proxy` configuration in Vite to forward `/api` requests to the backend server.
*   **Solution:** Added `server: { proxy: { '/api': 'http://localhost:8000' } }` to `vite.config.ts`.

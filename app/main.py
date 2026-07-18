from typing import Dict, Any
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routes import ingest, query
from os import PathLike
from pathlib import Path

PLACEHOLDER_HTML = "<h1>Bookmarks RAG Knowledge Assistant API is running</h1>"


def select_static_directory(
    frontend_dist: str | PathLike[str] = "frontend/dist",
    fallback_static: str | PathLike[str] = "static",
) -> str:
    """Prefer a built frontend, creating an API placeholder only as fallback."""
    frontend_path = Path(frontend_dist)
    if (frontend_path / "index.html").is_file():
        return str(frontend_path)

    fallback_path = Path(fallback_static)
    fallback_path.mkdir(parents=True, exist_ok=True)
    fallback_index = fallback_path / "index.html"
    if not fallback_index.is_file():
        fallback_index.write_text(PLACEHOLDER_HTML, encoding="utf-8")
    return str(fallback_path)


STATIC_DIRECTORY = select_static_directory()

app = FastAPI(
    title="Bookmarks RAG Knowledge Assistant",
    description="Local-first RAG tool for browser bookmarks",
    version="0.1.0"
)

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for local tool, restrict if deployed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency Injection Setup (Placeholders for now)
# In a real implementation, we would initialize the specific 
# embedder, store, and LLM implementations here based on config.
embedder = None
storage = None
llm = None

@app.on_event("startup")
async def startup_event() -> None:
    print(f"Starting Bookmarks RAG Knowledge Assistant with config: {settings}")
    print("\n" + "="*50)
    print("🚀 Backend API running at: http://localhost:8000")
    if Path(STATIC_DIRECTORY).resolve() == Path("frontend/dist").resolve():
        print("🎨 Built frontend UI running at: http://localhost:8000")
    else:
        print("🎨 Vite development UI: run separately at http://localhost:5173")
    print("="*50 + "\n")
    # Initialize DB if needed (tables created on first connection usually)
    pass

@app.get("/health")
async def health_check() -> Dict[str, str]:
    return {"status": "ok", "version": "0.1.0"}

# Register routers
app.include_router(ingest.router, prefix="/api", tags=["ingest"])
app.include_router(query.router, prefix="/api", tags=["query"])

# Mount after API routes so the catch-all frontend cannot swallow them.
app.mount("/", StaticFiles(directory=STATIC_DIRECTORY, html=True), name="static")

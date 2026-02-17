from typing import Dict, Any
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routes import ingest, query
import os

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
    print("🎨 Frontend UI running at:  http://localhost:5173")
    print("="*50 + "\n")
    # Initialize DB if needed (tables created on first connection usually)
    pass

@app.get("/health")
async def health_check() -> Dict[str, str]:
    return {"status": "ok", "version": "0.1.0"}

# Register routers
app.include_router(ingest.router, prefix="/api", tags=["ingest"])
app.include_router(query.router, prefix="/api", tags=["query"])

# Mount static files
# Ensure static directory exists
if not os.path.exists("static"):
    os.makedirs("static")

# Check if index.html exists, if not create it
if not os.path.exists("static/index.html"):
    with open("static/index.html", "w") as f:
        f.write("<h1>Bookmarks RAG Knowledge Assistant API is running</h1>")

app.mount("/", StaticFiles(directory="static", html=True), name="static")

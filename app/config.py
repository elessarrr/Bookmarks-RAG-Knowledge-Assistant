import yaml
import os
from dataclasses import dataclass
from typing import Any

@dataclass
class Settings:
    embedding_model: str
    chunk_size: int
    chunk_overlap: int
    top_k: int
    ollama_base_url: str
    duckdb_path: str
    llm_model: str

    @classmethod
    def load(cls, config_path: str = "config.yaml") -> "Settings":
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found at {config_path}")
        
        try:
            with open(config_path, "r") as f:
                config_data = yaml.safe_load(f) or {}
        except Exception as e:
            raise RuntimeError(f"Failed to parse config file: {e}")

        required_fields = [
            "embedding_model", "chunk_size", "chunk_overlap", 
            "top_k", "ollama_base_url", "duckdb_path", "llm_model"
        ]
        
        missing = [field for field in required_fields if field not in config_data]
        if missing:
            raise ValueError(f"Missing required configuration fields: {', '.join(missing)}")

        return cls(
            embedding_model=str(config_data["embedding_model"]),
            chunk_size=int(config_data["chunk_size"]),
            chunk_overlap=int(config_data["chunk_overlap"]),
            top_k=int(config_data["top_k"]),
            ollama_base_url=str(config_data["ollama_base_url"]),
            duckdb_path=str(config_data["duckdb_path"]),
            llm_model=str(config_data["llm_model"]),
        )

# Load settings immediately to fail fast on startup if config is invalid
try:
    settings = Settings.load()
except Exception as e:
    # We print the error but don't crash module import immediately, 
    # though usage will likely fail. 
    # In a real app, we might want to let the exception bubble up 
    # or handle it in main.py.
    # For now, we'll allow import-time loading for simplicity as requested.
    # But to be safe for tests that might not have config in cwd:
    if os.environ.get("TESTING") != "true":
        print(f"Configuration Error: {e}")
        # We don't raise here to allow importing 'Settings' class in tests without config.yaml
        settings = None # type: ignore
    else:
        settings = None # type: ignore

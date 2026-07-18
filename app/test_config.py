"""
Tests for Settings config loading, focused on the RAGAS judge model and failure paths.

The judge model must be a first-class, separately-configurable setting: reusing
llm_model as the RAGAS judge is judge/generator conflation (the model grades its
own output), which is the single biggest weakness of the eval harness. These
tests pin that it's parsed when present and defaults to something *other than*
the generator when absent.
"""

import textwrap

import pytest

from app.config import Settings

BASE_CONFIG = """
embedding_model: "all-MiniLM-L6-v2"
chunk_size: 400
chunk_overlap: 50
top_k: 5
ollama_base_url: "http://localhost:11434"
duckdb_path: "./data/bookmarks.duckdb"
llm_model: "llama3.2:3b"
"""


def _write(tmp_path, body):
    p = tmp_path / "config.yaml"
    p.write_text(textwrap.dedent(body))
    return str(p)


def test_ragas_judge_model_parsed_when_present(tmp_path):
    path = _write(tmp_path, BASE_CONFIG + '\nragas_judge_model: "qwen2.5:32b"\n')
    settings = Settings.load(path)
    assert settings.ragas_judge_model == "qwen2.5:32b"


def test_ragas_judge_model_defaults_when_absent(tmp_path):
    """Backward compatible: an existing config.yaml with no judge field must
    still load, and the default judge must not silently equal the generator."""
    path = _write(tmp_path, BASE_CONFIG)
    settings = Settings.load(path)
    assert settings.ragas_judge_model
    assert settings.ragas_judge_model != settings.llm_model


def test_missing_config_file_raises_file_not_found(tmp_path):
    missing_path = tmp_path / "missing-config.yaml"

    with pytest.raises(FileNotFoundError, match=str(missing_path)):
        Settings.load(str(missing_path))


def test_invalid_yaml_raises_runtime_error(tmp_path):
    path = _write(tmp_path, "llm_model: [unclosed")

    with pytest.raises(RuntimeError, match="Failed to parse config file"):
        Settings.load(path)


def test_missing_required_keys_raise_value_error(tmp_path):
    path = _write(
        tmp_path,
        """
        embedding_model: "all-MiniLM-L6-v2"
        chunk_size: 400
        """,
    )

    with pytest.raises(ValueError, match="Missing required configuration fields") as exc_info:
        Settings.load(path)

    message = str(exc_info.value)
    assert "chunk_overlap" in message
    assert "llm_model" in message

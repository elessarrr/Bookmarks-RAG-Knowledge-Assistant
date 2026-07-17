"""
Integrity checks for the eval dataset (evals/dataset/qa_pairs.json).

The dataset is the ground truth every retrieval/generation metric is measured
against, so a too-small or malformed set silently makes the whole eval harness
meaningless (a 5-question set that mostly asks about the tool's own docs is a
lexical-overlap check, not a retrieval test). These tests encode the minimum
the harness needs to produce a defensible number: enough questions, valid
schema, and a real spread of difficulty including genuinely hard/ambiguous
items that stress retrieval rather than reward keyword overlap.
"""

import json
import os
from urllib.parse import urlparse

import pytest

DATASET_PATH = os.path.join(os.path.dirname(__file__), "dataset", "qa_pairs.json")

VALID_DIFFICULTIES = {"easy", "medium", "hard"}


@pytest.fixture(scope="module")
def qa_pairs():
    with open(DATASET_PATH, "r") as f:
        return json.load(f)


def test_dataset_has_enough_questions(qa_pairs):
    """A 5-item set is too small to distinguish real retrieval quality from
    small-N noise. The project's own task list targeted 25; 15 is the floor
    below which per-strategy comparison numbers aren't trustworthy."""
    assert len(qa_pairs) >= 15


def test_every_pair_has_required_schema(qa_pairs):
    for i, item in enumerate(qa_pairs):
        assert "question" in item and item["question"].strip(), f"pair {i} missing question"
        assert "difficulty" in item, f"pair {i} missing difficulty"
        assert item["difficulty"] in VALID_DIFFICULTIES, f"pair {i} bad difficulty"
        urls = item.get("ground_truth_urls", [])
        assert isinstance(urls, list) and urls, f"pair {i} has no ground_truth_urls"
        for url in urls:
            parsed = urlparse(url)
            assert parsed.scheme in ("http", "https") and parsed.netloc, f"pair {i} bad url {url}"


def test_dataset_includes_hard_and_ambiguous_items(qa_pairs):
    """The point of expanding the set is harder retrieval, not just more of the
    same easy doc-title lookups. Require a real tail of hard items."""
    hard = [p for p in qa_pairs if p.get("difficulty") == "hard"]
    assert len(hard) >= 3


def test_questions_are_unique(qa_pairs):
    questions = [p["question"].strip().lower() for p in qa_pairs]
    assert len(questions) == len(set(questions)), "duplicate questions in dataset"

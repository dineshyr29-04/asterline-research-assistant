import hashlib

import pytest

from src.config import Settings
from src.retrieval import CORPUS_SHA256, load_corpus, query_facets


def test_original_corpus_integrity():
    path = Settings().corpus_path
    assert hashlib.sha256(path.read_bytes()).hexdigest() == CORPUS_SHA256
    records = load_corpus(path)
    assert len(records) == 75 and len({r["doc_id"] for r in records}) == 25


def test_modified_corpus_is_rejected(tmp_path):
    path = tmp_path / "modified.jsonl"
    path.write_text('{"chunk_id":"fake:0"}')
    with pytest.raises(ValueError, match="integrity"):
        load_corpus(path)


def test_query_decomposition_preserves_versions_and_comparisons():
    facets = query_facets("Compare retention with Explorer timeline retention. Can cold storage extend the timeline?")
    assert len(facets) == 3
    assert query_facets("What was the timeout in version 2.2?") == []

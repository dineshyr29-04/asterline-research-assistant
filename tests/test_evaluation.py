"""Check that the named reviewer artifacts preserve measured data, not invented scores."""
import json

from scripts.evaluate import write_comparison_artifacts
from src.config import ROOT


def test_named_comparison_artifacts_preserve_recorded_measurements(tmp_path):
    recorded = json.loads((ROOT / "evaluation/results.json").read_text())
    write_comparison_artifacts(recorded, tmp_path)
    for name in ("baseline", "improved"):
        exported = json.loads((tmp_path / f"{name}.json").read_text())
        assert exported["summary"] == recorded[name]["summary"]
        assert exported["cases"] == recorded[name]["cases"]
        assert exported["corpus_sha256"] == recorded["corpus_sha256"]

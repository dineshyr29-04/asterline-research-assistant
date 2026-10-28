"""Validate submission artifacts and ensure tracked text does not contain configured keys."""
import hashlib
import json
import os
import subprocess

from src.config import ROOT, Settings
from src.retrieval import CORPUS_SHA256


def main():
    settings = Settings.from_env()
    names = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True).splitlines()
    if ".env" in names or any(n.startswith(("runtime/", ".venv/")) for n in names):
        raise ValueError("Local secrets or generated state must not be tracked")
    secrets = [settings.api_key, os.getenv("LANGSMITH_API_KEY", "")]
    for name in names:
        data = (ROOT / name).read_bytes()
        if any(secret and secret.encode() in data for secret in secrets):
            raise ValueError("A tracked file contains a configured credential; refusing submission")
    assert hashlib.sha256(settings.corpus_path.read_bytes()).hexdigest() == CORPUS_SHA256
    for name in ["README.md", "SUBMISSION.md", "docs/design.md", "docs/ai-use.md", "docs/demo.md",
                 ".env.example", "requirements.lock.txt", "evaluation/analysis.md"]:
        assert (ROOT / name).is_file(), f"Missing {name}"
    live = json.loads((ROOT / "evaluation/live-results.json").read_text())["generation"]
    assert len(live["cases"]) == 24, "Research evaluation is incomplete"
    memory = json.loads((ROOT / "evaluation/live-memory-results.json").read_text())
    assert memory["total"] == 6, "Memory evaluation is incomplete"
    shares = json.loads((ROOT / "evaluation/shared-runs.json").read_text())
    assert any(r.get("anonymous_access_verified") and r["suite"] == "research" for r in shares["runs"])
    assert any(r.get("anonymous_access_verified") and r["suite"] == "memory" for r in shares["runs"])
    print("PASS: intact corpus, required artifacts, completed evaluations, public research/memory evidence and no tracked configured keys")


if __name__ == "__main__":
    main()

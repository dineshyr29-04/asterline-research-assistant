"""Create an honest submission index from actual saved evaluation results."""
import json
from pathlib import Path

from src.config import ROOT


def main():
    research = json.loads((ROOT / "evaluation/live-results.json").read_text())["generation"]
    memory = json.loads((ROOT / "evaluation/live-memory-results.json").read_text())
    shares = json.loads((ROOT / "evaluation/shared-runs.json").read_text())
    passed = research["summary"]["pattern_passes"]
    links = [r for r in shares["runs"] if r.get("anonymous_access_verified")]
    table = ["| Suite / case | Outcome | Public trace |", "|---|---|---|"]
    for row in links:
        table.append(f"| {row['suite']} / {row['case']} | {row['status']} | [Open trace]({row['public_url']}) |")
    text = f"""# Asterline assignment submission

Repository: https://github.com/dineshyr29-04/asterline-research-assistant

## Run locally

Use Python 3.12. Install `requirements.lock.txt`, copy `.env.example` to `.env`, configure Groq (free tier) or local Ollama and LangSmith, then run `python launch.py`. See [README](README.md).

## Included deliverables

- [Design note and architecture diagram](docs/design.md).
- [Unchanged original corpus](data/corpus.jsonl), SHA-256 verified on every load.
- [Research evaluation results](evaluation/live-results.json) and [memory conversation results](evaluation/live-memory-results.json).
- [Failure analysis and measured retrieval improvement](evaluation/analysis.md).
- [AI-use disclosure](docs/ai-use.md) and [walkthrough](docs/demo.md).

## Actual evaluation results

Generation model: `{research['model']}` via Groq's OpenAI-compatible endpoint.

- Research: {research['summary']['cases']} actual questions; {passed} pass the authored answer-pattern checks; {research['summary']['provider_errors']} provider errors; {research['summary']['verification_failures']} verification failures. Pattern checks are proxies, not a claim of perfect semantic accuracy.
- Memory: {memory['passed']}/{memory['total']} actual conversation checks passed (context, restart, correction, isolation, forgetting).
- Retrieval: all expected passages found for 24/24 questions at eight chunks, compared with 23/24 for the dense baseline. MRR decreases; the trade-off is documented.
- Tests: run `python -m pytest tests -q` for deterministic storage, privacy, provider, orchestration and UI checks.

## Reviewer access

The free LangSmith account supports one seat and does not allow a second-member invitation. The following {len(links)} **individual trace links were checked through the public API without authentication**. They show synthetic research and memory runs. They do not grant whole-project membership. If whole-project access is mandatory, please advise an accepted free-tier review route; no reviewer invitation is claimed.

Project (requires owner/workspace access): https://smith.langchain.com/o/50f0f811-ae6c-434f-90b1-987936ceff44/projects/p/663fc501-699d-4534-b740-95fdc40b29e7

""" + "\n".join(table) + "\n"
    (ROOT / "SUBMISSION.md").write_text(text, encoding="utf-8")
    (ROOT / "docs/runs.md").write_text("# Actual LangSmith evidence\n\nSee [submission index](../SUBMISSION.md) for the complete public run table and free-tier access limitation.\n\n" + "\n".join(table) + "\n", encoding="utf-8")
    print(f"Prepared SUBMISSION.md with {len(links)} anonymously verified run links")


if __name__ == "__main__":
    main()

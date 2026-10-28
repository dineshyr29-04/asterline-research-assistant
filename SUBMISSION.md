# Asterline assignment submission

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

Generation model: `openai/gpt-oss-120b` via Groq's OpenAI-compatible endpoint.

- Research: 24 actual questions; 21 pass the authored answer-pattern checks; 0 provider errors; 0 verification failures. Pattern checks are proxies, not a claim of perfect semantic accuracy.
- [Review of the three pattern misses](evaluation/manual-review.json): two scoring false alarms and one remaining incomplete numerical example are documented rather than hidden.
- Memory: 6/6 actual conversation checks passed (context, restart, correction, isolation, forgetting).
- Retrieval: all expected passages found for 24/24 questions at eight chunks, compared with 23/24 for the dense baseline. MRR decreases; the trade-off is documented.
- Tests: run `python -m pytest tests -q` for deterministic storage, privacy, provider, orchestration and UI checks.

## Reviewer access

The free LangSmith account supports one seat and does not allow a second-member invitation. The following 14 **individual trace links were checked through the public API without authentication**. They show synthetic research and memory runs. They do not grant whole-project membership. If whole-project access is mandatory, please advise an accepted free-tier review route; no reviewer invitation is claimed.

Project (requires owner/workspace access): https://smith.langchain.com/o/50f0f811-ae6c-434f-90b1-987936ceff44/projects/p/663fc501-699d-4534-b740-95fdc40b29e7

| Suite / case | Outcome | Public trace |
|---|---|---|
| research / price-team | answered | [Open trace](https://smith.langchain.com/public/e489f47e-2d0c-4789-9b49-dda508fdcc0c/r) |
| research / cold-conflict | answered | [Open trace](https://smith.langchain.com/public/af30371a-6b92-4954-92a0-40d3e96a9f2e/r) |
| research / retention-types | answered | [Open trace](https://smith.langchain.com/public/5b49b586-2fb1-4178-bfb8-586b3fb71f94/r) |
| research / stipend-conflict | answered | [Open trace](https://smith.langchain.com/public/ac9349a2-1dec-4c4d-9ae1-f1305f5406dc/r) |
| research / duplicate-cleanup | answered | [Open trace](https://smith.langchain.com/public/d9f35b0b-4d2d-459d-a450-1c2e53d1b533/r) |
| research / hipaa-unknown | answered | [Open trace](https://smith.langchain.com/public/09f2114c-abc6-4e35-a28e-31065590be05/r) |
| memory / automatic-context | answered | [Open trace](https://smith.langchain.com/public/bff0cb15-809f-474d-9147-1656f82719a4/r) |
| memory / restart-new-session-followup | answered | [Open trace](https://smith.langchain.com/public/2cc04838-a27d-49f2-8f44-a32b17e7c615/r) |
| memory / automatic-correction | answered | [Open trace](https://smith.langchain.com/public/2021d3a0-8e21-443c-9c83-14af6ae5a24d/r) |
| memory / cross-user-isolation | abstained | [Open trace](https://smith.langchain.com/public/f79e732c-9e16-454a-a7b8-fe9fee12fb5e/r) |
| memory / forget-command | memory | [Open trace](https://smith.langchain.com/public/d45905e8-7c81-477a-add7-ff79d862fc9b/r) |
| memory / forget-no-resurrection-after-restart | abstained | [Open trace](https://smith.langchain.com/public/63b50426-ce60-498e-9f18-2b1027e6588d/r) |
| research-before-fix / cold-conflict | abstained | [Open trace](https://smith.langchain.com/public/2d610436-d6f2-4325-8c9d-5941d28dc8a4/r) |
| research-before-fix / stipend-conflict | abstained | [Open trace](https://smith.langchain.com/public/c28b4ade-3ef5-471c-a834-f0986a329d71/r) |

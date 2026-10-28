# Assignment requirement-to-file map

Start with [SUBMISSION.md](../SUBMISSION.md). This map identifies concrete evidence rather than claiming perfection.

| Requirement | Implementation / submission file | Verification / limitation |
|---|---|---|
| Working repository with one launch command | `app.py`, `launch.py`, optional `run.sh`, `README.md` | `python launch.py`; HTTP smoke and UI tests |
| Unchanged 75-chunk, 25-document corpus | `data/corpus.jsonl`, `data/corpus.sha256` | Hash checked at load and by tests; original PDF unchanged |
| Dependencies and secret-free environment example | `requirements.txt`, `requirements.lock.txt`, `.env.example`, `.gitignore` | CI installs lock; configured keys scanned before submission |
| Local embeddings and vector store | `src/retrieval.py` | MiniLM sentence-transformer via local FastEmbed ONNX + persistent Chroma; generated data ignored |
| Three meaningful agents | `src/agents.py`, `docs/design.md` | Memory, Research, Verifier; feedback changes a rejected draft; plain sequential Python |
| Chunk ID/title citations | `render_draft()` in `src/agents.py` | Current format `[chunk_id | title]`; tests cover it; historical live files retain recorded format |
| Conflicting, historical and missing evidence | Research/Verifier prompts, `evaluation/cases.json` | Retention, stipend, AQL versions, incidents, APAC and unpublished prices |
| Persistent conversations and memory | `src/memory.py` | Real SQLite tests and actual conversation sequence |
| User isolation | Ownership checks in `MemoryStore` | Cross-user sessions rejected; selector is not authentication |
| Corrections and forgetting | `save_many()`, `forget()`, UI controls and commands | Upsert, individual/all delete, history invalidation, natural forget request |
| Memory distinct from company truth | Separate tables/prompts and evidence-only claim validation | Stored workspace context is never authoritative company evidence |
| LangSmith inspectable runs | `src/tracing.py`, `docs/runs.md`, `evaluation/shared-runs.json` | Actual success, conflict, memory and before-fix traces; public links checked anonymously |
| Reviewer access | `SUBMISSION.md`, `docs/runs.md` | Individual public traces supplied; one-seat free account cannot grant whole-project membership |
| Short design note and architecture diagram | `docs/design.md` | Information flow, agent roles, memory, conflict strategy, trade-offs and limitations |
| Reproducible research and memory evaluation | `scripts/evaluate.py`, `scripts/evaluate_memory.py`, `tests/run_eval.py`, tests | Retrieval, pattern checks, citations and memory assertions reported separately |
| Baseline result | `evaluation/baseline.json` | Actual dense retrieval measurements |
| Improved result | `evaluation/improved.json` | Actual improved retrieval measurements at same eight-chunk budget |
| Failure analysis and measured improvement | `evaluation/analysis.md`, before-fix JSON artifacts | Source diversity improvement, query-placeholder failure, disconnects and quote typography documented |
| AI-use disclosure | `docs/ai-use.md` | What Codex produced/verified; human review is not fabricated |
| Explainable walkthrough and demo | `docs/code-walkthrough.md`, `docs/demo.md`, README's two-minute section | File responsibilities, data in/out and representative questions with actual links |

The supplied file tree was a preference, not a reason to duplicate working code. This repo keeps one canonical `evaluation/cases.json` and uses `Assistant.ask()` instead of adding a redundant `graph.py`. The existing Groq configuration remains supported; new setups default to Ollama. Live Ollama quality is not claimed without an installed and exercised model.

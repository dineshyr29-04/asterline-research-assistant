# Asterline Research Assistant

A research assistant that answers from Asterline's supplied company documents, explains conflicting evidence, and remembers useful workspace context across conversations and application restarts.

**Three collaborating agents · Local embeddings and vector storage · Persistent, user-scoped memory · Evidence verification · Opt-in LangSmith traces**

## Reviewer: start here

| Requested deliverable | Exact file |
|---|---|
| Submission and accessible trace links | [SUBMISSION.md](SUBMISSION.md) |
| Design note and Mermaid architecture | [docs/design.md](docs/design.md) |
| Baseline results | [evaluation/baseline.json](evaluation/baseline.json) |
| Improved results | [evaluation/improved.json](evaluation/improved.json) |
| Evaluation, failures and improvement explanation | [evaluation/analysis.md](evaluation/analysis.md) |
| Actual model research / memory results | [evaluation/live-results.json](evaluation/live-results.json) / [evaluation/live-memory-results.json](evaluation/live-memory-results.json) |
| AI-use disclosure | [docs/ai-use.md](docs/ai-use.md) |
| Interview code explanation | [docs/code-walkthrough.md](docs/code-walkthrough.md) |
| Demo questions and real traces | [docs/demo.md](docs/demo.md) |
| Complete requirement-to-file map | [docs/requirements-checklist.md](docs/requirements-checklist.md) |

## Architecture and responsibilities

The workflow is plain, sequential Python in `Assistant.ask()`; it does not use LangGraph or a hidden orchestration framework.

**UI → user memory/context → local retrieval → Research draft → Verifier/revision → cited answer → persistence**

| Role | Decision it owns | Implementation |
|---|---|---|
| Memory agent | Resolve follow-ups; propose safe user context and corrections | `MemoryAgent.plan()` plus SQLite controls |
| Research agent | Draft supported claims from retrieved company evidence | Research prompt and `_research_and_verify()` |
| Evidence Verifier | Reject unsupported, incomplete or incorrectly scoped claims; request one repair | Deterministic quote/ID checks plus a separate verification model call |

Answer formatting is deterministic, not a fourth model agent. It emits citations such as **[pricing:0 \| Plans and billing]**. User memory never establishes company facts. Retrieval preserves all original metadata; the UI shows source URLs even though repeated URLs are omitted from model prompts to save quota.

## Quick start

Requires **Python 3.12**. These commands work from the repository root.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.lock.txt
Copy-Item .env.example .env
```

On macOS/Linux, use `source .venv/bin/activate` and `cp .env.example .env` instead.

The example defaults to local Ollama. Install Ollama, start its local service and pull the configured model:

```text
ollama pull llama3.1:8b
```

If the service is not already running, use `ollama serve` in a separate terminal. Generation requires the downloaded model and sufficient local memory; no generation API key is needed. This repository's actual live evaluation used Groq; the Ollama adapter has protocol-level automated tests, not a claimed live Ollama evaluation.

After selecting a provider in `.env`, launch with one command:

```text
python launch.py
```

Open **http://127.0.0.1:8501**. Without credentials, you can already browse all source documents and manage memory. Research requires a working generation provider; there is no simulated production answer mode.

On macOS/Linux you can equivalently run `sh run.sh` after activating the environment. The portable `python launch.py` command works on all platforms.

### Generation options

| Option | Configuration | Account / cost |
|---|---|---|
| Local Ollama (default) | `LLM_PROVIDER=ollama`, `OLLAMA_MODEL=llama3.1:8b`, `OLLAMA_BASE_URL=http://localhost:11434` | Local inference; install Ollama and download the model. No paid API required. |
| OpenAI-compatible API (optional) | `LLM_PROVIDER=openai`, `OPENAI_MODEL`, `OPENAI_API_KEY`, `OPENAI_BASE_URL` | The example includes Groq's compatible endpoint; stay on its rate-limited Free Plan. Other providers may charge. JSON object mode and temperature 0 must be supported. |

Existing `.env` files using `GENERATION_PROVIDER` and `MODEL_NAME` continue to work. Documented provider-specific names take precedence when both are set. Your existing local credentials are not changed by this update.

| Other environment setting | Purpose / default |
|---|---|
| `EMBEDDING_MODEL` | Local `sentence-transformers/all-MiniLM-L6-v2` ONNX weights |
| `RUNTIME_DIR` | Generated vectors, models and SQLite data; default `runtime/`, ignored by Git |
| `RETRIEVAL_MODE` | `hybrid` (improved) or `dense` (baseline) |
| `PROVIDER_TIMEOUT_SECONDS` / `PROVIDER_MAX_RETRIES` | Bounded provider timeout/retries; defaults 45 / 2 |
| `LANGSMITH_TRACING` / `LANGSMITH_API_KEY` | Enable tracing and supply a private key; no export occurs without a key |
| `LANGSMITH_PROJECT` / `LANGSMITH_ENDPOINT` | Trace destination; see `.env.example` |

Embedding inference always runs locally using FastEmbed ONNX `sentence-transformers/all-MiniLM-L6-v2`. First research use downloads approximately 90 MB of weights into `runtime/models/`. No embedding API key is required. To prepare the model and Chroma index in advance:

```text
python -m scripts.prepare
```

The application uses SQLite for memory/history and Chroma for company evidence under ignored `runtime/`. Keep the server bound to localhost. The user selector simulates identities; it is not production authentication.

## Try it

1. Ask: **What is the current weekly on-call stipend? Why does the runbook disagree?** Expect the current $175 figure with the handbook and older $140 runbook explained.
2. Ask: **For Team, compare searchable run-record retention with Run Explorer timeline retention. Can cold storage extend the timeline?** The concepts must remain distinct.
3. Send `/remember workspace_plan=Team`, then open a new conversation and ask **What warehouse destinations can my plan use?** Restart the app and repeat.
4. Send `/correct workspace_plan=Enterprise` and ask the same question. The older Team context must not govern it.
5. Switch to Bob. Alice's memories and conversation history must not appear.
6. Delete memory through the sidebar or `/forget workspace_plan`. Old chat history is cleared to prevent the forgotten context returning.
7. Ask **Is Asterline HIPAA certified?** The corpus does not establish that certification; the answer should acknowledge the evidence gap.

Expand **Agent decisions** and **Evidence passages** to inspect the latest research. Every factual claim requires a known chunk ID and verbatim evidence quote before independent semantic review. One rejected draft can be revised; a second rejection produces a safe failure rather than an unverified answer.

## Memory controls

| Operation | Command / UI |
|---|---|
| Inspect | Your memory sidebar, with provenance and update time |
| Remember | `/remember workspace_plan=Team`, or sidebar form |
| Correct | `/correct workspace_plan=Enterprise`, or replace the value in the form |
| Forget one item | `/forget workspace_plan`, or its Forget button |
| Forget all | `/forget all`, or the sidebar's explicit clear control |
| Disable automatic memory writes | Turn off **Remember useful context**; explicit commands still work |

Allowed keys: `workspace_plan`, `project_region`, `project_name`, `response_style`, `work_goal`. The Memory agent can also propose these from clear user statements. Only source-backed proposals from the current message are eligible; company facts, hypotheticals, secrets and sensitive details are excluded. Automatic extraction is model-dependent and tested separately from deterministic storage guarantees.

All memory/history operations include the selected user ID. Sessions persist. Cross-session memory is selective; the entire previous conversation is not copied into every new session. Corrections and forgetting clear that user's past messages across sessions, while preserving other users' data. This deliberately sacrifices old conversation history to prevent stale context being reused. Forgetting is local; previously exported LangSmith traces must be managed separately in LangSmith.

## Evaluation and verification

```text
python -m pytest tests -q
python -m scripts.evaluate
```

The default evaluation runs **real local embeddings against the original corpus**, without a generation key. Results are committed in [evaluation/results.json](evaluation/results.json). It compares dense retrieval, lexical fusion alone, and the final comparison-aware retrieval at the same eight-chunk budget.

The deterministic suite covers provider/configuration compatibility, exact citation formatting, natural forgetting, storage/privacy, agent handoffs and actual Streamlit AppTest execution. The one-command launch also passed HTTP health and HTML endpoint checks (`python -m scripts.smoke_server` against a running server).

`python tests/run_eval.py` is an equivalent entry point for the same evaluator. The single canonical question set is `evaluation/cases.json`; there is no duplicate question file to drift out of sync. Every local evaluation also writes the explicitly named `evaluation/baseline.json` and `evaluation/improved.json`.

| Metric, 24 research cases | Dense baseline | Final retrieval |
|---|---:|---:|
| All expected evidence retrieved | 23/24 (95.83%) | 24/24 (100%) |
| Mean expected-evidence recall | 98.61% | 100% |
| Mean reciprocal rank | 0.9375 | 0.8948 |

The improvement trades some first-hit ranking for complete evidence coverage. These are **retrieval metrics, not answer accuracy**. The small, authored benchmark does not establish generalization. See [failure analysis](evaluation/analysis.md).

To reproduce the actual answer and conversational-memory evaluations:

```text
python -m scripts.evaluate --live --output evaluation/live-results.json
python -m scripts.evaluate_memory --output evaluation/live-memory-results.json
```

Use `--limit 3` on `scripts.evaluate --live` for a small initial provider check. Live research can make three generation calls per question, or up to five with a revision. Review live answers manually: regex checks and model verification are imperfect proxies. Deterministic tests use explicit fixture responses and **do not measure real LLM quality**.

## LangSmith observability

Set `LANGSMITH_TRACING=true`, `LANGSMITH_API_KEY` and `LANGSMITH_PROJECT` in `.env`, then restart. Use synthetic user data only. Traces contain the root question, Memory agent decision, retrieval IDs/dates, Research draft, Verifier approval/rejection, revision feedback and final status. User identifiers are hashed; common credential/email formats are redacted. No API key is intentionally serialized.

After live evaluation, capture successful, conflict, memory-continuity and difficult/failed runs in [docs/runs.md](docs/runs.md). Grant the assignment reviewer access to the project or provide an accessible project link. A locally displayed trace ID alone does not prove a run was uploaded or is accessible.

**Submission evidence:** see [SUBMISSION.md](SUBMISSION.md) for actual live results, verified public LangSmith links and the free-tier reviewer-access limitation. The public links share individual synthetic runs; they do not grant whole-project membership.

Historical live JSON outputs and their public traces are preserved as recorded. Older runs use the earlier source-label display; current answers use `[chunk_id | title]`. The review/readability update does not rewrite historical model evidence or invent new scores.

## Limitations and AI use

The user selector is a local demonstration, not authentication. SQLite is unencrypted. Forgetting removes local context but not exported traces. Corrections clear old conversations to prevent stale values returning. One generation model serves three distinct roles, so correlated mistakes remain possible; deterministic citation/quote checks cannot establish semantic correctness. The documented live service-credit example still omits a numerical calculation. The small authored evaluation is not a guarantee of unseen-question accuracy.

Codex helped implement, document and test the system. Automated tests, real retrieval runs and live Groq/LangSmith checks are recorded. Candidate personal review is not assumed: use the checklist in [docs/ai-use.md](docs/ai-use.md) before claiming you personally reviewed or ran anything.

## How to explain this project in 2 minutes

“This is a Streamlit research assistant with a plain Python workflow and three distinct agent roles. The Memory agent resolves follow-ups using only the selected user's context. A local MiniLM sentence-transformer, running through ONNX, and a persistent Chroma database retrieve company evidence; lexical fusion and comparison facets improve source coverage. The Research agent drafts claims with quotations. Deterministic checks validate source IDs and exact evidence, and a separate Verifier checks dates, scope, supersession and support. Rejected drafts get one repair attempt. The answer renderer cites chunk IDs and titles. User context lives separately in SQLite and never becomes company truth. Memory survives restarts, supports corrections and forgetting, and is isolated by user. LangSmith records each decision. Evaluation compares a dense baseline with improved retrieval and separately tests live answers and memory. The failure analysis includes real mistakes and limitations.”

For interview preparation, read this section, [the code walkthrough](docs/code-walkthrough.md), then `src/agents.py`, `src/memory.py` and `src/retrieval.py` in that order.

## Repository guide

- [Design and architecture](docs/design.md): agent contracts, information flow, memory policy and limitations.
- [Evaluation and failure analysis](evaluation/analysis.md): metrics, reproducible improvement and known weaknesses.
- [Walkthrough](docs/demo.md): a short, reproducible demonstration and ownership questions.
- [Trace evidence](docs/runs.md): actual research and memory runs for review.
- [AI-use disclosure](docs/ai-use.md): assistance used and how the output was checked.
- `data/corpus.jsonl`: original 75 chunks from 25 documents, byte-for-byte preserved; SHA-256 recorded in `data/corpus.sha256` and enforced at load.

## Troubleshooting

- **Provider not configured:** copy `.env.example` to `.env`; set a valid API key or start Ollama and pull your chosen model. Restart after changing configuration.
- **Model download fails:** allow the Hugging Face/model storage download, then rerun `python -m scripts.prepare`. After caching, embeddings need no remote inference service.
- **401 / 403:** check the key, model access and endpoint. Raw provider response bodies are not shown or saved.
- **429 / 5xx / timeout / upstream disconnect:** bounded retries honor numeric `Retry-After` with a sixty-second cap; failures show useful errors and do not save a new answer or automatic memory update. Resume interrupted research evaluations with `--resume` to retain completed cases.
- **Invalid JSON / rejected answer:** choose a model that follows the structured schema, inspect evidence, or narrow the question. Verification is intentionally conservative.
- **Corpus integrity error:** restore the original file from Git. Do not edit or reformat it.
- **Fresh local demo:** stop the app and remove your generated `runtime/` directory yourself if a clean state is needed. This deletes local memories and cached artifacts; it does not remove shared traces.

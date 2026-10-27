# Asterline Research Assistant

A research assistant that answers from Asterline's supplied company documents, explains conflicting evidence, and remembers useful workspace context across conversations and application restarts.

**Three collaborating agents · Local embeddings and vector storage · Persistent, user-scoped memory · Evidence verification · Opt-in LangSmith traces**

## Quick start

Requires **Python 3.12**. These commands work from the repository root.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.lock.txt
Copy-Item .env.example .env
```

On macOS/Linux, use `source .venv/bin/activate` and `cp .env.example .env` instead.

Configure one generation provider in `.env`, then launch with one command:

```text
python launch.py
```

Open **http://127.0.0.1:8501**. Without credentials, you can already browse all source documents and manage memory. Research requires a working generation provider; there is no simulated production answer mode.

### Generation options

| Option | Configuration | Account / cost |
|---|---|---|
| OpenAI or compatible API | `GENERATION_PROVIDER=openai`, `OPENAI_API_KEY`, `MODEL_NAME`, `OPENAI_BASE_URL` | Account/API key; provider usage charges may apply. Model must support Chat Completions JSON object mode and temperature 0. |
| Local Ollama | `GENERATION_PROVIDER=ollama`, `MODEL_NAME=llama3.2`, `OLLAMA_BASE_URL=http://localhost:11434` | Install Ollama and pull the selected model first. Generation runs locally; needs sufficient memory/CPU/GPU. No paid API required. |

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

Local verification completed with **32 passing tests**, including actual Streamlit AppTest execution. The one-command launch also passed HTTP health and HTML endpoint checks (`python -m scripts.smoke_server` against a running server).

| Metric, 24 research cases | Dense baseline | Final retrieval |
|---|---:|---:|
| All expected evidence retrieved | 23/24 (95.83%) | 24/24 (100%) |
| Mean expected-evidence recall | 98.61% | 100% |
| Mean reciprocal rank | 0.9375 | 0.8948 |

The improvement trades some first-hit ranking for complete evidence coverage. These are **retrieval metrics, not answer accuracy**. The small, authored benchmark does not establish generalization. See [failure analysis](evaluation/analysis.md).

Once generation credentials are configured, run actual answer and conversational-memory evaluations:

```text
python -m scripts.evaluate --live --output evaluation/live-results.json
python -m scripts.evaluate_memory --output evaluation/live-memory-results.json
```

Use `--limit 3` on `scripts.evaluate --live` for a small initial provider check. Live research can make three generation calls per question, or up to five with a revision. Review live answers manually: regex checks and model verification are imperfect proxies. Deterministic tests use explicit fixture responses and **do not measure real LLM quality**.

## LangSmith observability

Set `LANGSMITH_TRACING=true`, `LANGSMITH_API_KEY` and `LANGSMITH_PROJECT` in `.env`, then restart. Use synthetic user data only. Traces contain the root question, Memory agent decision, retrieval IDs/dates, Research draft, Verifier approval/rejection, revision feedback and final status. User identifiers are hashed; common credential/email formats are redacted. No API key is intentionally serialized.

After live evaluation, capture successful, conflict, memory-continuity and difficult/failed runs in [docs/runs.md](docs/runs.md). Grant the assignment reviewer access to the project or provide an accessible project link. A locally displayed trace ID alone does not prove a run was uploaded or is accessible.

**Submission status:** local implementation, deterministic tests and retrieval benchmark are complete. Real-provider answer/memory evaluation and accessible LangSmith run links remain pending until you configure credentials. Do not submit the pending trace checklist as completed evidence.

## Repository guide

- [Design and architecture](docs/design.md): agent contracts, information flow, memory policy and limitations.
- [Evaluation and failure analysis](evaluation/analysis.md): metrics, reproducible improvement and known weaknesses.
- [Walkthrough](docs/demo.md): a short, reproducible demonstration and ownership questions.
- [Trace evidence and final checklist](docs/runs.md): remaining credential-dependent submission steps.
- [AI-use disclosure](docs/ai-use.md): assistance used and how the output was checked.
- `data/corpus.jsonl`: original 75 chunks from 25 documents, byte-for-byte preserved; SHA-256 recorded in `data/corpus.sha256` and enforced at load.

## Troubleshooting

- **Provider not configured:** copy `.env.example` to `.env`; set a valid API key or start Ollama and pull your chosen model. Restart after changing configuration.
- **Model download fails:** allow the Hugging Face/model storage download, then rerun `python -m scripts.prepare`. After caching, embeddings need no remote inference service.
- **401 / 403:** check the key, model access and endpoint. Raw provider response bodies are not shown or saved.
- **429 / 5xx / timeout:** bounded retries honor numeric `Retry-After` with a ten-second cap; failures show useful errors and do not save a new answer or automatic memory update.
- **Invalid JSON / rejected answer:** choose a model that follows the structured schema, inspect evidence, or narrow the question. Verification is intentionally conservative.
- **Corpus integrity error:** restore the original file from Git. Do not edit or reformat it.
- **Fresh local demo:** stop the app and remove your generated `runtime/` directory yourself if a clean state is needed. This deletes local memories and cached artifacts; it does not remove shared traces.

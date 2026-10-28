# Code walkthrough for interview preparation

## Reading order

1. README's two-minute explanation and reviewer table.
2. `src/agents.py`: read `Assistant.ask()` first, then follow its helper calls.
3. `src/memory.py`: understand the three SQLite tables and why deletion clears history.
4. `src/retrieval.py`: understand local embeddings, ranking and the measured improvement.
5. `src/provider.py` and `src/tracing.py`: generation failure boundaries and trace export.
6. The tests and `evaluation/analysis.md`: explain what is proven and what remains uncertain.

Do not say this is a LangGraph application. The working architecture is an explicit sequential Python workflow. An extra `graph.py` or fourth answer model would add indirection without helping this MVP.

## Follow one question through the code

For “My workspace uses Team. Which Warehouse Export destinations can I use?”:

1. `app.py` supplies a selected user ID, that user's session ID, question and memory toggle to `Assistant.ask()`.
2. `MemoryStore.history()` checks session ownership before data is read. Privacy checks reject common credentials/sensitive details before any model or trace call.
3. Commands such as forgetting are deterministic. Otherwise only this user's memories and current-session history are loaded. Missing private plan context can produce a local clarification.
4. `MemoryAgent.plan()` resolves a search question and proposes a `workspace_plan=Team` update backed by an exact quote from the current user message. Proposed memory is not yet written. An unrelated placeholder query falls back to the actual question.
5. `_retrieve()` calls `Retriever.search()` and `expand_scope()`. These return original company chunks and metadata, not old assistant answers or user memory.
6. `_research_and_verify()` makes a Research call, validates the result with `validate_draft()`, then makes a separate Verifier call. Rejection feeds issues back for one revision; a second rejection returns a safe failure.
7. `render_draft()` formats supported claims with `[chunk_id | title]`. It is deterministic presentation, not a fourth agent.
8. Only after approval are proposed memories upserted and the question/answer pair stored. LangSmith spans record decisions, source IDs, draft, review and final status.

## Application and source files

| File | Why it exists / main functions | Input → output | Connections |
|---|---|---|---|
| `launch.py` | Starts Streamlit through the active Python interpreter | CLI options → localhost server | Launches `app.py`; one portable command |
| `run.sh` | Small Unix convenience wrapper | CLI options → same launch command | Delegates to `launch.py`; does not create another startup path |
| `app.py` | `main()` assembles `render_sidebar()`, `render_conversation()`, `render_sources()` and `render_help()`; `get_retriever()` caches heavy resources; `LazyRetriever` delays model loading | UI selection/message → `Result` displayed to selected user | Calls config, store, provider, assistant and tracer; UI sections have named responsibilities |
| `src/config.py` | `Settings` holds runtime choices; `from_env()` resolves documented variables and legacy aliases; `provider_problem()` reports missing API configuration safely | `.env` / environment → immutable settings | Used by app and scripts; secrets excluded from repr |
| `src/provider.py` | `GenerationProvider.complete()` implements Ollama and OpenAI-compatible JSON requests; `parse_json()` checks response shape; `ProviderError` is safe to display | Role prompt + payload → dictionary, or safe error | Uses settings, bounded retries and timeouts; tests substitute only the HTTP transport |
| `src/retrieval.py` | `load_corpus()` enforces the hash; `tokens()` and `query_facets()` prepare search; `Retriever` indexes local vectors, ranks with dense/lexical fusion and expands document scope | Question → original evidence dictionaries | FastEmbed runs MiniLM ONNX locally; Chroma persists under ignored `runtime/`; corpus is never edited |
| `src/memory.py` | `MemoryStore` owns SQLite; `new_session`, `history`, `memories`, `save_many`, `forget` cover the lifecycle | User/session and safe values → user-scoped records | Every operation includes user ID; corrections/deletion clear that user's historical context |
| `src/agents.py` | Agent prompts; `MemoryAgent.plan`; `source_quote`, `validate_draft`, `render_draft`; `Assistant` coordinates named steps | User question + context + evidence → `Result` | `_clarify_missing_plan`, `_retrieve`, `_research_and_verify` make control flow explicit; no base classes or inheritance framework |
| `src/privacy.py` | `contains_secret`, `safe_memory`, `redact` implement conservative heuristics | Text → refusal decision or redacted text | Runs before provider/storage and before trace export; not comprehensive DLP |
| `src/tracing.py` | `Tracer.span()` creates nested, opt-in LangSmith spans; `clean()` redacts nested content; `user_tag()` hashes IDs | Explicit inputs/outputs → inspectable trace IDs | No automatic Settings/header serialization; disabled tracing does not call the service |
| `src/__init__.py` | Identifies the application package | Import → package namespace | No startup side effects |

The three agent roles use separate prompts/calls, not three different model providers. Research and Verifier are explicit steps inside `_research_and_verify()`, so there are no unnecessary thin subclasses to navigate.

## Memory schema and guarantees

- `sessions`: `(user_id, session_id, created_at)` identifies ownership.
- `messages`: user, session, role, content and timestamp retain current-session conversation.
- `memories`: `(user_id, key)` is a unique key; value, provenance and update time explain what is stored.
- `save_many()` upserts rather than accumulates contradictory versions. Replacing a value clears that user's old messages.
- `forget()` deletes selected/all memories and that user's old messages, preventing history from silently restoring a deleted value. Other users are unaffected.
- No memory update or answer is saved after a failed provider/verification path. Explicit commands work without a model.

## Evaluation and utility scripts

| File | What to explain |
|---|---|
| `scripts/evaluate.py` | `retrieval_metrics()` compares modes against expected chunk IDs; `live_metrics()` uses synthetic users and a temporary DB; `generation_report()` keeps answer checks separate; `write_comparison_artifacts()` writes measured baseline/improved files. `main()` handles options/checkpoints. |
| `tests/run_eval.py` | Familiar alternate command that delegates to the same evaluator. No duplicated scoring logic. Canonical cases remain in `evaluation/cases.json`. |
| `scripts/evaluate_memory.py` | Runs the actual-provider conversation sequence, reconstructs storage/orchestrator for restart continuity, then checks correction, user isolation and forgetting. Explicit deletion and missing-context clarification are local decisions. |
| `scripts/prepare.py` | Verifies corpus, downloads embedding weights if needed and builds Chroma once. |
| `scripts/extract_corpus.py` | One-time extraction of the original PDF attachment with its known hash. Only this optional developer utility requires `pypdf`; normal setup already includes the original corpus. |
| `scripts/check_connections.py` | Tiny actual generation request and LangSmith upload/read-back check. A connection check is not research-quality evidence. |
| `scripts/smoke_server.py` | Checks health and HTML of an already running localhost server. |
| `scripts/share_evaluation_runs.py` | Explicit `--share` publishes only allowlisted synthetic evaluation runs, scans for configured credentials, reuses existing links and checks public access without authentication. It must not be used to publish personal conversations. |
| `scripts/prepare_submission.py` | Builds the submission index/run table from actual saved artifacts. Does not fabricate scores. |
| `scripts/check_submission.py` | Verifies corpus hash, required files, completed evaluations, public evidence and absence of configured credentials in tracked files. |
| `scripts/__init__.py` | Enables `python -m scripts.NAME`; no runtime business logic. |

## Tests: know which ones use test doubles

| File | Guarantee / limit |
|---|---|
| `tests/test_memory.py` | Real temporary SQLite: restart, isolation, correction, individual/all deletion and unsafe-memory refusal. |
| `tests/test_agents.py` | Clearly labelled fixture providers/retrievers test role handoffs, repair, consent, failure paths, quote validation, exact citation style and natural forgetting. They do not measure model quality. |
| `tests/test_provider.py` | Mock HTTP transport tests JSON protocols, retry bounds, authentication failure and disconnect safety. No paid API calls. |
| `tests/test_config.py` | Isolated environment verifies Ollama default and legacy/new variable precedence without personal credentials. |
| `tests/test_retrieval.py` | Original corpus integrity and query decomposition. Actual embedding benchmark is separate. |
| `tests/test_privacy.py` | Redaction, memory exclusions and disabled tracing. Heuristics cannot recognize every secret. |
| `tests/test_ui.py` | Real Streamlit AppTest: page loads, user switching and local clarification visibility. |
| `tests/test_evaluation.py` | Named baseline/improved exports preserve measured summaries/cases instead of inventing scores. |

## Explain the artifacts and limitations

`baseline.json` and `improved.json` are measured retrieval runs at the same budget. `results.json` also retains the intermediate lexical-fusion comparison. Actual model answers live in `live-results.json`; memory assertions in `live-memory-results.json`. Before-fix files preserve observed failures. `manual-review.json` explains regex false alarms and the remaining numerical-example omission. Original live outputs/traces are historical evidence; they are not rewritten when presentation changes.

Expect to explain why valid citations are not proof of semantic correctness, why a later general overview need not supersede a specific policy, why forgetting exported traces is separate, and why a demo user selector is not authentication. The free LangSmith account provides public individual traces, not an additional reviewer seat.

# Evaluation, failure analysis and improvement

## What was actually run

The committed `results.json` was generated using real local FastEmbed MiniLM embeddings and a persistent local Chroma index, on the unchanged 75-chunk corpus. After generation credentials were configured, the actual Groq research suite and conversational-memory sequence were also run. See `live-results.json`, `live-memory-results.json` and the submission index for their outcomes and verified public traces. Retrieval metrics below remain distinct from live answer checks.

The deterministic pytest suite separately verifies memory persistence/isolation/correction/deletion, privacy checks, provider retry/error handling, three-role handoffs, rejected-draft repair and UI user switching. Fixture providers are explicitly named fixtures; their responses are not model-quality evidence.

## Cases and metrics

`cases.json` contains 24 authored research questions: 16 development cases and eight reserved cases. Development covers conflicting dates/policies, plan/scope distinctions, historical versions, incident fixes, missing facts and unknown commercial commitments. Reserved cases cover credits, HTTP acceptance semantics, anomaly warmup, warehouse deletion, incident cause, query caching, batch size and SDK buffering.

Each case names expected source chunks and answer patterns. A case's expected source list is a useful ground truth, not the only possible evidence set: a valid answer may cite equivalent release notes. Review apparent live failures manually.

- **Mean expected-evidence recall @8:** mean fraction of expected chunks present. Measures coverage needed for synthesis.
- **All-evidence rate @8:** fraction of questions for which every specified passage was retrieved. A conflict answer needs both sides.
- **MRR @8:** reciprocal rank of the first expected passage. Measures early relevance but not complete reasoning support.
- **Live-only pattern checks:** presence of expected numbers or caveats. Limited proxies, not semantic correctness.
- **Live-only expected-source coverage and citation-ID validity:** distinguish retrieval misses, missing citations and fabricated references. IDs existing in the corpus do not prove entailment.
- **Memory tests:** persistent values after restart, disallowed cross-user/session operations, replacement rather than accumulation, deletion without history resurrection and refusal to retain unsafe information.

## Results at the same eight-chunk retrieval budget

| Method | Mean evidence recall | All evidence | MRR |
|---|---:|---:|---:|
| Dense baseline | 0.9861 | 23/24 | 0.9375 |
| Dense + lexical fusion only | 0.9861 | 23/24 | 0.8948 |
| Fusion + comparison facets + document diversity | 1.0000 | 24/24 | 0.8948 |

The eight reserved questions retained 100% expected-evidence coverage. This is a small authored suite, not an independent external benchmark or evidence of perfect answers. The final algorithm was informed by development failures; new unseen conversation sequences remain necessary.

## Observed failure and measured improvement

Question: **For Team, compare searchable run-record retention with Run Explorer timeline retention. Can cold storage extend the timeline?**

The dense baseline retrieved `retention:2`, `traces:1`, `retention:0`, `security:1`, `release-22:1`, `retention:1`, `onboarding:2`, and `architecture:1`. It missed `pricing:1`, the passage with Team's 180-day searchable retention. Similar wording clustered retrieval around timelines and cold storage. A model could therefore explain the concepts yet fail to support the advertised searchable period.

Adding lexical fusion alone did not recover the passage and lowered first-hit ranking overall. Rather than claiming it was an improvement, the benchmark records it separately.

The final change splits explicit comparison facets and avoids letting several passages from the same document crowd out another applicable document. It retrieves the missing pricing passage within the same eight initial slots, raising all-evidence coverage from 23/24 to 24/24. Full text and metadata remain unchanged. No answer or query-ID lookup table was added.

An intermediate regression treated short incidental questions as independent facets; that displaced relevant duplicate-export cleanup evidence. Facet construction now requires substantial standalone clauses while retaining short explicit comparison subjects. The committed results reflect the corrected implementation. Query-decomposition and incident cases guard this behaviour.

## Failure paths tested without an API

- Fabricated chunk ID: rejected deterministically, feedback reaches a second Research draft, and a supported revision is accepted.
- Incorrect evidence quote: rejected even when the chunk ID exists.
- Verifier rejects both drafts: no unverified answer or automatic memory is saved.
- Provider failure / 503 / 429 / 401: bounded retries where appropriate, useful safe errors, no raw body disclosure.
- User Bob requests Alice's session: rejected before conversation access or model calls.
- Correction / forgetting: old context cleared across sessions, other users preserved, deleted context not reinserted as a command transcript.

The cases in this subsection are injected failures testing code paths. Actual hosted-model and transport failures are described below and preserved separately.

## Actual live failures and fixes

- **Unrelated query rewrite:** the context model sometimes copied the schema's example phrase, "standalone company research question", causing retrieval to return generic company material and then an unnecessary abstention. `live-before-fixes.json` preserves these outcomes. The prompt now uses a concrete grounded example, and a deterministic guard rejects unrelated/placeholder rewrites. Subsequent cold-storage and stipend conflict answers retrieve and cite the applicable current and older documents.
- **Upstream disconnect and free-tier limits:** an HTTP protocol disconnect originally escaped the narrower network-error handler. The provider now catches transport errors, retries within limits and returns a safe failure. Numeric Retry-After is honored up to sixty seconds; the evaluation saves after each case and can resume without rerunning completed questions. Actual transient provider failures are preserved in `live-after-query-fix.json` and the first memory-run artifact.
- **Typographic quote rejection:** the duplicate-export answer used a non-breaking hyphen in "pre-existing" while the corpus used ASCII. Both drafts failed the exact quote check despite matching words. A narrow matcher now canonicalizes only whitespace and typographic hyphen variants to the exact source substring; changed words or numbers remain invalid. A regression test covers both accepted typography and rejected semantic changes.
- **Missing private context:** after forgetting, or for a different user, a personal plan question should not depend on a remote provider or guess from company documentation. A local context guard now asks which plan the user uses when neither durable memory nor the current user's conversation has a plan hint. This is tested with an unavailable provider and Alice's context present only in Alice's store.
- **Incomplete numeric answer (remaining limitation):** the service-credit answer describes the highest-tier rule without computing the 50% tier for the supplied 98.8% uptime example. The research contract was strengthened and the case rerun, but the recorded final answer still omits this calculation. This partial answer remains visible rather than being marked successful.

Some authored regex checks are stricter than the actual question. The Team/Redshift case expects the word "Enterprise" even though a correct response can simply reject Redshift for Team and list BigQuery/Snowflake. The batch-size pattern expects an ASCII space, while a supported answer may render a narrow no-break space in "1 MB". Keep those automatic outcomes visible and distinguish manual review from pattern scores; do not claim the regex suite alone establishes semantic accuracy.

## Final live results

The final 24-question research artifact records 21/24 automatic pattern passes, zero provider errors, zero verification failures and valid corpus chunk IDs in every answer. Two pattern misses are false alarms described above; the service-credit numerical example remains incomplete. `manual-review.json` records these distinctions as Codex-assisted review, not an independent human accuracy score.

The final actual-provider memory sequence passes 6/6 checks: automatic context, new-session continuity after reopening storage, correction, cross-user isolation, forgetting, and no resurrection after reopening. Missing personal context and explicit forgetting use deterministic local controls; they do not need generation calls. The earlier network-failure outcomes are preserved in `live-memory-before-network-retry.json`.

Public representative runs, including before-fix failures, are linked from the submission index after unauthenticated access checks. The account's one-seat free tier does not provide whole-project membership to an additional reviewer; public individual traces are the supplied review mechanism.

## Readability update verification

`baseline.json` and `improved.json` now expose the measured local retrieval runs directly under the requested names; the evaluator regenerates them rather than maintaining hand-copied scores. The compact workflow has named context, retrieval, research/review and formatting steps. One post-change actual Groq question is recorded separately in `readability-smoke.json` to check the refactored flow and `[chunk_id | title]` presentation. Earlier full model evaluations remain as originally recorded. Ollama is the new-install default; existing compatible-provider variables remain supported. Ollama protocol tests are mocked, and no live local-model score is claimed.

## Reproduce and extend

```text
python -m pytest tests -q
python -m scripts.evaluate
python -m scripts.evaluate --live --output evaluation/live-results.json
python -m scripts.evaluate_memory --output evaluation/live-memory-results.json
```

The first retrieval run downloads model weights. Live research uses isolated temporary users/databases; it does not touch application memory. Shared traces should use synthetic data. Record model name, configuration, run links, failed cases and any subsequent improvements with their actual results. Inspect abstentions and false-confidence cases manually. Particularly test ambiguous pronouns, denied/hypothetical memory statements, adversarial documentary text and multi-step corrections.

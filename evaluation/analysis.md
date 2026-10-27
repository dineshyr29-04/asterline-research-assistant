# Evaluation, failure analysis and improvement

## What was actually run

The committed `results.json` was generated using real local FastEmbed MiniLM embeddings and a persistent local Chroma index, on the unchanged 75-chunk corpus. No generation API credentials were available. **No real-provider answer accuracy, automatic memory quality or successful LangSmith upload is claimed.**

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

These are injected failures testing code paths. They are not examples of actual hosted model failures.

## Reproduce and extend

```text
python -m pytest tests -q
python -m scripts.evaluate
python -m scripts.evaluate --live --output evaluation/live-results.json
python -m scripts.evaluate_memory --output evaluation/live-memory-results.json
```

The first retrieval run downloads model weights. Live research uses isolated temporary users/databases; it does not touch application memory. Shared traces should use synthetic data. Record model name, configuration, run links, failed cases and any subsequent improvements with their actual results. Inspect abstentions and false-confidence cases manually. Particularly test ambiguous pronouns, denied/hypothetical memory statements, adversarial documentary text and multi-step corrections.

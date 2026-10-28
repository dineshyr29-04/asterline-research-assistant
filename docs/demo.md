# Five-minute walkthrough

Before starting: configure generation and LangSmith, run `python -m scripts.prepare`, then `python launch.py`. Use only synthetic identities. Verify traces are actually visible in the configured project.

## Representative questions and expected behaviour

| Say / ask | What to demonstrate |
|---|---|
| What does Team cost and what retention does it include? | $449/month and 180-day searchable retention with pricing citations |
| How long is cold recovery storage? I found an old page saying 60 days. | Current 20-day period and explicit supersession of the older 60-day statement |
| What changed in patch 2.1.2? | Stable export deduplication; existing duplicate rows still required cleanup |
| Were alerts lost in INC-2026-03? | Delayed, not lost; correct incident and patch evidence |
| When will APAC launch? | No announced date; do not invent one |
| Remember that my workspace uses Team. | Propose safe user context, not company truth |
| Actually I moved to Enterprise. | Replace the plan and invalidate stale history |
| Forget my workspace plan. | Delete the plan and old history; this natural request works without a model |

## Actual trace examples

- [Successful research run](https://smith.langchain.com/public/e489f47e-2d0c-4789-9b49-dda508fdcc0c/r).
- [Actual difficult before-fix run](https://smith.langchain.com/public/2d610436-d6f2-4325-8c9d-5941d28dc8a4/r): a copied query placeholder caused an inappropriate abstention; compare with the corrected conflict run in `docs/runs.md`.
- [Automatic memory run](https://smith.langchain.com/public/bff0cb15-809f-474d-9147-1656f82719a4/r).

These are recorded historical runs, not placeholders. Their older source-label style is preserved as evidence; the current renderer uses `[chunk_id | title]`.

## Five-minute route

1. **Grounded conflict (one minute).** Ask the current on-call stipend and why documents disagree. Open the handbook/runbook passages and show the exact IDs, dates and explicit supersession. Follow Memory → Retrieve → Research → Verifier in LangSmith.
2. **Research scope (one minute).** Compare Team searchable record retention, Explorer timeline retention and cold storage. Explain the retrieval failure found by evaluation and why comparison facets plus source diversity recovered the missing pricing evidence.
3. **Continuity (one minute).** As Alice, remember Team, ask about warehouse destinations, create a new conversation and ask a follow-up. Restart the server, reopen the same conversation and show that memory/history survived.
4. **Correction and isolation (one minute).** Correct Alice's plan to Enterprise. Show the single replaced value, invalidated old history and changed eligible destinations. Switch to Bob and demonstrate no inherited Alice context.
5. **Forget and uncertainty (one minute).** Delete Alice's plan, open a new session and ask a plan-dependent question; it should clarify rather than recover deleted context. Ask about HIPAA certification to demonstrate an evidence gap. Show an actual difficult/failed trace from live evaluation.

## Be ready to explain

- Why memory is separate from company evidence and previous answers cannot establish facts.
- Why "newest publication wins" would be wrong for a topic-specific policy conflict.
- Why deterministic quote validity is necessary but insufficient for semantic correctness.
- Where a user ID is applied in database operations and what the demo selector cannot secure.
- Why corrections and forgetting clear conversations, and what happens to exported traces.
- What the three agents contribute beyond labels, and how Verifier feedback changes Research.
- What the benchmark measures, what its MRR regression means, and why 100% retrieval is not perfect answer accuracy.
- How to investigate an unsupported answer using evidence, draft and review spans.

For a small new requirement, trace the responsible contract and add a meaningful regression case. Example: introducing another memory category requires a key allowlist change, Memory prompt change, privacy consideration, UI availability and a lifecycle test; it should not require changing the company corpus.

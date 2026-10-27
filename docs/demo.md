# Five-minute walkthrough

Before starting: configure generation and LangSmith, run `python -m scripts.prepare`, then `python launch.py`. Use only synthetic identities. Verify traces are actually visible in the configured project.

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

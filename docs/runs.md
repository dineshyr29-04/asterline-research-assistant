# Trace evidence and submission checklist

## Current status

Implementation, local retrieval evaluation and deterministic verification are present. Generation and LangSmith credentials were intentionally left for the candidate to configure. **Live model evaluation and remotely accessible runs are pending. No trace links below have been fabricated.**

## Complete after configuring credentials

1. Copy `.env.example` to `.env`; choose the generation provider/model.
2. Set `LANGSMITH_TRACING=true`, `LANGSMITH_API_KEY` and `LANGSMITH_PROJECT`; restart the application.
3. Run `python -m scripts.evaluate --live --output evaluation/live-results.json` and `python -m scripts.evaluate_memory --output evaluation/live-memory-results.json`.
4. Open the LangSmith project. Confirm the runs were uploaded, inspect nested agent spans and verify no secrets or real personal data are present.
5. Record actual links in the table below. Grant access to **radialpulse@nxtwave.co.in** or provide an accessible project link, as requested by the assignment. Confirm reviewer access rather than relying on your own authenticated browser.
6. Review failed/uncertain cases, retain representative failures honestly, and update analysis with model-specific findings.

| Required evidence | Actual accessible URL | What reviewer should inspect |
|---|---|---|
| LangSmith project | Pending credentials | Project access and all representative runs |
| Supported answer | Pending live run | Known chunk IDs, exact quotes, independent review |
| Temporal conflict | Pending live run | Effective date/scope and explicit supersession |
| Cross-session memory | Pending live run | Alice context retained after restart |
| Correction / forgetting / isolation | Pending live run | Replaced context, deleted history, Bob isolation |
| Difficult or failed case | Pending live run | Real model refusal/revision/failure and honest diagnosis |

Synthetic injected failures may be useful for debugging, but label them as injected; they do not replace a real difficult-case account. A trace ID created locally does not by itself establish remote upload or shared access.

## Final repository check

- [x] Working app and three distinct collaborating agents.
- [x] Unchanged original corpus, verified by SHA-256.
- [x] Local embedding inference and persistent local vector store.
- [x] User-scoped persistent memory and conversations, inspect/correct/forget controls.
- [x] Setup, tested dependency lock, one launch command and secret-free `.env.example`.
- [x] Design note with diagram, limitations and trade-offs.
- [x] Reproducible local retrieval evaluation with observed failure and measured improvement.
- [x] Deterministic provider, orchestration, memory, privacy and UI tests.
- [x] AI-use disclosure and walkthrough.
- [ ] Run and manually review actual provider research and memory evaluations.
- [ ] Add accessible LangSmith project/run links and confirm reviewer access.
- [ ] Review `git status`, ensure no secrets/generated user databases are staged, and push the final commits.

The assignment's deadline text says "Oct 27th (Wed) EOD". The supplied package preserves this wording; confirm the intended year/date with the issuer if it is ambiguous. Do not infer an extension from the weekday mismatch.

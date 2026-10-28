# AI-use disclosure

OpenAI Codex assisted with requirement analysis, architecture choices, implementation, documentation, authored evaluation cases, test creation and debugging. It used local terminal/file tools, Python/PDF extraction, pytest, Streamlit's AppTest and local embedding/retrieval runs.

Validation performed: extracted the PDF's original embedded corpus and checked its SHA-256 and 75-chunk/25-document counts; ran actual local-embedding retrieval comparisons; exercised SQLite persistence and user isolation; tested correction/forgetting, credential redaction, HTTP failure handling, citation/quote checks and repair handoffs; checked the Streamlit interface with AppTest.

Scripted model fixtures were used only for deterministic tests and are identified as such. After credentials were configured, Codex ran actual Groq research and memory evaluations and inspected LangSmith handoffs. Live failures exposed copied schema placeholders in query rewriting and an unhandled upstream disconnect; these led to code fixes and regression tests. Actual evaluation artifacts, including limitations and failures, are recorded under `evaluation/`. Public links are checked through unauthenticated requests before being listed as accessible; no whole-project reviewer invitation is claimed on the one-seat free plan.

The submitting candidate remains responsible for reviewing and understanding the code, running the credential-dependent evaluations, checking output and explaining the design during the walkthrough. Update this disclosure after additional validation or tools are used.

The readability pass added a requirement-to-file map, code walkthrough, explicit baseline/improved exports, Ollama-first configuration with legacy compatibility, named workflow helpers, the requested citation format and natural forgetting. Tests and a post-change smoke check verify these changes. The app uses plain Python orchestration, not LangGraph; local sentence-transformer inference uses FastEmbed ONNX rather than a hosted embedding API.

## Candidate ownership checklist — complete personally

These boxes are intentionally not marked by an AI assistant. They describe personal actions only the candidate can truthfully attest to:

- [ ] I read `docs/code-walkthrough.md` and followed the major source files.
- [ ] I ran the documented tests myself and understood what uses test doubles.
- [ ] I validated retrieval, correction, forgetting and user isolation in the app.
- [ ] I reviewed the actual evaluation results, false alarms and remaining numerical limitation.
- [ ] I followed a real LangSmith trace and can explain the verifier's decision.
- [ ] I checked generated output instead of blindly trusting it and can justify the design trade-offs.

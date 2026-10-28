# AI-use disclosure

OpenAI Codex assisted with requirement analysis, architecture choices, implementation, documentation, authored evaluation cases, test creation and debugging. It used local terminal/file tools, Python/PDF extraction, pytest, Streamlit's AppTest and local embedding/retrieval runs.

Validation performed: extracted the PDF's original embedded corpus and checked its SHA-256 and 75-chunk/25-document counts; ran actual local-embedding retrieval comparisons; exercised SQLite persistence and user isolation; tested correction/forgetting, credential redaction, HTTP failure handling, citation/quote checks and repair handoffs; checked the Streamlit interface with AppTest.

Scripted model fixtures were used only for deterministic tests and are identified as such. After credentials were configured, Codex ran actual Groq research and memory evaluations and inspected LangSmith handoffs. Live failures exposed copied schema placeholders in query rewriting and an unhandled upstream disconnect; these led to code fixes and regression tests. Actual evaluation artifacts, including limitations and failures, are recorded under `evaluation/`. Public links are checked through unauthenticated requests before being listed as accessible; no whole-project reviewer invitation is claimed on the one-seat free plan.

The submitting candidate remains responsible for reviewing and understanding the code, running the credential-dependent evaluations, checking output and explaining the design during the walkthrough. Update this disclosure after additional validation or tools are used.

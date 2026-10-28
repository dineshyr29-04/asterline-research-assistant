"""Actual-provider conversation sequences using a fresh, synthetic database."""
import argparse
import json
import re
import tempfile
from pathlib import Path

from src.agents import Assistant
from src.config import ROOT, Settings
from src.memory import MemoryStore
from src.provider import GenerationProvider, ProviderError
from src.retrieval import Retriever
from src.tracing import Tracer


def run(settings, retriever):
    rows = []
    provider = GenerationProvider(settings)
    tracer = Tracer(settings.tracing)
    with tempfile.TemporaryDirectory(prefix="asterline-memory-eval-") as directory:
        path = Path(directory) / "memory.sqlite3"
        store = MemoryStore(path)
        assistant = Assistant(store, retriever, provider, tracer)
        session = store.new_session("synthetic-alice")

        def ask(case_id, user, active_session, question, assertion):
            try:
                result = assistant.ask(user, active_session, question)
                passed = assertion(result)
                rows.append({"id": case_id, "passed": bool(passed), "status": result.status,
                             "answer": result.answer, "trace_id": result.trace_id,
                             "memory": store.memories(user)})
            except (ProviderError, ValueError) as exc:
                rows.append({"id": case_id, "passed": False, "status": "error", "error": str(exc),
                             "trace_id": assistant.tracer.last_trace_id})
            print(f"Live memory: {case_id} -> {rows[-1]['status']} (pass={rows[-1]['passed']})", flush=True)

        def memory_is(user, key, value):
            return any(r["key"] == key and r["value"] == value for r in store.memories(user))

        ask("automatic-context", "synthetic-alice", session,
            "My workspace uses Team. Please remember that. Which Warehouse Export destinations can I use?",
            lambda r: memory_is("synthetic-alice", "workspace_plan", "Team")
            and bool(re.search("BigQuery", r.answer, re.I)) and bool(re.search("Snowflake", r.answer, re.I)))

        # Reopen persistence and reconstruct the orchestrator, as after a process restart.
        store = MemoryStore(path)
        assistant = Assistant(store, retriever, provider, tracer)
        session = store.new_session("synthetic-alice")
        ask("restart-new-session-followup", "synthetic-alice", session,
            "How many days of searchable run-record retention does my plan include?",
            lambda r: memory_is("synthetic-alice", "workspace_plan", "Team") and "180" in r.answer)

        ask("automatic-correction", "synthetic-alice", session,
            "Correction: my workspace now uses Enterprise. Remember that instead of Team. How many days of searchable run-record retention does my plan include?",
            lambda r: memory_is("synthetic-alice", "workspace_plan", "Enterprise") and "540" in r.answer)

        bob = store.new_session("synthetic-bob")
        ask("cross-user-isolation", "synthetic-bob", bob,
            "What workspace plan do I use?",
            lambda r: store.memories("synthetic-bob") == [] and r.status == "abstained")

        ask("forget-command", "synthetic-alice", session, "/forget all",
            lambda r: store.memories("synthetic-alice") == [] and store.history("synthetic-alice", session) == [])

        store = MemoryStore(path)
        assistant = Assistant(store, retriever, provider, tracer)
        fresh = store.new_session("synthetic-alice")
        ask("forget-no-resurrection-after-restart", "synthetic-alice", fresh,
            "What workspace plan do I use?",
            lambda r: store.memories("synthetic-alice") == [] and r.status == "abstained")
    return {"label": "Actual-provider synthetic conversation sequences; manually review answers and traces",
            "model": settings.model, "provider": settings.provider,
            "passed": sum(row["passed"] for row in rows), "total": len(rows), "cases": rows}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "evaluation/live-memory-results.json")
    args = parser.parse_args()
    settings = Settings.from_env()
    if settings.provider_problem():
        parser.error(settings.provider_problem())
    result = run(settings, Retriever(settings))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Actual-provider memory sequences: {result['passed']}/{result['total']} checks passed")
    print("Results:", args.output)


if __name__ == "__main__":
    main()

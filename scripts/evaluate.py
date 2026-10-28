"""Reproducible retrieval benchmark; optional real-provider answer evaluation.

Run: python -m scripts.evaluate [--live] [--output evaluation/results.json]
Live evaluation uses synthetic cases and a temporary database, never actual user memory.
"""
import argparse
import hashlib
import json
import re
import tempfile
import time
from pathlib import Path

from src.agents import Assistant
from src.config import ROOT, Settings
from src.memory import MemoryStore
from src.provider import GenerationProvider, ProviderError
from src.retrieval import CORPUS_SHA256, Retriever
from src.tracing import Tracer


def retrieval_metrics(retriever, cases, mode, k):
    rows = []
    for case in cases:
        found = [r["chunk_id"] for r in retriever.search(case["question"], k, mode)]
        required = set(case["sources"])
        matches = required.intersection(found)
        rows.append({"id": case["id"], "split": case["split"], "retrieved": found,
                     "expected": case["sources"], "recall": len(matches) / len(required),
                     "all_evidence_found": required.issubset(found),
                     "reciprocal_rank": next((1 / (i + 1) for i, cid in enumerate(found) if cid in required), 0),
                     "missing": sorted(required - set(found))})
    summaries = {}
    for split in ("all", "development", "heldout"):
        selected = [r for r in rows if split == "all" or r["split"] == split]
        summaries[split] = {"cases": len(selected), "mean_evidence_recall": round(sum(r["recall"] for r in selected) / len(selected), 4),
                            "all_evidence_rate": round(sum(r["all_evidence_found"] for r in selected) / len(selected), 4),
                            "mrr": round(sum(r["reciprocal_rank"] for r in selected) / len(selected), 4)}
    return {"mode": mode, "k": k, "summary": summaries, "cases": rows}


def live_metrics(retriever, cases, settings, checkpoint=None, previous=None):
    rows = list(previous or [])
    completed = {r["id"] for r in rows if r["status"] != "error"}
    selected_ids = {case["id"] for case in cases}
    rows = [r for r in rows if r["id"] in completed or r["id"] not in selected_ids]
    with tempfile.TemporaryDirectory(prefix="asterline-eval-") as temp:
        store = MemoryStore(Path(temp) / "eval.sqlite3")
        assistant = Assistant(store, retriever, GenerationProvider(settings), Tracer(settings.tracing))
        for case in cases:
            if case["id"] in completed:
                continue
            user = "synthetic-evaluator-" + case["id"]
            session = store.new_session(user)
            started = time.monotonic()
            try:
                result = assistant.ask(user, session, case["question"], remember=False)
                cited = set(re.findall(r"\b[a-z][a-z0-9-]*:\d+\b", result.answer))
                rows.append({"id": case["id"], "status": result.status, "answer": result.answer,
                             "expected_patterns_pass": all(re.search(p, result.answer, re.I) for p in case["patterns"]),
                             "expected_source_coverage": len(cited.intersection(case["sources"])) / len(case["sources"]),
                             "citation_ids_valid": cited.issubset(retriever.by_id),
                             "trace_id": result.trace_id, "seconds": round(time.monotonic() - started, 2)})
            except (ProviderError, ValueError) as exc:
                rows.append({"id": case["id"], "status": "error", "error": str(exc),
                             "trace_id": assistant.tracer.last_trace_id})
            print(f"Live research: {case['id']} -> {rows[-1]['status']} ({len(rows)} results saved)", flush=True)
            if checkpoint:
                checkpoint(generation_report(rows, settings))
    return generation_report(rows, settings)


def generation_report(rows, settings):
    return {"label": "Actual generation; regex checks are limited proxies, manually review answers",
            "model": settings.model, "provider": settings.provider,
            "summary": {"cases": len(rows), "provider_errors": sum(r["status"] == "error" for r in rows),
                        "pattern_passes": sum(r.get("expected_patterns_pass", False) for r in rows),
                        "verification_failures": sum(r["status"] == "verification_failed" for r in rows)},
            "cases": rows}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--resume", action="store_true", help="Keep completed cases; retry provider errors from the output file")
    parser.add_argument("--case", action="append", default=[], help="Rerun a specific case ID while retaining other saved results with --resume")
    parser.add_argument("--limit", type=int, default=0, help="Optional live-case limit for provider cost control")
    parser.add_argument("--k", type=int, default=8)
    parser.add_argument("--output", type=Path, default=ROOT / "evaluation/results.json")
    args = parser.parse_args()
    previous = json.loads(args.output.read_text(encoding="utf-8")) if args.resume and args.output.exists() else {}
    settings = Settings.from_env()
    cases_path = ROOT / "evaluation/cases.json"
    cases = json.loads(cases_path.read_text())
    retriever = Retriever(settings)
    result = {"corpus_sha256": CORPUS_SHA256, "cases_sha256": hashlib.sha256(cases_path.read_bytes()).hexdigest(),
              "embedding_model": settings.embedding_model, "generation_evaluated": args.live,
              "baseline": retrieval_metrics(retriever, cases, "dense", args.k),
              "lexical_only_change": retrieval_metrics(retriever, cases, "fusion", args.k),
              "improved": retrieval_metrics(retriever, cases, "hybrid", args.k)}
    if args.live:
        if settings.provider_problem():
            parser.error(settings.provider_problem())
        def checkpoint(generation):
            result["generation"] = generation
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
        selected = [c for c in cases if c["id"] in args.case] if args.case else cases[:args.limit] if args.limit else cases
        if args.case and len(selected) != len(set(args.case)):
            parser.error("Unknown case ID")
        previous_rows = [r for r in previous.get("generation", {}).get("cases", []) if r["id"] not in args.case]
        result["generation"] = live_metrics(retriever, selected, settings, checkpoint, previous_rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    for name in ("baseline", "lexical_only_change", "improved"):
        print(name, json.dumps(result[name]["summary"]))
    print("Generation evaluated:", args.live)
    print("Results:", args.output)


if __name__ == "__main__":
    main()

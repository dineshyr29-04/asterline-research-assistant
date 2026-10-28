"""Share only the synthetic evaluation traces explicitly listed in saved results.

Mutating command: python -m scripts.share_evaluation_runs --share
Checks known credentials before publishing and verifies links via an unauthenticated API request.
"""
import argparse
import json
import os
import re
import time
from pathlib import Path

import httpx

from src.config import ROOT, Settings
from src.privacy import contains_secret


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--share", action="store_true", help="Explicitly publish synthetic evaluation runs")
    args = parser.parse_args()
    settings = Settings.from_env()
    from langsmith import Client
    client = Client()
    expected_questions = {c["question"] for c in json.loads((ROOT / "evaluation/cases.json").read_text())}
    expected_questions.update({
        "My workspace uses Team. Please remember that. Which Warehouse Export destinations can I use?",
        "How many days of searchable run-record retention does my plan include?",
        "Correction: my workspace now uses Enterprise. Remember that instead of Team. How many days of searchable run-record retention does my plan include?",
        "What workspace plan do I use?",
    })
    secrets = [settings.api_key, os.getenv("LANGSMITH_API_KEY", "")]
    records, errors = [], []
    output = ROOT / "evaluation/shared-runs.json"
    for filename, section, suite in [("live-results.json", "generation", "research"),
                                     ("live-memory-results.json", None, "memory"),
                                     ("live-before-fixes.json", "generation", "research-before-fix")]:
        path = ROOT / "evaluation" / filename
        if not path.exists():
            continue
        data = json.loads(path.read_text())
        for case in (data[section] if section else data)["cases"]:
            if suite == "research-before-fix" and case.get("expected_patterns_pass"):
                continue
            trace_id = case.get("trace_id")
            if not trace_id:
                continue
            try:
                root = client.read_run(trace_id)
            except Exception:
                errors.append({"case": case["id"], "trace_id": trace_id,
                               "reason": "Trace read failed; no public access claimed"})
                continue
            if root.name == "asterline.conversation":
                if (root.inputs or {}).get("question") not in expected_questions:
                    raise ValueError("Refusing to publish a trace outside the synthetic evaluation question allowlist")
            elif root.name != "asterline.memory_control":
                raise ValueError("Refusing to publish an unknown trace type")
            runs = list(client.list_runs(trace_id=trace_id))
            for run in runs:
                raw = run.json()
                if any(secret and secret in raw for secret in secrets):
                    raise ValueError("Refusing to publish a trace containing a configured credential")
                if contains_secret(json.dumps({"inputs": run.inputs, "outputs": run.outputs})):
                    raise ValueError("Refusing to publish a trace containing a possible credential")
            row = {"suite": suite, "case": case["id"],
                   "status": case["status"], "trace_id": trace_id, "child_spans": len(runs) - 1}
            if args.share:
                url = client.share_run(trace_id)
                token = re.search(r"/public/([a-f0-9-]+)", url).group(1)
                endpoint = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com").rstrip("/")
                # Intentionally no cookies, auth headers, or LangSmith client for this check.
                response = None
                for attempt in range(3):
                    try:
                        response = httpx.get(f"{endpoint}/public/{token}/run", timeout=20)
                        response.raise_for_status()
                        break
                    except httpx.HTTPError:
                        if attempt == 2:
                            raise
                        time.sleep(2)
                shared = response.json()
                if shared["id"] != trace_id:
                    raise ValueError("Shared trace did not match the requested evaluation")
                row.update(public_url=url, anonymous_access_verified=True)
            records.append(row)
            output.write_text(json.dumps({"publicly_shared": args.share, "runs": records, "errors": errors}, indent=2), encoding="utf-8")
            print(f"{'Shared and verified' if args.share else 'Checked'}: {row['suite']}/{row['case']}", flush=True)
    output.write_text(json.dumps({"publicly_shared": args.share, "runs": records, "errors": errors}, indent=2), encoding="utf-8")
    print(f"Recorded {len(records)} traces in {output}")


if __name__ == "__main__":
    main()

"""Small live provider + LangSmith smoke check; never print credentials."""
import json
import os
import time
from pathlib import Path

from src.config import Settings
from src.provider import GenerationProvider, ProviderError
from src.tracing import Tracer


def main():
    settings = Settings.from_env()
    tracer = Tracer(settings.tracing)
    report = {"provider": settings.provider, "model": settings.model,
              "tracing_enabled": tracer.enabled, "generation_ok": False, "trace_readable": False}
    trace_id = None
    try:
        with tracer.span("asterline.connection_check", {"synthetic_test": True}) as span:
            response = GenerationProvider(settings).complete(
                "connection_check", 'Return only JSON: {"ok": true}.', {"synthetic_test": True})
            report["generation_ok"] = response.get("ok") is True
            span.outputs = {"generation_ok": report["generation_ok"]}
            trace_id = span.trace_id
    except ProviderError as exc:
        report["provider_error"] = str(exc)
    if tracer.enabled and trace_id:
        from langsmith.run_trees import get_cached_client

        client = get_cached_client()
        client.flush()
        for attempt in range(3):
            try:
                run = client.read_run(trace_id)
                report["trace_readable"] = True
                report["trace_id"] = trace_id
                report["run_url"] = client.get_run_url(run=run)
                report["project"] = os.getenv("LANGSMITH_PROJECT", "asterline-research-assistant")
                break
            except Exception:
                if attempt < 2:
                    time.sleep(2)
        if not report["trace_readable"]:
            report["trace_error"] = "Trace upload/read could not be confirmed. Check key permissions and endpoint."
    path = Path("evaluation/connection-check.json")
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

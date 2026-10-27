"""Nested, opt-in LangSmith traces with redacted content and opaque user IDs."""
import hashlib
import os
from contextlib import contextmanager
from types import SimpleNamespace

from src.privacy import redact


def clean(value):
    if isinstance(value, dict):
        return {k: clean(v) for k, v in value.items() if k not in {"api_key", "authorization"}}
    if isinstance(value, list):
        return [clean(v) for v in value]
    return redact(value) if isinstance(value, str) else value


def user_tag(user_id):
    return hashlib.sha256(user_id.encode()).hexdigest()[:12]


class Tracer:
    def __init__(self, enabled=False):
        self.enabled = enabled and bool(os.getenv("LANGSMITH_API_KEY"))

    @contextmanager
    def span(self, name, inputs, metadata=None):
        result = SimpleNamespace(outputs={}, run_id=None, trace_id=None)
        if not self.enabled:
            yield result
            return
        from langsmith import trace, tracing_context

        # Explicit spans only: do not automatically serialize arbitrary Python objects.
        with tracing_context(enabled=True):
            with trace(name, inputs=clean(inputs), metadata=clean(metadata or {}),
                       project_name=os.getenv("LANGSMITH_PROJECT", "asterline-research-assistant")) as run:
                result.run_id = str(run.id)
                result.trace_id = str(run.trace_id)
                yield result
                run.end(outputs=clean(result.outputs))

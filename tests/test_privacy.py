from src.privacy import redact, safe_memory
from src.tracing import Tracer, clean, user_tag


def test_nested_trace_redaction():
    cleaned = clean({"question": "email person@example.com api_key=abc123", "api_key": "private",
                     "draft": [{"text": "Bearer synthetic-credential"}]})
    assert "private" not in str(cleaned) and "abc123" not in str(cleaned)
    assert "person@example.com" not in str(cleaned) and "synthetic-credential" not in str(cleaned)
    assert cleaned["draft"][0]["text"] == "[secret redacted]"


def test_tracing_off_has_no_network_and_preserves_decisions():
    with Tracer(False).span("test", {"question": "synthetic"}) as span:
        span.outputs = {"decision": "abstain"}
    assert span.trace_id is None and span.outputs["decision"] == "abstain"


def test_memory_privacy_and_opaque_user_identifier():
    assert not safe_memory("passport number 1234")
    assert safe_memory("Investigate synthetic ingestion failures")
    assert user_tag("alice") != "alice" and user_tag("alice") != user_tag("bob")

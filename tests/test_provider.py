import httpx
import pytest

from src.config import Settings
from src.provider import GenerationProvider, ProviderError, parse_json


def test_rate_limit_respects_bounded_retry_after():
    attempts, sleeps = [], []

    def handler(request):
        attempts.append(request)
        if len(attempts) == 1:
            return httpx.Response(429, headers={"Retry-After": "1000"})
        return httpx.Response(200, json={"choices": [{"message": {"content": '{"ok":true}'}}]})

    provider = GenerationProvider(Settings(api_key="synthetic-test-key"), httpx.MockTransport(handler), sleeps.append)
    assert provider.complete("test", "JSON only", {}) == {"ok": True}
    assert len(attempts) == 2 and sleeps == [10]


def test_exhausted_provider_does_not_expose_response_body():
    provider = GenerationProvider(Settings(api_key="synthetic-test-key", retries=1),
                                  httpx.MockTransport(lambda req: httpx.Response(503, text="secret payload")), lambda _: None)
    with pytest.raises(ProviderError) as exc:
        provider.complete("test", "JSON only", {})
    assert "secret payload" not in str(exc.value)


def test_auth_failure_is_not_retried():
    calls = []

    def handler(request):
        calls.append(1)
        return httpx.Response(401, text="raw api_key=should-not-leak")

    provider = GenerationProvider(Settings(api_key="synthetic-test-key"), httpx.MockTransport(handler))
    with pytest.raises(ProviderError, match="HTTP 401"):
        provider.complete("test", "JSON", {})
    assert len(calls) == 1


def test_invalid_json_and_missing_credentials():
    with pytest.raises(ProviderError):
        parse_json("not JSON")
    with pytest.raises(ProviderError):
        parse_json("[]")
    with pytest.raises(ProviderError, match="OPENAI_API_KEY"):
        GenerationProvider(Settings()).complete("test", "JSON", {})


def test_ollama_json_protocol():
    def handler(request):
        assert str(request.url) == "http://localhost:11434/api/chat"
        assert "authorization" not in request.headers
        return httpx.Response(200, json={"message": {"content": '{"ok":true}'}})

    provider = GenerationProvider(Settings(provider="ollama", base_url="http://localhost:11434"), httpx.MockTransport(handler))
    assert provider.complete("test", "JSON", {}) == {"ok": True}

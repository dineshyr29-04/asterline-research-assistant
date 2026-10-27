"""Bounded HTTP generation with validated JSON and safe errors."""
import json
import time
from urllib.parse import urlparse

import httpx


class ProviderError(RuntimeError):
    """A safe, user-facing failure. Never contains raw provider response bodies."""


def parse_json(content):
    value = content.strip()
    if value.startswith("```"):
        value = value.split("\n", 1)[-1].rsplit("```", 1)[0]
    try:
        result = json.loads(value)
    except (ValueError, TypeError) as exc:
        raise ProviderError("The model returned invalid JSON. Retry or choose a stronger model.") from exc
    if not isinstance(result, dict):
        raise ProviderError("The model returned an unexpected response structure.")
    return result


class GenerationProvider:
    def __init__(self, settings, transport=None, sleeper=time.sleep):
        self.settings = settings
        self.transport = transport
        self.sleeper = sleeper

    def complete(self, role, system, payload):
        problem = self.settings.provider_problem()
        if problem:
            raise ProviderError(problem)
        s = self.settings
        parsed = urlparse(s.base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ProviderError("Provider base URL must be an HTTP(S) endpoint.")
        if parsed.scheme == "http" and parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
            raise ProviderError("Remote model endpoints must use HTTPS.")
        messages = [{"role": "system", "content": system},
                    {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}]
        if s.provider == "ollama":
            url = s.base_url.rstrip("/") + "/api/chat"
            body = {"model": s.model, "messages": messages, "stream": False, "format": "json",
                    "options": {"temperature": 0, "num_predict": 2200}}
            headers = {}
        else:
            url = s.base_url.rstrip("/") + "/chat/completions"
            body = {"model": s.model, "messages": messages, "temperature": 0,
                    "response_format": {"type": "json_object"}, "max_tokens": 2200}
            headers = {"Authorization": "Bearer " + s.api_key}
        with httpx.Client(timeout=s.timeout, transport=self.transport) as client:
            for attempt in range(s.retries + 1):
                try:
                    response = client.post(url, json=body, headers=headers)
                except (httpx.TimeoutException, httpx.NetworkError) as exc:
                    if attempt == s.retries:
                        raise ProviderError("Model provider timed out or is unreachable. No answer was saved.") from exc
                    self.sleeper(min(2 ** attempt, 8))
                    continue
                if response.status_code == 429 or response.status_code >= 500:
                    if attempt == s.retries:
                        raise ProviderError("Model provider is rate-limited or unavailable. Try again shortly.")
                    try:
                        delay = float(response.headers.get("Retry-After", 2 ** attempt))
                    except ValueError:
                        delay = 2 ** attempt
                    self.sleeper(min(10, max(0, delay)))
                    continue
                if response.status_code >= 400:
                    raise ProviderError(f"Model request failed (HTTP {response.status_code}). Check provider settings.")
                try:
                    data = response.json()
                    content = data["message"]["content"] if s.provider == "ollama" else data["choices"][0]["message"]["content"]
                    return parse_json(content)
                except (KeyError, IndexError, TypeError, ValueError) as exc:
                    raise ProviderError("Model provider returned an unexpected response structure.") from exc
        raise ProviderError("Model request could not be completed.")

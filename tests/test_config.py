"""Environment compatibility checks without reading or using personal credentials."""
import pytest

from src.config import Settings


@pytest.fixture
def clean_env(tmp_path, monkeypatch):
    for key in ("LLM_PROVIDER", "GENERATION_PROVIDER", "MODEL_NAME", "OLLAMA_MODEL", "OLLAMA_BASE_URL",
                "OPENAI_MODEL", "OPENAI_BASE_URL", "OPENAI_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    path = tmp_path / ".env"
    path.write_text("")
    return path


def test_ollama_is_the_default_without_credentials(clean_env):
    settings = Settings.from_env(clean_env)
    assert settings.provider == "ollama" and settings.model == "llama3.1:8b"
    assert settings.base_url == "http://localhost:11434" and settings.provider_problem() is None


def test_existing_free_provider_configuration_still_works(clean_env, monkeypatch):
    monkeypatch.setenv("GENERATION_PROVIDER", "openai")
    monkeypatch.setenv("MODEL_NAME", "synthetic-legacy-model")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://example.org/v1")
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-test-key")
    settings = Settings.from_env(clean_env)
    assert settings.provider == "openai" and settings.model == "synthetic-legacy-model"
    assert settings.provider_problem() is None


def test_documented_variables_take_precedence_over_legacy_aliases(clean_env, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("GENERATION_PROVIDER", "openai")
    monkeypatch.setenv("OLLAMA_MODEL", "synthetic-local-model")
    monkeypatch.setenv("MODEL_NAME", "synthetic-legacy-model")
    settings = Settings.from_env(clean_env)
    assert settings.provider == "ollama" and settings.model == "synthetic-local-model"

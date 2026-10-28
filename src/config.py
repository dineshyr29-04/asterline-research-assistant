"""Environment configuration, with no credentials in reprs or error messages."""
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
OLLAMA_MODEL = "llama3.1:8b"
OLLAMA_URL = "http://localhost:11434"
OPENAI_MODEL = "gpt-4o-mini"
OPENAI_URL = "https://api.openai.com/v1"


@dataclass(frozen=True)
class Settings:
    runtime_dir: Path = ROOT / "runtime"
    corpus_path: Path = ROOT / "data/corpus.jsonl"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    provider: str = "ollama"
    model: str = OLLAMA_MODEL
    base_url: str = OLLAMA_URL
    api_key: str = field(default="", repr=False)
    timeout: float = 45
    retries: int = 2
    retrieval_mode: str = "hybrid"
    tracing: bool = False

    @classmethod
    def from_env(cls, env_file=None):
        """Prefer the documented names; keep existing installations' aliases working."""
        load_dotenv(env_file if env_file is not None else ROOT / ".env")
        provider = (os.getenv("LLM_PROVIDER") or os.getenv("GENERATION_PROVIDER") or "ollama").lower()
        if provider == "ollama":
            model = os.getenv("OLLAMA_MODEL") or os.getenv("MODEL_NAME") or OLLAMA_MODEL
            base_url = os.getenv("OLLAMA_BASE_URL", OLLAMA_URL)
        else:
            model = os.getenv("OPENAI_MODEL") or os.getenv("MODEL_NAME") or OPENAI_MODEL
            base_url = os.getenv("OPENAI_BASE_URL", OPENAI_URL)
        runtime = Path(os.getenv("RUNTIME_DIR", "runtime"))
        return cls(
            runtime_dir=runtime if runtime.is_absolute() else ROOT / runtime,
            provider=provider,
            model=model,
            base_url=base_url,
            api_key=os.getenv("OPENAI_API_KEY", ""),
            embedding_model=os.getenv("EMBEDDING_MODEL", cls.embedding_model),
            timeout=min(120, max(1, float(os.getenv("PROVIDER_TIMEOUT_SECONDS", "45")))),
            retries=min(3, max(0, int(os.getenv("PROVIDER_MAX_RETRIES", "2")))),
            retrieval_mode=os.getenv("RETRIEVAL_MODE", "hybrid"),
            tracing=os.getenv("LANGSMITH_TRACING", "false").lower() == "true",
        )

    def provider_problem(self):
        if self.provider not in {"openai", "ollama"}:
            return "LLM_PROVIDER must be openai or ollama (GENERATION_PROVIDER is a supported alias)."
        if self.provider == "openai" and not self.api_key:
            return "Set OPENAI_API_KEY in .env, or configure local Ollama."
        return None

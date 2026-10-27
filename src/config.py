"""Environment configuration, with no credentials in reprs or error messages."""
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Settings:
    runtime_dir: Path = ROOT / "runtime"
    corpus_path: Path = ROOT / "data/corpus.jsonl"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    base_url: str = "https://api.openai.com/v1"
    api_key: str = field(default="", repr=False)
    timeout: float = 45
    retries: int = 2
    retrieval_mode: str = "hybrid"
    tracing: bool = False

    @classmethod
    def from_env(cls):
        load_dotenv(ROOT / ".env")
        provider = os.getenv("GENERATION_PROVIDER", "openai").lower()
        runtime = Path(os.getenv("RUNTIME_DIR", "runtime"))
        return cls(
            runtime_dir=runtime if runtime.is_absolute() else ROOT / runtime,
            provider=provider,
            model=os.getenv("MODEL_NAME", "llama3.2" if provider == "ollama" else "gpt-4o-mini"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434") if provider == "ollama"
            else os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            api_key=os.getenv("OPENAI_API_KEY", ""),
            embedding_model=os.getenv("EMBEDDING_MODEL", cls.embedding_model),
            timeout=min(120, max(1, float(os.getenv("PROVIDER_TIMEOUT_SECONDS", "45")))),
            retries=min(3, max(0, int(os.getenv("PROVIDER_MAX_RETRIES", "2")))),
            retrieval_mode=os.getenv("RETRIEVAL_MODE", "hybrid"),
            tracing=os.getenv("LANGSMITH_TRACING", "false").lower() == "true",
        )

    def provider_problem(self):
        if self.provider not in {"openai", "ollama"}:
            return "GENERATION_PROVIDER must be openai or ollama."
        if self.provider == "openai" and not self.api_key:
            return "Set OPENAI_API_KEY in .env, or configure local Ollama."
        return None

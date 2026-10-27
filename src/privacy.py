"""Conservative safeguards; these are not a general-purpose DLP system."""
import re

SECRET = re.compile(
    r"(?i)(?:\b(?:sk|gsk|ghp|github_pat|lsv2_pt|hf)[-_][a-z0-9_-]{12,}"
    r"|\bBearer\s+\S+|\b(?:api[_ -]?key|password|secret|token|credential)\s*[:=]\s*\S+"
    r"|-----BEGIN [A-Z ]*PRIVATE KEY-----)"
)
EMAIL = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
SENSITIVE = re.compile(r"(?i)\b(?:diagnos\w*|medical|pregnan\w*|passport|social security|credit card|bank account)\b")


def contains_secret(text):
    return bool(SECRET.search(text))


def safe_memory(text):
    return len(text) <= 600 and not (contains_secret(text) or SENSITIVE.search(text) or EMAIL.search(text))


def redact(text):
    return EMAIL.sub("[email redacted]", SECRET.sub("[secret redacted]", str(text)))

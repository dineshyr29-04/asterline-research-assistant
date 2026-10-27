import copy

import pytest

from src.agents import Assistant, validate_draft
from src.config import Settings
from src.memory import MemoryStore
from src.provider import ProviderError
from src.retrieval import load_corpus

RECORDS = load_corpus(Settings().corpus_path)
SOURCE = next(r for r in RECORDS if r["chunk_id"] == "handbook:1")
DRAFT = {"claims": [{"text": "The weekly on-call stipend is $175, effective 2026-01-01.",
                     "sources": [{"chunk_id": "handbook:1", "quote": SOURCE["text"]}]}], "uncertainty": ""}


class FixtureRetriever:
    mode = "fixture"

    def search(self, query):
        return [SOURCE]

    def expand_scope(self, evidence):
        return evidence


class FixtureProvider:
    """Scripted responses test orchestration, NOT model answer quality."""
    def __init__(self, bad_first=False, reject=False, fail=False):
        self.calls = []
        self.bad_first, self.reject, self.fail = bad_first, reject, fail

    def complete(self, role, system, payload):
        self.calls.append((role, payload))
        if self.fail:
            raise ProviderError("Synthetic provider failure")
        if role == "memory":
            return {"search_query": payload["CURRENT_MESSAGE"], "updates": [], "reason": "No user context to retain"}
        if role == "research":
            draft = copy.deepcopy(DRAFT)
            if self.bad_first and sum(r == "research" for r, _ in self.calls) == 1:
                draft["claims"][0]["sources"][0]["chunk_id"] = "fabricated:0"
            return draft
        return {"approved": not self.reject, "issues": ["Unsupported scope"] if self.reject else []}


def make_assistant(tmp_path, **kwargs):
    store = MemoryStore(tmp_path / "memory.sqlite3")
    provider = FixtureProvider(**kwargs)
    return Assistant(store, FixtureRetriever(), provider), store.new_session("alice"), provider


def test_three_agents_and_citations(tmp_path):
    app, session, provider = make_assistant(tmp_path)
    result = app.ask("alice", session, "What is the current on-call stipend?")
    assert result.status == "answered"
    assert "$175" in result.answer and "handbook:1" in result.answer and "Employee handbook" in result.answer
    assert [role for role, _ in provider.calls] == ["memory", "research", "verifier"]
    assert len(app.store.history("alice", session)) == 2


def test_fabricated_citation_triggers_real_repair_handoff(tmp_path):
    app, session, provider = make_assistant(tmp_path, bad_first=True)
    result = app.ask("alice", session, "Current stipend?")
    assert result.status == "answered"
    research = [p for role, p in provider.calls if role == "research"]
    assert len(research) == 2 and "REVIEW_FEEDBACK" in research[-1]
    assert result.decisions[1]["approved"] is False


def test_rejection_and_provider_failure_do_not_save_answers(tmp_path):
    app, session, _ = make_assistant(tmp_path, reject=True)
    result = app.ask("alice", session, "Current stipend?")
    assert result.status == "verification_failed"
    assert app.store.history("alice", session) == []
    app.provider.fail = True
    with pytest.raises(ProviderError):
        app.ask("alice", session, "Current stipend?")
    assert app.store.history("alice", session) == []


def test_memory_commands_work_without_a_provider_and_forget_is_not_reinserted(tmp_path):
    app, session, provider = make_assistant(tmp_path, fail=True)
    app.ask("alice", session, "/remember workspace_plan=Team")
    assert app.store.memories("alice")[0]["value"] == "Team"
    app.ask("alice", session, "/correct workspace_plan=Enterprise")
    assert app.store.memories("alice")[0]["value"] == "Enterprise"
    app.ask("alice", session, "/forget all")
    assert app.store.memories("alice") == [] and app.store.history("alice", session) == []
    assert provider.calls == []


def test_secrets_blocked_before_provider_or_storage(tmp_path):
    app, session, provider = make_assistant(tmp_path)
    result = app.ask("alice", session, "Please remember api_key=synthetic-secret-value")
    assert result.status == "blocked" and provider.calls == []
    assert app.store.memories("alice") == [] and app.store.history("alice", session) == []


def test_exact_quote_validation_rejects_wrong_evidence():
    draft = copy.deepcopy(DRAFT)
    draft["claims"][0]["sources"][0]["quote"] = "The stipend is $999 per week."
    assert "verbatim" in validate_draft(draft, [SOURCE])[0]


class MemoryFixtureProvider(FixtureProvider):
    def complete(self, role, system, payload):
        if role == "memory":
            self.calls.append((role, payload))
            return {"search_query": "Current stipend?", "updates": [
                {"key": "workspace_plan", "value": "Team", "quote": "My workspace uses Team"},
                {"key": "api_key", "value": "not-allowed", "quote": "My workspace uses Team"},
                {"key": "work_goal", "value": "Invented memory", "quote": "not in the message"}],
                "reason": "Synthetic memory proposal"}
        return super().complete(role, system, payload)


@pytest.mark.parametrize("remember,reject,expected", [(True, False, "Team"), (False, False, None), (True, True, None)])
def test_automatic_memory_requires_current_evidence_consent_and_verified_answer(tmp_path, remember, reject, expected):
    store = MemoryStore(tmp_path / "memory.sqlite3")
    session = store.new_session("alice")
    provider = MemoryFixtureProvider(reject=reject)
    assistant = Assistant(store, FixtureRetriever(), provider)
    assistant.ask("alice", session, "My workspace uses Team. What is the stipend?", remember=remember)
    memories = store.memories("alice")
    if expected is None:
        assert memories == []
    else:
        assert [(m["key"], m["value"]) for m in memories] == [("workspace_plan", expected)]

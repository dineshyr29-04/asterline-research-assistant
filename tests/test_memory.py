import pytest

from src.memory import MemoryStore


@pytest.fixture
def store(tmp_path):
    return MemoryStore(tmp_path / "memory.sqlite3")


def test_restart_and_separate_session_continuity(store):
    session = store.new_session("alice")
    store.save("alice", "workspace_plan", "Team")
    store.add_exchange("alice", session, "My workspace uses Team", "Understood")
    restarted = MemoryStore(store.path)
    assert restarted.history("alice", session)[0]["content"] == "My workspace uses Team"
    new_session = restarted.new_session("alice")
    assert restarted.history("alice", new_session) == []
    assert restarted.memories("alice")[0]["value"] == "Team"


def test_user_isolation_rejects_foreign_session(store):
    session = store.new_session("alice")
    store.save("alice", "project_name", "Secret synthetic project")
    assert store.memories("bob") == []
    assert store.sessions("bob") == []
    with pytest.raises(ValueError):
        store.history("bob", session)
    with pytest.raises(ValueError):
        store.add_exchange("bob", session, "hello", "hello")


def test_correction_invalidates_stale_history_across_sessions(store):
    sessions = [store.new_session("alice") for _ in range(2)]
    store.save("alice", "workspace_plan", "Team")
    for session in sessions:
        store.add_exchange("alice", session, "Team workspace", "Team context")
    store.save("alice", "workspace_plan", "Enterprise")
    assert store.memories("alice")[0]["value"] == "Enterprise"
    assert all(store.history("alice", s) == [] for s in sessions)


def test_forget_clears_all_old_context_but_not_other_users(store):
    alice = store.new_session("alice")
    bob = store.new_session("bob")
    store.save("alice", "workspace_plan", "Team")
    store.save("alice", "response_style", "concise")
    store.save("bob", "workspace_plan", "Launch")
    store.add_exchange("alice", alice, "Remember Team", "OK")
    store.add_exchange("bob", bob, "Remember Launch", "OK")
    store.forget("alice", "workspace_plan")
    restarted = MemoryStore(store.path)
    assert [r["key"] for r in restarted.memories("alice")] == ["response_style"]
    assert restarted.history("alice", alice) == []
    assert restarted.memories("bob")[0]["value"] == "Launch"
    assert len(restarted.history("bob", bob)) == 2
    restarted.forget("alice")
    assert restarted.memories("alice") == []


@pytest.mark.parametrize("key,value", [
    ("api_key", "anything"), ("work_goal", "api_key=secret123"),
    ("work_goal", "My medical diagnosis"), ("project_name", "person@example.org"),
    ("workspace_plan", "sk-1234567890abcdefghijk"),
])
def test_refuse_sensitive_or_unapproved_memory(store, key, value):
    with pytest.raises(ValueError):
        store.save("alice", key, value)
    assert store.memories("alice") == []

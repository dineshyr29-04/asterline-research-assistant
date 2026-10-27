from pathlib import Path

from streamlit.testing.v1 import AppTest

from src.memory import MemoryStore


def test_ui_loads_without_credentials_and_switches_user_context(tmp_path, monkeypatch):
    monkeypatch.setenv("RUNTIME_DIR", str(tmp_path))
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("LANGSMITH_TRACING", "false")
    store = MemoryStore(tmp_path / "memory.sqlite3")
    store.save("alice", "workspace_plan", "Team")
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py")).run(timeout=15)
    assert not app.exception
    assert any("OPENAI_API_KEY" in x.value for x in app.warning)
    assert any("Team" == x.value for x in app.markdown)
    app.sidebar.selectbox[0].select("bob").run()
    assert not app.exception
    assert any("Nothing remembered" in x.value for x in app.info)
    assert not any("Team" == x.value for x in app.markdown)

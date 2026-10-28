"""Local demonstration UI. User selection simulates identity; it is not authentication."""
import streamlit as st

from src.agents import Assistant
from src.config import Settings
from src.memory import MEMORY_KEYS, MemoryStore
from src.provider import GenerationProvider, ProviderError
from src.retrieval import Retriever, load_corpus
from src.tracing import Tracer

st.set_page_config(page_title="Asterline | Research that remembers", page_icon="✦", layout="wide")


@st.cache_resource(show_spinner=False)
def get_retriever(settings):
    return Retriever(settings)


class LazyRetriever:
    """Allow memory management and corpus browsing without a model download."""
    def __init__(self, settings):
        self.settings = settings
        self.mode = settings.retrieval_mode

    def search(self, query):
        return get_retriever(self.settings).search(query)

    def expand_scope(self, evidence):
        return get_retriever(self.settings).expand_scope(evidence)


def clear_user_results(user):
    for key in list(st.session_state.get("results", {})):
        if key[0] == user:
            del st.session_state.results[key]


def render_sidebar(settings, store, tracer):
    with st.sidebar:
        st.title("✦ Asterline")
        st.caption("RESEARCH WORKSPACE")
        user = st.selectbox("Synthetic user", ["alice", "bob", "charlie"],
                            help="Local demo identities, not authentication. Use synthetic data only.")
        sessions = store.sessions(user)
        if not sessions:
            sessions = [store.new_session(user)]
        if st.button("＋ New conversation", use_container_width=True):
            new = store.new_session(user)
            st.session_state[f"session_{user}"] = new
            st.rerun()
        session = st.selectbox("Conversation", sessions, key=f"session_{user}",
                               format_func=lambda s: "Conversation " + s[:8])
        remember = st.toggle("Remember useful context", value=True,
                             help="Only workspace context and preferences. Explicit commands still work when off.")
        st.divider()
        st.subheader("Your memory")
        st.caption("User statements guide scope. Company answers always need documentary evidence.")
        memories = store.memories(user)
        for row in memories:
            with st.container(border=True):
                st.markdown(f"**{row['key'].replace('_', ' ').title()}**")
                st.write(row["value"])
                st.caption(f"{row['provenance']} · {row['updated_at'][:10]}")
                if st.button("Forget", key=f"forget_{user}_{row['key']}"):
                    store.forget(user, row["key"])
                    clear_user_results(user)
                    st.rerun()
        if not memories:
            st.info("Nothing remembered yet.")
        with st.expander("Add or correct context"):
            with st.form(f"memory_{user}"):
                key = st.selectbox("Context type", sorted(MEMORY_KEYS))
                value = st.text_input("Value", max_chars=600)
                if st.form_submit_button("Save context"):
                    try:
                        store.save(user, key, value)
                        clear_user_results(user)
                        st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))
        st.caption("Corrections and forgetting clear your old chat history to prevent stale context returning.")
        confirm = st.checkbox("Clear all my memory and chat history", key=f"confirm_{user}")
        if st.button("Forget everything", disabled=not confirm, use_container_width=True):
            store.forget(user)
            clear_user_results(user)
            st.rerun()
        st.divider()
        st.caption(f"Generation: {settings.provider} · {settings.model}")
        st.caption("Local embeddings · Local vector store · SQLite memory")
        if tracer.enabled:
            st.caption("LangSmith tracing enabled. Shared runs must contain synthetic data only.")
        else:
            st.caption("LangSmith tracing off" + (" — API key missing" if settings.tracing else ""))
    return user, session, remember


def render_conversation(store, assistant, user, session, remember):
    history = store.history(user, session, limit=100)
    if not history:
        st.info("Try: What is the current on-call stipend? Why do the documents give different figures?")
        st.caption("Other examples: Team record vs Explorer retention · AQL limits in v2.2 vs v2.3 · "
                   "Why did Warehouse Export create duplicates?")
    for message in history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    result = st.session_state.results.get((user, session))
    if result:
        if not history or history[-1]["content"] != result.answer:
            with st.chat_message("assistant"):
                st.markdown(result.answer)
        if result.saved_memory:
            st.caption("Remembered: " + ", ".join(result.saved_memory))
        if result.decisions:
            with st.expander("Agent decisions · latest question"):
                st.json(result.decisions)
        if result.trace_id:
            st.caption("LangSmith trace ID: " + result.trace_id)
        if result.evidence:
            with st.expander("Evidence passages · latest question"):
                for source in result.evidence:
                    st.markdown(f"**{source['chunk_id']} · {source['title']}**")
                    st.caption(f"Published {source['published']} · v{source['version']} · {source['source_url']}")
                    st.write(source["text"])
    question = st.chat_input("Ask about Asterline, or use /remember, /correct, /forget")
    if question:
        from src.agents import Result
        try:
            with st.spinner("Resolving context → retrieving evidence → researching → verifying…"):
                answer = assistant.ask(user, session, question, remember=remember)
            if answer.status == "memory" or answer.saved_memory:
                clear_user_results(user)
            st.session_state.results[(user, session)] = answer
        except (ProviderError, ValueError) as exc:
            st.session_state.results[(user, session)] = Result(str(exc), status="error")
        except Exception:
            # Never expose raw SDK/provider exceptions which may contain credentials or user payloads.
            st.session_state.results[(user, session)] = Result(
                "A local retrieval or storage operation failed. Check write access, available disk space and "
                "embedding model download connectivity, then restart. No unverified answer was saved.", status="error")
        st.rerun()


def render_sources(corpus):
    search = st.text_input("Filter source text or title", placeholder="retention, stipend, INC-2026-03…")
    for source in corpus:
        if search.lower() in (source["title"] + " " + source["text"] + " " + source["chunk_id"]).lower():
            with st.expander(source["chunk_id"] + " · " + source["title"]):
                st.caption(f"{source['category']} · {source['published']} · version {source['version']}")
                st.write(source["text"])
                st.code(source["source_url"])


def render_help():
            st.markdown("""
    1. **Memory agent** resolves follow-ups and selectively proposes user context.
    2. **Research agent** answers from local retrieval, with exact evidence quotations.
    3. **Verifier agent** checks support, scope and conflicts. It can reject a draft and request one revision.

    Company documentation is the authority. User memory and past answers cannot establish company facts.

    **Commands:** `/remember workspace_plan=Team`, `/correct workspace_plan=Enterprise`,
    `/forget workspace_plan`, `/forget all`.

    Use synthetic users only. A user selector demonstrates storage isolation; anyone with access to this local
    application can select another demo identity. Production authentication is outside this assignment's scope.

    Local embeddings need a one-time model download. Generation uses your configured API or Ollama;
    hosted generation may cost money. LangSmith tracing is opt-in and sends redacted synthetic run data
    to your configured LangSmith project. Forgetting clears local context, not previously exported traces;
    manage shared traces separately in LangSmith.
    """)


def main():
    settings = Settings.from_env()
    store = MemoryStore(settings.runtime_dir / "memory.sqlite3")
    corpus = load_corpus(settings.corpus_path)
    tracer = Tracer(settings.tracing)
    assistant = Assistant(store, LazyRetriever(settings), GenerationProvider(settings), tracer)
    st.session_state.setdefault("results", {})

    user, session, remember = render_sidebar(settings, store, tracer)

    st.title("Research that remembers")
    st.markdown("Trustworthy answers from company documentation, with context you control.")
    col1, col2, col3 = st.columns(3)
    col1.metric("Evidence chunks", len(corpus))
    col2.metric("Source documents", len({r["doc_id"] for r in corpus}))
    col3.metric("Collaborating agents", 3)
    problem = settings.provider_problem()
    if problem:
        st.warning(problem + " You can browse sources and manage memory now. Configure .env and restart to ask research questions.")
    chat_tab, sources_tab, help_tab = st.tabs(["Conversation", "Knowledge base", "How it works"])
    with chat_tab:
        render_conversation(store, assistant, user, session, remember)
    with sources_tab:
        render_sources(corpus)
    with help_tab:
        render_help()


if __name__ == "__main__":
    main()

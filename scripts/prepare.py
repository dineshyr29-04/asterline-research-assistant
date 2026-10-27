"""Download local embedding weights, verify corpus and build the persistent index."""
from src.config import Settings
from src.retrieval import Retriever


def main():
    settings = Settings.from_env()
    retriever = Retriever(settings)
    print(f"Ready: {retriever.collection.count()} local vectors, model={settings.embedding_model}")


if __name__ == "__main__":
    main()

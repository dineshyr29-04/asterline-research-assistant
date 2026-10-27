"""Local ONNX embeddings + persistent Chroma; optional lexical rank fusion."""
import hashlib
import json
import math
import re
from collections import Counter

CORPUS_SHA256 = "f63fc05cf43204485c98bd8fb6d89860a32c16a7e906bc90975e7c3954fe9fb1"
STOP = set("a an the is are was were for to of in on and or what how does do can my our it its this that with about".split())


def tokens(text):
    return [t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in STOP]


def load_corpus(path):
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != CORPUS_SHA256:
        raise ValueError("Corpus integrity check failed; restore the unchanged original corpus.jsonl")
    records = [json.loads(line) for line in raw.splitlines() if line.strip()]
    if len(records) != 75 or len({r["chunk_id"] for r in records}) != 75:
        raise ValueError("Expected exactly 75 unique chunks")
    return records


class Retriever:
    def __init__(self, settings):
        import chromadb
        from chromadb.config import Settings as ChromaSettings
        from fastembed import TextEmbedding

        self.records = load_corpus(settings.corpus_path)
        self.by_id = {r["chunk_id"]: r for r in self.records}
        self.mode = settings.retrieval_mode
        self.encoder = TextEmbedding(settings.embedding_model,
                                     cache_dir=str(settings.runtime_dir / "models"), threads=2)
        self.client = chromadb.PersistentClient(path=str(settings.runtime_dir / "vectors"),
                                               settings=ChromaSettings(anonymized_telemetry=False))
        fingerprint = hashlib.sha256((CORPUS_SHA256 + settings.embedding_model).encode()).hexdigest()[:16]
        self.collection = self.client.get_or_create_collection(
            "asterline-" + fingerprint, embedding_function=None,
            metadata={"hnsw:space": "cosine", "corpus_sha256": CORPUS_SHA256,
                      "embedding_model": settings.embedding_model})
        if self.collection.count() != len(self.records):
            passages = [r["title"] + "\n" + r["text"] for r in self.records]
            vectors = [v.tolist() for v in self.encoder.embed(passages)]
            self.collection.upsert(ids=list(self.by_id), embeddings=vectors,
                                   documents=passages,
                                   metadatas=[{k: v for k, v in r.items() if k != "text"} for r in self.records])
        self.bags = [Counter(tokens(r["title"] + " " + r["text"])) for r in self.records]
        self.avg_length = sum(sum(b.values()) for b in self.bags) / len(self.bags)
        self.df = Counter(t for b in self.bags for t in b)

    def lexical_rank(self, query):
        scores = {}
        for r, bag in zip(self.records, self.bags):
            score = 0.0
            length = sum(bag.values())
            for term in set(tokens(query)):
                freq = bag[term]
                idf = math.log(1 + (len(self.records) - self.df[term] + 0.5) / (self.df[term] + 0.5))
                score += idf * freq * 2.2 / (freq + 1.2 * (0.25 + 0.75 * length / self.avg_length))
            if score > 0:
                scores[r["chunk_id"]] = score
        return sorted(scores, key=lambda cid: (-scores[cid], cid))

    def search(self, query, limit=8, mode=None):
        if not query.strip():
            return []
        mode = mode or self.mode
        if mode not in {"dense", "hybrid"}:
            raise ValueError("Retrieval mode must be dense or hybrid")
        vector = next(iter(self.encoder.query_embed(query))).tolist()
        dense = self.collection.query(query_embeddings=[vector], n_results=len(self.records), include=["distances"])
        dense_ids = dense["ids"][0]
        distances = dict(zip(dense_ids, dense["distances"][0]))
        ranked = dense_ids
        if mode == "hybrid":
            # Reciprocal rank fusion keeps numerical BM25 and cosine scales separate.
            scores = Counter()
            for ranking in (dense_ids, self.lexical_rank(query)):
                for rank, cid in enumerate(ranking, 1):
                    scores[cid] += 1 / (20 + rank)
            ranked = sorted(scores, key=lambda cid: (-scores[cid], cid))
        return [{**self.by_id[cid], "distance": round(distances[cid], 5)} for cid in ranked[:limit]]

    def expand_scope(self, evidence, max_chunks=14):
        """Read siblings of the best two documents to avoid isolated-chunk conclusions."""
        ids = {r["chunk_id"] for r in evidence}
        result = list(evidence)
        docs = list(dict.fromkeys(r["doc_id"] for r in evidence))[:2]
        for r in self.records:
            if r["doc_id"] in docs and r["chunk_id"] not in ids and len(result) < max_chunks:
                result.append({**r, "distance": None})
        return result

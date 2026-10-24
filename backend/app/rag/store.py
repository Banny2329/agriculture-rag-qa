"""ChromaDB 向量存储与检索：集合 agri_kb，余弦距离。"""
import logging
from pathlib import Path
from typing import Any

import chromadb
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings

from app.rag.embedder import Embedder

logger = logging.getLogger(__name__)

COLLECTION_NAME = "agri_kb"


class BgeEmbeddingFunction(EmbeddingFunction):
    """桥接 Chroma 与本地 bge 模型，避免 Chroma 自行下载默认模型。"""

    def __init__(self, embedder: Embedder):
        self._embedder = embedder

    def __call__(self, input: Documents) -> Embeddings:
        return self._embedder.embed_documents(list(input))


class VectorStore:
    def __init__(self, persist_dir: Path, embedder: Embedder):
        self._client = chromadb.PersistentClient(path=str(persist_dir))
        self._ef = BgeEmbeddingFunction(embedder)
        self._collection = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
            embedding_function=self._ef,
        )

    def reset(self) -> None:
        """清空并重建集合，保证建档幂等。"""
        try:
            self._client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass
        self._collection = self._client.create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
            embedding_function=self._ef,
        )
        logger.info("向量库已清空重建")

    def add(self, ids: list[str], documents: list[str],
            metadatas: list[dict], embeddings: list[list[float]]) -> None:
        self._collection.add(
            ids=ids, documents=documents, metadatas=metadatas, embeddings=embeddings
        )

    def query(self, query_embedding: list[float], n_results: int = 5,
              min_score: float = 0.3) -> list[dict[str, Any]]:
        """余弦距离转相似度，低于 min_score 的结果丢弃。"""
        res = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )
        hits: list[dict[str, Any]] = []
        docs = (res.get("documents") or [[]])[0]
        metas = (res.get("metadatas") or [[]])[0]
        dists = (res.get("distances") or [[]])[0]
        for doc, meta, dist in zip(docs, metas, dists):
            score = 1.0 - float(dist)  # cosine 距离 → 相似度
            if score < min_score:
                continue
            hits.append({"text": doc, "source": meta.get("source", ""),
                         "page": meta.get("page", ""), "score": round(score, 4)})
        return hits

    def count(self) -> int:
        return self._collection.count()

    def get_by_sources(self, sources: list[str], max_chars: int = 60000) -> list[dict[str, Any]]:
        """按文件名取分块文本（用于用户指定文件随消息发送的上下文）。"""
        data = self._collection.get(
            where={"source": {"$in": sources}}, include=["documents", "metadatas"]
        )
        docs = data.get("documents") or []
        metas = data.get("metadatas") or []
        hits = [
            {"text": d, "source": m.get("source", ""), "page": m.get("page", "")}
            for d, m in zip(docs, metas)
            if d and m
        ]
        out, total = [], 0
        for h in hits:
            remaining = max_chars - total
            if remaining <= 0:
                break
            text = h["text"] if len(h["text"]) <= remaining else h["text"][:remaining]
            out.append({**h, "text": text})
            total += len(text)
        return out

    def all_meta(self) -> list[dict]:
        """返回全部元数据，用于知识库状态展示。"""
        data = self._collection.get(include=["metadatas"])
        return [m for m in (data.get("metadatas") or []) if m]

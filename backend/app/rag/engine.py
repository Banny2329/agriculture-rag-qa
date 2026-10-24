"""RAG 引擎：建档（ingest）、检索、回答生成，串起知识库 → 向量 → LLM 全链路。"""
import logging
import threading
import time
import uuid
from pathlib import Path
from typing import Any

from app.config import settings
from app.knowledge.chunker import chunk_text
from app.knowledge.parser import parse_pdf
from app.llm.client import LLMClient
from app.rag.embedder import Embedder
from app.rag.store import VectorStore
from app.system_prompt import SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class RagEngine:
    def __init__(self):
        self._lock = threading.Lock()
        self._embedder: Embedder | None = None
        self._store: VectorStore | None = None
        self._llm: LLMClient | None = None
        self._kb_state: dict[str, Any] = {
            "built_at": None, "documents": [], "chunks": 0,
            "skipped": [], "ingesting": False,
        }

    # ---------- 懒加载 ----------
    def _ensure_embedder_store(self) -> tuple[Embedder, VectorStore]:
        if self._store is None:
            with self._lock:
                if self._store is None:
                    self._embedder = Embedder()
                    self._store = VectorStore(settings.chroma_path, self._embedder)
        return self._embedder, self._store

    def _ensure_llm(self) -> LLMClient:
        if self._llm is None:
            with self._lock:
                if self._llm is None:
                    if not settings.deepseek_api_key:
                        raise RuntimeError("客服大脑未配置：请在 .env 填写 DEEPSEEK_API_KEY")
                    self._llm = LLMClient(
                        api_key=settings.deepseek_api_key,
                        base_url=settings.deepseek_base_url,
                        model=settings.deepseek_model,
                    )
        return self._llm

    # ---------- 知识库建档 ----------
    def ingest(self) -> dict[str, Any]:
        """扫描 PDF 目录 → 解析 → 分块 → 向量化 → 重建索引。"""
        self._ensure_embedder_store()
        pdf_dir = settings.pdf_path
        pdf_dir.mkdir(parents=True, exist_ok=True)
        files = sorted(pdf_dir.glob("*.pdf"))
        if not files:
            self._kb_state.update(
                {"built_at": None, "documents": [], "chunks": 0,
                 "skipped": ["知识库文件夹中没有 PDF 文件"], "ingesting": False})
            return {"ingested_files": 0, "chunks": 0, "skipped": ["无 PDF 文件"]}

        pages_all = []
        skipped: list[str] = []
        for f in files:
            try:
                pages = parse_pdf(f)
            except Exception as exc:
                logger.warning("解析失败 %s: %s", f.name, exc)
                skipped.append(f"{f.name}：解析失败（{exc}）")
                continue
            if not pages:
                skipped.append(f"{f.name}：无法提取文本（扫描件且 OCR 失败）")
            else:
                pages_all.extend(pages)

        # 分块
        blocks: list[tuple[str, int, str]] = []
        for page in pages_all:
            for text in chunk_text(page.text, settings.chunk_size, settings.chunk_overlap):
                blocks.append((page.source, page.page_no, text))

        if not blocks:
            self._kb_state.update(
                {"built_at": None, "documents": [], "chunks": 0,
                 "skipped": skipped, "ingesting": False})
            return {"ingested_files": 0, "chunks": 0, "skipped": skipped}

        # 向量化（批量）
        embedder, store = self._embedder, self._store
        embeddings = embedder.embed_documents([b[2] for b in blocks])
        ids = [f"{source}-p{page}-{i}" for i, (source, page, _) in enumerate(blocks)]
        metadatas = [{"source": source, "page": page} for source, page, _ in blocks]

        store.reset()
        store.add(ids=ids, documents=[b[2] for b in blocks],
                  metadatas=metadatas, embeddings=embeddings)

        doc_names = sorted({source for source, _, _ in blocks})
        self._kb_state.update({
            "built_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "documents": doc_names,
            "chunks": len(blocks),
            "skipped": skipped,
            "ingesting": False,
        })
        logger.info("建档完成：%d 份文档，%d 个分块", len(doc_names), len(blocks))
        return {"ingested_files": len(doc_names), "chunks": len(blocks),
                "documents": doc_names, "skipped": skipped}

    # ---------- 增量建档（仅上传的文件，不重建全部） ----------
    def ingest_files(self, files: list[Path]) -> dict[str, Any]:
        """解析并追加指定文件到现有索引，知识库其余部分不受影响。"""
        self._ensure_embedder_store()
        store: VectorStore = self._store  # type: ignore[assignment]
        blocks: list[tuple[str, int, str]] = []
        skipped: list[str] = []
        for f in files:
            try:
                pages = parse_pdf(f)
            except Exception as exc:
                logger.warning("解析失败 %s: %s", f.name, exc)
                skipped.append(f"{f.name}：解析失败（{exc}）")
                continue
            if not pages:
                skipped.append(f"{f.name}：无法提取文本（扫描件且 OCR 失败）")
                continue
            for page in pages:
                for text in chunk_text(page.text, settings.chunk_size, settings.chunk_overlap):
                    blocks.append((f.name, page.page_no, text))

        result = {"uploaded": [f.name for f in files], "chunks": len(blocks),
                  "skipped": skipped}
        if not blocks:
            return result

        # 向量化并追加（不 reset，保留已有索引）
        embedder, store = self._embedder, self._store
        embeddings = embedder.embed_documents([b[2] for b in blocks])
        ids = [f"{source}-{uuid.uuid4().hex[:10]}-{i}"
               for i, (source, _, _) in enumerate(blocks)]
        metadatas = [{"source": source, "page": page} for source, page, _ in blocks]
        store.add(ids=ids, documents=[b[2] for b in blocks],
                  metadatas=metadatas, embeddings=embeddings)

        # 更新内存状态：文档合并、分块数以向量库实际数为准
        new_docs = sorted({source for source, _, _ in blocks})
        old_docs = self._kb_state.get("documents") or []
        if not old_docs:
            old_docs = sorted({m.get("source") for m in store.all_meta() if m.get("source")})
        self._kb_state.update({
            "built_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "documents": sorted(set(old_docs) | set(new_docs)),
            "chunks": store.count(),
            "skipped": skipped,
            "ingesting": False,
        })
        logger.info("增量建档完成：%d 份文档，%d 个分块", len(new_docs), len(blocks))
        result["documents"] = new_docs
        return result

    # ---------- 检索 ----------
    def retrieve(self, question: str) -> list[dict[str, Any]]:
        embedder, store = self._ensure_embedder_store()
        q_emb = embedder.embed_query(question)
        return store.query(q_emb, n_results=settings.top_k, min_score=settings.min_score)

    # ---------- 问答 ----------
    def answer(self, question: str, files: list[str] | None = None) -> dict[str, Any]:
        question = question.strip()
        if not question:
            raise ValueError("问题不能为空")

        hits: list[dict[str, Any]] = []
        if files:
            # 用户指定文件：直接从这些文件取分块内容作为上下文，确保 AI 基于该文件回答
            store = self._ensure_embedder_store()[1]
            hits = store.get_by_sources(files)

        sources = [
            {"doc": h["source"], "page": h["page"]} for h in hits
        ]
        # 去重来源（按 文档+页码）
        seen, dedup = set(), []
        for s in sources:
            key = (s["doc"], s["page"])
            if key not in seen:
                seen.add(key)
                dedup.append(s)

        if files and hits:
            context = "\n\n".join(
                f"【来源：{h['source']} · 第{h['page']}页】\n{h['text']}" for h in hits
            )
            user_prompt = (
                f"用户上传并指定了文件：{'、'.join(files)}。"
                "请严格依据下面这些文件的内容回答，涉及具体数据时标注「（来源：{文档名}）」：\n\n"
                f"<资料>\n{context}\n</资料>\n\n"
                f"<问题>\n{question}\n</问题>"
            )
        elif hits:
            context = "\n\n".join(
                f"【来源：{h['source']} · 第{h['page']}页】\n{h['text']}" for h in hits
            )
            user_prompt = (
                "以下是知识库检索到的资料片段，请严格依据这些片段回答，"
                "涉及具体数据时标注「（来源：{文档名}）」：\n\n"
                f"<资料>\n{context}\n</资料>\n\n"
                f"<问题>\n{question}\n</问题>"
            )
        else:
            # 知识库无相关资料：让 AI 基于专业知识给出通用分析与建议（不得提示转人工、不附固定提示语）
            user_prompt = (
                "知识库中未检索到与该问题直接相关的资料。\n"
                "请基于农业专业知识先给出通用、稳妥的分析与建议"
                "（不得编造具体剂量、产量、价格、政策等数据，不附加温馨提示）。\n\n"
                f"<问题>\n{question}\n</问题>"
            )

        llm = self._ensure_llm()
        answer_text = llm.chat(SYSTEM_PROMPT, user_prompt)
        return {
            "answer": answer_text,
            "sources": dedup,
            "kb_ready": self._kb_state["chunks"] > 0,
        }

    def kb_status(self) -> dict[str, Any]:
        # 直接读向量库（不触发模型加载）：进程内已初始化则复用，否则轻量直连
        if self._store is not None:
            chunks, metas = self._store.count(), self._store.all_meta()
        else:
            try:
                import chromadb
                from app.rag.store import COLLECTION_NAME
                client = chromadb.PersistentClient(path=str(settings.chroma_path))
                col = client.get_collection(COLLECTION_NAME)
                chunks = col.count()
                data = col.get(include=["metadatas"])
                metas = [m for m in (data.get("metadatas") or []) if m]
            except Exception:
                chunks, metas = 0, []
        state = dict(self._kb_state)
        # 进程重启后内存状态为空，但向量库已有数据时，从向量库推导展示
        if state.get("chunks", 0) == 0 and chunks > 0:
            state["documents"] = sorted({m.get("source") for m in metas if m.get("source")})
            state["chunks"] = chunks
            state["built_at"] = state.get("built_at") or "（历史建档数据）"
        return {**state, "stored_chunks": chunks,
                "api_key_configured": bool(settings.deepseek_api_key)}

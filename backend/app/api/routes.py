"""API 路由：健康检查、问答、知识库建档/状态/上传。"""
import logging
import threading
import uuid

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

from app.config import settings
from app.rag.engine import RagEngine

logger = logging.getLogger(__name__)

router = APIRouter()
engine = RagEngine()
_ingest_lock = threading.Lock()


class ChatRequest(BaseModel):
    question: str
    recent_files: list[str] = []  # 用户本次会话上传的文件，问答时作为指定上下文


class ChatResponse(BaseModel):
    answer: str
    sources: list[dict]
    kb_ready: bool
    transferred_to_human: bool = False


def _build_chat_response(answer: str, sources: list[dict], kb_ready: bool) -> ChatResponse:
    return ChatResponse(answer=answer, sources=sources, kb_ready=kb_ready)


@router.get("/health")
def health():
    return {
        "status": "ok",
        "api_key_configured": bool(settings.deepseek_api_key),
        "kb_ready": engine.kb_status()["chunks"] > 0,
    }


@router.get("/api/kb/status")
def kb_status():
    return engine.kb_status()


@router.post("/api/kb/ingest")
def kb_ingest():
    """扫描 knowledge_base 文件夹并重建索引。"""
    if not _ingest_lock.acquire(blocking=False):
        raise HTTPException(status_code=409, detail="知识库正在建档中，请稍候")
    try:
        return engine.ingest()
    finally:
        _ingest_lock.release()


@router.post("/api/kb/upload")
async def kb_upload(files: list[UploadFile] = File(...)):
    """上传 PDF 到知识库文件夹（增量建档，不重建整个索引）。"""
    saved = []
    for f in files:
        if not f.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail=f"{f.filename} 不是 PDF 文件")
        dest = settings.pdf_path / f.filename
        content = await f.read()
        dest.write_bytes(content)
        saved.append(dest)
    if not _ingest_lock.acquire(blocking=False):
        raise HTTPException(status_code=409, detail="知识库正在建档中，请稍候")
    try:
        result = engine.ingest_files(saved)
        result["uploaded"] = [p.name for p in saved]
        return result
    finally:
        _ingest_lock.release()


@router.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="问题不能为空")
    if not settings.deepseek_api_key:
        raise HTTPException(
            status_code=503,
            detail="客服大脑未配置：请在项目根目录 .env 中填写 DEEPSEEK_API_KEY 后重启服务",
        )
    try:
        result = engine.answer(req.question, files=req.recent_files or None)
    except Exception as exc:
        logger.exception("问答失败")
        raise HTTPException(status_code=500, detail=f"服务处理失败：{exc}") from exc
    return _build_chat_response(
        answer=result["answer"], sources=result["sources"], kb_ready=result["kb_ready"]
    )

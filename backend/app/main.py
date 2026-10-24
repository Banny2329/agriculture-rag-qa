"""FastAPI 应用入口：uvicorn app.main:app --reload"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="农作物农技问答 RAG 智能客服", version="1.0.0")

# 开发环境放开跨域（前端 Vite 默认 5173 端口）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.on_event("startup")
def on_startup():
    logger.info("服务已启动：http://%s:%s （文档 http://%s:%s/docs）",
                settings.host, settings.port, settings.host, settings.port)
    if not settings.deepseek_api_key:
        logger.warning("未配置 DEEPSEEK_API_KEY，问答接口将返回 503；请在 .env 中填写后重启。")
    if not settings.pdf_path.exists() or not list(settings.pdf_path.glob("*.pdf")):
        logger.warning("知识库文件夹 %s 中暂无 PDF，请放入农技资料后调用 /api/kb/ingest 建档。",
                       settings.pdf_path)

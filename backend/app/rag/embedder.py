"""bge-small-zh-v1.5 向量化。首次使用会从 HF 镜像下载模型（约 100MB）。"""
import logging
import os

# 必须在导入 sentence_transformers 之前设置镜像，config.apply_env 已在包导入时执行
from app.config import settings

# 模型已本地缓存后走离线加载，避免加载时访问 HF 镜像偶发挂起阻塞服务
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# BAAI 官方建议的检索查询指令（仅用于 query，不用于文档）
_QUERY_INSTRUCTION = "为这个句子生成表示以用于检索相关文章："
_MODEL_NAME = "BAAI/bge-small-zh-v1.5"


class Embedder:
    """中文向量化封装，输出 L2 归一化向量（余弦相似度）。"""

    def __init__(self, model_name: str = _MODEL_NAME):
        logger.info("加载向量模型 %s ...", model_name)
        self._model = SentenceTransformer(model_name)
        logger.info("向量模型加载完成")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._model.encode(
            texts, normalize_embeddings=True, show_progress_bar=False
        ).tolist()

    def embed_query(self, text: str) -> list[float]:
        return self._model.encode(
            [_QUERY_INSTRUCTION + text], normalize_embeddings=True
        )[0].tolist()

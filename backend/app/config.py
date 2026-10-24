"""全局配置：从 .env 读取，未配置项使用默认值。"""
import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# 项目根目录（backend 的上一级）
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    # DeepSeek
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    # 知识库与向量库
    pdf_dir: str = "knowledge_base"
    chroma_dir: str = "data/chroma"
    top_k: int = 5
    chunk_size: int = 500
    chunk_overlap: int = 50
    min_score: float = 0.35

    # 模型下载镜像
    hf_endpoint: str = "https://hf-mirror.com"

    # 服务
    host: str = "127.0.0.1"
    port: int = 8000

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def pdf_path(self) -> Path:
        p = Path(self.pdf_dir)
        return p if p.is_absolute() else BASE_DIR / p

    @property
    def chroma_path(self) -> Path:
        p = Path(self.chroma_dir)
        return p if p.is_absolute() else BASE_DIR / p

    def apply_env(self) -> None:
        """将镜像等环境变量写入 os.environ（须在导入相关库之前调用）。"""
        if self.hf_endpoint:
            os.environ.setdefault("HF_ENDPOINT", self.hf_endpoint)


settings = Settings()
settings.apply_env()

# 兼容用户系统环境变量：.env 未填 Key 时，回退读取系统变量（DATAOPAI_API_KEY 为用户已有变量）
if not settings.deepseek_api_key:
    for var in ("DEEPSEEK_API_KEY", "DATAOPAI_API_KEY", "API_KEY"):
        if os.environ.get(var):
            settings.deepseek_api_key = os.environ[var]
            break

"""DeepSeek 对话接口（OpenAI 兼容）。"""
import logging

from openai import OpenAI

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self, api_key: str, base_url: str, model: str):
        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def chat(self, system: str, user: str,
             temperature: float = 0.3, max_tokens: int = 1200) -> str:
        resp = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return (resp.choices[0].message.content or "").strip()

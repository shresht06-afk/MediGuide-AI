import time
from collections.abc import Iterator

from openai import OpenAI

from .config import Settings
from .safety import SYSTEM_PROMPT


class LLMService:
    def __init__(self, config: Settings):
        self.config = config

    def _client(self) -> OpenAI:
        if not self.config.api_key:
            raise RuntimeError("The AI provider is not configured.")
        return OpenAI(base_url="https://openrouter.ai/api/v1", api_key=self.config.api_key, timeout=60.0)

    def stream(self, messages: list[dict]) -> Iterator[tuple[str, float | None]]:
        started = time.perf_counter()
        first_token: float | None = None
        stream = self._client().chat.completions.create(model=self.config.model, messages=[{"role": "system", "content": SYSTEM_PROMPT}, *messages[-12:]], stream=True)
        for chunk in stream:
            if not chunk.choices:
                continue
            text = chunk.choices[0].delta.content
            if text:
                if first_token is None:
                    first_token = time.perf_counter() - started
                yield text, first_token

"""LLM providers. In Russia use YandexGPT (default) or any OpenAI-compatible endpoint
(Yandex AI Studio compatible API, a self-hosted Qwen/DeepSeek via vLLM/Ollama, etc.)."""
from __future__ import annotations

import json
from typing import Protocol

import httpx


class LLMError(Exception):
    pass


class LLM(Protocol):
    async def complete(self, system: str, user: str, temperature: float = 0.3) -> str: ...


class YandexGPT:
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

    def __init__(self, api_key: str, folder_id: str, model: str = "yandexgpt/latest",
                 http: httpx.AsyncClient | None = None):
        if not api_key or not folder_id:
            raise LLMError("Для YandexGPT нужны YANDEX_API_KEY и YANDEX_FOLDER_ID")
        self.api_key, self.folder_id, self.model = api_key, folder_id, model
        self.http = http or httpx.AsyncClient(timeout=60)

    async def complete(self, system: str, user: str, temperature: float = 0.3) -> str:
        body = {
            "modelUri": f"gpt://{self.folder_id}/{self.model}",
            "completionOptions": {"stream": False, "temperature": temperature, "maxTokens": "2000"},
            "messages": [{"role": "system", "text": system}, {"role": "user", "text": user}],
        }
        headers = {"Authorization": f"Api-Key {self.api_key}", "x-folder-id": self.folder_id}
        try:
            r = await self.http.post(self.url, json=body, headers=headers)
        except httpx.HTTPError as e:
            raise LLMError(f"YandexGPT недоступен: {e.__class__.__name__}") from e
        if r.status_code != 200:
            raise LLMError(f"YandexGPT HTTP {r.status_code}: {r.text[:300]}")
        try:
            return r.json()["result"]["alternatives"][0]["message"]["text"]
        except (KeyError, IndexError, ValueError) as e:
            raise LLMError(f"YandexGPT: неожиданный ответ {r.text[:300]}") from e


class OpenAICompatible:
    def __init__(self, base_url: str, api_key: str, model: str, http: httpx.AsyncClient | None = None):
        if not base_url or not model:
            raise LLMError("Для OpenAI-совместимого API нужны OPENAI_BASE_URL и OPENAI_MODEL")
        self.base_url, self.api_key, self.model = base_url.rstrip("/"), api_key, model
        self.http = http or httpx.AsyncClient(timeout=60)

    async def complete(self, system: str, user: str, temperature: float = 0.3) -> str:
        body = {"model": self.model, "temperature": temperature,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        try:
            r = await self.http.post(f"{self.base_url}/chat/completions", json=body, headers=headers)
        except httpx.HTTPError as e:
            raise LLMError(f"LLM недоступна: {e.__class__.__name__}") from e
        if r.status_code != 200:
            raise LLMError(f"LLM HTTP {r.status_code}: {r.text[:300]}")
        try:
            return r.json()["choices"][0]["message"]["content"]
        except (KeyError, IndexError, ValueError) as e:
            raise LLMError(f"LLM: неожиданный ответ {r.text[:300]}") from e


class MockLLM:
    """Deterministic offline model for demos and tests (no translation quality!)."""

    async def complete(self, system: str, user: str, temperature: float = 0.3) -> str:
        data = json.loads(user)
        if "seller_text" in data:
            text = data["seller_text"]
            return json.dumps({"reply": f"{text}", "reply_translation": text}, ensure_ascii=False)
        rating = data.get("rating")
        reply = ("Спасибо за отзыв! Нам очень жаль, что так вышло — передали информацию на склад."
                 if rating and rating <= 3 else "Спасибо за ваш отзыв и выбор нашего магазина!")
        if data.get("kind") == "question":
            reply = "Здравствуйте! Уточним информацию и ответим вам."
        return json.dumps({"buyer_lang": "ru", "translation": data.get("text", ""), "reply": reply,
                           "reply_translation": reply, "needs_input": data.get("kind") == "question"},
                          ensure_ascii=False)


def make_llm(settings) -> LLM:
    p = settings.llm_provider
    if p == "yandex":
        return YandexGPT(settings.yandex_api_key, settings.yandex_folder_id, settings.yandex_model)
    if p == "openai":
        return OpenAICompatible(settings.openai_base_url, settings.openai_api_key, settings.openai_model)
    if p == "mock":
        return MockLLM()
    raise LLMError(f"Неизвестный LLM_PROVIDER={p}")

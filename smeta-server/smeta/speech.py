"""Распознавание речи для голосовых смет: голосовое → текст → обычный разбор работ.

Движок выбирается переменными окружения, бот не привязан к одному провайдеру:
    SMETA_STT_PROVIDER = openai | yandex   (по умолчанию openai)
    SMETA_STT_API_KEY  = ключ провайдера    (пусто = голос выключен)
    SMETA_STT_MODEL    = модель для openai   (по умолчанию whisper-1)

Telegram отдаёт голосовые в формате OGG/Opus — и Whisper, и Yandex принимают его
напрямую, перекодирование не нужно.
"""
from __future__ import annotations

import os

OPENAI_URL = "https://api.openai.com/v1/audio/transcriptions"
YANDEX_URL = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize"


def provider() -> str:
    return os.getenv("SMETA_STT_PROVIDER", "openai").strip().lower()


def api_key() -> str:
    return os.getenv("SMETA_STT_API_KEY", "").strip()


def enabled() -> bool:
    return bool(api_key()) and provider() not in {"", "off", "нет"}


async def transcribe(audio: bytes, filename: str = "voice.ogg") -> str:
    """Голосовое (OGG/Opus) → распознанный русский текст. Бросает исключение при ошибке сети/ключа."""
    name = provider()
    if name in {"openai", "whisper"}:
        return await _openai(audio, filename)
    if name == "yandex":
        return await _yandex(audio)
    raise RuntimeError(f"неизвестный провайдер распознавания речи: {name}")


async def _openai(audio: bytes, filename: str) -> str:
    import httpx

    url = os.getenv("SMETA_STT_URL", OPENAI_URL)
    model = os.getenv("SMETA_STT_MODEL", "whisper-1")
    headers = {"Authorization": f"Bearer {api_key()}"}
    files = {"file": (filename, audio, "audio/ogg")}
    data = {"model": model, "language": "ru"}
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(url, headers=headers, files=files, data=data)
        response.raise_for_status()
        return (response.json().get("text") or "").strip()


async def _yandex(audio: bytes) -> str:
    import httpx

    url = os.getenv("SMETA_STT_URL", YANDEX_URL)
    headers = {"Authorization": f"Api-Key {api_key()}"}
    params = {"lang": "ru-RU", "topic": "general", "format": "oggopus"}
    folder = os.getenv("SMETA_STT_FOLDER_ID", "").strip()
    if folder:
        params["folderId"] = folder
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(url, headers=headers, params=params, content=audio)
        response.raise_for_status()
        return (response.json().get("result") or "").strip()

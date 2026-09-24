"""Demo marketplace: realistic sample reviews/questions, replies go nowhere.

Used for the crowdfunding video, onboarding without API keys, and manual testing.
"""
from __future__ import annotations

from .base import BaseClient, Incoming

SAMPLES = [
    Incoming("demo-1", "review", "Пришёл с трещиной на крышке, упаковка была мятая. Товар в целом нормальный, но осадок остался.",
             "Термокружка Steel 450 мл", "100001", 2),
    Incoming("demo-2", "review", "", "Термокружка Steel 450 мл", "100001", 5),
    Incoming("demo-3", "question", "Бул кружка посудомоечная машинада жууга болобу?", "Термокружка Steel 450 мл", "100001"),
    Incoming("demo-4", "review", "Juda yaxshi, issiqlikni uzoq saqlaydi. Rahmat!", "Термокружка Steel 450 мл", "100001", 5),
    Incoming("demo-5", "question", "Есть ли размер побольше, литр например?", "Термокружка Steel 450 мл", "100001"),
]


class DemoClient(BaseClient):
    code = "demo"

    def headers(self) -> dict:
        return {}

    async def check(self) -> None:
        return None

    async def fetch_new(self, limit: int) -> list[Incoming]:
        return SAMPLES[:limit]

    async def reply(self, kind: str, external_id: str, text: str, extra: dict) -> None:
        return None

"""Wildberries: Feedbacks & Questions API (feedbacks-api.wildberries.ru).

Token: seller cabinet -> Settings -> API access, category "Questions and reviews" (Вопросы и отзывы).
"""
from __future__ import annotations

from .base import BaseClient, Incoming, MarketplaceError


class WildberriesClient(BaseClient):
    code = "wildberries"
    base_url = "https://feedbacks-api.wildberries.ru"

    def headers(self) -> dict:
        return {"Authorization": self.creds["token"]}

    async def _get(self, path: str, take: int) -> dict:
        j = await self.request("GET", path, params={"isAnswered": "false", "take": take, "skip": 0, "order": "dateDesc"})
        if j.get("error"):
            raise MarketplaceError(f"wildberries: {j.get('errorText') or j}")
        return j.get("data") or {}

    async def check(self) -> None:
        await self._get("/api/v1/feedbacks", 1)

    async def fetch_new(self, limit: int) -> list[Incoming]:
        out: list[Incoming] = []
        for fb in (await self._get("/api/v1/feedbacks", limit)).get("feedbacks") or []:
            pd = fb.get("productDetails") or {}
            parts = [fb.get("text") or ""]
            if fb.get("pros"):
                parts.append(f"Достоинства: {fb['pros']}")
            if fb.get("cons"):
                parts.append(f"Недостатки: {fb['cons']}")
            out.append(Incoming(
                external_id=str(fb["id"]), kind="review", text="\n".join(p for p in parts if p).strip(),
                product=pd.get("productName") or "", sku=str(pd.get("nmId") or ""),
                rating=fb.get("productValuation"),
            ))
        for q in (await self._get("/api/v1/questions", limit)).get("questions") or []:
            pd = q.get("productDetails") or {}
            out.append(Incoming(
                external_id=str(q["id"]), kind="question", text=q.get("text") or "",
                product=pd.get("productName") or "", sku=str(pd.get("nmId") or ""),
            ))
        return out

    async def reply(self, kind: str, external_id: str, text: str, extra: dict) -> None:
        if kind == "review":
            await self.request("POST", "/api/v1/feedbacks/answer", json={"id": external_id, "text": text})
        else:
            await self.request("PATCH", "/api/v1/questions",
                               json={"id": external_id, "answer": {"text": text}, "state": "wbRu"})

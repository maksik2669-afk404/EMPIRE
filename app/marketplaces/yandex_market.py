"""Yandex Market Partner API (api.partner.market.yandex.ru) — product reviews.

Key: partner cabinet -> Settings -> API and modules -> API key with access to reviews ("Отзывы").
businessId: the cabinet ID shown in the partner cabinet URL/settings.
Questions via API are not in the MVP yet; they still have to be answered in the cabinet.
"""
from __future__ import annotations

from .base import BaseClient, Incoming, MarketplaceError


class YandexMarketClient(BaseClient):
    code = "yandex_market"
    base_url = "https://api.partner.market.yandex.ru"

    def headers(self) -> dict:
        return {"Api-Key": self.creds["api_key"]}

    @property
    def _biz(self) -> str:
        return f"/businesses/{int(self.creds['business_id'])}"

    async def _feedbacks(self, limit: int) -> list[dict]:
        j = await self.request("POST", f"{self._biz}/goods-feedback",
                               params={"limit": max(1, min(limit, 50))}, json={"reactionStatus": "NEED_REACTION"})
        if j.get("status") == "ERROR":
            raise MarketplaceError(f"yandex_market: {j.get('errors')}")
        return (j.get("result") or {}).get("feedbacks") or []

    async def check(self) -> None:
        await self._feedbacks(1)

    async def fetch_new(self, limit: int) -> list[Incoming]:
        out = []
        for fb in await self._feedbacks(limit):
            d = fb.get("description") or {}
            parts = [d.get("comment") or ""]
            if d.get("advantages"):
                parts.append(f"Достоинства: {d['advantages']}")
            if d.get("disadvantages"):
                parts.append(f"Недостатки: {d['disadvantages']}")
            ident = fb.get("identifiers") or {}
            out.append(Incoming(
                external_id=str(fb["feedbackId"]), kind="review", text="\n".join(p for p in parts if p).strip(),
                sku=str(ident.get("offerId") or ""), rating=(fb.get("statistics") or {}).get("rating"),
            ))
        return out

    async def reply(self, kind: str, external_id: str, text: str, extra: dict) -> None:
        await self.request("POST", f"{self._biz}/goods-feedback/comments/update",
                           json={"feedbackId": int(external_id), "comment": {"text": text}})

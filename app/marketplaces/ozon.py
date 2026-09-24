"""Ozon Seller API (api-seller.ozon.ru).

IMPORTANT: Ozon opens the review and question methods only to sellers with the
Premium Plus / Premium Pro subscription. Without it the API answers 403.
"""
from __future__ import annotations

from .base import AuthError, BaseClient, Incoming


class OzonClient(BaseClient):
    code = "ozon"
    base_url = "https://api-seller.ozon.ru"

    def headers(self) -> dict:
        return {"Client-Id": str(self.creds["client_id"]), "Api-Key": self.creds["api_key"]}

    async def _reviews(self, limit: int) -> list[dict]:
        j = await self.request("POST", "/v1/review/list",
                               json={"limit": max(20, min(limit, 100)), "sort_dir": "DESC", "status": "UNPROCESSED"})
        return j.get("reviews") or []

    async def check(self) -> None:
        try:
            await self._reviews(20)
        except AuthError as e:
            raise AuthError(f"{e}. Проверьте Client-Id/Api-Key и подписку Premium Plus/Pro — "
                            "без неё Ozon не отдаёт отзывы через API.") from e

    async def fetch_new(self, limit: int) -> list[Incoming]:
        out = [
            Incoming(external_id=str(r["id"]), kind="review", text=r.get("text") or "",
                     sku=str(r.get("sku") or ""), rating=r.get("rating"))
            for r in (await self._reviews(limit))[:limit]
        ]
        j = await self.request("POST", "/v1/question/list", json={"filter": {"status": "UNPROCESSED"}, "last_id": ""})
        for q in (j.get("questions") or [])[:limit]:
            out.append(Incoming(external_id=str(q["id"]), kind="question", text=q.get("text") or "",
                                sku=str(q.get("sku") or ""), extra={"sku": q.get("sku")}))
        return out

    async def reply(self, kind: str, external_id: str, text: str, extra: dict) -> None:
        if kind == "review":
            await self.request("POST", "/v1/review/comment/create",
                               json={"review_id": external_id, "text": text, "mark_review_as_processed": True})
        else:
            await self.request("POST", "/v1/question/answer/create",
                               json={"question_id": external_id, "sku": int(extra["sku"]), "text": text})

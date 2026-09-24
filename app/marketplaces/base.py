"""Common marketplace client: retries, error mapping, normalised incoming items."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

import httpx


class MarketplaceError(Exception):
    """Temporary or unexpected marketplace error."""


class AuthError(MarketplaceError):
    """Invalid key / no access (401, 403). The account needs the seller's attention."""


@dataclass
class Incoming:
    external_id: str
    kind: str  # "review" | "question"
    text: str
    product: str = ""
    sku: str = ""
    rating: int | None = None
    extra: dict = field(default_factory=dict)


class BaseClient:
    code = ""
    base_url = ""
    retries = 3

    def __init__(self, creds: dict, http: httpx.AsyncClient | None = None):
        self.creds = creds
        self._http = http or httpx.AsyncClient(timeout=30)
        self._own_http = http is None

    def headers(self) -> dict:
        raise NotImplementedError

    async def request(self, method: str, path: str, **kw) -> dict:
        url = self.base_url + path
        delay = 1.0
        for attempt in range(self.retries):
            try:
                r = await self._http.request(method, url, headers=self.headers(), **kw)
            except httpx.HTTPError as e:
                if attempt == self.retries - 1:
                    raise MarketplaceError(f"{self.code}: сеть недоступна ({e.__class__.__name__})") from e
                await asyncio.sleep(delay)
                delay *= 2
                continue
            if r.status_code in (401, 403):
                raise AuthError(f"{self.code}: доступ запрещён ({r.status_code}): {self._err(r)}")
            if r.status_code == 429 or r.status_code >= 500:
                if attempt == self.retries - 1:
                    raise MarketplaceError(f"{self.code}: HTTP {r.status_code}: {self._err(r)}")
                retry_after = r.headers.get("Retry-After") or r.headers.get("X-Ratelimit-Retry")
                await asyncio.sleep(float(retry_after) if retry_after and retry_after.isdigit() else delay)
                delay *= 2
                continue
            if r.status_code >= 400:
                raise MarketplaceError(f"{self.code}: HTTP {r.status_code}: {self._err(r)}")
            if not r.content:
                return {}
            try:
                return r.json()
            except ValueError:
                return {}
        raise MarketplaceError(f"{self.code}: исчерпаны попытки")  # pragma: no cover

    @staticmethod
    def _err(r: httpx.Response) -> str:
        try:
            j = r.json()
        except ValueError:
            return r.text[:300]
        if isinstance(j, dict):
            errs = j.get("errors")
            if isinstance(errs, list) and errs and isinstance(errs[0], dict):
                return str(errs[0].get("message") or errs[0])[:300]
            return str(j.get("errorText") or j.get("message") or j.get("detail") or j)[:300]
        return str(j)[:300]

    async def close(self) -> None:
        if self._own_http:
            await self._http.aclose()

    # --- interface implemented by every marketplace
    async def check(self) -> None:
        """Raises AuthError/MarketplaceError if the credentials do not work."""
        raise NotImplementedError

    async def fetch_new(self, limit: int) -> list[Incoming]:
        """Unanswered reviews and questions, newest first."""
        raise NotImplementedError

    async def reply(self, kind: str, external_id: str, text: str, extra: dict) -> None:
        raise NotImplementedError

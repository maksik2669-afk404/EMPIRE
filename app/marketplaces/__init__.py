from __future__ import annotations

import httpx

from .base import AuthError, BaseClient, Incoming, MarketplaceError
from .demo import DemoClient
from .ozon import OzonClient
from .wildberries import WildberriesClient
from .yandex_market import YandexMarketClient

CLIENTS: dict[str, type[BaseClient]] = {
    "wildberries": WildberriesClient,
    "ozon": OzonClient,
    "yandex_market": YandexMarketClient,
    "demo": DemoClient,
}

TITLES = {"wildberries": "Wildberries", "ozon": "Ozon", "yandex_market": "Яндекс Маркет", "demo": "Demo"}


def parse_credentials(marketplace: str, raw: str) -> dict:
    """Turns the seller's message into a credentials dict. Raises ValueError on bad format."""
    parts = raw.split()
    if marketplace == "wildberries":
        if len(parts) != 1 or len(parts[0]) < 20:
            raise ValueError("wb")
        return {"token": parts[0]}
    if marketplace == "ozon":
        if len(parts) != 2 or not parts[0].isdigit():
            raise ValueError("ozon")
        return {"client_id": parts[0], "api_key": parts[1]}
    if marketplace == "yandex_market":
        if len(parts) != 2:
            raise ValueError("ym")
        key, biz = (parts[0], parts[1]) if parts[1].isdigit() else (parts[1], parts[0])
        if not biz.isdigit():
            raise ValueError("ym")
        return {"api_key": key, "business_id": biz}
    if marketplace == "demo":
        return {}
    raise ValueError(marketplace)


def make_client(marketplace: str, creds: dict, http: httpx.AsyncClient | None = None) -> BaseClient:
    return CLIENTS[marketplace](creds, http)


__all__ = ["AuthError", "BaseClient", "Incoming", "MarketplaceError", "CLIENTS", "TITLES",
           "parse_credentials", "make_client"]

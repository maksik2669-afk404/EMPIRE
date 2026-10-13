"""Shared state for the Telegram layer: dependencies and access to the current estimate."""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from .catalog import Catalog
from .materials import OfferBook
from .model import Estimate
from .store import Store

DATA = Path(os.getenv("SMETA_DATA_DIR", "data"))


@dataclass
class Deps:
    store: Store
    catalog: Catalog
    offers: OfferBook
    export_dir: Path
    logo_dir: Path = field(default_factory=lambda: DATA / "logos")
    bot_username: str = ""                    # для реферальных ссылок t.me/<bot>?start=ref_<id>


@dataclass
class Ctx:
    """Everything a screen needs to render itself."""

    deps: Deps
    tg_id: int
    data: dict = field(default_factory=dict)

    def current(self) -> tuple[int, Estimate] | None:
        return current(self.deps, self.tg_id)

    def catalog(self) -> Catalog:
        return self.deps.store.catalog(self.tg_id, self.deps.catalog)

    def offers(self) -> OfferBook:
        return self.deps.store.offers(self.tg_id, self.deps.offers)

    def settings(self) -> dict:
        return self.deps.store.settings(self.tg_id)

    def logo(self) -> Path | None:
        for suffix in (".png", ".jpg"):
            path = self.deps.logo_dir / f"{self.tg_id}{suffix}"
            if path.exists():
                return path
        return None


def current(deps: Deps, tg_id: int) -> tuple[int, Estimate] | None:
    estimate_id = deps.store.settings(tg_id)["current_id"]
    if not estimate_id:
        return None
    estimate = deps.store.load_estimate(tg_id, int(estimate_id))
    return (int(estimate_id), estimate) if estimate else None


def new_estimate(deps: Deps, tg_id: int, *, object_name: str = "", customer: str = "", contract: str = "") -> tuple[int, Estimate]:
    settings = deps.store.settings(tg_id)
    catalog = deps.store.catalog(tg_id, deps.catalog)
    estimate = Estimate(
        number=deps.store.next_number(tg_id),
        title="Локальная смета",
        customer=customer,
        object_name=object_name,
        contract=contract,
        date=date.today(),
        company=deps.store.company(tg_id),
        indices=catalog.index(settings["index_name"] or None),
        vat_pct=settings["vat_pct"],
        floor_with_nr=settings["floor_with_nr"],
        basis="справочник расценок / договорные цены",
    )
    estimate_id = deps.store.save_estimate(tg_id, estimate)
    deps.store.update_settings(tg_id, current_id=estimate_id)
    return estimate_id, estimate


def save(deps: Deps, tg_id: int, estimate_id: int, estimate: Estimate) -> None:
    deps.store.save_estimate(tg_id, estimate, estimate_id)


def safe_name(text: str) -> str:
    return re.sub(r"[^\w\-. ]+", "_", text, flags=re.U).strip() or "smeta"

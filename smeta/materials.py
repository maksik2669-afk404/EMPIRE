"""Supplier offers: price lists with discounts, used to price materials and count margin.

The client-facing estimate always shows the retail price. Purchase prices, discounts and
suppliers live here and never reach the exported estimate.
"""
from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

from .catalog import tokens
from .money import ONE, ZERO, dec, money, pct
from .units import norm_unit

CASHLESS = "безнал"
CASH = "нал"


@dataclass
class Offer:
    """One line of a supplier price list."""

    material: str
    unit: str = "шт"
    price: Decimal = ZERO            # прайс поставщика до скидки
    discount_pct: Decimal = ZERO     # скидка подрядчику
    retail: Decimal | None = None    # розница (что обычно ставят в смету заказчику)
    supplier: str = ""
    inn: str = ""
    payment: str = CASHLESS
    min_qty: Decimal = ZERO
    note: str = ""
    keywords: str = ""

    def __post_init__(self) -> None:
        self.unit = norm_unit(self.unit) or "шт"
        self.price = dec(self.price)
        self.discount_pct = dec(self.discount_pct)
        self.min_qty = dec(self.min_qty)
        if self.retail is not None:
            self.retail = dec(self.retail)
        self.payment = CASH if str(self.payment).strip().lower().startswith(("нал", "cash")) else CASHLESS

    @property
    def net(self) -> Decimal:
        """Purchase price for the contractor, discount applied."""
        return money(self.price * (ONE - pct(self.discount_pct)))

    @property
    def sell(self) -> Decimal:
        """Price to put in the estimate: retail if given, otherwise the undiscounted price."""
        return money(self.retail if self.retail is not None else self.price)

    def search_text(self) -> str:
        return f"{self.material} {self.keywords}"


@dataclass
class OfferBook:
    offers: list[Offer] = field(default_factory=list)

    @classmethod
    def from_csv(cls, text: str) -> "OfferBook":
        lines = text.lstrip("﻿").splitlines()
        while lines and (not lines[0].strip() or lines[0].lstrip().startswith("#")):
            lines.pop(0)
        body = "\n".join(lines)
        delimiter = ";" if ";" in (lines[0] if lines else "") else ","
        out: list[Offer] = []
        for row in csv.DictReader(io.StringIO(body), delimiter=delimiter):
            values = {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
            name = values.get("material") or values.get("наименование") or ""
            if not name:
                continue
            out.append(
                Offer(
                    material=name,
                    unit=values.get("unit") or values.get("ед.изм.") or values.get("ед") or "шт",
                    price=dec(values.get("price") or values.get("цена")),
                    discount_pct=dec(values.get("discount") or values.get("скидка")),
                    retail=dec(values["retail"], None) if values.get("retail") else (
                        dec(values["розница"], None) if values.get("розница") else None),
                    supplier=values.get("supplier") or values.get("поставщик") or "",
                    inn=values.get("inn") or values.get("инн") or "",
                    payment=values.get("payment") or values.get("оплата") or CASHLESS,
                    min_qty=dec(values.get("min_qty") or values.get("минимум")),
                    note=values.get("note") or values.get("примечание") or "",
                    keywords=values.get("keywords") or values.get("ключевые слова") or "",
                )
            )
        return cls(out)

    @classmethod
    def load(cls, path: Path | str) -> "OfferBook":
        p = Path(path)
        return cls.from_csv(p.read_text(encoding="utf-8")) if p.exists() else cls()

    def find(self, name: str, unit: str | None = None, *, threshold: float = 0.5) -> list[Offer]:
        """Offers for a material, cheapest purchase price first."""
        wanted = tokens(name)
        if not wanted:
            return []
        scored: list[tuple[float, Offer]] = []
        for offer in self.offers:
            have = set(tokens(offer.search_text()))
            if not have:
                continue
            hits = sum(1 for word in wanted if word in have)
            score = hits / len(wanted)
            if unit and norm_unit(unit) != offer.unit:
                score *= 0.6
            if score >= threshold:
                scored.append((score, offer))
        scored.sort(key=lambda pair: (-pair[0], pair[1].net))
        return [offer for _, offer in scored]

    def best(self, name: str, unit: str | None = None) -> Offer | None:
        found = self.find(name, unit)
        return found[0] if found else None

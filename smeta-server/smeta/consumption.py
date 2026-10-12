"""Материалы из объёмов работ по нормам расхода — с округлением до упаковок."""
from __future__ import annotations

import math
from decimal import Decimal

from . import datafiles
from .catalog import _is_demolition, tokens
from .materials import OfferBook
from .model import MATERIAL, WORK, Estimate, Position
from .money import ZERO, dec, money, pct, qty_str

SOURCE = "нормы расхода"
SECTION = "Материалы по нормам расхода"


def _rule_matches(rule: str, name_tokens: set[str]) -> bool:
    want = [word for word in rule.split() if not word.startswith("-")]
    avoid = [word[1:] for word in rule.split() if word.startswith("-")]
    return (all(any(t in name_tokens for t in tokens(word)) for word in want)
            and not any(any(t in name_tokens for t in tokens(word)) for word in avoid))


def calculate(estimate: Estimate, offers: OfferBook | None = None) -> list[Position]:
    """Material positions for all work positions; one line per material, packs rounded up."""
    needs: dict[str, dict] = {}
    for position in estimate.positions:
        if position.kind != WORK or position.qty <= ZERO:
            continue
        name_tokens = set(tokens(position.name))
        if _is_demolition(list(name_tokens)):
            continue
        for rule in datafiles.material_norms():
            if not _rule_matches(rule.get("match", ""), name_tokens):
                continue
            material = rule["material"]
            need = position.qty * dec(rule.get("per_unit")) * (1 + pct(rule.get("waste")))
            entry = needs.setdefault(material, {"rule": rule, "need": ZERO, "works": []})
            entry["need"] += need
            entry["works"].append(position.name)
    out: list[Position] = []
    for material, entry in needs.items():
        rule = entry["rule"]
        pack = dec(rule.get("pack")) or Decimal(1)
        packs = Decimal(math.ceil(entry["need"] / pack))
        offer = offers.best(material) if offers else None
        price = offer.sell * (pack if offer.unit == rule.get("unit") and pack != 1 else 1) if offer else dec(rule.get("price"))
        cost = offer.net * (pack if offer.unit == rule.get("unit") and pack != 1 else 1) if offer else None
        position = Position.commercial(material, packs, rule.get("pack_unit") or "шт", money(price),
                                       kind=MATERIAL, cost=cost, section=SECTION)
        position.source = SOURCE
        position.note = f"{qty_str(money(entry['need']))} {rule.get('unit')} по норме, упаковка {qty_str(pack)}"
        out.append(position)
    return out


def apply(estimate: Estimate, offers: OfferBook | None = None) -> list[Position]:
    """Replace previously calculated material lines with a fresh calculation."""
    fresh = calculate(estimate, offers)
    estimate.positions = [p for p in estimate.positions if p.source != SOURCE] + fresh
    return fresh

"""Draft lines + rate catalog -> estimate positions, with an honest status per line."""
from __future__ import annotations

from dataclasses import dataclass, field

from .catalog import Catalog, Rate
from .materials import OfferBook
from .model import MATERIAL, Position
from .money import ZERO
from .parser import DraftLine, parse_text
from .units import norm_unit, parse_unit

MATCHED = "matched"            # found in the catalog, norms applied
PRICED = "priced"              # the customer named the price - no catalog needed
FROM_PRICE_LIST = "price_list"  # a material priced from a supplier price list
NEEDS_PRICE = "needs_price"     # not in the catalog and no price given: ask the user
UNIT_MISMATCH = "unit_mismatch"  # found, but the rate is measured in something else


@dataclass
class Match:
    draft: DraftLine
    position: Position
    status: str
    score: float = 0.0
    rate: Rate | None = None
    alternatives: list[Rate] = field(default_factory=list)
    offer: object | None = None   # materials.Offer, when priced from a price list

    @property
    def needs_input(self) -> bool:
        return self.status in (NEEDS_PRICE, UNIT_MISMATCH)

    @property
    def comment(self) -> str:
        if self.status == MATCHED:
            return f"{self.rate.code} · совпадение {int(self.score * 100)}%" if self.rate else ""
        if self.status == PRICED:
            return "цена задана вручную"
        if self.status == FROM_PRICE_LIST:
            return f"прайс: {self.offer.supplier}" if self.offer else "по прайсу"
        if self.status == UNIT_MISMATCH:
            return f"расценка {self.rate.code} в «{self.rate.unit}», указано «{self.draft.unit}»" if self.rate else ""
        return "нет в справочнике — нужна цена"


def build(
    drafts: list[DraftLine],
    catalog: Catalog,
    *,
    offers: OfferBook | None = None,
    section: str = "",
    threshold: float = 0.55,
) -> list[Match]:
    """Turn drafts into positions. Nothing is invented: unmatched lines come back with price 0."""
    out: list[Match] = []
    for draft in drafts:
        found = catalog.search(draft.name, limit=4)
        best = found[0] if found and found[0][1] >= threshold else None
        alternatives = [rate for rate, _ in found[1:]]

        if not draft.has_price and draft.kind == MATERIAL and offers is not None:
            offer = offers.best(draft.name, draft.unit)
            if offer is not None:
                position = Position.commercial(
                    offer.material, draft.qty, draft.unit or offer.unit, offer.sell,
                    kind=MATERIAL, cost=offer.net, section=section,
                )
                out.append(Match(draft, position, FROM_PRICE_LIST, 1.0, None, alternatives, offer))
                continue

        if draft.has_price:
            # The customer's own price wins over any catalog norm.
            offer = offers.best(draft.name, draft.unit) if (offers and draft.kind == MATERIAL) else None
            position = Position.commercial(
                _title(draft, best[0] if best else None),
                draft.qty,
                draft.unit,
                draft.price,
                kind=draft.kind,
                cost=offer.net if offer else None,
                section=section,
            )
            if best:
                position.code = best[0].code
            out.append(Match(draft, position, PRICED, best[1] if best else 0.0, best[0] if best else None, alternatives))
            continue

        if best:
            rate = best[0]
            _, rate_unit = parse_unit(rate.unit)
            mismatch = bool(draft.unit) and not draft.qty_guessed and norm_unit(draft.unit) != rate_unit
            position = Position.from_rate(rate, draft.qty, catalog.norms(rate.work_type), section=section)
            if mismatch:
                position.note = f"проверьте единицу: расценка в «{rate.unit}»"
            out.append(
                Match(draft, position, UNIT_MISMATCH if mismatch else MATCHED, best[1], rate, alternatives)
            )
            continue

        position = Position.commercial(
            _title(draft, None), draft.qty, draft.unit, ZERO, kind=draft.kind, section=section
        )
        out.append(Match(draft, position, NEEDS_PRICE, 0.0, None, alternatives))
    return out


def build_from_text(text: str, catalog: Catalog, **kwargs) -> list[Match]:
    return build(parse_text(text), catalog, **kwargs)


def _title(draft: DraftLine, rate: Rate | None) -> str:
    """Keep what the user typed, but use the catalog wording when it clearly matches."""
    if rate and len(draft.name) < 12:
        return rate.name
    return draft.name[:1].upper() + draft.name[1:]

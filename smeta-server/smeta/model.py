"""Estimate model: positions, totals (direct costs + NR/SP + VAT), cuts and markups.

Two kinds of positions live side by side:
  * normative  - FER-style norms (OT/EM/ZPM/MAT per published unit) + indices + NR/SP;
  * commercial - a single unit price agreed with the customer ("цена за работу").
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from datetime import date
from decimal import Decimal

from .catalog import Indices, NrSp, Rate
from .money import ONE, ZERO, dec, money, pct, rub
from .units import norm_unit, parse_unit

WORK = "work"
MATERIAL = "material"
EQUIPMENT = "equipment"
KINDS = (WORK, MATERIAL, EQUIPMENT)
KIND_TITLES = {WORK: "Работы", MATERIAL: "Материалы", EQUIPMENT: "Оборудование"}


def inn_is_valid(inn: str) -> bool:
    """Checksum check for 10- and 12-digit INN (order of Minfin / FNS algorithm)."""
    digits = re.sub(r"\D", "", inn or "")
    if len(digits) not in (10, 12):
        return False
    nums = [int(c) for c in digits]

    def control(weights: list[int]) -> int:
        return sum(w * n for w, n in zip(weights, nums)) % 11 % 10

    if len(digits) == 10:
        return control([2, 4, 10, 3, 5, 9, 4, 6, 8]) == nums[9]
    first = control([7, 2, 4, 10, 3, 5, 9, 4, 6, 8])
    second = control([3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8])
    return first == nums[10] and second == nums[11]


@dataclass
class Company:
    """Header of the printed estimate: who issues it."""

    name: str = ""
    inn: str = ""
    kpp: str = ""
    address: str = ""
    phone: str = ""
    email: str = ""
    signer: str = ""
    signer_title: str = "Директор"
    vat_payer: bool = True

    @property
    def filled(self) -> bool:
        return bool(self.name and self.inn)

    def header_lines(self) -> list[str]:
        parts = [self.name] if self.name else []
        ids = ", ".join(x for x in (f"ИНН {self.inn}" if self.inn else "", f"КПП {self.kpp}" if self.kpp else "") if x)
        if ids:
            parts.append(ids)
        if self.address:
            parts.append(self.address)
        contacts = ", ".join(x for x in (self.phone, self.email) if x)
        if contacts:
            parts.append(contacts)
        return parts


@dataclass
class PositionCosts:
    """One position recalculated into current prices."""

    ot: Decimal = ZERO
    em: Decimal = ZERO
    zpm: Decimal = ZERO
    mat: Decimal = ZERO
    other: Decimal = ZERO     # договорная цена позиции (НР/СП и маржа уже внутри)
    nr: Decimal = ZERO
    sp: Decimal = ZERO
    tz: Decimal = ZERO

    @property
    def direct(self) -> Decimal:
        return self.ot + self.em + self.mat + self.other

    @property
    def total(self) -> Decimal:
        return money(self.direct + self.nr + self.sp)

    def floor(self, with_nr: bool = True) -> Decimal:
        """Below this the position is sold at a loss: direct costs (+ overheads), zero profit."""
        return money(self.direct + (self.nr if with_nr else ZERO))


@dataclass
class Position:
    name: str
    unit: str = "шт"
    qty: Decimal = ONE
    kind: str = WORK
    code: str = ""
    section: str = ""
    note: str = ""
    # commercial price (already in current prices, NR/SP and margin included)
    unit_price: Decimal | None = None
    unit_cost: Decimal | None = None      # self cost per unit, if known (for loss warnings)
    # normative norms per published unit, base prices
    ot: Decimal = ZERO
    em: Decimal = ZERO
    zpm: Decimal = ZERO
    mat: Decimal = ZERO
    tz: Decimal = ZERO
    unit_factor: Decimal = ONE            # '100 м2' -> 100
    nr_pct: Decimal = ZERO
    sp_pct: Decimal = ZERO
    coef: Decimal = ONE                   # поправочный коэффициент к объёму расценки
    adj: Decimal = ONE                    # накопленный рез/наценка
    source: str = ""
    # коэффициенты к элементам затрат (стеснённость, высота, ночное время...)
    k_ot: Decimal = ONE
    k_em: Decimal = ONE
    k_mat: Decimal = ONE
    k_basis: str = ""
    # выполнение: отмечено прорабом и закрыто актами КС-2 (в единицах позиции)
    done: Decimal = ZERO
    acted: Decimal = ZERO
    # сдельная ставка бригады за единицу (наряд-задание)
    crew_price: Decimal | None = None

    def __post_init__(self) -> None:
        self.qty = dec(self.qty)
        self.unit = norm_unit(self.unit) or "шт"
        for name in ("ot", "em", "zpm", "mat", "tz", "nr_pct", "sp_pct", "done", "acted"):
            setattr(self, name, dec(getattr(self, name)))
        self.unit_factor = dec(self.unit_factor, ONE) or ONE
        for name in ("coef", "adj", "k_ot", "k_em", "k_mat"):
            setattr(self, name, dec(getattr(self, name), ONE))
        for name in ("unit_price", "unit_cost", "crew_price"):
            value = getattr(self, name)
            if value is not None and value != "":
                setattr(self, name, dec(value))
            else:
                setattr(self, name, None)

    # ---------- money ----------

    @property
    def normative(self) -> bool:
        return self.unit_price is None

    @property
    def norm_qty(self) -> Decimal:
        """Quantity expressed in published units (85 м2 of a '100 м2' rate -> 0.85)."""
        return self.qty / self.unit_factor * self.coef

    def costs(self, indices: Indices) -> PositionCosts:
        if not self.normative:
            # a commercial price is a lump sum: no cost structure to report.
            # Its coefficient is the one for labour (works) or for materials.
            k = self.k_mat if self.kind == MATERIAL else self.k_ot
            return PositionCosts(other=money(self.qty * (self.unit_price or ZERO) * self.adj * k))
        n = self.norm_qty
        ot = self.ot * n * indices.ot * self.adj * self.k_ot
        em = self.em * n * indices.em * self.adj * self.k_em
        zpm = self.zpm * n * indices.zpm_index() * self.adj * self.k_em
        mat = self.mat * n * indices.mat * self.adj * self.k_mat
        fot = ot + zpm
        return PositionCosts(
            ot=money(ot),
            em=money(em),
            zpm=money(zpm),
            mat=money(mat),
            nr=money(fot * pct(self.nr_pct)),
            sp=money(fot * pct(self.sp_pct)),
            tz=self.tz * n,
        )

    def total(self, indices: Indices) -> Decimal:
        return self.costs(indices).total

    def base_total(self, indices: Indices) -> Decimal:
        """Total before any cut/markup - the reference point for '-20%'."""
        if self.adj == ONE:
            return self.total(indices)
        clone = self.copy()
        clone.adj = ONE
        return clone.total(indices)

    def unit_price_now(self, indices: Indices) -> Decimal:
        if self.unit_price is not None:
            k = self.k_mat if self.kind == MATERIAL else self.k_ot
            return money(self.unit_price * self.adj * k)
        if not self.qty:
            return ZERO
        return money(self.total(indices) / self.qty)

    def floor(self, indices: Indices, with_nr: bool = True) -> Decimal | None:
        """Self-cost of the position, or None if unknown (commercial price without cost).

        Always computed at adj = 1: cutting the estimate does not cut what the work costs.
        """
        if self.normative:
            clone = self.copy()
            clone.adj = ONE
            return clone.costs(indices).floor(with_nr)
        if self.unit_cost is None:
            return None
        return money(self.qty * self.unit_cost)

    def copy(self) -> "Position":
        return Position(**asdict(self))

    # ---------- coefficients ----------

    @property
    def has_coefficients(self) -> bool:
        return (self.k_ot, self.k_em, self.k_mat) != (ONE, ONE, ONE)

    def apply_coefficient(self, name: str, k_ot=ONE, k_em=ONE, k_mat=ONE, basis: str = "") -> None:
        """Multiply element coefficients and record the basis for the 'Обоснование' column."""
        k_ot, k_em, k_mat = dec(k_ot, ONE), dec(k_em, ONE), dec(k_mat, ONE)
        self.k_ot *= k_ot
        self.k_em *= k_em
        self.k_mat *= k_mat
        parts = [f"{label} {value:g}" for label, value in (("ОТ", k_ot), ("ЭМ", k_em), ("МАТ", k_mat)) if value != ONE]
        note = f"{name}: К " + ", ".join(parts) if parts else name
        if basis:
            note += f" ({basis})"
        self.k_basis = f"{self.k_basis}; {note}" if self.k_basis else note

    def clear_coefficients(self) -> None:
        self.k_ot = self.k_em = self.k_mat = ONE
        self.k_basis = ""

    # ---------- progress ----------

    @property
    def remaining(self) -> Decimal:
        return max(self.qty - self.done, ZERO)

    @property
    def to_act(self) -> Decimal:
        """Done but not yet closed by a KS-2 act."""
        return max(self.done - self.acted, ZERO)

    # ---------- serialisation ----------

    def to_dict(self) -> dict:
        data = asdict(self)
        return {k: (str(v) if isinstance(v, Decimal) else v) for k, v in data.items()}

    @classmethod
    def from_dict(cls, data: dict) -> "Position":
        allowed = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in allowed})

    @classmethod
    def from_rate(
        cls,
        rate: Rate,
        qty,
        norms: NrSp | None = None,
        *,
        unit: str | None = None,
        section: str = "",
        coef=ONE,
    ) -> "Position":
        factor, base_unit = parse_unit(rate.unit)
        return cls(
            name=rate.name,
            unit=norm_unit(unit) or base_unit,
            qty=dec(qty),
            kind=WORK,
            code=rate.code,
            section=section,
            ot=rate.ot,
            em=rate.em,
            zpm=rate.zpm,
            mat=rate.mat,
            tz=rate.tz,
            unit_factor=factor,
            nr_pct=norms.nr if norms else ZERO,
            sp_pct=norms.sp if norms else ZERO,
            coef=dec(coef, ONE),
            source=rate.source,
        )

    @classmethod
    def commercial(cls, name: str, qty, unit: str, price, *, kind: str = WORK, cost=None, section: str = "") -> "Position":
        return cls(
            name=name,
            unit=unit,
            qty=dec(qty),
            kind=kind,
            section=section,
            unit_price=dec(price),
            unit_cost=None if cost is None else dec(cost),
        )


@dataclass
class Totals:
    ot: Decimal = ZERO
    em: Decimal = ZERO
    zpm: Decimal = ZERO
    mat: Decimal = ZERO
    other: Decimal = ZERO
    nr: Decimal = ZERO
    sp: Decimal = ZERO
    tz: Decimal = ZERO
    by_kind: dict[str, Decimal] = field(default_factory=dict)
    vat_pct: Decimal = ZERO
    limited: list[tuple[str, Decimal, Decimal]] = field(default_factory=list)  # (название, %, сумма)

    @property
    def direct(self) -> Decimal:
        return money(self.ot + self.em + self.mat + self.other)

    @property
    def smr(self) -> Decimal:
        """Итого по позициям: прямые затраты + НР + СП."""
        return money(self.direct + self.nr + self.sp)

    @property
    def limited_total(self) -> Decimal:
        return money(sum((amount for _, _, amount in self.limited), ZERO))

    @property
    def subtotal(self) -> Decimal:
        """Итого без НДС: позиции + лимитированные затраты."""
        return money(self.smr + self.limited_total)

    @property
    def vat(self) -> Decimal:
        return money(self.subtotal * pct(self.vat_pct))

    @property
    def total(self) -> Decimal:
        return money(self.subtotal + self.vat)


@dataclass
class Estimate:
    number: str = ""
    title: str = "Локальная смета"
    customer: str = ""
    object_name: str = ""
    date: date = field(default_factory=date.today)
    company: Company = field(default_factory=Company)
    positions: list[Position] = field(default_factory=list)
    indices: Indices = field(default_factory=Indices)
    vat_pct: Decimal = Decimal(22)  # основная ставка НДС; живое значение — в data/tax/rates.csv
    history: list[str] = field(default_factory=list)
    basis: str = ""   # «ФЕР / ФСНБ-2022» или «договорные цены»
    # Накладные расходы считать частью себестоимости (ООО с офисом) или нет (бригада).
    floor_with_nr: bool = True
    contract: str = ""                                          # «№ 14 от 01.10.2026»
    limited: list[dict] = field(default_factory=list)          # {"name", "pct", "basis"}
    status: str = "draft"
    status_log: list[dict] = field(default_factory=list)       # {"status", "at", "note"}
    sent_at: str = ""
    payments: list[dict] = field(default_factory=list)         # {"date", "amount", "note"}
    schedule: list[dict] = field(default_factory=list)         # {"name", "pct", "due"}
    acts: list[dict] = field(default_factory=list)             # закрытые КС-2
    kp: dict = field(default_factory=dict)                     # условия коммерческого предложения
    crew: str = ""                                              # бригада / бригадир для наряда

    def __post_init__(self) -> None:
        self.vat_pct = dec(self.vat_pct)
        if isinstance(self.date, str):
            self.date = date.fromisoformat(self.date)

    # ---------- positions ----------

    def add(self, position: Position) -> Position:
        self.positions.append(position)
        return position

    def remove(self, index: int) -> Position | None:
        """index is 1-based, as shown to the user."""
        if 1 <= index <= len(self.positions):
            return self.positions.pop(index - 1)
        return None

    def of_kind(self, kind: str) -> list[Position]:
        return [p for p in self.positions if p.kind == kind]

    def sections(self) -> list[tuple[str, list[Position]]]:
        order: list[str] = []
        groups: dict[str, list[Position]] = {}
        for position in self.positions:
            key = position.section or ""
            if key not in groups:
                groups[key] = []
                order.append(key)
            groups[key].append(position)
        return [(key, groups[key]) for key in order]

    # ---------- money ----------

    def totals(self) -> Totals:
        out = Totals(vat_pct=self.vat_pct)
        for position in self.positions:
            costs = position.costs(self.indices)
            out.ot += costs.ot
            out.em += costs.em
            out.zpm += costs.zpm
            out.mat += costs.mat
            out.other += costs.other
            out.nr += costs.nr
            out.sp += costs.sp
            out.tz += costs.tz
            out.by_kind[position.kind] = out.by_kind.get(position.kind, ZERO) + costs.total
        smr = out.smr
        for item in self.limited:
            rate = dec(item.get("pct"))
            out.limited.append((str(item.get("name", "")), rate, money(smr * pct(rate))))
        return out

    def scale(self) -> Decimal:
        """Grand total per ruble of positions - spreads limited costs and VAT over parts."""
        totals = self.totals()
        return totals.total / totals.smr if totals.smr else ONE

    def copy(self) -> "Estimate":
        return Estimate.from_dict(self.to_dict())

    def total(self) -> Decimal:
        return self.totals().total

    def floor(self) -> Decimal:
        """Sum of known self-costs. Positions with unknown cost contribute 0."""
        return money(sum((p.floor(self.indices, self.floor_with_nr) or ZERO) for p in self.positions))

    # ---------- cuts and markups ----------

    def adjust(self, percent, scope: str = "all", *, label: str = "") -> Decimal:
        """'-20' cuts by 20 %, '+15' marks up. scope: all | work | material | equipment."""
        delta = dec(percent)
        factor = ONE + pct(delta)
        if factor <= ZERO:
            raise ValueError("нельзя срезать 100 % и больше")
        touched = 0
        for position in self.positions:
            if scope != "all" and position.kind != scope:
                continue
            position.adj *= factor
            touched += 1
        sign = "+" if delta >= 0 else "−"
        where = {"all": "вся смета", WORK: "только работы", MATERIAL: "только материалы",
                 EQUIPMENT: "только оборудование"}.get(scope, scope)
        self.history.append(label or f"{sign}{abs(delta)}% ({where}, позиций: {touched})")
        return self.total()

    def _grand(self, smr: Decimal) -> Decimal:
        """Grand total for a given sum of positions - the same rounding as totals()."""
        limited = sum((money(smr * pct(dec(item.get("pct")))) for item in self.limited), ZERO)
        subtotal = money(smr + limited)
        return money(subtotal + money(subtotal * pct(self.vat_pct)))

    def fit_to(self, target) -> Decimal:
        """Scale every position so that the grand total equals `target` (contract haggling).

        Limited costs and VAT are rounded separately, so with them some kopeck values are
        unreachable; then the closest reachable total is used (never more than 1 kopeck off).
        """
        goal = money(target)
        if goal <= ZERO:
            raise ValueError("целевая сумма должна быть больше нуля")
        for _ in range(4):
            current = self.total()
            if current == goal:
                break
            if current <= ZERO:
                raise ValueError("нельзя подогнать смету с нулевым итогом")
            factor = goal / current
            for position in self.positions:
                position.adj *= factor
        if self.total() != goal:
            self._fine_tune(goal)
        self.history.append(f"подгон под итог {goal}")
        return self.total()

    def _fine_tune(self, goal: Decimal) -> None:
        smr = self.totals().smr
        candidates = [smr + Decimal(step) / 100 for step in range(-300, 301)]
        best = min(candidates, key=lambda value: (abs(self._grand(value) - goal), abs(value - smr)))
        delta = best - smr
        priced = [p for p in self.positions if p.total(self.indices) > ZERO]
        if not delta or not priced:
            return
        # the commercial position rounds in one step; fall back to the biggest one
        biggest = max(priced, key=lambda p: (not p.normative, p.total(self.indices)))
        want = biggest.total(self.indices) + delta
        for _ in range(40):
            now = biggest.total(self.indices)
            if now == want or now <= ZERO:
                break
            biggest.adj *= want / now
            if biggest.total(self.indices) == now:          # застряли на округлении - микрошаг
                biggest.adj *= ONE + (Decimal("1e-9") if want > now else Decimal("-1e-9"))

    def reset_adjustments(self) -> Decimal:
        for position in self.positions:
            position.adj = ONE
        self.history.append("сброс всех корректировок")
        return self.total()

    def discount_pct(self) -> Decimal:
        """How far the current total sits from the untouched one, in percent."""
        base = money(sum(p.base_total(self.indices) for p in self.positions))
        if base <= ZERO:
            return ZERO
        current = money(sum(p.total(self.indices) for p in self.positions))
        return ((current - base) / base * Decimal(100)).quantize(Decimal("0.1"))

    # ---------- sanity checks ----------

    def warnings(self) -> list[str]:
        out: list[str] = []
        if not self.company.filled:
            out.append("Не заполнена шапка: название организации и ИНН (/company).")
        elif not inn_is_valid(self.company.inn):
            out.append(f"ИНН {self.company.inn} не проходит проверку контрольной суммы.")
        if not self.positions:
            out.append("В смете нет позиций.")
        for index, position in enumerate(self.positions, 1):
            if position.qty <= ZERO:
                out.append(f"Поз. {index} «{position.name}»: объём не указан.")
            if position.total(self.indices) <= ZERO:
                out.append(f"Поз. {index} «{position.name}»: цена не задана.")
                continue
            floor = position.floor(self.indices, self.floor_with_nr)
            if floor is not None and position.total(self.indices) < floor:
                out.append(
                    f"Поз. {index} «{position.name}»: ниже себестоимости — "
                    f"{rub(position.total(self.indices))} против {rub(floor)} ₽."
                )
        if self.positions and all(p.normative for p in self.positions) and self.indices.ot == ONE:
            out.append("Индекс пересчёта = 1,0: проверьте, что расценки уже в текущих ценах.")
        return out

    # ---------- serialisation ----------

    def to_dict(self) -> dict:
        return {
            "number": self.number,
            "title": self.title,
            "customer": self.customer,
            "object_name": self.object_name,
            "date": self.date.isoformat(),
            "company": asdict(self.company),
            "positions": [p.to_dict() for p in self.positions],
            "indices": {k: (str(v) if isinstance(v, Decimal) else v) for k, v in asdict(self.indices).items()},
            "vat_pct": str(self.vat_pct),
            "history": list(self.history),
            "basis": self.basis,
            "floor_with_nr": self.floor_with_nr,
            "contract": self.contract,
            "limited": [{k: (str(v) if isinstance(v, Decimal) else v) for k, v in item.items()} for item in self.limited],
            "status": self.status,
            "status_log": list(self.status_log),
            "sent_at": self.sent_at,
            "payments": [{k: (str(v) if isinstance(v, Decimal) else v) for k, v in item.items()} for item in self.payments],
            "schedule": [{k: (str(v) if isinstance(v, Decimal) else v) for k, v in item.items()} for item in self.schedule],
            "acts": list(self.acts),
            "kp": dict(self.kp),
            "crew": self.crew,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Estimate":
        indices_raw = data.get("indices") or {}
        indices = Indices(
            region=indices_raw.get("region", "демо"),
            period=indices_raw.get("period", ""),
            ot=dec(indices_raw.get("ot"), ONE),
            em=dec(indices_raw.get("em"), ONE),
            mat=dec(indices_raw.get("mat"), ONE),
            zpm=dec(indices_raw["zpm"], ONE) if indices_raw.get("zpm") else None,
        )
        return cls(
            number=data.get("number", ""),
            title=data.get("title", "Локальная смета"),
            customer=data.get("customer", ""),
            object_name=data.get("object_name", ""),
            date=date.fromisoformat(data["date"]) if data.get("date") else date.today(),
            company=Company(**(data.get("company") or {})),
            positions=[Position.from_dict(p) for p in data.get("positions", [])],
            indices=indices,
            vat_pct=dec(data.get("vat_pct"), Decimal(20)),
            history=list(data.get("history") or []),
            basis=data.get("basis", ""),
            floor_with_nr=bool(data.get("floor_with_nr", True)),
            contract=data.get("contract", ""),
            limited=list(data.get("limited") or []),
            status=data.get("status", "draft"),
            status_log=list(data.get("status_log") or []),
            sent_at=data.get("sent_at", ""),
            payments=list(data.get("payments") or []),
            schedule=list(data.get("schedule") or []),
            acts=list(data.get("acts") or []),
            kp=dict(data.get("kp") or {}),
            crew=data.get("crew", ""),
        )

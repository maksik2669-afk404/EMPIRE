"""Rate catalog: FER-style norms (OT/EM/ZPM/MAT per published unit), NR/SP rates, price indices.

The repository ships a DEMO catalog only. Official FSNB-2022 (FER) data is published by
Minstroy in FGIS CS; the user exports it and imports here with `Catalog.from_csv`.
Nothing in the demo file may be used as a legally binding rate.
"""
from __future__ import annotations

import csv
import difflib
import io
import re
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

from .money import ONE, ZERO, dec
from .units import parse_unit

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "rates"

# Columns we accept in an imported CSV. Keys are canonical, values are spellings seen in
# exports from Grand-Smeta / Smeta.ru / FGIS CS and in hand-made files.
_COLUMNS: dict[str, tuple[str, ...]] = {
    "code": ("code", "шифр", "код", "обоснование", "номер расценки"),
    "name": ("name", "наименование", "наименование работ", "работа", "описание"),
    "unit": ("unit", "ед.изм.", "ед. изм.", "единица измерения", "ед", "измеритель"),
    "ot": ("ot", "от", "оплата труда", "зп", "зпр", "оплата труда рабочих"),
    "em": ("em", "эм", "эксплуатация машин", "машины"),
    "zpm": ("zpm", "зпм", "в т.ч. зпм", "оплата труда машинистов"),
    "mat": ("mat", "мат", "материалы", "мр"),
    "tz": ("tz", "тз", "затраты труда", "чел.-ч", "трудозатраты"),
    "work_type": ("work_type", "вид работ", "тип работ", "нр/сп", "раздел"),
    "source": ("source", "источник", "сборник"),
    "keywords": ("keywords", "ключевые слова", "синонимы"),
}


def _canon_columns(fieldnames: list[str]) -> dict[str, str]:
    """Map a CSV header to canonical keys."""
    out: dict[str, str] = {}
    for raw in fieldnames or []:
        key = (raw or "").strip().lower().lstrip("﻿")
        for canon, spellings in _COLUMNS.items():
            if key in spellings:
                out[canon] = raw
                break
    return out


_STOP = {
    "и", "в", "во", "на", "с", "со", "по", "из", "за", "до", "для", "от", "под", "над",
    "при", "без", "о", "об", "к", "у", "не", "то", "же", "или", "а", "по-", "шт",
}
# Longest-first so 'ями' is stripped before 'и'.
_ENDINGS = (
    "ами", "ями", "ого", "его", "ому", "ему", "ыми", "ими", "ая", "яя", "ое", "ее",
    "ые", "ие", "ый", "ий", "ом", "ем", "ах", "ях", "ов", "ев", "ей", "ию", "ья",
    "ье", "ую", "юю", "иу", "а", "о", "е", "у", "ю", "я", "ы", "и", "ь", "й",
)
# A demolition rate and the matching installation rate share almost every keyword
# ('демонтаж штукатурки' vs 'штукатурка стен'), so the marker has to match explicitly.
_DEMOLITION = {"демонт", "разбор", "снос", "снять", "сбить", "срубит", "удален", "вывоз"}
# Heads that say nothing about *what* is being built ('Монтаж ...', 'Устройство ...').
# A specific head ('Шпатлёвка', 'Окраска', 'Кладка') must be matched by the query,
# otherwise 'покраска стен' happily lands on 'Шпатлёвка стен под окраску'.
_GENERIC_HEADS = {
    "монтаж", "устрой", "укладк", "установ", "разраб", "планир", "погруз", "сборка",
    "прокла", "обратн", "армиро", "работы", "ремонт",
}


def _stem(word: str) -> str:
    """Crude Russian stemmer: strip a case ending, then cut to 6 chars."""
    if len(word) > 4:
        for ending in _ENDINGS:
            if word.endswith(ending) and len(word) - len(ending) >= 3:
                word = word[: -len(ending)]
                break
    return word[:6]


def tokens(text: str) -> list[str]:
    text = (text or "").lower().replace("ё", "е")
    words = re.findall(r"[а-яa-z0-9]+", text)
    return [_stem(w) for w in words if w not in _STOP and len(w) > 1]


def _is_demolition(words: list[str]) -> bool:
    return any(w in _DEMOLITION for w in words)


def _matches(word: str, pool: list[str], threshold: float = 0.78) -> bool:
    return any(
        word == other or difflib.SequenceMatcher(None, word, other).ratio() >= threshold
        for other in pool
    )


@dataclass(frozen=True)
class Rate:
    """One catalog rate in base prices, per published unit (e.g. per 100 m2)."""

    code: str
    name: str
    unit: str = "шт"          # as published: '100 м2'
    ot: Decimal = ZERO        # labour, base prices
    em: Decimal = ZERO        # machines, incl. zpm
    zpm: Decimal = ZERO       # machine operators' labour (NR/SP base = ot + zpm)
    mat: Decimal = ZERO       # materials
    tz: Decimal = ZERO        # man-hours
    work_type: str = "прочие"
    source: str = ""
    keywords: str = ""

    @property
    def unit_factor(self) -> Decimal:
        return parse_unit(self.unit)[0]

    @property
    def unit_base(self) -> str:
        return parse_unit(self.unit)[1]

    @property
    def direct(self) -> Decimal:
        """Direct costs per published unit, base prices."""
        return self.ot + self.em + self.mat

    def search_text(self) -> str:
        return f"{self.name} {self.keywords}"


@dataclass
class NrSp:
    """Overheads (NR) and estimated profit (SP), percent of (OT + ZPM)."""

    work_type: str
    nr: Decimal
    sp: Decimal
    title: str = ""


@dataclass
class Indices:
    """Base -> current price conversion. Element-wise indices, FGIS CS, per region/quarter."""

    region: str = "демо"
    period: str = ""
    ot: Decimal = ONE
    em: Decimal = ONE
    mat: Decimal = ONE
    zpm: Decimal | None = None   # defaults to the EM index (ZPM is part of EM)

    def zpm_index(self) -> Decimal:
        return self.zpm if self.zpm is not None else self.em

    @classmethod
    def flat(cls, value) -> "Indices":
        """Single index to SMR when element-wise indices are unknown."""
        v = dec(value, ONE)
        return cls(region="единый индекс", ot=v, em=v, mat=v)


@dataclass
class Catalog:
    rates: list[Rate] = field(default_factory=list)
    nr_sp: dict[str, NrSp] = field(default_factory=dict)
    indices: dict[str, Indices] = field(default_factory=dict)

    # ---------- loading ----------

    @classmethod
    def from_csv(cls, text: str, *, source: str = "") -> "Catalog":
        """Import rates from a CSV/TSV export. Separator and header spelling are detected."""
        return cls(rates=parse_rates_csv(text, source=source))

    @classmethod
    def load(cls, directory: Path | str = DATA_DIR) -> "Catalog":
        base = Path(directory)
        cat = cls()
        for path in sorted(base.glob("*.csv")):
            if path.name == "nr_sp.csv":
                cat.nr_sp.update(parse_nr_sp_csv(path.read_text(encoding="utf-8")))
            elif path.name == "indices.csv":
                cat.indices.update(parse_indices_csv(path.read_text(encoding="utf-8")))
            else:
                cat.rates.extend(parse_rates_csv(path.read_text(encoding="utf-8"), source=path.stem))
        return cat

    def extend(self, other: "Catalog") -> "Catalog":
        known = {r.code for r in self.rates if r.code}
        self.rates.extend(r for r in other.rates if not r.code or r.code not in known)
        self.nr_sp.update(other.nr_sp)
        self.indices.update(other.indices)
        return self

    # ---------- lookups ----------

    def by_code(self, code: str) -> Rate | None:
        key = (code or "").strip().lower().replace(" ", "")
        for rate in self.rates:
            if rate.code.lower().replace(" ", "") == key:
                return rate
        return None

    def norms(self, work_type: str) -> NrSp:
        key = (work_type or "").strip().lower()
        if key in self.nr_sp:
            return self.nr_sp[key]
        return self.nr_sp.get("прочие", NrSp("прочие", ZERO, ZERO, "норматив не задан"))

    def index(self, name: str | None = None) -> Indices:
        if name and name in self.indices:
            return self.indices[name]
        if self.indices:
            return next(iter(self.indices.values()))
        return Indices()

    def search(self, query: str, limit: int = 5) -> list[tuple[Rate, float]]:
        """Fuzzy search by words. Returns (rate, score 0..1) sorted best first."""
        code_hit = self.by_code(query)
        if code_hit:
            return [(code_hit, 1.0)]
        wanted = tokens(query)
        if not wanted:
            return []
        wants_demolition = _is_demolition(wanted)
        scored: list[tuple[Rate, float]] = []
        for rate in self.rates:
            have = tokens(rate.search_text())
            if not have:
                continue
            hits = 0.0
            for word in wanted:
                best = 0.0
                for candidate in have:
                    if word == candidate:
                        best = 1.0
                        break
                    ratio = difflib.SequenceMatcher(None, word, candidate).ratio()
                    best = max(best, ratio if ratio >= 0.78 else 0.0)
                hits += best
            coverage = hits / len(wanted)
            name_words = tokens(rate.name)
            precision = hits / len(name_words) if name_words else 0.0
            score = coverage * 0.75 + min(precision, 1.0) * 0.25
            if all(word in have for word in wanted):
                score += 0.1
            head = name_words[0] if name_words else ""
            if head and head not in _GENERIC_HEADS and not _matches(head, wanted):
                score *= 0.6
            if _is_demolition(name_words) != wants_demolition:
                score *= 0.4
            score = min(round(score, 4), 1.0)
            if score >= 0.3:
                scored.append((rate, score))
        scored.sort(key=lambda pair: (-pair[1], pair[0].code))
        return scored[:limit]

    def best(self, query: str, threshold: float = 0.55) -> tuple[Rate, float] | None:
        found = self.search(query, limit=1)
        if found and found[0][1] >= threshold:
            return found[0]
        return None


# ---------- CSV parsers ----------


def _reader(text: str):
    """DictReader over a CSV whose leading '#' lines are comments."""
    lines = text.lstrip("﻿").splitlines()
    while lines and (not lines[0].strip() or lines[0].lstrip().startswith("#")):
        lines.pop(0)
    body = "\n".join(lines)
    sample = body[:4096]
    header = sample.splitlines()[0] if sample.splitlines() else ""
    try:
        delimiter = csv.Sniffer().sniff(sample, delimiters=";,\t|").delimiter
    except csv.Error:
        delimiter = next((c for c in (";", "\t", ",", "|") if c in header), ";")
    return csv.DictReader(io.StringIO(body), delimiter=delimiter)


def parse_rates_csv(text: str, *, source: str = "") -> list[Rate]:
    reader = _reader(text)
    columns = _canon_columns(reader.fieldnames or [])
    if "name" not in columns:
        raise ValueError("в файле нет столбца с наименованием работ")
    out: list[Rate] = []
    for row in reader:
        def cell(key: str, default: str = "") -> str:
            column = columns.get(key)
            return (row.get(column) or default).strip() if column else default

        name = cell("name")
        if not name or name.startswith("#"):
            continue
        out.append(
            Rate(
                code=cell("code"),
                name=name,
                unit=cell("unit", "шт") or "шт",
                ot=dec(cell("ot")),
                em=dec(cell("em")),
                zpm=dec(cell("zpm")),
                mat=dec(cell("mat")),
                tz=dec(cell("tz")),
                work_type=(cell("work_type") or "прочие").lower(),
                source=cell("source") or source,
                keywords=cell("keywords"),
            )
        )
    return out


def parse_nr_sp_csv(text: str) -> dict[str, NrSp]:
    out: dict[str, NrSp] = {}
    for row in _reader(text):
        values = {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
        key = (values.get("work_type") or values.get("вид работ") or "").lower()
        if not key:
            continue
        out[key] = NrSp(
            work_type=key,
            nr=dec(values.get("nr") or values.get("нр")),
            sp=dec(values.get("sp") or values.get("сп")),
            title=values.get("title") or values.get("название") or key,
        )
    return out


def parse_indices_csv(text: str) -> dict[str, Indices]:
    out: dict[str, Indices] = {}
    for row in _reader(text):
        values = {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
        name = values.get("name") or values.get("название") or values.get("region") or ""
        if not name:
            continue
        out[name] = Indices(
            region=values.get("region") or name,
            period=values.get("period") or values.get("период") or "",
            ot=dec(values.get("ot") or values.get("иот"), ONE),
            em=dec(values.get("em") or values.get("иэм"), ONE),
            mat=dec(values.get("mat") or values.get("имат"), ONE),
            zpm=dec(values.get("zpm"), None) if (values.get("zpm") or "") else None,
        )
    return out

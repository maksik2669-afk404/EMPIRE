"""Column meaning from a header cell. Shared by the CSV catalog and the file importer.

One table of rules, so a spelling learned from a real FSNB export works everywhere.
"""
from __future__ import annotations

import csv
import io
import re
from pathlib import Path

# Sub-header cells that say nothing on their own: the meaning sits in the parent cell.
GENERIC_HEADERS = {"всего", "итого", "руб", "рублей", "сумма", "значение", "кол-во", "коэффициент"}

# Short Latin field names used by DBF-based rate bases.
LATIN_ALIASES = {
    "shifr": "code", "kod": "code", "code": "code", "nrsp": "work_type",
    "naim": "name", "naimen": "name", "name": "name", "opis": "name", "descr": "name",
    "edizm": "unit", "ed": "unit", "ei": "unit", "unit": "unit",
    "ot": "ot", "zp": "ot", "zpr": "ot", "fot": "ot", "ozp": "ot",
    "em": "em", "emm": "em", "zpm": "zpm",
    "mat": "mat", "mr": "mat", "smat": "mat",
    "tz": "tz", "ztr": "tz", "tzr": "tz", "tzm": "tzm", "ztm": "tzm",
    "pz": "pz", "vsego": "pz",
}


def normalize_header(text) -> str:
    """'ОплатаТрудаРабочих' -> 'оплата труда рабочих'; 'Ед_изм.' -> 'ед изм'."""
    raw = str(text or "")
    raw = re.sub(r"(?<=[а-яa-zA-Z])(?=[А-ЯA-Z])", " ", raw)     # CamelCase -> words
    raw = raw.replace("_", " ").replace("ё", "е").replace("Ё", "Е").lower()
    raw = re.sub(r"[\n\r\t]+", " ", raw)
    raw = re.sub(r"[«»\"'()\[\]{}.,;:/\\]+", " ", raw)
    return re.sub(r"\s{2,}", " ", raw).strip()


def classify(header) -> str | None:
    """Map one header cell to a canonical field. Order matters - see the comments."""
    h = normalize_header(header)
    if not h or h.isdigit():
        return None
    compact = h.replace(" ", "").replace("-", "")
    if compact in LATIN_ALIASES:
        return LATIN_ALIASES[compact]
    # 1. machine operators' man-hours before anything that mentions машинист
    if "машинист" in h and ("затраты труда" in h or "чел" in h or h.startswith(("зтм", "тзм"))):
        return "tzm"
    # 2. a column that says "эксплуатация" is the machines column even when it adds
    #    "в том числе оплата труда машинистов"
    if "эксплуатаци" in h or h in {"эм", "эмм", "em", "машины", "эксплуатация машин"}:
        return "em"
    # 3. only then a dedicated ЗПМ column
    if "машинист" in h or h in {"зпм", "зп машинистов", "zpm"}:
        return "zpm"
    if "затраты труда" in h or "чел -ч" in h or "чел ч" in h or h in {"тз", "зтр", "tz", "трудозатраты"}:
        return "tz"
    if "оплата труда" in h or "заработная плата" in h or h in {"от", "зп", "зпр", "ot", "фот"}:
        return "ot"
    if "материал" in h or h in {"мат", "мр", "mat"}:
        return "mat"
    if "прямые затраты" in h or h in {"пз", "pz", "всего", "сметная стоимость", "стоимость"}:
        return "pz"
    if "шифр" in h or "обоснование" in h or "расценк" in h and "наименование" not in h or h in {"код", "code", "номер"}:
        return "code"
    if "наименование" in h or "описание" in h or h in {"name", "работа", "работы", "ресурс"}:
        return "name"
    if "измеритель" in h or "единица" in h or h.startswith("ед") or h in {"unit", "ед изм"}:
        return "unit"
    if "вид работ" in h or h in {"work_type", "тип работ"}:
        return "work_type"
    if "ключев" in h or h == "keywords":
        return "keywords"
    if "источник" in h or "сборник" in h or h == "source":
        return "source"
    # index tables
    if "регион" in h or "субъект" in h or h == "region":
        return "region"
    if "период" in h or "квартал" in h or "кв " in h or h == "period":
        return "period"
    if "вид строительства" in h or "объект" in h or h == "group":
        return "group"
    if h in {"смр", "индекс смр", "ксмр", "smr"} or ("индекс" in h and "смр" in h):
        return "smr"
    if h.startswith("иот") or h in {"иот"}:
        return "ot"
    if h.startswith("иэм") or h in {"иэм"}:
        return "em"
    if h.startswith("имат") or h in {"имат", "им"}:
        return "mat"
    if "индекс" in h:
        return "smr"
    return None


def match_columns(headers: list) -> dict[str, int]:
    """Classify a header row. The first column of each meaning wins."""
    out: dict[str, int] = {}
    for index, cell in enumerate(headers):
        field_name = classify(cell)
        if field_name and field_name not in out:
            out[field_name] = index
    return out


_SBORNIK_WORK_TYPE: dict[str, str] | None = None


def sbornik_work_type(code: str, table: dict[str, str] | None = None) -> str:
    """Guess the NR/SP work type from a FER/GESN code prefix ('ФЕР15-01-...' -> отделочные)."""
    global _SBORNIK_WORK_TYPE
    if table is None:
        if _SBORNIK_WORK_TYPE is None:
            _SBORNIK_WORK_TYPE = _load_sbornik_map()
        table = _SBORNIK_WORK_TYPE
    digits = re.sub(r"^[^\d]*", "", (code or "").strip())
    number = re.match(r"(\d{1,2})", digits)
    if not number:
        return ""
    return table.get(number.group(1).lstrip("0") or "0", "")


def _load_sbornik_map() -> dict[str, str]:
    """data/rates/sbornik_work_type.csv: номер сборника ФЕР/ГЭСН -> вид работ."""
    path = Path(__file__).resolve().parent.parent / "data" / "rates" / "sbornik_work_type.csv"
    out: dict[str, str] = {}
    if not path.exists():
        return out
    lines = [line for line in path.read_text(encoding="utf-8").splitlines()
             if line.strip() and not line.lstrip().startswith("#")]
    for row in csv.reader(io.StringIO("\n".join(lines[1:])), delimiter=";"):
        if len(row) >= 2 and row[0].strip():
            out[row[0].strip().lstrip("0") or "0"] = row[1].strip().lower()
    return out

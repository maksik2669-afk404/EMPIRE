"""Small CSV reference tables that live in data/ and are edited without touching code."""
from __future__ import annotations

import csv
import io
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"


def read_table(path: Path | str) -> list[dict[str, str]]:
    """Rows of a ';'-separated CSV with '#' comment lines; missing file -> []."""
    source = Path(path)
    if not source.exists():
        return []
    lines = [line for line in source.read_text(encoding="utf-8").lstrip("﻿").splitlines()
             if line.strip() and not line.lstrip().startswith("#")]
    if not lines:
        return []
    reader = csv.DictReader(io.StringIO("\n".join(lines)), delimiter=";")
    return [{(k or "").strip(): (v or "").strip() for k, v in row.items()} for row in reader]


def coefficients() -> list[dict[str, str]]:
    return read_table(DATA / "rates" / "coefficients.csv")


def limited_presets() -> list[dict[str, str]]:
    return read_table(DATA / "rates" / "limited.csv")


def templates() -> list[dict[str, str]]:
    return read_table(DATA / "templates" / "templates.csv")


def material_norms() -> list[dict[str, str]]:
    return read_table(DATA / "materials" / "norms.csv")


def companions() -> list[dict[str, str]]:
    return read_table(DATA / "audit" / "companions.csv")


def plans() -> list[dict[str, str]]:
    return read_table(DATA / "billing" / "plans.csv")

"""Product facts: parsing seller input (text or CSV exported from Excel)."""
from __future__ import annotations

import csv
import io

SHOP_WIDE = "*"  # facts about the shop in general: delivery, warranty, returns
MAX_FACTS = 4000
class _Semicolon(csv.excel):
    delimiter = ";"


_HEADER_WORDS = {"sku", "артикул", "nmid", "offerid", "offer_id", "article", "货号"}


def parse_text(raw: str) -> tuple[str, str]:
    """'SKU\\nfacts...' -> (sku, facts). 'SKU -' -> (sku, '') meaning delete. Raises ValueError."""
    raw = raw.strip()
    first, _, rest = raw.partition("\n")
    first = first.strip()
    if " " in first and not rest:  # "SKU -" or "SKU facts on one line"
        first, rest = first.split(" ", 1)
    sku, facts = first.strip(), rest.strip()
    if not sku or len(sku) > 64 or (not facts and raw.split()[-1] != "-"):
        raise ValueError("format")
    return sku, ("" if facts == "-" else facts[:MAX_FACTS])


def parse_csv(data: bytes) -> tuple[list[tuple[str, str, str]], int]:
    """CSV with columns sku;name;facts (or sku;facts). Returns (rows, skipped_rows)."""
    for enc in ("utf-8-sig", "cp1251"):  # Excel in Russia saves CSV in cp1251
        try:
            text = data.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError("encoding")
    try:
        dialect = csv.Sniffer().sniff(text[:4096], delimiters=";,\t")
    except csv.Error:
        dialect = _Semicolon
    rows, skipped = [], 0
    for i, row in enumerate(csv.reader(io.StringIO(text), dialect)):
        cells = [c.strip() for c in row]
        if i == 0 and cells and cells[0].lower().replace(" ", "") in _HEADER_WORDS:
            continue
        if len(cells) < 2 or not cells[0] or not any(cells[1:]):
            skipped += bool(any(cells))
            continue
        if len(cells) == 2:
            sku, name, facts = cells[0], "", cells[1]
        else:
            sku, name, facts = cells[0], cells[1], "; ".join(c for c in cells[2:] if c)
        if not facts:
            facts, name = name, ""
        rows.append((sku[:64], name[:200], facts[:MAX_FACTS]))
    return rows, skipped

"""SQLite storage: company header, estimates, imported rate catalogs and price lists."""
from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from datetime import date, datetime, timezone
from pathlib import Path

from .catalog import Catalog, parse_rates_csv
from .materials import OfferBook
from .model import Company, Estimate
from .money import dec

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    tg_id INTEGER PRIMARY KEY,
    company TEXT NOT NULL DEFAULT '{}',
    vat_pct TEXT NOT NULL DEFAULT '20',
    index_name TEXT NOT NULL DEFAULT '',
    floor_with_nr INTEGER NOT NULL DEFAULT 1,
    counter INTEGER NOT NULL DEFAULT 0,
    current_id INTEGER,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS estimates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id INTEGER NOT NULL,
    number TEXT NOT NULL DEFAULT '',
    title TEXT NOT NULL DEFAULT '',
    data TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS imports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id INTEGER NOT NULL,
    kind TEXT NOT NULL,              -- rates | offers
    name TEXT NOT NULL DEFAULT '',
    body TEXT NOT NULL,
    rows INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_estimates_user ON estimates(tg_id, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_imports_user ON imports(tg_id, kind);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Store:
    def __init__(self, path: str | Path = "data/smeta.db") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    # ---------- users ----------

    def user(self, tg_id: int) -> sqlite3.Row:
        row = self.conn.execute("SELECT * FROM users WHERE tg_id = ?", (tg_id,)).fetchone()
        if row is None:
            self.conn.execute(
                "INSERT INTO users (tg_id, created_at) VALUES (?, ?)", (tg_id, _now())
            )
            self.conn.commit()
            row = self.conn.execute("SELECT * FROM users WHERE tg_id = ?", (tg_id,)).fetchone()
        return row

    def company(self, tg_id: int) -> Company:
        raw = json.loads(self.user(tg_id)["company"] or "{}")
        allowed = set(Company.__dataclass_fields__)
        return Company(**{k: v for k, v in raw.items() if k in allowed})

    def save_company(self, tg_id: int, company: Company) -> None:
        self.user(tg_id)
        self.conn.execute(
            "UPDATE users SET company = ? WHERE tg_id = ?",
            (json.dumps(asdict(company), ensure_ascii=False), tg_id),
        )
        self.conn.commit()

    def settings(self, tg_id: int) -> dict:
        row = self.user(tg_id)
        return {
            "vat_pct": dec(row["vat_pct"]),
            "index_name": row["index_name"],
            "floor_with_nr": bool(row["floor_with_nr"]),
            "current_id": row["current_id"],
        }

    def update_settings(self, tg_id: int, **fields) -> None:
        self.user(tg_id)
        allowed = {"vat_pct", "index_name", "floor_with_nr", "current_id"}
        pairs = {k: v for k, v in fields.items() if k in allowed}
        if not pairs:
            return
        sets = ", ".join(f"{k} = ?" for k in pairs)
        values = [str(v) if k == "vat_pct" else (int(v) if k == "floor_with_nr" else v) for k, v in pairs.items()]
        self.conn.execute(f"UPDATE users SET {sets} WHERE tg_id = ?", (*values, tg_id))
        self.conn.commit()

    def next_number(self, tg_id: int) -> str:
        row = self.user(tg_id)
        counter = int(row["counter"]) + 1
        self.conn.execute("UPDATE users SET counter = ? WHERE tg_id = ?", (counter, tg_id))
        self.conn.commit()
        return f"СМ-{date.today().year}-{counter:04d}"

    # ---------- estimates ----------

    def save_estimate(self, tg_id: int, estimate: Estimate, estimate_id: int | None = None) -> int:
        payload = json.dumps(estimate.to_dict(), ensure_ascii=False)
        if estimate_id:
            self.conn.execute(
                "UPDATE estimates SET number = ?, title = ?, data = ?, updated_at = ? WHERE id = ? AND tg_id = ?",
                (estimate.number, estimate.title, payload, _now(), estimate_id, tg_id),
            )
            self.conn.commit()
            return estimate_id
        cursor = self.conn.execute(
            "INSERT INTO estimates (tg_id, number, title, data, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (tg_id, estimate.number, estimate.title, payload, _now(), _now()),
        )
        self.conn.commit()
        return int(cursor.lastrowid)

    def load_estimate(self, tg_id: int, estimate_id: int) -> Estimate | None:
        row = self.conn.execute(
            "SELECT data FROM estimates WHERE id = ? AND tg_id = ?", (estimate_id, tg_id)
        ).fetchone()
        return Estimate.from_dict(json.loads(row["data"])) if row else None

    def list_estimates(self, tg_id: int, limit: int = 10) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT id, number, title, updated_at FROM estimates WHERE tg_id = ? ORDER BY updated_at DESC LIMIT ?",
            (tg_id, limit),
        ).fetchall()

    def delete_estimate(self, tg_id: int, estimate_id: int) -> bool:
        cursor = self.conn.execute(
            "DELETE FROM estimates WHERE id = ? AND tg_id = ?", (estimate_id, tg_id)
        )
        self.conn.commit()
        return cursor.rowcount > 0

    # ---------- imports ----------

    def add_import(self, tg_id: int, kind: str, name: str, body: str, rows: int) -> int:
        cursor = self.conn.execute(
            "INSERT INTO imports (tg_id, kind, name, body, rows, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (tg_id, kind, name, body, rows, _now()),
        )
        self.conn.commit()
        return int(cursor.lastrowid)

    def imports(self, tg_id: int, kind: str) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT id, name, rows, created_at FROM imports WHERE tg_id = ? AND kind = ? ORDER BY id DESC",
            (tg_id, kind),
        ).fetchall()

    def drop_imports(self, tg_id: int, kind: str) -> int:
        cursor = self.conn.execute("DELETE FROM imports WHERE tg_id = ? AND kind = ?", (tg_id, kind))
        self.conn.commit()
        return cursor.rowcount

    def catalog(self, tg_id: int, base: Catalog) -> Catalog:
        """Base (demo or official) catalog plus everything this user imported. User rates win."""
        merged = Catalog(rates=[], nr_sp=dict(base.nr_sp), indices=dict(base.indices))
        for row in self.conn.execute(
            "SELECT body FROM imports WHERE tg_id = ? AND kind = 'rates' ORDER BY id", (tg_id,)
        ):
            try:
                merged.rates.extend(parse_rates_csv(row["body"]))
            except ValueError:
                continue
        merged.extend(Catalog(rates=list(base.rates)))
        return merged

    def offers(self, tg_id: int, base: OfferBook | None = None) -> OfferBook:
        book = OfferBook(list(base.offers) if base else [])
        for row in self.conn.execute(
            "SELECT body FROM imports WHERE tg_id = ? AND kind = 'offers' ORDER BY id", (tg_id,)
        ):
            book.offers = OfferBook.from_csv(row["body"]).offers + book.offers
        return book

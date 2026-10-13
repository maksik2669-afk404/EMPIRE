"""SQLite storage: company header, estimates and their versions, imports, subscription."""
from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import asdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from .catalog import Catalog, parse_indices_csv, parse_rates_csv
from .materials import OfferBook
from .model import Company, Estimate
from .money import dec

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    tg_id INTEGER PRIMARY KEY,
    company TEXT NOT NULL DEFAULT '{}',
    vat_pct TEXT NOT NULL DEFAULT '22',
    index_name TEXT NOT NULL DEFAULT '',
    floor_with_nr INTEGER NOT NULL DEFAULT 1,
    use_demo_rates INTEGER NOT NULL DEFAULT 1,
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
    kind TEXT NOT NULL,              -- rates | offers | indices
    name TEXT NOT NULL DEFAULT '',
    body TEXT NOT NULL,
    rows INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    estimate_id INTEGER NOT NULL,
    tg_id INTEGER NOT NULL,
    n INTEGER NOT NULL,
    label TEXT NOT NULL DEFAULT '',
    data TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS billing (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id INTEGER NOT NULL,
    plan TEXT NOT NULL,
    amount TEXT NOT NULL,
    currency TEXT NOT NULL,
    charge_id TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS promo_used (
    tg_id INTEGER NOT NULL,
    code TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (tg_id, code)
);
CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS ref_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    referrer_id INTEGER NOT NULL,
    days INTEGER NOT NULL,
    created_at TEXT NOT NULL
);
"""

# Columns added after the first release: (table, column, ddl). Old databases get them on start.
MIGRATIONS = (
    ("users", "use_demo_rates", "INTEGER NOT NULL DEFAULT 1"),
    ("users", "paid_until", "TEXT NOT NULL DEFAULT ''"),
    ("users", "estimates_created", "INTEGER NOT NULL DEFAULT 0"),
    ("users", "sub_reminded", "TEXT NOT NULL DEFAULT ''"),
    ("users", "tax_ip", "INTEGER NOT NULL DEFAULT 0"),
    ("users", "tax_staff", "INTEGER NOT NULL DEFAULT 1"),
    ("users", "tax_annual", "TEXT NOT NULL DEFAULT ''"),
    ("users", "username", "TEXT NOT NULL DEFAULT ''"),
    ("estimates", "status", "TEXT NOT NULL DEFAULT 'draft'"),
    ("estimates", "total", "TEXT NOT NULL DEFAULT '0'"),
    ("estimates", "sent_at", "TEXT NOT NULL DEFAULT ''"),
    ("estimates", "remind_at", "TEXT NOT NULL DEFAULT ''"),
    ("users", "referred_by", "TEXT NOT NULL DEFAULT ''"),
    ("users", "ref_rewarded", "INTEGER NOT NULL DEFAULT 0"),
    ("users", "ref_count", "INTEGER NOT NULL DEFAULT 0"),
)
INDEXES = """
CREATE INDEX IF NOT EXISTS idx_estimates_user ON estimates(tg_id, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_estimates_remind ON estimates(status, remind_at);
CREATE INDEX IF NOT EXISTS idx_imports_user ON imports(tg_id, kind);
CREATE INDEX IF NOT EXISTS idx_versions_estimate ON versions(estimate_id, n);
"""
SETTINGS = {"vat_pct", "index_name", "floor_with_nr", "use_demo_rates", "current_id", "tax_ip",
            "tax_staff", "tax_annual", "paid_until", "sub_reminded", "username"}
FLAGS = {"floor_with_nr", "use_demo_rates", "tax_ip", "tax_staff"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Store:
    def __init__(self, path: str | Path = "data/smeta.db") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self._migrate()
        self.conn.executescript(INDEXES)
        self._data_migrations()
        self.conn.commit()

    def _migrate(self) -> None:
        for table, column, ddl in MIGRATIONS:
            existing = {row["name"] for row in self.conn.execute(f"PRAGMA table_info({table})")}
            if column not in existing:
                self.conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")

    def _data_migrations(self) -> None:
        """Разовые правки данных — каждая под флагом в `meta`, чтобы отработать ровно один раз."""
        done = {row["key"] for row in self.conn.execute("SELECT key FROM meta")}
        if "vat_2026" not in done:
            from . import tax
            # НДС 20 % не действует с 01.01.2026 (ФЗ-425): всех, кто остался на старом
            # значении по умолчанию, поднимаем до текущей ставки из data/tax/rates.csv.
            # Нулевой НДС (УСН) и осознанно выставленные ставки не трогаем.
            self.conn.execute("UPDATE users SET vat_pct = ? WHERE vat_pct = '20'", (str(tax.current_vat()),))
            self.conn.execute("INSERT INTO meta (key, value) VALUES ('vat_2026', ?)", (_now(),))

    def close(self) -> None:
        self.conn.close()

    # ---------- users ----------

    def user(self, tg_id: int) -> sqlite3.Row:
        row = self.conn.execute("SELECT * FROM users WHERE tg_id = ?", (tg_id,)).fetchone()
        if row is None:
            from . import tax
            self.conn.execute("INSERT INTO users (tg_id, vat_pct, created_at) VALUES (?, ?, ?)",
                              (tg_id, str(tax.current_vat()), _now()))
            self.conn.commit()
            row = self.conn.execute("SELECT * FROM users WHERE tg_id = ?", (tg_id,)).fetchone()
        return row

    def company(self, tg_id: int) -> Company:
        raw = json.loads(self.user(tg_id)["company"] or "{}")
        allowed = set(Company.__dataclass_fields__)
        return Company(**{k: v for k, v in raw.items() if k in allowed})

    def save_company(self, tg_id: int, company: Company) -> None:
        self.user(tg_id)
        self.conn.execute("UPDATE users SET company = ? WHERE tg_id = ?",
                          (json.dumps(asdict(company), ensure_ascii=False), tg_id))
        self.conn.commit()

    def settings(self, tg_id: int) -> dict:
        row = self.user(tg_id)
        return {
            "vat_pct": dec(row["vat_pct"]),
            "index_name": row["index_name"],
            "floor_with_nr": bool(row["floor_with_nr"]),
            "use_demo_rates": bool(row["use_demo_rates"]),
            "current_id": row["current_id"],
            "tax_ip": bool(row["tax_ip"]),
            "tax_staff": bool(row["tax_staff"]),
            "tax_annual": dec(row["tax_annual"], None) if row["tax_annual"] else None,
            "paid_until": row["paid_until"],
            "estimates_created": int(row["estimates_created"]),
            "sub_reminded": row["sub_reminded"],
        }

    def update_settings(self, tg_id: int, **fields) -> None:
        self.user(tg_id)
        pairs = {k: v for k, v in fields.items() if k in SETTINGS}
        if not pairs:
            return
        sets = ", ".join(f"{k} = ?" for k in pairs)
        values = []
        for key, value in pairs.items():
            if key in FLAGS:
                values.append(int(bool(value)))
            elif key in {"vat_pct", "tax_annual"}:
                values.append("" if value is None else str(value))
            else:
                values.append(value)
        self.conn.execute(f"UPDATE users SET {sets} WHERE tg_id = ?", (*values, tg_id))
        self.conn.commit()

    def next_number(self, tg_id: int) -> str:
        counter = int(self.user(tg_id)["counter"]) + 1
        self.conn.execute("UPDATE users SET counter = ? WHERE tg_id = ?", (counter, tg_id))
        self.conn.commit()
        return f"СМ-{date.today().year}-{counter:04d}"

    def all_users(self) -> list[int]:
        return [row["tg_id"] for row in self.conn.execute("SELECT tg_id FROM users")]

    # ---------- referrals ----------

    def register_referral(self, new_id: int, referrer_id: int, welcome_days: int) -> dict | None:
        """Новый пользователь пришёл по ссылке: фиксируем пригласившего и даём новичку бонусные дни.

        Срабатывает только для НОВОГО пользователя (строки ещё нет), не для себя и только если
        пригласивший реально существует. Пригласившего наградим позже — на его первой смете.
        """
        if not referrer_id or referrer_id == new_id:
            return None
        if self.conn.execute("SELECT 1 FROM users WHERE tg_id = ?", (new_id,)).fetchone():
            return None                                   # не новый — ссылку игнорируем
        if not self.conn.execute("SELECT 1 FROM users WHERE tg_id = ?", (referrer_id,)).fetchone():
            return None                                   # пригласившего нет в базе
        from . import tax
        self.conn.execute(
            "INSERT INTO users (tg_id, vat_pct, referred_by, created_at) VALUES (?, ?, ?, ?)",
            (new_id, str(tax.current_vat()), str(referrer_id), _now()))
        self.conn.commit()
        until = self.extend_subscription(new_id, welcome_days) if welcome_days > 0 else None
        return {"referrer_id": referrer_id, "welcome_days": welcome_days, "until": until}

    def _reward_referrer(self, new_id: int) -> None:
        """На первой смете приглашённого начисляем пригласившему дни Pro (до потолка) и ставим в очередь уведомление."""
        row = self.conn.execute("SELECT referred_by, ref_rewarded FROM users WHERE tg_id = ?", (new_id,)).fetchone()
        if not row or not row["referred_by"] or row["ref_rewarded"]:
            return
        self.conn.execute("UPDATE users SET ref_rewarded = 1 WHERE tg_id = ?", (new_id,))   # один раз, что бы ни было дальше
        referrer = str(row["referred_by"])
        referrer_id = int(referrer) if referrer.lstrip("-").isdigit() else 0
        ref_row = (self.conn.execute("SELECT ref_count FROM users WHERE tg_id = ?", (referrer_id,)).fetchone()
                   if referrer_id else None)
        if ref_row is None:
            self.conn.commit()
            return
        try:
            days = int(os.getenv("SMETA_REF_DAYS", "14"))
            cap = int(os.getenv("SMETA_REF_CAP_DAYS", "180"))
        except ValueError:
            days, cap = 14, 180
        earned = int(ref_row["ref_count"]) * days
        self.conn.execute("UPDATE users SET ref_count = ref_count + 1 WHERE tg_id = ?", (referrer_id,))
        if days > 0 and earned < cap:
            self.extend_subscription(referrer_id, days)
            self.conn.execute("INSERT INTO ref_queue (referrer_id, days, created_at) VALUES (?, ?, ?)",
                              (referrer_id, days, _now()))
        self.conn.commit()

    def ref_stats(self, tg_id: int) -> dict:
        row = self.user(tg_id)
        return {"ref_count": int(row["ref_count"]), "referred_by": row["referred_by"]}

    def pop_ref_rewards(self, limit: int = 50) -> list[sqlite3.Row]:
        """Забрать и удалить накопившиеся уведомления о реферальных наградах (для цикла напоминаний)."""
        rows = self.conn.execute("SELECT id, referrer_id, days FROM ref_queue ORDER BY id LIMIT ?", (limit,)).fetchall()
        if rows:
            self.conn.executemany("DELETE FROM ref_queue WHERE id = ?", [(row["id"],) for row in rows])
            self.conn.commit()
        return rows

    # ---------- estimates ----------

    def save_estimate(self, tg_id: int, estimate: Estimate, estimate_id: int | None = None) -> int:
        payload = json.dumps(estimate.to_dict(), ensure_ascii=False)
        total = str(estimate.total())
        if estimate_id:
            self.conn.execute(
                "UPDATE estimates SET number = ?, title = ?, data = ?, updated_at = ?, status = ?, total = ?, "
                "sent_at = ? WHERE id = ? AND tg_id = ?",
                (estimate.number, estimate.title, payload, _now(), estimate.status, total, estimate.sent_at,
                 estimate_id, tg_id),
            )
            self.conn.commit()
            return estimate_id
        cursor = self.conn.execute(
            "INSERT INTO estimates (tg_id, number, title, data, created_at, updated_at, status, total, sent_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (tg_id, estimate.number, estimate.title, payload, _now(), _now(), estimate.status, total, estimate.sent_at),
        )
        self.user(tg_id)
        self.conn.execute("UPDATE users SET estimates_created = estimates_created + 1 WHERE tg_id = ?", (tg_id,))
        self.conn.commit()
        self._reward_referrer(tg_id)
        return int(cursor.lastrowid)

    def load_estimate(self, tg_id: int, estimate_id: int) -> Estimate | None:
        row = self.conn.execute("SELECT data FROM estimates WHERE id = ? AND tg_id = ?",
                                (estimate_id, tg_id)).fetchone()
        return Estimate.from_dict(json.loads(row["data"])) if row else None

    def list_estimates(self, tg_id: int, limit: int = 10, offset: int = 0) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT id, number, title, updated_at, status, total FROM estimates WHERE tg_id = ? "
            "ORDER BY updated_at DESC, id DESC LIMIT ? OFFSET ?",
            (tg_id, limit, offset),
        ).fetchall()

    def count_estimates(self, tg_id: int) -> int:
        return int(self.conn.execute("SELECT COUNT(*) FROM estimates WHERE tg_id = ?", (tg_id,)).fetchone()[0])

    def all_estimates(self, tg_id: int) -> list[tuple[int, Estimate]]:
        return [(row["id"], Estimate.from_dict(json.loads(row["data"])))
                for row in self.conn.execute("SELECT id, data FROM estimates WHERE tg_id = ?", (tg_id,))]

    def delete_estimate(self, tg_id: int, estimate_id: int) -> bool:
        cursor = self.conn.execute("DELETE FROM estimates WHERE id = ? AND tg_id = ?", (estimate_id, tg_id))
        self.conn.execute("DELETE FROM versions WHERE estimate_id = ? AND tg_id = ?", (estimate_id, tg_id))
        if self.user(tg_id)["current_id"] == estimate_id:
            self.conn.execute("UPDATE users SET current_id = NULL WHERE tg_id = ?", (tg_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    # ---------- reminders ----------

    def set_reminder(self, tg_id: int, estimate_id: int, when: datetime | None) -> None:
        value = when.isoformat(timespec="seconds") if when else ""
        self.conn.execute("UPDATE estimates SET remind_at = ? WHERE id = ? AND tg_id = ?", (value, estimate_id, tg_id))
        self.conn.commit()

    def due_reminders(self, now: datetime) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT id, tg_id, number, title, total FROM estimates "
            "WHERE status = 'sent' AND remind_at != '' AND remind_at <= ?",
            (now.isoformat(timespec="seconds"),),
        ).fetchall()

    # ---------- versions ----------

    def save_version(self, tg_id: int, estimate_id: int, estimate: Estimate, label: str = "") -> int:
        row = self.conn.execute("SELECT COALESCE(MAX(n), 0) FROM versions WHERE estimate_id = ? AND tg_id = ?",
                                (estimate_id, tg_id)).fetchone()
        number = int(row[0]) + 1
        self.conn.execute(
            "INSERT INTO versions (estimate_id, tg_id, n, label, data, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (estimate_id, tg_id, number, label, json.dumps(estimate.to_dict(), ensure_ascii=False), _now()),
        )
        self.conn.commit()
        return number

    def versions(self, tg_id: int, estimate_id: int) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT n, label, created_at, data FROM versions WHERE estimate_id = ? AND tg_id = ? ORDER BY n",
            (estimate_id, tg_id),
        ).fetchall()

    def load_version(self, tg_id: int, estimate_id: int, number: int) -> Estimate | None:
        row = self.conn.execute("SELECT data FROM versions WHERE estimate_id = ? AND tg_id = ? AND n = ?",
                                (estimate_id, tg_id, number)).fetchone()
        return Estimate.from_dict(json.loads(row["data"])) if row else None

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
        """Imported rates first; the shipped demo catalog only while `use_demo_rates` is on.

        Mixing an official FSNB import with demo prices would silently put made-up numbers
        into a real estimate, so importing turns the demo base off (see «Справочники»).
        """
        merged = Catalog(rates=[], nr_sp=dict(base.nr_sp), indices=dict(base.indices))
        for row in self.conn.execute(
            "SELECT body FROM imports WHERE tg_id = ? AND kind = 'rates' ORDER BY id", (tg_id,)
        ):
            try:
                merged.rates.extend(parse_rates_csv(row["body"]))
            except ValueError:
                continue
        own = len(merged.rates)
        for row in self.conn.execute(
            "SELECT body FROM imports WHERE tg_id = ? AND kind = 'indices' ORDER BY id", (tg_id,)
        ):
            try:
                merged.indices.update(parse_indices_csv(row["body"]))
            except (ValueError, KeyError):
                continue
        if not own or self.settings(tg_id)["use_demo_rates"]:
            merged.extend(Catalog(rates=list(base.rates)))
        return merged

    def offers(self, tg_id: int, base: OfferBook | None = None) -> OfferBook:
        book = OfferBook(list(base.offers) if base else [])
        for row in self.conn.execute(
            "SELECT body FROM imports WHERE tg_id = ? AND kind = 'offers' ORDER BY id", (tg_id,)
        ):
            book.offers = OfferBook.from_csv(row["body"]).offers + book.offers
        return book

    # ---------- subscription ----------

    def paid_until(self, tg_id: int) -> datetime | None:
        raw = self.user(tg_id)["paid_until"]
        return datetime.fromisoformat(raw) if raw else None

    def extend_subscription(self, tg_id: int, days: int, now: datetime | None = None) -> datetime:
        now = now or datetime.now(timezone.utc)
        current = self.paid_until(tg_id)
        start = current if current and current > now else now
        until = (start + timedelta(days=days)).replace(microsecond=0)
        self.conn.execute("UPDATE users SET paid_until = ?, sub_reminded = '' WHERE tg_id = ?",
                          (until.isoformat(timespec="seconds"), tg_id))
        self.conn.commit()
        return until

    def add_billing(self, tg_id: int, plan: str, amount: str, currency: str, charge_id: str) -> None:
        self.conn.execute(
            "INSERT INTO billing (tg_id, plan, amount, currency, charge_id, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (tg_id, plan, amount, currency, charge_id, _now()),
        )
        self.conn.commit()

    def charge_seen(self, charge_id: str) -> bool:
        return bool(charge_id) and self.conn.execute(
            "SELECT 1 FROM billing WHERE charge_id = ?", (charge_id,)).fetchone() is not None

    def promo_used(self, tg_id: int, code: str) -> bool:
        return self.conn.execute("SELECT 1 FROM promo_used WHERE tg_id = ? AND code = ?",
                                 (tg_id, code)).fetchone() is not None

    def use_promo(self, tg_id: int, code: str) -> None:
        self.conn.execute("INSERT OR IGNORE INTO promo_used (tg_id, code, created_at) VALUES (?, ?, ?)",
                          (tg_id, code, _now()))
        self.conn.commit()

    def expiring_subscriptions(self, now: datetime, days: int = 3) -> list[sqlite3.Row]:
        edge = (now + timedelta(days=days)).isoformat(timespec="seconds")
        return self.conn.execute(
            "SELECT tg_id, paid_until FROM users WHERE paid_until != '' AND paid_until <= ? AND paid_until > ? "
            "AND sub_reminded != paid_until",
            (edge, now.isoformat(timespec="seconds")),
        ).fetchall()

    def billing_stats(self) -> dict:
        row = self.conn.execute("SELECT COUNT(*), COALESCE(SUM(CAST(amount AS REAL)), 0) FROM billing").fetchone()
        active = self.conn.execute("SELECT COUNT(*) FROM users WHERE paid_until > ?",
                                   (_now(),)).fetchone()[0]
        users = self.conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        return {"payments": row[0], "amount": row[1], "active": active, "users": users}

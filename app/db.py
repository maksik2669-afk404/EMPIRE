"""SQLite storage. Buyer names are deliberately NOT stored (152-FZ data minimisation)."""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    tg_id INTEGER PRIMARY KEY,
    lang TEXT NOT NULL DEFAULT 'ru',
    signature TEXT NOT NULL DEFAULT '',
    auto_min_rating INTEGER NOT NULL DEFAULT 0,   -- 0 = auto-reply off; 4 or 5 = auto-reply to reviews >= N stars
    monthly_limit INTEGER NOT NULL,
    used INTEGER NOT NULL DEFAULT 0,
    month TEXT NOT NULL,
    quota_warned TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id INTEGER NOT NULL REFERENCES users(tg_id),
    marketplace TEXT NOT NULL,
    creds_enc TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1,
    last_error TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    external_id TEXT NOT NULL,
    kind TEXT NOT NULL,                 -- review | question
    product TEXT NOT NULL DEFAULT '',
    sku TEXT NOT NULL DEFAULT '',
    rating INTEGER,
    text TEXT NOT NULL DEFAULT '',
    buyer_lang TEXT NOT NULL DEFAULT '',
    translation TEXT NOT NULL DEFAULT '',
    draft TEXT NOT NULL DEFAULT '',
    draft_translation TEXT NOT NULL DEFAULT '',
    needs_input INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL,               -- pending | sent | auto_sent | skipped | error
    error TEXT NOT NULL DEFAULT '',
    extra TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    sent_at TEXT,
    UNIQUE (account_id, kind, external_id)
);
"""


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")  # same format as SQLite datetime()


def this_month() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


@dataclass
class User:
    tg_id: int
    lang: str
    signature: str
    auto_min_rating: int
    monthly_limit: int
    used: int
    month: str
    quota_warned: str
    created_at: str = ""


@dataclass
class Account:
    id: int
    tg_id: int
    marketplace: str
    creds_enc: str
    active: int
    last_error: str


@dataclass
class Item:
    id: int
    account_id: int
    external_id: str
    kind: str
    product: str
    sku: str
    rating: int | None
    text: str
    buyer_lang: str
    translation: str
    draft: str
    draft_translation: str
    needs_input: int
    status: str
    error: str
    extra: str
    created_at: str
    sent_at: str | None

    @property
    def extra_dict(self) -> dict:
        return json.loads(self.extra or "{}")


class DB:
    def __init__(self, path: str):
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def _exec(self, sql: str, args: tuple = ()) -> sqlite3.Cursor:
        cur = self.conn.execute(sql, args)
        self.conn.commit()
        return cur

    # ---- users
    def get_or_create_user(self, tg_id: int, default_limit: int) -> User:
        self._exec(
            "INSERT OR IGNORE INTO users (tg_id, monthly_limit, month, created_at) VALUES (?, ?, ?, ?)",
            (tg_id, default_limit, this_month(), now()),
        )
        return self.get_user(tg_id)  # type: ignore[return-value]

    def get_user(self, tg_id: int) -> User | None:
        row = self.conn.execute("SELECT * FROM users WHERE tg_id=?", (tg_id,)).fetchone()
        if not row:
            return None
        user = User(**dict(row))
        if user.month != this_month():  # new month -> reset usage counter
            self._exec("UPDATE users SET used=0, month=? WHERE tg_id=?", (this_month(), tg_id))
            user.used, user.month = 0, this_month()
        return user

    def update_user(self, tg_id: int, **fields) -> None:
        cols = ", ".join(f"{k}=?" for k in fields)
        self._exec(f"UPDATE users SET {cols} WHERE tg_id=?", (*fields.values(), tg_id))

    def try_consume_quota(self, tg_id: int) -> bool:
        """Atomically spend one AI draft from the monthly quota."""
        self.get_user(tg_id)  # resets the counter on a new month
        cur = self._exec("UPDATE users SET used=used+1 WHERE tg_id=? AND used < monthly_limit", (tg_id,))
        return cur.rowcount == 1

    def refund_quota(self, tg_id: int) -> None:
        self._exec("UPDATE users SET used=used-1 WHERE tg_id=? AND used > 0", (tg_id,))

    # ---- accounts
    def add_account(self, tg_id: int, marketplace: str, creds_enc: str) -> int:
        cur = self._exec(
            "INSERT INTO accounts (tg_id, marketplace, creds_enc, created_at) VALUES (?, ?, ?, ?)",
            (tg_id, marketplace, creds_enc, now()),
        )
        return int(cur.lastrowid)

    def get_account(self, account_id: int) -> Account | None:
        row = self.conn.execute(
            "SELECT id, tg_id, marketplace, creds_enc, active, last_error FROM accounts WHERE id=?", (account_id,)
        ).fetchone()
        return Account(**dict(row)) if row else None

    def list_accounts(self, tg_id: int | None = None, active_only: bool = False) -> list[Account]:
        sql = "SELECT id, tg_id, marketplace, creds_enc, active, last_error FROM accounts WHERE 1=1"
        args: list = []
        if tg_id is not None:
            sql += " AND tg_id=?"
            args.append(tg_id)
        if active_only:
            sql += " AND active=1"
        return [Account(**dict(r)) for r in self.conn.execute(sql + " ORDER BY id", args)]

    def set_account_state(self, account_id: int, *, active: int | None = None, last_error: str | None = None) -> None:
        if active is not None:
            self._exec("UPDATE accounts SET active=? WHERE id=?", (active, account_id))
        if last_error is not None:
            self._exec("UPDATE accounts SET last_error=? WHERE id=?", (last_error, account_id))

    def delete_account(self, account_id: int, tg_id: int) -> bool:
        return self._exec("DELETE FROM accounts WHERE id=? AND tg_id=?", (account_id, tg_id)).rowcount == 1

    # ---- items
    def item_exists(self, account_id: int, kind: str, external_id: str) -> bool:
        return self.conn.execute(
            "SELECT 1 FROM items WHERE account_id=? AND kind=? AND external_id=?", (account_id, kind, external_id)
        ).fetchone() is not None

    def add_item(self, account_id: int, **f) -> int:
        f.setdefault("extra", "{}")
        if isinstance(f["extra"], dict):
            f["extra"] = json.dumps(f["extra"], ensure_ascii=False)
        f.update(account_id=account_id, created_at=now())
        cols = ", ".join(f)
        cur = self._exec(f"INSERT INTO items ({cols}) VALUES ({', '.join('?' * len(f))})", tuple(f.values()))
        return int(cur.lastrowid)

    def get_item(self, item_id: int) -> Item | None:
        row = self.conn.execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone()
        return Item(**dict(row)) if row else None

    def update_item(self, item_id: int, **fields) -> None:
        cols = ", ".join(f"{k}=?" for k in fields)
        self._exec(f"UPDATE items SET {cols} WHERE id=?", (*fields.values(), item_id))

    def item_owner(self, item_id: int) -> int | None:
        row = self.conn.execute(
            "SELECT a.tg_id FROM items i JOIN accounts a ON a.id=i.account_id WHERE i.id=?", (item_id,)
        ).fetchone()
        return row[0] if row else None

    # ---- admin stats (traction numbers for the crowdfunding page)
    def stats(self) -> dict:
        q = lambda sql: self.conn.execute(sql).fetchone()[0]  # noqa: E731
        by_status = dict(self.conn.execute("SELECT status, COUNT(*) FROM items GROUP BY status").fetchall())
        by_mp = dict(self.conn.execute("SELECT marketplace, COUNT(*) FROM accounts GROUP BY marketplace").fetchall())
        return {
            "users": q("SELECT COUNT(*) FROM users"),
            "users_with_accounts": q("SELECT COUNT(DISTINCT tg_id) FROM accounts"),
            "accounts_by_marketplace": by_mp,
            "items_by_status": by_status,
            "sent_30d": q("SELECT COUNT(*) FROM items WHERE status IN ('sent','auto_sent') "
                          "AND sent_at >= datetime('now','-30 days')"),
        }

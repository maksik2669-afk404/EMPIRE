import sqlite3

import pytest
from cryptography.fernet import Fernet

from app import ai
from app.crypto import Vault
from app.db import DB
from app.facts import parse_csv, parse_text
from app.llm import MockLLM
from app.marketplaces import Incoming
from app.service import Engine, QuotaError
from tests.test_engine import FakeClient, FakeNotifier


def test_parse_text():
    assert parse_text("100001\nСталь 304, 450 мл") == ("100001", "Сталь 304, 450 мл")
    assert parse_text("100001 Сталь 304") == ("100001", "Сталь 304")
    assert parse_text("*\nДоставка 1-3 дня") == ("*", "Доставка 1-3 дня")
    assert parse_text("100001 -") == ("100001", "")
    for bad in ["100001", "", "x" * 70 + "\nfacts"]:
        with pytest.raises(ValueError):
            parse_text(bad)


def test_parse_csv_excel_cp1251_and_header():
    data = "Артикул;Название;Факты\n100001;Кружка;Сталь 304;450 мл\n;;\n100002;;Только факты\nbad\n".encode("cp1251")
    rows, skipped = parse_csv(data)
    assert rows == [("100001", "Кружка", "Сталь 304; 450 мл"), ("100002", "", "Только факты")]
    assert skipped == 1


def test_parse_csv_two_columns_utf8():
    rows, _ = parse_csv("sku,facts\nA-1,\"cotton, 200g\"\n".encode("utf-8-sig"))
    assert rows == [("A-1", "", "cotton, 200g")]


def test_old_database_is_migrated(tmp_path):
    path = tmp_path / "old.db"
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE users (tg_id INTEGER PRIMARY KEY, lang TEXT NOT NULL DEFAULT 'ru', signature TEXT NOT NULL "
                 "DEFAULT '', auto_min_rating INTEGER NOT NULL DEFAULT 0, monthly_limit INTEGER NOT NULL, used INTEGER "
                 "NOT NULL DEFAULT 0, month TEXT NOT NULL, quota_warned TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL)")
    conn.execute("INSERT INTO users (tg_id, monthly_limit, month, created_at) VALUES (1, 100, '2026-09', 'x')")
    conn.commit()
    conn.close()
    assert DB(str(path)).get_user(1).auto_questions == 0


class SpyLLM(MockLLM):
    def __init__(self):
        self.payloads = []

    async def complete(self, system, user, temperature=0.3):
        self.payloads.append(user)
        return await super().complete(system, user, temperature)


@pytest.fixture
def env():
    FakeClient.incoming = [Incoming("q1", "question", "Можно в посудомойку?", "Кружка", "100001"),
                           Incoming("q2", "question", "А крышка есть?", "Другое", "999")]
    FakeClient.replies, FakeClient.fail_fetch, FakeClient.fail_reply = [], None, None
    db = DB(":memory:")
    vault = Vault(Fernet.generate_key().decode())
    db.get_or_create_user(1, 100)
    acc_id = db.add_account(1, "wildberries", vault.encrypt({"token": "t"}))
    llm, notifier = SpyLLM(), FakeNotifier()
    engine = Engine(db, vault, llm, notifier, client_factory=lambda mp, creds: FakeClient(creds))
    return db, engine, notifier, llm, acc_id


async def test_facts_reach_the_prompt_and_enable_auto_answer(env):
    db, engine, notifier, llm, acc_id = env
    db.set_facts(1, "100001", "Можно мыть в посудомойке, крышка не герметична", name="Кружка")
    db.set_facts(1, "*", "Доставка со склада WB")
    db.update_user(1, auto_questions=1)
    await engine.poll_account(db.get_account(acc_id))
    assert "посудомойке" in llm.payloads[0] and "Доставка со склада WB" in llm.payloads[0]
    assert "посудомойке" not in llm.payloads[1]  # facts of another SKU are not leaked
    assert FakeClient.replies == [("question", "q1", notifier.items[0].draft)]  # q2 has no product facts
    assert [i.status for i in notifier.items] == ["auto_sent", "pending"]


async def test_questions_not_auto_answered_when_setting_off(env):
    db, engine, notifier, llm, acc_id = env
    db.set_facts(1, "100001", "Можно мыть в посудомойке")
    await engine.poll_account(db.get_account(acc_id))
    assert FakeClient.replies == []


async def test_add_facts_from_card_redrafts(env):
    db, engine, notifier, llm, acc_id = env
    await engine.poll_account(db.get_account(acc_id))
    item = notifier.items[0]
    assert item.needs_input == 1
    new = await engine.add_facts_and_redraft(item.id, 1, "Можно мыть в посудомойке")
    assert new.needs_input == 0 and "посудомойке" in new.draft
    assert dict(db.list_facts(1)) == {"100001": "Кружка"}


async def test_make_card_quota_and_refund(env):
    db, engine, *_ = env
    card = await engine.make_card(1, "Steel mug 450 ml")
    assert card.title and card.keywords and card.attributes == [("Объём", "450 мл")]

    class Broken:
        async def complete(self, *a, **k):
            return '{"title": ""}'

    engine.llm = Broken()
    used = db.get_user(1).used
    with pytest.raises(ai.DraftError):
        await engine.make_card(1, "x")
    assert db.get_user(1).used == used  # refunded
    db.update_user(1, monthly_limit=used)
    with pytest.raises(QuotaError):
        await engine.make_card(1, "x")

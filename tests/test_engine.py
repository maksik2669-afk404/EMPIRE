import json

import pytest
from cryptography.fernet import Fernet

from app import ai
from app.bot.handlers import render_card
from app.bot.texts import T
from app.crypto import Vault
from app.db import DB
from app.llm import MockLLM
from app.marketplaces import AuthError, BaseClient, Incoming, MarketplaceError
from app.service import Engine, QuotaError


class FakeClient(BaseClient):
    code = "wildberries"
    incoming: list[Incoming] = []
    replies: list = []
    fail_fetch: Exception | None = None
    fail_reply: Exception | None = None

    def headers(self):
        return {}

    async def fetch_new(self, limit):
        if FakeClient.fail_fetch:
            raise FakeClient.fail_fetch
        return FakeClient.incoming[:limit]

    async def reply(self, kind, external_id, text, extra):
        if FakeClient.fail_reply:
            raise FakeClient.fail_reply
        FakeClient.replies.append((kind, external_id, text))


class FakeNotifier:
    def __init__(self):
        self.items, self.texts = [], []

    async def item(self, tg_id, item, account):
        self.items.append(item)

    async def text(self, tg_id, key, **kw):
        self.texts.append(key)


@pytest.fixture
def env():
    FakeClient.incoming = [
        Incoming("r5", "review", "Отлично", "Кружка", "1", 5),
        Incoming("r2", "review", "Сломано", "Кружка", "1", 2),
        Incoming("q1", "question", "Можно в посудомойку?", "Кружка", "1"),
    ]
    FakeClient.replies, FakeClient.fail_fetch, FakeClient.fail_reply = [], None, None
    db = DB(":memory:")
    vault = Vault(Fernet.generate_key().decode())
    db.get_or_create_user(1, 100)
    acc_id = db.add_account(1, "wildberries", vault.encrypt({"token": "secret"}))
    notifier = FakeNotifier()
    engine = Engine(db, vault, MockLLM(), notifier, client_factory=lambda mp, creds: FakeClient(creds))
    return db, engine, notifier, acc_id


async def test_poll_creates_items_and_dedupes(env):
    db, engine, notifier, acc_id = env
    assert await engine.poll_account(db.get_account(acc_id)) == 3
    assert await engine.poll_account(db.get_account(acc_id)) == 0
    assert [i.status for i in notifier.items] == ["pending"] * 3
    assert FakeClient.replies == []  # auto-reply is off by default
    assert "secret" not in db.get_account(acc_id).creds_enc


async def test_auto_reply_only_good_reviews(env):
    db, engine, notifier, acc_id = env
    db.update_user(1, auto_min_rating=4)
    await engine.poll_account(db.get_account(acc_id))
    assert [r[1] for r in FakeClient.replies] == ["r5"]  # not the 2★ review, never a question
    assert [i.status for i in notifier.items] == ["auto_sent", "pending", "pending"]


async def test_auto_reply_failure_falls_back_to_manual(env):
    db, engine, notifier, acc_id = env
    db.update_user(1, auto_min_rating=5)
    FakeClient.fail_reply = MarketplaceError("boom")
    await engine.poll_account(db.get_account(acc_id))
    assert notifier.items[0].status == "pending" and "boom" in notifier.items[0].error


async def test_send_skip_and_ownership(env):
    db, engine, notifier, acc_id = env
    await engine.poll_account(db.get_account(acc_id))
    item = notifier.items[1]
    sent = await engine.send(item.id, 1)
    assert sent.status == "sent" and FakeClient.replies == [("review", "r2", item.draft)]
    await engine.send(item.id, 1)  # idempotent: no double reply
    assert len(FakeClient.replies) == 1
    assert engine.skip(notifier.items[2].id, 1).status == "skipped"
    with pytest.raises(PermissionError):
        await engine.send(notifier.items[0].id, 999)


async def test_send_error_keeps_item_pending(env):
    db, engine, notifier, acc_id = env
    await engine.poll_account(db.get_account(acc_id))
    FakeClient.fail_reply = MarketplaceError("already answered")
    with pytest.raises(MarketplaceError):
        await engine.send(notifier.items[0].id, 1)
    assert db.get_item(notifier.items[0].id).status == "pending"


async def test_quota(env):
    db, engine, notifier, acc_id = env
    db.update_user(1, monthly_limit=2)
    assert await engine.poll_account(db.get_account(acc_id)) == 2
    assert await engine.poll_account(db.get_account(acc_id)) == 0
    assert notifier.texts == ["quota_exceeded"]  # warned once per month, not every poll
    with pytest.raises(QuotaError):
        await engine.regenerate(notifier.items[0].id, 1)


async def test_auth_error_disables_account(env):
    db, engine, notifier, acc_id = env
    FakeClient.fail_fetch = AuthError("401")
    await engine.poll_all()
    assert db.get_account(acc_id).active == 0 and notifier.texts == ["account_disabled"]


async def test_llm_failure_refunds_quota(env):
    db, engine, notifier, acc_id = env

    class Broken:
        async def complete(self, *a, **k):
            return "not json at all"

    engine.llm = Broken()
    assert await engine.poll_account(db.get_account(acc_id)) == 0
    assert db.get_user(1).used == 0


async def test_draft_blocks_contacts_and_parses_fences():
    class LLM:
        async def complete(self, system, user, temperature=0.3):
            return '```json\n{"buyer_lang":"kk","translation":"t","reply":"Пишите в t.me/shop","reply_translation":"r"}\n```'

    d = await ai.make_draft(LLM(), marketplace="ozon", kind="review", text="x", product="", rating=5, seller_lang="zh")
    assert d.buyer_lang == "kk" and d.needs_input  # contacts => never auto-sent


async def test_seller_edit_same_language_skips_llm():
    class Boom:
        async def complete(self, *a, **k):
            raise AssertionError("LLM must not be called")

    assert await ai.translate_seller_reply(Boom(), seller_text="Да", seller_lang="ru", buyer_lang="ru") == ("Да", "Да")


def test_texts_complete_and_card_escaped(env):
    db, *_ , acc_id = env
    for lang in T:
        assert set(T[lang]) == set(T["ru"]), lang
    item_id = db.add_item(acc_id, external_id="x", kind="review", text="<script>", draft="Ответ <b>",
                          buyer_lang="ru", status="pending", extra={"a": 1})
    text, kb = render_card(db.get_item(item_id), db.get_account(acc_id), "zh")
    assert "<script>" not in text and "&lt;script&gt;" in text and kb is not None
    db.update_item(item_id, status="sent")
    assert render_card(db.get_item(item_id), db.get_account(acc_id), "ru")[1] is None
    assert json.loads(db.get_item(item_id).extra) == {"a": 1}

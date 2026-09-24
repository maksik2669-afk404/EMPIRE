"""Core engine, independent of Telegram: poll marketplaces, draft replies, send them.

A future web UI or MAX bot only needs another Notifier implementation.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Protocol

from . import ai
from .crypto import Vault
from .db import DB, Account, Item, now, this_month
from .llm import LLM
from .marketplaces import TITLES, AuthError, BaseClient, Incoming, MarketplaceError, make_client

log = logging.getLogger(__name__)


class Notifier(Protocol):
    async def item(self, tg_id: int, item: Item, account: Account) -> None: ...
    async def text(self, tg_id: int, key: str, **kw) -> None: ...


class Engine:
    def __init__(self, db: DB, vault: Vault, llm: LLM, notifier: Notifier, max_items: int = 20, client_factory=None):
        self.db, self.vault, self.llm, self.notifier = db, vault, llm, notifier
        self.max_items = max_items
        self._client_factory = client_factory or make_client
        self._locks: dict[int, asyncio.Lock] = {}

    def client(self, acc: Account) -> BaseClient:
        return self._client_factory(acc.marketplace, self.vault.decrypt(acc.creds_enc))

    # ------------------------------------------------------------------ polling
    async def poll_all(self) -> None:
        for acc in self.db.list_accounts(active_only=True):
            try:
                await self.poll_account(acc)
            except Exception:  # one broken account must not stop the others
                log.exception("poll failed for account %s", acc.id)

    async def poll_user(self, tg_id: int) -> int:
        total = 0
        for acc in self.db.list_accounts(tg_id, active_only=True):
            total += await self.poll_account(acc)
        return total

    async def poll_account(self, acc: Account) -> int:
        lock = self._locks.setdefault(acc.id, asyncio.Lock())
        async with lock:
            client = self.client(acc)
            try:
                return await self._poll(acc, client)
            finally:
                await client.close()

    async def _poll(self, acc: Account, client: BaseClient) -> int:
        try:
            incoming = await client.fetch_new(self.max_items)
        except AuthError as e:
            self.db.set_account_state(acc.id, active=0, last_error=str(e))
            await self.notifier.text(acc.tg_id, "account_disabled", mp=TITLES[acc.marketplace], error=str(e))
            return 0
        except MarketplaceError as e:
            log.warning("account %s: %s", acc.id, e)
            self.db.set_account_state(acc.id, last_error=str(e))
            return 0

        new = 0
        for inc in incoming:
            if self.db.item_exists(acc.id, inc.kind, inc.external_id):
                continue
            user = self.db.get_user(acc.tg_id)
            if not self.db.try_consume_quota(acc.tg_id):
                if user and user.quota_warned != this_month():
                    self.db.update_user(acc.tg_id, quota_warned=this_month())
                    await self.notifier.text(acc.tg_id, "quota_exceeded", limit=user.monthly_limit)
                break
            try:
                draft, has_facts = await self._draft(acc.marketplace, inc, user)
            except ai.DraftError as e:
                self.db.refund_quota(acc.tg_id)  # nothing was drafted; the item is retried on the next poll
                log.warning("draft failed for %s/%s: %s", acc.id, inc.external_id, e)
                continue
            item_id = self.db.add_item(
                acc.id, external_id=inc.external_id, kind=inc.kind, product=inc.product, sku=inc.sku,
                rating=inc.rating, text=inc.text, buyer_lang=draft.buyer_lang, translation=draft.translation,
                draft=draft.reply, draft_translation=draft.reply_translation, needs_input=int(draft.needs_input),
                status="pending", extra=inc.extra,
            )
            new += 1
            if self._auto_ok(user, inc, draft, has_facts):
                try:
                    await client.reply(inc.kind, inc.external_id, draft.reply, inc.extra)
                    self.db.update_item(item_id, status="auto_sent", sent_at=now())
                except MarketplaceError as e:  # fall back to manual approval
                    self.db.update_item(item_id, error=str(e))
            await self.notifier.item(acc.tg_id, self.db.get_item(item_id), acc)
        self.db.set_account_state(acc.id, last_error="")
        return new

    @staticmethod
    def _auto_ok(user, inc: Incoming, draft: ai.Draft, has_facts: bool) -> bool:
        if draft.needs_input:
            return False
        if inc.kind == "question":  # only when the seller's own facts about this product cover the answer
            return bool(user.auto_questions) and has_facts
        return user.auto_min_rating > 0 and inc.rating is not None and inc.rating >= user.auto_min_rating

    async def _draft(self, marketplace: str, inc: Incoming, user) -> tuple[ai.Draft, bool]:
        facts, has_facts = self.db.facts_for(user.tg_id, inc.sku)
        draft = await ai.make_draft(self.llm, marketplace=marketplace, kind=inc.kind, text=inc.text,
                                    product=inc.product, rating=inc.rating, seller_lang=user.lang,
                                    signature=user.signature, facts=facts)
        return draft, has_facts

    # ------------------------------------------------------------------ actions from the seller
    def _load(self, item_id: int, tg_id: int) -> tuple[Item, Account]:
        item = self.db.get_item(item_id)
        acc = self.db.get_account(item.account_id) if item else None
        if not item or not acc or acc.tg_id != tg_id:
            raise PermissionError("not your item")
        return item, acc

    async def send(self, item_id: int, tg_id: int) -> Item:
        item, acc = self._load(item_id, tg_id)
        if item.status in ("sent", "auto_sent"):
            return item
        client = self.client(acc)
        try:
            await client.reply(item.kind, item.external_id, item.draft, item.extra_dict)
        except MarketplaceError as e:
            self.db.update_item(item_id, error=str(e))
            raise
        finally:
            await client.close()
        self.db.update_item(item_id, status="sent", sent_at=now(), error="")
        return self.db.get_item(item_id)

    def skip(self, item_id: int, tg_id: int) -> Item:
        self._load(item_id, tg_id)
        self.db.update_item(item_id, status="skipped")
        return self.db.get_item(item_id)

    async def regenerate(self, item_id: int, tg_id: int) -> Item:
        item, acc = self._load(item_id, tg_id)
        if not self.db.try_consume_quota(tg_id):
            raise QuotaError()
        user = self.db.get_user(tg_id)
        inc = Incoming(item.external_id, item.kind, item.text, item.product, item.sku, item.rating, item.extra_dict)
        try:
            d, _ = await self._draft(acc.marketplace, inc, user)
        except ai.DraftError:
            self.db.refund_quota(tg_id)
            raise
        self.db.update_item(item_id, draft=d.reply, draft_translation=d.reply_translation,
                            needs_input=int(d.needs_input), translation=d.translation, buyer_lang=d.buyer_lang)
        return self.db.get_item(item_id)

    async def set_seller_text(self, item_id: int, tg_id: int, text: str) -> Item:
        item, _ = self._load(item_id, tg_id)
        user = self.db.get_user(tg_id)
        reply, back = await ai.translate_seller_reply(self.llm, seller_text=text, seller_lang=user.lang,
                                                      buyer_lang=item.buyer_lang or "ru")
        self.db.update_item(item_id, draft=reply, draft_translation=back, needs_input=0)
        return self.db.get_item(item_id)


    async def add_facts_and_redraft(self, item_id: int, tg_id: int, facts: str) -> Item:
        """Seller answers the 'needs facts' prompt once; the facts are reused for every future question."""
        item, _ = self._load(item_id, tg_id)
        self.db.set_facts(tg_id, item.sku or "*", facts[:4000], name=item.product)
        return await self.regenerate(item_id, tg_id)

    async def make_card(self, tg_id: int, product_info: str) -> ai.Card:
        if not self.db.try_consume_quota(tg_id):
            raise QuotaError()
        try:
            return await ai.make_card(self.llm, product_info=product_info, seller_lang=self.db.get_user(tg_id).lang)
        except ai.DraftError:
            self.db.refund_quota(tg_id)
            raise


class QuotaError(Exception):
    pass

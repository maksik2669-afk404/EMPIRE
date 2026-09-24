"""Drafting replies: detect the buyer's language, translate for the seller, write a safe reply."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass

from .llm import LLM, LLMError

LANG_NAMES = {
    "ru": "Russian", "en": "English", "zh": "Chinese (Simplified)", "tr": "Turkish", "kk": "Kazakh",
    "uz": "Uzbek", "ky": "Kyrgyz", "hy": "Armenian", "be": "Belarusian", "tg": "Tajik", "az": "Azerbaijani",
}
MP_NAMES = {"wildberries": "Wildberries", "ozon": "Ozon", "yandex_market": "Yandex Market", "demo": "Wildberries"}
MAX_REPLY = 1000

# Anything that looks like contacts/links must never be auto-sent: marketplaces penalise it.
_CONTACTS = re.compile(r"(https?://|www\.|t\.me/|@\w{3,}|\+?\d[\d\s\-()]{8,}\d|[\w.+-]+@[\w-]+\.\w+)", re.I)

DRAFT_SYSTEM = """You write replies on behalf of a seller on the Russian marketplace {mp}.
Return ONLY one JSON object, without markdown.

Rules for the reply to the buyer:
- Write it in the buyer's language, detected from the buyer's text. If the text is empty or unclear, use Russian.
- Polite, warm, specific to what the buyer wrote. 1-4 sentences, at most 500 characters.
- Never include links, phone numbers, e-mails or messengers; never invite the buyer to contact outside the marketplace.
- Never promise refunds, compensation, gifts or discounts. Never ask the buyer to change or delete a rating.
- "product_facts" come from the seller and are true; use them (translated into the buyer's language) to answer.
- Never invent product facts (sizes, materials, compatibility, stock, delivery dates) that are not in "product_facts".
  If a correct answer needs facts that are not there, write a short polite reply the seller will complete
  and set "needs_input" to true.
- Negative review: apologise, acknowledge the concrete problem, say in general terms what the seller does about it
  (e.g. "we passed this to quality control"); if relevant, remind that returns go through the marketplace rules.
- Positive review without text: thank briefly, vary wording, no clichés.
- If a signature is provided, end the reply with it.

JSON keys:
"buyer_lang": ISO 639-1 code of the buyer's language,
"translation": the buyer's text translated into {seller_lang} ("" if the buyer's text is empty),
"reply": the reply in the buyer's language,
"reply_translation": the reply translated into {seller_lang},
"needs_input": true or false"""

EDIT_SYSTEM = """A marketplace seller wrote a reply to a buyer in {seller_lang}.
Translate it into {buyer_lang} naturally and politely, fixing grammar. Keep the meaning.
Do not add facts, promises, links or contacts. Return ONLY JSON:
{{"reply": "<reply in {buyer_lang}>", "reply_translation": "<your reply translated back into {seller_lang}>"}}"""


class DraftError(Exception):
    pass


@dataclass
class Draft:
    buyer_lang: str
    translation: str
    reply: str
    reply_translation: str
    needs_input: bool


def extract_json(text: str) -> dict:
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise DraftError(f"модель вернула не JSON: {text[:200]}")
    try:
        data = json.loads(text[start:end + 1])
    except json.JSONDecodeError as e:
        raise DraftError(f"модель вернула битый JSON: {text[:200]}") from e
    if not isinstance(data, dict):
        raise DraftError("модель вернула не объект")
    return data


def has_contacts(text: str) -> bool:
    return bool(_CONTACTS.search(text))


async def _ask(llm: LLM, system: str, payload: dict) -> dict:
    user = json.dumps(payload, ensure_ascii=False)
    last: Exception | None = None
    for _ in range(2):  # one retry on malformed output
        try:
            return extract_json(await llm.complete(system, user))
        except DraftError as e:
            last = e
    raise DraftError(str(last))


async def make_draft(llm: LLM, *, marketplace: str, kind: str, text: str, product: str, rating: int | None,
                     seller_lang: str, signature: str = "", facts: str = "") -> Draft:
    system = DRAFT_SYSTEM.format(mp=MP_NAMES.get(marketplace, marketplace),
                                 seller_lang=LANG_NAMES.get(seller_lang, seller_lang))
    payload = {"kind": kind, "product": product, "rating": rating, "text": text, "signature": signature,
               "product_facts": facts}
    try:
        d = await _ask(llm, system, payload)
    except LLMError as e:
        raise DraftError(str(e)) from e
    reply = str(d.get("reply") or "").strip()
    if not reply:
        raise DraftError("модель вернула пустой ответ")
    reply = reply[:MAX_REPLY]
    return Draft(
        buyer_lang=str(d.get("buyer_lang") or "ru").lower()[:5],
        translation=str(d.get("translation") or "").strip(),
        reply=reply,
        reply_translation=str(d.get("reply_translation") or reply).strip(),
        needs_input=bool(d.get("needs_input")) or has_contacts(reply),
    )


async def translate_seller_reply(llm: LLM, *, seller_text: str, seller_lang: str, buyer_lang: str) -> tuple[str, str]:
    """Returns (reply in buyer language, back-translation for the seller)."""
    if buyer_lang == seller_lang:
        return seller_text[:MAX_REPLY], seller_text[:MAX_REPLY]
    system = EDIT_SYSTEM.format(seller_lang=LANG_NAMES.get(seller_lang, seller_lang),
                                buyer_lang=LANG_NAMES.get(buyer_lang, buyer_lang))
    try:
        d = await _ask(llm, system, {"seller_text": seller_text})
    except LLMError as e:
        raise DraftError(str(e)) from e
    reply = str(d.get("reply") or "").strip()
    if not reply:
        raise DraftError("модель вернула пустой перевод")
    return reply[:MAX_REPLY], str(d.get("reply_translation") or seller_text).strip()


# ------------------------------------------------------------------ product card localisation
CARD_SYSTEM = """You are an e-commerce copywriter for Russian marketplaces (Wildberries, Ozon, Yandex Market).
A seller describes a product in any language. Write a Russian product card optimised for marketplace search.
Return ONLY one JSON object, without markdown.

Rules:
- Use ONLY facts from the seller's input. Never invent specifications, materials, sizes, certificates,
  country of origin or guarantees. Put important facts buyers will look for but the seller did not give into "missing".
- "title": Russian, at most 60 characters: product type + key feature + brand/model if given.
  No CAPS, no emojis, no words like «лучший», «№1», «хит», «топ», no other brands.
- "description": Russian, 800-1500 characters, plain paragraphs: benefits first, then usage and care.
  Naturally include the main search phrases. No links, contacts, prices or delivery promises.
- "keywords": 15-25 Russian search phrases real buyers type, from generic to specific, lowercase.
- "attributes": key characteristics [{{"name": "...", "value": "..."}}] in Russian, only from the input.
- "seller_summary": 2-3 sentences in {seller_lang}: what the card emphasises and why.
- "missing": list of strings in {seller_lang}: facts to add to make the card stronger.

JSON keys: "title", "description", "keywords", "attributes", "seller_summary", "missing".
"""

TITLE_LIMIT = 60


@dataclass
class Card:
    title: str
    description: str
    keywords: list[str]
    attributes: list[tuple[str, str]]
    seller_summary: str
    missing: list[str]


def _str_list(v) -> list[str]:
    return [str(x).strip() for x in v if str(x).strip()] if isinstance(v, list) else []


async def make_card(llm: LLM, *, product_info: str, seller_lang: str) -> Card:
    system = CARD_SYSTEM.format(seller_lang=LANG_NAMES.get(seller_lang, seller_lang))
    try:
        d = await _ask(llm, system, {"product_info": product_info})
    except LLMError as e:
        raise DraftError(str(e)) from e
    title, description = str(d.get("title") or "").strip(), str(d.get("description") or "").strip()
    if not title or not description:
        raise DraftError("модель не вернула название или описание")
    attrs = []
    for a in d.get("attributes") or []:
        if isinstance(a, dict) and a.get("name") and a.get("value"):
            attrs.append((str(a["name"]).strip(), str(a["value"]).strip()))
    return Card(title=title, description=description[:3000], keywords=_str_list(d.get("keywords"))[:30],
                attributes=attrs[:30], seller_summary=str(d.get("seller_summary") or "").strip(),
                missing=_str_list(d.get("missing"))[:15])

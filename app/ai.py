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
- Never invent product facts (sizes, materials, compatibility, stock, delivery dates). If a correct answer needs facts
  that are not in the input, write a short polite reply the seller will complete and set "needs_input" to true.
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
                     seller_lang: str, signature: str = "") -> Draft:
    system = DRAFT_SYSTEM.format(mp=MP_NAMES.get(marketplace, marketplace),
                                 seller_lang=LANG_NAMES.get(seller_lang, seller_lang))
    payload = {"kind": kind, "product": product, "rating": rating, "text": text, "signature": signature}
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

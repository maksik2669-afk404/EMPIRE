"""Screens of the bot: text + inline keyboard for every menu, and the input wizards.

Every screen except the main menu ends with «⬅️ Назад» and «🏠 Меню». Screens are pure
functions of the context, so they are tested without Telegram.

Callback data:  go:<screen>   open a screen (pushed on the back stack)
                bk            back to the previous screen
                hm            main menu
                a:<action>    do something, then redraw
                ib / is       back / skip inside an input wizard
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from html import escape
from typing import Callable

from aiogram.types import (
    InlineKeyboardButton as Button,
    InlineKeyboardMarkup as Markup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    WebAppInfo,
)

from . import billing, consumption, datafiles, funnel, obmer, progress, render, tax, templates
from .context import Ctx
from .docs import crew_rows
from .model import MATERIAL, WORK, Estimate, inn_is_valid
from .money import ZERO, dec, money, qty_str, rub
from .profit import build_report

MENU_TEXT = "🏠 Меню"
ESTIMATE_TEXT = "🧮 Текущая смета"
PAGE = 8

Rows = list[list[tuple[str, str]]]


def reply_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=MENU_TEXT), KeyboardButton(text=ESTIMATE_TEXT)]],
        resize_keyboard=True, is_persistent=True, input_field_placeholder="Пишите работы: штукатурка стен 120 м2",
    )


def _button(text: str, data: str) -> Button:
    if data.startswith("https://"):
        return Button(text=text, web_app=WebAppInfo(url=data))     # кнопка мини-аппа
    return Button(text=text, callback_data=data)


def kb(rows: Rows, *, nav: bool = True) -> Markup:
    keyboard = [[_button(text, data) for text, data in row] for row in rows if row]
    if nav:
        keyboard.append([Button(text="⬅️ Назад", callback_data="bk"), Button(text="🏠 Меню", callback_data="hm")])
    return Markup(inline_keyboard=keyboard)


def short(text: str, size: int = 30) -> str:
    return text if len(text) <= size else text[: size - 1] + "…"


def pager(prefix: str, page: int, total: int, size: int = PAGE) -> list[tuple[str, str]]:
    pages = max((total - 1) // size + 1, 1)
    if pages == 1:
        return []
    row = []
    if page > 0:
        row.append(("◀️", f"go:{prefix}:{page - 1}"))
    row.append((f"{page + 1}/{pages}", f"go:{prefix}:{page}"))
    if page < pages - 1:
        row.append(("▶️", f"go:{prefix}:{page + 1}"))
    return row


def need_estimate() -> tuple[str, Markup]:
    return ("Текущей сметы нет — создайте новую или откройте из списка.",
            kb([[("🧮 Новая смета", "a:new"), ("📂 Мои сметы", "go:list:0")]]))


# ================================================================== screens


def home(ctx: Ctx) -> tuple[str, Markup]:
    company = ctx.deps.store.company(ctx.tg_id)
    found = ctx.current()
    lines = ["🏠 <b>Главное меню</b>", ""]
    lines.append(f"🏢 {escape(company.name)}" if company.name else "🏢 Компания не заполнена — начните с «Компания»")
    lines.append(billing.status_text(ctx.deps.store, ctx.tg_id))
    rows: Rows = [[("🧮 Новая смета", "a:new"), ("📂 Мои сметы", "go:list:0")]]
    from .webapp import webapp_url

    if webapp_url():
        rows.insert(0, [("📱 Открыть приложение", webapp_url())])
    if found:
        _, estimate = found
        lines.append(f"▶️ Текущая: {escape(estimate.number)} · {rub(estimate.total())} ₽ · "
                     f"{funnel.TITLES.get(estimate.status, '')}")
        rows.append([(f"▶️ Продолжить {estimate.number}", "go:est")])
    lines += ["", "Или просто напишите работы текстом — я добавлю их в текущую смету."]
    rows += [
        [("📐 Обмер помещений", "go:obm"), ("🏗 Смета по шаблону", "go:tpl")],
        [("🔍 Проверить чужую смету", "go:aud"), ("🧾 Налоги", "go:tax")],
        [("📊 Воронка продаж", "go:stats"), ("🏢 Компания", "go:co")],
        [("📚 Справочники", "go:refs"), ("💳 Подписка", "go:sub")],
        [("❓ Помощь", "go:help")],
    ]
    return "\n".join(lines), kb(rows, nav=False)


def estimate_screen(ctx: Ctx) -> tuple[str, Markup]:
    found = ctx.current()
    if not found:
        return need_estimate()
    _, estimate = found
    status = funnel.TITLES.get(estimate.status, estimate.status)
    text = render.estimate_text(estimate) + f"\n\n🏷 Статус: {status}"
    if not estimate.positions:
        return text, kb([
            [("➕ Добавить работы", "a:ask:works")],
            [("📐 Из обмера", "go:obm"), ("🏗 По шаблону", "go:tpl")],
        ])
    rows: Rows = [
        [("➕ Добавить работы", "a:ask:works"), ("✏️ Позиции", "go:items:0")],
        [("📉 Скидка / наценка", "go:cut"), ("⚙️ Коэффициенты", "go:coef")],
        [("📊 Лимитированные", "go:lim"), ("🧱 Материалы по нормам", "go:mat")],
        [("📄 Документы", "go:docs"), ("📈 Выполнение и оплаты", "go:prog")],
        [("💰 Профит", "go:profit"), ("🧾 Налоги", "go:tax")],
        [(f"🏷 {status}", "go:stat"), ("🕓 Версии", "go:ver")],
        [("🔁 Пересчёт цен", "go:rep"), ("👷 Бригада", "go:crew")],
    ]
    return text, kb(rows)


def items(ctx: Ctx, page: int = 0) -> tuple[str, Markup]:
    found = ctx.current()
    if not found:
        return need_estimate()
    _, estimate = found
    total = len(estimate.positions)
    start = page * PAGE
    rows: Rows = []
    for index in range(start, min(start + PAGE, total)):
        position = estimate.positions[index]
        icon = "🧱" if position.kind == MATERIAL else "🔨"
        mark = " ❓" if position.total(estimate.indices) <= ZERO else ""
        rows.append([(f"{index + 1}. {icon} {short(position.name, 32)}{mark}", f"go:pos:{index + 1}")])
    rows.append(pager("items", page, total))
    rows.append([("➕ Добавить работы", "a:ask:works")])
    return f"✏️ <b>Позиции сметы</b> ({total})\nНажмите на позицию, чтобы изменить её.", kb(rows)


def position_card(ctx: Ctx, index: int) -> tuple[str, Markup]:
    found = ctx.current()
    if not found:
        return need_estimate()
    _, estimate = found
    if not 1 <= index <= len(estimate.positions):
        return "Такой позиции уже нет.", kb([[("✏️ К списку позиций", "go:items:0")]])
    position = estimate.positions[index - 1]
    lines = [
        f"<b>{index}. {escape(position.name)}</b>",
        f"Шифр: {escape(position.code) or 'договорная цена'}",
        f"Объём: {qty_str(position.qty)} {position.unit}",
        f"Цена: {rub(position.unit_price_now(estimate.indices))} ₽/{position.unit}",
        f"Сумма: <b>{rub(position.total(estimate.indices))} ₽</b>",
    ]
    if position.k_basis:
        lines.append(f"⚙️ {escape(position.k_basis)}")
    if position.done:
        lines.append(f"✅ Выполнено {qty_str(position.done)} из {qty_str(position.qty)} {position.unit}, "
                     f"закрыто актами {qty_str(position.acted)}")
    if position.crew_price is not None:
        lines.append(f"👷 Ставка бригады: {rub(position.crew_price)} ₽/{position.unit}")
    if position.note:
        lines.append(f"📝 {escape(position.note)}")
    rows: Rows = [
        [("📏 Объём", f"a:ask:qty:{index}"), ("💬 Цена", f"a:ask:price:{index}")],
        [("✅ Выполнено", f"a:ask:done:{index}"), ("👷 Ставка бригады", f"a:ask:crew:{index}")],
        [("⚙️ Коэффициент", f"go:pcoef:{index}"), ("🗑 Удалить", f"a:del:{index}")],
    ]
    nav_row = []
    if index > 1:
        nav_row.append(("◀️ Пред.", f"go:pos:{index - 1}"))
    if index < len(estimate.positions):
        nav_row.append(("След. ▶️", f"go:pos:{index + 1}"))
    rows.append(nav_row)
    return "\n".join(lines), kb(rows)


def cut_screen(ctx: Ctx) -> tuple[str, Markup]:
    found = ctx.current()
    if not found:
        return need_estimate()
    _, estimate = found
    discount = estimate.discount_pct()
    lines = ["📉 <b>Скидка и наценка</b>", f"Итого сейчас: <b>{rub(estimate.total())} ₽</b>"]
    if discount:
        lines.append(f"Корректировка от исходной: {discount:+}%")
    losses = [w for w in estimate.warnings() if "себестоим" in w]
    if losses:
        lines.append("")
        lines.append(f"⚠️ Ниже себестоимости позиций: {len(losses)}")
        lines += [f"• {escape(w)}" for w in losses[:4]]
    lines.append("\nСкидка режет цены всех позиций; себестоимость при этом не меняется — бот покажет убыток.")
    rows: Rows = [
        [("−5%", "a:cut:-5"), ("−10%", "a:cut:-10"), ("−15%", "a:cut:-15")],
        [("−20%", "a:cut:-20"), ("−25%", "a:cut:-25"), ("−30%", "a:cut:-30")],
        [("+5%", "a:cut:5"), ("+10%", "a:cut:10"), ("+15%", "a:cut:15")],
        [("🔨 −10% только работы", "a:cutw:-10"), ("🧱 −10% материалы", "a:cutm:-10")],
        [("🎯 Подогнать под сумму", "a:ask:fit"), ("♻️ Сбросить", "a:reset")],
    ]
    return "\n".join(lines), kb(rows)


def coef_screen(ctx: Ctx, index: int | None = None) -> tuple[str, Markup]:
    found = ctx.current()
    if not found:
        return need_estimate()
    _, estimate = found
    where = f"к позиции {index}" if index else "ко всем работам сметы"
    lines = [f"⚙️ <b>Коэффициенты {where}</b>",
             "Коэффициент умножает оплату труда (ОТ), машины (ЭМ) и материалы (МАТ) и печатается "
             "в смете как обоснование."]
    applied = sorted({p.k_basis for p in estimate.positions if p.k_basis})
    if applied and not index:
        lines.append("\nУже применено:")
        lines += [f"• {escape(item)}" for item in applied[:6]]
    rows: Rows = []
    for row in datafiles.coefficients():
        label = f"{row['name'][:34]} ×{row['k_ot']}"
        rows.append([(label, f"a:pcoef:{index}:{row['code']}" if index else f"a:coef:{row['code']}")])
    if not index:
        rows.append([("✍️ Свой коэффициент", "a:ask:coef_custom"), ("🧹 Снять все", "a:coef_clear")])
    else:
        rows.append([("🧹 Снять с позиции", f"a:pcoef_clear:{index}")])
    return "\n".join(lines), kb(rows)


def limited_screen(ctx: Ctx) -> tuple[str, Markup]:
    found = ctx.current()
    if not found:
        return need_estimate()
    _, estimate = found
    totals = estimate.totals()
    lines = ["📊 <b>Лимитированные затраты</b>",
             "Начисляются процентом от итога по позициям, до НДС — как в настоящей смете.",
             f"Итого по позициям: {rub(totals.smr)} ₽"]
    for name, rate, amount in totals.limited:
        lines.append(f"✅ {escape(name)} {rate:g}% — {rub(amount)} ₽")
    current = {item["name"] for item in estimate.limited}
    rows: Rows = []
    for row in datafiles.limited_presets():
        mark = "✅" if row["name"] in current else "▫️"
        rows.append([(f"{mark} {short(row['name'], 34)} {row['pct']}%", f"a:lim:{row['code']}")])
    rows.append([("✍️ Своя статья", "a:ask:lim_custom"), ("🧹 Убрать все", "a:lim_clear")])
    return "\n".join(lines), kb(rows)


def materials_screen(ctx: Ctx) -> tuple[str, Markup]:
    found = ctx.current()
    if not found:
        return need_estimate()
    _, estimate = found
    preview = consumption.calculate(estimate, ctx.offers())
    lines = ["🧱 <b>Материалы по нормам расхода</b>"]
    if not preview:
        lines.append("Для работ этой сметы нет норм расхода. Нормы — в файле data/materials/norms.csv.")
        return "\n".join(lines), kb([])
    total = ZERO
    for position in preview:
        amount = position.total(estimate.indices)
        total += amount
        lines.append(f"• {escape(short(position.name, 40))}: {qty_str(position.qty)} {position.unit} — {rub(amount)} ₽")
    lines.append(f"\nИтого материалов: <b>{rub(total)} ₽</b> (без НДС)")
    lines.append("Количество округлено до целых упаковок с запасом; цена — из прайса поставщика, если он есть.")
    already = any(p.source == consumption.SOURCE for p in estimate.positions)
    rows: Rows = [[("✅ Добавить в смету" if not already else "♻️ Пересчитать в смете", "a:mat")]]
    if already:
        rows.append([("🗑 Убрать материалы по нормам", "a:mat_rm")])
    return "\n".join(lines), kb(rows)


def docs_screen(ctx: Ctx) -> tuple[str, Markup]:
    found = ctx.current()
    if not found:
        return need_estimate()
    _, estimate = found
    warnings = estimate.warnings()
    lines = ["📄 <b>Документы</b>", f"Смета {escape(estimate.number)} · {rub(estimate.total())} ₽"]
    if warnings:
        lines.append(f"⚠️ {escape(warnings[0])}")
    rows: Rows = [
        [("📄 Смета Excel", "a:doc:xlsx"), ("📕 Смета PDF", "a:doc:pdf")],
        [("💼 Коммерческое предложение", "a:doc:kp"), ("✍️ Условия КП", "a:ask:kp")],
        [("👷 Наряд бригаде", "a:doc:naryad"), ("📝 КС-2 и КС-3", "go:prog")],
        [("📎 Допсоглашение", "go:ver"), ("💰 Файл маржи (для себя)", "a:doc:margin")],
        [("📋 Договор №", "a:ask:contract")],
    ]
    return "\n".join(lines), kb(rows)


def progress_screen(ctx: Ctx) -> tuple[str, Markup]:
    found = ctx.current()
    if not found:
        return need_estimate()
    _, estimate = found
    info = progress.progress(estimate)
    to_act = sum(1 for p in estimate.positions if p.to_act > ZERO)
    text = "📈 <b>Выполнение и оплаты</b>\n\n" + escape(info.as_text())
    if to_act:
        text += f"\n\n📝 Готово к закрытию актом позиций: {to_act}"
    rows: Rows = [
        [("✅ Отметить выполнение", "go:pick:0")],
        [("📝 Сформировать КС-2 и КС-3", "a:act")] if to_act else [],
        [("💵 Внести оплату", "a:ask:pay"), ("🗓 График платежей", "go:sched")],
        [("📑 Акты", "go:acts")] if estimate.acts else [],
    ]
    return text, kb(rows)


def pick_screen(ctx: Ctx, page: int = 0) -> tuple[str, Markup]:
    found = ctx.current()
    if not found:
        return need_estimate()
    _, estimate = found
    works = [(i, p) for i, p in enumerate(estimate.positions, 1)]
    start = page * PAGE
    rows: Rows = []
    for index, position in works[start:start + PAGE]:
        share = (position.done / position.qty * 100) if position.qty else ZERO
        icon = "✅" if share >= 100 else ("🟡" if share > 0 else "▫️")
        rows.append([(f"{icon} {index}. {short(position.name, 28)} {share:.0f}%", f"a:ask:done:{index}")])
    rows.append(pager("pick", page, len(works)))
    rows.append([("✅ Всё выполнено", "a:done_all")])
    return "✅ <b>Что выполнено?</b>\nВыберите позицию и укажите объём или процент.", kb(rows)


def schedule_screen(ctx: Ctx) -> tuple[str, Markup]:
    found = ctx.current()
    if not found:
        return need_estimate()
    _, estimate = found
    lines = ["🗓 <b>График платежей</b>"]
    if estimate.schedule:
        lines.append("Сейчас: " + ", ".join(f"{s['name']} {s['pct']}%" for s in estimate.schedule))
    lines.append("Выберите схему — сроки встанут через каждые 14 дней от сегодня.")
    rows: Rows = [[(f"💳 {name}", f"a:sched:{name}")] for name in progress.SCHEDULE_PRESETS]
    rows.append([("🧹 Убрать график", "a:sched_clear")])
    return "\n".join(lines), kb(rows)


def acts_screen(ctx: Ctx) -> tuple[str, Markup]:
    found = ctx.current()
    if not found:
        return need_estimate()
    _, estimate = found
    lines = ["📑 <b>Акты по смете</b>"]
    rows: Rows = []
    for act in estimate.acts:
        lines.append(f"№ {act['number']} от {act['date']} — {rub(dec(act['total']))} ₽")
        rows.append([(f"📥 КС-2 и КС-3 № {act['number']}", f"a:actget:{act['number']}")])
    return "\n".join(lines), kb(rows)


def status_screen(ctx: Ctx) -> tuple[str, Markup]:
    found = ctx.current()
    if not found:
        return need_estimate()
    _, estimate = found
    lines = ["🏷 <b>Статус сметы</b>", f"Сейчас: {funnel.TITLES.get(estimate.status, estimate.status)}"]
    if estimate.status == "sent":
        lines.append(f"Напомню, если заказчик не ответит {funnel.REMIND_DAYS} дня.")
    rows: Rows = [[(f"{icon} {title}", f"a:status:{code}")] for code, icon, title in funnel.STATUSES
                  if code != estimate.status]
    return "\n".join(lines), kb(rows)


def versions_screen(ctx: Ctx) -> tuple[str, Markup]:
    found = ctx.current()
    if not found:
        return need_estimate()
    estimate_id, estimate = found
    saved = ctx.deps.store.versions(ctx.tg_id, estimate_id)
    lines = ["🕓 <b>Версии сметы</b>",
             "Сохраните версию перед изменениями — потом из разницы получится допсоглашение."]
    rows: Rows = [[("💾 Сохранить текущую версию", "a:ver_save")]]
    for row in saved[-8:]:
        label = f" {row['label']}" if row["label"] else ""
        lines.append(f"v{row['n']}{escape(label)} — {row['created_at'][:16].replace('T', ' ')}")
        rows.append([(f"🔀 v{row['n']}{short(label, 20)} ↔ текущая", f"go:vd:{row['n']}")])
    return "\n".join(lines), kb(rows)


def version_diff_screen(ctx: Ctx, number: int) -> tuple[str, Markup]:
    from .versions import diff

    found = ctx.current()
    if not found:
        return need_estimate()
    estimate_id, estimate = found
    old = ctx.deps.store.load_version(ctx.tg_id, estimate_id, number)
    if old is None:
        return "Версия не найдена.", kb([])
    change = diff(old, estimate)
    rows: Rows = [[("📎 Допсоглашение на разницу", f"a:ds:{number}")] if change.changes else [],
                  [("↩️ Вернуть эту версию", f"a:restore:{number}")]]
    return f"<b>v{number} → текущая</b>\n" + escape(change.as_text()), kb(rows)


def reprice_screen(ctx: Ctx) -> tuple[str, Markup]:
    found = ctx.current()
    if not found:
        return need_estimate()
    _, estimate = found
    catalog = ctx.catalog()
    lines = ["🔁 <b>Пересчёт по новым ценам</b>",
             f"Сейчас индекс: {escape(estimate.indices.region)} {escape(estimate.indices.period)}".strip(),
             "Выберите новый индекс или пересчитайте материалы по свежему прайсу. "
             "Сначала покажу разницу — применится только после подтверждения."]
    rows: Rows = []
    for number, name in enumerate(list(catalog.indices)[:10], 1):
        rows.append([(f"📈 {short(name, 38)}", f"a:rep:{number}")])
    rows.append([("🏪 Материалы по новому прайсу", "a:rep:offers")])
    return "\n".join(lines), kb(rows)


def reprice_preview(ctx: Ctx) -> tuple[str, Markup]:
    from .reprice import reprice

    found = ctx.current()
    pending = ctx.data.get("pending_rep")
    if not found or not pending:
        return "Нечего пересчитывать.", kb([])
    _, estimate = found
    result = reprice(estimate, **reprice_args(ctx, pending))
    return escape(result.as_text()), kb([[("✅ Применить к смете", "a:rep_apply")],
                                         [("📥 Сравнение Excel + письмо заказчику", "a:rep_files")]])


def reprice_args(ctx: Ctx, pending: dict) -> dict:
    if pending.get("offers"):
        return {"offers": ctx.offers()}
    names = list(ctx.catalog().indices)
    number = int(pending.get("index", 0))
    if not 1 <= number <= len(names):
        return {}
    return {"indices": ctx.catalog().indices[names[number - 1]]}


def crew_screen(ctx: Ctx) -> tuple[str, Markup]:
    found = ctx.current()
    if not found:
        return need_estimate()
    _, estimate = found
    _, total, missing = crew_rows(estimate)
    works = money(sum((p.total(estimate.indices) for p in estimate.positions if p.kind == WORK), ZERO))
    lines = ["👷 <b>Бригада и наряд-задание</b>",
             f"Бригада: {escape(estimate.crew) or 'не указана'}",
             f"Работы по смете: {rub(works)} ₽",
             f"К выплате бригаде: {rub(total)} ₽"]
    if works and total:
        lines.append(f"Остаётся подрядчику с работ: {rub(works - total)} ₽ ({(works - total) / works * 100:.0f}%)")
    if missing:
        lines.append(f"Без ставки: {missing} поз. — задайте процентом ниже или в карточке позиции.")
    rows: Rows = [
        [("30%", "a:crewpct:30"), ("40%", "a:crewpct:40"), ("50%", "a:crewpct:50"), ("60%", "a:crewpct:60")],
        [("✍️ Бригадир / бригада", "a:ask:crew_name"), ("🧹 Сбросить ставки", "a:crew_clear")],
        [("📄 Наряд-задание", "a:doc:naryad")],
    ]
    return "\n".join(lines) + "\n\nКнопки с процентами ставят ставку бригады как долю от цены работ.", kb(rows)


def profit_screen(ctx: Ctx) -> tuple[str, Markup]:
    found = ctx.current()
    if not found:
        return need_estimate()
    _, estimate = found
    report = build_report(estimate, ctx.offers())
    return render.profit_text(report), kb([[("📥 Файл маржи", "a:doc:margin"), ("🧾 После налогов", "go:tax")]])


def obmer_screen(ctx: Ctx) -> tuple[str, Markup]:
    rooms = [obmer.Room(**room) for room in ctx.data.get("rooms", [])]
    text = "📐 <b>Обмер помещений</b>\n\n" + escape(obmer.summary_text(rooms))
    text += "\n\nДобавьте помещение одной строкой: <code>кухня 4,2 3,1 2,7 д1 о1</code> (д — дверей, о — окон)."
    rows: Rows = [[("➕ Добавить помещение", "a:ask:room")]]
    if rooms:
        rows.append([("🧱 Выбрать работы → в смету", "go:obmw"), ("🏗 Шаблон по обмеру", "go:tpl")])
        rows.append([("↩️ Убрать последнее", "a:obm_pop"), ("🧹 Очистить", "a:obm_clear")])
    return text, kb(rows)


def obmer_works_screen(ctx: Ctx) -> tuple[str, Markup]:
    rooms = [obmer.Room(**room) for room in ctx.data.get("rooms", [])]
    if not rooms:
        return "Сначала добавьте помещения.", kb([[("➕ Добавить помещение", "a:ask:room")]])
    values = obmer.summary(rooms)
    chosen = set(ctx.data.get("obm_works", []))
    rows: Rows = []
    for key, label, _, unit, var in obmer.WORKS:
        mark = "✅" if key in chosen else "▫️"
        rows.append([(f"{mark} {label} — {qty_str(values[var])} {unit}", f"a:obmt:{key}")])
    rows.append([("➕ Добавить выбранные в смету", "a:obm_add")])
    return "🧱 <b>Какие работы делаем?</b>\nОтметьте — объёмы уже посчитаны по обмеру.", kb(rows)


def templates_screen(ctx: Ctx) -> tuple[str, Markup]:
    rows: Rows = [[(entry["title"], f"go:tpl1:{code}")] for code, entry in templates.catalog_of_templates().items()]
    text = ("🏗 <b>Смета по шаблону</b>\nНесколько чисел про объект — и готовый набор работ с объёмами. "
            "Потом всё можно поправить.")
    return text, kb(rows)


def template_screen(ctx: Ctx, code: str) -> tuple[str, Markup]:
    entry = templates.catalog_of_templates().get(code)
    if not entry:
        return "Шаблон не найден.", kb([])
    works = ", ".join(sorted({row["work"] for row in entry["lines"]}))
    text = f"{entry['title']}\n\nРаботы: {escape(works)}"
    rows: Rows = [[("✍️ Ввести площадь и высоту", f"a:ask:tpl:{code}")]]
    if ctx.data.get("rooms"):
        rows.insert(0, [("📐 Взять размеры из обмера", f"a:tplobm:{code}")])
    return text, kb(rows)


def template_preview(ctx: Ctx) -> tuple[str, Markup]:
    pending = ctx.data.get("pending_tpl") or {}
    if not pending:
        return "Нет рассчитанного шаблона.", kb([[("🏗 К шаблонам", "go:tpl")]])
    values = {k: dec(v) for k, v in pending["vars"].items()}
    matches = templates.build_template(pending["code"], values, ctx.catalog(), ctx.offers())
    from .model import Estimate as _Estimate

    sample = _Estimate(indices=ctx.catalog().index(ctx.settings()["index_name"] or None), vat_pct=ctx.settings()["vat_pct"])
    for match in matches:
        sample.add(match.position)
    title = templates.catalog_of_templates()[pending["code"]]["title"]
    lines = [f"{title} — предварительно", "",
             f"Площадь {qty_str(values['S'])} м², высота {qty_str(values['H'])} м, стены {qty_str(values['W'])} м²",
             f"Позиций: {len(matches)}, итого ≈ <b>{rub(sample.total())} ₽</b>"]
    for note in pending.get("notes", []):
        lines.append(f"ℹ️ {escape(note)}")
    unmatched = [m.draft.name for m in matches if m.status == "needs_price"]
    if unmatched:
        lines.append(f"❓ Нет в справочнике, нужна цена: {escape(', '.join(unmatched))}")
    rows: Rows = [[("➕ В текущую смету", "a:tpl_add"), ("🆕 Новой сметой", "a:tpl_new")]]
    return "\n".join(lines), kb(rows)


def audit_screen(ctx: Ctx) -> tuple[str, Markup]:
    text = ("🔍 <b>Проверка чужой сметы</b>\n\nПришлите файл сметы (Excel или CSV) следующим сообщением.\n"
            "Проверю арифметику, повторы, «Итого» и НДС, сравню цены со справочником и подскажу, "
            "какие работы могли забыть.")
    return text, kb([])


def tax_screen(ctx: Ctx) -> tuple[str, Markup]:
    settings = ctx.settings()
    form = "ИП" if settings["tax_ip"] else "ООО"
    staff = "есть" if settings["tax_staff"] else "нет"
    annual = f"{rub(settings['tax_annual'])} ₽" if settings["tax_annual"] else "не задан"
    lines = ["🧾 <b>Налоги</b>", f"Форма: {form} · работники: {staff} · годовой доход: {annual}"]
    found = ctx.current()
    rows: Rows = [
        [(f"{'👤 ИП' if settings['tax_ip'] else '🏢 ООО'} (сменить)", "a:tax_ip"),
         (f"👷 Работники: {staff}", "a:tax_staff")],
        [("📅 Годовой доход", "a:ask:tax_annual"), ("📜 Ставки", "a:tax_rates")],
    ]
    if found and found[1].positions:
        inputs = tax_inputs(ctx, found[1])
        lines.append("")
        lines.append(f"<pre>{escape(tax.compare_text(inputs))}</pre>")
        rows.insert(0, [("🎯 Сколько ставить, чтобы получить X", "a:ask:tax_target")])
    else:
        lines.append("\nТекущей сметы нет — можно посчитать по сумме.")
        rows.insert(0, [("🧮 Посчитать по сумме", "a:ask:tax_manual")])
    return "\n".join(lines), kb(rows)


def tax_inputs(ctx: Ctx, estimate: Estimate) -> tax.Money:
    settings = ctx.settings()
    totals = estimate.totals()
    report = build_report(estimate, ctx.offers())
    materials = money(sum((row.cost or ZERO) for row in report.materials))
    crew = sum((p.crew_price * p.qty for p in estimate.positions if p.crew_price is not None), ZERO)
    payroll = money(crew if crew else totals.ot + totals.zpm)
    other = money(max(report.cost_total - materials - payroll, ZERO))
    return tax.Money(revenue=estimate.total(), vat_in_revenue=totals.vat, materials=materials, payroll=payroll,
                     other_costs=other, employees=settings["tax_staff"], ip=settings["tax_ip"],
                     annual_revenue=settings["tax_annual"])


def company_screen(ctx: Ctx) -> tuple[str, Markup]:
    settings = ctx.settings()
    company = ctx.deps.store.company(ctx.tg_id)
    lines = [render.company_text(company)]
    if company.inn and not inn_is_valid(company.inn):
        lines.append("⚠️ ИНН не проходит проверку контрольной суммы.")
    lines.append(f"\n🧾 НДС в сметах: {settings['vat_pct']:g}%" if settings["vat_pct"] else "\n🧾 Сметы без НДС (УСН)")
    lines.append("🏢 Накладные — в себестоимости" if settings["floor_with_nr"] else "👷 Накладные не в себестоимости")
    lines.append("🖼 Логотип загружен" if ctx.logo() else "🖼 Логотипа нет")
    rows: Rows = [
        [("✏️ Заполнить реквизиты", "a:ask:company")],
        [("🖼 Логотип для КП", "a:ask:logo"), (f"🧾 НДС {tax.current_vat():g}% / без НДС", "a:vat")],
        [("🏢 Накладные в себестоимости вкл/выкл", "a:nr")],
    ]
    return "\n".join(lines), kb(rows)


def refs_screen(ctx: Ctx) -> tuple[str, Markup]:
    settings = ctx.settings()
    own = sum(row["rows"] for row in ctx.deps.store.imports(ctx.tg_id, "rates"))
    indices = sum(row["rows"] for row in ctx.deps.store.imports(ctx.tg_id, "indices"))
    offers = sum(row["rows"] for row in ctx.deps.store.imports(ctx.tg_id, "offers"))
    catalog = ctx.catalog()
    lines = ["📚 <b>Справочники</b>",
             f"Своих расценок: {own} · индексов: {indices} · строк прайса: {offers}",
             f"Демо-расценки: {'включены' if settings['use_demo_rates'] else 'отключены'} · всего доступно: {len(catalog.rates)}",
             f"Индекс: {escape(settings['index_name'] or 'текущие цены')}",
             "", "Загрузка: ФСНБ-2022 и индексы ФГИС ЦС (XLSX, XML, DBF, CSV, ZIP до 20 МБ) или прайс поставщика."]
    if ctx.tg_id in billing.admins():                     # подсказка по большим файлам — только администратору
        lines.append("Больше 20 МБ — на сервере: <code>python3 -m smeta.fgis load файл</code>")
    rows: Rows = [
        [("📥 Загрузить файл", "a:ask:import"), ("🔎 Найти расценку", "a:ask:rates_q")],
        [("📈 Индекс пересчёта", "go:idx:0"), ("🗂 Демо вкл/выкл", "a:base")],
        [("🧹 Удалить загруженное", "a:import_clear")],
    ]
    return "\n".join(lines), kb(rows)


def index_screen(ctx: Ctx, page: int = 0) -> tuple[str, Markup]:
    catalog = ctx.catalog()
    names = list(catalog.indices)
    current = ctx.settings()["index_name"] or (names[0] if names else "")
    rows: Rows = []
    for number in range(page * PAGE, min((page + 1) * PAGE, len(names))):
        name = names[number]
        value = catalog.indices[name]
        mark = "✅ " if name == current else ""
        rows.append([(f"{mark}{short(name, 30)} · {value.ot}/{value.em}/{value.mat}", f"a:idx:{number + 1}")])
    rows.append(pager("idx", page, len(names)))
    return ("📈 <b>Индекс пересчёта в текущие цены</b>\nИОТ / ИЭМ / ИМАТ. Выбранный применяется к текущей смете.",
            kb(rows))


def subscription_screen(ctx: Ctx) -> tuple[str, Markup]:
    lines = ["💳 <b>Подписка</b>", billing.status_text(ctx.deps.store, ctx.tg_id), ""]
    rows: Rows = []
    token = billing.provider_token()
    for item in billing.plans():
        price = f"{item.price_rub} ₽" if token else f"{item.stars} ⭐"
        rows.append([(f"{item.title} — {price}", f"a:buy:{item.code}")])
    lines.append("Подписка открывает готовые документы: смета, КП, наряд, КС-2/КС-3. "
                 "Расчёт на экране — всегда бесплатно.")
    if billing.tribute_pay_url(ctx.tg_id):
        rows.append([("💳 Оплатить по СБП (Tribute)", "a:tribute")])
    rows.append([("🎟 Ввести промокод", "a:ask:promo")])
    if ctx.tg_id in billing.admins():
        stats = ctx.deps.store.billing_stats()
        lines.append(f"\n👑 Пользователей {stats['users']}, активных подписок {stats['active']}, "
                     f"оплат {stats['payments']} на {stats['amount']:.0f}")
    return "\n".join(lines), kb(rows)


def estimates_list(ctx: Ctx, page: int = 0) -> tuple[str, Markup]:
    rows_db = ctx.deps.store.list_estimates(ctx.tg_id, limit=PAGE, offset=page * PAGE)
    total = ctx.deps.store.count_estimates(ctx.tg_id)
    icons = {code: icon for code, icon, _ in funnel.STATUSES}
    rows: Rows = [[(f"{icons.get(row['status'], '📝')} {row['number']} · {rub(dec(row['total']))} ₽",
                    f"a:open:{row['id']}")] for row in rows_db]
    rows.append(pager("list", page, total))
    rows.append([("🧮 Новая смета", "a:new")])
    text = f"📂 <b>Мои сметы</b> ({total})" if total else "📂 Смет пока нет."
    return text, kb(rows)


def stats_screen(ctx: Ctx) -> tuple[str, Markup]:
    estimates = [estimate for _, estimate in ctx.deps.store.all_estimates(ctx.tg_id)]
    return escape(funnel.stats(estimates).as_text()), kb([[("📂 Мои сметы", "go:list:0")]])


def help_screen(ctx: Ctx) -> tuple[str, Markup]:
    text = (
        "❓ <b>Как пользоваться</b>\n\n"
        "1. 🏢 Компания — один раз заполните реквизиты, они попадут в шапку всех документов.\n"
        "2. 🧮 Новая смета — объект и заказчик.\n"
        "3. Пишите работы обычным текстом: <code>штукатурка стен 120 м2</code>, "
        "<code>стяжка 85 м2 по 700</code>, <code>мат: керамогранит 22 м2</code>.\n"
        "   Или 📐 обмер / 🏗 шаблон — объёмы посчитаются сами.\n"
        "4. 📄 Документы — смета, КП, наряд, КС-2/КС-3, допсоглашение.\n"
        "5. 💰 Профит и 🧾 Налоги — сколько останется вам.\n\n"
        "На каждом шаге есть «⬅️ Назад» и «🏠 Меню». Кнопка «🏠 Меню» внизу экрана работает всегда.\n\n"
        + render.HELP
    )
    return text, kb([])


# ================================================================== router


SCREENS: dict[str, Callable] = {
    "home": home, "est": estimate_screen, "items": items, "pos": position_card, "cut": cut_screen,
    "coef": coef_screen, "pcoef": coef_screen, "lim": limited_screen, "mat": materials_screen,
    "docs": docs_screen, "prog": progress_screen, "pick": pick_screen, "sched": schedule_screen,
    "acts": acts_screen, "stat": status_screen, "ver": versions_screen, "vd": version_diff_screen,
    "rep": reprice_screen, "reppv": reprice_preview, "crew": crew_screen, "profit": profit_screen, "obm": obmer_screen,
    "obmw": obmer_works_screen, "tpl": templates_screen, "tpl1": template_screen, "tplp": template_preview,
    "aud": audit_screen, "tax": tax_screen, "co": company_screen, "refs": refs_screen, "idx": index_screen,
    "sub": subscription_screen, "list": estimates_list, "stats": stats_screen, "help": help_screen,
}
INT_ARG = {"items", "pos", "pcoef", "pick", "vd", "idx", "list"}


def render_screen(screen: str, ctx: Ctx) -> tuple[str, Markup]:
    name, _, arg = screen.partition(":")
    handler = SCREENS.get(name, home)
    if not arg:
        return handler(ctx)
    if name in INT_ARG:
        try:
            return handler(ctx, int(arg))
        except ValueError:
            return handler(ctx)
    return handler(ctx, arg)


# ================================================================== input wizards


@dataclass
class Step:
    key: str
    prompt: str
    optional: bool = False
    parse: Callable[[str], object] | None = None      # raises ValueError with a human message
    quick: list[tuple[str, str]] = field(default_factory=list)   # extra buttons: (label, value)


def _number(text: str) -> Decimal:
    value = dec((text or "").replace("₽", "").replace("%", "").replace(" ", ""), None)
    if value is None:
        raise ValueError("нужно число, например 85 или 2,7")
    return value


def _positive(text: str) -> Decimal:
    value = _number(text)
    if value <= ZERO:
        raise ValueError("число должно быть больше нуля")
    return value


def _inn(text: str) -> str:
    digits = "".join(ch for ch in text if ch.isdigit())
    if not inn_is_valid(digits):
        raise ValueError("ИНН не сходится по контрольной сумме — проверьте цифры")
    return digits


WIZARDS: dict[str, list[Step]] = {
    "company": [
        Step("name", "🏢 Название организации или ИП (как в документах):"),
        Step("inn", "🔢 ИНН (10 или 12 цифр):", parse=_inn),
        Step("kpp", "КПП (у ИП нет — пропустите):", optional=True),
        Step("address", "📍 Адрес:", optional=True),
        Step("phone", "📞 Телефон:", optional=True),
        Step("email", "✉️ E-mail:", optional=True),
        Step("signer", "✍️ Кто подписывает — должность и ФИО, например «Директор Иванов И.И.»:", optional=True),
    ],
    "new": [
        Step("object_name", "🏠 Объект — адрес или название:", optional=True),
        Step("customer", "👤 Заказчик — название и ИНН или ФИО:", optional=True),
        Step("contract", "📋 Договор — номер и дата (можно позже):", optional=True),
    ],
    "tpl": [
        Step("area", "📏 Площадь пола, м²:", parse=_positive),
        Step("height", "↕️ Высота потолков, м:", parse=_positive, quick=[("2,5", "2.5"), ("2,7", "2.7"), ("3,0", "3")]),
        Step("rooms", "🚪 Сколько жилых комнат?", parse=_positive, quick=[("1", "1"), ("2", "2"), ("3", "3"), ("4", "4")]),
        Step("baths", "🛁 Сколько санузлов?", parse=_number, quick=[("0", "0"), ("1", "1"), ("2", "2")]),
        Step("perimeter", "📐 Периметр всех помещений, м (не знаете — пропустите, оценю):", optional=True, parse=_positive),
    ],
    "tpl_bath": [
        Step("area", "📏 Площадь пола санузла, м²:", parse=_positive),
        Step("height", "↕️ Высота, м:", parse=_positive, quick=[("2,5", "2.5"), ("2,7", "2.7")]),
        Step("perimeter", "📐 Периметр, м (не знаете — пропустите):", optional=True, parse=_positive),
    ],
    "coef_custom": [
        Step("name", "⚙️ Название коэффициента (например «Работа на высоте»):"),
        Step("k_ot", "К к оплате труда (ОТ), например 1,15:", parse=_positive, quick=[("1,1", "1.1"), ("1,15", "1.15"), ("1,2", "1.2")]),
        Step("k_em", "К к машинам (ЭМ):", parse=_positive, quick=[("1", "1"), ("1,15", "1.15")]),
        Step("k_mat", "К к материалам (МАТ):", parse=_positive, quick=[("1", "1")]),
    ],
    "lim_custom": [
        Step("name", "📊 Название статьи затрат:"),
        Step("pct", "Процент от итога по позициям:", parse=_positive, quick=[("1", "1"), ("2", "2"), ("3", "3")]),
    ],
    "pay": [
        Step("amount", "💵 Сумма оплаты, ₽:", parse=_positive),
        Step("note", "📝 Комментарий (аванс, платёжка №…):", optional=True),
    ],
    "kp": [
        Step("term", "⏱ Срок выполнения (например «30 рабочих дней»):", optional=True),
        Step("warranty", "🛡 Гарантия (например «24 месяца»):", optional=True),
        Step("valid_days", "📅 Сколько дней действует предложение?", optional=True, parse=_positive,
             quick=[("7", "7"), ("14", "14"), ("30", "30")]),
    ],
    "tax_manual": [
        Step("revenue", "💰 Сумма договора (как в смете, с НДС если он есть), ₽:", parse=_positive),
        Step("materials", "🧱 Закупка материалов, ₽:", optional=True, parse=_number),
        Step("payroll", "👷 Оплата рабочим, ₽:", optional=True, parse=_number),
    ],
    # single-step inputs
    "works": [Step("text", "✍️ Напишите работы, по одной в строке:\n<code>штукатурка стен 120 м2\nстяжка пола 85 м2 по 700\nмат: керамогранит 22 м2</code>")],
    "fit": [Step("amount", "🎯 Под какую сумму подогнать итог, ₽?", parse=_positive)],
    "qty": [Step("value", "📏 Новый объём:", parse=_positive)],
    "price": [Step("value", "💬 Цена за единицу, ₽ (договорная, заменит расценку):", parse=_positive)],
    "crew": [Step("value", "👷 Ставка бригады за единицу, ₽:", parse=_number)],
    "done": [Step("value", "✅ Сколько выполнено? Объём, процент или «всё»:",
                  quick=[("25%", "25%"), ("50%", "50%"), ("75%", "75%"), ("100%", "всё")])],
    "contract": [Step("value", "📋 Номер и дата договора, например «№ 14 от 01.10.2026»:")],
    "crew_name": [Step("value", "👷 Бригада или бригадир (ФИО, телефон):")],
    "room": [Step("value", "📐 Помещение: название и размеры, например <code>кухня 4,2 3,1 2,7 д1 о1</code>")],
    "tax_annual": [Step("value", "📅 Ожидаемый доход за год, ₽ (для лимитов УСН и НДС):", parse=_positive)],
    "tax_target": [Step("value", "🎯 Сколько хотите получить на руки после налогов, ₽?", parse=_positive)],
    "promo": [Step("value", "🎟 Промокод:")],
    "rates_q": [Step("value", "🔎 Что найти в справочнике? Например «плитка» или шифр:")],
    "lost": [Step("value", "❌ Почему проиграли? (дорого, выбрали другого, отложили…)", optional=True,
                  quick=[("💸 Дорого", "дорого"), ("🤝 Выбрали другого", "выбрали другого"), ("⏸ Отложили", "отложили")])],
    "import": [Step("value", "📥 Пришлите файл: ФСНБ/ФЕР (XLSX, XML, DBF, ZIP), индексы ФГИС ЦС или прайс поставщика.")],
    "audit": [Step("value", "🔍 Пришлите файл сметы (Excel или CSV).")],
    "logo": [Step("value", "🖼 Пришлите логотип картинкой (PNG или JPG).")],
}
FILE_INPUTS = {"import", "audit", "logo"}


def wizard_prompt(kind: str, step_index: int) -> tuple[str, Markup]:
    steps = WIZARDS[kind]
    step = steps[step_index]
    counter = f"Шаг {step_index + 1} из {len(steps)}\n" if len(steps) > 1 else ""
    rows: Rows = []
    if step.quick:
        rows.append([(label, f"iv:{value}") for label, value in step.quick])
    nav = [("⬅️ Назад", "ib")]
    if step.optional:
        nav.append(("⏭ Пропустить", "is"))
    nav.append(("🏠 Меню", "hm"))
    rows.append(nav)
    return counter + step.prompt, kb(rows, nav=False)

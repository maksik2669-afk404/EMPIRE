"""Text rendering for Telegram (HTML parse mode). Kept free of aiogram so it stays testable."""
from __future__ import annotations

from html import escape

from .builder import FROM_PRICE_LIST, MATCHED, NEEDS_PRICE, PRICED, UNIT_MISMATCH, Match
from .model import MATERIAL, Company, Estimate
from .money import ZERO, qty_str, rub
from .profit import ProfitReport

MAX_POSITIONS = 25

START = (
    "🧮 <b>Сметчик</b> — считает смету из обычного текста.\n\n"
    "Напишите работы как говорите, одной строкой на работу:\n"
    "<code>штукатурка стен 120 м2\n"
    "стяжка пола 85 м2 по 700\n"
    "розетки 24 точки\n"
    "мат: керамогранит 22 м2 1550</code>\n\n"
    "Я найду расценку в справочнике, посчитаю накладные расходы, сметную прибыль и НДС, "
    "и отдам готовый файл с вашей шапкой (название, ИНН, номер сметы).\n\n"
    "1️⃣ /company — один раз заполнить шапку\n"
    "2️⃣ /new — начать смету\n"
    "3️⃣ вбить работы текстом\n"
    "4️⃣ /xlsx или /pdf — файл заказчику, /profit — маржа только для вас\n\n"
    "/help — все команды"
)

HELP = (
    "<b>Команды</b>\n"
    "/new — новая смета (объект, заказчик)\n"
    "/smeta — показать текущую смету\n"
    "/company — шапка: название, ИНН, КПП, адрес, телефон, подписант\n"
    "/xlsx, /pdf — файл для заказчика\n"
    "/profit — маржа и экономия на материалах (только вам)\n"
    "/cut 20 — срезать смету на 20% (<code>/cut 20 работы</code> — только работы)\n"
    "/up 15 — поднять на 15%\n"
    "/fit 900000 — подогнать итог под сумму\n"
    "/reset — убрать все корректировки\n"
    "/price 4 1500 — задать цену позиции № 4\n"
    "/qty 4 85 — изменить объём позиции № 4\n"
    "/del 4 — удалить позицию № 4\n"
    "/vat 0 — смета без НДС (УСН), /vat 20 — с НДС\n"
    "/nr off — не считать накладные расходы частью себестоимости (бригада)\n"
    "/rates плитка — поиск по справочнику расценок\n"
    "/import — загрузить свои расценки или прайс поставщика (CSV)\n"
    "/list — мои сметы, /open 12 — открыть смету\n\n"
    "Как вбивать работы: <code>наименование объём ед.изм. [по цене]</code>.\n"
    "Материал — строка с префиксом <code>мат:</code>.\n"
    "Размеры можно перемножить: <code>плитка 2,7х4,2 м2 х 1500</code>."
)


def company_text(company: Company) -> str:
    if not company.name and not company.inn:
        return "Шапка не заполнена. /company — заполнить."
    lines = ["<b>Шапка сметы</b>"]
    for label, value in (
        ("Организация", company.name),
        ("ИНН", company.inn),
        ("КПП", company.kpp),
        ("Адрес", company.address),
        ("Телефон", company.phone),
        ("Подписант", f"{company.signer_title} {company.signer}".strip()),
    ):
        lines.append(f"{label}: {escape(value) if value else '—'}")
    return "\n".join(lines)


def matches_text(matches: list[Match]) -> str:
    """What the parser understood - shown right after a text message with works."""
    if not matches:
        return (
            "Не понял ни одной строки. Формат: <code>наименование объём ед.изм.</code>, "
            "например <code>штукатурка стен 120 м2</code>."
        )
    lines = [f"Разобрал строк: {len(matches)}"]
    for match in matches:
        icon = {MATCHED: "✅", PRICED: "💬", FROM_PRICE_LIST: "🧾",
                UNIT_MISMATCH: "⚠️", NEEDS_PRICE: "❓"}.get(match.status, "•")
        lines.append(
            f"{icon} {escape(match.position.name)} — {qty_str(match.position.qty)} {match.position.unit}"
            + (f" · {escape(match.comment)}" if match.comment else "")
        )
    unmatched = [m for m in matches if m.status == NEEDS_PRICE]
    if unmatched:
        lines.append("")
        lines.append(
            "❓ Этих работ нет в справочнике. Задайте цену: <code>/price НОМЕР ЦЕНА</code> "
            "или допишите строку с ценой: <code>подшив сайдингом 30 м2 по 900</code>."
        )
    mismatched = [m for m in matches if m.status == UNIT_MISMATCH]
    if mismatched:
        lines.append("⚠️ Проверьте единицы измерения — расценка считается в другой единице.")
    return "\n".join(lines)


def estimate_text(estimate: Estimate, limit: int = MAX_POSITIONS) -> str:
    totals = estimate.totals()
    header = f"<b>Смета {escape(estimate.number) if estimate.number else ''}</b>".replace("  ", " ")
    lines = [header.strip()]
    if estimate.title:
        lines.append(escape(estimate.title))
    if estimate.customer:
        lines.append(f"Заказчик: {escape(estimate.customer)}")
    if estimate.object_name:
        lines.append(f"Объект: {escape(estimate.object_name)}")
    lines.append("")

    if not estimate.positions:
        lines.append("Позиций пока нет — вбейте работы текстом.")
        return "\n".join(lines)

    for index, position in enumerate(estimate.positions, 1):
        if index > limit:
            lines.append(f"… и ещё {len(estimate.positions) - limit} позиций (все — в файле)")
            break
        total = position.total(estimate.indices)
        mark = " ❓ нужна цена" if total <= ZERO else ""
        if position.kind == MATERIAL:
            mark += " 🧱"
        lines.append(
            f"<b>{index}.</b> {escape(position.name)}{mark}\n"
            f"    {qty_str(position.qty)} {position.unit} × {rub(position.unit_price_now(estimate.indices))} "
            f"= <b>{rub(total)}</b> ₽"
        )
    lines.append("")
    if totals.nr or totals.sp:
        lines.append(f"Прямые затраты: {rub(totals.direct)} ₽")
        if totals.nr:
            lines.append(f"Накладные расходы: {rub(totals.nr)} ₽")
        if totals.sp:
            lines.append(f"Сметная прибыль: {rub(totals.sp)} ₽")
    lines.append(f"Итого без НДС: {rub(totals.subtotal)} ₽")
    if estimate.vat_pct:
        lines.append(f"НДС {totals.vat_pct:g}%: {rub(totals.vat)} ₽")
    lines.append(f"<b>ВСЕГО: {rub(totals.total)} ₽</b>")

    discount = estimate.discount_pct()
    if discount:
        sign = "−" if discount < ZERO else "+"
        lines.append(f"Корректировка: {sign}{str(abs(discount)).replace('.', ',')}%")
    warnings = estimate.warnings()
    if warnings:
        lines.append("")
        lines.append("⚠️ " + "\n⚠️ ".join(escape(w) for w in warnings[:5]))
        if len(warnings) > 5:
            lines.append(f"… ещё {len(warnings) - 5} замечаний")
    return "\n".join(lines)


def profit_text(report: ProfitReport) -> str:
    return f"<pre>{escape(report.as_text())}</pre>"


def rates_text(found: list) -> str:
    if not found:
        return "Ничего не нашёл. Попробуйте другое слово или добавьте свою расценку через /import."
    lines = ["<b>Нашёл расценки</b>"]
    for rate, score in found:
        lines.append(
            f"<code>{escape(rate.code)}</code> {escape(rate.name)}\n"
            f"    {rate.unit} · ОТ {rub(rate.ot)} · ЭМ {rub(rate.em)} · МАТ {rub(rate.mat)} "
            f"· {escape(rate.work_type)} · {int(score * 100)}%"
        )
    lines.append("")
    lines.append("Чтобы взять расценку, впишите её шифр строкой: <code>ДЕМО-03.01 120 м2</code>")
    return "\n".join(lines)


def estimates_list_text(rows: list) -> str:
    if not rows:
        return "Смет пока нет. /new — создать."
    lines = ["<b>Мои сметы</b>"]
    for row in rows:
        lines.append(f"<code>/open {row['id']}</code> — {escape(row['number'] or '—')} {escape(row['title'] or '')}")
    return "\n".join(lines)

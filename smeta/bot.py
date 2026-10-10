"""Telegram interface for the estimate bot (aiogram 3)."""
from __future__ import annotations

import asyncio
import logging
import os
import re
from dataclasses import dataclass
from datetime import date
from io import BytesIO
from pathlib import Path

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command, CommandObject, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton as Btn,
    InlineKeyboardMarkup as Kb,
    Message,
)

from . import render
from .builder import build_from_text
from .catalog import Catalog
from .export_pdf import estimate_to_pdf
from .export_xlsx import estimate_to_xlsx, margin_to_xlsx
from .materials import OfferBook
from .model import Company, Estimate, MATERIAL, inn_is_valid
from .money import ZERO, dec, rub
from .profit import build_report
from .store import Store

log = logging.getLogger(__name__)
router = Router()
SKIP = {"-", "—", "нет", "пропустить", "skip"}


@dataclass
class Deps:
    store: Store
    catalog: Catalog
    offers: OfferBook
    export_dir: Path


class CompanyForm(StatesGroup):
    name = State()
    inn = State()
    kpp = State()
    address = State()
    phone = State()
    signer = State()


class NewForm(StatesGroup):
    object_name = State()
    customer = State()


class FitForm(StatesGroup):
    amount = State()


def keyboard() -> Kb:
    return Kb(inline_keyboard=[
        [Btn(text="−10%", callback_data="cut:10"), Btn(text="−20%", callback_data="cut:20"),
         Btn(text="−30%", callback_data="cut:30")],
        [Btn(text="+10%", callback_data="up:10"), Btn(text="🎯 под сумму", callback_data="fit"),
         Btn(text="♻️ сброс", callback_data="reset")],
        [Btn(text="📄 Excel", callback_data="xlsx"), Btn(text="📕 PDF", callback_data="pdf")],
        [Btn(text="💰 Профит (только мне)", callback_data="profit")],
    ])


# ---------- estimate helpers ----------


def _new_estimate(deps: Deps, tg_id: int, *, object_name: str = "", customer: str = "") -> Estimate:
    settings = deps.store.settings(tg_id)
    catalog = deps.store.catalog(tg_id, deps.catalog)
    return Estimate(
        number=deps.store.next_number(tg_id),
        title="Локальная смета",
        customer=customer,
        object_name=object_name,
        date=date.today(),
        company=deps.store.company(tg_id),
        indices=catalog.index(settings["index_name"] or None),
        vat_pct=settings["vat_pct"],
        floor_with_nr=settings["floor_with_nr"],
        basis="договорные цены / справочник расценок",
    )


def _current(deps: Deps, tg_id: int) -> tuple[int, Estimate] | None:
    settings = deps.store.settings(tg_id)
    estimate_id = settings["current_id"]
    if not estimate_id:
        return None
    estimate = deps.store.load_estimate(tg_id, int(estimate_id))
    return (int(estimate_id), estimate) if estimate else None


def _require(deps: Deps, tg_id: int) -> tuple[int, Estimate]:
    found = _current(deps, tg_id)
    if found:
        return found
    estimate = _new_estimate(deps, tg_id)
    estimate_id = deps.store.save_estimate(tg_id, estimate)
    deps.store.update_settings(tg_id, current_id=estimate_id)
    return estimate_id, estimate


def _save(deps: Deps, tg_id: int, estimate_id: int, estimate: Estimate) -> None:
    deps.store.save_estimate(tg_id, estimate, estimate_id)


def _safe_name(text: str) -> str:
    return re.sub(r"[^\w\-. ]+", "_", text, flags=re.U).strip() or "smeta"


# ---------- basics ----------


@router.message(CommandStart())
async def cmd_start(message: Message, deps: Deps) -> None:
    deps.store.user(message.from_user.id)
    await message.answer(render.START)


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(render.HELP)


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Отменил.")


# ---------- company header ----------


@router.message(Command("company"))
async def cmd_company(message: Message, state: FSMContext, deps: Deps) -> None:
    await message.answer(render.company_text(deps.store.company(message.from_user.id)))
    await state.set_state(CompanyForm.name)
    await message.answer("Название организации или ИП (как в документах):")


@router.message(CompanyForm.name)
async def form_name(message: Message, state: FSMContext) -> None:
    await state.update_data(name=(message.text or "").strip())
    await state.set_state(CompanyForm.inn)
    await message.answer("ИНН (10 или 12 цифр):")


@router.message(CompanyForm.inn)
async def form_inn(message: Message, state: FSMContext) -> None:
    inn = re.sub(r"\D", "", message.text or "")
    if not inn_is_valid(inn):
        await message.answer("Это не похоже на ИНН — контрольная сумма не сходится. Введите ещё раз или «-»:")
        if (message.text or "").strip().lower() not in SKIP:
            return
        inn = ""
    await state.update_data(inn=inn)
    await state.set_state(CompanyForm.kpp)
    await message.answer("КПП (или «-», если ИП):")


@router.message(CompanyForm.kpp)
async def form_kpp(message: Message, state: FSMContext) -> None:
    value = (message.text or "").strip()
    await state.update_data(kpp="" if value.lower() in SKIP else value)
    await state.set_state(CompanyForm.address)
    await message.answer("Адрес (или «-»):")


@router.message(CompanyForm.address)
async def form_address(message: Message, state: FSMContext) -> None:
    value = (message.text or "").strip()
    await state.update_data(address="" if value.lower() in SKIP else value)
    await state.set_state(CompanyForm.phone)
    await message.answer("Телефон (или «-»):")


@router.message(CompanyForm.phone)
async def form_phone(message: Message, state: FSMContext) -> None:
    value = (message.text or "").strip()
    await state.update_data(phone="" if value.lower() in SKIP else value)
    await state.set_state(CompanyForm.signer)
    await message.answer("Кто подписывает смету — должность и ФИО (например «Директор Иванов И.И.»):")


@router.message(CompanyForm.signer)
async def form_signer(message: Message, state: FSMContext, deps: Deps) -> None:
    raw = (message.text or "").strip()
    title, _, name = raw.partition(" ")
    data = await state.get_data()
    await state.clear()
    company = Company(
        name=data.get("name", ""),
        inn=data.get("inn", ""),
        kpp=data.get("kpp", ""),
        address=data.get("address", ""),
        phone=data.get("phone", ""),
        signer=name.strip() or raw,
        signer_title=title.strip() if name else "Директор",
    )
    deps.store.save_company(message.from_user.id, company)
    found = _current(deps, message.from_user.id)
    if found:
        estimate_id, estimate = found
        estimate.company = company
        _save(deps, message.from_user.id, estimate_id, estimate)
    await message.answer("Шапка сохранена.\n\n" + render.company_text(company))
    await message.answer("Теперь /new — начать смету, или сразу вбивайте работы текстом.")


# ---------- new estimate ----------


@router.message(Command("new"))
async def cmd_new(message: Message, state: FSMContext) -> None:
    await state.set_state(NewForm.object_name)
    await message.answer("Объект (адрес или название, «-» чтобы пропустить):")


@router.message(NewForm.object_name)
async def form_object(message: Message, state: FSMContext) -> None:
    value = (message.text or "").strip()
    await state.update_data(object_name="" if value.lower() in SKIP else value)
    await state.set_state(NewForm.customer)
    await message.answer("Заказчик (название и ИНН, «-» чтобы пропустить):")


@router.message(NewForm.customer)
async def form_customer(message: Message, state: FSMContext, deps: Deps) -> None:
    value = (message.text or "").strip()
    data = await state.get_data()
    await state.clear()
    tg_id = message.from_user.id
    estimate = _new_estimate(
        deps, tg_id,
        object_name=data.get("object_name", ""),
        customer="" if value.lower() in SKIP else value,
    )
    estimate_id = deps.store.save_estimate(tg_id, estimate)
    deps.store.update_settings(tg_id, current_id=estimate_id)
    await message.answer(
        f"Смета {estimate.number} создана. Вбивайте работы — по одной в строке:\n"
        "<code>штукатурка стен 120 м2\nстяжка пола 85 м2 по 700\nмат: керамогранит 22 м2 1550</code>"
    )


# ---------- adding positions from free text ----------


# StateFilter(None): во время диалогов (/company, /new, подгон под сумму) текст идёт в них
@router.message(StateFilter(None), F.text, ~F.text.startswith("/"))
async def add_positions(message: Message, deps: Deps) -> None:
    tg_id = message.from_user.id
    estimate_id, estimate = _require(deps, tg_id)
    catalog = deps.store.catalog(tg_id, deps.catalog)
    matches = build_from_text(message.text or "", catalog, offers=deps.store.offers(tg_id, deps.offers))
    if not matches:
        await message.answer(render.matches_text(matches))
        return
    for match in matches:
        estimate.add(match.position)
    _save(deps, tg_id, estimate_id, estimate)
    await message.answer(render.matches_text(matches))
    await message.answer(render.estimate_text(estimate), reply_markup=keyboard())


@router.message(Command("smeta"))
async def cmd_smeta(message: Message, deps: Deps) -> None:
    found = _current(deps, message.from_user.id)
    if not found:
        await message.answer("Текущей сметы нет. /new — создать.")
        return
    await message.answer(render.estimate_text(found[1]), reply_markup=keyboard())


# ---------- editing ----------


async def _apply_and_show(message: Message, deps: Deps, estimate_id: int, estimate: Estimate) -> None:
    _save(deps, message.from_user.id, estimate_id, estimate)
    await message.answer(render.estimate_text(estimate), reply_markup=keyboard())


@router.message(Command("cut", "up"))
async def cmd_cut(message: Message, command: CommandObject, deps: Deps) -> None:
    found = _current(deps, message.from_user.id)
    if not found:
        await message.answer("Сметы нет. /new")
        return
    estimate_id, estimate = found
    args = (command.args or "").split()
    if not args:
        await message.answer("Сколько процентов? Например: <code>/cut 20</code> или <code>/cut 20 работы</code>")
        return
    percent = dec(args[0].replace("%", ""))
    scope = "all"
    if len(args) > 1:
        word = args[1].lower()
        scope = {"работы": "work", "работа": "work", "материалы": MATERIAL, "материал": MATERIAL,
                 "оборудование": "equipment"}.get(word, "all")
    try:
        estimate.adjust(-percent if command.command == "cut" else percent, scope)
    except ValueError as error:
        await message.answer(str(error))
        return
    await _apply_and_show(message, deps, estimate_id, estimate)


@router.message(Command("fit"))
async def cmd_fit(message: Message, command: CommandObject, deps: Deps, state: FSMContext) -> None:
    found = _current(deps, message.from_user.id)
    if not found:
        await message.answer("Сметы нет. /new")
        return
    if not (command.args or "").strip():
        await state.set_state(FitForm.amount)
        await message.answer("Под какую сумму подогнать итог? Напишите число:")
        return
    await _fit(message, deps, found, command.args)


@router.message(FitForm.amount)
async def form_fit(message: Message, deps: Deps, state: FSMContext) -> None:
    await state.clear()
    found = _current(deps, message.from_user.id)
    if found:
        await _fit(message, deps, found, message.text or "")


async def _fit(message: Message, deps: Deps, found: tuple[int, Estimate], raw: str) -> None:
    estimate_id, estimate = found
    target = dec((raw or "").replace(" ", "").replace("₽", ""))
    try:
        estimate.fit_to(target)
    except ValueError as error:
        await message.answer(str(error))
        return
    await _apply_and_show(message, deps, estimate_id, estimate)


@router.message(Command("reset"))
async def cmd_reset(message: Message, deps: Deps) -> None:
    found = _current(deps, message.from_user.id)
    if not found:
        await message.answer("Сметы нет. /new")
        return
    estimate_id, estimate = found
    estimate.reset_adjustments()
    await _apply_and_show(message, deps, estimate_id, estimate)


@router.message(Command("price", "qty"))
async def cmd_price(message: Message, command: CommandObject, deps: Deps) -> None:
    found = _current(deps, message.from_user.id)
    if not found:
        await message.answer("Сметы нет. /new")
        return
    estimate_id, estimate = found
    args = (command.args or "").split()
    if len(args) < 2:
        example = "/price 4 1500" if command.command == "price" else "/qty 4 85"
        await message.answer(f"Формат: <code>{example}</code>")
        return
    try:
        index = int(args[0])
    except ValueError:
        await message.answer("Первым числом — номер позиции из списка.")
        return
    if not 1 <= index <= len(estimate.positions):
        await message.answer(f"Нет позиции № {index}.")
        return
    position = estimate.positions[index - 1]
    value = dec(args[1])
    if command.command == "qty":
        position.qty = value
    else:
        position.unit_price = value
        position.adj = dec(1)
        position.ot = position.em = position.zpm = position.mat = ZERO
        position.nr_pct = position.sp_pct = ZERO
        position.code = ""
    await _apply_and_show(message, deps, estimate_id, estimate)


@router.message(Command("del"))
async def cmd_del(message: Message, command: CommandObject, deps: Deps) -> None:
    found = _current(deps, message.from_user.id)
    if not found:
        await message.answer("Сметы нет. /new")
        return
    estimate_id, estimate = found
    try:
        index = int((command.args or "").strip())
    except ValueError:
        await message.answer("Формат: <code>/del 4</code>")
        return
    removed = estimate.remove(index)
    if not removed:
        await message.answer(f"Нет позиции № {index}.")
        return
    await message.answer(f"Удалил: {removed.name}")
    await _apply_and_show(message, deps, estimate_id, estimate)


@router.message(Command("vat"))
async def cmd_vat(message: Message, command: CommandObject, deps: Deps) -> None:
    value = dec((command.args or "").replace("%", "").strip())
    deps.store.update_settings(message.from_user.id, vat_pct=value)
    found = _current(deps, message.from_user.id)
    if found:
        estimate_id, estimate = found
        estimate.vat_pct = value
        await _apply_and_show(message, deps, estimate_id, estimate)
        return
    await message.answer(f"НДС: {value:g}%")


@router.message(Command("nr"))
async def cmd_nr(message: Message, command: CommandObject, deps: Deps) -> None:
    flag = (command.args or "").strip().lower() not in {"off", "нет", "0", "выкл"}
    deps.store.update_settings(message.from_user.id, floor_with_nr=flag)
    found = _current(deps, message.from_user.id)
    if found:
        estimate_id, estimate = found
        estimate.floor_with_nr = flag
        _save(deps, message.from_user.id, estimate_id, estimate)
    await message.answer(
        "Накладные расходы считаю частью себестоимости (вариант для организации с офисом)."
        if flag else
        "Накладные расходы в себестоимость не включаю (вариант для бригады)."
    )


# ---------- catalog ----------


@router.message(Command("rates"))
async def cmd_rates(message: Message, command: CommandObject, deps: Deps) -> None:
    query = (command.args or "").strip()
    if not query:
        await message.answer("Что искать? Например: <code>/rates плитка</code>")
        return
    catalog = deps.store.catalog(message.from_user.id, deps.catalog)
    await message.answer(render.rates_text(catalog.search(query, limit=5)))


@router.message(Command("import"))
async def cmd_import(message: Message, deps: Deps) -> None:
    tg_id = message.from_user.id
    rates = deps.store.imports(tg_id, "rates")
    offers = deps.store.imports(tg_id, "offers")
    lines = [
        "<b>Импорт CSV</b>",
        "Пришлите файлом (.csv, разделитель «;»).",
        "",
        "Расценки: <code>Шифр;Наименование;Ед.изм.;ОТ;ЭМ;ЗПМ;МАТ;ТЗ;Вид работ</code>",
        "Прайс поставщика: <code>material;unit;price;discount;retail;supplier;payment</code>",
        "",
        f"Загружено: расценок — {sum(r['rows'] for r in rates)}, строк прайса — {sum(r['rows'] for r in offers)}",
        "/import_clear — удалить всё загруженное",
    ]
    await message.answer("\n".join(lines))


@router.message(Command("import_clear"))
async def cmd_import_clear(message: Message, deps: Deps) -> None:
    tg_id = message.from_user.id
    removed = deps.store.drop_imports(tg_id, "rates") + deps.store.drop_imports(tg_id, "offers")
    await message.answer(f"Удалил загруженных файлов: {removed}.")


@router.message(F.document)
async def got_document(message: Message, deps: Deps, bot: Bot) -> None:
    document = message.document
    name = document.file_name or "import.csv"
    if not name.lower().endswith((".csv", ".txt")):
        await message.answer("Нужен CSV (.csv или .txt), разделитель «;».")
        return
    if (document.file_size or 0) > 5 * 1024 * 1024:
        await message.answer("Файл больше 5 МБ — разбейте на части.")
        return
    buffer = BytesIO()
    await bot.download(document, destination=buffer)
    raw = buffer.getvalue()
    for encoding in ("utf-8-sig", "utf-8", "cp1251"):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        await message.answer("Не смог прочитать файл: сохраните его в UTF-8 или Windows-1251.")
        return

    kind, count = _detect_import(text)
    if not count:
        await message.answer(
            "Не нашёл в файле ни расценок, ни строк прайса. Проверьте заголовок столбцов — /import."
        )
        return
    deps.store.add_import(message.from_user.id, kind, name, text, count)
    what = "расценок" if kind == "rates" else "строк прайса"
    await message.answer(f"Загрузил {count} {what} из «{name}». Теперь они используются первыми.")


def _detect_import(text: str) -> tuple[str, int]:
    """Guess whether a CSV is a rate catalog or a supplier price list."""
    head = "\n".join(text.splitlines()[:6]).lower()
    if any(word in head for word in ("скидка", "discount", "поставщик", "supplier", "розница", "retail")):
        return "offers", len(OfferBook.from_csv(text).offers)
    try:
        return "rates", len(Catalog.from_csv(text).rates)
    except ValueError:
        return "offers", len(OfferBook.from_csv(text).offers)


# ---------- files ----------


async def _send_files(message: Message, deps: Deps, estimate: Estimate, kind: str) -> None:
    warnings = estimate.warnings()
    if not estimate.positions:
        await message.answer("В смете нет позиций.")
        return
    stem = _safe_name(f"Смета_{estimate.number or estimate.date.isoformat()}")
    deps.export_dir.mkdir(parents=True, exist_ok=True)
    path = deps.export_dir / f"{stem}.{'xlsx' if kind == 'xlsx' else 'pdf'}"
    if kind == "xlsx":
        estimate_to_xlsx(estimate, path)
    else:
        estimate_to_pdf(estimate, path)
    caption = f"Итого по смете: {rub(estimate.total())} ₽"
    if warnings:
        caption += "\n⚠️ " + warnings[0]
    await message.answer_document(FSInputFile(path), caption=caption)
    path.unlink(missing_ok=True)


@router.message(Command("xlsx", "excel"))
async def cmd_xlsx(message: Message, deps: Deps) -> None:
    found = _current(deps, message.from_user.id)
    if not found:
        await message.answer("Сметы нет. /new")
        return
    await _send_files(message, deps, found[1], "xlsx")


@router.message(Command("pdf"))
async def cmd_pdf(message: Message, deps: Deps) -> None:
    found = _current(deps, message.from_user.id)
    if not found:
        await message.answer("Сметы нет. /new")
        return
    await _send_files(message, deps, found[1], "pdf")


@router.message(Command("profit"))
async def cmd_profit(message: Message, deps: Deps) -> None:
    found = _current(deps, message.from_user.id)
    if not found:
        await message.answer("Сметы нет. /new")
        return
    offers = deps.store.offers(message.from_user.id, deps.offers)
    report = build_report(found[1], offers)
    await message.answer(
        render.profit_text(report),
        reply_markup=Kb(inline_keyboard=[[Btn(text="📥 Файл с расчётом маржи", callback_data="profit_file")]]),
    )


# ---------- estimates list ----------


@router.message(Command("list"))
async def cmd_list(message: Message, deps: Deps) -> None:
    await message.answer(render.estimates_list_text(deps.store.list_estimates(message.from_user.id)))


@router.message(Command("open"))
async def cmd_open(message: Message, command: CommandObject, deps: Deps) -> None:
    try:
        estimate_id = int((command.args or "").strip())
    except ValueError:
        await message.answer("Формат: <code>/open 12</code> (номера — в /list)")
        return
    estimate = deps.store.load_estimate(message.from_user.id, estimate_id)
    if not estimate:
        await message.answer("Такой сметы нет.")
        return
    deps.store.update_settings(message.from_user.id, current_id=estimate_id)
    await message.answer(render.estimate_text(estimate), reply_markup=keyboard())


# ---------- callbacks ----------


@router.callback_query(F.data)
async def on_callback(call: CallbackQuery, deps: Deps, state: FSMContext) -> None:
    tg_id = call.from_user.id
    action = call.data or ""
    found = _current(deps, tg_id)
    if not found:
        await call.answer("Сметы нет", show_alert=True)
        return
    estimate_id, estimate = found

    if action.startswith(("cut:", "up:")):
        percent = dec(action.split(":", 1)[1])
        estimate.adjust(-percent if action.startswith("cut:") else percent)
        _save(deps, tg_id, estimate_id, estimate)
        await call.message.answer(render.estimate_text(estimate), reply_markup=keyboard())
    elif action == "reset":
        estimate.reset_adjustments()
        _save(deps, tg_id, estimate_id, estimate)
        await call.message.answer(render.estimate_text(estimate), reply_markup=keyboard())
    elif action == "fit":
        await state.set_state(FitForm.amount)
        await call.message.answer("Под какую сумму подогнать итог? Напишите число:")
    elif action in {"xlsx", "pdf"}:
        await _send_files(call.message, deps, estimate, action)
    elif action == "profit":
        report = build_report(estimate, deps.store.offers(tg_id, deps.offers))
        await call.message.answer(
            render.profit_text(report),
            reply_markup=Kb(inline_keyboard=[[Btn(text="📥 Файл с расчётом маржи", callback_data="profit_file")]]),
        )
    elif action == "profit_file":
        report = build_report(estimate, deps.store.offers(tg_id, deps.offers))
        deps.export_dir.mkdir(parents=True, exist_ok=True)
        path = deps.export_dir / _safe_name(f"Профит_{estimate.number}.xlsx")
        margin_to_xlsx(report, path, estimate)
        await call.message.answer_document(
            FSInputFile(path), caption="Только для вас. Заказчику этот файл не отправляют."
        )
        path.unlink(missing_ok=True)
    await call.answer()


# ---------- entry point ----------


def build_deps() -> Deps:
    base = Catalog.load()
    offers_path = Path(os.getenv("SMETA_OFFERS", "data/suppliers/demo.csv"))
    return Deps(
        store=Store(os.getenv("SMETA_DB_PATH", "data/smeta.db")),
        catalog=base,
        offers=OfferBook.load(offers_path),
        export_dir=Path(os.getenv("SMETA_EXPORT_DIR", "data/export")),
    )


async def run() -> None:
    token = os.getenv("SMETA_BOT_TOKEN") or os.getenv("BOT_TOKEN") or ""
    if not token:
        raise SystemExit("Нет токена: SMETA_BOT_TOKEN=... (получить у @BotFather)")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    deps = build_deps()
    bot = Bot(token, default=DefaultBotProperties(parse_mode="HTML"))
    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher.include_router(router)
    log.info("расценок: %s, прайс: %s", len(deps.catalog.rates), len(deps.offers.offers))
    try:
        await dispatcher.start_polling(bot, deps=deps)
    finally:
        deps.store.close()
        await bot.session.close()


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()

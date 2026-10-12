"""Command line: text in -> XLSX/PDF out. Lets you see the result without a Telegram token.

    python3 -m smeta.cli --demo
    python3 -m smeta.cli works.txt --company "ООО СтройПро" --inn 7707083893 --cut 20 --profit
    echo "штукатурка стен 120 м2" | python3 -m smeta.cli -
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from .builder import build_from_text
from .catalog import Catalog
from .export_pdf import estimate_to_pdf
from .export_xlsx import estimate_to_xlsx, margin_to_xlsx
from .materials import OfferBook
from .model import Company, Estimate
from .money import dec, rub
from .profit import build_report

DEMO = """штукатурка стен 120 м2
шпаклевка стен 120 м2
покраска стен 120 м2
стяжка пола 85 м2
плитка на пол 20 м2
розетки 24 точки
натяжной потолок 85 м2
вывоз мусора 3 т
подшив сайдингом 30 м2 по 900
мат: керамогранит 22 м2 1550
мат: штукатурка гипсовая 30 кг 170 шт 650
мат: кабель ввг 180 м 135
"""


def _plain(text: str) -> str:
    """Strip the Telegram HTML tags - the CLI prints to a terminal."""
    import re

    return re.sub(r"<[^>]+>", "", text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="smeta", description="Сметчик: текст -> смета в XLSX и PDF")
    parser.add_argument("source", nargs="?", help="файл с работами, '-' для stdin")
    parser.add_argument("--demo", action="store_true", help="посчитать демо-смету")
    parser.add_argument("--out", default="data/export", help="куда положить файлы")
    parser.add_argument("--rates", help="CSV со своими расценками (ФЕР)")
    parser.add_argument("--offers", default="data/suppliers/demo.csv", help="CSV с прайсом поставщиков")
    parser.add_argument("--company", default="", help="название организации для шапки")
    parser.add_argument("--inn", default="", help="ИНН")
    parser.add_argument("--kpp", default="")
    parser.add_argument("--phone", default="")
    parser.add_argument("--signer", default="", help="ФИО подписанта")
    parser.add_argument("--number", default="", help="номер сметы")
    parser.add_argument("--title", default="Локальная смета")
    parser.add_argument("--customer", default="")
    parser.add_argument("--object", dest="object_name", default="")
    parser.add_argument("--index", default="", help="название индекса пересчёта из data/rates/indices.csv")
    parser.add_argument("--vat", default="20", help="НДС, %% (0 для УСН)")
    parser.add_argument("--cut", default="0", help="срезать смету на N %%")
    parser.add_argument("--fit", default="", help="подогнать итог под сумму")
    parser.add_argument("--no-nr-in-cost", action="store_true", help="не включать накладные в себестоимость")
    parser.add_argument("--profit", action="store_true", help="показать маржу и выгрузить внутренний файл")
    args = parser.parse_args(argv)

    if args.demo:
        text = DEMO
    elif args.source == "-":
        text = sys.stdin.read()
    elif args.source:
        text = Path(args.source).read_text(encoding="utf-8")
    else:
        parser.print_help()
        return 2

    catalog = Catalog.load()
    if args.rates:
        catalog.extend(Catalog.from_csv(Path(args.rates).read_text(encoding="utf-8"), source=args.rates))
    offers = OfferBook.load(args.offers)

    estimate = Estimate(
        number=args.number or f"СМ-{date.today().year}-0001",
        title=args.title,
        customer=args.customer,
        object_name=args.object_name,
        company=Company(
            name=args.company, inn=args.inn, kpp=args.kpp, phone=args.phone,
            signer=args.signer, signer_title="Директор",
        ),
        indices=catalog.index(args.index or None),
        vat_pct=dec(args.vat),
        floor_with_nr=not args.no_nr_in_cost,
        basis="справочник расценок / договорные цены",
    )
    matches = build_from_text(text, catalog, offers=offers)
    for match in matches:
        estimate.add(match.position)

    from . import render

    print(_plain(render.matches_text(matches)))
    if dec(args.cut):
        estimate.adjust(-dec(args.cut))
    if args.fit:
        estimate.fit_to(dec(args.fit))
    print()
    print(_plain(render.estimate_text(estimate, limit=100)))

    out = Path(args.out)
    xlsx = estimate_to_xlsx(estimate, out / f"{estimate.number}.xlsx")
    pdf = estimate_to_pdf(estimate, out / f"{estimate.number}.pdf")
    print()
    print(f"Файлы: {xlsx}, {pdf}")

    if args.profit:
        report = build_report(estimate, offers)
        print()
        print(report.as_text())
        margin = margin_to_xlsx(report, out / f"{estimate.number}-профит.xlsx", estimate)
        print(f"Внутренний файл: {margin}")
    print(f"\nИтого к оплате: {rub(estimate.total())} ₽")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

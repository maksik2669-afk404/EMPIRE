"""PDF export of the customer-facing estimate (A4 landscape, Cyrillic font embedded)."""
from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .model import MATERIAL, Estimate
from .money import qty_str, rub

FONT = "DejaVuSans"
FONT_BOLD = "DejaVuSans-Bold"
_FONT_DIRS = (
    "/usr/share/fonts/truetype/dejavu",
    "/usr/share/fonts/dejavu",
    "/Library/Fonts",
    "C:/Windows/Fonts",
)
_registered = False


def _register_fonts() -> tuple[str, str]:
    """Register DejaVu (ships with most distros). Falls back to Helvetica without Cyrillic."""
    global _registered
    if _registered:
        return FONT, FONT_BOLD
    for directory in _FONT_DIRS:
        regular = Path(directory) / "DejaVuSans.ttf"
        bold = Path(directory) / "DejaVuSans-Bold.ttf"
        if regular.exists():
            pdfmetrics.registerFont(TTFont(FONT, str(regular)))
            pdfmetrics.registerFont(TTFont(FONT_BOLD, str(bold if bold.exists() else regular)))
            _registered = True
            return FONT, FONT_BOLD
    return "Helvetica", "Helvetica-Bold"


def estimate_to_pdf(estimate: Estimate, path: str | Path) -> Path:
    font, font_bold = _register_fonts()
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(out),
        pagesize=landscape(A4),
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
        title=f"Смета {estimate.number}".strip(),
        author=estimate.company.name,
    )
    base = getSampleStyleSheet()["Normal"]
    small = ParagraphStyle("small", parent=base, fontName=font, fontSize=8, leading=10)
    cell = ParagraphStyle("cell", parent=small, fontSize=8)
    right = ParagraphStyle("right", parent=small, alignment=TA_RIGHT)
    head = ParagraphStyle("head", parent=small, fontName=font_bold, fontSize=8, alignment=TA_CENTER)
    title = ParagraphStyle("title", parent=base, fontName=font_bold, fontSize=14, alignment=TA_CENTER, spaceAfter=4)
    sub = ParagraphStyle("sub", parent=base, fontName=font, fontSize=10, alignment=TA_CENTER, spaceAfter=6)

    story: list = []
    for index, line in enumerate(estimate.company.header_lines()):
        story.append(Paragraph(line, ParagraphStyle(
            f"h{index}", parent=small, fontName=font_bold if index == 0 else font, fontSize=10 if index == 0 else 8)))
    story.append(Spacer(1, 6 * mm))
    number = f" № {estimate.number}" if estimate.number else ""
    story.append(Paragraph(f"ЛОКАЛЬНАЯ СМЕТА{number}", title))
    if estimate.title:
        story.append(Paragraph(estimate.title, sub))
    meta = [
        ("Заказчик", estimate.customer),
        ("Объект", estimate.object_name),
        ("Основание", estimate.basis),
        ("Уровень цен", f"{estimate.indices.region} {estimate.indices.period}".strip()),
        ("Дата", estimate.date.strftime("%d.%m.%Y")),
    ]
    for label, value in meta:
        if value:
            story.append(Paragraph(f"<b>{label}:</b> {value}", small))
    story.append(Spacer(1, 4 * mm))

    data = [[
        Paragraph("№", head), Paragraph("Обоснование", head), Paragraph("Наименование работ и затрат", head),
        Paragraph("Ед.", head), Paragraph("Кол-во", head), Paragraph("Цена, ₽", head), Paragraph("Всего, ₽", head),
    ]]
    section_rows: list[int] = []
    counter = 0
    sections = estimate.sections()
    for name, positions in sections:
        if name and len(sections) > 1:
            section_rows.append(len(data))
            data.append([Paragraph(f"<b>{name}</b>", cell), "", "", "", "", "", ""])
        for position in positions:
            counter += 1
            note = " (материал)" if position.kind == MATERIAL else ""
            data.append([
                Paragraph(str(counter), cell),
                Paragraph(position.code or "договорная", cell),
                Paragraph(f"{position.name}{note}", cell),
                Paragraph(position.unit, cell),
                Paragraph(qty_str(position.qty), right),
                Paragraph(rub(position.unit_price_now(estimate.indices)), right),
                Paragraph(rub(position.total(estimate.indices)), right),
            ])

    widths = [12 * mm, 30 * mm, 118 * mm, 16 * mm, 20 * mm, 28 * mm, 30 * mm]
    table = Table(data, colWidths=widths, repeatRows=1)
    style = [
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#808080")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EFEFEF")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
    ]
    for row in section_rows:
        style.append(("SPAN", (0, row), (-1, row)))
        style.append(("BACKGROUND", (0, row), (-1, row), colors.HexColor("#F5F5F5")))
    table.setStyle(TableStyle(style))
    story.append(table)
    story.append(Spacer(1, 4 * mm))

    totals = estimate.totals()
    rows: list[tuple[str, object, bool]] = [("Прямые затраты, всего", totals.direct, True)]
    for label, value in (
        ("в том числе оплата труда рабочих", totals.ot),
        ("эксплуатация машин и механизмов", totals.em),
        ("материалы и изделия", totals.mat),
        ("работы и затраты по договорным ценам", totals.other),
        ("Накладные расходы", totals.nr),
        ("Сметная прибыль", totals.sp),
    ):
        if value:
            rows.append((label, value, False))
    rows.append(("Итого без НДС", totals.subtotal, True))
    if estimate.vat_pct:
        rows.append((f"НДС {totals.vat_pct:g}%", totals.vat, False))
    rows.append(("ВСЕГО по смете", totals.total, True))

    totals_data = [[
        Paragraph(f"<b>{label}</b>" if bold else label, right),
        Paragraph(f"<b>{rub(value)}</b>" if bold else rub(value), right),
    ] for label, value, bold in rows]
    totals_table = Table(totals_data, colWidths=[sum(widths[:6]), widths[6]])
    totals_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#808080")),
        ("BACKGROUND", (1, 0), (1, -1), colors.HexColor("#F7F7F7")),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(totals_table)
    if totals.tz:
        story.append(Spacer(1, 2 * mm))
        story.append(Paragraph(f"Справочно: затраты труда {float(totals.tz):.1f} чел.-ч", small))

    story.append(Spacer(1, 10 * mm))
    signer = estimate.company.signer or ""
    sign = Table(
        [[Paragraph(f"Составил: {estimate.company.signer_title} ______________ {signer}", small),
          Paragraph("Заказчик: ______________", small)]],
        colWidths=[sum(widths) / 2, sum(widths) / 2],
    )
    story.append(sign)
    doc.build(story)
    return out

"""Сметы по шаблонам: несколько чисел про объект -> готовый набор работ с объёмами."""
from __future__ import annotations

import ast
import math
from decimal import Decimal

from . import datafiles
from .builder import Match, build
from .catalog import Catalog
from .materials import OfferBook
from .model import MATERIAL, WORK
from .money import ZERO, dec, money
from .obmer import DOOR_H, DOOR_W, WIN_H, WIN_W
from .parser import DraftLine

_FUNCS = {"ceil": math.ceil, "floor": math.floor, "max": max, "min": min, "round": round}


def safe_eval(expression: str, variables: dict[str, Decimal]) -> Decimal:
    """Arithmetic only: numbers, the variables, + - * / ** and ceil/floor/max/min/round."""
    tree = ast.parse(expression.replace(",", ".") if "(" not in expression else expression, mode="eval")

    def walk(node):
        if isinstance(node, ast.Expression):
            return walk(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return Decimal(str(node.value))
        if isinstance(node, ast.Name):
            if node.id not in variables:
                raise ValueError(f"неизвестная переменная {node.id}")
            return dec(variables[node.id])
        if isinstance(node, ast.BinOp):
            left, right = walk(node.left), walk(node.right)
            ops = {ast.Add: lambda: left + right, ast.Sub: lambda: left - right,
                   ast.Mult: lambda: left * right, ast.Div: lambda: left / right,
                   ast.Pow: lambda: left ** right}
            if type(node.op) not in ops:
                raise ValueError("недопустимая операция")
            return ops[type(node.op)]()
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
            value = walk(node.operand)
            return -value if isinstance(node.op, ast.USub) else value
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in _FUNCS:
            args = [walk(arg) for arg in node.args]
            return dec(_FUNCS[node.func.id](*args))
        raise ValueError("недопустимое выражение в шаблоне")

    return dec(walk(tree))


def catalog_of_templates() -> dict[str, dict]:
    """code -> {"title", "lines": [row, ...]}"""
    out: dict[str, dict] = {}
    for row in datafiles.templates():
        code = row.get("template", "")
        if not code:
            continue
        entry = out.setdefault(code, {"title": row.get("title", code), "lines": []})
        entry["lines"].append(row)
    return out


def variables(area, height, rooms=1, baths=0, perimeter=None, doors=None, windows=None) -> tuple[dict[str, Decimal], list[str]]:
    """Derive every template variable from a few numbers. Returns (vars, assumptions)."""
    S, H = dec(area), dec(height)
    R, N = dec(rooms) or Decimal(1), dec(baths)
    notes: list[str] = []
    if S <= ZERO or H <= ZERO:
        raise ValueError("площадь и высота должны быть больше нуля")
    if perimeter in (None, "", ZERO):
        side = Decimal(math.sqrt(float(S / (R + N if R + N else 1))))
        P = money(side * 4 * (R + N if R + N else 1))
        notes.append(f"периметр оценён как у квадратных комнат: {P} м — для точности введите его или сделайте обмер")
    else:
        P = dec(perimeter)
    D = dec(doors) if doors not in (None, "") else R + N
    O = dec(windows) if windows not in (None, "") else R
    if doors in (None, ""):
        notes.append(f"дверей принято {D} (по комнате и санузлу)")
    if windows in (None, ""):
        notes.append(f"окон принято {O} (по одному на комнату)")
    W = money(max(P * H - D * DOOR_W * DOOR_H - O * WIN_W * WIN_H, ZERO))
    return {
        "S": S, "C": S, "P": P, "H": H, "W": W, "R": R, "N": N, "D": D, "O": O,
        "L": money(max(P - D * DOOR_W, ZERO)), "K": money(O * (2 * WIN_H + WIN_W)),
    }, notes


def bathroom_variables(area, height, perimeter=None) -> tuple[dict[str, Decimal], list[str]]:
    values, notes = variables(area, height, rooms=1, baths=0, perimeter=perimeter, doors=1, windows=0)
    return values, [note for note in notes if "двер" not in note and "окон" not in note]


def build_template(code: str, values: dict[str, Decimal], catalog: Catalog,
                   offers: OfferBook | None = None, section: str = "") -> list[Match]:
    templates = catalog_of_templates()
    if code not in templates:
        raise ValueError(f"нет шаблона {code}")
    drafts: list[DraftLine] = []
    for row in templates[code]["lines"]:
        quantity = money(safe_eval(row["formula"], values))
        if quantity <= ZERO:
            continue
        drafts.append(DraftLine(raw=row["work"], name=row["work"], qty=quantity, unit=row.get("unit") or "шт",
                                kind=MATERIAL if row.get("kind") == "material" else WORK))
    return build(drafts, catalog, offers=offers, section=section or templates[code]["title"].split(" ", 1)[-1])

"""Канал вниз до оператора — независимый от DJI.

Модуль не имеет порта данных на потребительском Mavic, поэтому телеметрия идёт
своим LoRa-линком. На SF9/BW125 это ~1.7 кбит/с, поэтому пакет должен быть
плотным: 9 байт на цель, до 8 целей в кадре.
"""
from __future__ import annotations

import struct
from dataclasses import dataclass

from .fusion import Alert
from .targets import TargetClass

MAGIC = 0xD5
VERSION = 1
MAX_TRACKS_PER_FRAME = 8
_LEVELS = ("INFO", "WARN", "CRITICAL")

_HEADER = struct.Struct("<BBBH")   # magic, ver<<4|count, seq, own_alt_m
_TRACK = struct.Struct("<BBBbHbH")  # id, flags, brg, elev, range, closing, ident_hash


def _crc8(data: bytes) -> int:
    crc = 0x00
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = ((crc << 1) ^ 0x07) & 0xFF if crc & 0x80 else (crc << 1) & 0xFF
    return crc


def ident_hash(ident: str | None) -> int:
    """16-битный отпечаток серийника — чтобы оператор видел «тот же дрон»."""
    if not ident:
        return 0
    h = 0x1505
    for ch in ident.encode():
        h = ((h * 33) ^ ch) & 0xFFFF
    return h


@dataclass
class TrackReport:
    track_id: int
    target_class: TargetClass
    range_exact: bool
    level: str
    bearing_deg: float | None
    elevation_deg: float | None
    range_m: float
    closing_mps: float
    ident_hash: int


def encode(alerts: list[Alert], seq: int, own_alt_m: float) -> bytes:
    """Собрать кадр. Цели сверх лимита отбрасываются — alerts уже отсортированы."""
    picked = alerts[:MAX_TRACKS_PER_FRAME]
    body = bytearray()
    for a in picked:
        tr = a.track
        rng = tr.range_m if tr.range_is_exact else (tr.range_ema_m or 0.0)
        flags = int(tr.target_class) & 0x03
        if tr.range_is_exact:
            flags |= 0x04
        flags |= (_LEVELS.index(a.level) & 0x03) << 3
        brg = 0xFF if tr.bearing_deg is None else int(round(tr.bearing_deg / 360.0 * 254)) & 0xFF
        elev = 0 if tr.elevation_deg is None else max(-90, min(90, int(round(tr.elevation_deg))))
        body += _TRACK.pack(
            tr.track_id & 0xFF,
            flags,
            brg,
            elev,
            min(65535, max(0, int(round(rng)))),
            max(-127, min(127, int(round(tr.closing_mps)))),
            ident_hash(tr.ident),
        )
    head = _HEADER.pack(
        MAGIC, (VERSION << 4) | len(picked), seq & 0xFF, max(0, min(65535, int(own_alt_m)))
    )
    frame = head + bytes(body)
    return frame + bytes([_crc8(frame)])


def decode(frame: bytes) -> tuple[int, float, list[TrackReport]]:
    """Разбор кадра на земле. Бросает ValueError на битом пакете."""
    if len(frame) < _HEADER.size + 1:
        raise ValueError("кадр короче заголовка")
    if _crc8(frame[:-1]) != frame[-1]:
        raise ValueError("CRC не сошлась")
    magic, verlen, seq, own_alt = _HEADER.unpack_from(frame, 0)
    if magic != MAGIC:
        raise ValueError("не наш пакет")
    if (verlen >> 4) != VERSION:
        raise ValueError(f"версия протокола {verlen >> 4} не поддерживается")
    count = verlen & 0x0F
    expected = _HEADER.size + count * _TRACK.size + 1
    if len(frame) != expected:
        raise ValueError(f"ожидалось {expected} байт, получено {len(frame)}")

    reports: list[TrackReport] = []
    off = _HEADER.size
    for _ in range(count):
        tid, flags, brg, elev, rng, closing, ih = _TRACK.unpack_from(frame, off)
        off += _TRACK.size
        reports.append(
            TrackReport(
                track_id=tid,
                target_class=TargetClass(flags & 0x03),
                range_exact=bool(flags & 0x04),
                level=_LEVELS[(flags >> 3) & 0x03],
                bearing_deg=None if brg == 0xFF else brg / 254.0 * 360.0,
                elevation_deg=float(elev),
                range_m=float(rng),
                closing_mps=float(closing),
                ident_hash=ih,
            )
        )
    return seq, float(own_alt), reports


def frame_size(n_tracks: int) -> int:
    return _HEADER.size + min(n_tracks, MAX_TRACKS_PER_FRAME) * _TRACK.size + 1

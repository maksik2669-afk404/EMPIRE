#!/usr/bin/env python3
"""WINTER ARC reels: stills + text overlays + animated tracker -> 10 vertical 1080x1920 reels (Pillow + ffmpeg).

Env: IMG_DIR (img0..img11.png), OUT_DIR, TMP_DIR, FONT_BIG (Oswald Bold), FONT_SMALL (Montserrat SemiBold),
FFMPEG, ONLY (comma list of reel numbers). Silent audio track: add a trending sound inside Instagram/TikTok.
"""
import os
import random
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
FF = os.environ.get("FFMPEG", "ffmpeg")
IMG = os.environ.get("IMG_DIR", "img")
OUT = os.environ.get("OUT_DIR", "out")
TMP = os.environ.get("TMP_DIR", "tmp")
F_BIG = os.environ.get("FONT_BIG", "Oswald.ttf")
F_SMALL = os.environ.get("FONT_SMALL", "Montserrat.ttf")
ICE, FROST, MUTED, BG = (125, 211, 252), (224, 242, 254), (127, 149, 186), (10, 16, 32)
ENC = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", "-r", str(FPS)]
CTA = "ТАБЛИЦА — В TELEGRAM-БОТЕ"
CTA_SUB = "ССЫЛКА В ПРОФИЛЕ"

THEMES = {
    "him": dict(accent=(125, 211, 252), checked=(12, 53, 83), today=(18, 62, 99), title="WINTER ARC · HIM 2026",
                habits=["ПОДЪЁМ", "ТРЕН", "ДУШ", "ЧТЕНИЕ", "ВОДА", "ЕДА", "БЕЗ СОЦ", "ЦЕЛЬ"]),
    "her": dict(accent=(199, 210, 254), checked=(35, 42, 87), today=(44, 52, 112), title="WINTER ARC · HER 2026",
                habits=["ПОДЪЁМ", "ТРЕН", "УХОД", "ЧТЕНИЕ", "ВОДА", "ЕДА", "СПАСИБО", "ШАГИ"]),
}

# Scenes: ("img", image_no, seconds, BIG TEXT, kicker above, sub below) | ("trk", theme, seconds, top text)
#         ("end", image_no, big text) | ("flash",)
REELS = [
    [("img", 3, 1.7, "WINTER ARC\nНАЧИНАЕТСЯ", "", "1 ОКТЯБРЯ"), ("flash",), ("img", 0, 1.0, "92 ДНЯ", "", ""),
     ("img", 2, 0.9, "8 ПРИВЫЧЕК", "", ""), ("img", 5, 0.9, "КАЖДЫЙ\nДЕНЬ", "", ""), ("flash",),
     ("trk", "him", 3.2, "ВСЁ В ОДНОЙ\nТАБЛИЦЕ"), ("end", 9, "ГДЕ ТЫ БУДЕШЬ\n31 ДЕКАБРЯ?")],
    [("img", 0, 1.9, "POV:\nТЫ НАЧАЛ,", "", "ПОКА ВСЕ ЖДУТ ПОНЕДЕЛЬНИКА"), ("flash",), ("img", 3, 0.8, "06:30", "", ""),
     ("img", 5, 0.8, "ХОЛОДНЫЙ\nДУШ", "", ""), ("img", 2, 0.8, "ТРЕНИРОВКА", "", ""), ("img", 6, 0.8, "20 СТРАНИЦ", "", ""),
     ("trk", "him", 3.0, "ГАЛОЧКА\nЗА ГАЛОЧКОЙ"), ("end", 8, "НАЧНИ\nСЕГОДНЯ")],
    [("img", 2, 1.6, "НЕ РАССКАЗЫВАЙ.", "WINTER ARC", ""), ("img", 9, 1.3, "ПОКАЗЫВАЙ.", "", ""), ("flash",),
     ("img", 0, 0.9, "МЕНЬШЕ СЛОВ", "", ""), ("img", 5, 0.9, "БОЛЬШЕ ДЕЛ", "", ""),
     ("trk", "him", 3.0, "ДОКАЗАТЕЛЬСТВА —\nЗДЕСЬ"), ("end", 9, "ТИШИНА.\nДИСЦИПЛИНА.\nРЕЗУЛЬТАТ.")],
    [("img", 4, 1.7, "WINTER ARC", "", "HER VERSION"), ("flash",), ("img", 11, 0.9, "УХОД\nУТРОМ И ВЕЧЕРОМ", "", ""),
     ("img", 7, 0.9, "ТРЕНИРОВКА", "", ""), ("img", 1, 0.9, "3 БЛАГОДАРНОСТИ", "", ""), ("img", 4, 0.8, "10 000 ШАГОВ", "", ""),
     ("trk", "her", 3.2, "ТВОЯ ТАБЛИЦА\nНА 92 ДНЯ"), ("end", 1, "СТАНЬ ТОЙ,\nКЕМ ОБЕЩАЛА\nСЕБЕ СТАТЬ")],
    [("img", 8, 1.9, "ЧЕРЕЗ 92 ДНЯ", "", "ТЫ СКАЖЕШЬ СЕБЕ СПАСИБО"), ("img", 3, 1.6, "ИЛИ ПРИДУМАЕШЬ\nОПРАВДАНИЕ", "", ""),
     ("flash",), ("trk", "him", 3.0, "ВЫБЕРИ\nПЕРВОЕ"), ("end", 8, "ВЫБОР\nЗА ТОБОЙ")],
    [("img", 3, 1.3, "ПРАВИЛА\nWINTER ARC", "", ""), ("img", 0, 1.4, "НИКАКИХ\nНУЛЕВЫХ ДНЕЙ", "ПРАВИЛО 1", ""),
     ("img", 2, 1.5, "СОРВАЛСЯ —\nНЕ ЖДИ\nПОНЕДЕЛЬНИКА", "ПРАВИЛО 2", ""), ("img", 6, 1.3, "МЕНЬШЕ\nЭКРАНА", "ПРАВИЛО 3", ""),
     ("flash",), ("trk", "her", 3.0, "СЛЕДИ\nЗА СЕРИЕЙ"), ("end", 9, "СОХРАНИ,\nЧТОБЫ\nНЕ ПОТЕРЯТЬ")],
    [("img", 0, 1.4, "СЕРИЯ", "", "С 0 ДО 92"), ("img", 2, 0.7, "ДЕНЬ 1", "", ""), ("img", 5, 0.7, "ДЕНЬ 17", "", ""),
     ("img", 9, 0.7, "ДЕНЬ 45", "", ""), ("img", 8, 0.9, "ДЕНЬ 92", "", ""), ("flash",),
     ("trk", "him", 3.0, "НЕ РВИ\nСЕРИЮ"), ("end", 8, "ДОЙДИ\nДО КОНЦА")],
    [("img", 4, 1.6, "ОНА НЕ ЖДЁТ\nВЕСНЫ", "", ""), ("img", 1, 1.4, "ОНА СТРОИТ\nСЕБЯ ЗИМОЙ", "", ""), ("flash",),
     ("img", 7, 0.7, "ТЕЛО", "", ""), ("img", 11, 0.7, "КОЖА", "", ""), ("img", 1, 0.7, "ГОЛОВА", "", ""),
     ("trk", "her", 3.0, "8 ПРИВЫЧЕК.\n92 ДНЯ."), ("end", 4, "ТВОЯ\nЗИМА")],
    [("img", 3, 1.7, "ДО СТАРТА\nWINTER ARC", "", "ОСТАЛОСЬ НЕСКОЛЬКО ДНЕЙ"), ("img", 10, 1.3, "ПОДГОТОВЬСЯ\nЗАРАНЕЕ", "", ""),
     ("flash",), ("trk", "him", 2.2, "ДЛЯ НЕГО"), ("trk", "her", 2.2, "ДЛЯ НЕЁ"), ("end", 10, "ЗАБЕРИ\nДО 1 ОКТЯБРЯ")],
    [("img", 2, 1.4, "ЭТО НЕ\nМОТИВАЦИЯ", "", ""), ("img", 0, 1.3, "ЭТО\nСИСТЕМА", "", ""), ("flash",),
     ("img", 10, 1.0, "8 ГАЛОЧЕК\nВ ДЕНЬ", "", ""), ("trk", "him", 3.0, "ПРОГРЕСС\nВИДНО СРАЗУ"),
     ("end", 9, "СИСТЕМА\nСИЛЬНЕЕ\nМОТИВАЦИИ")],
]
END_SECONDS = 2.4
TRK_SECONDS = 3.2

_fonts = {}


def font(path, size):
    key = (path, size)
    if key not in _fonts:
        _fonts[key] = ImageFont.truetype(path, size)
    return _fonts[key]


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("ffmpeg failed: " + " ".join(cmd[:12]) + "\n" + r.stderr[-1500:])


def tracked(d, cx, y, s, f, fill, track):
    """Centered text with letter spacing."""
    w = sum(d.textlength(ch, font=f) for ch in s) + track * max(0, len(s) - 1)
    x = cx - w / 2
    for ch in s:
        d.text((x, y), ch, font=f, fill=fill)
        x += d.textlength(ch, font=f) + track


def fit(d, lines, path, start, max_w, min_size=60):
    size = start
    while size > min_size and max(d.textlength(l, font=font(path, size)) for l in lines) > max_w:
        size -= 4
    return font(path, size), size


def overlay(path, big="", kicker="", sub="", pos="center", cta=False):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    lines = [l for l in big.split("\n") if l]
    fb, size = fit(d, lines, F_BIG, 176 if pos != "top" else 120, 960) if lines else (None, 0)
    lh = int(size * 1.1)
    block = lh * len(lines)
    cy = {"center": 900, "top": 150 + block / 2, "end": 720}[pos]
    y0 = cy - block / 2
    if lines and pos != "top":  # soft dark scrim behind text for readability
        scrim = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(scrim).rectangle([0, y0 - 140, W, y0 + block + 160], fill=(2, 6, 16, 120))
        im.alpha_composite(scrim.filter(ImageFilter.GaussianBlur(70)))
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dg = ImageDraw.Draw(glow)
    for i, l in enumerate(lines):
        dg.text((W / 2, y0 + i * lh), l, font=fb, fill=ICE + (255,), anchor="ma")
    glow = glow.filter(ImageFilter.GaussianBlur(24))
    glow.putalpha(glow.getchannel("A").point(lambda v: int(v * 0.6)))
    im.alpha_composite(glow)
    d = ImageDraw.Draw(im)
    for i, l in enumerate(lines):
        d.text((W / 2, y0 + i * lh), l, font=fb, fill=(255, 255, 255, 255), anchor="ma")
    if kicker:
        fk, _ = fit(d, [kicker], F_SMALL, 40, 900, 24)
        tracked(d, W / 2, y0 - 78, kicker, fk, ICE + (255,), 8)
    if sub:
        fs, _ = fit(d, [sub], F_SMALL, 46, 960, 24)
        tracked(d, W / 2, y0 + block + 26, sub, fs, FROST + (255,), 4)
    if cta:
        tracked(d, W / 2, y0 - 90, "WINTER ARC 2026 · HIM / HER", font(F_SMALL, 34), ICE + (255,), 8)
        top = y0 + block + 110
        d.rounded_rectangle([110, top, W - 110, top + 124], 62, fill=(186, 230, 253, 255))
        fc, _ = fit(d, [CTA], F_SMALL, 42, 780, 24)
        d.text((W / 2, top + 62), CTA, font=fc, fill=(3, 16, 31, 255), anchor="mm")
        tracked(d, W / 2, top + 160, CTA_SUB, font(F_SMALL, 32), MUTED + (255,), 10)
    im.save(path)


def motion(i, n):
    """Different camera moves so repeated stills never look the same."""
    return [
        (f"1+0.14*on/{n}", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),              # push in
        (f"1.16-0.14*on/{n}", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),           # pull out
        ("1.14", f"(iw-iw/zoom)*on/{n}", "ih/2-(ih/zoom/2)"),                     # pan right
        ("1.14", "iw/2-(iw/zoom/2)", f"(ih-ih/zoom)*(1-on/{n})"),                 # tilt up
    ][i % 4]


GRADE = "eq=contrast=1.12:saturation=0.72:brightness=-0.05,colorbalance=bs=0.12:bm=0.06:bh=0.04,noise=alls=12:allf=t,vignette=PI/4"


def img_scene(out, img, dur, ov, k, end=False):
    n = max(2, round(dur * FPS))
    z, x, y = motion(k, n) if not end else (f"1+0.06*on/{n}", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)")
    extra = ",boxblur=14:2,eq=brightness=-0.16:saturation=0.6" if end else ""
    fc = (f"[0]scale=2160:3840:force_original_aspect_ratio=increase,crop=2160:3840,"
          f"zoompan=z='{z}':x='{x}':y='{y}':d=1:s={W}x{H}:fps={FPS},{GRADE}{extra}[v];"
          f"[1]format=rgba,fade=in:st=0:d=0.12:alpha=1[o];[v][o]overlay=0:0,format=yuv420p[out]")
    run([FF, "-y", "-loop", "1", "-framerate", str(FPS), "-i", img, "-loop", "1", "-framerate", str(FPS), "-i", ov,
         "-filter_complex", fc, "-map", "[out]", "-frames:v", str(n), *ENC, out])


def flash(out):
    run([FF, "-y", "-f", "lavfi", "-i", f"color=c=0xE0F2FE:s={W}x{H}:r={FPS}", "-frames:v", "2", *ENC, out])


# ---------------------------------------------------------------- animated tracker (phone with the sheet)
def tracker_video(theme, out):
    t = THEMES[theme]
    acc = t["accent"]
    rng = random.Random(7)
    rows, cols = 12, 8
    pattern = [[rng.random() < (0.95 if r < 9 else 0.8) for _ in range(cols)] for r in range(rows)]
    order = [(r, c) for r in range(rows) for c in range(cols) if pattern[r][c]]
    snow = [(rng.random() * W, rng.random() * H, rng.uniform(1.2, 3.4), rng.uniform(0.6, 1.8)) for _ in range(110)]
    bg = Image.new("RGB", (W, H))
    dbg = ImageDraw.Draw(bg)
    for yy in range(H):
        k = yy / H
        dbg.line([(0, yy), (W, yy)], fill=(int(14 - 10 * k), int(30 - 21 * k), int(58 - 37 * k)))
    frames = os.path.join(TMP, "trk_" + theme)
    os.makedirs(frames, exist_ok=True)
    n = round(TRK_SECONDS * FPS)
    px0, py0, px1, py1 = 100, 400, 980, 1760
    sx0, sy0, sx1 = px0 + 20, py0 + 20, px1 - 20
    x0 = sx0 + 34
    date_w, cell, pct_w = 104, 76, 92
    for f in range(n):
        p = min(1.0, f / (n * 0.8))
        p = 1 - (1 - p) ** 2
        k = round(p * len(order))
        done = set(order[:k])
        cur_row = order[k][0] if k < len(order) else rows - 1
        im = bg.copy()
        d = ImageDraw.Draw(im)
        for (sx, sy, r, s) in snow:
            yy = (sy + f * s * 5) % H
            d.ellipse([sx - r, yy - r, sx + r, yy + r], fill=(190, 220, 245))
        d.rounded_rectangle([px0, py0, px1, py1], 76, fill=(5, 8, 16), outline=(46, 64, 100), width=4)
        d.rounded_rectangle([sx0, sy0, sx1, py1 - 20], 58, fill=BG)
        d.rounded_rectangle([W / 2 - 86, py0 + 36, W / 2 + 86, py0 + 66], 15, fill=(5, 8, 16))
        y = sy0 + 76
        d.text((x0, y), t["title"], font=font(F_BIG, 52), fill=(232, 241, 255))
        d.text((x0, y + 74), "01.10 — 31.12 · 92 ДНЯ · НЕ РВИ СЕРИЮ", font=font(F_SMALL, 22), fill=acc)
        # KPI tiles
        row_done = [sum((r, c) in done for c in range(cols)) for r in range(rows)]
        ok_rows = [v >= 0.8 * cols for v in row_done]
        streak = 0
        for okr in ok_rows:
            if not okr:
                break
            streak += 1
        tiles = [("ПРОГРЕСС", f"{round(100 * k / (rows * cols))}%"), ("ДНЕЙ", str(sum(ok_rows))), ("СЕРИЯ", str(streak))]
        tw = (sx1 - sx0 - 68 - 2 * 18) / 3
        ty = y + 130
        for i, (lab, val) in enumerate(tiles):
            tx = x0 + i * (tw + 18)
            d.rounded_rectangle([tx, ty, tx + tw, ty + 128], 18, fill=(17, 26, 46))
            d.text((tx + tw / 2, ty + 20), lab, font=font(F_SMALL, 17), fill=MUTED, anchor="mt")
            d.text((tx + tw / 2, ty + 48), val, font=font(F_BIG, 58), fill=acc, anchor="mt")
        # progress bar
        by = ty + 156
        segs = 28
        sw = (sx1 - sx0 - 68) / segs
        filled = round(segs * k / (rows * cols))
        for i in range(segs):
            d.rounded_rectangle([x0 + i * sw + 2, by, x0 + (i + 1) * sw - 4, by + 18], 5,
                                fill=acc if i < filled else (27, 39, 66))
        # table
        hy = by + 50
        d.rounded_rectangle([x0 - 10, hy, sx1 - 24, hy + 52], 10, fill=(21, 33, 58))
        d.text((x0 + date_w / 2, hy + 26), "ДАТА", font=font(F_SMALL, 15), fill=MUTED, anchor="mm")
        for c in range(cols):
            d.text((x0 + date_w + c * cell + cell / 2, hy + 26), t["habits"][c], font=font(F_SMALL, 13), fill=acc,
                   anchor="mm")
        d.text((x0 + date_w + cols * cell + pct_w / 2, hy + 26), "%", font=font(F_SMALL, 16), fill=MUTED, anchor="mm")
        rh = 64
        for r in range(rows):
            ry = hy + 60 + r * rh
            if r == cur_row:
                d.rounded_rectangle([x0 - 10, ry, sx1 - 24, ry + rh - 6], 10, fill=t["today"])
            elif r % 2:
                d.rectangle([x0 - 10, ry, sx1 - 24, ry + rh - 6], fill=(13, 21, 40))
            d.text((x0 + date_w / 2, ry + rh / 2 - 3), f"{r + 1:02d}.10", font=font(F_SMALL, 20), fill=(232, 241, 255),
                   anchor="mm")
            for c in range(cols):
                cx = x0 + date_w + c * cell + cell / 2
                cy = ry + rh / 2 - 3
                if (r, c) in done:
                    d.rounded_rectangle([cx - 19, cy - 19, cx + 19, cy + 19], 8, fill=acc)
                    d.line([(cx - 10, cy + 1), (cx - 3, cy + 9), (cx + 11, cy - 8)], fill=BG, width=5)
                else:
                    d.rounded_rectangle([cx - 18, cy - 18, cx + 18, cy + 18], 8, outline=(52, 70, 106), width=3)
            pct = round(100 * row_done[r] / cols)
            d.text((x0 + date_w + cols * cell + pct_w / 2, ry + rh / 2 - 3), f"{pct}%", font=font(F_BIG, 26),
                   fill=acc if pct >= 80 else MUTED, anchor="mm")
        im.save(os.path.join(frames, f"{f:03d}.png"))
    run([FF, "-y", "-framerate", str(FPS), "-i", os.path.join(frames, "%03d.png"),
         "-vf", "noise=alls=5:allf=t,format=yuv420p", *ENC, out])


def trk_scene(out, base, dur, ov):
    n = max(2, round(dur * FPS))
    fc = (f"[0]setpts=PTS*{dur / TRK_SECONDS:.4f}[v];[1]format=rgba,fade=in:st=0:d=0.15:alpha=1[o];"
          f"[v][o]overlay=0:0,format=yuv420p[out]")
    run([FF, "-y", "-i", base, "-loop", "1", "-framerate", str(FPS), "-i", ov, "-filter_complex", fc,
         "-map", "[out]", "-frames:v", str(n), *ENC, out])


def build(no, scenes, trackers):
    segs = []
    for i, s in enumerate(scenes):
        seg = os.path.join(TMP, f"r{no:02d}_{i:02d}.mp4")
        ov = os.path.join(TMP, f"r{no:02d}_{i:02d}.png")
        if s[0] == "img":
            overlay(ov, s[3], s[4], s[5])
            img_scene(seg, os.path.join(IMG, f"img{s[1]}.png"), s[2], ov, i + no)
        elif s[0] == "trk":
            overlay(ov, s[3], pos="top")
            trk_scene(seg, trackers[s[1]], s[2], ov)
        elif s[0] == "end":
            overlay(ov, s[2], pos="end", cta=True)
            img_scene(seg, os.path.join(IMG, f"img{s[1]}.png"), END_SECONDS, ov, 0, end=True)
        else:
            flash(seg)
        segs.append(seg)
    out = os.path.join(OUT, f"winter_arc_reel_{no:02d}.mp4")
    inputs = sum([["-i", s] for s in segs], [])
    fc = "".join(f"[{i}:v]" for i in range(len(segs))) + f"concat=n={len(segs)}:v=1:a=0[v]"
    run([FF, "-y", *inputs, "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-filter_complex", fc,
         "-map", "[v]", "-map", f"{len(segs)}:a", "-shortest", *ENC, "-c:a", "aac", "-b:a", "96k",
         "-movflags", "+faststart", out])
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(TMP, exist_ok=True)
    only = {int(x) for x in os.environ.get("ONLY", "").split(",") if x}
    todo = [(i + 1, s) for i, s in enumerate(REELS) if not only or i + 1 in only]
    need = {s[1] for _, sc in todo for s in sc if s[0] == "trk"}
    trackers = {}
    for th in sorted(need):
        trackers[th] = os.path.join(TMP, f"tracker_{th}.mp4")
        tracker_video(th, trackers[th])
        print("tracker", th, "ok", flush=True)
    for no, scenes in todo:
        print("built", build(no, scenes, trackers), flush=True)


if __name__ == "__main__":
    main()

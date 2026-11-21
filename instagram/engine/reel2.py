"""Zinger reel v2 - motion-designed, 1080x1920 @30fps, with a synthesized soundtrack."""
import math, os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS, DUR = 1080, 1920, 30, 14.0
FD = "/usr/share/fonts/opentype/inter/"
def font(w, s): return ImageFont.truetype(FD + f"Inter-{w}.otf", s)

LIME = (199, 240, 130)
LIME2 = (163, 230, 53)
WHITE = (255, 255, 255)
INK = (8, 30, 22)
CUTS = [0.0, 2.6, 5.4, 8.6, 11.0, DUR]

# ---------- easing ----------
def cl(x): return max(0.0, min(1.0, x))
def e_out(x): x = cl(x); return 1 - (1 - x) ** 3
def e_inout(x): x = cl(x); return x * x * (3 - 2 * x)
def e_back(x, s=1.9):
    x = cl(x) - 1
    return x * x * ((s + 1) * x + s) + 1
def lerp(a, b, k): return a + (b - a) * k

# ---------- assets ----------
def load(n): return Image.open(os.path.join(HERE, n))
burger = load("zinger.png").convert("RGBA")
bb = burger.getbbox(); burger = burger.crop(bb)
logo = load("logo.png").convert("RGBA").resize((300, 300), Image.LANCZOS)
m = Image.new("L", logo.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, 299, 299], 72, fill=255)
logo.putalpha(m)
SHOTS = {k: load(v).convert("RGB") for k, v in
         {"zinger": "c_zinger.png", "qty": "d_qty.png", "done": "e_done.png", "list": "b_list.png"}.items()}

# background: deep green radial gradient + film grain
yy, xx = np.mgrid[0:H, 0:W]
r = np.sqrt(((xx - W * 0.5) / W) ** 2 + ((yy - H * 0.42) / H) ** 2)
k = np.clip(r / 0.75, 0, 1)[..., None]
BG = (np.array([22, 78, 56]) * (1 - k) + np.array([4, 20, 14]) * k).astype(np.uint8)
BG_IMG = Image.fromarray(BG, "RGB").convert("RGBA")
rng = np.random.default_rng(7)
GRAIN = [Image.fromarray(np.dstack([np.full((H // 2, W // 2), 255, np.uint8)] * 3 +
         [rng.integers(0, 14, (H // 2, W // 2), dtype=np.uint8)]), "RGBA").resize((W, H)) for _ in range(4)]

def blob(radius, color, alpha):
    s = radius * 4
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    ImageDraw.Draw(im).ellipse([radius, radius, 3 * radius, 3 * radius], fill=color + (alpha,))
    return im.filter(ImageFilter.GaussianBlur(radius * 0.6))
BLOB_A = blob(260, LIME2, 70)
BLOB_B = blob(220, (60, 200, 150), 60)
GLOW = blob(330, LIME2, 120)

# phone mockup (screen = screenshot scaled)
PW = 700
PH_SCREEN = round(2532 * PW / 1170)
def phone(shot_name, crop_top=0):
    shot = SHOTS[shot_name]
    sc = shot.resize((PW, round(shot.height * PW / shot.width)), Image.LANCZOS)
    sc = sc.crop((0, crop_top, PW, crop_top + PH_SCREEN))
    bez = 22
    ph = Image.new("RGBA", (PW + 2 * bez, PH_SCREEN + 2 * bez), (0, 0, 0, 0))
    d = ImageDraw.Draw(ph)
    d.rounded_rectangle([0, 0, ph.width - 1, ph.height - 1], 96, fill=(12, 14, 13, 255))
    d.rounded_rectangle([3, 3, ph.width - 4, ph.height - 4], 93, outline=(70, 80, 75, 255), width=3)
    mask = Image.new("L", sc.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, PW - 1, PH_SCREEN - 1], 76, fill=255)
    ph.paste(sc, (bez, bez), mask)
    d.rounded_rectangle([ph.width / 2 - 95, bez + 16, ph.width / 2 + 95, bez + 66], 25, fill=(0, 0, 0, 255))
    return ph
PHONES = {"zinger": phone("zinger", 0), "qty": phone("qty", 0), "done": phone("done", 0)}
SHADOW = Image.new("RGBA", (PW + 200, PH_SCREEN + 200), (0, 0, 0, 0))
ImageDraw.Draw(SHADOW).rounded_rectangle([100, 120, PW + 144, PH_SCREEN + 144], 100, fill=(0, 0, 0, 150))
SHADOW = SHADOW.filter(ImageFilter.GaussianBlur(40))

# where things live on the phone screen (screenshot px / 1170 * PW), measured from captures
SCALE = PW / 1170
ROW_404 = (424 * 3 * SCALE / 1, 0)  # unused helper

# ---------- drawing helpers ----------
def paste_scaled(dst, im, cx, cy, s, rot=0, alpha=1.0):
    if s <= 0.01 or alpha <= 0.01: return
    w, h = max(1, int(im.width * s)), max(1, int(im.height * s))
    t = im.resize((w, h), Image.BILINEAR)
    if rot: t = t.rotate(rot, Image.BICUBIC, expand=True)
    if alpha < 1:
        a = t.getchannel("A").point(lambda v: int(v * alpha)); t.putalpha(a)
    dst.alpha_composite(t, (int(cx - t.width / 2), int(cy - t.height / 2)))

def text_layer(txt, f, fill, stroke=0, sfill=INK):
    d0 = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    x0, y0, x1, y1 = d0.textbbox((0, 0), txt, font=f, stroke_width=stroke)
    im = Image.new("RGBA", (x1 - x0 + 40, y1 - y0 + 40), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((20 - x0, 20 - y0), txt, font=f, fill=fill, stroke_width=stroke, stroke_fill=sfill)
    return im
_tl = {}
def T(txt, f, fill, stroke=0):
    key = (txt, f.size, f.path, fill, stroke)
    if key not in _tl: _tl[key] = text_layer(txt, f, fill, stroke)
    return _tl[key]

def pop_text(dst, txt, f, fill, x, y, t0, t, anchor="l", stroke=0, shadow=True):
    """Text that pops in with an overshoot at t0. x,y = left/center + top."""
    k = (t - t0) / 0.28
    if k <= 0: return
    s = 0.6 + 0.4 * e_back(k)
    im = T(txt, f, fill, stroke)
    cx = x + im.width / 2 if anchor == "l" else x
    cy = y + im.height / 2
    if shadow:
        sh = T(txt, f, (0, 0, 0, 110), stroke)
        paste_scaled(dst, sh, cx + 6, cy + 10, s, alpha=cl(k * 2))
    paste_scaled(dst, im, cx, cy, s, alpha=cl(k * 2))

def pill(dst, x0, y0, x1, y1, fill, r=None):
    if len(fill) == 4 and fill[3] < 255:
        lay = Image.new("RGBA", dst.size, (0, 0, 0, 0))
        ImageDraw.Draw(lay).rounded_rectangle([x0, y0, x1, y1], r or (y1 - y0) / 2, fill=fill)
        dst.alpha_composite(lay)
    else:
        ImageDraw.Draw(dst).rounded_rectangle([x0, y0, x1, y1], r or (y1 - y0) / 2, fill=fill)

F_HUGE = font("Black", 196)
F_BIG = font("Black", 132)
F_MID = font("ExtraBold", 84)
F_SM = font("Bold", 46)
F_TAG = font("SemiBold", 36)
F_CAP = font("ExtraBold", 54)
F_TILE = font("Black", 64)
F_TILE_S = font("SemiBold", 28)

# ---------- karaoke captions ----------
SUBS = [
    (0.15, 2.5, "Nimeni nu-ți spune cât are un Zinger."),
    (2.75, 5.3, "404 de calorii. Fișa oficială KFC."),
    (5.55, 8.5, "Plus încă 1.188 de produse din fast-food."),
    (8.7, 10.9, "Cauți. Alegi gramajul. Gata."),
    (11.15, 13.8, "Scrie ZINGER și-ți trimit linkul."),
]
def word_times(a, b, text):
    ws = text.split(); L = [len(w) + 2 for w in ws]; tot = sum(L); out = []; c = a
    for w, l in zip(ws, L):
        d = (b - a - 0.3) * l / tot; out.append((w, c, c + d)); c += d
    return out
SUBW = [word_times(*s) for s in SUBS]

def captions(dst, t):
    for (a, b, _), words in zip(SUBS, SUBW):
        if not (a <= t < b + 0.1): continue
        d = ImageDraw.Draw(dst)
        lines, line, maxw = [], [], 760
        for w in words:
            test = " ".join(x[0] for x in line + [w])
            if d.textlength(test, font=F_CAP) > maxw and line: lines.append(line); line = [w]
            else: line.append(w)
        lines.append(line)
        LH = 76
        y = 1440 - LH * len(lines) - 14
        appear = e_out((t - a) / 0.2)
        widths = [d.textlength(" ".join(x[0] for x in ln), font=F_CAP) for ln in lines]
        bw = max(widths) + 64
        back = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(back).rounded_rectangle([455 - bw / 2, y - 14, 455 + bw / 2, y + LH * len(lines) + 8], 30,
                                               fill=(4, 18, 12, int(150 * appear)))
        dst.alpha_composite(back)
        for ln, lw in zip(lines, widths):
            layer = Image.new("RGBA", (W, LH + 30), (0, 0, 0, 0))
            ld = ImageDraw.Draw(layer)
            x = 455 - lw / 2
            for w, w0, w1 in ln:
                active = w0 <= t
                col = LIME if (active and t < w1 + 0.35) else (WHITE if active else (255, 255, 255, 110))
                if ("ZINGER" in w or "PLAN" in w) and active: col = LIME
                lift = -5 if (w0 <= t < w0 + 0.12) else 0
                ld.text((x, 62 + lift), w, font=F_CAP, fill=col, anchor="ls", stroke_width=6, stroke_fill=INK)
                x += d.textlength(w + " ", font=F_CAP)
            dst.alpha_composite(layer, (0, int(y + (1 - appear) * 20 - 6)))
            y += LH

def brand_tag(dst, t):
    d = ImageDraw.Draw(dst)
    lw = d.textlength("jurnalalimentar.fit", font=F_TAG)
    small = logo.resize((52, 52), Image.LANCZOS)
    pill(dst, 60, 250, 60 + lw + 112, 318, (255, 255, 255, 34))
    dst.alpha_composite(small, (72, 258))
    d.text((138, 284), "jurnalalimentar.fit", font=F_TAG, fill=WHITE, anchor="lm")

def ripple(dst, cx, cy, t, t0):
    k = (t - t0) / 0.45
    if not 0 <= k <= 1: return
    rr = 30 + 90 * e_out(k)
    ImageDraw.Draw(dst).ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=LIME + (int(255 * (1 - k)),), width=10)
    if k < 0.4:
        ImageDraw.Draw(dst).ellipse([cx - 26, cy - 26, cx + 26, cy + 26], fill=(255, 255, 255, int(200 * (1 - k / 0.4))))

def checkmark(dst, cx, cy, s, k):
    if k <= 0: return
    d = ImageDraw.Draw(dst)
    r = s * e_back(k)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=LIME2)
    p = [(cx - r * 0.45, cy + r * 0.02), (cx - r * 0.1, cy + r * 0.36), (cx + r * 0.5, cy - r * 0.32)]
    d.line(p, fill=INK, width=max(3, int(r * 0.2)), joint="curve")

# ---------- scenes ----------
def bg(t):
    im = BG_IMG.copy()
    im.alpha_composite(BLOB_A, (int(-300 + 120 * math.sin(t * 0.6)), int(1150 + 90 * math.cos(t * 0.5))))
    im.alpha_composite(BLOB_B, (int(560 + 100 * math.cos(t * 0.7)), int(-150 + 120 * math.sin(t * 0.4))))
    return im

def s_hook(im, t):
    # burger slams in with spin + overshoot, then floats
    k = (t - 0.0) / 0.55
    s = 0.95 * e_back(k, 1.6) + 0.02 * math.sin(t * 3)
    rot = lerp(-25, 0, e_out(k)) + 2.5 * math.sin(t * 2.2)
    shake = 10 * math.sin(t * 60) * max(0, 1 - t / 0.35)
    paste_scaled(im, GLOW, 540, 1010, 0.8 + 0.25 * e_out(k), alpha=cl(k))
    paste_scaled(im, burger, 540 + shake, 1000 + 18 * math.sin(t * 2.5), s * 1.05, rot)
    pop_text(im, "CÂTE CALORII", F_BIG, WHITE, 64, 360, 0.05, t)
    pop_text(im, "ARE UN", F_BIG, WHITE, 64, 505, 0.45, t)
    # the word ZINGER? slams with a wobble
    k2 = (t - 0.95) / 0.3
    if k2 > 0:
        lay = T("ZINGER?", F_HUGE, LIME)
        sh = T("ZINGER?", F_HUGE, (0, 0, 0, 120))
        s2 = 1.5 - 0.5 * e_back(k2, 2.4)
        wob = 3 * math.sin((t - 0.95) * 18) * max(0, 1 - (t - 0.95) / 0.8)
        paste_scaled(im, sh, 64 + lay.width / 2 + 8, 640 + lay.height / 2 + 12, s2, wob, alpha=cl(k2 * 2))
        paste_scaled(im, lay, 64 + lay.width / 2, 640 + lay.height / 2, s2, wob, alpha=cl(k2 * 2))

def counter(im, t, t0, dur, value, x, y, f, fill, prefix="", fmt=None):
    k = e_out((t - t0) / dur)
    if t < t0: return
    v = int(round(value * k))
    s = fmt(v) if fmt else str(v)
    pop_text(im, prefix + s, f, fill, x, y, t0, t + 1)  # already popped; scale settles

def s_404(im, t):
    lt = t - 2.6
    # phone rises
    k = e_out(lt / 0.55)
    py = lerp(1960, 820, k)
    im.alpha_composite(SHADOW, (int(540 - SHADOW.width / 2), int(py - 100)))
    ph = PHONES["zinger"]
    # show the Zinger row near the top of the phone: crop zinger screenshot around the row
    im.alpha_composite(ph, (int(540 - ph.width / 2), int(py)))
    # highlight around the "404 kcal · 150 g" product row (row spans y~360..480 in 390-wide capture)
    hy0 = py + 22 + 360 * (PW / 390); hy1 = py + 22 + 485 * (PW / 390)
    if lt > 0.7:
        pk = cl((lt - 0.7) / 0.3); pul = 6 * math.sin(lt * 8)
        ImageDraw.Draw(im).rounded_rectangle([540 - PW / 2 + 10 - pul, hy0 - pul, 540 + PW / 2 - 10 + pul, hy1 + pul],
                                             36, outline=LIME + (int(255 * pk),), width=10)
    # big counter
    if lt > 0.1:
        v = int(round(404 * e_out((lt - 0.1) / 0.9)))
        lay = T(str(v), F_HUGE, LIME)
        pk = e_back((lt - 0.1) / 0.3)
        paste_scaled(im, T(str(v), F_HUGE, (0, 0, 0, 120)), 64 + 260 + 8, 380 + 125 + 12, 0.6 + 0.4 * pk)
        paste_scaled(im, lay, 64 + 260, 380 + 125, 0.6 + 0.4 * pk)
        pop_text(im, "kcal", F_MID, WHITE, 640, 470, 0.25 + 2.6, t)
    pop_text(im, "fișa oficială KFC", F_SM, INK, 0, 0, 99, t)  # placeholder (drawn as pill below)
    if lt > 0.9:
        pk = e_back((lt - 0.9) / 0.3)
        tw = ImageDraw.Draw(im).textlength("din fișa oficială KFC", font=F_SM)
        pill_im = Image.new("RGBA", (int(tw + 70), 84), (0, 0, 0, 0))
        pill(pill_im, 0, 0, pill_im.width - 1, 83, LIME + (255,))
        ImageDraw.Draw(pill_im).text((35, 42), "din fișa oficială KFC", font=F_SM, fill=INK, anchor="lm")
        paste_scaled(im, pill_im, 64 + pill_im.width / 2, 690, 0.6 + 0.4 * pk)
    # burger sticker
    paste_scaled(im, burger, 900, 450, 0.32 * e_back((lt - 0.2) / 0.4), 12 + 4 * math.sin(lt * 3))

TILES = [("KFC", "KFC", (166, 38, 46), (255, 248, 235)), ("BK", "Burger King", (245, 190, 150), (120, 50, 20)),
         ("PH", "Pizza Hut", (190, 30, 45), WHITE), ("Z", "Zoomserie", (225, 210, 240), (110, 70, 150)),
         ("CX", "Chopstix", (230, 60, 50), WHITE), ("SK", "Socului Kebap", (250, 205, 90), (90, 50, 10)),
         ("TK", "Turkish Kitchen", (40, 110, 160), WHITE), ("P&P", "Pep & Pepper", (40, 40, 40), (255, 210, 60)),
         ("TX", "Taksim", (200, 70, 40), WHITE), ("BMB", "Boss Mini", (20, 20, 20), WHITE),
         ("OT", "Oro Toro", (230, 170, 40), (60, 30, 0)), ("FRY", "FRYDAY", (255, 120, 40), WHITE)]
_tiles = {}
def tile(i):
    if i in _tiles: return _tiles[i]
    mark, name, bgc, fgc = TILES[i]
    im = Image.new("RGBA", (200, 250), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([10, 10, 190, 190], 46, fill=bgc + (255,))
    f = F_TILE if len(mark) <= 2 else font("Black", 50)
    d.text((100, 100), mark, font=f, fill=fgc, anchor="mm")
    d.text((100, 222), name, font=F_TILE_S, fill=(255, 255, 255, 210), anchor="mm")
    _tiles[i] = im; return im

def fmt_ro(v): return f"{v:,}".replace(",", ".")

def s_list(im, t):
    lt = t - 5.4
    if lt > 0.0:
        v = int(round(1188 * e_out(lt / 1.3)))
        pk = e_back(lt / 0.3)
        lay = T("+" + fmt_ro(v), F_HUGE, LIME)
        paste_scaled(im, T("+" + fmt_ro(v), F_HUGE, (0, 0, 0, 120)), 64 + lay.width / 2 + 8, 470 + 12, 0.6 + 0.4 * pk)
        paste_scaled(im, lay, 64 + lay.width / 2, 470, 0.6 + 0.4 * pk)
    pop_text(im, "produse din fast-food", F_MID, WHITE, 64, 590, 5.4 + 0.3, t)
    for i in range(12):
        c, rrow = i % 4, i // 4
        cx = 150 + c * 195; cy = 860 + rrow * 205
        k = (lt - 0.35 - i * 0.07) / 0.35
        if k <= 0: continue
        bob = 6 * math.sin(lt * 3 + i)
        paste_scaled(im, tile(i), cx, cy + bob, 0.78 * e_back(k, 2.2), (1 - e_out(k)) * 20)

def s_steps(im, t):
    lt = t - 8.6
    steps = [(0.0, "zinger", "Cauți", (0, 420)), (0.8, "qty", "Alegi gramajul", (520, 1060)), (1.6, "done", "Gata", None)]
    cur = max(i for i, s in enumerate(steps) if lt >= s[0])
    st0, shot, label, tap = steps[cur]
    sk = e_out((lt - st0) / 0.25)
    py = 820 if cur > 0 else lerp(1960, 820, e_out(lt / 0.4))
    im.alpha_composite(SHADOW, (int(540 - SHADOW.width / 2), int(py - 100)))
    ph = PHONES[shot]
    x = 540 - ph.width / 2 + (1 - sk) * (120 if cur else 0)
    im.alpha_composite(ph, (int(x), int(py)))
    if tap:
        ripple(im, 540 - PW / 2 + tap[0] * 0 + PW / 2, py + 22 + tap[1] * (PW / 390) * 0 + (480 if cur == 0 else 1320), t, 8.6 + st0 + 0.35)
    # step chips
    for i, (s0, _, lab, _) in enumerate(steps):
        if lt < s0: continue
        y = 360 + i * 118
        on = i == cur
        k = e_back((lt - s0) / 0.3)
        d = ImageDraw.Draw(im)
        fnt = F_MID
        tw = d.textlength(lab, font=fnt)
        chip = Image.new("RGBA", (int(tw + 190), 108), (0, 0, 0, 0))
        pill(chip, 0, 0, chip.width - 1, 107, (LIME + (255,)) if on else (255, 255, 255, 40))
        cd = ImageDraw.Draw(chip)
        cd.ellipse([14, 14, 94, 94], fill=INK if on else (255, 255, 255, 60))
        cd.text((54, 54), str(i + 1), font=F_SM, fill=LIME if on else WHITE, anchor="mm")
        cd.text((118, 54), lab, font=fnt, fill=INK if on else WHITE, anchor="lm")
        paste_scaled(im, chip, 64 + chip.width / 2, y + 54, 0.6 + 0.4 * k)
    if cur == 2:
        checkmark(im, 820, 1150, 90, (lt - 1.75) / 0.35)

def s_cta(im, t):
    lt = t - 11.0
    beat = 0.5
    pulse = 1 + 0.05 * max(0, math.cos((lt % beat) / beat * math.pi)) ** 8
    paste_scaled(im, GLOW, 455, 520, 0.7, alpha=0.8)
    paste_scaled(im, logo, 455, 520, 0.85 * e_back(lt / 0.4), (1 - e_out(lt / 0.4)) * -30)
    pop_text(im, "Scrie în comentarii", F_MID, WHITE, 455, 760, 11.25, t, anchor="c")
    # ZINGER pill
    k = (lt - 0.5) / 0.35
    if k > 0:
        d = ImageDraw.Draw(im)
        tw = d.textlength("ZINGER", font=F_HUGE)
        pim = Image.new("RGBA", (int(tw + 120), 250), (0, 0, 0, 0))
        pill(pim, 0, 0, pim.width - 1, 249, LIME + (255,), 70)
        ImageDraw.Draw(pim).text((pim.width / 2, 125), "ZINGER", font=F_HUGE, fill=INK, anchor="mm")
        # comment bubble tail
        ImageDraw.Draw(pim).polygon([(90, 249), (150, 249), (70, 249)], fill=LIME)
        paste_scaled(im, pim, 455, 1000, (0.5 + 0.5 * e_back(k, 2.6)) * pulse * 0.82, 3 * math.sin(lt * 4) * max(0, 1 - lt / 2))
    pop_text(im, "și-ți trimit linkul", F_MID, WHITE, 455, 1150, 11.9, t, anchor="c")

SCENES = [s_hook, s_404, s_list, s_steps, s_cta]

def frame(t):
    im = bg(t)
    si = max(i for i in range(len(SCENES)) if t >= CUTS[i])
    SCENES[si](im, t)
    brand_tag(im, t)
    captions(im, t)
    im.alpha_composite(GRAIN[int(t * FPS) % 4])
    # punch-in + flash on each cut
    dt = t - CUTS[si]
    if si > 0 and dt < 0.22:
        z = 1 + 0.06 * (1 - dt / 0.22)
        cw, ch = W / z, H / z
        im = im.resize((W, H), Image.BILINEAR, box=((W - cw) / 2, (H - ch) / 2, (W + cw) / 2, (H + ch) / 2))
        fl = Image.new("RGBA", (W, H), (255, 255, 255, int(110 * (1 - dt / 0.22))))
        im.alpha_composite(fl)
    # progress bar (top, thin)
    ImageDraw.Draw(im).rounded_rectangle([60, 214, 60 + (W - 120) * t / DUR, 222], 4, fill=LIME + (200,))
    return im.convert("RGB")

# ---------- soundtrack ----------
POPS = [0.05, 0.45, 0.95, 2.7, 3.5, 5.4] + [5.75 + i * 0.07 for i in range(12)] + [8.95, 9.75, 10.55, 11.5]
TICKS = [(2.7, 0.9), (5.4, 1.3)]
STABS = [(0.95, 880), (11.5, 659.25), (11.5, 987.77)]
def soundtrack(path):
    sr = 44100; n = int(sr * DUR); out = np.zeros(n)
    tt = np.arange(n) / sr
    bpm = 120; b = 60 / bpm
    def add(sig, at, g=1.0):
        i = int(at * sr); j = min(n, i + len(sig)); out[i:j] += sig[:j - i] * g
    L = int(0.35 * sr); x = np.arange(L) / sr
    kick = np.sin(2 * np.pi * (45 + 110 * np.exp(-x * 30)) * x) * np.exp(-x * 9)
    hat = np.random.default_rng(1).standard_normal(int(0.05 * sr)) * np.exp(-np.arange(int(0.05 * sr)) / sr * 90)
    hat = np.diff(hat, prepend=0)
    clapn = np.random.default_rng(2).standard_normal(int(0.18 * sr))
    clap = clapn * np.exp(-np.arange(len(clapn)) / sr * 22)
    notes = [55.0, 55.0, 65.41, 49.0]  # A1 A1 C2 G1
    for i in range(int(DUR / b) + 1):
        at = i * b
        if at < DUR - 0.05:
            add(kick, at, 0.95)
            if i % 2 == 1: add(clap, at, 0.22)
            add(hat, at + b / 2, 0.18)
            f0 = notes[(i // 4) % 4]
            bl = int(b * sr * 0.9); bx = np.arange(bl) / sr
            bass = np.sign(np.sin(2 * np.pi * f0 * bx)) * 0.5 + np.sin(2 * np.pi * f0 * bx)
            bass *= np.exp(-bx * 3.5) * np.minimum(1, bx * 200)
            add(bass, at, 0.16)
    # simple lead stabs on the hook and CTA
    for at, f in STABS:
        l = int(0.4 * sr); lx = np.arange(l) / sr
        add((np.sin(2 * np.pi * f * lx) + 0.3 * np.sin(4 * np.pi * f * lx)) * np.exp(-lx * 7), at, 0.18)
    # whooshes into each cut
    for c in CUTS[1:-1]:
        l = int(0.35 * sr); wn = np.random.default_rng(int(c * 10)).standard_normal(l)
        env = np.sin(np.linspace(0, np.pi, l)) ** 2
        k_ = np.exp(-np.arange(200) / 30); wn = np.convolve(wn, k_ / k_.sum(), "same")
        add(wn * env, c - 0.3, 0.9)
    # pops on word slams / tiles
    for at in POPS:
        l = int(0.06 * sr); px = np.arange(l) / sr
        add(np.sin(2 * np.pi * (900 - 6000 * px) * px) * np.exp(-px * 60), at, 0.22)
    # counter ticks
    for a, d in TICKS:
        for j in range(14):
            at = a + d * (1 - (1 - j / 14) ** 0.5)
            l = int(0.015 * sr); add(np.sin(2 * np.pi * 2400 * np.arange(l) / sr) * np.hanning(l), at, 0.12)
    fade = np.minimum(1, (DUR - tt) / 0.6)
    out = np.tanh(out * 1.4) * 0.8 * fade
    st = np.stack([out, out], 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((st * 32767).astype(np.int16).tobytes())

if __name__ == "__main__":
    out = sys.argv[1]
    if len(sys.argv) > 2 and sys.argv[2] == "preview":
        for tp in [0.3, 1.6, 4.3, 7.6, 9.2, 10.6, 12.8]:
            frame(tp).save(os.path.join(HERE, f"pv_{tp:.1f}.png"))
        sys.exit()
    wav = os.path.join(HERE, "music.wav"); soundtrack(wav)
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav,
                           "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
                           "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out],
                          stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)):
        ff.stdin.write(frame(i / FPS).tobytes())
    ff.stdin.close(); ff.wait(); print("done", out)

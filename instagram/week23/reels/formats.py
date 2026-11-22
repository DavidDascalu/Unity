"""Seven different reel formats (no shared template), each with its own music.

    python3 formats.py <x1..x7> frames 1,4,8 | audio | seg i n
x1 chat · x2 macro scan · x3 kinetic type · x4 real screen recording · x5 split screen · x6 POV · x7 day timelapse
"""
import math, os, re, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__)); SPOT = os.path.join(HERE, "..", "..", "spot"); ENGINE = os.path.join(HERE, "..", "..", "engine")
REC = os.path.join(HERE, "rec")
sys.path.insert(0, SPOT)
import render as R
import audio as AU
from render import W, H, k01, eo, eio, eback, lerp, lerp2, paste, fade, scaled, place3d, glow_line, text_img, AS, LOGO, GLOW_G, F

KEY = sys.argv[1]
MP3 = {"x1": "x1_voce.mp3", "x2": "x2_barcode.mp3", "x3": "x3_buget.mp3", "x4": "x4_nuti.mp3", "x5": "x5_gratuit.mp3", "x6": "x6_sync.mp3", "x7": "x7_momente.mp3"}[KEY]
KW = {"x2": "ETICHETA", "x3": "PLAN"}.get(KEY, "JURNAL")
SUBS = {
 "x1": ["Ai mâinile ocupate?", "Spui ce ai mâncat, cu vocea.", "Verifici ce a înțeles.", "Confirmi și intră în jurnal.", "Scrie JURNAL în comentarii!"],
 "x2": ["Ai produsul în mână?", "Scanezi codul de bare.", "Verifici produsul și gramajul.", "Confirmi și gata.", "Scrie ETICHETA în comentarii!"],
 "x3": ["Ai un buget pentru mâncare?", "Îl treci în profil, în lei pe săptămână.", "Apoi îți generezi planul.", "Cu lista de cumpărături inclusă.", "Scrie PLAN în comentarii!"],
 "x4": ["Prima dată în aplicație?", "Nuti te ghidează pas cu pas.", "Îți arată cum adaugi o masă.", "Sau cum îți faci planul.", "Scrie JURNAL în comentarii!"],
 "x5": ["Ce primești gratuit?", "Jurnalul și înregistrarea meselor.", "Premium adaugă planul personal și analiza AI.", "De la 25 de lei pe lună.", "Scrie JURNAL în comentarii!"],
 "x6": ["Telefon dimineața, laptop la birou?", "Intri în cont.", "Profilul și mesele se sincronizează.", "Același jurnal, oriunde.", "Scrie JURNAL în comentarii!"],
 "x7": ["Mic dejun, prânz, gustare, cină.", "Fiecare masă are locul ei.", "Vezi ziua pe momente.", "Și totalul zilei, dintr-o privire.", "Scrie JURNAL în comentarii!"]}[KEY]
VO = 0.45
LIME = (199, 240, 130); LIME2 = (148, 230, 2); INK = (8, 30, 22); DARK = (11, 15, 12); WHITE = (255, 255, 255); GREEN = (37, 94, 70); MINT = (244, 246, 241)

def phrase_starts(mp3):
    x = AU.load_mp3(mp3)
    out = subprocess.run(["ffmpeg", "-hide_banner", "-i", mp3, "-af", "silencedetect=noise=-38dB:d=0.25", "-f", "null", "-"], capture_output=True, text=True).stderr
    ends = [float(v) for v in re.findall(r"silence_end: ([0-9.]+)", out)]
    return [s + VO for s in ([AU.onset(x)] + [e for e in ends if e < len(x) / AU.SR - 0.2])[:5]], len(x) / AU.SR + VO
P, VEND = phrase_starts(os.path.join(HERE, MP3))
DUR = round(VEND + 1.6, 2)
PE = [P[i + 1] - 0.12 if i < 4 else DUR for i in range(5)]   # phrase end

def words_timing(i):
    ws = SUBS[i].replace(",", "").replace("!", "").replace("?", "").replace(".", "").split()
    a, b = P[i], PE[i] - 0.1; L = [len(w) + 2 for w in ws]; tot = sum(L); out = []; c = a
    for w, l in zip(ws, L): d = (b - a) * l / tot; out.append((w, c, c + d)); c += d
    return out

def cap(path): return Image.open(path).convert("RGB")
def rr(d, box, r, **k): d.rounded_rectangle(box, r, **k)
def tiktok_caption(c, txt, y, a, size=64, width=920):
    """White bold text with black outline, TikTok style."""
    f = F("x", size); d0 = ImageDraw.Draw(Image.new("RGBA", (1, 1))); lines, ln = [], ""
    for w in txt.split():
        t = (ln + " " + w).strip()
        if d0.textlength(t, font=f) <= width: ln = t
        else: lines.append(ln); ln = w
    lines.append(ln)
    lay = Image.new("RGBA", (W, int(len(lines) * size * 1.25 + 40)), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for j, l in enumerate(lines): d.text((W / 2, 20 + j * size * 1.25), l, font=f, fill=WHITE, anchor="ma", stroke_width=9, stroke_fill=(0, 0, 0))
    paste(c, fade(lay, a), 0, y)
def logo_pill(c, kw, cy, a, bg=LIME, fg=INK, s=1.0):
    fnt = F("dk", 150); w = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textlength(kw, font=fnt)
    pim = Image.new("RGBA", (int(w + 140), 230), (0, 0, 0, 0)); ImageDraw.Draw(pim).rounded_rectangle([0, 0, pim.width - 1, 229], 64, fill=bg + (255,))
    ImageDraw.Draw(pim).text((pim.width / 2, 118), kw, font=fnt, fill=fg, anchor="mm")
    s = s * min(1, 900 / pim.width); paste(c, fade(scaled(pim, s), a), 540 - pim.width * s / 2, cy - pim.height * s / 2)
def tap(c, x, y, t, t0, col=WHITE):
    k = k01(t, t0, t0 + 0.45)
    if 0 < k < 1:
        d = ImageDraw.Draw(c); r = lerp(24, 100, eo(k)); d.ellipse([x - r, y - r, x + r, y + r], outline=col + (int(230 * (1 - k)),), width=7)
        if k < 0.35: d.ellipse([x - 30, y - 30, x + 30, y + 30], fill=col + (int(170 * (1 - k / 0.35)),))

# ========================= x1 · CHAT =========================
def chat_frame(t):
    c = Image.new("RGBA", (W, H), (233, 239, 230, 255)); d = ImageDraw.Draw(c)
    for yy in range(0, H, 90):
        for xx in range((yy // 90) % 2 * 45, W, 90): d.ellipse([xx, yy + 300, xx + 6, yy + 306], fill=(220, 228, 216))
    bubbles = []   # (t_appear, side, kind, payload)
    bubbles.append((P[0] + 0.1, "me", "text", "Am mâinile ocupate..."))
    bubbles.append((P[1] + 0.1, "me", "voice", None))
    bubbles.append((P[1] + 1.6, "app", "typing", None))
    bubbles.append((P[2], "app", "items", ["Am înțeles:", "Iaurt simplu · 150 g", "Banană · 1 bucată", "Verifici?"]))
    bubbles.append((P[3], "me", "text", "Confirm"))
    bubbles.append((P[3] + 0.8, "app", "done", "Adăugat în jurnal."))
    shown = [b for b in bubbles if t >= b[0] and not (b[2] == "typing" and t >= P[2])]
    def size(b):
        if b[2] == "text": return (min(760, ImageDraw.Draw(Image.new("RGBA", (1, 1))).textlength(b[3], font=F("m", 50)) + 80), 120)
        if b[2] == "voice": return (640, 130)
        if b[2] == "typing": return (200, 110)
        if b[2] == "items": return (700, 380)
        return (620, 120)
    total = sum(size(b)[1] + 30 for b in shown); y = 1640 - total
    for b in shown:
        w, h = size(b); k = eback(k01(t, b[0], b[0] + 0.35), 1.4); me = b[1] == "me"
        bub = Image.new("RGBA", (int(w), h), (0, 0, 0, 0)); bd = ImageDraw.Draw(bub)
        rr(bd, [0, 0, w - 1, h - 1], 46, fill=(LIME if me else WHITE) + (255,))
        if b[2] == "text": bd.text((40, h / 2), b[3], font=F("m", 50), fill=INK, anchor="lm")
        elif b[2] == "voice":
            bd.ellipse([24, 25, 104, 105], fill=INK); bd.polygon([(52, 45), (52, 85), (86, 65)], fill=LIME)
            prog = k01(t, b[0] + 0.2, b[0] + 2.2)
            for j in range(34):
                hh = 10 + 38 * abs(math.sin(j * 1.7) * math.sin(j * 0.31 + 1)); x = 130 + j * 14
                bd.rounded_rectangle([x, 65 - hh, x + 7, 65 + hh], 3, fill=INK if j / 34 < prog else (90, 120, 80))
            bd.text((w - 30, 65), "0:02", font=F("m", 34), fill=INK, anchor="rm")
        elif b[2] == "typing":
            for j in range(3):
                yo = 8 * math.sin(t * 9 - j * 0.8); bd.ellipse([45 + j * 45, 45 + yo, 75 + j * 45, 75 + yo], fill=(150, 160, 152))
        elif b[2] == "items":
            bd.text((40, 55), b[3][0], font=F("s", 46), fill=INK)
            for j, it in enumerate(b[3][1:3]):
                rr(bd, [40, 120 + j * 90, w - 40, 195 + j * 90], 26, fill=(236, 243, 234)); bd.text((70, 157 + j * 90), it, font=F("m", 42), fill=INK, anchor="lm")
            bd.text((40, 318), b[3][3], font=F("s", 44), fill=GREEN)
        else:
            bd.ellipse([30, 30, 90, 90], fill=LIME2); bd.line([(45, 60), (56, 72), (77, 48)], fill=INK, width=7); bd.text((115, 60), b[3], font=F("s", 46), fill=INK, anchor="lm")
        x = (W - 60 - w) if me else 60
        s = max(0.05, min(1.05, k)); bb = scaled(bub, s)
        paste(c, bb, x + (w - bb.width) * (1 if me else 0), y + (h - bb.height) / 2); y += h + 30
    # header
    rr(d, [0, 0, W, 250], 0, fill=(255, 255, 255)); lg = scaled(LOGO, 0.075); paste(c, lg, 60, 135 - lg.height / 2)
    d.text((180, 110), "Jurnal Alimentar", font=F("b", 46), fill=INK); d.text((180, 168), "Asistent · online", font=F("m", 34), fill=(90, 120, 100))
    # input bar
    rr(d, [40, 1700, W - 160, 1820], 60, fill=WHITE); d.text((90, 1760), "Spune ce ai mâncat...", font=F("m", 42), fill=(140, 150, 144), anchor="lm")
    mic_on = P[1] <= t < P[1] + 2.2; mr = 60 + (8 * math.sin(t * 12) if mic_on else 0)
    d.ellipse([W - 140 - mr + 60, 1760 - mr, W - 140 + mr + 60, 1760 + mr], fill=LIME2 if mic_on else INK)
    d.rounded_rectangle([W - 92, 1730, W - 68, 1775], 12, fill=WHITE); d.arc([W - 106, 1745, W - 54, 1795], 0, 180, fill=WHITE, width=5)
    if t >= P[4]:
        k = eo(k01(t, P[4], P[4] + 0.5)); sheet = Image.new("RGBA", (W, 900), (0, 0, 0, 0)); sd = ImageDraw.Draw(sheet)
        rr(sd, [0, 0, W, 960], 70, fill=DARK + (255,)); lg = scaled(LOGO, 0.16); sheet.alpha_composite(lg, (540 - lg.width // 2, 70))
        sd.text((540, 330), "Scrie în comentarii", font=F("s", 52), fill=WHITE, anchor="mm")
        paste(c, sheet, 0, lerp(H, H - 900, k)); logo_pill(c, KW, lerp(H + 600, H - 900 + 520, k), 1.0)
    return c

# ========================= x2 · MACRO SCAN =========================
BARS = []
_r = np.random.default_rng(7); x = 0
while x < 900: w_ = int(_r.integers(6, 26)); BARS.append((x, w_)); x += w_ + int(_r.integers(8, 22))
DIGITS = "5 941234 567890"
def macro_frame(t):
    c = Image.new("RGBA", (W, H), (250, 250, 247, 255)); d = ImageDraw.Draw(c)
    if t < PE[0] + 0.2:
        a = 1 - eio(k01(t, PE[0] - 0.1, PE[0] + 0.2))
        for j, (w_, f) in enumerate([("Ai produsul", 120), ("în mână?", 140)]):
            k = eo(k01(t, 0.15 + j * 0.3, 0.6 + j * 0.3)); im = text_img(w_, F("dk", f), INK if j == 0 else GREEN)
            paste(c, fade(im, k * a), 540 - im.width / 2, 620 + j * 170 + (1 - k) * 40)
        hd = lerp(150, 930, eio(k01(t, 0.2, 1.2))); glow_line(c, [(150, 1030), (hd, 1030)], width=10, col=(56, 120, 90))
    if P[1] - 0.3 <= t < PE[2] + 0.3:
        z = lerp(0.7, 1.6, eio(k01(t, P[1] - 0.3, P[1] + 1.5))) if t < P[2] else lerp(1.6, 0.55, eio(k01(t, P[2], P[2] + 0.6)))
        a = eo(k01(t, P[1] - 0.3, P[1] + 0.2)) * (1 - eio(k01(t, PE[2], PE[2] + 0.3)))
        bc = Image.new("RGBA", (1000, 760), (255, 255, 255, 255)); bd = ImageDraw.Draw(bc)
        for xb, wb in BARS: bd.rectangle([50 + xb, 60, 50 + xb + wb, 560], fill=(20, 20, 18))
        nd = int(len(DIGITS) * k01(t, P[1] + 0.9, P[1] + 1.8)); bd.text((500, 640), DIGITS[:nd], font=F("b", 76), fill=(20, 20, 18), anchor="mm")
        if t < P[2] + 0.1:
            u = math.sin((t - P[1]) * 5) * 0.5 + 0.5; ly = 60 + u * 500; ok = t > P[1] + 1.0
            col = (40, 200, 80) if ok else (240, 60, 60)
            glw = Image.new("RGBA", bc.size, (0, 0, 0, 0)); ImageDraw.Draw(glw).rectangle([20, ly - 10, 980, ly + 10], fill=col + (200,))
            bc.alpha_composite(glw.filter(ImageFilter.GaussianBlur(10))); ImageDraw.Draw(bc).rectangle([20, ly - 3, 980, ly + 3], fill=col + (255,))
        im = scaled(bc, z); blur = abs(math.sin((t - P[1]) * 1.3)) * 3 if t < P[1] + 1.0 else 0
        if blur > 0.6: im = im.filter(ImageFilter.GaussianBlur(blur))
        paste(c, fade(im, a), 540 - im.width / 2, 900 - im.height / 2)
        for (cx, cy, sx, sy) in [(90, 360, 1, 1), (990, 360, -1, 1), (90, 1440, 1, -1), (990, 1440, -1, -1)]:
            d.line([(cx, cy), (cx + 120 * sx, cy)], fill=GREEN + (int(255 * a),), width=12); d.line([(cx, cy), (cx, cy + 120 * sy)], fill=GREEN + (int(255 * a),), width=12)
    if P[2] <= t < PE[2] + 0.3:
        a = eo(k01(t, P[2] + 0.2, P[2] + 0.6)) * (1 - eio(k01(t, PE[2], PE[2] + 0.3)))
        cd = Image.new("RGBA", (900, 520), (0, 0, 0, 0)); cdd = ImageDraw.Draw(cd); rr(cdd, [0, 0, 899, 519], 50, fill=WHITE, outline=(220, 228, 216), width=4)
        cdd.text((60, 60), "PRODUS GĂSIT", font=F("b", 38), fill=GREEN); cdd.text((60, 120), "Verifică produsul", font=F("db", 64), fill=INK)
        g = 100 + 50 * eio(k01(t, P[2] + 1.0, P[2] + 1.8))
        rr(cdd, [60, 300, 840, 440], 40, fill=(236, 243, 234)); cdd.ellipse([90, 325, 180, 415], fill=WHITE); cdd.text((135, 370), "−", font=F("b", 60), fill=INK, anchor="mm")
        cdd.ellipse([720, 325, 810, 415], fill=LIME); cdd.text((765, 368), "+", font=F("b", 60), fill=INK, anchor="mm")
        cdd.text((450, 370), f"{int(round(g))} g", font=F("dk", 84), fill=INK, anchor="mm")
        place3d(c, cd, 540, 1320, 1.0, rx=lerp(20, 4, a), alpha=a, shadow=0.35)
        tap(c, 540 + (765 - 450) * 1.0, 1320 + (370 - 260), t, P[2] + 1.0, GREEN)
    if P[3] <= t < PE[3] + 0.3:
        a = 1 - eio(k01(t, PE[3], PE[3] + 0.3)); k = eback(k01(t, P[3], P[3] + 0.45), 1.7)
        r = 1400 * eio(k01(t, P[3], P[3] + 0.5)); d.ellipse([540 - r, 960 - r, 540 + r, 960 + r], fill=LIME + (int(255 * a),))
        if k > 0.2:
            s = 200 * min(1.1, k); d.line([(540 - s * 0.45, 960), (540 - s * 0.08, 960 + s * 0.35), (540 + s * 0.5, 960 - s * 0.32)], fill=INK + (int(255 * a),), width=36, joint="curve")
        im = text_img("Confirmat.", F("dk", 110), INK); paste(c, fade(im, a * eo(k01(t, P[3] + 0.3, P[3] + 0.7))), 540 - im.width / 2, 1260)
    if t >= P[4]:
        k = eo(k01(t, P[4], P[4] + 0.5)); lg = scaled(LOGO, 0.22); paste(c, fade(lg, k), 540 - lg.width / 2, 470)
        im = text_img("Scrie în comentarii", F("s", 54), INK); paste(c, fade(im, k), 540 - im.width / 2, 820)
        logo_pill(c, KW, 1060, eo(k01(t, P[4] + 0.3, P[4] + 0.7)), bg=INK, fg=LIME, s=0.8 + 0.2 * eback(k01(t, P[4] + 0.3, P[4] + 0.8), 1.8))
    return c

# ========================= x3 · KINETIC TYPE =========================
BGS = [LIME, DARK, WHITE, GREEN, (216, 135, 85)]
EMPH = {"buget", "lei", "planul", "cumpărături", "profil", "PLAN", "săptămână"}
WT = [w for i in range(4) for w in words_timing(i)]
def kinetic_frame(t):
    if t >= P[4]:
        c = Image.new("RGBA", (W, H), LIME + (255,)); k = eback(k01(t, P[4], P[4] + 0.4), 2.0)
        im = text_img("Scrie", F("dk", 170), INK); paste(c, scaled(im, max(0.05, k)), 540 - im.width * k / 2, 520)
        logo_pill(c, KW, 960, 1.0, bg=INK, fg=LIME, s=max(0.05, eback(k01(t, P[4] + 0.25, P[4] + 0.65), 2.2)))
        im = text_img("în comentarii", F("dk", 110), INK); paste(c, fade(im, eo(k01(t, P[4] + 0.5, P[4] + 0.9))), 540 - im.width / 2, 1180)
        lg = scaled(LOGO, 0.12); paste(c, lg, 540 - lg.width / 2, 1500)
        return c
    cur = None
    for j, (w, a, b) in enumerate(WT):
        if a <= t < (WT[j + 1][1] if j + 1 < len(WT) else P[4]): cur = (j, w, a)
    if t < WT[0][1] or cur is None:
        c = Image.new("RGBA", (W, H), DARK + (255,)); hd = lerp(150, 930, eio(k01(t, 0.0, 0.5))); glow_line(c, [(150, 960), (hd, 960)], width=12); return c
    j, w, a = cur; bg = BGS[j % len(BGS)]; fg = INK if bg in (LIME, WHITE, (216, 135, 85)) else WHITE
    c = Image.new("RGBA", (W, H), bg + (255,))
    emph = w.strip().lower() in {e.lower() for e in EMPH}
    size = 230 if emph else 170
    f = F("dk", size); tw = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textlength(w, font=f)
    if tw > 960: f = F("dk", int(size * 960 / tw))
    im = text_img(w, f, (GREEN if (emph and bg in (LIME, WHITE)) else (LIME if emph else fg)))
    k = eback(k01(t, a, a + 0.18), 2.4); lt = t - a
    s = 0.6 + 0.4 * k + 0.04 * lt; rot = (j % 2 * 2 - 1) * 3 * (1 - eo(k01(t, a, a + 0.25)))
    lay = scaled(im, max(0.05, s)).rotate(rot, Image.BICUBIC, expand=True)
    paste(c, lay, 540 - lay.width / 2, 960 - lay.height / 2)
    prev = WT[j - 1][0] if j > 0 else ""
    if prev:
        pim = text_img(prev, F("dk", 60), fg); paste(c, fade(pim, 0.25), 540 - pim.width / 2, 600)
    bar = k01(t, P[0], P[4]); ImageDraw.Draw(c).rectangle([0, H - 14, W * bar, H], fill=(GREEN if bg != GREEN else LIME))
    return c

# ========================= x4 · REAL SCREEN RECORDING =========================
RECF = sorted(f for f in os.listdir(REC) if f[:3].isdigit())
def rec(name): return cap(os.path.join(REC, name))
SX = 1080 / 1170
def screenrec_frame(t):
    c = Image.new("RGBA", (W, H), (20, 24, 21, 255))
    if t < P[1] + 0.3: img = rec(RECF[0]); zc, zz = (540, 900), 1.0
    elif t < P[1] + 0.95:
        idx = min(9, 2 + int((t - P[1] - 0.3) / 0.08)); img = rec(RECF[idx]); zc, zz = (540, 900), 1.0
    elif t < P[2]: img = rec(RECF[10]); zc, zz = (540, 600), lerp(1.0, 1.25, eio(k01(t, P[1] + 1.0, P[1] + 1.8)))
    elif t < P[3]:
        img = rec(RECF[10]) if t < P[2] + 0.5 else rec("add_modal.png"); zc, zz = (540, 760), (1.25 if t < P[2] + 0.5 else lerp(1.15, 1.0, eio(k01(t, P[2] + 0.5, P[2] + 1.2))))
    else:
        img = rec(RECF[10]) if t < P[3] + 0.5 else rec("more_light.png"); zc, zz = (540, 760), (1.25 if t < P[3] + 0.5 else 1.08)
    scr = img.resize((W, round(img.height * SX))).convert("RGBA")
    m = Image.new("L", scr.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, scr.width - 1, scr.height - 1], 60, fill=255); scr.putalpha(m)
    canvas = Image.new("RGBA", (W, H), (20, 24, 21, 255)); paste(canvas, scr, 0, 40)
    d = ImageDraw.Draw(canvas)
    # taps, in capture css px * 3 * SX, +40
    def px(x, y): return (x * 3 * SX, y * 3 * SX + 40)
    tx, ty = px(354, 540); tap(canvas, tx, ty, t, P[1], GREEN)
    if P[2] <= t < P[2] + 0.6: tx, ty = px(153, 336); tap(canvas, tx, ty, t, P[2] + 0.05, GREEN)
    if P[3] <= t < P[3] + 0.6: tx, ty = px(150, 366); tap(canvas, tx, ty, t, P[3] + 0.05, GREEN)
    if t >= P[3] + 0.5 and t < P[4]:
        hx, hy = (855 * SX, 895 * SX + 40); r = 150 + 12 * math.sin(t * 7); d.rounded_rectangle([hx - 250, hy - 120, hx + 250, hy + 120], 50, outline=LIME2, width=10)
    # zoom
    if zz != 1.0:
        cw, ch = W / zz, H / zz; x0 = min(max(zc[0] - cw / 2, 0), W - cw); y0 = min(max(zc[1] - ch / 2, 0), H - ch)
        canvas = canvas.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + cw, y0 + ch))
    c.alpha_composite(canvas)
    # TikTok-style caption at the top
    for i in range(4):
        if P[i] - 0.05 <= t < PE[i] + 0.1:
            tiktok_caption(c, SUBS[i], 150, eo(k01(t, P[i] - 0.05, P[i] + 0.2)))
    # REC chip
    d2 = ImageDraw.Draw(c); rr(d2, [40, 60, 270, 120], 30, fill=(0, 0, 0, 150)); d2.ellipse([60, 75, 90, 105], fill=(240, 60, 60) if int(t * 2) % 2 == 0 else (120, 40, 40))
    d2.text((105, 90), "ecran real", font=F("b", 32), fill=WHITE, anchor="lm")
    if t >= P[4]:
        k = eo(k01(t, P[4], P[4] + 0.5)); sheet = Image.new("RGBA", (W, 1000), (0, 0, 0, 0)); sd = ImageDraw.Draw(sheet)
        rr(sd, [0, 0, W, 1060], 70, fill=MINT + (255,)); lg = scaled(LOGO, 0.16); sheet.alpha_composite(lg, (540 - lg.width // 2, 70))
        sd.text((540, 330), "Scrie în comentarii", font=F("s", 52), fill=INK, anchor="mm")
        paste(c, sheet, 0, lerp(H, H - 1000, k)); logo_pill(c, KW, lerp(H + 600, H - 1000 + 520, k), 1.0)
    return c

# ========================= x5 · SPLIT SCREEN =========================
def split_frame(t):
    merge = eio(k01(t, P[4], P[4] + 0.6)); mid = lerp(960, 1920 + 200, merge) if t >= P[4] else 960
    c = Image.new("RGBA", (W, H), LIME + (255,)); d = ImageDraw.Draw(c); d.rectangle([0, 0, W, mid], fill=DARK)
    if t < PE[0] + 0.2:
        a = 1 - eio(k01(t, PE[0] - 0.1, PE[0] + 0.2))
        im = text_img("Ce primești", F("dk", 120), WHITE); paste(c, fade(im, eo(k01(t, 0.1, 0.5)) * a), 540 - im.width / 2, 760)
        im = text_img("gratuit?", F("dk", 140), INK); paste(c, fade(im, eo(k01(t, 0.4, 0.8)) * a), 540 - im.width / 2, 990)
    def label(txt, y, col, a): im = text_img(txt, F("b", 44), col); paste(c, fade(im, a), 80, y)
    if P[1] <= t < P[4] + 0.6:
        a = eo(k01(t, P[1], P[1] + 0.4)) * (1 - merge)
        label("GRATUIT", 200, (178, 231, 154), a)
        for j, it in enumerate(["Jurnalul", "Înregistrarea meselor"]):
            k = eo(k01(t, P[1] + 0.2 + j * 0.35, P[1] + 0.6 + j * 0.35)); im = text_img(("✓ " if False else "") + it, F("db", 76), WHITE)
            d.ellipse([lerp(-200, 80, k), 330 + j * 150, lerp(-200, 80, k) + 60, 390 + j * 150], fill=LIME2 + (int(255 * a),))
            paste(c, fade(im, k * a), lerp(-600, 170, k), 318 + j * 150)
    if P[2] <= t < P[4] + 0.6:
        a = eo(k01(t, P[2], P[2] + 0.4)) * (1 - merge)
        label("PREMIUM", 1020, GREEN, a)
        for j, it in enumerate(["Plan personal", "Analiză AI", "Ținte zilnice"]):
            k = eo(k01(t, P[2] + 0.2 + j * 0.3, P[2] + 0.6 + j * 0.3)); im = text_img(it, F("db", 76), INK)
            d.ellipse([lerp(1300, 80, k), 1150 + j * 140, lerp(1300, 80, k) + 60, 1210 + j * 140], fill=INK + (int(255 * a),))
            paste(c, fade(im, k * a), lerp(1500, 170, k), 1138 + j * 140)
    if P[3] <= t < P[4] + 0.6:
        k = eback(k01(t, P[3], P[3] + 0.45), 1.8); a = 1 - merge
        st = Image.new("RGBA", (520, 300), (0, 0, 0, 0)); sd = ImageDraw.Draw(st); rr(sd, [0, 0, 519, 299], 50, fill=INK + (255,))
        sd.text((260, 120), "25 lei", font=F("dk", 120), fill=LIME, anchor="mm"); sd.text((260, 230), "pe lună · 79,99/an", font=F("s", 40), fill=WHITE, anchor="mm")
        st = st.rotate(-8, Image.BICUBIC, expand=True); paste(c, fade(scaled(st, max(0.05, 1.6 - 0.6 * k)), min(1, k) * a), 690 - st.width * (1.6 - 0.6 * k) / 2, 1560 - st.height * (1.6 - 0.6 * k) / 2)
    if t >= P[1] - 0.2 and t < P[4] + 0.6:
        rot = (t * 90) % 360; vs = Image.new("RGBA", (200, 200), (0, 0, 0, 0)); vd = ImageDraw.Draw(vs); vd.ellipse([0, 0, 199, 199], fill=WHITE, outline=INK, width=8)
        vd.text((100, 102), "VS", font=F("dk", 80), fill=INK, anchor="mm"); vs = vs.rotate(6 * math.sin(t * 3), Image.BICUBIC)
        paste(c, fade(vs, 1 - merge), 540 - 100, mid - 100)
    if t >= P[4]:
        k = eo(k01(t, P[4] + 0.3, P[4] + 0.8)); lg = scaled(LOGO, 0.2); paste(c, fade(lg, k), 540 - lg.width / 2, 520)
        im = text_img("Scrie în comentarii", F("s", 54), INK); paste(c, fade(im, k), 540 - im.width / 2, 850)
        logo_pill(c, KW, 1080, k, bg=INK, fg=LIME)
    return c

# ========================= x6 · POV =========================
HOME = cap(os.path.join(ENGINE, "a_home.png")); SIGN = rec("signup.png")
def pov_frame(t):
    c = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    g = np.linspace(0, 1, H)[:, None]; room = (np.array([62, 48, 36]) * (1 - g) + np.array([24, 20, 18]) * g)
    c = Image.fromarray(np.dstack([np.repeat(room[:, None, :], W, 1)[:, :, 0, :].astype(np.uint8) if False else np.broadcast_to(room[:, None, :], (H, W, 3)).astype(np.uint8)]).squeeze(), "RGB").convert("RGBA")
    paste(c, fade(scaled(R.GLOW_W, 1.4), 0.9), 540 - R.GLOW_W.width * 0.7, 600 - R.GLOW_W.width * 0.7)
    shake = (6 * math.sin(t * 2.3) + 3 * math.sin(t * 5.1), 5 * math.cos(t * 1.9))
    whip = k01(t, P[2] - 0.15, P[2] + 0.35)
    def phone_with(img):
        scr = Image.new("RGB", (AS.SW, AS.SH), MINT); sc = img.resize((AS.SW, round(img.height * AS.SW / img.width))); scr.paste(sc, (0, 150)); return R.phone_img(scr)
    if t < P[2] + 0.2:
        ph = phone_with(SIGN if t >= P[1] else HOME); ox = -1400 * eio(whip)
        place3d(c, ph, 540 + shake[0] + ox, 1130 + shake[1], 0.52, rz=-4 + 2 * math.sin(t), rx=8, shadow=0.7)
        if t >= P[1]: tap(c, 540 + ox, 1130 + 380, t, P[1] + 0.4)
    if t >= P[2] - 0.15:
        ox = 1400 * (1 - eio(whip))
        lap = Image.new("RGBA", (1000, 700), (0, 0, 0, 0)); ld = ImageDraw.Draw(lap); rr(ld, [70, 0, 930, 590], 30, fill=(28, 30, 29, 255)); rr(ld, [0, 590, 1000, 660], 24, fill=(160, 158, 152, 255))
        view = HOME.crop((0, 0, 1170, 760)).resize((820, 535)); lap.paste(view, (90, 25))
        s3 = t >= P[3]; lx = 540 + ox + (110 if s3 else 0)
        place3d(c, lap, lx + shake[0] * 0.5, 1050, 0.95 if not s3 else lerp(0.95, 0.78, eio(k01(t, P[3], P[3] + 0.5))), rx=6, shadow=0.6)
        if s3:
            ks = eo(k01(t, P[3], P[3] + 0.5)); place3d(c, phone_with(HOME), lerp(-200, 210, ks), 1230, 0.32, rz=-6, alpha=ks, shadow=0.6)
            for j in range(3):
                u = ((t * 0.9 + j / 3) % 1); p = lerp2((300, 1150), (560, 1000), u); a = math.sin(u * math.pi)
                ImageDraw.Draw(c).ellipse([p[0] - 13, p[1] - 13, p[0] + 13, p[1] + 13], fill=LIME2 + (int(255 * a),))
    if 0 < whip < 1:
        c = c.filter(ImageFilter.BoxBlur(0)) if False else c
        mb = c.resize((W // 8, H), Image.BILINEAR).resize((W, H), Image.BILINEAR); c = Image.blend(c, mb, math.sin(whip * math.pi) * 0.85)
    caps = ["POV: ai notat micul dejun pe telefon", "Intri în cont", "...și la birou e deja pe laptop", "Același jurnal, oriunde."]
    for i in range(4):
        if P[i] - 0.05 <= t < PE[i] + 0.1: tiktok_caption(c, caps[i], 180, eo(k01(t, P[i] - 0.05, P[i] + 0.2)), size=68)
    if t >= P[4]:
        k = eo(k01(t, P[4], P[4] + 0.5)); ov = Image.new("RGBA", (W, H), DARK + (int(225 * k),)); c.alpha_composite(ov)
        lg = scaled(LOGO, 0.22); paste(c, fade(lg, k), 540 - lg.width / 2, 470); tiktok_caption(c, "Scrie în comentarii", 820, k, size=56)
        logo_pill(c, KW, 1080, eo(k01(t, P[4] + 0.3, P[4] + 0.7)))
    return c

# ========================= x7 · DAY TIMELAPSE =========================
SKY = [(0.0, (246, 214, 168), (159, 208, 232)), (0.33, (126, 194, 240), (207, 233, 255)), (0.62, (243, 178, 122), (226, 200, 220)), (0.85, (40, 50, 90), (90, 80, 120)), (1.0, (11, 20, 48), (27, 42, 74))]
def sky_at(u):
    for (a, t0, b0), (b, t1, b1) in zip(SKY, SKY[1:]):
        if a <= u <= b: k = (u - a) / (b - a); return tuple(int(lerp(x, y, k)) for x, y in zip(t0, t1)), tuple(int(lerp(x, y, k)) for x, y in zip(b0, b1))
    return SKY[-1][1], SKY[-1][2]
MOM = [("Mic dejun", "07:30"), ("Prânz", "13:00"), ("Gustare", "16:30"), ("Cină", "20:00")]
def day_frame(t):
    u = k01(t, 0, P[4]); top, bot = sky_at(u)
    g = np.linspace(0, 1, H)[:, None, None]; arr = (np.array(top) * (1 - g) + np.array(bot) * g)
    c = Image.fromarray(np.broadcast_to(arr, (H, W, 3)).astype(np.uint8), "RGB").convert("RGBA"); d = ImageDraw.Draw(c)
    ang = math.pi * (1 - u); sx, sy = 540 + 460 * math.cos(ang), 760 - 520 * math.sin(ang)
    night = u > 0.8
    sun = Image.new("RGBA", (400, 400), (0, 0, 0, 0)); sd = ImageDraw.Draw(sun)
    sd.ellipse([100, 100, 300, 300], fill=((240, 240, 230) if night else (255, 230, 140)) + (255,)); sun = sun.filter(ImageFilter.GaussianBlur(2))
    glow = Image.new("RGBA", (700, 700), (255, 230, 160, 0)); ImageDraw.Draw(glow).ellipse([150, 150, 550, 550], fill=(255, 230, 160, 90)); glow = glow.filter(ImageFilter.GaussianBlur(80))
    paste(c, glow, sx - 350, sy - 350); paste(c, sun, sx - 200, sy - 200)
    if night:
        for j in range(40):
            x, y = (j * 263) % W, (j * 137) % 900; d.ellipse([x, y, x + 4, y + 4], fill=(255, 255, 255, int(200 * k01(u, 0.8, 0.95))))
    hours = lerp(7.5, 21.5, u); tc = INK if u < 0.75 else WHITE
    clk = f"{int(hours):02d}:{int((hours % 1) * 60):02d}"; im = text_img(clk, F("dk", 150), tc); paste(c, im, 540 - im.width / 2, 900)
    # timeline of moments
    for j, (n, hh) in enumerate(MOM):
        tj = [P[0] + 0.05, P[0] + 0.55, P[0] + 1.1, P[0] + 1.6][j]; k = eback(k01(t, tj, tj + 0.35), 1.4)
        if k <= 0 or t >= P[2] + 0.2: continue
        cd = Image.new("RGBA", (860, 140), (0, 0, 0, 0)); cdd = ImageDraw.Draw(cd); rr(cdd, [0, 0, 859, 139], 44, fill=(255, 255, 255, 235))
        cdd.text((50, 70), n, font=F("db", 60), fill=INK, anchor="lm"); cdd.text((810, 70), hh, font=F("b", 46), fill=GREEN, anchor="rm")
        a = 1 - eio(k01(t, P[2] - 0.1, P[2] + 0.2)); yy = 1130 + j * 160 if t < P[1] else lerp(1130 + j * 160, 1130 + j * 160 - 40 * math.sin(j), eo(k01(t, P[1], P[1] + 0.5)))
        place3d(c, cd, 540, yy, max(0.05, min(1.05, k)), rx=lerp(25, 0, min(1, k)), alpha=min(1, k) * a, shadow=0.25)
    if P[2] <= t < P[4]:
        k = eo(k01(t, P[2], P[2] + 0.7)); o = eio(k01(t, P[3] - 0.1, P[3] + 0.3))
        scr = Image.new("RGB", (AS.SW, AS.SH), (17, 35, 27)); hm = cap(os.path.join(ENGINE, "ov", "home_macros.png")); hm = hm.resize((AS.SW, round(hm.height * AS.SW / hm.width))); scr.paste(hm, (0, 150))
        place3d(c, R.phone_img(scr), 540, lerp(2300, 1350, k), 0.42, ry=-8, alpha=1 - o, shadow=0.6)
    if P[3] <= t < P[4] + 0.3:
        k = eo(k01(t, P[3], P[3] + 0.8)); a = 1 - eio(k01(t, P[4], P[4] + 0.3))
        ring = Image.new("RGBA", (620, 620), (0, 0, 0, 0)); rd = ImageDraw.Draw(ring); rd.ellipse([30, 30, 590, 590], outline=(255, 255, 255, 60), width=54)
        for jj, (col, fr) in enumerate([((178, 231, 154), 0.38), ((216, 135, 85), 0.33), ((118, 156, 187), 0.2)]):
            st = -90 + 360 * sum(f for _, f in [((0), 0.38), ((0), 0.33), ((0), 0.2)][:jj]); rd.arc([30, 30, 590, 590], st, st + 360 * fr * k, fill=col + (255,), width=54)
        rd.text((310, 290), "Totalul", font=F("db", 64), fill=WHITE, anchor="mm"); rd.text((310, 365), "zilei", font=F("db", 64), fill=WHITE, anchor="mm")
        paste(c, fade(ring, a * min(1, k * 2)), 540 - 310, 1150)
    if t >= P[4]:
        k = eo(k01(t, P[4], P[4] + 0.5)); lg = scaled(LOGO, 0.22); paste(c, fade(lg, k), 540 - lg.width / 2, 1100)
        tiktok_caption(c, "Scrie în comentarii", 1430, k, size=54); logo_pill(c, KW, 1640, eo(k01(t, P[4] + 0.3, P[4] + 0.7)))
    return c

FRAME = {"x1": chat_frame, "x2": macro_frame, "x3": kinetic_frame, "x4": screenrec_frame, "x5": split_frame, "x6": pov_frame, "x7": day_frame}[KEY]
SUBS_ON = KEY in ("x2", "x5", "x7")
def subtitles(c, t):
    for i, txt in enumerate(SUBS):
        a = P[i]; b = PE[i]
        if a - 0.05 <= t < b + 0.2 and i < 4:
            k = eo(k01(t, a - 0.05, a + 0.2)) * (1 - eio(k01(t, b, b + 0.2)))
            im = text_img(txt, F("b", 46), WHITE); pad = Image.new("RGBA", (im.width + 40, im.height + 8), (0, 0, 0, 0))
            ImageDraw.Draw(pad).rounded_rectangle([0, 0, pad.width - 1, pad.height - 1], 34, fill=(6, 9, 7, 180)); pad.alpha_composite(im, (20, 4))
            if pad.width > 1000: pad = scaled(pad, 1000 / pad.width)
            paste(c, fade(pad, k), W / 2 - pad.width / 2, 1760)

def frame(t):
    c = FRAME(t)
    if SUBS_ON: subtitles(c, t)
    c.alpha_composite(R.GRAIN[int(t * 60) % 8])
    if t < 0.04: c = Image.blend(Image.new("RGBA", (W, H), (0, 0, 0, 255)), c, t / 0.04)
    if t > DUR - 0.35: c = Image.blend(c, Image.new("RGBA", (W, H), (0, 0, 0, 255)), k01(t, DUR - 0.35, DUR))
    return c.convert("RGB")

# ========================= music, one style per format =========================
def t_(d): return np.arange(int(d * AU.SR)) / AU.SR
def kick(g=1.0): x = t_(0.35); return np.sin(2 * np.pi * (45 + 110 * np.exp(-x * 30)) * x) * np.exp(-x * 9) * g
def hat(): n = np.random.default_rng(1).standard_normal(int(0.05 * AU.SR)); return np.diff(n * np.exp(-t_(0.05) * 90), prepend=0)
def clap(): n = np.random.default_rng(2).standard_normal(int(0.18 * AU.SR)); return n * np.exp(-t_(0.18) * 22)
def chordpad(b, chords, seg, g=0.02, bright=1.0):
    for ci in range(int(DUR / seg) + 1):
        ch = chords[ci % len(chords)]; x = t_(seg + 1.0); e = np.minimum(1, x / 0.4) * np.minimum(1, np.maximum(0, (seg + 1.0 - x) / 1.0))
        for f in ch: AU.place(b, (np.sin(2 * np.pi * f * x) + 0.3 * bright * np.sin(4 * np.pi * f * x)) * e, ci * seg, g)
def music(style):
    N = AU.N; b = np.zeros((N, 2)); C1 = [[220, 277.2, 329.6], [185, 233.1, 277.2], [196, 246.9, 293.7], [164.8, 207.7, 246.9]]
    if style == "house":
        bt = 60 / 124
        for i in range(int(DUR / bt)):
            at = i * bt; AU.place(b, kick(), at, 0.9); AU.place(b, hat(), at + bt / 2, 0.22)
            if i % 2: AU.place(b, clap(), at, 0.25)
            f0 = [55, 55, 73.4, 65.4][(i // 4) % 4]; x = t_(bt * 0.45); AU.place(b, (np.sign(np.sin(2 * np.pi * f0 * x)) * 0.4 + np.sin(2 * np.pi * f0 * x)) * np.exp(-x * 6), at + bt / 2, 0.18)
        chordpad(b, C1, bt * 8, 0.016, 1.5)
    elif style == "lofi":
        bt = 60 / 82
        for i in range(int(DUR / bt)):
            at = i * bt + (0.03 if i % 2 else 0); AU.place(b, kick(0.8), at, 0.6 if i % 2 == 0 else 0)
            if i % 2: AU.place(b, clap() * 0.6, at, 0.2)
            for h in range(2): AU.place(b, hat() * 0.6, at + h * bt / 2 + 0.02, 0.12)
        chordpad(b, [[261.6, 329.6, 392, 493.9], [220, 261.6, 329.6, 392], [174.6, 220, 261.6, 329.6], [196, 246.9, 293.7, 349.2]], bt * 4, 0.02, 0.3)
        crackle = np.random.default_rng(3).standard_normal(N) * (np.random.default_rng(4).random(N) > 0.9993) * 0.4; b[:, 0] += crackle; b[:, 1] += crackle
    elif style == "tech":
        bt = 60 / 110
        for i in range(int(DUR / bt)):
            AU.place(b, kick(0.7), i * bt, 0.6 if i % 4 in (0, 3) else 0)
            for s in range(4): AU.place(b, AU.tick(3200 if s % 2 else 2400, 0.012), i * bt + s * bt / 4, 0.08)
        x = t_(DUR); AU.place(b, np.sin(2 * np.pi * 55 * x) * (0.5 + 0.5 * np.sin(2 * np.pi * x / (bt * 2))) , 0, 0.08)
    elif style == "pluck":
        bt = 60 / 100; notes = [523.3, 659.3, 784, 659.3, 587.3, 698.5, 880, 698.5]
        for i in range(int(DUR / (bt / 2))):
            x = t_(0.4); f = notes[i % len(notes)]; AU.place(b, (np.sin(2 * np.pi * f * x) + 0.3 * np.sin(4 * np.pi * f * x)) * np.exp(-x * 9), i * bt / 2, 0.06)
        for i in range(int(DUR / bt)):
            AU.place(b, kick(0.7), i * bt, 0.6 if i % 2 == 0 else 0); AU.place(b, clap() * 0.7, i * bt, 0.18 if i % 2 else 0)
        chordpad(b, C1, bt * 4, 0.014)
    elif style == "upbeat":
        bt = 60 / 116
        for i in range(int(DUR / bt)):
            AU.place(b, kick(), i * bt, 0.85); AU.place(b, hat(), i * bt + bt / 2, 0.25); AU.place(b, hat() * 0.5, i * bt + bt / 4, 0.1)
            if i % 2: AU.place(b, clap(), i * bt, 0.3)
        for i in range(int(DUR / (bt / 2))):
            x = t_(0.2); f = [440, 554.4, 659.3, 554.4][i % 4]; AU.place(b, np.sin(2 * np.pi * f * x) * np.exp(-x * 14), i * bt / 2, 0.05)
    else:
        AU.DUR = DUR; return AU.music()
    fade_ = np.minimum(1, np.arange(N) / (0.2 * AU.SR)) * np.minimum(1, (N - np.arange(N)) / (0.8 * AU.SR))
    return np.tanh(b * 1.1) * fade_[:, None]

STYLE = {"x1": "lofi", "x2": "tech", "x3": "house", "x4": "pluck", "x5": "upbeat", "x6": "lofi", "x7": "ambient"}[KEY]
def build_audio():
    AU.DUR = DUR; AU.N = int(AU.SR * DUR); N = AU.N; s = np.zeros((N, 2))
    AU.place(s, AU.soft_impact(), 0.05, 0.4)
    for p in P[1:5]: AU.place(s, AU.whoosh(0.4, 1.2), p - 0.28, 0.3)
    if KEY == "x1":
        for tt in [P[0] + 0.1, P[1] + 0.1, P[2], P[3], P[3] + 0.8]: AU.place(s, AU.pop(1200), tt, 0.25)
    if KEY == "x2":
        AU.place(s, AU.scanner_beep(), P[1] + 1.0, 0.25); AU.place(s, AU.laser_hum(1.2), P[1] + 0.1, 0.1); AU.place(s, AU.key_click(), P[2] + 1.0, 0.4); AU.place(s, AU.success_chime(), P[3] + 0.1, 0.25)
    if KEY == "x3":
        for w, a, _ in WT: AU.place(s, AU.tick(1800, 0.02), a, 0.15)
    if KEY == "x4":
        for tt in [P[1], P[2] + 0.05, P[3] + 0.05]: AU.place(s, AU.key_click(), tt, 0.45)
    if KEY == "x5":
        for tt in [P[1] + 0.2, P[1] + 0.55, P[2] + 0.2, P[2] + 0.5, P[2] + 0.8]: AU.place(s, AU.whoosh(0.25, 1.8), tt, 0.25)
        AU.place(s, AU.soft_impact(), P[3] + 0.2, 0.6)
    if KEY == "x6": AU.place(s, AU.whoosh(0.5, 0.9), P[2] - 0.2, 0.7); AU.place(s, AU.key_click(), P[1] + 0.4, 0.4)
    if KEY == "x7":
        for j in range(4): AU.place(s, AU.pop(900 + j * 150), [P[0] + 0.05, P[0] + 0.55, P[0] + 1.1, P[0] + 1.6][j], 0.2)
    AU.place(s, AU.success_chime(), P[4] + 0.4, 0.15)
    m = music(STYLE); v = np.zeros((N, 2)); AU.place(v, AU.load_mp3(os.path.join(HERE, MP3)), VO, 1.0)
    vel = np.abs(v[:, 0]); kk = np.ones(int(0.12 * AU.SR)) / int(0.12 * AU.SR); duck = 1 - 0.45 * np.clip(np.convolve(vel, kk, "same") * 12, 0, 1)
    mix = (v * 0.95 + np.tanh(s * 1.2) * 0.7 + m * 0.9 * duck[:, None]) * 0.7
    raw = os.path.join(HERE, f"{KEY}_mix_raw.wav"); AU.write(raw, mix); out = os.path.join(HERE, f"{KEY}_mix.wav")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", raw, "-af", "loudnorm=I=-14:TP=-1.0:LRA=9", "-ar", "48000", out], check=True); os.remove(raw)

if __name__ == "__main__":
    mode = sys.argv[2]
    if mode == "frames":
        for tp in [float(x) for x in sys.argv[3].split(",")]: frame(tp).save(os.path.join(HERE, f"{KEY}_f{tp:05.2f}.png"))
        print(KEY, [round(p, 2) for p in P], DUR)
    elif mode == "audio": build_audio()
    elif mode == "seg":
        i, n = int(sys.argv[3]), int(sys.argv[4]); fps = 60; N = int(round(DUR * fps)); a, b = N * i // n, N * (i + 1) // n
        ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1080x1920", "-r", str(fps), "-i", "-",
                               "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p", os.path.join(HERE, f"{KEY}_seg{i}.mp4")], stdin=subprocess.PIPE)
        for k in range(a, b): ff.stdin.write(frame(k / fps).tobytes())
        ff.stdin.close(); ff.wait()

"""Two extra reels in new formats.

    python3 formats_extra.py <g1|g2> frames 1,4 | audio | seg i n
g1 delivery unboxing (food ordered online, logged in the journal) · g2 city map (restaurant assistant)
Glovo is named in the voice and text only: no logo, no brand colours, no partnership implied.
"""
import math, os, re, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__)); SPOT = os.path.join(HERE, "..", "spot"); ENGINE = os.path.join(HERE, "..", "engine")
sys.path.insert(0, SPOT)
import render as R
import audio as AU
from render import W, H, k01, eo, eio, eback, lerp, lerp2, paste, fade, scaled, place3d, glow_line, text_img, AS, LOGO, F

KEY = sys.argv[1]
MP3 = {"g1": "g1_glovo.mp3", "g2": "g2_asistent.mp3"}[KEY]; KW = "JURNAL"
SUBS = {"g1": ["Ai comandat pe Glovo?", "Deschizi jurnalul.", "Cauți restaurantul și produsul.", "Pui porția și gata, e în jurnal.", "Scrie JURNAL în comentarii!"],
        "g2": ["Ai mâncat în oraș?", "Spui asistentului ce ai mâncat și de unde.", "Caută restaurantul în orașul tău și produsul din meniu.", "Îți arată sursa, tu confirmi și intră în jurnal.", "Scrie JURNAL în comentarii!"]}[KEY]
VO = 0.45
INK = (8, 30, 22); LIME = (199, 240, 130); LIME2 = (148, 230, 2); GREEN = (37, 94, 70); WHITE = (255, 255, 255); MINT = (244, 246, 241); KRAFT = (196, 160, 112)

def phrase_starts(mp3):
    x = AU.load_mp3(mp3)
    out = subprocess.run(["ffmpeg", "-hide_banner", "-i", mp3, "-af", "silencedetect=noise=-38dB:d=0.25", "-f", "null", "-"], capture_output=True, text=True).stderr
    ends = [float(v) for v in re.findall(r"silence_end: ([0-9.]+)", out)]
    return [s + VO for s in ([AU.onset(x)] + [e for e in ends if e < len(x) / AU.SR - 0.2])[:5]], len(x) / AU.SR + VO
P, VEND = phrase_starts(os.path.join(HERE, MP3)); DUR = round(VEND + 1.6, 2); PE = [P[i + 1] - 0.12 if i < 4 else DUR for i in range(5)]

def rr(d, b, r, **k): d.rounded_rectangle(b, r, **k)
def cap(n): return Image.open(os.path.join(ENGINE, n)).convert("RGB")
def phone_of(img):
    scr = Image.new("RGB", (AS.SW, AS.SH), MINT); sc = img.resize((AS.SW, round(img.height * AS.SW / img.width))); scr.paste(sc, (0, 150)); return R.phone_img(scr)
def tap(c, x, y, t, t0, col=LIME2):
    k = k01(t, t0, t0 + 0.45)
    if 0 < k < 1:
        d = ImageDraw.Draw(c); r = lerp(24, 100, eo(k)); d.ellipse([x - r, y - r, x + r, y + r], outline=col + (int(230 * (1 - k)),), width=8)
        if k < 0.35: d.ellipse([x - 30, y - 30, x + 30, y + 30], fill=(255, 255, 255, int(170 * (1 - k / 0.35))))
def pill_kw(c, cy, a, s=1.0, bg=LIME, fg=INK):
    fnt = F("dk", 150); w = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textlength(KW, font=fnt)
    pim = Image.new("RGBA", (int(w + 140), 230), (0, 0, 0, 0)); ImageDraw.Draw(pim).rounded_rectangle([0, 0, pim.width - 1, 229], 64, fill=bg + (255,))
    ImageDraw.Draw(pim).text((pim.width / 2, 118), KW, font=fnt, fill=fg, anchor="mm"); s *= min(1, 900 / pim.width)
    paste(c, fade(scaled(pim, max(0.05, s)), a), 540 - pim.width * s / 2, cy - pim.height * s / 2)
def subtitles(c, t):
    for i, txt in enumerate(SUBS[:4]):
        a, b = P[i], PE[i]
        if a - 0.05 <= t < b + 0.2:
            k = eo(k01(t, a - 0.05, a + 0.2)) * (1 - eio(k01(t, b, b + 0.2)))
            im = text_img(txt, F("b", 46), WHITE); pad = Image.new("RGBA", (im.width + 40, im.height + 8), (0, 0, 0, 0))
            ImageDraw.Draw(pad).rounded_rectangle([0, 0, pad.width - 1, pad.height - 1], 34, fill=(6, 9, 7, 185)); pad.alpha_composite(im, (20, 4))
            if pad.width > 1000: pad = scaled(pad, 1000 / pad.width)
            paste(c, fade(pad, k), W / 2 - pad.width / 2, 1760)

# ========================= g1 · DELIVERY UNBOXING =========================
TABLE = Image.open(os.path.join(SPOT, "assets", "table.png")).convert("RGBA").resize((W, H))
def bag(open_k=0.0):
    im = Image.new("RGBA", (620, 820), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.polygon([(40, 140), (580, 140), (600, 800), (20, 800)], fill=KRAFT)
    for x in range(60, 580, 46): d.line([(x, 150), (x - 8, 790)], fill=(184, 148, 100), width=2)
    top = lerp(0, -60, open_k); d.polygon([(40, 140 + top), (580, 140 + top), (560, 60 + top * 2), (60, 60 + top * 2)], fill=(176, 140, 95))
    d.arc([230, 20 + top * 2, 390, 160 + top * 2], 180, 360, fill=(150, 116, 76), width=14)
    rr(d, [120, 330, 500, 620], 24, fill=(252, 250, 244)); d.text((150, 360), "COMANDA TA", font=F("x", 40), fill=INK)
    for j, s in enumerate(["1 × burger", "1 × băutură", "livrată"]):
        d.text((150, 430 + j * 55), s, font=F("m", 38), fill=(70, 70, 66)); d.ellipse([430, 435 + j * 55, 465, 470 + j * 55], fill=GREEN)
    return im
def g1_frame(t):
    c = TABLE.copy(); c.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, 60)))
    paste(c, fade(scaled(R.GLOW_W, 1.3), 0.9), 540 - R.GLOW_W.width * 0.65, 700 - R.GLOW_W.width * 0.65)
    d = ImageDraw.Draw(c)
    kb = eback(k01(t, 0.05, 0.55), 1.2); aside = eio(k01(t, P[1] - 0.1, P[1] + 0.6))
    bx = lerp(540, 900, aside); by = lerp(-500, 900, min(1, kb)) + lerp(0, 200, aside); bs = lerp(1.0, 0.6, aside)
    if t < P[4] + 0.3:
        b = bag(k01(t, 0.6, 1.2)).rotate(lerp(0, -12, aside), Image.BICUBIC, expand=True)
        place3d(c, b, bx, by, bs, alpha=1 - eio(k01(t, P[4], P[4] + 0.3)), shadow=0.7)
    if t < PE[0] + 0.2:
        im = text_img("Ai comandat", F("dk", 110), WHITE); paste(c, fade(im, eo(k01(t, 0.3, 0.7)) * (1 - eio(k01(t, PE[0], PE[0] + 0.2)))), 540 - im.width / 2, 260)
        im = text_img("pe Glovo?", F("dk", 130), LIME); paste(c, fade(im, eo(k01(t, 0.6, 1.0)) * (1 - eio(k01(t, PE[0], PE[0] + 0.2)))), 540 - im.width / 2, 400)
    if P[1] - 0.1 <= t < P[4] + 0.3:
        k = eo(k01(t, P[1] - 0.1, P[1] + 0.6)); a = 1 - eio(k01(t, P[4], P[4] + 0.3))
        if t < P[2]: img = cap("a_home.png")
        elif t < P[2] + 1.0: img = cap("b_list.png")
        elif t < P[3]: img = cap("c_zinger.png")
        elif t < P[3] + 1.3: img = cap("d_qty.png")
        else: img = cap("e_done.png")
        px, py, s = lerp(400, 430, k), lerp(2400, 1000, k), 0.5
        place3d(c, phone_of(img), px, py, s, rz=lerp(-14, -6, k), alpha=a, shadow=0.85)
        def at(xc, yc): return R.scr2frame(xc * 1179 / 1170, yc * 1179 / 1170 + 150, px, py, s)
        if P[2] <= t < P[2] + 1.0: x, y = at(585, 950); tap(c, x, y, t, P[2] + 0.45)
        if P[2] + 1.0 <= t < P[3]: x, y = at(585, 1200); tap(c, x, y, t, P[2] + 1.5)
        if P[3] <= t < P[3] + 1.3: x, y = at(900, 1830); tap(c, x, y, t, P[3] + 0.8)
    if t >= P[4]:
        k = eback(k01(t, P[4], P[4] + 0.5), 1.4)
        st = Image.new("RGBA", (860, 820), (0, 0, 0, 0)); sd = ImageDraw.Draw(st); rr(sd, [0, 0, 859, 819], 40, fill=(252, 250, 244))
        sd.line([(40, 120), (820, 120)], fill=(200, 200, 194), width=3); sd.text((430, 70), "JURNAL ALIMENTAR", font=F("x", 46), fill=GREEN, anchor="mm")
        lg = scaled(LOGO, 0.14); st.alpha_composite(lg, (430 - lg.width // 2, 160))
        sd.text((430, 420), "Scrie în comentarii", font=F("s", 54), fill=INK, anchor="mm")
        place3d(c, st.rotate(-3, Image.BICUBIC, expand=True), 540, 930, max(0.05, min(1.05, k)), shadow=0.6)
        pill_kw(c, 1120, eo(k01(t, P[4] + 0.3, P[4] + 0.7)), 0.85)
    return c

# ========================= g2 · CITY MAP =========================
_r = np.random.default_rng(42)
MAP = Image.new("RGBA", (2400, 3200), (238, 234, 224, 255)); md = ImageDraw.Draw(MAP)
for _ in range(14):
    x, y = _r.integers(0, 2400), _r.integers(0, 3200); md.ellipse([x - 160, y - 110, x + 160, y + 110], fill=(205, 228, 190))
riv = [(0, 900), (500, 1100), (900, 1000), (1400, 1300), (1900, 1250), (2400, 1500)]; md.line(riv, fill=(170, 205, 230), width=90, joint="curve")
for y in range(0, 3200, 180): md.line([(0, y + _r.integers(-20, 20)), (2400, y + _r.integers(-20, 20))], fill=WHITE, width=int(_r.choice([10, 16, 26])))
for x in range(0, 2400, 200): md.line([(x + _r.integers(-30, 30), 0), (x + _r.integers(-30, 30), 3200)], fill=WHITE, width=int(_r.choice([10, 16, 26])))
md.line([(0, 3200), (2400, 0)], fill=(250, 246, 230), width=40); md.line([(0, 600), (2400, 2600)], fill=(250, 246, 230), width=34)
PINS = [(_r.integers(250, 2150), _r.integers(400, 2800)) for _ in range(16)]; HERO = (1250, 1700)
def g2_frame(t):
    # camera on the map
    if t < P[2]: zc, z = (1200, 1600), lerp(0.66, 0.72, k01(t, 0, P[2]))
    elif t < P[3]: zc, z = lerp2((1200, 1600), HERO, eio(k01(t, P[2] + 1.2, P[3]))), lerp(0.72, 1.15, eio(k01(t, P[2] + 1.2, P[3])))
    else: zc, z = HERO, 1.15
    cw, ch = W / z, H / z
    view = MAP.resize((W, H), Image.BILINEAR, box=(zc[0] - cw / 2, zc[1] - ch / 2, zc[0] + cw / 2, zc[1] + ch / 2))
    c = view.copy(); d = ImageDraw.Draw(c)
    def m2s(p): return ((p[0] - (zc[0] - cw / 2)) * z, (p[1] - (zc[1] - ch / 2)) * z)
    if t >= P[2]:
        for j, p in enumerate(PINS + [HERO]):
            kp = eback(k01(t, P[2] + 0.1 + j * 0.06, P[2] + 0.4 + j * 0.06), 2.0)
            if kp <= 0: continue
            x, y = m2s(p); hero = p == HERO; s = (1.6 if hero and t > P[2] + 1.2 else 1.0) * min(1.1, kp); col = LIME2 if hero else GREEN
            d.ellipse([x - 16 * s, y - 6 * s + 4, x + 16 * s, y + 6 * s + 4], fill=(0, 0, 0, 60))
            d.ellipse([x - 26 * s, y - 70 * s, x + 26 * s, y - 18 * s], fill=col); d.polygon([(x - 20 * s, y - 36 * s), (x + 20 * s, y - 36 * s), (x, y)], fill=col)
            d.ellipse([x - 10 * s, y - 54 * s, x + 10 * s, y - 34 * s], fill=WHITE)
            if hero and t > P[2] + 1.2:
                lab = text_img("KFC", F("x", 40), INK); pad = Image.new("RGBA", (lab.width + 20, lab.height), (0, 0, 0, 0)); rr(ImageDraw.Draw(pad), [0, 0, pad.width - 1, pad.height - 1], 30, fill=WHITE + (255,)); pad.alpha_composite(lab, (10, 0))
                paste(c, pad, x + 40, y - 110)
        u = k01(t, P[2], P[2] + 1.4)
        if 0 < u < 1:
            cx, cy = m2s((1200, 1600)); r = 1100 * u; d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=GREEN + (int(200 * (1 - u)),), width=10)
    if t < PE[0] + 0.25:
        a = 1 - eio(k01(t, PE[0], PE[0] + 0.25)); bar = Image.new("RGBA", (W, 420), (0, 0, 0, 0)); rr(ImageDraw.Draw(bar), [60, 60, W - 60, 380], 60, fill=INK + (235,))
        im = text_img("Ai mâncat", F("dk", 100), WHITE); bar.alpha_composite(im, (540 - im.width // 2, 80)); im = text_img("în oraș?", F("dk", 110), LIME); bar.alpha_composite(im, (540 - im.width // 2, 210))
        paste(c, fade(bar, eo(k01(t, 0.1, 0.5)) * a), 0, 520 - (1 - eo(k01(t, 0.1, 0.5))) * 60)
    if P[1] - 0.1 <= t < P[3]:
        a = eo(k01(t, P[1] - 0.1, P[1] + 0.3)) * (1 - eio(k01(t, P[3] - 0.3, P[3])))
        msg = "Un Zinger de la KFC"; n = int(len(msg) * k01(t, P[1] + 0.3, P[1] + 1.6))
        bx = Image.new("RGBA", (W - 120, 160), (0, 0, 0, 0)); bd = ImageDraw.Draw(bx); rr(bd, [0, 0, bx.width - 1, 159], 80, fill=WHITE + (250,))
        bd.text((60, 80), msg[:n] + ("|" if (t * 2) % 1 < 0.5 else ""), font=F("m", 54), fill=INK, anchor="lm")
        bd.ellipse([bx.width - 140, 20, bx.width - 20, 140], fill=LIME2); bd.rounded_rectangle([bx.width - 95, 45, bx.width - 65, 100], 15, fill=INK); bd.arc([bx.width - 110, 70, bx.width - 50, 120], 0, 180, fill=INK, width=6)
        paste(c, fade(bx, a), 60, 1540 + (1 - a) * 60)
    if t >= P[3]:
        a = 1 - eio(k01(t, P[4], P[4] + 0.3)); k = eback(k01(t, P[3], P[3] + 0.45), 1.4)
        cd = Image.new("RGBA", (900, 640), (0, 0, 0, 0)); dd = ImageDraw.Draw(cd); rr(dd, [0, 0, 899, 639], 56, fill=WHITE)
        dd.text((60, 60), "KFC", font=F("x", 40), fill=GREEN); dd.text((60, 120), "Zinger® Burger", font=F("db", 72), fill=INK)
        dd.text((60, 230), "404 kcal · 1 porție", font=F("dk", 64), fill=GREEN)
        rr(dd, [60, 340, 470, 420], 40, outline=GREEN, width=4); dd.text((265, 380), "Vezi sursa oficială", font=F("s", 34), fill=GREEN, anchor="mm")
        done = t > P[3] + 1.6
        rr(dd, [60, 470, 840, 590], 60, fill=LIME2 if done else INK); dd.text((450, 530), "Adăugat în jurnal." if done else "Confirmă", font=F("b", 50), fill=INK if done else LIME, anchor="mm")
        place3d(c, cd, 540, 900, max(0.05, min(1.05, k)), alpha=a, shadow=0.6)
        tap(c, 540, 900 - 320 + 530, t, P[3] + 1.2, LIME2)
        dis = text_img("Valorile nutriționale sunt estimări și pot varia.", F("m", 28), INK); paste(c, fade(dis, a * eo(k01(t, P[3] + 0.3, P[3] + 0.7))), 540 - dis.width / 2, 1290)
    if t >= P[4]:
        k = eo(k01(t, P[4], P[4] + 0.5)); c.alpha_composite(Image.new("RGBA", (W, H), INK + (int(225 * k),)))
        lg = scaled(LOGO, 0.22); paste(c, fade(lg, k), 540 - lg.width / 2, 470)
        im = text_img("Scrie în comentarii", F("s", 54), WHITE); paste(c, fade(im, k), 540 - im.width / 2, 820); pill_kw(c, 1060, eo(k01(t, P[4] + 0.3, P[4] + 0.7)))
    return c

FRAME = {"g1": g1_frame, "g2": g2_frame}[KEY]
def frame(t):
    c = FRAME(t); subtitles(c, t); c.alpha_composite(R.GRAIN[int(t * 60) % 8])
    if t < 0.04: c = Image.blend(Image.new("RGBA", (W, H), (0, 0, 0, 255)), c, t / 0.04)
    if t > DUR - 0.35: c = Image.blend(c, Image.new("RGBA", (W, H), (0, 0, 0, 255)), k01(t, DUR - 0.35, DUR))
    return c.convert("RGB")

# ========================= music =========================
def t_(dd): return np.arange(int(dd * AU.SR)) / AU.SR
def kick(g=1.0): x = t_(0.35); return np.sin(2 * np.pi * (45 + 110 * np.exp(-x * 30)) * x) * np.exp(-x * 9) * g
def shaker(): n = np.random.default_rng(1).standard_normal(int(0.06 * AU.SR)); return np.diff(n * np.exp(-t_(0.06) * 60), prepend=0)
def marimba(f, dd=0.5): x = t_(dd); return (np.sin(2 * np.pi * f * x) + 0.4 * np.sin(2 * np.pi * f * 4 * x) * np.exp(-x * 30)) * np.exp(-x * 7)
def saw(f, dd): x = t_(dd); return 2 * ((f * x) % 1) - 1
def music():
    N = AU.N; b = np.zeros((N, 2))
    if KEY == "g1":
        bt = 60 / 100; pat = [1, 0, 0, 1, 0, 0, 1, 0]
        for i in range(int(DUR / (bt / 2))):
            at = i * bt / 2
            if pat[i % 8]: AU.place(b, kick(0.8), at, 0.6)
            AU.place(b, shaker(), at + 0.02, 0.12 if i % 2 else 0.06)
            f = [392, 440, 523.3, 440, 587.3, 523.3, 440, 392][i % 8] * (1 if (i // 8) % 2 == 0 else 0.89)
            if i % 2 == 0 or i % 8 == 3: AU.place(b, marimba(f), at, 0.09, pan=(-0.3 if i % 4 else 0.3))
    else:
        bt = 60 / 110; chords = [[220, 261.6, 329.6], [174.6, 220, 261.6], [196, 246.9, 293.7], [164.8, 196, 246.9]]
        for i in range(int(DUR / (bt / 4))):
            ch = chords[(i // 16) % 4]; f = ch[i % 3] * 2; x = t_(bt / 4); AU.place(b, saw(f, bt / 4) * np.exp(-x * 14) * 0.4, i * bt / 4, 0.06, pan=0.4 * math.sin(i))
            if i % 4 == 0: AU.place(b, kick(0.8), i * bt / 4, 0.55)
        for ci in range(int(DUR / (bt * 4)) + 1):
            x = t_(bt * 4 + 0.5); e = np.minimum(1, x / 0.3) * np.minimum(1, np.maximum(0, (bt * 4 + 0.5 - x) / 0.5))
            for f in chords[ci % 4]: AU.place(b, (saw(f, bt * 4 + 0.5) * 0.3 + np.sin(2 * np.pi * f * x)) * e, ci * bt * 4, 0.012)
    fade_ = np.minimum(1, np.arange(N) / (0.2 * AU.SR)) * np.minimum(1, (N - np.arange(N)) / (0.8 * AU.SR))
    return np.tanh(b * 1.1) * fade_[:, None]
def build_audio():
    AU.DUR = DUR; AU.N = int(AU.SR * DUR); N = AU.N; s = np.zeros((N, 2))
    for p in P[1:5]: AU.place(s, AU.whoosh(0.4, 1.1), p - 0.28, 0.28)
    if KEY == "g1":
        x = t_(0.9); bell = sum(np.sin(2 * np.pi * f * x) * np.exp(-x * 4) for f in (659.3, 523.3)); AU.place(s, np.sin(2 * np.pi * 659.3 * x) * np.exp(-x * 4), 0.05, 0.2); AU.place(s, np.sin(2 * np.pi * 523.3 * x) * np.exp(-x * 4), 0.4, 0.2)
        AU.place(s, AU.soft_impact(0.5), 0.5, 0.5); AU.place(s, AU.whoosh(0.4, 2.0), 0.7, 0.3)
        for tt in (P[2] + 0.45, P[2] + 1.5, P[3] + 0.8): AU.place(s, AU.key_click(), tt, 0.45)
        AU.place(s, AU.success_chime(), P[3] + 1.35, 0.2)
    else:
        for j in range(17): AU.place(s, AU.pop(900 + (j % 5) * 120), P[2] + 0.1 + j * 0.06, 0.12)
        AU.place(s, AU.ring_tone(1.4), P[2], 0.05)
        for j in range(19): AU.place(s, AU.tick(2600, 0.012), P[1] + 0.3 + j * 0.068, 0.12)
        AU.place(s, AU.key_click(), P[3] + 1.2, 0.45); AU.place(s, AU.success_chime(), P[3] + 1.6, 0.2)
    AU.place(s, AU.success_chime(), P[4] + 0.4, 0.12)
    m = music(); v = np.zeros((N, 2)); AU.place(v, AU.load_mp3(os.path.join(HERE, MP3)), VO, 1.0)
    vel = np.abs(v[:, 0]); kk = np.ones(int(0.12 * AU.SR)) / int(0.12 * AU.SR); duck = 1 - 0.45 * np.clip(np.convolve(vel, kk, "same") * 12, 0, 1)
    mix = (v * 0.95 + np.tanh(s * 1.2) * 0.7 + m * 0.9 * duck[:, None]) * 0.7
    raw = os.path.join(HERE, f"{KEY}_mix_raw.wav"); AU.write(raw, mix); out = os.path.join(HERE, f"{KEY}_mix.wav")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", raw, "-af", "loudnorm=I=-14:TP=-1.0:LRA=9", "-ar", "48000", out], check=True); os.remove(raw)

if __name__ == "__main__":
    mode = sys.argv[2]
    if mode == "frames":
        for tp in [float(x) for x in sys.argv[3].split(",")]: frame(tp).save(os.path.join(HERE, f"{KEY}_f{tp:05.2f}.png"))
        print(KEY, [round(float(p), 2) for p in P], DUR)
    elif mode == "audio": build_audio()
    elif mode == "seg":
        i, n = int(sys.argv[3]), int(sys.argv[4]); fps = 60; N = int(round(DUR * fps)); a, b = N * i // n, N * (i + 1) // n
        ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1080x1920", "-r", str(fps), "-i", "-",
                               "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p", os.path.join(HERE, f"{KEY}_seg{i}.mp4")], stdin=subprocess.PIPE)
        for k in range(a, b): ff.stdin.write(frame(k / fps).tobytes())
        ff.stdin.close(); ff.wait()

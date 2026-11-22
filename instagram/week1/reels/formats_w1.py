"""Week-1 reels redone in three new formats.

    python3 formats_w1.py <r25|r27|r29> frames 1,4 | audio | seg i n
r25 calendar + receipt · r27 polaroid on corkboard · r29 marker on graph paper
"""
import math, os, re, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__)); SPOT = os.path.join(HERE, "..", "..", "spot")
sys.path.insert(0, SPOT)
import render as R
import audio as AU
from render import W, H, k01, eo, eio, eback, lerp, lerp2, paste, fade, scaled, place3d, glow_line, poly_partial, text_img, LOGO, F

KEY = sys.argv[1]
MP3 = {"r25": "r25_plan.mp3", "r27": "r27_scan.mp3", "r29": "r29_trend.mp3"}[KEY]
KW = {"r25": "PLAN", "r27": "ETICHETA", "r29": "JURNAL"}[KEY]
SUBS = {"r25": ["Nu mai întreba ce mănânci mâine.", "Completezi profilul o dată.", "Primești un plan pe 1, 7 sau 30 de zile.", "Plus lista de cumpărături.", "Scrie PLAN în comentarii!"],
        "r27": ["Ai o etichetă în mână?", "O scanezi.", "Valorile intră singure în jurnal.", "Poza rămâne în browser.", "Scrie ETICHETA în comentarii!"],
        "r29": ["Te-ai cântărit azi și te-ai speriat?", "Variațiile zilnice sunt normale.", "Urmărește tendința, nu o singură cifră.", "Un pas odată.", "Scrie JURNAL în comentarii!"]}[KEY]
VO = 0.45
INK = (8, 30, 22); LIME = (199, 240, 130); GREEN = (37, 94, 70); WHITE = (255, 255, 255)
MONO = lambda s: ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", s)
HAND = lambda s: ImageFont.truetype("/usr/share/fonts/opentype/inter/InterDisplay-BoldItalic.otf", s)

def phrase_starts(mp3):
    x = AU.load_mp3(mp3)
    out = subprocess.run(["ffmpeg", "-hide_banner", "-i", mp3, "-af", "silencedetect=noise=-38dB:d=0.25", "-f", "null", "-"], capture_output=True, text=True).stderr
    ends = [float(v) for v in re.findall(r"silence_end: ([0-9.]+)", out)]
    return [s + VO for s in ([AU.onset(x)] + [e for e in ends if e < len(x) / AU.SR - 0.2])[:5]], len(x) / AU.SR + VO
P, VEND = phrase_starts(os.path.join(HERE, MP3)); DUR = round(VEND + 1.6, 2); PE = [P[i + 1] - 0.12 if i < 4 else DUR for i in range(5)]

def rr(d, box, r, **k): d.rounded_rectangle(box, r, **k)
def shadowed(c, im, x, y, a=1.0, blur=18, off=(10, 18), op=0.35):
    sh = Image.new("RGBA", (im.width + 80, im.height + 80), (0, 0, 0, 0)); m = im.getchannel("A").point(lambda v: int(v * op * a))
    sh.paste((0, 0, 0, 255), (40, 40), m); paste(c, sh.filter(ImageFilter.GaussianBlur(blur)), x - 40 + off[0], y - 40 + off[1]); paste(c, fade(im, a), x, y)
def subtitles(c, t, bg=(6, 9, 7, 180)):
    for i, txt in enumerate(SUBS[:4]):
        a, b = P[i], PE[i]
        if a - 0.05 <= t < b + 0.2:
            k = eo(k01(t, a - 0.05, a + 0.2)) * (1 - eio(k01(t, b, b + 0.2)))
            im = text_img(txt, F("b", 46), WHITE); pad = Image.new("RGBA", (im.width + 40, im.height + 8), (0, 0, 0, 0))
            ImageDraw.Draw(pad).rounded_rectangle([0, 0, pad.width - 1, pad.height - 1], 34, fill=bg); pad.alpha_composite(im, (20, 4))
            if pad.width > 1000: pad = scaled(pad, 1000 / pad.width)
            paste(c, fade(pad, k), W / 2 - pad.width / 2, 1760)

# ========================= r25 · CALENDAR + RECEIPT =========================
yy, xx = np.mgrid[0:H, 0:W]
_n = np.random.default_rng(5)
KRAFT = Image.fromarray(np.clip(np.dstack([np.full((H, W), v) for v in (236, 226, 208)]) + _n.normal(0, 5, (H, W, 1)) - (np.sqrt(((xx - 540) / 900.) ** 2 + ((yy - 900) / 1400.) ** 2) * 40)[..., None], 0, 255).astype(np.uint8), "RGB").convert("RGBA")
def cal_page(top, big, sub=""):
    im = Image.new("RGBA", (720, 820), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    rr(d, [0, 60, 719, 819], 30, fill=(252, 250, 245)); rr(d, [0, 60, 719, 230], 30, fill=GREEN); d.rectangle([0, 200, 719, 230], fill=GREEN)
    for x in (180, 540): d.ellipse([x - 26, 30, x + 26, 90], fill=(70, 70, 66)); d.ellipse([x - 14, 42, x + 14, 78], fill=(200, 200, 196))
    d.text((360, 150), top, font=F("x", 64), fill=WHITE, anchor="mm")
    f = F("dk", 300 if len(big) <= 2 else 200); d.text((360, 520), big, font=f, fill=INK, anchor="mm")
    if sub: d.text((360, 720), sub, font=F("b", 60), fill=GREEN, anchor="mm")
    return im
RECEIPT_ITEMS = ["LEGUME", "OUĂ", "IAURT", "OVĂZ", "FRUCTE", "PÂINE INTEGRALĂ"]
def receipt(k):
    full = Image.new("RGBA", (640, 1100), (0, 0, 0, 0)); d = ImageDraw.Draw(full)
    d.rectangle([0, 0, 639, 1080], fill=(255, 255, 252))
    for x in range(0, 640, 32): d.polygon([(x, 1080), (x + 16, 1100), (x + 32, 1080)], fill=(255, 255, 252))
    d.text((320, 70), "JURNAL ALIMENTAR", font=MONO(36), fill=INK, anchor="mm"); d.text((320, 120), "LISTA DE CUMPĂRĂTURI", font=MONO(32), fill=INK, anchor="mm")
    d.text((320, 165), "- - - - - - - - - - - - - - -", font=MONO(30), fill=(120, 120, 116), anchor="mm")
    for j, it in enumerate(RECEIPT_ITEMS):
        d.rectangle([60, 220 + j * 100, 100, 260 + j * 100], outline=INK, width=4); d.text((130, 240 + j * 100), it, font=MONO(40), fill=INK, anchor="lm")
    d.text((320, 860), "- - - - - - - - - - - - - - -", font=MONO(30), fill=(120, 120, 116), anchor="mm")
    d.text((320, 920), "PLAN PE 1 / 7 / 30 ZILE", font=MONO(32), fill=INK, anchor="mm"); d.text((320, 975), "MULȚUMIM!", font=MONO(32), fill=INK, anchor="mm")
    h = int(1100 * k); return full.crop((0, 0, 640, h)) if h > 2 else None
def r25_frame(t):
    c = KRAFT.copy(); d = ImageDraw.Draw(c)
    if t < PE[0] + 0.25:      # tomorrow's page with a question, torn off at the end
        pg = cal_page("MÂINE", "?", "ce mănânc?"); tear = eio(k01(t, PE[0] - 0.25, PE[0] + 0.25))
        k = eback(k01(t, 0.05, 0.45), 1.3)
        place3d(c, pg, 540 + 300 * tear, 900 + 900 * tear ** 2, max(0.05, min(1.05, k)), rz=-25 * tear, rx=10 * tear, alpha=1 - tear * 0.3, shadow=0.5)
    if P[1] - 0.1 <= t < PE[1] + 0.3:   # clipboard profile form
        a = 1 - eio(k01(t, PE[1], PE[1] + 0.3)); k = eo(k01(t, P[1] - 0.1, P[1] + 0.4))
        cb = Image.new("RGBA", (760, 1000), (0, 0, 0, 0)); cd = ImageDraw.Draw(cb)
        rr(cd, [0, 40, 759, 999], 30, fill=(150, 110, 70)); rr(cd, [40, 90, 719, 960], 10, fill=(252, 250, 245)); rr(cd, [250, 0, 510, 90], 20, fill=(120, 120, 116))
        cd.text((80, 140), "PROFIL", font=F("x", 56), fill=GREEN)
        for j, it in enumerate(["Vârstă", "Greutate", "Înălțime", "Activitate", "Ce nu mănânci"]):
            y = 260 + j * 130; cd.rectangle([80, y, 140, y + 60], outline=INK, width=6); cd.text((170, y + 30), it, font=HAND(56), fill=INK, anchor="lm")
            kk = k01(t, P[1] + 0.35 + j * 0.25, P[1] + 0.55 + j * 0.25)
            if kk > 0: pts = [(88, y + 30), (105, y + 50), (150, y - 8)]; cd.line(poly_partial(pts, kk), fill=GREEN, width=12, joint="curve")
        place3d(c, cb, 540, lerp(2200, 960, k), 0.95, rz=-2, alpha=a, shadow=0.6)
    if P[2] - 0.1 <= t < PE[2] + 0.3:   # flip-calendar 1 → 7 → 30
        a = 1 - eio(k01(t, PE[2], PE[2] + 0.3)); lt = t - P[2]
        ws = [(0.0, "1", "zi"), (1.25, "7", "zile"), (1.85, "30", "de zile")]
        cur = max(j for j, w in enumerate(ws) if lt >= w[0] or j == 0)
        if cur + 1 < len(ws) and lt > ws[cur + 1][0] - 0.25:
            under = cal_page("PLAN", ws[cur + 1][1], ws[cur + 1][2]); place3d(c, under, 540, 960, 1.0, alpha=a, shadow=0.5)
            fk = eio(k01(lt, ws[cur + 1][0] - 0.25, ws[cur + 1][0])); top = cal_page("PLAN", ws[cur][1], ws[cur][2])
            place3d(c, top, 540, 960 - 120 * fk, 1.0, rx=-85 * fk, alpha=a * (1 - fk * 0.6), shadow=0)
        else:
            place3d(c, cal_page("PLAN", ws[cur][1], ws[cur][2]), 540, 960, 1.0 * eo(k01(t, P[2] - 0.1, P[2] + 0.3)) + 0.0001, alpha=a, shadow=0.5)
    if P[3] - 0.1 <= t < DUR:   # receipt printing out of a slot
        k = eio(k01(t, P[3], P[3] + 1.6)); rc = receipt(k)
        rr(d, [170, 200, 910, 300], 40, fill=(40, 42, 40)); d.rectangle([210, 270, 870, 284], fill=(10, 10, 10))
        if rc is not None: shadowed(c, rc, 220, 284, 1.0, off=(8, 10))
        rr(d, [170, 200, 910, 270], 40, fill=(52, 54, 52)); d.ellipse([820, 222, 850, 252], fill=(148, 230, 2) if int(t * 4) % 2 else (60, 90, 40))
    if t >= P[4]:   # rubber stamp PLAN on the receipt
        ks = k01(t, P[4] + 0.1, P[4] + 0.35); s = lerp(2.2, 1.0, eio(ks))
        st = Image.new("RGBA", (620, 260), (0, 0, 0, 0)); sd = ImageDraw.Draw(st); rr(sd, [0, 0, 619, 259], 30, outline=GREEN, width=16)
        sd.text((310, 130), KW, font=F("dk", 170), fill=GREEN, anchor="mm")
        st = st.rotate(-12, Image.BICUBIC, expand=True); stt = scaled(st, s)
        if ks > 0: paste(c, fade(stt, min(1, ks * 3) * 0.9), 540 - stt.width / 2, 760 - stt.height / 2)
        im = text_img("Scrie în comentarii", F("x", 56), INK); paste(c, fade(im, eo(k01(t, P[4] + 0.4, P[4] + 0.8))), 540 - im.width / 2, 1450)
        im = text_img("Premium · de la 25 lei/lună", F("m", 42), GREEN); paste(c, fade(im, eo(k01(t, P[4] + 0.6, P[4] + 1.0))), 540 - im.width / 2, 1540)
    return c

# ========================= r27 · POLAROID ON CORKBOARD =========================
cn = _n.random((H // 4, W // 4)); cork = (np.dstack([cn * 40 + 170, cn * 30 + 120, cn * 20 + 70])).astype(np.uint8)
CORK = Image.fromarray(cork, "RGB").resize((W, H), Image.NEAREST).filter(ImageFilter.GaussianBlur(1.2)).convert("RGBA")
LABEL = Image.open(os.path.join(SPOT, "assets", "label.png")).convert("RGBA")
def pin(c, x, y, col=(220, 60, 60)):
    d = ImageDraw.Draw(c); d.ellipse([x - 26 + 6, y - 26 + 8, x + 26 + 6, y + 26 + 8], fill=(0, 0, 0, 80)); d.ellipse([x - 26, y - 26, x + 26, y + 26], fill=col); d.ellipse([x - 12, y - 16, x, y - 4], fill=(255, 255, 255, 140))
def sticky(txt1, txt2, col):
    im = Image.new("RGBA", (420, 400), (0, 0, 0, 0)); d = ImageDraw.Draw(im); d.rectangle([0, 0, 419, 399], fill=col + (255,)); d.rectangle([0, 0, 419, 40], fill=tuple(max(0, v - 18) for v in col) + (255,))
    d.text((210, 150), txt1, font=HAND(54), fill=INK, anchor="mm"); d.text((210, 270), txt2, font=F("dk", 84), fill=INK, anchor="mm"); return im
def r27_frame(t):
    c = CORK.copy()
    if t < PE[0] + 0.3:
        a = 1 - eio(k01(t, PE[0], PE[0] + 0.3)); k = eback(k01(t, 0.05, 0.5), 1.2)
        lb = scaled(LABEL, 0.75).rotate(-4, Image.BICUBIC, expand=True)
        if k > 0.02: shadowed(c, scaled(lb, min(1.05, k)), 540 - lb.width * min(1.05, k) / 2, 760, a)
        pin(c, 540, 770)
        im = text_img("Ai o etichetă în mână?", F("x", 70), WHITE); paste(c, fade(im, eo(k01(t, 0.3, 0.7)) * a), 540 - im.width / 2, 400)
    if P[1] - 0.1 <= t < PE[2] + 0.3:
        fl = max(0, 1 - abs(t - P[1] - 0.1) / 0.15)
        a = 1 - eio(k01(t, PE[2] + 0.0, PE[2] + 0.3)) if False else 1.0
        dev = k01(t, P[1] + 0.3, P[1] + 1.8); slide = eo(k01(t, P[1] + 0.1, P[1] + 0.6))
        pol = Image.new("RGBA", (620, 740), (0, 0, 0, 0)); pd = ImageDraw.Draw(pol); pd.rectangle([0, 0, 619, 739], fill=(250, 250, 246))
        photo = LABEL.resize((540, 540 * LABEL.height // LABEL.width)).crop((0, 0, 540, 540)).convert("RGB")
        photo = Image.blend(Image.new("RGB", photo.size, (235, 235, 230)), photo, eio(dev)); pol.paste(photo, (40, 40))
        pd.text((310, 660), "eticheta mea", font=HAND(44), fill=(60, 60, 60), anchor="mm")
        pr = pol.rotate(lerp(0, 5, slide), Image.BICUBIC, expand=True)
        x = lerp(540, 330, eo(k01(t, P[2], P[2] + 0.5))); y = lerp(-800, 700, slide)
        shadowed(c, pr, x - pr.width / 2, y - pr.height / 2 + 300 * 0, 1.0)
        pin(c, x, y - pr.height / 2 + 40, (60, 140, 220))
        if fl > 0: c.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(230 * fl))))
    if P[2] <= t < DUR:
        vals = [("Calorii", "61 kcal", (255, 236, 120)), ("Proteine", "3,5 g", LIME), ("Carbohidrați", "4,7 g", (250, 190, 140)), ("Grăsimi", "3,3 g", (170, 205, 235))]
        pos = [(800, 470), (810, 900), (290, 1330), (790, 1330)]
        for j, ((n, v, col), (x, y)) in enumerate(zip(vals, pos)):
            k = eback(k01(t, P[2] + 0.2 + j * 0.3, P[2] + 0.55 + j * 0.3), 1.5)
            if k <= 0: continue
            st = scaled(sticky(n, v, col), 0.62).rotate((-1) ** j * 5, Image.BICUBIC, expand=True); st = scaled(st, min(1.05, k))
            shadowed(c, st, x - st.width / 2, y - st.height / 2, 1.0, off=(6, 12)); pin(c, x, y - st.height / 2 + 22, (240, 200, 40))
        if t < P[4]:
            dis = text_img("Valorile nutriționale sunt estimări și pot varia.", F("m", 28), WHITE); paste(c, fade(dis, eo(k01(t, P[2] + 0.4, P[2] + 0.8))), 540 - dis.width / 2, 1690)
    if P[3] <= t < P[4] + 0.3:
        k = eback(k01(t, P[3], P[3] + 0.45), 1.4); a = 1 - eio(k01(t, P[4], P[4] + 0.3))
        note = Image.new("RGBA", (760, 300), (0, 0, 0, 0)); nd = ImageDraw.Draw(note); nd.rectangle([0, 0, 759, 299], fill=(255, 255, 255))
        nd.rounded_rectangle([40, 90, 140, 200], 18, outline=GREEN, width=10); nd.arc([60, 40, 120, 130], 180, 360, fill=GREEN, width=10)
        nd.text((180, 110), "Fotografia se procesează", font=HAND(48), fill=INK); nd.text((180, 180), "în browser.", font=HAND(48), fill=GREEN)
        nt = scaled(note.rotate(-3, Image.BICUBIC, expand=True), max(0.05, min(1.05, k))); shadowed(c, nt, 540 - nt.width / 2, 700 - nt.height / 2, a); pin(c, 540, 700 - nt.height / 2 + 30)
    if t >= P[4]:
        k = eback(k01(t, P[4], P[4] + 0.5), 1.4)
        big = Image.new("RGBA", (820, 760), (0, 0, 0, 0)); bd = ImageDraw.Draw(big); bd.rectangle([0, 0, 819, 759], fill=LIME + (255,))
        lg = scaled(LOGO, 0.16); big.alpha_composite(lg, (410 - lg.width // 2, 60))
        bd.text((410, 360), "Scrie în comentarii", font=HAND(60), fill=INK, anchor="mm"); bd.text((410, 520), KW, font=F("dk", 150), fill=INK, anchor="mm")
        bt = scaled(big.rotate(3, Image.BICUBIC, expand=True), max(0.05, min(1.05, k))); shadowed(c, bt, 540 - bt.width / 2, 900 - bt.height / 2, 1.0); pin(c, 540, 900 - bt.height / 2 + 40)
    return c

# ========================= r29 · MARKER ON GRAPH PAPER =========================
GRID = Image.new("RGBA", (W, H), (250, 251, 247, 255)); gd = ImageDraw.Draw(GRID)
for x in range(0, W, 40): gd.line([(x, 0), (x, H)], fill=(205, 222, 232) if x % 200 else (170, 198, 214), width=2)
for y in range(0, H, 40): gd.line([(0, y), (W, y)], fill=(205, 222, 232) if y % 200 else (170, 198, 214), width=2)
gd.line([(110, 0), (110, H)], fill=(235, 140, 140), width=4)
def marker(c, pts, k, col, width=14):
    if k <= 0 or len(pts) < 2: return
    part = poly_partial(pts, k); d = ImageDraw.Draw(c); d.line(part, fill=col, width=width, joint="curve")
    for p in (part[0], part[-1]): d.ellipse([p[0] - width / 2, p[1] - width / 2, p[0] + width / 2, p[1] + width / 2], fill=col)
def jitter(pts, a=3, seed=1):
    r = np.random.default_rng(seed); return [(x + r.normal(0, a), y + r.normal(0, a)) for x, y in pts]
def hand_text(c, txt, x, y, size, col, k):
    if k <= 0: return
    im = text_img(txt, HAND(size), col); w = int(im.width * min(1, k)); paste(c, im.crop((0, 0, max(1, w), im.height)), x, y)
_rng = np.random.default_rng(29); DAILY = _rng.normal(0, 1, 18) * 0.9 - np.linspace(0, 1.4, 18)
TREND = np.convolve(np.pad(DAILY, 3, mode="edge"), np.ones(7) / 7, "valid")
def cpts(v, x0=170, x1=930, y0=760, y1=1240):
    lo, hi = DAILY.min() - 0.3, DAILY.max() + 0.3; return [(lerp(x0, x1, i / (len(v) - 1)), lerp(y1, y0, (q - lo) / (hi - lo))) for i, q in enumerate(v)]
def r29_frame(t):
    c = GRID.copy(); d = ImageDraw.Draw(c)
    if t < PE[0] + 0.3:
        a = 1 - eio(k01(t, PE[0], PE[0] + 0.3))
        hand_text(c, "Te-ai cântărit", 170, 640, 110, (40, 40, 40), k01(t, 0.15, 0.95) * a if a > 0.5 else 0)
        hand_text(c, "azi?", 170, 790, 140, GREEN, k01(t, 0.9, 1.3) if a > 0.5 else 0)
        circ = [(300 + 190 * math.cos(th), 880 + 110 * math.sin(th)) for th in np.linspace(-0.3, 2 * math.pi + 0.2, 60)]
        if a > 0.5: marker(c, jitter(circ, 4, 2), k01(t, 1.3, 1.9), (230, 90, 70), 10)
        if a > 0.5 and t > 1.9:   # worried face doodle
            fk = k01(t, 1.9, 2.4); cx, cy = 780, 1200
            marker(c, [(cx + 110 * math.cos(th), cy + 110 * math.sin(th)) for th in np.linspace(0, 2 * math.pi, 40)], fk, (40, 40, 40), 9)
            if fk > 0.6: d.ellipse([cx - 45, cy - 35, cx - 25, cy - 15], fill=(40, 40, 40)); d.ellipse([cx + 25, cy - 35, cx + 45, cy - 15], fill=(40, 40, 40)); d.arc([cx - 50, cy + 20, cx + 50, cy + 90], 200, 340, fill=(40, 40, 40), width=8)
    if P[1] <= t < P[4]:
        a = 1.0; dp = cpts(DAILY)
        d.line([(170, 1300), (930, 1300)], fill=(40, 40, 40), width=5); d.line([(170, 700), (170, 1300)], fill=(40, 40, 40), width=5)
        kd = eio(k01(t, P[1] + 0.1, P[1] + 1.7)); marker(c, jitter(dp, 2, 3), kd, (90, 90, 90), 8)
        for j, p in enumerate(dp):
            if j / (len(dp) - 1) <= kd: d.ellipse([p[0] - 10, p[1] - 10, p[0] + 10, p[1] + 10], fill=(90, 90, 90))
        hand_text(c, "zi cu zi", 190, 1330, 64, (90, 90, 90), k01(t, P[1] + 0.8, P[1] + 1.4))
        if t >= P[2]:
            tp = cpts(TREND); dense = [lerp2(tp[int(i)], tp[min(len(tp) - 1, int(i) + 1)], i - int(i)) for i in np.linspace(0, len(tp) - 1.001, 100)]
            marker(c, jitter(dense, 1.5, 4), eio(k01(t, P[2] + 0.1, P[2] + 1.6)), GREEN, 18)
            hand_text(c, "tendința", 620, 1330, 72, GREEN, k01(t, P[2] + 1.2, P[2] + 1.8))
            j0 = int(np.argmin(DAILY[:10])); px, py = dp[j0]; xk = k01(t, P[2] + 1.6, P[2] + 2.1)
            marker(c, [(px - 30, py - 30), (px + 30, py + 30)], xk, (230, 90, 70), 9); marker(c, [(px + 30, py - 30), (px - 30, py + 30)], k01(t, P[2] + 1.9, P[2] + 2.3), (230, 90, 70), 9)
            hand_text(c, "o singură cifră", px - 120, py + 50, 44, (230, 90, 70), k01(t, P[2] + 2.0, P[2] + 2.6))
        hand_text(c, "Fără cifre care sperie.", 170, 520, 72, (40, 40, 40), k01(t, P[1] + 0.2, P[1] + 1.2))
        if t >= P[3]:   # footsteps
            for j in range(6):
                fk = k01(t, P[3] + j * 0.2, P[3] + j * 0.2 + 0.15)
                if fk <= 0: continue
                x = 230 + j * 130; y = 1520 + (j % 2) * 50
                d.ellipse([x - 26, y - 40, x + 26, y + 40], fill=GREEN + (int(255 * fk),)); d.ellipse([x - 22, y + 46, x + 22, y + 76], fill=GREEN + (int(255 * fk),))
            hand_text(c, "Un pas odată.", 300, 1640, 70, GREEN, k01(t, P[3] + 0.4, P[3] + 1.2))
    if t >= P[4]:
        k = eio(k01(t, P[4], P[4] + 0.4)); c.alpha_composite(Image.new("RGBA", (W, H), (250, 251, 247, int(240 * k))))
        box = [(160, 760), (920, 760), (920, 1300), (160, 1300), (160, 760)]; marker(c, jitter(box, 3, 9), k01(t, P[4] + 0.1, P[4] + 0.8), GREEN, 14)
        hand_text(c, "Scrie în comentarii", 230, 820, 70, (40, 40, 40), k01(t, P[4] + 0.3, P[4] + 0.9))
        im = text_img(KW, F("dk", 170), GREEN); paste(c, fade(im, eo(k01(t, P[4] + 0.6, P[4] + 1.0))), 540 - im.width / 2, 960)
        lg = scaled(LOGO, 0.14); paste(c, fade(lg, eo(k01(t, P[4] + 0.6, P[4] + 1.0))), 540 - lg.width / 2, 1380)
    return c

FRAME = {"r25": r25_frame, "r27": r27_frame, "r29": r29_frame}[KEY]
def frame(t):
    c = FRAME(t); subtitles(c, t); c.alpha_composite(R.GRAIN[int(t * 60) % 8])
    if t < 0.04: c = Image.blend(Image.new("RGBA", (W, H), (0, 0, 0, 255)), c, t / 0.04)
    if t > DUR - 0.35: c = Image.blend(c, Image.new("RGBA", (W, H), (0, 0, 0, 255)), k01(t, DUR - 0.35, DUR))
    return c.convert("RGB")

# ========================= music =========================
def t_(dd): return np.arange(int(dd * AU.SR)) / AU.SR
def kick(g=1.0): x = t_(0.35); return np.sin(2 * np.pi * (45 + 110 * np.exp(-x * 30)) * x) * np.exp(-x * 9) * g
def snare(): n = np.random.default_rng(2).standard_normal(int(0.2 * AU.SR)); x = t_(0.2); return n * np.exp(-x * 20) * 0.7 + np.sin(2 * np.pi * 190 * x) * np.exp(-x * 25) * 0.5
def hat(): n = np.random.default_rng(1).standard_normal(int(0.04 * AU.SR)); return np.diff(n * np.exp(-t_(0.04) * 110), prepend=0)
def ks_pluck(f, dd=1.2):   # Karplus-Strong string
    N = int(dd * AU.SR); p = max(2, int(AU.SR / f)); buf = np.random.default_rng(int(f)).uniform(-1, 1, p); out = np.zeros(N)
    for i in range(N): out[i] = buf[i % p]; buf[i % p] = 0.996 * 0.5 * (buf[i % p] + buf[(i + 1) % p])
    return out
def piano(f, dd=1.6):
    x = t_(dd); return sum(np.sin(2 * np.pi * f * h * x) * np.exp(-x * (2.2 + h)) / h for h in (1, 2, 3)) * np.minimum(1, x / 0.005)
def music(style):
    N = AU.N; b = np.zeros((N, 2))
    if style == "funk":
        bt = 60 / 104; line = [55, 0, 55, 65.4, 0, 73.4, 55, 0, 82.4, 0, 73.4, 65.4, 55, 0, 49, 0]
        for i in range(int(DUR / (bt / 4))):
            at = i * bt / 4
            if i % 4 == 0: AU.place(b, kick(), at, 0.8 if (i // 4) % 2 == 0 else 0.5)
            if i % 8 == 4: AU.place(b, snare(), at, 0.35)
            if i % 2 == 0: AU.place(b, hat(), at, 0.12)
            f0 = line[i % 16]
            if f0: x = t_(bt / 4 * 0.9); AU.place(b, (np.sin(2 * np.pi * f0 * x) + 0.4 * np.sign(np.sin(2 * np.pi * f0 * x))) * np.exp(-x * 9), at, 0.2)
        for i in range(int(DUR / (bt * 2))):
            for f in (261.6, 329.6, 392): x = t_(0.12); AU.place(b, np.sin(2 * np.pi * f * x) * np.exp(-x * 30), i * bt * 2 + bt * 1.5, 0.05)
    elif style == "guitar":
        bt = 60 / 92; chords = [[196, 246.9, 293.7, 392], [164.8, 196, 246.9, 329.6], [130.8, 164.8, 196, 261.6], [146.8, 185, 220, 293.7]]
        for i in range(int(DUR / (bt / 2))):
            ch = chords[(i // 8) % 4]; AU.place(b, ks_pluck(ch[i % 4], 1.0), i * bt / 2, 0.11, pan=(-0.3 if i % 2 else 0.3))
        for i in range(int(DUR / bt)): AU.place(b, kick(0.6), i * bt, 0.45 if i % 2 == 0 else 0)
    else:
        bt = 60 / 80; prog = [[261.6, 329.6, 392], [220, 261.6, 329.6], [174.6, 220, 261.6], [196, 246.9, 293.7]]
        for i in range(int(DUR / (bt * 2)) + 1):
            for j, f in enumerate(prog[i % 4]): AU.place(b, piano(f, 2.2), i * bt * 2 + j * 0.06, 0.05)
            AU.place(b, piano(prog[i % 4][0] / 2, 2.0), i * bt * 2, 0.06)
            for s in range(3): AU.place(b, piano(prog[i % 4][(s + 1) % 3] * 2, 0.8), i * bt * 2 + bt * (0.5 + s * 0.5), 0.025)
    fade_ = np.minimum(1, np.arange(N) / (0.2 * AU.SR)) * np.minimum(1, (N - np.arange(N)) / (0.8 * AU.SR))
    return np.tanh(b * 1.1) * fade_[:, None]
def scribble(dd):
    n = np.random.default_rng(int(dd * 100)).standard_normal(int(dd * AU.SR)); x = t_(dd)
    return np.diff(n, prepend=0) * (0.5 + 0.5 * np.abs(np.sin(2 * np.pi * 7 * x))) * 0.5
def build_audio():
    AU.DUR = DUR; AU.N = int(AU.SR * DUR); N = AU.N; s = np.zeros((N, 2))
    for p in P[1:5]: AU.place(s, AU.whoosh(0.4, 1.0), p - 0.28, 0.25)
    if KEY == "r25":
        AU.place(s, AU.whoosh(0.5, 1.6), PE[0] - 0.2, 0.5)
        for j in range(5): AU.place(s, scribble(0.2), P[1] + 0.35 + j * 0.25, 0.25)
        for tt in (P[2] + 1.0, P[2] + 1.6): AU.place(s, AU.whoosh(0.25, 2.0), tt, 0.4)
        x = t_(1.6); AU.place(s, np.diff(np.random.default_rng(6).standard_normal(len(x)), prepend=0) * (0.4 + 0.6 * (np.sin(2 * np.pi * 30 * x) > 0)) * 0.3, P[3], 0.5)
        AU.place(s, AU.soft_impact(), P[4] + 0.33, 0.8); AU.place(s, AU.wood_knock(), P[4] + 0.33, 0.5)
    if KEY == "r27":
        AU.place(s, AU.shutter(), P[1] + 0.05, 0.6); x = t_(0.9); AU.place(s, np.random.default_rng(8).standard_normal(len(x)) * np.exp(-x * 4) * 0.2, P[1] + 0.15, 0.3)
        for j in range(4): AU.place(s, AU.wood_knock(), P[2] + 0.2 + j * 0.3, 0.35)
        AU.place(s, AU.wood_knock(), P[3], 0.4); AU.place(s, AU.wood_knock(), P[4], 0.5)
    if KEY == "r29":
        AU.place(s, scribble(0.8), 0.15, 0.3); AU.place(s, scribble(0.6), 1.3, 0.3); AU.place(s, scribble(1.6), P[1] + 0.1, 0.25); AU.place(s, scribble(1.5), P[2] + 0.1, 0.3)
        for j in range(6): AU.place(s, AU.pop(700 + j * 80), P[3] + j * 0.2, 0.15)
        AU.place(s, scribble(0.7), P[4] + 0.1, 0.3)
    AU.place(s, AU.success_chime(), P[4] + 0.5, 0.12)
    m = music({"r25": "funk", "r27": "guitar", "r29": "piano"}[KEY]); v = np.zeros((N, 2)); AU.place(v, AU.load_mp3(os.path.join(HERE, MP3)), VO, 1.0)
    vel = np.abs(v[:, 0]); kk = np.ones(int(0.12 * AU.SR)) / int(0.12 * AU.SR); duck = 1 - 0.45 * np.clip(np.convolve(vel, kk, "same") * 12, 0, 1)
    mix = (v * 0.95 + np.tanh(s * 1.2) * 0.7 + m * 0.9 * duck[:, None]) * 0.7
    raw = os.path.join(HERE, f"{KEY}_v2_mix_raw.wav"); AU.write(raw, mix); out = os.path.join(HERE, f"{KEY}_v2_mix.wav")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", raw, "-af", "loudnorm=I=-14:TP=-1.0:LRA=9", "-ar", "48000", out], check=True); os.remove(raw)

if __name__ == "__main__":
    mode = sys.argv[2]
    if mode == "frames":
        for tp in [float(x) for x in sys.argv[3].split(",")]: frame(tp).save(os.path.join(HERE, f"{KEY}_v2_f{tp:05.2f}.png"))
        print(KEY, [round(float(p), 2) for p in P], DUR)
    elif mode == "audio": build_audio()
    elif mode == "seg":
        i, n = int(sys.argv[3]), int(sys.argv[4]); fps = 60; N = int(round(DUR * fps)); a, b = N * i // n, N * (i + 1) // n
        ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1080x1920", "-r", str(fps), "-i", "-",
                               "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p", os.path.join(HERE, f"{KEY}_v2_seg{i}.mp4")], stdin=subprocess.PIPE)
        for k in range(a, b): ff.stdin.write(frame(k / fps).tobytes())
        ff.stdin.close(); ff.wait()

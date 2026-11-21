"""Cinematic overview reel for jurnalalimentar.fit - 1080x1920, voiced by ElevenLabs take ovvo1.mp3."""
import math, os, sys, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import reel2 as R
from reel2 import cl, e_out, e_inout, e_back, lerp, LIME, LIME2, WHITE, INK, logo

W, H, FPS = 1080, 1920, 30
DUR = 22.5
VO = 0.3  # voice offset
FD = "/usr/share/fonts/opentype/inter/"
def F(name, s): return ImageFont.truetype(FD + name + ".otf", s)
F_DISP_L = F("InterDisplay-Light", 118)
F_DISP_B = F("InterDisplay-Black", 150)
F_DISP_M = F("InterDisplay-SemiBold", 96)
F_CHAP = F("Inter-SemiBold", 34)
F_SUB = F("Inter-Medium", 46)
F_WORD = F("InterDisplay-Bold", 104)
F_TAG = F("Inter-Medium", 40)

def img(n): return Image.open(os.path.join(HERE, n)).convert("RGB")
SCREENS = {k: img(v) for k, v in {
    "home": "ov/home_full.png", "scan": "ov/scan.png", "menu": "ov/rest_menu.png", "photo": "ov/photo.png",
    "macros": "ov/home_macros.png", "history": "ov/history_full.png", "more": "ov/more.png"}.items()}

# ---------- phone with a dark bezel ----------
PW = 640
def build_phone(shot):
    sc = shot.resize((PW, round(shot.height * PW / shot.width)), Image.LANCZOS)
    sh = sc.height
    b = 20
    ph = Image.new("RGBA", (PW + 2 * b, sh + 2 * b), (0, 0, 0, 0)); d = ImageDraw.Draw(ph)
    d.rounded_rectangle([0, 0, ph.width - 1, ph.height - 1], 92, fill=(14, 16, 15, 255))
    d.rounded_rectangle([2, 2, ph.width - 3, ph.height - 3], 90, outline=(95, 110, 100, 255), width=3)
    m = Image.new("L", sc.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, PW - 1, sh - 1], 74, fill=255)
    ph.paste(sc, (b, b), m)
    d.rounded_rectangle([ph.width / 2 - 88, b + 14, ph.width / 2 + 88, b + 60], 23, fill=(0, 0, 0, 255))
    # glass highlight
    gl = Image.new("RGBA", ph.size, (0, 0, 0, 0)); gd = ImageDraw.Draw(gl)
    gd.polygon([(0, 0), (ph.width * 0.55, 0), (0, ph.height * 0.35)], fill=(255, 255, 255, 18))
    ph.alpha_composite(Image.composite(gl, Image.new("RGBA", ph.size, (0, 0, 0, 0)), ph.getchannel("A")))
    return ph
PHONES = {k: build_phone(v) for k, v in SCREENS.items()}

def coeffs(dst, src):
    A = []; B = []
    for (x, y), (u, v) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); B.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); B.append(v)
    return np.linalg.solve(np.array(A, float), np.array(B, float)).tolist()

def place_phone(canvas, ph, cx, cy, scale=1.0, ry=0.0, rx=0.0, rz=0.0, alpha=1.0, blur=0, shadow=True):
    """Project the phone in 3D (degrees) and composite it centred at (cx, cy)."""
    w, h = ph.width * scale, ph.height * scale
    f = 2600.0
    pts = []
    for x, y in [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]:
        a = math.radians(rz); x, y = x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)
        a = math.radians(ry); x, z = x * math.cos(a), x * math.sin(a)
        a = math.radians(rx); y, z = y * math.cos(a) - z * math.sin(a), y * math.sin(a) + z * math.cos(a)
        s = f / (f + z); pts.append((cx + x * s, cy + y * s))
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    x0, y0 = int(max(min(xs) - 2, -2000)), int(max(min(ys) - 2, -2000))
    x1, y1 = int(max(xs) + 2), int(max(ys) + 2)
    bw, bh = x1 - x0, y1 - y0
    if bw <= 4 or bh <= 4: return
    local = [(px - x0, py - y0) for px, py in pts]
    src = [(0, 0), (ph.width, 0), (ph.width, ph.height), (0, ph.height)]
    t = ph.transform((bw, bh), Image.PERSPECTIVE, coeffs(local, src), Image.BILINEAR)
    if blur: t = t.filter(ImageFilter.GaussianBlur(blur))
    if alpha < 1: t.putalpha(t.getchannel("A").point(lambda v: int(v * alpha)))
    if shadow:
        sh = Image.new("RGBA", (bw + 240, bh + 240), (0, 0, 0, 0))
        ImageDraw.Draw(sh).polygon([(px + 120, py + 150) for px, py in local], fill=(0, 0, 0, int(160 * alpha)))
        sh = sh.resize((sh.width // 4, sh.height // 4)).filter(ImageFilter.GaussianBlur(14)).resize(sh.size)
        canvas.alpha_composite(sh, (x0 - 120, y0 - 120)) if x0 - 120 >= 0 and y0 - 120 >= 0 else paste_any(canvas, sh, x0 - 120, y0 - 120)
    paste_any(canvas, t, x0, y0)

def paste_any(canvas, im, x, y):
    """alpha_composite that tolerates negative / off-canvas offsets."""
    sx, sy = max(0, -x), max(0, -y)
    dx, dy = max(0, x), max(0, y)
    w = min(im.width - sx, canvas.width - dx); h = min(im.height - sy, canvas.height - dy)
    if w <= 0 or h <= 0: return
    canvas.alpha_composite(im.crop((sx, sy, sx + w, sy + h)), (dx, dy))

# ---------- atmosphere ----------
yy, xx = np.mgrid[0:H, 0:W]
rr = np.sqrt(((xx - W / 2) / (W * 0.9)) ** 2 + ((yy - H * 0.45) / (H * 0.75)) ** 2)
BG = (np.array([10, 34, 25]) * np.clip(1 - rr, 0, 1)[..., None] + np.array([2, 7, 5])).astype(np.uint8)
BG_IMG = Image.fromarray(BG, "RGB").convert("RGBA")
VIG = Image.fromarray(np.dstack([np.zeros((H, W), np.uint8)] * 3 + [(np.clip((rr - 0.45) / 0.6, 0, 1) ** 1.6 * 230).astype(np.uint8)]), "RGBA")
rng = np.random.default_rng(3)
GRAIN = [Image.fromarray(np.dstack([rng.integers(0, 255, (H // 2, W // 2), dtype=np.uint8)] * 3 +
         [np.full((H // 2, W // 2), 16, np.uint8)]), "RGBA").resize((W, H)) for _ in range(6)]
def soft(r, col, a):
    s = int(r * 4); im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    ImageDraw.Draw(im).ellipse([r, r, 3 * r, 3 * r], fill=col + (a,)); return im.filter(ImageFilter.GaussianBlur(r * 0.7))
GLOW_L = soft(320, LIME2, 110)
GLOW_T = soft(280, (40, 190, 150), 90)
BOKEH = []
for i in range(34):
    r = int(rng.integers(6, 34)); BOKEH.append((soft(r, (210, 245, 170) if i % 3 else (255, 255, 255), int(rng.integers(40, 120))),
                                                float(rng.uniform(0, W)), float(rng.uniform(0, H)), float(rng.uniform(8, 40)), float(rng.uniform(0, 6.28))))

def atmosphere(t, glow_xy=(540, 1100), glow_k=1.0):
    im = BG_IMG.copy()
    gx, gy = glow_xy
    paste_any(im, GLOW_T, int(gx - 640 - 200 * math.sin(t * 0.3)), int(gy - 560 + 80 * math.cos(t * 0.25)))
    if glow_k > 0:
        g = GLOW_L if glow_k >= 1 else Image.fromarray((np.array(GLOW_L) * np.array([1, 1, 1, glow_k])).astype(np.uint8), "RGBA")
        paste_any(im, g, int(gx - 640), int(gy - 640))
    for sp, x, y, v, ph in BOKEH:
        yy_ = (y - v * t) % (H + 200) - 100
        paste_any(im, sp, int(x + 30 * math.sin(t * 0.4 + ph) - sp.width / 2), int(yy_ - sp.height / 2))
    return im

def light_sweep(im, t, t0, dur=1.1):
    k = (t - t0) / dur
    if not 0 <= k <= 1: return
    band = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(band)
    x = lerp(-700, W + 700, e_inout(k))
    d.polygon([(x - 160, 0), (x + 40, 0), (x - 420, H), (x - 620, H)], fill=(220, 255, 190, int(60 * math.sin(k * math.pi))))
    im.alpha_composite(band.filter(ImageFilter.GaussianBlur(40)))

# ---------- type ----------
_cache = {}
def tlayer(txt, font, fill, spacing=0):
    key = (txt, font.path, font.size, fill, spacing)
    if key in _cache: return _cache[key]
    d0 = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    wid = sum(d0.textlength(c, font=font) for c in txt) + spacing * (len(txt) - 1)
    asc, desc = font.getmetrics()
    im = Image.new("RGBA", (int(wid + 60), asc + desc + 60), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    x = 30
    for c in txt:
        d.text((x, 30 + asc), c, font=font, fill=fill, anchor="ls"); x += d0.textlength(c, font=font) + spacing
    _cache[key] = im; return im

def reveal(canvas, txt, font, fill, x, y, t, t0, t1=None, dur=0.6, spacing=0, anchor="l", rise=30, out=0.35):
    """Blur-in / blur-out text. (x, y) = left (or centre) and top."""
    k = (t - t0) / dur
    if k <= 0: return
    kout = 1.0 if t1 is None else cl((t1 - t) / out)
    if kout <= 0: return
    k = e_out(k); a = min(k, kout)
    lay = tlayer(txt, font, fill, spacing)
    q = round((1 - a) * 8) / 8
    if q > 0:
        lay = lay.filter(ImageFilter.GaussianBlur(q * 14))
    if a < 1: lay = lay.copy(); lay.putalpha(lay.getchannel("A").point(lambda v: int(v * a)))
    px = x - 30 if anchor == "l" else x - lay.width / 2
    paste_any(canvas, lay, int(px), int(y - 30 + (1 - k) * rise))

def chapter(canvas, t, t0, t1, num, label):
    reveal(canvas, num, F_CHAP, LIME, 70, 300, t, t0, t1, spacing=6)
    k = e_out((t - t0 - 0.1) / 0.6) * cl((t1 - t) / 0.35)
    if k > 0:
        ImageDraw.Draw(canvas).line([(130, 322), (130 + 120 * k, 322)], fill=LIME + (int(255 * k),), width=3)
    reveal(canvas, label, F_CHAP, (225, 235, 228), 280, 300, t, t0 + 0.12, t1, spacing=8)

# ---------- scenes (absolute times; voice phrase starts are +VO) ----------
P = [0.0, 2.01, 4.42, 6.10, 8.17, 9.95, 12.41, 15.55, 17.15, 18.84]
P = [p + VO for p in P]
CUTS = [0.0, 2.15, 4.55, 6.25, 8.3, 10.1, 12.55, 15.45, 19.0, DUR]

def sc_open(t):
    im = atmosphere(t, (540, 980), glow_k=e_inout(t / 1.6) * 0.8)
    reveal(im, "Nu mai ghici", F_DISP_L, (235, 240, 236), 540, 720, t, 0.35, anchor="c", spacing=2)
    reveal(im, "caloriile.", F_DISP_B, LIME, 540, 860, t, 0.95, anchor="c", spacing=1, rise=50)
    light_sweep(im, t, 0.9, 1.2)
    return im

def sc_phone(t):
    lt = t - CUTS[1]
    im = atmosphere(t, (540, 1250))
    k = e_out(lt / 1.1)
    place_phone(im, PHONES["home"], 560, lerp(1950, 1260, k) + 10 * math.sin(t), 0.95 + 0.04 * lt / 2.4,
                ry=lerp(-28, -12, k) + 2 * lt, rx=lerp(18, 6, k), rz=lerp(-6, -2, k))
    reveal(im, "Telefonul tău", F_DISP_M, WHITE, 70, 330, t, CUTS[1] + 0.05)
    reveal(im, "le știe deja.", F_DISP_M, LIME, 70, 450, t, CUTS[1] + 0.55)
    return im

def headline(im, t, t0, t1, l1, l2):
    reveal(im, l1, F_DISP_M, WHITE, 70, 372, t, t0 + 0.15, t1, rise=24)
    reveal(im, l2, F_DISP_M, LIME, 70, 486, t, t0 + 0.45, t1, rise=24)

def feature(t, i, shot, num, label, ry0, ry1, extra=None, lines=None):
    a, b = CUTS[i], CUTS[i + 1]; lt = t - a; k = e_out(lt / 0.9); span = b - a
    im = atmosphere(t, (560 if i % 2 else 500, 1150))
    side = 1 if i % 2 else -1
    place_phone(im, PHONES[shot], 540 + side * lerp(160, 40, k), 1240 + 8 * math.sin(t * 1.2),
                lerp(0.86, 0.98, lt / span), ry=lerp(ry0, ry1, lt / span), rx=lerp(10, 4, k), rz=side * lerp(4, 1, k))
    chapter(im, t, a + 0.05, b + 0.3, num, label)
    if lines: headline(im, t, a, b + 0.3, *lines)
    if extra: extra(im, t, lt)
    return im

def scan_fx(im, t, lt):
    # green scan beam sweeping the phone screen
    if lt < 0.3: return
    y = 800 + (math.sin((lt - 0.3) * 3.2) * 0.5 + 0.5) * 860
    beam = Image.new("RGBA", (W, 160), (0, 0, 0, 0)); d = ImageDraw.Draw(beam)
    d.rectangle([250, 76, 830, 84], fill=LIME + (230,))
    beam = beam.filter(ImageFilter.GaussianBlur(10)); ImageDraw.Draw(beam).rectangle([270, 78, 810, 82], fill=(240, 255, 220, 255))
    paste_any(im, beam, 0, int(y - 80))

def shutter_fx(im, t, lt):
    k = (lt - 0.45) / 0.35
    if 0 <= k <= 1:
        im.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(200 * (1 - k)))))

def sc_scan(t): return feature(t, 2, "scan", "01", "SCANEAZĂ", -18, -6, scan_fx, ("Scanezi", "eticheta."))
def sc_menu(t): return feature(t, 3, "menu", "02", "RESTAURANTE", 16, 6, None, ("Cauți meniul", "de la restaurant."))
def sc_photo(t): return feature(t, 4, "photo", "03", "POZĂ MASĂ", -14, -4, shutter_fx, ("Fotografiezi", "farfuria."))

def sc_day(t):
    a, b = CUTS[5], CUTS[6]; lt = t - a; k = e_out(lt / 1.0)
    im = atmosphere(t, (540, 1150))
    place_phone(im, PHONES["history"], lerp(820, 760, k), 1250, 0.78, ry=24, rx=6, rz=5, blur=5, alpha=0.85)
    place_phone(im, PHONES["macros"], lerp(300, 330, k), 1270, 0.78, ry=-24, rx=6, rz=-5, blur=5, alpha=0.85)
    place_phone(im, PHONES["home"], 540, lerp(1800, 1250, k), 0.95, ry=lerp(-8, 3, lt / 2.4), rx=lerp(14, 4, k))
    chapter(im, t, a + 0.05, b + 0.3, "04", "ZIUA TA")
    headline(im, t, a, b + 0.3, "Vezi ziua ta,", "dintr-o privire.")
    return im

def sc_plan(t):
    a, b = CUTS[6], CUTS[7]; lt = t - a; k = e_out(lt / 1.0)
    im = atmosphere(t, (520, 1150))
    place_phone(im, PHONES["more"], 540, 1260 + 6 * math.sin(t), lerp(0.84, 1.0, lt / 2.9), ry=lerp(20, 4, k), rx=lerp(12, 3, k), rz=lerp(3, 0, k))
    chapter(im, t, a + 0.05, b + 0.3, "05", "PLANUL TĂU")
    headline(im, t, a, b + 0.3, "Un plan făcut", "pentru tine.")
    k2 = e_back((lt - 1.0) / 0.4)
    if lt > 1.0:
        tw = ImageDraw.Draw(im).textlength("Premium", font=F_TAG)
        chip = Image.new("RGBA", (int(tw + 64), 76), (0, 0, 0, 0))
        R.pill(chip, 0, 0, chip.width - 1, 75, LIME + (255,))
        ImageDraw.Draw(chip).text((32, 38), "Premium", font=F_TAG, fill=INK, anchor="lm")
        R.paste_scaled(im, chip, 700 + chip.width / 2 - 90, 322, 0.6 + 0.4 * k2)
    return im

def sc_logo(t):
    a = CUTS[7]; lt = t - a
    im = atmosphere(t, (540, 820), glow_k=cl(lt / 0.8))
    k = e_out((lt - 0.15) / 1.0)
    if k > 0:
        s = lerp(0.5, 0.95, k)
        lg = logo.copy()
        if k < 1: lg.putalpha(lg.getchannel("A").point(lambda v: int(v * k)))
        R.paste_scaled(im, lg, 540, 760, s)
    reveal(im, "Jurnal Alimentar", F_WORD, WHITE, 540, 1000, t, P[7] - 0.05, anchor="c", spacing=1)
    reveal(im, "ALIMENTAȚIE CU RITM", F_CHAP, LIME, 540, 1160, t, P[8] - 0.05, anchor="c", spacing=12)
    light_sweep(im, t, a + 0.1, 1.4)
    return im

def sc_cta(t):
    a = CUTS[8]; lt = t - a
    im = atmosphere(t, (540, 900), glow_k=0.8)
    R.paste_scaled(im, logo, 540, 600, 0.45)
    reveal(im, "Scrie în comentarii", F_DISP_M if False else F_SUB, (225, 235, 228), 540, 760, t, a + 0.1, anchor="c")
    k = (lt - 0.35) / 0.45
    if k > 0:
        pulse = 1 + 0.03 * math.sin(lt * 5)
        tw = ImageDraw.Draw(im).textlength("JURNAL", font=F_DISP_B)
        pim = Image.new("RGBA", (int(tw + 150), 230), (0, 0, 0, 0))
        R.pill(pim, 0, 0, pim.width - 1, 229, LIME + (255,), 64)
        ImageDraw.Draw(pim).text((pim.width / 2, 118), "JURNAL", font=F_DISP_B, fill=INK, anchor="mm")
        R.paste_scaled(im, pim, 540, 940, (0.55 + 0.45 * e_back(k, 1.8)) * pulse * 0.82)
    reveal(im, "și-ți trimit linkul", F_SUB, (225, 235, 228), 540, 1090, t, a + 0.9, anchor="c")
    reveal(im, "jurnalalimentar.fit", F_CHAP, LIME, 540, 1200, t, a + 1.3, anchor="c", spacing=4)
    return im

SCENES = [sc_open, sc_phone, sc_scan, sc_menu, sc_photo, sc_day, sc_plan, sc_logo, sc_cta]

SUBS = [(P[0], P[1] - 0.4, "Nu mai ghici caloriile."), (P[1], P[2] - 0.5, "Telefonul tău le știe deja."),
        (P[2], P[3] - 0.5, "Scanezi eticheta."), (P[3], P[4] - 0.3, "Cauți meniul de la restaurant."),
        (P[4], P[5] - 0.3, "Fotografiezi farfuria."), (P[5], P[6] - 0.3, "Vezi ziua ta, dintr-o privire."),
        (P[6], P[7] - 0.8, "Și primești un plan făcut pentru tine.")]

def subtitles(im, t):
    for a, b, s in SUBS:
        if a <= t < b:
            if s in ("Nu mai ghici caloriile.",): return  # already huge on screen
            k = cl((t - a) / 0.25) * cl((b - t) / 0.25)
            lay = tlayer(s, F_SUB, (240, 245, 240))
            sh = tlayer(s, F_SUB, (0, 0, 0))
            for L, off in ((sh, 3), (lay, 0)):
                L2 = L.copy(); L2.putalpha(L.getchannel("A").point(lambda v: int(v * k * (0.8 if off else 1))))
                paste_any(im, L2, int(455 - L.width / 2 + off), int(1360 + off))

def frame(t):
    i = max(j for j in range(len(SCENES)) if t >= CUTS[j])
    im = SCENES[i](t)
    XF = 0.45
    if i > 0 and t - CUTS[i] < XF:
        prev = SCENES[i - 1](t)
        k = e_inout((t - CUTS[i]) / XF)
        prev = prev.filter(ImageFilter.GaussianBlur(k * 18))
        im = Image.blend(prev, im, k)
    im.alpha_composite(VIG)
    im.alpha_composite(GRAIN[int(t * FPS) % 6])
    # global fade in/out
    if t < 0.35: im = Image.blend(Image.new("RGBA", (W, H), (0, 0, 0, 255)), im, t / 0.35)
    if t > DUR - 0.5: im = Image.blend(im, Image.new("RGBA", (W, H), (0, 0, 0, 255)), (t - (DUR - 0.5)) / 0.5)
    return im.convert("RGB")

# ---------- score ----------
def score(path):
    sr = 44100; n = int(sr * DUR); tt = np.arange(n) / sr; out = np.zeros(n)
    def add(sig, at, g=1.0):
        i = int(at * sr); j = min(n, i + len(sig))
        if i < n: out[i:j] += sig[:j - i] * g
    # pad: slow chords Am - F - C - G, 2.8 s each
    chords = [[220.0, 261.63, 329.63], [174.61, 220.0, 261.63], [196.0, 261.63, 329.63], [196.0, 246.94, 293.66]]
    seg = 2.8
    for ci in range(int(DUR / seg) + 1):
        ch = chords[ci % 4]; a = ci * seg; L = int((seg + 1.2) * sr); x = np.arange(L) / sr
        env = np.minimum(1, x / 0.9) * np.minimum(1, np.maximum(0, (seg + 1.2 - x) / 1.2))
        sig = sum(np.sin(2 * np.pi * f * x + 0.3 * np.sin(2 * np.pi * 0.2 * x)) + 0.5 * np.sin(2 * np.pi * f * 1.003 * x)
                  + 0.25 * np.sin(2 * np.pi * f * 2 * x) for f in ch)
        add(sig * env, a, 0.035)
        add(np.sin(2 * np.pi * ch[0] / 2 * x) * env, a, 0.05)
    # soft arpeggio plucks
    step = 60 / 100 / 2
    for i in range(int(DUR / step)):
        at = i * step
        if 15.3 < at < 15.9: continue
        ch = chords[int(at / seg) % 4]; f = ch[i % 3] * 2
        L = int(0.5 * sr); x = np.arange(L) / sr
        add((np.sin(2 * np.pi * f * x) + 0.2 * np.sin(4 * np.pi * f * x)) * np.exp(-x * 7), at, 0.03 if at < 2 else 0.045)
    # heartbeat sub pulse from the phone reveal on
    for i in range(int((DUR - 2.15) / 0.6)):
        at = 2.15 + i * 0.6
        if 15.0 < at < 15.6: continue
        L = int(0.3 * sr); x = np.arange(L) / sr
        add(np.sin(2 * np.pi * (40 + 60 * np.exp(-x * 25)) * x) * np.exp(-x * 10), at, 0.32)
    # riser into the logo, then impact
    L = int(1.6 * sr); x = np.arange(L) / sr
    noise = np.random.default_rng(5).standard_normal(L)
    rise = noise * (x / 1.6) ** 2 * 0.25 + np.sin(2 * np.pi * (200 + 900 * (x / 1.6) ** 2) * x) * (x / 1.6) ** 3 * 0.15
    add(rise, CUTS[7] - 1.6, 0.6)
    L = int(2.5 * sr); x = np.arange(L) / sr
    boom = np.sin(2 * np.pi * (30 + 70 * np.exp(-x * 6)) * x) * np.exp(-x * 1.6)
    boom += np.random.default_rng(6).standard_normal(L) * np.exp(-x * 9) * 0.25
    add(boom, CUTS[7], 0.75)
    # whooshes on transitions
    for c in CUTS[1:7] + [CUTS[8]]:
        L = int(0.6 * sr); wn = np.random.default_rng(int(c * 100)).standard_normal(L)
        k_ = np.exp(-np.arange(300) / 60); wn = np.convolve(wn, k_ / k_.sum(), "same")
        add(wn * np.sin(np.linspace(0, np.pi, L)) ** 3, c - 0.35, 0.5)
    # shutter click on the photo scene
    L = int(0.08 * sr); x = np.arange(L) / sr
    add(np.random.default_rng(9).standard_normal(L) * np.exp(-x * 80), CUTS[4] + 0.45, 0.35)
    # gentle shimmer on the logo
    for j, f in enumerate([1318.5, 1567.98, 1975.53]):
        L = int(1.8 * sr); x = np.arange(L) / sr
        add(np.sin(2 * np.pi * f * x) * np.exp(-x * 2.2), CUTS[7] + 0.15 + j * 0.12, 0.03)
    out *= np.minimum(1, tt / 0.3) * np.minimum(1, (DUR - tt) / 0.8)
    out = np.tanh(out * 1.2) * 0.85
    st = np.stack([out, out], 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes((st * 32767).astype(np.int16).tobytes())

if __name__ == "__main__":
    out = sys.argv[1]
    if len(sys.argv) > 2:
        for tp in [float(x) for x in sys.argv[2].split(",")]:
            frame(tp).save(os.path.join(HERE, f"pv4_{tp:.1f}.png"))
        sys.exit()
    mus = os.path.join(HERE, "score4.wav"); score(mus)
    mix = os.path.join(HERE, "mix4.wav"); vo = os.path.join(HERE, "ovvo1.mp3")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mus, "-i", vo, "-filter_complex",
                    f"[1:a]adelay={int(VO*1000)}|{int(VO*1000)},aformat=channel_layouts=stereo,volume=1.5,apad,asplit=2[v][sc];"
                    "[0:a]volume=0.8[m];[m][sc]sidechaincompress=threshold=0.03:ratio=6:attack=30:release=400[md];"
                    "[md][v]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.0:LRA=11", "-ar", "44100", mix], check=True)
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", mix,
                           "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
                           "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)):
        ff.stdin.write(frame(i / FPS).tobytes())
    ff.stdin.close(); ff.wait(); print("done", out)

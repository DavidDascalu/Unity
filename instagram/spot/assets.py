"""Phase 2 assets for the 'Alimentație cu ritm' spot (9:16, 1080x1920).

Everything is drawn in code. App screens are rebuilt by eye from jurnalalimentar.fit
in dark mode, at 3x (1179x2556, iPhone 15 Pro points x3) so they stay sharp when the
phone fills the frame. Data on screens is real: search results and the label values
come from the app's own USDA catalog.

    python3 assets.py            -> writes assets/*.png and assets/_sheet.png
"""
import math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "assets")
LOGO_SRC = os.path.join(HERE, "..", "engine", "logo.png")   # official brand-logo.png from the site
os.makedirs(OUT, exist_ok=True)

# ---------- brand tokens (from the site CSS) ----------
SCENE = (11, 15, 12)        # #0B0F0C  (brief)
CARD = (26, 31, 27)         # #1A1F1B  (brief)
CARD2 = (34, 41, 36)
LINE = (48, 58, 51)
TEXT = (244, 246, 241)      # #F4F6F1  = --bg of the light theme
MUTED = (165, 188, 169)     # #A5BCA9  = --color-muted, Noapte verde
ACCENT = (148, 230, 2)      # #94E602  = logo leaf median
ACCENT_HI = (188, 251, 16)  # #BCFB10  = logo leaf highlight
PROT = (178, 231, 154)      # #B2E79A  = --green, Noapte verde (brightened protein green)
CARB = (216, 135, 85)       # #D88755  = --orange
FAT = (118, 156, 187)       # #769CBB  = --blue
INK = (8, 30, 22)

FD = "/usr/share/fonts/opentype/inter/"
def F(w, s): return ImageFont.truetype(FD + {"r": "Inter-Regular", "m": "Inter-Medium", "s": "Inter-SemiBold",
                                              "b": "Inter-Bold", "x": "Inter-ExtraBold", "k": "Inter-Black",
                                              "db": "InterDisplay-Bold", "dk": "InterDisplay-Black"}[w] + ".otf", s)

SW, SH = 1179, 2556          # screen at 3x
S = 3                        # px per point

def save(im, name):
    p = os.path.join(OUT, name); im.save(p); return p

def rr(d, box, r, **kw): d.rounded_rectangle(box, r, **kw)

# ---------- 1. logo with real transparency ----------
def logo_alpha():
    im = Image.open(LOGO_SRC).convert("RGB")
    a = np.asarray(im).astype(np.float32)
    # background is near-black green (#011102); leaf is bright. Alpha from luminance with a soft knee,
    # colour un-premultiplied against the background so edges stay clean.
    bg = np.array([1, 17, 2], np.float32)
    lum = a.max(axis=2)
    alpha = np.clip((lum - 28) / 70.0, 0, 1)
    col = np.where(alpha[..., None] > 0.02, (a - bg * (1 - alpha[..., None])) / np.maximum(alpha[..., None], 0.02), 0)
    out = np.dstack([np.clip(col, 0, 255), alpha * 255]).astype(np.uint8)
    lg = Image.fromarray(out, "RGBA")
    lg = lg.crop(lg.getbbox())
    return save(lg, "logo_alpha.png"), lg

# ---------- 2. titanium iPhone ----------
def phone_frame():
    pad = 30 * S // 3 * 3
    W, H = SW + 2 * 54, SH + 2 * 54
    im = Image.new("RGBA", (W + 40, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # side buttons
    for y0, y1, x in [(560, 760, 8), (820, 1100, 8), (1160, 1440, 8), (820, 1180, W + 22)]:
        rr(d, [x, y0, x + 14, y1], 7, fill=(120, 118, 112, 255))
    body = Image.new("RGBA", (W, H), (0, 0, 0, 0)); bd = ImageDraw.Draw(body)
    rr(bd, [0, 0, W - 1, H - 1], 210, fill=(104, 102, 97, 255))
    # brushed titanium: vertical gradient + fine noise on the rim
    g = np.linspace(0, 1, H)[:, None]
    tint = (np.array([150, 147, 140]) * (1 - g) + np.array([86, 84, 80]) * g)[..., None].transpose(0, 2, 1)
    tint = np.repeat(tint, W, axis=1)
    noise = np.random.default_rng(1).normal(0, 4, (H, W, 1))
    tex = np.clip(tint + noise, 0, 255).astype(np.uint8)
    tex_im = Image.fromarray(tex, "RGB").convert("RGBA")
    body = Image.composite(tex_im, body, body.getchannel("A"))
    bd = ImageDraw.Draw(body)
    rr(bd, [3, 3, W - 4, H - 4], 207, outline=(210, 206, 198, 255), width=4)
    rr(bd, [16, 16, W - 17, H - 17], 196, fill=(6, 7, 6, 255))            # black bezel
    im.alpha_composite(body, (20, 0))
    return im, (20 + 54, 54)   # frame, screen offset

def place_screen(frame_and_off, screen):
    frame, (ox, oy) = frame_and_off
    ph = frame.copy()
    m = Image.new("L", (SW, SH), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, SW - 1, SH - 1], 160, fill=255)
    ph.paste(screen.convert("RGB"), (ox, oy), m)
    d = ImageDraw.Draw(ph)
    rr(d, [ox + SW / 2 - 186, oy + 33, ox + SW / 2 + 186, oy + 141], 54, fill=(0, 0, 0, 255))   # dynamic island
    gl = Image.new("RGBA", ph.size, (0, 0, 0, 0)); gd = ImageDraw.Draw(gl)
    gd.polygon([(ox, oy), (ox + SW * 0.6, oy), (ox, oy + SH * 0.32)], fill=(255, 255, 255, 14))
    ph.alpha_composite(gl)
    return ph

# ---------- 3. app UI in dark mode ----------
def status_bar(d):
    d.text((150, 92), "9:41", font=F("s", 51), fill=TEXT, anchor="lm")
    for i in range(4):
        h = 18 + i * 9; d.rectangle([882 + i * 21, 108 - h, 896 + i * 21, 108], fill=TEXT)
    rr(d, [990, 76, 1080, 110], 10, outline=TEXT, width=4); rr(d, [996, 82, 1060, 104], 6, fill=TEXT)

def screen_base():
    im = Image.new("RGB", (SW, SH), SCENE); d = ImageDraw.Draw(im); status_bar(d); return im, d

def header(d, eyebrow, title, y=230):
    d.text((72, y), eyebrow, font=F("b", 36), fill=PROT)
    d.text((72, y + 60), title, font=F("db", 96), fill=TEXT)

SALMON = [("Somon sălbatic, gătit", 182), ("Somon atlantic, gătit", 206),
          ("Fish, salmon, Atlantic, wild, raw", 142), ("Fish, salmon, coho, wild, raw", 146),
          ("Fish, salmon, sockeye, raw", 131), ("Fish, salmon, pink, cooked, dry heat", 153)]   # real app results for "somon"

def search_screen(query="somon", rows=6, focus=True):
    im, d = screen_base()
    header(d, "ÎNREGISTRARE NOUĂ", "Adaugă un aliment")
    # mode pills
    x = 72
    for lab, on in [("Caută aliment", True), ("Scanează eticheta", False)]:
        w = d.textlength(lab, font=F("s", 42)) + 90
        rr(d, [x, 460, x + w, 576], 58, fill=ACCENT if on else CARD, outline=None if on else LINE, width=3)
        d.text((x + 45, 518), lab, font=F("s", 42), fill=INK if on else TEXT, anchor="lm"); x += w + 24
    rr(d, [72, 640, SW - 72, 2050], 60, fill=CARD)
    d.text((126, 700), "Caută în română sau engleză", font=F("s", 40), fill=MUTED)
    rr(d, [126, 770, SW - 126, 920], 44, fill=CARD2)
    d.text((186, 845), query, font=F("m", 54), fill=TEXT, anchor="lm")
    if focus:   # the green rhythm line becomes the focus underline
        d.rounded_rectangle([150, 905, SW - 150, 917], 6, fill=ACCENT)
    d.text((126, 980), "Aliment și preparare", font=F("s", 40), fill=MUTED)
    y = 1040
    for name, kc in SALMON[:rows]:
        nm = name
        while d.textlength(nm, font=F("m", 44)) > SW - 252 - 300: nm = nm[:-2]
        if nm != name: nm = nm.rstrip(" ,") + "…"
        d.text((126, y + 36), nm, font=F("m", 44), fill=TEXT, anchor="lm")
        d.text((SW - 126, y + 36), f"{kc} kcal", font=F("b", 44), fill=PROT, anchor="rm")
        d.line([(126, y + 96), (SW - 126, y + 96)], fill=LINE, width=2); y += 150
    d.text((126, 1990), "25 variante · valori medii USDA per 100 g", font=F("m", 36), fill=MUTED)
    rr(d, [600, 2250, SW - 72, 2420], 85, fill=ACCENT); d.text((870, 2335), "Adaugă în jurnal", font=F("b", 48), fill=INK, anchor="mm")
    return im

def food_card(name, kcal, w=900, h=300):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    rr(d, [0, 0, w - 1, h - 1], 56, fill=CARD + (245,), outline=LINE + (255,), width=3)
    rr(d, [40, 40, 160, 160], 36, fill=(56, 40, 30, 255))
    d.ellipse([70, 74, 130, 126], fill=(232, 132, 92, 255)); d.arc([70, 74, 130, 126], 200, 340, fill=(250, 190, 160, 255), width=5)
    lines, line = [], ""
    for word in name.split():
        t = (line + " " + word).strip()
        if d.textlength(t, font=F("s", 50)) < w - 240: line = t
        else: lines.append(line); line = word
    lines.append(line)
    for i, l in enumerate(lines[:2]): d.text((200, 52 + i * 62), l, font=F("s", 50), fill=TEXT)
    d.text((200, h - 74), f"{kcal} kcal", font=F("db", 64), fill=ACCENT_HI)
    d.text((200 + d.textlength(f"{kcal} kcal", font=F("db", 64)) + 18, h - 60), "/ 100 g", font=F("m", 40), fill=MUTED)
    return im

LABEL = {"kcal": "61", "prot": "3,5", "carb": "4,7", "fat": "3,3", "salt": "0,12"}   # Iaurt simplu integral, USDA via the app

def nutrition_label():
    w, h = 900, 1180
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    paper = Image.new("RGB", (w, h), (247, 244, 236))
    n = np.random.default_rng(4).normal(0, 3, (h, w, 1)); paper = Image.fromarray(np.clip(np.asarray(paper) + n, 0, 255).astype(np.uint8))
    m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], 28, fill=255)
    im.paste(paper, (0, 0), m); d = ImageDraw.Draw(im)
    k = (24, 24, 22)
    d.text((60, 60), "Declarație nutrițională", font=F("x", 58), fill=k)
    d.text((60, 140), "Iaurt simplu integral · valori medii per 100 g", font=F("s", 36), fill=k)
    d.rectangle([60, 210, w - 60, 226], fill=k)
    rows = [("Energie", f"{LABEL['kcal']} kcal", True), ("Grăsimi", f"{LABEL['fat']} g", False),
            ("Glucide", f"{LABEL['carb']} g", False), ("Proteine", f"{LABEL['prot']} g", False), ("Sare", f"{LABEL['salt']} g", False)]
    y = 260
    for lab, val, bold in rows:
        f = F("b" if bold else "m", 50)
        d.text((60, y + 50), lab, font=f, fill=k, anchor="lm"); d.text((w - 60, y + 50), val, font=f, fill=k, anchor="rm")
        d.line([(60, y + 110), (w - 60, y + 110)], fill=(60, 60, 56), width=3); y += 130
    # barcode
    x = 60; rng = np.random.default_rng(9)
    while x < 520:
        bw = int(rng.integers(3, 12)); d.rectangle([x, h - 200, x + bw, h - 70], fill=k); x += bw + int(rng.integers(4, 12))
    return im

def scan_screen(extracted=5, added=False):
    im, d = screen_base()
    header(d, "SCANEAZĂ ETICHETA", "Fotografiază eticheta")
    rr(d, [72, 470, SW - 72, 1460], 60, fill=(4, 6, 5))
    lab = nutrition_label().resize((720, 880))
    im.paste(lab, ((SW - 720) // 2, 530), lab)
    for (cx, cy, sx, sy) in [(120, 520, 1, 1), (SW - 120, 520, -1, 1), (120, 1410, 1, -1), (SW - 120, 1410, -1, -1)]:
        d.line([(cx, cy), (cx + 90 * sx, cy)], fill=ACCENT, width=10); d.line([(cx, cy), (cx, cy + 90 * sy)], fill=ACCENT, width=10)
    rr(d, [72, 1520, SW - 72, 2190], 60, fill=CARD)
    d.text((126, 1580), "Valori per 100 g", font=F("s", 40), fill=MUTED)
    vals = [("Calorii", f"{LABEL['kcal']} kcal", ACCENT_HI), ("Proteine", f"{LABEL['prot']} g", PROT),
            ("Carbohidrați", f"{LABEL['carb']} g", CARB), ("Grăsimi", f"{LABEL['fat']} g", FAT)]
    y = 1650
    for i, (n_, v, c) in enumerate(vals):
        on = i < extracted
        d.text((126, y + 40), n_, font=F("m", 48), fill=TEXT if on else (90, 100, 94), anchor="lm")
        d.text((SW - 126, y + 40), v if on else "—", font=F("b", 52), fill=c if on else (90, 100, 94), anchor="rm"); y += 120
    rr(d, [72, 2250, SW - 72, 2420], 85, fill=ACCENT)
    d.text((SW / 2, 2335), "Adăugat în jurnal." if added else "Adaugă în jurnal", font=F("b", 52), fill=INK, anchor="mm")
    return im

def glass_card(days_done=5):
    w, h = 900, 560
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    rr(d, [0, 0, w - 1, h - 1], 64, fill=(255, 255, 255, 22), outline=(255, 255, 255, 60), width=3)
    d.text((60, 60), "REZUMATUL ZILEI", font=F("b", 34), fill=PROT)
    d.text((60, 110), "Un pas odată", font=F("db", 84), fill=TEXT)
    days = ["L", "Ma", "Mi", "J", "V", "S", "D"]
    for i, dd in enumerate(days):
        cx = 110 + i * 113; cy = 380
        done = i < days_done
        d.ellipse([cx - 42, cy - 42, cx + 42, cy + 42], fill=ACCENT if done else (255, 255, 255, 28))
        if done: d.line([(cx - 18, cy + 2), (cx - 4, cy + 18), (cx + 20, cy - 16)], fill=INK, width=9, joint="curve")
        d.text((cx, cy + 82), dd, font=F("s", 34), fill=MUTED, anchor="mm")
    return im

def notification():
    w, h = 1000, 230
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    rr(d, [0, 0, w - 1, h - 1], 60, fill=(38, 42, 40, 235))
    lg = Image.open(LOGO_SRC).convert("RGBA").resize((120, 120)); m = Image.new("L", (120, 120), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, 119, 119], 28, fill=255); lg.putalpha(m); im.alpha_composite(lg, (40, 55))
    d.text((190, 52), "JURNAL ALIMENTAR", font=F("s", 30), fill=MUTED); d.text((w - 40, 52), "acum", font=F("m", 30), fill=MUTED, anchor="ra")
    d.text((190, 100), "Mementouri blânde", font=F("b", 42), fill=TEXT)
    d.text((190, 156), "Ai adăugat micul dejun?", font=F("m", 40), fill=TEXT)
    return im

# ---------- 4. kitchen: table + plate ----------
def wood_table(w=1600, h=1400):
    rng = np.random.default_rng(12)
    y = np.linspace(0, 1, h)[:, None]; x = np.linspace(0, 1, w)[None, :]
    grain = np.sin((y * 6 + 0.25 * np.sin(x * 5 + y * 4)) * 2 * np.pi * 3.0) * 0.5 + 0.5
    grain += 0.2 * np.sin((y * 61 + x * 1.7) * 2 * np.pi)
    plank = (np.floor(y * 3.0) % 2) * 0.07
    base = np.array([138, 92, 56]) * (0.72 + 0.22 * grain[..., None] + plank[..., None])
    n = rng.normal(0, 5, (h, w, 1))
    warm = np.exp(-(((x - 0.5) / 0.45) ** 2 + ((y - 0.35) / 0.5) ** 2))[..., None]   # warm pool of light
    img = base * (0.55 + 0.75 * warm) + n
    gaps = (np.abs((y * 3.0) % 1 - 0) < 0.003)[..., None] & (x >= 0)[..., None]
    img = np.where(gaps, img * 0.4, img)
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB")

def plate(size=900):
    s = size; im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    yy, xx = np.mgrid[0:s, 0:s]; c = s / 2
    r = np.sqrt((xx - c) ** 2 + (yy - c) ** 2) / (s / 2)
    # ceramic: rim, well, soft speculars
    a = np.clip((1 - r) * 60, 0, 1)
    shade = 236 - 30 * np.clip((r - 0.62) / 0.06, 0, 1) * np.clip((0.75 - r) / 0.08, 0, 1) - 18 * r
    lx = np.exp(-(((xx - c * 0.7) / (s * 0.25)) ** 2 + ((yy - c * 0.6) / (s * 0.18)) ** 2))
    col = np.dstack([shade + 10 * lx, shade + 8 * lx, shade * 0.97 + 6 * lx])
    rim = (np.abs(r - 0.70) < 0.012)
    col[rim] *= 0.9
    im = Image.fromarray(np.dstack([np.clip(col, 0, 255), a * 255]).astype(np.uint8), "RGBA")
    d = ImageDraw.Draw(im)
    # salmon fillet: organic mask, seared gradient, diagonal fat bands, soft specular
    fil = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    m = Image.new("L", (s, s), 0); md = ImageDraw.Draw(m)
    pts = [(c - 250, c - 40), (c - 200, c - 130), (c - 40, c - 150), (c + 140, c - 120), (c + 200, c - 50),
           (c + 170, c + 60), (c + 20, c + 95), (c - 160, c + 80), (c - 240, c + 30)]
    md.polygon(pts, fill=255); m = m.filter(ImageFilter.GaussianBlur(9)).point(lambda v: 255 if v > 128 else int(v * 1.9))
    u = (xx - c) / s; v = (yy - c) / s
    bands = 0.5 + 0.5 * np.sin((u * 1.0 + v * 0.35 + 0.05 * np.sin(v * 25 + u * 8)) * 2 * np.pi * 16)
    bands = np.clip((bands - 0.9) / 0.1, 0, 1) * 0.8
    top = np.clip((-(v) * 4 + 0.6), 0, 1)
    rgb = np.dstack([236 - 40 * top, 128 - 30 * top, 86 - 20 * top])
    rgb = rgb * (1 - bands[..., None]) + np.array([252, 206, 180]) * bands[..., None]
    spec = np.exp(-(((u + 0.08) / 0.12) ** 2 + ((v + 0.06) / 0.05) ** 2))[..., None]
    rgb = np.clip(rgb + 40 * spec, 0, 255)
    fil = Image.fromarray(np.dstack([rgb, np.asarray(m)]).astype(np.uint8), "RGBA")
    fd = ImageDraw.Draw(fil)
    # asparagus spears
    for k_ in range(5):
        sp = Image.new("RGBA", (460, 60), (0, 0, 0, 0)); sd = ImageDraw.Draw(sp)
        sd.rounded_rectangle([0, 16, 400, 44], 14, fill=(84, 140, 50, 255))
        sd.ellipse([370, 8, 450, 52], fill=(106, 158, 60, 255))
        sd.line([(14, 24), (360, 24)], fill=(150, 198, 104, 255), width=5)
        for q in range(5): sd.polygon([(60 + q * 70, 16), (80 + q * 70, 6), (92 + q * 70, 18)], fill=(96, 150, 56, 255))
        sp = sp.rotate(-6 + k_ * 3, Image.BICUBIC, expand=True)
        fil.alpha_composite(sp, (int(c - 230 + k_ * 12), int(c + 110 + k_ * 34)))
    # lemon wedge
    fd.pieslice([c + 150, c - 250, c + 320, c - 80], 120, 300, fill=(246, 214, 72, 255))
    fd.pieslice([c + 166, c - 234, c + 304, c - 96], 120, 300, fill=(252, 236, 150, 255))
    fil = fil.filter(ImageFilter.GaussianBlur(0.8))
    sh = fil.getchannel("A").filter(ImageFilter.GaussianBlur(14)); shadow = Image.new("RGBA", (s, s), (40, 30, 20, 0)); shadow.putalpha(sh.point(lambda v: int(v * 0.35)))
    im.alpha_composite(shadow, (8, 14)); im.alpha_composite(fil)
    return im

# ---------- 5. calendar + end card ----------
def calendar(done=21):
    w, h = 960, 900
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    rr(d, [0, 0, w - 1, h - 1], 60, fill=CARD + (250,))
    d.text((60, 50), "Istoricul tău", font=F("db", 70), fill=TEXT)
    d.text((60, 140), "Zile cu înregistrări · ultimele 30 de zile", font=F("m", 36), fill=MUTED)
    for i in range(30):
        cx = 120 + (i % 7) * 120; cy = 280 + (i // 7) * 120
        on = i < done
        rr(d, [cx - 48, cy - 48, cx + 48, cy + 48], 26, fill=ACCENT if on else (40, 48, 42))
        d.text((cx, cy), str(i + 1), font=F("b", 36), fill=INK if on else MUTED, anchor="mm")
    return im

def end_card(lg):
    im = Image.new("RGB", (1080, 1920), SCENE); d = ImageDraw.Draw(im)
    g = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0)); ImageDraw.Draw(g).ellipse([140, 360, 940, 1160], fill=ACCENT + (40,))
    im.paste(g.filter(ImageFilter.GaussianBlur(160)), (0, 0), g.filter(ImageFilter.GaussianBlur(160)))
    L = lg.resize((420, int(420 * lg.height / lg.width)), Image.LANCZOS); im.paste(L, ((1080 - L.width) // 2, 520), L)
    d.text((540, 1120), "Jurnal Alimentar", font=F("db", 96), fill=TEXT, anchor="mm")
    d.text((540, 1220), "jurnalalimentar.fit", font=F("s", 52), fill=MUTED, anchor="mm")
    rr(d, [300, 1330, 780, 1460], 65, fill=ACCENT); d.text((540, 1395), "Descarcă aplicația", font=F("b", 48), fill=INK, anchor="mm")
    return im

if __name__ == "__main__":
    _, lg = logo_alpha()
    fr = phone_frame(); save(fr[0], "phone_frame.png")
    shots = {"screen_search": search_screen(), "screen_scan": scan_screen(), "screen_scan_added": scan_screen(added=True)}
    for k, v in shots.items(): save(v, k + ".png"); save(place_screen(fr, v), "phone_" + k[7:] + ".png")
    for i, (n, kc) in enumerate(SALMON): save(food_card(n, kc), f"card_{i + 1}.png")
    save(nutrition_label(), "label.png"); save(glass_card(), "glass_card.png"); save(notification(), "notification.png")
    save(wood_table(), "table.png"); save(plate(), "plate.png"); save(calendar(), "calendar.png"); save(end_card(lg), "end_card.png")
    # contact sheet
    order = ["logo_alpha", "phone_search", "phone_scan", "phone_scan_added", "card_1", "card_3", "label", "glass_card",
             "notification", "table", "plate", "calendar", "end_card"]
    tiles = []
    for n in order:
        t = Image.open(os.path.join(OUT, n + ".png")).convert("RGBA"); t.thumbnail((360, 560))
        bg = Image.new("RGBA", (380, 580), SCENE + (255,)); bg.alpha_composite(t, ((380 - t.width) // 2, (580 - t.height) // 2))
        ImageDraw.Draw(bg).text((10, 556), n, font=F("m", 18), fill=MUTED); tiles.append(bg)
    cols = 7; sheet = Image.new("RGB", (380 * cols, 580 * math.ceil(len(tiles) / cols)), (30, 30, 30))
    for i, t in enumerate(tiles): sheet.paste(t, ((i % cols) * 380, (i // cols) * 580), t)
    sheet.save(os.path.join(OUT, "_sheet.png")); print("ok", len(order))

"""'Alimentație cu ritm' - one continuous 9:16 shot, rendered entirely in code (+ the real plate photo).

    python3 render.py preview      -> out/preview_540x960_30fps.mp4
    python3 render.py final        -> out/spot_1080x1920_60fps.mp4 (with 3-subframe motion blur)
    python3 render.py frames 0.2,3.5,...   -> out/f_<t>.png stills

Frames are composed at 1080x1920 in layout coordinates; preview just downsamples.
All timings come from audio/cues.json, the same cue list the sound was built on.
"""
import json, math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import assets as AS

W, H = 1080, 1920
CUE = json.load(open(os.path.join(HERE, "audio", "cues.json"), encoding="utf-8"))
C = CUE["cues"]; DUR = CUE["duration"]
OUT = os.path.join(HERE, "out"); os.makedirs(OUT, exist_ok=True)

SCENE, TEXT, MUTED, ACC, ACC_HI = AS.SCENE, AS.TEXT, AS.MUTED, AS.ACCENT, AS.ACCENT_HI
PROT, CARB, FAT, INK = AS.PROT, AS.CARB, AS.FAT, AS.INK
INKLINE = (70, 92, 80)          # the line "cooled into ink"
F = AS.F

# ---------------- easing ----------------
def cl(x, a=0.0, b=1.0): return max(a, min(b, x))
def k01(t, a, b): return cl((t - a) / (b - a)) if b > a else float(t >= a)
def eo(x): x = cl(x); return 1 - (1 - x) ** 3
def eio(x): x = cl(x); return x * x * (3 - 2 * x)
def eio5(x): x = cl(x); return x ** 3 * (x * (6 * x - 15) + 10)
def eback(x, s=1.4): x = cl(x) - 1; return x * x * ((s + 1) * x + s) + 1
def lerp(a, b, k): return a + (b - a) * k
def lerp2(p, q, k): return (lerp(p[0], q[0], k), lerp(p[1], q[1], k))

# ---------------- static assets ----------------
A = lambda n: Image.open(os.path.join(HERE, "assets", n)).convert("RGBA")
LOGO = A("logo_alpha.png")
PLATE = A("plate_photo.png")
TABLE = Image.open(os.path.join(HERE, "assets", "table.png")).convert("RGB")
FRAME = AS.phone_frame()
CARDS = [A(f"card_{i + 1}.png") for i in range(6)]
LABEL = A("label.png")
GLASS = AS.glass_card(5)
NOTIF = A("notification.png")
END = Image.open(os.path.join(HERE, "assets", "end_card.png")).convert("RGBA")
yy, xx = np.mgrid[0:H, 0:W]
rr = np.sqrt(((xx - W / 2) / (W * 0.95)) ** 2 + ((yy - H * 0.45) / (H * 0.8)) ** 2)
VIG = Image.fromarray(np.dstack([np.zeros((H, W), np.uint8)] * 3 + [(np.clip((rr - 0.42) / 0.6, 0, 1) ** 1.7 * 210).astype(np.uint8)]), "RGBA")
_rng = np.random.default_rng(5)
GRAIN = [Image.fromarray(np.dstack([_rng.integers(0, 255, (H // 2, W // 2), dtype=np.uint8)] * 3 + [np.full((H // 2, W // 2), 12, np.uint8)]), "RGBA").resize((W, H)) for _ in range(8)]
def soft(r, col, a):
    s = int(r * 4); im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    ImageDraw.Draw(im).ellipse([r, r, 3 * r, 3 * r], fill=col + (a,)); return im.filter(ImageFilter.GaussianBlur(r * 0.7))
GLOW_W = soft(420, (255, 214, 150), 38)   # warm breathing glow
GLOW_G = soft(300, ACC, 60)

# ---------------- compositing helpers ----------------
def paste(canvas, im, x, y):
    x, y = int(round(x)), int(round(y))
    sx, sy = max(0, -x), max(0, -y); dx, dy = max(0, x), max(0, y)
    w = min(im.width - sx, canvas.width - dx); h = min(im.height - sy, canvas.height - dy)
    if w > 0 and h > 0: canvas.alpha_composite(im.crop((sx, sy, sx + w, sy + h)), (dx, dy))

def fade(im, a):
    if a >= 0.999: return im
    im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * a))); return im

def fast_blur(im, r):
    if r < 0.6: return im
    f = 4 if r > 8 else 2
    s = im.resize((max(1, im.width // f), max(1, im.height // f)), Image.BILINEAR).filter(ImageFilter.GaussianBlur(r / f))
    return s.resize(im.size, Image.BILINEAR)

def scaled(im, s):
    return im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.BILINEAR)

def coeffs(dst, src):
    Am, B = [], []
    for (x, y), (u, v) in zip(dst, src):
        Am.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); B.append(u)
        Am.append([0, 0, 0, x, y, 1, -v * x, -v * y]); B.append(v)
    return np.linalg.solve(np.array(Am, float), np.array(B, float)).tolist()

def project(w, h, cx, cy, s, rx=0, ry=0, rz=0, f=2400.0):
    pts = []
    for x, y in [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]:
        x, y = x * s, y * s
        a = math.radians(rz); x, y = x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)
        a = math.radians(ry); x, z = x * math.cos(a), x * math.sin(a)
        a = math.radians(rx); y, z = y * math.cos(a) - z * math.sin(a), y * math.sin(a) + z * math.cos(a)
        k = f / (f + z); pts.append((cx + x * k, cy + y * k))
    return pts

def place3d(canvas, im, cx, cy, s, rx=0, ry=0, rz=0, alpha=1.0, blur=0, shadow=0.0):
    pts = project(im.width, im.height, cx, cy, s, rx, ry, rz)
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    x0, y0, x1, y1 = int(min(xs)) - 2, int(min(ys)) - 2, int(max(xs)) + 2, int(max(ys)) + 2
    if x1 - x0 < 4 or y1 - y0 < 4 or x1 < 0 or y1 < 0 or x0 > W or y0 > H: return pts
    local = [(px - x0, py - y0) for px, py in pts]
    src_scale = min(1.0, max(0.15, (x1 - x0) / im.width * 1.3))   # pre-shrink big sources for speed
    srcim = im if src_scale > 0.95 else scaled(im, src_scale)
    src = [(0, 0), (srcim.width, 0), (srcim.width, srcim.height), (0, srcim.height)]
    t = srcim.transform((x1 - x0, y1 - y0), Image.PERSPECTIVE, coeffs(local, src), Image.BILINEAR)
    if shadow > 0:
        sh = Image.new("RGBA", (x1 - x0 + 200, y1 - y0 + 240), (0, 0, 0, 0))
        ImageDraw.Draw(sh).polygon([(px + 100, py + 150) for px, py in local], fill=(0, 0, 0, int(170 * shadow * alpha)))
        paste(canvas, fast_blur(sh, 40), x0 - 100, y0 - 100)
    if blur: t = fast_blur(t, blur)
    paste(canvas, fade(t, alpha), x0, y0)
    return pts

# ---------------- the rhythm line ----------------
def glow_line(canvas, pts, width=10, col=ACC, inten=1.0, head=None):
    if len(pts) < 2 or inten <= 0.01: return
    lay = Image.new("RGBA", (W // 4, H // 4), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    q = [(x / 4, y / 4) for x, y in pts]
    d.line(q, fill=col + (int(160 * inten),), width=max(2, int(width * 2.2 / 4)), joint="curve")
    lay = lay.filter(ImageFilter.GaussianBlur(6)).resize((W, H), Image.BILINEAR)
    canvas.alpha_composite(lay)
    core = Image.new("RGBA", (W, H), (0, 0, 0, 0)); cd = ImageDraw.Draw(core)
    cd.line(pts, fill=tuple(min(255, int(c * 0.6 + 255 * 0.4)) for c in col) + (int(255 * min(1, inten)),), width=max(2, int(width * 0.5)), joint="curve")
    canvas.alpha_composite(core)
    if head is not None:
        hx, hy = head; g = scaled(GLOW_G, 0.35 * (0.8 + 0.4 * inten)); paste(canvas, g, hx - g.width / 2, hy - g.height / 2)

def poly_partial(pts, k):
    """First fraction k of a polyline (by length)."""
    if k >= 1: return pts
    seg = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]; L = sum(seg) * k; out = [pts[0]]
    for i, s in enumerate(seg):
        if L <= s:
            out.append(lerp2(pts[i], pts[i + 1], L / s if s else 0)); break
        out.append(pts[i + 1]); L -= s
    return out

def ellipse_pts(cx, cy, a, b, a0=0, a1=360, n=90, tilt=0):
    out = []
    for i in range(n + 1):
        th = math.radians(lerp(a0, a1, i / n))
        x, y = a * math.cos(th), b * math.sin(th)
        ct, st = math.cos(math.radians(tilt)), math.sin(math.radians(tilt))
        out.append((cx + x * ct - y * st, cy + x * st + y * ct))
    return out

# ---------------- type ----------------
_tc = {}
def text_img(txt, font, fill, accent=None, acol=ACC_HI):
    key = (txt, font.path, font.size, fill, accent)
    if key in _tc: return _tc[key]
    d0 = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    asc, desc = font.getmetrics(); w = d0.textlength(txt, font=font)
    im = Image.new("RGBA", (int(w + 40), asc + desc + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(im); x = 20
    for word in txt.split(" "):
        col = acol if accent and word.strip(".,!?").lower() == accent.lower() else fill
        d.text((x, 20 + asc), word, font=font, fill=col, anchor="ls"); x += d0.textlength(word + " ", font=font)
    _tc[key] = im; return im

def reveal(canvas, txt, font, cx, top, t, t0, t1=None, fill=TEXT, accent=None, rise=26):
    k = eo(k01(t, t0, t0 + 0.55)); ko = 1.0 if t1 is None else eio(k01(t, t1, t1 - 0.35 if False else t1 + 0.35))
    a = k * (1 - (0 if t1 is None else eio(k01(t, t1, t1 + 0.35))))
    if a <= 0.01: return
    im = text_img(txt, font, fill, accent)
    q = round((1 - a) * 6) / 6
    if q > 0: im = im.filter(ImageFilter.GaussianBlur(q * 12))
    paste(canvas, fade(im, a), cx - im.width / 2, top - 20 + (1 - k) * rise)

SUBS = [("Ce mănânci azi?", 2.50, 4.0), ("Scanezi. Gata!", 5.00, 7.0), ("Fiecare masă contează.", 8.00, 9.9),
        ("Un pas odată.", 12.20, 13.6)]       # 17.60 "Alimentație cu ritm." is shown as the tagline itself
F_SUB = F("b", 50)

def subtitles(canvas, t):
    for txt, a, b in SUBS:
        if a - 0.05 <= t < b + 0.3:
            k = eo(k01(t, a - 0.05, a + 0.2)) * (1 - eio(k01(t, b, b + 0.3)))
            im = text_img(txt, F_SUB, TEXT)
            pad = Image.new("RGBA", (im.width + 40, im.height + 8), (0, 0, 0, 0))
            ImageDraw.Draw(pad).rounded_rectangle([0, 0, pad.width - 1, pad.height - 1], 38, fill=(6, 9, 7, 170))
            pad.alpha_composite(im, (20, 4))
            paste(canvas, fade(pad, k), W / 2 - pad.width / 2, 1738 + (1 - k) * 12)

DISCLAIMER = text_img("Valorile nutriționale sunt estimări și pot varia.", F("m", 26), (150, 165, 155))

# ---------------- phone ----------------
PH_S = 0.46                                  # phone scale on screen (frame 1327x2664 -> ~664x1332)
PH_CX, PH_CY = 540, 1010
def phone_img(screen):
    return AS.place_screen(FRAME, screen)

def scr2frame(x, y, cx, cy, s):
    """Screen pixel (in the 1179x2556 screen) -> frame coords, for an un-rotated phone."""
    fw, fh = FRAME[0].size; ox, oy = FRAME[1]
    return (cx + (ox + x - fw / 2) * s, cy + (oy + y - fh / 2) * s)

def typed(t):
    n = sum(1 for tt in C["type"] if t >= tt); return "somon"[:n]

# ---------------- scenes (each draws into the canvas in layout coords) ----------------
LOGO_W = 400
def logo_layer(canvas, cx, cy, w, reveal_x=None, alpha=1.0):
    lg = scaled(LOGO, w / LOGO.width)
    if reveal_x is not None:
        m = Image.new("L", lg.size, 0); rx = reveal_x - (cx - lg.width / 2)
        if rx > 0: ImageDraw.Draw(m).rectangle([0, 0, rx, lg.height], fill=255)
        m = m.filter(ImageFilter.GaussianBlur(6)); a = ImageChops.multiply(lg.getchannel("A"), m); lg = lg.copy(); lg.putalpha(a)
    paste(canvas, fade(lg, alpha), cx - lg.width / 2, cy - lg.height / 2)
    return lg.height

def s1_impact(c, t):
    ly = 1140
    if t < C["impact"]:                                   # light streak flying at the camera
        k = eio(t / C["impact"]); half = lerp(30, 520, k); th = lerp(4, 26, k)
        glow_line(c, [(540 - half, ly), (540 + half, ly)], width=th, inten=lerp(0.4, 1.3, k))
        return
    lt = t - C["impact"]
    head = lerp(150, 930, eio5(k01(t, C["impact"] + 0.05, 1.35)))
    flash = max(0, 1 - lt / 0.25)
    if flash > 0: paste(c, fade(scaled(GLOW_G, 1.4), flash), 540 - 840, ly - 840)
    for i in range(18):                                   # light shards
        a = (i * 137.5) % 360; sp = 420 + (i * 53) % 260; d = eo(k01(lt, 0, 0.7)) * sp
        x, y = 540 + math.cos(math.radians(a)) * d, ly + math.sin(math.radians(a)) * d * 0.55
        if lt < 0.75:
            ImageDraw.Draw(c).line([(x, y), (x - math.cos(math.radians(a)) * 30, y - math.sin(math.radians(a)) * 16)],
                                   fill=ACC_HI + (int(255 * (1 - lt / 0.75)),), width=4)
    logo_layer(c, 540, 860, LOGO_W, reveal_x=head + 10)
    glow_line(c, [(150, ly), (head, ly)], width=12, inten=1.0, head=(head, ly) if head < 925 else None)

def s2_search(c, t):
    # logo lifts and fades, phone rises and lands on 2.40, line becomes the search focus line
    k = eio(k01(t, 1.6, 2.3))
    logo_layer(c, 540, lerp(860, 170, k), lerp(LOGO_W, 150, k), alpha=1 - eio(k01(t, 1.9, 2.35)))
    land = C["phone_land"]
    py = lerp(2400, PH_CY, eback(k01(t, 1.75, land), 1.1)) if t < land + 0.01 else PH_CY + 8 * math.sin((t - land) * 1.3)
    rows = sum(1 for x in [2.80, 2.95, 3.10, 3.20, 3.30, 3.30] if t >= x) if t >= 2.8 else 0
    scr = AS.search_screen(typed(t), rows=min(6, rows * 2 if rows < 3 else 6), focus=False)
    back = eio(k01(t, 3.4, 3.9)) * (1 - eio(k01(t, 4.5, 4.95)))
    cam = (1.0 + 0.10 * eio(k01(t, 4.3, 4.8))) * (1 - 0.14 * back)
    s = PH_S * cam
    ph = phone_img(scr)
    place3d(c, ph, PH_CX, py + 60 * back, s, rx=lerp(14, 0, eo(k01(t, 1.75, land))), blur=back * 6, alpha=1 - 0.35 * back, shadow=0.8)
    # line: from under the logo into the search field underline
    a = scr2frame(150, 911, PH_CX, py, s); b = scr2frame(1179 - 150, 911, PH_CX, py, s)
    km = eio(k01(t, 1.6, 2.55))
    p0 = lerp2((150, 1140), a, km); p1 = lerp2((930, 1140), b, km)
    glow_line(c, [p0, p1], width=lerp(12, 7, km), inten=1.0 - 0.2 * k01(t, 3.4, 4.0))
    # six cards peel off into depth and fan out
    if t >= C["cards"][0]:
        for i, card in enumerate(CARDS):
            t0 = C["cards"][i]; kc = eo(k01(t, t0, t0 + 0.5))
            if kc <= 0: continue
            row_y = scr2frame(0, 1080 + i * 150, PH_CX, py, s)[1]
            ang = lerp(-30, 30, i / 5)
            tx = 540 + math.sin(math.radians(ang)) * 860; ty = 700 + (i % 3) * 330 + (1 - math.cos(math.radians(ang))) * 300
            cx = lerp(540, tx, kc); cy = lerp(row_y, ty, kc)
            depth = 1 - abs(i - 2.5) / 2.5
            place3d(c, card, cx, cy, lerp(0.45, 0.62 + 0.10 * depth, kc), ry=lerp(0, -ang * 0.9, kc), rx=lerp(0, 8, kc),
                    rz=lerp(0, ang * 0.35, kc), alpha=min(1, kc * 2) * (1 - eio(k01(t, 4.85, 5.2))), blur=(1 - depth) * 3 * kc, shadow=0.5)
        # line outlines card 1
        if t >= C["outline_card1"]:
            ang = -30; tx = 540 + math.sin(math.radians(ang)) * 860; ty = 700 + (1 - math.cos(math.radians(ang))) * 300
            pts = project(CARDS[0].width, CARDS[0].height, tx, ty, 0.62, ry=27, rx=8, rz=-10.5)
            path = pts + [pts[0]]
            glow_line(c, poly_partial(path, eio(k01(t, C["outline_card1"], C["outline_card1"] + 0.35))), width=6,
                      inten=1 - eio(k01(t, 4.9, 5.2)))
    return py, s

def s3_scan(c, t):
    # phone swings to the scan screen, photographs the label, laser = the line, TAP on Adaugă, line shoots out
    k = eio(k01(t, 4.8, 5.3))
    extracted = sum(1 for x in C["extract"] if t >= x) - 1 if t >= C["extract"][0] else 0
    scr = AS.scan_screen(extracted=max(0, min(4, extracted)), added=t >= C["added"])
    s = PH_S * lerp(1.10, 1.18, k)
    ry = lerp(0, -6, k) + lerp(0, 6, eio(k01(t, 6.0, 6.6)))
    py = PH_CY + lerp(0, 40, k)
    # the paper label floats in front for the shutter, then is "inside" the viewfinder
    if t < 5.5:
        kl = eo(k01(t, 4.85, 5.15)); a = 1 - eio(k01(t, 5.15, 5.45))
        place3d(c, LABEL, 540, lerp(1900, 860, kl), 0.62, rx=lerp(30, 10, kl), rz=-4, alpha=a, shadow=0.6)
    ph = phone_img(scr)
    pts = place3d(c, ph, PH_CX, py, s, ry=ry, shadow=0.8)
    if abs(t - C["shutter"]) < 0.18:
        c.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(200 * (1 - abs(t - C["shutter"]) / 0.18)))))
    # laser over the viewfinder
    la, lb = C["laser"]
    if la <= t <= lb + 0.1:
        u = (math.sin((t - la) / (lb - la) * math.pi * 2 - math.pi / 2) * 0.5 + 0.5)
        y = scr2frame(0, lerp(560, 1390, u), PH_CX, py, s)[1]
        x0 = scr2frame(130, 0, PH_CX, py, s)[0]; x1 = scr2frame(1179 - 130, 0, PH_CX, py, s)[0]
        glow_line(c, [(x0, y), (x1, y)], width=8, inten=1.0)
    # TAP ripple on Adaugă
    bx, by = scr2frame(590, 2335, PH_CX, py, s)
    kt = k01(t, C["tap_add"], C["tap_add"] + 0.45)
    if 0 < kt < 1:
        r = lerp(20, 110, eo(kt)); ImageDraw.Draw(c).ellipse([bx - r, by - r, bx + r, by + r], outline=(255, 255, 255, int(220 * (1 - kt))), width=6)
    # line shoots up out of the button
    ks = k01(t, 6.15, 6.6)
    if ks > 0:
        top = lerp(by, -50, eo(ks)); glow_line(c, [(bx, by), (bx, top)], width=lerp(10, 18, ks), inten=1.2 * (1 - k01(t, 6.6, 7.0)))
    if 5.3 <= t <= 7.0:
        a = eo(k01(t, 5.4, 5.8)) * (1 - eio(k01(t, 6.8, 7.0)))
        paste(c, fade(DISCLAIMER, a), W / 2 - DISCLAIMER.width / 2, 1855)
    return (PH_CX, scr2frame(0, 1300, PH_CX, py, s)[1])

MAC = [("Proteine", "3,5 g", PROT, 0.72), ("Carbohidrați", "4,7 g", CARB, 0.58), ("Grăsimi", "3,3 g", FAT, 0.46)]
def dial_img(t, size=900):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0)); d = ImageDraw.Draw(im); cx = cy = size / 2
    for i, (lab, val, col, frac) in enumerate(MAC):
        r = 400 - i * 92
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(34, 42, 36, 255), width=58)
        kf = eio(k01(t, C["rings"][0] + i * 0.18, C["rings"][1] - 0.2 + i * 0.05)) * frac
        if kf > 0.002:
            d.arc([cx - r, cy - r, cx + r, cy + r], -90, -90 + 360 * kf, fill=col + (255,), width=58)
            ang = math.radians(-90 + 360 * kf); hx, hy = cx + r * math.cos(ang), cy + r * math.sin(ang)
            d.ellipse([hx - 34, hy - 34, hx + 34, hy + 34], fill=tuple(min(255, int(v * 0.5 + 128)) for v in col) + (255,))
    kc = int(round(61 * eio(k01(t, C["kcal_ticks"][0], C["kcal_ticks"][-1]))))
    d.text((cx, cy - 30), str(kc), font=F("dk", 150), fill=TEXT, anchor="mm")
    d.text((cx, cy + 70), "kcal înregistrate", font=F("m", 36), fill=MUTED, anchor="mm")
    return im

def s4_dial(c, t):
    # we came through the screen: the dial grows out of the dark, rotates to 3/4, glass card, dive
    k = eo(k01(t, 7.1, 7.8))
    ry = lerp(0, 24, eio(k01(t, 8.0, 9.4))); rx = lerp(0, 10, eio(k01(t, 8.0, 9.4)))
    dive = eio(k01(t, 9.6, 10.1))
    place3d(c, dial_img(t), lerp(540, 470, eio(k01(t, 8.0, 9.4))), 900, lerp(0.6, 0.98, k) * (1 + 0.6 * dive), ry=ry, rx=rx,
            alpha=k * (1 - dive), blur=dive * 14)
    # legend
    for i, (lab, val, col, _) in enumerate(MAC):
        a = eo(k01(t, 7.6 + i * 0.12, 8.0 + i * 0.12)) * (1 - dive) * (1 - eio(k01(t, 8.85, 9.15)))
        y = 1420 + i * 64
        im = text_img(f"{lab}  {val}", F("s", 40), TEXT)
        if a < 0.03: continue
        dot = Image.new("RGBA", (34, 34), (0, 0, 0, 0)); ImageDraw.Draw(dot).ellipse([2, 2, 32, 32], fill=col + (255,)); paste(c, fade(dot, a), 298, y + 16)
        paste(c, fade(im, a), 350, y)
    kg = eback(k01(t, C["glass_card"], C["glass_card"] + 0.5), 1.2)
    if t >= C["glass_card"]:
        place3d(c, GLASS, lerp(640, 560, kg), lerp(1560, 1470, kg), 0.66, ry=-18, rx=6, alpha=min(1, kg) * (1 - dive), blur=dive * 10, shadow=0.5)
    paste(c, fade(DISCLAIMER, (1 - dive) * eo(k01(t, 7.4, 7.9))), W / 2 - DISCLAIMER.width / 2, 1855)

def table_layer(t):
    # wood plane in perspective, warm
    tb = TABLE.resize((1600, 1400)).convert("RGBA")
    return tb

TB_CACHE = {}
def s5_kitchen(c, t):
    ke = eio(k01(t, 9.9, 10.6))
    tb = table_layer(t)
    place3d(c, tb, 540, lerp(1500, 1320, ke), 1.25, rx=62, alpha=ke, blur=lerp(16, 2, ke))
    warm = scaled(GLOW_W, 1.3); paste(c, fade(warm, ke * (0.8 + 0.2 * math.sin(t * 1.4))), 540 - warm.width / 2, 700 - warm.height / 2)
    # words carved on the table; the plate settles on "masă"
    kw = eo(k01(t, 10.6, 11.2)) * (1 - eio(k01(t, 13.0, 13.4)))
    words = text_img("Fiecare masă contează.", F("db", 84), TEXT, accent="masă")
    paste(c, fade(words, kw), 540 - words.width / 2, 1330)
    masa_x = 540 - words.width / 2 + 20 + ImageDraw.Draw(Image.new("RGBA", (1, 1))).textlength("Fiecare ", font=F("db", 84)) + 95
    land = C["plate_settle"]; kp = eio(k01(t, 10.1, land))
    px = lerp(560, masa_x + 10, kp); py = lerp(760, 1360, kp) + (6 * math.sin((t - 10) * 2.2) if t < land else 0)
    ps = lerp(0.62, 0.40, kp)
    pts = place3d(c, PLATE, px, py, ps, rx=lerp(8, 0, kp), rz=lerp(-6, 0, kp), alpha=eo(k01(t, 10.0, 10.5)) * (1 - eio(k01(t, 13.1, 13.5))),
                  shadow=0.9 if t >= land - 0.2 else 0.5)
    pw, ph = PLATE.width * ps, PLATE.height * ps
    # the line orbits the plate once, then settles on the rim and cools into ink
    o0, o1 = C["plate_orbit"]
    if t >= o0:
        ko = eio(k01(t, o0, o1)); a_end = lerp(0, 360, ko) + 200
        col = tuple(int(lerp(a_, b_, eio(k01(t, o1, o1 + 0.9)))) for a_, b_ in zip(ACC, INKLINE))
        if t < o1:
            path = ellipse_pts(px, py, pw * 0.62, ph * 0.62, a_end - 70, a_end, 30)
            glow_line(c, path, width=9, col=col, head=path[-1])
        else:
            path = ellipse_pts(px, py, pw * 0.505, ph * 0.505, 200, 200 + 360 * eio(k01(t, o1, o1 + 0.6)), 80)
            glow_line(c, path, width=lerp(9, 5, k01(t, o1, o1 + 0.9)), col=col, inten=lerp(1.0, 0.55, k01(t, o1, o1 + 0.9)) * (1 - eio(k01(t, 13.1, 13.5))))
    # notification
    kn = eback(k01(t, C["notification"], C["notification"] + 0.45), 1.0) * (1 - eio(k01(t, 13.0, 13.4)))
    if t >= C["notification"]:
        paste(c, fade(scaled(NOTIF, 0.92), cl(kn)), 540 - NOTIF.width * 0.46, lerp(-260, 250, cl(kn)))

def calendar_img(t):
    im = AS.calendar(done=0).copy(); d = ImageDraw.Draw(im)
    for i in range(30):
        kd = k01(t, C["days"][min(i, 20)], C["days"][min(i, 20)] + 0.15) if i < 21 else 0
        if kd <= 0: continue
        cx = 120 + (i % 7) * 120; cy = 280 + (i // 7) * 120
        g = tuple(int(lerp(a, b, kd)) for a, b in zip((40, 48, 42), ACC))
        d.rounded_rectangle([cx - 48, cy - 48, cx + 48, cy + 48], 26, fill=g)
        d.text((cx, cy), str(i + 1), font=F("b", 36), fill=INK if kd > 0.5 else MUTED, anchor="mm")
    return im

def s6_progress(c, t):
    ku = eio(k01(t, 13.3, 14.1))
    reveal(c, "Un pas odată.", F("db", 96), 540, 300, t, 13.5, 17.35, accent="pas")
    cal = calendar_img(t)
    pts = place3d(c, cal, 540, lerp(1150, 900, ku), 0.92, rx=lerp(70, 8, ku), ry=lerp(0, -6, eio(k01(t, 14, 17))), alpha=ku * (1 - eio(k01(t, 17.3, 17.7))), shadow=0.6)
    # line walks the lit days
    if C["days"][0] <= t <= C["days"][-1] + 0.3:
        i = min(20, int((t - C["days"][0]) / 0.075))
        tl, tr, br, bl = pts
        def cal2frame(u, v):  # bilinear in the projected quad (u,v in 0..1 of card)
            top = lerp2(tl, tr, u); bot = lerp2(bl, br, u); return lerp2(top, bot, v)
        cx = (120 + (i % 7) * 120) / 960; cy = (280 + (i // 7) * 120 + 60) / 900
        x0 = (120 - 48) / 960
        glow_line(c, [cal2frame(x0, cy), cal2frame(cx, cy)], width=6, head=cal2frame(cx, cy))
    # weight curve, no numbers
    k0, k1 = C["curve"]
    if t >= k0:
        kc = eio(k01(t, k0, k1)); base_y = 1560
        xs = np.linspace(170, 910, 60); ys = base_y - 30 - 70 * np.sin(np.linspace(0.2, 2.9, 60)) + 14 * np.sin(np.linspace(0, 11, 60))
        path = list(zip(xs, ys)); a = 1 - eio(k01(t, 17.3, 17.7))
        ImageDraw.Draw(c).line([(170, base_y + 60), (910, base_y + 60)], fill=(48, 58, 51, int(255 * a)), width=2)
        part = poly_partial(path, kc)
        glow_line(c, part, width=7, inten=a, head=part[-1] if kc < 1 else None)
        lab = text_img("tendința greutății", F("m", 32), MUTED); paste(c, fade(lab, a * kc), 170, base_y + 76)

def s7_final(c, t):
    k = eio(k01(t, 17.5, 18.1))
    logo_layer(c, 540, 820, lerp(260, LOGO_W, k), alpha=k)
    ly = 1100
    half = lerp(40, 390, eo(k01(t, 17.5, 17.9)))
    pulse = max(0, 1 - (t - C["final_hit"]) / 0.4) if t >= C["final_hit"] else 0
    glow_line(c, [(540 - half, ly), (540 + half, ly)], width=12 + 18 * pulse, inten=1 + pulse)
    if pulse > 0:
        g = scaled(GLOW_G, 1.0 + pulse); paste(c, fade(g, pulse), 540 - g.width / 2, ly - g.height / 2)
    reveal(c, "Alimentație cu ritm.", F("db", 92), 540, 1180, t, 17.6, accent="ritm")

def s_end(c, t):
    k = eio(k01(t, 19.2, 19.9)); z = 1 + 0.03 * k01(t, 19.2, 21.2)
    e = scaled(END, z); paste(c, fade(e, k), 540 - e.width / 2, 960 - e.height / 2)

# ---------------- camera + frame ----------------
def camera(t):
    # slow drift always; shakes on the two hits; push through the phone screen 6.6-7.2
    dx = 10 * math.sin(t * 0.7) + 6 * math.sin(t * 1.9); dy = 8 * math.cos(t * 0.55); rot = 0.4 * math.sin(t * 0.45)
    z = 1.0 + 0.015 * math.sin(t * 0.8)
    for hit, amp in [(C["impact"], 16), (C["final_hit"], 10)]:
        if 0 <= t - hit < 0.35:
            e = (1 - (t - hit) / 0.35) ** 2; dx += amp * e * math.sin((t - hit) * 90); dy += amp * e * math.cos((t - hit) * 77)
    push = eio(k01(t, 6.55, 7.15)) if t < 7.15 else 0.0
    z *= 1 + 5.0 * push ** 2.2
    return dx, dy, rot, z, push

def frame(t):
    c = Image.new("RGBA", (W, H), SCENE + (255,))
    breathe = 0.75 + 0.25 * math.sin(t * 2 * math.pi / 4.0)
    g = scaled(GLOW_W, 1.15); paste(c, fade(g, breathe), 540 - g.width / 2, 860 - g.height / 2)
    focus = (540, 960)
    if t < 1.6: s1_impact(c, t)
    elif t < 4.8: s2_search(c, t)
    elif t < 7.2: focus = s3_scan(c, t)
    if 7.1 <= t < 10.1: s4_dial(c, t)
    if 9.9 <= t < 13.5: s5_kitchen(c, t)
    if 13.3 <= t < 17.7: s6_progress(c, t)
    if 17.5 <= t < 19.6: s7_final(c, t)
    if t >= 19.2: s_end(c, t)
    dx, dy, rot, z, push = camera(t)
    cx, cy = focus if push > 0 else (540, 960)
    # affine camera around (cx, cy)
    cos, sin = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    a, b = cos / z, sin / z; d_, e = -sin / z, cos / z
    cxo, cyo = W / 2 + dx, H / 2 + dy
    tx = cx - a * cxo - b * cyo; ty = cy - d_ * cxo - e * cyo
    c = c.transform((W, H), Image.AFFINE, (a, b, tx, d_, e, ty), Image.BILINEAR, fillcolor=SCENE + (255,))
    if push > 0.25: c = Image.blend(c, Image.new("RGBA", (W, H), SCENE + (255,)), cl((push - 0.25) / 0.45))
    subtitles(c, t)
    c.alpha_composite(VIG); c.alpha_composite(GRAIN[int(t * 60) % 8])
    if t < 0.05: c = Image.blend(Image.new("RGBA", (W, H), (0, 0, 0, 255)), c, t / 0.05)
    if t > DUR - 0.4: c = Image.blend(c, Image.new("RGBA", (W, H), (0, 0, 0, 255)), k01(t, DUR - 0.4, DUR))
    return c.convert("RGB")

def render(out, fps, size, subframes=1, mix=os.path.join(HERE, "audio", "mix.wav")):
    n = int(round(DUR * fps))
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{size[0]}x{size[1]}",
                           "-r", str(fps), "-i", "-", "-i", mix, "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out],
                          stdin=subprocess.PIPE)
    for i in range(n):
        t = i / fps
        if subframes > 1:
            acc = None
            for s in range(subframes):
                f = np.asarray(frame(t + (s / subframes - 0.5) / fps * 0.5), np.float32)
                acc = f if acc is None else acc + f
            im = Image.fromarray((acc / subframes).astype(np.uint8))
        else:
            im = frame(t)
        if im.size != size: im = im.resize(size, Image.LANCZOS)
        ff.stdin.write(im.tobytes())
        if i % 60 == 0: print(f"{i}/{n}", flush=True)
    ff.stdin.close(); ff.wait(); print("done", out)

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "preview"
    if mode == "frames":
        for tp in [float(x) for x in sys.argv[2].split(",")]:
            frame(tp).save(os.path.join(OUT, f"f_{tp:05.2f}.png"))
    elif mode == "preview":
        render(os.path.join(OUT, "preview_540x960_30fps.mp4"), 30, (540, 960))
    elif mode == "final":
        render(os.path.join(OUT, "spot_1080x1920_60fps.mp4"), 60, (1080, 1920), subframes=3)

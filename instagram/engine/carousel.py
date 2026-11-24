"""Brand carousel renderer: 1080x1350 slides for @jurnalul.alimentar, in the site's 2026 design
(cream / mint / night-green surfaces, Fraunces display serif, Inter text, white cards, orange call to action).

Usage: python3 carousel.py spec.json out_dir prefix
spec = {"style": "light"|"lime"|"dark", "slides": [{"kind": "cover"|"stake"|"item"|"recap"|"list"|"swatches"|"cta", ...}]}
"""
import json, os, sys
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1080, 1350
M = 96                       # side margin
FD = "/usr/share/fonts/opentype/inter/"
FRAUNCES = os.path.join(HERE, "fonts", "Fraunces.ttf")
HANDLE = "@jurnalul.alimentar"; SITE = "jurnalalimentar.fit"

@lru_cache(None)
def F(n, s): return ImageFont.truetype(FD + n + ".otf", s)
@lru_cache(None)
def FR(s, w=400):
    f = ImageFont.truetype(FRAUNCES, s); f.set_variation_by_axes([min(144, max(9, s)), w, 0, 0]); return f

def hx(c): return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))
ORANGE = hx("#ff7a3d"); ORANGE_INK = hx("#2b1407")
STYLES = {
    #        bg top        bg bottom     ink            accent         muted          card           border         soft tile      halo
    "light": ("#fbf7f0", "#f6f1e7", "#193b2e", "#1e7a50", "#61766b", "#ffffff", "#e6e2d6", "#edf3ed", "#e8f2e6"),
    "lime":  ("#e8f2e6", "#dcebd6", "#193b2e", "#b4531f", "#4f6a5c", "#ffffff", "#d2e3cf", "#f0f6eb", "#d1e69d"),
    "dark":  ("#20563e", "#153a2b", "#fbf7f0", "#c2ee83", "#b9cfc0", "#24503d", "#2f6149", "#2c5c46", "#2b6b4d"),
}
S = {}
def set_style(name):
    t, b, ink, acc, mut, card, bord, soft, halo = (hx(c) for c in STYLES[name])
    yy, xx = np.mgrid[0:H, 0:W]
    k = (yy / H)[..., None]
    bg = np.array(t) * (1 - k) + np.array(b) * k
    r = np.sqrt(((xx - W * 0.85) / W) ** 2 + ((yy - H * 0.12) / H) ** 2); g = np.clip(1 - r / 0.55, 0, 1)[..., None] ** 2
    bg = bg * (1 - g * 0.7) + np.array(halo) * g * 0.7
    S.update(name=name, bg=Image.fromarray(bg.astype(np.uint8), "RGB"), ink=ink, acc=acc, mut=mut, card=card, bord=bord, soft=soft)

logo_src = Image.open(os.path.join(HERE, "logo.png")).convert("RGBA")
def logo(sz, rad):
    lg = logo_src.resize((sz, sz), Image.LANCZOS); m = Image.new("L", (sz, sz), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, sz - 1, sz - 1], rad, fill=255); lg.putalpha(ImageChops.multiply(lg.getchannel("A"), m)); return lg

def wrap(d, text, font, maxw):
    out = []
    for para in text.split("\n"):
        line = ""
        for w in para.split():
            t = (line + " " + w).strip()
            if d.textlength(t, font=font) <= maxw: line = t
            else: out.append(line); line = w
        out.append(line)
    return out

def tracked(d, x, y, text, font, fill, track):
    for ch in text:
        d.text((x, y), ch, font=font, fill=fill, anchor="ls"); x += d.textlength(ch, font=font) + track
    return x

def vfont(text, size):   # Fraunces has no arrows: fall back to Inter for those values
    return F("InterDisplay-SemiBold", int(size * 0.86)) if any(c in text for c in "→←") else FR(size)

def card(im, box, r=34, fill=None, border=True):
    x0, y0, x1, y1 = [int(v) for v in box]
    if S["name"] != "dark":
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle([x0, y0 + 14, x1, y1 + 14], r, fill=(27, 73, 49, 26)); im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(22)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([x0, y0, x1, y1], r, fill=fill or S["card"], outline=S["bord"] if border else None, width=2)
    return d

def base(i, n):
    im = S["bg"].convert("RGBA"); d = ImageDraw.Draw(im)
    im.alpha_composite(logo(76, 20), (M, 78))
    tracked(d, M + 100, 108, "JURNAL ALIMENTAR", F("Inter-SemiBold", 22), S["mut"], 4.2)
    d.text((M + 100, 146), "Alimentație cu ritm", font=FR(34), fill=S["ink"], anchor="ls")
    if n > 1:
        f = F("Inter-SemiBold", 28); t = f"{i} / {n}"; w = d.textlength(t, font=f)
        d.rounded_rectangle([W - M - w - 48, 88, W - M, 144], 28, fill=S["soft"]); d.text((W - M - w / 2 - 24, 117), t, font=f, fill=S["ink"], anchor="mm")
    d.line([(M, 196), (W - M, 196)], fill=S["bord"], width=2)
    d.text((M, H - 86), HANDLE, font=F("Inter-Medium", 28), fill=S["mut"], anchor="lm")
    d.text((W - M, H - 86), SITE, font=F("Inter-Medium", 28), fill=S["mut"], anchor="rm")
    return im, d

def eyebrow(d, y, text):
    d.line([(M, y - 10), (M + 52, y - 10)], fill=S["mut"], width=2)
    tracked(d, M + 76, y, text, F("Inter-SemiBold", 26), S["mut"], 4.5)
    return y + 56

SYM = "=×≈→←+−"
def is_fr(font): return getattr(font, "path", "") == FRAUNCES
def runs(line, font):   # Fraunces draws math symbols as hairlines and has no arrows: set those in Inter
    if not is_fr(font) or not any(c in SYM for c in line): return [(line, font)]
    sf = F("Inter-Regular", int(font.size * 0.62)); out = []
    for ch in line:
        f = sf if ch in SYM else font
        if out and out[-1][1] is f: out[-1] = (out[-1][0] + ch, f)
        else: out.append((ch, f))
    return out
def rich(d, x, y, line, font, fill, anchor="la"):
    rs = runs(line, font)
    if len(rs) == 1: d.text((W / 2, y) if anchor == "ma" else (x, y), line, font=font, fill=fill, anchor=anchor); return
    tw = sum(d.textlength(t, font=f) for t, f in rs)
    if anchor == "ma": x = W / 2 - tw / 2
    base_y = y + font.getmetrics()[0]
    for t, f in rs:
        yy = base_y - (font.size * 0.12 if f is not font else 0)
        d.text((x, yy), t, font=f, fill=fill, anchor="ls"); x += d.textlength(t, font=f)

def text_block(d, x, y, text, font, fill, maxw, lh=1.1, anchor="la"):
    for line in wrap(d, text, font, maxw):
        rich(d, x, y, line, font, fill, anchor)
        y += font.size * lh
    return y

def fit(d, text, size, maxw, maxlines, w=400):
    while size > 50 and len(wrap(d, text, FR(size, w), maxw)) > maxlines: size -= 4
    return FR(size, w)

def orange_pill(d, x, y, text, font, center=False, plus=True):
    w = d.textlength(text, font=font) + (font.size * 1.1 if plus else 0); h = font.size * 2.2
    if center: x = W / 2 - (w + 2 * font.size * 1.2) / 2
    d.rounded_rectangle([x, y, x + w + 2 * font.size * 1.2, y + h], h / 2, fill=ORANGE)
    tx = x + font.size * 1.2
    if plus:
        cx, cy, a = tx + font.size * 0.35, y + h / 2, font.size * 0.36
        d.line([(cx - a, cy), (cx + a, cy)], fill=ORANGE_INK, width=max(3, font.size // 9)); d.line([(cx, cy - a), (cx, cy + a)], fill=ORANGE_INK, width=max(3, font.size // 9))
        tx += font.size * 1.1
    d.text((tx, y + h / 2 + 1), text, font=font, fill=ORANGE_INK, anchor="lm")
    return y + h

def render(spec, out_dir, prefix):
    set_style(spec.get("style", "light"))
    slides = spec["slides"]; n = len(slides); paths = []
    for i, s in enumerate(slides, 1):
        page, _ = base(i, n); kind = s["kind"]; ink, acc, mut = S["ink"], S["acc"], S["mut"]
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im); bottom = H - 170
        if kind == "cover":
            y = 300
            if s.get("eyebrow"): y = eyebrow(d, y, s["eyebrow"])
            big = 124 if not s.get("image") else 104
            ft = fit(d, s["title"] + " " + s.get("accent", ""), big, W - 2 * M, 4)
            y = text_block(d, M, y + 10, s["title"], ft, ink, W - 2 * M, 1.02)
            if s.get("accent"): y = text_block(d, M, y, s["accent"], ft, acc, W - 2 * M, 1.02)
            y = text_block(d, M, y + 34, s.get("sub", ""), F("Inter-Regular", 40), mut, W - 2 * M - 40, 1.42)
            if s.get("image"):
                pic = Image.open(os.path.join(HERE, s["image"])).convert("RGBA"); mw, mh = s.get("image_box", [840, 420]); pic.thumbnail((mw, mh), Image.LANCZOS)
                py = int(y + 40); card(im, [M, py, W - M, py + pic.height + 60]); im.alpha_composite(pic, ((W - pic.width) // 2, py + 30)); d = ImageDraw.Draw(im)
            if s.get("keyword"): bottom = H - 330
            if s.get("swipe"): bottom = H - 260
        elif kind == "stake":
            ft = fit(d, s["title"], 104, W - 2 * M, 5)
            y = text_block(d, M, 330, s["title"], ft, ink, W - 2 * M, 1.06)
            text_block(d, M, y + 40, s.get("sub", ""), F("Inter-Regular", 42), mut, W - 2 * M - 40, 1.42)
        elif kind == "item":
            y = eyebrow(d, 300, s.get("rank", "").upper()) if s.get("rank") else 300
            big = FR(280); d.text((M - 8, y - 20), s["value"], font=big, fill=acc)
            vw = d.textlength(s["value"], font=big); d.text((M + vw + 14, y + 210), s.get("unit", ""), font=F("Inter-SemiBold", 56), fill=ink, anchor="ls")
            y = text_block(d, M, y + 300, s["name"], FR(76), ink, W - 2 * M, 1.08)
            text_block(d, M, y + 24, s.get("note", ""), F("Inter-Regular", 38), mut, W - 2 * M, 1.4)
        elif kind == "recap":
            ft = fit(d, s["title"], 84, W - 2 * M, 2)
            y = text_block(d, M, 260, s["title"], ft, ink, W - 2 * M, 1.05) + 36
            rh = 132 if len(s["rows"]) <= 4 else 118
            d = card(im, [M, y, W - M, y + rh * len(s["rows"]) + 20])
            for j, (name, val) in enumerate(s["rows"]):
                cy = y + 10 + rh * j + rh / 2
                if j: d.line([(M + 40, cy - rh / 2), (W - M - 40, cy - rh / 2)], fill=S["bord"], width=2)
                nf = F("Inter-Medium", 40)
                while d.textlength(name, font=nf) > 600 and nf.size > 26: nf = F("Inter-Medium", nf.size - 2)
                d.text((M + 44, cy), name, font=nf, fill=ink, anchor="lm")
                d.text((W - M - 44, cy + 4), val, font=vfont(val, 66), fill=acc, anchor="rm")
            y += rh * len(s["rows"]) + 20
            if s.get("foot"): text_block(d, M, y + 34, s["foot"], F("Inter-Regular", 30), mut, W - 2 * M, 1.4)
        elif kind == "list":
            ft = fit(d, s["title"], 84, W - 2 * M, 2)
            y = text_block(d, M, 260, s["title"], ft, ink, W - 2 * M, 1.05) + 30
            for j, (t1, t2) in enumerate(s["rows"]):
                lines = wrap(d, t2, F("Inter-Regular", 34), W - 2 * M - 210); hh = max(190, 116 + 46 * len(lines))
                d = card(im, [M, y, W - M, y + hh])
                d.rounded_rectangle([M + 32, y + 32, M + 120, y + 120], 24, fill=S["soft"])
                d.text((M + 76, y + 78), str(j + 1), font=FR(52), fill=acc, anchor="mm")
                d.text((M + 152, y + 34), t1, font=F("Inter-SemiBold", 42), fill=ink)
                text_block(d, M + 152, y + 98, t2, F("Inter-Regular", 34), mut, W - 2 * M - 210, 1.35)
                y += hh + 22
            if s.get("foot"): text_block(d, M, y + 14, s["foot"], F("Inter-Regular", 30), mut, W - 2 * M, 1.4)
        elif kind == "swatches":
            ft = fit(d, s["title"], 84, W - 2 * M, 2)
            y = text_block(d, M, 260, s["title"], ft, ink, W - 2 * M, 1.05) + 36
            rh = 120; d = card(im, [M, y, W - M, y + rh * len(s["rows"]) + 20])
            for j, (name, bgc, accc) in enumerate(s["rows"]):
                cy = y + 10 + rh * j + rh / 2
                if j: d.line([(M + 40, cy - rh / 2), (W - M - 40, cy - rh / 2)], fill=S["bord"], width=2)
                d.ellipse([M + 40, cy - 38, M + 116, cy + 38], fill=hx(bgc), outline=S["bord"], width=3); d.ellipse([M + 60, cy - 18, M + 96, cy + 18], fill=hx(accc))
                d.text((M + 150, cy), name, font=FR(52), fill=ink, anchor="lm")
            y += rh * len(s["rows"]) + 20
            if s.get("foot"): text_block(d, M, y + 34, s["foot"], F("Inter-Regular", 30), mut, W - 2 * M, 1.4)
        elif kind == "cta":
            im.alpha_composite(logo(168, 44), (W // 2 - 84, 290)); d = ImageDraw.Draw(im)
            ft = fit(d, s["title"], 76, W - 2 * M, 3)
            y = text_block(d, M, 520, s["title"], ft, ink, W - 2 * M, 1.08, anchor="ma")
            kf = F("Inter-Bold", 104); kw = s["keyword"]; w = d.textlength(kw, font=kf); top = y + 50
            d.rounded_rectangle([W / 2 - w / 2 - 80, top, W / 2 + w / 2 + 80, top + 200], 100, fill=ORANGE)
            d.text((W / 2, top + 102), kw, font=kf, fill=ORANGE_INK, anchor="mm")
            text_block(d, M, top + 250, s.get("sub", ""), F("Inter-Regular", 40), mut, W - 2 * M, 1.4, anchor="ma")
        bb = im.getbbox() or (0, 260, W, 260); top = 240
        dy = max(top - bb[1], int((top + bottom) / 2 - (bb[1] + bb[3]) / 2)) if bb[3] - bb[1] < bottom - top else top - bb[1]
        page.alpha_composite(im, (0, dy)); im = page; d = ImageDraw.Draw(im)
        if kind == "cover" and s.get("keyword"): orange_pill(d, M, H - 300, "Scrie " + s["keyword"] + " în comentarii", F("Inter-SemiBold", 38))
        if kind == "cover" and s.get("swipe"): d.text((W - M, H - 205), s["swipe"], font=F("Inter-SemiBold", 36), fill=acc, anchor="rm")
        p = os.path.join(out_dir, f"{prefix} - slide {i}.png"); im.convert("RGB").save(p, optimize=True); paths.append(p)
    return paths

if __name__ == "__main__":
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    os.makedirs(sys.argv[2], exist_ok=True)
    for p in render(spec, sys.argv[2], sys.argv[3]): print(p)

"""Brand carousel renderer: 1080x1350 slides for @jurnalul.alimentar.

Usage: python3 carousel.py spec.json out_dir prefix
spec = {"slides": [{"kind": "cover"|"stake"|"item"|"recap"|"cta", ...}], "source": "..."}
"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1080, 1350
FD = "/usr/share/fonts/opentype/inter/"
def F(n, s): return ImageFont.truetype(FD + n + ".otf", s)
LIME = (199, 240, 130); INK = (8, 30, 22); WHITE = (255, 255, 255); MUTED = (170, 196, 182)
HANDLE = "@jurnalul.alimentar"

yy, xx = np.mgrid[0:H, 0:W]
r = np.sqrt(((xx - W * 0.5) / W) ** 2 + ((yy - H * 0.4) / H) ** 2)
k = np.clip(r / 0.8, 0, 1)[..., None]
BG = Image.fromarray((np.array([22, 78, 56]) * (1 - k) + np.array([5, 22, 16]) * k).astype(np.uint8), "RGB")
glow = Image.new("RGBA", (900, 900), (0, 0, 0, 0))
ImageDraw.Draw(glow).ellipse([200, 200, 700, 700], fill=(163, 230, 53, 70))
glow = glow.filter(ImageFilter.GaussianBlur(120))
logo = Image.open(os.path.join(HERE, "logo.png")).convert("RGBA").resize((64, 64), Image.LANCZOS)
m = Image.new("L", (64, 64), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, 63, 63], 16, fill=255); logo.putalpha(m)

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

def base(i, n, glow_xy=(540, 520)):
    im = BG.convert("RGBA"); im.alpha_composite(glow, (glow_xy[0] - 450, glow_xy[1] - 450))
    d = ImageDraw.Draw(im)
    im.alpha_composite(logo, (120, H - 150))
    d.text((200, H - 118), HANDLE, font=F("Inter-SemiBold", 32), fill=MUTED, anchor="lm")
    d.text((W - 120, H - 118), f"{i}/{n}", font=F("Inter-SemiBold", 32), fill=MUTED, anchor="rm")
    return im, d

def text_block(d, x, y, text, font, fill, maxw, lh=1.1):
    for line in wrap(d, text, font, maxw):
        d.text((x, y), line, font=font, fill=fill); y += font.size * lh
    return y

def pill(d, x, y, text, font, fg=INK, bg=LIME, pad=(30, 16)):
    w = d.textlength(text, font=font)
    d.rounded_rectangle([x, y, x + w + 2 * pad[0], y + font.size + 2 * pad[1]], (font.size + 2 * pad[1]) / 2, fill=bg)
    d.text((x + pad[0], y + pad[1] + font.size / 2 + 2), text, font=font, fill=fg, anchor="lm")
    return y + font.size + 2 * pad[1]

def render(spec, out_dir, prefix):
    slides = spec["slides"]; n = len(slides); paths = []
    for i, s in enumerate(slides, 1):
        im, d = base(i, n)
        kind = s["kind"]
        if kind == "cover":
            y = 300
            if s.get("eyebrow"): y = pill(d, 120, y, s["eyebrow"], F("Inter-Bold", 34)) + 50
            y = text_block(d, 120, y, s["title"], F("InterDisplay-Black", 118), WHITE, 840, 1.04)
            if s.get("accent"): y = text_block(d, 120, y, s["accent"], F("InterDisplay-Black", 118), LIME, 840, 1.04)
            text_block(d, 120, y + 40, s.get("sub", ""), F("Inter-Medium", 42), MUTED, 840, 1.3)
            if s.get("swipe"): d.text((W - 120, H - 230), s["swipe"], font=F("Inter-Bold", 38), fill=LIME, anchor="rm")
        elif kind == "stake":
            y = text_block(d, 120, 380, s["title"], F("InterDisplay-Bold", 92), WHITE, 840, 1.1)
            text_block(d, 120, y + 40, s.get("sub", ""), F("Inter-Medium", 44), MUTED, 840, 1.35)
        elif kind == "item":
            d.text((120, 300), s.get("rank", ""), font=F("Inter-Bold", 40), fill=LIME)
            big = F("InterDisplay-Black", 300)
            d.text((104, 360), s["value"], font=big, fill=LIME)
            vw = d.textlength(s["value"], font=big)
            d.text((120 + vw + 10, 610), s.get("unit", ""), font=F("InterDisplay-Bold", 64), fill=WHITE)
            y = text_block(d, 120, 760, s["name"], F("InterDisplay-Bold", 76), WHITE, 840, 1.1)
            text_block(d, 120, y + 24, s.get("note", ""), F("Inter-Medium", 38), MUTED, 840, 1.35)
        elif kind == "recap":
            d.text((120, 260), s["title"], font=F("InterDisplay-Black", 76), fill=WHITE)
            y = 400
            for name, val in s["rows"]:
                d.rounded_rectangle([120, y, W - 120, y + 108], 30, fill=(255, 255, 255, 26) if False else (34, 74, 58))
                d.text((160, y + 54), name, font=F("Inter-SemiBold", 40), fill=WHITE, anchor="lm")
                d.text((W - 160, y + 54), val, font=F("InterDisplay-Bold", 46), fill=LIME, anchor="rm")
                y += 128
            if s.get("foot"): text_block(d, 120, y + 20, s["foot"], F("Inter-Medium", 32), MUTED, 840, 1.35)
        elif kind == "cta":
            im.alpha_composite(Image.open(os.path.join(HERE, "logo.png")).convert("RGBA").resize((200, 200)), (440, 230))
            y = text_block(d, 120, 500, s["title"], F("InterDisplay-Bold", 64), WHITE, 840, 1.15)
            kw = F("InterDisplay-Black", 150); w = d.textlength(s["keyword"], font=kw)
            d.rounded_rectangle([540 - w / 2 - 70, y + 40, 540 + w / 2 + 70, y + 250], 64, fill=LIME)
            d.text((540, y + 148), s["keyword"], font=kw, fill=INK, anchor="mm")
            text_block(d, 120, y + 300, s.get("sub", ""), F("Inter-Medium", 42), MUTED, 840, 1.35)
        p = os.path.join(out_dir, f"{prefix} - slide {i}.png"); im.convert("RGB").save(p, optimize=True); paths.append(p)
    return paths

if __name__ == "__main__":
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    os.makedirs(sys.argv[2], exist_ok=True)
    for p in render(spec, sys.argv[2], sys.argv[3]): print(p)

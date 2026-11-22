"""Brand carousel renderer: 1080x1350 slides for @jurnalul.alimentar.

Usage: python3 carousel.py spec.json out_dir prefix
spec = {"slides": [{"kind": "cover"|"stake"|"item"|"recap"|"cta", ...}], "source": "..."}
"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1080, 1350
FD = "/usr/share/fonts/opentype/inter/"
def F(n, s): return ImageFont.truetype(FD + n + ".otf", s)
LIME = (199, 240, 130); INK = (8, 30, 22); WHITE = (255, 255, 255); MUTED = (170, 196, 182)
ACCT = LIME; ROW = (34, 74, 58)

HANDLE = "@jurnalul.alimentar"

yy, xx = np.mgrid[0:H, 0:W]
r = np.sqrt(((xx - W * 0.5) / W) ** 2 + ((yy - H * 0.4) / H) ** 2)
k = np.clip(r / 0.8, 0, 1)[..., None]
BG = Image.fromarray((np.array([22, 78, 56]) * (1 - k) + np.array([5, 22, 16]) * k).astype(np.uint8), "RGB")
glow = Image.new("RGBA", (900, 900), (0, 0, 0, 0))
ImageDraw.Draw(glow).ellipse([200, 200, 700, 700], fill=(163, 230, 53, 70))
glow = glow.filter(ImageFilter.GaussianBlur(120))
STYLES = {   # bg centre, bg edge, glow, text, accent text, muted, row, pill bg, pill text
    "dark":  ((22, 78, 56), (5, 22, 16), (163, 230, 53, 70), (255, 255, 255), (199, 240, 130), (170, 196, 182), (34, 74, 58), (199, 240, 130), (8, 30, 22)),
    "light": ((246, 248, 243), (226, 233, 224), (199, 240, 130, 110), (32, 51, 42), (37, 94, 70), (110, 128, 118), (255, 255, 255), (199, 240, 130), (8, 30, 22)),
    "lime":  ((214, 246, 160), (176, 228, 96), (255, 255, 255, 90), (8, 30, 22), (37, 94, 70), (44, 82, 62), (240, 252, 222), (8, 30, 22), (199, 240, 130)),
}
def set_style(name):
    global BG, glow, WHITE, ACCT, MUTED, ROW, LIME, INK
    c0, c1, g, WHITE, ACCT, MUTED, ROW, LIME, INK = STYLES[name]
    BG = Image.fromarray((np.array(c0) * (1 - k) + np.array(c1) * k).astype(np.uint8), "RGB")
    glow = Image.new("RGBA", (900, 900), g[:3] + (0,)); ImageDraw.Draw(glow).ellipse([200, 200, 700, 700], fill=g)
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
    if n > 1: d.text((W - 120, H - 118), f"{i}/{n}", font=F("Inter-SemiBold", 32), fill=MUTED, anchor="rm")
    return im, d

def text_block(d, x, y, text, font, fill, maxw, lh=1.1):
    for line in wrap(d, text, font, maxw):
        d.text((x, y), line, font=font, fill=fill); y += font.size * lh
    return y

def pill(d, x, y, text, font, fg=None, bg=None, pad=(30, 16)):
    fg = fg or INK; bg = bg or LIME
    w = d.textlength(text, font=font)
    d.rounded_rectangle([x, y, x + w + 2 * pad[0], y + font.size + 2 * pad[1]], (font.size + 2 * pad[1]) / 2, fill=bg)
    d.text((x + pad[0], y + pad[1] + font.size / 2 + 2), text, font=font, fill=fg, anchor="lm")
    return y + font.size + 2 * pad[1]

def render(spec, out_dir, prefix):
    set_style(spec.get("style", "dark"))
    slides = spec["slides"]; n = len(slides); paths = []
    for i, s in enumerate(slides, 1):
        im, d = base(i, n)
        kind = s["kind"]
        if kind == "cover":
            y = 300
            if s.get("eyebrow"): y = pill(d, 120, y, s["eyebrow"], F("Inter-Bold", 34)) + 50
            y = text_block(d, 120, y, s["title"], F("InterDisplay-Black", 118), WHITE, 840, 1.04)
            if s.get("accent"): y = text_block(d, 120, y, s["accent"], F("InterDisplay-Black", 118), ACCT, 840, 1.04)
            text_block(d, 120, y + 40, s.get("sub", ""), F("Inter-Medium", 42), MUTED, 840, 1.3)
            if s.get("swipe"): d.text((W - 120, H - 230), s["swipe"], font=F("Inter-Bold", 38), fill=ACCT, anchor="rm")
            if s.get("image"):
                pic = Image.open(os.path.join(HERE, s["image"])).convert("RGBA"); mw, mh = s.get("image_box", [840, 420])
                pic.thumbnail((mw, mh), Image.LANCZOS)
                if s.get("image_round"):
                    mk = Image.new("L", pic.size, 0); ImageDraw.Draw(mk).rounded_rectangle([0, 0, pic.width - 1, pic.height - 1], 40, fill=255)
                    pic.putalpha(ImageChops.multiply(pic.getchannel("A"), mk))
                im.alpha_composite(pic, ((W - pic.width) // 2, int(s.get("image_y", H - 200 - pic.height - (150 if s.get("keyword") else 0)))))
                d = ImageDraw.Draw(im)
            if s.get("keyword"):
                kw = F("Inter-Bold", 40); txt = "Scrie " + s["keyword"] + " în comentarii"; w = d.textlength(txt, font=kw)
                d.rounded_rectangle([120, H - 300, 120 + w + 80, H - 210], 45, fill=LIME); d.text((160, H - 255), txt, font=kw, fill=INK, anchor="lm")
        elif kind == "swatches":
            d.text((120, 250), s["title"], font=F("InterDisplay-Black", 76), fill=WHITE)
            y = 370
            for name, bgc, acc in s["rows"]:
                h2 = lambda x: tuple(int(x[i:i + 2], 16) for i in (1, 3, 5))
                d.rounded_rectangle([120, y, W - 120, y + 118], 34, fill=ROW)
                d.ellipse([150, y + 19, 230, y + 99], fill=h2(bgc), outline=(255, 255, 255), width=3)
                d.ellipse([172, y + 41, 208, y + 77], fill=h2(acc))
                d.text((270, y + 59), name, font=F("InterDisplay-Bold", 48), fill=WHITE, anchor="lm")
                y += 130
            if s.get("foot"): text_block(d, 120, y + 10, s["foot"], F("Inter-Medium", 30), MUTED, 840, 1.3)
        elif kind == "list":
            d.text((120, 250), s["title"], font=F("InterDisplay-Black", 72), fill=WHITE)
            y = 380
            for j, (t1, t2) in enumerate(s["rows"]):
                d.rounded_rectangle([120, y, W - 120, y + 200], 34, fill=ROW)
                d.ellipse([150, y + 40, 220, y + 110], fill=LIME); d.text((185, y + 76), str(j + 1), font=F("Inter-Bold", 38), fill=INK, anchor="mm")
                d.text((250, y + 40), t1, font=F("InterDisplay-Bold", 44), fill=WHITE)
                text_block(d, 250, y + 100, t2, F("Inter-Medium", 32), MUTED, 680, 1.3)
                y += 224
            if s.get("foot"): text_block(d, 120, y + 6, s["foot"], F("Inter-Medium", 30), MUTED, 840, 1.35)
        elif kind == "stake":
            y = text_block(d, 120, 380, s["title"], F("InterDisplay-Bold", 92), WHITE, 840, 1.1)
            text_block(d, 120, y + 40, s.get("sub", ""), F("Inter-Medium", 44), MUTED, 840, 1.35)
        elif kind == "item":
            d.text((120, 300), s.get("rank", ""), font=F("Inter-Bold", 40), fill=ACCT)
            big = F("InterDisplay-Black", 300)
            d.text((104, 360), s["value"], font=big, fill=ACCT)
            vw = d.textlength(s["value"], font=big)
            d.text((120 + vw + 10, 610), s.get("unit", ""), font=F("InterDisplay-Bold", 64), fill=WHITE)
            y = text_block(d, 120, 760, s["name"], F("InterDisplay-Bold", 76), WHITE, 840, 1.1)
            text_block(d, 120, y + 24, s.get("note", ""), F("Inter-Medium", 38), MUTED, 840, 1.35)
        elif kind == "recap":
            d.text((120, 260), s["title"], font=F("InterDisplay-Black", 76), fill=WHITE)
            y = 400
            for name, val in s["rows"]:
                d.rounded_rectangle([120, y, W - 120, y + 108], 30, fill=ROW)
                d.text((160, y + 54), name, font=F("Inter-SemiBold", 40), fill=WHITE, anchor="lm")
                d.text((W - 160, y + 54), val, font=F("InterDisplay-Bold", 46), fill=ACCT, anchor="rm")
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

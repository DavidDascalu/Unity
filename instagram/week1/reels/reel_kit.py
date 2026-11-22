"""Short 9:16 reels in the style of the 'Alimentație cu ritm' spot (same engine, same rhythm line).

    python3 reel_kit.py r25 frames 1,4,8      -> stills
    python3 reel_kit.py r25 seg i n           -> one parallel segment (60 fps, 1080x1920)
    python3 reel_kit.py r25 audio             -> voice + SFX + music mix
Scene cuts follow the phrase starts of the ElevenLabs voiceover.
"""
import math, os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
SPOT = os.path.join(HERE, "..", "..", "spot")
sys.path.insert(0, SPOT)
import render as R
import audio as AU
from render import (W, H, k01, eo, eio, eback, lerp, lerp2, paste, fade, scaled, fast_blur, place3d, glow_line, poly_partial,
                    text_img, reveal, AS, LOGO, GLOW_G, GLOW_W, VIG, GRAIN, SCENE, TEXT, MUTED, ACC, ACC_HI, PROT, CARB, FAT, INK, F)

VO = 0.55
ENGINE = os.path.join(HERE, "..", "..", "engine")

def phrase_starts(mp3):
    x = AU.load_mp3(mp3); sr = AU.SR
    out = subprocess.run(["ffmpeg", "-hide_banner", "-i", mp3, "-af", "silencedetect=noise=-38dB:d=0.25", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    import re
    ends = [float(v) for v in re.findall(r"silence_end: ([0-9.]+)", out)]
    starts = [AU.onset(x)] + [e for e in ends if e < len(x) / sr - 0.2]
    return [s + VO for s in starts[:5]], len(x) / sr + VO

REELS = {
    "r25": {"mp3": "r25_plan.mp3", "kw": "PLAN", "subs": ["Nu mai întreba ce mănânci mâine.", "Completezi profilul o dată.",
            "Primești un plan pe 1, 7 sau 30 de zile.", "Plus lista de cumpărături.", "Scrie PLAN în comentarii!"]},
    "r27": {"mp3": "r27_scan.mp3", "kw": "ETICHETA", "subs": ["Ai o etichetă în mână?", "O scanezi.",
            "Valorile intră singure în jurnal.", "Poza rămâne în browser.", "Scrie ETICHETA în comentarii!"]},
    "r29": {"mp3": "r29_trend.mp3", "kw": "JURNAL", "subs": ["Te-ai cântărit azi și te-ai speriat?", "Variațiile zilnice sunt normale.",
            "Urmărește tendința, nu o singură cifră.", "Un pas odată.", "Scrie JURNAL în comentarii!"]},
}
KEY = sys.argv[1]; CFG = REELS[KEY]
P, VEND = phrase_starts(os.path.join(HERE, CFG["mp3"]))
DUR = round(VEND + 1.8, 2)
CUTS = [0.0] + [p - 0.12 for p in P[1:]] + [DUR]

# ---------- shared bits ----------
def app_screen(path):
    """A real 1170x1992 app capture fitted into the 1179x2556 phone screen."""
    cap = Image.open(path).convert("RGB").resize((AS.SW, round(1992 * AS.SW / 1170)))
    scr = Image.new("RGB", (AS.SW, AS.SH), SCENE); scr.paste(cap, (0, 150)); d = ImageDraw.Draw(scr); AS.status_bar(d)
    return scr

def step_title(c, t, a, b, num, txt):
    if num:
        k = eback(k01(t, a, a + 0.35)); al = (1 - eio(k01(t, b, b + 0.3)))
        chip = Image.new("RGBA", (110, 110), (0, 0, 0, 0)); ImageDraw.Draw(chip).ellipse([0, 0, 109, 109], fill=ACC + (255,))
        ImageDraw.Draw(chip).text((55, 57), str(num), font=F("dk", 70), fill=INK, anchor="mm")
        if al > 0.02: paste(c, fade(scaled(chip, max(0.05, 0.5 + 0.5 * k)), al), 70, 300)
        reveal(c, txt, F("db", 78), 640, 300, t, a + 0.05, b, fill=TEXT)
    else:
        reveal(c, txt, F("db", 84), 540, 300, t, a + 0.05, b)

def subtitles(c, t):
    for i, txt in enumerate(CFG["subs"]):
        a = P[i]; b = (P[i + 1] - 0.15) if i < 4 else VEND
        if a - 0.05 <= t < b + 0.25:
            k = eo(k01(t, a - 0.05, a + 0.2)) * (1 - eio(k01(t, b, b + 0.25)))
            im = text_img(txt, F("b", 48), TEXT)
            pad = Image.new("RGBA", (im.width + 40, im.height + 8), (0, 0, 0, 0))
            ImageDraw.Draw(pad).rounded_rectangle([0, 0, pad.width - 1, pad.height - 1], 36, fill=(6, 9, 7, 170)); pad.alpha_composite(im, (20, 4))
            if pad.width > 1000: pad = scaled(pad, 1000 / pad.width)
            paste(c, fade(pad, k), W / 2 - pad.width / 2, 1738 + (1 - k) * 12)

def opener_line(c, t, y=1120):
    if t < 0.2:
        k = eio(t / 0.2); half = lerp(30, 480, k); glow_line(c, [(540 - half, y), (540 + half, y)], width=lerp(4, 24, k), inten=lerp(0.4, 1.3, k)); return
    head = lerp(170, 910, eio(k01(t, 0.22, 1.2))); flash = max(0, 1 - (t - 0.2) / 0.25)
    if flash > 0: paste(c, fade(scaled(GLOW_G, 1.3), flash), 540 - 780, y - 780)
    glow_line(c, [(170, y), (head, y)], width=11, head=(head, y) if head < 905 else None)

def cta(c, t, a, chip=None):
    k = eo(k01(t, a, a + 0.6))
    lg = scaled(LOGO, 0.22); paste(c, fade(lg, k), 540 - lg.width / 2, 470)
    reveal(c, "Scrie în comentarii", F("s", 52), 540, 820, t, a + 0.15)
    kp = k01(t, a + 0.35, a + 0.8)
    if kp > 0:
        kw = CFG["kw"]; fnt = F("dk", 150); w = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textlength(kw, font=fnt)
        pim = Image.new("RGBA", (int(w + 140), 230), (0, 0, 0, 0)); ImageDraw.Draw(pim).rounded_rectangle([0, 0, pim.width - 1, 229], 64, fill=ACC + (255,))
        ImageDraw.Draw(pim).text((pim.width / 2, 118), kw, font=fnt, fill=INK, anchor="mm")
        pulse = 1 + 0.03 * math.sin((t - a) * 6)
        s = (0.55 + 0.45 * eback(kp, 1.8)) * pulse * min(1, 900 / pim.width)
        paste(c, scaled(pim, s), 540 - pim.width * s / 2, 1000 - pim.height * s / 2 + 40)
    if chip: reveal(c, chip, F("m", 40), 540, 1220, t, a + 0.7, fill=MUTED)
    y = 1150; half = lerp(0, 330, eo(k01(t, a + 0.2, a + 0.9))); glow_line(c, [(540 - half, 1380), (540 + half, 1380)], width=8)

# ---------- reel 25: Plan Premium ----------
MORE = app_screen(os.path.join(ENGINE, "ov", "more.png"))
def r25(c, t):
    if t < CUTS[1] + 0.3:
        a = 1 - eio(k01(t, CUTS[1] - 0.2, CUTS[1] + 0.3))
        reveal(c, "Ce mănânci", F("dk", 130), 540, 700, t, 0.25, CUTS[1] - 0.1)
        reveal(c, "mâine?", F("dk", 150), 540, 860, t, 0.55, CUTS[1] - 0.1, fill=ACC_HI)
        ks = eio(k01(t, 1.25, 1.55))
        if ks > 0: ImageDraw.Draw(c).line([(150, 1010), (lerp(150, 930, ks), 985)], fill=(255, 92, 92, int(255 * a)), width=20)
        opener_line(c, t)
    if CUTS[1] <= t < CUTS[2] + 0.3:
        a0 = CUTS[1]; k = eo(k01(t, a0, a0 + 0.8)); out = eio(k01(t, CUTS[2] - 0.1, CUTS[2] + 0.3))
        step_title(c, t, a0, CUTS[2] - 0.1, 1, "Profilul tău")
        place3d(c, R.phone_img(MORE), 540, lerp(2300, 1080, k) + 8 * math.sin(t), 0.5, ry=lerp(-16, -6, k), rx=lerp(14, 4, k), alpha=1 - out, blur=out * 12, shadow=0.8)
    if CUTS[2] <= t < CUTS[3] + 0.3:
        a0 = CUTS[2]; out = eio(k01(t, CUTS[3] - 0.1, CUTS[3] + 0.3)); lt = t - a0
        step_title(c, t, a0, CUTS[3] - 0.1, 2, "Planul tău")
        segs = ["1 zi", "7 zile", "30 zile"]; sw, sh = 280, 120
        pos = 0 if lt < 0.9 else (lerp(0, 1, eio(k01(lt, 0.9, 1.15))) if lt < 1.5 else lerp(1, 2, eio(k01(lt, 1.5, 1.75))))
        bar = Image.new("RGBA", (sw * 3 + 20, sh + 20), (0, 0, 0, 0)); bd = ImageDraw.Draw(bar)
        bd.rounded_rectangle([0, 0, bar.width - 1, bar.height - 1], 70, fill=(34, 41, 36, 255))
        hx = 10 + pos * sw; bd.rounded_rectangle([hx, 10, hx + sw, 10 + sh], 60, fill=ACC + (255,))
        for i, s_ in enumerate(segs): bd.text((10 + i * sw + sw / 2, 10 + sh / 2), s_, font=F("b", 46), fill=INK if abs(pos - i) < 0.5 else TEXT, anchor="mm")
        paste(c, fade(bar, eo(k01(lt, 0, 0.4)) * (1 - out)), 540 - bar.width / 2, 520)
        cell, gap = 108, 14; gx = 540 - (6 * cell + 5 * gap) / 2
        for i in range(30):
            kk = eback(k01(lt, 1.9 + i * 0.03, 2.2 + i * 0.03), 2.0)
            if kk <= 0: continue
            tile = Image.new("RGBA", (cell, cell), (0, 0, 0, 0)); td = ImageDraw.Draw(tile)
            td.rounded_rectangle([0, 0, cell - 1, cell - 1], 26, fill=AS.CARD + (255,)); td.text((16, 10), str(i + 1), font=F("b", 32), fill=TEXT)
            for j, col in enumerate([PROT, CARB, FAT]): td.ellipse([18 + j * 28, cell - 34, 38 + j * 28, cell - 14], fill=col)
            ss = max(0.05, kk); tile = scaled(tile, ss)
            paste(c, fade(tile, 1 - out), gx + (i % 6) * (cell + gap) + cell / 2 - tile.width / 2, 760 + (i // 6) * (cell + gap) + cell / 2 - tile.height / 2)
    if CUTS[3] <= t < CUTS[4] + 0.3:
        a0 = CUTS[3]; out = eio(k01(t, CUTS[4] - 0.1, CUTS[4] + 0.3)); lt = t - a0
        step_title(c, t, a0, CUTS[4] - 0.1, 3, "Cumpărături")
        card = Image.new("RGBA", (760, 600), (0, 0, 0, 0)); d = ImageDraw.Draw(card)
        d.rounded_rectangle([0, 0, 759, 599], 56, fill=AS.CARD + (255,))
        for i, it in enumerate(["Legume", "Ouă", "Iaurt", "Ovăz"]):
            y = 60 + i * 128; done = lt > 0.35 + i * 0.22
            d.rounded_rectangle([50, y, 130, y + 80], 22, fill=(AS.ACCENT + (255,)) if done else (48, 58, 51, 255))
            if done: d.line([(68, y + 42), (86, y + 60), (114, y + 22)], fill=INK, width=9)
            d.text((170, y + 40), it, font=F("db", 54), fill=MUTED if done else TEXT, anchor="lm")
        place3d(c, card, 540, lerp(1500, 1000, eo(k01(lt, 0, 0.6))), 1.0, rx=lerp(20, 4, eo(k01(lt, 0, 0.6))), ry=-4, alpha=1 - out, shadow=0.6)
    if t >= CUTS[4]: cta(c, t, CUTS[4], chip="Premium · de la 25 lei/lună")

# ---------- reel 27: Scanează eticheta ----------
LABEL = Image.open(os.path.join(SPOT, "assets", "label.png")).convert("RGBA")
def r27(c, t):
    if t < CUTS[1] + 0.3:
        out = eio(k01(t, CUTS[1] - 0.2, CUTS[1] + 0.3))
        reveal(c, "Ai o etichetă", F("dk", 110), 540, 330, t, 0.25, CUTS[1] - 0.1)
        reveal(c, "în mână?", F("dk", 130), 540, 470, t, 0.5, CUTS[1] - 0.1, fill=ACC_HI)
        k = eo(k01(t, 0.1, 0.9))
        place3d(c, LABEL, 540, lerp(1900, 1150, k) + 10 * math.sin(t * 2), 0.62, rx=lerp(40, 14, k), rz=lerp(-12, -4, k), alpha=1 - out, shadow=0.7)
        opener_line(c, t, y=1640)
    if CUTS[1] <= t < CUTS[3] + 0.3:
        a0 = CUTS[1]; k = eo(k01(t, a0, a0 + 0.6)); out = eio(k01(t, CUTS[3] - 0.1, CUTS[3] + 0.3))
        ext = 0 if t < CUTS[2] else min(4, int((t - CUTS[2]) / 0.35) + 1)
        added = t >= CUTS[2] + 1.9
        scr = AS.scan_screen(extracted=ext, added=added)
        s = 0.48; py = lerp(2300, 1000, k)
        place3d(c, R.phone_img(scr), 540, py, s, ry=lerp(-12, -3, k), alpha=1 - out, blur=out * 12, shadow=0.8)
        sh = abs(t - (a0 + 0.55))
        if sh < 0.15: c.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(190 * (1 - sh / 0.15)))))
        la, lb = a0 + 0.6, CUTS[2] + 1.4
        if la <= t <= lb and out < 0.5:
            u = math.sin((t - la) / (lb - la) * math.pi * 3 - math.pi / 2) * 0.5 + 0.5
            y = R.scr2frame(0, lerp(560, 1390, u), 540, py, s)[1]
            glow_line(c, [(R.scr2frame(130, 0, 540, py, s)[0], y), (R.scr2frame(1049, 0, 540, py, s)[0], y)], width=8)
        bx, by = R.scr2frame(590, 2335, 540, py, s); kt = k01(t, CUTS[2] + 1.75, CUTS[2] + 2.2)
        if 0 < kt < 1:
            r_ = lerp(20, 110, eo(kt)); ImageDraw.Draw(c).ellipse([bx - r_, by - r_, bx + r_, by + r_], outline=(255, 255, 255, int(220 * (1 - kt))), width=6)
        if t >= CUTS[2]:
            dis = R.DISCLAIMER; paste(c, fade(dis, eo(k01(t, CUTS[2], CUTS[2] + 0.4)) * (1 - out)), W / 2 - dis.width / 2, 1855)
    if CUTS[3] <= t < CUTS[4] + 0.3:
        a0 = CUTS[3]; out = eio(k01(t, CUTS[4] - 0.1, CUTS[4] + 0.3)); k = eback(k01(t, a0, a0 + 0.6), 1.2)
        card = Image.new("RGBA", (860, 520), (0, 0, 0, 0)); d = ImageDraw.Draw(card)
        d.rounded_rectangle([0, 0, 859, 519], 64, fill=(255, 255, 255, 22), outline=(255, 255, 255, 60), width=3)
        d.rounded_rectangle([70, 80, 170, 180], 26, outline=ACC + (255,), width=8); d.arc([90, 30, 150, 110], 180, 360, fill=ACC + (255,), width=8)
        d.text((220, 96), "Confidențialitate", font=F("b", 38), fill=PROT)
        d.text((70, 240), "Fotografia se", font=F("db", 74), fill=TEXT); d.text((70, 330), "procesează în browser.", font=F("db", 66), fill=ACC_HI)
        place3d(c, card, 540, 980, 1.0 * min(1, max(0.05, k)), ry=lerp(-20, -6, min(1, k)), rx=6, alpha=min(1, k) * (1 - out), shadow=0.5)
    if t >= CUTS[4]: cta(c, t, CUTS[4])

# ---------- reel 29: tendința ----------
rng = np.random.default_rng(29)
DAYS = 21
DAILY = 0.55 * np.sin(np.linspace(0, 2.6, DAYS)) * 0 + rng.normal(0, 1, DAYS) * 0.9 - np.linspace(0, 1.4, DAYS)
TREND = np.convolve(np.pad(DAILY, 3, mode="edge"), np.ones(7) / 7, "valid")
def chart_pts(vals, x0=140, x1=940, y0=780, y1=1320):
    lo, hi = DAILY.min() - 0.3, DAILY.max() + 0.3
    return [(lerp(x0, x1, i / (len(vals) - 1)), lerp(y1, y0, (v - lo) / (hi - lo))) for i, v in enumerate(vals)]
def r29(c, t):
    if t < CUTS[1] + 0.3:
        reveal(c, "Te-ai cântărit", F("dk", 110), 540, 640, t, 0.25, CUTS[1] - 0.1)
        reveal(c, "azi?", F("dk", 150), 540, 790, t, 0.55, CUTS[1] - 0.1, fill=ACC_HI)
        opener_line(c, t)
    if CUTS[1] <= t < CUTS[3] + 0.3:
        a0 = CUTS[1]; out = eio(k01(t, CUTS[3] - 0.1, CUTS[3] + 0.3))
        d = ImageDraw.Draw(c)
        d.line([(140, 1360), (940, 1360)], fill=(48, 58, 51, int(255 * (1 - out))), width=3)
        pts = chart_pts(DAILY); kd = eio(k01(t, a0 + 0.1, a0 + 1.6))
        n = max(2, int(kd * DAYS))
        grey = t >= CUTS[2]
        col = (120, 132, 124) if grey else TEXT
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
        ld.line(pts[:n], fill=col + (int(255 * (1 - out) * (0.7 if grey else 1)),), width=4)
        for x, y in pts[:n]: ld.ellipse([x - 9, y - 9, x + 9, y + 9], fill=col + (int(255 * (1 - out)),))
        c.alpha_composite(lay)
        reveal(c, "zi cu zi", F("m", 40), 260, 1390, t, a0 + 0.2, CUTS[3] - 0.1, fill=MUTED)
        if t >= CUTS[2]:
            kt = eio(k01(t, CUTS[2] + 0.1, CUTS[2] + 1.6))
            tp = chart_pts(TREND)
            dense = [lerp2(tp[int(i)], tp[min(len(tp) - 1, int(i) + 1)], i - int(i)) for i in np.linspace(0, len(tp) - 1.001, 120)]
            part = poly_partial(dense, kt); glow_line(c, part, width=12, inten=1 - out, head=part[-1] if kt < 1 else None)
            reveal(c, "tendința", F("b", 44), 820, 1390, t, CUTS[2] + 0.4, CUTS[3] - 0.1, fill=ACC_HI)
        step_title(c, t, a0, CUTS[3] - 0.1, 0, "Fără cifre care sperie.")
    if CUTS[3] <= t < CUTS[4] + 0.3:
        a0 = CUTS[3]; out = eio(k01(t, CUTS[4] - 0.1, CUTS[4] + 0.3)); k = eback(k01(t, a0, a0 + 0.5), 1.2)
        place3d(c, R.GLASS, 540, 980, 1.05 * max(0.05, min(1, k)), ry=-10, rx=6, alpha=min(1, k) * (1 - out), shadow=0.5)
    if t >= CUTS[4]: cta(c, t, CUTS[4])

SCENE_FN = {"r25": r25, "r27": r27, "r29": r29}[KEY]

def frame(t):
    c = Image.new("RGBA", (W, H), SCENE + (255,))
    g = scaled(GLOW_W, 1.15); paste(c, fade(g, 0.75 + 0.25 * math.sin(t * 2 * math.pi / 4)), 540 - g.width / 2, 860 - g.height / 2)
    SCENE_FN(c, t)
    dx = 10 * math.sin(t * 0.7) + 6 * math.sin(t * 1.9); dy = 8 * math.cos(t * 0.55); rot = 0.35 * math.sin(t * 0.45); z = 1 + 0.015 * math.sin(t * 0.8)
    for hit, amp in [(0.2, 14), (CUTS[4] + 0.4, 8)]:
        if 0 <= t - hit < 0.35:
            e = (1 - (t - hit) / 0.35) ** 2; dx += amp * e * math.sin((t - hit) * 90); dy += amp * e * math.cos((t - hit) * 77)
    for cut in CUTS[1:5]:                               # gentle push-in on each phrase
        z *= 1 + 0.035 * math.sin(math.pi * k01(t, cut - 0.25, cut + 0.35))
    cs, sn = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    a, b, d_, e = cs / z, sn / z, -sn / z, cs / z; cx, cy = W / 2 + dx, H / 2 + dy
    c = c.transform((W, H), Image.AFFINE, (a, b, 540 - a * cx - b * cy, d_, e, 960 - d_ * cx - e * cy), Image.BILINEAR, fillcolor=SCENE + (255,))
    subtitles(c, t)
    c.alpha_composite(VIG); c.alpha_composite(GRAIN[int(t * 60) % 8])
    if t < 0.05: c = Image.blend(Image.new("RGBA", (W, H), (0, 0, 0, 255)), c, t / 0.05)
    if t > DUR - 0.4: c = Image.blend(c, Image.new("RGBA", (W, H), (0, 0, 0, 255)), k01(t, DUR - 0.4, DUR))
    return c.convert("RGB")

def build_audio():
    AU.DUR = DUR; AU.N = int(AU.SR * DUR); N = AU.N
    b = np.zeros((N, 2))
    AU.place(b, AU.whoosh(0.2, 1.4, rise=True), 0.0, 0.5); AU.place(b, AU.soft_impact(), 0.2, 0.6); AU.place(b, AU.sub_hit(), 0.2, 0.8)
    AU.place(b, AU.shards(), 0.2, 0.15); AU.place(b, AU.whoosh(1.0, 0.8), 0.25, 0.2)
    for cut in CUTS[1:5]: AU.place(b, AU.whoosh(0.5, 1.1), cut - 0.3, 0.35)
    AU.place(b, AU.soft_impact(), CUTS[4] + 0.4, 0.5); AU.place(b, AU.sub_hit(1.4), CUTS[4] + 0.4, 0.7); AU.place(b, AU.success_chime(), CUTS[4] + 0.5, 0.12)
    if KEY == "r25":
        for i in range(30): AU.place(b, AU.tick(1900 + i * 30, 0.025), CUTS[2] + 1.9 + i * 0.03, 0.08)
        for i in range(4): AU.place(b, AU.key_click(), CUTS[3] + 0.35 + i * 0.22, 0.3)
    if KEY == "r27":
        AU.place(b, AU.shutter(), CUTS[1] + 0.55, 0.45); AU.place(b, AU.scanner_beep(), CUTS[1] + 0.6, 0.15)
        AU.place(b, AU.laser_hum(CUTS[2] + 1.4 - CUTS[1] - 0.6), CUTS[1] + 0.6, 0.1)
        for i in range(4): AU.place(b, AU.tick(2600), CUTS[2] + i * 0.35, 0.25)
        AU.place(b, AU.key_click(), CUTS[2] + 1.75, 0.5); AU.place(b, AU.success_chime(), CUTS[2] + 1.9, 0.2)
    if KEY == "r29":
        for i in range(DAYS): AU.place(b, AU.tick(2000 + (i % 5) * 120, 0.02), CUTS[1] + 0.1 + i * 1.5 / DAYS, 0.08)
        AU.place(b, AU.ring_tone(1.5), CUTS[2] + 0.1, 0.05)
    m = AU.music()
    v = np.zeros((N, 2)); x = AU.load_mp3(os.path.join(HERE, CFG["mp3"])); AU.place(v, x, VO, 1.0)
    vel = np.abs(v[:, 0]); kk = np.ones(int(0.12 * AU.SR)) / int(0.12 * AU.SR); duck = 1 - 0.5 * np.clip(np.convolve(vel, kk, "same") * 12, 0, 1)
    mix = (v * 0.95 + np.tanh(b * 1.2) * 0.75 * (0.6 + 0.4 * duck[:, None]) + m * 1.2 * duck[:, None]) * 0.7
    raw = os.path.join(HERE, f"{KEY}_mix_raw.wav"); AU.write(raw, mix)
    out = os.path.join(HERE, f"{KEY}_mix.wav")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", raw, "-af", "loudnorm=I=-14:TP=-1.0:LRA=9", "-ar", "48000", out], check=True)
    os.remove(raw); print("audio", out, DUR)

if __name__ == "__main__":
    mode = sys.argv[2]
    if mode == "frames":
        for tp in [float(x) for x in sys.argv[3].split(",")]: frame(tp).save(os.path.join(HERE, f"{KEY}_f{tp:05.2f}.png"))
        print("cuts", [round(x, 2) for x in CUTS])
    elif mode == "audio": build_audio()
    elif mode == "seg":
        i, n = int(sys.argv[3]), int(sys.argv[4]); fps = 60; N = int(round(DUR * fps)); a, b = N * i // n, N * (i + 1) // n
        ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1080x1920", "-r", str(fps), "-i", "-",
                               "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p", os.path.join(HERE, f"{KEY}_seg{i}.mp4")], stdin=subprocess.PIPE)
        for k in range(a, b): ff.stdin.write(frame(k / fps).tobytes())
        ff.stdin.close(); ff.wait()

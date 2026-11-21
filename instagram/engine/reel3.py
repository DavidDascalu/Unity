"""Premium meal-plan reel - reuses the motion engine in reel2.py."""
import math, os, sys, subprocess
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reel2 as R
from reel2 import (W, H, FPS, LIME, LIME2, WHITE, INK, cl, e_out, e_back, e_inout, lerp, paste_scaled,
                   pop_text, pill, T, font, F_HUGE, F_BIG, F_MID, F_SM, logo, GLOW, SHADOW, PW, phone)

DUR = 14.0
R.DUR = DUR
CUTS = [0.0, 2.5, 5.3, 6.6, 9.7, 11.3, DUR]
R.SHOTS["more"] = Image.open(os.path.join(R.HERE, "p_Mai_mult.png")).convert("RGB")
PH_MORE = phone("more", 0)

CARD = (250, 252, 249)
CARD_INK = (24, 40, 33)
MUTED = (110, 128, 120)
APPG = (31, 94, 70)
F_ROW = font("SemiBold", 46)
F_ROWB = font("ExtraBold", 50)
F_STEP = font("Black", 92)

def card(w, h, r=48):
    im = Image.new("RGBA", (w + 80, h + 100), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([40, 60, w + 40, h + 60], r, fill=(0, 0, 0, 120))
    from PIL import ImageFilter
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(28)))
    ImageDraw.Draw(im).rounded_rectangle([40, 40, w + 40, h + 40], r, fill=CARD + (255,))
    return im, 40

def step_title(im, t, t0, num, text):
    k = e_back((t - t0) / 0.3)
    if t < t0: return
    d = ImageDraw.Draw(im)
    chip = Image.new("RGBA", (124, 124), (0, 0, 0, 0))
    ImageDraw.Draw(chip).ellipse([0, 0, 123, 123], fill=LIME + (255,))
    ImageDraw.Draw(chip).text((62, 64), str(num), font=F_STEP, fill=INK, anchor="mm")
    paste_scaled(im, chip, 64 + 62, 400, 0.5 + 0.5 * k)
    pop_text(im, text, F_BIG, WHITE, 214, 325, t0 + 0.08, t)

# ---------------- scenes ----------------
QS = [(-30, 900, 0.0, 1.1), (840, 1080, 0.25, 0.8), (130, 1250, 0.5, 0.9), (900, 640, 0.15, 0.7), (720, 1350, 0.4, 1.0)]

def s_hook(im, t):
    # floating question marks
    for i, (x, y, d0, s) in enumerate(QS):
        k = (t - d0) / 0.4
        if k <= 0: continue
        q = T("?", F_HUGE, (199, 240, 130, 90) if i % 2 else (255, 255, 255, 60))
        paste_scaled(im, q, x + 120 + 20 * math.sin(t * 2 + i), y + 25 * math.cos(t * 1.7 + i),
                     s * 1.6 * e_back(k), 15 * math.sin(t * 1.3 + i * 2))
    pop_text(im, "CE MĂNÂNC", F_BIG, WHITE, 64, 520, 0.05, t)
    k2 = (t - 0.45) / 0.3
    if k2 > 0:
        lay = T("MÂINE?", F_HUGE, LIME)
        s2 = 1.45 - 0.45 * e_back(k2, 2.4)
        wob = 3 * math.sin((t - 0.45) * 18) * max(0, 1 - (t - 0.45) / 0.8)
        paste_scaled(im, T("MÂINE?", F_HUGE, (0, 0, 0, 120)), 64 + lay.width / 2 + 8, 670 + lay.height / 2 + 12, s2, wob, alpha=cl(k2 * 2))
        paste_scaled(im, lay, 64 + lay.width / 2, 670 + lay.height / 2, s2, wob, alpha=cl(k2 * 2))
    # strike-through
    ks = e_out((t - 1.35) / 0.25)
    if ks > 0:
        d = ImageDraw.Draw(im)
        x1 = lerp(50, 820, ks)
        d.line([(50, 760), (x1, 735)], fill=(255, 92, 92, 255), width=22)
        d.line([(50, 620), (lerp(50, 720, ks), 600)], fill=(255, 92, 92, 255), width=18)
    # stamp
    k3 = (t - 1.6) / 0.3
    if k3 > 0:
        txt = "NU MAI ÎNTREBA."
        tw = ImageDraw.Draw(im).textlength(txt, font=F_MID)
        st = Image.new("RGBA", (int(tw + 90), 130), (0, 0, 0, 0))
        pill(st, 0, 0, st.width - 1, 129, LIME + (255,), 34)
        ImageDraw.Draw(st).text((st.width / 2, 66), txt, font=F_MID, fill=INK, anchor="mm")
        paste_scaled(im, st, 64 + st.width / 2, 1000, 1.6 - 0.6 * e_back(k3, 2.0), -4)

def s_profile(im, t):
    lt = t - 2.5
    step_title(im, t, 2.5, 1, "Profilul tău")
    # real app screen, tilted phone in the back
    kph = e_out(lt / 0.5)
    ph = PH_MORE.rotate(-8, Image.BICUBIC, expand=True)
    paste_scaled(im, ph, lerp(1300, 820, kph), 1180, 0.62, alpha=1.0)
    # profile card slides in
    kc = e_out((lt - 0.25) / 0.45)
    cw, chh = 700, 760
    c, o = card(cw, chh)
    d = ImageDraw.Draw(c)
    d.text((o + 44, o + 46), "PROFIL", font=F_SM, fill=APPG)
    rows = ["Vârstă", "Greutate", "Înălțime", "Activitate"]
    for i, r in enumerate(rows):
        y = o + 130 + i * 112
        kr = cl((lt - 0.55 - i * 0.22) / 0.25)
        d.text((o + 44, y + 30), r, font=F_ROW, fill=CARD_INK, anchor="lm")
        d.rounded_rectangle([o + 380, y, o + cw - 44, y + 62], 31, fill=(236, 243, 238, 255))
        if kr > 0:
            d.rounded_rectangle([o + 380, y, o + 380 + (cw - 424) * kr, y + 62], 31, fill=(199, 240, 130, 255))
            if kr >= 1:
                d.ellipse([o + cw - 100, y + 9, o + cw - 56, y + 53], fill=APPG + (255,))
                d.line([(o + cw - 90, y + 32), (o + cw - 81, y + 42), (o + cw - 66, y + 22)], fill=WHITE, width=6)
    d.text((o + 44, o + 600), "Ce nu mănânci", font=F_ROWB, fill=CARD_INK)
    chips = ["arahide", "lactoză"]
    x = o + 44
    for i, ch in enumerate(chips):
        kk = cl((lt - 1.6 - i * 0.25) / 0.2)
        if kk <= 0: continue
        w = d.textlength(ch, font=F_ROW) + 110
        d.rounded_rectangle([x, o + 672, x + w, o + 742], 35, fill=(255, 226, 226, 255))
        d.text((x + 30, o + 707), ch, font=F_ROW, fill=(170, 40, 40), anchor="lm")
        d.line([(x + w - 58, o + 693), (x + w - 34, o + 721)], fill=(170, 40, 40), width=6)
        d.line([(x + w - 34, o + 693), (x + w - 58, o + 721)], fill=(170, 40, 40), width=6)
        x += w + 20
    paste_scaled(im, c, lerp(-500, 430, kc), 880, 0.86 if kc > 0 else 0, lerp(-10, -2, kc))

RINGS = [("kcal", (46, 160, 105)), ("proteine", (62, 168, 112)), ("carbo", (240, 150, 50)), ("grăsimi", (70, 120, 210))]
def s_targets(im, t):
    lt = t - 5.3
    step_title(im, t, 5.3, 2, "Ținte zilnice")
    d = ImageDraw.Draw(im)
    for i, (lab, col) in enumerate(RINGS):
        cx = 250 + (i % 2) * 400; cy = 760 + (i // 2) * 360
        k = e_back((lt - i * 0.1) / 0.35)
        if k <= 0: continue
        r = 140 * k
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(42, 92, 70), width=int(26 * k) or 1)
        f = e_out((lt - 0.15 - i * 0.1) / 0.7)
        if f > 0:
            d.arc([cx - r, cy - r, cx + r, cy + r], -90, -90 + 360 * f * 0.86, fill=col + (255,), width=int(26 * k) or 1)
        d.text((cx, cy), lab, font=F_SM, fill=WHITE, anchor="mm")

def s_plan(im, t):
    lt = t - 6.6
    step_title(im, t, 6.6, 3, "Planul tău")
    # segmented control 1 / 7 / 30
    d = ImageDraw.Draw(im)
    segs = ["1 zi", "7 zile", "30 zile"]
    x0, y0, sw, sh = 64, 520, 250, 116
    kin = e_back(lt / 0.3)
    bar = Image.new("RGBA", (sw * 3 + 20, sh + 20), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bar)
    pill(bar, 0, 0, bar.width - 1, bar.height - 1, (255, 255, 255, 36))
    # highlight slides 0 -> 1 -> 2, synced to the voice ("1, 7 sau 30")
    pos = 0 if lt < 1.15 else (lerp(0, 1, e_inout((lt - 1.15) / 0.22)) if lt < 1.6 else lerp(1, 2, e_inout((lt - 1.6) / 0.22)))
    hx = 10 + pos * sw
    pill(bar, hx, 10, hx + sw, 10 + sh, LIME + (255,))
    for i, s in enumerate(segs):
        on = abs(pos - i) < 0.5
        bd.text((10 + i * sw + sw / 2, 10 + sh / 2), s, font=F_ROWB, fill=INK if on else WHITE, anchor="mm")
    paste_scaled(im, bar, x0 + bar.width / 2, y0 + bar.height / 2, 0.6 + 0.4 * kin)
    # 30-day calendar grid
    cols, cell, gap = 6, 100, 12
    gx = 64 + (790 - (cols * cell + (cols - 1) * gap)) / 2
    for i in range(30):
        c_, r_ = i % cols, i // cols
        k = e_back((lt - 1.95 - i * 0.025) / 0.3, 2.2)
        if k <= 0: continue
        cx = gx + c_ * (cell + gap) + cell / 2; cy = 700 + r_ * (cell + gap) + cell / 2
        tile = Image.new("RGBA", (cell, cell), (0, 0, 0, 0))
        td = ImageDraw.Draw(tile)
        td.rounded_rectangle([0, 0, cell - 1, cell - 1], 26, fill=CARD + (255,))
        td.text((16, 12), str(i + 1), font=F_SM, fill=CARD_INK)
        for j, col in enumerate([(46, 160, 105), (240, 150, 50), (70, 120, 210)]):
            td.ellipse([18 + j * 28, cell - 34, 38 + j * 28, cell - 14], fill=col)
        paste_scaled(im, tile, cx, cy, k)

def s_shop(im, t):
    lt = t - 9.7
    pop_text(im, "Lista de", F_BIG, WHITE, 64, 330, 9.7, t)
    pop_text(im, "cumpărături", F_BIG, LIME, 64, 470, 9.8, t)
    kc = e_out(lt / 0.4)
    c, o = card(720, 560)
    d = ImageDraw.Draw(c)
    items = ["Legume", "Ouă", "Iaurt", "Ovăz"]
    for i, it in enumerate(items):
        y = o + 50 + i * 125
        done = lt > 0.45 + i * 0.22
        d.rounded_rectangle([o + 44, y + 10, o + 124, y + 90], 22, fill=(APPG + (255,)) if done else (236, 243, 238, 255))
        if done:
            d.line([(o + 62, y + 52), (o + 80, y + 70), (o + 108, y + 32)], fill=WHITE, width=9)
        d.text((o + 160, y + 50), it, font=F_ROWB, fill=MUTED if done else CARD_INK, anchor="lm")
        if done:
            tw = d.textlength(it, font=F_ROWB)
            d.line([(o + 160, y + 52), (o + 160 + tw, y + 52)], fill=MUTED, width=5)
    paste_scaled(im, c, 455, lerp(1500, 920, kc), 1.0, lerp(6, 0, kc))

def s_cta(im, t):
    lt = t - 11.3
    beat = 0.5
    pulse = 1 + 0.05 * max(0, math.cos((lt % beat) / beat * math.pi)) ** 8
    paste_scaled(im, GLOW, 455, 500, 0.7, alpha=0.8)
    paste_scaled(im, logo, 455, 500, 0.75 * e_back(lt / 0.4), (1 - e_out(lt / 0.4)) * -30)
    pop_text(im, "Scrie în comentarii", F_MID, WHITE, 455, 700, 11.45, t, anchor="c")
    k = (lt - 0.35) / 0.35
    if k > 0:
        tw = ImageDraw.Draw(im).textlength("PLAN", font=F_HUGE)
        pim = Image.new("RGBA", (int(tw + 160), 250), (0, 0, 0, 0))
        pill(pim, 0, 0, pim.width - 1, 249, LIME + (255,), 70)
        ImageDraw.Draw(pim).text((pim.width / 2, 125), "PLAN", font=F_HUGE, fill=INK, anchor="mm")
        paste_scaled(im, pim, 455, 930, (0.5 + 0.5 * e_back(k, 2.6)) * pulse * 0.9, 3 * math.sin(lt * 4) * max(0, 1 - lt / 2))
    k4 = (lt - 0.9) / 0.3
    if k4 > 0:
        txt = "Premium · de la 25 lei/lună"
        tw = ImageDraw.Draw(im).textlength(txt, font=F_SM)
        ch = Image.new("RGBA", (int(tw + 64), 84), (0, 0, 0, 0))
        pill(ch, 0, 0, ch.width - 1, 83, (255, 255, 255, 40))
        ImageDraw.Draw(ch).text((32, 42), txt, font=F_SM, fill=WHITE, anchor="lm")
        paste_scaled(im, ch, 455, 1130, 0.6 + 0.4 * e_back(k4))

R.SCENES = [s_hook, s_profile, s_targets, s_plan, s_shop, s_cta]
R.CUTS = CUTS
R.SUBS = [
    (0.1, 2.4, "Nu mai întreba ce mănânci mâine."),
    (2.6, 5.2, "Pui vârsta, greutatea și ce nu mănânci."),
    (5.35, 6.55, "Primești ținte zilnice."),
    (6.7, 9.6, "Și un plan pe 1, 7 sau 30 de zile."),
    (9.75, 11.2, "Plus lista de cumpărături."),
    (11.4, 13.8, "Scrie PLAN. Mâine știi deja."),
]
R.SUBW = [R.word_times(*s) for s in R.SUBS]
R.POPS = [0.05, 0.45, 1.6, 2.55, 2.75] + [3.05 + i * 0.22 for i in range(4)] + [4.1, 4.35, 5.3, 5.4, 5.5, 5.6, 6.6,
          7.5, 8.0] + [8.2 + i * 0.025 * 3 for i in range(10)] + [10.15 + i * 0.22 for i in range(4)] + [11.3, 11.65, 12.2]
R.TICKS = []
R.STABS = [(0.45, 880), (1.35, 440), (11.65, 659.25), (11.65, 987.77)]


# ---- sync to the ElevenLabs voiceover (take 1), offset 0.2 s ----
VO_OFF = 0.2
OLD = CUTS[:]
DUR = 14.8
NEW = [0.0, 2.1, 5.15, 6.65, 9.93, 11.6, DUR]
R.DUR = DUR
def to_old(t):
    i = max(j for j in range(6) if t >= NEW[j])
    a, b, oa, ob = NEW[i], NEW[i + 1], OLD[i], OLD[i + 1]
    return oa + (t - a) * (ob - oa) / (b - a) if i < 5 else oa + (t - a)
OLD_SCENES = list(R.SCENES)
R.SCENES = [(lambda f: (lambda im, t: f(im, to_old(t))))(f) for f in OLD_SCENES]
R.CUTS = NEW
o = VO_OFF
R.SUBS = [
    (0.0 + o, 1.75 + o, "Nu mai întreba ce mănânci mâine."),
    (1.96 + o, 4.8 + o, "Pui vârsta, greutatea și ce nu mănânci."),
    (5.0 + o, 6.4 + o, "Primești ținte zilnice."),
    (6.5 + o, 9.55 + o, "Și un plan pe 1, 7 sau 30 de zile."),
    (9.78 + o, 11.1 + o, "Plus lista de cumpărături."),
    (11.47 + o, 14.4, "Scrie PLAN. Mâine știi deja."),
]
R.SUBW = [R.word_times(a, b + 0.3, s) for a, b, s in R.SUBS]
def old_to_new(x):
    i = max(j for j in range(6) if x >= OLD[j])
    return NEW[i] + (x - OLD[i]) * (NEW[i + 1] - NEW[i]) / (OLD[i + 1] - OLD[i]) if i < 5 else NEW[i] + (x - OLD[i])
R.POPS = [old_to_new(x) for x in R.POPS]
R.STABS = [(old_to_new(a), f) for a, f in R.STABS]

if __name__ == "__main__":
    out = sys.argv[1]
    if len(sys.argv) > 2:
        for tp in [float(x) for x in sys.argv[2].split(",")]:
            R.frame(tp).save(os.path.join(R.HERE, f"pv3_{tp:.1f}.png"))
        sys.exit()
    wav = os.path.join(R.HERE, "music3.wav"); R.soundtrack(wav)
    mix = os.path.join(R.HERE, "mix3.wav")
    vo = os.path.join(R.HERE, "vo1.mp3")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-i", vo, "-filter_complex",
                    "[1:a]adelay=200|200,aformat=channel_layouts=stereo,volume=1.6,apad,asplit=2[v][sc];"
                    "[0:a]volume=0.55[m];[m][sc]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=300[md];"
                    "[md][v]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95", "-ar", "44100", mix], check=True)
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", mix,
                           "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
                           "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out],
                          stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)):
        ff.stdin.write(R.frame(i / FPS).tobytes())
    ff.stdin.close(); ff.wait(); print("done", out)

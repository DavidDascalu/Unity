"""Data-driven 9:16 reels on the spot engine, dark or light style.

    python3 reel_gen.py <key> frames 1,4,8   |   python3 reel_gen.py <key> audio   |   python3 reel_gen.py <key> seg i n
Five scenes per reel, cut on the five phrases of the ElevenLabs voiceover.
"""
import math, os, re, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
SPOT = os.path.join(HERE, "..", "..", "spot"); ENGINE = os.path.join(HERE, "..", "..", "engine")
sys.path.insert(0, SPOT)
import render as R
import audio as AU
from render import (W, H, k01, eo, eio, eback, lerp, lerp2, paste, fade, scaled, place3d, glow_line, poly_partial, text_img, AS, LOGO, GLOW_G, F)

PAL = {
    "dark":  dict(bg=(11, 15, 12), text=(244, 246, 241), muted=(165, 188, 169), acc=(148, 230, 2), acc_txt=(188, 251, 16),
                  card=(26, 31, 27), card2=(34, 41, 36), line=(148, 230, 2), warm=(255, 214, 150, 38), vig=210, pill_fg=(8, 30, 22), sub_bg=(6, 9, 7, 170)),
    "light": dict(bg=(244, 246, 241), text=(32, 51, 42), muted=(110, 128, 118), acc=(199, 240, 130), acc_txt=(37, 94, 70),
                  card=(255, 255, 255), card2=(236, 242, 234), line=(56, 120, 90), warm=(199, 240, 130, 70), vig=70, pill_fg=(8, 30, 22), sub_bg=(32, 51, 42, 210)),
}
SC = lambda n: os.path.join(ENGINE, "ov", n)
LT = lambda n: os.path.join(ENGINE, n)

def app_screen(path, bg):
    cap = Image.open(path).convert("RGB").resize((AS.SW, round(Image.open(path).height * AS.SW / Image.open(path).width)))
    scr = Image.new("RGB", (AS.SW, AS.SH), bg); scr.paste(cap, (0, 150)); return scr

REELS = {
 "x1": dict(mp3="x1_voce.mp3", kw="JURNAL", style="dark",
   subs=["Ai mâinile ocupate?", "Spui ce ai mâncat, cu vocea.", "Verifici ce a înțeles.", "Confirmi și intră în jurnal.", "Scrie JURNAL în comentarii!"],
   scenes=[("title", ["Ai mâinile", "ocupate?"]), ("mic", "Spune cu vocea"), ("rows", "Verifici", [["Iaurt simplu", "150 g"], ["Banană", "1 bucată"]]),
           ("done", "Adăugat în jurnal."), ("cta", None)]),
 "x2": dict(mp3="x2_barcode.mp3", kw="ETICHETA", style="light",
   subs=["Ai produsul în mână?", "Scanezi codul de bare.", "Verifici produsul și gramajul.", "Confirmi și gata.", "Scrie ETICHETA în comentarii!"],
   scenes=[("title", ["Ai produsul", "în mână?"]), ("barcode", None), ("rows", "Verifici", [["Produsul", "corect?"], ["Gramajul", "cât ai mâncat"]]),
           ("done", "Confirmat."), ("cta", None)]),
 "x3": dict(mp3="x3_buget.mp3", kw="PLAN", style="dark",
   subs=["Ai un buget pentru mâncare?", "Îl treci în profil, în lei pe săptămână.", "Apoi îți generezi planul.", "Cu lista de cumpărături inclusă.", "Scrie PLAN în comentarii!"],
   scenes=[("title", ["Ai un buget", "pentru mâncare?"]), ("field", "Buget săptămânal (RON)"), ("phone", SC("more.png")),
           ("list", ["Legume", "Ouă", "Iaurt", "Ovăz"]), ("cta", "Premium · de la 25 lei/lună")]),
 "x4": dict(mp3="x4_nuti.mp3", kw="JURNAL", style="light",
   subs=["Prima dată în aplicație?", "Nuti te ghidează pas cu pas.", "Îți arată cum adaugi o masă.", "Sau cum îți faci planul.", "Scrie JURNAL în comentarii!"],
   scenes=[("title", ["Prima dată", "în aplicație?"]), ("bubble", ["Nuti · Ghidul tău", "Salut! Te ajut să găsești ce ai nevoie."]),
           ("tour", (LT("a_home.png"), "Apasă aici pentru a adăuga un aliment.", (585, 1825))),
           ("tour", (LT("p_Mai_mult.png"), "Deschide Profil și plan.", (855, 895))), ("cta", None)]),
 "x5": dict(mp3="x5_gratuit.mp3", kw="JURNAL", style="dark",
   subs=["Ce primești gratuit?", "Jurnalul și înregistrarea meselor.", "Premium adaugă planul personal și analiza AI.", "De la 25 de lei pe lună.", "Scrie JURNAL în comentarii!"],
   scenes=[("title", ["Ce primești", "gratuit?"]), ("rows", "Cont gratuit", [["Jurnalul local", "inclus"], ["Înregistrarea meselor", "inclusă"]]),
           ("rows", "Premium", [["Plan personal", "inclus"], ["Analiză AI", "inclusă"], ["Ținte zilnice", "incluse"]]),
           ("stat", ("25 lei", "pe lună · sau 79,99 lei pe an")), ("cta", None)]),
 "x6": dict(mp3="x6_sync.mp3", kw="JURNAL", style="light",
   subs=["Telefon dimineața, laptop la birou?", "Intri în cont.", "Profilul și mesele se sincronizează.", "Același jurnal, oriunde.", "Scrie JURNAL în comentarii!"],
   scenes=[("title", ["Telefon sau", "laptop?"]), ("rows", "Intri în cont", [["Email", ""], ["Parolă", ""]]), ("sync", LT("a_home.png")),
           ("title", ["Același jurnal,", "oriunde."]), ("cta", None)]),
 "x7": dict(mp3="x7_momente.mp3", kw="JURNAL", style="dark",
   subs=["Mic dejun, prânz, gustare, cină.", "Fiecare masă are locul ei.", "Vezi ziua pe momente.", "Și totalul zilei, dintr-o privire.", "Scrie JURNAL în comentarii!"],
   scenes=[("moments", ["Mic dejun", "Prânz", "Gustare", "Cină"]), ("title", ["Fiecare masă", "are locul ei."]), ("phone", SC("home_macros.png")),
           ("phone", SC("home_full.png")), ("cta", None)]),
}
KEY = sys.argv[1]; CFG = REELS[KEY]; P_ = PAL[CFG["style"]]
VO = 0.55

def phrase_starts(mp3):
    x = AU.load_mp3(mp3)
    out = subprocess.run(["ffmpeg", "-hide_banner", "-i", mp3, "-af", "silencedetect=noise=-38dB:d=0.25", "-f", "null", "-"], capture_output=True, text=True).stderr
    ends = [float(v) for v in re.findall(r"silence_end: ([0-9.]+)", out)]
    starts = [AU.onset(x)] + [e for e in ends if e < len(x) / AU.SR - 0.2]
    return [s + VO for s in starts[:5]], len(x) / AU.SR + VO
P, VEND = phrase_starts(os.path.join(HERE, CFG["mp3"]))
DUR = round(VEND + 1.8, 2)
CUTS = [0.0] + [p - 0.12 for p in P[1:]] + [DUR]

# ---------- palette-aware helpers ----------
def reveal(c, txt, font, cx, top, t, t0, t1=None, fill=None, accent=False):
    k = eo(k01(t, t0, t0 + 0.55)); a = k * (1 - (0 if t1 is None else eio(k01(t, t1, t1 + 0.35))))
    if a <= 0.01: return
    im = text_img(txt, font, (P_["acc_txt"] if accent else (fill or P_["text"])))
    q = round((1 - a) * 6) / 6
    if q > 0: im = im.filter(ImageFilter.GaussianBlur(q * 12))
    if im.width > 1000: im = scaled(im, 1000 / im.width)
    paste(c, fade(im, a), cx - im.width / 2, top - 20 + (1 - k) * 26)

def out_k(t, i): return eio(k01(t, CUTS[i + 1] - 0.1, CUTS[i + 1] + 0.3)) if i < 4 else 0.0

def card_img(w, h, r=56):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ImageDraw.Draw(im).rounded_rectangle([0, 0, w - 1, h - 1], r, fill=P_["card"] + (255,),
        outline=(P_["card2"] + (255,)) if CFG["style"] == "light" else None, width=3); return im

def phone(screen_img): return R.phone_img(screen_img)

# ---------- scenes ----------
def s_title(c, t, i, lines):
    a, b = CUTS[i], CUTS[i + 1]
    reveal(c, lines[0], F("dk", 120), 540, 700, t, a + 0.15, b - 0.1)
    reveal(c, lines[1], F("dk", 132), 540, 850, t, a + 0.4, b - 0.1, accent=True)
    if i == 0:
        y = 1120
        if t < 0.2:
            k = eio(t / 0.2); half = lerp(30, 480, k); glow_line(c, [(540 - half, y), (540 + half, y)], width=lerp(4, 24, k), col=P_["line"], inten=lerp(0.4, 1.2, k))
        else:
            head = lerp(170, 910, eio(k01(t, 0.22, 1.2))); glow_line(c, [(170, y), (head, y)], width=11, col=P_["line"], head=(head, y) if head < 905 else None)
            fl = max(0, 1 - (t - 0.2) / 0.25)
            if fl > 0: paste(c, fade(scaled(GLOW_G, 1.3), fl), 540 - 780, y - 780)
    else:
        half = lerp(0, 330, eo(k01(t, a + 0.3, a + 1.0))) * (1 - out_k(t, i)); glow_line(c, [(540 - half, 1120), (540 + half, 1120)], width=9, col=P_["line"])

def s_rows(c, t, i, title, rows):
    a = CUTS[i]; o = out_k(t, i)
    reveal(c, title, F("db", 90), 540, 380, t, a + 0.05, CUTS[i + 1] - 0.1)
    for j, (n, v) in enumerate(rows):
        k = eback(k01(t, a + 0.25 + j * 0.25, a + 0.65 + j * 0.25), 1.3)
        if k <= 0: continue
        cd = card_img(860, 150, 44); d = ImageDraw.Draw(cd)
        d.ellipse([40, 45, 100, 105], fill=P_["acc"] + (255,)); d.line([(55, 76), (68, 89), (88, 62)], fill=P_["pill_fg"], width=7)
        d.text((130, 75), n, font=F("db", 52), fill=P_["text"], anchor="lm")
        if v: d.text((820, 75), v, font=F("s", 42), fill=P_["acc_txt"] if CFG["style"] == "light" else P_["acc"], anchor="rm")
        place3d(c, cd, 540, 680 + j * 190, max(0.05, min(1.05, k)), rx=lerp(20, 0, min(1, k)), alpha=min(1, k) * (1 - o), shadow=0.35)

def s_phone(c, t, i, path, tilt=-6):
    a = CUTS[i]; k = eo(k01(t, a, a + 0.8)); o = out_k(t, i)
    place3d(c, phone(app_screen(path, P_["bg"] if CFG["style"] == "dark" else (244, 246, 241))), 540, lerp(2300, 1000, k) + 8 * math.sin(t), 0.5,
            ry=lerp(-16, tilt, k), rx=lerp(14, 4, k), alpha=1 - o, blur=o * 12, shadow=0.8)
    return k

def s_mic(c, t, i, label):
    a = CUTS[i]; o = out_k(t, i); lt = t - a; k = eback(k01(t, a, a + 0.5), 1.3)
    reveal(c, label, F("db", 80), 540, 360, t, a + 0.05, CUTS[i + 1] - 0.1)
    d = ImageDraw.Draw(c); r = 150 * max(0.05, min(1.1, k))
    for ring in range(3):
        rr_ = r + ((lt * 120 + ring * 70) % 210); al = int(120 * (1 - ((lt * 120 + ring * 70) % 210) / 210) * (1 - o))
        d.ellipse([540 - rr_, 960 - rr_, 540 + rr_, 960 + rr_], outline=P_["acc"] + (al,), width=6)
    d.ellipse([540 - r, 960 - r, 540 + r, 960 + r], fill=P_["acc"] + (int(255 * (1 - o)),))
    d.rounded_rectangle([510, 880, 570, 990], 30, fill=P_["pill_fg"] + (int(255 * (1 - o)),))
    d.arc([480, 920, 600, 1030], 0, 180, fill=P_["pill_fg"] + (int(255 * (1 - o)),), width=10); d.line([(540, 1030), (540, 1060)], fill=P_["pill_fg"], width=10)
    pts = [(220 + x * 6.4, 1300 + 60 * math.sin(x * 0.35 + lt * 9) * math.sin(x * 0.07) * (1 - o)) for x in range(101)]
    glow_line(c, pts, width=8, col=P_["line"], inten=1 - o)

def s_barcode(c, t, i, _=None):
    a = CUTS[i]; o = out_k(t, i); k = s_phone(c, t, i, LT("a_home.png") if False else SC("scan.png"))
    lab = Image.open(os.path.join(SPOT, "assets", "label.png")).convert("RGBA"); bc = lab.crop((40, 950, 600, 1110))
    pc = Image.new("RGBA", (700, 300), (255, 255, 255, 255)); pc.alpha_composite(bc.resize((620, 180)), (40, 60))
    place3d(c, pc, 540, 900, 0.95 * k, rz=-3, alpha=k * (1 - o), shadow=0.5)
    u = math.sin((t - a) * 4) * 0.5 + 0.5
    if k > 0.5: glow_line(c, [(200, 820 + u * 160), (880, 820 + u * 160)], width=8, col=(255, 80, 80) if False else P_["line"], inten=1 - o)

def s_done(c, t, i, label):
    a = CUTS[i]; o = out_k(t, i); k = eback(k01(t, a, a + 0.5), 1.6)
    d = ImageDraw.Draw(c); r = 170 * max(0.05, min(1.1, k))
    d.ellipse([540 - r, 900 - r, 540 + r, 900 + r], fill=P_["acc"] + (int(255 * (1 - o)),))
    if k > 0.3: d.line([(540 - r * 0.42, 905), (540 - r * 0.08, 900 + r * 0.33), (540 + r * 0.45, 900 - r * 0.3)], fill=P_["pill_fg"] + (int(255 * (1 - o)),), width=24, joint="curve")
    reveal(c, label, F("db", 84), 540, 1170, t, a + 0.3, CUTS[i + 1] - 0.1)

def s_field(c, t, i, label):
    a = CUTS[i]; o = out_k(t, i); k = eo(k01(t, a, a + 0.6)); lt = t - a
    cd = card_img(880, 360); d = ImageDraw.Draw(cd)
    d.text((50, 60), "PROFIL", font=F("b", 36), fill=P_["acc_txt"] if CFG["style"] == "light" else (178, 231, 154))
    d.text((50, 120), label, font=F("db", 56), fill=P_["text"])
    d.rounded_rectangle([50, 220, 830, 320], 30, fill=P_["card2"] + (255,))
    d.text((90, 270), "lei / săptămână", font=F("m", 44), fill=P_["muted"], anchor="lm")
    if (lt * 2) % 1 < 0.6: d.line([(88, 240), (88, 300)], fill=P_["text"], width=4)
    place3d(c, cd, 540, lerp(1300, 900, k), 1.0, rx=lerp(25, 4, k), ry=-4, alpha=k * (1 - o), shadow=0.5)
    half = lerp(0, 380, eo(k01(t, a + 0.4, a + 1.1))) * (1 - o); glow_line(c, [(540 - half, 1170), (540 + half, 1170)], width=8, col=P_["line"])

def s_list(c, t, i, items):
    a = CUTS[i]; o = out_k(t, i); lt = t - a; k = eo(k01(t, a, a + 0.6))
    reveal(c, "Cumpărături", F("db", 90), 540, 330, t, a + 0.05, CUTS[i + 1] - 0.1)
    cd = card_img(760, 600); d = ImageDraw.Draw(cd)
    for j, it in enumerate(items):
        y = 60 + j * 128; done = lt > 0.35 + j * 0.22
        d.rounded_rectangle([50, y, 130, y + 80], 22, fill=(P_["acc"] + (255,)) if done else (P_["card2"] + (255,)))
        if done: d.line([(68, y + 42), (86, y + 60), (114, y + 22)], fill=P_["pill_fg"], width=9)
        d.text((170, y + 40), it, font=F("db", 54), fill=P_["muted"] if done else P_["text"], anchor="lm")
    place3d(c, cd, 540, lerp(1500, 1000, k), 1.0, rx=lerp(20, 4, k), ry=-4, alpha=k * (1 - o), shadow=0.6)

def s_bubble(c, t, i, lines):
    a = CUTS[i]; o = out_k(t, i); k = eback(k01(t, a, a + 0.5), 1.3)
    cd = card_img(880, 360, 60); d = ImageDraw.Draw(cd)
    lg = scaled(LOGO, 0.07); cd.alpha_composite(lg, (50, 50))
    d.text((180, 95), lines[0], font=F("b", 40), fill=P_["acc_txt"])
    y = 180
    for ln in [lines[1][:26], lines[1][26:]]:
        d.text((50, y), ln.strip(), font=F("db", 54), fill=P_["text"]); y += 70
    place3d(c, cd, 540, 900, max(0.05, min(1.05, k)), rz=lerp(-6, -1, min(1, k)), alpha=min(1, k) * (1 - o), shadow=0.5)

def s_tour(c, t, i, spec):
    path, tip, (tx, ty) = spec; a = CUTS[i]; o = out_k(t, i); k = eo(k01(t, a, a + 0.6))
    s = 0.5; py = lerp(2300, 1080, k)
    place3d(c, phone(app_screen(path, (244, 246, 241))), 540, py, s, alpha=1 - o, shadow=0.8)
    hx, hy = R.scr2frame(tx * 1179 / 1170, ty * 1179 / 1170 + 150, 540, py, s)
    pul = 1 + 0.15 * math.sin((t - a) * 8)
    if k > 0.6:
        d = ImageDraw.Draw(c); rr_ = 60 * pul; d.ellipse([hx - rr_, hy - rr_, hx + rr_, hy + rr_], outline=P_["line"] + (int(255 * (1 - o)),), width=8)
    tipim = text_img(tip, F("b", 40), P_["pill_fg"]); pad = Image.new("RGBA", (tipim.width + 30, tipim.height + 10), (0, 0, 0, 0))
    ImageDraw.Draw(pad).rounded_rectangle([0, 0, pad.width - 1, pad.height - 1], 34, fill=P_["acc"] + (255,)); pad.alpha_composite(tipim, (15, 5))
    if pad.width > 980: pad = scaled(pad, 980 / pad.width)
    paste(c, fade(pad, eo(k01(t, a + 0.5, a + 0.9)) * (1 - o)), 540 - pad.width / 2, 300)

def s_stat(c, t, i, spec):
    val, lab = spec; a = CUTS[i]; o = out_k(t, i); k = eback(k01(t, a, a + 0.5), 1.5)
    im = text_img(val, F("dk", 230), P_["acc_txt"] if CFG["style"] == "light" else P_["acc"])
    paste(c, fade(scaled(im, max(0.05, 0.6 + 0.4 * k)), min(1, k) * (1 - o)), 540 - im.width * (0.6 + 0.4 * k) / 2, 760)
    reveal(c, lab, F("m", 48), 540, 1080, t, a + 0.3, CUTS[i + 1] - 0.1, fill=P_["muted"])

def s_sync(c, t, i, path):
    a = CUTS[i]; o = out_k(t, i); k = eo(k01(t, a, a + 0.7)); lt = t - a
    scr = app_screen(path, (244, 246, 241))
    lap = Image.new("RGBA", (900, 620), (0, 0, 0, 0)); ld = ImageDraw.Draw(lap)
    ld.rounded_rectangle([60, 0, 840, 520], 30, fill=(30, 32, 31, 255)); ld.rounded_rectangle([0, 520, 900, 580], 20, fill=(150, 150, 146, 255))
    view = scr.crop((0, 150, 1179, 150 + 640)).resize((740, 480)); lap.paste(view, (80, 20))
    place3d(c, lap, lerp(900, 640, k), 820, 0.78, ry=lerp(30, 14, k), alpha=k * (1 - o), shadow=0.5)
    place3d(c, phone(scr), lerp(100, 300, k), 1180, 0.3, ry=-10, alpha=k * (1 - o), shadow=0.6)
    for j in range(3):
        u = ((lt * 0.9 + j / 3) % 1); p = lerp2((360, 1050), (620, 900), u)
        d = ImageDraw.Draw(c); d.ellipse([p[0] - 12, p[1] - 12, p[0] + 12, p[1] + 12], fill=P_["line"] + (int(255 * math.sin(u * math.pi) * (1 - o)),))

def s_moments(c, t, i, names):
    a = CUTS[i]; o = out_k(t, i)
    for j, n in enumerate(names):
        k = eback(k01(t, a + 0.15 + j * 0.3, a + 0.55 + j * 0.3), 1.4)
        if k <= 0: continue
        cd = card_img(800, 160, 46); d = ImageDraw.Draw(cd)
        d.text((60, 80), n, font=F("db", 64), fill=P_["text"], anchor="lm"); d.ellipse([700, 50, 760, 110], fill=P_["acc"] + (255,))
        place3d(c, cd, 540, 560 + j * 200, max(0.05, min(1.05, k)), rx=lerp(25, 0, min(1, k)), alpha=min(1, k) * (1 - o), shadow=0.35)
    if i == 0 and t < 1.2:
        head = lerp(140, 940, eio(k01(t, 0.05, 1.1))); glow_line(c, [(140, 1420), (head, 1420)], width=10, col=P_["line"], head=(head, 1420))

def s_cta(c, t, i, chip):
    a = CUTS[i]; k = eo(k01(t, a, a + 0.6))
    lg = scaled(LOGO, 0.22); paste(c, fade(lg, k), 540 - lg.width / 2, 470)
    reveal(c, "Scrie în comentarii", F("s", 52), 540, 820, t, a + 0.15)
    kp = k01(t, a + 0.35, a + 0.8)
    if kp > 0:
        kw = CFG["kw"]; fnt = F("dk", 150); w = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textlength(kw, font=fnt)
        pim = Image.new("RGBA", (int(w + 140), 230), (0, 0, 0, 0)); ImageDraw.Draw(pim).rounded_rectangle([0, 0, pim.width - 1, 229], 64, fill=P_["acc"] + (255,))
        ImageDraw.Draw(pim).text((pim.width / 2, 118), kw, font=fnt, fill=P_["pill_fg"], anchor="mm")
        s = (0.55 + 0.45 * eback(kp, 1.8)) * (1 + 0.03 * math.sin((t - a) * 6)) * min(1, 900 / pim.width)
        paste(c, scaled(pim, s), 540 - pim.width * s / 2, 1040 - pim.height * s / 2)
    if chip: reveal(c, chip, F("m", 40), 540, 1220, t, a + 0.7, fill=P_["muted"])
    half = lerp(0, 330, eo(k01(t, a + 0.2, a + 0.9))); glow_line(c, [(540 - half, 1380), (540 + half, 1380)], width=8, col=P_["line"])

FN = {"title": s_title, "rows": s_rows, "phone": s_phone, "mic": s_mic, "barcode": s_barcode, "done": s_done, "field": s_field,
      "list": s_list, "bubble": s_bubble, "tour": s_tour, "stat": s_stat, "sync": s_sync, "moments": s_moments, "cta": s_cta}

def subtitles(c, t):
    for i, txt in enumerate(CFG["subs"]):
        a = P[i]; b = (P[i + 1] - 0.15) if i < 4 else VEND
        if a - 0.05 <= t < b + 0.25:
            k = eo(k01(t, a - 0.05, a + 0.2)) * (1 - eio(k01(t, b, b + 0.25)))
            im = text_img(txt, F("b", 48), (244, 246, 241))
            pad = Image.new("RGBA", (im.width + 40, im.height + 8), (0, 0, 0, 0))
            ImageDraw.Draw(pad).rounded_rectangle([0, 0, pad.width - 1, pad.height - 1], 36, fill=P_["sub_bg"]); pad.alpha_composite(im, (20, 4))
            if pad.width > 1000: pad = scaled(pad, 1000 / pad.width)
            paste(c, fade(pad, k), W / 2 - pad.width / 2, 1738 + (1 - k) * 12)

yy, xx = np.mgrid[0:H, 0:W]; rr = np.sqrt(((xx - W / 2) / (W * 0.95)) ** 2 + ((yy - H * 0.45) / (H * 0.8)) ** 2)
VIG = Image.fromarray(np.dstack([np.zeros((H, W), np.uint8)] * 3 + [(np.clip((rr - 0.42) / 0.6, 0, 1) ** 1.7 * P_["vig"]).astype(np.uint8)]), "RGBA")
WARM = Image.new("RGBA", (1700, 1700), P_["warm"][:3] + (0,)); ImageDraw.Draw(WARM).ellipse([420, 420, 1280, 1280], fill=P_["warm"]); WARM = WARM.filter(ImageFilter.GaussianBlur(220))

def frame(t):
    c = Image.new("RGBA", (W, H), P_["bg"] + (255,))
    paste(c, fade(WARM, 0.75 + 0.25 * math.sin(t * 2 * math.pi / 4)), 540 - 850, 860 - 850)
    for i, sc in enumerate(CFG["scenes"]):
        if CUTS[i] <= t < CUTS[i + 1] + 0.3:
            FN[sc[0]](c, t, i, *sc[1:])
    dx = 10 * math.sin(t * 0.7) + 6 * math.sin(t * 1.9); dy = 8 * math.cos(t * 0.55); rot = 0.35 * math.sin(t * 0.45); z = 1 + 0.015 * math.sin(t * 0.8)
    for hit, amp in [(0.2, 14), (CUTS[4] + 0.4, 8)]:
        if 0 <= t - hit < 0.35:
            e = (1 - (t - hit) / 0.35) ** 2; dx += amp * e * math.sin((t - hit) * 90); dy += amp * e * math.cos((t - hit) * 77)
    for cut in CUTS[1:5]: z *= 1 + 0.035 * math.sin(math.pi * k01(t, cut - 0.25, cut + 0.35))
    cs, sn = math.cos(math.radians(rot)), math.sin(math.radians(rot)); a, b, d_, e = cs / z, sn / z, -sn / z, cs / z; cx, cy = W / 2 + dx, H / 2 + dy
    c = c.transform((W, H), Image.AFFINE, (a, b, 540 - a * cx - b * cy, d_, e, 960 - d_ * cx - e * cy), Image.BILINEAR, fillcolor=P_["bg"] + (255,))
    subtitles(c, t); c.alpha_composite(VIG); c.alpha_composite(R.GRAIN[int(t * 60) % 8])
    if t < 0.05: c = Image.blend(Image.new("RGBA", (W, H), (0, 0, 0, 255)), c, t / 0.05)
    if t > DUR - 0.4: c = Image.blend(c, Image.new("RGBA", (W, H), P_["bg"] + (255,)), k01(t, DUR - 0.4, DUR))
    return c.convert("RGB")

def build_audio():
    AU.DUR = DUR; AU.N = int(AU.SR * DUR); N = AU.N; b = np.zeros((N, 2))
    AU.place(b, AU.whoosh(0.2, 1.4, rise=True), 0.0, 0.5); AU.place(b, AU.soft_impact(), 0.2, 0.6); AU.place(b, AU.sub_hit(), 0.2, 0.8); AU.place(b, AU.shards(), 0.2, 0.15)
    for cut in CUTS[1:5]: AU.place(b, AU.whoosh(0.5, 1.1), cut - 0.3, 0.35)
    for i, sc in enumerate(CFG["scenes"]):
        if sc[0] in ("rows", "moments", "list"): [AU.place(b, AU.pop(1000 + j * 120), CUTS[i] + 0.25 + j * 0.25, 0.18) for j in range(4)]
        if sc[0] == "done": AU.place(b, AU.success_chime(), CUTS[i] + 0.1, 0.2)
        if sc[0] in ("barcode",): AU.place(b, AU.scanner_beep(), CUTS[i] + 0.6, 0.15)
        if sc[0] == "tour": AU.place(b, AU.key_click(), CUTS[i] + 0.6, 0.35)
        if sc[0] == "stat": AU.place(b, AU.soft_impact(0.5), CUTS[i] + 0.1, 0.4)
    AU.place(b, AU.soft_impact(), CUTS[4] + 0.4, 0.5); AU.place(b, AU.sub_hit(1.4), CUTS[4] + 0.4, 0.7); AU.place(b, AU.success_chime(), CUTS[4] + 0.5, 0.12)
    m = AU.music(); v = np.zeros((N, 2)); AU.place(v, AU.load_mp3(os.path.join(HERE, CFG["mp3"])), VO, 1.0)
    vel = np.abs(v[:, 0]); kk = np.ones(int(0.12 * AU.SR)) / int(0.12 * AU.SR); duck = 1 - 0.5 * np.clip(np.convolve(vel, kk, "same") * 12, 0, 1)
    mix = (v * 0.95 + np.tanh(b * 1.2) * 0.75 * (0.6 + 0.4 * duck[:, None]) + m * 1.2 * duck[:, None]) * 0.7
    raw = os.path.join(HERE, f"{KEY}_mix_raw.wav"); AU.write(raw, mix); out = os.path.join(HERE, f"{KEY}_mix.wav")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", raw, "-af", "loudnorm=I=-14:TP=-1.0:LRA=9", "-ar", "48000", out], check=True); os.remove(raw)

if __name__ == "__main__":
    mode = sys.argv[2]
    if mode == "frames":
        for tp in [float(x) for x in sys.argv[3].split(",")]: frame(tp).save(os.path.join(HERE, f"{KEY}_f{tp:05.2f}.png"))
        print(KEY, "cuts", [round(x, 2) for x in CUTS])
    elif mode == "audio": build_audio()
    elif mode == "seg":
        i, n = int(sys.argv[3]), int(sys.argv[4]); fps = 60; N = int(round(DUR * fps)); a, b = N * i // n, N * (i + 1) // n
        ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1080x1920", "-r", str(fps), "-i", "-",
                               "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p", os.path.join(HERE, f"{KEY}_seg{i}.mp4")], stdin=subprocess.PIPE)
        for k in range(a, b): ff.stdin.write(frame(k / fps).tobytes())
        ff.stdin.close(); ff.wait()

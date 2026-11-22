"""Assemble 'AI video editor/export/Saptamana 1 (22-29 nov)': every post and reel in posting order,
each with a '- descriere.txt' note (day, time, keyword, ready-to-paste caption)."""
import json, os, shutil, subprocess, glob

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
X = os.path.join(REPO, "AI video editor", "export", "Saptamana 1 (22-29 nov)")
P = json.load(open(os.path.join(HERE, "posts.json"), encoding="utf-8"))
C = json.load(open(os.path.join(HERE, "captions.json"), encoding="utf-8"))
RC = json.load(open(os.path.join(HERE, "reel_captions.json"), encoding="utf-8"))
SPOT_CAP = open(os.path.join(REPO, "instagram", "spot", "descriere.txt"), encoding="utf-8").read().strip()
DESSERT_CAP = open(os.path.join(REPO, "instagram", "days", "2026-11-22", "descriere.txt"), encoding="utf-8").read().strip()

ORDER = [  # (kind, key, day, time, keyword, title)
    ("post_d22", None, "Duminica 22 nov", "19:00", "JURNAL", "CARUSEL Calorii prajituri"),
    ("post", "D22_P2", None, None, None, None),
    ("reel", "spot", "Luni 23 nov", "19:30", "JURNAL", "REEL Prezentare Jurnal Alimentar"),
    ("post", "L23_P1", None, None, None, None), ("post", "L23_P2", None, None, None, None),
    ("post", "Ma24_P1", None, None, None, None), ("post", "Ma24_P2", None, None, None, None),
    ("reel", "r25", "Miercuri 25 nov", "19:30", "PLAN", "REEL Plan calendar si bon"),
    ("post", "Mi25_P1", None, None, None, None), ("post", "Mi25_P2", None, None, None, None),
    ("post", "J26_P1", None, None, None, None), ("post", "J26_P2", None, None, None, None),
    ("reel", "r27", "Vineri 27 nov", "19:30", "ETICHETA", "REEL Polaroid eticheta"),
    ("post", "V27_P1", None, None, None, None), ("post", "V27_P2", None, None, None, None),
    ("post", "S28_P1", None, None, None, None), ("post", "S28_P2", None, None, None, None),
    ("reel", "r29", "Duminica 29 nov", "19:30", "JURNAL", "REEL Tendinta pe caiet"),
    ("post", "D29_P1", None, None, None, None), ("post", "D29_P2", None, None, None, None),
]

def note(path, day, time, kw, kind, caption, extra=""):
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"{day.upper()} · ora {time} · {kind} · cuvânt-cheie: {kw}\n\n{extra}DESCRIERE (copiaz-o în Instagram):\n\n{caption}\n")

def compress(src, dst):
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", src, "-c:v", "libx264", "-preset", "medium", "-crf", "23",
                    "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", dst], check=True)

if os.path.isdir(X): shutil.rmtree(X)
os.makedirs(X)
lines = []
for n, (kind, key, day, time, kw, title) in enumerate(ORDER, 1):
    if kind == "post":
        p = P[key]; day, time, kw, title = p["day"], p["time"], p["kw"], p["title"]
    name = f"{n:02d} - {day} - {title}"
    if kind in ("post", "post_d22"):
        src = sorted(glob.glob(os.path.join(HERE, "render", f"{key} - slide *.png"))) if kind == "post" else \
              sorted(glob.glob(os.path.join(REPO, "instagram", "days", "2026-11-22", "carusel3_render", "*.png")))
        multi = len(src) > 1
        for i, s in enumerate(src, 1):
            shutil.copy(s, os.path.join(X, f"{name} - slide {i}.png" if multi else f"{name}.png"))
        fmt = f"CARUSEL ({len(src)} slide-uri)" if multi else "IMAGINE"
        extra = f"Urcă slide 1 → {len(src)} în ordine, într-o singură postare.\n\n" if multi else ""
        cap = DESSERT_CAP if kind == "post_d22" else C[key]
        note(os.path.join(X, f"{name} - descriere.txt"), day, time, kw, fmt, cap, extra)
    else:
        src = os.path.join(REPO, "instagram", "spot", "out", "spot_1080x1920_60fps.mp4") if key == "spot" else os.path.join(HERE, "reels", f"{key}_v2.mp4")
        compress(src, os.path.join(X, f"{name}.mp4"))
        cap = SPOT_CAP if key == "spot" else RC[key.upper()]
        note(os.path.join(X, f"{name} - descriere.txt"), day, time, kw, "REEL 9:16, 60 fps, cu voce", cap)
    lines.append(f"  {n:02d}. {day}, {time}: {title} ({kw})")

with open(os.path.join(X, "00 - CITESTE-MA.txt"), "w", encoding="utf-8") as f:
    f.write("SĂPTĂMÂNA 1 · 22–29 noiembrie 2026\n\nÎn fiecare zi 2 postări, iar din 2 în 2 zile și un reel. Toate sunt gata.\n"
            "Lângă fiecare material e un fișier „- descriere.txt” cu ziua, ora, cuvântul-cheie și descrierea gata de copiat.\n\n"
            + "\n".join(lines) + "\n\nCuvinte-cheie cu răspuns automat în DM: JURNAL, PLAN, ETICHETA, POZA.\n")
print("ok", len(ORDER), X)

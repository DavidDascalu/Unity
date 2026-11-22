"""Assemble weeks 2 and 3 into 'AI video editor/export/', posting order, each with a '- descriere.txt' note."""
import json, os, shutil, subprocess, glob
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
P = json.load(open(os.path.join(HERE, "posts.json"), encoding="utf-8")); C = json.load(open(os.path.join(HERE, "captions.json"), encoding="utf-8"))
RC = json.load(open(os.path.join(HERE, "reel_captions.json"), encoding="utf-8"))
REEL = {"x1": ("Marti 1 dec", "JURNAL", "REEL Chat cu vocea"), "x2": ("Joi 3 dec", "ETICHETA", "REEL Scan cod de bare"),
        "x3": ("Sambata 5 dec", "PLAN", "REEL Buget kinetic"), "x4": ("Luni 7 dec", "JURNAL", "REEL Nuti pe ecran real"),
        "x5": ("Miercuri 9 dec", "JURNAL", "REEL Gratuit vs Premium split"), "x6": ("Vineri 11 dec", "JURNAL", "REEL POV telefon si laptop"),
        "x7": ("Duminica 13 dec", "JURNAL", "REEL O zi in timelapse")}
WEEKS = {"Saptamana 2 (30 nov-6 dec)": ["L30_P1", "L30_P2", "Ma1_P1", "Ma1_P2", "x1", "Mi2_P1", "Mi2_P2", "J3_P1", "J3_P2", "x2",
                                        "V4_P1", "V4_P2", "S5_P1", "S5_P2", "x3", "D6_P1", "D6_P2"],
         "Saptamana 3 (7-13 dec)": ["L7_P1", "L7_P2", "x4", "Ma8_P1", "Ma8_P2", "Mi9_P1", "Mi9_P2", "x5", "J10_P1", "J10_P2",
                                    "V11_P1", "V11_P2", "x6", "S12_P1", "S12_P2", "D13_P1", "D13_P2", "x7"]}
def note(path, day, time, kw, kind, cap, extra=""):
    open(path, "w", encoding="utf-8").write(f"{day.upper()} · ora {time} · {kind}" + (f" · cuvânt-cheie: {kw}" if kw else "") + f"\n\n{extra}DESCRIERE (copiaz-o în Instagram):\n\n{cap}\n")
for wk, keys in WEEKS.items():
    X = os.path.join(REPO, "AI video editor", "export", wk)
    if os.path.isdir(X): shutil.rmtree(X)
    os.makedirs(X); lines = []
    for n, k in enumerate(keys, 1):
        if k.startswith("x"):
            day, kw, title = REEL[k]; time = "19:30"; name = f"{n:02d} - {day} - {title}"
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", os.path.join(HERE, "reels", f"{k}.mp4"), "-c:v", "libx264", "-preset", "medium", "-crf", "23",
                            "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", os.path.join(X, name + ".mp4")], check=True)
            note(os.path.join(X, name + " - descriere.txt"), day, time, kw, "REEL 9:16, 60 fps, cu voce", RC[k])
        else:
            p = P[k]; day, time, kw, title = p["day"], p["time"], p["kw"], p["title"]; name = f"{n:02d} - {day} - {title}"
            src = sorted(glob.glob(os.path.join(HERE, "render", f"{k} - slide *.png"))); multi = len(src) > 1
            for i, s in enumerate(src, 1): shutil.copy(s, os.path.join(X, f"{name} - slide {i}.png" if multi else f"{name}.png"))
            note(os.path.join(X, name + " - descriere.txt"), day, time, kw, f"CARUSEL ({len(src)} slide-uri)" if multi else "IMAGINE", C[k],
                 f"Urcă slide 1 → {len(src)} în ordine, într-o singură postare.\n\n" if multi else "")
        lines.append(f"  {n:02d}. {day}, {time}: {title}" + (f" ({kw})" if kw else ""))
    open(os.path.join(X, "00 - CITESTE-MA.txt"), "w", encoding="utf-8").write(
        f"{wk.upper()}\n\nÎn fiecare zi 2 postări, iar din 2 în 2 zile și un reel. Toate sunt gata.\nLângă fiecare material e un fișier „- descriere.txt” cu ziua, ora, cuvântul-cheie și descrierea.\n\n"
        + "\n".join(lines) + "\n\nCuvinte-cheie cu răspuns automat în DM: JURNAL, PLAN, ETICHETA, IDEI.\n")
    print(wk, len(keys))

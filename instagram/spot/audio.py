"""Phase 3: voice track, synthesized SFX and ambient music for the 'Alimentație cu ritm' spot.

All sound effects and music are synthesized here with numpy (no sample library).
Every cue time comes from CUES below, which the renderer will share, so picture and sound
stay locked to the same beat sheet.

    python3 audio.py   -> audio/voice.wav, audio/sfx.wav, audio/music.wav, audio/mix.wav (48 kHz)
"""
import json, os, subprocess, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
A = os.path.join(HERE, "audio")
SR = 48000
DUR = 21.2
N = int(SR * DUR)
rng = np.random.default_rng(2026)

# ---------------- beat sheet (seconds) ----------------
VOICE = [  # file, time the first word starts
    ("1_ce_mananci_B.mp3", 2.50), ("2_scanezi_A.mp3", 5.00), ("3_fiecare_A.mp3", 8.00),
    ("4_un_pas_A.mp3", 12.20), ("5_alimentatie_A.mp3", 17.60)]
CUES = {
    "line_in": 0.00, "impact": 0.17, "logo_rest": 1.40,
    "phone_land": 2.40, "type": [2.55, 2.70, 2.86, 3.02, 3.18], "autocomplete": [2.80, 3.10, 3.30],
    "cards": [3.40 + i * 0.194 for i in range(6)], "outline_card1": 4.45,
    "cam_scan": 4.80, "shutter": 5.15, "laser": [5.30, 5.95], "extract": [5.45, 5.60, 5.75, 5.90, 6.00],
    "tap_add": 6.03, "added": 6.12, "through_screen": 7.05,
    "rings": [7.40, 9.20], "kcal_ticks": [7.45 + i * 0.09 for i in range(18)], "glass_card": 9.10, "dive": 9.70,
    "kitchen": 10.00, "plate_orbit": [10.40, 11.40], "plate_settle": 12.00, "notification": 12.60,
    "calendar": 13.30, "days": [13.70 + i * 0.075 for i in range(21)], "curve": [15.40, 17.00],
    "line_return": 17.50, "final_hit": 17.90, "end_card": 19.20,
}

def ensure_dir(): os.makedirs(A, exist_ok=True)

def load_mp3(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()

def onset(x, thr=10 ** (-38 / 20)):
    idx = np.where(np.abs(x) > thr)[0]
    return idx[0] / SR if len(idx) else 0.0

def write(path, x):
    x = np.asarray(x, np.float32)
    if x.ndim == 1: x = np.stack([x, x], 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())

def place(buf, sig, t, gain=1.0, pan=0.0):
    i = int(t * SR)
    if i >= len(buf): return
    j = min(len(buf), i + len(sig))
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    buf[i:j, 0] += sig[:j - i] * gain * l * 1.414
    buf[i:j, 1] += sig[:j - i] * gain * r * 1.414

def t_(d): return np.arange(int(d * SR)) / SR
def env(d, a=0.005, r=None):
    x = t_(d); r = r or d
    return np.minimum(1, x / a) * np.exp(-x / max(r, 1e-4) * 5)
def lp(x, k=40):
    ker = np.exp(-np.arange(k * 4) / k); ker /= ker.sum(); return np.convolve(x, ker, "same")
def hp(x): return np.diff(x, prepend=0)

# ---------------- SFX ----------------
def whoosh(d=0.6, bright=1.0, rise=False):
    x = t_(d); n = rng.standard_normal(len(x))
    shape = np.sin(np.pi * x / d) ** 2 if not rise else (x / d) ** 2.2 * np.minimum(1, (d - x) / 0.04)
    k = int(60 / bright); s = lp(n, k) - lp(n, k * 6)
    return s / (np.abs(s).max() + 1e-9) * shape

def sub_hit(d=1.2):
    x = t_(d); f = 38 + 70 * np.exp(-x * 14)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 3.2)

def soft_impact(d=0.9):
    x = t_(d); body = np.sin(2 * np.pi * np.cumsum(90 + 120 * np.exp(-x * 30)) / SR) * np.exp(-x * 9)
    n = lp(rng.standard_normal(len(x)), 6) * np.exp(-x * 30) * 0.6
    return body + n

def shards(d=0.9, count=14):
    out = np.zeros(int(d * SR))
    for _ in range(count):
        st = rng.uniform(0, d * 0.6); f = rng.uniform(2800, 6500); L = int(rng.uniform(0.08, 0.3) * SR)
        x = np.arange(L) / SR; s = np.sin(2 * np.pi * f * x) * np.exp(-x * 18) * rng.uniform(0.2, 0.6)
        i = int(st * SR); out[i:i + L] += s[:len(out) - i]
    return out

def tick(f=2200, d=0.03):
    x = t_(d); return np.sin(2 * np.pi * f * x) * np.exp(-x * 160) + 0.3 * hp(rng.standard_normal(len(x))) * np.exp(-x * 300)

def key_click():
    x = t_(0.05); n = hp(rng.standard_normal(len(x))) * np.exp(-x * 220)
    return n * 0.8 + np.sin(2 * np.pi * 1300 * x) * np.exp(-x * 120) * 0.3

def pop(f=900):
    x = t_(0.09); return np.sin(2 * np.pi * (f + 900 * np.exp(-x * 60)) * x) * np.exp(-x * 45)

def shutter():
    a = hp(rng.standard_normal(int(0.03 * SR))) * np.exp(-t_(0.03) * 120)
    b = hp(rng.standard_normal(int(0.05 * SR))) * np.exp(-t_(0.05) * 90)
    out = np.zeros(int(0.12 * SR)); out[:len(a)] += a; out[int(0.06 * SR):int(0.06 * SR) + len(b)] += b * 0.8
    return out

def scanner_beep():
    x = t_(0.16); return np.sin(2 * np.pi * 1760 * x) * np.minimum(1, x / 0.005) * np.minimum(1, (0.16 - x) / 0.02)

def laser_hum(d):
    x = t_(d); f = 420 + 380 * (x / d)
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.4 + 0.2 * np.sin(2 * np.pi * np.cumsum(f * 2.01) / SR)) * np.sin(np.pi * x / d) ** 1.5

def success_chime():
    out = np.zeros(int(0.9 * SR))
    for i, f in enumerate([880.0, 1318.5]):
        x = t_(0.7); s = (np.sin(2 * np.pi * f * x) + 0.25 * np.sin(4 * np.pi * f * x)) * np.exp(-x * 5)
        j = int(i * 0.11 * SR); out[j:j + len(s)] += s
    return out

def ring_tone(d):
    x = t_(d); f = 220 * 2 ** (x / d)                         # one octave up as the rings fill
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.3 * np.sin(2 * np.pi * np.cumsum(f * 1.5) / SR)) * np.sin(np.pi * x / d) ** 2

def wood_knock():
    x = t_(0.25); s = sum(np.sin(2 * np.pi * f * x) * np.exp(-x * dmp) for f, dmp in [(180, 28), (420, 40), (760, 55)])
    return s + lp(rng.standard_normal(len(x)), 4) * np.exp(-x * 60) * 0.5

def ceramic_ring():
    x = t_(1.4); return sum(np.sin(2 * np.pi * f * x) * np.exp(-x * dmp) * g for f, dmp, g in
                             [(1840, 3.5, 0.5), (2710, 4.5, 0.35), (4120, 6, 0.2), (5590, 8, 0.12)])

def notif_ping():
    out = np.zeros(int(0.8 * SR))
    for i, f in enumerate([1174.7, 1568.0]):
        x = t_(0.6); s = np.sin(2 * np.pi * f * x) * np.exp(-x * 7); j = int(i * 0.09 * SR); out[j:j + len(s)] += s
    return out

def room_tone(d):
    n = rng.standard_normal(int(d * SR)); return (lp(n, 400) - lp(n, 3000)) * 4

def sfx_bus():
    b = np.zeros((N, 2)); C = CUES
    place(b, whoosh(0.2, 1.4, rise=True), 0.0, 0.5)
    place(b, soft_impact(), C["impact"], 0.7); place(b, sub_hit(), C["impact"], 0.9); place(b, shards(), C["impact"], 0.18)
    place(b, whoosh(1.1, 0.8), 0.25, 0.22, pan=-0.4)                         # line runs left -> right
    place(b, whoosh(0.4), C["phone_land"] - 0.35, 0.35); place(b, soft_impact(0.5), C["phone_land"], 0.45)
    for t in C["type"]: place(b, key_click(), t, 0.35)
    for t in C["autocomplete"]: place(b, pop(1100), t, 0.18)
    for i, t in enumerate(C["cards"]): place(b, whoosh(0.28, 1.6), t, 0.18, pan=-0.6 + i * 0.24)
    place(b, shards(0.5, 6), C["outline_card1"], 0.1)
    place(b, whoosh(0.6, 0.9), C["cam_scan"] - 0.3, 0.3)
    place(b, shutter(), C["shutter"], 0.45)
    place(b, scanner_beep(), C["laser"][0], 0.16); place(b, laser_hum(C["laser"][1] - C["laser"][0]), C["laser"][0], 0.12)
    for t in C["extract"]: place(b, tick(2600), t, 0.25)
    place(b, key_click(), C["tap_add"], 0.5); place(b, success_chime(), C["added"], 0.22)
    place(b, whoosh(0.5, 1.2), C["through_screen"] - 0.25, 0.4)
    place(b, ring_tone(C["rings"][1] - C["rings"][0]), C["rings"][0], 0.06)
    for t in C["kcal_ticks"]: place(b, tick(3000, 0.02), t, 0.08)
    place(b, whoosh(0.5, 1.8), C["glass_card"], 0.15)
    place(b, whoosh(0.8, 0.6), C["dive"] - 0.2, 0.35)
    place(b, room_tone(C["calendar"] - C["kitchen"]) * np.sin(np.linspace(0, np.pi, int((C["calendar"] - C["kitchen"]) * SR)))[:],
          C["kitchen"], 0.05)
    place(b, whoosh(1.0, 1.0), C["plate_orbit"][0], 0.2, pan=0.3)
    place(b, wood_knock(), C["plate_settle"], 0.55); place(b, ceramic_ring(), C["plate_settle"] + 0.01, 0.12)
    place(b, notif_ping(), C["notification"], 0.2)
    place(b, whoosh(0.6, 0.9), C["calendar"] - 0.3, 0.3)
    for i, t in enumerate(C["days"]): place(b, tick(1900 + i * 40, 0.025), t, 0.1, pan=-0.5 + (i % 7) / 6)
    place(b, whoosh(C["curve"][1] - C["curve"][0], 2.2) * 0.6, C["curve"][0], 0.15)
    place(b, whoosh(0.4, 1.1, rise=True), C["line_return"], 0.4)
    place(b, soft_impact(), C["final_hit"], 0.6); place(b, sub_hit(1.6), C["final_hit"], 0.85); place(b, shards(1.2, 10), C["final_hit"], 0.12)
    place(b, success_chime(), C["end_card"] + 0.05, 0.1)
    return b

# ---------------- music: ambient pad with a slow pulse ----------------
def music():
    b = np.zeros((N, 2))
    chords = [[110.0, 164.81, 220.0, 277.18], [92.5, 138.59, 185.0, 220.0], [98.0, 146.83, 196.0, 246.94], [82.41, 123.47, 164.81, 207.65]]
    seg = 5.3
    for ci in range(5):
        ch = chords[ci % 4]; a = ci * seg; d = seg + 2.0; x = t_(d)
        e = np.minimum(1, x / 1.8) * np.minimum(1, np.maximum(0, (d - x) / 2.0))
        for k, f in enumerate(ch):
            for det, pan in [(0.997, -0.5), (1.003, 0.5)]:
                s = np.sin(2 * np.pi * f * det * x + 0.4 * np.sin(2 * np.pi * 0.13 * x + k)) * e
                place(b, s, a, 0.018, pan)
    # slow pulse (the "rhythm"): soft low thump every 0.75 s, from the phone landing to the final hit
    for t in np.arange(2.40, 17.9, 0.75):
        x = t_(0.5); s = np.sin(2 * np.pi * (52 + 30 * np.exp(-x * 20)) * x) * np.exp(-x * 9)
        place(b, s, t, 0.12)
    # swell under the end card
    x = t_(2.2); place(b, (np.sin(2 * np.pi * 220 * x) + np.sin(2 * np.pi * 330 * x)) * np.sin(np.pi * x / 2.2) ** 2, 19.0, 0.02)
    fade = np.minimum(1, np.arange(N) / (0.4 * SR)) * np.minimum(1, (N - np.arange(N)) / (1.0 * SR))
    return b * fade[:, None]

def voice_track():
    b = np.zeros((N, 2)); info = []
    for f, t in VOICE:
        x = load_mp3(os.path.join(A, "voice", f)); o = onset(x)
        place(b, x, t - o, 1.0); info.append({"file": f, "word_start": t, "placed_at": round(t - o, 3), "dur": round(len(x) / SR, 3)})
    return b, info

if __name__ == "__main__":
    ensure_dir()
    v, info = voice_track(); s = sfx_bus(); m = music()
    write(os.path.join(A, "voice.wav"), v * 0.95)
    write(os.path.join(A, "sfx.wav"), np.tanh(s * 1.2) * 0.9)
    write(os.path.join(A, "music.wav"), m)
    # ducking: music and quiet SFX dip 6 dB under the voice
    vel = np.abs(v[:, 0]); k = np.ones(int(0.12 * SR)) / int(0.12 * SR)
    duck = 1 - 0.5 * np.clip(np.convolve(vel, k, "same") * 12, 0, 1)
    mix = v * 0.95 + np.tanh(s * 1.2) * 0.75 * (0.6 + 0.4 * duck[:, None]) + m * 1.2 * duck[:, None]
    write(os.path.join(A, "mix_raw.wav"), mix * 0.7)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", os.path.join(A, "mix_raw.wav"),
                    "-af", "loudnorm=I=-14:TP=-1.0:LRA=9", "-ar", str(SR), os.path.join(A, "mix.wav")], check=True)
    json.dump({"voice": info, "cues": CUES, "duration": DUR}, open(os.path.join(A, "cues.json"), "w"), indent=1, ensure_ascii=False)
    print(json.dumps(info, ensure_ascii=False, indent=1))

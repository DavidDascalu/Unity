import sys, subprocess, os
sys.argv = [sys.argv[0]] + sys.argv[1:]
import render as R
from PIL import Image
i, n = int(sys.argv[1]), int(sys.argv[2]); fps = 60
N = int(round(R.DUR * fps)); a, b = N * i // n, N * (i + 1) // n
out = os.path.join(R.OUT, f"seg_{i}.mp4")
ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1080x1920", "-r", str(fps), "-i", "-",
                       "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
for k in range(a, b): ff.stdin.write(R.frame(k / fps).tobytes())
ff.stdin.close(); ff.wait(); print("seg", i, a, b)

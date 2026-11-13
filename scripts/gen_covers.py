# scripts/gen_covers.py —— 生成 12 张低饱和渐变封面（SVG，离线可用）
import os

PALETTE = [
    ("#1a1620", "#2e2436"), ("#171b20", "#24303a"), ("#1d1618", "#3a2628"),
    ("#16191a", "#26322f"), ("#1a1720", "#33283a"), ("#1c1a16", "#3a3226"),
    ("#161a1d", "#23323a"), ("#1d171c", "#382a33"), ("#171a18", "#26332c"),
    ("#1a1816", "#342e24"), ("#18171d", "#2c2836"), ("#17191b", "#262e34"),
]

TPL = """<svg xmlns="http://www.w3.org/2000/svg" width="800" height="450" viewBox="0 0 800 450">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{a}"/>
      <stop offset="100%" stop-color="{b}"/>
    </linearGradient>
    <radialGradient id="r" cx="0.72" cy="0.28" r="0.62">
      <stop offset="0%" stop-color="#c9b8e8" stop-opacity="0.16"/>
      <stop offset="100%" stop-color="#c9b8e8" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="800" height="450" fill="url(#g)"/>
  <rect width="800" height="450" fill="url(#r)"/>
  <circle cx="612" cy="126" r="88" fill="none" stroke="#c9b8e8" stroke-opacity="0.14" stroke-width="1"/>
  <circle cx="612" cy="126" r="132" fill="none" stroke="#c9b8e8" stroke-opacity="0.08" stroke-width="1"/>
  <path d="M120 330 Q220 240 320 330 T520 330" fill="none" stroke="#e6e1ee" stroke-opacity="0.10" stroke-width="2"/>
  <rect x="48" y="48" width="10" height="10" fill="#9d8cc4" fill-opacity="0.55" transform="rotate(45 53 53)"/>
  <text x="48" y="412" font-family="monospace" font-size="15" fill="#e6e1ee" fill-opacity="0.22" letter-spacing="3">STRAY CAT</text>
  <text x="700" y="412" font-family="monospace" font-size="15" fill="#e6e1ee" fill-opacity="0.22">{n:02d}</text>
</svg>
"""

out = os.path.join("web", "public", "covers")
os.makedirs(out, exist_ok=True)
for i, (a, b) in enumerate(PALETTE, start=1):
    with open(os.path.join(out, f"c{i}.svg"), "w", encoding="utf-8") as f:
        f.write(TPL.format(a=a, b=b, n=i))
print(f"生成 {len(PALETTE)} 张封面 -> {out}")
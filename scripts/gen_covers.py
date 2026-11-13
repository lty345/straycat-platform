# scripts/gen_covers.py -- 12 张几何线条猫封面（矢量、离线、风格统一）
import os

PALETTE = [
    ('#1a1620', '#2e2436'), ('#171b20', '#24303a'), ('#1d1618', '#3a2628'),
    ('#16191a', '#26322f'), ('#1a1720', '#33283a'), ('#1c1a16', '#3a3226'),
    ('#161a1d', '#23323a'), ('#1d171c', '#382a33'), ('#171a18', '#26332c'),
    ('#1a1816', '#342e24'), ('#18171d', '#2c2836'), ('#17191b', '#262e34'),
]
# 每张的微调：横向位置 / 缩放 / 旋转，避免 12 张一模一样
TWEAK = [
    (400, 1.00, 0), (372, 0.94, -3), (428, 1.05, 2), (390, 0.97, -2),
    (412, 1.02, 3), (378, 0.92, 1), (420, 1.04, -1), (396, 0.99, 2),
    (406, 1.01, -3), (384, 0.95, 3), (416, 1.03, -2), (398, 0.98, 1),
]

TPL = '''<svg xmlns="http://www.w3.org/2000/svg" width="800" height="450" viewBox="0 0 800 450">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{c1}"/><stop offset="100%" stop-color="{c2}"/>
    </linearGradient>
    <radialGradient id="glow" cx="0.68" cy="0.32" r="0.62">
      <stop offset="0%" stop-color="#c9b8e8" stop-opacity="0.16"/>
      <stop offset="100%" stop-color="#c9b8e8" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="800" height="450" fill="url(#bg)"/>
  <rect width="800" height="450" fill="url(#glow)"/>
  <circle cx="612" cy="120" r="96" fill="none" stroke="#c9b8e8" stroke-opacity="0.10"/>
  <circle cx="612" cy="120" r="142" fill="none" stroke="#c9b8e8" stroke-opacity="0.05"/>
  <g transform="translate({x},150) scale({s}) rotate({r})" fill="none" stroke="#e6e1ee"
     stroke-width="2.2" stroke-opacity="0.60" stroke-linecap="round" stroke-linejoin="round">
    <path d="M-44 -14 L-57 -53 L-22 -38"/>
    <path d="M44 -14 L57 -53 L22 -38"/>
    <circle cx="0" cy="0" r="46"/>
    <path d="M-46 18 C-58 90 -40 132 0 132 C40 132 58 90 46 18"/>
    <path d="M40 116 C88 122 106 90 92 60"/>
    <path d="M-19 1 q7 -9 13 0"/>
    <path d="M6 1 q7 -9 13 0"/>
    <path d="M-4 14 l4 5 l4 -5"/>
    <path d="M-30 16 L-58 11 M-30 23 L-58 27"/>
    <path d="M30 16 L58 11 M30 23 L58 27"/>
  </g>
  <rect x="48" y="48" width="9" height="9" fill="#9d8cc4" fill-opacity="0.5" transform="rotate(45 52 52)"/>
  <text x="48" y="414" font-family="monospace" font-size="13" fill="#e6e1ee" fill-opacity="0.20" letter-spacing="3">STRAY CAT</text>
  <text x="716" y="414" font-family="monospace" font-size="13" fill="#e6e1ee" fill-opacity="0.20">{n:02d}</text>
</svg>
'''

out = os.path.join('web', 'public', 'covers')
os.makedirs(out, exist_ok=True)
for i, ((c1, c2), (x, s, r)) in enumerate(zip(PALETTE, TWEAK), start=1):
    with open(os.path.join(out, 'c%d.svg' % i), 'w', encoding='utf-8') as f:
        f.write(TPL.format(c1=c1, c2=c2, x=x, s=s, r=r, n=i))
print('已生成 %d 张几何猫封面 -> %s' % (len(PALETTE), out))
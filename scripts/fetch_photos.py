# scripts/fetch_photos.py -- 从 cataas.com 抓真实猫照片（免费 API，无需 key）
# 用途：给 24 篇内容各配一张真实照片，裁成 800x450 (16:9) 存到 web/public/covers/
# 说明：cataas 是社区猫图池，图片可自由使用；出处见生成的 ATTRIBUTIONS.md
import json
import os
import urllib.parse
import urllib.request
from io import BytesIO

from PIL import Image

BASE = 'https://cataas.com'
OUT = os.path.join('web', 'public', 'covers')
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
SIZE = (800, 450)

# 想优先匹配的标签（按 SEED 顺序 24 篇）
WANT = [
    'orange', 'kitten', 'cute', 'tabby', 'sleepy', 'cat',
    'cute', 'orange', 'kitten', 'cute', 'tabby', 'black',
    'cat', 'cute', 'sleepy', 'cute', 'box', 'tabby',
    'cute', 'kitten', 'sleepy', 'box', 'cute', 'tabby',
]


def fetch(url, timeout=25):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def api_cats(tag=None, limit=30):
    q = '%s/api/cats?limit=%d' % (BASE, limit)
    if tag:
        q += '&tags=' + urllib.parse.quote(tag)
    try:
        return json.loads(fetch(q).decode('utf-8'))
    except Exception as e:
        print('  api fail [%s]: %s' % (tag, e))
        return []


def crop_169(data):
    img = Image.open(BytesIO(data)).convert('RGB')
    w, h = img.size
    target = SIZE[0] / SIZE[1]
    if w / h > target:
        nw = int(h * target)
        img = img.crop(((w - nw) // 2, 0, (w + nw) // 2, h))
    else:
        nh = int(w / target)
        img = img.crop((0, (h - nh) // 2, w, (h + nh) // 2))
    return img.resize(SIZE, Image.LANCZOS)


def main():
    os.makedirs(OUT, exist_ok=True)
    pool = []
    seen = set()
    for tag in ['orange', 'kitten', 'cute', 'tabby', 'black', 'sleepy', 'box', None]:
        for it in api_cats(tag):
            if it['id'] in seen:
                continue
            seen.add(it['id'])
            pool.append(it)
        print('  池子累计 %d 张（刚抓 tag=%s）' % (len(pool), tag))
        if len(pool) >= 80:
            break

    ok = 0
    lines = []
    for i in range(24):
        want = WANT[i] if i < len(WANT) else None
        cand = [x for x in pool if want and want in (x.get('tags') or [])]
        if not cand:
            cand = pool
        if not cand:
            print('  [%02d] 没有候选了' % (i + 1))
            continue
        it = cand[i % len(cand)] if len(cand) > 1 else cand[0]
        pool.remove(it)
        url = '%s/cat/%s' % (BASE, it['id'])
        try:
            img = crop_169(fetch(url))
            path = os.path.join(OUT, 'p%02d.jpg' % (i + 1))
            img.save(path, 'JPEG', quality=86, optimize=True)
            ok += 1
            tags = ','.join(it.get('tags') or [])
            lines.append('| p%02d.jpg | %s/cat/%s | tags: %s |' % (i + 1, BASE, it['id'], tags or '-'))
            print('  [%02d] ok  %-22s tags=%s' % (i + 1, it['id'], tags[:30]))
        except Exception as e:
            print('  [%02d] 下载失败 %s' % (i + 1, e))

    with open(os.path.join(OUT, 'ATTRIBUTIONS.md'), 'w', encoding='utf-8') as f:
        f.write('# 图片来源\n\n')
        f.write('全部图片来自 [cataas.com](https://cataas.com)（Cat as a Service），\n')
        f.write('免费猫图 API，无需授权密钥。若用于公开项目请自行确认许可。\n\n')
        f.write('| 文件 | 原始地址 | 标签 |\n|---|---|---|\n')
        f.write('\n'.join(lines) + '\n')
    print('\n完成 %d/24 张 -> %s' % (ok, OUT))


if __name__ == '__main__':
    main()
#!/usr/bin/env python3
"""抓取 yurinavi feed 中每篇文章的 og:image，存到 feed/images/，并生成 images.json。"""
import hashlib
import json
import os
import re
import time
import urllib.request

FEED = 'feed/yurinavi.xml'
IMG_DIR = 'feed/images'
OUT = 'feed/images.json'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36'
MAX_ITEMS = 20
MAX_BYTES = 2_000_000
KEEP_DAYS = 14
REPO_SLUG = 'wxhbd/yuri-feed'


def fetch(url, timeout=25):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def main():
    if not os.path.exists(FEED):
        print('feed not found:', FEED)
        return
    xml = open(FEED, encoding='utf-8', errors='replace').read()
    links = re.findall(r'<link>(https://yurinavi\.com/[^<]+)</link>', xml)
    # 去重保序
    seen = set()
    links = [l for l in links if not (l in seen or seen.add(l))][:MAX_ITEMS]
    os.makedirs(IMG_DIR, exist_ok=True)

    mapping = {}
    for link in links:
        h = hashlib.sha1(link.encode()).hexdigest()[:16]
        path = os.path.join(IMG_DIR, h + '.jpg')
        mapping[link] = f'https://cdn.jsdelivr.net/gh/{REPO_SLUG}@main/feed/images/{h}.jpg'
        if os.path.exists(path):
            continue
        try:
            html = fetch(link).decode('utf-8', 'replace')
            m = re.search(r'property="og:image"\s+content="([^"]+)"', html)
            if not m:
                m = re.search(r'content="([^"]+)"\s+property="og:image"', html)
            if not m:
                print('no-og', link)
                continue
            data = fetch(m.group(1))
            if len(data) > MAX_BYTES:
                print('too-big', link, len(data))
                continue
            open(path, 'wb').write(data)
            print('ok', h, len(data))
            time.sleep(0.6)
        except Exception as e:
            print('fail', link, e)

    json.dump(mapping, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

    # 清理过期图片
    cutoff = time.time() - KEEP_DAYS * 86400
    for name in os.listdir(IMG_DIR):
        p = os.path.join(IMG_DIR, name)
        try:
            if os.path.getmtime(p) < cutoff:
                os.remove(p)
        except OSError:
            pass

    print('images.json 条目:', len(mapping))


if __name__ == '__main__':
    main()

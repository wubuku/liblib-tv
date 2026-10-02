"""站点链接体检：把源 Markdown 里的每个站内链接，对照构建产物的实际 id 逐个核。

⭐ 为什么单独写一个：`build-site.sh` 的「产物无死链」**只校验目标文件存在**，
   **完全不校验 `#锚点`**。本脚本用构建产物里的真实 `id="..."` 反查，
   专门抓「标题改过、链接没跟着改」这一类。

用法：先 `./build-site.sh`，再 `python3 tools/link-audit.py`。
"""
import glob
import os
import posixpath
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 手册根，不是 tools/
os.chdir(ROOT)

DIST = '.vitepress/dist'
if not os.path.isdir(DIST):
    sys.exit('先跑 ./build-site.sh')

ids = {}
for f in glob.glob(DIST + '/**/*.html', recursive=True):
    ids[f.split(DIST + '/', 1)[1]] = set(re.findall(r'id="([^"]+)"', open(f, encoding='utf-8').read()))

LINK = re.compile(r'\]\(([^)\s]+\.md)#([^)]+)\)')
bad = []
total = 0
for f in sorted(glob.glob('10-tasks/*.md') + glob.glob('*.md')):
    base = f.rsplit('/', 1)[0] if '/' in f else ''
    for m in LINK.finditer(open(f, encoding='utf-8').read()):
        total += 1
        target, frag = m.group(1), m.group(2)
        key = posixpath.normpath(posixpath.join(base, target)).replace('.md', '.html')
        if key not in ids:
            bad.append((f, target + '#' + frag, '目标页不存在（解析成 ' + key + '）'))
        elif frag not in ids[key]:
            near = [i for i in ids[key] if frag[:5] and frag[:5] in i]
            bad.append((f, target + '#' + frag, '锚点失效；近似 id: ' + str(near[:3])))

print('站点链接体检：共 %d 条锚点链接，失效 %d 条' % (total, len(bad)))
for b in bad:
    print('  x %s -> %s | %s' % b)
sys.exit(1 if bad else 0)

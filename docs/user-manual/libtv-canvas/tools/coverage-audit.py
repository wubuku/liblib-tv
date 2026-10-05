#!/usr/bin/env python3
"""手册覆盖体检：把 task-inventory.yml 的每个任务，跟它挂的页面、实际字数、截图数对上。

为什么要有这个脚本（缺陷 455）：
`AUDIT.md` 里堆着四批生成历史面板的实点读数，`10-tasks/` 却没有一页讲它、零截图 ——
**内部审计比用户手册记得细**，而这件事在看 manifest 和页面的时候完全看不出来。
⇒ 这里定期算一张表：**哪个任务的「页面 / 字数 / 截图」是偏低的**，好排下一批写什么。

⛔ 本脚本只读：只解析 yml / md / manifest，不改任何文件。
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CJK = re.compile(r'[\u3000-\u303f\u4e00-\u9fff\uff00-\uffef]')
IMG = re.compile(r'!\[[^\]]*\]\(([^)]+)\)')


def 正文长度(md):
    """粗略去掉代码块与表格分隔线之后的字数。"""
    txt = md
    txt = re.sub(r'```.*?```', '', txt, flags=re.S)
    return len(CJK.findall(txt))


def 读(p):
    with open(os.path.join(ROOT, p), encoding='utf-8') as f:
        return f.read()


def main():
    inv = 读('task-inventory.yml')
    manifest = 读('screenshots/manifest.yml')

    # manifest 里 task_id -> 图片数
    桶 = {}
    for m in re.finditer(r'- file: (\S+)\n\s+task_id: (\S+)', manifest):
        桶[m.group(2)] = 桶.get(m.group(2), 0) + 1

    # 解析任务块
    块 = re.split(r'\n  - id: ', inv)[1:]
    行 = []
    for b in 块:
        tid = b.split('\n', 1)[0].strip()
        def 取(键):
            m = re.search(r'^\s+%s:\s*(.+)$' % 键, b, re.M)
            return m.group(1).strip() if m else ''
        标题 = 取('title').strip("'\"")
        状态 = 取('status')
        频次 = 取('frequency')
        mp = re.findall(r'^\s+- (\S+\.md)\s*$', b, re.M)
        字 = 0
        图 = 0
        存在的 = []
        for p in mp:
            full = os.path.join(ROOT, p)
            if not os.path.exists(full):
                存在的.append(p + '⛔缺文件')
                continue
            存在的.append(p)
            md = 读(p)
            字 += 正文长度(md)
            图 += len(IMG.findall(md))
        行.append({
            'id': tid, '标题': 标题, '状态': 状态, '频次': 频次,
            '页数': len(存在的), '页': 存在的, '字数': 字, '图数': 图,
            '清单图': 桶.get(tid, 0),
        })

    行.sort(key=lambda r: (-r['频次'].count('core'), r['字数']))
    宽 = max(len(r['标题']) for r in 行)
    print('%-22s %-10s %-8s %5s %5s %5s  %s' % ('任务', '状态', '频次', '页数', '字数', '图数', '标题'))
    print('-' * 100)
    for r in 行:
        标 = ''
        if r['页数'] <= 1 and r['图数'] <= 1:
            标 = '  ⚠️ 只有一页/一张图'
        print('%-22s %-10s %-8s %5d %5d %5d  %s%s' % (
            r['id'], r['状态'], r['频次'], r['页数'], r['字数'], r['图数'], r['标题'], 标))
        for p in r['页']:
            if '⛔' in p:
                print('      ⛔ %s' % p)

    薄 = [r for r in 行 if r['图数'] <= 2]
    print('\n=== 截图 ≤2 张的任务（下一批的候选） ===')
    for r in 薄:
        print('  %-22s %-4d 图 / %-6d 字  %s' % (r['id'], r['图数'], r['字数'], r['标题']))

    孤儿 = set(桶) - {r['id'] for r in 行}
    if 孤儿:
        print('\n⚠️ manifest 里有、task-inventory 里没有的 task_id：%s' % sorted(孤儿))
    return 0


if __name__ == '__main__':
    sys.exit(main())

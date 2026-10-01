#!/usr/bin/env python3
"""死状态普查工具 (Batch 349 引入): 统计某个 store 每个状态字段的外部读取点。

Batch 348 靠粗糙正则数出「16 个死成员」——错的(`selectedNodeId`/`setNodes` 明明
在用)。Batch 349 换成直接计数, 结果是 frameosStore 33 个**数据**字段里只有
`generations` 一个真正零外部读。**测量方法本身要先验证**, 否则会拿着错误的
量级去改代码。

方法学纪律: 不能只看 store 自己的 set/初始化行 —— 那些是"写"。要找的是
「在 src/ 下、store 之外、真正读这个字段的地方」。零外部读 = 死状态候选。

**边界(别把它当门禁用)**:
  1. 本工具只看**数据字段**, 不看 action(所以「零调用 action」要另查);
  2. "零外部读"对「只在 store 内部读」的字段(如 frameosStore 的 nodeClipboard)
     会误报 —— 这些字段要人工判读, 不能直接当死状态;
  3. TS 类型/字符串里出现的同名字段不算读取。
真要门禁化, 必须先消掉 2 这类误报, 否则就是个假绿制造机。

用法:
    python3 scripts/frameos_deadstate_census.py
    python3 scripts/frameos_deadstate_census.py src/store/jimengStore.ts JimengCanvasState
"""

import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DEFAULT_STORE = "src/store/frameosStore.ts"
DEFAULT_IFACE = "FrameosCanvasState"

store_rel = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_STORE
interface = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_IFACE
STORE = ROOT / store_rel
src = STORE.read_text()


def extract_data_fields(text: str, interface: str) -> list[str]:
    """抽状态接口的**数据字段**, 排除箭头函数形式的 action。

    误报类 1(Batch 350 实测): 多行函数签名的**参数**会被单行正则误当成字段 ——
    jimengStore 的 `applyTrim: (\n  id: string,\n  trimmedDuration: number,\n)` 里
    `trimmedDuration: number,` 单独占一行, 完全符合「标识符 + 冒号」的形状。
    修法: 跟踪括号深度, 只把**深度 0** 的行当字段候选。
    """
    start = text.find(f"interface {interface} {{")
    if start < 0:
        start = text.find(f"export interface {interface} {{")
    if start < 0:
        raise SystemExit(f"找不到 interface {interface}")
    end = text.index("\n}", start)
    body = text[start:end]

    fields: list[str] = []
    depth = 0
    for line in body.splitlines():
        s = line.strip()
        opens, closes = s.count("("), s.count(")")
        if depth == 0:
            if not s or s.startswith("//") or s.startswith("/*"):
                depth += opens - closes
                continue
            fm = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\??\s*:", s)
            if fm and "=>" not in s and "(" not in s.split(":")[0]:
                fields.append(fm.group(1))
        depth += opens - closes
        if depth < 0:
            depth = 0
    return fields


fields = extract_data_fields(src, interface)
print(f"# {store_rel} :: {interface} 状态数据字段: {len(fields)} 个\n")

# 全仓扫 src/ 下所有 .ts/.tsx, 统计每个字段在 store 之外的读取
files = subprocess.run(
    ["git", "ls-files", "src/"], capture_output=True, text=True, cwd=ROOT
).stdout.split()
files = [f for f in files if f.endswith((".ts", ".tsx")) and f != store_rel]

# store hook 名 —— 用于判定「这一行确实在跟本 store 打交道」。
# 误报类 2(Batch 350 实测): hook 真名是 `useJimengStore`, 而文件名是 `jimengStore`;
# 用 `\bjimengStore\b` 匹配**永远命中不了** `useJimengStore`(use 与 Jimeng 之间
# 没有词边界) → groupNames/groupColors 被误判成死状态, 而它们其实在
# JimengGroupFrames.tsx:69 被**解构**读取。
# 这里刻意用**无词边界的大小写不敏感子串**匹配: 这个工具的假阳性方向是
# 「把活字段判成死的」, 那是会诱导人删掉在用代码的**危险方向**, 所以宁可多算。
store_key = Path(store_rel).stem.replace(".ts", "")
hook_pat = re.compile(re.escape(store_key), re.IGNORECASE)

rows = []
for name in fields:
    prop: dict[str, list[int]] = defaultdict(list)   # 层 A: s.field 属性访问(强证据)
    destr: dict[str, list[int]] = defaultdict(list)  # 层 B: 与 store 同行出现的裸标识符(解构等)
    pat_prop = re.compile(rf"\.\s*{re.escape(name)}\b")
    pat_bare = re.compile(rf"\b{re.escape(name)}\b")
    for f in files:
        try:
            text = (ROOT / f).read_text()
        except Exception:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if pat_prop.search(line):
                prop[f].append(i)
            elif pat_bare.search(line) and hook_pat.search(line):
                destr[f].append(i)
    a = sum(len(v) for v in prop.values())
    b = sum(len(v) for v in destr.values())
    hits = prop or destr
    rows.append((name, a, b, hits))

rows.sort(key=lambda r: (r[1] + r[2]))

dead = [n for n, a, b, _ in rows if a == 0 and b == 0]
print("| 字段 | A:属性访问 | B:解构/同行 | 涉及文件(前3) |")
print("|---|---|---|---|")
for name, a, b, hits in rows:
    tag = "**两层都 0**" if (a == 0 and b == 0) else ", ".join(sorted(hits)[:3])
    print(f"| `{name}` | {a} | {b} | {tag} |")

print("\n# 死状态候选(属性访问与解构两层都为 0, 需再人工判读 store 内部读):")
print(dead or "(无)")

only_destructure = [n for n, a, b, _ in rows if a == 0 and b > 0]
if only_destructure:
    print(f"\n# 只被解构读取(层 A 为 0 但层 B > 0 —— 活着, 别当死状态): {only_destructure}")

if dead:
    print("\n# 死状态字段在 store 内部的全部出现位置:")
    for i, line in enumerate(src.splitlines(), 1):
        if any(re.search(rf"\b{re.escape(n)}\b", line) for n in dead):
            print(f"  L{i}: {line.strip()}")

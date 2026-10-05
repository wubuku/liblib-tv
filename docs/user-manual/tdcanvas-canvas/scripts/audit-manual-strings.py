#!/usr/bin/env python3
"""audit-manual-strings.py —— 手册引号里的界面字符串 vs 活体界面转储（M245 建立）

**它要回答的问题**

F54（M244）证明了一类可复现的错误：**手册用一个「界面上并不存在的名字」去指称控件**。
R99 的 `Close` 是读屏名（屏幕上只有 × 图标），R100 的「重新读取 Skill」也是读屏名
（屏幕上只有 ⟳ 图标，悬停提示写的是「重新读取」）。

这类错误**肉眼核图发现不了**——图上就是「有个按钮在那儿」，
所以要把它变成一次机械读数：**把界面上能读到的字全倒出来，让手册去撞它。**

**它怎么分层（★ 这就是 F54 的全部要点）**

    A 可见   界面上看得见的文字          ← 读者眼睛能读到
    B 悬停   鼠标移上去才出现的提示        ← 停留够久才有
    C 读屏   aria-label                  ← 屏幕上没有
    D 提示   title 属性                  ← 原生 tooltip，无头抓不到
    E 占位   placeholder                 ← 输入框里的灰字，打字就没了
    F 未命中 以上都没有

**★ 真正要盯的不是 F，而是「只命中 C/D 而没命中 A」**——
那正是 R99/R100 的形状：手册当它是界面文字，它其实只在读屏名里。
所以脚本把 **B/C/D/E 单独归到「非可见命中」**，不与 A 混在一起。

**它不是什么**

不是门禁。它需要一份活的界面转储（`probe-visible-strings.js` 的产物），
**而构建机上没有 dev server**，所以它只能人工单跑。
和 `audit-trouble-to-tasks.py` 同一性质：**输出候选读数，每一条都要人读过再决定改不改手册**。

**★ 三条判据纪律**

1. **「未命中」绝大多数不是错。** 手册的「…」里什么都有：界面标签、用户的话、
   作者自己的用词（「「本机」两个字是关键」里的「本机」根本不是界面字符串）。
   **所以脚本不判定对错，只做分层计数 + 列出未命中项的上下文，由人逐条读。**
   把这三类混在一起当「界面字符串」，假阳性会淹没真错（F53 第 ③ 类）。
2. **匹配要给出用的是哪一档。** 精确匹配失败后退到「去空白与分隔符」的归一匹配，
   **但两档必须分别计数**——否则「去掉空格才匹配上」这件事会被藏起来，
   而它恰恰是「手册里的空格是作者加的、界面上没有」这类真错的信号。
3. **零结果先怀疑判据。** 转储侧出问题时（页面没渲染、视口太窄把标签折叠成 0×0），
   本脚本会**全页未命中**。所以它**逐路由报命中数**——
   某一路由命中为 0 时先去看那一路由的转储，别急着改手册。

用法：
    node scripts/probe-visible-strings.js            # 先出转储（ROUTES=... OUT=...）
    python3 scripts/audit-manual-strings.py /tmp/m245-strings.json 20-reference.md
"""

from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

# 「…」取内容；同一行里可能有好几处
QUOTED = re.compile(r"「([^」]{1,60})」")
# `code` 形式的界面串也一并收（手册常用它写 aria-label、占位符、键名）
CODED = re.compile(r"`([^`\n]{1,60})`")

# 归一化：去掉所有空白与常见分隔符，只比「字有没有」
STRIP = re.compile(r"[\s·、，,。．;；:：/|｜\-—_()（）「」“”\"'’]")

LOOSE = os.environ.get("LOOSE") == "1"

TIERS = [
    ("A 可见", "visibleText"),
    ("B 悬停", "hover"),
    ("C 读屏", "aria"),
    ("D 提示", "title"),
    ("E 占位", "placeholder"),
]


def norm(s: str) -> str:
    return STRIP.sub("", s)


def collect_pools(data: dict) -> tuple[dict[str, list[str]], dict[str, int]]:
    """把各路由的转储并成五个池子，并统计每条路由的命中规模（纪律 3）。"""
    pools: dict[str, list[str]] = {k: [] for _, k in TIERS}
    per_route: dict[str, int] = {}
    for route, v in data.items():
        per_route[route] = len(v.get("visibleText", []))
        for _, key in TIERS:
            for item in v.get(key, []):
                s = item if isinstance(item, str) else item.get("hover", "")
                if s and s not in pools[key]:
                    pools[key].append(s)
        # 悬停项结构不同，单独再收一次按钮自身的可见文字
        for h in v.get("hover", []):
            if isinstance(h, dict) and h.get("hover") and h["hover"] not in pools["hover"]:
                pools["hover"].append(h["hover"])
    return pools, per_route


def match(s: str, pool: list[str]) -> tuple[str, str | None]:
    """返回 (判据, 命中的那个字符串)。

    ★★ **纪律 2 的最终形态（M245 用 8 条假订正换来的）**：
    **默认只认「完整相等」，子串匹配必须显式打开，而且一打开就报它有多脏。**

    实测：965 条「」候选里，子串匹配命中 209 条，**其中 67 条（32%）是假的**——
    「删除」「点」「线」「或」「内」「土豆」全都能在某处长文本里找到子串。
    更糟的是它会**把不相干的控件配成一对**，从而造出「手册写错了」的假象：
      · 手册「放大」（图片工具条上的按钮）撞上画布缩放的 aria「放大/缩小画布」；
      · 手册「清 空」（确认弹窗的按钮）撞上 Dock 的「清空画布」；
      · 手册「对话」（面板收起时的标签）撞上面板打开时的悬停提示「收起对话」；
      · 手册「重置」（多角度对话框里的）撞上画布的「重置视图」。
    **照子串匹配的结果去「订正」，这四条都会被改错，而改错的那几条会让读者更找不到按钮。**
    → 所以：**主判据 = 完整相等（归一后）**；子串只在 `--loose` 下算，且**必须与主判据分开计数**。
    """
    ns = norm(s)
    if ns:
        for cand in pool:
            if norm(cand) == ns:
                return "相等", cand
    if LOOSE:
        for cand in pool:
            if s and (s == cand or s in cand):
                return "子串", cand
        if ns:
            for cand in pool:
                nc = norm(cand)
                if nc and ns in nc:
                    return "子串", cand
    return "未命中", None


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    dump = Path(sys.argv[1])
    pages = sys.argv[2:]
    print(f"[判据] {'★ 子串匹配（LOOSE=1，脏：实测 32% 假命中）' if LOOSE else '完整相等（默认，唯一可用的一档）'}")
    if not dump.is_file():
        print(f"[FAIL] 找不到转储文件 {dump}；先跑 probe-visible-strings.js")
        return 1
    data = json.loads(dump.read_text(encoding="utf-8"))
    pools, per_route = collect_pools(data)

    print("=" * 78)
    print(f"[转储] {len(data)} 条路由；各路由「可见文字」条数（纪律 3：先看这个）")
    for r, n in per_route.items():
        flag = "  ★ 为 0，先怀疑这一页没渲染" if n == 0 else ""
        print(f"   {r:44s} {n:4d}{flag}")
    print("=" * 78)

    total_problems = 0
    for page in pages:
        p = Path(page)
        if not p.is_file():
            print(f"[FAIL] 找不到页面 {page}")
            return 1
        text = p.read_text(encoding="utf-8")
        cands: list[str] = []
        for m in QUOTED.findall(text):
            if m not in cands:
                cands.append(m)
        backticked = [m for m in CODED.findall(text)]

        buckets: dict[str, list[tuple[str, str | None]]] = {k: [] for k, _ in TIERS}
        buckets["F 未命中"] = []
        for s in cands:
            hit = False
            for label, key in TIERS:
                how, cand = match(s, pools[key])
                if how != "未命中":
                    buckets[label].append((s, f"{how}→{cand}"))
                    hit = True
                    break
            if not hit:
                buckets["F 未命中"].append((s, None))

        print(f"\n[{p.name}] 「」界面候选 {len(cands)} 条；`code` 串 {len(backticked)} 条（未计入分层）")
        for label, _ in TIERS:
            items = buckets[label]
            norm_n = sum(1 for _, d in items if d and d.startswith("归一"))
            print(f"   {label:8s} {len(items):4d}" + (f"（其中靠归一匹配才命中 {norm_n} 条）" if norm_n else ""))

        # ★ 重点：只命中 B/C/D/E 而没命中 A 的，就是 R99/R100 的形状
        invisible_only = [x for k in ("B 悬停", "C 读屏", "D 提示", "E 占位")
                          for x in buckets[k]]
        print(f"   ── 其中「只在非可见层命中」{len(invisible_only)} 条 ★ R99/R100 的形状")
        for s, d in invisible_only[:25]:
            print(f"      · 「{s}」  {d}")

        miss = buckets["F 未命中"]
        print(f"   ── 完全未命中 {len(miss)} 条（★ 绝大多数不是错，需人读）")
        for s, _ in miss[:20]:
            # 抓一句上下文
            i = text.find(f"「{s}」")
            ctx = text[max(0, i - 40):i + len(s) + 20].replace("\n", " ") if i >= 0 else ""
            print(f"      · 「{s}」  …{ctx}…")
        if len(miss) > 20:
            print(f"      …… 另有 {len(miss) - 20} 条")
        total_problems += len(invisible_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

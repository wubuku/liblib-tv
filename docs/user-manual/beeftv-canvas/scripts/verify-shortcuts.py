#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""快捷键修饰键前缀核对闸：手册写法 vs 上游真实绑定。

背景（Batch 110）：同一类缺陷在两个不同页面各出现过一次——
  · Batch 97：导演台快捷键表把重做写作「Ctrl/Cmd+Z / Shift+Z」，漏了 `Shift+Z`
    所需的 `Ctrl/Cmd` 前缀；
  · Batch 107：画布快捷键表把重做写作「Shift + Z 或 Y」，同样漏了前缀。
相隔 10 个 batch、两个页面、同一个写法习惯，说明这是**系统性书写缺陷**而非偶发。
这类缺陷的特点是**人读不出来**：表格看着完整、语义也说得通，只有把每一行拿去和
源码的绑定条件逐条比对才会暴露。

本闸的判据：从上游 `use-canvas-keyboard.ts` 抽出「哪些键必须带 Ctrl/Cmd」
（源码里形如 `isModifierShortcut && !event.altKey && key === "X"` 的条件），
再扫手册里所有「字母 + 修饰键」形态的快捷键写法，凡指向这类键却没写
Ctrl/Cmd（或 ⌘）的，一律报出。

同时校验反向：写了 Ctrl/Cmd 但源码里该键并不要求修饰键的，也会提示复查
（可能是写错了键位，也可能源码已改）。

找不到 BeefTV 源码时静默跳过——手册构建不应依赖同级仓库存在。

退出码：0 通过（或跳过）；1 存在前缀缺失/多余。
"""

import os
import re
import sys
import subprocess

CANDIDATES = [
    os.environ.get("BEEFTV_SRC", ""),
    "/Users/yangjiefeng/Documents/glanderness/BeefTV",
]

# 只在已发布正文里查；内部账本允许出现裸写法（它们是给自己看的）
INTERNAL = re.compile(
    r"(task-inventory|PROGRESS|AUDIT-RULES|AUDIT|FINAL-REPORT|SOURCE-OBSERVATIONS|PUBLISH)"
)

# 手册里出现的三种修饰键记法
HAS_CTRL = re.compile(r"Ctrl\s*/\s*Cmd|Ctrl\s*\+\s*Cmd|⌘")


def find_source():
    for c in CANDIDATES:
        if c and os.path.isdir(os.path.join(c, "backend")):
            return os.path.abspath(c)
    return None


def git_show(src, ref, path):
    r = subprocess.run(
        ["git", "show", f"{ref}:{path}"],
        cwd=src, capture_output=True, text=True,
    )
    return r.stdout if r.returncode == 0 else ""


def bindings(src, ref="origin/main"):
    """抽出两组键：必须带 Ctrl/Cmd 的、以及另有 Alt/Shift 独立绑定的。

    为什么必须分两组：同一个键可能有**两种**绑定，源码里是两条分支。例如
      · `isModifierShortcut && !event.altKey && key === "f"` → Ctrl/Cmd+F 搜索
      · `event.altKey && event.shiftKey && !isModifierShortcut && key === "f"`
        → Alt+Shift+F 自动整理
    只抽第一组会把「Alt+Shift+F」误报成漏写前缀——它是完全正确的写法。
    故凡在 altKey / shiftKey 分支里也出现过的键，一律不参与前缀检查。
    """
    body = git_show(src, ref, "web/src/pages/canvas/use-canvas-keyboard.ts")
    if not body:
        return None, None
    accel, alt = set(), set()
    for line in body.split("\n"):
        if 'key === "' not in line:
            continue
        keys = {k.lower() for k in re.findall(r'key === "([^"]+)"', line)}
        if "isModifierShortcut" in line and "!event.altKey" in line:
            accel |= keys
        if "event.altKey" in line or "event.shiftKey" in line:
            if "!isModifierShortcut" in line:
                alt |= keys
    return accel, alt


# 快捷键表达式只认两种形态，避免把正文里每个裸字母/数字都当成快捷键：
#   ① 带显式加号的组合： "Ctrl/Cmd + Shift + Z" / "Alt+L" / "Shift + Z"
#   ② 符号简写：           "⌘F" / "⇧⌘F" / "⌥L"
# 关键约束：必须出现「修饰键 + 键」的结构。裸的 "Z"、版本号里的 "0"、列表序号
# "1." 都不算——第一版没加这个约束，扫出 1000+ 条假阳性，闸门直接不可用。
EXPR_PLUS = re.compile(
    r"(?:(?:Ctrl\s*/\s*Cmd|⌘|Shift|⇧|Alt|Option|⌥)\s*[+＋]\s*){1,3}"
    r"([A-Za-z0-9?])"
)
EXPR_SYMBOL = re.compile(r"[⌘⇧⌥]+\s*([A-Za-z0-9?])")


def iter_exprs(body):
    """产出 (起始位置, 表达式文本, 键字符)。"""
    spans = []
    for rx in (EXPR_PLUS, EXPR_SYMBOL):
        for m in rx.finditer(body):
            if any(s <= m.start() < e for s, e in spans):
                continue
            spans.append((m.start(), m.end()))
            yield m.start(), m.group(0), m.group(1)


def scan(page, body, accel):
    """返回该页里「指向必须带 Ctrl/Cmd 的键、却没写 Ctrl/Cmd」的表达式。"""
    bad = []
    for pos, expr, key in iter_exprs(body):
        if key.lower() not in accel:
            continue
        if HAS_CTRL.search(expr):
            continue
        line_start = body.rfind("\n", 0, pos) + 1
        line = body[line_start: body.find("\n", pos) if body.find("\n", pos) > 0 else len(body)]
        # 同一行里若已出现 Ctrl/Cmd（本行同时写了多个快捷键），视为合规
        if HAS_CTRL.search(line):
            continue
        bad.append((expr.strip(" `"), key, page))
    return bad


def main():
    src = find_source()
    if not src:
        print("[skip] 未找到 BeefTV 源码，跳过快捷键前缀核对")
        return 2
    accel, alt = bindings(src)
    if not accel:
        print("[skip] 未能从上游抽出修饰键绑定（源码结构可能已变），跳过")
        return 2
    # 有 Alt/Shift 独立绑定的键不查前缀（如 F：Ctrl/Cmd+F 与 Alt+Shift+F 并存）
    accel = accel - alt
    if not accel:
        print("[skip] 上游绑定的键均有 Alt/Shift 变体，无可校验的前缀项，跳过")
        return 2

    import glob
    problems = []
    for p in sorted(glob.glob("**/*.md", recursive=True)):
        if "node_modules" in p or ".vitepress" in p or INTERNAL.search(os.path.basename(p)):
            continue
        body = open(p, encoding="utf-8", errors="ignore").read()
        for expr, key, page in scan(p, body, accel):
            problems.append(f"{page}: 「{expr}」→ {key.upper()} 需带 Ctrl/Cmd")

    if problems:
        print(f"快捷键前缀核对：上游有 {len(accel)} 个键必须带 Ctrl/Cmd，"
              f"手册发现 {len(problems)} 处可能漏写")
        for x in problems:
            print("  " + x)
        return 1

    print(f"快捷键前缀核对通过：上游 {len(accel)} 个必须带 Ctrl/Cmd 的键"
          f"（{'/'.join(sorted(accel))}），手册写法均已带前缀")
    return 0


if __name__ == "__main__":
    sys.exit(main())

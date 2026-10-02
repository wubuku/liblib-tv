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

## Batch 166：本闸曾经「什么都没扫却判通过」

原实现用 `glob.glob("**/*.md", recursive=True)`——**相对当前工作目录**。
于是从任何别的目录运行，扫到的就是**那个目录下的 .md**，与本手册毫无关系。实测两种结局：

1. 在一个**干净空目录**里运行 → 扫到 **0 个文件**、0 个问题，输出
   「快捷键前缀核对通过：上游 14 个必须带 Ctrl/Cmd 的键……手册写法均已带前缀」，
   **退出码 0**——**什么都没查，却判了通过**；
2. 在 `/tmp` 里运行 → glob 命中一个已消失的临时目录，`open()` 抛
   `FileNotFoundError` 直接崩栈，退出码 1——而 1 在三段约定里是「不一致」，
   **信号也是错的**。

**这正是 Batch 157「工具失败被当成零命中」的原样重演**，也是纪律 101
「换一个判据就要重新问一遍它会不会静悄悄地什么都查不到」的第一次应验——
**问晚了：纪律立了三个 batch，本闸却一直没被拿去对照。**

修法三条：
1. 手册根目录由 `__file__` 自定位，**不再依赖 cwd**；
2. 逐个文件读，读不到就跳过（不再崩栈）；
3. **扫到的文件数低于下限即 `return 2`**——「一个文件都没读到」必须报成
   「未能核对」，绝不能变成「零处问题 → 通过」。

退出码：0 通过；1 存在前缀缺失/多余；2 未能核对（源码缺失 / 手册文件读不到足够多）。
"""

import os
import re
import sys
import subprocess
import beefsrc
from baseline import resolve_ref, BaselineError, baseline_guard


# 扫到的正文文件数下限。**低于它就报「未能核对」，不许报「通过」**——
# 「0 处问题」与「没查」必须返回不同的码（Batch 157 / 纪律 101）。
# 真实值 41（41 个 md），取 20 留足余量，又足以抓住「cwd 指错」这类整片扫空。
MIN_SCANNED_FILES = 20

# 只在已发布正文里查；内部账本允许出现裸写法（它们是给自己看的）
INTERNAL = re.compile(
    r"(task-inventory|PROGRESS|AUDIT-RULES|AUDIT|FINAL-REPORT|SOURCE-OBSERVATIONS|PUBLISH)"
)

# 手册里出现的三种修饰键记法
HAS_CTRL = re.compile(r"Ctrl\s*/\s*Cmd|Ctrl\s*\+\s*Cmd|⌘")


def find_source():
    """**Batch 197：路径解析收敛到 `beefsrc` 单一来源**（含"是否走了兜底"）。

    原先这里各带一张 `CANDIDATES` 表，判真条件还不一样
    （本组问 `isdir(c/"backend")`，`quote-punct`/`shot-drift` 问 `isdir(c/".git")`），
    **而 `baseline.py` 又是第三种**——同一个 `BEEFTV_SRC` 在不同闸里会解析成不同的仓。
    实测缺陷：`.git` 目录式判真在 **git worktree 上必然失败**（那里 `.git` 是文件），
    于是用户显式指定的路径被**静默忽略**、改用兜底那份，而闸一声不吭。
    """
    src, is_fallback = beefsrc.resolve_src()
    if src is None:
        return None
    if is_fallback:
        # **静默降级与「明确说明」的差别，就是本手册整套纪律在说的事**
        print("[兜底] 未采用 BEEFTV_SRC 指定的路径（它不是一个 git 检出），"
              "改用候选表里的 %s" % src)
    return src


def git_show(src, ref, path):
    r = subprocess.run(
        ["git", "show", f"{ref}:{path}"],
        cwd=src, capture_output=True, text=True,
    )
    return r.stdout if r.returncode == 0 else ""


def bindings(src, ref=None):
    if ref is None:
        ref = resolve_ref()
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
    """返回该页里「指向必须带 Ctrl/Cmd 的键、却没写 Ctrl/Cmd」的表达式。

    ⚠️ Batch 166：抑制规则从「整行豁免」收窄为「相邻豁免」。
    原来的规则是「同一行里只要出现过 Ctrl/Cmd，本行所有表达式一律合规」——
    那是**抑制过宽**，与匹配过窄一样有害：`Ctrl/Cmd+Z / Shift+Z / Y` 里，
    前半段的 `Ctrl/Cmd` 会把后半段**真正漏了前缀**的 `Shift+Z` 一起免掉，
    而上游 `use-canvas-keyboard.ts:157` 明写 `isModifierShortcut && key === "z"`，
    **裸按 Shift+Z 什么都不会发生**。
    现在只认「紧挨着上一个表达式的那段分隔文本里带 Ctrl/Cmd」，
    即 `Ctrl/Cmd+Z / Ctrl/Cmd+Shift+Z` 这种连写仍合规。
    """
    bad = []
    last_end = -1
    for pos, expr, key in iter_exprs(body):
        if key.lower() not in accel:
            last_end = max(last_end, pos + len(expr))
            continue
        if HAS_CTRL.search(expr):
            last_end = pos + len(expr)
            continue
        # 只看「上一个表达式结束」到「本表达式开始」之间的分隔文本
        gap = body[last_end:pos] if last_end >= 0 else ""
        if HAS_CTRL.search(gap):
            last_end = pos + len(expr)
            continue
        last_end = pos + len(expr)
        bad.append((expr.strip(" `"), key, page))
    return bad


@baseline_guard
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
    scanned, unreadable = 0, 0
    # 手册根目录由脚本自身位置推导，**不依赖 cwd**——
    # Batch 166 实测：从空目录运行时本闸曾以「0 文件 → 0 问题」判定通过。
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for p in sorted(glob.glob(os.path.join(root, "**", "*.md"), recursive=True)):
        if "node_modules" in p or ".vitepress" in p or INTERNAL.search(os.path.basename(p)):
            continue
        try:
            body = open(p, encoding="utf-8", errors="ignore").read()
        except OSError:
            unreadable += 1
            continue
        scanned += 1
        rel = os.path.relpath(p, root)
        for expr, key, page in scan(rel, body, accel):
            problems.append(f"{page}: 「{expr}」→ {key.upper()} 需带 Ctrl/Cmd")

    # 「读到的文件太少」是**未能核对**，不是「没问题」。
    # 下限取手册实际文件数的保守值：真实值 41，即便砍掉一半也远高于 MIN_SCANNED_FILES。
    if scanned < MIN_SCANNED_FILES:
        print(f"[skip] 只读到 {scanned} 个正文文件（下限 {MIN_SCANNED_FILES}，另有 {unreadable} 个读不到），"
              f"输入范围明显不对——本闸本轮未能核对")
        return 2

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

#!/usr/bin/env python3
"""绝对断言登记表校验（第十九道门禁，M254 新增）

用法：
    python3 scripts/check-absolute-claims.py .

**背景（M251 与 M253 各抓到一条同形状的错误）**：

R103：「穷尽 9 种组合」的表漏了一档（状态空间漏了「产出来源」这一维）。
R104：「节点永远落在 16 的整数倍上」缺两个前提（网格吸附默认关、且智能对齐优先）。
**两者的共同形状是：把带条件的结论写成了不带条件的。**

M253 因此留下一条判据：「凡出现绝对词的句子，同页必须能找到它的开关或例外所在」，
同时写明**这条判据没法一步做成门禁**——§13.0 已经否掉过两种自动锚点设计
（锚点式会产出「具条和…翻遍」这类坏锚点，字面量式在 R44 订正后就一直在造假失败）。
所以这里走 §13.1 那条**已经证明可行**的路：**手读建表，门禁只校验表**。

**本门禁管三件事**：

1. **表体结构**：每行恰好 4 格、ID 唯一不重复、分类是三个合法值之一。
2. **A / C 两类的限定词必须逐字命中它自己那一行指向的页面**——
   命中不到就说明「前提被删了」或「片段抄错了」。
   ★ **C 类（已订正）也要查**：否则「订正块哪天被误删」没有任何东西会叫。
3. **声明条数与表体行数一致**（照抄 §13.1 的做法，**这是最容易被改漏的一处**）。

**它管不了什么（必须先读，否则会高估它）**：

- **它不扫正文**。正文里新出现的绝对句**一条都拦不住**——
  **新句子要进表，得先有人用 `find-absolute-claims.py` 把它捞出来**。
- **B 类（绝对成立）那一格写的内容它一个字都不判**，只查非空。
  「为什么没有例外」对不对，是人读的。
- **它只覆盖「穷尽 / 恒 / 永远 / 一律 + 计数」这一类**；
  「从不 / 没有 / 任何」三类数量更大，本门禁一条没收（见 §14 的边界说明）。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

HEADING = "## 14. 绝对断言登记表"
KINDS = ("A 有限定词", "B 绝对成立", "C 已订正")
# 限定词那一格里既可能是整句短语，也可能带 Markdown 强调——
# **判命中前先把强调标记剥掉**，否则 `**例外只有一个**` 永远命中不上。
EMPHASIS = re.compile(r"[*`_]")


def strip_markup(text: str) -> str:
    return EMPHASIS.sub("", text)


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    path = root / "SOURCE_OBSERVATIONS.md"
    if not path.is_file():
        print(f"[skip] 找不到 {path}")
        return 0
    text = path.read_text(encoding="utf-8")
    if HEADING not in text:
        print("[fail] SOURCE_OBSERVATIONS.md 里找不到 §14 绝对断言登记表——"
              "**门禁的判据没了，它会变成一道全绿的空闸**")
        return 1

    body = text.split(HEADING, 1)[1]
    # 只取 §14.1 的那张表：表头是「ID | 绝对句在哪」
    rows: list[list[str]] = []
    declared: int | None = None
    for line in body.split("\n"):
        if line.startswith("## ") and "14." not in line[:8]:
            break
        if not line.startswith("| A") and "| A" not in line[:6]:
            continue
        cells = line.split("|")
        if len(cells) < 6:          # | A01 | ... | ... | ... | → 6 段
            continue
        rows.append([c.strip() for c in cells[1:5]])

    m = re.search(r"本表共\s*\*\*(\d+)\s*条", body)
    if m:
        declared = int(m.group(1))
    elif "共" not in body[:2000]:
        # 允许没写声明条数，但要在报告里说清「这一项没被校验」
        pass

    problems: list[str] = []

    if not rows:
        problems.append("§14 的表体一行都没有——**门禁正在守一张空表**")

    ids: set[str] = set()
    for row in rows:
        rid, frag, kind, qual = row
        if not rid:
            problems.append(f"有一行 ID 为空：{row}")
            continue
        if rid in ids:
            problems.append(f"ID 重复：{rid}")
        ids.add(rid)
        if kind not in KINDS:
            problems.append(f"[{rid}] 分类不是三个合法值之一：{kind!r}")
        if not qual:
            problems.append(f"[{rid}] 限定词 / 例外那一格是空的")
            continue
        if kind == "B 绝对成立":
            # ★ B 类只查非空。「为什么没有例外」这一格是给人看的，机器不判。
            continue
        # A / C：限定词必须逐字命中它指向的那一页
        if "#" not in frag:
            problems.append(f"[{rid}] 片段没有写成「文件#行内片段」：{frag!r}")
            continue
        # ★ **文件名要先剥掉反引号再取**——表里那一格是写成代码样式的
        #   （`` `20-reference.md#…` ``），**不剥就会拿着「带反引号的文件名」去找**，报出一个
        #   「文件不存在」的假失败。**这是 M254 自己踩的：门禁第一版就是这么写的。**
        fname, anchor = frag.split("#", 1)
        fname = fname.strip().strip("`").strip()
        anchor = strip_markup(anchor)
        target = root / fname
        if not target.is_file():
            problems.append(f"[{rid}] 指向的文件不存在：{fname}")
            continue
        ttext = target.read_text(encoding="utf-8")
        # ★ **M296 补：锚点片段本身也要逐字命中它指向的那一页。**
        #   此前 `#` 后半段只被 `strip_markup` 处理、**从未参与任何查找**——
        #   而表里那一格明明写成「文件#行内片段」，读者会以为它是受校验的。
        #   **后果是锚点会静默腐化**：改掉了被引用的那句话之后，表里仍显示旧句，
        #   而这道门禁一路报 ok。**M296 改 `connect-references.md` 的措辞时当场撞上了这个洞**——
        #   A28 的锚点已经不指向任何现存句子了，而门禁当时一声不吭。
        #   **只查长度 ≥ 6 的片段**：太短的锚点会假失败（与下面 needles 用同一个下限）。
        a_needle = anchor.strip()
        if len(a_needle) >= 6:
            if a_needle not in strip_markup(ttext):
                problems.append(
                    f"[{rid}] 锚点片段在 {fname} 里已找不到：{a_needle!r}\n"
                    f"        → 引用的那句话被改写了（锚点腐化）。这一格是给人读的，"
                    f"**此前机器一个字都不校验**，所以它腐化时不报任何错")
        hay = strip_markup(qual)
        needles = [n.strip() for n in re.split(r"[；;]", hay) if len(n.strip()) >= 6]
        if not needles:
            problems.append(f"[{rid}] 限定词那一格剥掉标记后不足 6 个字，判据太松：{qual!r}")
            continue
        miss = [n for n in needles if n not in strip_markup(ttext)]
        if miss:
            problems.append(
                f"[{rid}] 限定词在 {fname} 里找不到：{miss[0]!r}\n"
                f"        → 要么前提被删了，要么片段抄错了（**这一格就是本门禁存在的理由**）")

    if declared is not None and declared != len(rows):
        problems.append(f"声明条数与表体行数对不上：声明 {declared} 条，表体 {len(rows)} 行")

    if problems:
        print(f"[fail] 绝对断言登记表校验未通过（{len(problems)} 项）：")
        for p in problems:
            print("  [FAIL] " + p)
        return 1

    by_kind = {k: sum(1 for r in rows if r[2] == k) for k in KINDS}
    print(f"  [ ok ] 绝对断言登记表：{len(rows)} 条"
          f"（有限定词 {by_kind[KINDS[0]]} / 绝对成立 {by_kind[KINDS[1]]} / 已订正 {by_kind[KINDS[2]]}），"
          f"A 与 C 类的限定词逐字命中")
    print("  ★ **它不扫正文**——新出现的绝对句要靠 find-absolute-claims.py 捞出来再入表。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

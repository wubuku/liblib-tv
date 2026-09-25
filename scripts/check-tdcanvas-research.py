#!/usr/bin/env python3
"""TDCanvas 调研包自检脚本（docs/research/tdcanvas-2026-09-26）。

复跑三项包内一致性校验（只读，不修改任何文档）：
1. § 交叉引用：包内 `§x.y` 引用必须能解析到 SOURCE_ANALYSIS.md / UPSTREAM_DIFF_AUDIT.md 的编号标题。
2. TD/UP 卡号：包内 `TD-xx` / `UP-xx` 引用必须能解析到 PATTERN_CARDS.md 的卡标题。
3. 计数一致性：ADOPTION 矩阵行号连续（1..26）、逐行决策与汇总分桶一致；
   README/docs 索引中声明的模式卡数（21）与矩阵行数（26）与实际一致。

用法：python3 scripts/check-tdcanvas-research.py
退出码：0 = 全部通过；1 = 存在问题（逐条打印）。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent / "docs" / "research" / "tdcanvas-2026-09-26"
EXPECTED_CARDS = 21
EXPECTED_ROWS = 26

problems: list[str] = []


def read(name: str) -> str:
    return (PKG / name).read_text(encoding="utf-8")


def numbered_headings(text: str) -> set[str]:
    out = set()
    for line in text.splitlines():
        m = re.match(r"^#{1,3}\s+(\d+(?:\.\d+)?)[.、\s]", line)
        if m:
            out.add(m.group(1))
    return out


def main() -> int:
    for f in sorted(PKG.glob("*.md")):
        if not f.is_file():
            problems.append(f"缺少文件: {f.name}")
    sa = numbered_headings(read("SOURCE_ANALYSIS.md"))
    ua = numbered_headings(read("UPSTREAM_DIFF_AUDIT.md"))
    pc = read("PATTERN_CARDS.md")
    cards = set(re.findall(r"^## ((?:TD|UP)-\d{2})", pc, re.M))

    # 1. § 交叉引用
    for f in sorted(PKG.glob("*.md")):
        if f.name == "ITERATION_LOG.md":
            continue
        for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            for m in re.finditer(r"§(\d+(?:\.\d+)?)", line):
                if m.group(1) not in sa and m.group(1) not in ua:
                    problems.append(f"§ 引用无法解析: {f.name}:{i} §{m.group(1)}")

    # 2. TD/UP 卡号
    for f in sorted(PKG.glob("*.md")):
        if f.name == "ITERATION_LOG.md":
            continue
        refs = set(re.findall(r"\b(TD-\d{2}|UP-\d{2})\b", f.read_text(encoding="utf-8")))
        for ref in sorted(refs - cards):
            problems.append(f"卡号无法解析: {f.name} → {ref}")

    # 3a. ADOPTION 矩阵行号与决策分桶
    ad = read("ADOPTION_DECISION_MATRIX.md")
    body, summary = ad.split("## 汇总", 1)
    rows = [int(n) for n in re.findall(r"^\| (\d+) \|", body, re.M)]
    if rows != list(range(1, EXPECTED_ROWS + 1)):
        problems.append(f"矩阵行号不连续或不等于 1..{EXPECTED_ROWS}: {rows}")
    vocab_line = body.split("\n", 4)
    # 决策统计只看表格行（| 开头），排除头部决策词汇说明
    row_decisions: dict[str, int] = {}
    for line in body.splitlines():
        if not line.startswith("|"):
            continue
        for d in re.findall(
            r"`(ADOPT_METHOD|ADAPT_TO_LIBTV|ADAPT_TO_JIMENG|RESEARCH_ONLY|DEFER|REJECT_TRANSPLANT)`", line
        ):
            row_decisions[d] = row_decisions.get(d, 0) + 1
    summary_rows = re.findall(r"^- `(?:ADOPT_METHOD|ADAPT)`?[^：]*：(.+)$", summary, re.M)
    adapt_ids = re.findall(r"#(\d+)", re.search(r"- `ADAPT`.*", summary, re.M).group(0)) if re.search(r"- `ADAPT`.*", summary, re.M) else []
    checks = {
        "ADOPT_METHOD": row_decisions.get("ADOPT_METHOD", 0),
        "RESEARCH_ONLY": row_decisions.get("RESEARCH_ONLY", 0),
        "DEFER": row_decisions.get("DEFER", 0),
        "REJECT_TRANSPLANT": row_decisions.get("REJECT_TRANSPLANT", 0),
    }
    for label, expected in checks.items():
        m = re.search(rf"- `{label}`：(.+)$", summary, re.M)
        got = len(re.findall(r"#\d+", m.group(1))) if m else -1
        if got != expected:
            problems.append(f"汇总 {label} 计数不符: 汇总 {got} vs 逐行 {expected}")
    adapt_rows = 0
    for line in body.splitlines():
        if line.startswith("|") and re.search(r"ADAPT_TO_(LIBTV|JIMENG)", line):
            adapt_rows += 1
    m = re.search(r"- `ADAPT`（候选[^）]*）：(.+)$", summary, re.M)
    got = len(re.findall(r"#\d+", m.group(1))) if m else -1
    if got != adapt_rows:
        problems.append(f"汇总 ADAPT 计数不符: 汇总 {got} vs 逐行 {adapt_rows}")

    # 3b. README/索引中的计数声明
    readme = read("README.md")
    if f"{EXPECTED_CARDS} 张模式卡" not in readme:
        problems.append(f"README 未声明 {EXPECTED_CARDS} 张模式卡")
    if f"{EXPECTED_ROWS} 项机制" not in readme:
        problems.append(f"README 未声明 {EXPECTED_ROWS} 项机制")
    actual_cards = len(cards)
    if actual_cards != EXPECTED_CARDS:
        problems.append(f"实际模式卡数 {actual_cards} != 声明 {EXPECTED_CARDS}")

    # 4. INTERACTION_CATALOG ↔ ADOPTION 对齐
    cat = read("INTERACTION_CATALOG.md")
    adapt_marks = cat.count("候选 ADAPT")
    summary_adapt = re.search(r"- `ADAPT`（候选[^）]*）：(.+)$", summary, re.M)
    adapt_ids = re.findall(r"#(\d+)", summary_adapt.group(1)) if summary_adapt else []
    if adapt_marks != len(adapt_ids):
        problems.append(
            f"INTERACTION_CATALOG「候选 ADAPT」标记数 {adapt_marks} 与矩阵 ADAPT 行数 {len(adapt_ids)} 不一致"
        )
    for sec in ["5.1", "5.2", "5.3", "5.4", "6.1", "6.2", "6.3"]:
        if f"§{sec}" not in body:
            problems.append(f"ADOPTION 矩阵缺少对 UPSTREAM §{sec} 的采纳行覆盖")
    for up in sorted(re.findall(r"^## (UP-\d{2})", pc, re.M)):
        if f"（{up}）" not in body:
            problems.append(f"上游参考卡 {up} 在 ADOPTION 矩阵中无对应行")

    if problems:
        print("TDCanvas 调研包自检：发现问题")
        for p in problems:
            print(f"  - {p}")
        return 1
    print(
        "TDCanvas 调研包自检：通过 "
        f"（§ 引用 / TD-UP 卡号 / 矩阵 {EXPECTED_ROWS} 行与汇总分桶 / 模式卡 {actual_cards} 张 / 计数声明一致）"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""BeefTV 调研包自检脚本（docs/research/beeftv-canvas-2026-09-27）。

复跑六项包内一致性校验（只读，不修改任何文档）：
1. § 交叉引用：包内 `§x[.y]` 引用必须能解析到 SOURCE_ANALYSIS.md 的编号标题。
2. BF 卡号：包内 `BF-xx` 引用必须能解析到 PATTERN_CARDS.md 的 `## BF-xx` 卡标题。
3. ADOPTION 矩阵：行号连续（1..44）；逐行决策（第 4 列）与「分桶汇总」表的
   数量与行号清单双向一致；每个被引用的 BF 卡都存在；每张卡都被矩阵至少引用一次。
4. 计数声明：README 中声明的模式卡数（45）与矩阵行数（44）与实际一致；
   索引（docs/research/README.md、docs/index.md）中包含本包条目。
5. 锁定提交锚点 `85c9686` 无异值混淆。
6. SOURCE_ANALYSIS 结构防撞（v82 轮新增）：编号标题不得重复（§32.60/§32.61
   曾被末两节误用撞号）；`| N |` 台账行号不得重复（末两节行号曾误从 262 重新
   起算，与既有行碰撞）。

用法：python3 scripts/check-beeftv-research.py
退出码：0 = 全部通过；1 = 存在问题（逐条打印）。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PKG = REPO / "docs" / "research" / "beeftv-canvas-2026-09-27"
EXPECTED_CARDS = 45
EXPECTED_ROWS = 44
LOCKED_SHORT = "85c9686"
DECISIONS = ("ADOPT_METHOD", "ADAPT", "RESEARCH_ONLY", "DEFER", "REJECT")

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
    for name in (
        "README.md",
        "REPORT.md",
        "SOURCE_ANALYSIS.md",
        "INTERACTION_CATALOG.md",
        "PATTERN_CARDS.md",
        "ADOPTION_DECISION_MATRIX.md",
        "ITERATION_LOG.md",
    ):
        if not (PKG / name).is_file():
            problems.append(f"缺少文件: {name}")

    sa = numbered_headings(read("SOURCE_ANALYSIS.md"))
    pc = read("PATTERN_CARDS.md")
    cards = set(re.findall(r"^## (BF-\d{2})", pc, re.M))

    # 1. § 交叉引用（ITERATION_LOG 允许叙述性提及，不做强校验）
    for f in sorted(PKG.glob("*.md")):
        if f.name == "ITERATION_LOG.md":
            continue
        for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            for m in re.finditer(r"§(\d+(?:\.\d+)?)", line):
                if m.group(1) not in sa:
                    problems.append(f"§ 引用无法解析: {f.name}:{i} §{m.group(1)}")

    # 2. BF 卡号引用
    for f in sorted(PKG.glob("*.md")):
        if f.name == "ITERATION_LOG.md":
            continue
        refs = set(re.findall(r"\bBF-\d{2}\b", f.read_text(encoding="utf-8")))
        for ref in sorted(refs - cards):
            problems.append(f"卡号无法解析: {f.name} → {ref}")

    # 3a. ADOPTION 矩阵行号与逐行决策
    ad = read("ADOPTION_DECISION_MATRIX.md")
    body, summary = ad.split("## 分桶汇总", 1)
    rows = [int(n) for n in re.findall(r"^\| (\d+) \|", body, re.M)]
    if rows != list(range(1, EXPECTED_ROWS + 1)):
        problems.append(f"矩阵行号不连续或不等于 1..{EXPECTED_ROWS}: {rows}")

    row_decisions: dict[str, list[int]] = {d: [] for d in DECISIONS}
    for line in body.splitlines():
        m = re.match(r"^\| (\d+) \|", line)
        if not m:
            continue
        cells = [c.strip() for c in line.split("|")]
        # cells: '', 行号, 机制, 模式卡, 决策, 理由, ''
        decision = cells[4] if len(cells) > 4 else ""
        if decision not in DECISIONS:
            problems.append(f"矩阵行 {m.group(1)} 决策列无法识别: {decision!r}")
            continue
        row_decisions[decision].append(int(m.group(1)))
        card_refs = re.findall(r"BF-\d{2}", cells[3] if len(cells) > 3 else "")
        for ref in card_refs:
            if ref not in cards:
                problems.append(f"矩阵行 {m.group(1)} 引用未知卡 {ref}")

    # 3c. 每张卡必须被矩阵至少引用一次（防止扩卡时漏加决策行）
    referenced_cards: set[str] = set()
    for line in body.splitlines():
        m = re.match(r"^\| (\d+) \|", line)
        if not m:
            continue
        cells = [c.strip() for c in line.split("|")]
        referenced_cards.update(re.findall(r"BF-\d{2}", cells[3] if len(cells) > 3 else ""))
    for card in sorted(cards - referenced_cards):
        problems.append(f"模式卡 {card} 未被 ADOPTION 矩阵任何行引用")

    # 3b. 分桶汇总表双向一致
    for m in re.finditer(r"^\| (\w+) \| (\d+) \| ([\d,]+) \|", summary, re.M):
        bucket, count, ids_text = m.group(1), int(m.group(2)), m.group(3)
        if bucket not in DECISIONS:
            problems.append(f"汇总表出现未知分桶: {bucket}")
            continue
        ids = [int(x) for x in ids_text.split(",")]
        actual = sorted(row_decisions[bucket])
        if len(ids) != count:
            problems.append(f"汇总 {bucket}: 计数 {count} 与行号清单长度 {len(ids)} 不符")
        if sorted(ids) != actual:
            problems.append(f"汇总 {bucket}: 行号清单 {sorted(ids)} 与逐行决策 {actual} 不符")

    total_summary = sum(int(m.group(1)) for m in re.finditer(r"^\| \w+ \| (\d+) \| [\d,]+ \|", summary, re.M))
    if total_summary != EXPECTED_ROWS:
        problems.append(f"汇总合计 {total_summary} != 矩阵行数 {EXPECTED_ROWS}")

    # 4. 计数声明与索引登记
    readme = read("README.md")
    if f"{EXPECTED_CARDS} 张模式卡" not in readme:
        problems.append(f"README 未声明 {EXPECTED_CARDS} 张模式卡")
    if f"{EXPECTED_ROWS} 项机制" not in readme:
        problems.append(f"README 未声明 {EXPECTED_ROWS} 项机制")
    if len(cards) != EXPECTED_CARDS:
        problems.append(f"实际模式卡数 {len(cards)} != 声明 {EXPECTED_CARDS}")

    research_index = (REPO / "docs" / "research" / "README.md").read_text(encoding="utf-8")
    docs_index = (REPO / "docs" / "index.md").read_text(encoding="utf-8")
    for label, text in (("docs/research/README.md", research_index), ("docs/index.md", docs_index)):
        if "beeftv-canvas-2026-09-27" not in text:
            problems.append(f"{label} 未登记本调研包条目")

    # 5. 锁定提交锚点防混淆：包内不得出现其他「锁定提交 xxxxxxx」短哈希
    for f in sorted(PKG.glob("*.md")):
        for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            for m in re.finditer(r"锁定提交 `([0-9a-f]{7,40})", line):
                if not m.group(1).startswith(LOCKED_SHORT):
                    problems.append(f"锁定提交锚点异常: {f.name}:{i} {m.group(1)}")

    # 6. SOURCE_ANALYSIS 结构防撞：编号标题与台账行号均不得重复
    sa_text = read("SOURCE_ANALYSIS.md")
    seen_headings: set[str] = set()
    for n in re.findall(r"^#{1,3}\s+(\d+(?:\.\d+)?)[.、\s]", sa_text, re.M):
        if n in seen_headings:
            problems.append(f"SOURCE_ANALYSIS 编号标题重复: §{n}")
        seen_headings.add(n)
    seen_rows: set[int] = set()
    for n in re.findall(r"^\| (\d+) \|", sa_text, re.M):
        k = int(n)
        if k in seen_rows:
            problems.append(f"SOURCE_ANALYSIS 台账行号重复: {k}")
        seen_rows.add(k)

    if problems:
        print("check-beeftv-research: 存在问题")
        for p in problems:
            print(f"- {p}")
        return 1
    print(f"check-beeftv-research: OK（卡 {len(cards)}/{EXPECTED_CARDS}，矩阵 {len(rows)}/{EXPECTED_ROWS} 行，分桶/引用/锚点一致）")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""校验任务深度评级在「账本 ↔ 索引分组 ↔ 首页表格」三处严格一致。

**为什么需要这道检查（M58 实测）**：`task-inventory.yml` 是任务的唯一源头，
`coverage` 字段驱动 `audit_manual.py` 的门禁（core/flagship 任务必须有截图）。
但评级会被**复制**到两个下游消费者——`10-tasks/README.md` 的分组小节标题，
和 `README.md` 任务指南表格的「深度」列。M58 发现 `use-prompt-library` 在账本里
是 `full`，却被两个下游都列为「简明」；`audit_manual.py` 只校验 coverage 取值
是否合法（白名单），不校验三处语义一致，于是一路绿灯放行。

这类漂移的代价：账本是权威、评级又决定门禁强度，读者看到的深度与实际门禁
强度对不上，且没有任何一道检查会报错。

本脚本把三处评级拉平核对：
1. 解析 `task-inventory.yml` 每个任务的 `id` → `coverage`（权威来源）
2. 解析 `10-tasks/README.md` 的「## 旗舰/完整/简明任务」分组 → 任务
3. 解析 `README.md` 任务指南表格的「深度」列（旗舰/完整/简明）→ 任务
4. 三者两两比对：同一任务在三处的评级必须相同

评级词表（与 audit_manual.py 的 TASK_COVERAGES 对齐的子集）：
  concise  = 简明
  full     = 完整
  flagship = 旗舰

退出码 0 表示三处评级一致，1 表示存在漂移或无法解析。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

INVENTORY = "task-inventory.yml"
INDEX = "10-tasks/README.md"
README = "README.md"

# 账本 coverage 取值 → 中文标签（三处共用的唯一映射）
COVERAGE_TO_LABEL = {
    "flagship": "旗舰",
    "full": "完整",
    "concise": "简明",
}
LABEL_TO_COVERAGE = {v: k for k, v in COVERAGE_TO_LABEL.items()}


def fail(problems: list[str]) -> int:
    for problem in problems:
        print(f"  [评级] {problem}")
    if problems:
        print(f"评级一致性校验失败：{len(problems)} 项")
        return 1
    return 0


def parse_inventory(text: str) -> tuple[dict[str, str], list[str]]:
    """从 task-inventory.yml 抽出 {task_id: coverage}，并返回解析告警。"""
    ratings: dict[str, str] = {}
    problems: list[str] = []
    current_id: str | None = None
    for line in text.splitlines():
        m_id = re.match(r"  - id: (\S+)", line)
        if m_id:
            current_id = m_id.group(1)
            continue
        m_cov = re.match(r"    coverage: (\S+)", line)
        if m_cov and current_id:
            value = m_cov.group(1)
            if value not in COVERAGE_TO_LABEL:
                problems.append(
                    f"{INVENTORY}: 任务 {current_id} 的 coverage={value} 不在词表 "
                    f"{sorted(COVERAGE_TO_LABEL)}"
                )
            ratings[current_id] = value
            current_id = None
    return ratings, problems


def parse_grouped_index(text: str) -> tuple[dict[str, str], list[str]]:
    """从 10-tasks/README.md 抽出 {task: 评级}，按「## 旗舰/完整/简明任务」小节判定。"""
    ratings: dict[str, str] = {}
    problems: list[str] = []
    current_label: str | None = None
    for line in text.splitlines():
        m_head = re.match(r"##\s*(.+?)\s*$", line)
        if m_head:
            raw = m_head.group(1)
            # 标题形如「旗舰任务」，需剥掉尾部「任务」再匹配词表
            label = raw[: -len("任务")] if raw.endswith("任务") else raw
            if label in LABEL_TO_COVERAGE:
                current_label = label
            elif "任务" in raw:
                problems.append(
                    f"{INDEX}: 分组标题「{raw}」不在词表 {sorted(LABEL_TO_COVERAGE)}"
                )
                current_label = None
            continue
        m_link = re.match(r"-\s*\[([^\]]+)\]\(([A-Za-z0-9._-]+\.md)\)", line)
        if m_link and current_label:
            task = Path(m_link.group(2)).stem
            ratings[task] = LABEL_TO_COVERAGE[current_label]
    return ratings, problems


def parse_readme_table(text: str) -> tuple[dict[str, str], list[str]]:
    """从 README.md 任务指南表格抽出 {task: 评级}，读「深度」列。"""
    ratings: dict[str, str] = {}
    problems: list[str] = []
    in_table = False
    for line in text.splitlines():
        # 定位任务指南表格：以「我想」表头开始
        if re.match(r"\|\s*我想", line):
            in_table = True
            continue
        if in_table and re.match(r"\|\s*-+", line):
            continue
        if in_table and not line.strip().startswith("|"):
            in_table = False
            continue
        if not in_table:
            continue
        m_cell = re.match(r"\|\s*([^|]+?)\s*\|\s*\[[^\]]+\]\((?:10-tasks/)?([A-Za-z0-9._-]+\.md)\)\s*\|\s*([^|]+?)\s*\|", line)
        if m_cell:
            task = Path(m_cell.group(2)).stem
            label = m_cell.group(3)
            if label in LABEL_TO_COVERAGE:
                ratings[task] = LABEL_TO_COVERAGE[label]
            else:
                problems.append(
                    f"{README}: 任务 {task} 的深度列「{label}」不在词表 {sorted(LABEL_TO_COVERAGE)}"
                )
    return ratings, problems


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    problems: list[str] = []

    inv_path = root / INVENTORY
    index_path = root / INDEX
    readme_path = root / README
    for path in (inv_path, index_path, readme_path):
        if not path.is_file():
            print(f"  [评级] 缺少文件 {path.name}")
            return 1

    inv_ratings, inv_problems = parse_inventory(inv_path.read_text(encoding="utf-8"))
    problems += inv_problems
    index_ratings, index_problems = parse_grouped_index(index_path.read_text(encoding="utf-8"))
    problems += index_problems
    readme_ratings, readme_problems = parse_readme_table(readme_path.read_text(encoding="utf-8"))
    problems += readme_problems

    if not inv_ratings:
        problems.append(f"{INVENTORY}: 未能解析出任何 coverage 评级")

    # 三处两两比对
    sources = [
        (INVENTORY, inv_ratings),
        (INDEX, index_ratings),
        (README, readme_ratings),
    ]
    for i, (name_a, ratings_a) in enumerate(sources):
        for name_b, ratings_b in sources[i + 1 :]:
            keys = set(ratings_a) | set(ratings_b)
            for task in sorted(keys):
                va = ratings_a.get(task)
                vb = ratings_b.get(task)
                if va is None:
                    problems.append(f"{task}: {name_a} 未收录该任务，{name_b} 记为「{COVERAGE_TO_LABEL.get(vb, vb)}」")
                elif vb is None:
                    problems.append(f"{task}: {name_b} 未收录该任务，{name_a} 记为「{COVERAGE_TO_LABEL.get(va, va)}」")
                elif va != vb:
                    problems.append(
                        f"{task}: 评级漂移——{name_a} 记为「{COVERAGE_TO_LABEL[va]}」，"
                        f"{name_b} 记为「{COVERAGE_TO_LABEL[vb]}」"
                    )

    if problems:
        return fail(problems)
    print(
        f"  [ ok ] 评级校验：{len(inv_ratings)} 个任务在账本/索引/首页表格三处评级一致"
        f"（{ {COVERAGE_TO_LABEL[v]: sum(1 for x in inv_ratings.values() if x == v) for v in sorted(set(inv_ratings.values()))} }）"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

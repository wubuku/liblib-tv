#!/usr/bin/env python3
"""校验 task-inventory.yml 的 screenshot_count 字段与 manifest 实数一致。

**为什么需要这道检查（M59 实测）**：账本 review_note 里用散文写着「截图 N 张
入 manifest」，但 N 长期无人回写——M59 实测 3 条写着数字的与实数不符
（create-nodes 2→5、manage-assets 10→13、use-agent 4→8），另有 10 条干脆
没写数字。这类"账本说 N 张、实际 M 张"的失修不会让任何现有门禁报错。

**为什么用字段而不是继续数散文**：一开始想直接正则抓 review_note 里的
"N 张"，但 M59 写回时发现——订正文字里同时含历史数字（"原共 10 张已过期"）
和正确现状（"实为 13 张"），取最后一个还是取第一个都会抓错。这正是 M54
「派生数据手工维护必然过期」与 M52「按点名改必然漏」的合流：与其用正则猜
散文里的数字，不如把数字变成**可机械解析的字段**，由脚本从 manifest 实测
回填，门禁只比字段。历史叙述保留在 review_note 里作审计轨迹，但不再参与校验。

本脚本做两组核对：
1. 每个任务都有 screenshot_count 字段（缺字段即 fail——那是没登记）
2. 字段值 == manifest 里该 task_id 的实际条目数（对不上即 fail）

退出码 0 表示账本与 manifest 一致，1 表示有失修。
用法：python3 scripts/check-inventory-freshness.py <手册目录>
"""

from __future__ import annotations

import collections
import re
import sys
from pathlib import Path

INVENTORY = "task-inventory.yml"
MANIFEST = "screenshots/manifest.yml"


def fail(problems: list[str]) -> int:
    for problem in problems:
        print(f"  [账本新鲜度] {problem}")
    if problems:
        print(f"账本新鲜度校验失败：{len(problems)} 项")
        return 1
    return 0


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    problems: list[str] = []

    inv_path = root / INVENTORY
    mf_path = root / MANIFEST
    for path in (inv_path, mf_path):
        if not path.is_file():
            print(f"  [账本新鲜度] 缺少文件 {path}")
            return 1

    # manifest 实数：task_id -> 条目数
    mf_text = mf_path.read_text(encoding="utf-8")
    by_task: collections.Counter = collections.Counter(
        re.findall(r"- file: \S+\n\s+task_id: (\S+)", mf_text)
    )

    # 账本：按任务块抽 screenshot_count
    inv_text = inv_path.read_text(encoding="utf-8")
    declared: dict[str, int] = {}
    cur: str | None = None
    for line in inv_text.splitlines():
        m_id = re.match(r"  - id: (\S+)", line)
        if m_id:
            cur = m_id.group(1)
            continue
        m_cnt = re.match(r"    screenshot_count: (\d+)", line)
        if m_cnt and cur:
            declared[cur] = int(m_cnt.group(1))
            cur = None

    if not declared:
        problems.append(f"{INVENTORY}: 未能解析出任何 screenshot_count 字段")

    for task in sorted(set(declared) | set(by_task)):
        got = declared.get(task)
        real = by_task.get(task, 0)
        if got is None:
            problems.append(
                f"{task}: 账本缺 screenshot_count 字段（manifest 实为 {real} 张）"
            )
        elif got != real:
            problems.append(
                f"{task}: 账本 screenshot_count={got}，但 manifest 实为 {real} 张"
                f"（差 {real - got:+d}）——"
                f"新增截图后回填该字段"
            )

    if problems:
        return fail(problems)
    print(
        f"  [ ok ] 账本新鲜度：{len(declared)} 个任务的 screenshot_count "
        f"与 manifest 实数（合计 {sum(by_task.values())} 张）逐条一致"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

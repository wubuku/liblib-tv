#!/usr/bin/env python3
"""账本 YAML 可解析性校验（第十五道门禁，M123 新增）。

**背景（M123 是一次真实故障，不是一次假想）**：写 M123 的分析脚本时用
`yaml.safe_load` 读 `task-inventory.yml`，直接崩在

    task-inventory.yml:143, column 340: mapping values are not allowed here

原因很朴素：那几行的 `review_note` 里**嵌了带半角 ` : ` 的源码片段**，例如

    {menu.type === "node" ? <复制> : null}
    `text: "text.chat"`
    duplicate: "复制"

YAML 的 plain scalar 一旦出现「冒号 + 空格」就被当成 `key: value`，于是整个文件
**根本不是合法 YAML**。同样的问题还有另外两处（163 行、263 行），都是早期批次写进去的。

**为什么此前一直没被发现**：**十四道门禁里没有任何一道 import yaml**——它们全都用
正则按行解析账本（见 `grep -l yaml scripts/*.py` 无输出）。正则读得动坏掉的 YAML，
所以「门禁全绿」与「账本是合法 YAML」是两件事，而后者从未被检查过。

后果不是构建失败，而是**任何将来想用标准 YAML 工具消费这份账本的人都会当场崩掉**，
而且崩在离真正原因（第 340 列）很远的地方。

本门禁只做四件事，全部是**不涉及语义的结构断言**：

1. `yaml.safe_load` 必须成功（**这条就是抓上面那个故障的**）；
2. 顶层必须是映射或序列，且能取出任务列表；
3. 每个任务必须有非空 `id`，且 `id` 不重复——**重复 id 会让按 id 查找的工具静默取到第一条**；
4. 每条 evidence 的 `type` 必须在已知集合内。

**它不检查 note 内容写得对不对**，那是 `check-claims.py` 的事。

**降级**：本机没装 PyYAML 时**显式跳过并说明**，不假装通过、也不假装失败。

用法：

    python3 scripts/check-inventory-yaml.py .
"""

from __future__ import annotations

import sys
from pathlib import Path

INVENTORY = "task-inventory.yml"
# 账本实际使用的证据类型只有这三种：runtime（运行时取证）、static（源码 file:line）、
# boundary（如实记下的边界/未实测项）。
#
# 这个集合是**故意写窄**的：将来新增类型而没同步这里，门禁会当场变红。
# 那正是它该做的——把「新增证据类型」变成一件需要显式确认的事，
# 而不是悄悄混进来让下游工具按已知集合处理时静默失配。
#
# （第一版这里写的是 runtime/static/derived/source，结果账本里那个 `boundary`
#  当场把门禁顶红了——der 与 source 是我按常见约定臆想的，账本里并不存在。
#  **门禁的判据集合必须从实际数据里数出来，不能照着惯例编。**）
KNOWN_EVIDENCE_TYPES = {"runtime", "static", "boundary"}


def main(argv: list[str]) -> int:
    root = Path(argv[1] if len(argv) > 1 else ".").resolve()
    path = root / INVENTORY

    if not path.is_file():
        print(f"[FAIL] 找不到账本 {INVENTORY}")
        return 1

    try:
        import yaml  # noqa: PLC0415
    except ImportError:
        print("  [skip] 本机没有 PyYAML，跳过 YAML 可解析性校验")
        print(f"[ ok ] 账本 YAML 校验：已跳过（缺 PyYAML，无法判定 {INVENTORY} 是否为合法 YAML）")
        return 0

    raw = path.read_text(encoding="utf-8")
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        print("[FAIL] 账本不是合法 YAML：")
        mark = getattr(exc, "problem_mark", None)
        if mark is not None:
            print(f"    位置：第 {mark.line + 1} 行第 {mark.column + 1} 列")
            lines = raw.split("\n")
            lo, hi = max(0, mark.line - 1), min(len(lines), mark.line + 2)
            for n in range(lo, hi):
                flag = "  ← 报错行" if n == mark.line else ""
                print(f"    {n + 1:>5} | {lines[n][:160]}{flag}")
        print(f"    原因：{getattr(exc, 'problem', exc)}")
        print()
        print("    这是**真实故障**，通常因为某个值里嵌了带半角「冒号 + 空格」的源码片段，例如")
        print("    `{a === \"b\" ? x : null}`、`key: \"value\"`。YAML 的 plain scalar 一旦")
        print("    出现「冒号 + 空格」就会被当成 key: value。")
        print("    修法：把该值用**单引号**整体包起来（单引号内的半角双引号无需转义）。")
        return 1

    # ② 顶层结构：要么是 {tasks: [...]}，要么直接是 [...]
    if isinstance(data, dict):
        tasks = data.get("tasks")
    elif isinstance(data, list):
        tasks = data
    else:
        print(f"[FAIL] 账本顶层是 {type(data).__name__}，既不是映射也不是序列")
        return 1
    if not isinstance(tasks, list) or not tasks:
        print(f"[FAIL] 账本里取不到任务列表（顶层是 {type(data).__name__}）")
        return 1

    # ③ id 非空且唯一
    ids: list[str] = []
    for i, task in enumerate(tasks, 1):
        if not isinstance(task, dict):
            print(f"[FAIL] 第 {i} 个任务不是映射，而是 {type(task).__name__}")
            return 1
        tid = task.get("id")
        if not isinstance(tid, str) or not tid.strip():
            print(f"[FAIL] 第 {i} 个任务缺少非空字符串 id")
            return 1
        ids.append(tid)

    dupes = sorted({t for t in ids if ids.count(t) > 1})
    if dupes:
        print("[FAIL] 任务 id 重复：")
        for d in dupes:
            print(f"    {d}")
        print("    重复 id 会让「按 id 查任务」的工具静默取到第一条，后面的永远读不到。")
        return 1

    # ④ evidence 的 type 必须在已知集合内
    bad_types: list[tuple[str, str]] = []
    n_ev = 0
    for task in tasks:
        for ev in task.get("evidence") or []:
            n_ev += 1
            if not isinstance(ev, dict):
                continue
            t = ev.get("type")
            if t not in KNOWN_EVIDENCE_TYPES:
                bad_types.append((task["id"], str(t)))
    if bad_types:
        print("[FAIL] evidence 的 type 不在已知集合内：")
        for tid, t in bad_types:
            print(f"    {tid}: type={t!r}")
        print(f"    已知取值：{', '.join(sorted(KNOWN_EVIDENCE_TYPES))}")
        return 1

    print(f"[ ok ] 账本 YAML 校验：{INVENTORY} 是合法 YAML，{len(tasks)} 个任务 id 唯一，{n_ev} 条证据 type 合法")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

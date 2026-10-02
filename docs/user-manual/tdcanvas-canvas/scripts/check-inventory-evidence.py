#!/usr/bin/env python3
"""账本证据一致性校验（第十七道门禁，M133 新增）。

**背景（M133 查的是一次真实的记账漏洞，不是一次假想故障）**：
`task-inventory.yml` 里每个任务有两块记录——

- `evidence`：结构化字段，**每条都带 `type`**（static / runtime / boundary），
  且 `check-inventory-yaml.py` 会校验 type 在已知集合内、id 不重复；
- `review_note`：自由文本，**门禁一个字都不看**。

结果是：M101/M102/M103/M104 四个批次的运行时取证（组的徽标计数、删组不删成员、
复制粘贴的归属语义、组内连线），以及 M60/M78 两个批次的运行时取证，**全部只写在
`review_note` 里**，`evidence` 始终只有一条 `static`。**受校验的字段说「只有源码证据」，
不受校验的字段说「实测过好几轮」——账本自己跟自己打架。**

**为什么这条必须变成门禁**：光修一次没用。下一个批次只要把运行时结论写进
`review_note` 而忘了同步 `evidence`，同样的漂移会重新长出来，而且**从产物和门禁输出里
完全看不出来**（构建照样绿）。

**本门禁只做一件事**：读 `review_note`，若它声称做过运行时/实测，而 `evidence` 里
**一条 `runtime` 或 `boundary` 都没有**，就判失败。

**否定形态怎么办**：「未实测」里也含「实测」两个字，直接匹配会误报。
所以**触发词前面 3 个字符内出现「未」就不算触发**——这个否定形态是从现有 15 个任务的
真实数据里数出来的（`review_note` 与 `evidence` 里只出现了 `未实测` 一种），
**不是照惯例编的**。将来出现新的否定写法，本门禁会误报，那时按「判据集合要从实际数据
数出来」的原则补进去即可。

**它不检查 note 内容写得对不对**，那是 `check-claims.py` 的事。

用法：

    python3 scripts/check-inventory-evidence.py .
"""

from __future__ import annotations

import sys
from pathlib import Path

TRIGGERS = ("实测", "运行时")
NEGATION_WINDOW = 3
NEGATION_MARK = "未"
RUNTIME_TYPES = {"runtime", "boundary"}


def main(argv: list[str]) -> int:
    root = Path(argv[1] if len(argv) > 1 else ".").resolve()
    inv = root / "task-inventory.yml"
    if not inv.exists():
        print("[skip] 账本不存在，跳过证据一致性校验")
        return 0

    try:
        import yaml
    except ImportError:
        print("[skip] 本机没装 PyYAML，无法按语义读账本，显式跳过（不假装通过）")
        return 0

    try:
        data = yaml.safe_load(inv.read_text(encoding="utf-8"))
    except Exception as e:  # YAML 坏了是 check-inventory-yaml.py 的职责，这里不重复报
        print(f"[skip] 账本不是合法 YAML，交给第十五道门禁处理：{e}")
        return 0

    tasks = data.get("tasks") if isinstance(data, dict) else data
    if not isinstance(tasks, list):
        print("[skip] 取不到任务列表，跳过")
        return 0

    problems: list[str] = []
    for t in tasks:
        if not isinstance(t, dict):
            continue
        tid = t.get("id", "(无 id)")
        note = t.get("review_note") or ""
        types = {e.get("type") for e in (t.get("evidence") or []) if isinstance(e, dict)}

        claimed = []
        for w in TRIGGERS:
            start = 0
            while True:
                i = note.find(w, start)
                if i < 0:
                    break
                window = note[max(0, i - NEGATION_WINDOW):i]
                if NEGATION_MARK not in window:
                    claimed.append(w)
                start = i + 1

        if claimed and not (types & RUNTIME_TYPES):
            problems.append(
                f"{tid}：review_note 里有「{'、'.join(sorted(set(claimed)))}」的表述，"
                f"但 evidence 只有 {sorted(types) or '（空）'}，"
                f"一条 runtime / boundary 都没有"
            )

    if problems:
        print("[FAIL] 账本证据一致性校验未通过：")
        for p in problems:
            print(f"    [记账漂移] {p}")
        print("  记账漂移 = 运行时结论只写在不受门禁校验的 review_note 里，")
        print("  受校验的 evidence 却仍说只有源码证据。补上 runtime 条目，")
        print("  或把 review_note 里的说法改回与 evidence 一致。")
        return 1

    n_runtime = sum(
        1 for t in tasks if isinstance(t, dict)
        for e in (t.get("evidence") or []) if isinstance(e, dict) and e.get("type") in RUNTIME_TYPES
    )
    print(
        f"[ ok ] 证据一致性校验：{len(tasks)} 个任务里，"
        f"凡 review_note 声称实测/运行时的都有对应的 runtime 或 boundary 条目"
        f"（共 {n_runtime} 条）"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

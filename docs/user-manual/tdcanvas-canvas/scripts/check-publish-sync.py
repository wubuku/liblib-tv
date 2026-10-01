#!/usr/bin/env python3
"""发布文档一致性校验：`PUBLISH.md` 描述的门禁集合必须与 `build-site.sh` 实际调用的一致。

背景（M106）：`PUBLISH.md` 用一整节表格描述"构建时的门禁"——门禁叫什么、拦什么、
哪一批发现的。这张表是**维护者据以排查的唯一索引**：构建挂了先看它。

但这张表是**手写的**，脚本才是事实源，两者之间**没有任何机制相连**。实测本批
打开它就抓到一处已经漂移的描述（标题写"十道门禁"，表里却列了 12 行）。这类漂移
的特点是**永远不会自己报错**：脚本照跑、门禁照过，只有照着文档排查的人会被误导。

本门禁做两件事：

1. 从 `build-site.sh` 里抽出**实际被调用**的 `scripts/*.py`（排除纯工具脚本
   `update-build-stats.py`，它不是门禁）；
2. 从 `PUBLISH.md` 的门禁表首列抽出**文档声称**的门禁名；
3. 断言两个集合**完全相等**，并单独核对 `build-site.sh` 声明的步骤总数与
   `PUBLISH.md` 步骤表里的行数。

**为什么用"集合相等"而不是"文档 ⊇ 脚本"**：少写一个门禁同样有害——排查的人
按文档走，漏掉的那道门禁根本不会出现在他的排查清单里。多写一个则是把不存在的
门禁写进文档，一样是误导。两个方向都得拦住。

用法：

    python3 scripts/check-publish-sync.py .
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

PUBLISH = "PUBLISH.md"
BUILD = "build-site.sh"

# 工具脚本而非门禁：它只负责回填 README 的构建统计，不拦任何东西
NOT_GATES = {"update-build-stats.py"}


def strip_comments(sh: str) -> str:
    """去掉整行注释。

    **这不是洁癖，是本门禁的第一个真实陷阱**：M106 实测 `audit_manual.py` 在
    `build-site.sh` 里出现 3 次，**全部在注释里**（都是解释历史事故的长注释），
    构建脚本从来没有执行过它。若不剥注释，它会被当成"脚本调用的门禁"，
    门禁表里那行就永远查不出问题——而事实上 PUBLISH.md 把它同时写成
    「手动单跑的审计步骤」和「构建时的门禁」，是**文档内部自相矛盾**。
    """
    return "\n".join(
        line for line in sh.splitlines() if not line.lstrip().startswith("#")
    )


def gates_in_build(build_sh: str) -> set[str]:
    body = strip_comments(build_sh)
    names = {Path(m).name for m in re.findall(r"scripts/[A-Za-z0-9_.-]+\.py", body)}
    return {n for n in names if n not in NOT_GATES}


def gates_in_publish(text: str) -> set[str]:
    """只取「构建时的门禁」那张表的**首列**——``脚本名`` 单元格。

    按表头定位到那一节再取，避免把文档里别处提到的脚本名算进来。
    """
    start = text.find("### 构建时的")
    if start < 0:
        return set()
    body = text[start:]
    names: set[str] = set()
    for line in body.splitlines():
        m = re.match(r"^\|\s*`([A-Za-z0-9_.-]+\.py)`\s*\|", line)
        if m:
            names.add(m.group(1))
    return names


def steps_in_build(build_sh: str) -> int:
    total = re.findall(r"步骤 \d+/(\d+)", build_sh)
    return max((int(n) for n in total), default=0)


def steps_in_publish(text: str) -> int:
    """步骤表里形如 `| 1/6 | 环境检查 | ...` 的行数。"""
    return len(re.findall(r"^\|\s*\d+/(\d+)\s*\|", text, re.M))


def main(argv: list[str]) -> int:
    root = Path(argv[1] if len(argv) > 1 else ".").resolve()
    pub = root / PUBLISH
    build = root / BUILD

    for p in (pub, build):
        if not p.exists():
            print(f"[FAIL] 找不到 {p.name}")
            return 1

    text = pub.read_text(encoding="utf-8")
    sh = build.read_text(encoding="utf-8")

    real = gates_in_build(sh)
    doc = gates_in_publish(text)

    ok = True

    missing = sorted(real - doc)          # 脚本跑了、文档没写
    extra = sorted(doc - real)            # 文档写了、脚本没跑
    if missing:
        print("[FAIL] 以下门禁被 build-site.sh 调用，但 PUBLISH.md 的门禁表里没有：")
        for n in missing:
            print(f"    {n}")
        ok = False
    if extra:
        print("[FAIL] 以下门禁写在 PUBLISH.md 的门禁表里，但 build-site.sh 并没有调用：")
        for n in extra:
            print(f"    {n}")
        ok = False

    steps_real = steps_in_build(sh)
    steps_doc = steps_in_publish(text)
    if steps_real and steps_doc and steps_real != steps_doc:
        print(f"[FAIL] 构建步骤数不一致：build-site.sh 声明 {steps_real} 步，"
              f"PUBLISH.md 步骤表写了 {steps_doc} 行")
        ok = False

    if not ok:
        print("    门禁表是维护者排查的唯一索引，两边对不上会直接误导排查。")
        return 1

    print(f"[ ok ] 发布文档一致性：{len(real)} 道门禁的文档与脚本集合一致"
          f"（构建步骤 {steps_real} 步，文档 {steps_doc} 行）")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

#!/usr/bin/env python3
"""门禁「零命中处理」一致性校验（第二十道门禁，M151 新增）。

**背景（M151 查的是一次真实的静默放行，不是一次假想故障）**：

M150 发现：把 `task-inventory.yml` 抽走后，依赖它的五道门禁里
**四道 exit=1「缺少文件」，只有 `check-inventory-evidence` 打印 `[skip]` 并 exit=0**——
构建输出里它那一行读起来就是「ok」，**而实际上它什么都没查**。
这正是 `PUBLISH.md`「第一条判据」点名的形态：**「没找到」绝不能等同于「不用找了」**。

**但 M151 全量复验后发现：那是唯一一处**。为免下批重做这套实验（抽走输入 → 对比行为），
本门禁把它固化成常设检查。

**它做什么**：对每一组「输入文件 ↔ 门禁」，抽走输入、观察门禁是报错还是**静默放行**。
**静默放行 = 该门禁声称通过、实际什么都没查**，这是要抓的东西。

**它不做的一件事（必须说清）**：**配对必须由人工给出，不能靠 grep 猜。**
M151 第一版实验用 grep 从源码里提取「依赖的文件名」，结果把
**文档字符串和注释里的文件名也提取了出来**——
`check-anchors` / `check-tables` 明明扫的是全部 md，却被配成「依赖 PUBLISH.md」，
抽走 PUBLISH 后它们 exit=0，被误判成「静默放行」。
**这是实验设计的错，不是门禁的错。**
所以下面的 `PAIRS` 是**人工核实的真实依赖关系**，并在 `CONFIRMED_CLEAN` 里记下了
「曾经误判、后经核实为真豁免」的若干条——**留着它们，是为了让下批不要再误判一次**。

用法：

    python3 scripts/check-gate-silence.py <手册根> [--root <实验用副本>]
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# (被抽走的输入, 门禁) —— 人工核实：这道门禁真的读这个文件
PAIRS: list[tuple[str, str]] = [
    ("task-inventory.yml", "check-inventory-yaml"),
    ("task-inventory.yml", "check-inventory-freshness"),
    ("task-inventory.yml", "check-ratings"),
    ("task-inventory.yml", "check-ledger-pin"),
    ("task-inventory.yml", "check-inventory-evidence"),
    ("task-inventory.yml", "check-structure"),
    ("screenshots/manifest.yml", "check-inventory-freshness"),
    ("screenshots/manifest.yml", "check-structure"),
    ("PUBLISH.md", "check-publish-sync"),
    ("PUBLISH.md", "check-probe-contracts"),
    ("10-tasks/README.md", "check-ratings"),
    ("10-tasks/README.md", "check-structure"),
    ("SOURCE_OBSERVATIONS.md", "check-ledger-pin"),
    ("build-site.sh", "check-publish-sync"),
]

# 曾被误判为「静默放行」、经核实确属真豁免的配对。
# 留在这里，是为了下批别再把注释里的文件名当成依赖。
CONFIRMED_CLEAN: list[tuple[str, str, str]] = [
    ("PUBLISH.md", "check-anchors",
     "扫的是全部 md，PUBLISH 只是顺带被扫到；源码里出现 PUBLISH 是在文档字符串里"),
    ("PUBLISH.md", "check-tables",
     "同上——扫全部 md，源码命中在文档字符串"),
    ("SOURCE_OBSERVATIONS.md", "check-source-refs",
     "源码命中在文档字符串，不构成依赖"),
    ("SOURCE_OBSERVATIONS.md", "check-retractions",
     "同上"),
    ("build-site.sh", "check-structure",
     "源码里出现 build-site.sh 是在文件头的说明段，实际只读 .vitepress/config.mjs"),
]


def run_gate(root: Path, gate: str) -> int:
    done = subprocess.run(
        [sys.executable, str(root / "scripts" / f"{gate}.py"), str(root)],
        capture_output=True,
        text=True,
    )
    return done.returncode


def main() -> int:
    source = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    if not (source / "scripts").is_dir():
        print(f"  [静默] 找不到脚本目录：{source}")
        return 1

    silent: list[str] = []
    checked = 0
    for dep, gate in PAIRS:
        target = source / dep
        script = source / "scripts" / f"{gate}.py"
        if not target.exists() or not script.exists():
            print(f"  [静默] 跳过 {gate} ← {dep}（文件不存在，无法做抽走实验）")
            continue
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / "copy"
            shutil.copytree(source, work, ignore=shutil.ignore_patterns(
                "node_modules", ".vitepress", ".git", "__pycache__"))
            (work / dep).unlink()
            checked += 1
            code = run_gate(work, gate)
        if code == 0:
            silent.append(f"{dep} 被抽走后，{gate} 仍 exit=0 —— 声称通过，实际什么都没查")

    for line in silent:
        print(f"  [静默] {line}")
    if silent:
        print(
            f"门禁静默放行校验失败：{len(silent)}/{checked} 组存在「输入没了仍报通过」。"
            "缺 PyYAML 等环境类跳过可以保留，但**措辞必须是「未执行」而不是「通过」**。"
        )
        return 1
    print(f"  [ ok ] 门禁静默放行校验：{checked} 组「抽走输入」实验中无一例静默通过")
    print(
        f"         （另有 {len(CONFIRMED_CLEAN)} 组经人工核实为真豁免，已记在脚本头，勿重复误判）"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

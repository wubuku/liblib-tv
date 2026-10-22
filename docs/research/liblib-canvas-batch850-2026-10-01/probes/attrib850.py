#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 850 受控对照：把本批改过的源码**按字节换回 HEAD** ⟹ ⟹ 重跑旧门禁
⟹ ⟹ 看读数**逐条有没有变**。

★★ **为什么要连跑两遍**：736 的 **C8**（两契约互斥）盯的是**焦点事件**的计数
⟹ ⟹ 它对**时序**敏感 ⟹ ⟹ 4317 多人共用 ⟹ ⟹ 偶发会差一条
⟹ ⟹ ★ 「**一轮的差**」不能直接当因果 ⟹ ⟹ 必须复跑再判。

## ★★ 本批额外盯 batch 840

★ 本批把中列的**层级**改了（图区多两层包裹）⟹ ⟹ 且把 `.ce-preview-tools`
从「left/top 绝对定位」改成「left:50%/bottom:16px 居中」
⟹ ⟹ 而 840 的门禁**正在比** `.ce-preview-tools`／`.ce-figure`／`.ce-tool` 的几何
⟹ ⟹ ⟹ 所以 840 必须**在 HEAD 与工作副本上读数逐条完全相同**
⟹ ⟹ ⟹ 不同 ⟹ ⟹ 就是本批**破坏**了 840 已经对照过的几何 ⟹ ⟹ 那要迁移。
"""
import hashlib
import pathlib
import subprocess
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")

# ★ 本批改过的**被跟踪**文件（源码）
CHANGED = [
    "src/components/CharacterEditorPanel.tsx",
    "src/components/character-studio.css",
]
# ★ 旧账目标（历史批次）
TARGETS = ["736", "748", "749", "782"]
# ★ 本批**动过其比对选择器**的门禁（⟹ ⟹ 读数必须与 HEAD **逐条相同**）
WATCH = ["840"]


def sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run(batch: str) -> str:
    script = ROOT / ("scripts/verify-liblib-batch%s.py" % batch)
    r = subprocess.run([sys.executable, str(script)], capture_output=True,
                       text=True, timeout=3600, cwd=str(ROOT))
    out = (r.stdout or "") + (r.stderr or "")
    tail = [ln for ln in out.splitlines() if ln.strip()][-2:]
    return "rc=%d | %s" % (r.returncode, " ／ ".join(t.strip() for t in tail))


def run_twice(batch: str) -> str:
    """★ 连跑**两遍** ⟹ ⟹ 取**第二遍**的读数（★ 见模块 docstring）。"""
    first = run(batch)
    second = run(batch)
    return "第1遍 %s  ⟹ 第2遍 %s" % (first, second)


def main():
    backups = {}
    before = {}
    for rel in CHANGED:
        p = ROOT / rel
        backups[p] = p.read_bytes()
        before[p] = sha(p)
    try:
        subprocess.run(["git", "checkout", "--"] + CHANGED, cwd=str(ROOT), check=True)
        print("已换回 HEAD（%d 个文件）\n" % len(CHANGED))
        for b in TARGETS:
            print("HEAD 上 %s ⟹ %s" % (b, run_twice(b)))
        for b in WATCH:
            print("HEAD 上 %s ⟹ %s" % (b, run_twice(b)))
    finally:
        for p, data in backups.items():
            p.write_bytes(data)
        for rel in CHANGED:
            p = ROOT / rel
            if sha(p) != before[p]:
                raise SystemExit("复原失败：%s 的 SHA-256 对不上" % p)
        print("\n已按 SHA-256 逐字节复原")
    print("\n=== 本批工作副本上（用于对照）===")
    for b in TARGETS:
        print("本批 %s ⟹ %s" % (b, run_twice(b)))
    for b in WATCH:
        print("本批 %s ⟹ %s" % (b, run_twice(b)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

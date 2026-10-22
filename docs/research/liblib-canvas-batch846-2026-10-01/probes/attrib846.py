#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 846 受控对照实验：把本批改动的文件**换回 HEAD** ⟹ 重跑旧账门禁 ⟹ 比对。

★★ 为什么必须做：回归跑出来的**红**，不能直接算成本批的锅 —— 有的红是**旧账**
   （判据的期望值已经过时）。⟹ 正解是**受控对照**：
     ① 把本批改过的文件按**字节**备份（记 SHA-256）；
     ② `git checkout --` 换回 HEAD 版本；
     ③ 重跑同一条门禁；
     ④ 按 SHA-256 **逐字节复原**。
   ⟹ 「HEAD 上也红」 ⟹ 旧账；「HEAD 上绿、现在红」 ⟹ 本批的锅。

★ 不用 stash、不用 worktree（★ 本仓库有他人未提交的 WIP ⟹ stash 会卷进去）。

★ 本批**额外**对照 840／841／842／843：它们在 batch 846 时**迁移**了
  「未实现的那一段」的断言（★ 第四段已实现 ⟹ ⟹ 改盯第五段）
  ⟹ ⟹ 现在应当**全绿**。

⚠️ ★ 只换回**源码**（两个文件）⟹ ⟹ **门禁脚本**与**探针**保持本批的版本
   ⟹ ⟹ 否则 840–843 读的还是旧键名（`F2_第四段` 等）⟹ ⟹ 必然读不到 ⟹ ⟹ 那不是对照
   ⟹ ⟹ ⟹ ★ 换言之：**迁移本身**也要归因 ⟹ ⟹ 见下面「MIGRATED」的说明。
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
# ★ 本批**连带迁移**的四个门禁（应当全绿）
MIGRATED = ["840", "841", "842", "843"]


def sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run(batch: str) -> str:
    script = ROOT / ("scripts/verify-liblib-batch%s.py" % batch)
    r = subprocess.run([sys.executable, str(script)], capture_output=True,
                       text=True, timeout=1800, cwd=str(ROOT))
    out = (r.stdout or "") + (r.stderr or "")
    tail = [ln for ln in out.splitlines() if ln.strip()][-2:]
    return "rc=%d | %s" % (r.returncode, " ／ ".join(t.strip() for t in tail))


def run_twice(batch: str) -> str:
    """★ 连跑**两遍** ⟹ ⟹ 取**第二遍**的读数。

    ★★ 为什么：736 的 **C8**（两契约互斥）盯的是**焦点事件**的计数
    ⟹ ⟹ 它对**时序**敏感 ⟹ ⟹ 4317 多人共用 ⟹ ⟹ 偶发会差一条
    ⟹ ⟹ ★ batch 846 的 attrib 第一轮就踩到了：HEAD 上 6/10、工作副本上 5/10
    ⟹ ⟹ 重跑三遍都是 6/10 ⟹ ⟹ 那 5/10 是**偶发波动**，不是本批的锅
    ⟹ ⟹ ★ **「一轮的差」不能直接当因果** ⟹ ⟹ 必须复跑再判。
    """
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
    print("\n=== 本批连带迁移的四个门禁（应当全绿）===")
    for b in MIGRATED:
        print("本批 %s ⟹ %s" % (b, run(b)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

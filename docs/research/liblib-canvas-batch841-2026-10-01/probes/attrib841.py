#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 841 受控对照实验：把本批改动的文件**换回 HEAD** ⟹ 重跑 736／748／749／782 ⟹ 比对。

★★ 为什么必须做：回归跑出来的**红**，不能直接算成本批的锅 —— 有的红是**旧账**
   （判据的期望值已经过时）。⟹ 正解是**受控对照**：
     ① 把本批改过的文件按**字节**备份（记 SHA-256）；
     ② `git checkout --` 换回 HEAD 版本；
     ③ 重跑同一条门禁；
     ④ 按 SHA-256 **逐字节复原**。
   ⟹ 「HEAD 上也红」 ⟹ 旧账；「HEAD 上绿、现在红」 ⟹ 本批的锅。

★ 不用 stash、不用 worktree（★ 本仓库有他人未提交的 WIP ⟹ stash 会卷进去）。
"""
import hashlib
import pathlib
import subprocess
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")

# ★ 本批改过的**被跟踪**文件（源码）
CHANGED = [
    "src/components/CharacterEditorPanel.tsx",
]
TARGETS = ["736", "748", "749", "782"]


def sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run(batch: str) -> str:
    script = ROOT / ("scripts/verify-liblib-batch%s.py" % batch)
    r = subprocess.run([sys.executable, str(script)], capture_output=True,
                       text=True, timeout=1800, cwd=str(ROOT))
    out = (r.stdout or "") + (r.stderr or "")
    tail = [ln for ln in out.splitlines() if ln.strip()][-3:]
    return "rc=%d | %s" % (r.returncode, " ／ ".join(t.strip() for t in tail))


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
            print("HEAD 上 %s ⟹ %s" % (b, run(b)))
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
        print("本批 %s ⟹ %s" % (b, run(b)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

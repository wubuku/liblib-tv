#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 851 受控对照：把本批改过的源码**按字节换回 HEAD** ⟹ ⟹ 重跑旧门禁
⟹ ⟹ 看读数**逐条有没有变**。

★★ **为什么要连跑两遍**：换回源码后 4317 要热更 ⟹ ⟹ 第一次跑有可能赶上热更中途
⟹ ⟹ ★ 「**一轮的差**」不能直接当因果 ⟹ ⟹ 必须复跑再判。

## ★ 本批盯哪些门禁

★ 本批改过两处**被跟踪**的源码：

- `src/components/director/DirectorViewport.tsx`
  （新增快捷键控制器；`OrbitControls` 的 target 从字面量改成 state；
  `DirectorCameraSnapshotBridge` 的导演视角 target 改成读真实 orbit 中心；新增三个 `data-` 属性）
- `src/components/director/directorViewportMath.ts`（新增两个纯函数，未删改既有导出）

★ 因此必须**在 HEAD 与工作副本上读数逐条完全相同**的门禁：

- `830` 导演台快捷键面板（★ 本批的靶子背景）
- `831` 快捷键对话框
- `543` 重置视角（★ 本批改的就是这条路径）
- `840` 角色编辑器（本批**没碰**它 ⟹ ⟹ 属「连带没坏」）
- `850` 上一批（本批**没碰**角色编辑器 ⟹ ⟹ 属「连带没坏」）

★ 另跑四条**旧账**（736／748／749／782）⟹ ⟹ 它们在 HEAD 上也红 ⟹ ⟹ **不是本批引入的**。
"""
import hashlib
import pathlib
import subprocess
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")

CHANGED = [
    "src/components/director/DirectorViewport.tsx",
    "src/components/director/directorViewportMath.ts",
]
TARGETS = ["736", "748", "749", "782"]
WATCH = ["830", "831", "543", "840", "850"]


def sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run(batch: str) -> str:
    script = ROOT / ("scripts/verify-liblib-batch%s.py" % batch)
    if not script.exists():
        return "（无此门禁）"
    r = subprocess.run([sys.executable, str(script)], capture_output=True,
                       text=True, timeout=3600, cwd=str(ROOT))
    out = (r.stdout or "") + (r.stderr or "")
    tail = [ln for ln in out.splitlines() if ln.strip()][-2:]
    return "rc=%s | %s" % (r.returncode, " ／ ".join(t.strip() for t in tail))


def run_twice(batch: str) -> str:
    first = run(batch)
    second = run(batch)
    return "第1遍 %s  ⟹ 第2遍 %s" % (first, second)


def main() -> int:
    backups = {}
    before = {}
    for rel in CHANGED:
        p = ROOT / rel
        backups[p] = p.read_bytes()
        before[p] = sha(p)
    head_reads = {}
    try:
        subprocess.run(["git", "checkout", "--"] + CHANGED, cwd=str(ROOT), check=True)
        print("已换回 HEAD（%d 个文件）\n" % len(CHANGED))
        for b in TARGETS:
            head_reads[b] = run_twice(b)
            print("HEAD 上 %s ⟹ %s" % (b, head_reads[b]), flush=True)
        for b in WATCH:
            head_reads[b] = run_twice(b)
            print("HEAD 上 %s ⟹ %s" % (b, head_reads[b]), flush=True)
    finally:
        for p, data in backups.items():
            p.write_bytes(data)
        print("\n已复原工作副本")
        for p in backups:
            assert sha(p) == before[p], "★ 复原后哈希不一致：%s" % p
            print("  复原校验 OK %s %s" % (p.name, sha(p)[:16]))

    print("\n=== 工作副本上再跑一遍（★ 必须与 HEAD 逐条完全相同）===")
    diffs = []
    for b in TARGETS + WATCH:
        work = run_twice(b)
        same = work == head_reads.get(b)
        print("  %-5s %s" % (b, "一致 ✓" if same else "★★ 不一致"))
        if not same:
            diffs.append(
                {"batch": b, "HEAD": head_reads.get(b), "工作副本": work}
            )
    print("\n受控对照：%d/%d 条读数逐条完全相同"
          % (len(TARGETS) + len(WATCH) - len(diffs), len(TARGETS) + len(WATCH)))
    return 0 if not diffs else 1


if __name__ == "__main__":
    sys.exit(main())

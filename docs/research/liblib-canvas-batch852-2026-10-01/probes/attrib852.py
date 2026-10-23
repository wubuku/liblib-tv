#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 852 受控对照：把本批改过的源码**按字节换回 HEAD** ⟹ ⟹ 重跑旧门禁
⟹ ⟹ 看读数**逐条有没有变**。

★★ **为什么要连跑两遍**：换回源码后 4317 要热更 ⟹ ⟹ 第一次跑有可能赶上热更中途
⟹ ⟹ ★ 「**一轮的差**」不能直接当因果 ⟹ ⟹ 必须复跑再判。

★ ★ **复原用白名单**：`CHANGED` 是**明确列出的两个相对路径**（不是黑名单），
⟹ ⟹ 不会把本批自己的源码或别人的 WIP 一起回退；⟹ ⟹ 且复原走**字节备份**
（不是 `git checkout`）⟹ ⟹ 复原后逐字节校验哈希。

## ★ 本批盯哪些门禁

★ 本批改过两处**被跟踪**的源码：

- `src/components/director/DirectorViewport.tsx`
  （新增 V／R／F／X 快捷键分支；`translationSnap` 步长 0.5 → 1）
- `src/components/director/directorViewportMath.ts`
  （新增三个导出，未删改既有导出）

★ 因此必须**在 HEAD 与工作副本上读数逐条完全相同**的门禁：

- `851` 导演台视图类快捷键（★ 本批在**同一个控制器**上加了分支 ⟹ 必须没坏）
- `852` 本批（★ 在 HEAD 上**必然红** ⟹ ⟹ 它属于下面的「已知旧账」）
- `550`／`588` 网格吸附（★ 本批改了**吸附步长** ⟹ ⟹ 开关语义必须没坏）
- `830` 导演台快捷键面板
- `831` 快捷键对话框
- `543` 重置视角
- `840`／`850` 角色编辑器（本批没碰 ⟹ ⟹ 属「连带没坏」）
- `835` 属性增量账（851 迁过它 ⟹ ⟹ 应当绿）

★ 另跑**旧账**（`736`／`748`／`749`／`782`／`831`／`852`）⟹ ⟹ 它们在 HEAD 上也红
⟹ ⟹ **不是本批引入的**。
"""
import hashlib
import pathlib
import subprocess
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")

# ★ ★ 白名单：只列本批**确实改过**的两个相对路径
CHANGED = [
    "src/components/director/DirectorViewport.tsx",
    "src/components/director/directorViewportMath.ts",
]
# ★ 旧账（HEAD 上也是红的）
#   ★ `741` 是本批回归里**新发现**的一条红 ⟹ ⟹ 它的失败判据是 `C1`／`C3`
#   （`setNodes`／`setEdges` 的**条件记账**），★ 与吸附步长无关 ⟹ ⟹
#   但**必须由本脚本在 HEAD 上跑一遍来定案** ⟹ ⟹ 不能靠「看起来无关」。
TARGETS = ["736", "748", "749", "782", "831", "741", "852"]
# ★ 必须逐条相同的绿门禁
WATCH = ["851", "550", "588", "830", "543", "840", "850", "835"]


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
    if first != second:
        return "★两遍不一致 | %s ⟹ %s" % (first, second)
    return first


def main() -> int:
    backups = {}
    before = {}
    for rel in CHANGED:
        p = ROOT / rel
        backups[p] = p.read_bytes()
        before[p] = sha(p)

    # ★ 先打印清单再执行（★ 白名单，不是黑名单）
    print("将要换回 HEAD 的文件（白名单，共 %d 个）：" % len(CHANGED))
    for rel in CHANGED:
        print("   ", rel)

    head_reads = {}
    try:
        subprocess.run(["git", "checkout", "--"] + CHANGED, cwd=str(ROOT), check=True)
        print("已换回 HEAD\n")
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
            diffs.append({"batch": b, "HEAD": head_reads.get(b), "工作副本": work})
    total = len(TARGETS) + len(WATCH)
    print("\n受控对照：%d/%d 条读数逐条完全相同" % (total - len(diffs), total))
    out = {"批次": 852, "总数": total, "一致数": total - len(diffs),
           "不一致": diffs,
           "HEAD读数": {k: v for k, v in head_reads.items()}}
    (ROOT / "docs/research/liblib-canvas-batch852-2026-10-01/raw/attrib-852.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0 if not diffs else 1


if __name__ == "__main__":
    import json  # noqa: E402  (放最后，避免与上面 import 顺序冲突)
    sys.exit(main())

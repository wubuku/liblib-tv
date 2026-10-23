#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 853 定点对照：只查 `87` 与 `91` 这两条**新增的红**是不是本批引入的。

## ★ 为什么单独做这个

★ 回归 62 条里红 8 条：`831`／`741`／`736`／`748`／`749`／`782` 是**已知旧账**，
★ 而 `87`／`91` 是**本批第一次进回归清单**的组相关门禁 ⟹ ⟹ 它们红的原因**不能猜**。

★ 方法（白名单，字节级复原）：
  1. 把本批改过的源码**按字节换回 HEAD**（`git checkout --`），
     并把**本批新建**的文件**移走**（★ 它不在 HEAD 里 ⟹ ⟹ `git checkout` 对它无效）；
  2. 在 HEAD 上跑 `87`／`91` **两遍**（★ 换回源码后 4317 要热更 ⟹ ⟹ 一遍不能当因果）；
  3. 复原工作副本，再跑两遍；
  4. 比对：**HEAD 与工作副本读数相同** ⟹ ⟹ 这两条红**不是本批引入的**。

## 输出
  raw/attrib-87-91.json
"""
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
BATCH = ROOT / "docs/research/liblib-canvas-batch853-2026-10-01"
RAW = BATCH / "raw"

# ★ ★ 白名单
CHANGED = ["src/components/director/DirectorDesk.tsx"]
NEWFILE = "src/components/director/directorShortcutRules.ts"
TARGETS = ["87", "91"]


def sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run(batch: str) -> str:
    script = ROOT / ("scripts/verify-liblib-batch%s.py" % batch)
    r = subprocess.run([sys.executable, str(script)], capture_output=True,
                       text=True, timeout=3600, cwd=str(ROOT))
    out = (r.stdout or "") + (r.stderr or "")
    tail = [ln.strip() for ln in out.splitlines() if ln.strip()][-2:]
    return "rc=%s | %s" % (r.returncode, " ／ ".join(tail))


def run_twice(batch: str) -> str:
    a = run(batch)
    b = run(batch)
    if a != b:
        return "★两遍不一致 | %s ⟹ %s" % (a, b)
    return a


def main() -> int:
    backups = {}
    before = {}
    for rel in CHANGED:
        p = ROOT / rel
        backups[p] = p.read_bytes()
        before[p] = sha(p)
    new_p = ROOT / NEWFILE
    new_backup = new_p.read_bytes() if new_p.exists() else None
    new_before = sha(new_p) if new_p.exists() else None
    stash = RAW / ".rules-stash.ts"

    print("将要换回 HEAD 的文件（白名单）：")
    for rel in CHANGED:
        print("   ", rel)
    print("将要移走的本批新建文件：", NEWFILE)

    head_reads = {}
    try:
        subprocess.run(["git", "checkout", "--"] + CHANGED, cwd=str(ROOT), check=True)
        if new_backup is not None:
            stash.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(new_p), str(stash))
        print("已换回 HEAD\n")
        for b in TARGETS:
            head_reads[b] = run_twice(b)
            print("HEAD 上 %s ⟹ %s" % (b, head_reads[b]), flush=True)
    finally:
        for p, data in backups.items():
            p.write_bytes(data)
        if new_backup is not None:
            if new_p.exists():
                new_p.unlink()
            shutil.move(str(stash), str(new_p))
        print("\n已复原工作副本")
        for p in backups:
            assert sha(p) == before[p], "★ 复原后哈希不一致：%s" % p
            print("  复原校验 OK %s %s" % (p.name, sha(p)[:16]))
        if new_before:
            assert sha(new_p) == new_before, "★ 复原后新建文件哈希不一致"
            print("  复原校验 OK %s %s" % (new_p.name, sha(new_p)[:16]))

    print("\n=== 工作副本上再跑一遍 ===")
    diffs = []
    work_reads = {}
    for b in TARGETS:
        work = run_twice(b)
        work_reads[b] = work
        same = work == head_reads.get(b)
        print("  %-5s %s" % (b, "一致 ✓" if same else "★★ 不一致"))
        if not same:
            diffs.append({"batch": b, "HEAD": head_reads.get(b), "工作副本": work})
    out = {
        "批次": 853,
        "说明": "只查 87／91 这两条新增的红是否由本批引入",
        "总数": len(TARGETS),
        "一致数": len(TARGETS) - len(diffs),
        "不一致": diffs,
        "HEAD读数": head_reads,
        "工作副本读数": work_reads,
    }
    (RAW / "attrib-87-91.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n定点对照：%d/%d 条读数逐条相同" % (len(TARGETS) - len(diffs), len(TARGETS)))
    return 0 if not diffs else 1


if __name__ == "__main__":
    sys.exit(main())

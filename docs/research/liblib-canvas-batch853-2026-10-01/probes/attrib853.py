#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 853 受控对照：把本批改过的源码**按字节换回 HEAD** ⟹ ⟹ 重跑旧门禁
⟹ ⟹ 看读数**逐条有没有变**。

★★ **为什么要连跑两遍**：换回源码后 4317 要热更 ⟹ ⟹ 第一次跑有可能赶上热更中途
⟹ ⟹ ★ 「**一轮的差**」不能直接当因果 ⟹ ⟹ 必须复跑再判。

★ ★ **复原用白名单**：`CHANGED` 是**明确列出的相对路径**（不是黑名单），
⟹ ⟹ 不会把本批自己的源码或别人的 WIP 一起回退；⟹ ⟹ 且复原走**字节备份**
（不是 `git checkout`）⟹ ⟹ 复原后逐字节校验哈希。

★ ★★ **新增文件要单独处理**：`src/components/director/directorShortcutRules.ts`
是本批**新建**的 ⟹ ⟹ 它**不在 HEAD 里** ⟹ ⟹ `git checkout --` 对它无效
⟹ ⟹ 必须**移走**（而不是删）⟹ ⟹ 复原时移回来 ⟹ ⟹ 并逐字节校验。

## ★ 本批盯哪些门禁

★ 本批改过一处**被跟踪**源码 ＋ 新增一个文件：

- `src/components/director/DirectorDesk.tsx`（新增 g／d 快捷键分支 ＋ 绑定）
- `src/components/director/directorShortcutRules.ts`（新增）

★ 因此必须**在 HEAD 与工作副本上读数逐条完全相同**的门禁：

- `852` 导演台变换类快捷键（★ 本批在**同一个 keydown 监听器**上加了分支 ⟹ 必须没坏）
- `851` 导演台视图类快捷键（★ 同上）
- `850` 角色大编辑器／左列分段
- `830` 导演台快捷键面板（★ 本批的 ⌘G／⌘⇧D 与面板那两行必须一致）
- `543` 重置视角　`550`／`588` 网格吸附　`840` 角色编辑器　`835` 属性增量账
- `45`／`50`／`85`／`87`／`88`／`792` **组相关**（★ 本批接线的正是这条通路）

★ 另跑**旧账**（`736`／`748`／`749`／`782`／`831`／`741`）⟹ ⟹ 它们在 HEAD 上也红
⟹ ⟹ **不是本批引入的**；以及 `853` 本批（★ 在 HEAD 上**必然红** ⟹ ⟹ 门禁有牙）。
"""
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")

# ★ ★ 白名单：只列本批**确实改过**的相对路径
CHANGED = [
    "src/components/director/DirectorDesk.tsx",
]
# ★ 本批**新建**的文件（HEAD 里没有 ⟹ ⟹ `git checkout --` 对它无效）
NEWFILE = "src/components/director/directorShortcutRules.ts"

# ★ 旧账（HEAD 上也是红的）＋ 本批（在 HEAD 上必然红 ⟹ ⟹ 门禁有牙）
TARGETS = ["736", "748", "749", "782", "831", "741", "853"]
# ★ 必须逐条相同的绿门禁
WATCH = ["852", "851", "850", "830", "543", "550", "588", "840", "835",
         "45", "50", "85", "87", "88", "792"]


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

    new_p = ROOT / NEWFILE
    new_backup = new_p.read_bytes() if new_p.exists() else None
    new_before = sha(new_p) if new_p.exists() else None
    stash = ROOT / "docs/research/liblib-canvas-batch853-2026-10-01/raw/.rules-stash.ts"

    # ★ 先打印清单再执行（★ 白名单，不是黑名单）
    print("将要换回 HEAD 的文件（白名单，共 %d 个）：" % len(CHANGED))
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
        for b in WATCH:
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
    out = {"批次": 853, "总数": total, "一致数": total - len(diffs),
           "不一致": diffs,
           "HEAD读数": {k: v for k, v in head_reads.items()}}
    (ROOT / "docs/research/liblib-canvas-batch853-2026-10-01/raw/attrib-853.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0 if not diffs else 1


if __name__ == "__main__":
    sys.exit(main())

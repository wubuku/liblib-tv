#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 834：给 749／750／751 三条门禁做**归因**——是本批引入的红，还是既有旧账？

★ 方法（沿用 batch 832 的做法，**不用 stash、不用 worktree**）：
  ① 把本批改过的那几个文件**备份**到 /tmp（逐个 sha256 记录）；
  ② 把它们**换回 HEAD 的版本**（新文件先移出源码树）；
  ③ 在**旧版本**上跑这三条门禁 ⟹ 拿到「本批之前」的判据结果；
  ④ 把本批的文件**原样搬回来**（逐个 sha256 复核）。

★ 任何一步失败都**必须**停下来 ⟹ 不允许带着半恢复的树继续。
"""
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
BACKUP = pathlib.Path("/tmp/b834-backup")
FILES = [
    "src/components/director/DirectorTimeline.tsx",
    "src/components/director/DirectorDesk.tsx",
    "src/components/director/DirectorTimelineGuide.tsx",
]
GATES = ["749", "750", "751"]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot():
    return {f: sha(ROOT / f) for f in FILES if (ROOT / f).exists()}


def run_gate(num):
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / f"verify-liblib-batch{num}.py")],
        cwd=str(ROOT), capture_output=True, text=True, timeout=600)
    out = (proc.stdout or "") + (proc.stderr or "")
    lines = [ln.strip() for ln in out.splitlines() if ln.strip()]
    verdict = ""
    for ln in reversed(lines):
        if "判据" in ln or "passed" in ln or "verification" in ln:
            verdict = ln
            break
    return {"exit": proc.returncode, "verdict": verdict[:200],
            "tail": lines[-3:]}


def main():
    BACKUP.mkdir(parents=True, exist_ok=True)
    before = snapshot()
    if len(before) != len(FILES):
        raise SystemExit("★ 源码树里少了要备份的文件：%r" % (set(FILES) - set(before),))
    for f in FILES:
        shutil.copy2(ROOT / f, BACKUP / pathlib.Path(f).name)
    # ★ 复核备份
    for f in FILES:
        name = pathlib.Path(f).name
        if sha(BACKUP / name) != before[f]:
            raise SystemExit("★ 备份校验失败：%s" % f)
    print("已备份", len(before), "个文件")

    old = {}
    try:
        # ② 换回 HEAD 的版本
        subprocess.run(["git", "checkout", "HEAD", "--",
                        "src/components/director/DirectorTimeline.tsx",
                        "src/components/director/DirectorDesk.tsx"],
                       cwd=str(ROOT), check=True)
        (ROOT / "src/components/director/DirectorTimelineGuide.tsx").unlink()
        print("已换回 HEAD 版本")
        # ③ 在旧版本上跑
        for g in GATES:
            old[g] = run_gate(g)
            print("旧版本 batch %s :: exit=%s %s" % (g, old[g]["exit"], old[g]["verdict"]))
    finally:
        # ④ 搬回来
        for f in FILES:
            name = pathlib.Path(f).name
            shutil.copy2(BACKUP / name, ROOT / f)
        after = snapshot()
        if after != before:
            missing = {k: (before.get(k), after.get(k)) for k in set(before) | set(after)
                       if before.get(k) != after.get(k)}
            raise SystemExit("★ 复原后 sha256 不一致：%r" % missing)
        print("已复原本批文件，sha256 全部一致 ✔")

    out = {"旧版本(HEAD)的判据结果": old,
           "★用法": "把「旧版本」与本批的新结果对比：旧版本也红 ⟹ 既有旧账；"
                  "旧版本绿、本批红 ⟹ 本批引入的红"}
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

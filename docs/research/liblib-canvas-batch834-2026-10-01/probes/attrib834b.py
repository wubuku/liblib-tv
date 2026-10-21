#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 834：给 **748** 做**归因**——C1／C3／C4 的红是本批引入，还是既有旧账？

748 的 C1／C3 把导演台 `data-*` 属性的静态并集**锁死成 batch 748 时点的快照**
（去重字面量并集 446 / 补 `dataset.` 后有效并集 447 / 按文件求和 460），
运行时首屏 200 / 走完 7 枚 rail 累计 250。

★ 本批新增 `DirectorTimelineGuide.tsx`（含若干 `data-director-timeline-guide-*`），
并给 4 枚常驻目标 ＋ 导出按钮挂了 `data-director-timeline-guide-target`
⟹ **静态并集必然被本批推高** ⟹ 所以「数字变了」这件事本身**不能**证明是本批的锅，
必须拿「本批之前」的读数来比。

★ 方法（沿用 batch 832／834 的做法，**不用 stash、不用 worktree**）：
  ① 逐个 sha256 备份本批改过的三个文件到 /tmp；
  ② 把它们**换回 HEAD 的版本**（新文件先移出源码树）；
  ③ 在**旧版本**上跑 748 ⟹ 拿到「本批之前」的判据结果与**具体数字**；
  ④ 把本批的文件**原样搬回来**（逐个 sha256 复核）。

★ 748 会把产物写进 `docs/research/liblib-canvas-batch748-2026-10-01/runtime-audit.json`
  ⟹ 跑完必须**复原**该产物（`git checkout --`），否则会把回归副产物带进提交。
"""
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
BACKUP = pathlib.Path("/tmp/b834b-backup")
FILES = [
    "src/components/director/DirectorTimeline.tsx",
    "src/components/director/DirectorDesk.tsx",
    "src/components/director/DirectorTimelineGuide.tsx",
]
AUDIT = pathlib.Path("docs/research/liblib-canvas-batch748-2026-10-01/runtime-audit.json")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot():
    return {f: sha(ROOT / f) for f in FILES if (ROOT / f).exists()}


def read_c123():
    """从 748 的 runtime-audit.json 里取出 C1／C3／C4 的**实际数字**。"""
    p = ROOT / AUDIT
    if not p.exists():
        return {"__missing__": str(p)}
    d = json.loads(p.read_text(encoding="utf-8"))
    res = d.get("summary", {}).get("results", {})
    c3 = res.get("C3_diff", {})
    c4 = res.get("C4_rail", {})
    st = res.get("C1_static", {})
    return {
        "C1_static": {k: st.get(k) for k in
                      ("fileCount", "sumByFile", "unionCount", "sharedAcrossFiles")},
        "C3": {k: c3.get(k) for k in
               ("firstPaintCount", "afterRailWalkCount", "staticLiteralUnion",
                "staticEffectiveUnion", "staticSumByFile", "directorKindsSeen",
                "extraOnPage", "residueAfterWalk")},
        "C4_rail": c4 if not isinstance(c4, dict) else {k: c4.get(k) for k in list(c4)[:6]},
    }


def run_gate(num):
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / f"verify-liblib-batch{num}.py")],
        cwd=str(ROOT), capture_output=True, text=True, timeout=1800)
    out = (proc.stdout or "") + (proc.stderr or "")
    lines = [ln.strip() for ln in out.splitlines() if ln.strip()]
    verdicts = [ln for ln in lines if ln.startswith(("PASS", "FAIL"))]
    return {"exit": proc.returncode, "verdicts": verdicts, "tail": lines[-3:]}


def main():
    BACKUP.mkdir(parents=True, exist_ok=True)
    before = snapshot()
    if len(before) != len(FILES):
        raise SystemExit("★ 源码树里少了要备份的文件：%r" % (set(FILES) - set(before),))
    for f in FILES:
        shutil.copy2(ROOT / f, BACKUP / pathlib.Path(f).name)
    for f in FILES:
        name = pathlib.Path(f).name
        if sha(BACKUP / name) != before[f]:
            raise SystemExit("★ 备份校验失败：%s" % f)
    print("已备份", len(before), "个文件", flush=True)

    old = {}
    old_numbers = {}
    try:
        subprocess.run(["git", "checkout", "HEAD", "--",
                        "src/components/director/DirectorTimeline.tsx",
                        "src/components/director/DirectorDesk.tsx"],
                       cwd=str(ROOT), check=True)
        (ROOT / "src/components/director/DirectorTimelineGuide.tsx").unlink()
        print("已换回 HEAD 版本（引导组件已移出源码树）", flush=True)

        old["748"] = run_gate(748)
        old_numbers["748"] = read_c123()
        print("旧版本 batch 748 :: exit=%s" % old["748"]["exit"], flush=True)
        for v in old["748"]["verdicts"]:
            print("   ", v, flush=True)
    finally:
        for f in FILES:
            name = pathlib.Path(f).name
            shutil.copy2(BACKUP / name, ROOT / f)
        after = snapshot()
        if after != before:
            missing = {k: (before.get(k), after.get(k)) for k in set(before) | set(after)
                       if before.get(k) != after.get(k)}
            raise SystemExit("★ 复原后 sha256 不一致：%r" % missing)
        print("已复原本批文件，sha256 全部一致 ✔", flush=True)

    out = {
        "旧版本(HEAD＝batch 833)的 748 判据": old,
        "旧版本(HEAD)的 748 实际数字": old_numbers,
        "★用法": "旧版本也红同样的检查 ⟹ 既有旧账；"
                 "旧版本绿、本批红 ⟹ 本批引入的红。"
                 "★ 注意：748 的 C1／C3 把静态并集锁死成 748 时点的快照，"
                 "任何新增 `data-*` 的批次都会让它变红 ⟹ 变红本身不构成「本批引入」的证据，"
                 "要看**是不是同一条检查**、以及数字差多少。",
    }
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

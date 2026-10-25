#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 868 探针：★ **受控对照** ⟹ ⟹ 证明那 28 条红**不是本批引入**。

## ★ ★★ 为什么必须做「受控对照」（★ 不能只靠推理）

★ 那些红的**静态筛查**显示：★ **只有 `729`／`766`** 提到了本批改过的文件
⟹ ⟹ ⟹ ⟹ ⇒ ★ 看着像「其余都与本批无关」⟹ ⟹ ⟹ ⟹ ⇒ ★ ★★ **但这不够**：
⟹ ⟹ ⟹ ⟹ ⇒ ★ 门禁是**运行时**的 ⟹ ⟹ ⟹ ⟹ ⇒ ★ 一个门禁**碰**哪个文件
⟹ ⟹ ⟹ ⟹ ⇒ ★ **不由它脚本里出现没出现那个文件名**决定
⟹ ⟹ ⟹ ⟹ ⇒ ★ 有些门禁是**扫目录**的（★ `718`／`729`／`730`／`735`／`737`／`742`／`762`／`771`
⟹ ⟹ ⟹ ⟹ ⇒ ★ 扫 `src/**` ⟹ ⟹ ⟹ ⟹ ⇒ ★ 它们**会**读到我改的那两个文件）
⟹ ⟹ ⟹ ⟹ ⇒ ★ 而**本批我改的 `CharacterLibraryPanel.tsx` 是**整个 `src/` 里**被读得最多的文件之一**。

★ 所以本探针做**受控对照**（★ 沿用 batch 866 的做法）：
  - **态 A ＝ HEAD 态**：★ 把本批改过的**源文件**换回 HEAD 版
    ⟹ ⟹ ⟹ ⟹ ⇒ ★ 其余一切不变（★ 门禁脚本不动）
  - **态 B ＝ WORK 态**：★ 本批工作副本
  - ★ 同一批门禁、**同一口径**各跑一遍 ⟹ ⟹ ⟹ ⟹ ⇒ **红绿对比**
  - ★ 只有「态 A 绿 / 态 B 红」的才算**本批引入** ⟹ ⟹ ⟹ ⟹ ⇒ 其余是**旧账**。

## ★ 纪律

- 只换**本批改过的源文件**（★ 3 个：`CharacterLibraryPanel.tsx`／
  `DirectorCameraMotionTab.tsx`／`verify-liblib-batch698.py`）
  ⟹ ⟹ ⟹ ⟹ ⇒ ★ **不动**任何别人在改的文件；
- ★ **绝不用 stash** ⟹ ⟹ 用 `git show HEAD:<path>` 取回旧版；
- 换源码后**等 dev server 重编**（★ 12s）；
- 复原后必须校验 **SHA-256 == 基线**；
- ★ 收到 SIGTERM 时也要**先复原**再退出；
- ★ 只跑**那 28 条红的** ⟹ ⟹ ⟹ ⟹ ⇒ 不重跑全量（★ 4317 多人共用 ⟹ ⟹ 不能并发）。

## 输出
  raw/controlled-868.json
  raw/controlled-868/<态>/<门禁>.txt
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from gateutil868 import extract_failures, last_meaningful  # noqa: E402

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
BATCH = ROOT / "docs/research/liblib-canvas-batch868-2026-10-01"
RAW = BATCH / "raw"

# ★ ★ 本批改过的**源文件**（★ 只换这三个 ⟹ ⟹ 别的文件一律不碰）
SRC = [
    "src/components/CharacterLibraryPanel.tsx",
    "src/components/director/DirectorCameraMotionTab.tsx",
]
# ★ ★★ 门禁脚本里**本批改过**的那一个（★ 698 判据被反转 ⟹ ⟹ 它自己在 HEAD 态是**旧判据**）
GATE_SRC = ["scripts/verify-liblib-batch698.py"]

NODE = pathlib.Path.home() / ".nvm/versions/node/v24.6.0/bin/node"


def sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run_gate(batch: str, ext: str, cwd: pathlib.Path) -> dict:
    script = cwd / ("scripts/verify-liblib-batch%s.%s" % (batch, ext))
    cmd = ([str(NODE), str(script)] if ext == "mjs"
           else [sys.executable, str(script)])
    t0 = time.time()
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=1800,
                           cwd=str(cwd))
        rc, out = p.returncode, (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired:
        rc, out = "timeout", ""
    fails = extract_failures(out)
    return {"rc": rc, "failures": fails, "last": last_meaningful(out),
            "seconds": round(time.time() - t0, 1), "out": out}


def main() -> int:
    base = json.loads((RAW / "new-gates-868.json").read_text(encoding="utf-8"))
    reds = [(str(r["batch"]), str(r["ext"])) for r in base["逐条"]
            if r.get("rc") not in (0, None)]
    # ★ 868 自己不在对照里（★ 它是本批新门禁 ⟹ ⟹ 它的红是「清单还没生成」⟹ ⟹ 待会儿单独处理）
    reds = [g for g in reds if g[0] != "868"]
    print("★ 对照 %s 条红门禁" % len(reds), flush=True)

    audit: dict[str, object] = {
        "batch": 868,
        "title": "受控对照：★ 证明那 28 条红**不是本批引入**",
        "换回HEAD的源文件": SRC + GATE_SRC,
        "门禁": ["%s.%s" % g for g in reds],
    }

    backup = pathlib.Path(tempfile.mkdtemp(prefix="b868attrib-"))
    base_sha: dict[str, str] = {}
    for rel in SRC + GATE_SRC:
        p = ROOT / rel
        base_sha[rel] = sha(p)
        shutil.copy2(p, backup / (pathlib.Path(rel).name + ".bak"))
    print("★ 备份目录：%s" % backup, flush=True)

    def restore():
        for rel in SRC + GATE_SRC:
            shutil.copy2(backup / (pathlib.Path(rel).name + ".bak"), ROOT / rel)

    def on_term(signum, frame):  # noqa: ANN001
        print("★ 收到信号 ⟹ 复原后退出", flush=True)
        restore()
        raise SystemExit(143)

    signal.signal(signal.SIGTERM, on_term)
    signal.signal(signal.SIGINT, on_term)

    states: dict[str, dict] = {}
    try:
        # ── 态 A：HEAD 态（★ 源文件换回 HEAD 版）──
        for rel in SRC:
            blob = subprocess.run(["git", "show", "HEAD:%s" % rel], cwd=ROOT,
                                  capture_output=True)
            if blob.returncode == 0:
                (ROOT / rel).write_bytes(blob.stdout)
            else:
                print("★ 取不到 HEAD 版：%s" % rel, flush=True)
        # ★ ★ 门禁脚本**也**换回 HEAD 版（★ 698 在 HEAD 态是**旧判据** ⟹ ⟹ 那才是对照基线）
        for rel in GATE_SRC:
            blob = subprocess.run(["git", "show", "HEAD:%s" % rel], cwd=ROOT,
                                  capture_output=True)
            if blob.returncode == 0:
                (ROOT / rel).write_bytes(blob.stdout)
        time.sleep(14)
        out_dir = RAW / "controlled-868" / "HEAD"
        out_dir.mkdir(parents=True, exist_ok=True)
        A: dict[str, dict] = {}
        for b, e in reds:
            r = run_gate(b, e, ROOT)
            (out_dir / ("batch%s.%s.txt" % (b, e))).write_text(
                r["out"], encoding="utf-8")
            A["%s.%s" % (b, e)] = {k: r[k] for k in
                                   ("rc", "failures", "last", "seconds")}
            print("  [HEAD] %-8s rc=%-5s %s" % (b + "." + e, r["rc"],
                                                (r["failures"][0][:80] if r["failures"]
                                                 else r["last"][:70])), flush=True)
        states["HEAD"] = A

        # ── 态 B：WORK 态（本批工作副本）──
        restore()
        time.sleep(14)
        out_dir = RAW / "controlled-868" / "WORK"
        out_dir.mkdir(parents=True, exist_ok=True)
        B: dict[str, dict] = {}
        for b, e in reds:
            r = run_gate(b, e, ROOT)
            (out_dir / ("batch%s.%s.txt" % (b, e))).write_text(
                r["out"], encoding="utf-8")
            B["%s.%s" % (b, e)] = {k: r[k] for k in
                                   ("rc", "failures", "last", "seconds")}
            print("  [WORK] %-8s rc=%-5s %s" % (b + "." + e, r["rc"],
                                                (r["failures"][0][:80] if r["failures"]
                                                 else r["last"][:70])), flush=True)
        states["WORK"] = B
    finally:
        restore()
        shutil.rmtree(backup, ignore_errors=True)

    after = {rel: sha(ROOT / rel) for rel in SRC + GATE_SRC}
    audit["restored"] = after == base_sha
    audit["sha"] = {"base": base_sha, "after": after}
    if not audit["restored"]:
        raise SystemExit("★ 复原自检失败")

    A, B = states["HEAD"], states["WORK"]
    introduced, old, fixed = [], [], []
    for key in sorted(A):
        a_red = A[key]["rc"] != 0
        b_red = B[key]["rc"] != 0
        if a_red and b_red:
            old.append(key)
        elif b_red and not a_red:
            introduced.append(key)
        elif a_red and not b_red:
            fixed.append(key)
    audit["HEAD态红"] = [k for k in sorted(A) if A[k]["rc"] != 0]
    audit["WORK态红"] = [k for k in sorted(B) if B[k]["rc"] != 0]
    audit["本批引入的红"] = introduced
    audit["两态都红（旧账）"] = old
    audit["HEAD红而WORK绿（本批修好）"] = fixed
    audit["逐条"] = {k: {"HEAD": A[k], "WORK": B[k]} for k in sorted(A)}

    (RAW / "controlled-868.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n★ HEAD 态红 %s 条 ／ WORK 态红 %s 条"
          % (len(audit["HEAD态红"]), len(audit["WORK态红"])), flush=True)
    print("★ ★ 本批引入的红：%s" % (introduced or "无"), flush=True)
    print("★ 本批修好的：%s" % (fixed or "无"), flush=True)
    print("读数已落盘：%s" % (RAW / "controlled-868.json"))
    return 1 if introduced else 0


if __name__ == "__main__":
    sys.exit(main())

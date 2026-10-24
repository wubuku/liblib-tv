#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 862 定点归因：扩大回归清单后**新红**的 4 条 ⟹ ⟹ 是本批引入还是旧账？

★ 新红的 4 条（上一批 861 的清单里**没有**它们 ⟹ ⟹ 本批把清单扩大到 107 条
才第一次看见）：
  `35`（等 `[data-director-aspect-frame]` 超时）、`645`、`722`、`629`。

★ 归因方法（**受控对照**）：把这 4 条门禁分别在两个态上各跑一遍 ⟹ ⟹
  - **HEAD 态**（本批的两个源文件换回 `git show HEAD:<path>`）
  - **WORK 态**（本批工作副本）
⟹ ⟹ `onlyOnWORK` ＝ **本批引入**（必须修）；
⟹ ⟹ `onlyOnHEAD` ＝ 本批整改掉的旧行为；
⟹ ⟹ 两边都红 ＝ **旧账**（与本批无关，如实登记）。

★ 纪律：绝不用 stash；跑完**字节级**复原 ＋ SHA-256 自检；收到信号也先复原。

## 输出
  docs/research/liblib-canvas-batch862-2026-10-01/raw/legacy-attribution.json
"""
from __future__ import annotations

import hashlib
import json
import shutil
import signal
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch862-2026-10-01"
RAW = BATCH / "raw/attrib-legacy"

SRC = [
    "src/components/director/DirectorViewport.tsx",
    "src/components/director/DirectorAspectPanel.tsx",
]

# ★ 扩大清单后新红的那 4 条
GATES = [
    "scripts/verify-liblib-batch35.py",
    "scripts/verify-liblib-batch645.py",
    "scripts/verify-liblib-batch722.py",
    "scripts/verify-liblib-batch629.py",
]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def extract_failures(text: str) -> list[str]:
    out: list[str] = []
    for ln in text.splitlines():
        s = ln.strip()
        if s.startswith("FAILED:"):
            out.extend([x.strip() for x in s[len("FAILED:"):].split(",") if x.strip()])
        elif s.startswith("FAIL ｜") or s.startswith("FAIL |"):
            out.append(s[:160])
        elif "TimeoutError" in s or "AssertionError" in s:
            out.append(s[:160])
    seen: set[str] = set()
    uniq = []
    for f in out:
        if f not in seen:
            seen.add(f)
            uniq.append(f)
    return uniq


def run_gate(path: str, label: str) -> dict:
    name = Path(path).stem
    out_dir = RAW / label
    out_dir.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run([sys.executable, str(ROOT / path)], cwd=ROOT,
                          capture_output=True, text=True, timeout=3600)
    out = (proc.stdout or "") + (proc.stderr or "")
    (out_dir / f"{name}.txt").write_text(out, encoding="utf-8")
    failed = extract_failures(out)
    print(f"  [{label}] {name}  rc={proc.returncode}  红条 {len(failed)}", flush=True)
    return {"rc": proc.returncode, "failed": failed,
            "tail": [x.strip() for x in out.splitlines() if x.strip()][-3:]}


def main() -> int:
    audit: dict = {"batch": 862, "gates": GATES, "src": SRC}
    backup = Path(tempfile.mkdtemp(prefix="b862legacy-"))
    base = {rel: sha(ROOT / rel) for rel in SRC}
    for rel in SRC:
        shutil.copy2(ROOT / rel, backup / Path(rel).name)

    def _on_term(signum, frame):  # noqa: ANN001
        for rel in SRC:
            shutil.copy2(backup / Path(rel).name, ROOT / rel)
        raise SystemExit(143)

    signal.signal(signal.SIGTERM, _on_term)
    signal.signal(signal.SIGINT, _on_term)

    try:
        # ── HEAD 态 ──
        for rel in SRC:
            blob = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=ROOT,
                                  capture_output=True)
            (ROOT / rel).write_bytes(blob.stdout)
        head = {g: run_gate(g, "HEAD") for g in GATES}

        # ── WORK 态 ──
        for rel in SRC:
            shutil.copy2(backup / Path(rel).name, ROOT / rel)
        work = {g: run_gate(g, "WORK") for g in GATES}
    finally:
        for rel in SRC:
            shutil.copy2(backup / Path(rel).name, ROOT / rel)
        shutil.rmtree(backup, ignore_errors=True)

    audit["restored"] = {rel: sha(ROOT / rel) == base[rel] for rel in SRC}
    audit["head"] = head
    audit["work"] = work

    attribution = {}
    for g in GATES:
        h = set(head[g]["failed"])
        w = set(work[g]["failed"])
        only_work = sorted(w - h)
        only_head = sorted(h - w)
        if head[g]["rc"] != 0 and work[g]["rc"] != 0 and not only_work:
            verdict = "旧账（HEAD 与 WORK 都红，且红条相同）"
        elif only_work:
            verdict = "★ 本批引入（必须修）"
        elif head[g]["rc"] != 0 and work[g]["rc"] == 0:
            verdict = "本批修好的旧问题"
        else:
            verdict = "需人工看"
        attribution[g] = {"verdict": verdict,
                          "onlyOnWORK": only_work, "onlyOnHEAD": only_head,
                          "headRc": head[g]["rc"], "workRc": work[g]["rc"],
                          "headFailed": head[g]["failed"],
                          "workFailed": work[g]["failed"]}
        print(f"\n== {g} == {verdict}")
        print("   HEAD 红:", head[g]["failed"][:4])
        print("   WORK 红:", work[g]["failed"][:4])
        if only_work:
            print("   ★ 只有 WORK 红:", only_work)

    audit["attribution"] = attribution
    (RAW.parent / "legacy-attribution.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
    introduced = [g for g, a in attribution.items()
                  if "本批引入" in a["verdict"]]
    print(f"\n复原自检：{audit['restored']}")
    print(f"本批引入的新红：{introduced or '（无）'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

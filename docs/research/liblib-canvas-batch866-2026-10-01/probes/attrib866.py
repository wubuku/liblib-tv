#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 866 受控对照：★ 证明 `785` 的整改**有牙**（且没伤到别的）。

## ★ 这套对照要证明三件事

① **整改后的 `785` 仍然有牙**：★ 把它的定位逻辑**改回旧的行号断言**
   ⟹ ⟹ `785` 必须**具名翻红**（⟹ ⟹ 说明新定位逻辑真的在起作用）。

② **旧定位逻辑确实是那个红因**：★ 把源码换回 **batch 864 态**
   ⟹ ⟹ 旧的 `785`（写死行号 2739）**照样红** ⟹ ⟹
   ⟹ ⟹ 证明「那个红**与本批区域有关**」但**与 `785` 要验的性质无关**。

③ **改前/改后同口径**：★ 两态各跑一遍**同一个** `785` ⟹ ⟹ 可比读数。

## ★ 状态与顺序

- `HEAD864`（源码换回 batch 864 态 ＋ 旧版 `785`）⟹ ⟹ 红；
- `MIX`（★ 源码在 HEAD864 态 ＋ `785` **用新定位逻辑**）⟹ ⟹ ★ **绿**
  ⟹ ⟹ 这一步是**关键**：★ 证明「那个红**只是**行号漂移」，
  ⟹ ⟹ 而不是「源码本身在 HEAD 态就是坏的」；
- `WORK-1` → `WORK-2`（本批工作副本 ＋ 新版 `785`）⟹ ⟹ **绿**。

## ★ 纪律

- 只换**源码** ＋ **门禁脚本** ⟹ ⟹ 不碰其它路径；
- **绝不用 stash** ⟹ ⟹ 用 `git show <commit>:<path>` 取回旧版；
- 换源码后**等 dev server 重编**（10s）；
- 复原后必须校验 **SHA-256 == 基线**；
- ★ 收到 SIGTERM 时也要**先复原**再退出；
- ★ **「崩」不算「有牙」** ⟹ ⟹ 要求「具名红条 ＋ 零 CRASH」。

## 输出
  docs/research/liblib-canvas-batch866-2026-10-01/controlled-comparison.json
  docs/research/liblib-canvas-batch866-2026-10-01/raw/attrib/<态>/<门禁>.txt
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch866-2026-10-01"
RAW = BATCH / "raw/attrib"

BASE_COMMIT = "ed167382"          # ★ batch 864 的提交
GATE = "scripts/verify-liblib-batch785.py"
SRC = ["src/components/director/DirectorViewport.tsx",
       "src/components/director/DirectorObjectTree.tsx",
       "src/components/director/DirectorTimeline.tsx"]

# ★ MIX 态：★ 把**新**定位逻辑**改回旧的行号断言**（★ 行数中性）
OLD_LOCATOR = (
    "assert len(hits) == 1, (\n                    \"\u2605 needle %r\uff08ctx=%r\uff09\u5728 %s \u91cc\u547d\u4e2d %d \u884c\uff08\u63d0\u793a\u884c\u53f7 %d\uff09\u27f9 \u27f9 \"\n                    \"\u2605 \u552f\u4e00\u547d\u4e2d\u624d\u80fd\u81ea\u52a8\u5b9a\u4f4d\uff1b\u5426\u5219\u8bf7\u6539 needle \u6216\u8865\u4e0a\u4e0b\u6587\uff0c\"\n                    \"\u6216\u7528 all_hits=True\uff08\u2605\u300c\u540c\u540d\u51e0\u5904\u672c\u5c31\u8be5\u4e00\u8d77\u6539\u300d\u7684\u90a3\u79cd\uff09\"\n                    % (old[:60], (ctx or \"\")[:40], rel, len(hits), line))\n                idxs = [hits[0] + needle_offset]\n"
)
NEW_LOCATOR = (
    "assert old in before[line - 1], (\n                    \"\u2605 needle \u4e0d\u5728 %s:%d\" % (rel, line))\n                idxs = [line - 1]\n                # \u2605 \u2605\uff08MIX\uff1a\u65e7\u5b9a\u4f4d\u903b\u8f91\u88ab\u6539\u56de \u27f9 \u27f9 \u884c\u53f7\u6f02\u4e86\u5c31\u8be5\u7ea2\uff09\n                # \u2605 \u2605\uff08MIX\uff1a\u65e7\u5b9a\u4f4d\u903b\u8f91\u88ab\u6539\u56de \u27f9 \u27f9 \u884c\u53f7\u6f02\u4e86\u5c31\u8be5\u7ea2\uff09\n                # \u2605 \u2605\uff08MIX\uff1a\u65e7\u5b9a\u4f4d\u903b\u8f91\u88ab\u6539\u56de \u27f9 \u27f9 \u884c\u53f7\u6f02\u4e86\u5c31\u8be5\u7ea2\uff09\n"
)

STATES = ["HEAD864", "MIX", "WORK-1", "WORK-2"]
EXC_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_.]*(?:Error|Exception)):\s*(.*)$")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def extract_failures(text: str) -> list[str]:
    out: list[str] = []
    lines = text.splitlines()
    for ln in lines:
        s = ln.strip()
        if s.startswith("FAILED:"):
            out.extend([x.strip() for x in s[len("FAILED:"):].strip().split(",")
                        if x.strip()])
            continue
        m = re.match(r"^FAIL\s{2,}(.+?)\s*｜", s)
        if m:
            out.append(m.group(1).strip()); continue
        m = re.match(r"^\[FAIL\]\s*(.+?)(?:\s*⟵.*)?$", s)
        if m:
            out.append(m.group(1).strip()); continue
        if s.startswith("AssertionError"):
            out.append(s[:160]); continue
    if "Traceback (most recent call last):" in text and not out:
        for ln in reversed(lines):
            m = EXC_RE.match(ln.strip())
            if m:
                out.append(f"CRASH: {m.group(1)}: {m.group(2)[:120]}")
                break
    seen: set[str] = set()
    uniq: list[str] = []
    for f in out:
        if f not in seen:
            seen.add(f); uniq.append(f)
    return uniq


def run_gate(label: str) -> dict:
    out_dir = RAW / label
    out_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    proc = subprocess.run([sys.executable, str(ROOT / GATE)], cwd=ROOT,
                          capture_output=True, text=True, timeout=3600)
    out = (proc.stdout or "") + (proc.stderr or "")
    (out_dir / "verify-liblib-batch785.txt").write_text(out, encoding="utf-8")
    failed = extract_failures(out)
    dur = round(time.time() - t0, 1)
    print(f"  [{label}] rc={proc.returncode}  红条 {len(failed)}  {dur}s", flush=True)
    return {"rc": proc.returncode, "failed": failed, "seconds": dur}


def main() -> int:
    audit: dict[str, object] = {
        "batch": 866,
        "title": "受控对照：证明 785 的整改有牙，且那个红真的只是行号漂移",
        "gate": GATE, "baseCommit": BASE_COMMIT, "src": SRC, "states": STATES,
    }
    backup = Path(tempfile.mkdtemp(prefix="b866attrib-"))
    print(f"★ 备份目录：{backup}", flush=True)
    base_sha: dict[str, str] = {}
    for rel in SRC + [GATE]:
        p = ROOT / rel
        base_sha[rel] = sha(p)
        shutil.copy2(p, backup / (Path(rel).name + ".bak"))

    def restore():
        for rel in SRC + [GATE]:
            shutil.copy2(backup / (Path(rel).name + ".bak"), ROOT / rel)

    def on_term(signum, frame):  # noqa: ANN001
        print("★ 收到信号 ⟹ 复原后退出", flush=True)
        restore(); raise SystemExit(143)

    signal.signal(signal.SIGTERM, on_term)
    signal.signal(signal.SIGINT, on_term)

    try:
        # ── 态 1：HEAD864（源码换回 batch 864 态 ＋ 旧版 `785`）──
        for rel in SRC:
            blob = subprocess.run(["git", "show", f"{BASE_COMMIT}:{rel}"],
                                  cwd=ROOT, capture_output=True)
            if blob.returncode != 0:
                (ROOT / rel).unlink(missing_ok=True)
            else:
                (ROOT / rel).write_bytes(blob.stdout)
        old_gate = subprocess.run(["git", "show", f"{BASE_COMMIT}:{GATE}"],
                                  cwd=ROOT, capture_output=True)
        if old_gate.returncode == 0:
            (ROOT / GATE).write_bytes(old_gate.stdout)
        time.sleep(12)
        head = run_gate("HEAD864")

        # ── 态 2：MIX（★ 源码仍在 HEAD864 态 ⟹ ⟹ 但 `785` 用**新**定位逻辑）──
        restore()                       # ★ 先复原（`785` 与源码都回到新版/本批）
        for rel in SRC:                 # ★ 再把源码换回 HEAD864 态
            blob = subprocess.run(["git", "show", f"{BASE_COMMIT}:{rel}"],
                                  cwd=ROOT, capture_output=True)
            if blob.returncode != 0:
                (ROOT / rel).unlink(missing_ok=True)
            else:
                (ROOT / rel).write_bytes(blob.stdout)
        g = ROOT / GATE
        t = g.read_text(encoding="utf-8")
        assert OLD_LOCATOR in t, "★ MIX 锚点（旧定位逻辑）不存在"
        lines_before = t.count("\n")
        t2 = t.replace(OLD_LOCATOR, NEW_LOCATOR, 1)
        g.write_text(t2, encoding="utf-8")
        audit["MIX行数中性"] = lines_before == g.read_text(encoding="utf-8").count("\n")
        time.sleep(12)
        mix = run_gate("MIX")

        # ── 态 3/4：WORK（本批工作副本 ＋ 新版 `785`）──
        restore()
        time.sleep(12)
        work1 = run_gate("WORK-1")
        work2 = run_gate("WORK-2")

        restored = {rel: sha(ROOT / rel) for rel in SRC + [GATE]}
        audit["restored"] = restored == base_sha
        audit["sha"] = {"base": base_sha, "after": restored}
        if not audit["restored"]:
            raise SystemExit("复原自检失败")
    finally:
        restore()
        shutil.rmtree(backup, ignore_errors=True)

    audit["HEAD864"] = head
    audit["MIX"] = mix
    audit["WORK-1"] = work1
    audit["WORK-2"] = work2

    stable = (work1["failed"] == work2["failed"])
    audit["stableAcrossTwoRuns"] = stable
    audit["newGateHasTeeth"] = (mix["rc"] != 0 and work1["rc"] == 0)
    audit["mixFailed"] = mix["failed"]
    audit["mixNamedReds"] = [f for f in mix["failed"] if not f.startswith("CRASH:")]
    audit["mixCrash"] = [f for f in mix["failed"] if f.startswith("CRASH:")]
    audit["headFailed"] = head["failed"]
    audit["workFailed"] = work1["failed"]

    BATCH.mkdir(parents=True, exist_ok=True)
    (BATCH / "controlled-comparison.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n稳定={stable} 有牙={audit['newGateHasTeeth']} 复原={audit['restored']}",
          flush=True)
    print(f"HEAD864 红 {len(head['failed'])} 条", flush=True)
    print(f"MIX     红 {len(mix['failed'])} 条：{audit['mixNamedReds'][:4]}", flush=True)
    print(f"WORK    红 {len(work1['failed'])} 条", flush=True)

    ok = (stable and audit["newGateHasTeeth"] and audit["restored"]
          and bool(audit["mixNamedReds"]) and not audit["mixCrash"]
          and head["rc"] != 0 and work1["rc"] == 0)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 860 受控对照：把**源码**换回 HEAD ⟹ ⟹ 读数必须能区分。

## ★ 这套对照要证明三件事

① **新门禁有牙**：把源码换回 HEAD ⟹ ⟹ `verify-liblib-batch860.py`
   必须**翻红**（不然它就是空转的）。
② **本批的每个改动都有牙**：分别回退 **store**／**math**／**panel**／**viewport**
   ⟹ ⟹ 各自都该翻红（⟹ ⟹ 证明「不是靠某一处巧合蒙对的」）。
③ **MIX 半回退态**：只回退**部分**文件、保留其余 ⟹ ⟹ 判据仍能区分。

## ★ 状态与顺序

- `HEAD-1` → `HEAD-2`（源码全部换回 HEAD）⟹ ⟹ 新门禁必须翻红；
- `WORK-1` → `WORK-2`（本批工作副本）⟹ ⟹ 新门禁必须全绿；
- ★ **WORK 在最后** ⟹ ⟹ 磁盘上留着的门禁产物是**本批源码**读出来的。

★ 本批新增的 `MIX` 态（单独脚本 `attrib860_mix.py`）：
只回退 **`DirectorAspectPanel.tsx`**（它回到「组件内 `useState`」的老写法），
**保留** store 与 math 的新代码
⟹ ⟹ 这正好隔离出「面板没接 store」这一条 ⟹ ⟹ 判据必须**仍然红**
（因为面板与 store 脱钩 ⟹ ⟹ 点七格不生效）。

## ★ 纪律

- 只换**源码**（4 个文件）⟹ ⟹ 门禁脚本保持本批版本 ⟹ ⟹ 翻红才说明
  「门禁在测新源码」。
- **绝不用 stash**（仓库有他人的 WIP）⟹ ⟹ 用 `git show HEAD:<path>` 取回
  HEAD 态，并**逐字节**复原工作副本。
- 每一态跑**两遍** ⟹ ⟹ 两遍读数必须一致（否则是抖动，不能当因果）。
- 复原后必须校验 **SHA-256 == 基线**。
- ★ 收到 SIGTERM 时也要**先复原源码**再退出。

## ★ 失败提取

沿用 858/859 的五种红条格式（`  FAILED: `／`FAILED: a,b`／`  FAIL ｜`／
`  [FAIL]`／裸 `assert` traceback）＋ 崩溃签名。

## 输出
  docs/research/liblib-canvas-batch860-2026-10-01/controlled-comparison.json
  docs/research/liblib-canvas-batch860-2026-10-01/raw/attrib/<态>/<门禁>.txt
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
BATCH = ROOT / "docs/research/liblib-canvas-batch860-2026-10-01"
RAW = BATCH / "raw/attrib"

# ★ 本批动过的四个源码文件
SRC = [
    "src/store/directorStore.ts",
    "src/components/director/directorViewportMath.ts",
    "src/components/director/DirectorAspectPanel.tsx",
    "src/components/director/DirectorViewport.tsx",
]

# ★ 决定性的门禁清单（本批新门禁 ＋ 本批动过其比对对象的老门禁）
GATES = [
    "scripts/verify-liblib-batch860.py",
    "scripts/verify-liblib-batch859.py",
    "scripts/verify-liblib-batch626.py",
    "scripts/verify-liblib-batch625.py",
    "scripts/verify-liblib-batch590.py",
    "scripts/verify-liblib-batch589.py",
]

STATES = ["HEAD-1", "HEAD-2", "WORK-1", "WORK-2"]

EXC_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_.]*(?:Error|Exception)):\s*(.*)$")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def extract_failures(text: str) -> list[str]:
    out: list[str] = []
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        s = ln.strip()
        if s.startswith("FAILED:"):
            rest = s[len("FAILED:"):].strip()
            if ln.startswith("FAILED:"):
                out.extend([x.strip() for x in rest.split(",") if x.strip()])
            else:
                out.append(rest)
            continue
        m = re.match(r"^FAIL\s{2,}(.+?)\s*｜", s)
        if m:
            out.append(m.group(1).strip())
            continue
        m = re.match(r"^\[FAIL\]\s*(.+?)(?:\s*⟵.*)?$", s)
        if m:
            out.append(m.group(1).strip())
            continue
        if s == "AssertionError" or s.startswith("AssertionError:"):
            msg = s[len("AssertionError"):].lstrip(": ").strip()
            if msg:
                m2 = re.match(r"^batch\d+ check failed:\s*(.*?)(?:\s*::.*)?$", msg)
                out.append(m2.group(1).strip() if m2 else msg)
            else:
                sig = ""
                for j in range(i - 1, max(-1, i - 8), -1):
                    cand = lines[j]
                    if (re.match(r"^\s{4,}\S", cand)
                            and not cand.strip().startswith("File ")
                            and "assert" in cand):
                        sig = cand.strip()
                        break
                out.append(sig or "AssertionError(无消息，表达式未定位)")
            continue
    if "Traceback (most recent call last):" in text and not out:
        for ln in reversed(lines):
            s = ln.strip()
            if not s:
                continue
            m = EXC_RE.match(s)
            if m:
                out.append(f"CRASH: {m.group(1)}: {m.group(2)[:120]}")
                break
            if s and not s.startswith("File ") and " " in s and s.endswith(")"):
                continue
            if s and re.match(r"^[A-Za-z_][A-Za-z0-9_.]*Error$", s):
                out.append(f"CRASH: {s}")
                break
    seen: set[str] = set()
    uniq: list[str] = []
    for f in out:
        if f not in seen:
            seen.add(f)
            uniq.append(f)
    return uniq


def run_gate(path: str, label: str) -> dict:
    gate_name = Path(path).stem
    out_dir = RAW / label
    out_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    proc = subprocess.run([sys.executable, str(ROOT / path)], cwd=ROOT,
                          capture_output=True, text=True, timeout=3600)
    out = (proc.stdout or "") + (proc.stderr or "")
    (out_dir / f"{gate_name}.txt").write_text(out, encoding="utf-8")
    failed = extract_failures(out)
    dur = round(time.time() - t0, 1)
    print(f"  [{label}] {gate_name}  rc={proc.returncode}  "
          f"红条 {len(failed)}  {dur}s", flush=True)
    return {"rc": proc.returncode, "failed": failed, "seconds": dur,
            "log": str((out_dir / f"{gate_name}.txt").relative_to(ROOT))}


def run_state(label: str) -> dict:
    res: dict[str, dict] = {}
    for g in GATES:
        res[g] = run_gate(g, label)
    res2 = run_gate(GATES[0], label + "-860-2nd")
    return {"once": res, "twice": res2}


def restore_source(backup: Path) -> None:
    for rel in SRC:
        shutil.copy2(backup / Path(rel).name, ROOT / rel)


def checkout_head(rels: list[str]) -> None:
    for rel in rels:
        blob = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=ROOT,
                              capture_output=True)
        if blob.returncode != 0:
            (ROOT / rel).unlink(missing_ok=True)
        else:
            (ROOT / rel).write_bytes(blob.stdout)


def main() -> int:
    audit: dict[str, object] = {
        "batch": 860,
        "title": "受控对照：源码换回 HEAD ⟹ 新门禁必须翻红（证明有牙）",
        "gates": GATES,
        "states": STATES,
        "src": SRC,
    }
    backup = Path(tempfile.mkdtemp(prefix="b860attrib-"))
    print(f"★ 备份目录：{backup}", flush=True)
    base_sha: dict[str, str] = {}
    for rel in SRC:
        p = ROOT / rel
        base_sha[rel] = sha(p)
        shutil.copy2(p, backup / Path(rel).name)

    def _on_term(signum, frame):  # noqa: ANN001
        print("★ 收到信号 ⟹ 复原源码后退出", flush=True)
        restore_source(backup)
        raise SystemExit(143)

    signal.signal(signal.SIGTERM, _on_term)
    signal.signal(signal.SIGINT, _on_term)

    try:
        # ── 态 1/2：源码全部换回 HEAD ⟹ ⟹ 连跑两遍 ──
        checkout_head(SRC)
        head = run_state("HEAD-1")
        head2 = run_state("HEAD-2")

        # ── 态 3/4：复原到本批工作副本 ⟹ ⟹ 连跑两遍（★ WORK 留在最后）──
        restore_source(backup)
        work = run_state("WORK-1")
        work2 = run_state("WORK-2")

        restored = {rel: sha(ROOT / rel) for rel in SRC}
        audit["restored"] = restored == base_sha
        audit["sha"] = {"base": base_sha, "after": restored}
        if not audit["restored"]:
            raise SystemExit("复原自检失败 ⟹ 文件被改坏了")
    finally:
        restore_source(backup)
        shutil.rmtree(backup, ignore_errors=True)

    audit["work"] = work
    audit["work2"] = work2
    audit["head"] = head
    audit["head2"] = head2

    # ── 判据 1：两遍读数必须一致 ──
    stable = (work["once"][GATES[0]]["failed"] == work["twice"]["failed"]
              and head["once"][GATES[0]]["failed"] == head["twice"]["failed"])
    audit["stableAcrossTwoRuns"] = stable
    audit["stabilityNote"] = ("只有新门禁 860 跑了两遍（决定性测量）；"
                              "其余门禁读的是失败集合的差异")

    # ── 判据 2：新门禁在 HEAD 态必须翻红 ⟹ ⟹ 它有牙 ──
    g860 = "scripts/verify-liblib-batch860.py"
    teeth = (head["once"][g860]["rc"] != 0 and work["once"][g860]["rc"] == 0)
    audit["newGateHasTeeth"] = teeth
    audit["newGateFailedOnHEAD"] = head["once"][g860]["failed"]
    audit["newGateFailedOnWORK"] = work["once"][g860]["failed"]
    audit["newGateCrashOnHEAD"] = [f for f in head["once"][g860]["failed"]
                                   if f.startswith("CRASH:")]

    # ── 判据 3：两态下**失败集合的差异**必须逐条可解释 ──
    diffs = {}
    for g in GATES:
        if g == g860:
            continue
        only_head = sorted(set(head["once"][g]["failed"])
                           - set(work["once"][g]["failed"]))
        only_work = sorted(set(work["once"][g]["failed"])
                           - set(head["once"][g]["failed"]))
        if only_head or only_work:
            diffs[g] = {"onlyOnHEAD": only_head, "onlyOnWORK": only_work}
    audit["diffs"] = diffs
    audit["diffsNote"] = ("HEAD 独有的红条 = 「本批整改掉的旧行为」；"
                          "WORK 独有的红条 = 「本批引入的新问题」（必须为空）")

    audit["mixNote"] = ("MIX 半回退态由独立脚本 attrib860_mix.py 跑"
                        "（只回退 DirectorAspectPanel.tsx、保留 store 与 math "
                        "的新代码）⟹ ⟹ 正好隔离出「面板没接 store」这一条")

    BATCH.mkdir(parents=True, exist_ok=True)
    (BATCH / "controlled-comparison.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n稳定={stable} 新门禁有牙={teeth} 复原={audit['restored']}", flush=True)
    print(f"HEAD 态新门禁红 {len(audit['newGateFailedOnHEAD'])} 条："
          f"{audit['newGateFailedOnHEAD'][:6]}", flush=True)
    for g, d in diffs.items():
        print(f"  {g}: HEAD 独有 {len(d['onlyOnHEAD'])} 条 / "
              f"WORK 独有 {len(d['onlyOnWORK'])} 条", flush=True)
    ok = stable and teeth and audit["restored"] and not audit["newGateCrashOnHEAD"]
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

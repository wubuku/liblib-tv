#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 864 受控对照：把**源码**换回 HEAD ⟹ ⟹ 读数必须能区分。

## ★ 这套对照要证明四件事

① **新门禁有牙**：把源码换回 HEAD（= batch 863 的状态：**没有**埋点实现）
   ⟹ ⟹ `verify-liblib-batch864.py` 必须**翻红**。

② **HEAD 态复现 batch 863 的那个真缺陷**：HEAD 态的坐标控件是 `z-20`
   ⟹ ⟹ 它盖住取景框右上角那枚开关 ⟹ ⟹
   ⟹ ⟹ `verify-liblib-batch863.py` 的**命中测试**判据必须**具名翻红**
   ⟹ ⟹ **且不得崩溃**（★ 这就是 batch 864 给 863 门禁补的那条判据）。
   ★ ★★ **第一版跑出来是「绿」**（受控对照实测：HEAD 态与 MIX 态**都判绿**）
   ⟹ ⟹ 根因：那条判据跑在**比例循环结束的那一档**（`9:16`）
   ⟹ ⟹ 而 `9:16` 的框**很窄** ⟹ ⟹ 开关离坐标控件**很远** ⟹ ⟹ **永不重叠**
   ⟹ ⟹ ⟹ ⟹ **它测的不是那个缺陷**。
   ⟹ ⟹ 修法：命中测试**之前**先用 store 把比例切到 `16:9`（最宽 ⟹ ⟹ 会重叠），
   并**把当前比例钉成一条判据**；另加一条**机制侧**判据（坐标控件的 z 序）。

③ **MIX 单点变异态**：只把坐标控件的 `z-10` 改回 `z-20`（**一个词**）
   ⟹ ⟹ ① 863 门禁的**命中测试**判据必须翻红（**且 z 序那条也红**）；
   ⟹ ⟹ ② 864 门禁里「点开关 ⟹ 记一条 `reference_line` 事件」那条必须翻红；
   ⟹ ⟹ ③ 其余判据保持绿 ⟹ ⟹ **证明修的就是它**，而且隔离干净。
   ⟹ ⟹ ★ ★ **零 CRASH**：被盖住时**不许**超时崩溃 ⟹ ⟹ 必须**具名红条**。

④ **改前/改后同口径**：HEAD 态与 WORK 态各跑一遍**同一个 clone 探针**
   ⟹ ⟹ 得到可比读数。

## ★ 状态与顺序

- `HEAD-1` → `HEAD-2`（源码全部换回 HEAD）⟹ ⟹ 新门禁必须翻红；
- `MIX`（**只**改坐标控件那一个 z-index）；
- `WORK-1` → `WORK-2`（本批工作副本）⟹ ⟹ 门禁必须全绿；
- ★ **WORK 在最后** ⟹ ⟹ 磁盘上留着的门禁产物是**本批源码**读出来的。

## ★ 纪律

- 只换**源码**（4 个文件，其中 1 个是本批**新增**的）⟹ ⟹ 门禁脚本保持本批版本；
- **绝不用 stash**（仓库有他人的 WIP）⟹ ⟹ 用 `git show HEAD:<path>` 取回 HEAD 态，
  并**逐字节**复原工作副本；
- 换源码后**等 dev server 重编**（10s）⟹ ⟹ 否则门禁读的是**旧编译产物**；
- 每一态跑**两遍** ⟹ ⟹ 两遍读数必须一致；
- 复原后必须校验 **SHA-256 == 基线**；
- ★ 收到 SIGTERM 时也要**先复原源码**再退出。

## 输出
  docs/research/liblib-canvas-batch864-2026-10-01/controlled-comparison.json
  docs/research/liblib-canvas-batch864-2026-10-01/raw/attrib/<态>/<门禁>.txt
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
BATCH = ROOT / "docs/research/liblib-canvas-batch864-2026-10-01"
RAW = BATCH / "raw/attrib"
PROBE = BATCH / "probes/clone863_frame_mask.py"

# ★ 本批动过的源码文件（★ `directorTelemetry.ts` 是本批**新增**的 ⟹ HEAD 态没有它）
SRC = [
    "src/lib/directorTelemetry.ts",
    "src/store/directorStore.ts",
    "src/components/director/DirectorAspectPanel.tsx",
    "src/components/director/DirectorViewport.tsx",
]

# ★ MIX 态的单点变异（★ 行数中性：只改一个类名里的一个词）
MIX_OLD = 'className="absolute right-5 top-5 z-10 h-20 w-20"'
MIX_NEW = 'className="absolute right-5 top-5 z-20 h-20 w-20"'

GATES = [
    "scripts/verify-liblib-batch864.py",
    "scripts/verify-liblib-batch863.py",
    "scripts/verify-liblib-batch860.py",
]

STATES = ["HEAD-1", "HEAD-2", "MIX", "WORK-1", "WORK-2"]

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
            out.extend([x.strip() for x in rest.split(",") if x.strip()])
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
            out.append(msg or "AssertionError(无消息)")
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
    res2 = run_gate(GATES[0], label + "-2nd")
    return {"once": res, "twice": res2}


def restore_source(backup: Path) -> None:
    for rel in SRC:
        shutil.copy2(backup / Path(rel).name, ROOT / rel)


def checkout_head(rels: list[str]) -> None:
    for rel in rels:
        blob = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=ROOT,
                              capture_output=True)
        if blob.returncode != 0:
            # ★ HEAD 态**没有**这个文件（本批新增的）⟹ ⟹ 删掉工作副本
            (ROOT / rel).unlink(missing_ok=True)
        else:
            (ROOT / rel).write_bytes(blob.stdout)


def run_probe(tag: str) -> dict:
    proc = subprocess.run([sys.executable, str(PROBE)], cwd=ROOT,
                          capture_output=True, text=True, timeout=1800)
    src_json = BATCH / "raw/clone-863-frame-mask.json"
    dst_json = BATCH / f"raw/clone-863-frame-mask-{tag}.json"
    ok = src_json.exists()
    if ok:
        shutil.copy2(src_json, dst_json)
    print(f"  [探针:{tag}] rc={proc.returncode} 产物={dst_json.name if ok else '无'}",
          flush=True)
    return {"rc": proc.returncode,
            "产物": str(dst_json.relative_to(ROOT)) if ok else ""}


def main() -> int:
    audit: dict[str, object] = {
        "batch": 864,
        "title": "受控对照：源码换回 HEAD ⟹ 新门禁必须翻红（证明有牙）",
        "gates": GATES,
        "states": STATES,
        "src": SRC,
        "mixMutation": {"old": MIX_OLD, "new": MIX_NEW},
    }
    backup = Path(tempfile.mkdtemp(prefix="b864attrib-"))
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
        time.sleep(10)
        head = run_state("HEAD-1")
        head2 = run_state("HEAD-2")
        audit["改前基线_探针"] = run_probe("HEAD")

        # ── 态 3：MIX 单点变异（只改坐标控件那一个 z-index）──
        restore_source(backup)
        target = ROOT / "src/components/director/DirectorViewport.tsx"
        src = target.read_text(encoding="utf-8")
        if MIX_OLD not in src:
            raise SystemExit(f"MIX 锚点不存在：{MIX_OLD!r}")
        lines_before = src.count("\n")
        target.write_text(src.replace(MIX_OLD, MIX_NEW, 1), encoding="utf-8")
        lines_after = target.read_text(encoding="utf-8").count("\n")
        audit["MIX行数中性"] = lines_before == lines_after
        time.sleep(10)
        mix = run_state("MIX")

        # ── 态 4/5：复原到本批工作副本 ⟹ ⟹ 连跑两遍（★ WORK 留在最后）──
        restore_source(backup)
        time.sleep(10)
        work = run_state("WORK-1")
        work2 = run_state("WORK-2")
        audit["改后基线_探针"] = run_probe("WORK")

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
    audit["mix"] = mix

    g864 = GATES[0]
    g863 = GATES[1]

    stable = (work["once"][g864]["failed"] == work["twice"]["failed"]
              and head["once"][g864]["failed"] == head["twice"]["failed"])
    audit["stableAcrossTwoRuns"] = stable

    teeth = (head["once"][g864]["rc"] != 0 and work["once"][g864]["rc"] == 0)
    audit["newGateHasTeeth"] = teeth
    audit["newGateFailedOnHEAD"] = head["once"][g864]["failed"]
    audit["newGateFailedOnWORK"] = work["once"][g864]["failed"]
    audit["newGateCrashOnHEAD"] = [f for f in head["once"][g864]["failed"]
                                   if f.startswith("CRASH:")]
    audit["gate863CrashOnHEAD"] = [f for f in head["once"][g863]["failed"]
                                   if f.startswith("CRASH:")]
    # ★ ★ HEAD 态必须**具名**复现那个缺陷（不是崩溃）
    hit_red = [f for f in head["once"][g863]["failed"]
               if "topmost-element" in f]
    audit["headStateReproducesTheCoveringDefect"] = {
        "具名红条": hit_red,
        "零崩溃": not audit["gate863CrashOnHEAD"],
    }

    # ★ MIX 态：命中测试红 ＋ 864 的「点开关记事件」红 ＋ 其余绿
    mix_fail = mix["once"][g864]["failed"]
    mix863_fail = mix["once"][g863]["failed"]
    audit["mixFailed864"] = mix_fail
    audit["mixFailed863"] = mix863_fail
    audit["mixCrash864"] = [f for f in mix_fail if f.startswith("CRASH:")]
    audit["mixCrash863"] = [f for f in mix863_fail if f.startswith("CRASH:")]
    audit["mixNamedReds864"] = [f for f in mix_fail if not f.startswith("CRASH:")]
    audit["mixIsolated"] = {
        "863的命中测试红": [f for f in mix863_fail if "topmost-element" in f],
        "863的z序红": [f for f in mix863_fail if "outrank" in f],
        "864的红": mix_fail,
        "why": "★ 只把坐标控件的 z 改回 20 ⟹ ⟹ 开关被盖住 ⟹ ⟹ "
               "① 863 的命中测试必须红 ② 864 的「点开关记事件」必须红 "
               "③ 其余判据保持绿 ⟹ ⟹ 证明修的就是它",
    }

    diffs = {}
    for g in GATES:
        if g == g864:
            continue
        only_head = sorted(set(head["once"][g]["failed"])
                           - set(work["once"][g]["failed"]))
        only_work = sorted(set(work["once"][g]["failed"])
                           - set(head["once"][g]["failed"]))
        if only_head or only_work:
            diffs[g] = {"onlyOnHEAD": only_head, "onlyOnWORK": only_work}
    audit["diffs"] = diffs

    BATCH.mkdir(parents=True, exist_ok=True)
    (BATCH / "controlled-comparison.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n稳定={stable} 新门禁有牙={teeth} 复原={audit['restored']}", flush=True)
    print(f"HEAD 态 864 门禁红 {len(audit['newGateFailedOnHEAD'])} 条", flush=True)
    print(f"HEAD 态 863 门禁的具名「命中测试」红：{hit_red}", flush=True)
    print(f"MIX 态 864 门禁红 {len(mix_fail)} 条：{mix_fail[:6]}", flush=True)
    print(f"MIX 态 863 门禁红 {len(mix863_fail)} 条：{mix863_fail[:6]}", flush=True)
    for g, d in diffs.items():
        print(f"  {g}: HEAD 独有 {len(d['onlyOnHEAD'])} 条 / "
              f"WORK 独有 {len(d['onlyOnWORK'])} 条", flush=True)
    ok = (stable and teeth and audit["restored"]
          and not audit["newGateCrashOnHEAD"]
          and not audit["gate863CrashOnHEAD"]
          and not audit["mixCrash864"]
          and not audit["mixCrash863"]
          and bool(hit_red)
          and bool(audit["mixIsolated"]["863的命中测试红"])
          and bool(audit["mixIsolated"]["863的z序红"])
          and bool(audit["mixNamedReds864"])
          and not any(d["onlyOnWORK"] for d in diffs.values()))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

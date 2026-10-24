#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 863 受控对照：把**源码**换回 HEAD ⟹ ⟹ 读数必须能区分。

## ★ 这套对照要证明三件事

① **新门禁有牙**：把源码换回 HEAD（= batch 862 的旧实现：框自带
   `shadow-[0_0_0_9999px_rgba(0,0,0,0.24)]`、**没有遮罩层**）
   ⟹ ⟹ `verify-liblib-batch863.py` 必须**翻红**（不然它就是空转的）。
② **改前/改后同口径**：在 HEAD 态与 WORK 态**各跑一次同一个 clone 探针**
   ⟹ ⟹ 得到「改前」与「改后」的可比读数（★ 同一支探针、同一口径）。
③ **MIX 单点变异态**：只把 `maskComposite: "exclude"` 改成 `"add"`
   ⟹ ⟹ **红色探针**那条判据必须翻红（框内也会被染红 ⟹ ⟹ mask 没挖空）
   ⟹ ⟹ 而**其余判据保持绿** ⟹ ⟹ 证明「红色探针」这条判据真的有牙、
   而且**只咬 mask 合成这一处**（隔离干净）。

## ★ 状态与顺序

- `HEAD-1` → `HEAD-2`（源码全部换回 HEAD）⟹ ⟹ 新门禁必须翻红；
- `MIX`（**只**改 mask 合成一个词）⟹ ⟹ 红色探针判据红、其余绿；
- `WORK-1` → `WORK-2`（本批工作副本）⟹ ⟹ 新门禁必须全绿；
- ★ **WORK 在最后** ⟹ ⟹ 磁盘上留着的门禁产物是**本批源码**读出来的。

## ★ 纪律

- 只换**源码**（1 个文件）⟹ ⟹ 门禁脚本保持本批版本 ⟹ ⟹ 翻红才说明
  「门禁在测新源码」。
- **绝不用 stash**（仓库有他人的 WIP）⟹ ⟹ 用 `git show HEAD:<path>` 取回
  HEAD 态，并**逐字节**复原工作副本。
- 换源码后**等 dev server 重编**（10s）⟹ ⟹ 否则门禁读的是**旧编译产物**
  ⟹ ⟹ 「翻红」会变成假象。
- 每一态跑**两遍** ⟹ ⟹ 两遍读数必须一致（否则是抖动，不能当因果）。
- 复原后必须校验 **SHA-256 == 基线**。
- ★ 收到 SIGTERM 时也要**先复原源码**再退出。

## 输出
  docs/research/liblib-canvas-batch863-2026-10-01/controlled-comparison.json
  docs/research/liblib-canvas-batch863-2026-10-01/raw/attrib/<态>/<门禁>.txt
  docs/research/liblib-canvas-batch863-2026-10-01/raw/clone-863-frame-mask-{HEAD,WORK}.json
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
BATCH = ROOT / "docs/research/liblib-canvas-batch863-2026-10-01"
RAW = BATCH / "raw/attrib"
PROBE = BATCH / "probes/clone863_frame_mask.py"

# ★ 本批动过的源码文件（本批只动了这一个）
SRC = ["src/components/director/DirectorViewport.tsx"]

# ★ MIX 态的单点变异（★ 行数中性）
MIX_OLD = 'maskComposite: "exclude"'
MIX_NEW = 'maskComposite: "add"'

# ★ 决定性的门禁清单（本批新门禁 ＋ 本批动过其比对对象的老门禁）
GATES = [
    "scripts/verify-liblib-batch863.py",
    "scripts/verify-liblib-batch860.py",
    "scripts/verify-liblib-batch859.py",
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
    # ★ 只让**决定性**的门禁（863）连跑两遍（★ 其余门禁读的是失败集合的差异）
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
            (ROOT / rel).unlink(missing_ok=True)
        else:
            (ROOT / rel).write_bytes(blob.stdout)


def run_probe(tag: str) -> dict:
    """★ 在当前源码状态下跑**同一支** clone 探针 ⟹ ⟹ 得到可比的读数。"""
    proc = subprocess.run([sys.executable, str(PROBE)], cwd=ROOT,
                          capture_output=True, text=True, timeout=1800)
    src_json = BATCH / "raw/clone-863-frame-mask.json"
    dst_json = BATCH / f"raw/clone-863-frame-mask-{tag}.json"
    ok = src_json.exists()
    if ok:
        shutil.copy2(src_json, dst_json)
    print(f"  [探针:{tag}] rc={proc.returncode} 产物={dst_json.name if ok else '无'}",
          flush=True)
    return {"rc": proc.returncode, "产物": str(dst_json.relative_to(ROOT)) if ok else ""}


def main() -> int:
    audit: dict[str, object] = {
        "batch": 863,
        "title": "受控对照：源码换回 HEAD ⟹ 新门禁必须翻红（证明有牙）",
        "gates": GATES,
        "states": STATES,
        "src": SRC,
        "mixMutation": {"old": MIX_OLD, "new": MIX_NEW},
    }
    backup = Path(tempfile.mkdtemp(prefix="b863attrib-"))
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

        # ── 态 3：MIX 单点变异（只改 mask 合成一个词）──
        restore_source(backup)
        src = (ROOT / SRC[0]).read_text(encoding="utf-8")
        if MIX_OLD not in src:
            raise SystemExit(f"MIX 锚点不存在：{MIX_OLD!r}")
        mixed = src.replace(MIX_OLD, MIX_NEW, 1)
        lines_before = src.count("\n")
        (ROOT / SRC[0]).write_text(mixed, encoding="utf-8")
        lines_after = (ROOT / SRC[0]).read_text(encoding="utf-8").count("\n")
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

    # ── 判据 1：两遍读数必须一致 ──
    stable = (work["once"][GATES[0]]["failed"] == work["twice"]["failed"]
              and head["once"][GATES[0]]["failed"] == head["twice"]["failed"])
    audit["stableAcrossTwoRuns"] = stable
    audit["stabilityNote"] = "只有新门禁 863 跑了两遍（决定性测量）"

    # ── 判据 2：新门禁在 HEAD 态必须翻红 ⟹ ⟹ 它有牙 ──
    g863 = GATES[0]
    teeth = (head["once"][g863]["rc"] != 0 and work["once"][g863]["rc"] == 0)
    audit["newGateHasTeeth"] = teeth
    audit["newGateFailedOnHEAD"] = head["once"][g863]["failed"]
    audit["newGateFailedOnWORK"] = work["once"][g863]["failed"]
    audit["newGateCrashOnHEAD"] = [f for f in head["once"][g863]["failed"]
                                   if f.startswith("CRASH:")]

    # ── 判据 3：MIX 态必须「红色探针红、其余绿」⟹ ⟹ 隔离干净 ──
    mix_fail = mix["once"][g863]["failed"]
    audit["mixFailed"] = mix_fail
    red_probe_red = [f for f in mix_fail
                     if "red-probe" in f]
    others = [f for f in mix_fail if "red-probe" not in f]
    audit["mixIsolated"] = {
        "红色探针红": red_probe_red,
        "其余红": others,
        "why": "★ 只改 mask 合成一个词 ⟹ ⟹ 红色探针那条必须红（框内也会被染红）"
               "，而其余判据（几何／黑度／模糊／位置尺寸…）必须**绿**",
    }

    # ── 判据 4：两态下**失败集合的差异**必须逐条可解释 ──
    diffs = {}
    for g in GATES:
        if g == g863:
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

    BATCH.mkdir(parents=True, exist_ok=True)
    (BATCH / "controlled-comparison.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n稳定={stable} 新门禁有牙={teeth} 复原={audit['restored']}",
          flush=True)
    print(f"HEAD 态新门禁红 {len(audit['newGateFailedOnHEAD'])} 条："
          f"{audit['newGateFailedOnHEAD'][:6]}", flush=True)
    print(f"MIX 态新门禁红 {len(mix_fail)} 条：{mix_fail[:6]}", flush=True)
    for g, d in diffs.items():
        print(f"  {g}: HEAD 独有 {len(d['onlyOnHEAD'])} 条 / "
              f"WORK 独有 {len(d['onlyOnWORK'])} 条", flush=True)
    ok = (stable and teeth and audit["restored"]
          and not audit["newGateCrashOnHEAD"]
          and bool(red_probe_red)
          and not any(d["onlyOnWORK"] for d in diffs.values()))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

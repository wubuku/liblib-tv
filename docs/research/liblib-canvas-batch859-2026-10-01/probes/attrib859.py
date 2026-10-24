#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 859 受控对照：把**源码**换回 HEAD ⟹ ⟹ 读数必须能区分。

## ★ 这套对照要证明三件事

① **新门禁有牙**：把源码换回 HEAD ⟹ ⟹ `verify-liblib-batch859.py`
   必须**大面积翻红**（不然它就是空转的）。
② **迁移后的老门禁有牙**：本批迁移过 8 条老门禁（538／589／613／617／
   619／624／625／626）⟹ ⟹ 它们在 HEAD 态（浮层模型）必须**翻红**，
   在 WORK 态（面板模型）必须**绿**。
③ **MIX 半回退态有牙**（★ batch 858 立的做法，本批沿用）：
   全回退只证明「门禁依赖新源码」；**MIX 态**（只把
   `DirectorIconRail.tsx` ＋ `DirectorDesk.tsx` 换回 HEAD、**保留**本批
   新建的两个面板文件）才逼出**判据层**的牙。

## ★ 状态顺序

**HEAD-1 → HEAD-2 → WORK-1 → WORK-2** ⟹ ⟹ **WORK 在最后** ⟹ ⟹
跑完之后磁盘上留着的门禁产物就是**本批源码**读出来的，不是 HEAD 态读出来的。

★ MIX 半回退态由**独立脚本** `attrib859_mix.py` 跑（★ 沿用 batch 858 的形状）⟹ ⟹
理由：MIX 态必须**紧接在 WORK 态之后**才可比（中间不能有别的改动）⟹ ⟹
但如果混在同一个脚本里、且排在最后 ⟹ ⟹ 磁盘上留下的会是 MIX 态的产物
⟹ ⟹ **不对**。所以拆开：先跑本脚本（结尾是 WORK 态），紧接着跑 MIX 脚本。

## ★ 纪律

- 只换**源码**（4 个文件）⟹ ⟹ 门禁脚本保持本批的版本 ⟹ ⟹ 翻红才说明
  「门禁在测新源码」。
- **绝不用 stash**（仓库有他人的 WIP）⟹ ⟹ 用 `git show HEAD:<path>` 取回
  HEAD 态，并**逐字节**复原工作副本。
- 每一态跑**两遍** ⟹ ⟹ 两遍读数必须一致（否则说明有抖动，不能拿它当因果）。
- 复原后必须校验 **SHA-256 == 基线**。
- ★ 收到 SIGTERM 时也要**先复原源码**再退出（后台任务被中止时 finally 未必跑）。
- ★ HEAD 态下本批**新建**的两个面板文件**不存在** ⟹ ⟹ 门禁**不许崩**
  （崩出来的红是**假牙**）⟹ ⟹ `verify-liblib-batch859.py` 已改成
  「文件缺失 ⟹ 源码当空串 ⟹ 逐条判据各自报红」。

## ★ 失败提取（全格式）

沿用 858 的五种红条格式（`  FAILED: `／`FAILED: a,b`／`  FAIL ｜`／
`  [FAIL]`／裸 `assert` traceback）＋ 崩溃签名。

## 输出
  docs/research/liblib-canvas-batch859-2026-10-01/controlled-comparison.json
  docs/research/liblib-canvas-batch859-2026-10-01/raw/attrib/<态>/<门禁>.txt
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
BATCH = ROOT / "docs/research/liblib-canvas-batch859-2026-10-01"
RAW = BATCH / "raw/attrib"

# ★ 本批动过的四个源码文件（HEAD 态是「浮层模型」；后两个**本批新建**）
SRC = [
    "src/components/director/DirectorPanoramaPanel.tsx",
    "src/components/director/DirectorAspectPanel.tsx",
    "src/components/director/DirectorIconRail.tsx",
    "src/components/director/DirectorDesk.tsx",
]

# ★ MIX 半回退态：只回退这两个（它们在 HEAD 里是浮层模型），
#   **保留**本批新建的两个面板文件（它们在 HEAD 里不存在）。
MIX_REVERT = [
    "src/components/director/DirectorIconRail.tsx",
    "src/components/director/DirectorDesk.tsx",
]

# ★ 只跑**决定性**的那几条 ⟹ ⟹ 受控对照要在有限的后台时限里跑完
#   （四态 × 每条门禁一次 ＋ 新门禁每态两遍 ＋ MIX 一次）
#   · 859（新门禁 ⟹ ⟹ 要证明它**有牙**）
#   · 538／589／613／617／619／624／625／626（★ 本批**迁移过**的门禁
#     ⟹ ⟹ 要证明「迁移后的判据**还有牙**」）
#   · 857（★ 用来对照：D10 登记它是**归档型门禁**、结构上无运行时牙
#     ⟹ ⟹ 它在 MIX 态应当**仍然全绿** ⟹ ⟹ 这正是归档型门禁的特征）
GATES = [
    "scripts/verify-liblib-batch859.py",
    "scripts/verify-liblib-batch538.py",
    "scripts/verify-liblib-batch589.py",
    "scripts/verify-liblib-batch613.py",
    "scripts/verify-liblib-batch617.py",
    "scripts/verify-liblib-batch619.py",
    "scripts/verify-liblib-batch624.py",
    "scripts/verify-liblib-batch625.py",
    "scripts/verify-liblib-batch626.py",
    "scripts/verify-liblib-batch857.py",
]

STATES = ["HEAD-1", "HEAD-2", "WORK-1", "WORK-2"]

EXC_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_.]*(?:Error|Exception)):\s*(.*)$")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def extract_failures(text: str) -> list[str]:
    """把 5 种红条格式统一成「一个失败名」的列表。"""
    out: list[str] = []
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        s = ln.strip()
        # ① "  FAILED: <名字>" ／ "FAILED: a, b"（行首无缩进）
        if s.startswith("FAILED:"):
            rest = s[len("FAILED:"):].strip()
            if ln.startswith("FAILED:"):
                out.extend([x.strip() for x in rest.split(",") if x.strip()])
            else:
                out.append(rest)
            continue
        # ② "  FAIL  <名字> ｜ <详情>"
        m = re.match(r"^FAIL\s{2,}(.+?)\s*｜", s)
        if m:
            out.append(m.group(1).strip())
            continue
        # ③ "  [FAIL] <名字>  ⟵ <详情>"
        m = re.match(r"^\[FAIL\]\s*(.+?)(?:\s*⟵.*)?$", s)
        if m:
            out.append(m.group(1).strip())
            continue
        # ④/⑤ assert 型
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
    # ★ 崩溃签名：崩在读文件上的红是**假牙** ⟹ ⟹ 必须能识别出来
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
    """跑一条门禁 ⟹ ⟹ 完整 stdout+stderr 落盘 + 解析红条。"""
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
    """跑一遍全部门禁 ＋ 新门禁再跑一遍（决定性测量必须连跑两遍）。"""
    res: dict[str, dict] = {}
    for g in GATES:
        res[g] = run_gate(g, label)
    res2 = run_gate(GATES[0], label + "-859-2nd")
    return {"once": res, "twice": res2}


def restore_source(backup: Path) -> None:
    for rel in SRC:
        dest = backup / Path(rel).name
        if dest.exists():
            shutil.copy2(dest, ROOT / rel)
        else:
            (ROOT / rel).unlink(missing_ok=True)


def checkout_head(rels: list[str]) -> None:
    """把指定的源码文件换回 HEAD 态（HEAD 里没有的 ⟹ ⟹ 删掉）。"""
    for rel in rels:
        blob = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=ROOT,
                              capture_output=True)
        if blob.returncode != 0:
            (ROOT / rel).unlink(missing_ok=True)
        else:
            (ROOT / rel).write_bytes(blob.stdout)


def main() -> int:
    audit: dict[str, object] = {
        "batch": 859,
        "title": "受控对照：源码换回 HEAD ⟹ 新门禁必须翻红（证明有牙）",
        "gates": GATES,
        "states": STATES,
        "src": SRC,
        "mixRevert": MIX_REVERT,
    }
    backup = Path(tempfile.mkdtemp(prefix="b859attrib-"))
    print(f"★ 备份目录：{backup}", flush=True)
    base_sha: dict[str, str] = {}
    for rel in SRC:
        p = ROOT / rel
        base_sha[rel] = sha(p)
        shutil.copy2(p, backup / Path(rel).name)

    # ★ 收到 SIGTERM ⟹ ⟹ 先复原源码再退出（后台任务被中止时 finally 未必跑）
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

        # ── 复原校验：逐字节 ──
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

    # ── 判据 1：两遍读数必须一致（否则有抖动，不能当因果）──
    stable = (work["once"][GATES[0]]["failed"] == work["twice"]["failed"]
              and head["once"][GATES[0]]["failed"] == head["twice"]["failed"])
    audit["stableAcrossTwoRuns"] = stable
    audit["stabilityNote"] = ("只有新门禁 859 跑了两遍（决定性测量）；"
                              "其余门禁读的是失败集合的差异")

    # ── 判据 2：新门禁在 HEAD 态必须翻红 ⟹ ⟹ 它有牙 ──
    g859 = "scripts/verify-liblib-batch859.py"
    teeth = (head["once"][g859]["rc"] != 0 and work["once"][g859]["rc"] == 0)
    audit["newGateHasTeeth"] = teeth
    audit["newGateFailedOnHEAD"] = head["once"][g859]["failed"]
    audit["newGateFailedOnWORK"] = work["once"][g859]["failed"]
    # ★ 崩出来的红是**假牙** ⟹ ⟹ HEAD 态的红条里不许有 CRASH
    audit["newGateCrashOnHEAD"] = [f for f in head["once"][g859]["failed"]
                                   if f.startswith("CRASH:")]

    # ── 判据 3：被迁移的老门禁在 HEAD 态也必须翻红（证明它们测的是新源码）──
    migrated = [g for g in GATES if g != g859]
    audit["migratedGates"] = {
        g: {"head": head["once"][g]["rc"] != 0, "work": work["once"][g]["rc"] == 0,
            "headFailed": head["once"][g]["failed"],
            "workFailed": work["once"][g]["failed"]}
        for g in migrated
    }

    # ── 判据 4：两态下**失败集合的差异**必须逐条可解释 ──
    diffs = {}
    for g in migrated:
        only_head = sorted(set(head["once"][g]["failed"])
                           - set(work["once"][g]["failed"]))
        only_work = sorted(set(work["once"][g]["failed"])
                           - set(head["once"][g]["failed"]))
        if only_head or only_work:
            diffs[g] = {"onlyOnHEAD": only_head, "onlyOnWORK": only_work}
    audit["diffs"] = diffs
    audit["diffsNote"] = ("HEAD 独有的红条 = 「本批整改掉的旧行为」；"
                          "WORK 独有的红条 = 「本批引入的新问题」（必须为空）")

    # ── 判据 5：MIX 半回退态由**独立脚本**跑（`attrib859_mix.py`）⟹ ⟹
    #   它的结论会**合并**进 `controlled-comparison.json`。
    audit["mixNote"] = ("MIX 半回退态由独立脚本 attrib859_mix.py 跑"
                        "（只把 DirectorIconRail.tsx ＋ DirectorDesk.tsx 换回 HEAD、"
                        "**保留**本批新建的两个面板文件）"
                        "⟹ ⟹ 全回退只证明「门禁依赖新源码」；"
                        "MIX 才逼出**判据层**的牙")

    BATCH.mkdir(parents=True, exist_ok=True)
    (BATCH / "controlled-comparison.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n稳定={stable} 新门禁有牙={teeth} 复原={audit['restored']}", flush=True)
    print(f"HEAD 态新门禁红 {len(audit['newGateFailedOnHEAD'])} 条："
          f"{audit['newGateFailedOnHEAD'][:8]}", flush=True)
    for g, d in diffs.items():
        print(f"  {g}: HEAD 独有 {len(d['onlyOnHEAD'])} 条 / "
              f"WORK 独有 {len(d['onlyOnWORK'])} 条", flush=True)
    ok = stable and teeth and audit["restored"] and not audit["newGateCrashOnHEAD"]
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

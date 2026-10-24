#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 865 受控对照：把**源码**换回 HEAD ⟹ ⟹ 读数必须能区分。

## ★ 这套对照要证明四件事

① **新门禁有牙**：把源码换回 HEAD（= batch 864 的状态：**三分线与开关塞在框里**）
   ⟹ ⟹ `verify-liblib-batch865.py` 必须**具名**翻红。

② **HEAD 态复现 batch 864 登记的 D25**：HEAD 态的容器里只有**两个**子元素
   （遮罩层／框），而**三分线层与开关在框里面** ⟹ ⟹
   ⟹ ⟹ 865 门禁的「四者平级」判据必须**具名翻红** ⟹ ⟹ **且不得崩溃**。

③ **MIX 单点变异态**：★ 只把**三分线层**从「框的子元素」提成「框的兄弟」
   （**一个 JSX 标签位置**）⟹ ⟹ ① 865 的「四者平级」判据必须翻红；
   ⟹ ⟹ ② 862／863 门禁必须**保持绿** ⟹ ⟹ **证明改的就是它**，而且隔离干净。
   ★ ★★ **为什么选这一处**：★ 本批的核心就是「平级 vs 嵌套」⟹ ⟹
   ⟹ ⟹ MIX 态**必须正好打在那个轴上** ⟹ ⟹ 否则这轮对照什么都没证明。

④ **改前/改后同口径**：HEAD 态与 WORK 态各跑一遍**同一个 clone 探针**
   ⟹ ⟹ 得到可比读数。

## ★ 状态与顺序

- `HEAD-1` → `HEAD-2`（源码全部换回 HEAD）⟹ ⟹ 新门禁必须翻红；
- `MIX`（**只**把三分线层提成兄弟）；
- `WORK-1` → `WORK-2`（本批工作副本）⟹ ⟹ 门禁必须全绿；
- ★ **WORK 在最后** ⟹ ⟹ 磁盘上留着的门禁产物是**本批源码**读出来的。

## ★ 纪律

- 只换**源码**（1 个文件）⟹ ⟹ 门禁脚本保持本批版本；
- **绝不用 stash**（仓库有他人的 WIP）⟹ ⟹ 用 `git show HEAD:<path>` 取回 HEAD 态，
  并**逐字节**复原工作副本；
- 换源码后**等 dev server 重编**（10s）⟹ ⟹ 否则门禁读的是**旧编译产物**；
- 每一态跑**两遍** ⟹ ⟹ 两遍读数必须一致；
- 复原后必须校验 **SHA-256 == 基线**；
- ★ 收到 SIGTERM 时也要**先复原源码**再退出；
- ★ **「崩」不算「有牙」**（batch 864 的教训）⟹ ⟹ 判据要求「具名红条 ＋ 零 CRASH」。

## 输出
  docs/research/liblib-canvas-batch865-2026-10-01/controlled-comparison.json
  docs/research/liblib-canvas-batch865-2026-10-01/raw/attrib/<态>/<门禁>.txt
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
BATCH = ROOT / "docs/research/liblib-canvas-batch865-2026-10-01"
RAW = BATCH / "raw/attrib"

# ★ 本批动过的源码文件（★ 只有这 1 个）
SRC = ["src/components/director/DirectorViewport.tsx"]

# ★ ★★ MIX 态的单点变异：★ 把**框**从「自闭合」改成「开标签 ＋ 闭合标签」，
#   ⟹ ⟹ 而闭合标签落在**三分线层之后** ⟹ ⟹
#   ⟹ ⟹ 于是**三分线层从「框的兄弟」变成「框的子元素」** ⟹ ⟹ 正好打中 D25 的轴。
#   ⟹ ⟹ ★ **行数中性**：★ 只在**两处各改一行**（框的 `/>` → `>`；三分线层末尾
#   ⟹ ⟹ `) : null}` → `) : null}</div>`）⟹ ⟹ 行数**不变** ⟹ ⟹ 位置偏移也不变。
MIX_OLD_FRAME = '          outlineOffset: "-1px",\n        }}\n      />\n'
MIX_NEW_FRAME = '          outlineOffset: "-1px",\n        }}\n      >\n'
# ★ 闭合锚点必须**唯一**：★ `        </div>\n      ) : null}\n` 全文出现 **3** 处
#   ⟹ ⟹ 所以扩到**三分线层最后一条线**那段上下文 ⟹ ⟹ 唯一命中。
MIX_OLD_CLOSE = (
    '            style={{ top: "66.667%", backgroundColor: "rgba(255,255,255,0.5)" }}\n'
    '          />\n'
    '        </div>\n'
    '      ) : null}\n'
)
MIX_NEW_CLOSE = (
    '            style={{ top: "66.667%", backgroundColor: "rgba(255,255,255,0.5)" }}\n'
    '          />\n'
    '        </div>\n'
    '      ) : null}</div>\n'
)

GATES = [
    "scripts/verify-liblib-batch865.py",
    "scripts/verify-liblib-batch862.py",
    "scripts/verify-liblib-batch863.py",
]

STATES = ["HEAD-1", "HEAD-2", "MIX", "WORK-1", "WORK-2"]

EXC_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_.]*(?:Error|Exception)):\s*(.*)$")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def extract_failures(text: str) -> list[str]:
    out: list[str] = []
    lines = text.splitlines()
    for ln in lines:
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
            (ROOT / rel).unlink(missing_ok=True)
        else:
            (ROOT / rel).write_bytes(blob.stdout)


def main() -> int:
    audit: dict[str, object] = {
        "batch": 865,
        "title": "受控对照：源码换回 HEAD ⟹ 新门禁必须具名翻红（证明有牙）",
        "gates": GATES,
        "states": STATES,
        "src": SRC,
    }
    backup = Path(tempfile.mkdtemp(prefix="b865attrib-"))
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

    mix_ok = False
    mix_detail: dict[str, object] = {}
    try:
        # ── 态 1/2：源码全部换回 HEAD ⟹ ⟹ 连跑两遍 ──
        checkout_head(SRC)
        time.sleep(10)
        head = run_state("HEAD-1")
        head2 = run_state("HEAD-2")

        # ── 态 3：MIX 单点变异（★ 只把三分线层搬进框里 ⟹ ⟹ 破坏「平级」）──
        restore_source(backup)
        target = ROOT / "src/components/director/DirectorViewport.tsx"
        src = target.read_text(encoding="utf-8")
        # ★ ★ 两处**各改一行** ⟹ ⟹ 行数中性 ⟹ ⟹ 位置偏移也不变
        if MIX_OLD_FRAME not in src:
            raise SystemExit(f"MIX 锚点（框）不存在：{MIX_OLD_FRAME!r}")
        if MIX_OLD_CLOSE not in src:
            raise SystemExit(f"MIX 锚点（闭合）不存在：{MIX_OLD_CLOSE!r}")
        if src.count(MIX_OLD_CLOSE) != 1:
            raise SystemExit(f"MIX 锚点（闭合）不唯一：{src.count(MIX_OLD_CLOSE)}")
        lines_before = src.count("\n")
        mutated = src.replace(MIX_OLD_FRAME, MIX_NEW_FRAME, 1)
        mutated = mutated.replace(MIX_OLD_CLOSE, MIX_NEW_CLOSE, 1)
        target.write_text(mutated, encoding="utf-8")
        lines_after = target.read_text(encoding="utf-8").count("\n")
        audit["MIX行数中性"] = lines_before == lines_after
        audit["MIX旧锚点"] = MIX_OLD_FRAME
        audit["MIX新锚点"] = MIX_NEW_FRAME
        mix_ok = True
        mix_detail["行数中性"] = lines_before == lines_after
        time.sleep(10)
        mix = run_state("MIX")

        # ── 态 4/5：复原到本批工作副本 ⟹ ⟹ 连跑两遍（★ WORK 留在最后）──
        restore_source(backup)
        time.sleep(10)
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
    audit["mix"] = mix

    g865 = GATES[0]

    stable = (work["once"][g865]["failed"] == work["twice"]["failed"]
              and head["once"][g865]["failed"] == head["twice"]["failed"]
              and mix["once"][g865]["failed"] == mix["twice"]["failed"])
    audit["stableAcrossTwoRuns"] = stable

    teeth = (head["once"][g865]["rc"] != 0 and work["once"][g865]["rc"] == 0)
    audit["newGateHasTeeth"] = teeth
    audit["newGateFailedOnHEAD"] = head["once"][g865]["failed"]
    audit["newGateFailedOnWORK"] = work["once"][g865]["failed"]
    audit["newGateCrashOnHEAD"] = [f for f in head["once"][g865]["failed"]
                                   if f.startswith("CRASH:")]
    audit["newGateCrashOnMIX"] = [f for f in mix["once"][g865]["failed"]
                                  if f.startswith("CRASH:")]

    # ★ ★ HEAD 态必须**具名**复现 D25（不是崩溃）
    head_red = head["once"][g865]["failed"]
    named_head = [f for f in head_red if not f.startswith("CRASH:")]
    audit["headStateReproducesD25"] = {
        "具名红条": named_head,
        "零崩溃": not audit["newGateCrashOnHEAD"],
    }

    # ★ ★ MIX 态：865 的「四者平级／空框」判据必须红 ⟹ ⟹ 862／863 必须**保持绿**
    mix_fail = mix["once"][g865]["failed"]
    mix_named = [f for f in mix_fail if not f.startswith("CRASH:")]
    mix_other = {}
    for g in GATES[1:]:
        mix_other[g] = mix["once"][g]["failed"]
    audit["mixFailed865"] = mix_fail
    audit["mixNamedReds865"] = mix_named
    audit["mixOtherGates"] = mix_other
    audit["mixIsolated"] = {
        "865的红": mix_named,
        "862的红": mix_other.get(GATES[1], []),
        "863的红": mix_other.get(GATES[2], []),
        "why": "★ 只把三分线层搬进框里 ⟹ ⟹ 865 的「四者平级」与「空框」必须红 "
               "⟹ ⟹ 862／863 必须**保持绿** ⟹ ⟹ 证明改的就是它，且隔离干净",
    }

    diffs = {}
    for g in GATES:
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
    print(f"HEAD 态 865 门禁红 {len(head_red)} 条", flush=True)
    print(f"HEAD 态具名红：{named_head[:6]}", flush=True)
    print(f"MIX 态 865 门禁红 {len(mix_fail)} 条：{mix_named[:8]}", flush=True)
    for g, d in diffs.items():
        print(f"  {g}: HEAD 独有 {len(d['onlyOnHEAD'])} 条 / "
              f"WORK 独有 {len(d['onlyOnWORK'])} 条", flush=True)

    ok = (stable and teeth and audit["restored"]
          and not audit["newGateCrashOnHEAD"]
          and not audit["newGateCrashOnMIX"]
          and bool(named_head)
          and bool(mix_named)
          and not mix_other.get(GATES[1])
          and not mix_other.get(GATES[2])
          and not any(d["onlyOnWORK"] for d in diffs.values()))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

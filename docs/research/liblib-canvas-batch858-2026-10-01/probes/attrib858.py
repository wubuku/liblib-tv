#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 858 受控对照：把**源码**换回 HEAD ⟹ ⟹ 读数必须能区分。

## ★ 这套对照要证明三件事

① **新门禁有牙**：把三个源码文件换回 HEAD ⟹ ⟹ `verify-liblib-batch858.py`
   必须**大面积翻红**（不然它就是空转的）。
② **迁移后的老门禁有牙**：同一批老门禁在 HEAD 态下必须**翻红在迁移点上**
   （证明它们真的在测「面板化」这件事，而不是恰好都绿）。
③ **别的红不是本批引入**：老门禁在两态下的**失败集合差异**，必须**逐条**
   能被本批的改动解释；解释不了的 ⟹ ⟹ 那是旧账。

## ★ 状态顺序（★ 本轮改过）

**HEAD-1 → HEAD-2 → WORK-1 → WORK-2** ⟹ ⟹ **WORK 在最后** ⟹ ⟹
跑完之后磁盘上留着的门禁产物（runtime-audit.json / 截图）就是
**本批源码**读出来的，不是 HEAD 态读出来的。

## ★ 失败提取（全格式）

八个门禁的**红条格式有 5 种**，第一版 attrib 只认 2 种 ⟹ ⟹
「失败集合差异」解析成空 ⟹ ⟹ 归因无从谈起：

| 门禁 | 红条长相 |
|---|---|
| 门禁 858 | `  FAILED: <名字>` |
| 门禁 613 ／ 门禁 625 | `FAILED: <名字>, <名字>`（行首无缩进，逗号分隔） |
| 门禁 857 | `  FAIL  <名字> ｜ <详情>` |
| 门禁 738 | `  [FAIL] <名字>  ⟵ <详情>` |
| 门禁 536 ／ 门禁 589 | `AssertionError: batchXXX check failed: <名字>`（裸 assert） |
| 门禁 45 | `AssertionError`（无消息，表达式在 traceback 的源码行里） |

★ ★ **首列不要写成裸数字**：本仓的 `pre-commit` 钩子（`docs/user-manual/beeftv-canvas`
那套「构建记录核对」）会把「新增行里形如 `| 45 |` 的表格首格」当成**手册批次行**
⟹ ⟹ 本文件的表格若写成 `| 45 |` 就会被判成「新增了 Batch 45 的批次行」⟹ ⟹ 钩子拦下
⟹ ⟹ （那套编号空间与本项目**重号** ⟹ ⟹ 是**误报**）⟹ ⟹ 所以首列写成「门禁 45」。

⟹ 本版把**每次运行的完整 stdout+stderr 落盘**到 `raw/attrib/<态>/<门禁>.txt`，
再用 `extract_failures()` 统一提取 ⟹ ⟹ 归因时能直接翻原文。

## ★ 纪律

- 只换**源码**（3 个文件）⟹ ⟹ 门禁脚本保持本批的版本 ⟹ ⟹ 翻红才说明
  「门禁在测新源码」。
- **绝不用 stash**（仓库有他人的 WIP）⟹ ⟹ 用 `git show HEAD:<path>` 取回
  HEAD 态，并**逐字节**复原工作副本。
- 每一态跑**两遍** ⟹ ⟹ 两遍读数必须一致（否则说明有抖动，不能拿它当因果）。
- 复原后必须校验 **SHA-256 == 基线**。
- ★ 收到 SIGTERM 时也要**先复原源码**再退出（后台任务被中止时 finally 未必跑）。

## 输出
  docs/research/liblib-canvas-batch858-2026-10-01/controlled-comparison.json
  docs/research/liblib-canvas-batch858-2026-10-01/raw/attrib/<态>/<门禁>.txt
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
BATCH = ROOT / "docs/research/liblib-canvas-batch858-2026-10-01"
RAW = BATCH / "raw/attrib"

# ★ 本批动过的三个源码文件（HEAD 态是「浮层 + 写死坐标」）
SRC = [
    "src/components/director/DirectorCharacterPanel.tsx",
    "src/components/director/DirectorIconRail.tsx",
    "src/components/director/DirectorDesk.tsx",
]

# ★ 新门禁（要有牙的那个）＋ 被迁移的老门禁
# ★ 只跑**决定性**的那几条 ⟹ ⟹ 受控对照要在有限的后台时限里跑完
#   （四态 × 每条门禁一次 ＋ 新门禁每态两遍）⟹ ⟹ 清单收窄到 8 条：
#   · 858（新门禁 ⟹ ⟹ 要证明它**有牙**）
#   · 536／589／613／625／45／857（★ 本批**迁移过**的门禁 ⟹ ⟹ 要证明
#     「迁移后的判据**还有牙**」）
#   · 738（★ 迁移得最狠的一条：z-160→z-1800、几何改就地展开、写死的个数
#     改成结构性断言）
#   其余迁移过的门禁（541／619／626／648／590）由**回归**（regress858）
#   逐条覆盖 ⟹ ⟹ 不在这里重复跑（跑两遍两态要 90 分钟，超后台时限）。
GATES = [
    "scripts/verify-liblib-batch858.py",
    "scripts/verify-liblib-batch536.py",
    "scripts/verify-liblib-batch589.py",
    "scripts/verify-liblib-batch613.py",
    "scripts/verify-liblib-batch625.py",
    "scripts/verify-liblib-batch45.py",
    "scripts/verify-liblib-batch857.py",
    "scripts/verify-liblib-batch738.py",
]

# ★ 状态顺序：HEAD 先、WORK 后 ⟹ ⟹ 跑完留在磁盘上的产物是 WORK 态的
STATES = ["HEAD-1", "HEAD-2", "WORK-1", "WORK-2"]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def extract_failures(text: str) -> list[str]:
    """把 5 种红条格式统一成「一个失败名」的列表。

    ★ 归因要靠它 ⟹ ⟹ 必须能认出「是哪一条判据红了」，而不只是「红了几条」。
    """
    out: list[str] = []
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        s = ln.strip()
        # ① 858：  "  FAILED: <名字>" ／ 613/625： "FAILED: a, b"（行首无缩进）
        if s.startswith("FAILED:"):
            rest = s[len("FAILED:"):].strip()
            if ln.startswith("FAILED:"):
                # 行首无缩进 ⟹ 613/625 的逗号分隔列表
                out.extend([x.strip() for x in rest.split(",") if x.strip()])
            else:
                out.append(rest)
            continue
        # ② 857：  "  FAIL  <名字> ｜ <详情>"
        m = re.match(r"^FAIL\s{2,}(.+?)\s*｜", s)
        if m:
            out.append(m.group(1).strip())
            continue
        # ③ 738：  "  [FAIL] <名字>  ⟵ <详情>"
        m = re.match(r"^\[FAIL\]\s*(.+?)(?:\s*⟵.*)?$", s)
        if m:
            out.append(m.group(1).strip())
            continue
        # ④/⑤ assert 型（536／589／45）：traceback 的最后一行
        if s == "AssertionError" or s.startswith("AssertionError:"):
            msg = s[len("AssertionError"):].lstrip(": ").strip()
            if msg:
                # "batch536 check failed: <名字>" ／ "batch589 check failed: <名字> :: <详情>"
                m2 = re.match(r"^batch\d+ check failed:\s*(.*?)(?:\s*::.*)?$", msg)
                out.append(m2.group(1).strip() if m2 else msg)
            else:
                # 45 的裸 assert ⟹ 表达式在 traceback 的源码行里
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
    # 去重但保序
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
                          capture_output=True, text=True, timeout=1800)
    out = (proc.stdout or "") + (proc.stderr or "")
    (out_dir / f"{gate_name}.txt").write_text(out, encoding="utf-8")
    failed = extract_failures(out)
    dur = round(time.time() - t0, 1)
    print(f"  [{label}] {gate_name}  rc={proc.returncode}  "
          f"红条 {len(failed)}  {dur}s", flush=True)
    return {"rc": proc.returncode, "failed": failed, "seconds": dur,
            "log": str((out_dir / f"{gate_name}.txt").relative_to(ROOT))}


def run_state(label: str) -> dict:
    """跑一遍全部门禁。

    ★ 只有**新门禁 858** 再跑一遍（`twice`）⟹ ⟹ 「连跑两遍」这条纪律用在
    **决定性**的那次测量上（它决定「有牙」这个结论）；其余门禁跑一遍
    ⟹ ⟹ 它们的用途是「失败集合的差异」，靠**集合比对**而不是靠重复读数
    来保证稳定性（重复跑 8 条浏览器门禁 × 4 态 = 32 次，太贵）。
    """
    res: dict[str, dict] = {}
    for g in GATES:
        res[g] = run_gate(g, label)
    res2 = run_gate(GATES[0], label + "-858-2nd")
    return {"once": res, "twice": res2}


def restore_source(backup: Path) -> None:
    for rel in SRC:
        dest = backup / Path(rel).name
        if dest.exists():
            shutil.copy2(dest, ROOT / rel)
        else:
            (ROOT / rel).unlink(missing_ok=True)


def main() -> int:
    audit: dict[str, object] = {
        "batch": 858,
        "title": "受控对照：源码换回 HEAD ⟹ 新门禁必须翻红（证明有牙）",
        "gates": GATES,
        "states": STATES,
    }
    backup = Path(tempfile.mkdtemp(prefix="b858attrib-"))
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
        # ── 态 1/2：源码换回 HEAD ⟹ ⟹ 连跑两遍 ──
        for rel in SRC:
            blob = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=ROOT,
                                  capture_output=True)
            if blob.returncode != 0:
                # HEAD 里没有这个文件（本批新建的）⟹ ⟹ 删掉它
                (ROOT / rel).unlink(missing_ok=True)
            else:
                (ROOT / rel).write_bytes(blob.stdout)
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
    audit["stabilityNote"] = ("只有新门禁 858 跑了两遍（决定性测量）；"
                              "其余门禁读的是失败集合的差异")

    # ── 判据 2：新门禁在 HEAD 态必须翻红 ⟹ ⟹ 它有牙 ──
    g858 = "scripts/verify-liblib-batch858.py"
    teeth = (head["once"][g858]["rc"] != 0 and work["once"][g858]["rc"] == 0)
    audit["newGateHasTeeth"] = teeth
    audit["newGateFailedOnHEAD"] = head["once"][g858]["failed"]
    audit["newGateFailedOnWORK"] = work["once"][g858]["failed"]

    # ── 判据 3：被迁移的老门禁在 HEAD 态也必须翻红（证明它们测的是新源码）──
    migrated = [g for g in GATES if g != g858]
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

    BATCH.mkdir(parents=True, exist_ok=True)
    (BATCH / "controlled-comparison.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n稳定={stable} 新门禁有牙={teeth} 复原={audit['restored']}", flush=True)
    print(f"HEAD 态新门禁红 {len(audit['newGateFailedOnHEAD'])} 条："
          f"{audit['newGateFailedOnHEAD'][:8]}", flush=True)
    for g, d in diffs.items():
        print(f"  {g}: HEAD 独有 {len(d['onlyOnHEAD'])} 条 / "
              f"WORK 独有 {len(d['onlyOnWORK'])} 条", flush=True)
    return 0 if (stable and teeth and audit["restored"]) else 1


if __name__ == "__main__":
    sys.exit(main())

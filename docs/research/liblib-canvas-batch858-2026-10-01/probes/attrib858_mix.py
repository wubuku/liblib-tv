#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 858 受控对照·补充：**MIX 半回退态** ＋ **统一归因报告**。

## ★ 为什么要有 MIX 态（第一版 attrib 的盲区）

主受控对照（attrib858.py）把**三个源文件全换回 HEAD** ⟹ ⟹
`DirectorCharacterPanel.tsx`（本批新建）在 HEAD 里不存在 ⟹ ⟹
门禁 45／857／738 **在读源文件那一步就 FileNotFoundError 崩掉**，
根本没走到浏览器层的判据。

⟹ ⟹ 那只证明了「门禁依赖本批的新源码」，**没证明「迁移后的判据本身有牙」**。

★ MIX 态的做法：**只把旧的两个文件换回 HEAD**（`DirectorIconRail.tsx`
＋ `DirectorDesk.tsx`），**保留本批新建的 `DirectorCharacterPanel.tsx`**
⟹ ⟹ 门禁能读得到源文件 ⟹ ⟹ 会一路走到浏览器层 ⟹ ⟹
**判据本身**必须翻红（这才是「有牙」的强证据）。

## ★ 归因报告为什么重算一遍

第一版提取器只认 5 种「红条」格式 ⟹ ⟹ **崩在 traceback 里的那种**（FileNotFoundError 等）
会被解析成「0 条红条」⟹ ⟹ 归因时看不出「它到底崩在哪一步」。

⟹ ⟹ 本脚本把**每一态每一门禁的完整输出**重新过一遍，
   崩掉的补上 `CRASH: <异常类型>: <消息>` 的签名，
   然后合并出唯一的 `controlled-comparison.json`。

## ★ 纪律

- **绝不用 stash**（仓库有他人的 WIP）⟹ ⟹ 用 `git show HEAD:<path>` 取 HEAD 态。
- 跑完必须**逐字节复原**并校验 SHA-256。
- 收到 SIGTERM ⟹ ⟹ 先复原再退出。
- 状态顺序：MIX 跑完就复原到 WORK ⟹ ⟹ 磁盘上留着的产物仍是 WORK 态的。

## 输出
  docs/research/liblib-canvas-batch858-2026-10-01/raw/attrib/MIX/<门禁>.txt
  docs/research/liblib-canvas-batch858-2026-10-01/controlled-comparison.json（合并覆盖）
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

SRC = [
    "src/components/director/DirectorCharacterPanel.tsx",
    "src/components/director/DirectorIconRail.tsx",
    "src/components/director/DirectorDesk.tsx",
]
# ★ MIX 态：**只有这两个**换回 HEAD；新建的那个文件保留本批版本
MIX_REVERT = [
    "src/components/director/DirectorIconRail.tsx",
    "src/components/director/DirectorDesk.tsx",
]

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

EXC_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_.]*(?:Error|Exception))\s*:\s*(.*)$")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def extract_failures(text: str) -> list[str]:
    """5 种红条格式 ＋ 1 种崩溃签名。"""
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
    # ★ 崩溃签名：traceback 里的异常（FileNotFoundError 等）⟹ ⟹ 也要能归因
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
                          capture_output=True, text=True, timeout=1800)
    out = (proc.stdout or "") + (proc.stderr or "")
    (out_dir / f"{gate_name}.txt").write_text(out, encoding="utf-8")
    failed = extract_failures(out)
    dur = round(time.time() - t0, 1)
    print(f"  [{label}] {gate_name}  rc={proc.returncode}  "
          f"红条 {len(failed)}  {dur}s", flush=True)
    return {"rc": proc.returncode, "failed": failed, "seconds": dur,
            "log": str((out_dir / f"{gate_name}.txt").relative_to(ROOT))}


def restore(backup: Path) -> None:
    for rel in SRC:
        dest = backup / Path(rel).name
        if dest.exists():
            shutil.copy2(dest, ROOT / rel)
        else:
            (ROOT / rel).unlink(missing_ok=True)


def main() -> int:
    backup = Path(tempfile.mkdtemp(prefix="b858mix-"))
    print(f"★ 备份目录：{backup}", flush=True)
    base_sha = {rel: sha(ROOT / rel) for rel in SRC}
    for rel in SRC:
        shutil.copy2(ROOT / rel, backup / Path(rel).name)

    def _on_term(signum, frame):  # noqa: ANN001
        print("★ 收到信号 ⟹ 复原源码后退出", flush=True)
        restore(backup)
        raise SystemExit(143)

    signal.signal(signal.SIGTERM, _on_term)
    signal.signal(signal.SIGINT, _on_term)

    try:
        # ── MIX 态：只把旧的两个文件换回 HEAD，新文件保留本批版本 ──
        for rel in MIX_REVERT:
            blob = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=ROOT,
                                  capture_output=True)
            assert blob.returncode == 0, rel
            (ROOT / rel).write_bytes(blob.stdout)
        mix: dict[str, dict] = {}
        for g in GATES:
            mix[g] = run_gate(g, "MIX")
        mix2 = run_gate(GATES[0], "MIX-858-2nd")
    finally:
        restore(backup)
        shutil.rmtree(backup, ignore_errors=True)

    restored = {rel: sha(ROOT / rel) for rel in SRC}
    if restored != base_sha:
        raise SystemExit("复原自检失败 ⟹ 文件被改坏了")

    # ── 合并报告：用**改进后的提取器**把所有态的日志重新过一遍 ──
    audit: dict[str, object] = {}
    main_path = BATCH / "controlled-comparison.json"
    if main_path.exists():
        audit = json.loads(main_path.read_text(encoding="utf-8"))

    def reload_state(label: str, gates: list[str]) -> dict:
        res: dict[str, dict] = {}
        for g in gates:
            log = RAW / label / f"{Path(g).stem}.txt"
            if not log.exists():
                continue
            text = log.read_text(encoding="utf-8")
            res[g] = {"rc": 1 if ("FAILED" in text or "Traceback" in text) else 0,
                      "failed": extract_failures(text),
                      "log": str(log.relative_to(ROOT))}
        return res

    states = ["HEAD-1", "HEAD-2", "WORK-1", "WORK-2"]
    reloaded = {s: reload_state(s, GATES) for s in states}
    reloaded["MIX"] = {g: {"rc": v["rc"], "failed": v["failed"], "log": v["log"]}
                       for g, v in mix.items()}

    audit["states"] = states + ["MIX"]
    audit["mixNote"] = ("MIX 半回退态：只把 DirectorIconRail.tsx ＋ DirectorDesk.tsx "
                        "换回 HEAD，保留本批新建的 DirectorCharacterPanel.tsx "
                        "⟹ ⟹ 门禁能读到源文件 ⟹ ⟹ 翻红必须发生在**判据**上，"
                        "而不是「文件不存在」这种假牙")
    audit["mix"] = {
        "rc": {g: v["rc"] for g, v in mix.items()},
        "failed": {g: v["failed"] for g, v in mix.items()},
        "twice": mix2,
        "stable": mix[GATES[0]]["failed"] == mix2["failed"],
    }
    audit["restored"] = True
    audit["sha"] = {"base": base_sha, "after": restored}

    # ── 判据：MIX 态下**每条**门禁都必须翻红（rc≠0），且红条不能是
    #    「CRASH: FileNotFoundError」这种假牙 ──
    mix_crash_only = [g for g, v in mix.items()
                      if v["failed"] and all(f.startswith("CRASH:") for f in v["failed"])]
    audit["mixAllRed"] = all(v["rc"] != 0 for v in mix.values())
    audit["mixCrashOnly"] = mix_crash_only
    audit["mixNote2"] = ("mixAllRed：MIX 态 8 条门禁全红 ⟹ ⟹ 迁移后的判据确实有牙；"
                         "mixCrashOnly 里的门禁仍只崩在读文件上 ⟹ ⟹ "
                         "它的判据层还没被压到（需另行说明）")

    # ── 各态的失败集合（供归因）──
    summary: dict[str, dict] = {}
    for s in states + ["MIX"]:
        summary[s] = {g: v.get("failed", []) for g, v in reloaded[s].items()}
    audit["failureSets"] = summary

    main_path.write_text(json.dumps(audit, ensure_ascii=False, indent=1),
                         encoding="utf-8")
    print(f"\nMIX 全红={audit['mixAllRed']}  复原={restored == base_sha}", flush=True)
    for g, v in mix.items():
        print(f"  {g}: rc={v['rc']} 红条 {v['failed'][:3]}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

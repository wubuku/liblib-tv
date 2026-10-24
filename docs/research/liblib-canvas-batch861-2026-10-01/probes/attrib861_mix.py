#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 861 受控对照 · **MIX 半回退态**（独立脚本）。

## ★ 为什么要有 MIX 态

**全回退**（四个文件全换回 HEAD）只证明：「门禁依赖新源码」。

**MIX 半回退态**（batch 858 立的做法，本批沿用）：
只把 **`DirectorPanoramaPanel.tsx`** 换回 HEAD
（⟹ ⟹ 它回到「三行没有 `onClick`」的老写法），
**保留** store / lib / picker 的**新**代码。

⟹ ⟹ 这正好**隔离出「三行没接行为」这一条**：
- store 里 `localPanoramaAsset` 还在 ⟹ ⟹ 静态判据（store 那几条）**不该红**；
- 但面板**不触发** file input、**不开**选择器 ⟹ ⟹
  **运行时判据必须红**（`clone:local-upload-opens-a-file-chooser`／
  `clone:history-opens-the-picker`／`clone:ai-generate-opens-the-picker`）。

⇒ ⇒ MIX 态红得「不多不少」⟹ ⟹ 才证明**判据层**有牙，
而不是「整个功能都没了所以红」。

## ★ 输出
  docs/research/liblib-canvas-batch861-2026-10-01/controlled-comparison.json（合并）
  docs/research/liblib-canvas-batch861-2026-10-01/raw/attrib/MIX/<门禁>.txt
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
BATCH = ROOT / "docs/research/liblib-canvas-batch861-2026-10-01"
RAW = BATCH / "raw/attrib"

SRC = [
    "src/store/directorStore.ts",
    "src/lib/directorCanvasMediaIngress.ts",
    "src/components/director/DirectorPanoramaPanel.tsx",
    "src/components/director/DirectorPanoramaPicker.tsx",
    "src/components/director/DirectorDesk.tsx",
]

# ★ MIX：**只**回退面板（store 与 math 保留本批新代码）
MIX_REVERT = ["src/components/director/DirectorPanoramaPanel.tsx"]

GATES = [
    "scripts/verify-liblib-batch861.py",
    "scripts/verify-liblib-batch860.py",
    "scripts/verify-liblib-batch590.py",
]


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
    exc_re = re.compile(r"^([A-Za-z_][A-Za-z0-9_.]*(?:Error|Exception)):\s*(.*)$")
    if "Traceback (most recent call last):" in text and not out:
        for ln in reversed(lines):
            s = ln.strip()
            if not s:
                continue
            m = exc_re.match(s)
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


def restore(backup: Path) -> None:
    for rel in SRC:
        shutil.copy2(backup / Path(rel).name, ROOT / rel)


def main() -> int:
    backup = Path(tempfile.mkdtemp(prefix="b860mix-"))
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
        for rel in MIX_REVERT:
            blob = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=ROOT,
                                  capture_output=True)
            assert blob.returncode == 0, rel
            (ROOT / rel).write_bytes(blob.stdout)
        mix: dict[str, dict] = {}
        for g in GATES:
            mix[g] = run_gate(g, "MIX")
        mix2 = run_gate(GATES[0], "MIX-860-2nd")
    finally:
        restore(backup)
        shutil.rmtree(backup, ignore_errors=True)

    restored = {rel: sha(ROOT / rel) for rel in SRC}
    if restored != base_sha:
        raise SystemExit("复原自检失败 ⟹ 文件被改坏了")

    main_path = BATCH / "controlled-comparison.json"
    audit: dict = {}
    if main_path.exists():
        audit = json.loads(main_path.read_text(encoding="utf-8"))
    else:
        print("★ 主报告不存在 ⟹ ⟹ 先跑 attrib860.py")

    stable = mix[GATES[0]]["failed"] == mix2["failed"]
    audit["mix"] = {"once": mix, "twice": mix2}
    audit["mixStable"] = stable
    audit["mixRestored"] = restored == base_sha
    audit["mixNote"] = (
        "MIX 半回退态：只把 DirectorPanoramaPanel.tsx 换回 HEAD"
        "（组件内 useState 的老写法）、**保留** store 与 math 的新代码 "
        "⟹ ⟹ 正好隔离出「面板没接 store」这一条："
        "store 那几条静态判据**不该红**、运行时判据**必须红**")
    audit["mixCrash"] = [f for g in GATES for f in mix[g]["failed"]
                         if f.startswith("CRASH:")]

    main_path.write_text(json.dumps(audit, ensure_ascii=False, indent=1),
                         encoding="utf-8")
    print(f"\nMIX 稳定={stable} 复原={audit['mixRestored']} "
          f"崩溃红条={len(audit['mixCrash'])}", flush=True)
    for g in GATES:
        print(f"  {Path(g).stem}: 红 {len(mix[g]['failed'])} 条 "
              f"{mix[g]['failed'][:4]}", flush=True)
    return 0 if (stable and audit["mixRestored"]
                 and not audit["mixCrash"]) else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 859 受控对照 · **MIX 半回退态**（独立脚本）。

## ★ 为什么要有 MIX 态

**全回退**（把四个源码文件全换回 HEAD）只证明一件事：**门禁依赖新源码**。
它**逼不出判据层的牙** —— 因为 HEAD 态里整个功能都不存在，
判据当然红 ⟹ ⟹ 红得「太容易」⟹ ⟹ 说明不了「判据本身够不够细」。

**MIX 半回退态**（batch 858 立的做法，本批沿用）：
只把 `DirectorIconRail.tsx` ＋ `DirectorDesk.tsx` 换回 HEAD（⟹ ⟹ 回到
**浮层模型**：rail 上挂 portal 浮层、左侧面板不认识 panorama／aspect 模式），
**保留**本批**新建**的两个面板文件（`DirectorPanoramaPanel.tsx` ＋
`DirectorAspectPanel.tsx`）。

⟹ ⟹ MIX 态下：
- 两个新面板文件**在位** ⟹ ⟹ 「文件存在」这类静态判据**不该红**；
- 但 rail／desk **不认识**它们 ⟹ ⟹ 「面板在 aside 里」「五模式互斥」
  「rail 选中态跟随模式」这类**行为判据**必须**红**。
⇒ ⇒ MIX 态红得「不多不少」⟹ ⟹ 才证明**判据层**有牙。

## ★ 与全回退态的差别

| 判据类型 | HEAD 全回退 | MIX 半回退 | 期望 |
|---|---|---|---|
| 静态（文件里有没有这个类串） | 红 | **红**（新面板文件仍在 ⟹ ⟹ 只红「rail 引用了旧浮层」那类） | 红 |
| 静态（`ASPECT_GLYPH` 在哪） | 红 | 红（rail 回退 ⟹ ⟹ 字形表不在 rail） | 红 |
| 行为（面板在 aside 里） | 红 | 红 | 红 |
| 行为（rail 选中态跟随模式） | 红 | 红 | 红 |
| 行为（旧浮层已清零） | 红 | 红（浮层回来了） | 红 |

## ★ 输出
  docs/research/liblib-canvas-batch859-2026-10-01/controlled-comparison.json（合并）
  docs/research/liblib-canvas-batch859-2026-10-01/raw/attrib/MIX/<门禁>.txt
"""
from __future__ import annotations

import hashlib
import json
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

# ★ 本批动过的四个源码文件
SRC = [
    "src/components/director/DirectorPanoramaPanel.tsx",
    "src/components/director/DirectorAspectPanel.tsx",
    "src/components/director/DirectorIconRail.tsx",
    "src/components/director/DirectorDesk.tsx",
]

# ★ MIX：只回退这两个（HEAD 里是浮层模型）；两个新建面板文件**保留**
MIX_REVERT = [
    "src/components/director/DirectorIconRail.tsx",
    "src/components/director/DirectorDesk.tsx",
]

# ★ 只跑**决定性**的那几条（与 attrib859.py 的清单一致）
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


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def extract_failures(text: str) -> list[str]:
    """与 attrib859.py 同口径的红条提取（5 种格式 ＋ 崩溃签名）。"""
    import re
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
        dest = backup / Path(rel).name
        if dest.exists():
            shutil.copy2(dest, ROOT / rel)
        else:
            (ROOT / rel).unlink(missing_ok=True)


def main() -> int:
    backup = Path(tempfile.mkdtemp(prefix="b859mix-"))
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
        # ── MIX 态：只回退 rail+desk，两个新面板文件保留 ──
        for rel in MIX_REVERT:
            blob = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=ROOT,
                                  capture_output=True)
            assert blob.returncode == 0, rel
            (ROOT / rel).write_bytes(blob.stdout)
        mix: dict[str, dict] = {}
        for g in GATES:
            mix[g] = run_gate(g, "MIX")
        # ★ 新门禁再跑一遍 ⟹ ⟹ 证明 MIX 态的读数**稳定**（不是抖动）
        mix2 = run_gate(GATES[0], "MIX-859-2nd")
    finally:
        restore(backup)
        shutil.rmtree(backup, ignore_errors=True)

    restored = {rel: sha(ROOT / rel) for rel in SRC}
    if restored != base_sha:
        raise SystemExit("复原自检失败 ⟹ 文件被改坏了")

    # ── 合并进主报告 ──
    main_path = BATCH / "controlled-comparison.json"
    audit: dict = {}
    if main_path.exists():
        audit = json.loads(main_path.read_text(encoding="utf-8"))
    else:
        print("★ 主报告不存在 ⟹ ⟹ 先跑 attrib859.py")

    stable = mix[GATES[0]]["failed"] == mix2["failed"]
    audit["mix"] = {"once": mix, "twice": mix2}
    audit["mixStable"] = stable
    audit["mixRestored"] = restored == base_sha
    audit["mixNote"] = (
        "MIX 半回退态：只把 DirectorIconRail.tsx ＋ DirectorDesk.tsx 换回 HEAD"
        "（浮层模型）、**保留**本批新建的两个面板文件 "
        "⟹ ⟹ 新门禁 859 必须**红**（rail/desk 不认识那两个面板）"
        "⟹ ⟹ 这才逼出**判据层**的牙"
        "（全回退态只证明「门禁依赖新源码」）")
    # ★ 崩溃的红是**假牙** ⟹ ⟹ 不许出现
    audit["mixCrash"] = [f for g in GATES for f in mix[g]["failed"]
                         if f.startswith("CRASH:")]

    main_path.write_text(json.dumps(audit, ensure_ascii=False, indent=1),
                         encoding="utf-8")
    print(f"\nMIX 稳定={stable} 复原={audit['mixRestored']} "
          f"崩溃红条={len(audit['mixCrash'])}", flush=True)
    for g in GATES:
        print(f"  {Path(g).stem}: 红 {len(mix[g]['failed'])} 条 "
              f"{mix[g]['failed'][:3]}", flush=True)
    return 0 if (stable and audit["mixRestored"]
                 and not audit["mixCrash"]) else 1


if __name__ == "__main__":
    sys.exit(main())

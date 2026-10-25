#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 868 探针：★ 把**清单之外**却碰导演台源文件的那批门禁跑一遍 ⟹ ⟹ 拿基线。

## ★ 靶子（★ 为什么是这批）

★ batch 866 的普查口径是「门禁**文本里出现**被跟踪源文件的**文件名**」
⟹ ⟹ ⟹ ⟹ ⇒ ★ 对「**按目录扫描**」的门禁是**失明**的
⟹ ⟹ ⟹ ⟹ ⇒ ★ `367` 扫的是整个 `src/components/**` ⟹ ⟹ 从不出现
⟹ ⟹ ⟹ ⟹ ⇒ `DirectorViewport.tsx` 这个名字 ⟹ ⟹ ⟹ ⟹ ⇒ 它**没进普查视野**
⟹ ⟹ ⟹ ⟹ ⇒ ★ 而它**当时已经是红的**（★ `CharacterLibraryPanel.tsx:632`
⟹ ⟹ ⟹ ⟹ ⇒ 「生成其他年龄版本」是**死按钮** ⟹ ⟹ ⟹ ⟹ ⇒ 而那条死按钮是
⟹ ⟹ ⟹ ⟹ ⇒ ★ **batch 840** 引入的）⟹ ⟹ ⟹ ⟹ ⇒ ★ **红的从来没人看见**。

## ★ 放宽后的口径

★ 门禁「碰了被跟踪源文件」⟹ ⟹ 满足**任一**：
  ① 文本里出现**文件名**（366 原口径）
  ② 文本里出现**目录名**（`src/components` / `src/store` / `src/lib`）
  ③ 文本里对 `src` 做了 `rglob` / `glob`（★ **按目录扫描**的典型形状）

## ★ 输出
  raw/new-gates-868.json
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch868-2026-10-01"
RAW = BATCH / "raw"
REGRESS = BATCH.parent / "liblib-canvas-batch867-2026-10-01/probes/regress867.py"

TRACKED_SRC = [
    "src/components/director/DirectorViewport.tsx",
    "src/components/director/DirectorAspectPanel.tsx",
    "src/store/directorStore.ts",
    "src/lib/directorTelemetry.ts",
]
TRACKED_DIRS = ["src/components", "src/store", "src/lib"]


def parse_gates(text: str) -> list[tuple[str, str]]:
    text = re.sub(r'"""[\s\S]*?"""', " ", text)
    text = re.sub(r"#[^\n]*", " ", text)
    m = re.search(r"^GATES\s*=\s*\[(.*?)^\]", text, re.S | re.M)
    if not m:
        return []
    return re.findall(r'\("([^"]+)",\s*"([^"]+)"\)', m.group(1))


def touches(txt: str) -> bool:
    if any(r.split("/")[-1] in txt for r in TRACKED_SRC):
        return True
    if any(d in txt for d in TRACKED_DIRS):
        return True
    return bool(re.search(r"rglob\(|glob\(", txt)) and "src" in txt


def main() -> int:
    reg_text = REGRESS.read_text(encoding="utf-8")
    listed = set(parse_gates(reg_text))
    gates: list[tuple[str, str]] = []
    for p in sorted((ROOT / "scripts").glob("verify-liblib-batch*.py")) + \
            sorted((ROOT / "scripts").glob("verify-liblib-batch*.mjs")):
        mm = re.match(r"verify-liblib-batch(.+)\.(py|mjs)$", p.name)
        if not mm:
            continue
        try:
            txt = p.read_text(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            continue
        if touches(txt):
            gates.append((mm.group(1), mm.group(2)))
    missing = sorted(set(gates) - listed)
    print("碰被跟踪源文件的门禁：%s ／ 其中清单外：%s" % (len(set(gates)), len(missing)))

    # ★ ★★ `.mjs` 门禁**不能直接执行**（★ 没有可执行位）⟹ ⟹ 必须用 `node` 跑
    #   ⟹ ⟹ ★ 第一版直接 `[str(script)]` ⟹ ⟹ ⟹ ⟹ ⇒ `PermissionError` ⟹ ⟹ ⟹ ⟹
    #   ⟹ ⟹ ⟹ ⟹ ⇒ 整轮**崩在第 39 条**⟹ ⟹ ⟹ ⟹ ⇒ ★ 而且因为是**末尾才落盘**
    #   ⟹ ⟹ ⟹ ⟹ ⇒ ★ 前 39 条的读数**全丢**⟹ ⟹ ⟹ ⟹ ⇒ ★ 同型：**落盘要增量**
    NODE = pathlib.Path.home() / ".nvm/versions/node/v24.6.0/bin/node"
    # ★ 断点续跑：★ 上一轮已经跑过的 ⟹ ⟹ 不再重跑
    part = RAW / "new-gates-868.partial.json"
    done: dict[tuple[str, str], dict] = {}
    if part.exists():
        try:
            for r in json.loads(part.read_text(encoding="utf-8")).get("逐条", []):
                done[(str(r["batch"]), str(r["ext"]))] = r
        except Exception:  # noqa: BLE001
            done = {}
    results = []
    for batch, ext in missing:
        key = (batch, ext)
        if key in done:
            results.append(done[key])
            print("%-6s %-4s rc=%-5s %s" % (batch, ext, done[key]["rc"],
                                          "[续跑]"), flush=True)
            continue
        script = ROOT / ("scripts/verify-liblib-batch%s.%s" % (batch, ext))
        cmd = ([str(NODE), str(script)] if ext == "mjs"
               else [sys.executable, str(script)])
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=1800,
                               cwd=str(ROOT))
            rc = r.returncode
            out = (r.stdout or "") + (r.stderr or "")
        except subprocess.TimeoutExpired:
            rc, out = "timeout", ""
        verdict = None
        for ln in out.splitlines():
            if ln.strip().endswith("通过") and "/" in ln:
                verdict = ln.strip().split()[-1]
        if verdict is None:
            tail = [x.strip() for x in out.splitlines() if x.strip()][-3:]
            verdict = ("rc=%s " % rc) + (" ／ ".join(tail))[-160:]
        results.append({"batch": batch, "ext": ext, "rc": rc, "verdict": verdict})
        print("%-6s %-4s rc=%-5s %s" % (batch, ext, rc, verdict[:110]), flush=True)
        # ★ 增量落盘（★ 崩了也不丢前面的读数）
        part.write_text(json.dumps({"逐条": results}, ensure_ascii=False, indent=1),
                        encoding="utf-8")

    red = [r for r in results if r["rc"] not in (0, None)]
    out = {
        "碰被跟踪源文件的门禁数": len(set(gates)),
        "清单外": len(missing),
        "红条数": len(red),
        "红": ["%s.%s" % (r["batch"], r["ext"]) for r in red],
        "逐条": results,
    }
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / "new-gates-868.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n★ 跑完 %s 条 ⟹ ⟹ 红 %s 条" % (len(results), len(red)))
    print("★ 红的：%s" % out["红"])
    print("读数已落盘：%s" % (RAW / "new-gates-868.json"))
    return 0


if __name__ == "__main__":
    sys.exit(main())

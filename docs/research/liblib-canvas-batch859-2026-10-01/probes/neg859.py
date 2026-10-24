#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 859 阴性对照：证明新门禁 `verify-liblib-batch859.py` **真的能红**。

## ★ 为什么要做这个

「门禁全绿」有两种可能：① 产品对、门禁有牙；② 产品错、门禁是空转。
本脚本**故意把源码改坏**，逐条证明新门禁会**对应地**翻红。

## ★ 纪律（沿用 batch 856/857/858 的口径）

① 每个变异都**先断言文件真的被改了**（比对 SHA-256）⟹ ⟹ 不会出现
   「脚本崩了 → 文件没改 → 闸门全绿 → 误判成负控有效」。
② 每次变异后**跑完整门禁**，记录**红了哪一条**⟹ ⟹ 归因只看 FAIL 行。
③ 每个变异后**字节级复原**（SHA-256 必须回到基线）。
④ 收尾再复核一遍全部文件 == 基线哈希。
⑤ 变异**行数中性**（改同一个字符串，不增删行）⟹ ⟹ diff 干净、可审。
⑥ ★ **归因关键字先跑一次变异、读首条红灯的原文，再定**（不按「我以为的落点」写）。

## ★ 本批的九条变异各自对应一条**行为判据**（不是只测字符串）

| 变异 | 改坏什么 | 期望翻红的判据 |
| --- | --- | --- |
| M1 | 面板不撑满（去掉 `h-full`） | `panel:panorama-rect`（高度 1028） |
| M2 | 行字号 13px→12px | `panel:panorama-row-*`（字号） |
| M3 | 「AI生成」→「AI 生成」 | `panel:panorama-row-AI生成`（逐字文本） |
| M4 | 网格 gap 8px→0 | `panel:aspect-grid`（列间距） |
| M5 | 格子高 72px→64px | `panel:aspect-cell-*`（高度） |
| M6 | 选中边框 0.85→0.1 | `panel:aspect-cell-自适应`（选中态描边） |
| M7 | rail 选中态脱钩 | `panel:rail-entry-is-pressed` |
| M8 | 画幅面板常驻（两面板同时在 DOM） | `panel:only-one-mode-in-dom`（模式互斥） |
| M9 | 旧浮层属性复活 | `panel:old-flyouts-are-gone` |

## ★ 输出
  docs/research/liblib-canvas-batch859-2026-10-01/negative-audit.json
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch859-2026-10-01"
GATE = ROOT / "scripts/verify-liblib-batch859.py"

PANO = ROOT / "src/components/director/DirectorPanoramaPanel.tsx"
ASP = ROOT / "src/components/director/DirectorAspectPanel.tsx"
RAIL = ROOT / "src/components/director/DirectorIconRail.tsx"
DESK = ROOT / "src/components/director/DirectorDesk.tsx"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run_gate() -> tuple[int, list[str]]:
    """跑门禁 ⟹ ⟹ 返回 (退出码, 失败判据名列表)。"""
    proc = subprocess.run([sys.executable, str(GATE)], cwd=ROOT,
                          capture_output=True, text=True, timeout=1800)
    failed = [ln.split(":", 1)[1].strip()
              for ln in proc.stdout.splitlines() if ln.startswith("  FAILED: ")]
    return proc.returncode, failed


def apply(path: Path, old: str, new: str, expect_count: int = 1) -> None:
    t = path.read_text(encoding="utf-8")
    if t.count(old) != expect_count:
        raise SystemExit(
            f"[变异] 锚点出现 {t.count(old)} 次，期望 {expect_count} 次：{old!r}")
    if old.count("\n") != new.count("\n"):
        raise SystemExit(f"[变异] 不是行数中性：{old!r} → {new!r}")
    path.write_text(t.replace(old, new), encoding="utf-8")


# ★ 每个变异：(名字, 文件, 锚点, 替换, 期望翻红的判据, 锚点期望出现次数)
MUTATIONS = [
    ("M1-全景图面板不撑满（去掉 h-full）",
     PANO,
     'className="flex h-full min-h-0 w-full flex-col bg-[#171717]"',
     'className="flex min-h-0 w-full flex-col bg-[#171717]"',
     ["panel:panorama-rect"], 1),
    ("M2-全景图行字号 13px 改 12px",
     PANO,
     'text-left text-[13px] leading-5',
     'text-left text-[12px] leading-5',
     ["source:panorama-row-class-is-the-source-eu",
      "panel:panorama-row-本地上传",
      "panel:panorama-row-历史记录",
      "panel:panorama-row-AI生成"], 1),
    ("M3-「AI生成」改成「AI 生成」（多一个空格）",
     PANO,
     '{ id: "ai-generate", label: "AI生成", icon: Sparkles },',
     '{ id: "ai-generate", label: "AI 生成", icon: Sparkles },',
     ["panel:panorama-row-AI生成"], 1),
    ("M4-画幅网格列间距 8px 改 0",
     ASP,
     'const GRID_CLASS = "grid grid-cols-2 gap-2 px-2 pb-3";',
     'const GRID_CLASS = "grid grid-cols-2 gap-0 px-2 pb-3";',
     ["source:aspect-grid-class-is-the-source-grid",
      "panel:aspect-grid"], 1),
    ("M5-画幅格子高 72px 改 64px",
     ASP,
     # ★ 锚点带**行尾分号** ⟹ ⟹ 只命中 `const CELL_CLASS = …;` 那一行，
     #   不会命中文件头注释里逐字抄的那份（★ 首次锚点自检命中 2 次）。
     '"hover:bg-white/8 flex h-[72px] flex-col items-center justify-center '
     'gap-2 rounded-xl border text-[12px] text-white/90 transition-colors '
     'disabled:cursor-not-allowed disabled:opacity-35";',
     '"hover:bg-white/8 flex h-[64px] flex-col items-center justify-center '
     'gap-2 rounded-xl border text-[12px] text-white/90 transition-colors '
     'disabled:cursor-not-allowed disabled:opacity-35";',
     ["source:aspect-cell-class-is-the-source-cell",
      "panel:aspect-cell-自适应",
      "panel:aspect-cell-21:9"], 1),
    ("M6-画幅选中态描边 0.85 改 0.1",
     ASP,
     'aspectRatio === ratio ? "border-white/85" : "border-white/10",',
     'aspectRatio === ratio ? "border-white/10" : "border-white/10",',
     ["panel:aspect-cell-自适应"], 1),
    ("M7-rail 选中态与面板模式脱钩",
     RAIL,
     '    if (id === "panorama") return panelView === "panorama";',
     '    if (id === "panorama") return false;',
     ["panel:rail-entry-is-pressed"], 1),
    ("M8-画幅面板常驻（两个模式面板同时在 DOM）",
     DESK,
     '<DirectorAspectPanel active={leftPanelView === "aspect"} />',
     '<DirectorAspectPanel active />',
     ["panel:only-one-mode-in-dom"], 1),
    ("M9-旧浮层属性复活（面板改回 flyout 属性名）",
     PANO,
     '      data-director-panorama-panel',
     '      data-director-panorama-flyout',
     ["panel:old-flyouts-are-gone"], 1),
]


def main() -> int:
    audit: dict[str, object] = {
        "batch": 859,
        "title": "阴性对照：改坏源码 ⟹ 新门禁必须对应翻红",
        "mutations": [],
    }
    files = [PANO, ASP, RAIL, DESK]
    baseline = {p: sha(p) for p in files}
    backup_dir = Path(tempfile.mkdtemp(prefix="b859neg-"))
    for p in files:
        shutil.copy2(p, backup_dir / p.name)
    try:
        # ── 基线：先确认门禁本身是绿的 ⟹ ⟹ 之后的红只能是变异造成的 ──
        base_code, base_failed = run_gate()
        audit["baseline"] = {"exit": base_code, "failed": base_failed}
        print(f"[基线] gate exit={base_code} 红条={len(base_failed)}")
        if base_code != 0:
            print("★ 基线就不绿 ⟹ 阴性对照无意义，先修门禁")
            return 1

        for item in MUTATIONS:
            name, path, old, new, expect = item[:5]
            expect_count = item[5] if len(item) > 5 else 1
            before_len = path.stat().st_size
            before_sha = sha(path)
            apply(path, old, new, expect_count)
            after_sha = sha(path)
            # ★ 断言「文件真的被改了」⟹ ⟹ 防止「变异没生效 ⟹ 闸门全绿 ⟹ 误判」
            if after_sha == before_sha:
                audit["mutations"].append({"name": name, "ok": False,
                                           "why": "变异后哈希没变（变异没生效）"})
                print(f"[{name}] 变异后哈希没变 ⟹ 负控无效")
                shutil.copy2(backup_dir / path.name, path)
                continue
            # ★ 给 dev server 一点时间感知到源码变化（HMR 触发的重编译）
            time.sleep(1.0)
            code, failed = run_gate()
            hit = [f for f in failed if any(exp in f for exp in expect)]
            ok = code != 0 and bool(hit)
            audit["mutations"].append({
                "name": name, "file": path.name,
                "bytesBefore": before_len, "bytesAfter": path.stat().st_size,
                "gateExit": code, "failedChecks": failed,
                "expectedToFail": expect, "hit": hit, "ok": ok,
                "firstRed": failed[0] if failed else None,
            })
            print(f"[{name}] gate exit={code} 命中={hit} "
                  f"({'OK' if ok else '★ 负控无效'})")
            # ★ 字节级复原
            shutil.copy2(backup_dir / path.name, path)
            if sha(path) != baseline[path]:
                raise SystemExit(f"[{name}] 复原后哈希对不上 ⟹ 文件被改坏了")
        # ── 收尾：全部文件必须 == 基线 ──
        final = {p.name: sha(p) for p in files}
        expect_map = {p.name: baseline[p] for p in files}
        audit["restored"] = final == expect_map
        print(f"复原自检：{final == expect_map}")
        for p in files:
            if sha(p) != baseline[p]:
                raise SystemExit(f"收尾自检失败：{p}")
    finally:
        shutil.rmtree(backup_dir, ignore_errors=True)

    BATCH.mkdir(parents=True, exist_ok=True)
    (BATCH / "negative-audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
    ok = all(m.get("ok") for m in audit["mutations"]) and audit["restored"]
    print(f"\n{sum(1 for m in audit['mutations'] if m.get('ok'))}/"
          f"{len(audit['mutations'])} 条负控有效；复原自检={audit['restored']}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

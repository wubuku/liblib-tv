#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 858 阴性对照：证明新门禁**真的能红**。

## ★ 为什么要做这个

「门禁全绿」有两种可能：① 产品对、门禁有牙；② 产品错、门禁是空转。
本脚本**故意把源码改坏**，逐条证明新门禁会**对应地翻红**。

## ★ 纪律（沿用 batch 856/857 的口径）

① 每个变异都**先断言文件真的被改了**（比对 SHA-256 ＋ 长度）⟹ ⟹
   不会出现「脚本崩了 → 文件没改 → 闸门全绿 → 误判成负控有效」。
② 每次变异后**跑完整门禁**，记录**红了哪几条**⟹ ⟹ 归因只看 FAIL 行。
③ 每个变异后**字节级复原**（SHA-256 必须回到基线）。
④ 收尾再复核一遍全部文件 == 基线哈希。
⑤ 变异**行数中性**（改同一个字符串，不增删行）⟹ ⟹ diff 干净、可审。

## 输出
  docs/research/liblib-canvas-batch858-2026-10-01/negative-audit.json
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch858-2026-10-01"
GATE = ROOT / "scripts/verify-liblib-batch858.py"

PANEL = ROOT / "src/components/director/DirectorCharacterPanel.tsx"
DESK = ROOT / "src/components/director/DirectorDesk.tsx"
RAIL = ROOT / "src/components/director/DirectorIconRail.tsx"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run_gate() -> tuple[int, list[str]]:
    """跑门禁 ⟹ ⟹ 返回 (退出码, 失败判据名列表)。"""
    proc = subprocess.run([sys.executable, str(GATE)], cwd=ROOT,
                          capture_output=True, text=True, timeout=900)
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


# ★ 每个变异：名字、文件、锚点、替换、期望翻红的判据（子串）
# 每项： (名字, 文件, 锚点, 替换, 期望翻红的判据, 锚点期望出现次数)
MUTATIONS = [
    # ── N1：把「互斥」拆掉（面板与场景树同时存在）⟹ D1 的根因回来 ──
    ("N1-面板与场景树不再互斥",
     DESK,
     '        {leftPanelView === "scene" ? <DirectorObjectTree /> : null}',
     '        {leftPanelView === "scene" || leftPanelView === "character" '
     '? <DirectorObjectTree /> : null}',
     ["panel:scene-tree-is-gone-mutually-exclusive"], 1),
    # ── N2：crowd 按钮的行高被改（32 → 40）⟹ 落点与对话框位置全偏 ──
    ("N2-行高被改（h-8→h-10）",
     PANEL,
     'const ROW_CLASS =\n'
     '  "flex h-8 w-full items-center gap-2 rounded-lg px-2 text-left text-[13px] '
     'leading-5 text-white/88 transition-colors hover:bg-white/8 disabled:cursor-not-allowed '
     'disabled:opacity-45";',
     'const ROW_CLASS =\n'
     '  "flex h-10 w-full items-center gap-2 rounded-lg px-2 text-left text-[13px] '
     'leading-5 text-white/88 transition-colors hover:bg-white/8 disabled:cursor-not-allowed '
     'disabled:opacity-45";',
     ["panel:row-geometry-32px-13px-at-x-56-w-216",
      "panel:row-ys-match-the-source-measurement",
      "crowd:button-is-at-the-source-measured-rect"]),
    # ── N3：去掉 leading-[1.55] 补偿 ⟹ 对话框高 203（源站 204） ──
    ("N3-去掉行高补偿（对话框矮 1px）",
     PANEL,
     'text-[11px] leading-[1.55] text-white/55',
     'text-[11px] text-white/55',
     ["crowd:dialog-is-at-the-source-measured-rect",
      "crowd:dialog-internal-segments-match-the-source"], 3),
    # ── N4：crowd 行不再声明 aria-haspopup=dialog ──
    ("N4-crowd 行去掉 aria-haspopup",
     PANEL,
     'aria-haspopup={item.id === "crowd-3x3" ? "dialog" : undefined}',
     'aria-haspopup={undefined}',
     ["panel:crowd-row-has-aria-haspopup-dialog"], 1),
    # ── N5：几何就地展开改成绝对定位浮层（回到旧模型）──
    ("N5-几何改成绝对定位浮层",
     PANEL,
     'className="border-white/8 ml-3 border-l pl-1"',
     'className="border-white/8 absolute left-3 top-0 w-[204px]"',
     ["geometry:expands-in-place-at-the-source-measured-rect",
      "geometry:is-inside-the-panel-not-a-portal"]),
    # ── N6：rail 选中态不再跟随面板模式（回到旧的两份真相）──
    ("N6-rail 选中态与面板模式脱钩",
     RAIL,
     '    if (id === "add-character") return panelView === "character";',
     '    if (id === "add-character") return false;',
     ["panel:rail-add-character-is-pressed"], 1),
    # ── N7：几何与 crowd 不再共用一个状态 ──
    ("N7-几何与 crowd 不再互斥",
     PANEL,
     '    if (itemId === "geometry") {\n'
     '      // ★ 源站逐字：`O(e => "geometry"===e ? null : "geometry")`\n'
     '      setSubmenu((current) => (current === "geometry" ? null : "geometry"));',
     '    if (itemId === "geometry") {\n'
     '      // ★ 源站逐字：`O(e => "geometry"===e ? null : "geometry")`\n'
     '      setSubmenu((current) => (current === "geometry" ? null : "crowd"));',
     # ★ 归因关键字**先跑一次变异、读首条红灯的原文再定**（别按「我以为的
     #   落点」写）：
     #   把几何那一项改成「切到 crowd」 ⟹ ⟹ 几何**根本不再展开** ⟹ ⟹
     #   首条红灯落在「几何就地展开」那条 ⟹ ⟹ **不是**「crowd 关掉了几何」那条。
     ["geometry:expands-in-place-at-the-source-measured-rect",
      "geometry:eight-items-199x32"], 1),
]


def main() -> int:
    audit: dict[str, object] = {
        "batch": 858,
        "title": "阴性对照：改坏源码 ⟹ 新门禁必须对应翻红",
        "mutations": [],
    }
    files = [PANEL, DESK, RAIL]
    baseline = {p: sha(p) for p in files}
    backup_dir = Path(tempfile.mkdtemp(prefix="b858neg-"))
    for p in files:
        shutil.copy2(p, backup_dir / p.name)
    try:
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
                continue
            code, failed = run_gate()
            hit = [f for f in failed
                   if any(exp in f for exp in expect)]
            ok = code != 0 and bool(hit)
            audit["mutations"].append({
                "name": name, "file": path.name,
                "bytesBefore": before_len, "bytesAfter": path.stat().st_size,
                "gateExit": code, "failedChecks": failed,
                "expectedToFail": expect, "hit": hit, "ok": ok,
            })
            print(f"[{name}] gate exit={code} 命中={hit} "
                  f"({'OK' if ok else '★ 负控无效'})")
            # ★ 字节级复原
            shutil.copy2(backup_dir / path.name, path)
            if sha(path) != baseline[path]:
                raise SystemExit(f"[{name}] 复原后哈希对不上 ⟹ 文件被改坏了")
        # ── 收尾：全部文件必须 == 基线 ──
        final = {p.name: sha(p) for p in files}
        expect = {p.name: baseline[p] for p in files}
        audit["restored"] = final == expect
        print(f"复原自检：{final == expect}")
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

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 860 阴性对照：证明新门禁 `verify-liblib-batch860.py` **真的能红**。

## ★ 为什么要做这个

「门禁全绿」有两种可能：① 产品对、门禁有牙；② 产品错、门禁是空转。
本脚本**故意把源码改坏**，逐条证明新门禁会**对应地**翻红。

## ★ 纪律（沿用 856/857/858/859 的口径）

① 每个变异都**先断言文件真的被改了**（比对 SHA-256）⟹ ⟹ 不会出现
   「脚本崩了 → 文件没改 → 闸门全绿 → 误判成负控有效」。
② 每次变异后**跑完整门禁**，记录**红了哪一条**⟹ ⟹ 归因只看 FAIL 行。
③ 每个变异后**字节级复原**（SHA-256 必须回到基线）。
④ 收尾再复核一遍全部文件 == 基线哈希。
⑤ 变异**行数中性**（改同一个字符串，不增删行）。
⑥ ★ 变异后要**给 dev server 一点时间**感知源码变化（HMR 重编译）。

## ★ 本批的变异各自对应哪条判据

| 变异 | 改坏什么 | 期望翻红的判据 |
|---|---|---|
| N1 | 面板退回组件内 `useState`（不接 store） | `source:panel-writes-to-the-store` ＋ `panel:frame-ratio-for-*` |
| N2 | `getDirectorFrameRect` 忽略 `null`（自适应也画框） | `source:frame-rect-accepts-a-null-ratio` ＋ `panel:auto-has-no-framing-box` |
| N3 | 比例值算错（21:9 写成 16:9） | `source:frame-aspect-values-are-numeric` ＋ `panel:frame-ratio-for-21:9` |
| N4 | 少了 21:9 这一档 | `source:frame-aspect-covers-the-six-source-ratios` |
| N5 | 框不居中（left 写死） | `panel:frame-is-horizontally-centred-for-*` ＋ `panel:all-frames-share-one-centre` |
| N6 | 框不内切（左右边距不等） | `panel:frame-insets-the-available-area-for-*` |
| N7 | 面板的选中态标记反了 | `panel:selection-is-on-*` |
| N8 | 取景框的 `data-director-aspect-ratio` 标记写错 | `panel:frame-marks-*` |
| N9 | store 里没有 `frameAspectRatio` 状态 | `source:store-has-a-separate-frame-aspect-state` ＋ 运行时那几条 |

## ★ 输出
  docs/research/liblib-canvas-batch860-2026-10-01/negative-audit.json
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
BATCH = ROOT / "docs/research/liblib-canvas-batch860-2026-10-01"
GATE = ROOT / "scripts/verify-liblib-batch860.py"

STORE = ROOT / "src/store/directorStore.ts"
MATH = ROOT / "src/components/director/directorViewportMath.ts"
PANEL = ROOT / "src/components/director/DirectorAspectPanel.tsx"
VIEW = ROOT / "src/components/director/DirectorViewport.tsx"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run_gate() -> tuple[int, list[str]]:
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


MUTATIONS = [
    ("N1-面板不接 store（读不到也写不进）",
     PANEL,
     # ★ 行数中性 ⟹ ⟹ 替换成**同样两行**：
     #   读的是**不存在的状态字段**、写的是**空函数**
     #   ⟹ ⟹ 面板彻底与 store 脱钩 ⟹ ⟹ 点哪档都不生效
     #   （★ 不引入 `useState` ⟹ ⟹ 免掉「忘了 import」这个坑）
     '  const frameAspectRatio = useDirectorStore((state) => state.frameAspectRatio);\n'
     '  const setFrameAspectRatio = useDirectorStore((state) => state.setFrameAspectRatio);',
     '  const frameAspectRatio = useDirectorStore((state) => state.frameAspectRatioX);\n'
     '  const setFrameAspectRatio = useDirectorStore((state) => state.setFrameAspectRatioX);',
     ["source:panel-writes-to-the-store",
      "panel:frame-ratio-for-21:9",
      "panel:selection-is-on-21:9"], 1),

    ("N2-自适应也画框（忽略 null）",
     MATH,
     '  if (ratio === null || !Number.isFinite(ratio) || ratio <= 0) return null;',
     '  if (!Number.isFinite(ratio as number) || (ratio as number) <= 0) return null;',
     ["source:frame-rect-accepts-a-null-ratio",
      "panel:auto-has-no-framing-box"], 1),

    ("N3-21:9 的比例值算错",
     STORE,
     '  "21:9": 21 / 9,',
     '  "21:9": 16 / 9,',
     ["source:frame-aspect-values-are-numeric",
      "panel:frame-ratio-for-21:9"], 1),

    ("N4-类型里少了 21:9 这一档",
     STORE,
     # ★ 行数中性 ⟹ ⟹ **不删那一行**，只把里面的档名换掉
     #   （`"21:9"` → `"20:9"`）⟹ ⟹ 类型里就没有 21:9 了。
     '  | "21:9"',
     '  | "20:9"',
     ["source:frame-aspect-covers-the-six-source-ratios"], 1),

    ("N5-框不居中（left 写死 0）",
     MATH,
     '    left: (viewportWidth - width) / 2,',
     '    left: 0,',
     ["panel:frame-is-horizontally-centred-for-",
      "panel:all-frames-share-one-centre"], 1),

    ("N6-框不内切（左右边距不等）",
     MATH,
     '    left: (viewportWidth - width) / 2,\n'
     '    top: topPadding + (availableHeight - height) / 2,',
     '    left: (viewportWidth - width) / 2 + 7,\n'
     '    top: topPadding + (availableHeight - height) / 2,',
     ["panel:frame-insets-the-available-area-for-",
      "panel:all-frames-share-one-centre"], 1),

    ("N7-面板选中态标记反了",
     PANEL,
     '            aria-pressed={selected === ratio}',
     '            aria-pressed={selected !== ratio}',
     ["panel:selection-is-on-"], 1),

    ("N8-取景框的比例标记写错",
     VIEW,
     # ★ ⚠ 第一版改的是 `?? "auto"`（**自适应**那一支）⟹ ⟹ 但自适应时
     #   **框不在场** ⟹ ⟹ 那个标记压根不出现 ⟹ ⟹ **测不到任何东西**
     #   （★ 负控无效 ⟹ ⟹ 根因是「判据漏了一个分支」，已补 `panel:auto-has-no-frame-mark`）。
     #   ⇒ 改成改**有框时**的标记（`frameAspectRatio` 那一支）⟹ ⟹ 真能被抓到。
     '      data-director-aspect-ratio={frameAspectRatio ?? "auto"}',
     '      data-director-aspect-ratio={(frameAspectRatio ?? "auto") + "x"}',
     ["panel:frame-marks-"], 1),

    ("N9-store 的取景比例初始值不是自适应",
     STORE,
     # ★ ⚠ 第一版改的是 **TS 接口里的字段名** ⟹ ⟹ TS 类型**不参与运行时**
     #   ⟹ ⟹ 运行时对象键没变 ⟹ ⟹ 行为完全没变 ⟹ ⟹ 门禁绿是**正确的**
     #   ⟹ ⟹ 但那条变异**测不到任何东西**（负控无效）。
     #   ⇒ 改成改**运行时初始值**（`null` → `"16:9"`）⟹ ⟹ 真的会让框一开场就出现。
     '  frameAspectRatio: null,',
     '  frameAspectRatio: "16:9",',
     ["source:frame-aspect-initial-state-is-auto",
      "panel:auto-has-no-framing-box"], 1),
]


def main() -> int:
    audit: dict[str, object] = {
        "batch": 860,
        "title": "阴性对照：改坏源码 ⟹ 新门禁必须对应翻红",
        "mutations": [],
    }
    files = [STORE, MATH, PANEL, VIEW]
    baseline = {p: sha(p) for p in files}
    backup_dir = Path(tempfile.mkdtemp(prefix="b860neg-"))
    for p in files:
        shutil.copy2(p, backup_dir / p.name)
    try:
        base_code, base_failed = run_gate()
        audit["baseline"] = {"exit": base_code, "failed": base_failed}
        print(f"[基线] gate exit={base_code} 红条={len(base_failed)}", flush=True)
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
            if after_sha == before_sha:
                audit["mutations"].append({"name": name, "ok": False,
                                           "why": "变异后哈希没变（变异没生效）"})
                print(f"[{name}] 变异后哈希没变 ⟹ 负控无效")
                shutil.copy2(backup_dir / path.name, path)
                continue
            # ★ 给 dev server 一点时间感知源码变化
            time.sleep(1.2)
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
                  f"({'OK' if ok else '★ 负控无效'})", flush=True)
            shutil.copy2(backup_dir / path.name, path)
            if sha(path) != baseline[path]:
                raise SystemExit(f"[{name}] 复原后哈希对不上 ⟹ 文件被改坏了")
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

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 861 阴性对照：证明新门禁 `verify-liblib-batch861.py` **真的能红**。

## ★ 为什么要做这个

「门禁全绿」有两种可能：① 产品对、门禁有牙；② 产品错、门禁是空转。
本脚本**故意把源码改坏**，逐条证明新门禁会**对应地**翻红。

## ★ 纪律（沿用 856/857/858/859/860 的口径）

① 每个变异都**先断言文件真的被改了**（比对 SHA-256）⟹ ⟹ 不会出现
   「脚本崩了 → 文件没改 → 闸门全绿 → 误判成负控有效」；
② 每次变异后**跑完整门禁**，记录**红了哪一条**⟹ ⟹ 归因只看 FAIL 行；
③ 每个变异后**字节级复原**（SHA-256 必须回到基线）；
④ 收尾再复核一遍全部文件 == 基线哈希；
⑤ 变异**行数中性**（改同一个字符串，不增删行）；
⑥ ★ 变异后给 dev server 时间感知源码变化（Next 重新编译）。

## ★ 本批的变异各自对应哪条判据

| 变异 | 改坏什么 | 期望翻红的判据 |
|---|---|---|
| N1 | 三行的 onClick 分派失效（点了没反应） | `source:every-row-has-an-onclick` ＋ 三条 clone 行为判据 |
| N2 | 不触发隐藏 file input | `source:panel-clicks-the-file-input` ＋ `clone:local-upload-opens-a-file-chooser` |
| N3 | file input 的 accept 改成 video/* | `source:panel-has-a-hidden-file-input` ＋ `clone:there-is-a-hidden-image-file-input` |
| N4 | 选择器里删掉「生成」入口 | `source:the-picker-has-the-source-actions` |
| N5 | ★ 选择器里偷偷加一个 `fetch`（真实生成） | `source:the-generate-button-makes-no-network-call` |
| N6 | store 里没有 `localPanoramaAsset` | `source:store-has-the-local-panorama-asset` |
| N7 | 虚拟输入的前缀写错 | `source:ingress-merges-the-local-input` |
| N8 | 「当前全景图」不写来源 | `clone:the-current-panorama-becomes-the-local-one` |

## ★ 输出
  docs/research/liblib-canvas-batch861-2026-10-01/negative-audit.json
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
BATCH = ROOT / "docs/research/liblib-canvas-batch861-2026-10-01"
GATE = ROOT / "scripts/verify-liblib-batch861.py"

PANEL = ROOT / "src/components/director/DirectorPanoramaPanel.tsx"
PICKER = ROOT / "src/components/director/DirectorPanoramaPicker.tsx"
STORE = ROOT / "src/store/directorStore.ts"
INGRESS = ROOT / "src/lib/directorCanvasMediaIngress.ts"


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
    ("N1-三行的 onClick 分派失效（点了没反应）",
     PANEL,
     '                if (item.id === "local-upload") {',
     '                if (item.id === "local-upload-x") {',
     ["source:every-row-has-an-onclick",
      "clone:local-upload-opens-a-file-chooser",
      "clone:history-opens-the-picker",
      "clone:ai-generate-opens-the-picker"], 1),

    ("N2-不触发隐藏的 file input",
     PANEL,
     '    fileInputRef.current?.click();',
     '    void fileInputRef;',
     ["source:panel-clicks-the-file-input",
      "clone:local-upload-opens-a-file-chooser"], 1),

    ("N3-file input 的 accept 改成 video/*",
     PANEL,
     '          accept="image/*"',
     '          accept="video/*"',
     ["source:panel-has-a-hidden-file-input",
      "clone:there-is-a-hidden-image-file-input"], 1),

    ("N4-选择器里没有「生成」入口",
     PICKER,
     '                data-director-panorama-generate\n',
     '                data-director-panorama-generateX\n',
     ["source:the-picker-has-the-source-actions",
      "clone:the-ai-picker-adds-generate-and-upload"], 1),

    ("N5-★ 选择器里偷偷加一个 fetch（真实生成）",
     PICKER,
     '  const [selectedId, setSelectedId] = useState<string | null>(null);',
     '  const [selectedId, setSelectedId] = useState<string | null>(null); void fetch("/api/panorama/generate");',
     ["source:the-generate-button-makes-no-network-call"], 1),

    ("N6-store 里没有 localPanoramaAsset",
     STORE,
     '  localPanoramaAsset: DirectorLocalPanoramaAsset | null;\n',
     '  localPanoramaAssetX: DirectorLocalPanoramaAsset | null;\n',
     ["source:store-has-the-local-panorama-asset"], 1),

    ("N7-虚拟输入的前缀写错",
     INGRESS,
     'export const DIRECTOR_LOCAL_PANORAMA_SOURCE_PREFIX = "local-panorama:";',
     'export const DIRECTOR_LOCAL_PANORAMA_SOURCE_PREFIX = "local-pano2:";',
     ["source:ingress-merges-the-local-input"], 1),

    ("N8-「当前全景图」不写来源",
     PANEL,
     '        data-director-panorama-current-source={currentPanoramaSourceId ?? ""}',
     '        data-director-panorama-current-source=""',
     ["clone:the-current-panorama-becomes-the-local-one"], 1),
]


def main() -> int:
    audit: dict[str, object] = {
        "batch": 861,
        "title": "阴性对照：改坏源码 ⟹ 新门禁必须对应翻红",
        "mutations": [],
    }
    files = [PANEL, PICKER, STORE, INGRESS]
    baseline = {p: sha(p) for p in files}
    backup_dir = Path(tempfile.mkdtemp(prefix="b861neg-"))
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
            # ★ 给 dev server 时间感知源码变化（Next 会重新编译）
            time.sleep(2.5)
            code, failed = run_gate()
            hit = sorted({f for f in failed if any(exp in f for exp in expect)})
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
                raise SystemExit(f"★ 收尾复核失败：{p} 的哈希对不上基线")
    finally:
        for p in files:
            shutil.copy2(backup_dir / p.name, p)

    ok = all(m.get("ok") for m in audit["mutations"]) and audit["restored"]
    audit["ok"] = ok
    (BATCH / "negative-audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"== 阴性：{len(audit['mutations'])} 条负控有效；"
          f"复原自检={audit['restored']} ==")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

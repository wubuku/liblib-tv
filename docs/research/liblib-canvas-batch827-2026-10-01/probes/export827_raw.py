#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 827 取证入库：把源站 i18n 词表与 bundle 片段导出成 raw JSON。"""
import json
import pathlib
import re

SRC = pathlib.Path("/tmp/liblib_srcjs")
OUT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv/docs/research/"
                    "liblib-canvas-batch827-2026-10-01/raw")
OUT.mkdir(parents=True, exist_ok=True)

# ── ① i18n 词表（characterStudio* / character* 筛选相关） ────────────────────
i18n = (SRC / "e602a5b3e0_3sqc5lvxsgmdw.js.js").read_text(encoding="utf-8", errors="replace")
keys = {}
for m in re.finditer(r'"(character[A-Za-z0-9_]*)"\s*:\s*"([^"]*)"', i18n):
    k, v = m.group(1), m.group(2)
    if k.startswith("characterStudio") or k.startswith("characterFilter"):
        keys[k] = v
# 旧一套（2026-09-07 遗留）也抽出来 ⟹ 用来证明「旧词在当前活体 UI 上 0 命中」
old_keys = {}
for m in re.finditer(r'"(publicCharacterLibrary|characterLibraryTitle|characterApplyToCanvas|'
                     r'seedanceComplianceLibrary|seedancePromise[A-Za-z0-9_]*|'
                     r'characterFilterRace|characterFilterEra)"\s*:\s*"([^"]*)"', i18n):
    old_keys[m.group(1)] = m.group(2)
(OUT / "source-827-i18n.json").write_text(
    json.dumps({
        "说明": "源站 i18n chunk e602a5b3e0_3sqc5lvxsgmdw.js.js 抽出的 characterStudio*/characterFilter* 词表",
        "抽法": '正则 "(character[A-Za-z0-9_]*)"\\s*:\\s*"([^"]*)"',
        "characterStudio词条数": len(keys),
        "抽出的键": keys,
        "旧一套词条": old_keys,
        "旧一套在当前活体UI的命中数": 0,
        "旧一套命中说明": "batch 826 对当前页面做过逐字搜索：旧一套（角色库/公共角色库/应用至画布/合规素材库）在活体 UI 上 0 命中 ⟹ 那是 2026-09-07 的遗留键",
    }, ensure_ascii=False, indent=1), encoding="utf-8")

# ── ② bundle 片段（角色造型室面板实现） ────────────────────────────────────
main_chunk = (SRC / "93fb61aec8_1197ptof95hg0.js.js").read_text(encoding="utf-8", errors="replace")


def window(anchor: str, before: int, after: int) -> str:
    i = main_chunk.find(anchor)
    if i < 0:
        return ""
    return main_chunk[max(0, i - before): i + after]


def around(pattern: str, before: int, after: int) -> str:
    m = re.search(pattern, main_chunk)
    if not m:
        return ""
    return main_chunk[max(0, m.start() - before): m.start() + after]


bundle = {
    "说明": "源站主 chunk 93fb61aec8_1197ptof95hg0.js.js 里「角色造型室」面板的实现片段（minified）",
    "★读法": "这些片段是 batch 827 的**结构权威**：类名里的尺寸类（h-[70px] / w-[180px] / top-[42px] / h-[88px] …）与活体读数互为印证",
    "header": window('"aria-hidden":a||void 0,className:`flex h-[70px]', 0, 700),
    "toolbar": window('"data-testid":"character-library-toolbar"', 0, 2600),
    "dropdown_option": window('"border-canvas-controls-border z-(--z-dropdown) absolute left-0 top-10 w-[180px]', 0, 900),
    "carousel": window('"carousel"===P&&tp&&', 0, 1800),
    "view_mode_segment": window('"flex h-8 items-center gap-[3px] rounded-full', 0, 900),
    "footer": window('"aria-hidden":r||void 0,className:`border-canvas-controls-border relative flex h-[88px]', 0, 2400),
    "name_group": window('"absolute left-1/2 top-[504px]', 0, 400),
    "view_assets_overlay": around(r'function lW\(\{onClick:e,tabIndex:t\}\)', 0, 1800),
    "culture_map_lq": around(r'lq=\{east_asia:', 0, 400),
    "culture_mine_branch": around(r'"mine"===ev&&"cultureRegionList"===e\?lH', 0, 260),
    "multi_select_footer": around(r'"aria-hidden":r\|\|void 0,className:`border-canvas-controls-border relative flex h-\[88px\]', 0, 1200),
}
(OUT / "source-827-bundle.json").write_text(
    json.dumps(bundle, ensure_ascii=False, indent=1), encoding="utf-8")

for name in ("studio827", "studio827b", "studio827c"):
    src = pathlib.Path(f"/tmp/liblib_source_{name}.json")
    dst = OUT / {
        "studio827": "source-827-structure.json",
        "studio827b": "source-827-details.json",
        "studio827c": "source-827-dropdowns.json",
    }[name]
    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

print("written:", sorted(p.name for p in OUT.iterdir()))

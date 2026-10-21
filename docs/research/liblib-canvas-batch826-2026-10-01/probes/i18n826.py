#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从源站 i18n chunk 里抽出**新旧两套**角色相关键，入库为 raw 证据。

★ 目的：证明「公共角色库 / 角色库」在源站**当前**构建里只是**遗留的 i18n 键**，
  而「角色造型室 / 我的角色库 / 官方角色库」是**当前**在用的那一套。
"""
import json
import pathlib
import re

I18N = pathlib.Path("/tmp/liblib_srcjs/e602a5b3e0_3sqc5lvxsgmdw.js.js")
OUT = pathlib.Path("/tmp/source826_i18n.json")

WANTED = [
    "characterLibraryTitle",
    "characterStudioTitle",
    "characterStudioLibraryTitle",
    "characterStudioLibraryDescription",
    "characterStudioMyLibrary",
    "characterStudioOfficialLibrary",
    "characterStudioMultiSelect",
    "characterStudioExitMultiSelect",
    "characterStudioSearchPlaceholder",
    "characterStudioAddToCanvas",
    "characterStudioViewAssets",
    "characterStudioCreate",
    "characterStudioGenerate",
    "publicCharacterLibrary",
    "seedanceComplianceLibrary",
    "characterApplyToCanvas",
    "characterFilterGender",
    "characterFilterAgeGroup",
    "characterFilterCultureRegion",
    "characterStudioFilterGender",
    "characterStudioFilterAgeGroup",
    "characterStudioFilterCultureRegion",
]

text = I18N.read_text(encoding="utf-8", errors="replace")
found = {}
for k in WANTED:
    m = re.search(r'"%s":"((?:[^"\\]|\\.)*)"' % re.escape(k), text)
    if m:
        found[k] = m.group(1)

# 源站 i18n 里**含「角色库」的其它键**（用于看清有哪些并存的说法）
related = sorted(set(re.findall(r'"([A-Za-z0-9_]*(?:CharacterLibrary|CharacterStudio)[A-Za-z0-9_]*)":"((?:[^"\\]|\\.)*)"', text)))
related_map = {k: v for k, v in related}

out = {
    "i18n_chunk": I18N.name,
    "i18n_chunk_bytes": len(text),
    "抽出的键": found,
    "含 CharacterLibrary/CharacterStudio 的键": related_map,
}
OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(out, ensure_ascii=False, indent=1)[:4000])

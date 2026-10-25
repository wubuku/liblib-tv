#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 869 受控复跑：★ 把「回归读数里的 46 条新红」在**环境修复后**原样再跑一遍。

★ ★★ 为什么需要这一步：★ 那一轮回归跑在 **2026-10-26 01:05** 被人误装出来的
★ `node_modules/node_modules/`（★ 一份 **Sep 29** 的完整依赖树副本）污染期间
★ ⟹ ⟹ ⟹ ⟹ ⇒ Node 的解析链把 `three` 解析到了**第二份** ⟹ ⟹ ⟹ ⟹ ⇒ R3F 崩
★ ⟹ ⟹ ⟹ ⟹ ⇒ 导演台只渲染出 2 个按钮 ⟹ ⟹ ⟹ ⟹ ⇒ 于是**浏览器门禁集体超时**
★ ⟹ ⟹ ⟹ ⟹ ⇒ 45 条「新红」全是**环境型假红**。
★ ★★ 判据（★ 归因要靠对照、不能靠猜）：★ **同一批门禁、同一套方法**，
★ 只把环境改回（删掉误装的副本 ＋ 重启 dev server）⟹ ⟹ ⟹ ⟹ ⇒
★ ⟹ ⟹ ⟹ ⟹ 「转绿的那几条」＝环境型假红；★ 「仍然红的」＝ 真问题。
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import sys

BATCH = pathlib.Path(__file__).resolve().parents[1]
REGRESS = BATCH / "probes/regress869.py"
REG_JSON = BATCH / "raw/regression.json"
OUT = BATCH / "raw/newred-rerun-869.json"

spec = importlib.util.spec_from_file_location("regress869", REGRESS)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

verdict = json.loads(REG_JSON.read_text(encoding="utf-8"))["判定"]
new = verdict["新红"]
print("★ 待复跑的新红：%d 条" % len(new))

results = []
for item in new:
    batch, ext = item.split(".")
    res = mod.run(batch, ext)
    results.append(res)
    print("%-8s rc=%-5s %s" % (item, res["rc"], res["verdict"][:110]), flush=True)

still = ["%s.%s" % (r["batch"], r["ext"]) for r in results if r["rc"] != 0]
turned = [item for item in new if item not in still]
OUT.write_text(json.dumps({
    "说明": "★ 同 46 条、同方法，只把环境改回（删误装副本 ＋ 重启 dev server）",
    "逐条读数": results,
    "转绿（判为环境型假红）": turned,
    "仍红（真问题）": still,
    "总数": len(new),
}, ensure_ascii=False, indent=1), encoding="utf-8")
print("★ 转绿 %d 条（环境型假红）；仍红 %d 条" % (len(turned), len(still)))
print("★ 仍红清单：%s" % still)
print("★ 落盘：%s" % OUT)

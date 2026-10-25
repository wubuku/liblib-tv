#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 868 归因分析：★ 把普查读数变成「**哪些是真糊弄**」的判定。

## ★ ★★ 为什么「点了没反应」**不能直接等于**「糊弄」

★ 一个控件点了没反应 ⟹ ⟹ 有**四种**可能 ⟹ ⟹ 必须分开定性：

| # | 可能 | 判据 | 结论 |
| --- | --- | --- | --- |
| ① | 它是**输入控件** ⟹ ⟹ 点它只是**获得焦点** | `tag ∈ {input, textarea, select}` | ★ **正常** |
| ② | 它是**当前已选中**的项 ⟹ ⟹ 重复点它**本来就不该变** | `aria-pressed/aria-selected/aria-current == "true"` | ★ **正常** |
| ③ | **同组兄弟**点了**有强变化** ⟹ ⟹ 它自己没有 ⟹ ⟹ ⇒ 它**坏了** | 同 `group` 里有「点后状态变了」的兄弟 | ★ ★ **真糊弄** |
| ④ | 其它 ⟹ ⟹ **没有阳性对照** ⟹ ⟹ 判不了 | — | ★ **待人工** |

★ ★★ ③ 是**阳性对照**：★ 「它没反应」**必须**跟「它的兄弟有反应」**放在一起**
⟹ ⟹ ⟹ ⟹ ⇒ ★ 才有资格说「它坏了」⟹ ⟹ ⟹ ⟹ ⇒ ★ 单独说「它没反应」**不成立**。

## ★ 输出
  raw/analysis-868.json
"""
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch868-2026-10-01"
RAW = BATCH / "raw"

INPUT_TAGS = {"input", "textarea", "select"}


def classify(rec: dict) -> tuple[str, str]:
    """★ 一条普查记录 ⟹ ⟹ (定性, 依据)。"""
    c = rec["控件"]
    verdict = rec.get("判定")
    if verdict == "有反应":
        return "正常", "点了有反应"
    if verdict == "不可判":
        return "待人工", rec.get("原因", "")
    if verdict == "只变焦点":
        if c["tag"] in INPUT_TAGS:
            return "正常", "★ 输入控件 ⟹ ⟹ 点它只是获得焦点"
        if str(c.get("ariaPressed")) == "true" or str(c.get("ariaSelected")) == "true" \
                or str(c.get("ariaCurrent")) == "true":
            return "正常", "★ 当前已选中的项 ⟹ ⟹ 重复点它本来就不该变"
        sib = rec.get("同组兄弟")
        if sib and sib.get("兄弟判定") == "有反应":
            return "★ 真糊弄", ("★ 同组兄弟「%s」点了有强变化 ⟹ ⟹ 它自己没有 ⟹ ⟹ 它坏了"
                                % sib.get("兄弟"))
        return "待人工", "★ 只变焦点 ⟹ ⟹ 没有阳性对照"
    if verdict == "死":
        sib = rec.get("同组兄弟")
        if sib and sib.get("兄弟判定") == "有反应":
            return "★ 真糊弄", ("★ 同组兄弟「%s」点了有强变化 ⟹ ⟹ 它点了什么也没发生"
                                % sib.get("兄弟"))
        return "待人工", "★ 点了什么也没发生 ⟹ ⟹ 没有阳性对照"
    return "待人工", "★ 未知判定：%s" % verdict


def main() -> int:
    scopes = sys.argv[1:] or ["root", "director"]
    out: dict = {}
    total_fake = 0
    for scope in scopes:
        p = RAW / ("census-868-%s.json" % scope)
        if not p.exists():
            print("★ 缺读数：%s" % p)
            continue
        d = json.loads(p.read_text(encoding="utf-8"))
        if scope not in d:
            continue
        recs = d[scope].get("逐组", [])
        buckets = {"正常": [], "★ 真糊弄": [], "待人工": []}
        for rec in recs:
            verdict, why = classify(rec)
            c = rec["控件"]
            buckets[verdict].append({
                "组": rec.get("组"), "组员数": rec.get("组员数"),
                "tag": c["tag"], "aria": c["aria"], "text": c["text"],
                "data": c["data"], "定位器": c.get("loc"),
                "判定": rec.get("判定"), "依据": why,
                "同组兄弟": rec.get("同组兄弟"),
            })
        out[scope] = {
            "控件数": d[scope].get("控件数"),
            "组数": d[scope].get("组数"),
            "正常": len(buckets["正常"]),
            "真糊弄": len(buckets["★ 真糊弄"]),
            "待人工": len(buckets["待人工"]),
            "真糊弄清单": buckets["★ 真糊弄"],
            "待人工清单": buckets["待人工"],
        }
        total_fake += len(buckets["★ 真糊弄"])
        print("== %s == 控件 %s ／ 组 %s ⟹ ⟹ 正常 %s ／ ★真糊弄 %s ／ 待人工 %s" % (
            scope, out[scope]["控件数"], out[scope]["组数"],
            out[scope]["正常"], out[scope]["真糊弄"], out[scope]["待人工"]))
        for b in buckets["★ 真糊弄"]:
            print("   ★★ 糊弄：%s %s ⟹ ⟹ %s" % (b["tag"], b["aria"] or b["text"], b["依据"]))
        for b in buckets["待人工"]:
            print("   ?  待人工：%s %s ⟹ ⟹ %s" % (b["tag"], b["aria"] or b["text"], b["依据"]))
    out["真糊弄总数"] = total_fake
    (RAW / "analysis-868.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n★ 真糊弄总数：%d" % total_fake)
    print("读数已落盘：%s" % (RAW / "analysis-868.json"))
    return 0


if __name__ == "__main__":
    sys.exit(main())

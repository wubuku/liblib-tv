#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给 batch 830 的**旧读数文件**追加「★读数更正」。

★ 纪律：原始观测**一个字都不改**（那是当时探针看到的），只在文件末尾**追加**
  一段更正 ⟹ 后来人不会把已被推翻的读数当成事实，而原始证据仍在。

★ 本批更正了四处「探针自己的读数/自判」：
  1. `source-830-timeline-zoom.json` 的 `②改缩放.after=null` + `★没调到=true`
     ⟹ 含义是「没**精确命中**手打的目标值 70」，**不是「没改成」**
     （四次点击的回读都是 75，真值见 `③改缩放后.value=75`）。
  2. `source-830-shortcuts.json` 的「撤销 = Z」
     ⟹ 面板上撤销是 **⌘Z**（⌘ 是 SVG 图标，纯文本读数器看不见它）。
  3. `source-830-undo-fov.json` / `source-830-undo-rename.json` 的「按 Z 后不变」
     ⟹ 那两格是**前提不满足**的无效读数（源站撤销要 **⌘Z**，裸 Z 被明确排除）。
"""
import json
import pathlib

BASE = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv/docs/research/"
                    "liblib-canvas-batch830-2026-10-01/raw")

NOTES = {
    "source-830-timeline-zoom.json": {
        "★读数更正": (
            "「②改缩放.after = null」与「★没调到 = true」**不是「没改成」**，"
            "而是「没**精确命中**手打的目标值 70」：四次点击后的回读都是 75"
            "（见 ②改缩放.tries[*].value_after），真值见「③改缩放后.value = 75」。"
            "⟹ 根因是探针用「按手打比例点 71px 宽的轨道」这种**不可精确定位**的办法改值；"
            "精确法（聚焦滑杆后按方向键）见 source-830-undo-cmdz2.json。"
            "★ 本条更正由门禁 S2 钉住（缺了它门禁就红）。"),
        "★更正依据": "batch 830 探针 v9/v10 的精确法读数 + 门禁 S2",
    },
    "source-830-shortcuts.json": {
        "★读数更正": (
            "本文件的 leaves 读数里「撤销」右边只有「Z」，⟹ 看起来是**裸 Z**。"
            "**这是纯文本读数器的盲区**：源站面板上撤销那一行是 "
            "{id:\"undo-command\",icon:\"command\"} + {id:\"undo-key\",label:\"Z\"} ⟹ "
            "**⌘ 是一个 SVG 图标（⌘ 符号），没有文字** ⟹ 文本读数器读不到它。"
            "⟹ ★★ 面板实际写的是「撤销 **⌘Z**」；打组 ⌘G、解组 ⌘⇧D 同理。"
            "⟹ **「撤销 = Z」这条读数作废**，以 source-830-shortcut-code.json 的源码锚点为准。"),
        "★更正依据": "源站导演台组件 chunk 0fmehki05gkzw.js.js 的面板渲染代码",
    },
    "source-830-undo-fov.json": {
        "★读数更正": (
            "「⑧B_按Z后 / ⑪C_重开后按Z 读数不变」⟹ **这两格是前提不满足的无效读数**，"
            "**不能**支持「源站撤不掉 FOV 改动」。"
            "⟹ 源站键盘处理的条件是 `(\"z\"!==n||e.ctrlKey||e.metaKey)` ⟹ "
            "**撤销必须带 ⌘/Ctrl，裸 Z 被明确排除** ⟹ 本文件按的是裸 Z。"
            "⟹ 用 **⌘Z** 重测的读数见 source-830-undo-cmdz.json："
            "FOV 67→45 后按 ⌘Z **退回 67**，按 ⌘⇧Z **重做回 45** ⟹ 源站撤得掉。"),
        "★更正依据": "source-830-shortcut-code.json 的锚点「撤销键条件」+ source-830-undo-cmdz.json",
    },
    "source-830-undo-rename.json": {
        "★读数更正": (
            "「⑤按Z后 / ⑥再按Z后 名字不变」⟹ **这两格是前提不满足的无效读数**。"
            "⟹ 源站撤销要 **⌘Z**（见 source-830-shortcut-code.json 的锚点「撤销键条件」），"
            "本文件按的是裸 Z。"
            "⟹ 用 **⌘Z** 重测的读数见 source-830-undo-cmdz.json："
            "「机位1-830」按 ⌘Z **退回「机位1」**，按 ⌘⇧Z **重做回「机位1-830」**。"),
        "★更正依据": "source-830-shortcut-code.json 的锚点「撤销键条件」+ source-830-undo-cmdz.json",
    },
}


def main():
    for name, note in NOTES.items():
        p = BASE / name
        d = json.loads(p.read_text(encoding="utf-8"))
        d.update(note)
        p.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已加更正：", name)


if __name__ == "__main__":
    main()

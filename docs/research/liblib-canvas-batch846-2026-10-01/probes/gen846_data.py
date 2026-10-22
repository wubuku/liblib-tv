#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 846：从**入库的源站 raw** 机器提取 TSX 里的数据块。

★ 为什么要有这一步：这些清单（19 张卡的图源、35 枚 chip、21 枚色块的颜色）**手抄必错**
  ⟹ ⟹ 机器提取 ⟹ ⟹ 落进 `docs/research/liblib-canvas-batch846-2026-10-01/probes/outfit-data.ts.txt`
  ⟹ ⟹ 再由人贴进 `CharacterEditorPanel.tsx` ⟹ ⟹ 门禁会**逐条**与 raw 比对 ⟹ ⟹ 抄错了会红。

★ 坐标换算：源站的绝对坐标 ⟹ ⟹ **相对滚动区内容起点**（= 段顶 ＋ 标题行 40 ＋ pt-4 16）
  ⟹ ⟹ 也就是 clone 里 `.ce-section` 的 top 坐标（绝对定位子元素的参照系）。
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch846-2026-10-01"
RAW = BATCH / "raw/source-846-outfit.json"
OUT = BATCH / "probes/outfit-data.ts.txt"

# ★★ 段内坐标原点 ＝ **右栏列的左上角**（源站 abs 1273,231）
#   ⟹ ⟹ 标题行 40 ⟹ ⟹ 滚动区顶 = 271 ⟹ ⟹ 内容起点 = 287（pt-4 16）
#   ⟹ ⟹ clone 里 `.ce-section` 的 top/left **就是**相对这个原点的（绝对定位子元素
#      不受 padding 影响 ⟹ ⟹ 故 x 已经是「相对列左」的 24 起）
ORIGIN_Y = 271
ORIGIN_X = 1273


def main() -> int:
    raw = json.loads(RAW.read_text(encoding="utf-8"))["★读数"]
    chips = raw["chip"]
    cards = raw["卡片"]
    h3s = raw["H3"]

    def rel_x(b):
        return b["x"] - ORIGIN_X

    def rel_y(b):
        return b["y"] - ORIGIN_Y

    # ── H3 标题 ──
    lines = []
    lines.append("// ★★ Batch 846：左列第四段「服装造型」的四个小节标题（★ 源站实测）")
    lines.append("const OUTFIT_SECTION_TITLES: { title: string; top: number }[] = [")
    for h in h3s:
        lines.append('  { title: "%s", top: %d },' % (h["text"], rel_y(h["box"])))
    lines.append("];")
    lines.append("")

    # ── chip 行（发型 ＋ 妆容）──
    def chip_block(name, title):
        rows = [c for c in chips
                if c["box"]["w"] in (50, 74) and c["text"]]
        # ★ 按 H3 的归属切分：发型的那批在「发型」标题之下、妆容的那批在「妆容」标题之下
        return rows

    # 发型 chip：y 317..349（第一行 317）
    hair = [c for c in chips if c["text"] and c["box"]["y"] < 400]
    makeup = [c for c in chips if c["text"] and c["box"]["y"] >= 900]

    def emit_chips(var, items, comment):
        lines.append("// %s" % comment)
        lines.append("const %s: { label: string; x: number; y: number; w: number; sel: boolean }[] = ["
                     % var)
        for c in items:
            lines.append('  { label: "%s", x: %d, y: %d, w: %d, sel: %s },'
                         % (c["text"], rel_x(c["box"]), rel_y(c["box"]),
                            c["box"]["w"], "true" if c["选中"] == "true" else "false"))
        lines.append("];")
        lines.append("")

    emit_chips("OUTFIT_HAIR_CHIPS", hair,
               "★★ 发型的 chip 行（★ 7 枚 50×26；**「现代」初始选中** ⟹ 白底黑字）")
    emit_chips("OUTFIT_MAKEUP_CHIPS", makeup,
               "★★ 妆容的 chip 行（★ 7 枚，**宽度随文案变**（「欧美时尚」74 ⟹ 4 个字））")

    # ── 色块（发色 ＋ 口红）──
    def emit_swatches(var, items, comment):
        lines.append("// %s" % comment)
        lines.append("const %s: { color: string; x: number; y: number; sel: boolean; custom: boolean }[] = ["
                     % var)
        for c in items:
            color = c["style"]["backgroundColor"]
            custom = (c["aria"] == "自定义颜色")
            lines.append('  { color: "%s", x: %d, y: %d, sel: %s, custom: %s },'
                         % (color, rel_x(c["box"]), rel_y(c["box"]),
                            "true" if c["选中"] == "true" else "false",
                            "true" if custom else "false"))
        lines.append("];")
        lines.append("")

    hair_colors = [c for c in chips if c["box"]["w"] == 35 and c["box"]["y"] < 1200]
    lip_colors = [c for c in chips if c["box"]["w"] == 35 and c["box"]["y"] >= 1200]
    emit_swatches("OUTFIT_HAIR_COLORS", hair_colors,
                  "★★ 发色的色块（★ 10 枚颜色 ＋ 1 枚「自定义颜色」⟹ 初始选中**第一枚**）")
    emit_swatches("OUTFIT_LIP_COLORS", lip_colors,
                  "★★ 口红的色块（★ 10 枚；★ 「口红」那节**没有**「自定义颜色」）")

    # ── 卡片（发型 12 ＋ 妆容 7）──
    def emit_cards(var, items, comment):
        lines.append("// %s" % comment)
        lines.append("const %s: { label: string; img: string; x: number; y: number }[] = ["
                     % var)
        for c in items:
            lines.append('  { label: "%s", img: "%s", x: %d, y: %d },'
                         % (c["名字"], c["图源"], rel_x(c["卡盒"]), rel_y(c["卡盒"])))
        lines.append("];")
        lines.append("")

    hair_cards = [c for c in cards if c["卡盒"]["y"] < 1000]
    makeup_cards = [c for c in cards if c["卡盒"]["y"] >= 1000]
    emit_cards("OUTFIT_HAIR_CARDS", hair_cards,
               "★★ 发型的卡片（★ 12 张 76×96；★ 图是**引用**源站 CDN 的真实图）")
    emit_cards("OUTFIT_MAKEUP_CARDS", makeup_cards,
               "★★ 妆容的卡片（★ 7 张 76×96；★ 图是**引用**源站 CDN 的真实图）")

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("已写入", OUT, "（%d 行）" % len(lines))
    print("\n".join(lines[:14]))
    return 0


if __name__ == "__main__":
    sys.exit(main())

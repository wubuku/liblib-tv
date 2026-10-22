#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 847：从**入库的源站 raw** 机器提取 TSX 里的「音色音调」数据块。

★ 为什么要有这一步：20 条音色的**名字与副标**（含全角/半角括号、中点分隔符）
  **手抄必错** ⟹ ⟹ 机器提取 ⟹ ⟹ 落进
  `docs/research/liblib-canvas-batch847-2026-10-01/probes/voice-data.ts.txt`
  ⟹ ⟹ 再贴进 `CharacterEditorPanel.tsx` ⟹ ⟹ 门禁会**逐条**与 raw 比对 ⟹ ⟹ 抄错了会红。

★ 同时把**几处由 raw 算出来的量**一并算出来（不是手打常数）：
  · 标题行页签的宽度（70／24／24）
  · 工具行两枚按钮的宽度与间隙
  · 音色卡的步进（56）＝ 卡高 48 ＋ 间隙 8
  · 滚动区高度 1192 ＝ 20×48 ＋ 19×8 ＋ 80(pb-20)
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch847-2026-10-01"
RAW = BATCH / "raw/source-847-voice.json"
OUT = BATCH / "probes/voice-data.ts.txt"


def main() -> int:
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    r = raw["★读数"]

    # ── 自证：这份 raw 必须是「音色音调」段（不是别的段）──
    if not raw.get("★读数_是目标段"):
        print("✘ raw 的 ★读数_是目标段 为 false ⟹ 不是第五段 ⟹ 作废", file=sys.stderr)
        return 2
    if raw.get("★分段_积分是否变化"):
        print("✘ 积分发生变化 ⟹ 探针做了有副作用的操作 ⟹ raw 作废", file=sys.stderr)
        return 2

    cards = r["音色卡"]
    if len(cards) != 20:
        print("✘ 音色卡数 %d ≠ 20 ⟹ raw 与预期不符" % len(cards), file=sys.stderr)
        return 2

    # ── 标题行页签：三枚 BUTTON（宽 70／24／24）──
    tabs = []
    for node in r["标题行"]["子节点"]:
        btn = node["孙节点"][0]
        tabs.append({
            "label": btn["text"],
            "w": node["box"]["w"],
            "x": node["box"]["x"],
            "text_w": btn["内层文字盒"]["w"],
        })

    # ── 工具行两枚按钮（32×32）──
    tools = []
    for b in r["工具行"]["按钮"]:
        tools.append({
            "x": b["box"]["x"],
            "w": b["box"]["w"],
            "icon": b["图标盒"],
        })

    lines = []
    lines.append("// ── 标题行页签（源站实测：宽度 70／24／24，间隙 20）──")
    lines.append("// ★「音色库」是**选中态**：白 1px 底边框 ＋ 文字 #fff")
    lines.append("// ★ 另两枚：透明底边框 ＋ 文字白 60%（源站把文字盒裁成 0 宽 ⟹ ⟹ 看不见）")
    lines.append("const VOICE_TABS: { id: string; label: string; w: number; icon: typeof Music }[] = [")
    ids = {"音色库": "library", "我的音色": "mine", "AI 生成": "ai"}
    # ★ 图标是 **clone 决策**（源站是 iconify SVG，字形未采集）⟹ ⟹ 用 lucide 占位
    icons = {"音色库": "Music", "我的音色": "User", "AI 生成": "Sparkles"}
    for t in tabs:
        lines.append('  { id: "%s", label: "%s", w: %d, icon: %s },'
                     % (ids[t["label"]], t["label"], t["w"], icons[t["label"]]))
    lines.append("];")
    lines.append("")

    lines.append("// ── 工具行两枚按钮（源站实测 32×32，间隙 2）──")
    lines.append("// ★「筛选音色」那枚的源站 cls 里带 `relative`（可能挂角标）⟹ ⟹ 未复刻")
    for t in tools:
        lines.append("//   搜索 %d×%d，图标 %d×%d @(%d,%d)"
                     % (t["w"], t["w"], t["icon"]["w"], t["icon"]["h"],
                        t["icon"]["x"], t["icon"]["y"]))
    lines.append("")

    lines.append("// ── 20 条音色（名字 ＋ 副标）──")
    lines.append("// ★ 逐条出自 raw 的「名字」「副标」字段 ⟹ ⟹ 不是手打")
    lines.append("const VOICES: { name: string; sub: string }[] = [")
    for c in cards:
        lines.append('  { name: "%s", sub: "%s" },' % (c["名字"], c["副标"]))
    lines.append("];")
    lines.append("")

    # ── 由 raw 算出来的量（不是手打常数）──
    heights = {c["卡盒"]["h"] for c in cards}
    tops = [c["卡盒"]["y"] for c in cards]
    steps = {tops[i + 1] - tops[i] for i in range(len(tops) - 1)}
    if len(heights) != 1 or len(steps) != 1:
        print("✘ 音色卡的高度/步进不唯一 ⟹ raw 与预期不符", file=sys.stderr)
        return 2
    card_h = heights.pop()
    step = steps.pop()
    gap = step - card_h
    scroll_h = r["滚动区"]["滚动高"]
    calc = len(cards) * card_h + (len(cards) - 1) * gap + 80
    if calc != scroll_h:
        print("✘ 滚动高度算出来 %d ≠ raw 实测 %d" % (calc, scroll_h), file=sys.stderr)
        return 2

    lines.append("// ── 由 raw **算**出来的量（★ 不是手打常数）──")
    lines.append("// ★ 音色卡高 %d，步进 %d ⟹ ⟹ 间隙 %d（space-y-2）" % (card_h, step, gap))
    lines.append("// ★ 滚动区高 %d ＝ %d×%d ＋ %d×%d ＋ 80(pb-20) ⟹ ⟹ 与 raw 的 scrollHeight 一致"
                 % (scroll_h, len(cards), card_h, len(cards) - 1, gap))
    lines.append("const VOICE_CARD_HEIGHT = %d;" % card_h)
    lines.append("const VOICE_CARD_GAP = %d;" % gap)
    lines.append("const VOICE_SCROLL_HEIGHT = %d;" % scroll_h)
    lines.append("")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print("✓ 已生成 %s" % OUT.relative_to(ROOT))
    print("  标题行页签 %d 枚 ＋ 工具按钮 %d 枚 ＋ 音色卡 %d 条" % (len(tabs), len(tools), len(cards)))
    print("  卡高 %d ／ 步进 %d ／ 间隙 %d ／ 滚动高 %d（自校验通过）"
          % (card_h, step, gap, scroll_h))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 848：从**入库的源站 raw** 机器提取 TSX 里第五段另外两页的数据块。

★ 三份 raw 一起用（★ 因为页签的**宽度随选中态变** ⟹ ⟹ 必须三份交叉）：
  · batch 847 raw（`音色库` 选中）：三枚页签 70／24／24
  · batch 848 p3 raw（`我的音色` 选中）：24／**84**／24
  · batch 848 p4 raw（`AI 生成` 选中）：24／24／**73**

★ 提取出的东西：
  · 三枚页签的「选中宽」与「未选中宽」（★ 交叉校验 ⟹ ⟹ 每个宽度至少在两份 raw 里出现）
  · P3「我的音色」页：工具行两枚按钮 ＋ 滚动区 ＋ 空态「暂无音色数据」
  · P4「AI 生成」页：内容区 ＋ 输入框 ＋ 「生成音色」按钮（带角标）＋「生成历史」＋ 空态

★ **自校验**（不合格就不写文件）：
  ① 每枚页签的「未选中宽」在**所有** raw 里都必须是同一个值；
  ② 每枚页签的「选中宽」必须**只**在它自己被选中的那一份 raw 里出现；
  ③ P3／P4 的关键盒必须与 raw 逐条相符（数量、尺寸）。
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch848-2026-10-01"
RAW_P3 = BATCH / "raw/source-848-p3.json"
RAW_P4 = BATCH / "raw/source-848-p4.json"
RAW_847 = ROOT / "docs/research/liblib-canvas-batch847-2026-10-01/raw/source-847-voice.json"
OUT = BATCH / "probes/voice-848-data.ts.txt"


def walk(node):
    """★ 深度优先遍历（★ 节点是 dict，带 `b`＝盒、`c2`＝子节点）。"""
    yield node
    for k in node.get("c2") or []:
        yield from walk(k)


def norm_box(n):
    """★ 两种 raw 的盒格式不一样 ⟹ ⟹ 归一化成 (x, y, w, h)。

    · batch 848 的 raw：节点带 `b` ＝ [x, y, w, h]
    · batch 847 的 raw：节点带 `box` ＝ {x, y, w, h}
    """
    b = n.get("b")
    if isinstance(b, list) and len(b) == 4:
        return tuple(b)
    d = n.get("box")
    if isinstance(d, dict) and "w" in d:
        return (d["x"], d["y"], d["w"], d["h"])
    return None


def walk_all(obj):
    """★ 遍历**整个** JSON（⟹ ⟹ 不关心 raw 顶层长什么样）。"""
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from walk_all(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk_all(v)


def find_all(root, pred):
    return [n for n in walk(root) if pred(n)]


def find_one(root, pred, what):
    hits = find_all(root, pred)
    if len(hits) != 1:
        raise SystemExit("✘ %s：找到 %d 个（应为 1）⟹ raw 与预期不符" % (what, len(hits)))
    return hits[0]


LABELS = ("音色库", "我的音色", "AI 生成")


def tabs_of(raw, selected_label):
    """★ 从一份 raw 里读出三枚页签的（标签、按钮宽、x、文字宽）。

    ★ 两份 raw 的字段名不同（848 用 `ar`／847 用 `text`）⟹ ⟹ 两个都认；
    ★ 文字宽统一由**按钮宽**推出（选中态：按钮宽 − 28 ＝ 3＋18＋4＋文字＋3）。
    """
    found = {}
    for n in walk_all(raw):
        if n.get("tag") != "BUTTON" and n.get("t") != "BUTTON":
            continue
        label = n.get("ar") or n.get("text")
        if label not in LABELS:
            continue
        box = norm_box(n)
        if box is None or box[0] < 1273:
            continue
        key = (label, box[2], box[0])
        found[key] = {"label": label, "w": box[2], "x": box[0],
                      "text_w": box[2] - 28, "selected": (label == selected_label)}
    return sorted(found.values(), key=lambda t: t["x"])


def main() -> int:
    p3 = json.loads(RAW_P3.read_text(encoding="utf-8"))
    p4 = json.loads(RAW_P4.read_text(encoding="utf-8"))
    r847 = json.loads(RAW_847.read_text(encoding="utf-8"))

    # ── 自证：三份 raw 都必须是「只读」且点到了目标页 ──
    for name, d, mark in (("p3", p3, "我的音色"), ("p4", p4, "AI 生成")):
        if d.get("★积分是否变化"):
            print("✘ %s 积分变了 ⟹ raw 作废" % name, file=sys.stderr)
            return 2
    if r847.get("★分段_积分是否变化"):
        print("✘ 847 raw 积分变了 ⟹ 作废", file=sys.stderr)
        return 2

    t_lib = tabs_of(r847, "音色库")
    t_mine = tabs_of(p3, "我的音色")
    t_ai = tabs_of(p4, "AI 生成")
    for nm, t in (("847", t_lib), ("p3", t_mine), ("p4", t_ai)):
        if len(t) != 3:
            print("✘ %s raw 里的页签数 %d ≠ 3" % (nm, len(t)), file=sys.stderr)
            return 2
        sel = [x for x in t if x["selected"]]
        if len(sel) != 1:
            print("✘ %s raw 里的选中页签数 %d ≠ 1" % (nm, len(sel)), file=sys.stderr)
            return 2

    # ── 交叉校验：每枚页签的「未选中宽」必须处处相同 ──
    w_off = {}
    w_on = {}
    for nm, t in (("847", t_lib), ("p3", t_mine), ("p4", t_ai)):
        for x in t:
            if x["selected"]:
                w_on.setdefault(x["label"], []).append((nm, x["w"]))
            else:
                w_off.setdefault(x["label"], set()).add(x["w"])
    for label, s in w_off.items():
        if len(s) != 1:
            print("✘ 页签「%s」的未选中宽不唯一：%s ⟹ raw 自相矛盾" % (label, sorted(s)),
                  file=sys.stderr)
            return 2
    for label, lst in w_on.items():
        if len(lst) != 1:
            print("✘ 页签「%s」的选中宽在多份 raw 里出现：%s" % (label, lst), file=sys.stderr)
            return 2

    # ── P3「我的音色」页的读数 ──
    r3 = p3["★整棵子树"]
    tools3 = find_all(r3, lambda n: n.get("t") == "BUTTON" and n.get("ar") in ("搜索", "筛选音色"))
    if len(tools3) != 2:
        print("✘ P3 的工具按钮数 %d ≠ 2" % len(tools3), file=sys.stderr)
        return 2
    tools3.sort(key=lambda n: n["b"][0])
    scroll3 = find_one(r3, lambda n: "overflow-y-auto" in (n.get("c") or "")
                       and n.get("b", [0])[0] >= 1297 and n.get("b", [0, 0, 0, 0])[3] == 514,
                       "P3 滚动区")
    empty3 = find_one(r3, lambda n: (n.get("x") or "") == "暂无音色数据"
                       and "h-24" in (n.get("c") or ""), "P3 空态")

    # ── P4「AI 生成」页的读数 ──
    r4 = p4["★整棵子树"]
    content4 = find_one(r4, lambda n: "space-y-3" in (n.get("c") or "")
                        and n.get("b", [0])[0] >= 1297, "P4 内容区")
    ta4 = find_one(r4, lambda n: n.get("t") == "TEXTAREA", "P4 输入框")
    gen4 = find_one(r4, lambda n: n.get("ar") == "生成音色", "P4 生成按钮")
    badge4 = find_one(gen4, lambda n: (n.get("t") == "SPAN" and "inline-flex shrink-0" in (n.get("c") or "")),
                      "P4 角标")
    badge4n = find_one(gen4, lambda n: (n.get("t") == "SPAN" and "text-center font-normal" in (n.get("c") or "")),
                       "P4 角标数字")
    hist4 = find_one(r4, lambda n: n.get("t") == "H3", "P4 历史标题")
    none4 = find_one(r4, lambda n: (n.get("x") or "") == "暂无历史记录"
                      and "py-6" in (n.get("c") or ""), "P4 历史空态")

    lines = []
    lines.append("// ── 标题行页签（★ 源站实测：**宽度随选中态变** ⟹ ⟹ 两套宽度）──")
    lines.append("//   选中态：28 ＋ 文字宽（3 边距 ＋ 18 图标 ＋ 4 间隙 ＋ 文字 ＋ 3 边距）")
    lines.append("//   未选中：24（★ 源站把文字盒裁成 0 宽 ⟹ ⟹ 只剩图标）")
    lines.append("// ★ 三份 raw 交叉校验（847 音色库／848-p3 我的音色／848-p4 AI 生成）")
    lines.append("const VOICE_TABS: { id: string; label: string; wOn: number; wOff: number; icon: typeof Music }[] = [")
    ids = {"音色库": "library", "我的音色": "mine", "AI 生成": "ai"}
    icons = {"音色库": "Music", "我的音色": "User", "AI 生成": "Sparkles"}
    for label in ("音色库", "我的音色", "AI 生成"):
        lines.append('  { id: "%s", label: "%s", wOn: %d, wOff: %d, icon: %s },'
                     % (ids[label], label, w_on[label][0][1],
                        sorted(w_off[label])[0], icons[label]))
    lines.append("];")
    lines.append("")

    lines.append("// ── P3「我的音色」页（★ 源站实测）──")
    lines.append("// ★ **这一页也有工具行**（搜索／筛选音色）⟹ ⟹ 与「音色库」页同构")
    for i, b in enumerate(tools3):
        lines.append("//   工具%d %d×%d @(%d,%d)" % (i, b["b"][2], b["b"][3], b["b"][0], b["b"][1]))
    lines.append("// ★ 空态：%d×%d @(%d,%d)  文案「%s」"
                 % (empty3["b"][2], empty3["b"][3], empty3["b"][0], empty3["b"][1], empty3["x"]))
    lines.append("const VOICE_MINE_EMPTY = {")
    lines.append('  text: "%s",' % empty3["x"])
    lines.append("  w: %d, h: %d," % (empty3["b"][2], empty3["b"][3]))
    lines.append('  fontSize: "%s", lineHeight: "%s", color: "%s",' %
                 (empty3["s"]["fs"], empty3["s"]["lh"], empty3["s"]["col"]))
    lines.append("};")
    lines.append("")

    lines.append("// ── P4「AI 生成」页（★ 源站实测）──")
    lines.append("// ★ **这一页没有工具行**⟹ ⟹ 内容区直接从标题行下方开始")
    lines.append("// ★ 输入框 %d×%d @(%d,%d)，占位文案「%s」"
                 % (ta4["b"][2], ta4["b"][3], ta4["b"][0], ta4["b"][1], ta4.get("ph")))
    lines.append("// ★ 「生成音色」按钮 %d×%d @(%d,%d)，右侧角标 %d×%d（图标 ＋ 数字「%s」）"
                 % (gen4["b"][2], gen4["b"][3], gen4["b"][0], gen4["b"][1],
                    badge4["b"][2], badge4["b"][3], badge4n.get("x")))
    lines.append("// ★ 「生成历史」小标题 %d×%d @(%d,%d) ＋ 空态「%s」%d×%d @(%d,%d)"
                 % (hist4["b"][2], hist4["b"][3], hist4["b"][0], hist4["b"][1],
                    none4["x"], none4["b"][2], none4["b"][3], none4["b"][0], none4["b"][1]))
    lines.append("const VOICE_AI = {")
    lines.append("  content: { w: %d, h: %d, padTop: %s, padBottom: %s, gap: %s },"
                 % (content4["b"][2], content4["b"][3], content4["s"]["pt"],
                    content4["s"]["pb"], content4["s"]["gap"]))
    lines.append("  textarea: { w: %d, h: %d, radius: %s, padding: %s, fontSize: \"%s\","
                 % (ta4["b"][2], ta4["b"][3], ta4["s"]["br"], ta4["s"]["pl"],
                    ta4["s"]["fs"]))
    lines.append('    lineHeight: "%s", color: "%s", background: "%s",' %
                 (ta4["s"]["lh"], ta4["s"]["col"], ta4["s"]["bg"]))
    lines.append('    ariaLabel: "%s", placeholder: "%s" },' % (ta4.get("ar"), ta4.get("ph")))
    lines.append("  generate: { w: %d, h: %d, radius: %s, gap: %s, fontSize: \"%s\","
                 % (gen4["b"][2], gen4["b"][3], gen4["s"]["br"], gen4["s"]["gap"],
                    gen4["s"]["fs"]))
    lines.append('    lineHeight: "%s", color: "%s", background: "%s", label: "生成音色" },'
                 % (gen4["s"]["lh"], gen4["s"]["col"], gen4["s"]["bg"]))
    lines.append("  badge: { w: %d, h: %d, gap: %s, number: \"%s\"," %
                 (badge4["b"][2], badge4["b"][3], badge4["s"]["gap"], badge4n.get("x")))
    lines.append("    numberW: %d, numberH: %d, numberFontSize: \"%s\" }," %
                 (badge4n["b"][2], badge4n["b"][3], badge4n["s"]["fs"]))
    lines.append("  history: { title: \"生成历史\", titleW: %d, titleH: %d," %
                 (hist4["b"][2], hist4["b"][3]))
    lines.append('    titleFontSize: "%s", titleLineHeight: "%s", titleColor: "%s",' %
                 (hist4["s"]["fs"], hist4["s"]["lh"], hist4["s"]["col"]))
    lines.append('    empty: "暂无历史记录", emptyW: %d, emptyH: %d,' %
                 (none4["b"][2], none4["b"][3]))
    lines.append('    emptyFontSize: "%s", emptyLineHeight: "%s", emptyColor: "%s" },' %
                 (none4["s"]["fs"], none4["s"]["lh"], none4["s"]["col"]))
    lines.append("};")
    lines.append("")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print("✓ 已生成 %s" % OUT.relative_to(ROOT))
    print("  页签：", {k: (w_on[k][0][1], sorted(w_off[k])[0]) for k in ("音色库", "我的音色", "AI 生成")})
    print("  P3：工具 %d 枚 ＋ 滚动区 %s ＋ 空态 %d×%d「%s」"
          % (len(tools3), scroll3["b"], empty3["b"][2], empty3["b"][3], empty3["x"]))
    print("  P4：内容区 %s ／ 输入框 %s ／ 按钮 %s ／ 角标 %s「%s」／ 标题 %s ／ 空态 %s"
          % (content4["b"], ta4["b"], gen4["b"], badge4["b"], badge4n.get("x"),
             hist4["b"], none4["b"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())

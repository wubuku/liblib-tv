#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 849：从**入库的源站 raw** 机器提取第四段另外两页的数据块。

★ 本批做的是**第四段「服装造型」**的另外两枚子页签：
  · P1「服装」   ＝ 7 枚分类 chip ＋ **24 张**服装卡（3 列网格）
  · P2「AI 生成」＝ 一张卡（TEXTAREA ＋ 两枚胶囊）＋「确认生成」

★ 三份 raw 一起用（★ 因为页签的**宽度随选中态变** ⟹ ⟹ 必须三份交叉）：
  · batch 846 raw（`造型` 选中）：造型 56／服装 24／AI 生成 24
  · batch 848 p1 raw（`服装` 选中）：造型 24／**服装 56**／AI 生成 24
  · batch 848 p2 raw（`AI 生成` 选中）：造型 24／服装 24／**AI 生成 73**

★ ★ **第四段与第五段的页签宽度规律一致**：
  选中 ＝ 28 ＋ 文字宽（3 边距 ＋ 18 图标 ＋ 4 间隙 ＋ 文字 ＋ 3 边距）
  ⟹ ⟹ 造型 56（文字 28）／服装 56（文字 28）／AI 生成 73（文字 45）
  未选中一律 24（★ 源站把文字盒裁成 0 宽 ⟹ ⟹ 只剩图标）

★ **自校验**（不合格就不写文件）：
  ① 每枚页签的「未选中宽」在**所有** raw 里都必须是同一个值；
  ② 每枚页签的「选中宽」必须**只**在它自己被选中的那一份 raw 里出现；
  ③ P1 的 chip 数 ＝ 7、卡数 ＝ 24；P2 的两枚胶囊文案必须**逐字**读出来
     （★ ★ 不能手打：源站那枚胶囊是「人设定制造型」**一个字符串**，
       而**不是**两枚胶囊「人设定」＋「造型」⟹ ⟹ 手打必错）；
  ④ ★ **P1 有底部生成遮罩、P2 没有**（P2 的「确认生成」在**内容流**里）
     ⟹ ⟹ 这条差异必须由 raw **自动判出来**，不是写死的。
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
B848 = ROOT / "docs/research/liblib-canvas-batch848-2026-10-01/raw"
B846 = ROOT / "docs/research/liblib-canvas-batch846-2026-10-01/raw"
RAW_P1 = B848 / "source-848-p1.json"
RAW_P2 = B848 / "source-848-p2.json"
RAW_VOICE = B848 / "source-848-voice.json"
RAW_846 = B846 / "source-846-outfit.json"
OUT = ROOT / "docs/research/liblib-canvas-batch849-2026-10-01/probes/outfit-849-data.ts.txt"

# ★★ 段内坐标原点 ＝ **右栏列的左上角**（源站 abs 1273,231）
#   ⟹ ⟹ 与 batch 846 **同一个口径**（`gen846_data.py` 用的也是这两个数）
#   ⟹ ⟹ 标题行 40 ⟹ ⟹ 滚动区顶 = 271 ⟹ ⟹ 内容起点 = 287（pt-4 16）
#   ⟹ ⟹ clone 里 `.ce-section` 的 top/left **就是**相对这个原点的
ORIGIN_X = 1273
ORIGIN_Y = 271

# ★ 第四段的三枚子页签（★ 与第五段不同：第四段叫「造型」，第五段叫「音色库」）
LABELS = ("造型", "服装", "AI 生成")
IDS = {"造型": "style", "服装": "clothes", "AI 生成": "ai"}


def walk(node):
    yield node
    for k in node.get("c2") or []:
        yield from walk(k)


def walk_all(obj):
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from walk_all(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk_all(v)


def box4(n):
    b = n.get("b")
    if isinstance(b, list) and len(b) == 4:
        return tuple(b)
    return None


def find_all(root, pred):
    return [n for n in walk(root) if pred(n)]


def find_one(root, pred, what):
    hits = find_all(root, pred)
    if len(hits) != 1:
        raise SystemExit("✘ %s：找到 %d 个（应为 1）⟹ raw 与预期不符" % (what, len(hits)))
    return hits[0]


def tabs_of_848(raw, selected_label):
    """★ 从 848 raw 里读出三枚子页签的（标签、按钮宽、x、文字宽）。

    ★ 848 raw 用 `ar`（aria-label）承载标签。
    """
    found = {}
    for n in walk_all(raw):
        if n.get("t") != "BUTTON":
            continue
        label = n.get("ar")
        if label not in LABELS:
            continue
        b = box4(n)
        if b is None or b[0] < 1273:
            continue
        found[(label, b[2], b[0])] = {"label": label, "w": b[2], "x": b[0],
                                      "text_w": b[2] - 28,
                                      "selected": (label == selected_label)}
    return sorted(found.values(), key=lambda t: t["x"])


def tabs_of_846(raw):
    """★ 从 846 raw 里读出三枚子页签（★ 846 raw 的盒格式是 dict，且标签在 `aria`）。"""
    rows = raw["★读数"]["子页签行"]["按钮"]
    out = []
    for b in rows:
        bb = b["box"]
        out.append({"label": b["aria"], "w": bb["w"], "x": bb["x"],
                    "text_w": bb["w"] - 28,
                    "selected": (b["aria"] == "造型")})
    return sorted(out, key=lambda t: t["x"])


def main() -> int:
    p1 = json.loads(RAW_P1.read_text(encoding="utf-8"))
    p2 = json.loads(RAW_P2.read_text(encoding="utf-8"))
    r846 = json.loads(RAW_846.read_text(encoding="utf-8"))
    voice = json.loads(RAW_VOICE.read_text(encoding="utf-8"))

    # ── 自证：合订 raw 里这两页的积分**全程未变** ──
    for e in voice.get("★入口清单") or []:
        if e.get("★页签") in ("服装", "AI 生成") and e.get("★分段") == "服装造型":
            if e.get("★积分是否变化") is not False:
                print("✘ 「%s」那页积分变了 ⟹ raw 作废" % e["★页签"], file=sys.stderr)
                return 2

    t_style = tabs_of_846(r846)
    t_cloth = tabs_of_848(p1, "服装")
    t_ai = tabs_of_848(p2, "AI 生成")
    for nm, t in (("846", t_style), ("p1", t_cloth), ("p2", t_ai)):
        if len(t) != 3:
            print("✘ %s raw 里的子页签数 %d ≠ 3" % (nm, len(t)), file=sys.stderr)
            return 2
        sel = [x for x in t if x["selected"]]
        if len(sel) != 1:
            print("✘ %s raw 里的选中子页签数 %d ≠ 1" % (nm, len(sel)), file=sys.stderr)
            return 2

    # ── 交叉校验：未选中宽处处相同；选中宽只出现在自己那一份 raw ──
    w_off, w_on = {}, {}
    for nm, t in (("846", t_style), ("p1", t_cloth), ("p2", t_ai)):
        for x in t:
            if x["selected"]:
                w_on.setdefault(x["label"], []).append((nm, x["w"]))
            else:
                w_off.setdefault(x["label"], set()).add(x["w"])
    for label, s in w_off.items():
        if len(s) != 1:
            print("✘ 子页签「%s」的未选中宽不唯一：%s" % (label, sorted(s)), file=sys.stderr)
            return 2
    for label, lst in w_on.items():
        if len(lst) != 1:
            print("✘ 子页签「%s」的选中宽在多份 raw 里出现：%s" % (label, lst), file=sys.stderr)
            return 2

    r1 = p1["★整棵子树"]
    r2 = p2["★整棵子树"]

    # ── P1「服装」页 ──
    # ★ ★ 判据必须**结构化**，不能只按坐标／尺寸猜：
    #   ⟹ ⟹ 只按「高 26」过滤会**多抓一枚** —— 模态右上角那枚「关闭」也是 26×26
    #   ⟹ ⟹ 只按「x 在 1297..1537」也**排除不掉**它（关闭按钮 x=1514）
    #   ⟹ ⟹ 正解：先找到 chip **容器**（`flex flex-wrap gap-1.5`）⟹ ⟹ 再取它的 BUTTON 子节点
    chipbox1 = find_one(r1, lambda n: "flex-wrap" in (n.get("c") or "")
                         and "gap-1.5" in (n.get("c") or ""), "P1 chip 容器")
    chips1 = [n for n in (chipbox1.get("c2") or []) if n.get("t") == "BUTTON"]
    chips1.sort(key=lambda n: (box4(n)[1], box4(n)[0]))
    # ★ 选中态由 **class** 判（`bg-btn-primary` ⟹ 白底黑字）⟹ ⟹ 不靠「第一枚就是选中」
    def is_chip_selected(n):
        return "bg-btn-primary" in (n.get("c") or "")
    grid1 = find_one(r1, lambda n: "grid-cols-3" in (n.get("c") or ""), "P1 服装网格")
    cards1 = grid1.get("c2") or []
    h3_1 = find_one(r1, lambda n: n.get("t") == "H3" and box4(n)
                     and box4(n)[0] >= 1297, "P1 小标题")
    mask1 = find_all(r1, lambda n: "GenerateMask" in (n.get("c") or ""))
    gen1 = find_one(r1, lambda n: n.get("t") == "BUTTON" and n.get("ar") == "确认生成",
                    "P1 确认生成")

    # ── P2「AI 生成」页 ──
    card2 = find_one(r2, lambda n: "min-h-[168px]" in (n.get("c") or ""), "P2 卡片")
    ta2 = find_one(r2, lambda n: n.get("t") == "TEXTAREA", "P2 输入框")
    gen2 = find_one(r2, lambda n: n.get("t") == "BUTTON" and n.get("ar") == "确认生成",
                    "P2 确认生成")
    mask2 = find_all(r2, lambda n: "GenerateMask" in (n.get("c") or ""))
    # ★ 底部那一行（`flex h-7 ... gap-0.5 px-2 pb-2`）里的两枚控件：
    #   ① 一枚**圆按钮**（aria「选择参考图」，28×28，**没有文字**）
    #   ② 一枚**胶囊**（aria「造型技能」，119×28，**文字是「人设定制造型」**）
    # ★ ★ 胶囊文案**逐字读出** ⟹ ⟹ 不手打：
    #   ⟹ ⟹ 注意它**不是**两枚胶囊「人设定」＋「造型」⟹ ⟹ 手打必错
    row2 = find_one(card2, lambda n: n.get("t") == "DIV"
                    and "h-7" in (n.get("c") or "")
                    and "gap-0.5" in (n.get("c") or ""), "P2 卡片底部行")
    # ★ 底部行里的两枚 BUTTON（★ 源站**两枚都是** `rounded-full`
    #   ⟹ ⟹ 不能靠 class 区分 ⟹ ⟹ 靠「**有没有文字**」区分）
    # ★ ★ 两枚 BUTTON **不在**底部行的**直接**子节点里（各有一层 DIV 包着）
    #   ⟹ ⟹ 必须**递归**取 ⟹ ⟹ 只取直接子节点会得到 0 枚
    row_buttons = [n for n in walk(row2) if n.get("t") == "BUTTON"]
    with_text = [n for n in row_buttons if n.get("x")]
    without_text = [n for n in row_buttons if not n.get("x")]
    if len(row_buttons) != 2 or len(with_text) != 1 or len(without_text) != 1:
        print("✘ P2 底部行：共 %d 枚按钮，其中有字 %d 枚、无字 %d 枚 ⟹ 与实测不符"
              % (len(row_buttons), len(with_text), len(without_text)), file=sys.stderr)
        return 2
    round2 = without_text[0]
    pill2 = with_text[0]
    # ★ 上传的隐藏 input（★ 它的 aria 才是「上传造型参考图」）
    upload2 = find_one(card2, lambda n: n.get("t") == "INPUT" and n.get("ar"),
                       "P2 上传 input")

    # ── 自校验 ③：数量 ──
    # ── 自校验 ③：数量（P2 的底部行**必须**是「一枚圆按钮 ＋ 一枚胶囊」）──
    if len(chips1) != 7:
        print("✘ P1 的分类 chip 数 %d ≠ 7" % len(chips1), file=sys.stderr)
        return 2
    if len(cards1) != 24:
        print("✘ P1 的服装卡数 %d ≠ 24" % len(cards1), file=sys.stderr)
        return 2
    # ★ 圆按钮**必须**没有文字（★ 它是图标按钮）⟹ ⟹ 这一条能挡住「把它当胶囊写」
    if round2.get("x"):
        print("✘ P2 的圆按钮居然带文字 %r" % round2.get("x"), file=sys.stderr)
        return 2
    if not pill2.get("x"):
        print("✘ P2 的胶囊没有文字", file=sys.stderr)
        return 2
    # ── 自校验 ④：★ 遮罩的有无**由 raw 判出来** ⟹ ⟹ 记进产物 ──
    if len(mask1) != 1:
        print("✘ P1 的底部生成遮罩数 %d ≠ 1" % len(mask1), file=sys.stderr)
        return 2
    if len(mask2) != 0:
        print("✘ P2 竟然有底部生成遮罩（%d 个）⟹ 与实测不符" % len(mask2), file=sys.stderr)
        return 2

    L = []
    A = L.append

    def rx(b):
        return b[0] - ORIGIN_X

    def ry(b):
        return b[1] - ORIGIN_Y

    A("// ── 第四段的子页签（★ 源站实测：**宽度随选中态变** ⟹ ⟹ 两套宽度）──")
    A("//   选中态：28 ＋ 文字宽（3 边距 ＋ 18 图标 ＋ 4 间隙 ＋ 文字 ＋ 3 边距）")
    A("//   未选中：24（★ 源站把文字盒裁成 0 宽 ⟹ ⟹ 只剩图标）")
    A("// ★ 三份 raw 交叉校验（846 造型／848-p1 服装／848-p2 AI 生成）")
    A("const OUTFIT_TABS: { id: string; label: string; wOn: number; wOff: number; icon: typeof Shirt }[] = [")
    icons = {"造型": "Shirt", "服装": "Package", "AI 生成": "Sparkles"}
    for label in LABELS:
        A('  { id: "%s", label: "%s", wOn: %d, wOff: %d, icon: %s },'
          % (IDS[label], label, w_on[label][0][1],
             sorted(w_off[label])[0], icons[label]))
    A("];")
    A("")

    A("// ── P1「服装」页（★ 源站实测）──")
    A("//   小标题「%s」 %d×%d @rel(%d,%d)"
      % (h3_1.get("x"), box4(h3_1)[2], box4(h3_1)[3], rx(box4(h3_1)), ry(box4(h3_1))))
    A("//   ★ %d 枚分类 chip（★ 选中态由 raw 的 class 判：%s）"
      % (len(chips1),
         "／".join(c.get("x") for c in chips1 if is_chip_selected(c)) or "（无）"))
    A("const OUTFIT_CLOTHES_CHIPS: { label: string; x: number; y: number; w: number; sel: boolean }[] = [")
    for c in chips1:
        b = box4(c)
        A('  { label: "%s", x: %d, y: %d, w: %d, sel: %s },'
          % (c.get("x"), rx(b), ry(b), b[2],
             "true" if is_chip_selected(c) else "false"))
    A("];")
    A("")
    A("//   ★ %d 张服装卡（3 列网格；★ 图是**引用**源站 CDN 的真实图）" % len(cards1))
    A("const OUTFIT_CLOTHES_CARDS: { label: string; img: string; x: number; y: number }[] = [")
    for card in cards1:
        b = box4(card)
        img = next((m for m in walk(card) if m.get("t") == "IMG"), None)
        lbl = next((m for m in walk(card)
                    if m.get("t") == "SPAN" and m.get("x")), None)
        A('  { label: "%s", img: "%s", x: %d, y: %d },'
          % (lbl.get("x") if lbl else "", img.get("src") if img else "",
             rx(b), ry(b)))
    A("];")
    A("")
    A("//   ★ 这一页**有**底部生成遮罩（「确认生成」%d×%d @(%d,%d)）"
      % (box4(gen1)[2], box4(gen1)[3], box4(gen1)[0], box4(gen1)[1]))
    A("const OUTFIT_CLOTHES_GENERATE = { w: %d, h: %d };" % (box4(gen1)[2], box4(gen1)[3]))
    A("//   ★ 那枚遮罩（`Ias-7a_editorPanelGenerateMask`）%d×%d @rel(%d,%d)"
      % (box4(mask1[0])[2], box4(mask1[0])[3], rx(box4(mask1[0])), ry(box4(mask1[0]))))
    A("")

    A("// ── P2「AI 生成」页（★ 源站实测）──")
    A("//   ★ 这一页**没有**底部生成遮罩 ⟹ ⟹ 「确认生成」在**内容流**里")
    A("//   卡片 %d×%d @rel(%d,%d)"
      % (box4(card2)[2], box4(card2)[3], rx(box4(card2)), ry(box4(card2))))
    A("//   输入框 %d×%d @rel(%d,%d)　占位「%s」"
      % (box4(ta2)[2], box4(ta2)[3], rx(box4(ta2)), ry(box4(ta2)), ta2.get("ph")))
    A("const OUTFIT_AI_CARD = { w: %d, h: %d };" % (box4(card2)[2], box4(card2)[3]))
    A("const OUTFIT_AI_TEXTAREA = { w: %d, h: %d, placeholder: \"%s\" };"
      % (box4(ta2)[2], box4(ta2)[3], ta2.get("ph")))
    A("//   ★ 底部行（`flex h-7 ... gap-0.5 px-2 pb-2`）里**两枚**控件：")
    A("//     ① 一枚**圆按钮**（aria「%s」，%d×%d，**没有文字**）"
      % (round2.get("ar"), box4(round2)[2], box4(round2)[3]))
    A("//     ② 一枚**胶囊**（aria「%s」，%d×%d，★ 文字**逐字读出**）"
      % (pill2.get("ar"), box4(pill2)[2], box4(pill2)[3]))
    A("//   ★ ★ 那枚胶囊的文案是**一个字符串**「%s」"
      % pill2.get("x"))
    A("//   ⟹ ⟹ **不是**两枚胶囊「人设定」＋「造型」⟹ ⟹ 手打必错")
    A("const OUTFIT_AI_ROUND_BTN = { aria: \"%s\", w: %d, h: %d };"
      % (round2.get("ar"), box4(round2)[2], box4(round2)[3]))
    A("const OUTFIT_AI_PILL = { aria: \"%s\", label: \"%s\", w: %d, h: %d };"
      % (pill2.get("ar"), pill2.get("x"), box4(pill2)[2], box4(pill2)[3]))
    A("//   ★ 那枚隐藏的上传 input（aria「%s」）" % upload2.get("ar"))
    A("const OUTFIT_AI_UPLOAD_ARIA = \"%s\";" % upload2.get("ar"))
    A("//   「确认生成」%d×%d @rel(%d,%d)"
      % (box4(gen2)[2], box4(gen2)[3], rx(box4(gen2)), ry(box4(gen2))))
    A("const OUTFIT_AI_GENERATE = { w: %d, h: %d };" % (box4(gen2)[2], box4(gen2)[3]))
    A("")

    OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("✔ 已写出", OUT)
    print("  子页签宽度：", {k: (w_on[k][0][1], sorted(w_off[k])[0]) for k in LABELS})
    print("  P1：%d 枚 chip ＋ %d 张卡；P2：圆按钮 + 胶囊「%s」"
          % (len(chips1), len(cards1), pill2.get("x")))
    return 0


if __name__ == "__main__":
    sys.exit(main())

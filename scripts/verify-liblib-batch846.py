#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 846 门禁：左列第四段「服装造型」（**子页签行 ＋ 四个小节**）对齐源站。

## 这批做了什么

batch 845 做完了左列第三段 ⟹ ⟹ 「**仍未实现的那一块**」变成**左列第四～五段**。

本批实现**第四段**「服装造型」。★ 源站**只读**实测（raw 入库在
`docs/research/liblib-canvas-batch846-2026-10-01/raw/`）：

    ★★ 这一段**有标题行** ⟹ ⟹ 右栏**第一层是子页签行**（40 高）
       ⟹ ⟹ 内容起点 ＝ 右栏顶 + 40 + 16（比前两段**低 40px**）
       ⟹ ⟹ 且子页签行**不是**「脸部精修」段那一行（★ 见下）
    子页签行（NAV，**240** 宽 @1297，**gap 12px 靠左**）：
       造型（56，带文字 ＋ 前置图标）／服装（24）／AI 生成（24）
       ⟹ ⟹ ★ 与脸部段那六枚**不是同一个组件**（脸部段是 `justify-between` 均分）
    内容 ＝ 四个小节（各 240×22 的 H3）：
       发型 ⟹ chip 7 枚 ＋ 卡 12 张（76×96）
       发色 ⟹ 色块 11 枚（35×35）
       妆容 ⟹ chip 7 枚 ＋ 卡 7 张
       口红 ⟹ 色块 10 枚
    滚动区高 **1312**；底部生成遮罩**只有**整宽 240×36 的「确认生成」
       （★ **没有**「智能调整」⟹ ⟹ 与脸部段 196＋36 不同）

## ★ 本批还更正了**三处既存偏差**（batch 840 起就有）

① **页签行那条 240px 的底边框线整条没画**：源站的页签行是**两层**——外层 `px-6`
   （288 宽）＋ 内层 NAV（**240** 宽，带 `border-bottom: 1px solid
   rgba(255,255,255,.08)`）⟹ ⟹ 那条**整条 240px 的底边框线**画在内层上。
   clone 之前把两层**合并**成一个 288 宽的 `.ce-tabs` ⟹ ⟹ **那条线整条没画**。
   ★ 证据：`raw/pixel-diff-846-tabs.json`（改之前源站 y=270 整行有白 8% 的线、
   clone 那一行全是底色）。
② **卡片媒体区**的计算 `display` 源站是 **block**（clone 之前是 flex ＋ 绝对定位）⟹ ⟹
   源站那张图在 76×76 里是 74×74 且偏移 +1（等于居中）。
③ **色块**的计算 `line-height` 源站是 **24.8px**（clone 之前 24px）。

## 期望值从哪来（★ 全部机器提取，不手打坐标）

- `raw/source-846-outfit.json` ⟹ 结构与计算样式（★ 主 raw）
- `raw/source-846-tabfont.json` ⟹ 子页签的**内层文字 span** 与 borderBottom
  （★ 主 raw 的 `st()` 没取那两项 ⟹ ⟹ 另跑一趟补测）
- `raw/source-846-facetabs.json` ⟹ 脸部段六枚页签的同口径读数（用于对照）
- `raw/source-846-tabsnap.json` ＋ `raw/source-846-tabs.png` ⟹ 溢出行为 ＋ 像素证据
- `raw/pixel-diff-846-tabs.json` ⟹ 子页签行的逐像素对照

模态原点取 batch 841 raw 的实测值（361／161）。

## 判据（S1–S7）

S1 ★★★ **这一段不再是空态**：4 个 H3、14 枚 chip、21 枚色块、19 张卡
    ⟹ ★ 清单**逐条**等于源站 raw 机器提取的清单；且**没有**空态说明
S2 ★★★ **几何逐像素**：H3／chip／色块／卡片盒／卡片名盒／媒体盒／子页签盒
    ⟹ ★ **期望项数独立从 raw 算**（不拿 geo 自己的长度当分母 ⟹ 那是自证）
S3 ★★★ **外观**逐键比对：chip／色块／卡片名／媒体区／H3／子页签的计算样式
    ⟹ ★ 期望值取自 raw
S4 ★★★ **初始选中态**照抄源站：发型「现代」／妆容「现代」／发色**第一枚**／
    口红**第二枚**；★ 且 19 张卡**全部未选中**
S5 ★★★ **真交互**：点 chip「古风」⟹ 选中态转移；点色块 ⟹ 转移；点卡片 ⟹ 转移
    ⟹ ★ 选中态**真的**跟着变（不是写死的）
S6 ★★★ **结构事实**：这一段**有**子页签行（3 枚）⟹ 内容起点 ＝ 右栏顶 + 56；
    滚动区高 1312；「智能调整」数 **0**；点「服装」子页签 ⟹ 显示**如实说明**
    （★ 那一页的控件**源站未实测** ⟹ ⟹ 不编造）
S7 ★★ **如实标注**：README 必须写明——★ 卡片图**引用**源站 CDN（是引用不是复刻）、
    ★ 图标**字形**用的是 lucide 占位（源站是 iconify）、★ 「服装」「AI 生成」两页
    **未实测**、★ 更正了**一处既存偏差**（页签行的底边框线）
"""
import json
import pathlib
import subprocess
import sys
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
BATCH = ROOT / "docs/research/liblib-canvas-batch846-2026-10-01"
RAW846 = BATCH / "raw/source-846-outfit.json"
TABFONT = BATCH / "raw/source-846-tabfont.json"
PIXDIFF = BATCH / "raw/pixel-diff-846-tabs.json"
RAW841 = ROOT / "docs/research/liblib-canvas-batch841-2026-10-01/raw/source-841-tabs.json"
# ★★ **batch 849 起**：第四段「服装」页的期望值从这份 raw 机器提取
RAW848_P1 = ROOT / "docs/research/liblib-canvas-batch848-2026-10-01/raw/source-848-p1.json"
PROBE_CLONE = BATCH / "probes/clone846.py"
OUT = BATCH / "runtime-audit.json"

# ★★ 判据读的**样式键**（★ 与探针的 `sty()` 同一套 ⟹ ⟹ 逐键可比）
STYLE_KEYS = ["fontSize", "fontWeight", "lineHeight", "color", "backgroundColor",
              "borderRadius", "borderTopWidth", "borderTopColor", "paddingLeft",
              "paddingTop", "paddingRight", "paddingBottom", "display"]
# ★★ 几何键（★ 源站与 clone **同名**的盒 ⟹ ⟹ 可以逐像素比）
GEO_KEYS = ("H3盒", "chip盒", "色块盒", "卡片盒", "卡片名盒", "媒体盒", "子页签盒")


def read_json(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


def served_chunks() -> str:
    html = urllib.request.urlopen("http://localhost:4317/", timeout=60).read().decode("utf-8", "replace")
    import re
    urls = sorted(set(re.findall(r'/_next/static/chunks/[^"]+\.(?:js|css)', html)))
    out = []
    for u in urls:
        try:
            out.append(urllib.request.urlopen("http://localhost:4317" + u, timeout=60)
                       .read().decode("utf-8", "replace"))
        except Exception:  # noqa: BLE001
            pass
    return "\n".join(out)


def preflight_js() -> tuple:
    """等 dev server 重建完 TSX（服务端 JS 里要能看到**这一段独有**的标记）。"""
    marker = "outfit-swatch"        # ★ 只这一批才有 ⟹ ⟹ 等得到就说明确实重建了
    t0 = time.time()
    while time.time() - t0 < 120:
        try:
            if marker in served_chunks():
                return True, {"等了几秒": round(time.time() - t0, 1), "标记": marker}
        except Exception:  # noqa: BLE001
            pass
        time.sleep(3)
    return False, {"等了几秒": round(time.time() - t0, 1), "标记": marker}


def clothes_expect() -> dict:
    """★ 从**入库的源站 raw**（848 的 p1）机器提取第四段「服装」页的期望。

    ★ ★ 为什么**必须**机器提取：
    #   「小标题文案」是「服装」、chip 数 ＝ 7、卡数 ＝ 24
    #   ⟹ ⟹ 手打**可能**对 ⟹ ⟹ 但**改**了源站就会错 ⟹ ⟹ 而门禁要钉的是源站
    """
    raw = read_json(RAW848_P1)
    root = raw["★整棵子树"]

    def walk(n):
        yield n
        for k in n.get("c2") or []:
            yield from walk(k)

    h3 = [n for n in walk(root)
          if n.get("t") == "H3" and (n.get("b") or [0])[0] >= 1297]
    if len(h3) != 1:
        raise SystemExit("✘ P1 的小标题数 %d ≠ 1" % len(h3))
    chipbox = [n for n in walk(root)
               if "flex-wrap" in (n.get("c") or "") and "gap-1.5" in (n.get("c") or "")]
    if len(chipbox) != 1:
        raise SystemExit("✘ P1 的 chip 容器数 %d ≠ 1" % len(chipbox))
    chips = [n for n in (chipbox[0].get("c2") or []) if n.get("t") == "BUTTON"]
    grid = [n for n in walk(root) if "grid-cols-3" in (n.get("c") or "")]
    if len(grid) != 1:
        raise SystemExit("✘ P1 的网格数 %d ≠ 1" % len(grid))
    cards = grid[0].get("c2") or []
    return {
        "小标题": h3[0].get("x"),
        "chip数": len(chips),
        "卡数": len(cards),
    }


def build_expectations() -> dict:
    """从**入库的源站 raw** 里抽出这一段的期望值（几何 ＋ 外观 ＋ 清单）。

    ★★ 注意：源站 raw 的 `读数.chip` 是一个**混合数组**（35 条）——
       真正的 chip（高 26）14 枚 ＋ **色块**（高 35）21 枚
       ⟹ ⟹ 源站这两个控件**共用同一套胶囊类名** ⟹ ⟹ 探针选不出来
       ⟹ ⟹ 这里按**盒高**机械地分成两类（⟹ ⟹ 判据可复现 ⟹ ⟹ 不是手打清单）。
    """
    raw = read_json(RAW846)
    src = raw["★读数"]
    tabfont = read_json(TABFONT)
    modal = read_json(RAW841)["★各状态读数"]["A_默认态_脸部精修_皮肤"]["modal"]
    ox, oy = modal["x"], modal["y"]

    def R(b):
        return {"x": b["x"] - ox, "y": b["y"] - oy, "w": b["w"], "h": b["h"]}

    all_caps = src["chip"]
    chips = [c for c in all_caps if c["box"]["h"] == 26]
    swatches = [c for c in all_caps if c["box"]["h"] == 35]

    h3_rows = [{"文字": h["text"], "盒": R(h["box"]), "样式": h["style"]}
               for h in src["H3"]]
    chip_rows = [{"文字": c["text"], "盒": R(c["box"]), "样式": c["style"],
                  "选中": c.get("选中")} for c in chips]
    sw_rows = [{"盒": R(c["box"]), "样式": c["style"], "选中": c.get("选中")}
               for c in swatches]
    card_rows = [{"aria": c["aria"], "盒": R(c["卡盒"]), "名字盒": R(c["名字盒"]),
                  "媒体盒": R(c["媒体盒"]), "名字样式": c["名字样式"],
                  "媒体样式": c["媒体样式"], "选中": c.get("选中")}
                 for c in src["卡片"]]
    # ★ 子页签行（★ **可见文字**的口径 ⟹ ⟹ 源站未选中那两枚的 label span
    #   盒宽是 **0**（被 `overflow:hidden` 裁掉）⟹ ⟹ 那一层**不可见**
    #   ⟹ ⟹ 故它的排版**不参与**比对（⟹ ⟹ 记 None ⟹ ⟹ 与 clone 的 null 天然相等）
    tab_rows = [{"aria": b["aria"], "盒": R(b["box"]), "样式": b["style"],
                 "可见文字宽": (b.get("内层文字盒") or {}).get("w", 0),
                 "文字fontSize": ((b.get("内层文字样式") or {}).get("fontSize")
                                  if (b.get("内层文字盒") or {}).get("w", 0) > 0 else None),
                 "文字lineHeight": ((b.get("内层文字样式") or {}).get("lineHeight")
                                    if (b.get("内层文字盒") or {}).get("w", 0) > 0 else None),
                 "文字color": ((b.get("内层文字样式") or {}).get("color")
                               if (b.get("内层文字盒") or {}).get("w", 0) > 0 else None)}
                for b in tabfont["★子页签行"]["按钮"]]

    # ★ 初始选中态（★ 从 raw 机械提取 ⟹ ⟹ 不是手打）
    # ★★ 切分依据：源站 raw 的混合数组是**按段顺序**排的
    #   ⟹ 发型 chip 7 → 发色色块 11 → 妆容 chip 7 → 口红色块 10
    #   ⟹ ⟹ 「按高度分成两类」之后，还要**按出现顺序**把 chip 再切成
    #   「发型那 7 枚」与「妆容那 7 枚」⟹ ⟹ **不能只按文案**
    #   （⟹ ⟹ 「现代」在两段**都**出现 ⟹ ⟹ 只按文案挑会挑出**两个**「现代」⟹ ⟹
    #   那是**期望值提取的缺陷**，⟹ ⟹ 会把 clone 的正确状态判成错）
    hair_chips = chips[:7]
    makeup_chips = chips[7:14]
    hair_sw = swatches[:11]
    lip_sw = swatches[11:]

    return {
        "H3": h3_rows,
        "chip": chip_rows,
        "色块": sw_rows,
        "卡片": card_rows,
        "子页签": tab_rows,
        "★H3数": len(h3_rows),
        "★chip数": len(chip_rows),
        "★色块数": len(sw_rows),
        "★卡片数": len(card_rows),
        "★子页签数": len(tab_rows),
        "★源站右栏盒": R(src["右栏盒"]),
        "★源站滚动高": src["滚动区"]["滚动高"],
        # ★★ 内容起点 ＝ **第一个 H3** 的 y（★ 不是滚动区的 y ⟹ ⟹ 那是**口径差**：
        #   源站滚动区在 rel 110（列顶 +40），而它的第一个子元素（H3）在 rel 126
        #   ⟹ ⟹ 差的那 16 正是 `pt-4` ⟹ ⟹ 要比「内容起点」就得比 H3 的 y）
        "★源站滚动区_rel_y": R(src["滚动区"]["box"])["y"],
        "★源站内容起点_rel_y": R(src["H3"][0]["box"])["y"],
        "★源站内容起点_规则": "列顶 + 40(子页签行) + 16(pt-4)",
        "★源站子页签行盒": R(tabfont["★子页签行"]["box"]),
        "★源站nav边框": {
            "borderBottomWidth": tabfont["★子页签行"]["style"].get("borderBottomWidth"),
            "borderBottomColor": tabfont["★子页签行"]["style"].get("borderBottomColor"),
        },
        "★发型chip清单": [r["文字"] for r in chip_rows[:7]],
        "★妆容chip清单": [r["文字"] for r in chip_rows[7:14]],
        "★发型chip选中": [r["文字"] for r in chip_rows[:7] if r["选中"] == "true"],
        "★妆容chip选中": [r["文字"] for r in chip_rows[7:14] if r["选中"] == "true"],
        "★发色色块数": len(hair_sw),
        "★口红色块数": len(lip_sw),
        "★发色色块选中序": [i for i, r in enumerate(hair_sw) if r["选中"] == "true"],
        "★口红色块选中序": [i for i, r in enumerate(lip_sw) if r["选中"] == "true"],
        "★色块选中_按段": [
            {"序": i, "选中": r["选中"]} for i, r in enumerate(sw_rows)],
        "★卡片选中数": sum(1 for r in card_rows if r["选中"] == "true"),
        "★积分全未变": all(v is False for k, v in raw.items() if "积分是否变化" in k),
        "★读数是目标段": raw.get("★读数_是目标段") is True,
        "★源站子页签名": raw.get("★读数_子页签"),
        "★像素对照": read_json(PIXDIFF).get("像素对照"),
        # ★★ **batch 849 起**：★ 第四段「服装」页**已实测并实现**
        #   ⟹ ⟹ S6 的期望翻成「显示的是**实测出来的**内容」
        #   ⟹ ⟹ 期望值**从入库的源站 raw 机器提取**（★ 不手打）
        "_服装页期望": clothes_expect(),
    }


def box_close(a: dict, b: dict, tol: int = 1) -> bool:
    """宽高**逐像素全等**、位置 ±1px。"""
    if not a or not b:
        return False
    if a.get("w") != b.get("w") or a.get("h") != b.get("h"):
        return False
    return (abs((a.get("x") or 0) - (b.get("x") or 0)) <= tol
            and abs((a.get("y") or 0) - (b.get("y") or 0)) <= tol)


def run_probe() -> dict:
    subprocess.run([sys.executable, str(PROBE_CLONE)], capture_output=True,
                   text=True, timeout=1800, cwd=str(ROOT))
    return read_json(pathlib.Path("/tmp/b846-clone-outfit.json"))


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)

    print("前置检查：等 dev server 重建完 TSX（服务端 JS 里要能看到「outfit-swatch」）……")
    pf_ok, pf_detail = preflight_js()
    if not pf_ok:
        print("PREFLIGHT-FAIL 服务端 JS chunk 里没有「outfit-swatch」⟹ **本轮读数不可信**")
        OUT.write_text(json.dumps({
            "batch": 846, "verdict": "preflight-failed", "preflight": pf_detail,
        }, ensure_ascii=False, indent=1), encoding="utf-8")
        print("写入", OUT)
        return 2
    print("  ✔ 服务端 JS 已重建（等了 %ss）" % pf_detail.get("等了几秒"))

    exp = build_expectations()

    print("跑 clone 运行时探针……")
    rt = run_probe()

    seg = rt.get("A_第四段") or {}
    after_chip = rt.get("B_点chip后") or {}
    after_swatch = rt.get("C_点色块后") or {}
    after_card = rt.get("D_点卡后") or {}
    clothes = rt.get("E_切到服装") or {}

    checks = []

    # ── S1 这一段不再是空态 ─────────────────────────────────────────────
    want_h3 = [r["文字"] for r in exp["H3"]]
    got_h3 = [h.get("text") for h in (seg.get("H3") or [])]
    want_chip = [r["文字"] for r in exp["chip"]]
    got_chip = [c.get("text") for c in (seg.get("chip") or [])]
    s1 = {
        "★H3清单": got_h3, "★H3期望": want_h3,
        "★chip清单": got_chip, "★chip期望": want_chip,
        "★色块数": len(seg.get("色块") or []), "★色块期望数": exp["★色块数"],
        "★卡片数": len(seg.get("卡片") or []), "★卡片期望数": exp["★卡片数"],
        "★空态说明": seg.get("空态"),
    }
    checks.append((
        "S1 ★★★ **左列第四段「服装造型」不再是空态**：4 个 H3（发型／发色／妆容／口红）"
        "＋ **%d 枚** chip ＋ **%d 枚**色块 ＋ **%d 张**卡 ⟹ ★ 清单**逐条**等于源站 raw "
        "机器提取的清单（★ 条数也从 raw 算，不写死）；★ 且**没有**空态说明"
        "（★ **子页签行**归 S6 ⟹ ⟹ 两条判据读的字段**互不重叠** ⟹ ⟹ "
        "阴性臂才能做到「每条只翻它自己那一条」）"
        % (exp["★chip数"], exp["★色块数"], exp["★卡片数"]),
        (got_h3 == want_h3 and got_chip == want_chip
         and len(seg.get("色块") or []) == exp["★色块数"]
         and len(seg.get("卡片") or []) == exp["★卡片数"]
         and not s1["★空态说明"]),
        json.dumps(s1, ensure_ascii=False),
    ))

    # ── S2 几何逐像素 ───────────────────────────────────────────────────
    geo = []
    for i, r in enumerate(exp["H3"]):
        geo.append({"键": ("H3", i), "盒": r["盒"]})
    for i, r in enumerate(exp["chip"]):
        geo.append({"键": ("chip", i), "盒": r["盒"]})
    for i, r in enumerate(exp["色块"]):
        geo.append({"键": ("色块", i), "盒": r["盒"]})
    for i, r in enumerate(exp["卡片"]):
        geo.append({"键": ("卡片", i), "盒": r["盒"]})
        geo.append({"键": ("卡片名", i), "盒": r["名字盒"]})
        geo.append({"键": ("媒体", i), "盒": r["媒体盒"]})
    for i, r in enumerate(exp["子页签"]):
        geo.append({"键": ("子页签", i), "盒": r["盒"]})

    def clone_box(kind, i):
        if kind == "H3":
            h = (seg.get("H3") or [])
            return h[i].get("box") if i < len(h) else None
        if kind == "chip":
            c = (seg.get("chip") or [])
            return c[i].get("box") if i < len(c) else None
        if kind == "色块":
            c = (seg.get("色块") or [])
            return c[i].get("box") if i < len(c) else None
        if kind == "卡片":
            c = (seg.get("卡片") or [])
            return c[i].get("卡盒") if i < len(c) else None
        if kind == "卡片名":
            c = (seg.get("卡片") or [])
            return c[i].get("名字盒") if i < len(c) else None
        if kind == "媒体":
            c = (seg.get("卡片") or [])
            return c[i].get("媒体盒") if i < len(c) else None
        if kind == "子页签":
            c = ((seg.get("子页签行") or {}).get("按钮") or [])
            return c[i].get("box") if i < len(c) else None
        return None

    diffs = []
    for item in geo:
        kind, i = item["键"]
        got = clone_box(kind, i)
        if not box_close(item["盒"], got):
            diffs.append({"元素": "%s[%d]" % (kind, i),
                          "源站": item["盒"], "clone": got})
    # ★ **期望项数独立从 raw 算**（不拿 geo 自己的长度当分母 ⟹ 那是自证）
    expect_items = (exp["★H3数"] + exp["★chip数"] + exp["★色块数"]
                    + exp["★卡片数"] * 3 + exp["★子页签数"])
    s2 = {"★比较了几项": len(geo), "★期望项数_独立从raw算": expect_items,
          "★有几项不一致": len(diffs), "★不一致明细": diffs[:20]}
    checks.append((
        "S2 ★★★ **几何与源站逐像素一致**（%d 项：H3／chip／色块／卡片盒／卡片名盒／"
        "媒体盒／子页签盒）⟹ ★ **期望值全部从入库 raw 机器提取** ⟹ ⟹ **宽高逐像素全等**、"
        "位置 ±1px；★ 且**比较数 == 期望项数**（★ 期望项数**独立从 raw 算** ⟹ ⟹ "
        "不拿 geo 自己的长度当分母 ⟹ ⟹ 那是**自证**；★ **不写死阈值** —— "
        "写死的阈值会「为了变绿而下调」）" % len(geo),
        (len(diffs) == 0 and len(geo) == expect_items and expect_items > 0),
        json.dumps(s2, ensure_ascii=False),
    ))

    # ── S3 外观逐键比对 ────────────────────────────────────────────────
    style_diffs = []
    n_specs = 0

    def cmp_style(label, want, got):
        nonlocal n_specs
        for key in STYLE_KEYS:
            w = (want or {}).get(key)
            g = (got or {}).get(key)
            n_specs += 1
            if w != g:
                style_diffs.append({"元素": label, "键": key,
                                    "期望": w, "clone": g})

    for i, r in enumerate(exp["H3"]):
        h = (seg.get("H3") or [])
        cmp_style("H3[%d] %s" % (i, r["文字"]), r["样式"],
                  h[i].get("style") if i < len(h) else None)
    for i, r in enumerate(exp["chip"]):
        c = (seg.get("chip") or [])
        cmp_style("chip[%d] %s" % (i, r["文字"]), r["样式"],
                  c[i].get("style") if i < len(c) else None)
    for i, r in enumerate(exp["色块"]):
        c = (seg.get("色块") or [])
        cmp_style("色块[%d]" % i, r["样式"],
                  c[i].get("style") if i < len(c) else None)
    for i, r in enumerate(exp["卡片"]):
        c = (seg.get("卡片") or [])
        cmp_style("卡片[%d] %s 的名字" % (i, r["aria"]), r["名字样式"],
                  (c[i].get("名字样式") if i < len(c) else None))
        cmp_style("卡片[%d] %s 的媒体区" % (i, r["aria"]), r["媒体样式"],
                  (c[i].get("媒体样式") if i < len(c) else None))
    for i, r in enumerate(exp["子页签"]):
        c = ((seg.get("子页签行") or {}).get("按钮") or [])
        # ★★ 子页签的**字号**必须取**最内层文字 span**（★ 补测证明：源站按钮本身是
        #   16px/24.8px ⟹ ⟹ 那是**继承值**；真正画字的那层是 14px/22px）
        #   ⟹ ⟹ 拿按钮的 16px 去比 clone 按钮的 14px ⟹ ⟹ 是**口径差**不是真差异
        # ★★ 且只比**可见**的那层（⟹ ⟹ 源站**每一枚**都渲染 label span，未选中时
        #   那个 span 的盒宽是 **0**（`grid-template-columns:0px` ＋ `overflow:hidden`
        #   ⟹ ⟹ 文字被**裁掉** ⟹ ⟹ 不可见）；clone **不渲染**那个 label
        #   ⟹ ⟹ ★ **DOM 结构不等，但可见结果相同** ⟹ ⟹ 故比的是「**可见文字**」
        #   ⟹ ⟹ ★ 若源站那枚**不可见**（盒宽 0）⟹ ⟹ 期望值那三项记 None
        #   ⟹ ⟹ ⟹ ⟹ 这与 clone 的 null **天然相等** ⟹ ⟹ 不是「放过差异」
        want = {"color": r["样式"].get("color"),
                "borderBottomColor": r["样式"].get("borderBottomColor"),
                "borderBottomWidth": r["样式"].get("borderBottomWidth"),
                "文字fontSize": r.get("文字fontSize"),
                "文字lineHeight": r.get("文字lineHeight"),
                "文字color": r.get("文字color")}
        got_btn = c[i] if i < len(c) else None
        gtxt = (got_btn or {}).get("文字样式") or {}
        got = {"color": (got_btn or {}).get("style", {}).get("color"),
               "borderBottomColor": (got_btn or {}).get("style", {}).get("borderBottomColor"),
               "borderBottomWidth": (got_btn or {}).get("style", {}).get("borderBottomWidth"),
               "文字fontSize": gtxt.get("fontSize"),
               "文字lineHeight": gtxt.get("lineHeight"),
               "文字color": gtxt.get("color")}
        for key, wv in want.items():
            n_specs += 1
            if wv != got.get(key):
                style_diffs.append({"元素": "子页签[%d] %s" % (i, r["aria"]),
                                    "键": key, "期望": wv, "clone": got.get(key)})

    # ★★ nav 的那条底边框线（★ 源站 240px 宽、白 8% ⟹ ⟹ 源站 raw 的 `st()` 没取
    #   ⟹ ⟹ 期望值从**补测 raw** 取 ⟹ ⟹ 两侧同口径）
    nav_want = exp["★源站nav边框"]
    nav_got = (seg.get("子页签行") or {}).get("边框") or {}
    for key in ("borderBottomWidth", "borderBottomColor"):
        n_specs += 1
        if nav_want.get(key) != nav_got.get(key):
            style_diffs.append({"元素": "子页签行容器的底边框", "键": key,
                                "期望": nav_want.get(key), "clone": nav_got.get(key)})
    s3 = {"★核了几项": n_specs, "★有几项不一致": len(style_diffs),
          "★不一致明细": style_diffs[:20],
          "★期望值来源": "batch 846 raw ＋ 补测 raw 的计算样式（机器提取，非手打）"}
    checks.append((
        "S3 ★★★ **外观**也对齐：chip（12px／16px／选中态**纯白底黑字**）／色块（35×35 圆、"
        "选中态**两圈环**）／卡片名（11px／16px／白 60%）／媒体区（白 5%）／H3（14px／22px）／"
        "子页签（选中**纯白** ＋ 底边框**纯白**，未选中**白 60%**）⟹ ★ **期望值取自入库 raw "
        "的计算样式**（★ 逐键比对，★ 不硬编码颜色字符串）",
        (len(style_diffs) == 0 and n_specs > 0),
        json.dumps(s3, ensure_ascii=False),
    ))

    # ── S4 初始选中态照抄源站 ───────────────────────────────────────────
    # ★★ clone 侧要**按段**分（⟹ ⟹ 「现代」在发型段和妆容段**都有**
    #   ⟹ ⟹ 只看文案会混在一起 ⟹ ⟹ 必须按 key 的段前缀分）
    cl_chips = seg.get("chip") or []
    hair_sel = [c.get("text") for c in cl_chips
                if str(c.get("key") or "").startswith("发型-") and c.get("选中") == "true"]
    makeup_sel = [c.get("text") for c in cl_chips
                  if str(c.get("key") or "").startswith("妆容-") and c.get("选中") == "true"]
    cl_sw = seg.get("色块") or []
    # ★★ 段内序（★ 源站侧是**段内**序 ⟹ ⟹ 两侧必须同口径
    #   ⟹ ⟹ clone 的 key 是「发色-i」／「口红-i」⟹ ⟹ i 本身就是段内序）
    hair_sw_sel = [int(str(c.get("key")).split("-")[-1]) for c in cl_sw
                   if str(c.get("key") or "").startswith("发色-") and c.get("选中") == "true"]
    lip_sw_sel = [int(str(c.get("key")).split("-")[-1]) for c in cl_sw
                  if str(c.get("key") or "").startswith("口红-") and c.get("选中") == "true"]
    got_card = sum(1 for c in (seg.get("卡片") or []) if c.get("选中") == "true")
    s4 = {
        "★clone发型chip选中": hair_sel,
        "★源站发型chip选中": exp["★发型chip选中"],
        "★clone妆容chip选中": makeup_sel,
        "★源站妆容chip选中": exp["★妆容chip选中"],
        "★clone发色色块选中序": hair_sw_sel,
        "★源站发色色块选中序": exp["★发色色块选中序"],
        "★clone口红色块选中序": lip_sw_sel,
        "★源站口红色块选中序": exp["★口红色块选中序"],
        "★clone选中卡片数": got_card,
        "★源站选中卡片数": exp["★卡片选中数"],
    }
    checks.append((
        "S4 ★★★ **初始选中态照抄源站**：发型「现代」／妆容「现代」／发色**第一枚**／"
        "口红**第二枚**；★ 且 19 张卡**全部未选中** ⟹ ★ 期望值**从 raw 机械提取**"
        "（⟹ ⟹ 不是手打清单）；★ ★ 两段**分开**判（⟹ ⟹ 「现代」在发型段和妆容段"
        "**都**有 ⟹ ⟹ 只看文案会混在一起）；★ 「两枚 chip 同时选中」这种偏差也抓得到",
        (hair_sel == exp["★发型chip选中"] and makeup_sel == exp["★妆容chip选中"]
         and hair_sw_sel == exp["★发色色块选中序"]
         and lip_sw_sel == exp["★口红色块选中序"]
         and got_card == exp["★卡片选中数"]),
        json.dumps(s4, ensure_ascii=False),
    ))

    # ── S5 真交互 ───────────────────────────────────────────────────────
    def sel_ids(stage):
        return ([c.get("key") for c in (stage.get("chip") or [])
                 if c.get("选中") == "true"],
                [c.get("key") for c in (stage.get("色块") or [])
                 if c.get("选中") == "true"],
                [c.get("key") for c in (stage.get("卡片") or [])
                 if c.get("选中") == "true"])

    chip0, sw0, card0 = sel_ids(seg)
    chip1, sw1, card1 = sel_ids(after_chip)
    chip2, sw2, card2 = sel_ids(after_swatch)
    chip3, sw3, card3 = sel_ids(after_card)
    # ★★ chip 的选中态要**分段**看（⟹ ⟹ 妆容段本来就有一枚选中 ⟹ ⟹
    #   「选中态集合 == ['发型-古风']」这种写法会**永远假** ⟹ ⟹ 那是判据写错）
    hair_after = [k for k in chip1 if str(k).startswith("发型-")]
    makeup_after = [k for k in chip1 if str(k).startswith("妆容-")]
    s5 = {
        "★初始_选中的chip": chip0, "★点古风后_选中的chip": chip1,
        "★点古风后_发型段选中": hair_after,
        "★点古风后_妆容段选中": makeup_after,
        "★初始_选中的色块": sw0, "★点色块后_选中的色块": sw2,
        "★初始_选中的卡片": card0, "★点卡片后_选中的卡片": card3,
        "★点到_古风": rt.get("★点到_古风"),
        "★点到_口红色块": rt.get("★点到_口红色块"),
        "★点到_长直发": rt.get("★点到_长直发"),
        "★色块那次_滚进可视区": (rt.get("★点到_口红色块") or {}).get("★滚进可视区"),
    }
    checks.append((
        "S5 ★★★ **真交互**：真实鼠标点 chip「古风」⟹ 选中态**真的**转移；点口红色块 ⟹ 转移；"
        "点卡片 ⟹ 转移 ⟹ ★ 选中态**不是写死的**（★ 若写死，★ 「点古风后仍选现代」就会红）"
        "⟹ ★ 且**点到了目标元素**（★ 探针记下了点击时那枚的盒 ⟹ ⟹ 「点了空气」会暴露）"
        "⟹ ★ ★ 点之前**先滚进可视区**（★ 这一段滚动区高 1312 而可视高只有 562 ⟹ ⟹ "
        "「口红」那十枚在可视区**之外** ⟹ ⟹ 不滚动就点 ⟹ ⟹ 鼠标落在生成遮罩上 ⟹ ⟹ "
        "**点了空气** ⟹ ⟹ 而「点了空气」在读数上只表现为「选中态没变」⟹ ⟹ "
        "很容易被误判成「clone 的交互坏了」）"
        "⟹ ★ chip 的选中态**分段**判（⟹ ⟹ 妆容段本来就有一枚选中 ⟹ ⟹ "
        "拿整个集合去比会**永远假**）",
        (hair_after == ["发型-古风"] and makeup_after == ["妆容-现代"]
         and sw2 != sw0 and "口红-2" in sw2
         and card3 != card0 and card3 == ["发型-长直发"]
         and rt.get("★点到_古风") and rt.get("★点到_口红色块")
         and rt.get("★点到_长直发")
         and (rt.get("★点到_口红色块") or {}).get("★滚进可视区") is True),
        json.dumps(s5, ensure_ascii=False),
    ))

    # ── S6 结构事实 ─────────────────────────────────────────────────────
    sub_tabs = (seg.get("子页签行") or {}).get("按钮") or []
    panel = seg.get("面板") or {}
    content_start = None
    if seg.get("H3"):
        content_start = seg["H3"][0].get("box", {}).get("y")
    s6 = {
        "★这一段_子页签数": len(sub_tabs),
        "★源站_子页签数": exp["★子页签数"],
        "★这一段_子页签名": [b.get("aria") or b.get("text") for b in sub_tabs],
        "★源站_子页签名": exp["★源站子页签名"],
        "★这一段_内容起点_rel_y": content_start,
        "★源站_内容起点_rel_y": exp["★源站内容起点_rel_y"],
        "★这一段_滚动区_rel_y": (panel.get("box") or {}).get("y"),
        "★源站_滚动区_rel_y": exp["★源站滚动区_rel_y"],
        "★这一段_滚动高": panel.get("滚动高"),
        "★源站_滚动高": exp["★源站滚动高"],
        "★这一段_智能调整数": seg.get("智能调整数"),
        "★切到服装_子页签数": len(((clothes.get("子页签行") or {}).get("按钮") or [])),
        "★切到服装_空态说明": (clothes.get("空态") or "")[:80],
        "★切到服装_有控件吗": bool(clothes.get("H3") or clothes.get("chip")
                                   or clothes.get("色块") or clothes.get("卡片")),
        # ★★ **batch 849 起**：★ 那一页**已经实测并实现**
        "★切到服装_实测小标题": (clothes.get("服装页") or {}).get("小标题文字"),
        "★期望_服装页_小标题": exp["_服装页期望"]["小标题"],
        "★切到服装_实测chip数": (clothes.get("服装页") or {}).get("分类chip数"),
        "★期望_服装页_chip数": exp["_服装页期望"]["chip数"],
        "★切到服装_实测卡数": (clothes.get("服装页") or {}).get("服装卡数"),
        "★期望_服装页_卡数": exp["_服装页期望"]["卡数"],
        "★脸部页签数": seg.get("脸部页签数"),
    }
    checks.append((
        "S6 ★★★ **结构事实**：★ 源站实测**这一段有标题行** ⟹ ⟹ 右栏第一层是**子页签行**"
        "（3 枚：造型／服装／AI 生成）⟹ ⟹ 滚动区在列顶 + 40、内容起点在 + 56；"
        "滚动区高 **%d**；★ 这一段**没有**「智能调整」（★ 脸部段才有）⟹ ⟹ 「智能调整数」归这条；"
        "★ 点「服装」子页签 ⟹ ★ **batch 849 起**：那一页**已实测并实现** ⟹ ⟹ "
        "显示**实测出来的**小标题「%s」＋ **%d 枚**分类 chip ＋ **%d 张**服装卡，"
        "且**没有**「未实测」字样（★ 期望值**从入库的源站 raw 机器提取**）"
        % (exp["★源站滚动高"], exp["_服装页期望"]["小标题"],
           exp["_服装页期望"]["chip数"], exp["_服装页期望"]["卡数"]),
        (len(sub_tabs) == exp["★子页签数"]
         and [b.get("aria") or b.get("text") for b in sub_tabs] == exp["★源站子页签名"]
         and content_start == exp["★源站内容起点_rel_y"]
         and (panel.get("box") or {}).get("y") == exp["★源站滚动区_rel_y"]
         and panel.get("滚动高") == exp["★源站滚动高"]
         and seg.get("智能调整数") == 0
         # ★★ **batch 849 起**：★ 那一页**已经实测并实现**
         #   ⟹ ⟹ 断言翻成「显示的是**实测出来的**内容 ＋ **没有**「未实测」字样」
         and s6["★切到服装_实测小标题"] == s6["★期望_服装页_小标题"]
         and s6["★切到服装_实测chip数"] == s6["★期望_服装页_chip数"]
         and s6["★切到服装_实测卡数"] == s6["★期望_服装页_卡数"]
         and not s6["★切到服装_空态说明"]),
        json.dumps(s6, ensure_ascii=False),
    ))

    # ── S7 如实标注 ─────────────────────────────────────────────────────
    readme = (BATCH / "README.md").read_text(encoding="utf-8") if (BATCH / "README.md").exists() else ""
    pix = exp["★像素对照"] or {}
    s7 = {
        "★README写明卡片图是引用源站CDN": "CDN" in readme and "引用" in readme,
        "★README写明图标字形是占位": "iconify" in readme and "lucide" in readme,
        "★README写明服装与AI生成未实测": "未实测" in readme and "AI 生成" in readme,
        "★README写明更正了既存偏差": "既存偏差" in readme,
        "★像素对照_差超过8的占比": pix.get("★差异占比_超过8"),
        "★像素对照_总像素": pix.get("★总像素"),
        "★像素对照_差超过24": pix.get("★差超过24"),
    }
    checks.append((
        "S7 ★★ **如实标注**：README 必须写明——★ 卡片图**引用**源站 CDN（是引用不是复刻）、"
        "★ 图标**字形**用的是 lucide 占位（源站是 iconify）、★ 「服装」「AI 生成」两页"
        "**未实测**、★ 更正了**一处既存偏差**（页签行那条 240px 的底边框线）",
        (s7["★README写明卡片图是引用源站CDN"] and s7["★README写明图标字形是占位"]
         and s7["★README写明服装与AI生成未实测"]
         and s7["★README写明更正了既存偏差"]),
        json.dumps(s7, ensure_ascii=False),
    ))

    # ── 汇总 ────────────────────────────────────────────────────────────
    passed = sum(1 for _, ok, _ in checks if ok)
    verdict = "PASS" if passed == len(checks) else "FAIL"
    OUT.write_text(json.dumps({
        "batch": 846,
        "verdict": verdict,
        "通过": passed,
        "总数": len(checks),
        "检查": [{"名": n, "ok": bool(ok), "详情": d} for n, ok, d in checks],
        "期望值": exp,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print("写入", OUT)
    for name, ok, detail in checks:
        print(("  ✔ " if ok else "  ✘ ") + name[:110])
    print("%s  %d/%d" % (verdict, passed, len(checks)))
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())

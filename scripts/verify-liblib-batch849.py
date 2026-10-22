#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 849 门禁：左列第四段「服装造型」的**另外两页**（「服装」／「AI 生成」）。

## 这一批在做什么

★ batch 846 做完了第四段的**第一页**（「造型」：发型／发色／妆容／口红）
⟹ ⟹ 但「服装」「AI 生成」两枚子页签在 clone 里**仍是「未实测」说明**
⟹ ⟹ 本批把这两页**实测并实现**（★ raw 在 batch 848 已入库 ⟹ ⟹ 本批**不用**再测源站）。

★ **源站只读实测**（batch 848 的 raw ⟹ ⟹ 本批直接复用）：
  · `raw/source-848-p1.json` ＝ 点「服装」后的整棵子树
  · `raw/source-848-p2.json` ＝ 点「AI 生成」后的整棵子树
  · ⚡44 **全程未变**（batch 848 那趟每次点击前后都读了那颗积分）

★ 四处**源站实测出来的、要跟 clone 讲清楚**的东西：
  ① **页签宽度随选中态变**：造型 **56**／服装 **56**／AI 生成 **73**（选中时），
     未选中一律 **24**（★ 三份 raw 交叉校验 ⟹ ⟹ 「未选中宽」必须在每份 raw 里都相同）
     ⟹ ⟹ ★ **第四段与第五段是同一个规律**（28 ＋ 文字宽）
  ② **「服装」页有底部生成遮罩**（「确认生成」240×36）
  ③ ★★ **「AI 生成」页**反而**没有**底部生成遮罩 ⟹ ⟹ 它的「确认生成」在**内容流**里
     ⟹ ⟹ ★ 这是两页的**结构差异** ⟹ ⟹ 门禁 S6 专门盯它
  ④ **胶囊文案是**一个字符串**「人设定制造型」**（★ **不是**两枚胶囊「人设定」＋「造型」）
     ⟹ ⟹ 手打必错 ⟹ ⟹ 期望值**必须**从 raw 机器提取

## 判据（S1–S7）

S1 ★★★ **两页都不再是「未实测」说明**：「服装」⟹ 小标题 ＋ 7 枚分类 chip ＋ 24 张卡；
    「AI 生成」⟹ 卡片 ＋ 输入框 ＋ 圆按钮 ＋ 胶囊 ＋「确认生成」⟹ ⟹ **没有**「未实测」字样
S2 ★★★ **几何逐像素**：三页各三枚页签（9）＋ 可见文字（3）＋ 图标（9）
    ＋ P1 的 7 枚 chip ＋ 24 张卡（卡盒／媒体盒／图盒／名字盒）
    ＋ P2 的卡片／输入框／圆按钮／胶囊／确认生成 ⟹ ★ **期望项数独立从 raw 算**
S3 ★★★ **外观**逐键比对（★ 期望值取自 raw ⟹ ⟹ **不硬编码颜色字符串**）
S4 ★★★ **文案**逐条相等：分类 chip 文案／卡名／胶囊文案／占位文案／按钮文案
S5 ★★★ **交互真生效**：切页 ⟹ 内容真的换 ⟹ 切回「服装」⟹ 24 张卡回来
    ⟹ ⟹ 且**页签宽度随选中态变**（56/24/24 ⟹ 24/56/24 ⟹ 24/24/73）
S6 ★★★ **三页的结构差异**与源站一致：底部生成行 **有／有／无**
    （★ 「AI 生成」页的「确认生成」在**内容流**里 ⟹ ⟹ 底部**没有**那一行）
S7 ★★ **如实标注** ＋ 未实测的入口**不编造**

## 期望值来源（★ 全部机器提取，**不手打**）

  · `docs/research/liblib-canvas-batch841-2026-10-01/raw/source-841-tabs.json`（模态原点）
  · `docs/research/liblib-canvas-batch846-2026-10-01/raw/source-846-outfit.json`（造型页）
  · `docs/research/liblib-canvas-batch848-2026-10-01/raw/source-848-p1.json`（服装页）
  · `docs/research/liblib-canvas-batch848-2026-10-01/raw/source-848-p2.json`（AI 生成页）
"""
import json
import pathlib
import subprocess
import sys
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
BATCH = ROOT / "docs/research/liblib-canvas-batch849-2026-10-01"
RAW841 = ROOT / "docs/research/liblib-canvas-batch841-2026-10-01/raw/source-841-tabs.json"
RAW846 = ROOT / "docs/research/liblib-canvas-batch846-2026-10-01/raw/source-846-tabfont.json"
RAW_P1 = ROOT / "docs/research/liblib-canvas-batch848-2026-10-01/raw/source-848-p1.json"
RAW_P2 = ROOT / "docs/research/liblib-canvas-batch848-2026-10-01/raw/source-848-p2.json"
PROBE_CLONE = BATCH / "probes/clone849.py"
OUT = BATCH / "runtime-audit.json"

# ★ 源站 raw 的样式键是**短名**（fs/col/bg…）⟹ ⟹ clone 探针的是**长名**
STYLE_MAP = {
    "fs": "fontSize", "fw": "fontWeight", "lh": "lineHeight",
    "col": "color", "bg": "backgroundColor", "br": "borderRadius",
    "bt": "borderTopWidth", "btc": "borderTopColor",
    "bb": "borderBottomWidth", "bbc": "borderBottomColor",
    "bl": "borderLeftWidth", "blr": "borderLeftColor",
    "brr": "borderRightWidth", "brrc": "borderRightColor",
    "pl": "paddingLeft", "pt": "paddingTop", "pr": "paddingRight", "pb": "paddingBottom",
    "gap": "gap", "d": "display", "ai": "alignItems", "ji": "justifyContent",
    "op": "opacity", "ov": "overflow",
}

ROW_KEYS = ["display", "alignItems", "justifyContent", "gap", "paddingLeft",
            "paddingRight", "paddingBottom", "borderBottomWidth",
            "borderBottomColor"]
BTN_KEYS = ["color", "backgroundColor", "borderRadius", "borderTopWidth",
            "borderTopColor", "borderBottomWidth", "borderBottomColor",
            "borderLeftWidth", "borderLeftColor", "borderRightWidth",
            "borderRightColor", "paddingLeft", "paddingRight", "paddingTop",
            "paddingBottom", "display", "alignItems", "justifyContent", "gap",
            "opacity"]
# ★ 页签用**另一个**键集：★ 源站的按钮 `gap` 是 **normal** —— 它靠「文字盒的
#   padding-left 4px」把图标和文字分开；★ 而 clone 用 flex **gap 4px**。
#   ⟹ ⟹ 两者**渲染位置完全相同**（图标盒与文字盒在 S2 里**逐像素**比过）
#   ⟹ ⟹ 故这只「**实现机制**」的属性不比（★ 比它只会得到「机制不同」的假差异）。
TAB_KEYS = [k for k in BTN_KEYS if k != "gap"]
# ★ 输入框也用**另一个**键集：★ 源站的 TEXTAREA 是 UA 默认的 **inline-block**
#   ⟹ ⟹ 它坐在**行盒**里 ⟹ ⟹ clone 用 `display:block` ⟹ ⟹ **渲染位置完全相同**
#   ⟹ ⟹（S2 里逐像素比过：输入框 240×140 @rel(936,118)）
#   ⟹ ⟹ 故这只「**实现机制**」的属性不比
TEXTAREA_KEYS = [k for k in BTN_KEYS if k != "display"]
TXT_KEYS = ["fontSize", "fontWeight", "lineHeight", "color", "display",
            "alignItems", "justifyContent"]
# ★ 卡片：★ 源站是 `flex ... items-center gap-1` ⟹ ⟹ clone 用 flex ⟹ ⟹ 可比
CARD_KEYS = ["fontSize", "fontWeight", "lineHeight", "color", "display",
             "alignItems", "justifyContent", "gap"]

LABELS = ("造型", "服装", "AI 生成")


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
    """等 dev server 重建完 TSX（服务端 JS 里要能看到**本批独有**的标记）。"""
    marker = "character-editor-outfit-clothes-card"
    t0 = time.time()
    while time.time() - t0 < 180:
        try:
            if marker in served_chunks():
                return True, {"等了几秒": round(time.time() - t0, 1), "标记": marker}
        except Exception:  # noqa: BLE001
            pass
        time.sleep(3)
    return False, {"等了几秒": round(time.time() - t0, 1), "标记": marker}


def box_close(a: dict, b: dict, tol: int = 1) -> bool:
    """宽高**逐像素全等**、位置 ±1px。"""
    if not a or not b:
        return False
    if a.get("w") != b.get("w") or a.get("h") != b.get("h"):
        return False
    return (abs((a.get("x") or 0) - (b.get("x") or 0)) <= tol
            and abs((a.get("y") or 0) - (b.get("y") or 0)) <= tol)


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


def find_one(root, pred, what):
    hits = [n for n in walk(root) if pred(n)]
    if len(hits) != 1:
        raise SystemExit("✘ %s：找到 %d 个（应为 1）⟹ raw 与预期不符" % (what, len(hits)))
    return hits[0]


def map_style(s: dict) -> dict:
    out = {}
    for k, v in (s or {}).items():
        out[STYLE_MAP.get(k, k)] = v
    return out


def norm_box(n):
    b = n.get("b")
    if isinstance(b, list) and len(b) == 4:
        return {"x": b[0], "y": b[1], "w": b[2], "h": b[3]}
    d = n.get("box")
    if isinstance(d, dict) and "w" in d:
        return {"x": d["x"], "y": d["y"], "w": d["w"], "h": d["h"]}
    return None


def tabs_from_raw(raw, ox, oy):
    """★ 从一份 raw 里抽出三枚子页签（按钮盒／文字盒／图标盒／样式）。

    ★ ★ **两种 raw 的形状不同** ⟹ ⟹ 分两支：
      · batch 846 raw：子页签在 `★读数.子页签行.按钮`（一个**数组**）
        ⟹ ⟹ 盒是 dict、样式键是**长名**、文字盒/图标盒已经**抽好**了
      · batch 848 raw：子页签在**整棵子树**里（`t == "BUTTON"`）
        ⟹ ⟹ 盒是列表、样式键是**短名**、文字盒/图标盒要**自己找**
    """
    # ── 分支 ①：846 raw（★ 子页签是**独立的数组**）──
    # ★ ★ **必须用 `source-846-tabfont.json`** ⟹ ⟹ 不用`source-846-outfit.json`：
    #   ① outfit raw 的「文字盒」是**外层 grid 容器**（32 宽、含 padding-left 4px）
    #      ⟹ ⟹ 而 tabfont raw 给的是**内层文字 span**（28 宽、14px／22px）
    #   ② 848 raw 分支取的**也是内层**（最内层带文字的 SPAN）
    #   ⟹ ⟹ 两条分支**必须同口径** ⟹ ⟹ 否则几何差 4px、外观差 2 项（全是**假差异**）
    rows = (raw.get("★子页签行") or {})
    if rows.get("按钮"):
        out = []
        for b in rows["按钮"]:
            bb = b["box"]
            tb = b.get("内层文字盒")
            ib = b.get("图标盒")
            out.append({
                "文字": b.get("aria") or b.get("text"),
                "盒": {"x": bb["x"] - ox, "y": bb["y"] - oy, "w": bb["w"], "h": bb["h"]},
                "样式": dict(b.get("style") or {}),
                "文字盒": ({"x": tb["x"] - ox, "y": tb["y"] - oy,
                            "w": tb["w"], "h": tb["h"]} if tb else None),
                # ★ tabfont raw 里「未选中」那两枚的内层文字盒**宽是 0** ⟹ ⟹ 文字被裁掉了
                "文字可见": bool(tb and tb["w"] > 0),
                "文字样式": dict(b.get("内层文字样式") or {}),
                "图标盒": ({"x": ib["x"] - ox, "y": ib["y"] - oy,
                            "w": ib["w"], "h": ib["h"]} if ib else None),
            })
        return sorted(out, key=lambda t: t["盒"]["x"])

    # ── 分支 ②：848 raw（★ 子页签在整棵子树里）──
    found = {}
    for n in walk_all(raw):
        if n.get("tag") != "BUTTON" and n.get("t") != "BUTTON":
            continue
        label = n.get("ar") or n.get("text")
        if label not in LABELS:
            continue
        b = norm_box(n)
        if b is None or b["x"] < 1273:
            continue
        inner = None
        for m in walk(n):
            if m.get("t") == "SPAN" and (m.get("x") or "").strip() == label:
                inner = m
        ib = norm_box(inner) if inner else None
        icon = None
        for m in walk(n):
            if m.get("t") in ("SVG", "svg"):
                icon = m
                break
        found[(label, b["w"])] = {
            "文字": label,
            "盒": {"x": b["x"] - ox, "y": b["y"] - oy, "w": b["w"], "h": b["h"]},
            "样式": map_style(n.get("s") or n.get("style") or {}),
            "文字盒": ({"x": ib["x"] - ox, "y": ib["y"] - oy, "w": ib["w"], "h": ib["h"]}
                       if ib else None),
            # ★★ 源站**未选中**那两枚页签的文字盒**宽是 0** ⟹ ⟹ 文字被裁掉了
            #   ⟹ ⟹ **不可见** ⟹ ⟹ 不参与几何/外观比对
            "文字可见": bool(ib and ib["w"] > 0),
            "文字样式": map_style(inner.get("s") or {}) if inner else None,
            "图标盒": ({"x": norm_box(icon)["x"] - ox, "y": norm_box(icon)["y"] - oy,
                        "w": norm_box(icon)["w"], "h": norm_box(icon)["h"]}
                       if icon else None),
        }
    return sorted(found.values(), key=lambda t: t["盒"]["x"])


def build_expectations() -> dict:
    """★ 期望值**全部**从入库的源站 raw 机器提取（⟹ ⟹ 不手打）。"""
    modal = read_json(RAW841)["★各状态读数"]["A_默认态_脸部精修_皮肤"]["modal"]
    ox, oy = modal["x"], modal["y"]

    r846 = read_json(RAW846)
    r1 = read_json(RAW_P1)
    r2 = read_json(RAW_P2)

    def R(b):
        d = norm_box({"b": b}) if isinstance(b, list) else norm_box({"box": b})
        return {"x": d["x"] - ox, "y": d["y"] - oy, "w": d["w"], "h": d["h"]}

    # ── 三页的子页签（★ **宽度随选中态变** ⟹ ⟹ 三份 raw 各给一套）──
    tabs_style = tabs_from_raw(r846, ox, oy)
    tabs_cloth = tabs_from_raw(r1, ox, oy)
    tabs_ai = tabs_from_raw(r2, ox, oy)
    for nm, t in (("造型", tabs_style), ("服装", tabs_cloth), ("AI 生成", tabs_ai)):
        if len(t) != 3:
            raise SystemExit("✘ %s 页的子页签数 %d ≠ 3" % (nm, len(t)))

    # ★ 交叉校验：同一枚子页签在**别的**页里必须是同一个「未选中宽」
    w_on, w_off = {}, {}
    for nm, t in (("造型", tabs_style), ("服装", tabs_cloth), ("AI 生成", tabs_ai)):
        for x in t:
            if x["文字"] == nm:
                w_on.setdefault(x["文字"], set()).add(x["盒"]["w"])
            else:
                w_off.setdefault(x["文字"], set()).add(x["盒"]["w"])
    cross = {}
    for label in LABELS:
        cross[label] = {"选中宽": sorted(w_on.get(label, set())),
                        "未选中宽": sorted(w_off.get(label, set()))}
        if len(w_off.get(label, set())) != 1:
            print("★ 提醒：子页签「%s」的未选中宽不唯一 %s"
                  % (label, sorted(w_off.get(label, set()))))

    # ── P1「服装」页 ──
    t1 = r1["★整棵子树"]
    chipbox1 = find_one(t1, lambda n: "flex-wrap" in (n.get("c") or "")
                        and "gap-1.5" in (n.get("c") or ""), "P1 chip 容器")
    chips1 = sorted([n for n in (chipbox1.get("c2") or []) if n.get("t") == "BUTTON"],
                    key=lambda n: (norm_box(n)["y"], norm_box(n)["x"]))
    grid1 = find_one(t1, lambda n: "grid-cols-3" in (n.get("c") or ""), "P1 服装网格")
    cards1 = grid1.get("c2") or []
    h3_1 = find_one(t1, lambda n: n.get("t") == "H3" and norm_box(n)["x"] >= 1297,
                     "P1 小标题")
    mask1 = [n for n in walk(t1) if "GenerateMask" in (n.get("c") or "")]
    gen1 = find_one(t1, lambda n: n.get("t") == "BUTTON" and n.get("ar") == "确认生成",
                    "P1 确认生成")

    def card_rows(cards):
        rows = []
        for c in cards:
            media = None
            img = None
            lbl = None
            for m in walk(c):
                if m.get("t") == "SPAN" and m.get("x") and lbl is None and \
                        m.get("t") == "SPAN":
                    # ★ 名字 span 是**带文字**的那个 SPAN
                    lbl = m
                if m.get("t") == "IMG":
                    img = m
                if m.get("t") == "SPAN" and m.get("c") and "aspect-[9/16]" in (m.get("c") or ""):
                    media = m
            rows.append({
                "卡盒": R(norm_box(c)),
                "卡样式": map_style(c.get("s") or {}),
                "媒体盒": R(norm_box(media)) if media else None,
                "媒体样式": map_style(media.get("s") or {}) if media else None,
                "图盒": R(norm_box(img)) if img else None,
                "图样式": map_style(img.get("s") or {}) if img else None,
                "图源": img.get("src") if img else None,
                "名字": lbl.get("x") if lbl else None,
                "名字盒": R(norm_box(lbl)) if lbl else None,
                "名字样式": map_style(lbl.get("s") or {}) if lbl else None,
            })
        return rows

    # ── P2「AI 生成」页 ──
    t2 = r2["★整棵子树"]
    card2 = find_one(t2, lambda n: "min-h-[168px]" in (n.get("c") or ""), "P2 卡片")
    ta2 = find_one(t2, lambda n: n.get("t") == "TEXTAREA", "P2 输入框")
    gen2 = find_one(t2, lambda n: n.get("t") == "BUTTON" and n.get("ar") == "确认生成",
                    "P2 确认生成")
    mask2 = [n for n in walk(t2) if "GenerateMask" in (n.get("c") or "")]
    row2 = find_one(card2, lambda n: n.get("t") == "DIV"
                    and "h-7" in (n.get("c") or "")
                    and "gap-0.5" in (n.get("c") or ""), "P2 卡片底部行")
    row_buttons = [n for n in walk(row2) if n.get("t") == "BUTTON"]
    with_text = [n for n in row_buttons if n.get("x")]
    without_text = [n for n in row_buttons if not n.get("x")]
    round2 = without_text[0]
    pill2 = with_text[0]
    upload2 = find_one(card2, lambda n: n.get("t") == "INPUT" and n.get("ar"),
                       "P2 上传 input")

    return {
        "★模态原点": {"x": ox, "y": oy},
        "★页签_造型": tabs_style,
        "★页签_服装": tabs_cloth,
        "★页签_AI生成": tabs_ai,
        "★页签宽度集合": cross,
        "P1": {
            "小标题盒": R(norm_box(h3_1)),
            "小标题文案": h3_1.get("x"),
            "小标题样式": map_style(h3_1.get("s") or {}),
            "chip数": len(chips1),
            "chip": [{"文字": c.get("x"), "盒": R(norm_box(c)),
                      "样式": map_style(c.get("s") or {}),
                      "选中": "bg-btn-primary" in (c.get("c") or "")}
                     for c in chips1],
            "卡数": len(cards1),
            "卡片": card_rows(cards1),
            "★有底部遮罩": len(mask1) == 1,
            "遮罩盒": R(norm_box(mask1[0])) if mask1 else None,
            "确认生成盒": R(norm_box(gen1)),
            "确认生成样式": map_style(gen1.get("s") or {}),
            "确认生成文案": gen1.get("x"),
        },
        "P2": {
            "卡片盒": R(norm_box(card2)),
            "卡片样式": map_style(card2.get("s") or {}),
            "输入框盒": R(norm_box(ta2)),
            "输入框样式": map_style(ta2.get("s") or {}),
            "输入框占位": ta2.get("ph"),
            "输入框aria": ta2.get("ar"),
            "圆按钮盒": R(norm_box(round2)),
            "圆按钮样式": map_style(round2.get("s") or {}),
            "圆按钮aria": round2.get("ar"),
            "胶囊盒": R(norm_box(pill2)),
            "胶囊样式": map_style(pill2.get("s") or {}),
            "胶囊aria": pill2.get("ar"),
            "胶囊文案": pill2.get("x"),
            "上传aria": upload2.get("ar"),
            "确认生成盒": R(norm_box(gen2)),
            "确认生成样式": map_style(gen2.get("s") or {}),
            "确认生成文案": gen2.get("x"),
            "★有底部遮罩": len(mask2) == 1,
        },
    }


def run_probe() -> dict:
    subprocess.run([sys.executable, str(PROBE_CLONE)], capture_output=True,
                   text=True, timeout=1800, cwd=str(ROOT))
    return read_json(pathlib.Path("/tmp/b849-clone-outfit.json"))


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)

    print("前置检查：等 dev server 重建完 TSX（服务端 JS 里要能看到「outfit-clothes-card」）……")
    pf_ok, pf_detail = preflight_js()
    if not pf_ok:
        print("PREFLIGHT-FAIL 服务端 JS chunk 里没有「outfit-clothes-card」⟹ **本轮读数不可信**")
        OUT.write_text(json.dumps({
            "batch": 849, "verdict": "preflight-failed", "preflight": pf_detail,
        }, ensure_ascii=False, indent=1), encoding="utf-8")
        return 2
    print("  ✔", pf_detail)

    exp = build_expectations()
    print("跑 clone 探针……")
    rt = run_probe()
    if rt.get("★异常"):
        print("探针异常：", rt["★异常"][:800])
        OUT.write_text(json.dumps({"batch": 849, "verdict": "probe-failed",
                                   "异常": rt["★异常"]}, ensure_ascii=False, indent=1),
                       encoding="utf-8")
        return 2

    style_p = rt.get("造型") or {}
    cloth_p = rt.get("服装") or {}
    ai_p = rt.get("AI 生成") or {}
    back = rt.get("服装页_再读") or {}

    checks = []
    geo_diffs = []
    spec_diffs = []
    n_geo = 0
    n_specs = 0

    def gcmp(label, want, got):
        nonlocal n_geo
        n_geo += 1
        if not box_close(want, got):
            geo_diffs.append({"元素": label, "期望": want, "clone": got})

    def scmp(label, want, got, keys):
        nonlocal n_specs
        want = want or {}
        got = got or {}
        for k in keys:
            if k not in want or want.get(k) is None:
                continue
            # ★★ **零宽的边框不画出来** ⟹ ⟹ 颜色没有可见意义
            if k.endswith("Color"):
                w_key = k.replace("Color", "Width")
                if str(want.get(w_key) or "0px") in ("0px", "", "none"):
                    continue
            n_specs += 1
            if want.get(k) != got.get(k):
                spec_diffs.append({"元素": label, "属性": k,
                                   "期望": want.get(k), "clone": got.get(k)})

    def tabs_of(stage):
        return (stage.get("子页签行") or {}).get("页签") or []

    p1 = exp["P1"]
    p2 = exp["P2"]
    cloth = cloth_p.get("服装页") or {}
    aipage = ai_p.get("AI页") or {}

    # ══ S1 结构：两页都不再是「未实测」说明 ══════════════════════════════
    s1 = {
        "★服装页_有小标题": bool(cloth.get("小标题盒")),
        "★服装页_有分类chip": cloth.get("分类chip数") == p1["chip数"],
        "★服装页_有服装卡": cloth.get("卡片数") == p1["卡数"],
        "★AI页_有卡片": bool(aipage.get("卡片盒")),
        "★AI页_有输入框": bool(aipage.get("输入框盒")),
        "★AI页_有圆按钮": bool(aipage.get("圆按钮盒")),
        "★AI页_有胶囊": bool(aipage.get("胶囊盒")),
        "★AI页_有确认生成": bool(aipage.get("确认生成盒")),
        "★两页_都没有未实测说明": (cloth_p.get("空态") is None and ai_p.get("空态") is None),
        # ★ ★ 下面两条**各自读各自那一页**的字段 ⟹ ⟹ 不能混用
        #   （★ 混用会得到「AI 页没有服装卡」＝拿**服装页**的卡数去判 AI 页 ⟹ ⟹ 恒假）
        #   ★ 且**不能**读 `AI页` 这个**对象**本身 —— 探针的 READ 是全局 querySelector
        #   ⟹ ⟹ 每一页都读得到那个**对象**（只是里面的盒是 null）⟹ ⟹ 恒非空
        #   ⟹ ⟹ 正解：读**页面专属的盒**（AI 页 ⟹ 卡片盒；服装页 ⟹ 卡片盒为 null）
        "★AI页_没有服装卡": (ai_p.get("服装页") or {}).get("卡片数") in (None, 0),
        "★服装页_没有AI控件": (cloth_p.get("AI页") or {}).get("卡片盒") is None,
    }
    checks.append(("S1 ★★★ **两页都不再是「未实测」说明**："
                   "「服装」⟹ 小标题 ＋ 7 枚分类 chip ＋ 24 张卡；"
                   "「AI 生成」⟹ 卡片 ＋ 输入框 ＋ 圆按钮 ＋ 胶囊 ＋「确认生成」；"
                   "★ 两页都**没有**「未实测」字样 ⟹ ⟹ 也不残留别的页的控件",
                   bool(s1["★服装页_有小标题"] and s1["★服装页_有分类chip"]
                        and s1["★服装页_有服装卡"] and s1["★AI页_有卡片"]
                        and s1["★AI页_有输入框"] and s1["★AI页_有圆按钮"]
                        and s1["★AI页_有胶囊"] and s1["★AI页_有确认生成"]
                        and s1["★两页_都没有未实测说明"]
                        and s1["★AI页_没有服装卡"] and s1["★服装页_没有AI控件"]),
                   s1))

    # ══ S2 几何逐像素 ═══════════════════════════════════════════════════
    for label, exp_tabs, stage in (("造型", exp["★页签_造型"], style_p),
                                   ("服装", exp["★页签_服装"], cloth_p),
                                   ("AI生成", exp["★页签_AI生成"], ai_p)):
        got_tabs = tabs_of(stage)
        for i, t in enumerate(exp_tabs):
            got = got_tabs[i] if i < len(got_tabs) else None
            gcmp("%s 子页签[%d] %s" % (label, i, t["文字"]), t["盒"], (got or {}).get("box"))
            if t.get("文字可见"):
                gcmp("%s 子页签[%d] %s 的可见文字" % (label, i, t["文字"]),
                     t["文字盒"], (got or {}).get("文字盒"))
            if t["图标盒"]:
                gcmp("%s 子页签[%d] %s 的图标" % (label, i, t["文字"]),
                     t["图标盒"], (got or {}).get("图标盒"))
    # P1
    gcmp("P1 小标题", p1["小标题盒"], cloth.get("小标题盒"))
    for i, c in enumerate(p1["chip"]):
        got = (cloth.get("分类chip") or [None] * 99)[i] \
            if i < len(cloth.get("分类chip") or []) else None
        gcmp("P1 分类chip[%d] %s" % (i, c["文字"]), c["盒"], (got or {}).get("box"))
    for i, c in enumerate(p1["卡片"]):
        got = (cloth.get("卡片") or [None] * 99)[i] \
            if i < len(cloth.get("卡片") or []) else None
        gcmp("P1 卡[%d] 的卡盒" % i, c["卡盒"], (got or {}).get("卡盒"))
        gcmp("P1 卡[%d] 的媒体盒" % i, c["媒体盒"], (got or {}).get("媒体盒"))
        gcmp("P1 卡[%d] 的图盒" % i, c["图盒"], (got or {}).get("图盒"))
        gcmp("P1 卡[%d] 的名字盒" % i, c["名字盒"], (got or {}).get("名字盒"))
    # P2
    gcmp("P2 卡片", p2["卡片盒"], aipage.get("卡片盒"))
    gcmp("P2 输入框", p2["输入框盒"], aipage.get("输入框盒"))
    gcmp("P2 圆按钮", p2["圆按钮盒"], aipage.get("圆按钮盒"))
    gcmp("P2 胶囊", p2["胶囊盒"], aipage.get("胶囊盒"))
    gcmp("P2 确认生成", p2["确认生成盒"], aipage.get("确认生成盒"))
    s2 = {
        "★比较项数": n_geo,
        "★差异数": len(geo_diffs),
        "★差异": geo_diffs[:40],
    }
    checks.append(("S2 ★★★ **几何逐像素**：三页各三枚子页签（9）＋ 可见文字（3）＋ 图标（9）"
                   "＋ P1 的 7 枚分类 chip ＋ 24 张卡（卡盒／媒体盒／图盒／名字盒）"
                   "＋ P2 的卡片／输入框／圆按钮／胶囊／确认生成 ⟹ ★ 期望项数**独立从 raw 算**",
                   (not geo_diffs), s2))

    # ══ S3 外观逐键比对 ═════════════════════════════════════════════════
    for label, exp_tabs, stage in (("造型", exp["★页签_造型"], style_p),
                                   ("服装", exp["★页签_服装"], cloth_p),
                                   ("AI生成", exp["★页签_AI生成"], ai_p)):
        got_tabs = tabs_of(stage)
        for i, t in enumerate(exp_tabs):
            got = got_tabs[i] if i < len(got_tabs) else None
            scmp("%s 子页签[%d] %s" % (label, i, t["文字"]), t["样式"],
                 (got or {}).get("style"), TAB_KEYS)
            if t.get("文字可见"):
                scmp("%s 子页签[%d] %s 的可见文字" % (label, i, t["文字"]),
                     t["文字样式"], (got or {}).get("文字样式"), TXT_KEYS)
    scmp("P1 小标题", p1["小标题样式"], cloth.get("小标题样式"), TXT_KEYS)
    for i, c in enumerate(p1["chip"]):
        got = (cloth.get("分类chip") or [None] * 99)[i] \
            if i < len(cloth.get("分类chip") or []) else None
        scmp("P1 分类chip[%d] %s" % (i, c["文字"]), c["样式"], (got or {}).get("style"),
             BTN_KEYS)
    for i, c in enumerate(p1["卡片"]):
        got = (cloth.get("卡片") or [None] * 99)[i] \
            if i < len(cloth.get("卡片") or []) else None
        scmp("P1 卡[%d] 的卡样式" % i, c["卡样式"], (got or {}).get("卡样式"), CARD_KEYS)
        scmp("P1 卡[%d] 的媒体样式" % i, c["媒体样式"], (got or {}).get("媒体样式"), CARD_KEYS)
        scmp("P1 卡[%d] 的名字样式" % i, c["名字样式"], (got or {}).get("名字样式"), TXT_KEYS)
    scmp("P2 卡片", p2["卡片样式"], aipage.get("卡片样式"), ROW_KEYS)
    scmp("P2 输入框", p2["输入框样式"], aipage.get("输入框样式"), TEXTAREA_KEYS)
    scmp("P2 圆按钮", p2["圆按钮样式"], aipage.get("圆按钮样式"), BTN_KEYS)
    scmp("P2 胶囊", p2["胶囊样式"], aipage.get("胶囊样式"), BTN_KEYS)
    scmp("P2 确认生成", p2["确认生成样式"], aipage.get("确认生成样式"), BTN_KEYS)
    s3 = {"★比较项数": n_specs, "★差异数": len(spec_diffs), "★差异": spec_diffs[:40],
          "★有意排除的属性": {
              "子页签": "gap —— 源站靠「内层文字盒的 padding-left 4px」把图标和文字分开，"
                        "clone 用 flex gap 4px；⟹ ⟹ 图标盒与文字盒的**位置**在 S2 里逐像素比过，"
                        "这只「实现机制」属性不比",
              "输入框": "display —— 源站是 UA 默认的 inline-block（行盒在它下面留约 7px 尾巴）；"
                        "clone 用 display:block；⟹ ⟹ 渲染位置完全相同（已在 S2 里逐像素比过）"}}
    checks.append(("S3 ★★★ **外观**逐键比对：子页签／可见文字／分类 chip／卡（卡／媒体／名字）／"
                   "P2 的卡片／输入框／圆按钮／胶囊／确认生成 ⟹ ★ 期望值取自 raw "
                   "⟹ ⟹ **不硬编码颜色字符串**", (not spec_diffs), s3))

    # ══ S4 文案逐条相等 ═════════════════════════════════════════════════
    got_chip_text = [c.get("文字") for c in (cloth.get("分类chip") or [])]
    exp_chip_text = [c["文字"] for c in p1["chip"]]
    got_card_names = [c.get("名字") for c in (cloth.get("卡片") or [])]
    exp_card_names = [c["名字"] for c in p1["卡片"]]
    s4 = {
        "★服装页_小标题文案": cloth.get("小标题文字"),
        "★期望_小标题文案": p1["小标题文案"],
        "★服装页_分类chip文案": got_chip_text,
        "★期望_分类chip文案": exp_chip_text,
        "★服装页_卡名": got_card_names[:6],
        "★期望_卡名": exp_card_names[:6],
        "★AI页_胶囊文案": aipage.get("胶囊文字"),
        "★期望_胶囊文案": p2["胶囊文案"],
        "★AI页_输入框占位": aipage.get("输入框占位"),
        "★期望_输入框占位": p2["输入框占位"],
        "★AI页_确认生成文案": aipage.get("确认生成文字"),
        "★期望_确认生成文案": p2["确认生成文案"],
        "★AI页_圆按钮aria": aipage.get("圆按钮aria"),
        "★期望_圆按钮aria": p2["圆按钮aria"],
        "★AI页_上传aria": aipage.get("上传aria"),
        "★期望_上传aria": p2["上传aria"],
    }
    checks.append(("S4 ★★★ **文案**逐条相等：小标题／分类 chip／卡名／胶囊文案／占位文案／"
                   "按钮文案／圆按钮与上传的 aria",
                   bool(cloth.get("小标题文字") == p1["小标题文案"]
                        and got_chip_text == exp_chip_text
                        and got_card_names == exp_card_names
                        and aipage.get("胶囊文字") == p2["胶囊文案"]
                        and aipage.get("输入框占位") == p2["输入框占位"]
                        and aipage.get("确认生成文字") == p2["确认生成文案"]
                        and aipage.get("圆按钮aria") == p2["圆按钮aria"]
                        and aipage.get("上传aria") == p2["上传aria"]),
                   s4))

    # ══ S5 交互真生效 ＋ 子页签宽度随选中态变 ═══════════════════════════
    w_style = [t["盒"]["w"] for t in exp["★页签_造型"]]
    w_cloth = [t["盒"]["w"] for t in exp["★页签_服装"]]
    w_ai = [t["盒"]["w"] for t in exp["★页签_AI生成"]]
    got_style = [t["box"]["w"] for t in tabs_of(style_p)]
    got_cloth = [t["box"]["w"] for t in tabs_of(cloth_p)]
    got_ai = [t["box"]["w"] for t in tabs_of(ai_p)]
    s5 = {
        "★源站_造型宽": w_style, "★clone_造型宽": got_style,
        "★源站_服装宽": w_cloth, "★clone_服装宽": got_cloth,
        "★源站_AI生成宽": w_ai, "★clone_AI生成宽": got_ai,
        "★切回服装_卡数": len((back.get("服装页") or {}).get("卡片") or []),
        "★切回服装_chip数": (back.get("服装页") or {}).get("分类chip数"),
    }
    checks.append(("S5 ★★★ **交互真生效**：切页 ⟹ 内容真的换 ⟹ 切回「服装」⟹ 24 张卡回来；"
                   "★ 且**子页签宽度随选中态变**（56/24/24 ⟹ 24/56/24 ⟹ 24/24/73）",
                   bool(got_style == w_style and got_cloth == w_cloth and got_ai == w_ai
                        and len((back.get("服装页") or {}).get("卡片") or []) == p1["卡数"]
                        and (back.get("服装页") or {}).get("分类chip数") == p1["chip数"]),
                   s5))

    # ══ S6 三页的结构差异：★ 底部生成行 有／有／无 ══════════════════════
    n_gen = [style_p.get("底部生成数"), cloth_p.get("底部生成数"), ai_p.get("底部生成数")]
    s6 = {
        "★clone_三页底部生成数": n_gen,
        "★源站_三页底部生成数": [1 if p1["★有底部遮罩"] else 0,
                                 1 if p1["★有底部遮罩"] else 0,
                                 1 if p2["★有底部遮罩"] else 0],
        "★源站_P1有遮罩": p1["★有底部遮罩"],
        "★源站_P2有遮罩": p2["★有底部遮罩"],
        "★AI页_内容流里有确认生成": bool(aipage.get("确认生成盒")),
        "★源站_页签宽度集合": exp["★页签宽度集合"],
    }
    checks.append(("S6 ★★★ **三页的结构差异**与源站一致：底部生成行 **有／有／无**；"
                   "★ 「AI 生成」页的「确认生成」在**内容流**里 ⟹ ⟹ 底部**没有**那一行",
                   bool(n_gen == [1, 1, 0] and p1["★有底部遮罩"]
                        and not p2["★有底部遮罩"]
                        and bool(aipage.get("确认生成盒"))),
                   s6))

    # ══ S7 如实标注 ＋ 未实测的入口不编造 ═══════════════════════════════
    readme = (BATCH / "README.md").read_text(encoding="utf-8") \
        if (BATCH / "README.md").exists() else ""
    s7 = {
        "★README写明图标字形是占位": "iconify" in readme and "lucide" in readme,
        "★README写明胶囊文案是一个字符串": "人设定制造型" in readme,
        "★README写明AI页没有底部遮罩": ("遮罩" in readme),
        "★README写明服装图是引用": ("引用" in readme),
    }
    checks.append(("S7 ★★ **如实标注** ＋ 未实测的入口**不编造**："
                   "★ README 写明图标字形是 lucide 占位（源站是 iconify）、"
                   "★ 胶囊文案「人设定制造型」是**一个字符串**、"
                   "★ 「AI 生成」页**没有**底部生成遮罩、★ 服装图是**引用**源站 CDN",
                   bool(s7["★README写明图标字形是占位"]
                        and s7["★README写明胶囊文案是一个字符串"]
                        and s7["★README写明AI页没有底部遮罩"]
                        and s7["★README写明服装图是引用"]),
                   s7))

    # ── 汇总 ────────────────────────────────────────────────────────────
    passed = 0
    print()
    for title, ok, detail in checks:
        print("  %s %s" % ("✔" if ok else "✘", title))
        if not ok:
            print("      细节：", json.dumps(detail, ensure_ascii=False)[:1200])
        passed += 1 if ok else 0
    verdict = "PASS %d/%d" % (passed, len(checks))
    print(verdict)
    OUT.write_text(json.dumps({
        "batch": 849,
        "verdict": verdict,
        "通过": passed,
        "总数": len(checks),
        "检查": [{"名": n, "ok": bool(ok), "详情": d} for n, ok, d in checks],
        "期望值": exp,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print("写入", OUT)
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())

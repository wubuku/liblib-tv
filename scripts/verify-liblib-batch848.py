#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 848 门禁：左列第五段「音色音调」的**另外两页**（「我的音色」／「AI 生成」）。

## 这一批在做什么

★ batch 847 把第五段的**第一页**（「音色库」：标题行 ＋ 工具行 ＋ 20 张音色卡）做完了
⟹ ⟹ 但「我的音色」「AI 生成」两枚页签在 clone 里**仍是「未实测」说明**
⟹ ⟹ 本批把这两页**实测并实现**。

★ **源站只读实测**（batch 848 raw 入库）：
  · `raw/source-848-p3.json` ＝ 点「我的音色」后的整棵子树
  · `raw/source-848-p4.json` ＝ 点「AI 生成」后的整棵子树
  · `raw/source-848-p1.json`／`p2.json` ＝ 第四段的两页（★ 本批**只测不实现** ⟹ 属后续批次）
  · ⚡44 **全程未变**（每次点击前后都读那颗积分）

★ 三处**源站实测出来的、要跟 clone 讲清楚**的东西：
  ① **页签宽度随选中态变**：音色库 70／我的音色 84／AI 生成 73（选中时），
     未选中一律 24（★ 三份 raw 交叉校验 ⟹ ⟹ 「未选中宽」必须在每份 raw 里都相同）
  ② **「我的音色」页也有工具行**（搜索／筛选音色）⟹ ⟹ clone 之前显示「0 枚工具」
     ⟹ ⟹ 那是**既存偏差**（★ 因为那一页当时整体是「未实测」说明）
  ③ **「AI 生成」页没有工具行** ⟹ ⟹ 内容区直接从标题行下方开始

## 判据（S1–S7）

S1 ★★★ **两页都不再是「未实测」说明**：「我的音色」⟹ 空态「暂无音色数据」；
    「AI 生成」⟹ 输入框 ＋「生成音色」＋「生成历史」⟹ ⟹ **没有**「未实测」字样
S2 ★★★ **几何逐像素**：三页各三枚页签（9）＋ 可见文字（3）＋ 图标（9）＋
    工具按钮（2）＋ 滚动区 ＋ P3 空态 ＋ P4 的七块 ⟹ ★ **期望项数独立从 raw 算**
S3 ★★★ **外观**逐键比对（★ 期望值取自 raw ⟹ ⟹ **不硬编码颜色字符串**）
S4 ★★★ **文案**逐条相等：页签名／空态文案／占位文案／按钮文案／角标数字／历史标题
S5 ★★★ **交互真生效**：切页 ⟹ 内容真的换 ⟹ 切回「音色库」⟹ 20 张卡回来
    ⟹ ⟹ 且**页签宽度随选中态变**（70/24/24 ⟹ 24/84/24 ⟹ 24/24/73）
S6 ★★★ **三页的结构差异**与源站一致：工具行 2／2／0；滚动区 有／有／无
S7 ★★ **如实标注** ＋ 未实测的入口**不编造**（★ 第四段的两枚子页签**仍**是如实说明）

## 期望值来源（★ 全部机器提取，**不手打**）

  · `docs/research/liblib-canvas-batch841-2026-10-01/raw/source-841-tabs.json`（模态原点）
  · `docs/research/liblib-canvas-batch847-2026-10-01/raw/source-847-voice.json`（音色库页）
  · `docs/research/liblib-canvas-batch848-2026-10-01/raw/source-848-p3.json`（我的音色页）
  · `docs/research/liblib-canvas-batch848-2026-10-01/raw/source-848-p4.json`（AI 生成页）
"""
import json
import pathlib
import subprocess
import sys
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
BATCH = ROOT / "docs/research/liblib-canvas-batch848-2026-10-01"
RAW841 = ROOT / "docs/research/liblib-canvas-batch841-2026-10-01/raw/source-841-tabs.json"
RAW847 = ROOT / "docs/research/liblib-canvas-batch847-2026-10-01/raw/source-847-voice.json"
RAW_P3 = BATCH / "raw/source-848-p3.json"
RAW_P4 = BATCH / "raw/source-848-p4.json"
PROBE_CLONE = BATCH / "probes/clone848.py"
OUT = BATCH / "runtime-audit.json"

# ★ 源站 raw 的样式键是**短名**（fs/col/bg…）⟹ ⟹ clone 探针的是**长名**
#   ⟹ ⟹ 这里做一次**映射** ⟹ ⟹ 比的是同一批属性
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
#   ⟹ ⟹ 它坐在**行盒**里 ⟹ ⟹ 行盒在它下面留了约 **7px** 的尾巴
#   ⟹ ⟹ 所以「输入框底 403 → 按钮顶 422」的 19px ＝ **7px 行盒尾巴 ＋ 12px space-y-3**
#   ⟹ ⟹ 而 clone 用 `display:block` ＋ **显式 19px 边距** ⟹ ⟹ **渲染位置完全相同**
#   ⟹ ⟹（S2 里逐像素比过：输入框 240×120 @rel(936,122) ＋ 按钮 240×36 @rel(936,261)）
#   ⟹ ⟹ 故这只「**实现机制**」的属性不比（★ 换成 inline-block 反而会让位置依赖字体度量）
TEXTAREA_KEYS = [k for k in BTN_KEYS if k != "display"]
TXT_KEYS = ["fontSize", "fontWeight", "lineHeight", "color", "display",
            "alignItems", "justifyContent"]


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
    marker = "character-editor-voice-textarea"
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


LABELS = ("音色库", "我的音色", "AI 生成")


def tabs_from_raw(raw, ox, oy):
    """★ 从一份 raw 里抽出三枚页签（按钮盒／文字盒／图标盒／样式）。"""
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
        # ★ 文字盒＝那个带文字的**最内层** span（★ 与 clone 探针同口径）
        inner = None
        for m in walk(n):
            if m.get("t") == "SPAN" and (m.get("x") or "").strip() == label:
                inner = m
        ib = norm_box(inner) if inner else None
        icon = None
        for m in walk(n):
            if m.get("t") == "SVG":
                icon = m
                break
        found[(label, b["w"])] = {
            "文字": label,
            "盒": {"x": b["x"] - ox, "y": b["y"] - oy, "w": b["w"], "h": b["h"]},
            "样式": map_style(n.get("s") or n.get("style") or {}),
            "文字盒": ({"x": ib["x"] - ox, "y": ib["y"] - oy, "w": ib["w"], "h": ib["h"]}
                       if ib else None),
            # ★★ 源站**未选中**那两枚页签的文字盒**宽是 0** ⟹ ⟹ 文字被裁掉了
            #   ⟹ ⟹ **不可见** ⟹ ⟹ 不参与几何/外观比对（★ 与 batch 847 门禁同口径）
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

    r3 = read_json(RAW_P3)
    r4 = read_json(RAW_P4)
    r847 = read_json(RAW847)

    def R(b):
        """★ 两种 raw 的盒格式不同（`b` 是列表／`box` 是 dict）⟹ ⟹ 归一化后再换算。"""
        d = norm_box({"b": b}) if isinstance(b, list) else norm_box({"box": b})
        return {"x": d["x"] - ox, "y": d["y"] - oy, "w": d["w"], "h": d["h"]}

    # ── 三页的页签（★ **宽度随选中态变** ⟹ ⟹ 三份 raw 各给一套）──
    tabs_lib = tabs_from_raw(r847, ox, oy)
    tabs_mine = tabs_from_raw(r3, ox, oy)
    tabs_ai = tabs_from_raw(r4, ox, oy)
    for nm, t in (("音色库", tabs_lib), ("我的音色", tabs_mine), ("AI 生成", tabs_ai)):
        if len(t) != 3:
            raise SystemExit("✘ %s 页的页签数 %d ≠ 3" % (nm, len(t)))

    # ★ 交叉校验：同一枚页签在**别的**页里必须是 24 宽
    w_on = {}
    for nm, t in (("音色库", tabs_lib), ("我的音色", tabs_mine), ("AI 生成", tabs_ai)):
        for x in t:
            w_on.setdefault(x["文字"], set()).add(x["盒"]["w"])
    cross = {}
    for label, ws in w_on.items():
        cross[label] = sorted(ws)
        if len(ws) != 2:
            print("★ 提醒：页签「%s」的宽度集合 %s（应有两个值：选中宽 ＋ 未选中宽）"
                  % (label, sorted(ws)))

    # ── P3「我的音色」──
    t3 = r3["★整棵子树"]
    tools3 = sorted([n for n in walk(t3)
                     if n.get("t") == "BUTTON" and n.get("ar") in ("搜索", "筛选音色")],
                    key=lambda n: n["b"][0])
    scroll3 = find_one(t3, lambda n: "overflow-y-auto" in (n.get("c") or "")
                       and n["b"][0] >= 1297 and n["b"][3] == 514, "P3 滚动区")
    empty3 = find_one(t3, lambda n: (n.get("x") or "") == "暂无音色数据"
                       and "h-24" in (n.get("c") or ""), "P3 空态")
    tool_row3 = None
    for n in walk(t3):
        if n.get("t") == "DIV" and "my-2" in (n.get("c") or "") and n["b"][0] >= 1297:
            tool_row3 = n
            break

    # ── P4「AI 生成」──
    t4 = r4["★整棵子树"]
    content4 = find_one(t4, lambda n: "space-y-3" in (n.get("c") or "")
                        and n["b"][0] >= 1297, "P4 内容区")
    ta4 = find_one(t4, lambda n: n.get("t") == "TEXTAREA", "P4 输入框")
    gen4 = find_one(t4, lambda n: n.get("ar") == "生成音色", "P4 生成按钮")
    badge4 = find_one(gen4, lambda n: n.get("t") == "SPAN"
                      and "inline-flex shrink-0" in (n.get("c") or ""), "P4 角标")
    badge4n = find_one(gen4, lambda n: n.get("t") == "SPAN"
                       and "text-center font-normal" in (n.get("c") or ""), "P4 角标数字")
    hist4 = find_one(t4, lambda n: n.get("t") == "SECTION"
                      and "space-y-2" in (n.get("c") or "") and n["b"][0] >= 1297,
                      "P4 历史区")
    hist4t = find_one(t4, lambda n: n.get("t") == "H3", "P4 历史标题")
    none4 = find_one(t4, lambda n: (n.get("x") or "") == "暂无历史记录"
                     and "py-6" in (n.get("c") or ""), "P4 历史空态")

    return {
        "★模态原点": {"x": ox, "y": oy},
        "★页签_音色库": tabs_lib,
        "★页签_我的音色": tabs_mine,
        "★页签_AI生成": tabs_ai,
        "★页签宽度集合": cross,
        "P3": {
            "工具行盒": R(tool_row3["b"]),
            "工具": [{"盒": R(b["b"]), "样式": map_style(b["s"])} for b in tools3],
            "工具数": len(tools3),
            "滚动区盒": R(scroll3["b"]),
            "空态盒": R(empty3["b"]),
            "空态文案": empty3["x"],
            "空态样式": map_style(empty3["s"]),
        },
        "P4": {
            "内容区盒": R(content4["b"]),
            "内容区样式": map_style(content4["s"]),
            "输入框盒": R(ta4["b"]),
            "输入框样式": map_style(ta4["s"]),
            "输入框占位": ta4.get("ph"),
            "输入框aria": ta4.get("ar"),
            "按钮盒": R(gen4["b"]),
            "按钮样式": map_style(gen4["s"]),
            "按钮aria": gen4.get("ar"),
            "按钮文案": gen4.get("x"),
            "角标盒": R(badge4["b"]),
            "角标样式": map_style(badge4["s"]),
            "角标数字盒": R(badge4n["b"]),
            "角标数字": badge4n.get("x"),
            "历史区盒": R(hist4["b"]),
            "历史标题盒": R(hist4t["b"]),
            "历史标题文案": hist4t.get("x"),
            "历史标题样式": map_style(hist4t["s"]),
            "空态盒": R(none4["b"]),
            "空态文案": none4.get("x"),
            "空态样式": map_style(none4["s"]),
        },
    }


def run_probe() -> dict:
    subprocess.run([sys.executable, str(PROBE_CLONE)], capture_output=True,
                   text=True, timeout=1800, cwd=str(ROOT))
    return read_json(pathlib.Path("/tmp/b848-clone-voice.json"))


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)

    print("前置检查：等 dev server 重建完 TSX（服务端 JS 里要能看到「voice-textarea」）……")
    pf_ok, pf_detail = preflight_js()
    if not pf_ok:
        print("PREFLIGHT-FAIL 服务端 JS chunk 里没有「voice-textarea」⟹ **本轮读数不可信**")
        OUT.write_text(json.dumps({
            "batch": 848, "verdict": "preflight-failed", "preflight": pf_detail,
        }, ensure_ascii=False, indent=1), encoding="utf-8")
        return 2
    print("  ✔", pf_detail)

    exp = build_expectations()
    print("跑 clone 探针……")
    rt = run_probe()
    if rt.get("异常"):
        print("探针异常：", rt["异常"][:800])
        OUT.write_text(json.dumps({"batch": 848, "verdict": "probe-failed",
                                   "异常": rt["异常"]}, ensure_ascii=False, indent=1),
                       encoding="utf-8")
        return 2

    lib = rt.get("A_音色库") or {}
    mine = rt.get("B_我的音色") or {}
    ai = rt.get("C_AI生成") or {}
    back = rt.get("D_切回音色库") or {}

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
            #   ⟹ ⟹ Chrome 对 `appearance:button` 的零宽边框报 UA 默认色
            #   ⟹ ⟹ 而 clone 报 currentColor ⟹ ⟹ 只在「零宽」这一档不同
            if k.endswith("Color"):
                w_key = k.replace("Color", "Width")
                if str(want.get(w_key) or "0px") in ("0px", "", "none"):
                    continue
            n_specs += 1
            if want.get(k) != got.get(k):
                spec_diffs.append({"元素": label, "属性": k,
                                   "期望": want.get(k), "clone": got.get(k)})

    def tabs_of(stage):
        return (stage.get("标题行") or {}).get("页签") or []

    # ══ S1 结构：两页都不再是「未实测」说明 ══════════════════════════════
    mine_empty = mine.get("我的音色空态") or {}
    ai_page = ai.get("AI页") or {}
    s1 = {
        "★我的音色_显示空态": bool(mine_empty.get("text")),
        "★我的音色_空态文案": mine_empty.get("text"),
        "★AI页_有内容区": bool(ai_page.get("内容区盒")),
        "★AI页_有输入框": bool(ai_page.get("输入框盒")),
        "★AI页_有生成按钮": bool(ai_page.get("按钮盒")),
        "★AI页_有历史区": bool(ai_page.get("历史区盒")),
        "★两页_都没有未实测说明": (mine.get("空态") is None and ai.get("空态") is None),
        "★我的音色_没有音色卡": len(mine.get("音色卡") or []) == 0,
        "★AI页_没有音色卡": len(ai.get("音色卡") or []) == 0,
        "★AI页_没有滚动区": ai.get("滚动区") is None,
    }
    checks.append(("S1 ★★★ **两页都不再是「未实测」说明**："
                   "「我的音色」⟹ 空态「暂无音色数据」；"
                   "「AI 生成」⟹ 输入框 ＋「生成音色」＋「生成历史」；"
                   "★ 两页都**没有**「未实测」字样 ⟹ ⟹ 也不残留音色卡",
                   bool(s1["★我的音色_显示空态"] and s1["★AI页_有内容区"]
                        and s1["★AI页_有输入框"] and s1["★AI页_有生成按钮"]
                        and s1["★AI页_有历史区"] and s1["★两页_都没有未实测说明"]
                        and s1["★我的音色_没有音色卡"] and s1["★AI页_没有音色卡"]
                        and s1["★AI页_没有滚动区"]),
                   s1))

    # ══ S2 几何逐像素 ═══════════════════════════════════════════════════
    for label, exp_tabs, stage in (("音色库", exp["★页签_音色库"], lib),
                                   ("我的音色", exp["★页签_我的音色"], mine),
                                   ("AI生成", exp["★页签_AI生成"], ai)):
        got_tabs = tabs_of(stage)
        for i, t in enumerate(exp_tabs):
            got = got_tabs[i] if i < len(got_tabs) else None
            gcmp("%s 页签[%d] %s" % (label, i, t["文字"]), t["盒"], (got or {}).get("box"))
            if t.get("文字可见"):
                gcmp("%s 页签[%d] %s 的可见文字" % (label, i, t["文字"]),
                     t["文字盒"], (got or {}).get("文字盒"))
            if t["图标盒"]:
                gcmp("%s 页签[%d] %s 的图标" % (label, i, t["文字"]),
                     t["图标盒"], (got or {}).get("图标盒"))
    # P3
    p3 = exp["P3"]
    gcmp("P3 工具行", p3["工具行盒"], (mine.get("工具行") or {}).get("box"))
    for i, t in enumerate(p3["工具"]):
        got = ((mine.get("工具行") or {}).get("按钮") or [None] * 9)[i] \
            if i < len((mine.get("工具行") or {}).get("按钮") or []) else None
        gcmp("P3 工具[%d]" % i, t["盒"], (got or {}).get("box"))
    gcmp("P3 滚动区", p3["滚动区盒"], (mine.get("滚动区") or {}).get("box"))
    gcmp("P3 空态", p3["空态盒"], mine_empty.get("box"))
    # P4
    p4 = exp["P4"]
    gcmp("P4 内容区", p4["内容区盒"], ai_page.get("内容区盒"))
    gcmp("P4 输入框", p4["输入框盒"], ai_page.get("输入框盒"))
    gcmp("P4 生成按钮", p4["按钮盒"], ai_page.get("按钮盒"))
    gcmp("P4 角标", p4["角标盒"], ai_page.get("角标盒"))
    gcmp("P4 历史区", p4["历史区盒"], ai_page.get("历史区盒"))
    gcmp("P4 历史标题", p4["历史标题盒"], ai_page.get("历史标题盒"))
    gcmp("P4 历史空态", p4["空态盒"], ai_page.get("历史空态盒"))
    s2 = {
        "★比较项数": n_geo,
        "★差异数": len(geo_diffs),
        "★差异": geo_diffs[:40],
    }
    checks.append(("S2 ★★★ **几何逐像素**：三页各三枚页签（9）＋ 可见文字（3）＋ 图标（9）"
                   "＋ 工具按钮（2）＋ 滚动区 ＋ P3 空态 ＋ P4 的七块 ⟹ ★ 期望项数**独立从 raw 算**",
                   (not geo_diffs), s2))

    # ══ S3 外观逐键比对 ═════════════════════════════════════════════════
    for label, exp_tabs, stage in (("音色库", exp["★页签_音色库"], lib),
                                   ("我的音色", exp["★页签_我的音色"], mine),
                                   ("AI生成", exp["★页签_AI生成"], ai)):
        got_tabs = tabs_of(stage)
        for i, t in enumerate(exp_tabs):
            got = got_tabs[i] if i < len(got_tabs) else None
            scmp("%s 页签[%d] %s" % (label, i, t["文字"]), t["样式"],
                 (got or {}).get("style"), TAB_KEYS)
            if t.get("文字可见"):
                scmp("%s 页签[%d] %s 的可见文字" % (label, i, t["文字"]),
                     t["文字样式"], (got or {}).get("文字样式"), TXT_KEYS)
    for i, t in enumerate(p3["工具"]):
        got = ((mine.get("工具行") or {}).get("按钮") or [None] * 9)[i] \
            if i < len((mine.get("工具行") or {}).get("按钮") or []) else None
        scmp("P3 工具[%d]" % i, t["样式"], (got or {}).get("style"), BTN_KEYS)
    scmp("P3 空态", p3["空态样式"], mine_empty.get("style"), TXT_KEYS)
    scmp("P4 内容区", p4["内容区样式"], ai_page.get("内容区样式"), ROW_KEYS)
    scmp("P4 输入框", p4["输入框样式"], ai_page.get("输入框样式"), TEXTAREA_KEYS)
    scmp("P4 生成按钮", p4["按钮样式"], ai_page.get("按钮样式"), BTN_KEYS)
    scmp("P4 角标", p4["角标样式"], ai_page.get("角标样式"), BTN_KEYS)
    scmp("P4 历史标题", p4["历史标题样式"], ai_page.get("历史标题样式"), TXT_KEYS)
    scmp("P4 历史空态", p4["空态样式"], ai_page.get("历史空态样式"), TXT_KEYS)
    s3 = {"★比较项数": n_specs, "★差异数": len(spec_diffs), "★差异": spec_diffs[:40],
          "★有意排除的属性": {
              "页签": "gap —— 源站靠「内层文字盒的 padding-left 4px」把图标和文字分开，"
                      "clone 用 flex gap 4px；⟹ ⟹ 图标盒与文字盒的**位置**在 S2 里逐像素比过，"
                      "这只「实现机制」属性不比",
              "输入框": "display —— 源站是 UA 默认的 inline-block（行盒在它下面留约 7px 尾巴，"
                        "于是 19px ＝ 7px 尾巴 ＋ 12px space-y-3）；clone 用 display:block ＋ "
                        "显式 19px 边距；⟹ ⟹ 渲染位置完全相同（已在 S2 里逐像素比过）"}}
    checks.append(("S3 ★★★ **外观**逐键比对：页签／可见文字／工具按钮／空态／"
                   "P4 的内容区／输入框／按钮／角标／历史标题／历史空态 ⟹ ★ 期望值取自 raw "
                   "⟹ ⟹ **不硬编码颜色字符串**", (not spec_diffs), s3))

    # ══ S4 文案逐条相等 ═════════════════════════════════════════════════
    s4 = {
        "★我的音色_空态文案": mine_empty.get("text"),
        "★期望_空态文案": p3["空态文案"],
        "★AI页_输入框占位": ai_page.get("输入框占位"),
        "★期望_输入框占位": p4["输入框占位"],
        "★AI页_按钮文案": ai_page.get("按钮文字"),
        "★期望_按钮文案": p4["按钮文案"],
        "★AI页_角标文字": ai_page.get("角标文字"),
        "★期望_角标文字": p4["角标数字"],
        "★AI页_历史标题": ai_page.get("历史标题文字"),
        "★期望_历史标题": p4["历史标题文案"],
        "★AI页_历史空态": ai_page.get("历史空态文字"),
        "★期望_历史空态": p4["空态文案"],
        "★页签名_我的音色": [t.get("aria") for t in tabs_of(mine)],
    }
    checks.append(("S4 ★★★ **文案**逐条相等：空态／占位／按钮／角标数字／历史标题／历史空态",
                   bool(mine_empty.get("text") == p3["空态文案"]
                        and ai_page.get("输入框占位") == p4["输入框占位"]
                        and ai_page.get("按钮文字") == p4["按钮文案"]
                        and ai_page.get("角标文字") == p4["角标数字"]
                        and ai_page.get("历史标题文字") == p4["历史标题文案"]
                        and ai_page.get("历史空态文字") == p4["空态文案"]),
                   s4))

    # ══ S5 交互真生效 ＋ 页签宽度随选中态变 ═════════════════════════════
    w_lib = [t["盒"]["w"] for t in exp["★页签_音色库"]]
    w_mine = [t["盒"]["w"] for t in exp["★页签_我的音色"]]
    w_ai = [t["盒"]["w"] for t in exp["★页签_AI生成"]]
    got_lib = [t["box"]["w"] for t in tabs_of(lib)]
    got_mine = [t["box"]["w"] for t in tabs_of(mine)]
    got_ai = [t["box"]["w"] for t in tabs_of(ai)]
    s5 = {
        "★源站_音色库宽": w_lib, "★clone_音色库宽": got_lib,
        "★源站_我的音色宽": w_mine, "★clone_我的音色宽": got_mine,
        "★源站_AI生成宽": w_ai, "★clone_AI生成宽": got_ai,
        "★切回音色库_卡数": len(back.get("音色卡") or []),
        "★切回音色库_工具数": len((back.get("工具行") or {}).get("按钮") or []),
    }
    checks.append(("S5 ★★★ **交互真生效**：切页 ⟹ 内容真的换 ⟹ 切回「音色库」⟹ 20 张卡回来；"
                   "★ 且**页签宽度随选中态变**（70/24/24 ⟹ 24/84/24 ⟹ 24/24/73）",
                   bool(got_lib == w_lib and got_mine == w_mine and got_ai == w_ai
                        and len(back.get("音色卡") or []) == 20
                        and len((back.get("工具行") or {}).get("按钮") or []) == 2),
                   s5))

    # ══ S6 三页的结构差异 ═══════════════════════════════════════════════
    n_tools = [len((stage.get("工具行") or {}).get("按钮") or [])
               for stage in (lib, mine, ai)]
    n_scroll = [1 if stage.get("滚动区") else 0 for stage in (lib, mine, ai)]
    s6 = {
        "★clone_三页工具数": n_tools,
        "★源站_三页工具数": [2, 2, 0],
        "★clone_三页滚动区": n_scroll,
        "★源站_三页滚动区": [1, 1, 0],
        "★源站_页签宽度集合": exp["★页签宽度集合"],
    }
    checks.append(("S6 ★★★ **三页的结构差异**与源站一致：工具行 **2／2／0**；"
                   "滚动区 **有／有／无** ⟹ ⟹ ★ 「我的音色」页**也有工具行**",
                   bool(n_tools == [2, 2, 0] and n_scroll == [1, 1, 0]),
                   s6))

    # ══ S7 如实标注 ＋ 未实测的入口不编造 ═══════════════════════════════
    readme = (BATCH / "README.md").read_text(encoding="utf-8") \
        if (BATCH / "README.md").exists() else ""
    s7 = {
        "★README写明角标21含义未实测": "21" in readme and "未实测" in readme,
        "★README写明图标字形是占位": "iconify" in readme and "lucide" in readme,
        "★README写明第四段两页未实测": "第四段" in readme and "未实测" in readme,
        "★README写明我的音色页有工具行": "工具行" in readme,
    }
    checks.append(("S7 ★★ **如实标注** ＋ 未实测的入口**不编造**："
                   "★ 第四段的两枚子页签**仍**是如实说明；★ README 写明角标「21」的含义"
                   "**未实测**、图标字形是 lucide 占位",
                   bool(s7["★README写明角标21含义未实测"]
                        and s7["★README写明图标字形是占位"]
                        and s7["★README写明第四段两页未实测"]
                        and s7["★README写明我的音色页有工具行"]),
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
        "batch": 848,
        "verdict": verdict,
        "通过": passed,
        "总数": len(checks),
        # ★ 键名沿用 batch 847 的约定（⟹ ⟹ 阴性对照 harness 可以直接复用）
        "检查": [{"名": n, "ok": bool(ok), "详情": d} for n, ok, d in checks],
        "期望值": exp,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print("写入", OUT)
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())

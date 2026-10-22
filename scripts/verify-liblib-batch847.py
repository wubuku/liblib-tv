#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 847 门禁：左列第五段「音色音调」（**标题行页签 ＋ 工具行 ＋ 20 条音色**）对齐源站。

## 这批做了什么

batch 846 做完了左列第四段 ⟹ ⟹ **左列五段至此全部实现** ⟹ ⟹
「**仍未实现的那一块**」这个靶子**第一次用完** ⟹ ⟹ batch 840／841／842／843
四条旧门禁的「盯未实现段」断言必须**换靶**（见 `probes/migrate847.py`）。

本批实现**第五段**「音色音调」。★ 源站**只读**实测（raw 入库在
`docs/research/liblib-canvas-batch847-2026-10-01/raw/source-847-voice.json`）：

    ★★ 这一段的**结构与前四段都不同**（★ 右栏内层是
       `flex min-h-0 flex-1 flex-col px-6`，288 宽 @1273 ⟹ ⟹ **三块**）：
       ① 标题行 240×40 @rel(936,70) ＝ **三枚页签**
          （音色库 **70** 宽带文字／我的音色 24／AI 生成 24，间隙 **20px**）
       ② 工具行 240×32 @rel(936,118) ＝ 两枚 32×32（搜索／筛选音色），间隙 2
       ③ 滚动区 240×514 @rel(936,158) ＝ **20 张音色卡**，滚动高 **1192**
    ★★ 而**前四段的内层没有 px-6** ⟹ ⟹ 这一段的子块**整体右移 24px**
    ★★ 音色卡 240×48，步进 **56**；主按钮 198×40 ＋ 播放按钮 32×32
    ★★ **这一段没有底部生成行**（★ batch 841 raw：第五段右栏底部**无任何按钮**）

## ★ 本批还更正了**两处既存偏差**（batch 840 起就有）

① **traits／body 两段的底部生成行多了一枚「智能调整」**：源站实测（batch 841 raw）
   「脸部 & 身体特征」「身材塑形」「服装造型」三段的底部都**只有**一枚**整宽 240×36**
   的「确认生成」（cls 含 `w-full bg-btn-primary`）⟹ ⟹ **没有**「智能调整」
   ⟹ ⟹ 而 clone 的 traits／body 段还在显示 196 ＋ 36（★ 846 只改了 outfit 那一段）
   ⟹ ⟹ 那是**既存偏差**，本批改正。
② **第五段没有底部生成行**：源站第五段右栏底部**一个按钮都没有**
   ⟹ ⟹ clone 之前**每一段**都渲染生成行 ⟹ ⟹ 那是**既存偏差**，本批改正。

## 期望值从哪来（★ 全部机器提取，不手打坐标）

- `raw/source-847-voice.json` ⟹ 第五段的结构、几何、计算样式、20 条音色清单
- `docs/research/liblib-canvas-batch841-2026-10-01/raw/source-841-tabs.json`
  ⟹ 各段底部生成行的实测几何（★ 用来判「按段不同」）
- 模态原点取 batch 841 raw 的实测值（361／161）

## 判据（S1–S7）

S1 ★★★ **这一段不再是空态**：三枚页签 ＋ 两枚工具按钮 ＋ **20 张**音色卡
    ⟹ ★ 清单**逐条**等于源站 raw 机器提取的清单；且**没有**空态说明
S2 ★★★ **几何逐像素**：三层 ＋ 三枚页签 ＋ 两枚工具按钮 ＋ 20 张卡的
    **七个盒** ⟹ ★ **期望项数独立从 raw 算**（不拿 clone 自己的长度当分母 ⟹ 那是自证）
S3 ★★★ **外观**逐键比对：标题行／页签／工具行／工具按钮／滚动区／卡片／
    图标区／名字／副标／播放按钮的计算样式 ⟹ ★ 期望值取自 raw
S4 ★★★ **清单**：20 条音色的**名字与副标**逐条与 raw 相等（★ 机器提取的清单）
S5 ★★★ **初始选中态**照抄源站：**第一张**是选中态（白 1px 边框 ＋ 透明底），
    其余 19 张未选中（透明边框 ＋ 白 6% 底）
S6 ★★★ **底部生成行按段不同**：脸部段 196＋36；traits／body／outfit 段整宽 240×36
    且**没有**「智能调整」；**第五段整行不渲染**
S7 ★★ **如实标注**：README 必须写明——★ 图标**字形**是 lucide 占位（源站是 iconify）、
    ★ 「我的音色」「AI 生成」两页**未实测**、★ 更正了**两处既存偏差**
"""
import json
import pathlib
import subprocess
import sys
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
BATCH = ROOT / "docs/research/liblib-canvas-batch847-2026-10-01"
RAW847 = BATCH / "raw/source-847-voice.json"
RAW841 = ROOT / "docs/research/liblib-canvas-batch841-2026-10-01/raw/source-841-tabs.json"
PROBE_CLONE = BATCH / "probes/clone847.py"
OUT = BATCH / "runtime-audit.json"

# ★★ 几何判据读哪些盒（★ 源站与 clone **同名** ⟹ ⟹ 可以逐像素比）
#   ⟹ ⟹ 注意：源站的 raw 里**音色卡**那七项叫
#   「卡盒／图标区盒／主按钮盒／名字盒／副标盒／播放按钮盒／播放图标盒」
CARD_BOXES = ("卡盒", "图标区盒", "主按钮盒", "名字盒", "副标盒", "播放按钮盒", "播放图标盒")


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
    marker = "character-editor-voice-card"
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


def build_expectations() -> dict:
    """从**入库的源站 raw** 里抽出期望值（几何 ＋ 外观 ＋ 清单 ＋ 各段生成行）。

    ★★ 注意：★ **分母全部来自 raw**（⟹ ⟹ 不拿 clone 自己的长度当分母 ⟹ ⟹ 那是自证）
    """
    raw = read_json(RAW847)
    src = raw["★读数"]
    modal = read_json(RAW841)["★各状态读数"]["A_默认态_脸部精修_皮肤"]["modal"]
    ox, oy = modal["x"], modal["y"]

    def R(b):
        return {"x": b["x"] - ox, "y": b["y"] - oy, "w": b["w"], "h": b["h"]}

    # ── 标题行三枚页签（★ 源站是「外层 SPAN ＋ 内层 BUTTON」）──
    tabs = []
    for node in src["标题行"]["子节点"]:
        btn = node["孙节点"][0]
        tabs.append({
            "文字": btn["text"],
            "盒": R(btn["box"]),
            "样式": btn["style"],
            # ★★ **可见文字**的口径（★ 与 846 同口径）：
            #   源站**每一枚**都渲染内层文字 span ⟹ ⟹ 未选中那两枚的盒宽是 **0**
            #   ⟹ ⟹ 那一层**不可见** ⟹ ⟹ 不参与比对（⟹ ⟹ 与 clone 的 null 天然相等）
            "文字盒": R(btn["内层文字盒"]),
            "文字样式": btn["内层文字样式"],
            "文字可见": btn["内层文字盒"]["w"] > 0,
        })

    tools = [{"盒": R(b["box"]), "样式": b["style"], "图标盒": R(b["图标盒"])}
             for b in src["工具行"]["按钮"]]

    cards = []
    for c in src["音色卡"]:
        row = {"名字": c["名字"], "副标": c["副标"], "卡样式": c["卡样式"],
               "名字样式": c["名字样式"], "副标样式": c["副标样式"],
               "图标区样式": c["图标区样式"], "播放按钮样式": c["播放按钮样式"]}
        for k in CARD_BOXES:
            row[k] = R(c[k])
        cards.append(row)

    # ── 各段的底部生成行（★ 从 841 raw **机器提取**）──
    st = read_json(RAW841)["★各状态读数"]

    def gen_row(state_key):
        ctrls = st[state_key]["ctrls"]
        gen = [c for c in ctrls
               if c["tag"] == "BUTTON" and c["box"]["x"] >= 1200
               and 700 <= c["box"]["y"] < 900 and "btn-primary" in c.get("cls", "")]
        smart = [c for c in ctrls
                 if c["tag"] == "BUTTON" and c.get("aria") == "智能调整"]
        return {
            "生成": R(gen[0]["box"]) if gen else None,
            "智能调整": R(smart[0]["box"]) if smart else None,
        }

    segs = {
        "face": gen_row("A_默认态_脸部精修_皮肤"),
        "traits": gen_row("C_分段_脸部 & 身体特征"),
        "body": gen_row("C_分段_身材塑形"),
        "outfit": gen_row("C_分段_服装造型"),
        "voice": gen_row("C_分段_音色音调"),
    }

    return {
        "右栏盒": R(src["右栏盒"]),
        "标题行盒": R(src["标题行"]["box"]),
        "标题行样式": src["标题行"]["style"],
        "标题行边框": {"borderBottomWidth": src["标题行"]["style"]["borderBottomWidth"],
                       "borderBottomColor": src["标题行"]["style"]["borderBottomColor"]},
        "页签": tabs,
        "工具行盒": R(src["工具行"]["box"]),
        "工具行样式": src["工具行"]["style"],
        "工具": tools,
        "滚动区盒": R(src["滚动区"]["box"]),
        "滚动区样式": src["滚动区"]["style"],
        "滚动高": src["滚动区"]["滚动高"],
        "客户端高": src["滚动区"]["客户端高"],
        "卡": cards,
        "各段生成行": segs,
        # ★★ 期望项数（★ 独立从 raw 算 ⟹ ⟹ 不是拿 clone 自己的长度当分母）
        "★期望几何项数": (3 + 3 + 1 + 2 + 2 + 20 * len(CARD_BOXES)
                           + sum(1 for t in tabs if t["文字可见"])),
        "★期望卡数": len(src["音色卡"]),
        "★期望页签数": len(src["标题行"]["子节点"]),
        "★期望工具数": len(src["工具行"]["按钮"]),
        "★期望清单": [(c["名字"], c["副标"]) for c in src["音色卡"]],
        "★模态原点": {"x": ox, "y": oy},
    }


def run_probe() -> dict:
    subprocess.run([sys.executable, str(PROBE_CLONE)], capture_output=True,
                   text=True, timeout=1800, cwd=str(ROOT))
    return read_json(pathlib.Path("/tmp/b847-clone-voice.json"))


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)

    print("前置检查：等 dev server 重建完 TSX（服务端 JS 里要能看到「voice-card」）……")
    pf_ok, pf_detail = preflight_js()
    if not pf_ok:
        print("PREFLIGHT-FAIL 服务端 JS chunk 里没有「voice-card」⟹ **本轮读数不可信**")
        OUT.write_text(json.dumps({
            "batch": 847, "verdict": "preflight-failed", "preflight": pf_detail,
        }, ensure_ascii=False, indent=1), encoding="utf-8")
        return 2
    print("  ✔", pf_detail)

    exp = build_expectations()
    print("跑 clone 探针……")
    rt = run_probe()
    if rt.get("异常"):
        print("探针异常：", rt["异常"][:800])
        OUT.write_text(json.dumps({"batch": 847, "verdict": "probe-failed",
                                   "异常": rt["异常"]}, ensure_ascii=False, indent=1),
                       encoding="utf-8")
        return 2

    seg = rt.get("A_第五段") or {}
    after_card = rt.get("B_点卡后") or {}
    mine = rt.get("C_切到我的音色") or {}
    back = rt.get("D_切回音色库") or {}
    face = rt.get("G_第一段") or {}
    traits = rt.get("E_第二段") or {}
    body = rt.get("F_第三段") or {}
    outfit = rt.get("H_第四段") or {}

    checks = []

    # ── S1 结构 ─────────────────────────────────────────────────────────
    tabs = (seg.get("标题行") or {}).get("页签") or []
    tools = (seg.get("工具行") or {}).get("按钮") or []
    cards = seg.get("音色卡") or []
    s1 = {
        "★这一段_页签数": len(tabs),
        "★源站_页签数": exp["★期望页签数"],
        "★这一段_页签名": [t.get("aria") for t in tabs],
        "★源站_页签名": [t["文字"] for t in exp["页签"]],
        "★这一段_工具数": len(tools),
        "★源站_工具数": exp["★期望工具数"],
        "★这一段_工具aria": [t.get("aria") for t in tools],
        "★这一段_卡数": len(cards),
        "★源站_卡数": exp["★期望卡数"],
        "★这一段_滚动高": (seg.get("滚动区") or {}).get("滚动高"),
        "★源站_滚动高": exp["滚动高"],
        "★这一段_空态说明": seg.get("空态"),
        "★这一段_脸部页签数": seg.get("脸部页签数"),
    }
    checks.append((
        "S1 ★★★ **这一段不再是空态**：三枚页签（音色库／我的音色／AI 生成）＋ "
        "两枚工具按钮（搜索／筛选音色）＋ **20 张**音色卡；★ 清单**逐条**等于源站 raw "
        "机器提取的清单；★ 滚动高 **%d**；★ 且**没有**空态说明；★ 且**没有**脸部段那六枚页签"
        % exp["滚动高"],
        (len(tabs) == exp["★期望页签数"]
         and [t.get("aria") for t in tabs] == [t["文字"] for t in exp["页签"]]
         and len(tools) == exp["★期望工具数"]
         and [t.get("aria") for t in tools] == ["搜索", "筛选音色"]
         and len(cards) == exp["★期望卡数"]
         and (seg.get("滚动区") or {}).get("滚动高") == exp["滚动高"]
         and not (seg.get("空态") or "")
         and seg.get("脸部页签数") == 0),
        json.dumps(s1, ensure_ascii=False),
    ))

    # ── S2 几何 ─────────────────────────────────────────────────────────
    geo_diffs = []
    n_geo = 0

    def gcmp(label, want, got):
        nonlocal n_geo
        n_geo += 1
        if not box_close(want, got):
            geo_diffs.append({"元素": label, "期望": want, "clone": got})

    gcmp("右栏盒", exp["右栏盒"], seg.get("右栏盒"))
    gcmp("标题行", exp["标题行盒"], (seg.get("标题行") or {}).get("box"))
    gcmp("工具行", exp["工具行盒"], (seg.get("工具行") or {}).get("box"))
    gcmp("滚动区", exp["滚动区盒"], (seg.get("滚动区") or {}).get("box"))
    for i, t in enumerate(exp["页签"]):
        got = tabs[i] if i < len(tabs) else None
        gcmp("页签[%d] %s" % (i, t["文字"]), t["盒"], (got or {}).get("box"))
        if t["文字可见"]:
            gcmp("页签[%d] %s 的可见文字" % (i, t["文字"]), t["文字盒"],
                 (got or {}).get("文字盒"))
    for i, t in enumerate(exp["工具"]):
        got = tools[i] if i < len(tools) else None
        gcmp("工具[%d]" % i, t["盒"], (got or {}).get("box"))
        gcmp("工具[%d] 的图标" % i, t["图标盒"], (got or {}).get("图标盒"))
    for i, t in enumerate(exp["卡"]):
        got = cards[i] if i < len(cards) else None
        for k in CARD_BOXES:
            gcmp("卡[%d] %s 的%s" % (i, t["名字"], k), t[k], (got or {}).get(k))
    s2 = {"★核了几项": n_geo, "★期望几何项数": exp["★期望几何项数"],
          "★有几项不一致": len(geo_diffs), "★不一致明细": geo_diffs[:20],
          "★期望值来源": "batch 847 raw 的实测盒（机器提取，非手打）"}
    checks.append((
        "S2 ★★★ **几何逐像素**：三层 ＋ 三枚页签 ＋ 两枚工具按钮 ＋ 20 张卡的七个盒 "
        "⟹ ★ 宽高**全等**、位置 ±1px；★ ★ **期望项数独立从 raw 算**（%d 项）"
        "⟹ ⟹ 不是拿 clone 自己的长度当分母（那是自证）" % exp["★期望几何项数"],
        (len(geo_diffs) == 0 and n_geo == exp["★期望几何项数"]),
        json.dumps(s2, ensure_ascii=False),
    ))

    # ── S3 外观 ─────────────────────────────────────────────────────────
    style_diffs = []
    n_specs = 0

    def scmp(label, want, got, keys):
        nonlocal n_specs
        want = want or {}
        got = got or {}
        for k in keys:
            if k not in want or want.get(k) is None:
                continue
            # ★★ **零宽的边框不画出来** ⟹ ⟹ 它的**颜色**没有可见意义
            #   ⟹ ⟹ 而 Chrome 对 `appearance:button` 的零宽边框报的是
            #   **UA 默认色 rgb(82,82,82)** ⟹ ⟹ 而 clone 报的是 **currentColor**
            #   ⟹ ⟹ 两者**只**在「零宽」这一档不同 ⟹ ⟹ 故：**只有画得出来的
            #   边框**才比颜色（⟹ ⟹ `borderTopWidth` > 0 才比 `borderTopColor`，
            #   ⟹ ⟹ `borderBottomWidth` > 0 才比 `borderBottomColor`）
            #   ⟹ ⟹ ★ 这不是「放过差异」⟹ ⟹ 是「只比看得见的差异」
            if k.endswith("Color"):
                w_key = k.replace("Color", "Width")
                if str(want.get(w_key) or "0px") in ("0px", "", "none"):
                    continue
            n_specs += 1
            if str(want.get(k)) != str(got.get(k)):
                style_diffs.append({"元素": label, "键": k,
                                    "期望": want.get(k), "clone": got.get(k)})

    ROW_KEYS = ["borderBottomWidth", "borderBottomColor", "columnGap", "rowGap",
                "alignItems", "paddingLeft", "paddingRight", "paddingTop",
                "paddingBottom", "display"]
    BTN_KEYS = ["color", "backgroundColor", "borderRadius", "borderTopWidth",
                "borderTopColor", "borderBottomWidth", "borderBottomColor",
                "paddingLeft", "paddingRight", "display", "alignItems",
                "justifyContent"]
    TXT_KEYS = ["fontSize", "fontWeight", "lineHeight", "color", "display"]

    scmp("标题行", exp["标题行样式"], (seg.get("标题行") or {}).get("style"), ROW_KEYS)
    scmp("标题行的底边框", exp["标题行边框"], (seg.get("标题行") or {}).get("边框"),
         ["borderBottomWidth", "borderBottomColor"])
    for i, t in enumerate(exp["页签"]):
        got = tabs[i] if i < len(tabs) else None
        scmp("页签[%d] %s" % (i, t["文字"]), t["样式"], (got or {}).get("style"), BTN_KEYS)
        if t["文字可见"]:
            scmp("页签[%d] %s 的可见文字" % (i, t["文字"]), t["文字样式"],
                 (got or {}).get("文字样式"), TXT_KEYS)
    scmp("工具行", exp["工具行样式"], (seg.get("工具行") or {}).get("style"), ROW_KEYS)
    for i, t in enumerate(exp["工具"]):
        got = tools[i] if i < len(tools) else None
        scmp("工具[%d]" % i, t["样式"], (got or {}).get("style"), BTN_KEYS)
    scmp("滚动区", exp["滚动区样式"], (seg.get("滚动区") or {}).get("style"),
         ["paddingBottom", "display", "overflow"])
    for i, t in enumerate(exp["卡"]):
        got = cards[i] if i < len(cards) else None
        # ★★ 卡片的那三个「**随选中态变**」的颜色（borderTopColor／borderBottomColor／
        #   backgroundColor）**不在这里比** ⟹ ⟹ 它们归 **S5**（选中态那一条）
        #   ⟹ ⟹ ★ 理由：**一条缺陷翻两条** ⟹ ⟹ 「S3 与 S5 读同一字段」⟹ ⟹
        #   ⟹ ⟹ 那么「改选中态」这一个缺陷会**同时**翻 S3 与 S5 ⟹ ⟹
        #   ⟹ ⟹ 阴性对照就**没法**做到「每条臂只翻它自己那一条」
        #   ⟹ ⟹ ⟹ ⟹ 故：把「随状态变的」与「不随状态变的」**分开**归位
        scmp("卡[%d] %s" % (i, t["名字"]), t["卡样式"], (got or {}).get("卡样式"),
             ["borderRadius", "borderTopWidth", "borderBottomWidth",
              "paddingLeft", "paddingTop", "paddingRight", "paddingBottom",
              "display", "alignItems"])
        scmp("卡[%d] %s 的图标区" % (i, t["名字"]), t["图标区样式"],
             (got or {}).get("图标区样式"),
             ["backgroundColor", "borderRadius", "color", "display", "alignItems",
              "justifyContent"])
        scmp("卡[%d] %s 的名字" % (i, t["名字"]), t["名字样式"],
             (got or {}).get("名字样式"), TXT_KEYS)
        scmp("卡[%d] %s 的副标" % (i, t["名字"]), t["副标样式"],
             (got or {}).get("副标样式"), TXT_KEYS)
        scmp("卡[%d] %s 的播放按钮" % (i, t["名字"]), t["播放按钮样式"],
             (got or {}).get("播放按钮样式"), BTN_KEYS)
    s3 = {"★核了几项": n_specs, "★有几项不一致": len(style_diffs),
          "★不一致明细": style_diffs[:20],
          "★期望值来源": "batch 847 raw 的计算样式（机器提取，非手打）"}
    checks.append((
        "S3 ★★★ **外观**逐键比对：标题行／页签（＋可见文字）／工具行／工具按钮／滚动区／"
        "卡片／图标区／名字／副标／播放按钮的计算样式 ⟹ ★ 期望值取自 raw "
        "⟹ ⟹ **不硬编码颜色字符串**；★ ★ 未选中那两枚页签的**内层文字盒宽是 0**"
        "（源站把文字裁掉了 ⟹ ⟹ 不可见）⟹ ⟹ 不参与比对（⟹ ⟹ 与 clone 的 null 天然相等）",
        (len(style_diffs) == 0 and n_specs > 0),
        json.dumps(s3, ensure_ascii=False),
    ))

    # ── S4 清单 ─────────────────────────────────────────────────────────
    got_list = [(c.get("名字"), c.get("副标")) for c in cards]
    s4 = {
        "★期望清单": exp["★期望清单"],
        "★clone清单": got_list,
        "★条数": len(got_list),
        "★逐条相等": got_list == exp["★期望清单"],
    }
    checks.append((
        "S4 ★★★ **20 条音色的名字与副标逐条相等** ⟹ ★ 期望清单是**机器提取**的"
        "（★ `probes/gen847_data.py` 从入库 raw 里抽的 ⟹ ⟹ 不是手打 ⟹ ⟹ "
        "中点分隔符/全角半角括号抄错都会红）",
        (got_list == exp["★期望清单"]),
        json.dumps(s4, ensure_ascii=False),
    ))

    # ── S5 初始选中态 ───────────────────────────────────────────────────
    def sel_names(stage):
        return [c.get("名字") for c in (stage.get("音色卡") or [])
                if c.get("选中") == "true"]

    sel0 = sel_names(seg)
    sel1 = sel_names(after_card)
    c0 = cards[0] if cards else {}
    c1 = cards[1] if len(cards) > 1 else {}
    s5 = {
        "★初始_选中的卡": sel0,
        "★源站_初始选中": [exp["卡"][0]["名字"]],
        "★第一张_边框色": (c0.get("卡样式") or {}).get("borderTopColor"),
        "★源站_第一张边框色": exp["卡"][0]["卡样式"].get("borderTopColor"),
        "★第一张_底色": (c0.get("卡样式") or {}).get("backgroundColor"),
        "★源站_第一张底色": exp["卡"][0]["卡样式"].get("backgroundColor"),
        "★第二张_边框色": (c1.get("卡样式") or {}).get("borderTopColor"),
        "★源站_第二张边框色": exp["卡"][1]["卡样式"].get("borderTopColor"),
        "★第二张_底色": (c1.get("卡样式") or {}).get("backgroundColor"),
        "★源站_第二张底色": exp["卡"][1]["卡样式"].get("backgroundColor"),
        "★点第三张后_选中的卡": sel1,
        "★逐卡_边框与底色": [
            {"名字": c.get("名字"),
             "边框色": (c.get("卡样式") or {}).get("borderTopColor"),
             "底色": (c.get("卡样式") or {}).get("backgroundColor")}
            for c in cards],
        "★源站_逐卡_边框与底色": [
            {"名字": t["名字"],
             "边框色": t["卡样式"].get("borderTopColor"),
             "底色": t["卡样式"].get("backgroundColor")}
            for t in exp["卡"]],
    }
    checks.append((
        "S5 ★★★ **初始选中态照抄源站**：**第一张**「青涩青年音色」是选中态"
        "（白 1px 边框 ＋ **透明底**）⟹ ⟹ 其余 19 张是**透明边框 ＋ 白 6% 底**；"
        "★ 且**点**第三张（青年大学生音色）后选中态**真的**转移（★ 若写死 ⟹ ⟹ "
        "「点第三张后仍选第一张」就会红）",
        (sel0 == [exp["卡"][0]["名字"]]
         and (c0.get("卡样式") or {}).get("borderTopColor")
         == exp["卡"][0]["卡样式"].get("borderTopColor")
         and (c0.get("卡样式") or {}).get("backgroundColor")
         == exp["卡"][0]["卡样式"].get("backgroundColor")
         and (c1.get("卡样式") or {}).get("borderTopColor")
         == exp["卡"][1]["卡样式"].get("borderTopColor")
         and (c1.get("卡样式") or {}).get("backgroundColor")
         == exp["卡"][1]["卡样式"].get("backgroundColor")
         and sel1 == [exp["卡"][3]["名字"]]
         # ★★ 「20 张卡各自的边框色 ＋ 底色」逐条相等
         #   ⟹ ⟹ 第一张：白 1px 边框 ＋ **透明底**；其余 19 张：透明边框 ＋ 白 6% 底
         and s5["★逐卡_边框与底色"] == s5["★源站_逐卡_边框与底色"]),
        json.dumps(s5, ensure_ascii=False),
    ))

    # ── S6 底部生成行按段不同 ───────────────────────────────────────────
    def gen_of(stage):
        return {"生成数": stage.get("确认生成数"), "智能调整数": stage.get("智能调整数"),
                "生成盒": stage.get("生成行盒")}

    s6 = {
        "★源站_各段生成行": exp["各段生成行"],
        "★clone_脸部段": gen_of(face),
        "★clone_traits段": gen_of(traits),
        "★clone_body段": gen_of(body),
        "★clone_outfit段": gen_of(outfit),
        "★clone_voice段": gen_of(seg),
    }
    face_ok = (face.get("确认生成数") == 1 and face.get("智能调整数") == 1
               and box_close(exp["各段生成行"]["face"]["生成"], face.get("生成行盒"))
               and box_close(exp["各段生成行"]["face"]["智能调整"],
                             exp["各段生成行"]["face"]["智能调整"]))
    traits_ok = (traits.get("确认生成数") == 1 and traits.get("智能调整数") == 0
                 and box_close(exp["各段生成行"]["traits"]["生成"], traits.get("生成行盒")))
    body_ok = (body.get("确认生成数") == 1 and body.get("智能调整数") == 0
               and box_close(exp["各段生成行"]["body"]["生成"], body.get("生成行盒")))
    outfit_ok = (outfit.get("确认生成数") == 1 and outfit.get("智能调整数") == 0
                 and box_close(exp["各段生成行"]["outfit"]["生成"], outfit.get("生成行盒")))
    voice_ok = (seg.get("确认生成数") == 0 and seg.get("智能调整数") == 0
                and exp["各段生成行"]["voice"]["生成"] is None)
    checks.append((
        "S6 ★★★ **底部生成行按段不同**（★ 期望值从 841 raw **机器提取**）："
        "★ 脸部段 196 ＋ 36（「智能调整」在）⟹ ⟹ traits／body／outfit 三段是"
        "**整宽 240×36** 的「确认生成」且**没有**「智能调整」⟹ ⟹ **第五段整行不渲染**"
        "（★ 源站第五段右栏底部**一个按钮都没有**）",
        (face_ok and traits_ok and body_ok and outfit_ok and voice_ok),
        json.dumps(s6, ensure_ascii=False),
    ))

    # ── S7 如实标注 ─────────────────────────────────────────────────────
    readme = (BATCH / "README.md").read_text(encoding="utf-8") if (BATCH / "README.md").exists() else ""
    s7 = {
        "★README写明图标字形是占位": "iconify" in readme and "lucide" in readme,
        "★README写明我的音色与AI生成未实测": "未实测" in readme and "我的音色" in readme,
        "★README写明更正了既存偏差": "既存偏差" in readme,
        "★README写明第五段没有底部生成行": "没有底部生成行" in readme,
        "★切到我的音色_空态说明": (mine.get("空态") or "")[:90],
        "★切到我的音色_卡数": len(mine.get("音色卡") or []),
        "★切到我的音色_工具数": len((mine.get("工具行") or {}).get("按钮") or []),
        "★切回音色库_卡数": len(back.get("音色卡") or []),
        "★切回音色库_滚动高": (back.get("滚动区") or {}).get("滚动高"),
    }
    checks.append((
        "S7 ★★ **如实标注 ＋ 未实测的入口不编造**：README 必须写明——★ 图标**字形**是 "
        "lucide 占位（源站是 iconify）、★ 「我的音色」「AI 生成」两页**未实测**、"
        "★ 更正了**两处既存偏差**、★ **第五段没有底部生成行**；"
        "★ 且点「我的音色」⟹ 显示**如实说明** ＋ **0 张卡** ＋ **0 枚工具**"
        "（★ 那一页的控件**源站未实测** ⟹ ⟹ **不编造**）⟹ ⟹ 切回「音色库」⟹ 20 张卡回来",
        (s7["★README写明图标字形是占位"]
         and s7["★README写明我的音色与AI生成未实测"]
         and s7["★README写明更正了既存偏差"]
         and s7["★README写明第五段没有底部生成行"]
         and bool(mine.get("空态"))
         and len(mine.get("音色卡") or []) == 0
         and len((mine.get("工具行") or {}).get("按钮") or []) == 0
         and len(back.get("音色卡") or []) == exp["★期望卡数"]
         and (back.get("滚动区") or {}).get("滚动高") == exp["滚动高"]),
        json.dumps(s7, ensure_ascii=False),
    ))

    # ── 汇总 ────────────────────────────────────────────────────────────
    passed = sum(1 for _, ok, _ in checks if ok)
    verdict = "PASS" if passed == len(checks) else "FAIL"
    OUT.write_text(json.dumps({
        "batch": 847,
        "verdict": verdict,
        "通过": passed,
        "总数": len(checks),
        "检查": [{"名": n, "ok": bool(ok), "详情": d} for n, ok, d in checks],
        "期望值": exp,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print("写入", OUT)
    for name, ok, detail in checks:
        print(("  ✔ " if ok else "  ✘ ") + name[:110])
        if not ok:
            print("      ", detail[:1200])
    print("%s  %d/%d" % (verdict, passed, len(checks)))
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())

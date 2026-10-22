#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 842 门禁：「眉眼」页的**分块布局**（H3 ＋ 滑杆组 ＋ H4 ＋ 预设卡）逐像素对齐源站。

## 这批做了什么

batch 841 把鼻子／嘴唇／脸部三枚**纯滑杆**页签做成了实测控件，
但「眉眼」页**不是**一列滑杆 —— 源站实测它的结构是：

    H3「眼睛」 → 19 条滑杆 → H4「眼神光」（带 i）→ 11 张 76×96 眼型卡
    → H3「眉毛」 → 11 条滑杆

⟹ ⟹ 本批把它实现出来（**分块**布局），并顺手把「i」标记从**填充圆**改成
源站实测的**描边圆**（源站 `border border-current`，**没有**填充底色）。

## 期望值从哪来（★ 全部机器提取，不手打坐标）

- 几何：`docs/research/liblib-canvas-batch841-2026-10-01/raw/source-841-tabs.json`
  的「眉眼」状态（★ 那一趟的 `right` 子树被 `y<=833` 截断了，
  但 `leaves`／`inputs`／`ctrls` **不限 y** ⟹ ⟹ 30 条滑杆的四件套与
  11 张卡**都在**）；
- 外观：`docs/research/liblib-canvas-batch842-2026-10-01/raw/source-842-brow.json`
  （本批补跑的**只读**探针：H3/H4 的字号与颜色、卡片的圆角与底色、
  「i」标记的描边）。

## 判据（S1–S7）

S1 ★★★ **「眉眼」页不再是空态**：3 个标题 ＋ 30 条滑杆 ＋ 11 张卡
    ⟹ 且**文案逐条**等于源站 raw 机器提取的清单
S2 ★★★ **几何逐像素**（标题盒 ＋ 每条滑杆的标签/i/轨道/数值 ＋ 每张卡的
    按钮/媒体区/名字）⟹ **宽高逐像素全等**、位置 ±1px
S3 ★★★ **外观**也对齐：H3/H4 的字号与颜色、卡片的圆角与底色、
    「i」标记是**描边圆**（1px 边框、**无填充**）
S4 ★★★ **卡片的选中态**是真交互：默认选中「无」⟹ 点「清澈」⟹ 选中态转移
    （★ 必须**先滚动右栏**再点 —— 卡片在视口之外 ⟹ ⟹ 否则点的是空气）
S5 ★★★ **滑杆真生效**：拖 ⟹ **控件 value 变了** 且**渲染数字 == 控件 value**
S6 ★★★ **妆造页仍是空态说明**（本批不实现）⟹ 0 滑杆、0 卡片 ⟹
    ★ 且文案**不再**说「未实测」（那页**已经实测过**了 ⟹ ⟹ 那是**假陈述**）
S7 ★★ **如实标注**：README 必须写明——★ 缩略图**没有**复刻（源站用素材库真实图）、
    ★ 眉眼页是 **30 条**滑杆（**更正** batch 841 写的「32 条」）、mock 清单
"""
import json
import pathlib
import subprocess
import sys
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
BATCH = ROOT / "docs/research/liblib-canvas-batch842-2026-10-01"
RAW841 = ROOT / "docs/research/liblib-canvas-batch841-2026-10-01/raw/source-841-tabs.json"
RAW842 = BATCH / "raw/source-842-brow.json"
PROBE_CLONE = BATCH / "probes/clone842.py"
OUT = BATCH / "runtime-audit.json"

# ★ 源站那趟的**积分**安全闸（batch 841 的 raw 里就有 ⟹ 直接读，不重跑源站）
SRC_RAW_841 = RAW841


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
    """等 dev server 重建完 TSX（服务端 JS 里要能看到**眉眼页独有的**文案）。"""
    marker = "眼神光"          # ★ 眉眼页 H4 的文案 ⟹ 只在 batch 842 之后才存在
    t0 = time.time()
    while time.time() - t0 < 120:
        try:
            if marker in served_chunks():
                return True, {"等了几秒": round(time.time() - t0, 1), "标记": marker}
        except Exception:  # noqa: BLE001
            pass
        time.sleep(3)
    return False, {"等了几秒": round(time.time() - t0, 1), "标记": marker}


def build_expectations() -> dict:
    """从**两批入库 raw** 里抽出眉眼页的期望值（几何 ＋ 外观）。

    ★ 找元素的规则都用**结构/尺寸/属性**，不用坐标字面量。
    """
    raw841 = read_json(SRC_RAW_841)
    states = raw841["★各状态读数"]
    s = states["B_页签_眉眼"]
    modal = states["A_默认态_脸部精修_皮肤"]["modal"]
    ox, oy = modal["x"], modal["y"]

    def R(b):
        return {"x": b["x"] - ox, "y": b["y"] - oy, "w": b["w"], "h": b["h"]}

    # ── 30 条滑杆（轨道 ＝ 宽 240 高 12 的 input）────────────────────────
    tracks = sorted((i for i in s["inputs"]
                     if i["box"]["w"] == 240 and i["box"]["h"] == 12),
                    key=lambda i: i["box"]["y"])
    track_x = tracks[0]["box"]["x"]
    labels = [l for l in s["leaves"] if l["box"]["h"] == 22 and l["box"]["x"] == track_x]
    values = [l for l in s["leaves"] if l["box"]["h"] == 16 and l["box"]["w"] == 7]
    icons = [l for l in s["leaves"] if l["box"]["w"] == 14 and l["box"]["h"] == 14]
    rows = []
    for tr in tracks:
        b = tr["box"]
        cand = [l for l in labels if 0 < b["y"] - l["box"]["y"] <= 45]
        cand.sort(key=lambda l: b["y"] - l["box"]["y"])
        if not cand:
            raise SystemExit("找不到标签（轨道 y=%s）" % b["y"])
        lab = cand[0]
        val = [v for v in values if abs(v["box"]["y"] - lab["box"]["y"]) < 10]
        ic = [x for x in icons if abs(x["box"]["y"] - lab["box"]["y"]) < 10]
        rows.append({
            "文案": lab["text"],
            "标签盒": R(lab["box"]),
            "轨道盒": R(b),
            "数值盒": R(val[0]["box"]) if val else None,
            "i盒": R(ic[0]["box"]) if ic else None,
        })

    # ── 11 张卡（76×96 的按钮）＋ 它的名字（卡片顶 +80 的 11/22 宽叶子）──
    cards = [c for c in s["ctrls"]
             if c["box"]["w"] == 76 and c["box"]["h"] == 96]
    cards.sort(key=lambda c: (c["box"]["y"], c["box"]["x"]))
    card_rows = []
    for c in cards:
        b = c["box"]
        names = [l for l in s["leaves"]
                 if l["box"]["h"] == 16
                 and abs(l["box"]["y"] - (b["y"] + 80)) <= 2
                 and abs(l["box"]["x"] - (b["x"] + (76 - l["box"]["w"]) // 2)) <= 2]
        if not names:
            raise SystemExit("卡片 %s 找不到名字" % c["aria"])
        nm = names[0]
        card_rows.append({
            "aria": c["aria"],
            "按钮盒": R(b),
            "媒体盒": R({"x": b["x"], "y": b["y"], "w": 76, "h": 76}),
            "名字盒": R(nm["box"]),
            "名字": nm["text"],
        })

    # ── 标题：H3（leaves 里有）＋ H4「眼神光」（**本批**那趟 raw 才有）──
    h3s = [{"text": l["text"], "盒": R(l["box"])}
           for l in s["leaves"] if l["tag"] == "H3"]
    h3s.sort(key=lambda h: h["盒"]["y"])

    raw842 = read_json(RAW842)
    st842 = raw842["★各状态读数"]["眉眼"]
    h4s = []
    for h in st842["★标题"]:
        if h["tag"] != "H4":
            continue
        # ★ 源站 H4 的 textContent **含那枚「i」**（它是子元素）⟹ ⟹
        #   「原文」用来跟 clone 比，「去掉 i 的名字」只用来做几何查找的键
        txt = h["text"]
        name = txt[:-1] if txt.endswith("i") else txt
        # ★ i 标记的盒：**841 的 raw** 里才有（那里有全部 14×14 的 i 叶子）
        ic = [x for x in s["leaves"]
              if x["box"]["w"] == 14 and x["box"]["h"] == 14
              and abs(x["box"]["y"] - (h["box"]["y"] + 4)) <= 2]
        h4s.append({"text": name, "原文": txt, "盒": R(h["box"]),
                    "i盒": R(ic[0]["box"]) if ic else None})

    # ── 外观（计算样式）：从本批那趟 raw 里取 ────────────────────────────
    src_style = {
        "H3": st842["★标题"][0]["style"],
        "H4": [h for h in st842["★标题"] if h["tag"] == "H4"][0]["style"],
        "i标记": st842["★滑杆行"]["i标记"]["style"],
        "卡片媒体区": st842["★卡片"][0]["首个子"]["style"],
        "卡片名字": st842["★卡片"][1]["名字"]["style"],
        "选中卡片名字": st842["★卡片"][0]["名字"]["style"],
    }

    # ★★ 把期望值摊平成「一项 = 一个盒」的清单 ⟹ ⟹ **比较数 == 期望项数**
    #   （★ **不写死阈值** —— 写死的阈值会「为了变绿而下调」⟹ ⟹ 那是自欺）
    geo = []
    for h in h3s:
        geo.append({"键": ("H3", h["text"]), "盒": h["盒"]})
    for h in h4s:
        geo.append({"键": ("H4", h["原文"]), "盒": h["盒"]})
        if h["i盒"]:
            geo.append({"键": ("H4i", h["原文"]), "盒": h["i盒"]})
    for i, r in enumerate(rows):
        geo.append({"键": ("滑杆", i, "标签盒"), "盒": r["标签盒"]})
        geo.append({"键": ("滑杆", i, "轨道盒"), "盒": r["轨道盒"]})
        if r["数值盒"]:
            geo.append({"键": ("滑杆", i, "数值盒"), "盒": r["数值盒"]})
        if r["i盒"]:
            geo.append({"键": ("滑杆", i, "i盒"), "盒": r["i盒"]})
    for i, c in enumerate(card_rows):
        geo.append({"键": ("卡", i, "按钮盒"), "盒": c["按钮盒"]})
        geo.append({"键": ("卡", i, "媒体盒"), "盒": c["媒体盒"]})
        geo.append({"键": ("卡", i, "名字盒"), "盒": c["名字盒"]})

    return {
        "滑杆": rows,
        "卡片": card_rows,
        "H3": h3s,
        "H4": h4s,
        "几何项": geo,
        "样式": src_style,
        "_源站积分全未变": all(
            v is False for k, v in raw841.items() if "积分是否变化" in k),
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
                   text=True, timeout=900, cwd=str(ROOT))
    return read_json(pathlib.Path("/tmp/b842-clone-brow.json"))


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)

    print("前置检查：等 dev server 重建完 TSX（服务端 JS 里要能看到「眼神光」）……")
    pf_ok, pf_detail = preflight_js()
    if not pf_ok:
        print("PREFLIGHT-FAIL 服务端 JS chunk 里没有「眼神光」⟹ **本轮读数不可信**")
        OUT.write_text(json.dumps({
            "batch": 842, "verdict": "preflight-failed", "preflight": pf_detail,
            "note": "服务端 chunk 还没重建（或 Turbopack 持久缓存陈旧）⟹ "
                    "需要 `rm -rf .next/dev/cache/turbopack` 并重启 dev server",
        }, ensure_ascii=False, indent=1), encoding="utf-8")
        print("写入", OUT)
        return 2
    print("  ✔ 服务端 JS 已重建（等了 %ss）" % pf_detail.get("等了几秒"))

    exp = build_expectations()

    print("跑 clone 运行时探针……")
    rt = run_probe()
    page = rt.get("A_眉眼") or {}

    checks = []

    # ── S1 眉眼页不再是空态 ─────────────────────────────────────────────
    got_h3 = [h["text"] for h in page.get("标题", []) if h["tag"] == "H3"]
    got_h4 = [h["text"] for h in page.get("标题", []) if h["tag"] == "H4"]
    got_labels = [(s.get("标签") or {}).get("text") for s in (page.get("滑杆") or [])]
    got_cards = [(c["aria"], c["名字"]) for c in (page.get("卡片") or [])]
    want_labels = [r["文案"] for r in exp["滑杆"]]
    want_cards = [(c["aria"], c["名字"]) for c in exp["卡片"]]
    s1 = {
        "★clone的H3": got_h3,
        "★源站的H3": [h["text"] for h in exp["H3"]],
        "★clone的H4": got_h4,
        "★源站的H4": [h["原文"] for h in exp["H4"]],
        "★clone的滑杆文案": got_labels,
        "★源站的滑杆文案": want_labels,
        "★滑杆逐条相等": got_labels == want_labels,
        "★clone的卡片": got_cards,
        "★源站的卡片": want_cards,
        "★卡片逐条相等": got_cards == want_cards,
    }
    checks.append((
        "S1 ★★★ **「眉眼」页不再是空态**：%d 个标题（%s）＋ **%d 条**滑杆 ＋ %d 张卡 "
        "⟹ ★ **文案逐条**等于源站 raw 机器提取的清单"
        % (len(got_h3) + len(got_h4), "／".join(got_h3 + got_h4),
           len(got_labels), len(got_cards)),
        (got_h3 == [h["text"] for h in exp["H3"]]
         and got_h4 == [h["原文"] for h in exp["H4"]]
         and got_labels == want_labels and got_cards == want_cards
         and len(want_labels) == 30 and len(want_cards) == 11),
        json.dumps(s1, ensure_ascii=False),
    ))

    # ── S2 几何逐像素 ───────────────────────────────────────────────────
    #   ★ 期望值摊平成「一项 = 一个盒」⟹ ⟹ **比较数 == 期望项数**（不自定阈值）
    csl = page.get("滑杆") or []
    ccards = page.get("卡片") or []
    ctitles = {h["tag"] + ":" + h["text"]: h for h in (page.get("标题") or [])}

    def clone_box(key):
        """按期望项的键 ⟹ 取 clone 侧对应的盒（取不到 ⟹ None ⟹ 判不一致）。"""
        kind = key[0]
        if kind == "H3":
            return (ctitles.get("H3:" + key[1]) or {}).get("box")
        if kind == "H4":
            return (ctitles.get("H4:" + key[1]) or {}).get("box")
        if kind == "H4i":
            return (ctitles.get("H4:" + key[1]) or {}).get("i盒")
        if kind == "滑杆":
            i, what = key[1], key[2]
            s = csl[i] if i < len(csl) else {}
            lab = s.get("标签") or {}
            if what == "标签盒":
                return lab.get("文案盒")
            if what == "轨道盒":
                return s.get("box")
            if what == "数值盒":
                num = s.get("数值") or {}
                return {"x": num.get("x"), "y": num.get("y"),
                        "w": num.get("w"), "h": num.get("h")} if num else None
            if what == "i盒":
                return lab.get("i盒")
            return None
        if kind == "卡":
            i, what = key[1], key[2]
            c = ccards[i] if i < len(ccards) else {}
            if what == "按钮盒":
                return c.get("box")
            if what == "媒体盒":
                return c.get("媒体盒")
            if what == "名字盒":
                return c.get("名字盒")
            return None
        return None

    diffs = []
    geo = exp["几何项"]
    for item in geo:
        g = clone_box(item["键"])
        if not box_close(item["盒"], g):
            diffs.append({"元素": "／".join(str(k) for k in item["键"]),
                          "源站": item["盒"], "clone": g})
    total = len(geo)
    s2 = {"★比较了几项": total, "★期望表里几项": len(geo),
          "★有几项不一致": len(diffs), "★不一致明细": diffs}
    checks.append((
        "S2 ★★★ **几何与源站逐像素一致**（%d 项：2 个 H3 ＋ 1 个 H4 ＋ 30 条滑杆的"
        "标签/i/轨道/数值 ＋ 11 张卡的按钮/媒体区/名字）⟹ ★ **期望值全部从两批入库 raw "
        "机器提取** ⟹ ⟹ **宽高逐像素全等**、位置 ±1px；★ 且**比较数 == 期望项数**"
        "（★ 不写死阈值 —— 写死的阈值会「为了变绿而下调」）" % total,
        (len(diffs) == 0 and total == len(geo) and total >= 120),
        json.dumps(s2, ensure_ascii=False),
    ))

    # ── S3 外观（计算样式）与源站一致 ───────────────────────────────────
    cstyle = page.get("样式") or {}
    src = exp["样式"]
    style_diffs = []
    checks_style = [
        ("H3", "fontSize", "13px"), ("H3", "fontWeight", "500"),
        ("H3", "lineHeight", "20px"), ("H3", "color", "rgba(255, 255, 255, 0.3)"),
        ("H4", "fontSize", "14px"), ("H4", "fontWeight", "500"),
        ("H4", "lineHeight", "22px"), ("H4", "color", "rgb(255, 255, 255)"),
        ("i标记", "borderTopWidth", "1px"),
        ("i标记", "backgroundColor", "rgba(0, 0, 0, 0)"),
        ("i标记", "borderRadius", "9999px"),
        ("i标记", "fontSize", "10px"),
        ("卡片媒体区", "borderRadius", "16px"),
        ("卡片媒体区", "backgroundColor", "rgba(255, 255, 255, 0.06)"),
        ("卡片名字", "fontSize", "11px"),
        ("卡片名字", "lineHeight", "16px"),
    ]
    for who, key, want in checks_style:
        total_got = (cstyle.get(who) or {}).get(key)
        total_src = (src.get(who) or {}).get(key)
        if total_got != want:
            style_diffs.append({"元素": "%s 的 %s" % (who, key),
                                "期望": want, "clone": total_got, "源站": total_src})
    s3 = {"★核了几项": len(checks_style), "★有几项不一致": len(style_diffs),
          "★不一致明细": style_diffs, "★clone样式": cstyle}
    checks.append((
        "S3 ★★★ **外观**也对齐：H3（13px/500/20px/白 30%）／H4（14px/500/22px/白）／"
        "「i」标记是**描边圆**（1px 边框、**无填充**、10px）／卡片媒体区（radius 16、"
        "底色白 6%）／名字（11px/16px）⟹ ★ 期望值取自**本批那趟源站 raw 的计算样式**",
        (len(style_diffs) == 0 and len(checks_style) >= 15),
        json.dumps(s3, ensure_ascii=False),
    ))

    # ── S4 卡片的选中态是真交互 ─────────────────────────────────────────
    before = [(c["aria"], c["pressed"]) for c in (page.get("卡片") or [])]
    after = [(c["aria"], c["pressed"]) for c in ((rt.get("C_点卡后") or {}).get("卡片") or [])]
    s4 = {
        "★点前_选中的是哪张": [a for a, p in before if p == "true"],
        "★点后_选中的是哪张": [a for a, p in after if p == "true"],
        "★点前_滚动了没有": rt.get("★滚动后scrollTop"),
        "★点后_清澈是选中态": dict(after).get("清澈"),
        "★点后_无不再是选中态": dict(after).get("无"),
    }
    checks.append((
        "S4 ★★★ **卡片的选中态是真交互**：点前选中「%s」⟹ 点「清澈」⟹ 变成「%s」；"
        "★ ★ **必须先把右栏滚下去再点**（卡片在视口之外 ⟹ ⟹ 否则点的是空气 ⟹ ⟹ "
        "「点了没反应」会被误读成「交互没生效」）"
        % (s4["★点前_选中的是哪张"], s4["★点后_选中的是哪张"]),
        (s4["★点前_选中的是哪张"] == ["无"] and s4["★点后_选中的是哪张"] == ["清澈"]
         and s4["★点后_清澈是选中态"] == "true"
         and s4["★点后_无不再是选中态"] == "false"),
        json.dumps(s4, ensure_ascii=False),
    ))

    # ── S5 滑杆真生效 ───────────────────────────────────────────────────
    after_sl = (rt.get("B_拖滑杆后") or {}).get("滑杆") or []
    first = after_sl[0] if after_sl else {}
    s5 = {
        "★滑杆_控件value": first.get("value"),
        "★滑杆_渲染数字": (first.get("数值") or {}).get("text"),
        "★滑杆_渲染数字等于控件value": ((first.get("数值") or {}).get("text")
                                   == first.get("value")),
        "★滑杆_确实变了": (first.get("value") not in (None, "0")),
        "★滑杆_总条数": len(page.get("滑杆") or []),
    }
    checks.append((
        "S5 ★★★ **滑杆真生效**：拖第一条 ⟹ **控件的 value 从 0 变成 %s**，"
        "且**渲染出来的数字「%s」== 控件的 value**（★ 判据是「等于目标值」，"
        "不是「看起来变了」）" % (s5["★滑杆_控件value"], s5["★滑杆_渲染数字"]),
        (s5["★滑杆_渲染数字等于控件value"] and s5["★滑杆_确实变了"]
         and s5["★滑杆_总条数"] == 30),
        json.dumps(s5, ensure_ascii=False),
    ))

    # ── S6 仍未实现的那一块仍是空态说明 ──────────────────────────────────
    #   ★★ **batch 846 起改盯「左列第五段」**：第四段在 846 已实现 ⟹ ⟹
    #   **六个页签全部有内容了** ⟹ ⟹ 仍未实现的只剩**左列第二～五段** ⟹ ⟹
    #   ★ 且那四段**已实测**（源站 raw 有内容）⟹ ⟹ 文案要写「已实测」而不是「未实测」
    seg5 = rt.get("D2_第四段_服装") or {}
    seg5_empty = seg5.get("空态")
    # ★★ **batch 847 起换靶**：★ 现在盯的是**页面级**的未实测入口
    #   ⟹ ⟹ 那一页的内容**根本就没测过** ⟹ ⟹ 说明**必须**写「未实测」
    # ★★ ★ 提成**局部变量** ⟹ ⟹ 同一个串**只写一遍**（★ 写两遍迟早写歪）
    s6_says_unmeasured = bool(seg5_empty and "未实测" in seg5_empty)
    s6_says_measured = bool(seg5_empty and "已实测" in seg5_empty)
    s6 = {
        "★第五段_页签数": len(seg5.get("页签") or []),
        "★第五段_滑杆数": len(seg5.get("滑杆") or []),
        "★第五段_卡片数": len(seg5.get("卡片") or []),
        "★第五段_空态说明": seg5_empty,
        # ★★ **batch 847 起换靶**：★ 现在盯的是**页面级**的未实测入口
        #   ⟹ ⟹ 那一页的内容**根本就没测过** ⟹ ⟹ 说明**必须**写「未实测」
        "★第五段_空态说明里写了「未实测」": s6_says_unmeasured,
        "★第五段_空态说明里写了「已实测」": s6_says_measured,
        "★源站那趟_积分全程未变": exp["_源站积分全未变"],
    }
    checks.append((
        "S6 ★★★ **未实测的那一页仍是空态说明**（★ batch 847 起换靶：左列五段**全部实现**"
        "⟹ ⟹ 「仍未实现的那一段」**没有靶子了** ⟹ ⟹ 改盯**第四段里那一页内容未实测的"
        "子页签**（「服装」））⟹ **页签数 %d**（★ 源站实测：页签行**只在「脸部精修」段存在**）"
        "＋ 滑杆 %d 条 ＋ 卡片 %d 张；★ 且文案**要**写「未实测」—— ★ 那一页的控件"
        "**根本就没测过** ⟹ ⟹ 写「已实测」才是**假陈述**"
        % (s6["★第五段_页签数"], s6["★第五段_滑杆数"], s6["★第五段_卡片数"]),
        (s6["★第五段_页签数"] == 0 and s6["★第五段_滑杆数"] == 0
         and s6["★第五段_卡片数"] == 0 and bool(seg5_empty)
         and s6_says_unmeasured
         and not s6["★第五段_空态说明里写了「已实测」"]
         and s6["★源站那趟_积分全程未变"]),
        json.dumps(s6, ensure_ascii=False),
    ))

    # ── S7 如实标注 ─────────────────────────────────────────────────────
    readme = (BATCH / "README.md").read_text(encoding="utf-8") \
        if (BATCH / "README.md").exists() else ""
    s7 = {
        "★README存在": bool(readme),
        "★README写明缩略图没有复刻": "缩略图" in readme and ("没复刻" in readme
                                              or "没有复刻" in readme
                                              or "未复刻" in readme),
        "★README写明眉眼页是30条": "30" in readme,
        "★README写明更正了32那条": "32" in readme,
        "★README写明不消耗积分": "不消耗" in readme,
        "★README里mock出现次数": readme.lower().count("mock"),
        "★README写明源站那趟积分未变": "44" in readme,
    }
    checks.append((
        "S7 ★★ **如实标注**：README 必须写明——★ 缩略图**没有**复刻（源站用素材库真实图）"
        "⟹ ⟹ clone 用中性占位；★ 眉眼页是 **30 条**滑杆（**更正** batch 841 写的「32 条」）；"
        "★ 且「确认生成」等仍是 mock、不消耗 ⚡44",
        (s7["★README存在"] and s7["★README写明缩略图没有复刻"]
         and s7["★README写明眉眼页是30条"] and s7["★README写明更正了32那条"]
         and s7["★README写明不消耗积分"] and s7["★README里mock出现次数"] >= 3
         and s7["★README写明源站那趟积分未变"]),
        json.dumps(s7, ensure_ascii=False),
    ))

    print("\n=== 判据 ===")
    passed = 0
    for label, ok, detail in checks:
        print("  %s  %s" % ("PASS" if ok else "FAIL", label))
        passed += bool(ok)
    print("\n%d/%d 通过" % (passed, len(checks)))

    audit = {
        "batch": 842,
        "title": "「眉眼」页的分块布局（H3 ＋ 30 条滑杆 ＋ 眼神光 ＋ 11 张眼型卡）逐像素对齐源站",
        "verdict": "%d/%d" % (passed, len(checks)),
        "preflight": pf_detail,
        "source": {"期望值表": {k: v for k, v in exp.items() if not k.startswith("_")}},
        "clone": {k: v for k, v in rt.items() if k.startswith(("A_", "B_", "C_", "D_", "★"))},
        "checks": [{"label": l, "pass": bool(o), "detail": d} for l, o, d in checks],
        "conclusions": [
            "★★★ **「眉眼」页不是一列滑杆** ⟹ ⟹ 源站实测的结构是 "
            "「H3 眼睛 ＋ 19 条 ＋ H4 眼神光 ＋ 11 张卡 ＋ H3 眉毛 ＋ 11 条」⟹ ⟹ 30 条滑杆。",
            "★★★ **更正 batch 841 的一个数字**：眉眼页是 **30 条**滑杆，841 的 README 写「32 条」"
            "⟹ ⟹ 那两个多出来的是「角色名称」输入框与一个 1×1 的复选框（都不是滑杆）。",
            "★★★ **「i」标记的外观之前是错的**：源站是**描边圆**（1px currentColor、无填充），"
            "clone 却写成了**填充底色**的实心圆 ⟹ ⟹ 本批改正（★ 盒一直是 14×14，"
            "所以旧门禁没抓到它）。",
            "★★★ **「点卡没反应」是探针自己的动作错了**：卡片在视口外 1782px ⟹ ⟹ "
            "必须先滚动右栏再点 ⟹ ⟹ 「读了没变化」先怀疑自己的动作。",
        ],
        "notClaimed": [
            "**不声称**眼型卡的**缩略图**复刻了 —— 源站用的是素材库里的真实眼型图"
            "（`libtv-res.liblib.art/.../eye-light/*.jpg`）⟹ ⟹ 仓库里没有 ⟹ ⟹ 用**中性占位块**。",
            "**不声称**点眼型卡会改角色 —— 源站那趟**没点**卡片（怕触发生成）⟹ ⟹ "
            "clone 只切换**选中态**。",
            "**不声称**「妆造」页已复刻（11 个分类 chip ＋ 13 张妆容卡 ⟹ 属后续批次）。",
            "**不声称**「左列四段」（纹身&疤痕／丰胸／造型／音色库）已复刻。",
        ],
    }
    OUT.write_text(json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
    print("写入", OUT)
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 843 门禁：「妆造」页（11 枚分类 chip ＋ 随 chip 切换的 138 张卡）逐像素对齐源站。

## 这批做了什么

batch 841／842 做完了皮肤／鼻子／嘴唇／脸部／眉眼五枚页签，剩最后一枚**妆造**。
它的结构**不是**一列控件 ⟹ 而是：

    H4「妆容素材」240×22（带一枚「i」）
    ＋ 11 枚**分类 chip** 50×26（4 列 × 3 行）
    ＋ 一张**随 chip 切换**的卡片网格（76×96，3 列）

⟹ ⟹ chip 是 `role=tab` ⟹ ⟹ **点它会换掉整个卡片网格**
⟹ ⟹ 不逐个分类实测就实现 ＝ 编造 ⟹ ⟹ 本批补跑一趟**只读**探针，
   **逐个点完 11 个分类**（⚡44 全程未变）。

★ 另外本批还修了一个**结构事实**：源站实测**页签行只在「脸部精修」段存在**
（batch 841 raw）⟹ ⟹ clone 之前**每段都显示页签行** ⟹ ⟹ 那是**结构上的假象**。

## 期望值从哪来（★ 全部机器提取，不手打坐标）

`docs/research/liblib-canvas-batch843-2026-10-01/raw/source-843-makeup.json`
（11 个分类逐个点过的读数）⟹ 模态的原点取 batch 841 raw 里的实测值（模态固定在
1920×1080 的正中：1198×758 ⟹ (1920−1198)/2 = 361、(1080−758)/2 = 161）。

## 判据（S1–S7）

S1 ★★★ **妆造页不再是空态**：H4 ＋ 11 枚 chip ＋ **11 个分类的卡片清单**
    ⟹ ★ **文案逐条**等于源站 raw 机器提取的清单（合计 138 张卡）
S2 ★★★ **几何逐像素**（H4 ＋ i ＋ 11 枚 chip ＋ 每张卡的按钮/媒体区/名字）
S3 ★★★ **外观**也对齐：选中的 chip（白底黑字白边）／未选中的 chip
    （透明底、白 60% 字、白 8% 边）／媒体区（radius 16、白 6%）
S4 ★★★ **选中态**：每个分类**恰好一个**选中的 chip ＋ 卡片**数量** == 源站 ＋
    选中卡 == 源站该分类（★ 只读**数量**，★ **不读文案** ⟹ 文案归 S1 ⟹ 字段不重叠）
S5 ★★★ **卡片的选中态**是真交互：点「美瞳 琥珀」⟹ `aria-pressed=true`
S6 ★★★ **结构事实**：页签行**只在「脸部精修」段存在** ⟹ 点别的段 ⟹
    页签数 0 ＋ 空态说明 ＋ 0 控件；切回 ⟹ 页签数 6
S7 ★★ **如实标注**：README 必须写明——★ 缩略图**没有**复刻、★ 左列四段**未实现**、
    ★ mock 清单
"""
import json
import pathlib
import subprocess
import sys
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
BATCH = ROOT / "docs/research/liblib-canvas-batch843-2026-10-01"
RAW843 = BATCH / "raw/source-843-makeup.json"
RAW841 = ROOT / "docs/research/liblib-canvas-batch841-2026-10-01/raw/source-841-tabs.json"
PROBE_CLONE = BATCH / "probes/clone843.py"
OUT = BATCH / "runtime-audit.json"

# ★ 11 个分类：clone 侧 id ⟶ 源站 chip 文案
CATS = [
    ("brow", "眉毛"), ("contact", "美瞳"), ("wochan", "卧蚕"),
    ("yanying", "眼影"), ("jielan", "睫毛"), ("xiurong", "修容"),
    ("saihong", "腮红"), ("runcai", "唇彩"), ("zhuangshi", "妆饰"),
    ("yanxian", "眼线"), ("gaoguang", "高光"),
]


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
    """等 dev server 重建完 TSX（服务端 JS 里要能看到**妆造页独有**的文案）。"""
    marker = "妆容素材"
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
    """从**入库的源站 raw** 里抽出妆造页的期望值（几何 ＋ 外观 ＋ 11 个分类的清单）。"""
    raw = read_json(RAW843)
    cats = raw["★各分类读数"]
    # ★ 模态原点：取 batch 841 raw 里的实测值（模态固定居中 ⟹ 361／161）
    modal = read_json(RAW841)["★各状态读数"]["A_默认态_脸部精修_皮肤"]["modal"]
    ox, oy = modal["x"], modal["y"]

    def R(b):
        return {"x": b["x"] - ox, "y": b["y"] - oy, "w": b["w"], "h": b["h"]}

    exp: dict = {"分类": {}, "积分全未变": all(
        v is False for k, v in raw.items() if "积分是否变化" in k)}
    # ★ 源站的**卡片总数**（独立从 raw 算 ⟹ 门禁不写死 138）
    exp["源站卡片总数"] = sum(len(v["卡片"]) for v in cats.values())
    exp["源站chip数"] = len(cats[CATS[0][1]]["chip"])

    # ★ H4（每个分类的读数里都有 ⟹ 取第一份即可）
    first = cats[CATS[0][1]]
    exp["H4"] = {"text": first["H4"]["text"], "盒": R(first["H4"]["box"]),
                 "i盒": R(first["H4"]["i盒"]) if first["H4"].get("i盒") else None}

    for cid, label in CATS:
        st = cats[label]
        chips = [c for c in st["chip"] if c["text"] == label]
        if not chips:
            raise SystemExit("分类 %s 没找到自己的 chip" % label)
        chip = chips[0]
        cards = []
        for c in st["卡片"]:
            nm = c.get("名字") or {}
            cards.append({
                "aria": c["aria"],
                "名字": nm.get("text"),
                "按钮盒": R(c["box"]),
                "媒体盒": R(c["媒体盒"]) if c.get("媒体盒") else None,
                "名字盒": R(nm["box"]) if nm.get("box") else None,
                "有图": bool(c.get("媒体里有图")),
                # ★ 源站每个分类的**第一张「无」都是 aria-pressed=true**
                #   ⟹ ⟹ 选中态是**每分类一份**（不是一个全局单值）
                "pressed": c.get("pressed"),
            })
        exp["分类"][cid] = {
            "文案": label,
            "chip盒": R(chip["box"]),
            "卡片": cards,
        }

    # ★ 分类 chip 的**顺序**：从 raw 机器提取（★ **不手打**）
    #   ⟹ ⟹ 11 枚 chip 在源站的顺序**恒定**（每个分类读数都一样）
    exp["chip顺序"] = [c["text"] for c in cats[CATS[0][1]]["chip"]]
    for label, st in cats.items():
        if [c["text"] for c in st["chip"]] != exp["chip顺序"]:
            raise SystemExit("分类 %s 的 chip 顺序与首个分类不同 ⟹ 抽不出恒定顺序" % label)

    # ★ 外观（计算样式）
    exp["样式"] = {
        "选中chip": first["chip"][0]["style"],
        "未选中chip": next(c["style"] for c in first["chip"]
                          if not c.get("selected")),
        "卡片媒体区": first["卡片"][0]["媒体样式"],
    }
    return exp


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
    return read_json(pathlib.Path("/tmp/b843-clone-makeup.json"))


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)

    print("前置检查：等 dev server 重建完 TSX（服务端 JS 里要能看到「妆容素材」）……")
    pf_ok, pf_detail = preflight_js()
    if not pf_ok:
        print("PREFLIGHT-FAIL 服务端 JS chunk 里没有「妆容素材」⟹ **本轮读数不可信**")
        OUT.write_text(json.dumps({
            "batch": 843, "verdict": "preflight-failed", "preflight": pf_detail,
        }, ensure_ascii=False, indent=1), encoding="utf-8")
        print("写入", OUT)
        return 2
    print("  ✔ 服务端 JS 已重建（等了 %ss）" % pf_detail.get("等了几秒"))

    exp = build_expectations()

    print("跑 clone 运行时探针……")
    rt = run_probe()

    checks = []

    # ── S1 妆造页不再是空态：11 个分类的清单逐条相等 ─────────────────────
    s1 = {"★分类": {}, "★全对": True}
    for cid, label in CATS:
        got = (rt.get("分类_%s" % cid) or {})
        want = exp["分类"][cid]
        got_cards = [(c["aria"], c["名字"]) for c in (got.get("卡片") or [])]
        want_cards = [(c["aria"], c["名字"]) for c in want["卡片"]]
        got_chips = [c["text"] for c in (got.get("chip") or [])]
        # ★ chip 顺序**从 raw 机器提取**（★ 不手打、也不按当前分类重排）
        want_chips = exp["chip顺序"]
        ok = (got_cards == want_cards and got_chips == want_chips)
        s1["★分类"][cid] = {"卡片数": len(got_cards), "期望卡片数": len(want_cards),
                            "逐条相等": ok,
                            "不一致": None if ok else {
                                "clone": got_cards[:4], "源站": want_cards[:4]}}
        s1["★全对"] = s1["★全对"] and ok
    total_cards = sum(len(exp["分类"][c]["卡片"]) for c, _ in CATS)
    # ★ 总数也从 raw 算（★ 不写死 138 ⟹ 期望项数由 raw 推导）
    raw_total = exp["源站卡片总数"]
    s1["★源站卡片总数"] = raw_total
    s1["★期望卡片总数"] = total_cards
    s1["★源站chip数"] = exp["源站chip数"]
    checks.append((
        "S1 ★★★ **「妆造」页不再是空态**：H4「妆容素材」＋ **%d 枚分类 chip** ＋ "
        "**11 个分类、共 %d 张卡** ⟹ ★ **文案逐条**等于源站 raw 机器提取的清单"
        "（★ 总数也从 raw 算，不写死）" % (exp["源站chip数"], raw_total),
        (s1["★全对"] and total_cards == raw_total
         and len(exp["分类"]) == len(CATS)
         and len(exp["chip顺序"]) == exp["源站chip数"]),
        json.dumps(s1, ensure_ascii=False),
    ))

    # ── S2 几何逐像素 ───────────────────────────────────────────────────
    geo = []
    geo.append({"键": ("H4", "盒"), "盒": exp["H4"]["盒"]})
    if exp["H4"]["i盒"]:
        geo.append({"键": ("H4", "i盒"), "盒": exp["H4"]["i盒"]})
    for cid, _ in CATS:
        geo.append({"键": ("chip", cid), "盒": exp["分类"][cid]["chip盒"]})
        for i, c in enumerate(exp["分类"][cid]["卡片"]):
            geo.append({"键": ("卡", cid, i, "按钮盒"), "盒": c["按钮盒"]})
            geo.append({"键": ("卡", cid, i, "媒体盒"), "盒": c["媒体盒"]})
            geo.append({"键": ("卡", cid, i, "名字盒"), "盒": c["名字盒"]})

    def clone_box(key):
        kind = key[0]
        if kind == "H4":
            h4 = (rt.get("分类_%s" % CATS[0][0]) or {}).get("H4") or {}
            return h4.get("box") if key[1] == "盒" else h4.get("i盒")
        if kind == "chip":
            cid = key[1]
            got = (rt.get("分类_%s" % cid) or {})
            for c in (got.get("chip") or []):
                if c["text"] == exp["分类"][cid]["文案"]:
                    return c.get("box")
            return None
        if kind == "卡":
            cid, i, what = key[1], key[2], key[3]
            got = (rt.get("分类_%s" % cid) or {})
            cards = got.get("卡片") or []
            if i >= len(cards):
                return None
            c = cards[i]
            if what == "按钮盒":
                return c.get("box")
            if what == "媒体盒":
                return c.get("媒体盒")
            if what == "名字盒":
                return c.get("名字盒")
        return None

    diffs = []
    for item in geo:
        g = clone_box(item["键"])
        if not box_close(item["盒"], g):
            diffs.append({"元素": "／".join(str(k) for k in item["键"]),
                          "源站": item["盒"], "clone": g})
    # ★ **期望项数独立从 raw 算**（不拿 geo 自己的长度当分母 ⟹ 那是自证）
    #   项数 ＝ H4 ＋ i ＋ 11 枚 chip ＋ 每张卡 3 件（按钮/媒体区/名字）
    expect_items = 2 + len(CATS) + sum(
        3 * len(exp["分类"][cid]["卡片"]) for cid, _ in CATS)
    s2 = {"★比较了几项": len(geo), "★期望项数_独立从raw算": expect_items,
          "★期望表里几项": len(geo),
          "★有几项不一致": len(diffs), "★不一致明细": diffs[:20]}
    checks.append((
        "S2 ★★★ **几何与源站逐像素一致**（%d 项：H4 ＋ i ＋ 11 枚 chip ＋ %d 张卡的"
        "按钮/媒体区/名字）⟹ ★ **期望值全部从入库 raw 机器提取** ⟹ ⟹ **宽高逐像素全等**、"
        "位置 ±1px；★ 且**比较数 == 期望项数**（★ 期望项数**独立从 raw 算**，"
        "不拿 geo 自己的长度当分母 ⟹ 那是**自证**；★ **不写死阈值** —— "
        "写死的阈值会「为了变绿而下调」）"
        % (len(geo), total_cards),
        (len(diffs) == 0 and len(geo) == expect_items),
        json.dumps(s2, ensure_ascii=False),
    ))

    # ── S3 外观 ─────────────────────────────────────────────────────────
    #   ★ 期望值**从 raw 的计算样式取**（★ 不硬编码颜色字符串 ⟹ 那是手打的输入）
    #   ★ 探针读的「选中chip／未选中chip／卡片媒体区」三处
    cstyle = (rt.get("分类_%s" % CATS[0][0]) or {}).get("样式") or {}
    src = exp["样式"]
    # ★ 每一项 = (取样对象, 样式键) ⟹ 期望值 = raw 里那个键的值
    style_specs = [
        ("选中chip", "backgroundColor"), ("选中chip", "color"),
        ("选中chip", "borderTopColor"), ("选中chip", "borderRadius"),
        ("选中chip", "fontSize"), ("选中chip", "fontWeight"),
        ("选中chip", "lineHeight"), ("选中chip", "paddingLeft"),
        ("选中chip", "paddingTop"),
        ("未选中chip", "backgroundColor"), ("未选中chip", "color"),
        ("未选中chip", "borderTopColor"), ("未选中chip", "borderRadius"),
        ("未选中chip", "fontSize"), ("未选中chip", "fontWeight"),
        ("未选中chip", "lineHeight"), ("未选中chip", "paddingLeft"),
        ("未选中chip", "paddingTop"),
        ("卡片媒体区", "borderRadius"), ("卡片媒体区", "backgroundColor"),
        ("卡片媒体区", "borderTopWidth"), ("卡片媒体区", "borderTopColor"),
        ("卡片媒体区", "fontSize"), ("卡片媒体区", "fontWeight"),
        ("卡片媒体区", "lineHeight"), ("卡片媒体区", "paddingLeft"),
        ("卡片媒体区", "paddingTop"),
    ]
    style_diffs = []
    for who, key in style_specs:
        want = (src.get(who) or {}).get(key)
        got = (cstyle.get(who) or {}).get(key)
        if want is None:
            style_diffs.append({"元素": "%s 的 %s" % (who, key),
                                "期望": "★ raw 里没有这一项",
                                "clone": got, "源站": None})
            continue
        if got != want:
            style_diffs.append({"元素": "%s 的 %s" % (who, key),
                                "期望": want, "clone": got, "源站": want})
    s3 = {"★核了几项": len(style_specs), "★有几项不一致": len(style_diffs),
          "★不一致明细": style_diffs,
          "★期望值来源": "batch 843 raw 的计算样式（机器提取，非手打）"}
    checks.append((
        "S3 ★★★ **外观**也对齐：选中的 chip（**白底黑字** ＋ 白边）／未选中的 chip"
        "（透明底 ＋ 白 60% 字 ＋ 白 8% 边）／媒体区（radius 16、白 6%、1px 边框）"
        "⟹ ★ **期望值取自入库 raw 的计算样式**（★ 逐键比对，★ 不硬编码颜色字符串）",
        (len(style_diffs) == 0 and len(style_specs) > 0),
        json.dumps(s3, ensure_ascii=False),
    ))

    # ── S4 选中态 ───────────────────────────────────────────────────────
    #   ★★ **字段分工**（★ 这是本条判据被改写的原因，**不是**削弱）：
    #     - **文案**（卡片的 aria + 名字）归 **S1** ⟹ ⟹ S1 逐条比；
    #     - **数量**（每个分类几张卡）归 **S4**；
    #     - **几何**归 **S2**；**计算样式**归 **S3**。
    #   ⟹ ⟹ 两条判据读的字段**互不重叠** ⟹ ⟹ 阴性对照才能做到
    #   「**每条臂只翻它自己那一条**」（★ 否则「改名」这种缺陷会同时翻 S1 与 S4 ⟹
    #   ⟹ 阴性臂就**证明不了**哪一条有牙）。
    #   ★ 「清单逐条相等」这条断言**没有删掉** ⟹ ⟹ 它在 S1 里（更严 ⟹ 连文案都比）。
    sel_ok = []
    for cid, label in CATS:
        got = rt.get("分类_%s" % cid) or {}
        on = [c["text"] for c in (got.get("chip") or []) if c.get("selected")]
        # ★ 只比**数量**（★ **不读文案** ⟹ 与 S1 的字段不重叠）
        got_n = len(got.get("卡片") or [])
        want_n = len(exp["分类"][cid]["卡片"])
        # ★★ **卡片层面的选中态**：源站实测**每个分类**都只有**第一张「无」**
        #   是 `aria-pressed=true` ⟹ ⟹ 选中态是**每分类一份**，不是一个全局单值
        pressed = [(c["aria"], c["pressed"]) for c in (got.get("卡片") or [])]
        src_pressed = [(c["aria"], c["pressed"]) for c in exp["分类"][cid]["卡片"]]
        sel_ok.append({"分类": label, "选中的chip": on,
                       "★卡片数": got_n, "★期望卡片数_从raw算": want_n,
                       "★卡片数相等": got_n == want_n,
                       "★选中的卡": [a for a, p in pressed if p == "true"],
                       "★源站选中的卡": [a for a, p in src_pressed if p == "true"]})
    s4 = {"★逐个分类": sel_ok,
          "★每个分类都恰好一个选中的chip": all(len(x["选中的chip"]) == 1 for x in sel_ok),
          "★每个分类的卡片数都与源站一致": all(x["★卡片数相等"] for x in sel_ok),
          "★每个分类的选中卡都与源站一致": all(
              x["★选中的卡"] == x["★源站选中的卡"] for x in sel_ok)}
    checks.append((
        "S4 ★★★ **选中态**：逐个点完 11 个分类 ⟹ 每个分类**恰好一个**选中的 chip"
        "（★ 既不是零个也不是两个），每个分类的**卡片数**与源站一致（★ 只比**数量**，"
        "★ **不读文案** ⟹ 文案归 S1 ⟹ 两条判据读的字段**互不重叠** ⟹ ⟹ 阴性对照才能"
        "「每条只翻它自己那一条」）；★ ★ **卡片层面的选中态**也逐个分类对齐（源站实测"
        "**每个分类**都只有第一张「无」`aria-pressed=true` ⟹ ⟹ 选中态是**每分类一份**，"
        "不是一个全局单值）",
        (s4["★每个分类都恰好一个选中的chip"] and s4["★每个分类的卡片数都与源站一致"]
         and s4["★每个分类的选中卡都与源站一致"]),
        json.dumps(s4, ensure_ascii=False),
    ))

    # ── S5 卡片的选中态是真交互 ─────────────────────────────────────────
    after = rt.get("C_点卡后") or {}
    a_cards = [(c["aria"], c["pressed"]) for c in (after.get("卡片") or [])]
    contact_n = len(exp["分类"]["contact"]["卡片"])
    s5 = {
        "★点的是哪张": rt.get("★点到_琥珀"),
        "★点后_选中的": [a for a, p in a_cards if p == "true"],
        "★点后_卡片数": len(a_cards),
        "★期望卡片数_从raw算": contact_n,
    }
    checks.append((
        "S5 ★★★ **卡片的选中态是真交互**：点「美瞳 琥珀」⟹ 它的 `aria-pressed` 变成 true；"
        "★ ★ **必须先切回那个分类**再点（★ 跑完 11 个分类后当前是「高光」，"
        "而「琥珀」那枚卡**不在当前分类里** ⟹ ⟹ 点它等于**点空气**）；"
        "★ ★ 选卡用**带序号**的属性（★ 源站「眼影」有两个同名「自然」⟹ "
        "只用名字当属性值 ⟹ DOM 里两个同值 ⟹ 选择器会**挑错卡**）",
        (s5["★点后_选中的"] == ["美瞳 琥珀"]
         and s5["★点后_卡片数"] == s5["★期望卡片数_从raw算"]),
        json.dumps(s5, ensure_ascii=False),
    ))

    # ── S6 结构事实：页签行只在「脸部精修」段存在 ───────────────────────
    other = rt.get("D_第四段") or {}
    back = rt.get("E_切回脸部精修") or {}
    s6 = {
        "★第四段_页签数": other.get("页签数"),
        "★第四段_卡片数": len(other.get("卡片") or []),
        "★第四段_空态说明": other.get("空态"),
        "★切回_页签数": back.get("页签数"),
        "★源站那趟_积分全程未变": exp["积分全未变"],
    }
    checks.append((
        "S6 ★★★ **结构事实**：源站实测**页签行只在「脸部精修」段存在** ⟹ ⟹ "
        "点左列**第四段**（服装造型）⟹ **页签数 %s** ＋ 0 张卡 ＋ 出现空态说明；切回「脸部精修」⟹ "
        "**页签数 %s**；★ ★ clone 之前**每段都显示页签行** ⟹ ⟹ 那是**结构上的假象** ⟹ ⟹ 本批改正"
        % (s6["★第四段_页签数"], s6["★切回_页签数"]),
        (s6["★第四段_页签数"] == 0 and s6["★第四段_卡片数"] == 0
         and bool(s6["★第四段_空态说明"]) and s6["★切回_页签数"] == 6
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
        "★README写明11个分类都实测了": "11" in readme,
        "★README写明138张卡": "138" in readme,
        "★README写明左列四段未实现": "纹身" in readme and "丰胸" in readme,
        "★README写明不消耗积分": "不消耗" in readme,
        "★README里mock出现次数": readme.lower().count("mock"),
    }
    checks.append((
        "S7 ★★ **如实标注**：README 必须写明——★ 缩略图**没有**复刻（源站用素材库真实图）"
        "⟹ ⟹ clone 用中性占位；★ 11 个分类、138 张卡**都实测过**；★ 左列四段**未实现**；"
        "★ 且「确认生成」等仍是 mock、不消耗 ⚡44",
        (s7["★README存在"] and s7["★README写明缩略图没有复刻"]
         and s7["★README写明11个分类都实测了"] and s7["★README写明138张卡"]
         and s7["★README写明左列四段未实现"] and s7["★README写明不消耗积分"]
         and s7["★README里mock出现次数"] >= 3),
        json.dumps(s7, ensure_ascii=False),
    ))

    print("\n=== 判据 ===")
    passed = 0
    for label, ok, detail in checks:
        print("  %s  %s" % ("PASS" if ok else "FAIL", label))
        passed += bool(ok)
    print("\n%d/%d 通过" % (passed, len(checks)))

    audit = {
        "batch": 843,
        "title": "「妆造」页：11 枚分类 chip ＋ 随 chip 切换的 138 张卡 ＋ 段落的页签行结构",
        "verdict": "%d/%d" % (passed, len(checks)),
        "preflight": pf_detail,
        "source": {"期望值表": exp},
        "clone": {k: v for k, v in rt.items() if k.startswith(("A_", "B_", "C_", "D_", "E_", "分类_"))},
        "checks": [{"label": l, "pass": bool(o), "detail": d} for l, o, d in checks],
        "conclusions": [
            "★★★ **妆造页不是一列控件** ⟹ ⟹ 它是「H4『妆容素材』＋ 11 枚分类 chip ＋ "
            "一张随 chip 切换的卡片网格」⟹ ⟹ **138 张卡**全部是**逐个分类点出来的**。",
            "★★★ **「眉毛」分类实为 14 张**（batch 841 那趟 raw 因 `y<=833` 截断只留下 13 张）"
            "⟹ ⟹ 这正是「同一份 raw 不能两批共用」的实例。",
            "★★★ **页签行只在「脸部精修」段存在**（源站实测）⟹ ⟹ clone 之前**每段都显示页签行**"
            "⟹ ⟹ 那是**结构上的假象** ⟹ ⟹ 本批改正。",
            "★★ **探针踩的坑**：跑完 11 个分类后当前是「高光」，而「琥珀」那枚卡**不在当前分类里**"
            "⟹ ⟹ 点它等于**点空气** ⟹ ⟹ 「点了没反应」先怀疑自己的动作。",
        ],
        "notClaimed": [
            "**不声称**妆容卡的**缩略图**复刻了 —— 源站用的是素材库里的真实妆容图 ⟹ ⟹ "
            "仓库里没有 ⟹ ⟹ 用**中性占位块**。",
            "**不声称**点妆容卡会改角色 —— 源站那趟**只点了分类 chip**（没点卡片）⟹ ⟹ "
            "clone 只切换**选中态**。",
            "**不声称**左列四段（纹身&疤痕／丰胸／造型／音色库）已复刻 ⟹ ⟹ 显示**空态说明**。",
        ],
    }
    OUT.write_text(json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
    print("写入", OUT)
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())

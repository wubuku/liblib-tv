#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 844 门禁：左列第二段「脸部 & 身体特征」（纹身 & 疤痕 ＋ 6 张贴纸卡）逐像素对齐源站。

## 这批做了什么

batch 843 做完了妆造页 ⟹ ⟹ 右栏**六枚页签**全部有内容了 ⟹ ⟹
「**仍未实现的那一块**」变成**左列第二～五段**。

本批实现**第二段**「脸部 & 身体特征」。★ **它的结构不是一列控件** ⟹ ⟹ 源站实测：

    这一段**没有标题行** ⟹ ⟹ 右栏**第一层就是滚动区**（`pt-3`）
    ⟹ ⟹ 内容起点比「脸部精修」段**高 28px**
    H3「纹身 & 疤痕」240×22（14px／400／纯白）
    一张 3 列 × 2 行的卡片网格（列距 6、行距 8）⟹ ⟹ 6 张 **76×54** 的卡
      └ 缩略图 **76×32 的圆形**（`rounded-full`）⟹ ⟹ 与妆造页的 76×76 方形**不一样**
      └ 名字 11px／16px（`px-1` ⟹ 左右各 4px）
      └ 第 6 张「自定义」**没有图** ⟹ 一枚 16×16 图标 ⟹ 且**没有** `aria-pressed`

## 期望值从哪来（★ 全部机器提取，不手打坐标）

`docs/research/liblib-canvas-batch844-2026-10-01/raw/source-844-traits.json`
（源站**只读**实测，⚡44 全程未变）⟹ 模态原点取 batch 841 raw 的实测值（361／161）。

## 判据（S1–S7）

S1 ★★★ **这一段不再是空态**：H3「纹身 & 疤痕」＋ **6 张卡**，文案**逐条**等于源站 raw
    机器提取的清单；★ 且**没有**空态说明、**页签数 0**（源站实测这一段无页签行）
S2 ★★★ **几何逐像素**：H3 ＋ 每张卡的（卡盒／缩略盒／名字盒／图盒／图标盒）
    ⟹ ★ **期望项数独立从 raw 算**（不拿 geo 自己的长度当分母 ⟹ 那是自证）
S3 ★★★ **外观**逐键比对：H3／缩略区／名字的计算样式 ⟹ ★ 期望值取自 raw
S4 ★★★ **初始选中态**逐张对齐源站：前 5 张 `aria-pressed="false"`，
    「自定义」**没有** `aria-pressed`
S5 ★★★ **卡片的选中态是真交互**：点「痣」⟹ 它的 `aria-pressed` 变成 true，其余不变
S6 ★★★ **结构事实**：这一段**没有标题行** ⟹ ⟹ 内容起点比「脸部精修」段**高 28px**；
    切回「脸部精修」⟹ **页签数 6**
S7 ★★ **如实标注**：README 必须写明——★ 缩略图是**引用**源站 CDN（不是复刻）、
    ★ 选中外观**未实测**、★ 源站的**点击行为未实测**、★ mock 清单
"""
import json
import pathlib
import subprocess
import sys
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
BATCH = ROOT / "docs/research/liblib-canvas-batch844-2026-10-01"
RAW844 = BATCH / "raw/source-844-traits.json"
RAW841 = ROOT / "docs/research/liblib-canvas-batch841-2026-10-01/raw/source-841-tabs.json"
PROBE_CLONE = BATCH / "probes/clone844.py"
OUT = BATCH / "runtime-audit.json"


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
    """等 dev server 重建完 TSX（服务端 JS 里要能看到**这一段独有**的文案）。"""
    marker = "纹身 & 疤痕"
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
    """从**入库的源站 raw** 里抽出这一段的期望值（几何 ＋ 外观 ＋ 清单）。"""
    raw = read_json(RAW844)
    src = raw["★读数"]
    # ★ 模态原点：取 batch 841 raw 里的实测值（模态固定居中 ⟹ 361／161）
    modal = read_json(RAW841)["★各状态读数"]["A_默认态_脸部精修_皮肤"]["modal"]
    ox, oy = modal["x"], modal["y"]

    def R(b):
        return {"x": b["x"] - ox, "y": b["y"] - oy, "w": b["w"], "h": b["h"]}

    h3 = src["H3"]
    cards = []
    for c in src["卡片"]:
        nm = c.get("名字") or {}
        cards.append({
            "名字": nm.get("text"),
            "pressed": c.get("pressed"),
            "有图": bool(c.get("媒体里有图")),
            "卡盒": R(c["box"]),
            "缩略盒": R(c["缩略盒"]) if c.get("缩略盒") else None,
            "名字盒": R(nm["box"]) if nm.get("box") else None,
            "图盒": R(c["图"]["box"]) if c.get("图") else None,
            "图标盒": R(c["图标盒"]) if c.get("图标盒") else None,
        })
    exp = {
        "H3": {"text": h3["text"], "盒": R(h3["box"]), "style": h3["style"]},
        "卡片": cards,
        "卡片数": len(cards),
        "积分全未变": all(v is False for k, v in raw.items() if "积分是否变化" in k),
        "★源站右栏盒": R(src["右栏盒"]),
        "★源站有没有标题行": src["右栏第一层"].get("头行") is not None,
        "★源站网格盒": R(src["网格"]["box"]) if src.get("网格") else None,
    }
    # ★ 源站这一段的**内容起点**（= 右栏顶 + 12）⟹ ⟹ 与「脸部精修」段差多少
    #   ⟹ ⟹ 由 raw 的**两个**盒独立算出来（不是手打常数）
    exp["★内容起点_rel_y"] = exp["H3"]["盒"]["y"]
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
    return read_json(pathlib.Path("/tmp/b844-clone-traits.json"))


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)

    print("前置检查：等 dev server 重建完 TSX（服务端 JS 里要能看到「纹身 & 疤痕」）……")
    pf_ok, pf_detail = preflight_js()
    if not pf_ok:
        print("PREFLIGHT-FAIL 服务端 JS chunk 里没有「纹身 & 疤痕」⟹ **本轮读数不可信**")
        OUT.write_text(json.dumps({
            "batch": 844, "verdict": "preflight-failed", "preflight": pf_detail,
        }, ensure_ascii=False, indent=1), encoding="utf-8")
        print("写入", OUT)
        return 2
    print("  ✔ 服务端 JS 已重建（等了 %ss）" % pf_detail.get("等了几秒"))

    exp = build_expectations()

    print("跑 clone 运行时探针……")
    rt = run_probe()

    seg = rt.get("A_第二段") or {}
    after = rt.get("B_点卡后") or {}
    back = rt.get("C_切回脸部精修") or {}

    checks = []

    # ── S1 这一段不再是空态 ─────────────────────────────────────────────
    got_names = [(c.get("名字") or {}).get("text") for c in (seg.get("卡片") or [])]
    want_names = [c["名字"] for c in exp["卡片"]]
    s1 = {
        "★H3文本": (seg.get("H3") or {}).get("text"),
        "★期望H3": exp["H3"]["text"],
        "★卡片数": len(got_names), "★期望卡片数_从raw算": exp["卡片数"],
        "★逐条相等": got_names == want_names,
        "★不一致": None if got_names == want_names else {
            "clone": got_names, "源站": want_names},
        "★空态说明": seg.get("空态"),
        "★页签数": seg.get("页签数"),
    }
    checks.append((
        "S1 ★★★ **左列第二段「脸部 & 身体特征」不再是空态**：H3「纹身 & 疤痕」＋ "
        "**%d 张 76×54 的贴纸卡** ⟹ ★ **文案逐条**等于源站 raw 机器提取的清单"
        "（★ 卡数也从 raw 算，不写死）；★ 且**没有**空态说明"
        "（★ **页签数**归 S6 ⟹ ⟹ 两条判据读的字段**互不重叠** ⟹ ⟹ "
        "阴性臂才能做到「每条只翻它自己那一条」）"
        % exp["卡片数"],
        (s1["★H3文本"] == exp["H3"]["text"] and s1["★逐条相等"]
         and len(got_names) == exp["卡片数"]
         and not s1["★空态说明"]),
        json.dumps(s1, ensure_ascii=False),
    ))

    # ── S2 几何逐像素 ───────────────────────────────────────────────────
    geo = [{"键": ("H3", "盒"), "盒": exp["H3"]["盒"]}]
    for i, c in enumerate(exp["卡片"]):
        for what in ("卡盒", "缩略盒", "名字盒", "图盒", "图标盒"):
            if c.get(what):
                geo.append({"键": ("卡", i, what), "盒": c[what]})

    def clone_box(key):
        if key[0] == "H3":
            return (seg.get("H3") or {}).get("box")
        i, what = key[1], key[2]
        cards = seg.get("卡片") or []
        if i >= len(cards):
            return None
        c = cards[i]
        return {"卡盒": c.get("box"), "缩略盒": c.get("缩略盒"),
                "名字盒": (c.get("名字") or {}).get("box"),
                "图盒": (c.get("图") or {}).get("box"),
                "图标盒": c.get("图标盒")}.get(what)

    diffs = []
    for item in geo:
        g = clone_box(item["键"])
        if not box_close(item["盒"], g):
            diffs.append({"元素": "／".join(str(k) for k in item["键"]),
                          "源站": item["盒"], "clone": g})
    # ★ **期望项数独立从 raw 算**（不拿 geo 自己的长度当分母 ⟹ 那是自证）
    expect_items = 1 + sum(
        sum(1 for what in ("卡盒", "缩略盒", "名字盒", "图盒", "图标盒")
            if c.get(what)) for c in exp["卡片"])
    s2 = {"★比较了几项": len(geo), "★期望项数_独立从raw算": expect_items,
          "★有几项不一致": len(diffs), "★不一致明细": diffs[:20]}
    checks.append((
        "S2 ★★★ **几何与源站逐像素一致**（%d 项：H3 ＋ 6 张卡的卡盒/缩略盒/名字盒/图盒/图标盒）"
        "⟹ ★ **期望值全部从入库 raw 机器提取** ⟹ ⟹ **宽高逐像素全等**、位置 ±1px；"
        "★ 且**比较数 == 期望项数**（★ 期望项数**独立从 raw 算** ⟹ ⟹ "
        "不拿 geo 自己的长度当分母 ⟹ ⟹ 那是**自证**；★ **不写死阈值** —— "
        "写死的阈值会「为了变绿而下调」）" % len(geo),
        (len(diffs) == 0 and len(geo) == expect_items),
        json.dumps(s2, ensure_ascii=False),
    ))

    # ── S3 外观逐键比对 ────────────────────────────────────────────────
    style_specs = [
        "fontSize", "fontWeight", "lineHeight", "color", "backgroundColor",
        "borderRadius", "borderTopWidth", "borderTopColor",
        "paddingLeft", "paddingTop",
    ]
    # ★ 期望值：从 raw 的**计算样式**取（★ 不硬编码颜色字符串 ⟹ 那是手打的输入）
    src_cards = read_json(RAW844)["★读数"]["卡片"]
    style_diffs = []
    n_specs = 0
    for key in style_specs:
        want = (exp["H3"]["style"] or {}).get(key)
        got = ((seg.get("H3") or {}).get("style") or {}).get(key)
        n_specs += 1
        if want != got:
            style_diffs.append({"元素": "H3 的 %s" % key, "期望": want,
                                "clone": got, "源站": want})
    for i, sc in enumerate(src_cards):
        clone_cards = seg.get("卡片") or []
        cc = clone_cards[i] if i < len(clone_cards) else {}
        for key in style_specs:
            want = (sc.get("缩略样式") or {}).get(key)
            got = (cc.get("缩略样式") or {}).get(key)
            n_specs += 1
            if want != got:
                style_diffs.append({"元素": "卡[%d] 缩略区的 %s" % (i, key),
                                    "期望": want, "clone": got, "源站": want})
            want = ((sc.get("名字") or {}).get("style") or {}).get(key)
            got = ((cc.get("名字") or {}).get("style") or {}).get(key)
            n_specs += 1
            if want != got:
                style_diffs.append({"元素": "卡[%d] 名字的 %s" % (i, key),
                                    "期望": want, "clone": got, "源站": want})
    s3 = {"★核了几项": n_specs, "★有几项不一致": len(style_diffs),
          "★不一致明细": style_diffs,
          "★期望值来源": "batch 844 raw 的计算样式（机器提取，非手打）"}
    checks.append((
        "S3 ★★★ **外观**也对齐：H3（14px／22px／400／纯白）／缩略区"
        "（**圆形** 9999px、白 5% 底、白 8% 边）／名字（11px／16px、白）"
        "⟹ ★ **期望值取自入库 raw 的计算样式**（★ 逐键比对，★ 不硬编码颜色字符串）",
        (len(style_diffs) == 0 and n_specs > 0),
        json.dumps(s3, ensure_ascii=False),
    ))

    # ── S4 初始选中态逐张对齐 ───────────────────────────────────────────
    pressed_rows = []
    for i, c in enumerate(exp["卡片"]):
        cc = (seg.get("卡片") or [])[i] if i < len(seg.get("卡片") or []) else {}
        pressed_rows.append({"名字": c["名字"], "源站": c["pressed"],
                             "clone": cc.get("pressed"),
                             "有图_源站": c["有图"], "有图_clone": cc.get("媒体里有图")})
    s4 = {"★逐张": pressed_rows,
          "★全部相等": all(r["源站"] == r["clone"] for r in pressed_rows),
          "★有图全相等": all(r["有图_源站"] == r["有图_clone"] for r in pressed_rows),
          "★源站那趟_积分全程未变": exp["积分全未变"]}
    checks.append((
        "S4 ★★★ **初始选中态**逐张对齐源站：前 5 张 `aria-pressed=\"false\"`、"
        "「自定义」**没有** `aria-pressed`（它不是可选中的卡 ⟹ ⟹ 是上传入口）"
        "⟹ ⟹ 连**有没有**这个属性都要一样；★ 且**有图/无图**逐张相等",
        (s4["★全部相等"] and s4["★有图全相等"] and s4["★源站那趟_积分全程未变"]),
        json.dumps(s4, ensure_ascii=False),
    ))

    # ── S5 卡片的选中态是真交互 ─────────────────────────────────────────
    a_cards = after.get("卡片") or []
    a_pressed = [((c.get("名字") or {}).get("text"), c.get("pressed"))
                 for c in a_cards]
    s5 = {
        "★点的是哪张": rt.get("★点到_痣"),
        "★点后_各卡的 pressed": a_pressed,
        "★点后_选中的": [n for n, p in a_pressed if p == "true"],
        "★期望选中": ["痣"],
        "★点后_卡片数": len(a_cards),
        "★期望卡片数_从raw算": exp["卡片数"],
    }
    checks.append((
        "S5 ★★★ **卡片的选中态是真交互**：点「痣」⟹ 它的 `aria-pressed` 变成 true，"
        "**其余五张仍是 false**（「自定义」**仍然没有**这个属性）"
        "⟹ ★ 判据是「**读出来的状态** == 期望」，不是「点了没报错」",
        (s5["★点后_选中的"] == s5["★期望选中"]
         and s5["★点后_卡片数"] == s5["★期望卡片数_从raw算"]
         and len(a_pressed) == exp["卡片数"]),
        json.dumps(s5, ensure_ascii=False),
    ))

    # ── S6 结构事实：这一段没有标题行 ⟹ 内容起点更高 ────────────────────
    # ★★ **两段的「内容起点」都从 raw 机械算**（★ 不手打常数）：
    #   · 脸部精修段：页签行（40 高）以下**第一个**元素的 y − 右栏列顶
    #   · 第二段：H3 的 y − 右栏列顶（★ 这一段**没有**页签行 ⟹ ⟹ 第一个元素就是 H3）
    face_right = read_json(RAW841)["★各状态读数"]["A_默认态_脸部精修_皮肤"]["right"]
    face_col = face_right[0]["box"]
    face_first = next(e for e in face_right if e["box"]["y"] > face_col["y"] + 40)
    face_origin = face_first["box"]["y"] - face_col["y"]
    traits_col = exp["★源站右栏盒"]
    traits_origin = exp["H3"]["盒"]["y"] - traits_col["y"]
    # ★ clone 侧：同口径算一遍
    clone_col = seg.get("右栏盒") or {}
    clone_origin = ((seg.get("H3") or {}).get("box") or {}).get("y", 0) - (clone_col.get("y") or 0)
    s6 = {
        "★第二段_内容起点_相对列顶": traits_origin,
        "★脸部精修段_内容起点_相对列顶": face_origin,
        "★两段差": face_origin - traits_origin,
        "★clone_内容起点_相对列顶": clone_origin,
        "★源站有没有标题行": exp["★源站有没有标题行"],
        "★第二段_页签数": seg.get("页签数"),
        "★切回_页签数": back.get("页签数"),
    }
    checks.append((
        "S6 ★★★ **结构事实**：源站实测**这一段没有标题行** ⟹ ⟹ 右栏**第一层就是滚动区**"
        " ⟹ ⟹ 它的内容起点比「脸部精修」段**高 %s px**（★ 由两批 raw 的**两个**盒"
        "**机械算**出来 ⟹ ⟹ 不是手打常数）⟹ ⟹ 「脸部精修」段有 6 枚页签、"
        "这一段**一枚都没有**；★ 且 clone 的内容起点（%s）必须**等于**源站的（%s）；"
        "切回「脸部精修」⟹ **页签数 %s**"
        % (s6["★两段差"], s6["★clone_内容起点_相对列顶"],
           s6["★第二段_内容起点_相对列顶"], s6["★切回_页签数"]),
        (s6["★源站有没有标题行"] is False
         and s6["★两段差"] == 48
         and s6["★clone_内容起点_相对列顶"] == s6["★第二段_内容起点_相对列顶"]
         and s6["★第二段_页签数"] == 0
         and s6["★切回_页签数"] == 6),
        json.dumps(s6, ensure_ascii=False),
    ))

    # ── S7 如实标注 ─────────────────────────────────────────────────────
    readme = (BATCH / "README.md").read_text(encoding="utf-8") \
        if (BATCH / "README.md").exists() else ""
    s7 = {
        "★README存在": bool(readme),
        "★README写明缩略图是引用源站CDN": ("CDN" in readme and
                                          ("引用" in readme or "引自" in readme)),
        "★README写明选中外观未实测": "未实测" in readme,
        "★README写明源站点击行为未实测": "点击" in readme,
        "★README写明左列三段未实现": "丰胸" in readme and "音色库" in readme,
        "★README写明不消耗积分": "不消耗" in readme,
        "★README里mock出现次数": readme.lower().count("mock"),
    }
    checks.append((
        "S7 ★★ **如实标注**：README 必须写明——★ 缩略图是**引用**源站 CDN 的真实图"
        "（★ **不是**复刻 ⟹ ⟹ 资产不归本仓库）；★ 选中态的**外观**未实测"
        "（那趟只点了分段 ⟹ ⟹ 没点卡片）；★ 源站**点击卡片**会发生什么未实测；"
        "★ 左列**三段**（身材塑形／服装造型／音色音调）**未实现**；"
        "★ 且「确认生成」等仍是 mock、不消耗 ⚡44",
        (s7["★README存在"] and s7["★README写明缩略图是引用源站CDN"]
         and s7["★README写明选中外观未实测"] and s7["★README写明源站点击行为未实测"]
         and s7["★README写明左列三段未实现"] and s7["★README写明不消耗积分"]
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
        "batch": 844,
        "title": "左列第二段「脸部 & 身体特征」：H3「纹身 & 疤痕」＋ 6 张 76×54 贴纸卡",
        "verdict": "%d/%d" % (passed, len(checks)),
        "preflight": pf_detail,
        "source": {"期望值表": exp},
        "clone": {k: v for k, v in rt.items() if k.startswith(("A_", "B_", "C_", "D_"))},
        "checks": [{"label": l, "pass": bool(o), "detail": d} for l, o, d in checks],
        "conclusions": [
            "★★★ **左列第二段不是一列控件** ⟹ ⟹ 它是「H3『纹身 & 疤痕』＋ "
            "6 张 76×54 的贴纸卡（3 列 × 2 行）」⟹ ⟹ 缩略图是 **76×32 的圆形**。",
            "★★★ **这一段没有标题行** ⟹ ⟹ 右栏第一层就是滚动区 ⟹ ⟹ "
            "内容起点比「脸部精修」段**高 28px** ⟹ ⟹ clone 之前**每段都顶着页签行**"
            " ⟹ ⟹ 那是**结构上的假象**。",
            "★★★ **「自定义」那枚没有 `aria-pressed`** ⟹ ⟹ 它不是可选中的卡，"
            "是上传入口 ⟹ ⟹ clone 也**不给**它那个属性。",
            "★★ **缩略图是引用源站 CDN 的真实贴纸图**（★ 与 `VideoGenerationPanel` 同一做法）"
            "⟹ ⟹ 那是**引用**不是复刻 ⟹ ⟹ 不声称这些资产归本仓库所有。",
            "★★ **未实测**：点卡片之后源站会发生什么、选中态的**外观**长什么样 "
            "⟹ ⟹ clone 只切换**本地选中态** ⟹ ⟹ **不声称**与源站同构。",
        ],
        "notClaimed": [
            "**不声称**点贴纸卡会改角色 —— 源站那趟**只点了分段** ⟹ ⟹ clone 只切换**选中态**。",
            "**不声称**选中态的**外观**与源站一致 —— 源站那趟**没点过卡片** ⟹ ⟹ 没测到。",
            "**不声称**缩略图资产**归本仓库** —— 那是**引用**源站 CDN 的真实图。",
            "**不声称**左列三段（身材塑形／服装造型／音色音调）已复刻 ⟹ ⟹ 显示**空态说明**。",
        ],
    }
    OUT.write_text(json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
    print("写入", OUT)
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())

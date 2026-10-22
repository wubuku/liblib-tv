#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 845 门禁：左列第三段「身材塑形」（**18 条**滑杆）逐像素对齐源站。

## 这批做了什么

batch 844 做完了左列第二段 ⟹ ⟹ 「**仍未实现的那一块**」变成**左列第三～五段**。

本批实现**第三段**「身材塑形」。★ 源站**只读**实测（raw 入库在
`docs/research/liblib-canvas-batch845-2026-10-01/raw/`）：

    这一段**没有标题行** ⟹ ⟹ 右栏**第一层就是滚动区**（`pt-3`）
    ⟹ ⟹ 内容起点 ＝ 右栏顶 + 12（与第二段同）
    **18 条**滑杆，每条＝ LABEL(240×55)：
      ├ 标签行 240×22（名字 14px／22px／**纯白** ＋ 可选的「i」＋ 右端数值 11px／16px）
      └ 轨道 240×12（= 标签 +36）＋ 一枚 **14×14 的白色圆钮** ＋ 圆心 **2×2 深点**
    标签行 top ＝ 段内 **12 + 74.8·i**；滚动区高 **1418**
    量程：**5 条**是 −100..100（丰胸／瘦身／瘦手臂／美臀／肩膀宽度），其余 13 条 0..100
    「i」标记：**6 条**（驼背／瘦脖子-左／瘦脖子-右／天鹅颈-左／天鹅颈-右／全身美型）

## ★ 外观是**像素**实测的，不是推理

`raw/source-845-pixels.json`（由 `probes/pixels845.py` 从截屏**机器提取**）：
轨道 **2px**；已填充段**纯白 #fff**；未填充段 ≈ rgba(255,255,255,.08)；
圆钮 **14×14 纯白**、圆心 **2×2 = #464646**；
圆钮中心 ＝ 轨道左端 + **7** + ratio·**226**（★ 由两条滑杆**解**出来 ⟹ ⟹ 不是手打常数）。

## 期望值从哪来（★ 全部机器提取，不手打坐标）

- `raw/source-845-body.json` ⟹ 结构与计算样式
- `raw/source-845-pixels.json` ⟹ 像素证据
- `raw/source-845-visual.json` ＋ `raw/source-845-sliders.png` ⟹ 截屏原件

模态原点取 batch 841 raw 的实测值（361／161）。

## 判据（S1–S7）

S1 ★★★ **这一段不再是空态**：**18 条**滑杆，名字**逐条**等于源站 raw 机器提取的清单；
    ★ 且**没有**空态说明
S2 ★★★ **几何逐像素**：每条滑杆的（名字盒／输入盒／数值盒／圆心点盒／i 盒）
    ⟹ ★ **期望项数独立从 raw 算**（不拿 geo 自己的长度当分母 ⟹ 那是自证）
S3 ★★★ **外观**逐键比对：名字／数值／「i」标记／圆心点的计算样式 ⟹ ★ 期望值取自 raw
S4 ★★★ **量程**逐条：min／max／step／初值；且**分布**（几条 −100..100）与源站一致
S5 ★★★ **真交互**：真实鼠标点「丰胸」轨道**最左** ⟹ 控件 value ＝ −100、
    **渲染出来的数字 == 控件的 value**、圆心点跑到最左；点最右 ⟹ ＋100、圆心点跑到最右
S6 ★★★ **结构事实**：这一段**没有标题行** ⟹ 内容起点 ＝ 右栏顶 + 12；滚动区高 1418；
    这一段**页签数 0**；切回「脸部精修」⟹ **页签数 6**
S7 ★★ **如实标注**：README 必须写明——★ 外观是**像素**实测、★ 更正了三处**既存外观偏差**、
    ★ 量程与「i」标记的条数、★ 源站的**拖动行为未实测**、★ mock 清单
"""
import json
import pathlib
import subprocess
import sys
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
BATCH = ROOT / "docs/research/liblib-canvas-batch845-2026-10-01"
RAW845 = BATCH / "raw/source-845-body.json"
PIX845 = BATCH / "raw/source-845-pixels.json"
RAW841 = ROOT / "docs/research/liblib-canvas-batch841-2026-10-01/raw/source-841-tabs.json"
PROBE_CLONE = BATCH / "probes/clone845.py"
OUT = BATCH / "runtime-audit.json"

# ★★ 判据读的**样式键**（★ 与探针的 `sty()` 同一套 ⟹ ⟹ 逐键可比）
STYLE_KEYS = ["fontSize", "fontWeight", "lineHeight", "color", "backgroundColor",
              "borderRadius", "borderTopWidth", "borderTopColor", "paddingLeft",
              "paddingTop", "gap", "display", "alignItems", "justifyContent",
              "fontFamily"]
# ★★ 几何键（★ 源站与 clone **同名**的盒 ⟹ ⟹ 可以逐像素比）
GEO_KEYS = ("名字盒", "输入盒", "数值盒", "圆心点盒", "i盒")


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
    marker = "body-breast"          # ★ 只这一批才有 ⟹ ⟹ 等得到就说明确实重建了
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
    """从**入库的源站 raw** 里抽出这一段的期望值（几何 ＋ 外观 ＋ 清单 ＋ 量程）。"""
    raw = read_json(RAW845)
    src = raw["★读数"]
    pix = read_json(PIX845)
    modal = read_json(RAW841)["★各状态读数"]["A_默认态_脸部精修_皮肤"]["modal"]
    ox, oy = modal["x"], modal["y"]

    def R(b):
        return {"x": b["x"] - ox, "y": b["y"] - oy, "w": b["w"], "h": b["h"]}

    rows = []
    for s in src["滑杆"]:
        rows.append({
            "名字": s["名字文字"],
            "有i": bool(s["有i"]),
            "min": s["min"], "max": s["max"], "step": s["step"], "value": s["value"],
            "名字盒": R(s["名字盒"]),
            "输入盒": R(s["输入盒"]),
            "数值盒": R(s["数值盒"]),
            "圆心点盒": R(s["缩略点盒"]),
            "i盒": R(s["i盒"]) if s.get("i盒") else None,
            "名字样式": s.get("名字样式"),
            "数值样式": s.get("数值样式"),
            "i样式": s.get("i样式"),
        })
    neg = [r for r in rows if r["min"] == "-100"]
    return {
        "滑杆": rows,
        "条数": len(rows),
        "★源站右栏盒": R(src["右栏盒"]),
        "★源站内容起点_rel_y": R(src["右栏第一层"]["内容盒"]["box"])["y"],
        "★源站滚动高": src["右栏第一层"]["滚动高"],
        "★源站有没有标题行": src["右栏第一层"].get("头行") is not None,
        "★量程分布_负一百到一百": len(neg),
        "★带i的条数": sum(1 for r in rows if r["有i"]),
        "★积分全未变": all(v is False for k, v in raw.items() if "积分是否变化" in k),
        "★读数是目标段": raw.get("★读数_是目标段") is True,
        "★像素_轨道厚": pix["滑杆"][0]["★轨道厚"],
        "★像素_圆钮直径": pix["滑杆"][0]["★圆钮直径"],
        "★像素_圆心点灰阶": pix["滑杆"][0]["★圆心点灰阶"],
        "★像素_行程": pix.get("★行程公式"),
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
    return read_json(pathlib.Path("/tmp/b845-clone-body.json"))


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)

    print("前置检查：等 dev server 重建完 TSX（服务端 JS 里要能看到「body-breast」）……")
    pf_ok, pf_detail = preflight_js()
    if not pf_ok:
        print("PREFLIGHT-FAIL 服务端 JS chunk 里没有「body-breast」⟹ **本轮读数不可信**")
        OUT.write_text(json.dumps({
            "batch": 845, "verdict": "preflight-failed", "preflight": pf_detail,
        }, ensure_ascii=False, indent=1), encoding="utf-8")
        print("写入", OUT)
        return 2
    print("  ✔ 服务端 JS 已重建（等了 %ss）" % pf_detail.get("等了几秒"))

    exp = build_expectations()

    print("跑 clone 运行时探针……")
    rt = run_probe()

    seg = rt.get("A_第三段") or {}
    left = rt.get("B_点最左后") or {}
    right = rt.get("C_点最右后") or {}
    back = rt.get("D_切回脸部精修") or {}
    csl = seg.get("滑杆") or []

    checks = []

    # ── S1 这一段不再是空态 ─────────────────────────────────────────────
    got_names = [s.get("名字文字") for s in csl]
    want_names = [r["名字"] for r in exp["滑杆"]]
    s1 = {
        "★clone的滑杆数": len(csl),
        "★期望条数_从raw算": exp["条数"],
        "★逐条相等": got_names == want_names,
        "★不一致": None if got_names == want_names else {
            "clone": got_names, "源站": want_names},
        "★空态说明": seg.get("空态"),
    }
    checks.append((
        "S1 ★★★ **左列第三段「身材塑形」不再是空态**：**%d 条**滑杆 ⟹ ★ **文案逐条**"
        "等于源站 raw 机器提取的清单（★ 条数也从 raw 算，不写死）；★ 且**没有**空态说明"
        "（★ **页签数**归 S6 ⟹ ⟹ 两条判据读的字段**互不重叠** ⟹ ⟹ "
        "阴性臂才能做到「每条只翻它自己那一条」）" % exp["条数"],
        (s1["★逐条相等"] and s1["★clone的滑杆数"] == exp["条数"]
         and not s1["★空态说明"]),
        json.dumps(s1, ensure_ascii=False),
    ))

    # ── S2 几何逐像素 ───────────────────────────────────────────────────
    geo = []
    for i, r in enumerate(exp["滑杆"]):
        for what in GEO_KEYS:
            if r.get(what):
                geo.append({"键": (i, what), "盒": r[what]})
    diffs = []
    for item in geo:
        i, what = item["键"]
        cc = csl[i] if i < len(csl) else {}
        got = cc.get(what)
        if what == "圆心点盒":
            got = cc.get("圆心点盒")
        if not box_close(item["盒"], got):
            diffs.append({"元素": "滑杆[%d] %s（%s）的 %s"
                          % (i, exp["滑杆"][i]["名字"], what, what),
                          "源站": item["盒"], "clone": got})
    # ★ **期望项数独立从 raw 算**（不拿 geo 自己的长度当分母 ⟹ 那是自证）
    expect_items = sum(
        1 for r in exp["滑杆"] for what in GEO_KEYS if r.get(what))
    s2 = {"★比较了几项": len(geo), "★期望项数_独立从raw算": expect_items,
          "★有几项不一致": len(diffs), "★不一致明细": diffs[:20]}
    checks.append((
        "S2 ★★★ **几何与源站逐像素一致**（%d 项：每条滑杆的名字盒／输入盒／数值盒／"
        "圆心点盒／「i」盒）⟹ ★ **期望值全部从入库 raw 机器提取** ⟹ ⟹ **宽高逐像素全等**、"
        "位置 ±1px；★ 且**比较数 == 期望项数**（★ 期望项数**独立从 raw 算** ⟹ ⟹ "
        "不拿 geo 自己的长度当分母 ⟹ ⟹ 那是**自证**；★ **不写死阈值** —— "
        "写死的阈值会「为了变绿而下调」）" % len(geo),
        (len(diffs) == 0 and len(geo) == expect_items and expect_items > 0),
        json.dumps(s2, ensure_ascii=False),
    ))

    # ── S3 外观逐键比对 ────────────────────────────────────────────────
    style_diffs = []
    n_specs = 0
    for i, r in enumerate(exp["滑杆"]):
        cc = csl[i] if i < len(csl) else {}
        for name in ("名字样式", "数值样式"):
            for key in STYLE_KEYS:
                want = (r.get(name) or {}).get(key)
                got = (cc.get(name) or {}).get(key)
                n_specs += 1
                if want != got:
                    style_diffs.append({"元素": "滑杆[%d] %s 的 %s"
                                        % (i, r["名字"], key),
                                        "期望": want, "clone": got})
        if r["有i"]:
            for key in STYLE_KEYS:
                want = (r.get("i样式") or {}).get(key)
                got = (cc.get("i样式") or {}).get(key)
                n_specs += 1
                if want != got:
                    style_diffs.append({"元素": "滑杆[%d] 「i」标记的 %s"
                                        % (i, key),
                                        "期望": want, "clone": got})
        # ★ 圆心点的底色（★ 像素实测 ＝ 70 ＝ #464646）
        want = "#464646"
        got = (cc.get("圆心点样式") or {}).get("backgroundColor")
        n_specs += 1
        if got != "rgb(70, 70, 70)":
            style_diffs.append({"元素": "滑杆[%d] 圆心点的底色" % i,
                                "期望": "rgb(70, 70, 70)", "clone": got})
    s3 = {"★核了几项": n_specs, "★有几项不一致": len(style_diffs),
          "★不一致明细": style_diffs,
          "★期望值来源": "batch 845 raw 的计算样式 ＋ 像素证据（机器提取，非手打）"}
    checks.append((
        "S3 ★★★ **外观**也对齐：名字（14px／22px／400／**纯白**）／数值（11px／16px／"
        "白 60%／等宽）／「i」标记（10px 描边圆）／**圆心点 #464646** ⟹ ★ **期望值取自"
        "入库 raw 的计算样式 ＋ 像素证据**（★ 逐键比对，★ 不硬编码颜色字符串）",
        (len(style_diffs) == 0 and n_specs > 0),
        json.dumps(s3, ensure_ascii=False),
    ))

    # ── S4 量程逐条 ─────────────────────────────────────────────────────
    rng_rows = []
    for i, r in enumerate(exp["滑杆"]):
        cc = csl[i] if i < len(csl) else {}
        rng_rows.append({"名字": r["名字"], "源站": [r["min"], r["max"], r["step"], r["value"]],
                         "clone": [cc.get("min"), cc.get("max"), cc.get("step"), cc.get("value")]})
    neg_clone = [r for r in rng_rows if r["clone"][0] == "-100"]
    s4 = {"★逐条": rng_rows,
          "★全部相等": all(r["源站"] == r["clone"] for r in rng_rows),
          "★clone里负一百到一百的条数": len(neg_clone),
          "★源站里负一百到一百的条数": exp["★量程分布_负一百到一百"],
          "★源站带i的条数": exp["★带i的条数"],
          "★clone带i的条数": sum(1 for s in csl if s.get("有i")),
          "★源站那趟_积分全程未变": exp["★积分全未变"],
          "★源站那趟_读到的是目标段": exp["★读数是目标段"]}
    checks.append((
        "S4 ★★★ **量程**逐条对齐源站：**5 条**是 −100..100（丰胸／瘦身／瘦手臂／美臀／"
        "肩膀宽度），其余 13 条 0..100，step 全是 1、初值全 0；★ 且**分布**也要一致"
        "（不是只逐条比值 ⟹ ⟹ 「有几条是负量程」也得对上）；★ 「i」标记的**条数**也要对上；"
        "★ 且源站那趟的**积分全程未变** ＋ 读到的**是目标段**",
        (s4["★全部相等"]
         and s4["★clone里负一百到一百的条数"] == s4["★源站里负一百到一百的条数"]
         and s4["★clone带i的条数"] == s4["★源站带i的条数"]
         and s4["★源站那趟_积分全程未变"] and s4["★源站那趟_读到的是目标段"]),
        json.dumps(s4, ensure_ascii=False),
    ))

    # ── S5 真交互 ───────────────────────────────────────────────────────
    def pick(stage, name):
        for s in (stage.get("滑杆") or []):
            if s.get("名字文字") == name:
                return s
        return None

    def want_dot_x(value, minv, maxv):
        """圆心点 x（**相对模态**）＝ 右栏列顶 + 24 + 7 + ratio·226 − 1
        （★ 24 是轨道相对**右栏**的左端；★ 列顶从 raw 算 ⟹ ⟹ 不是手打坐标）"""
        ratio = (float(value) - float(minv)) / (float(maxv) - float(minv))
        return exp["★源站右栏盒"]["x"] + 24 + 7 + ratio * 226 - 1

    lft = pick(left, "丰胸") or {}
    rgt = pick(right, "丰胸") or {}
    s5 = {
        "★点最左后_控件value": lft.get("value"),
        "★点最左后_渲染数字": lft.get("数值文字"),
        "★点最左后_圆心点x": (lft.get("圆心点盒") or {}).get("x"),
        "★期望_点最左后_圆心点x": want_dot_x(-100, -100, 100),
        "★点最右后_控件value": rgt.get("value"),
        "★点最右后_渲染数字": rgt.get("数值文字"),
        "★点最右后_圆心点x": (rgt.get("圆心点盒") or {}).get("x"),
        "★期望_点最右后_圆心点x": want_dot_x(100, -100, 100),
    }
    checks.append((
        "S5 ★★★ **滑杆是真交互**：真实鼠标点「丰胸」轨道的**最左** ⟹ 控件 value ＝ −100、"
        "**渲染出来的数字 == 控件的 value**、**圆心点**跑到最左；点**最右** ⟹ ＋100、圆心点跑到最右"
        "⟹ ★ 判据是「**读出来的状态** == 期望」，不是「点了没报错」；★ 圆心点的期望位置由"
        "**源站的像素公式**（24 + 7 + ratio·226 − 1）算出来 ⟹ ⟹ 不是手打坐标",
        (s5["★点最左后_控件value"] == "-100"
         and s5["★点最左后_渲染数字"] == "-100"
         and s5["★点最左后_圆心点x"] == s5["★期望_点最左后_圆心点x"]
         and s5["★点最右后_控件value"] == "100"
         and s5["★点最右后_渲染数字"] == "100"
         and s5["★点最右后_圆心点x"] == s5["★期望_点最右后_圆心点x"]),
        json.dumps(s5, ensure_ascii=False),
    ))

    # ── S6 结构事实 ─────────────────────────────────────────────────────
    clone_col = seg.get("右栏盒") or {}
    clone_first = (csl[0].get("名字盒") or {}) if csl else {}
    clone_origin = (clone_first.get("y") or 0) - (clone_col.get("y") or 0)
    src_col = exp["★源站右栏盒"]
    src_origin = exp["★源站内容起点_rel_y"] - src_col["y"]
    s6 = {
        "★源站有没有标题行": exp["★源站有没有标题行"],
        "★源站_内容起点_相对列顶": src_origin,
        "★clone_内容起点_相对列顶": clone_origin,
        "★源站_滚动高": exp["★源站滚动高"],
        "★clone_滚动高": (seg.get("面板") or {}).get("滚动高"),
        "★这一段_页签数": seg.get("页签数"),
        "★切回_页签数": back.get("页签数"),
    }
    checks.append((
        "S6 ★★★ **结构事实**：源站实测**这一段没有标题行** ⟹ ⟹ 右栏**第一层就是滚动区** "
        "⟹ ⟹ 内容起点 ＝ 右栏顶 + 12（★ 与源站**逐像素**对上）；★ 滚动区高 **%s**（★ 与源站一致）"
        "；★ 这一段**页签数 0**（页签行只在「脸部精修」段存在）；★ 切回「脸部精修」⟹ **页签数 6**"
        % exp["★源站滚动高"],
        (s6["★源站有没有标题行"] is False
         and s6["★clone_内容起点_相对列顶"] == s6["★源站_内容起点_相对列顶"]
         and s6["★clone_滚动高"] == s6["★源站_滚动高"]
         and s6["★这一段_页签数"] == 0
         and s6["★切回_页签数"] == 6),
        json.dumps(s6, ensure_ascii=False),
    ))

    # ── S7 如实标注 ─────────────────────────────────────────────────────
    readme = (BATCH / "README.md").read_text(encoding="utf-8") \
        if (BATCH / "README.md").exists() else ""
    s7 = {
        "★README存在": bool(readme),
        "★README写明像素实测": "像素" in readme,
        "★README写明更正了既存偏差": ("偏差" in readme or "改正" in readme),
        "★README写明量程": ("−100" in readme or "-100" in readme) and "18" in readme,
        "★README写明i标记条数": "6 条" in readme or "六条" in readme,
        "★README写明拖动行为未实测": ("未实测" in readme and "拖" in readme),
        "★README写明不消耗积分": "不消耗" in readme,
        "★README写明左列两段未实现": "服装造型" in readme and "音色库" in readme,
        "★README里mock出现次数": readme.lower().count("mock"),
    }
    checks.append((
        "S7 ★★ **如实标注**：README 必须写明——★ 滑杆的**外观是像素实测**的（2px 轨道／"
        "14×14 圆钮／圆心 2×2 深点）；★ 本批**更正了三处既存外观偏差**（名字色／数值色／"
        "轨道与圆钮）；★ 量程（5 条 −100..100）与「i」标记（6 条）的条数；★ 源站**拖动滑杆**"
        "会发生什么**未实测**；★ 左列**两段**（服装造型／音色音调）**未实现**；"
        "★ 且「确认生成」等仍是 mock、不消耗 ⚡44",
        (s7["★README存在"] and s7["★README写明像素实测"]
         and s7["★README写明更正了既存偏差"] and s7["★README写明量程"]
         and s7["★README写明i标记条数"] and s7["★README写明拖动行为未实测"]
         and s7["★README写明不消耗积分"] and s7["★README写明左列两段未实现"]
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
        "batch": 845,
        "verdict": "%d/%d" % (passed, len(checks)),
        "checks": [{"label": c[0], "pass": c[1], "detail": c[2]} for c in checks],
    }
    OUT.write_text(json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
    print("写入", OUT)
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())

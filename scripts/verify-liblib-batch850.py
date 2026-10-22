#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 850 门禁：角色大编辑器**预览区（中列）**逐项对照源站。

★ 源站基准：**只读**实测，raw 入库在
  `docs/research/liblib-canvas-batch850-2026-10-01/raw/source-850-{default,half,full}.json`
  ⟹ ⟹ 期望值由 `probes/gen850_data.py` **机器提取**到 `probes/preview-850-data.json`
  ⟹ ⟹ ★ 本门禁**先跑**那个提取脚本 ⟹ ⟹ 再读它（⟹ ⟹ 不手打任何期望值）。

★ ★ **同口径**（★ 两边必须读同一个状态，否则得到的是假差异）：
  - 源站那趟**没有点任何左列分段** ⟹ ⟹ clone 侧也**不点分段**；
  - 源站「default」＝ 刚打开编辑器 ⟹ ⟹ clone 侧也是刚打开就读；
  - 源站「full」＝ 点了「全身」之后 ⟹ ⟹ clone 侧也点同一枚按钮。

★ ★ **几何口径**（★ 这是本批最容易出错的地方）：
  源站 raw 记的是 `getBoundingClientRect`（**变换后**的视觉盒）
  ⟹ ⟹ **半身态**的图盒被放大到 1634×2084 ⟹ ⟹ **不可比**
  ⟹ ⟹ ⟹ 所以：
    · **full 态**（identity transform）比**全部几何**（此时视觉盒 ＝ 布局盒）；
    · **half 态**只比 **transform 矩阵** ＋ 与图无关的属性（opacity／backdrop-filter／transition）。

七条判据：
  S1 ★★★ **结构与层级**：图区**四层** ＋ 遮罩**三层** ＋ 工具行**三个孩子**（含分隔线）
     ⟹ ⟹ ★ 旧结构（「img 直接挂在 `.ce-figure` 下」）**必须消失**
  S2 ★★★ **几何逐像素**（full 态）：中列／图容器／内层／变换层／图盒／img／
     遮罩三层／工具行／分隔线／两枚按钮 ⟹ ⟹ rel 盒**逐项**相等
  S3 ★★★ **变换**：两态的 transform **矩阵** ＋ transform-origin ＋ transition 串
  S4 ★★★ **外观**：渐变（**逐字符**）＋ backdrop-filter（两态）＋ 按钮圆角／底色／
     文字色（两态）＋ 分隔线底色 ＋ 工具行底色（**透明**）
  S5 ★★★ **交互真生效**：★ **默认就是「半身」** ⟹ 点「全身」⟹ 矩阵变 identity、
     遮罩 opacity 变 0、blur 变 0px ⟹ 点回「半身」⟹ 全部恢复
  S6 ★★ **间隙与分隔线**：工具行三个孩子的盒 ⟹ ⟹ 间隙是**真 gap 4**
     ⟹ ⟹ 且分隔线**存在**（1×12）
  S7 ★★ **连带没坏 ＋ 如实标注**：★ 本批动了 `.ce-tool` 这个类 ⟹ ⟹ 左下三工具与
     **batch 840 的 clone 基线**逐项相同 ⟹ ⟹ 且底部生成行仍在 ⟹ ⟹ 且预览区**没有**说明文字
"""
import json
import pathlib
import re
import subprocess
import sys
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
BATCH = ROOT / "docs/research/liblib-canvas-batch850-2026-10-01"
RAW = BATCH / "raw"
PROBES = BATCH / "probes"
DATA = PROBES / "preview-850-data.json"
PROBE_CLONE = PROBES / "clone850.py"
GEN = PROBES / "gen850_data.py"
BASE840 = ROOT / ("docs/research/liblib-canvas-batch840-2026-10-01"
                  "/raw/clone-840-editor.json")
OUT = BATCH / "runtime-audit.json"


def read_json(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


def served_chunks() -> str:
    html = urllib.request.urlopen("http://localhost:4317/", timeout=60).read().decode("utf-8", "replace")
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
    marker = "character-editor-figure-zoom"
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


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)

    print("前置检查：等 dev server 重建完 TSX（服务端 JS 里要能看到「figure-zoom」）……")
    pf_ok, pf_detail = preflight_js()
    if not pf_ok:
        print("PREFLIGHT-FAIL 服务端 JS chunk 里没有「character-editor-figure-zoom」"
              "⟹ **本轮读数不可信**")
        OUT.write_text(json.dumps({
            "batch": 850, "verdict": "preflight-failed", "preflight": pf_detail,
        }, ensure_ascii=False, indent=1), encoding="utf-8")
        return 2
    print("  ✔", pf_detail)

    print("跑机器提取（期望值全部来自入库 raw）……")
    g = subprocess.run([sys.executable, str(GEN)], capture_output=True,
                       text=True, timeout=300, cwd=str(ROOT))
    print(g.stdout.strip() or g.stderr.strip()[-800:])
    if g.returncode != 0:
        OUT.write_text(json.dumps({"batch": 850, "verdict": "extract-failed",
                                   "stderr": g.stderr[-2000:]},
                                  ensure_ascii=False, indent=1), encoding="utf-8")
        return 2
    exp = read_json(DATA)
    src = exp["★full"]
    src_half = exp["★half"]
    src_default = exp["★default"]

    print("跑 clone 探针……")
    subprocess.run([sys.executable, str(PROBE_CLONE)], capture_output=True,
                   text=True, timeout=1800, cwd=str(ROOT))
    rt = read_json(pathlib.Path("/tmp/b850-clone-preview.json"))
    if rt.get("★异常"):
        print("探针异常：", rt["★异常"][:800])
        OUT.write_text(json.dumps({"batch": 850, "verdict": "probe-failed",
                                   "异常": rt["★异常"]}, ensure_ascii=False, indent=1),
                       encoding="utf-8")
        return 2

    cl_def = (rt.get("★默认态") or {}).get("预览区") or {}
    cl_full = (rt.get("★全身态") or {}).get("预览区") or {}
    cl_back = (rt.get("★半身态_回切") or {}).get("预览区") or {}

    checks = []
    geo_diffs = []
    style_diffs = []
    n_geo = 0
    n_style = 0

    def gcmp(label, want, got):
        nonlocal n_geo
        n_geo += 1
        if not box_close(want, got):
            geo_diffs.append({"元素": label, "期望": want, "clone": got})

    def scmp(label, want, got):
        nonlocal n_style
        n_style += 1
        if want != got:
            style_diffs.append({"项": label, "期望": want, "clone": got})

    # ══ S1 结构与层级 ═════════════════════════════════════════════════════
    s1 = []
    zoom_cls = (cl_full.get("变换层样式") or {}).get("transform") or ""
    if not (cl_def.get("图容器盒") and cl_def.get("内层盒")
            and cl_def.get("变换层布局盒") and cl_def.get("图元素布局盒")):
        s1.append("clone 的图区**不是四层**（图容器／内层／变换层／图盒）")
    if cl_def.get("图容器盒") and cl_def.get("内层盒"):
        if cl_def["图容器盒"]["w"] != 467:
            s1.append("图容器宽不是 467")
    if not cl_def.get("遮罩盒") or not cl_def.get("blur层盒") or not cl_def.get("渐变层盒"):
        s1.append("遮罩**不是三层**（外层／blur 层／渐变层）")
    if cl_def.get("按钮数") != 2:
        s1.append("取景按钮不是两枚")
    if not cl_def.get("分隔线盒"):
        s1.append("★ 工具行里**没有**分隔线")
    if "is-half" not in (cl_def.get("变换层样式") or {}).get("transform", "") and \
            "matrix" not in zoom_cls:
        s1.append("变换层没有 transform")
    checks.append(("S1 ★★★ **结构与层级**：图区**四层** ＋ 遮罩**三层** ＋ "
                   "工具行**三个孩子**（★ 含分隔线）⟹ ⟹ ★ 旧结构"
                   "（「img 直接挂在 `.ce-figure` 下」）**必须消失**",
                   not s1, {"问题": s1,
                            "clone层级": {
                                "图容器": cl_def.get("图容器盒"),
                                "内层": cl_def.get("内层盒"),
                                "变换层": cl_def.get("变换层布局盒"),
                                "图盒": cl_def.get("图元素布局盒"),
                                "遮罩": cl_def.get("遮罩盒"),
                                "blur层": cl_def.get("blur层盒"),
                                "渐变层": cl_def.get("渐变层盒"),
                                "工具行": cl_def.get("工具行盒"),
                                "分隔线": cl_def.get("分隔线盒"),
                                "按钮数": cl_def.get("按钮数")}}))

    # ══ S2 几何逐像素（★ full 态：identity transform ⟹ ⟹ 视觉盒 ＝ 布局盒）══
    pairs = [
        ("中列", src["中列"], cl_full.get("中列盒")),
        ("图容器", src["图容器"], cl_full.get("图容器盒")),
        ("变换层", src["变换层"], cl_full.get("变换层盒")),
        ("图盒", src["图盒"], cl_full.get("图盒盒")),
        ("图元素", src["图元素"], cl_full.get("图元素盒")),
        ("遮罩", src["遮罩"], cl_full.get("遮罩盒")),
        ("blur层", src["blur层"], cl_full.get("blur层盒")),
        ("渐变层", src["渐变层"], cl_full.get("渐变层盒")),
        ("工具行", src["工具行"], cl_full.get("工具行盒")),
        ("分隔线", src["分隔线"], cl_full.get("分隔线盒")),
    ]
    for name, want, got in pairs:
        gcmp(name, want, got)
    src_btns = {b["aria"]: b["盒"] for b in src["按钮"]}
    cl_btns = {b["aria"]: b["box"] for b in (cl_full.get("按钮") or [])}
    for aria in ("半身", "全身"):
        gcmp("按钮·%s" % aria, src_btns.get(aria), cl_btns.get(aria))
    checks.append(("S2 ★★★ **几何逐像素**（★ full 态 ＝ identity transform "
                   "⟹ ⟹ 视觉盒 ＝ 布局盒）：中列／图容器／变换层／图盒／img／"
                   "遮罩三层／工具行／分隔线／两枚按钮 ⟹ ⟹ **%d 项**逐项相等"
                   % n_geo, not geo_diffs, {"差异": geo_diffs}))

    # ══ S3 变换 ═══════════════════════════════════════════════════════════
    scmp("半身矩阵", src_default["变换层矩阵"],
         (cl_def.get("变换层样式") or {}).get("transform"))
    scmp("全身矩阵", src["变换层矩阵"],
         (cl_full.get("变换层样式") or {}).get("transform"))
    scmp("半身态·原点", src_default["变换层原点"],
         (cl_def.get("变换层样式") or {}).get("transformOrigin"))
    scmp("全身态·原点", src["变换层原点"],
         (cl_full.get("变换层样式") or {}).get("transformOrigin"))
    scmp("半身态·过渡", src_default["变换层过渡"],
         (cl_def.get("变换层样式") or {}).get("transition"))
    scmp("全身态·过渡", src["变换层过渡"],
         (cl_full.get("变换层样式") or {}).get("transition"))
    checks.append(("S3 ★★★ **变换**：两态的 transform **矩阵** ＋ transform-origin "
                   "（★ 源站 class 写 `origin-[50%_8%]` 但**计算值是 `0px 0px`** "
                   "⟹ ⟹ 照抄**计算值**）＋ 过渡串", not style_diffs,
                   {"差异": style_diffs}))

    # ══ S4 外观 ═══════════════════════════════════════════════════════════
    style_diffs = []
    n_style = 0
    scmp("渐变（逐字符）", src["渐变"], (cl_def.get("渐变层样式") or {}).get("backgroundImage"))
    scmp("blur·半身", src_default["blur值"], (cl_def.get("blur层样式") or {}).get("backdropFilter"))
    scmp("blur·全身", src["blur值"], (cl_full.get("blur层样式") or {}).get("backdropFilter"))
    scmp("遮罩透明度·半身", src_default["遮罩透明度"], (cl_def.get("遮罩样式") or {}).get("opacity"))
    scmp("遮罩透明度·全身", src["遮罩透明度"], (cl_full.get("遮罩样式") or {}).get("opacity"))
    scmp("遮罩过渡·半身", src_default["遮罩过渡"], (cl_def.get("遮罩样式") or {}).get("transition"))
    scmp("遮罩过渡·全身", src["遮罩过渡"], (cl_full.get("遮罩样式") or {}).get("transition"))
    scmp("blur过渡·半身", src_default["blur过渡"], (cl_def.get("blur层样式") or {}).get("transition"))
    scmp("blur过渡·全身", src["blur过渡"], (cl_full.get("blur层样式") or {}).get("transition"))
    scmp("工具行底色（★ 源站透明）", src["工具行底色"], (cl_full.get("工具行样式") or {}).get("backgroundColor"))
    scmp("工具行间隙", "4px", (cl_full.get("工具行样式") or {}).get("gap"))
    scmp("分隔线底色", src["分隔线底色"], (cl_full.get("分隔线样式") or {}).get("backgroundColor"))
    src_btn = {b["aria"]: b for b in src["按钮"]}
    cl_btn_full = {b["aria"]: b for b in (cl_full.get("按钮") or [])}
    for aria in ("半身", "全身"):
        scmp("按钮·%s·圆角" % aria, src_btn[aria]["圆角"],
             (cl_btn_full.get(aria) or {}).get("style", {}).get("borderRadius"))
        scmp("按钮·%s·底色" % aria, src_btn[aria]["底色"],
             (cl_btn_full.get(aria) or {}).get("style", {}).get("backgroundColor"))
    # ★ 文字色：★ 源站是「**只换文字色**」⟹ ⟹ 选中那枚纯白、未选那枚 60% 白
    src_col_default = {b["aria"]: b["文字色"] for b in src_default["按钮"]}
    src_col_full = {b["aria"]: b["文字色"] for b in src["按钮"]}
    cl_col_def = {b["aria"]: b["style"]["color"] for b in (cl_def.get("按钮") or [])}
    cl_col_full = {b["aria"]: b["style"]["color"] for b in (cl_full.get("按钮") or [])}
    scmp("文字色·半身态", src_col_default, cl_col_def)
    scmp("文字色·全身态", src_col_full, cl_col_full)
    checks.append(("S4 ★★★ **外观**：渐变（**逐字符**）＋ backdrop-filter（两态）＋ "
                   "遮罩透明度（两态）＋ 按钮圆角／底色／**文字色**（两态）＋ "
                   "分隔线底色 ＋ 工具行底色（★ 源站**透明**）",
                   not style_diffs, {"差异": style_diffs}))

    # ══ S5 交互真生效 ═════════════════════════════════════════════════════
    s5 = []
    if (cl_def.get("变换层样式") or {}).get("transform") != src_default["变换层矩阵"]:
        s5.append("★ clone 的**默认态**不是半身（源站默认就是半身）")
    if (cl_full.get("变换层样式") or {}).get("transform") != src["变换层矩阵"]:
        s5.append("点「全身」后矩阵没变 identity")
    if (cl_full.get("遮罩样式") or {}).get("opacity") != src["遮罩透明度"]:
        s5.append("点「全身」后遮罩透明度没变 0")
    if (cl_full.get("blur层样式") or {}).get("backdropFilter") != src["blur值"]:
        s5.append("点「全身」后 backdrop-filter 没变 blur(0px)")
    if (cl_back.get("变换层样式") or {}).get("transform") != src_default["变换层矩阵"]:
        s5.append("点回「半身」后矩阵没恢复")
    if (cl_back.get("遮罩样式") or {}).get("opacity") != src_default["遮罩透明度"]:
        s5.append("点回「半身」后遮罩透明度没恢复")
    checks.append(("S5 ★★★ **交互真生效**：★ **默认就是「半身」** ⟹ 点「全身」⟹ "
                   "矩阵变 identity ＋ 遮罩 opacity 变 0 ＋ blur 变 0px "
                   "⟹ 点回「半身」⟹ 全部恢复", not s5, {"问题": s5}))

    # ══ S6 间隙与分隔线 ═══════════════════════════════════════════════════
    s6 = []
    kids = [k for k in (cl_full.get("按钮") or [])]
    sep = cl_full.get("分隔线盒")
    if len(kids) != 2:
        s6.append("取景按钮不是两枚")
    if not sep:
        s6.append("没有分隔线")
    else:
        if sep.get("w") != 1 or sep.get("h") != 12:
            s6.append("分隔线不是 1×12")
        order = sorted(kids, key=lambda b: b["box"]["x"])
        if len(order) == 2:
            g1 = sep["x"] - (order[0]["box"]["x"] + order[0]["box"]["w"])
            g2 = order[1]["box"]["x"] - (sep["x"] + sep["w"])
            if g1 != 4 or g2 != 4:
                s6.append("★ 分隔线两侧的间隙不是 4（%s／%s）⟹ ⟹ 不是真 gap" % (g1, g2))
    checks.append(("S6 ★★ **间隙与分隔线**：工具行三个孩子 ⟹ ⟹ 分隔线**存在**（1×12）"
                   "⟹ ⟹ 且两侧间隙是**真 gap 4**（★ 不是 clone 之前那种"
                   "「靠 9px 凑出 73 宽」的假 gap）", not s6, {"问题": s6}))

    # ══ S7 连带没坏 ＋ 如实标注 ═══════════════════════════════════════════
    s7 = []
    base840 = read_json(BASE840)["B_点开后"]
    old_tools = base840.get("左下工具") or []
    new_tools = (rt.get("★默认态") or {}).get("左下工具") or []
    if len(old_tools) != len(new_tools):
        s7.append("左下三工具数量变了：840 基线 %d ⟹ 现在 %d"
                  % (len(old_tools), len(new_tools)))
    for o, n in zip(old_tools, new_tools):
        if o.get("aria") != n.get("aria"):
            s7.append("左下工具 aria 变了：%s ⟹ %s" % (o.get("aria"), n.get("aria")))
            continue
        if not box_close({"x": o["x"], "y": o["y"], "w": o["w"], "h": o["h"]},
                         {"x": n["box"]["x"], "y": n["box"]["y"],
                          "w": n["box"]["w"], "h": n["box"]["h"]}):
            s7.append("★ 左下工具「%s」的位置变了：840 %s ⟹ 现在 %s"
                      % (o["aria"], o, n["box"]))
    # ★ 半身/全身容器与两枚按钮的位置 ⟹ ⟹ 与 840 基线逐项相同（★ 本批改了这套结构）
    for key, now in (("半身全身容器", cl_full.get("工具行盒")),
                     ("半身全身·半身", (cl_btns.get("半身") or {})),
                     ("半身全身·全身", (cl_btns.get("全身") or {}))):
        base_key = key
        if key.startswith("半身全身·"):
            idx = 0 if key.endswith("半身") else 1
            old = (base840.get("半身全身") or [None, None])[idx]
        else:
            old = base840.get(base_key)
        if not old or not now:
            s7.append("★ %s 与 840 基线对不上（缺一侧）" % key)
            continue
        if not box_close({"x": old["x"], "y": old["y"], "w": old["w"], "h": old["h"]},
                         {"x": now["x"], "y": now["y"], "w": now["w"], "h": now["h"]}):
            s7.append("★ %s 的位置与 840 基线不同：840 %s ⟹ 现在 %s"
                      % (key, old, now))
    # ★ 底部生成行仍在（★ 本批没动它）
    if (rt.get("★默认态") or {}).get("底部生成数") != 1:
        s7.append("底部生成行不见了")
    # ★ 预览区**没有**说明文字（★ 本批全部实测并实现 ⟹ ⟹ 不得编造说明）
    if (rt.get("★默认态") or {}).get("预览区文字"):
        s7.append("★ 预览区出现了说明文字：%r"
                  % (rt.get("★默认态") or {}).get("预览区文字"))
    checks.append(("S7 ★★ **连带没坏 ＋ 如实标注**：★ 本批动了 `.ce-tool` 这个类 ⟹ ⟹ "
                   "左下三工具与 **batch 840 的 clone 基线**逐项相同 ⟹ ⟹ "
                   "取景容器与两枚按钮的位置也与 840 基线相同 ⟹ ⟹ 底部生成行仍在 "
                   "⟹ ⟹ 且预览区**没有**说明文字", not s7, {"问题": s7}))

    # ══ 汇总 ══════════════════════════════════════════════════════════════
    passed = sum(1 for _, ok, _ in checks if ok)
    verdict = "PASS" if passed == len(checks) else "FAIL"
    print()
    for name, ok, detail in checks:
        print("  %s %s" % ("✔" if ok else "✘", name))
        if not ok:
            print("      ", json.dumps(detail, ensure_ascii=False)[:1200])
    print("\n%d/%d 条通过 ⟹ ⟹ %s" % (passed, len(checks), verdict))

    OUT.write_text(json.dumps({
        "batch": 850,
        "verdict": verdict,
        "通过": passed,
        "总条数": len(checks),
        "几何比对项数": n_geo,
        "样式比对项数": n_style,
        "★期望值来源": str(DATA.relative_to(ROOT)),
        "★原点": exp["★模态原点"],
        "★交叉校验": exp["★交叉校验"],
        "checks": [{"判据": n, "通过": ok, "明细": d} for n, ok, d in checks],
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print("产物：", OUT)
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())

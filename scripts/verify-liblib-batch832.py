#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 832 验收器 —— clone 导演台「添加机位」机位预设面板（**实施批次**）。

## 本批做了什么

batch 832 的盘点（`docs/research/liblib-canvas-batch832-2026-10-01/probes/diag832b.py`
的 DOM 差分）发现：源站 rail 的「添加机位」**不是**直接加一个机位
（那是 batch 540 的旧读数，本批被推翻）⟹ 它把**左侧资源栏切成一个视图**：
标题条「添加机位」 ＋ 2 列 × 15 枚机位预设（每枚 104×72）。
而 **clone 的 rail「添加机位」是 `kind: "action"` ⟹ 点击直接加机位、没有面板**。

本批把 clone 补成源站的形态：左侧栏多一个「机位预设」视图，
点 rail 的「添加机位」切过去、点「场景」切回来。

## 门禁怎么判

**逐字比对**：源站与 clone 的读数用**同一段读数 JS** 采
（`probes/camera832b.py` 与 `probes/cameraclone832.py`）⟹ 两边字段可直接相等比较。
几何、15 枚标签文字、15 条 SVG path 逐项相等才判过。

★ 期望值**从 raw 读**（`raw/source-832-camera-presets.json`，
  由 `probes/mk832raw.py` 从活体读数**程序化**整理）⟹ **不是手打**。

★ 纪律：每条判据都有**只翻它自己那一条**的阴性对照。
"""
import copy
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
BATCH = ROOT / "docs" / "research" / "liblib-canvas-batch832-2026-10-01"
RAW = BATCH / "raw"

SRC_RAW = RAW / "source-832-camera-presets.json"
CLONE_RAW = RAW / "clone-832-camera-presets.json"
SRC_PANEL = ROOT / "src" / "components" / "director" / "DirectorCameraPresetPanel.tsx"
SRC_RAIL = ROOT / "src" / "components" / "director" / "DirectorIconRail.tsx"
SRC_DESK = ROOT / "src" / "components" / "director" / "DirectorDesk.tsx"

# ── ★ 探针区开始 ────────────────────────────────────────────────────────────────
# ★ 本批的「探针」＝ **读入库读数的键名**（不是 DOM 选择器）：
#   键名一旦漂移，下面这些常量就取不到值 ⟹ 门禁自己会红。
K_SRC_PANEL = "面板"
K_SRC_TITLE = "title"
K_SRC_GRID = "gridBox"
K_SRC_PRESETS = "预设"
K_SRC_COUNT = "预设项数"
K_SRC_UNIQ = "唯一图标path数"
K_CLONE_OPEN = "②点添加机位后"
K_CLONE_TREE = "①开台后"
K_CLONE_BACK = "③点场景后"
K_CLONE_BACKTREE = "③b场景树还在"
# ── ★ 探针区结束 ────────────────────────────────────────────────────────────────


def _cells(raw):
    """取 clone 读数里的 15 枚格子（按读数结构）"""
    panel = raw.get(K_CLONE_OPEN) or {}
    return panel.get("cells") or []


def build_checks(src_raw, clone_raw, panel_src, rail_src, desk_src):
    C = []

    def ok(cid, cond, detail=None):
        C.append({"id": cid, "name": cid, "ok": bool(cond),
                  "detail": detail if detail is not None else ""})

    s_panel = src_raw.get(K_SRC_PANEL) or {}
    s_title = s_panel.get(K_SRC_TITLE) or {}
    s_grid = s_panel.get(K_SRC_GRID) or {}
    s_presets = src_raw.get(K_SRC_PRESETS) or []

    c_open = clone_raw.get(K_CLONE_OPEN) or {}
    c_tree = clone_raw.get(K_CLONE_TREE) or {}
    c_back = clone_raw.get(K_CLONE_BACK) or {}
    c_cells = c_open.get("cells") or []
    c_title = c_open.get("title") or {}
    c_grid = c_open.get("gridBox") or {}

    # ── S1 源站读数自洽（判据的地基）──
    ok("S1:★★★ **源站形态**（读数自洽）：面板 232×1028 @(48,52)、"
       "标题条 232×48 @(48,52)、网格 232×980 @(48,100)、"
       "**2 列 104px**、**15 枚预设**（每枚 104×72）、**15 枚共用同一枚图标**",
       (s_panel.get("box") or {}) == {"x": 48, "y": 52, "w": 232, "h": 1028}
       and (s_title.get("box") or {}) == {"x": 48, "y": 52, "w": 232, "h": 48}
       and (s_grid or {}) == {"x": 48, "y": 100, "w": 232, "h": 980}
       and s_panel.get("gridTemplateColumns") == "104px 104px"
       and src_raw.get(K_SRC_COUNT) == 15
       and src_raw.get(K_SRC_UNIQ) == 1,
       {"面板": s_panel.get("box"), "标题条": s_title.get("box"),
        "网格": s_grid, "列": s_panel.get("gridTemplateColumns"),
        "预设数": src_raw.get(K_SRC_COUNT),
        "唯一图标数": src_raw.get(K_SRC_UNIQ),
        "★图标共用": src_raw.get("★图标是共用的")})

    # ── S2 面板盒逐字相等 ──
    ok("S2:★★★★★ clone 的面板盒与源站**逐字相等**（232×1028 @(48,52)）"
       "⟹ ⟹ ★★ 面板**通到视口底**（源站左栏资源栏的高度）",
       (c_open.get("panelBox") or {}) == (s_panel.get("box") or {})
       and bool(c_open.get("panelBox")),
       {"源站": s_panel.get("box"), "clone": c_open.get("panelBox"),
        "★依据": "源站源码：`\"camera\"===z?` 分支渲染在**左侧资源栏**里，"
                 "不是浮层"})

    # ── S3 标题条逐字相等 ──
    ok("S3:★★★★★ clone 的标题条与源站**逐字相等**（232×48 @(48,52)，文案「添加机位」）",
       (c_title.get("box") or {}) == (s_title.get("box") or {})
       and (c_title.get("t") or "") == (s_title.get("t") or "") == "添加机位",
       {"源站": s_title.get("box"), "clone": c_title.get("box"),
        "源站文案": s_title.get("t"), "clone文案": c_title.get("t")})

    # ── S4 网格盒与列宽逐字相等 ──
    ok("S4:★★★★★ clone 的网格盒与源站**逐字相等**（232×980 @(48,100)）"
       "⟹ 且列宽**逐字相等**（`104px 104px`）⟹ ★ 2 列 × 104 + gap 8 = 232",
       (c_grid or {}) == (s_grid or {})
       and c_open.get("gridTemplateColumns") == s_panel.get("gridTemplateColumns"),
       {"源站网格": s_grid, "clone网格": c_grid,
        "源站列": s_panel.get("gridTemplateColumns"),
        "clone列": c_open.get("gridTemplateColumns")})

    # ── S5 15 枚预设逐行**几何**逐字相等 ──
    s_boxes = [(p.get("box"), p.get("svgBox")) for p in s_presets]
    c_boxes = [(c.get("box"), c.get("svgBox")) for c in c_cells]
    diff_rows = [i for i, (a, b) in enumerate(zip(s_boxes, c_boxes)) if a != b]
    ok("S5:★★★★★ clone 的 **15 枚预设逐枚几何逐字相等**"
       "（每枚的按钮盒 + 图标盒 全等）⟹ 包括「45° 俯拍」「过肩镜头（右）」"
       "这些**长标签**占的那一格",
       len(s_boxes) == 15 and len(c_boxes) == 15 and not diff_rows,
       {"不同的行号": diff_rows,
        "源站 15 枚几何": s_boxes,
        "clone 15 枚几何": c_boxes})

    # ── S6 15 枚预设的**文字**逐字相同 ──
    s_labels = [p.get("label") for p in s_presets]
    c_labels = [c.get("t") for c in c_cells]
    ok("S6:★★★★★ clone 的 15 枚预设**文字**与源站**逐字相同**"
       "（当前视角/正面中景/正面特写/正面全景/侧面跟拍/侧面近景/背面中景/"
       "俯拍全景/45° 俯拍/低角度仰拍/低角度广角/过肩镜头/过肩镜头（右）/鸟瞰/荷兰角）",
       s_labels == c_labels and len(c_labels) == 15
       and c_labels[0] == "当前视角" and c_labels[-1] == "荷兰角",
       {"源站": s_labels, "clone": c_labels})

    # ── S7 图标 path 逐字相等（15 枚共用一枚）──
    s_path = src_raw.get("唯一图标path") or ""
    c_paths = [c.get("pathD") or "" for c in c_cells]
    ok("S7:★★★★★ clone 的 15 枚预设图标 **SVG path 与源站逐字相同**"
       "（15 枚**共用同一枚** ⟹ 源站那枚是「机位」的通用符号）"
       "⟹ ★★ 期望值来自 raw（活体提取）⟹ 不是手打",
       bool(s_path) and len(c_paths) == 15
       and all(p == s_path for p in c_paths),
       {"源站 path 长度": len(s_path),
        "clone 15 枚是否全等源站": [p == s_path for p in c_paths],
        "clone 首枚 path": (c_paths[0] if c_paths else "")[:60]})

    # ── S8 图标的 **viewBox** 逐枚相等 ──
    # ★ 与 S5 严格分工：**S5 只读盒、S8 只读 viewBox** ⟹ 两者的阴性互不串门
    s_vb = [p.get("svgViewBox") for p in s_presets]
    c_vb = [c.get("svgViewBox") for c in c_cells]
    ok("S8:★★★★★ clone 的图标 **viewBox 逐枚**与源站相同"
       "（`0 0 16 16`）⟹ ★ 源站用的是 iconify `libtv` 图标集里的一枚"
       "⟹ ★★ 注意：**不能**把它收成集合再比「集合大小 == 1」——"
       "15 枚在**不同位置** ⟹ 集合必然有 8 个元素 ⟹ ★ 那是判据自己写错了",
       s_vb == c_vb and len(c_vb) == 15
       and all(v == "0 0 16 16" for v in c_vb),
       {"源站": s_vb[:3], "clone": c_vb[:3], "★逐枚全等": s_vb == c_vb,
        "★为什么这里不读盒": "盒的相等归 S5 ⟹ 两条判据读的字段不重叠 "
                          "⟹ 阴性互不串门"})

    # ── S9 第 0 枚「当前视角」的边框更亮 ──
    s_bright = [p.get("borderBright") for p in s_presets]
    c_bright = ["border-white/85" in (c.get("cls") or "") for c in c_cells]
    ok("S9:★★★★★ clone 的**第 0 枚「当前视角」边框更亮**（`border-white/85`）"
       "⟹ 其余 14 枚是 `border-white/10` ⟹ ★ 这条是**源站源码里的两处不同类名**"
       "（`border-white/85` vs `border-white/10`）⟹ 肉眼容易看漏",
       s_bright == c_bright
       and s_bright[0] is True
       and all(b is False for b in s_bright[1:]),
       {"源站": s_bright, "clone": c_bright})

    # ── S10 视图切换：点「添加机位」出面板，点「场景」切回场景树 ──
    # ★★ 判据必须读**视图判别字段**（`view`），不能读「有没有 232 宽的面板」——
    #   场景树**也是** 232 宽 ⟹ 用「有没有面板」当判据 ⟹ 恒真 ⟹ 判据等于没有。
    ok("S10:★★★★★ clone 的左侧资源栏会**在两个视图之间切换**"
       "（点 rail「添加机位」→ 机位预设面板；点「场景」→ 切回场景树）"
       "⟹ ★★ 这是源站的真实结构（源码 `\"camera\"===z?` 分支）"
       "⟹ ★ 而 clone 此前 rail 的「添加机位」是**直接加机位**（batch 540 的旧读数）"
       "⟹ ★★ 判据读的是**视图判别字段**（两者都 232 宽 ⟹ 「有没有面板」是恒真判据）",
       (clone_raw.get(K_CLONE_TREE) or {}).get("view") == "tree"
       and c_open.get("view") == "camera-presets"
       and (clone_raw.get(K_CLONE_BACK) or {}).get("view") == "tree"
       and clone_raw.get(K_CLONE_BACKTREE) is True,
       {"开台后 view": (clone_raw.get(K_CLONE_TREE) or {}).get("view"),
        "点添加机位后 view": c_open.get("view"),
        "点场景后 view": (clone_raw.get(K_CLONE_BACK) or {}).get("view"),
        "场景树还在": clone_raw.get(K_CLONE_BACKTREE),
        "★为什么不能读「有没有 232 宽的面板」": "场景树也是 232 宽 ⟹ 恒真"})

    # ── S11 源码锚点：clone 不再「点一下就加机位」 ──
    ok("S11:★★★★★ clone 的 rail「添加机位」**不再**是直接动作"
       "（`kind: \"action\"` 已改为 `\"panel\"`，并接到 `onOpenCameraPresets`）"
       "⟹ ★★ **batch 540 的旧读数（源站「添加机位」为直接动作）在本批被推翻**",
       '{ id: "add-camera", label: "添加机位", icon: Clapperboard, kind: "panel" }'
       in rail_src
       and "onOpenCameraPresets" in rail_src
       and "addDirectorCamera()" not in rail_src,
       {"rail 里的锚点": [ln.strip() for ln in rail_src.splitlines()
                     if "add-camera" in ln or "onOpenCameraPresets" in ln][:6],
        "★旧读数": "batch 540 写的是「源站 rail『添加机位』为直接动作（点击无面板）」"})

    # ── S12 源码锚点：面板组件的结构锚点 ──
    ok("S12:★★★★★ clone 的面板组件带**结构锚点**"
       "（`data-director-camera-preset-panel` / 每枚 `data-director-camera-preset`）"
       "⟹ 且**列表标签不是手打**：组件里那份清单由门禁 S6 按 raw 核验",
       "data-director-camera-preset-panel" in panel_src
       and "data-director-camera-preset=" in panel_src
       and "data-director-camera-preset-glyph" in panel_src
       and "gridTemplateColumns: \"104px 104px\"" in panel_src,
       {"组件里的锚点": [ln.strip() for ln in panel_src.splitlines()
                    if "data-director-camera-preset" in ln][:4],
        "★为什么网格宽度走 inline style": "4317 的 Tailwind 扫描是**冻结**的 "
                                     "⟹ 新增任意值类在 dev 上不生成"})

    # ── S13 源码锚点：Desk 的视图状态接线 ──
    ok("S13:★★★★★ clone 的 `DirectorDesk` 里**真的有**那个视图状态"
       "（`leftPanelView` = `\"tree\" | \"camera-presets\"`）"
       "⟹ 且左侧栏按它二选一渲染",
       "leftPanelView" in desk_src
       and '"camera-presets"' in desk_src
       and "DirectorCameraPresetPanel" in desk_src
       and "DirectorObjectTree" in desk_src
       # ★ 二选一的**渲染结构**（只在这一句里 ⟹ N13 删掉它就红）
       and ('leftPanelView === "camera-presets" ? (' in desk_src
            and "<DirectorCameraPresetPanel />" in desk_src
            and "<DirectorObjectTree />" in desk_src),
       {"desk 里的锚点": [ln.strip() for ln in desk_src.splitlines()
                     if "leftPanelView" in ln or "DirectorCameraPresetPanel" in ln][:6]})

    # ── S14 视图切换的两条源码路径（rail → desk）都在 ──
    ok("S14:★★★★★ rail 与 Desk 之间的**接线**两条都在"
       "（rail 调 `onOpenCameraPresets()` 开面板 / `onOpenCameraPresets(false)` 切回）"
       "⟹ ★ 「场景」条目必须能切回 ⟹ 否则用户会**卡在预设面板里**"
       "⟹ （这正是源站 `\"scene\"===z` 的那一支）",
       "onOpenCameraPresets?.()" in rail_src
       and "onOpenCameraPresets?.(false)" in rail_src
       and "onOpenCameraPresets={(open = true) =>" in desk_src,
       {"rail 里的调用": [ln.strip() for ln in rail_src.splitlines()
                    if "onOpenCameraPresets?" in ln][:3],
        "desk 里的接线": [ln.strip() for ln in desk_src.splitlines()
                    if "onOpenCameraPresets=" in ln][:2]})
    return C


# ── 阴性对照：每条**只**翻它自己那一条 ────────────────────────────────────────
def _negations():
    def n1(sr, cr, ps, rl, dk):
        # ★ 扰动必须打在**只有 S1 读**的字段上：源站的「预设项数」15→14。
        #   （早先扰动的是面板盒高 ⟹ 但 S2 是「源站 vs clone」比较 ⟹ 也读它 ⟹ 串门。）
        c = copy.deepcopy(sr)
        c[K_SRC_COUNT] = 14
        return c, cr, ps, rl, dk

    def n2(sr, cr, ps, rl, dk):
        c = copy.deepcopy(cr)
        c[K_CLONE_OPEN]["panelBox"] = {"x": 48, "y": 52, "w": 232, "h": 1027}
        return sr, c, ps, rl, dk

    def n3(sr, cr, ps, rl, dk):
        c = copy.deepcopy(cr)
        c[K_CLONE_OPEN]["title"]["box"]["y"] = 53
        return sr, c, ps, rl, dk

    def n4(sr, cr, ps, rl, dk):
        c = copy.deepcopy(cr)
        c[K_CLONE_OPEN]["gridTemplateColumns"] = "100px 100px"
        return sr, c, ps, rl, dk

    def n5(sr, cr, ps, rl, dk):
        c = copy.deepcopy(cr)
        c[K_CLONE_OPEN]["cells"][7]["box"]["x"] = 57
        return sr, c, ps, rl, dk

    def n6(sr, cr, ps, rl, dk):
        c = copy.deepcopy(cr)
        c[K_CLONE_OPEN]["cells"][0]["t"] = "当前视图"
        return sr, c, ps, rl, dk

    def n7(sr, cr, ps, rl, dk):
        c = copy.deepcopy(cr)
        c[K_CLONE_OPEN]["cells"][2]["pathD"] = "M0 0H16V16H0Z"
        return sr, c, ps, rl, dk

    def n8(sr, cr, ps, rl, dk):
        # ★ 扰动**只有 S8 读**的字段：viewBox（S5 只读盒，不读 viewBox）
        c = copy.deepcopy(cr)
        c[K_CLONE_OPEN]["cells"][3]["svgViewBox"] = "0 0 24 24"
        return sr, c, ps, rl, dk

    def n9(sr, cr, ps, rl, dk):
        c = copy.deepcopy(cr)
        c[K_CLONE_OPEN]["cells"][0]["cls"] = c[K_CLONE_OPEN]["cells"][0]["cls"].replace(
            "border-white/85", "border-white/10")
        return sr, c, ps, rl, dk

    def n10(sr, cr, ps, rl, dk):
        # ★ 扰动**视图判别字段**（只有 S10 读它）
        c = copy.deepcopy(cr)
        c[K_CLONE_BACK]["view"] = "camera-presets"
        return sr, c, ps, rl, dk

    def n11(sr, cr, ps, rl, dk):
        r = rl.replace(
            '{ id: "add-camera", label: "添加机位", icon: Clapperboard, kind: "panel" }',
            '{ id: "add-camera", label: "添加机位", icon: Clapperboard, kind: "action" }')
        return sr, cr, ps, r, dk

    def n12(sr, cr, ps, rl, dk):
        p = ps.replace("data-director-camera-preset-panel", "data-director-cam-panel")
        return sr, cr, p, rl, dk

    def n13(sr, cr, ps, rl, dk):
        # ★ 扰动**只有 S13 读**的结构：删掉「二选一渲染」那一支
        d = dk.replace('leftPanelView === "camera-presets" ? (', "false ? (")
        return sr, cr, ps, rl, d

    def n14(sr, cr, ps, rl, dk):
        r = rl.replace("onOpenCameraPresets?.(false)", "/* removed */")
        return sr, cr, ps, r, dk

    return [
        ("N1 把源站的「预设项数」改成 14 ⟹ S1 翻红", "S1", n1),
        ("N2 把 clone 面板盒高改成 1027 ⟹ S2 翻红", "S2", n2),
        ("N3 把 clone 标题条挪 1px ⟹ S3 翻红", "S3", n3),
        ("N4 把 clone 列宽改成 100px ⟹ S4 翻红", "S4", n4),
        ("N5 把 clone 第 8 枚挪 1px ⟹ S5 翻红", "S5", n5),
        ("N6 把「当前视角」写成「当前视图」⟹ S6 翻红", "S6", n6),
        ("N7 改坏 clone 第 3 枚的图标 path ⟹ S7 翻红", "S7", n7),
        ("N8 把 clone 第 4 枚的图标 viewBox 改成 0 0 24 24 ⟹ S8 翻红", "S8", n8),
        ("N9 把 clone 第 1 枚的亮边框改成普通边 ⟹ S9 翻红", "S9", n9),
        ("N10 把「点场景后仍有面板」改成 true ⟹ S10 翻红", "S10", n10),
        ("N11 把 rail 的 add-camera 改回 action ⟹ S11 翻红", "S11", n11),
        ("N12 改掉面板组件的 data 属性名 ⟹ S12 翻红", "S12", n12),
        ("N13 删掉 Desk 里「二选一渲染」那一支 ⟹ S13 翻红", "S13", n13),
        ("N14 删掉 rail 里「切回场景树」那条调用 ⟹ S14 翻红", "S14", n14),
    ]


def main():
    src_raw = json.loads(SRC_RAW.read_text(encoding="utf-8"))
    clone_raw = json.loads(CLONE_RAW.read_text(encoding="utf-8"))
    panel_src = SRC_PANEL.read_text(encoding="utf-8")
    rail_src = SRC_RAIL.read_text(encoding="utf-8")
    desk_src = SRC_DESK.read_text(encoding="utf-8")

    checks = build_checks(src_raw, clone_raw, panel_src, rail_src, desk_src)
    neg = []
    for label, expect, builder in _negations():
        args = builder(src_raw, clone_raw, panel_src, rail_src, desk_src)
        mc = build_checks(*args)
        turned = sorted({c["id"].split(":")[0] for c in mc if not c["ok"]})
        neg.append({"name": label, "期望翻红": expect, "实际翻红": turned,
                    "ok": turned == [expect]})

    passed = sum(1 for c in checks if c["ok"])
    report = {"batch": 832, "mode": "offline",
              "totals": {"passed": passed, "total": len(checks)},
              "阴性对照": {"passed": sum(1 for n in neg if n["ok"]),
                           "total": len(neg)},
              "checks": checks, "阴性": neg}
    (BATCH / "verify-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("主检查 %d/%d ｜ 阴性对照 %d/%d" % (
        passed, len(checks), report["阴性对照"]["passed"], len(neg)))
    for c in checks:
        print(("  ✔ " if c["ok"] else "  ✘ ") + c["id"][:92])
    for n in neg:
        print(("  ✔ " if n["ok"] else "  ✘ ") + n["name"][:50]
              + " → 实际翻红 " + ",".join(n["实际翻红"]))
    return 0 if passed == len(checks) and all(n["ok"] for n in neg) else 1


if __name__ == "__main__":
    sys.exit(main())

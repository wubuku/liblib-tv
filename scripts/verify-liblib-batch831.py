#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 831 验收器 —— clone 导演台「帮助 → 快捷键」面板（**实施批次**）。

## 本批做了什么

batch 830 登记了一个产品缺口：源站导演台**有**「帮助 → 快捷键」面板，
clone **没有**（只有一枚 `aria-label="帮助"` 的圆钮，**点了没反应**）。
本批把它按源站的当前形态建出来，并逐字对齐几何。

## 源站形态（2026-10-21 实测 + 源站组件代码 `0fmehki05gkzw.js.js`）

- 「帮助」圆钮 32×32 @(8,1040)，`aria-haspopup="menu"`
- 点开的是一枚**向上弹的 role=menu**（不是页签）：120×78 @(8,954)，
  两枚 menuitem：快捷键 / 使用教程，各 110×32
- 「快捷键」打开 **role=dialog aria-modal** 的 480×314 @(297,60)
  （源站代码里是**写死的绝对偏移** `left-[297px] top-[60px]`，不是居中）
- 标题「快捷键」48×22 @(322,81)／两列各 192×228 @(322,123) 与 @(563,123)
- 12 行，每行 h-7；键帽 28×28（⌘ 徽标是 **16×16 的 SVG**，不是文字）

## 门禁怎么判

**逐字比对**：源站与 clone 的读数用**同一段读数 JS** 采（`probes/help831.py`
与 `probes/clone831.py`），⟹ 两边字段可直接相等比较。几何、12 行标签与键帽
逐项相等才判过；另外有 4 条**源码锚点**（静态核验 clone 的实现，防回退）。

★ 纪律：每条判据都有**只翻它自己那一条**的阴性对照。
"""
import copy
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
BATCH = ROOT / "docs" / "research" / "liblib-canvas-batch831-2026-10-01"
RAW = BATCH / "raw"

# 源站的 ⌘ / ⌫ 图标 path（**期望值从 raw 读**，不是手打 —— 见下面 S12 的说明）
SRC_GEOM = RAW / "source-831-help-geometry.json"
SRC_ZORDER = RAW / "source-831-help-zorder.json"
SRC_TITLE = RAW / "source-831-title-detail.json"
SRC_CODE = RAW / "source-831-shortcut-code.json"
GLYPH_PIX = RAW / "glyph-831-pixel-compare.json"
CLONE_GEOM = RAW / "clone-831-help-geometry.json"
SRC_DIALOG = ROOT / "src" / "components" / "director" / "DirectorShortcutsDialog.tsx"
SRC_RAIL = ROOT / "src" / "components" / "director" / "DirectorIconRail.tsx"
SRC_DESK = ROOT / "src" / "components" / "director" / "DirectorDesk.tsx"
SRC_TIMELINE = ROOT / "src" / "components" / "director" / "DirectorTimeline.tsx"

# 探针用的视口（源站与 clone 两边同尺寸 ⟹ 绝对几何可直接比）
VIEWPORT_W = 1920
VIEWPORT_H = 1080

# ── ★ 探针区开始 ────────────────────────────────────────────────────────────────
# ★ 本批的「探针」＝ **读入库读数的键名**（不是 DOM 选择器）：
#   键名一旦漂移，下面这些常量就取不到值 ⟹ 门禁自己会红。
K_SRC_MENU = "②菜单打开"
K_SRC_DIALOG = "③快捷键对话框"
K_SRC_HELP_BTN = "①帮助按钮"
K_CLONE_MENU = "②菜单打开"
K_CLONE_DIALOG = "③快捷键对话框"
K_CLONE_HELP_BTN = "①帮助按钮"
K_CLONE_CLOSED = "④点外面后"
K_CLONE_ESC = "⑤Esc后"
K_CLONE_TUTORIAL = "⑥使用教程后"
K_CLONE_COVER_OPEN = "⓪时间轴展开时"
K_CLONE_COVER_CLOSED = "⓪b关掉时间轴后"
K_Z_OPEN = "①时间轴未开"
K_Z_EXPANDED = "②时间轴已开"
K_TITLE = "标题"
# ── ★ 探针区结束 ────────────────────────────────────────────────────────────────

# ★★ 源站的 ⌘ / ⌫ 图标 path：**期望值不在这里手打**，而是从 raw 读
#   （raw/source-831-shortcut-code.json，由 probes/extract831.py 从源站 chunk
#    **机器提取**）。
#   ⚠️ 本批第一版把 path **手打**进了本文件 ⟹ 门禁 S12 变成**自证式判据**
#      （只证明「clone 里那段 == 我手打的那段」⟹ 不证明「那段 == 源站的」）
#      ⟹ 而手打时确实把**下半部两条臂的先后顺序抄反了** ⟹ 门禁照样 15/15 全绿。
#      ⟹ 这是「手打的标识符是输入，不是测量」的实例：它被门禁读回后就成了"事实"。
# ⟹ 修法：期望值来自入库的**源站原文摘录**（含 path 所在的代码 excerpt），
#   抄错一个字符 ⟹ S12 当场翻红。
SRC_COMMAND_PATH = None  # 由 load_source_code() 填
SRC_DELETE_PATH = None   # 由 load_source_code() 填
SRC_CODE_DOC = None      # 由 load_source_code() 填

# 12 行的标签文字（源站面板原文，clone 必须逐字相同）
SHORTCUT_LABELS = [
    "俯视视角", "重置视角", "移动", "旋转", "缩放", "移动当前视角",
    "正面视角", "网格吸附", "打组", "解组", "撤销", "删除",
]


def load_source_code(doc):
    """从 raw 里取期望值（**不手打**）⟹ 并把全局常量填上。"""
    global SRC_COMMAND_PATH, SRC_DELETE_PATH, SRC_CODE_DOC
    SRC_CODE_DOC = doc
    SRC_COMMAND_PATH = (doc.get("图标") or {}).get("command", {}).get("path") or ""
    SRC_DELETE_PATH = (doc.get("图标") or {}).get("delete", {}).get("path") or ""
    return SRC_COMMAND_PATH, SRC_DELETE_PATH


def _box(obj):
    return obj.get("box") if isinstance(obj, dict) else None


def _rows_kids(dialog):
    """把一个对话框的 12 行摊平成 [(标签文字, 标签盒, 徽标文字, 徽标盒), …]"""
    out = []
    for row in (dialog.get("rows") or []):
        kids = row.get("kids") or []
        if len(kids) < 2:
            out.append((None, None, None, None))
            continue
        out.append((kids[0].get("t"), kids[0].get("box"),
                    kids[1].get("t"), kids[1].get("box")))
    return out


def build_checks(src_geom, clone_geom, src_zorder, src_title, src_code,
                 glyph_pix, dialog_src, rail_src, desk_src, timeline_src):
    C = []

    def ok(cid, cond, detail=None):
        C.append({"id": cid, "name": cid, "ok": bool(cond),
                  "detail": detail if detail is not None else ""})

    s_menu = ((src_geom.get(K_SRC_MENU) or {}).get("menu") or {})
    s_dlg = src_geom.get(K_SRC_DIALOG) or {}
    s_help = (src_geom.get(K_SRC_HELP_BTN) or {}).get("helpButton") or {}
    c_menu = ((clone_geom.get(K_CLONE_MENU) or {}).get("menu") or {})
    c_dlg = clone_geom.get(K_CLONE_DIALOG) or {}
    c_help = (clone_geom.get(K_CLONE_HELP_BTN) or {}).get("helpButton") or {}
    c_closed = clone_geom.get(K_CLONE_CLOSED) or {}
    c_esc = clone_geom.get(K_CLONE_ESC) or {}
    c_tut = clone_geom.get(K_CLONE_TUTORIAL) or {}
    c_cover_open = clone_geom.get(K_CLONE_COVER_OPEN) or {}
    c_cover_closed = clone_geom.get(K_CLONE_COVER_CLOSED) or {}

    # ── S1 源站读数自洽（判据的地基）──
    ok("S1:★★★ **源站形态**（读数自洽）：「帮助」圆钮 32×32 @(8,1040)、"
       "菜单 120×78 @(8,954)、快捷键对话框 480×314 @(297,60)、"
       "两列各 192×228 @(322,123) 与 @(563,123)、**12 行**、**4 个 16×16 的 SVG 图标**",
       (s_help.get("box") or {}) == {"x": 8, "y": 1040, "w": 32, "h": 32}
       and (s_menu.get("box") or {}) == {"x": 8, "y": 954, "w": 120, "h": 78}
       and (s_dlg.get("box") or {}) == {"x": 297, "y": 60, "w": 480, "h": 314}
       and [(c.get("box") or {}) for c in s_dlg.get("cols") or []]
       == [{"x": 322, "y": 123, "w": 192, "h": 228},
           {"x": 563, "y": 123, "w": 192, "h": 228}]
       and len(s_dlg.get("rows") or []) == 12
       and len(s_dlg.get("allSvgs") or []) == 4,
       {"帮助按钮": s_help.get("box"), "菜单": s_menu.get("box"),
        "对话框": s_dlg.get("box"), "列": [c.get("box") for c in s_dlg.get("cols") or []],
        "行数": len(s_dlg.get("rows") or []), "SVG 数": len(s_dlg.get("allSvgs") or [])})

    # ── S2 菜单盒逐字相等 ──
    ok("S2:★★★★★ clone 的「帮助」菜单盒与源站**逐字相等**（120×78 @(8,954)）"
       "⟹ 菜单是**向上弹**的（源站 `absolute bottom-full left-0`）",
       (c_menu.get("box") or {}) == (s_menu.get("box") or {})
       and (c_menu.get("box") or {}) != {},
       {"源站": s_menu.get("box"), "clone": c_menu.get("box"),
        "★依据": "源站代码：`absolute bottom-full left-0 z-50 pb-2` 包一层，"
               "内层 `w-[120px] … rounded-xl border border-white/10 p-1`"})

    # ── S3 菜单两项逐字相等 ──
    s_items = [(i.get("t"), i.get("box")) for i in s_menu.get("items") or []]
    c_items = [(i.get("t"), i.get("box")) for i in c_menu.get("items") or []]
    ok("S3:★★★★★ clone 的两枚菜单项（**快捷键** / **使用教程**）与源站**逐字相等**"
       "（各 110×32 @(13,959) 与 @(13,995)）",
       s_items == c_items and len(c_items) == 2
       and c_items[0][0] == "快捷键" and c_items[1][0] == "使用教程",
       {"源站": s_items, "clone": c_items})

    # ── S4 对话框盒逐字相等 ──
    ok("S4:★★★★★ clone 的快捷键对话框与源站**逐字相等**（480×314 @(297,60)，"
       "`role=dialog` + `aria-modal=true` + `aria-label=快捷键`）"
       "⟹ 源站是**写死的绝对偏移** `left-[297px] top-[60px]`（不是居中）",
       (c_dlg.get("box") or {}) == (s_dlg.get("box") or {})
       and c_dlg.get("aria") == "快捷键" and c_dlg.get("ariaModal") == "true"
       and s_dlg.get("aria") == c_dlg.get("aria")
       and s_dlg.get("ariaModal") == c_dlg.get("ariaModal"),
       {"源站": s_dlg.get("box"), "clone": c_dlg.get("box"),
        "aria": c_dlg.get("aria"), "aria-modal": c_dlg.get("ariaModal"),
        "★依据": "源站代码：`<div class=\"absolute left-[297px] top-[60px]\">` 包着对话框"})

    # ── S5 标题盒逐字相等（含那 4px 的来源）──
    s_title = (src_title.get(K_TITLE) or {}).get("h2") or {}
    # ★ 计算样式是**简写** `0px 0px 8px`（不是 `margin-bottom: 8px`）⟹ 取最后一项
    s_h2_margin = ((s_title.get("style") or {}).get("margin") or "").split()
    ok("S5:★★★★★ clone 的标题盒与源站**逐字相等**（48×22 @(322,**81**)）"
       "⟹ ★★ 那 4px 的来源查清了：源站 CSS **没重置标题的下外边距** ⟹ "
       "h2 带 UA 默认 `margin-bottom: 8px` ⟹ 在 22px 高的 flex 行里外边距盒居中 ⟹ "
       "边框盒被抬到行顶之上 4px（85→81）⟹ clone 的 preflight 清了 margin ⟹ "
       "本批照抄源站这个行为",
       (c_dlg.get("title") or {}).get("box") == (s_dlg.get("title") or {}).get("box")
       and (s_dlg.get("title") or {}).get("box")
       == {"x": 322, "y": 81, "w": 48, "h": 22}
       and len(s_h2_margin) == 3 and s_h2_margin[2] == "8px"
       and "marginBottom: 8" in dialog_src,
       {"源站标题": (s_dlg.get("title") or {}).get("box"),
        "clone标题": (c_dlg.get("title") or {}).get("box"),
        "源站 h2 的 margin 简写": (s_title.get("style") or {}).get("margin")})

    # ── S6 两列逐字相等 ──
    ok("S6:★★★★★ clone 的两列与源站**逐字相等**"
       "（各 192×228 @(322,123) 与 @(563,123)，中间 1px 竖线、左右各 24px）",
       [c.get("box") for c in c_dlg.get("cols") or []]
       == [c.get("box") for c in s_dlg.get("cols") or []],
       {"源站": [c.get("box") for c in s_dlg.get("cols") or []],
        "clone": [c.get("box") for c in c_dlg.get("cols") or []]})

    # ── S7 12 行逐行**几何**逐字相等（标签盒 + 键帽盒）──
    # ★ 与 S8 严格分工：**S7 只读盒、S8 只读文字** ⟹ 两者的阴性互不串门
    s_row_boxes = [(r[1], r[3]) for r in _rows_kids(s_dlg)]
    c_row_boxes = [(r[1], r[3]) for r in _rows_kids(c_dlg)]
    diff_rows = [i for i, (a, b) in enumerate(zip(s_row_boxes, c_row_boxes)) if a != b]
    ok("S7:★★★★★ clone 的 **12 行逐行几何逐字相等**（每行的标签盒 + 键帽盒 全等）"
       "⟹ 包括「WASDQE」那枚 74 宽的键帽、「打组 ⌘G」「解组 ⌘⇧D」「撤销 ⌘Z」"
       "三枚带 ⌘ 的行",
       len(s_row_boxes) == 12 and len(c_row_boxes) == 12 and not diff_rows,
       {"不同的行号": diff_rows,
        "源站 12 行几何": s_row_boxes,
        "clone 12 行几何": c_row_boxes})

    # ── S8 12 行标签文字与源站逐字相同 ──
    s_labels = [r[0] for r in _rows_kids(s_dlg)]
    c_labels = [r[0] for r in _rows_kids(c_dlg)]
    ok("S8:★★★★ clone 的 12 行标签文字与源站**逐字相同**"
       "（俯视视角/重置视角/移动/旋转/缩放/移动当前视角 ‖ 正面视角/网格吸附/"
       "打组/解组/撤销/删除）",
       s_labels == c_labels and c_labels == SHORTCUT_LABELS,
       {"源站": s_labels, "clone": c_labels})

    # ── S9 ⌘ / ⌫ 是 SVG 图标，不是文字 ──
    c_svgs = c_dlg.get("allSvgs") or []
    s_svgs = s_dlg.get("allSvgs") or []
    ok("S9:★★★★★ clone 的 **⌘ 与 ⌫ 徽标是 16×16 的 SVG**（共 4 个：⌘×3 + ⌫×1）"
       "⟹ ★★ 这正是 batch 830 的教训：⌘ 是**图标**、纯文本读数器读不到它"
       "⟹ 「撤销 = Z」那个读数才是盲区",
       len(c_svgs) == 4 and len(s_svgs) == 4
       and all(s.get("w") == 16 and s.get("h") == 16 for s in c_svgs)
       and all((s.get("x"), s.get("y"), s.get("w"), s.get("h"))
               == (s2.get("x"), s2.get("y"), s2.get("w"), s2.get("h"))
               for s, s2 in zip(c_svgs, s_svgs)),
       {"clone 的 SVG": [(s.get("x"), s.get("y"), s.get("w"), s.get("h")) for s in c_svgs],
        "源站的 SVG": [(s.get("x"), s.get("y"), s.get("w"), s.get("h")) for s in s_svgs]})

    # ── S10 交互：点外面关闭 + Esc 关闭 ──
    ok("S10:★★★★ clone 的对话框**点外面会关**、**Esc 也会关**"
       "（源站：`absolute inset-0 z-40` 遮罩 onMouseDown 关闭 + "
       "`if(tN){\"escape\"===n&&tL(!1);return}`）",
       c_closed.get("dialogs") == 0 and c_closed.get("overlay") == 0
       and c_esc.get("dialogs") == 0,
       {"点外面后": c_closed, "Esc后": c_esc})

    # ── S11 「使用教程」不是死按钮 + 引导泡在视口内 ──
    tut_box = c_tut.get("box") or {}
    ok("S11:★★★★★ clone 的「使用教程」**不是死按钮**：点了之后引导气泡出现"
       "（260×114 @(163,**850**)）⟹ ★★ 而且它**完全落在视口内**"
       "（y+h = 964 ≤ 1080）⟹ ★ 这条是本批顺手修掉的**旧缺陷**："
       "引导泡原先渲染在时间轴 section 里 ⟹ 祖先创建了 containing block ⟹ "
       "`top: calc(100vh - 230px)` 被算成相对那个祖先 ⟹ 绝对 y=**1749** ⟹ 掉到视口外",
       c_tut.get("coach") is True
       and tut_box == {"x": 163, "y": 850, "w": 260, "h": 114}
       and tut_box.get("y", 0) + tut_box.get("h", 0) <= VIEWPORT_H,
       {"引导泡": tut_box, "文字": (c_tut.get("text") or "")[:40],
        "视口高": VIEWPORT_H, "视口内": tut_box.get("y", 0) + tut_box.get("h", 0) <= VIEWPORT_H,
        "★修法": "改用 createPortal(…, document.body)（源站就是这么做的）"})

    # ── S12 源码锚点：两段图标 path 逐字复现（期望值来自 raw，不是手打）──
    ok("S12:★★★★★ clone 的组件里**逐字**复现了源站那两段图标 path"
       "（⌘ 的 `M5.25 5.25H10.75…` 与 ⌫ 的 `M6 5.75L10 9.75…`）"
       "⟹ 图标形状与源站同源，不是自造的近似图形"
       "⟹ ★★ **期望值来自 raw**（`probes/extract831.py` 从源站 chunk **机器提取**）"
       "⟹ ★ 不是手打 ⟹ 抄错一个字符就翻红",
       bool(SRC_COMMAND_PATH) and bool(SRC_DELETE_PATH)
       and SRC_COMMAND_PATH in dialog_src and SRC_DELETE_PATH in dialog_src,
       {"⌘ path 命中": SRC_COMMAND_PATH in dialog_src,
        "⌫ path 命中": SRC_DELETE_PATH in dialog_src,
        "期望值来源": "raw/source-831-shortcut-code.json（机器提取）",
        "★依据": "源站 chunk 0fmehki05gkzw.js.js 的 mC / mA 两个 SVG 组件"})

    # ── S13 源码锚点：帮助按钮的可及性与 aria ──
    ok("S13:★★★★★ clone 的「帮助」按钮带 `aria-haspopup=\"menu\"` 与 `aria-expanded`"
       "（源站同一款）⟹ 且菜单项是 `role=\"menuitem\"`"
       "⟹ ★「帮助」不再是那枚点了没反应的圆钮",
       'aria-haspopup="menu"' in rail_src
       and "aria-expanded={helpMenuOpen}" in rail_src
       and 'role="menuitem"' in rail_src
       and "data-director-help-menu-item" in rail_src,
       {"rail 里的锚点": [ln.strip() for ln in rail_src.splitlines()
                     if "aria-haspopup" in ln or "aria-expanded" in ln
                     or 'role="menuitem"' in ln][:4]})

    # ── S14 源码锚点：引导泡必须 portal 到 body（防回退）──
    ok("S14:★★★★★ clone 的引导气泡**必须**用 `createPortal(…, document.body)`"
       "（源站同款）⟹ 否则 fixed 会被祖先的 containing block 接管 ⟹ "
       "气泡掉到视口外（y=1749）⟹ 这条判据专门防这个回退",
       "createPortal(" in timeline_src
       and "document.body" in timeline_src
       and "data-director-timeline-coachmark" in timeline_src
       and "zIndex: 1800" in timeline_src,
       {"timeline 里的锚点": [ln.strip() for ln in timeline_src.splitlines()
                       if "createPortal(" in ln or "document.body" in ln
                       or "zIndex: 1800" in ln][:5],
        "★为什么 z 1800": "portal 到 body 后脱离导演台的 z-[100] 上下文 ⟹ "
                     "要用源站引导浮层同款的 z-[1800] 才压得住"})

    # ── S15 「帮助」可达性的前提：源站时间轴展开时也盖住它（clone 同构）──
    z_open = (src_zorder.get(K_Z_OPEN) or {}).get("stack") or []
    z_exp = (src_zorder.get(K_Z_EXPANDED) or {}).get("stack") or []
    ok("S15:★★★★★ **可达性的前提**记录在案：源站时间轴**展开**时「帮助」按钮"
       "**同样被盖住**（命中的是时间轴的条）⟹ ⟹ clone 的「被盖住」是**同构**的；"
       "真正的差别只在**默认值**（源站时间轴默认关 ⟹ 帮助按钮平时可达）"
       "⟹ ★ 本批把这条差异**如实记账**，不改 clone 的时间轴默认态"
       "（88 个门禁脚本依赖 clone 的时间轴存在）",
       (c_cover_open.get("timelineOpen") is True
        and c_cover_open.get("hitAria") == "收起属性")
       and (c_cover_closed.get("timelineOpen") is False
            and c_cover_closed.get("hitTag") == "path")
       and z_open and z_open[0].get("aria") == "帮助"
       and z_exp and z_exp[0].get("aria") != "帮助",
       {"clone 时间轴展开时": c_cover_open, "clone 关掉后": c_cover_closed,
        "源站时间轴未开时命中": (z_open[0] if z_open else {}).get("aria"),
        "源站时间轴展开时命中": (z_exp[0] if z_exp else {}).get("aria"),
        "★差异": "源站时间轴默认**关** ⟹ 帮助按钮平时可达；clone 默认**开** ⟹ 被盖住"})

    # ── S16 raw 自身可信：期望值必须是**源站原文摘录**里的东西 ──
    icons = (src_code or {}).get("图标") or {}
    excerpts = (src_code or {}).get("代码摘录") or {}
    ok("S16:★★★★★ **期望值的来源**可信：raw 里的两段 path 必须**嵌在它们自己的"
       "源站代码 excerpt 里**（excerpt 是从 chunk 原文截下来的）"
       "⟹ ★★ raw 不是「一个来源不明的字符串常量」"
       "⟹ ★★ 而且门禁核验的是「clone == 源站原文」，不是「clone == 我抄的」"
       "⟹ ★ 顺带核验类名锚点全部命中（面板/菜单/对话框的结构没抄错）",
       bool(icons)
       and all(g.get("path") and g["path"] in (g.get("excerpt") or "")
               for g in icons.values())
       and all(g.get("path_len") == len(g.get("path") or "")
               for g in icons.values())
       and all((g.get("path_offset") or 0) >= 0 for g in icons.values())
       and not (src_code or {}).get("未命中锚点")
       and all(excerpts.get(k) for k in ("帮助菜单", "快捷键对话框", "面板组件")),
       {"path 嵌在自己的 excerpt 里": {
           k: bool(g.get("path") and g["path"] in (g.get("excerpt") or ""))
           for k, g in icons.items()},
        "path 长度自洽": {
            k: g.get("path_len") == len(g.get("path") or "") for k, g in icons.items()},
        "未命中锚点": (src_code or {}).get("未命中锚点"),
        "代码摘录齐备": sorted(excerpts.keys()),
        "★这条是本批的教训": "第一版期望值是**手打**的 ⟹ 门禁成了自证式判据 "
                              "⟹ 手打时把 ⌘ path 下半部两条臂的先后顺序抄反了，"
                              "门禁却照样 15/15 全绿"})

    # ── S17 ⌘ 徽标的**像素**与源站同形（path 对了 ⟹ 渲染也对）──
    g = (glyph_pix or {}).get("command") or {}
    ok("S17:★★★★★ clone 的 **⌘ 徽标与源站逐像素同形**"
       "（同一坐标 16×16 裁剪，最大绝对差 ≤ 24 且差>8 的像素 ≤ 2）"
       "⟹ ★★ 这条**证明了 path 抄对了**：改对之前那版的实测是"
       "**最大差 54/255、10 个像素差>8**（明显不同形）"
       "⟹ ★★ 「path 字符串相等」只证明**数据**一致 ⟹ 这一条才证明**渲染**一致",
       bool(g) and g.get("判定") == "同形"
       and g.get("最大绝对差", 999) <= 24
       and g.get("差 > 8 的像素数", 999) <= 2
       and g.get("总像素数") == 256,
       {"判定": g.get("判定"), "最大绝对差": g.get("最大绝对差"),
        "差 > 8 的像素数": g.get("差 > 8 的像素数"),
        "总像素数": g.get("总像素数"), "对齐位移": g.get("对齐位移"),
        "★对照": "path 抄错那版的实测：最大差 54、10 个像素差>8"})
    return C


# ── 阴性对照：每条**只**翻它自己那一条 ────────────────────────────────────────
def _negations():
    def n1(sg, cg, sz, st, sc, gp, ds, rl, dk, tl):
        # ★ 扰动必须打在**只有 S1 读**的字段上：源站的「帮助」按钮盒 32→33。
        #   （早先扰动的是源站菜单盒高，但 S2 也拿源站菜单盒跟 clone 比 ⟹ 会串门。）
        c = copy.deepcopy(sg)
        c[K_SRC_HELP_BTN]["helpButton"]["box"] = {"x": 8, "y": 1040, "w": 33, "h": 32}
        return c, cg, sz, st, sc, gp, ds, rl, dk, tl

    def n2(sg, cg, sz, st, sc, gp, ds, rl, dk, tl):
        c = copy.deepcopy(cg)
        c[K_CLONE_MENU]["menu"]["box"] = {"x": 8, "y": 954, "w": 120, "h": 80}
        return sg, c, sz, st, sc, gp, ds, rl, dk, tl

    def n3(sg, cg, sz, st, sc, gp, ds, rl, dk, tl):
        c = copy.deepcopy(cg)
        c[K_CLONE_MENU]["menu"]["items"][1]["box"]["y"] = 996
        return sg, c, sz, st, sc, gp, ds, rl, dk, tl

    def n4(sg, cg, sz, st, sc, gp, ds, rl, dk, tl):
        c = copy.deepcopy(cg)
        c[K_CLONE_DIALOG]["box"] = {"x": 297, "y": 60, "w": 480, "h": 315}
        return sg, c, sz, st, sc, gp, ds, rl, dk, tl

    def n5(sg, cg, sz, st, sc, gp, ds, rl, dk, tl):
        c = copy.deepcopy(cg)
        c[K_CLONE_DIALOG]["title"]["box"]["y"] = 85
        return sg, c, sz, st, sc, gp, ds, rl, dk, tl

    def n6(sg, cg, sz, st, sc, gp, ds, rl, dk, tl):
        c = copy.deepcopy(cg)
        c[K_CLONE_DIALOG]["cols"][0]["box"]["x"] = 323
        return sg, c, sz, st, sc, gp, ds, rl, dk, tl

    def n7(sg, cg, sz, st, sc, gp, ds, rl, dk, tl):
        c = copy.deepcopy(cg)
        c[K_CLONE_DIALOG]["rows"][5]["kids"][1]["box"]["w"] = 72
        return sg, c, sz, st, sc, gp, ds, rl, dk, tl

    def n8(sg, cg, sz, st, sc, gp, ds, rl, dk, tl):
        c = copy.deepcopy(cg)
        c[K_CLONE_DIALOG]["rows"][0]["kids"][0]["t"] = "顶视视角"
        return sg, c, sz, st, sc, gp, ds, rl, dk, tl

    def n9(sg, cg, sz, st, sc, gp, ds, rl, dk, tl):
        c = copy.deepcopy(cg)
        c[K_CLONE_DIALOG]["allSvgs"] = []
        return sg, c, sz, st, sc, gp, ds, rl, dk, tl

    def n10(sg, cg, sz, st, sc, gp, ds, rl, dk, tl):
        c = copy.deepcopy(cg)
        c[K_CLONE_ESC]["dialogs"] = 1
        return sg, c, sz, st, sc, gp, ds, rl, dk, tl

    def n11(sg, cg, sz, st, sc, gp, ds, rl, dk, tl):
        c = copy.deepcopy(cg)
        c[K_CLONE_TUTORIAL]["box"] = {"x": 163, "y": 1749, "w": 260, "h": 114}
        return sg, c, sz, st, sc, gp, ds, rl, dk, tl

    def n12(sg, cg, sz, st, sc, gp, ds, rl, dk, tl):
        # ★ 扰动 clone 源码里那两段 path ⟹ S12（读 clone 与 raw）翻红
        d = ds.replace(SRC_COMMAND_PATH, "M0 0H16V16H0Z")
        return sg, cg, sz, st, sc, gp, d, rl, dk, tl

    def n16(sg, cg, sz, st, sc, gp, ds, rl, dk, tl):
        # ★ 扰动 **raw 自身**：把 ⌘ path 从它的源站 excerpt 里摘掉 ⟹
        #   S16（核验 raw 是原文摘录）翻红，而 S12 不动（clone 里那段没变）。
        c = copy.deepcopy(sc)
        g = c["图标"]["command"]
        g["excerpt"] = g["excerpt"].replace(g["path"], "M0 0H16V16H0Z")
        return sg, cg, sz, st, c, gp, ds, rl, dk, tl

    def n17(sg, cg, sz, st, sc, gp, ds, rl, dk, tl):
        # ★ 扰动**像素比对读数**：把最大绝对差改成「path 抄错那版」的实测值 54
        #   ⟹ S17 翻红（证明这条判据有牙），而别的判据都不读这个字段。
        c = copy.deepcopy(gp)
        c["command"]["最大绝对差"] = 54
        c["command"]["差 > 8 的像素数"] = 10
        c["command"]["判定"] = "★不同形"
        return sg, cg, sz, st, sc, c, ds, rl, dk, tl

    def n13(sg, cg, sz, st, sc, gp, ds, rl, dk, tl):
        r = rl.replace('aria-haspopup="menu"', 'aria-haspopup="listbox"')
        return sg, cg, sz, st, sc, gp, ds, r, dk, tl

    def n14(sg, cg, sz, st, sc, gp, ds, rl, dk, tl):
        t = tl.replace("createPortal(", "renderInline(")
        return sg, cg, sz, st, sc, gp, ds, rl, dk, t

    def n15(sg, cg, sz, st, sc, gp, ds, rl, dk, tl):
        c = copy.deepcopy(cg)
        c[K_CLONE_COVER_OPEN]["hitAria"] = "帮助"
        return sg, c, sz, st, sc, gp, ds, rl, dk, tl

    return [
        ("N1 把源站「帮助」按钮盒宽改成 33 ⟹ S1 翻红", "S1", n1),
        ("N2 把 clone 菜单盒高改成 80 ⟹ S2 翻红", "S2", n2),
        ("N3 把 clone 第二枚菜单项挪 1px ⟹ S3 翻红", "S3", n3),
        ("N4 把 clone 对话框高改成 315 ⟹ S4 翻红", "S4", n4),
        ("N5 把 clone 标题挪回 85 ⟹ S5 翻红", "S5", n5),
        ("N6 把 clone 左列挪 1px ⟹ S6 翻红", "S6", n6),
        ("N7 把 WASDQE 键帽宽改成 72 ⟹ S7 翻红", "S7", n7),
        ("N8 把「俯视视角」写成「顶视视角」⟹ S8 翻红", "S8", n8),
        ("N9 把 clone 的 SVG 列表清空 ⟹ S9 翻红", "S9", n9),
        ("N10 把 Esc 后的 dialogs 改成 1 ⟹ S10 翻红", "S10", n10),
        ("N11 把引导泡挪回视口外(1749) ⟹ S11 翻红", "S11", n11),
        ("N12 改坏 clone 的 ⌘ 图标 path ⟹ S12 翻红", "S12", n12),
        ("N13 把 aria-haspopup 改掉 ⟹ S13 翻红", "S13", n13),
        ("N14 把 createPortal 改掉 ⟹ S14 翻红", "S14", n14),
        ("N15 把「时间轴展开时命中」改成帮助 ⟹ S15 翻红", "S15", n15),
        ("N16 把 raw 里的 ⌘ path 从它的源站 excerpt 里摘掉 ⟹ S16 翻红", "S16", n16),
        ("N17 把像素比对的差异改成「path 抄错那版」的实测值 ⟹ S17 翻红", "S17", n17),
    ]


def main():
    src_geom = json.loads(SRC_GEOM.read_text(encoding="utf-8"))
    clone_geom = json.loads(CLONE_GEOM.read_text(encoding="utf-8"))
    src_zorder = json.loads(SRC_ZORDER.read_text(encoding="utf-8"))
    src_title = json.loads(SRC_TITLE.read_text(encoding="utf-8"))
    src_code = json.loads(SRC_CODE.read_text(encoding="utf-8"))
    glyph_pix = json.loads(GLYPH_PIX.read_text(encoding="utf-8"))
    # ★ 期望值从 raw 读（**不手打**）⟹ 见文件头「手打的标识符是输入，不是测量」
    load_source_code(src_code)
    dialog_src = SRC_DIALOG.read_text(encoding="utf-8")
    rail_src = SRC_RAIL.read_text(encoding="utf-8")
    desk_src = SRC_DESK.read_text(encoding="utf-8")
    timeline_src = SRC_TIMELINE.read_text(encoding="utf-8")

    checks = build_checks(src_geom, clone_geom, src_zorder, src_title, src_code,
                          glyph_pix, dialog_src, rail_src, desk_src, timeline_src)
    neg = []
    for label, expect, builder in _negations():
        args = builder(src_geom, clone_geom, src_zorder, src_title, src_code,
                       glyph_pix, dialog_src, rail_src, desk_src, timeline_src)
        mc = build_checks(*args)
        turned = sorted({c["id"].split(":")[0] for c in mc if not c["ok"]})
        neg.append({"name": label, "期望翻红": expect, "实际翻红": turned,
                    "ok": turned == [expect]})

    passed = sum(1 for c in checks if c["ok"])
    report = {"batch": 831, "mode": "offline",
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

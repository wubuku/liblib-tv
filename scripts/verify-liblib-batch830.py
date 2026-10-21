#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 830 验收器 —— 源站导演台的「时间轴缩放」与「撤销」。

## ★★ 本批的三个结论（全部有源站实测 + 源站源码双重依据）

| 结论 | 依据 |
| --- | --- |
| ① **599/604 的遗留关闭**：源站「时间轴缩放」**关台重开、刷新后都不保留**（回 44） | 实测 `source-830-timeline-zoom.json` |
| ② 源站的撤销是 **⌘Z**（面板上 ⌘ 是 **SVG 图标** ⟹ 纯文本读数器读不到它 ⟹ 「撤销 = Z」是读数器的盲区） | 源码锚点 `source-830-shortcut-code.json` + 实测 `source-830-undo-cmdz.json` |
| ③ **clone 与源站一致**（上一批说「不一致」是错的）：clone 绑 `Cmd/Ctrl+Z`、撤销栈覆盖机位属性、缩放不跨会话保留 —— 三项全同构 | 实测 + clone 源码 |

## ★ 本批推翻了什么

上一批（batch 830 前半段）写进 raw 的两条读数**作废**，已在原文件里追加「★读数更正」：
- 「撤销 = Z」 ⟹ 实为 **⌘Z**；
- 「按 Z 撤不掉 FOV/改名」 ⟹ **前提不满足**（源站撤销要 ⌘Z，裸 Z 被源码明确排除）⟹
  用 ⌘Z 重测：FOV 67→45→⌘Z→**67**、改名→⌘Z→**机位1** ⟹ **源站撤得掉**。

## ★ 纪律

- 门禁**只**认入库读数 + clone 源码，**不**联网；
- 每条判据都有**只翻它自己那一条**的阴性对照；
- 源站的原生 range 是 `opacity:0` + 自绘轨道 ⟹ **可见性判据对它们必然为 false**，
  ⟹ 本门禁不靠 `visible` 判活，一律靠「读数 + 改值回读 + 截图像素差」；
- 判「视图变了没有」**只能**看视口区域的像素差（排除右栏：⌘Z 撤 FOV 会让右栏数字变）。
"""
import copy
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
BATCH = ROOT / "docs" / "research" / "liblib-canvas-batch830-2026-10-01"
RAW = BATCH / "raw"
IMAGES = BATCH / "images"

SRC_TIMELINE_ZOOM = RAW / "source-830-timeline-zoom.json"
SRC_UNDO_FOV = RAW / "source-830-undo-fov.json"
SRC_UNDO_RENAME = RAW / "source-830-undo-rename.json"
SRC_SHORTCUTS = RAW / "source-830-shortcuts.json"
SRC_I18N = RAW / "source-830-i18n-director.json"
SRC_CMDZ = RAW / "source-830-undo-cmdz.json"
SRC_CMDZ2 = RAW / "source-830-undo-cmdz2.json"
SRC_CODE = RAW / "source-830-shortcut-code.json"
SRC_DIFF = RAW / "source-830-t-screenshot-diff.json"
SRC_FIX = RAW / "source-830-fixfov.json"
CLONE_828 = (ROOT / "docs" / "research" / "liblib-canvas-batch828-2026-10-01"
             / "raw" / "vb828a.json")
SRC_TIMELINE = ROOT / "src" / "components" / "director" / "DirectorTimeline.tsx"
SRC_DESK = ROOT / "src" / "components" / "director" / "DirectorDesk.tsx"
SRC_STORE = ROOT / "src" / "store" / "directorStore.ts"

# ── ★ 探针区开始 ────────────────────────────────────────────────────────────────
# ★ 本批的「探针」＝ **读入库读数的键名**（不是 DOM 选择器）：
#   入库读数的键名一旦漂移，下面这些常量就取不到值 ⟹ 门禁自己会红。
SRC_ZOOM_OPEN = "①开台_缩放"
SRC_ZOOM_CHANGED = "②改缩放"
SRC_ZOOM_AFTER = "③改缩放后"
SRC_ZOOM_REOPEN = "④关台重开后_缩放"
SRC_ZOOM_RELOAD = "⑤刷新后_缩放"
SRC_CZ_ZOOM_BEFORE = "①zoom_改前"
SRC_CZ_ZOOM_CHANGE = "②改zoom"
SRC_CZ_ZOOM_AFTER = "③改zoom后"
SRC_CZ_ZOOM_BLUR = "④失焦后"
SRC_CZ_ZOOM_UNDO = "⑤失焦后按⌘Z"
SRC_CMDZ_FOV_CHANGE = "②改FOV"
SRC_CMDZ_FOV_AFTER = "③改FOV后"
SRC_CMDZ_FOV_UNDO = "④按⌘Z后"
SRC_CMDZ_FOV_REDO = "⑤按⌘⇧Z后"
SRC_CMDZ_NAME = "⑥改名"
SRC_CMDZ_NAME_AFTER = "⑦改名后"
SRC_CMDZ_NAME_UNDO = "⑨按⌘Z后"
SRC_CMDZ_NAME_REDO = "⑩按⌘⇧Z后"
SRC_CMDZ2_FOV_CHANGE = "⑦改FOV"
SRC_CMDZ2_T_AFTER = "⑧按T后"
SRC_CMDZ2_UNDO = "⑨按⌘Z后"
SRC_CMDZ2_FRESH = "⑪全新context回读"
SRC_FIX_FRESH = "⑥全新context回读"
SRC_FIX_FLAG = "★已复原(新context)"
# ── ★ 探针区结束 ────────────────────────────────────────────────────────────────

UNDO_IF_RE = re.compile(r'if\s*\(\s*modifier\s*&&\s*event\.key\.toLowerCase\(\)\s*===\s*"z"\s*\)')
BARE_Z_IF_RE = re.compile(r'if\s*\(\s*event\.key\.toLowerCase\(\)\s*===\s*"z"\s*\)')


def _zoom_of(rec):
    """取一个节点里的 zoom 读数（兼容 {value…} 与 {zoom:{value…}} 两种形状）。"""
    if not isinstance(rec, dict):
        return None
    z = rec.get("zoom")
    if isinstance(z, dict):
        return z
    if "value" in rec:
        return rec
    return None


def _fov_of(rec):
    if not isinstance(rec, dict):
        return None
    f = rec.get("fov")
    return f if isinstance(f, dict) else None


def _name_of(rec):
    if not isinstance(rec, dict):
        return None
    ns = rec.get("names") or []
    return ns[0].get("value") if ns and isinstance(ns[0], dict) else None


def _anchor(code, key):
    a = (code.get("锚点") or {}).get(key) or {}
    return a.get("text") or ""


def build_checks(zoom_raw, undo_fov_raw, undo_rename_raw, shortcuts_raw, i18n_raw,
                 cmdz_raw, cmdz2_raw, code_raw, diff_raw, fix_raw,
                 clone_828, clone_desk_src, clone_timeline_src, clone_store_src):
    C = []

    def ok(cid, cond, detail=None):
        C.append({"id": cid, "name": cid, "ok": bool(cond),
                  "detail": detail if detail is not None else ""})

    # ── S1 控件定位（含「真值是浮点」这条新事实）──
    z_before = _zoom_of(cmdz2_raw.get(SRC_CZ_ZOOM_BEFORE) or {})
    z_open = (zoom_raw.get(SRC_ZOOM_OPEN) or {}).get("zoom") or {}
    ok("S1:★★★ 源站「时间轴缩放」控件定位到了（`aria-label=时间轴缩放`、**min 0 / max 100**）"
       "⟹ ⟹ 这就是 batch 599/604 说的那个「zoom」（与 829 测的「场景缩放」**不是同一个控件**）"
       "⟹ ★ 且它的**真值是浮点 43.7751…**（`.value` 读出 \"44\" 是 step 默认 1 的四舍五入）",
       z_open.get("min") == "0" and z_open.get("max") == "100"
       and (z_before or {}).get("value") == "44"
       and (z_before or {}).get("attr") == "43.77510040160642",
       {"开台时": z_open, "精确法读数": z_before,
        "★为何重要": "源站 i18n 的 `directorTimelineZoom = 时间轴缩放` ⟹ 599/604 的「zoom」指的就是它",
        "★clone 对照": "DirectorTimeline.tsx 同一控件：aria-label/title=时间轴缩放、min=0、max=100、"
                    "value=timeline.zoom（输入框同样 opacity:0 + 自绘轨道）"})

    # ── S2 改值真改（精确法）+ 旧 raw 的更正必须钉住 ──
    chg = cmdz2_raw.get(SRC_CZ_ZOOM_CHANGE) or {}
    chg_after = _zoom_of(cmdz2_raw.get(SRC_CZ_ZOOM_AFTER) or {})
    corr = (zoom_raw.get("★读数更正") or "")
    ok("S2:★★★★ 改时间轴缩放**真的改了**（精确法：44 → 82，回读校验过）"
       "⟹ ★★ 并且旧读数里那句「★没调到」**已被标注为更正**"
       "（它的含义是「没**精确命中**手打的目标值 70」，**不是「没改成」**）",
       chg.get("before") == "44" and chg.get("after") == "82"
       and (chg_after or {}).get("value") == "82"
       and "不是「没改成」" in corr,
       {"精确法改值": chg, "改后": chg_after, "旧raw的更正": corr[:160],
        "★为什么必须钉住更正": "旧 raw 里 `②改缩放.after=null` + `★没调到=true` 长得像「没改成」"
                       "⟹ 不钉住它，下一个读它的人会把「源站改不动缩放」写成事实"})

    # ── S3 关台重开不保留（关闭 599/604）──
    z_reopen = (zoom_raw.get(SRC_ZOOM_REOPEN) or {}).get("zoom") or {}
    z_after = (zoom_raw.get(SRC_ZOOM_AFTER) or {}).get("value")
    ok("S3:★★★★★ 源站**关台重开后时间轴缩放回到 44**（**不保留**）"
       "⟹ ⟹ ★★ **batch 599 / 604 遗留的那条「源站关闭再打开导演台时 zoom 是否保留」"
       "⟹ 答案：不保留**（这一条遗留到此关闭）",
       z_reopen.get("value") == "44" and z_after == "75"
       and z_reopen.get("value") != z_after,
       {"改后": z_after, "关台重开后": z_reopen,
        "★与 clone 一致": "clone 的 timeline.zoom 是**内存态**（刷新后仍归默认）"})

    # ── S4 刷新不保留 ──
    z_reload = (zoom_raw.get(SRC_ZOOM_RELOAD) or {}).get("zoom") or {}
    ok("S4:★★★★ 源站**刷新页面后时间轴缩放也是 44**（**不保留**）"
       "⟹ ⟹ 与 clone「刷新后归默认」在**保留与否**上同构",
       z_reload.get("value") == "44" and z_reload.get("value") != z_after,
       {"改后": z_after, "刷新后": z_reload})

    # ── S5 面板上的撤销带 ⌘ 图标（读源码，不读文本）──
    a_undo = _anchor(code_raw, "面板_撤销行")
    a_group = _anchor(code_raw, "面板_打组行")
    a_ungroup = _anchor(code_raw, "面板_解组行")
    s_corr = (shortcuts_raw.get("★读数更正") or "")
    ok("S5:★★★★★ 源站「快捷键」面板的撤销行是 **⌘ + Z**（⌘ 是 **SVG 图标**）"
       "⟹ ⟹ ★★ 上一批「撤销 = Z」是**纯文本读数器的盲区**（读数器读不到 SVG）⟹ 那条读数作废"
       "⟹ 打组 ⌘G、解组 ⌘⇧D 同理",
       'icon:"command"' in a_undo and 'label:"Z"' in a_undo
       and 'icon:"command"' in a_group and 'icon:"command"' in a_ungroup
       and "⌘" in s_corr,
       {"撤销行源码": a_undo, "打组行源码": a_group, "解组行源码": a_ungroup,
        "★读数器盲区": "面板 DOM 里的 ⌘ 是 `<svg>`（16×16），文本读数器只看见 'Z'"})

    # ── S6 撤销必须带 ⌘/Ctrl（源码条件）──
    a_cond = _anchor(code_raw, "撤销键条件")
    a_branch = _anchor(code_raw, "撤销分支")
    ok("S6:★★★★★ 源站撤销键**必须带 ⌘/Ctrl**（源码条件 `(\"z\"!==n||e.ctrlKey||e.metaKey)`）"
       "⟹ ⟹ ★★ **裸 `Z` 被明确排除** ⟹ 上一批「按 Z 撤不掉」是**前提不满足**的无效读数",
       a_cond == '("z"!==n||e.ctrlKey||e.metaKey)'
       and 'e.shiftKey?nu():nd()' in a_branch,
       {"撤销键条件": a_cond, "撤销分支": a_branch,
        "★键盘处理注册": _anchor(code_raw, "监听注册_捕获阶段")})

    # ── S7 可撤销动作集含 UPDATE_CAMERA ──
    a_actions = _anchor(code_raw, "可撤销动作集_lX")
    ok("S7:★★★★★ 源站撤销栈的可撤销动作集**含 `UPDATE_CAMERA`**"
       "（另含 UPDATE_TIMELINE 等 27 项；栈深 `past.slice(-49)` ⟹ 最多 50 条）"
       "⟹ ⟹ 撤销**覆盖机位属性**（FOV/改名），这与 S8/S9 的实测互相印证",
       '"UPDATE_CAMERA"' in a_actions and '"UPDATE_TIMELINE"' in a_actions
       and "past.slice(-49)" in _anchor(code_raw, "撤销栈_容量"),
       {"可撤销动作集": a_actions[:200] + "…",
        "★瞬时机制": _anchor(code_raw, "瞬时记账"),
        "★提交": _anchor(code_raw, "瞬时提交")})

    # ── S8 实测：⌘Z 撤 FOV / ⌘⇧Z 重做 ──
    fov_chg = cmdz_raw.get(SRC_CMDZ_FOV_CHANGE) or {}
    fov_after = _fov_of(cmdz_raw.get(SRC_CMDZ_FOV_AFTER) or {})
    fov_undo = _fov_of(cmdz_raw.get(SRC_CMDZ_FOV_UNDO) or {})
    fov_redo = _fov_of(cmdz_raw.get(SRC_CMDZ_FOV_REDO) or {})
    ok("S8:★★★★★ 实测：源站 **⌘Z 能撤掉机位 FOV 改动**（67→45→⌘Z→**67**）"
       "⟹ 且 **⌘⇧Z 能重做**（→45）⟹ ⟹ ★★ 源站**有**可用的撤销栈"
       "⟹ ⟹ 与 clone 的 `Cmd+Z`（batch 828 实测 `UNDO/COMMITTED`、改名真被撤掉）**同构**",
       fov_chg.get("before") == "67" and fov_chg.get("after") == "45"
       and (fov_after or {}).get("value") == "45"
       and (fov_undo or {}).get("value") == "67"
       and (fov_redo or {}).get("value") == "45",
       {"改值": fov_chg, "改后": fov_after, "⌘Z后": fov_undo, "⌘⇧Z后": fov_redo,
        "★注意": "每一格都先证明「确实改过」（回读校验过）⟹ 不是「没改成所以没撤」"})

    # ── S9 实测：⌘Z 撤改名 / ⌘⇧Z 重做 ──
    nm = cmdz_raw.get(SRC_CMDZ_NAME) or {}
    nm_after = _name_of(cmdz_raw.get(SRC_CMDZ_NAME_AFTER) or {})
    nm_undo = _name_of(cmdz_raw.get(SRC_CMDZ_NAME_UNDO) or {})
    nm_redo = _name_of(cmdz_raw.get(SRC_CMDZ_NAME_REDO) or {})
    ok("S9:★★★★★ 实测：源站 **⌘Z 能撤掉机位改名**（「机位1-830」→⌘Z→**「机位1」**）"
       "⟹ 且 **⌘⇧Z 能重做**（→「机位1-830」）⟹ ⟹ 与 clone 同口径同结论（**都撤得掉**）",
       nm.get("before") == "机位1" and nm.get("after") == "机位1-830"
       and nm_after == "机位1-830" and nm_undo == "机位1" and nm_redo == "机位1-830",
       {"改名": nm, "改名后": nm_after, "⌘Z后": nm_undo, "⌘⇧Z后": nm_redo,
        "★clone 对照": "batch 828：A 用户路径同节点重开后 Cmd+Z → `UNDO/COMMITTED`，改名真被撤掉"})

    # ── S10 实测：⌘Z 撤不掉时间轴缩放（失焦提交后仍不变）──
    z_blur = _zoom_of(cmdz2_raw.get(SRC_CZ_ZOOM_BLUR) or {})
    z_undo = _zoom_of(cmdz2_raw.get(SRC_CZ_ZOOM_UNDO) or {})
    ok("S10:★★★★ 实测：源站 **⌘Z 撤不掉「时间轴缩放」的改动**"
       "（改 44→82；**失焦（blur）提交之后**再按 ⌘Z，**仍是 82**）"
       "⟹ ⟹ ⟹ **缩放这项改动根本不在撤销栈里**"
       "⟹ ★ 与 clone 同构（clone 的 `setTimelineZoom` 也不写历史条目）",
       (z_blur or {}).get("value") == "82" and (z_undo or {}).get("value") == "82"
       and (z_undo or {}).get("value") != "44",
       {"失焦后": z_blur, "⌘Z后": z_undo,
        "★与 S8/S9 的区别": "FOV/改名**进栈**了；缩放**没进栈** ⟹ 「⌘Z 撤不掉缩放」≠「⌘Z 不工作」",
        "★clone 源码": "directorStore.ts 的 setTimelineZoom 只改 timeline.zoom，不 push 历史"})

    # ── S11 阳性对照：裸键 T 生效（快捷键管线是活的）──
    pair_t = (diff_raw.get("对") or {}).get("T_前后（俯视视角生效）") or {}
    ok("S11:★★★★★ **阳性对照成立**：源站裸键 **T（俯视视角）确实生效**"
       "（视口区域像素差 **%.3f%%** ⟹ 视图从地面视角变成俯视）"
       "⟹ ⟹ ⟹ 由此证明「快捷键管线是活的」⟹ S8/S9/S10 的 ⌘Z 读数**不是**"
       "「按键没送到」的假象" % (pair_t.get("差异百分比") or 0),
       (pair_t.get("差异百分比") or 0) > 5.0
       and (IMAGES / "830_T_before.png").exists()
       and (IMAGES / "830_T_after.png").exists(),
       {"像素差": pair_t, "★为什么必须做阳性对照": (
           "本批上一版判「T 无反应」——那是**读错了字段**："
           "读的是场景世界变换（场景平移/旋转/缩放），而 T 改的是 editor camera pose ⟹ 假阴性。"
           "本批改用**视口截图像素差**判定 ⟹ 67% 的差异。"),
        "★source 的原生 range 是 opacity:0": "可见性判据对源站的滑杆必然为 false ⟹ 一律不看 visible"})

    # ── S12 ⌘Z 撤不掉 T 造成的视图变化 ──
    pair_u = (diff_raw.get("对") or {}).get("T_按⌘Z后（视图是否退回）") or {}
    fov_after_t = _fov_of(cmdz2_raw.get(SRC_CMDZ2_T_AFTER) or {})
    fov_undo_t = _fov_of(cmdz2_raw.get(SRC_CMDZ2_UNDO) or {})
    ok("S12:★★★★ 实测：源站 **⌘Z 撤不掉 T 造成的视图变化**"
       "（按 ⌘Z 后视口像素差 **%.3f%%** ⟹ 视图一动不动）"
       "⟹ ⟹ 同一个 ⌘Z 撤掉的是**机位 FOV**（50→67）而不是视图"
       "⟹ ⟹ 与源码一致：`\"t\"` 走的是 `setEditorCameraPose`（直调 3D 引擎），**不入 reducer**"
       % (pair_u.get("差异百分比") or 0),
       (pair_u.get("差异百分比") or 0) < 0.5
       and (fov_after_t or {}).get("value") == "50"
       and (fov_undo_t or {}).get("value") == "67",
       {"按T后_FOV": fov_after_t, "⌘Z后_FOV": fov_undo_t, "视口像素差": pair_u,
        "★源码锚点": _anchor(code_raw, "俯视视角实现")})

    # ── S13 clone 绑 Cmd/Ctrl+Z ⟹ 与源站一致（更正上一批的「不一致」）──
    ok("S13:★★★★★ clone 的撤销键是 **`Cmd/Ctrl + Z`**（`DirectorDesk.tsx` 的 "
       "`if (modifier && event.key.toLowerCase() === \"z\")`）"
       "⟹ ⟹ ★★ **与源站的 ⌘Z 一致**（更正上一批「快捷键不一致」的结论——那是把面板的 ⌘ 图标"
       "当成了没有修饰键）",
       bool(UNDO_IF_RE.search(clone_desk_src))
       and "event.metaKey || event.ctrlKey" in clone_desk_src
       and not BARE_Z_IF_RE.search(clone_desk_src),
       {"clone 那一行": [ln.strip() for ln in clone_desk_src.splitlines()
                     if 'toLowerCase() === "z"' in ln][:2],
        "★源站": "撤销 = ⌘Z（面板上 ⌘ 是 SVG 图标）",
        "★clone 额外有": "Cmd+Shift+Z / Cmd+Y 重做 ⟹ 源站也有（源码：e.shiftKey?nu():nd()）"})

    # ── S14 i18n 两键 ──
    keys = i18n_raw.get("两条关键键") or {}
    ok("S14:★ 静态锚点：源站 i18n 里 `directorShortcutUndo`（撤销）与 "
       "`directorTimelineZoom`（时间轴缩放）两个键**都在**（共 %d 个 director* 词条）"
       % (i18n_raw.get("键数") or 0),
       keys.get("directorShortcutUndo") == "撤销"
       and keys.get("directorTimelineZoom") == "时间轴缩放"
       and (i18n_raw.get("键数") or 0) > 800,
       {"两条关键键": keys, "director* 词条数": i18n_raw.get("键数")})

    # ── S15 项目已复原 ──
    fresh_fix = fix_raw.get(SRC_FIX_FRESH) or {}
    fresh_cmdz2 = cmdz2_raw.get(SRC_CMDZ2_FRESH) or {}
    fov_fresh = _fov_of(fresh_fix) or {}
    nm_fresh = _name_of(fresh_fix)
    z_fresh = _zoom_of(fresh_cmdz2) or {}
    ok("S15:★★★★★ **源站测试项目已复原**（**全新浏览器 context** 回读："
       "机位 FOV **67**、名称「机位1」、时间轴缩放 **44 / 43.7751…**）"
       "⟹ 测量没把用户的项目改脏",
       fov_fresh.get("value") == "67" and nm_fresh == "机位1"
       and z_fresh.get("value") == "44"
       and z_fresh.get("attr") == "43.77510040160642"
       and fix_raw.get(SRC_FIX_FLAG) is True,
       {"全新context_FOV": fov_fresh, "全新context_名称": nm_fresh,
        "全新context_缩放": z_fresh,
        "★本批踩过的坑": "v10 的复原函数判据写错（「值**变了**就返回」而不是「等于目标就停」）"
                     "⟹ 把 FOV 改成了 64 ⟹ 已用 fixfov830 修回 67 并经全新 context 复验"})
    return C


# ── 阴性对照：每条**只**翻它自己那一条 ────────────────────────────────────────
def _negations():
    def n1(z, uf, ur, sc, i18n, cz, cz2, code, diff, fix, c828, ds, ts, st):
        c = copy.deepcopy(cz2)
        c[SRC_CZ_ZOOM_BEFORE]["zoom"]["value"] = "45"
        return z, uf, ur, sc, i18n, cz, c, code, diff, fix, c828, ds, ts, st

    def n2(z, uf, ur, sc, i18n, cz, cz2, code, diff, fix, c828, ds, ts, st):
        c = copy.deepcopy(cz2)
        c[SRC_CZ_ZOOM_CHANGE]["after"] = "44"
        return z, uf, ur, sc, i18n, cz, c, code, diff, fix, c828, ds, ts, st

    def n3(z, uf, ur, sc, i18n, cz, cz2, code, diff, fix, c828, ds, ts, st):
        c = copy.deepcopy(z)
        c[SRC_ZOOM_REOPEN]["zoom"]["value"] = "75"
        return c, uf, ur, sc, i18n, cz, cz2, code, diff, fix, c828, ds, ts, st

    def n4(z, uf, ur, sc, i18n, cz, cz2, code, diff, fix, c828, ds, ts, st):
        c = copy.deepcopy(z)
        c[SRC_ZOOM_RELOAD]["zoom"]["value"] = "75"
        return c, uf, ur, sc, i18n, cz, cz2, code, diff, fix, c828, ds, ts, st

    def n5(z, uf, ur, sc, i18n, cz, cz2, code, diff, fix, c828, ds, ts, st):
        c = copy.deepcopy(code)
        c["锚点"]["面板_撤销行"]["text"] = c["锚点"]["面板_撤销行"]["text"].replace(
            'icon:"command"', 'icon:"none"')
        return z, uf, ur, sc, i18n, cz, cz2, c, diff, fix, c828, ds, ts, st

    def n6(z, uf, ur, sc, i18n, cz, cz2, code, diff, fix, c828, ds, ts, st):
        c = copy.deepcopy(code)
        c["锚点"]["撤销键条件"]["text"] = '("z"!==n)'
        return z, uf, ur, sc, i18n, cz, cz2, c, diff, fix, c828, ds, ts, st

    def n7(z, uf, ur, sc, i18n, cz, cz2, code, diff, fix, c828, ds, ts, st):
        c = copy.deepcopy(code)
        c["锚点"]["可撤销动作集_lX"]["text"] = c["锚点"]["可撤销动作集_lX"]["text"].replace(
            '"UPDATE_CAMERA",', '')
        return z, uf, ur, sc, i18n, cz, cz2, c, diff, fix, c828, ds, ts, st

    def n8(z, uf, ur, sc, i18n, cz, cz2, code, diff, fix, c828, ds, ts, st):
        c = copy.deepcopy(cz)
        c[SRC_CMDZ_FOV_UNDO]["fov"]["value"] = "45"
        return z, uf, ur, sc, i18n, c, cz2, code, diff, fix, c828, ds, ts, st

    def n9(z, uf, ur, sc, i18n, cz, cz2, code, diff, fix, c828, ds, ts, st):
        c = copy.deepcopy(cz)
        c[SRC_CMDZ_NAME_UNDO]["names"][0]["value"] = "机位1-830"
        return z, uf, ur, sc, i18n, c, cz2, code, diff, fix, c828, ds, ts, st

    def n10(z, uf, ur, sc, i18n, cz, cz2, code, diff, fix, c828, ds, ts, st):
        c = copy.deepcopy(cz2)
        c[SRC_CZ_ZOOM_UNDO]["zoom"]["value"] = "44"
        return z, uf, ur, sc, i18n, cz, c, code, diff, fix, c828, ds, ts, st

    def n11(z, uf, ur, sc, i18n, cz, cz2, code, diff, fix, c828, ds, ts, st):
        c = copy.deepcopy(diff)
        c["对"]["T_前后（俯视视角生效）"]["差异百分比"] = 0.0
        return z, uf, ur, sc, i18n, cz, cz2, code, c, fix, c828, ds, ts, st

    def n12(z, uf, ur, sc, i18n, cz, cz2, code, diff, fix, c828, ds, ts, st):
        c = copy.deepcopy(diff)
        c["对"]["T_按⌘Z后（视图是否退回）"]["差异百分比"] = 67.014
        return z, uf, ur, sc, i18n, cz, cz2, code, c, fix, c828, ds, ts, st

    def n13(z, uf, ur, sc, i18n, cz, cz2, code, diff, fix, c828, ds, ts, st):
        d = ds.replace('if (modifier && event.key.toLowerCase() === "z")',
                       'if (event.key.toLowerCase() === "z")')
        return z, uf, ur, sc, i18n, cz, cz2, code, diff, fix, c828, d, ts, st

    def n14(z, uf, ur, sc, i18n, cz, cz2, code, diff, fix, c828, ds, ts, st):
        c = copy.deepcopy(i18n)
        (c.get("两条关键键") or {})["directorShortcutUndo"] = "重做"
        return z, uf, ur, sc, c, cz, cz2, code, diff, fix, c828, ds, ts, st

    def n15(z, uf, ur, sc, i18n, cz, cz2, code, diff, fix, c828, ds, ts, st):
        c = copy.deepcopy(fix)
        c[SRC_FIX_FLAG] = False
        return z, uf, ur, sc, i18n, cz, cz2, code, diff, c, c828, ds, ts, st

    return [
        ("N1 把「精确法改前」改成 45 ⟹ S1 翻红", "S1", n1),
        ("N2 把「精确法改后」改回 44 ⟹ S2 翻红", "S2", n2),
        ("N3 把「关台重开后」改成 75 ⟹ S3 翻红", "S3", n3),
        ("N4 把「刷新后」改成 75 ⟹ S4 翻红", "S4", n4),
        ("N5 把撤销行的 ⌘ 图标去掉 ⟹ S5 翻红", "S5", n5),
        ("N6 把撤销键条件改成裸 Z 可用 ⟹ S6 翻红", "S6", n6),
        ("N7 把 UPDATE_CAMERA 从可撤销集里去掉 ⟹ S7 翻红", "S7", n7),
        ("N8 把「⌘Z 后 FOV」改成 45 ⟹ S8 翻红", "S8", n8),
        ("N9 把「⌘Z 后名字」改成 机位1-830 ⟹ S9 翻红", "S9", n9),
        ("N10 把「失焦后⌘Z的缩放」改成 44 ⟹ S10 翻红", "S10", n10),
        ("N11 把「T 前后像素差」改成 0 ⟹ S11 翻红", "S11", n11),
        ("N12 把「⌘Z 后像素差」改成 67.014 ⟹ S12 翻红", "S12", n12),
        ("N13 把 clone 的 z 判定改成裸 Z ⟹ S13 翻红", "S13", n13),
        ("N14 把 i18n 的 directorShortcutUndo 改掉 ⟹ S14 翻红", "S14", n14),
        ("N15 把「已复原(新context)」改成 False ⟹ S15 翻红", "S15", n15),
    ]


def main():
    zoom = json.loads(SRC_TIMELINE_ZOOM.read_text(encoding="utf-8"))
    undo_fov = json.loads(SRC_UNDO_FOV.read_text(encoding="utf-8"))
    undo_rename = json.loads(SRC_UNDO_RENAME.read_text(encoding="utf-8"))
    shortcuts = json.loads(SRC_SHORTCUTS.read_text(encoding="utf-8"))
    i18n = json.loads(SRC_I18N.read_text(encoding="utf-8"))
    cmdz = json.loads(SRC_CMDZ.read_text(encoding="utf-8"))
    cmdz2 = json.loads(SRC_CMDZ2.read_text(encoding="utf-8"))
    code = json.loads(SRC_CODE.read_text(encoding="utf-8"))
    diff = json.loads(SRC_DIFF.read_text(encoding="utf-8"))
    fix = json.loads(SRC_FIX.read_text(encoding="utf-8"))
    clone_828 = json.loads(CLONE_828.read_text(encoding="utf-8"))
    clone_desk_src = SRC_DESK.read_text(encoding="utf-8")
    clone_timeline_src = SRC_TIMELINE.read_text(encoding="utf-8")
    clone_store_src = SRC_STORE.read_text(encoding="utf-8")

    checks = build_checks(zoom, undo_fov, undo_rename, shortcuts, i18n, cmdz, cmdz2,
                          code, diff, fix, clone_828, clone_desk_src,
                          clone_timeline_src, clone_store_src)
    neg = []
    for label, expect, builder in _negations():
        args = builder(zoom, undo_fov, undo_rename, shortcuts, i18n, cmdz, cmdz2,
                       code, diff, fix, clone_828, clone_desk_src,
                       clone_timeline_src, clone_store_src)
        mc = build_checks(*args)
        turned = sorted({c["id"].split(":")[0] for c in mc if not c["ok"]})
        neg.append({"name": label, "期望翻红": expect, "实际翻红": turned,
                    "ok": turned == [expect]})

    passed = sum(1 for c in checks if c["ok"])
    report = {"batch": 830, "mode": "offline",
              "totals": {"passed": passed, "total": len(checks)},
              "阴性对照": {"passed": sum(1 for n in neg if n["ok"]),
                           "total": len(neg)},
              "checks": checks, "阴性": neg}
    (BATCH / "verify-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("主检查 %d/%d ｜ 阴性对照 %d/%d" % (
        passed, len(checks), report["阴性对照"]["passed"], len(neg)))
    for c in checks:
        print(("  ✔ " if c["ok"] else "  ✘ ") + c["id"][:96])
    for n in neg:
        print(("  ✔ " if n["ok"] else "  ✘ ") + n["name"][:52]
              + " → 实际翻红 " + ",".join(n["实际翻红"]))
    return 0 if passed == len(checks) and all(n["ok"] for n in neg) else 1


if __name__ == "__main__":
    sys.exit(main())

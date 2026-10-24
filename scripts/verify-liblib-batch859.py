#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 859 门禁：「全景图」「选择画幅比例」**左侧面板模式**（源站逐字 ＋ 源站实测）。

## ★ 本批整改的是 batch 858 登记的 D8

源站逐字（源站 chunk，`aU` 组件）：
    `e?null:(0,i.jsxs)("div",{className:"flex w-[232px] min-w-0 flex-col
       bg-[#171717]",children:["scene"===z?n:null,"character"===z?(…),
       "camera"===z?(…),"panorama"===z?(…),"aspect"===z?(…)]})`
⟹ ⟹ 左侧那个 232px 的面板是**五模式互斥容器**
⟹ ⟹ **「全景图」「选择画幅比例」也是面板模式**，不是 rail 上的浮层。

clone 此前把这两个做成 **portal 浮层**（`data-director-panorama-flyout` /
`data-director-aspect-flyout`）⟹ ⟹ 与源站逐字不符 ⟹ ⟹ 本批改成面板。

## ★ 期望值的出处（**不是** clone 自己算的）

| 期望 | 出处 |
| --- | --- |
| 全景图：面板 @(48,52) 232 宽、标题条 232×48/12px、容器 `px-2` @(48,100) 232×96 | **源站实测**（`raw/source-859-panels.json` 的 `④全景图面板`） |
| 全景图：三行 @(56,100)/(56,132)/(56,164) 各 **216×32**、字号 **13px**、行高 **20px**、图标 **14×14** | 同上 |
| 全景图：三行文本逐字「本地上传」「历史记录」「AI生成」 | 同上 |
| 画幅比例：面板 @(48,52) 232 宽、标题条 232×48/12px | **源站实测**（`⑤画幅比例面板`） |
| 画幅比例：网格 @(48,100) 232×324、列 `104px 104px`、gap **8px**、padding `0px 8px 12px` | 同上 |
| 画幅比例：七格各 **104×72**、字号 **12px**、圆角 **12px**、边框 **1px**（选中 0.85／未选 0.1） | 同上 |
| 标题条类 `aO`、行类 `eu`、网格类、格子类 | **源站 chunk 逐字** |

## ★ 输出
  docs/research/liblib-canvas-batch859-2026-10-01/runtime-audit.json
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs/research/liblib-canvas-batch859-2026-10-01"
RAW = OUT_DIR / "raw"
BASE = "http://localhost:4317"

SRC_PANORAMA = ROOT / "src/components/director/DirectorPanoramaPanel.tsx"
SRC_ASPECT = ROOT / "src/components/director/DirectorAspectPanel.tsx"
SRC_RAIL = ROOT / "src/components/director/DirectorIconRail.tsx"
SRC_DESK = ROOT / "src/components/director/DirectorDesk.tsx"

# ── 源站实测的期望值（出处见上表） ────────────────────────────────
SOURCE_PANORAMA = {
    "panel": {"x": 48, "y": 52, "w": 232, "h": 1028},
    "title": {"x": 48, "y": 52, "w": 232, "h": 48},
    "title_font": "12px",
    "title_text": "全景图",
    "list": {"x": 48, "y": 100, "w": 232, "h": 96},
    "list_padding": "0px 8px",
    "rows": [
        {"text": "本地上传", "x": 56, "y": 100, "w": 216, "h": 32},
        {"text": "历史记录", "x": 56, "y": 132, "w": 216, "h": 32},
        {"text": "AI生成", "x": 56, "y": 164, "w": 216, "h": 32},
    ],
    "row_font": "13px",
    "row_line_height": "20px",
    "icon": {"w": 14, "h": 14},
}

SOURCE_ASPECT = {
    "panel": {"x": 48, "y": 52, "w": 232, "h": 1028},
    "title": {"x": 48, "y": 52, "w": 232, "h": 48},
    "title_font": "12px",
    "title_text": "选择画幅比例",
    "grid": {"x": 48, "y": 100, "w": 232, "h": 324},
    "columns": "104px 104px",
    "gap": "8px",
    "padding": "0px 8px 12px",
    "cells": [
        {"text": "自适应", "x": 56, "y": 100, "w": 104, "h": 72},
        {"text": "21:9", "x": 168, "y": 100, "w": 104, "h": 72},
        {"text": "16:9", "x": 56, "y": 180, "w": 104, "h": 72},
        {"text": "4:3", "x": 168, "y": 180, "w": 104, "h": 72},
        {"text": "1:1", "x": 56, "y": 260, "w": 104, "h": 72},
        {"text": "3:4", "x": 168, "y": 260, "w": 104, "h": 72},
        {"text": "9:16", "x": 56, "y": 340, "w": 104, "h": 72},
    ],
    "cell_font": "12px",
    "cell_radius": "12px",
    "cell_border_width": "1px",
}

# ★ 源站逐字的类名（chunk 提取）
TITLE_CLASS = ("flex h-12 shrink-0 items-center px-3 text-[12px] leading-5 "
               "text-white/90")
ROW_CLASS = ("flex h-8 w-full items-center gap-2 rounded-lg px-2 text-left "
             "text-[13px] leading-5 text-white/88 transition-colors "
             "hover:bg-white/8 disabled:cursor-not-allowed disabled:opacity-45")
GRID_CLASS = "grid grid-cols-2 gap-2 px-2 pb-3"
CELL_CLASS = ("hover:bg-white/8 flex h-[72px] flex-col items-center "
              "justify-center gap-2 rounded-xl border text-[12px] text-white/90 "
              "transition-colors disabled:cursor-not-allowed disabled:opacity-35")

# ★ 本批引入/用到的 Tailwind 类名 ⟹ ⟹ 必须**真的**在构建产物 CSS 里
#   （4317 的 Tailwind 扫描是冻结的 ⟹ ⟹ 新类名可能**静默无样式**）。
NEW_CLASSES = [
    "border-white/85", "border-white/10", "border-white/90",
    "hover:bg-white/8", "disabled:opacity-35", "grid-cols-2",
    "h-[72px]", "h-[11px]", "h-[14px]", "h-[7px]", "h-[9px]",
    "w-[14px]", "w-4", "w-2", "text-[12px]", "text-[13px]",
    "text-white/88", "text-white/90", "leading-5", "pb-3", "px-2",
    "rounded-xl", "rounded-lg", "rounded-sm", "shrink-0", "truncate",
    "transition-colors", "hover:bg-white/8",
]

READ = r"""()=>{
  const rect=(e)=>{ if(!e) return null; const r=e.getBoundingClientRect();
    return {x:Math.round(r.x), y:Math.round(r.y), w:Math.round(r.width),
            h:Math.round(r.height), right:Math.round(r.right),
            bottom:Math.round(r.bottom)}; };
  const q=(s)=>document.querySelector(s);
  const pano=q('[data-director-panorama-panel]');
  const asp=q('[data-director-aspect-panel]');
  const tree=q('[data-director-tree]');
  const vis=(e)=>{ if(!e) return false; const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0; };
  const railBtn=(id)=>{ const e=q("[data-director-rail-entry='"+id+"']");
    return e?{pressed:e.getAttribute('aria-pressed')}:null; };
  const inDom=(sel)=>document.querySelectorAll(sel).length;
  return {
    模式: (q('[data-director-left-panel-view]')||{getAttribute:()=>null})
            .getAttribute('data-director-left-panel-view'),
    场景树在场: Boolean(tree && vis(tree)),
    旧浮层_全景图: inDom('[data-director-panorama-flyout]'),
    旧浮层_画幅比例: inDom('[data-director-aspect-flyout]'),
    五模式在DOM: {
      character: inDom('[data-director-character-panel]'),
      camera: inDom('[data-director-camera-preset-panel]'),
      panorama: inDom('[data-director-panorama-panel]'),
      aspect: inDom('[data-director-aspect-panel]'),
    },
    rail: {
      scene: railBtn('scene'), addCharacter: railBtn('add-character'),
      addCamera: railBtn('add-camera'), panorama: railBtn('panorama'),
      aspectRatio: railBtn('aspect-ratio'),
    },
    全景图: pano ? {
      面板: rect(pano),
      在aside里: pano.closest('aside')!==null,
      标题条: rect(pano.querySelector('[data-director-panel-title="panorama"]')),
      标题文本: (pano.querySelector('[data-director-panel-title="panorama"]')||{}).innerText,
      标题字号: pano.querySelector('[data-director-panel-title="panorama"]')
        ? getComputedStyle(pano.querySelector('[data-director-panel-title="panorama"]')).fontSize : null,
      容器: rect(pano.querySelector('[data-director-panorama-list]')),
      容器内边距: pano.querySelector('[data-director-panorama-list]')
        ? getComputedStyle(pano.querySelector('[data-director-panorama-list]')).padding : null,
      行: [...pano.querySelectorAll('[data-director-panorama-option]')].map(e=>{
        const r=e.getBoundingClientRect();
        const cs=getComputedStyle(e);
        const svg=e.querySelector('svg');
        const svr=svg?svg.getBoundingClientRect():null;
        return {text:(e.textContent||'').replace(/\s+/g,' ').trim(),
                x:Math.round(r.x), y:Math.round(r.y),
                w:Math.round(r.width), h:Math.round(r.height),
                fontSize:cs.fontSize, lineHeight:cs.lineHeight,
                icon: svr?{w:Math.round(svr.width),h:Math.round(svr.height)}:null};
      }),
    } : null,
    画幅比例: asp ? {
      面板: rect(asp),
      在aside里: asp.closest('aside')!==null,
      标题条: rect(asp.querySelector('[data-director-panel-title="aspect"]')),
      标题文本: (asp.querySelector('[data-director-panel-title="aspect"]')||{}).innerText,
      标题字号: asp.querySelector('[data-director-panel-title="aspect"]')
        ? getComputedStyle(asp.querySelector('[data-director-panel-title="aspect"]')).fontSize : null,
      网格: rect(asp.querySelector('[data-director-aspect-grid]')),
      网格列: (()=>{const g=asp.querySelector('[data-director-aspect-grid]');
        return g?getComputedStyle(g).gridTemplateColumns:null;})(),
      网格列间距: (()=>{const g=asp.querySelector('[data-director-aspect-grid]');
        return g?getComputedStyle(g).columnGap:null;})(),
      网格内边距: (()=>{const g=asp.querySelector('[data-director-aspect-grid]');
        return g?getComputedStyle(g).padding:null;})(),
      格: [...asp.querySelectorAll('[data-director-aspect-option]')].map(e=>{
        const r=e.getBoundingClientRect();
        const cs=getComputedStyle(e);
        const g=e.querySelector('[data-director-aspect-glyph]');
        const gr=g?g.getBoundingClientRect():null;
        return {text:(e.textContent||'').replace(/\s+/g,' ').trim(),
                x:Math.round(r.x), y:Math.round(r.y),
                w:Math.round(r.width), h:Math.round(r.height),
                fontSize:cs.fontSize, borderRadius:cs.borderRadius,
                borderWidth:cs.borderWidth, borderColor:cs.borderColor,
                pressed:e.getAttribute('aria-pressed'),
                glyph: gr?{w:Math.round(gr.width),h:Math.round(gr.height)}:null};
      }),
    } : null,
  };
}"""


class Verifier:
    def __init__(self) -> None:
        self.count = 0
        self.failures: list[str] = []
        self.result: dict[str, Any] = {}

    def check(self, name: str, ok: bool, detail: Any = "") -> None:
        self.count += 1
        if not ok:
            self.failures.append(f"{name}  ⟵ {detail}")


def open_desk(page: Any) -> None:
    page.goto(BASE + "/", wait_until="domcontentloaded")
    page.wait_for_timeout(3000)
    page.evaluate(
        "() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")
    page.wait_for_function("() => Boolean(window.__director_store)", timeout=90_000)
    page.wait_for_timeout(1500)
    node = page.locator(".react-flow__node-script-execution").first
    try:
        node.scroll_into_view_if_needed(timeout=8000)
    except Exception:  # noqa: BLE001
        pass
    page.wait_for_timeout(400)
    try:
        node.hover(timeout=8000)
        page.wait_for_timeout(600)
    except Exception:  # noqa: BLE001
        pass
    page.locator("[data-open-director]").first.click(timeout=15000)
    page.wait_for_timeout(6500)
    page.evaluate(
        "() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")


def strip_comments(src: str) -> str:
    """去掉 `//` 行注释与 `/* */` 块注释 ⟹ ⟹ 让「查死代码」只看代码。

    ★ 为什么要这一步：判据若在**注释**里找到同名符号就会假红
    （★ 本批实测：我在文件里留了一段说明「portalFlyout 已被删除」的注释，
    门禁立刻报「还有 portalFlyout」⟹ ⟹ 那是注释、不是死代码）。
    """
    out = re.sub(r"/\*.*?\*/", " ", src, flags=re.S)
    out = re.sub(r"//[^\n]*", " ", out)
    return out


def extract_alpha(color: str) -> str:
    """从 `getComputedStyle().borderColor` 里取出**透明度**。

    ★ 为什么不用一条正则硬啃：`borderColor` 的**字符串形态**随浏览器而变
    ——本仓实测拿到的是 `oklab(0.999994 0.0000455678 0.0000200868 / 0.85)`
    （Chromium 新版的 oklab 色彩空间）⟹ ⟹ 但同一台机器上也可能是
    `rgba(255, 255, 255, 0.85)` 或 `rgb(255 255 255 / 85%)`。
    ⇒ ⇒ 判定「选中态描边 0.85／未选 0.1」必须**与形态无关**：
      ① 先找**斜杠后的那一段**（`/ 0.85`）；
      ② 斜杠后没有就退回找 `rgba(r, g, b, a)` 的**第 4 个分量**；
      ③ 都没有就找**百分号**形式（`85%` ⟹ 换算成 0.85）。
    ⇒ 提取不到时返回空串 ⟹ ⟹ 判据**红**（而不是默默当成 0 蒙混过去）。
    """
    s = (color or "").strip()
    if not s:
        return ""
    # ① oklab(...)／rgb(...) 的斜杠形式：`/ 0.85`
    m = re.search(r"/\s*([0-9]*\.?[0-9]+)\s*%?\s*\)?\s*$", s)
    if m:
        val = m.group(1)
        return f"{float(val) / 100:.4g}" if "%" in m.group(0) else f"{float(val):.4g}"
    # ② rgba(r, g, b, a) 的第 4 个分量
    m = re.match(r"rgba?\(\s*[^,]+,\s*[^,]+,\s*[^,]+,\s*([0-9]*\.?[0-9]+)\s*\)", s)
    if m:
        return f"{float(m.group(1)):.4g}"
    # ③ 裸数字（极少见）
    m = re.fullmatch(r"([0-9]*\.?[0-9]+)", s)
    if m:
        return f"{float(m.group(1)):.4g}"
    return ""


def rect_eq(got: dict[str, Any], want: dict[str, Any]) -> bool:
    """逐项比**数值**字段。

    ★ 只比两边都是数字的键 ⟹ ⟹ 期望值里混进来的字符串（如 `text`）
      不会被当成 0 去比 ⟹ ⟹ 也不会在这里崩掉。
      ★ 文本**另有**一条具名判据在比（`panel:panorama-row-<文本>` 等）⟹ ⟹
        这里静默跳过字符串**不会**漏判。
    """
    for k, v in want.items():
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            continue
        g = got.get(k)
        if not isinstance(g, (int, float)):
            return False
        if abs(g - v) > 0.6:
            return False
    return True


def main() -> int:
    v = Verifier()
    audit: dict[str, Any] = {"batch": 859,
                             "title": "「全景图」「选择画幅比例」左侧面板模式"}

    # ══ S1 源码契约（静态）══════════════════════════════════════════
    # ★ ★★ **源文件缺失时不许崩** ⟹ ⟹ 要报出**有名字的红条**。
    #   ★ 为什么：受控对照（attrib859）会把源码换回 HEAD ⟹ ⟹ HEAD 里**没有**
    #     这两个**本批新建**的面板文件 ⟹ ⟹ 若这里直接 `read_text` ⟹ ⟹
    #     门禁**抛异常**退出 ⟹ ⟹ 那条「红」是**崩出来的**、不是判据判出来的
    #     ⟹ ⟹ 属于**假牙**（★ batch 858 的教训：崩在读文件上的红是假牙）。
    #   ⇒ 缺失时把源码当**空串**继续走 ⟹ ⟹ 每条静态判据各自报红 ⟹ ⟹
    #     受控对照能看到「哪些判据因为文件没了而红」。
    pano_src = (SRC_PANORAMA.read_text(encoding="utf-8")
                if SRC_PANORAMA.exists() else "")
    asp_src = (SRC_ASPECT.read_text(encoding="utf-8")
               if SRC_ASPECT.exists() else "")
    rail_src = (SRC_RAIL.read_text(encoding="utf-8")
                if SRC_RAIL.exists() else "")
    desk_src = (SRC_DESK.read_text(encoding="utf-8")
                if SRC_DESK.exists() else "")
    v.check("source:both-panel-files-exist",
            SRC_PANORAMA.exists() and SRC_ASPECT.exists(),
            detail={"panorama": SRC_PANORAMA.exists(),
                    "aspect": SRC_ASPECT.exists()})
    norm = lambda s: re.sub(r"\s+", " ", s)
    # ★ ★★ **剥掉注释再比类串**。
    #   ★ 为什么必须剥：两个新面板的**文件头注释里逐字抄了源站类串**
    #     （例：`DirectorAspectPanel.tsx` 第 13–16 行把 `h-[72px] flex-col …`
    #     原样写在注释里）⟹ ⟹ 若拿**整个文件**去 `in` 一个类串，
    #     **注释里的那份拷贝就足以让判据变绿** ⟹ ⟹ 真正被改坏的
    #     **代码**反而测不出来（★ 本批实测：写 M5 变异时发现锚点命中 2 次）。
    #   ⇒ 静态契约判据必须只读**代码**（★ 判据读的东西要与它声称的东西同粒度）。
    pano_code = strip_comments(pano_src)
    asp_code = strip_comments(asp_src)
    rail_code = strip_comments(rail_src)
    desk_code = strip_comments(desk_src)
    v.check("source:panorama-title-class-is-the-source-aO",
            norm(TITLE_CLASS) in norm(pano_code),
            detail=TITLE_CLASS)
    v.check("source:panorama-row-class-is-the-source-eu",
            norm(ROW_CLASS) in norm(pano_code), detail=ROW_CLASS)
    v.check("source:panorama-container-is-px-2",
            '"px-2"' in pano_code and "data-director-panorama-list" in pano_code)
    v.check("source:aspect-grid-class-is-the-source-grid",
            norm(GRID_CLASS) in norm(asp_code), detail=GRID_CLASS)
    v.check("source:aspect-cell-class-is-the-source-cell",
            norm(CELL_CLASS) in norm(asp_code), detail=CELL_CLASS)
    v.check("source:aspect-glyph-table-moved-to-the-panel",
            "ASPECT_GLYPH" in asp_code and "ASPECT_GLYPH" not in rail_code)
    # ★ ★ 查的是**代码**，不是注释 ⟹ ⟹ 先剥掉注释再查。
    #   （★ 第一版直接 grep 整个文件 ⟹ ⟹ 把自己留在文件里的**知识注释**
    #   ——那段「z 陷阱」的说明里就写着 `portalFlyout`／`useFlyoutAnchor`
    #   ——当成了死代码 ⟹ ⟹ 假红。★ 判据读的东西必须与它声称的东西同粒度。）
    v.check("source:rail-has-no-portal-flyout-left",
            "data-director-panorama-flyout" not in rail_code
            and "data-director-aspect-flyout" not in rail_code
            and "portalFlyout" not in rail_code
            and "useFlyoutAnchor" not in rail_code)
    v.check("source:rail-selects-the-panel-mode-by-one-call",
            "onSelectLeftPanelView" in rail_code
            and "onSelectLeftPanelView?.(\"panorama\")" in rail_code
            and "onSelectLeftPanelView?.(\"aspect\")" in rail_code)
    v.check("source:desk-renders-both-mode-panels",
            "DirectorPanoramaPanel" in desk_code and "DirectorAspectPanel" in desk_code)
    v.check("source:desk-panel-view-has-five-modes",
            '"scene" | "character" | "camera" | "panorama" | "aspect"' in desk_code)

    # ══ S2 源站实测产物必须存在（期望值不许凭空写）══════════════════
    src_json = RAW / "source-859-panels.json"
    v.check("source:measurement-exists", src_json.exists(), detail=str(src_json))
    if src_json.exists():
        src = json.loads(src_json.read_text(encoding="utf-8"))
        sp = src.get("④全景图面板", {})
        sa = src.get("⑤画幅比例面板", {})
        v.check("source:panel-measured-232-at-48",
                sp.get("panel", {}).get("w") == 232
                and sp.get("panel", {}).get("x") == 48,
                detail=sp.get("panel"))
        v.check("source:panorama-rows-measured",
                len(sp.get("buttons") or []) == 3,
                detail=len(sp.get("buttons") or []))
        v.check("source:aspect-grid-measured",
                sa.get("grids") and sa["grids"][0]["gridTemplateColumns"]
                == SOURCE_ASPECT["columns"],
                detail=sa.get("grids"))
        v.check("source:scene-tree-is-absent-in-both-modes",
                sp.get("sceneTreePresent") is False
                and sa.get("sceneTreePresent") is False,
                detail={"panorama": sp.get("sceneTreePresent"),
                        "aspect": sa.get("sceneTreePresent")})

    # ══ S3/S4/S5 clone 实测（live DOM）══════════════════════════════
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport={"width": 1920, "height": 1080},
                                    device_scale_factor=1)
            errors: list[str] = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.on("console", lambda m: errors.append(m.text)
                    if m.type == "error" else None)
            open_desk(page)

            # —— 全景图模式 ——
            page.locator("[data-director-rail-entry='panorama']").first.click(
                timeout=15000)
            page.wait_for_timeout(700)
            pano = page.evaluate(READ)
            audit["全景图"] = pano
            v.check("panel:mode-is-panorama", pano.get("模式") == "panorama",
                    detail=pano.get("模式"))
            v.check("panel:scene-tree-is-gone", pano.get("场景树在场") is False,
                    detail=pano.get("场景树在场"))
            v.check("panel:old-flyouts-are-gone",
                    pano.get("旧浮层_全景图") == 0 and pano.get("旧浮层_画幅比例") == 0,
                    detail=[pano.get("旧浮层_全景图"), pano.get("旧浮层_画幅比例")])
            v.check("panel:only-one-mode-in-dom",
                    sum(1 for n in (pano.get("五模式在DOM") or {}).values() if n) == 1,
                    detail=pano.get("五模式在DOM"))
            v.check("panel:rail-entry-is-pressed",
                    (pano.get("rail") or {}).get("panorama", {}).get("pressed")
                    == "true", detail=(pano.get("rail") or {}).get("panorama"))
            P = pano.get("全景图") or {}
            v.check("panel:panorama-rect", rect_eq(P.get("面板") or {},
                                                    SOURCE_PANORAMA["panel"]),
                    detail=P.get("面板"))
            v.check("panel:panorama-is-inside-the-column",
                    bool(P.get("在aside里")), detail=P.get("在aside里"))
            v.check("panel:panorama-title",
                    rect_eq(P.get("标题条") or {}, SOURCE_PANORAMA["title"])
                    and (P.get("标题文本") or "").strip() == SOURCE_PANORAMA["title_text"]
                    and P.get("标题字号") == SOURCE_PANORAMA["title_font"],
                    detail={"box": P.get("标题条"), "text": P.get("标题文本"),
                            "font": P.get("标题字号")})
            v.check("panel:panorama-container",
                    rect_eq(P.get("容器") or {}, SOURCE_PANORAMA["list"])
                    and P.get("容器内边距") == SOURCE_PANORAMA["list_padding"],
                    detail={"box": P.get("容器"), "pad": P.get("容器内边距")})
            rows = P.get("行") or []
            v.check("panel:panorama-three-rows", len(rows) == 3, detail=len(rows))
            for i, want in enumerate(SOURCE_PANORAMA["rows"]):
                got = rows[i] if i < len(rows) else {}
                v.check(f"panel:panorama-row-{want['text']}",
                        got.get("text") == want["text"]
                        and rect_eq(got, want)
                        and got.get("fontSize") == SOURCE_PANORAMA["row_font"]
                        and got.get("lineHeight") == SOURCE_PANORAMA["row_line_height"]
                        and (got.get("icon") or {}).get("w")
                        == SOURCE_PANORAMA["icon"]["w"]
                        and (got.get("icon") or {}).get("h")
                        == SOURCE_PANORAMA["icon"]["h"],
                        detail=got)

            # —— 画幅比例模式 ——
            page.locator("[data-director-rail-entry='aspect-ratio']").first.click(
                timeout=15000)
            page.wait_for_timeout(700)
            asp = page.evaluate(READ)
            audit["画幅比例"] = asp
            v.check("panel:mode-is-aspect", asp.get("模式") == "aspect",
                    detail=asp.get("模式"))
            v.check("panel:scene-tree-is-gone-2", asp.get("场景树在场") is False,
                    detail=asp.get("场景树在场"))
            v.check("panel:only-one-mode-in-dom-2",
                    sum(1 for n in (asp.get("五模式在DOM") or {}).values() if n) == 1,
                    detail=asp.get("五模式在DOM"))
            v.check("panel:rail-entry-is-pressed-2",
                    (asp.get("rail") or {}).get("aspectRatio", {}).get("pressed")
                    == "true", detail=(asp.get("rail") or {}).get("aspectRatio"))
            A = asp.get("画幅比例") or {}
            v.check("panel:aspect-rect", rect_eq(A.get("面板") or {},
                                                  SOURCE_ASPECT["panel"]),
                    detail=A.get("面板"))
            v.check("panel:aspect-is-inside-the-column",
                    bool(A.get("在aside里")), detail=A.get("在aside里"))
            v.check("panel:aspect-title",
                    rect_eq(A.get("标题条") or {}, SOURCE_ASPECT["title"])
                    and (A.get("标题文本") or "").strip() == SOURCE_ASPECT["title_text"]
                    and A.get("标题字号") == SOURCE_ASPECT["title_font"],
                    detail={"box": A.get("标题条"), "text": A.get("标题文本"),
                            "font": A.get("标题字号")})
            v.check("panel:aspect-grid",
                    rect_eq(A.get("网格") or {}, SOURCE_ASPECT["grid"])
                    and A.get("网格列") == SOURCE_ASPECT["columns"]
                    and A.get("网格列间距") == SOURCE_ASPECT["gap"]
                    and A.get("网格内边距") == SOURCE_ASPECT["padding"],
                    detail={"box": A.get("网格"), "cols": A.get("网格列"),
                            "gap": A.get("网格列间距"), "pad": A.get("网格内边距")})
            cells = A.get("格") or []
            v.check("panel:aspect-seven-cells", len(cells) == 7, detail=len(cells))
            for i, want in enumerate(SOURCE_ASPECT["cells"]):
                got = cells[i] if i < len(cells) else {}
                alpha = extract_alpha(got.get("borderColor") or "")
                v.check(f"panel:aspect-cell-{want['text']}",
                        got.get("text") == want["text"]
                        and rect_eq(got, want)
                        and got.get("fontSize") == SOURCE_ASPECT["cell_font"]
                        and got.get("borderRadius") == SOURCE_ASPECT["cell_radius"]
                        and got.get("borderWidth") == SOURCE_ASPECT["cell_border_width"]
                        and (alpha == "0.85" if want["text"] == "自适应"
                             else alpha == "0.1"),
                        detail=got)

            # —— 选中项跨模式保留（面板常驻挂载）——
            page.locator("[data-director-aspect-option='16:9']").first.click(
                timeout=15000)
            page.wait_for_timeout(400)
            page.locator("[data-director-rail-entry='scene']").first.click(
                timeout=15000)
            page.wait_for_timeout(500)
            page.locator("[data-director-rail-entry='aspect-ratio']").first.click(
                timeout=15000)
            page.wait_for_timeout(700)
            back = page.evaluate(READ)
            audit["切走再切回"] = back
            cells2 = (back.get("画幅比例") or {}).get("格") or []
            picked = [c for c in cells2 if c.get("pressed") == "true"]
            v.check("panel:the-selection-survives-a-mode-switch",
                    len(picked) == 1 and picked[0].get("text") == "16:9",
                    detail=[(c.get("text"), c.get("pressed")) for c in cells2])

            v.check("diagnostics:no-page-errors",
                    not [e for e in errors if "TransformControls" not in e],
                    detail=errors[:5])
        finally:
            browser.close()

    # ══ S7 类名可用性（冻结的 Tailwind 扫描）════════════════════════
    checker = ROOT / "scripts/check-tailwind-classes-in-css.py"
    css_missing: list[str] = []
    if checker.exists():
        import subprocess
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False,
                                         encoding="utf-8") as fh:
            fh.write("\n".join(NEW_CLASSES))
            list_path = fh.name
        proc = subprocess.run(
            [sys.executable, str(checker), "--list-from", list_path],
            capture_output=True, text=True, cwd=str(ROOT))
        for line in proc.stdout.splitlines():
            if line.strip().startswith("MISS "):
                css_missing.append(line.strip()[5:].split()[0])
    else:
        css_missing = ["（检查器不存在）"]
    v.check("css:all-new-classes-exist", not css_missing, detail=css_missing)

    v.result = {"判据数": v.count, "失败": v.failures, "audit": audit}
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "runtime-audit.json").write_text(
        json.dumps(v.result, ensure_ascii=False, indent=1, default=str),
        encoding="utf-8")
    print(f"\n{v.count} 判据，{len(v.failures)} 失败")
    for f in v.failures:
        print("  FAILED: " + f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    sys.exit(main())

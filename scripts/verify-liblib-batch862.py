#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 862 门禁：**取景框上的「构图参考线」开关**（源站逐字 ＋ 源站实测）。

## ★ 本批整改的是什么

★ clone 的取景框（batch 860 接上的）**只有一条三分线，没有开关**：
  开关在 clone 自己的**视口底部胶囊**里（`aria-label="开启九宫格辅助线"`）。
★ 源站逐字（chunk 的 `mP` 组件 ＋ 调用点）：

```js
// mP 内部：
a?(0,i.jsx)("button",{type:"button",title:s("canvas:directorAspectFrameOverlay"),
  className:`nodrag nopan nowheel pointer-events-auto absolute z-20 flex h-8 w-8
    items-center justify-center rounded-lg transition-colors
    ${n?"bg-(--btn-secondary-bg) text-btn-primary"
       :"text-white/50 hover:bg-white/10 hover:text-white/80"}`,
  style:{left:u.left+u.width-40, top:u.top+8}, onClick:a,
  children:(0,i.jsx)(d.f,{className:"h-4 w-4 shrink-0","aria-hidden":!0})}),null

// 调用点：
(0,i.jsx)(mP,{aspectRatio:tr, …, showCompositionGrid:ti,
  onToggleCompositionGrid:null!==tr?()=>{…}:void 0})
```

⟹ ⟹ 三条**逐字**结论：
① 开关**长在取景框右上角**（`left = 框左 + 框宽 − 40`、`top = 框上 + 8`）；
② 开关**只在选了具体比例时存在**（`tr===null` ⟹ `a` 是 `undefined` ⟹ 按钮不在场）
   ⟹ ⟹ 与「取景框不在场」是同一个条件；
③ 开关的**开启态**用 `bg-(--btn-secondary-bg) text-btn-primary`
   （clone 无这两个变量 ⟹ 用源站实测值兜底）。

★ 源站运行时实测（`raw/source-862-frame-thirds.json` ＋ `…-style.json`）：
  框 @(329,185) 1262×710 ⟹ 按钮 @(1551,193) 32×32
  （329 + 1262 − 40 = 1551 ✔、185 + 8 = 193 ✔）⟹ ⟹ 位置公式**实测命中**。

## ★ 同口径的颜色对照（★ 两条 raw 必须同口径）

★ 源站把颜色写成 CSS 变量类 ⟹ ⟹ `getComputedStyle` 读回来是 `lab(...)`，
  而 clone 是 `rgba(...)` ⟹ ⟹ **字符串不可能逐字相等**。
⇒ ⇒ 判据比**归一化后的 RGBA**（源站侧用 canvas 画一遍再读像素）。

## ★ 输出
  docs/research/liblib-canvas-batch862-2026-10-01/runtime-audit.json
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs/research/liblib-canvas-batch862-2026-10-01"
RAW = OUT_DIR / "raw"
BASE = "http://localhost:4317"

SRC_VIEW = ROOT / "src/components/director/DirectorViewport.tsx"
SRC_PANEL = ROOT / "src/components/director/DirectorAspectPanel.tsx"
SRC_PLANNER = ROOT / "src/lib/directorDeletePlanner.ts"

RAW_SOURCE_FRAME = RAW / "source-862-frame-thirds.json"
RAW_SOURCE_STYLE = RAW / "source-862-frame-thirds-style.json"
RAW_SOURCE_ICON = RAW / "source-862-frame-thirds-icon.json"

# ★ 源站逐字（七档顺序 ＋ 源站逐字的档名）
RATIOS = ["21:9", "16:9", "4:3", "1:1", "3:4", "9:16"]

# ★ clone 运行时读数（★ 与探针同口径）
# ★ ★ 颜色一律**归一化成 canvas 像素**（源站侧就是这么读的）——
#   ★ 否则 clone 的 `rgba(255,255,255,0.5)`（alpha 0..1）与源站的
#   canvas 像素（alpha 0..255）**不是同一口径** ⟹ ⟹ 第一版判据正是在
#   这里翻车的（0.5 被 `int()` 截成 0 ⟹ ⟹ 三条颜色判据假红）。
READ = r"""()=>{
  const norm=(c)=>{
    const cv=document.createElement('canvas'); cv.width=8; cv.height=8;
    const ctx=cv.getContext('2d');
    ctx.clearRect(0,0,8,8);
    ctx.fillStyle='#000';
    ctx.fillStyle=c;            // ★ 非法值时 fillStyle 保持上一次（'#000'）
    ctx.fillRect(0,0,8,8);
    const d=ctx.getImageData(4,4,1,1).data;
    return {raw:c, rgba:[d[0],d[1],d[2],d[3]]};
  };
  const f=document.querySelector('[data-director-aspect-frame]');
  const btn=document.querySelector('[data-director-frame-thirds-toggle]');
  if(!f) return {框在场:false, 按钮在场:!!btn};
  const r=f.getBoundingClientRect();
  const cs=getComputedStyle(f);
  const out={框在场:true, 按钮在场:!!btn,
             框:{x:Math.round(r.x),y:Math.round(r.y),
                 w:Math.round(r.width),h:Math.round(r.height)},
             描边:{width:cs.outlineWidth,color:norm(cs.outlineColor),
                   offset:cs.outlineOffset,style:cs.outlineStyle},
             borderWidth:cs.borderTopWidth, 圆角:cs.borderRadius};
  if(btn){
    const br=btn.getBoundingClientRect();
    const bcs=getComputedStyle(btn);
    out.按钮={x:Math.round(br.x),y:Math.round(br.y),
              w:Math.round(br.width),h:Math.round(br.height),
              title:btn.title, ariaLabel:btn.getAttribute('aria-label'),
              pressed:btn.getAttribute('aria-pressed'),
              相对左:Math.round(br.x-r.x), 相对上:Math.round(br.y-r.y),
              期望左:Math.round(r.width)-40, 期望上:8,
              颜色:norm(bcs.color), 背景:norm(bcs.backgroundColor),
              pointerEvents:bcs.pointerEvents, position:bcs.position,
              zIndex:bcs.zIndex};
  }
  const thirds=[...document.querySelectorAll('[data-director-thirds] span')].map(s=>{
    const c=getComputedStyle(s); const rc=s.getBoundingClientRect();
    return {bg:norm(c.backgroundColor), w:Math.round(rc.width), h:Math.round(rc.height)};
  });
  out.三分线={条数:thirds.length, 线:thirds};
  return out;
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


def strip_comments(src: str) -> str:
    """去掉 `//` 行注释与 `/* */` 块注释 ⟹ ⟹ 静态判据只读**代码**。

    ★ batch 859 的教训：注释里逐字抄的类串**足以**让判据变绿 ⟹ ⟹ 假绿。
    """
    out = re.sub(r"/\*.*?\*/", " ", src, flags=re.S)
    out = re.sub(r"//[^\n]*", " ", out)
    return out


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


def pick_rgba(entry: Any) -> list[int] | None:
    """从归一化读数里取 RGBA 像素（源站侧与 clone 侧**都**是 canvas 像素 0..255）。"""
    if isinstance(entry, dict) and isinstance(entry.get("rgba"), list):
        return [int(x) for x in entry["rgba"]]
    if isinstance(entry, str):
        nums = re.findall(r"[\d.]+", entry)
        if len(nums) >= 4:
            alpha = float(nums[3])
            # ★ CSS 的 alpha 是 0..1，canvas 像素是 0..255 ⟹ ⟹ 换算到同一口径
            return [int(float(nums[0])), int(float(nums[1])), int(float(nums[2])),
                    int(round(alpha * 255)) if alpha <= 1 else int(alpha)]
    return None


def main() -> int:
    v = Verifier()
    audit: dict[str, Any] = {
        "batch": 862,
        "title": "取景框上的构图参考线开关（源站逐字 ＋ 源站实测）",
    }

    # ══ S0 原始读数必须在场 ═════════════════════════════════════
    for path in (RAW_SOURCE_FRAME, RAW_SOURCE_STYLE, RAW_SOURCE_ICON):
        v.check(f"raw:exists-{path.name}", path.exists(), detail=str(path))
    if not (RAW_SOURCE_FRAME.exists() and RAW_SOURCE_STYLE.exists()
            and RAW_SOURCE_ICON.exists()):
        print("缺源站原始读数 ⟹ 判失败，不许通过")
        v.result = {"判据数": v.count, "失败": v.failures, "audit": audit}
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        (OUT_DIR / "runtime-audit.json").write_text(
            json.dumps(v.result, ensure_ascii=False, indent=1, default=str),
            encoding="utf-8")
        return 1

    src_frame = json.loads(RAW_SOURCE_FRAME.read_text(encoding="utf-8"))
    src_style = json.loads(RAW_SOURCE_STYLE.read_text(encoding="utf-8"))
    src_icon = json.loads(RAW_SOURCE_ICON.read_text(encoding="utf-8"))

    # ══ S1 源码契约（静态、剥注释后比）════════════════════════════
    view_code = strip_comments(SRC_VIEW.read_text(encoding="utf-8"))
    panel_code = strip_comments(SRC_PANEL.read_text(encoding="utf-8"))
    planner_code = strip_comments(SRC_PLANNER.read_text(encoding="utf-8"))

    v.check("source:frame-has-a-thirds-toggle",
            "data-director-frame-thirds-toggle" in view_code,
            detail="取景框上要有那枚开关的挂载点")
    v.check("source:toggle-is-titled-composition-guides",
            'title="构图参考线"' in view_code
            and 'aria-label="构图参考线"' in view_code,
            detail="★ 源站的 title 是 i18n `canvas:directorAspectFrameOverlay`"
                   " ⟹ ⟹ 源站实测文本 ＝「构图参考线」")
    # ★ 位置公式（源站逐字 `left: u.left + u.width - 40` / `top: u.top + 8`）
    v.check("source:toggle-uses-the-source-position-formula",
            "left: frameWidth - 40" in view_code and "top: 8" in view_code,
            detail="★ 相对框的偏移 ＝ (框宽 − 40, 8)")
    # ★ 关闭态类名逐字（那几个类 clone 已在用 ⟹ 4317 上真的生成）
    v.check("source:toggle-off-class-is-verbatim",
            ("nodrag nopan nowheel pointer-events-auto absolute z-20 flex h-8 w-8 "
             "items-center justify-center rounded-lg transition-colors "
             "text-white/50 hover:bg-white/10 hover:text-white/80") in view_code,
            detail="源站逐字的关闭态类名")
    # ★ 开启态：clone 没有 `--btn-secondary-bg`／`btn-primary` ⟹ ⟹ inline style
    v.check("source:toggle-on-colors-use-the-measured-values",
            '"rgba(255,255,255,0.1)"' in view_code
            and '"rgb(9,202,245)"' in view_code,
            detail="★ 源站实测：开启态 bg ＝ rgba(255,255,255,0.1)、"
                   "前景 ＝ rgb(9,202,245)")
    # ★ 框的描边改成 outline（源站逐字）＋ 圆角 12px
    v.check("source:frame-uses-outline-not-border",
            'outline: "1px solid rgba(255,255,255,0.18)"' in view_code
            and 'outlineOffset: "-1px"' in view_code
            and 'borderRadius: "12px"' in view_code
            and "border-white/75" not in view_code,
            detail="★ 源站逐字：`outline-white/18 … outline -outline-offset-1 rounded-xl`")
    # ★ 三分线颜色（源站逐字 `bg-(--color-white-alpha-50)` ＝ 白 50%）
    v.check("source:thirds-use-the-source-colour",
            view_code.count('"rgba(255,255,255,0.5)"') == 4,
            detail={"出现次数": view_code.count('"rgba(255,255,255,0.5)"'),
                    "why": "★ 源站逐字是 4 条线（2 竖 2 横）"})
    # ★ svg path 必须与**源站原文**逐字相等（★ 期望值来自入库的源站原文）
    src_d = ""
    try:
        paths = (src_icon.get("关态") or {}).get("path") or []
        if paths:
            src_d = re.search(r'd="([^"]+)"', paths[0]).group(1)
    except Exception:  # noqa: BLE001
        src_d = ""
    v.check("source:toggle-icon-path-matches-the-source-verbatim",
            bool(src_d) and src_d in view_code,
            detail={"源站path长度": len(src_d),
                    "why": "★ 图标必须逐字取源站的 path，不能拿近似图形"})
    # ★ 面板的 disabled 契约（源站逐字 `disabled:!a`）
    v.check("source:aspect-panel-keeps-the-source-disabled-contract",
            "disabled={!hasCameras}" in panel_code
            and 'objects.some((object) => object.kind === "camera")' in panel_code,
            detail="★ 源站逐字：`hasCameras: rL.cameras.length > 0` ＋ `disabled:!a`")
    # ★ 「无机位」在 clone 侧**不可达**的依据（⟹ ⟹ 门禁只能是源码判据）
    v.check("source:last-camera-guard-makes-the-disabled-branch-unreachable",
            "DIRECTOR_LAST_CAMERA_REQUIRED" in planner_code,
            detail="★ clone 至少保留一个机位 ⟹ ⟹ `disabled={!hasCameras}` "
                   "在运行时永远不生效 ⟹ ⟹ 只能按源码逐字判")

    # ══ S2 源站运行时读数（期望值的唯一来源）══════════════════════
    s_frame = src_frame.get("选16比9_框") or []
    s_btn = (src_frame.get("选16比9_框上按钮") or {}).get("按钮") or []
    s_toggle = next((b for b in s_btn if b.get("title") == "构图参考线"), None)
    v.check("source:the-toggle-exists-on-the-frame",
            s_toggle is not None,
            detail={"候选": [b.get("title") for b in s_btn]})
    if s_toggle and s_frame:
        s_rect = s_frame[0]["rect"]
        v.check("source:toggle-size-is-32x32",
                s_toggle.get("w") == 32 and s_toggle.get("h") == 32,
                detail={"w": s_toggle.get("w"), "h": s_toggle.get("h")})
        v.check("source:toggle-position-follows-the-source-formula",
                s_toggle.get("x") - s_rect["x"] == s_rect["w"] - 40
                and s_toggle.get("y") - s_rect["y"] == 8,
                detail={"按钮x": s_toggle.get("x"), "框x": s_rect["x"],
                        "框宽": s_rect["w"], "期望按钮x": s_rect["x"] + s_rect["w"] - 40,
                        "按钮y": s_toggle.get("y"), "框y": s_rect["y"]})
    v.check("source:no-frame-and-no-toggle-on-auto",
            not (src_frame.get("自适应_框") or [])
            and not (src_frame.get("自适应_框上按钮") or {}).get("按钮"),
            detail="★ 源站逐字：`onToggleCompositionGrid:null!==tr?…:void 0`")
    v.check("source:clicking-the-toggle-shows-four-thirds",
            (src_frame.get("点开关后_三分线") or {}).get("条数") == 4,
            detail=(src_frame.get("点开关后_三分线") or {}).get("条数"))
    # ★ 归一化颜色（canvas 像素）
    norm = src_style.get("归一化颜色") or {}
    src_line_colours = [pick_rgba(norm.get(f"三分线_{i}")) for i in range(4)]
    src_btn_fg = pick_rgba(norm.get("按钮前景_开态"))
    src_btn_bg = pick_rgba(norm.get("按钮背景_开态"))
    src_outline = pick_rgba(norm.get("框描边"))
    v.check("source:thirds-are-white-at-50-percent",
            all(c is not None and c[0] > 250 and c[1] > 250 and c[2] > 250
                and 120 <= c[3] <= 135 for c in src_line_colours),
            detail=src_line_colours)
    v.check("source:toggle-on-colours-are-the-measured-ones",
            src_btn_fg == [9, 202, 245, 255]
            and src_btn_bg is not None and src_btn_bg[0] > 250
            and 20 <= src_btn_bg[3] <= 32,
            detail={"前景": src_btn_fg, "背景": src_btn_bg})
    v.check("source:frame-outline-is-white-at-18-percent",
            src_outline is not None and src_outline[0] > 250
            and src_outline[1] > 250 and src_outline[2] > 250
            and 40 <= src_outline[3] <= 52,
            detail=src_outline)

    # ══ S3 clone 运行时读数（门禁自己跑）══════════════════════════
    live: dict[str, Any] = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport={"width": 1920, "height": 1080},
                                    device_scale_factor=1)
            errors: list[str] = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            open_desk(page)

            auto = page.evaluate(READ)
            live["自适应"] = auto
            v.check("clone:auto-has-no-frame-and-no-toggle",
                    auto.get("框在场") is False and auto.get("按钮在场") is False,
                    detail=auto)

            page.locator("[data-director-rail-entry='aspect-ratio']").first.click(
                timeout=15000)
            page.wait_for_timeout(900)
            for ratio in RATIOS:
                page.locator(
                    f"[data-director-aspect-option='{ratio}']").first.click(timeout=8000)
                page.wait_for_timeout(700)
                live[ratio] = page.evaluate(READ)
                g = live[ratio]
                btn = g.get("按钮") or {}
                v.check(f"clone:toggle-sits-at-the-frame-corner-for-{ratio}",
                        btn.get("相对左") == btn.get("期望左")
                        and btn.get("相对上") == btn.get("期望上"),
                        detail={"相对": [btn.get("相对左"), btn.get("相对上")],
                                "期望": [btn.get("期望左"), btn.get("期望上")]})
                v.check(f"clone:toggle-is-32x32-for-{ratio}",
                        btn.get("w") == 32 and btn.get("h") == 32,
                        detail={"w": btn.get("w"), "h": btn.get("h")})
                v.check(f"clone:toggle-title-for-{ratio}",
                        btn.get("title") == "构图参考线"
                        and btn.get("ariaLabel") == "构图参考线",
                        detail={"title": btn.get("title"),
                                "aria": btn.get("ariaLabel")})
                v.check(f"clone:frame-outline-for-{ratio}",
                        (g.get("描边") or {}).get("width") == "1px"
                        and (g.get("描边") or {}).get("offset") == "-1px"
                        and g.get("圆角") == "12px"
                        and g.get("borderWidth") == "0px",
                        detail={"描边": g.get("描边"), "圆角": g.get("圆角"),
                                "border": g.get("borderWidth")})

            before = (live.get("16:9") or {}).get("三分线") or {}
            # ★ ★ **先断言那枚开关在（再点它）**——★ 否则在「源码换回 HEAD」的
            #   受控对照里，**元素不存在**会让 `click()` 直接 30s 超时 ⟹ ⟹
            #   门禁报出来的是 **CRASH**（崩溃签名）而不是**具名红条**
            #   ⟹ ⟹ 归因时看不出「是哪条判据不成立」⟹ ⟹ 这里改成：
            #   **先计数、具名判据、再决定要不要点**。
            toggle_count = page.locator(
                "[data-director-frame-thirds-toggle]").count()
            v.check("clone:the-toggle-is-mounted-before-it-is-clicked",
                    toggle_count == 1, detail={"count": toggle_count})
            if toggle_count == 1:
                page.locator("[data-director-frame-thirds-toggle]").first.click(
                    timeout=8000)
                page.wait_for_timeout(800)
            after = page.evaluate(READ)
            live["点开关后"] = after
            v.check("clone:thirds-are-off-before-the-click",
                    before.get("条数") == 0, detail=before)
            v.check("clone:clicking-the-toggle-shows-four-thirds",
                    (after.get("三分线") or {}).get("条数") == 4,
                    detail=(after.get("三分线") or {}).get("条数"))
            # ★ ★ 安全取值：★ 「源码换回 HEAD」时那枚开关**不存在** ⟹ ⟹
            #   分线是**空列表** ⟹ ⟹ 第一版这里写的是 `.get("线", [{}])[i]`
            #   ⟹ ⟹ i=1..3 直接 **IndexError** ⟹ ⟹ 门禁报出来的是 CRASH
            #   ⟹ ⟹ 具名红条根本没机会打印 ⟹ ⟹ 改成**按长度安全取**。
            lines = (after.get("三分线") or {}).get("线") or []
            clone_line_colours = [
                pick_rgba((lines[i] if i < len(lines) else {}).get("bg"))
                for i in range(4)
            ]
            v.check("clone:thirds-are-white-at-50-percent",
                    all(c is not None and c[0] > 250 and c[1] > 250 and c[2] > 250
                        and 120 <= c[3] <= 135 for c in clone_line_colours),
                    detail=clone_line_colours)
            open_btn = after.get("按钮") or {}
            clone_btn_fg = pick_rgba(open_btn.get("颜色"))
            clone_btn_bg = pick_rgba(open_btn.get("背景"))
            v.check("clone:toggle-on-colours-match-the-source",
                    clone_btn_fg == src_btn_fg and clone_btn_bg == src_btn_bg,
                    detail={"clone": [clone_btn_fg, clone_btn_bg],
                            "source": [src_btn_fg, src_btn_bg]})
            v.check("clone:toggle-on-sets-aria-pressed",
                    open_btn.get("pressed") == "true",
                    detail=open_btn.get("pressed"))

            if toggle_count == 1:
                page.locator("[data-director-frame-thirds-toggle]").first.click(
                    timeout=8000)
                page.wait_for_timeout(800)
            again = page.evaluate(READ)
            v.check("clone:clicking-again-hides-the-thirds",
                    (again.get("三分线") or {}).get("条数") == 0,
                    detail=(again.get("三分线") or {}).get("条数"))

            page.locator("[data-director-aspect-option='自适应']").first.click(
                timeout=8000)
            page.wait_for_timeout(700)
            back = page.evaluate(READ)
            live["回自适应"] = back
            v.check("clone:going-back-to-auto-removes-frame-and-toggle",
                    back.get("框在场") is False and back.get("按钮在场") is False,
                    detail=back)

            v.check("diagnostics:no-page-errors",
                    not [e for e in errors if "TransformControls" not in e],
                    detail=errors[:5])
            audit["live"] = live
        finally:
            browser.close()

    # ══ S4 同口径对照（源站 raw vs clone 现场读数）════════════════
    v.check("compare:thirds-colour-is-identical-across-sides",
            [pick_rgba(x) for x in
             [c.get("bg") for c in (live.get("点开关后", {}).get("三分线") or {})
              .get("线", [])]]
            == src_line_colours,
            detail={"clone": clone_line_colours, "source": src_line_colours})
    v.check("compare:toggle-size-is-identical-across-sides",
            (live.get("点开关后", {}).get("按钮") or {}).get("w") == 32
            and (live.get("点开关后", {}).get("按钮") or {}).get("h") == 32,
            detail="源站 32×32")

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

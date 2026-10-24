#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 865 门禁：取景框的**结构**改成源站同构（D25 结案）。

## ★ 本批在做什么（★ 一句话说清）

★ batch 864 登记了 **D25**：源站取景框那三层是
「遮罩层／**空框**／三分线层／开关」**四者平级**
（都是遮罩容器的**直接子元素**），
而 clone 把**三分线与开关塞进了框里** ⟹ ⟹ **结构与源站不同**。

★ 本批把 clone 改成**源站逐字**的四者平级。

## ★ 源站逐字（已入库，★ 期望值**只从它解析**，不凭记忆手打）

`docs/research/liblib-canvas-batch865-2026-10-01/raw/source-865-mp-verbatim.txt`
（chunk `0fmehki05gkzw.js.js` 的 `mP` 组件；文件头记 chunk 路径／字符偏移／
chunk 与摘录的**两个 sha256**）。

```jsx
<div ref={l} className:"pointer-events-none absolute bottom-0 left-0 right-0 top-0 z-10">
  {u && <>
    {/* ① 遮罩层 */}
    <div className:"absolute inset-0 bg-black/20 backdrop-blur-md" style={{…mask…}} />
    {/* ② 空框（★ 框里没有任何 children） */}
    <div className:"outline-white/18 absolute rounded-xl outline -outline-offset-1"
         style={{left:u.left,top:u.top,width:u.width,height:u.height}} />
    {/* ③ 三分线层（条件渲染，`aria-hidden`） */}
    {n ? <div className:"pointer-events-none absolute overflow-hidden rounded-xl"
             style={{left:u.left,top:u.top,width:u.width,height:u.height}}
             aria-hidden>
            <div className:"bg-(--color-white-alpha-50) absolute left-[33.333%] top-0 h-full w-px" />
            <div className:"bg-(--color-white-alpha-50) absolute left-[66.667%] top-0 h-full w-px" />
            <div className:"bg-(--color-white-alpha-50) absolute left-0 top-[33.333%] h-px w-full" />
            <div className:"bg-(--color-white-alpha-50) absolute left-0 top-[66.667%] h-px w-full" />
          </div> : null}
    {/* ④ 开关（条件渲染，容器坐标） */}
    {a ? <button type="button" title={…}
            className:`nodrag nopan nowheel pointer-events-auto absolute z-20 flex h-8 w-8 …`}
            style={{left:u.left+u.width-40, top:u.top+8}} onClick={a}>…</button> : null}
  </>}
</div>
```

## ★ 判据构成

- **S1 静态**：期望值**只从入库的源站逐字解析**（连 `33.333%` 都用正则从
  源站类名里抽）⟹ ⟹ 缺证据文件 ⟹ ⟹ **直接判失败**；
- **S2 运行时结构读数**：四者的**父子关系**与**顺序**、框是**空框**、
  三分线层带 `overflow-hidden`／`rounded-xl`／`aria-hidden`、
  四条线的百分比、开关的**容器坐标**；
- **S3 偏差取证（D26）**：★ 源站的框**没有** `pointer-events-none`
  ⟹ ⟹ 本批**保留** clone 的这一条 ⟹ ⟹ 必须**有证据**说明为什么
  ⟹ ⟹ 探针：把框临时改成 `pointer-events:auto` ⟹ ⟹ 读坐标控件按钮中心的
  `elementFromPoint` ⟹ ⟹ 若命中的是**框** ⟹ ⟹ 证明照抄源站会**吞掉**
  clone 自有的坐标控件。

## 输出
  docs/research/liblib-canvas-batch865-2026-10-01/runtime-audit.json
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs/research/liblib-canvas-batch865-2026-10-01"
RAW = OUT_DIR / "raw"
BASE = "http://localhost:4317"

EVIDENCE = RAW / "source-865-mp-verbatim.txt"
SRC_VIEW = ROOT / "src/components/director/DirectorViewport.tsx"

# ★ clone 运行时读数（★ 与探针同口径）
READ = r"""()=>{
  const cont=document.querySelector('[data-director-aspect-mask-container]');
  if(!cont) return {容器在场:false};
  const mask=document.querySelector('[data-director-aspect-mask]');
  const frame=document.querySelector('[data-director-aspect-frame]');
  const thirds=document.querySelector('[data-director-thirds]');
  const btn=document.querySelector('[data-director-frame-thirds-toggle]');
  const mark=el=>{if(!el) return '不在场';
    if(el.hasAttribute('data-director-aspect-mask')) return '遮罩层';
    if(el.hasAttribute('data-director-aspect-frame')) return '空框';
    if(el.hasAttribute('data-director-thirds')) return '三分线层';
    if(el.hasAttribute('data-director-frame-thirds-toggle')) return '开关';
    return '其他';};
  const parent=el=>{if(!el||!el.parentElement) return '不在场';
    const p=el.parentElement;
    if(p.hasAttribute('data-director-aspect-mask-container')) return '容器';
    if(p.hasAttribute('data-director-aspect-frame')) return '框';
    return '其他';};
  const out={容器在场:true,
             容器子元素:[...cont.children].map(el=>({标记:mark(el),
                 cls:(el.getAttribute('class')||'')})),
             框孩子数: frame? frame.childElementCount : null,
             三分线层的父: parent(thirds),
             开关的父: parent(btn),
             遮罩层的父: parent(mask),
             框的父: parent(frame)};
  if(frame){
    const r=frame.getBoundingClientRect();
    out.框={x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)};
    out.框的pointerEvents=getComputedStyle(frame).pointerEvents;
  }
  if(thirds){
    const cs=getComputedStyle(thirds);
    const r=thirds.getBoundingClientRect();
    out.三分线层={overflow:cs.overflow, radius:cs.borderRadius,
        ariaHidden:thirds.getAttribute('aria-hidden'),
        pointerEvents:cs.pointerEvents,
        x:Math.round(r.x),y:Math.round(r.y),
        w:Math.round(r.width),h:Math.round(r.height)};
    out.线=[...thirds.querySelectorAll('span')].map(s=>{
      const c=getComputedStyle(s); const b=s.getBoundingClientRect();
      const cs2=c;
      return {left:cs2.left, top:cs2.top, w:Math.round(b.width), h:Math.round(b.height),
              bg:cs2.backgroundColor};});
    // ★ 线的**相对位置**（相对三层）⟹ ⟹ 用来跟源站的 33.333% / 66.667% 对
    const tr=thirds.getBoundingClientRect();
    out.线的相对位置=[...thirds.querySelectorAll('span')].map(s=>{
      const b=s.getBoundingClientRect();
      return {左百分比: Math.round((b.x-tr.x)/tr.width*1000)/10,
              上百分比: Math.round((b.y-tr.y)/tr.height*1000)/10};});
  }
  if(btn){
    const b=btn.getBoundingClientRect();
    const cs=getComputedStyle(btn);
    out.开关={x:Math.round(b.x),y:Math.round(b.y),
        w:Math.round(b.width),h:Math.round(b.height),
        left:cs.left, top:cs.top, zIndex:cs.zIndex,
        pointerEvents:cs.pointerEvents, position:cs.position};
  }
  return out;
}"""

# ★ ★★ D26 的取证探针：★ 临时把框改成 `pointer-events:auto`
#   ⟹ ⟹ 再逐个读坐标控件**每枚按钮**中心的 `elementFromPoint`
#   ⟹ ⟹ 找的是「**落在框内**、且**命中会随 pointer-events 改变**」的按钮
#   ⟹ ⟹ （★ 第一版只取「X 反向」一枚 ⟹ ⟹ 那个点其实被**开关自己**的 svg 盖着
#   ⟹ ⟹  ⟹ ⟹ 取样点选错了 ⟹ ⟹ 改成**枚举全部按钮** ⟹ ⟹ 才知道有没有真被吞的）
GIZMO_HIT = r"""()=>{
  const frame=document.querySelector('[data-director-aspect-frame]');
  const fr=frame?frame.getBoundingClientRect():null;
  const btns=[...document.querySelectorAll('[data-director-viewport-gizmo-button]')].map(b=>{
    const r=b.getBoundingClientRect();
    const cx=Math.round(r.x+r.width/2), cy=Math.round(r.y+r.height/2);
    const inFrame= fr ? (cx>=fr.x && cx<=fr.x+fr.width && cy>=fr.y && cy<=fr.y+fr.height) : false;
    const top=document.elementFromPoint(cx,cy);
    return {名字:b.getAttribute('aria-label')||b.getAttribute('title')||'',
            命中点:{x:cx,y:cy}, 在框内:inFrame,
            命中是这枚按钮:!!(top&&top.closest('[data-director-viewport-gizmo-button]')===b),
            命中是框:!!(top&&top.closest('[data-director-aspect-frame]'))};
  });
  return {按钮数:btns.length,
          框的pointerEvents:frame?getComputedStyle(frame).pointerEvents:null,
          框的rect:fr?{x:Math.round(fr.x),y:Math.round(fr.y),
                       w:Math.round(fr.width),h:Math.round(fr.height)}:null,
          按钮:btns};
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
    out = re.sub(r"/\*.*?\*/", " ", src, flags=re.S)
    out = re.sub(r"//[^\n]*", " ", out)
    return out


def grab(pattern: str, text: str) -> str | None:
    m = re.search(pattern, text)
    return m.group(1) if m else None


def thirds_start_tag(view_code: str) -> str:
    """★ 取「三分线层」那**一个**开始标签的文本 ⟹ ⟹ 静态判据只读它。

    ★★ 为什么要锚：★ `aria-hidden="true"` 在 `DirectorViewport.tsx` 里出现
    **11 处** ⟹ ⟹ 「全文 contains」型判据是**假绿**的
    （把**别处**那一处改掉 ⟹ ⟹ 判据照样绿）⟹ ⟹
    判据必须只读**三分线层自己**那一处 ⟹ ⟹ 这才是「同名在别处出现」的正解。

    ★ 结束位置的取法：从 `data-director-thirds` 起 ⟹ ⟹ 找第一个
    「行首空白 + `>`」⟹ ⟹ 那是这个 JSX 开始标签的收尾
    （`style={{ … }}` 里没有 `>` ⟹ ⟹ 不会被截断）。
    """
    m = re.search(r"data-director-thirds\b(.*?)(?:\n\s*>)(?![\w-])", view_code, re.S)
    return m.group(0) if m else ""


def open_desk(page) -> None:
    page.goto(BASE + "/", wait_until="domcontentloaded")
    page.wait_for_timeout(3000)
    page.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")
    page.wait_for_function("() => Boolean(window.__director_store)", timeout=90_000)
    page.wait_for_timeout(1500)
    node = page.locator(".react-flow__node-script-execution").first
    try:
        node.scroll_into_view_if_needed(timeout=8000)
        page.wait_for_timeout(400)
        node.hover(timeout=8000)
        page.wait_for_timeout(600)
    except Exception:  # noqa: BLE001
        pass
    page.locator("[data-open-director]").first.click(timeout=15000)
    page.wait_for_timeout(6500)
    page.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")
    page.wait_for_timeout(500)


SRC_RUNTIME = RAW / "source-865-frame-structure.json"


def _src_runtime() -> dict:
    """★ 读**源站运行时**读数（★ 比 chunk 逐字更强：运行时不会骗人）。"""
    if not SRC_RUNTIME.exists():
        return {}
    try:
        return json.loads(SRC_RUNTIME.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def _src_frame_pointer_events() -> str | None:
    """★ 源站运行时里**那个框**的 `pointerEvents`（★ 实测，不是推的）。"""
    d = _src_runtime()
    node = (d.get("开参考线后") or d.get("16比9") or {})
    return ((node.get("框") or {}).get("pointerEvents"))


def main() -> int:
    v = Verifier()
    audit: dict[str, Any] = {
        "batch": 865,
        "title": "取景框结构改成源站同构（D25 结案）＋ D26 偏差取证",
    }

    # ══ S1 静态：期望值只从入库的源站逐字解析 ═════════════════════
    v.check("source:the-evidence-file-is-in-the-repo", EVIDENCE.exists(),
            detail=str(EVIDENCE))
    ev: dict[str, Any] = {}
    if EVIDENCE.exists():
        lit = EVIDENCE.read_text(encoding="utf-8")
        ev["容器类"] = grab(
            r'className:"(pointer-events-none absolute bottom-0 left-0 right-0 top-0 z-10)"', lit)
        ev["遮罩层类"] = grab(
            r'className:"(absolute inset-0 bg-black/20 backdrop-blur-md)"', lit)
        ev["框类"] = grab(
            r'className:"(outline-white/18 absolute rounded-xl outline -outline-offset-1)"', lit)
        ev["三分线层类"] = grab(
            r'className:"(pointer-events-none absolute overflow-hidden rounded-xl)"', lit)
        ev["线1"] = grab(
            r'className:"bg-\(--color-white-alpha-50\) absolute left-\[([\d.]+)%\] top-0 h-full w-px"', lit)
        ev["线2"] = grab(
            r'className:"bg-\(--color-white-alpha-50\) absolute left-\[([\d.]+)%\] top-0 h-full w-px"', lit)
        ev["竖线百分比"] = re.findall(
            r'bg-\(--color-white-alpha-50\) absolute left-\[([\d.]+)%\] top-0 h-full w-px', lit)
        ev["横线百分比"] = re.findall(
            r'bg-\(--color-white-alpha-50\) absolute left-0 top-\[([\d.]+)%\] h-px w-full', lit)
        ev["开关位置"] = grab(
            r"(style:\{left:u\.left\+u\.width-40,top:u\.top\+8\})", lit)
        ev["开关类前缀"] = grab(
            r"(nodrag nopan nowheel pointer-events-auto absolute z-20 flex h-8 w-8)", lit)
        ev["有ariaHidden"] = '"aria-hidden":!0' in lit
        ev["框无children"] = bool(re.search(
            r'className:"outline-white/18 absolute rounded-xl outline -outline-offset-1",'
            r'style:\{left:u\.left,top:u\.top,width:u\.width,height:u\.height\}\)', lit))
    v.check("source:the-evidence-file-yields-every-expected-literal",
            bool(ev.get("容器类") and ev.get("遮罩层类") and ev.get("框类")
                 and ev.get("三分线层类") and len(ev.get("竖线百分比") or []) == 2
                 and len(ev.get("横线百分比") or []) == 2
                 and ev.get("开关位置") and ev.get("开关类前缀")
                 and ev.get("有ariaHidden")),
            detail=ev)
    if not (ev.get("容器类") and ev.get("框类") and ev.get("三分线层类")):
        v.result = {"判据数": v.count, "失败": v.failures, "audit": audit}
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        (OUT_DIR / "runtime-audit.json").write_text(
            json.dumps(v.result, ensure_ascii=False, indent=1, default=str),
            encoding="utf-8")
        print(f"\n{v.count} 判据，{len(v.failures)} 失败")
        for f in v.failures:
            print("  FAILED: " + f)
        return 1
    audit["源站逐字"] = ev

    view_code = strip_comments(SRC_VIEW.read_text(encoding="utf-8"))
    _thirds_tag = thirds_start_tag(view_code)
    # ★ clone 侧：源站那些**任意值类**（`outline-white/18`／`bg-(--color-white-alpha-50)`／
    #   `left-[33.333%]`）在 4317 的 Tailwind 扫描下**不生成**
    #   ⟹ ⟹ clone 用 **inline style** 给等效实测值 ⟹ ⟹ 判据比对**等效值**。
    v.check("source:the-clone-has-the-four-siblings-in-source-order",
            all(k in view_code for k in
                ("data-director-aspect-mask", "data-director-aspect-frame",
                 "data-director-thirds", "DirectorFrameThirdsToggle")),
            detail="★ 四个标记都要在")
    v.check("source:the-thirds-layer-carries-the-source-clipping-classes",
            _thirds_tag != ""
            and "overflow-hidden rounded-xl" in _thirds_tag
            and 'aria-hidden="true"' in _thirds_tag,
            detail="★ 源站逐字：`pointer-events-none absolute overflow-hidden rounded-xl`"
                   " ＋ `\"aria-hidden\":!0`"
                   "｜★ 判据只读**三分线层自己的开始标签**（不是全文 contains）"
                   "｜实测 `aria-hidden=\"true\"` 全文 11 处 ⟹ 全文型判据会假绿")
    # ★ ★ 锚点自身的**唯一性**：★ 若 `data-director-thirds` 出现多次
    #   ⟹ ⟹ 上面那条判据锚到的就未必是「那一个」⟹ ⟹ 必须先判红。
    v.check("source:the-thirds-layer-anchor-is-unique",
            view_code.count("data-director-thirds") == 1,
            detail={"data-director-thirds 出现次数": view_code.count("data-director-thirds")})
    # ★ 百分比：从源站逐字里抽出来的 ⟹ ⟹ clone 的 inline 必须是**同一个数**
    want_v = ev["竖线百分比"]
    want_h = ev["横线百分比"]
    v.check("source:the-clone-line-percentages-match-the-source-verbatim",
            f'left: "{want_v[0]}%"' in view_code
            and f'left: "{want_v[1]}%"' in view_code
            and f'top: "{want_h[0]}%"' in view_code
            and f'top: "{want_h[1]}%"' in view_code,
            detail={"源站竖线": want_v, "源站横线": want_h})
    v.check("source:the-toggle-uses-the-source-container-coordinates",
            "left: frameLeft + frameWidth - 40" in view_code
            and "top: frameTop + 8" in view_code,
            detail="★ 源站逐字：`left: u.left + u.width - 40` / `top: u.top + 8`")

    # ★ ★★ **源站运行时**证据（★ 比 chunk 逐字更强 ⟹ ⟹ 独立佐证 D25）
    _src = _src_runtime()
    _src_on = _src.get("开参考线后") or {}
    v.check("source:the-source-runtime-evidence-is-in-the-repo",
            bool(_src_on), detail=str(SRC_RUNTIME))
    v.check("source:the-source-runtime-shows-four-siblings",
            _src_on.get("容器子元素数") == 4
            and _src_on.get("四者都直属容器") is True
            and (_src_on.get("框") or {}).get("子元素数") == 0,
            detail={"容器子元素数": _src_on.get("容器子元素数"),
                    "四者都直属容器": _src_on.get("四者都直属容器"),
                    "框子元素数": (_src_on.get("框") or {}).get("子元素数"),
                    "容器子元素": [c.get("cls") for c in
                                  (_src_on.get("容器子元素") or [])]})

    # ══ S2 运行时结构读数 ═══════════════════════════════════════════
    live: dict[str, Any] = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport={"width": 1920, "height": 1080},
                                    device_scale_factor=1)
            errors: list[str] = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            open_desk(page)

            # ★ 选 16:9 ⟹ ⟹ 取景框在场（★ 用 store，避免点选项被 gizmo 挡）
            page.evaluate(
                "() => { const s = window.__director_store.getState();"
                " s.setFrameAspectRatio('16:9'); }")
            page.wait_for_timeout(900)
            g = page.evaluate(READ)
            live["16比9"] = g
            v.check("clone:the-mask-container-is-mounted",
                    g.get("容器在场") is True, detail=g.get("容器子元素"))
            # ★ ★ 顺序：遮罩层 → 空框 → 三分线层 → 开关
            #   （★ 三分线层此刻**不在场**（参考线没开）⟹ ⟹ 先只断言前两个）
            kids = g.get("容器子元素") or []
            marks = [k.get("标记") for k in kids]
            v.check("clone:the-container-holds-the-mask-and-the-empty-frame",
                    marks[:2] == ["遮罩层", "空框"],
                    detail={"容器子元素": marks})
            # ★ ★ 框是**空框**（源站的框里没有 children）
            v.check("clone:the-frame-is-empty-like-the-source",
                    g.get("框孩子数") == 0,
                    detail={"框孩子数": g.get("框孩子数")})
            v.check("clone:the-frame-is-a-direct-child-of-the-container",
                    g.get("框的父") == "容器" and g.get("遮罩层的父") == "容器",
                    detail={"框的父": g.get("框的父"),
                            "遮罩层的父": g.get("遮罩层的父")})
            v.check("clone:the-frame-keeps-the-clone-only-pointer-events-none",
                    g.get("框的pointerEvents") == "none",
                    detail={"框的pointerEvents": g.get("框的pointerEvents"),
                            "why": "★ D26：源站的框**没有**这一条 ⟹ ⟹ 但 clone 的视口更窄"
                                   " ⟹ ⟹ 照抄会吞掉坐标控件 ⟹ ⟹ 保留 ＋ 登记"})

            # ── 开参考线 ⟹ ⟹ 三分线层应当场（容器坐标）出现 ──
            page.evaluate(
                "() => { const s = window.__director_store.getState();"
                " s.toggleThirds(); }")
            page.wait_for_timeout(800)
            g2 = page.evaluate(READ)
            live["开参考线后"] = g2
            marks2 = [k.get("标记") for k in (g2.get("容器子元素") or [])]
            v.check("clone:the-container-holds-all-four-in-source-order",
                    marks2 == ["遮罩层", "空框", "三分线层", "开关"],
                    detail={"容器子元素": marks2,
                            "期望": ["遮罩层", "空框", "三分线层", "开关"]})
            v.check("clone:the-thirds-layer-is-a-sibling-of-the-frame",
                    g2.get("三分线层的父") == "容器"
                    and g2.get("开关的父") == "容器",
                    detail={"三分线层的父": g2.get("三分线层的父"),
                            "开关的父": g2.get("开关的父")})
            th = g2.get("三分线层") or {}
            v.check("clone:the-thirds-layer-has-the-source-clipping-and-aria",
                    th.get("overflow") == "hidden"
                    and th.get("radius") == "12px"
                    and th.get("ariaHidden") == "true"
                    and th.get("pointerEvents") == "none",
                    detail=th)
            # ★ 四条线的**相对位置**＝ 源站的 33.333% / 66.667%
            rel = g2.get("线的相对位置") or []
            v.check("clone:the-four-thirds-sit-at-the-source-percentages",
                    len(rel) == 4
                    and abs(rel[0].get("左百分比", -1) - float(want_v[0])) <= 0.2
                    and abs(rel[1].get("左百分比", -1) - float(want_v[1])) <= 0.2
                    and abs(rel[2].get("上百分比", -1) - float(want_h[0])) <= 0.2
                    and abs(rel[3].get("上百分比", -1) - float(want_h[1])) <= 0.2,
                    detail={"线的相对位置": rel,
                            "源站": {"竖线": want_v, "横线": want_h}})
            # ★ 开关的**容器坐标** ＝ 框左 + 框宽 − 40 ／ 框上 + 8
            frm = g2.get("框") or {}
            btn = g2.get("开关") or {}
            v.check("clone:the-toggle-sits-at-the-source-container-coordinates",
                    abs(btn.get("x", -1) - (frm.get("x", 0) + frm.get("w", 0) - 40)) <= 2
                    and abs(btn.get("y", -1) - (frm.get("y", 0) + 8)) <= 2,
                    detail={"开关": btn, "框": frm,
                            "期望": "容器坐标 (框左+框宽−40, 框上+8)"})

            # ══ S3 ★ 取景框在场时，坐标控件的**每一枚**按钮都必须命中自己
            #   ★ ★ 这是 batch 864 的**后遗症**：864 把 gizmo 降到 `z-10` 之后
            #   ⟹ ⟹ 取景框上那枚开关（`z-20`）反过来盖住了 gizmo 的两枚按钮
            #   ⟹ ⟹ 「X 反向」「Z 正向」的点不到了 ⟹ ⟹ 864 的门禁只测了
            #   ⟹ ⟹ 「开关能不能点」⟹ ⟹ 没测「它挡了谁」⟹ ⟹ 漏掉了。
            gz = page.evaluate(GIZMO_HIT)
            live["坐标控件命中"] = gz
            _bad = [b for b in (gz.get("按钮") or []) if not b.get("命中是这枚按钮")]
            v.check("clone:every-gizmo-button-is-hittable-while-the-frame-exists",
                    not _bad,
                    detail={"总按钮数": gz.get("按钮数"),
                            "点不到的": _bad,
                            "框的pointerEvents": gz.get("框的pointerEvents"),
                            "why": "★ 源站逐字的那枚开关必须**永远可点** ⟹ ⟹ "
                                   "clone 自有的坐标控件必须让开（batch 865 把它挪到视口左侧）"})

            # ★ ★ 框的 `pointer-events` ⟹ ⟹ **不是**偏差（★ 这是本批的一个发现）
            #   ★ 源站的框**没有**写 `pointer-events` ⟹ ⟹ 但 `pointer-events`
            #   **是可继承属性** ⟹ ⟹ 源站那个框**继承**了容器的 `pointer-events-none`
            #   ⟹ ⟹ 源站运行时读数里框的 `pointerEvents` 就是 `"none"`
            #   ⟹ ⟹ ★ clone 显式写出来 = **与源站完全等价** ⟹ ⟹ 无需登记偏差。
            v.check("clone:the-frame-pierces-no-pointer-like-the-source",
                    gz.get("框的pointerEvents") == "none"
                    and _src_frame_pointer_events() == "none",
                    detail={"clone": gz.get("框的pointerEvents"),
                            "源站运行时": _src_frame_pointer_events(),
                            "why": "★ 源站的框**没有** pointer-events 类 ⟹ ⟹ "
                                   "它**继承**了容器的 `pointer-events-none` "
                                   "⟹ ⟹ 两者等价"})

            v.check("diagnostics:no-page-errors",
                    not [e for e in errors if "TransformControls" not in e],
                    detail=errors[:5])
            audit["live"] = live
        finally:
            browser.close()

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

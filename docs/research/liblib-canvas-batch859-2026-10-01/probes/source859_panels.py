#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 859 源站探针（**只读**）：量「全景图」「选择画幅比例」**两个面板模式**。

## ★ 靶子（batch 858 登记的 D8）

batch 858 实测发现：源站的左侧资源栏是**五模式互斥容器**
（`scene`／`character`／`camera`／`panorama`／`aspect`）⟹ ⟹
★ **「全景图」「选择画幅比例」也是面板模式**，不是浮层。
⟹ ⟹ 而 clone 把这两个做成了 rail 上的 **portal 浮层** ⟹ ⟹ 本批要改。

## ★ 源站逐字（chunk `/tmp/liblib_srcjs2/0fmehki05gkzw.js.js`）

- `"panorama"===z` ⟹ 标题条 `aO`（`canvas:directorPanorama`）＋ 容器 `px-2`
  ＋ **三枚行类 `eu`**：本地上传（`u.p.Upload`）／历史（`u.p.HistoryN`）／
  AI 生成（`aM.f`，`disabled:E`，`E?生成中:AI生成`）。
- `"aspect"===z` ⟹ 标题条 `aO`（`canvas:directorSelectAspectRatioHint`）
  ＋ 容器 `grid grid-cols-2 gap-2 px-2 pb-3`
  ＋ 每格 `h-[72px] … rounded-xl border`（选中 `border-white/85`／未选 `border-white/10`）。

## ★ 本探针要读到的（不能猜）

① rail 每一枚按钮的 `aria-label`／`aria-pressed`／位置 ⟹ ⟹ 认准哪枚是全景图、
   哪枚是画幅比例（**按结构与文案，不按位置硬猜**）；
② 切到全景图 ⟹ 面板矩形、标题文本、三枚行的**逐行矩形与字号**；
③ 切到画幅比例 ⟹ 面板矩形、标题文本、网格的**列数/间距/内边距**、
   每格的矩形与文本、比例字形的盒子；
④ ★ **这两个模式下场景树不在场**（互斥）⟹ ⟹ 坐实「它们是面板模式」；
⑤ ★ 页面上**没有**这两个的 portal 浮层（唯一的 portal 是 crowd 对话框）。

## ★ 副作用声明

**只点 rail 条目与面板里的「查看」类按钮**；**不点**任何会触发
付费 AI 生成／上传的按钮（源站逐字：AI 生成那枚 `disabled:E`，
历史/上传只读打开列表）。

## 输出
  raw/source-859-panels.json
  images/859src_panorama.png ／ 859src_aspect.png
"""
from __future__ import annotations

import json
import pathlib
import traceback

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch859-2026-10-01"
RAW = BATCH / "raw"
SHOTS = BATCH / "images"

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

# ★ rail 按钮（最左侧竖条）——带 aria-pressed 与文案
READ_RAIL = r"""()=>{
  const out = [];
  document.querySelectorAll('button').forEach(b=>{
    const r=b.getBoundingClientRect();
    if(r.width<=0||r.height<=0) return;
    if(r.x>70) return;
    if(r.y<40||r.y>1000) return;
    out.push({x:Math.round(r.x), y:Math.round(r.y),
      w:Math.round(r.width), h:Math.round(r.height),
      aria:b.getAttribute('aria-label')||'',
      pressed:b.getAttribute('aria-pressed'),
      title:b.getAttribute('title')||'',
      text:(b.textContent||'').replace(/\s+/g,' ').trim().slice(0,24)});
  });
  out.sort((a,b)=>a.y-b.y);
  return out;
}"""

# ★ 左侧 232 面板（模式互斥容器）——通用读数
READ_PANEL = r"""()=>{
  const vis=(e)=>{ if(!e) return false; const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0; };
  const rect=(e)=>{ if(!e) return null; const r=e.getBoundingClientRect();
    return {x:Math.round(r.x), y:Math.round(r.y), w:Math.round(r.width),
            h:Math.round(r.height), right:Math.round(r.right), bottom:Math.round(r.bottom)}; };
  const panels=[...document.querySelectorAll('div')].filter(e=>{
    const c=(e.className||'').toString();
    return c.indexOf('w-[232px]')>=0 && c.indexOf('flex-col')>=0;
  });
  const panel=panels.find(vis)||null;
  const info={panel: rect(panel),
              panelCls: panel?(panel.className||'').toString().slice(0,220):null,
              panelCount: panels.length};
  if(panel){
    const title=[...panel.querySelectorAll('div')].find(e=>{
      const c=(e.className||'').toString();
      return c.indexOf('h-12')>=0 && c.indexOf('shrink-0')>=0 && vis(e);
    });
    info.title=rect(title);
    info.titleCls=title?(title.className||'').toString().slice(0,180):null;
    info.titleFont=title?getComputedStyle(title).fontSize:null;
    info.titleText=title?(title.innerText||'').trim():null;
    // ★ 面板里**全部**可见按钮（逐个量；行类 h-8 / 卡片类 h-[72px]）
    info.buttons=[...panel.querySelectorAll('button')].filter(vis).map(e=>{
      const r=e.getBoundingClientRect();
      const cs=getComputedStyle(e);
      const sp=e.querySelector('span');
      const spc=sp?getComputedStyle(sp):null;
      const svg=e.querySelector('svg');
      const svr=svg?svg.getBoundingClientRect():null;
      return {text:(e.textContent||'').replace(/\s+/g,' ').trim().slice(0,20),
              x:Math.round(r.x), y:Math.round(r.y), w:Math.round(r.width),
              h:Math.round(r.height),
              cls:(e.className||'').toString().slice(0,190),
              fontSize:cs.fontSize, lineHeight:cs.lineHeight,
              spanFont:spc?spc.fontSize:null,
              spanLineHeight:spc?spc.lineHeight:null,
              spanText:sp?(sp.textContent||'').trim().slice(0,20):null,
              borderColor:cs.borderColor, borderWidth:cs.borderWidth,
              borderRadius:cs.borderRadius,
              disabled:e.disabled||false,
              svgBox: svr?{x:Math.round(svr.x),y:Math.round(svr.y),
                           w:Math.round(svr.width),h:Math.round(svr.height)}:null};
    });
    // ★ 网格容器（画幅比例那枚）
    info.grids=[...panel.querySelectorAll('div')].filter(vis).map(e=>{
      const c=(e.className||'').toString();
      if(c.indexOf('grid-cols-2')<0) return null;
      const cs=getComputedStyle(e);
      const r=e.getBoundingClientRect();
      return {cls:c.slice(0,180), box:rect(e),
              gridTemplateColumns:cs.gridTemplateColumns,
              columnGap:cs.columnGap, rowGap:cs.rowGap,
              padding:cs.padding, display:cs.display};
    }).filter(Boolean);
    // ★ 场景树在不在？（互斥 ⟹ 不该在）
    const aside=document.querySelector('aside');
    info.asideText=(aside?(aside.textContent||''):'').replace(/\s+/g,' ').trim().slice(0,160);
    info.sceneTreePresent=Boolean(aside&&(aside.textContent||'').includes('场景'));
    // ★ 直系子容器（面板的第二层）
    info.children=[...panel.children].map(e=>{
      const cs=getComputedStyle(e);
      return {tag:e.tagName, cls:(e.className||'').toString().slice(0,150),
              box:rect(e), padding:cs.padding, display:cs.display};
    });
  }
  // ★ 页面上有没有**固定定位的浮层**（portal）？
  info.fixedPortals=[...document.querySelectorAll('body *')].filter(e=>{
    const cs=getComputedStyle(e);
    if(cs.position!=='fixed') return false;
    const r=e.getBoundingClientRect();
    return r.width>40 && r.height>20 && r.x<700;
  }).map(e=>{
    const r=e.getBoundingClientRect();
    return {tag:e.tagName, cls:(e.className||'').toString().slice(0,140),
            x:Math.round(r.x), y:Math.round(r.y),
            w:Math.round(r.width), h:Math.round(r.height),
            z:getComputedStyle(e).zIndex,
            text:(e.textContent||'').replace(/\s+/g,' ').trim().slice(0,40)};
  }).slice(0,12);
  return info;
}"""


def open_desk(page) -> None:
    card = page.locator(".react-flow__node-director-console-3d").first
    card.hover()
    page.wait_for_timeout(600)
    page.locator(
        ".react-flow__node-director-console-3d button:has-text('打开导演台')"
    ).first.click()
    page.wait_for_timeout(8_000)


def main() -> int:
    out: dict = {}
    try:
        cookies = json.loads(COOKIE.read_text(encoding="utf-8"))
        with sync_playwright() as pw:
            br = pw.chromium.launch(headless=True)
            ctx = br.new_context(viewport={"width": 1920, "height": 1080},
                                 locale="zh-CN")
            ctx.add_cookies([{"name": c["name"], "value": c["value"],
                              "domain": c["domain"], "path": c.get("path", "/")}
                             for c in cookies])
            pg = ctx.new_page()
            pg.set_default_timeout(20_000)
            pg.goto(URL, wait_until="domcontentloaded", timeout=90_000)
            pg.wait_for_timeout(12_000)
            el = pg.query_selector("text=下次再说")
            if el:
                el.click()
                pg.wait_for_timeout(900)
            open_desk(pg)
            out["①导演台已打开"] = True

            if pg.query_selector("[data-director-practice-escape]"):
                out["②有练习浮层"] = True
                pg.keyboard.press("Escape")
                pg.wait_for_timeout(900)

            rail = pg.evaluate(READ_RAIL)
            out["③rail按钮"] = rail

            def pick(keyword: str) -> dict | None:
                for r in rail:
                    blob = f"{r.get('aria','')} {r.get('title','')} {r.get('text','')}"
                    if keyword in blob:
                        return r
                return None

            pano = pick("全景")
            asp = pick("画幅") or pick("比例")
            out["③全景图按钮"] = pano
            out["③画幅比例按钮"] = asp

            # ── ④ 全景图模式 ──
            if pano:
                pg.mouse.click(pano["x"] + pano["w"] / 2, pano["y"] + pano["h"] / 2)
                pg.wait_for_timeout(1_200)
                out["④全景图面板"] = pg.evaluate(READ_PANEL)
                out["④全景图时rail"] = pg.evaluate(READ_RAIL)
                pg.screenshot(path=str(SHOTS / "859src_panorama.png"))

            # ── ⑤ 画幅比例模式 ──
            if asp:
                pg.mouse.click(asp["x"] + asp["w"] / 2, asp["y"] + asp["h"] / 2)
                pg.wait_for_timeout(1_200)
                out["⑤画幅比例面板"] = pg.evaluate(READ_PANEL)
                out["⑤画幅比例时rail"] = pg.evaluate(READ_RAIL)
                pg.screenshot(path=str(SHOTS / "859src_aspect.png"))

            # ── ⑥ 切回场景 ⟹ 场景树该回来（互斥的另一头）──
            scene = pick("场景")
            out["⑥场景按钮"] = scene
            if scene:
                pg.mouse.click(scene["x"] + scene["w"] / 2,
                               scene["y"] + scene["h"] / 2)
                pg.wait_for_timeout(1_200)
                out["⑥切回场景后"] = pg.evaluate(READ_PANEL)
            pg.close()
    except Exception:  # noqa: BLE001
        out["★异常"] = traceback.format_exc()[-2500:]
    RAW.mkdir(parents=True, exist_ok=True)
    SHOTS.mkdir(parents=True, exist_ok=True)
    (RAW / "source-859-panels.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2)[:9000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

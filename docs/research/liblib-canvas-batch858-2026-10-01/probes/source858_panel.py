#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 858 源站探针（**只读**·不点「添加」·不产生任何副作用）：
量「添加角色」**面板**与「群众阵列」**对话框**的内部结构。

## ★ 为什么要有这个探针

clone 面板化之后，对话框落在 (280,388) 220×**203** ⟹ ⟹ 与 batch 857 对源站
实测的 220×**204** 差 **1px**。差在哪一段（标题行 / 网格 / 页脚）必须
**实测归因**，不能猜。

★ 于是本探针量源站对话框的**逐段高度**：
  · 标题行（含标题文字的行盒高度、字号、**字体栈**）
  · 网格（行数/列数那两格、间距那格跨两行）
  · 每个 label 的文字行盒高度、每个 input 的盒高
  · 页脚（取消 / 添加）
⟹ ⟹ 拿它与 clone 的同口径读数逐段相减 ⟹ ⟹ 就能定位那 1px。

★ 同时复核本批引以为据的源站几何：
  · 「添加角色」面板宽 232、标题条 h-12
  · 「群众 (3x3)」按钮 @ (56,388) 216×32
  · 「几何模型」**就地展开** @ (68,452) 204×256、每项 199×32
  · crowd / geometry **共用一个状态**（开一个关另一个）

## ★ 定位策略（全程按结构，不手打中文）

- crowd 入口 ＝「添加角色」面板里**唯一**那枚 `button[aria-haspopup="dialog"]`
  ⟹ ⟹ 逐个点左侧 rail 的按钮 ⟹ ⟹ 找**新出现**的那枚 ⟹ ⟹ 不靠文案。
- 群众对话框 ＝ 页面上**含 ≥2 个 number 输入**的 `role="dialog"`。

## 输出
  raw/source-858-panel.json
  images/858src_*.png
"""
import json
import pathlib
import traceback

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch858-2026-10-01"
RAW = BATCH / "raw"
SHOTS = BATCH / "images"

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

# ★ 左侧 rail 的按钮（按位置认：最左侧竖条）
READ_RAIL = r"""()=>{
  const out = [];
  document.querySelectorAll('button').forEach(b=>{
    const r=b.getBoundingClientRect();
    if(r.width<=0||r.height<=0) return;
    if(r.x>70) return;
    if(r.y<40||r.y>1000) return;
    out.push({x:Math.round(r.x), y:Math.round(r.y),
      w:Math.round(r.width), h:Math.round(r.height),
      aria:b.getAttribute('aria-label')||''});
  });
  out.sort((a,b)=>a.y-b.y);
  return out;
}"""

READ_POPUP_BTN = r"""()=>{
  const out=[];
  document.querySelectorAll('button[aria-haspopup="dialog"]').forEach(e=>{
    const r=e.getBoundingClientRect();
    if(r.width<=0||r.height<=0) return;
    out.push({x:Math.round(r.x), y:Math.round(r.y),
      w:Math.round(r.width), h:Math.round(r.height),
      aria:e.getAttribute('aria-label')||'',
      text:(e.textContent||'').replace(/\s+/g,' ').trim().slice(0,26)});
  });
  return out;
}"""

# ★★ 对话框**逐段**读数（本批的核心）
READ_DIALOG = r"""()=>{
  const all=[...document.querySelectorAll('[role="dialog"]')].map(dlg=>{
    const nums=[...dlg.querySelectorAll('input[type="number"]')];
    const r=dlg.getBoundingClientRect();
    const cs=getComputedStyle(dlg);
    const seg=(e)=>{ if(!e) return null; const b=e.getBoundingClientRect();
      return {x:Math.round(b.x), y:Math.round(b.y), w:Math.round(b.width), h:Math.round(b.height)}; };
    const kids=[...dlg.children].map((c,i)=>{
      const b=c.getBoundingClientRect();
      const ccs=getComputedStyle(c);
      return {i, tag:c.tagName, cls:(c.className||'').toString().slice(0,150),
              box:seg(c), marginTop:ccs.marginTop, marginBottom:ccs.marginBottom,
              display:ccs.display, gridTemplateColumns:ccs.gridTemplateColumns,
              rowGap:ccs.rowGap, columnGap:ccs.columnGap};
    });
    // ★ 标题文字的行盒
    const titleSpan=dlg.querySelector('span');
    const ts=titleSpan?getComputedStyle(titleSpan):null;
    // ★ 每个 label：文字 span 的行盒 + input 的盒高
    const labels=[...dlg.querySelectorAll('label')].map(l=>{
      const sp=l.querySelector('span'); const inp=l.querySelector('input');
      const ss=sp?getComputedStyle(sp):null;
      const is=inp?getComputedStyle(inp):null;
      return {cls:(l.className||'').toString().slice(0,140),
              labelBox:seg(l),
              spanBox:seg(sp), spanFont: ss?ss.fontSize:null,
              spanLineHeight: ss?ss.lineHeight:null,
              spanFontFamily: ss?ss.fontFamily:null,
              inputBox:seg(inp), inputFont: is?is.fontSize:null,
              inputHeight: is?is.height:null,
              aria:inp?inp.getAttribute('aria-label'):null,
              min:inp?inp.getAttribute('min'):null,
              max:inp?inp.getAttribute('max'):null,
              step:inp?inp.getAttribute('step'):null,
              v:inp?inp.value:null};
    });
    const btns=[...dlg.querySelectorAll('button')].map(b=>{
      const bcs=getComputedStyle(b);
      return {text:(b.textContent||'').replace(/\s+/g,' ').trim().slice(0,16),
              cls:(b.className||'').toString().slice(0,150),
              box:seg(b), height:bcs.height, fontSize:bcs.fontSize};
    });
    return {aria:dlg.getAttribute('aria-label')||'',
            n:nums.length, visible:r.width>0&&r.height>0,
            box:seg(dlg), z:cs.zIndex, bg:cs.backgroundColor,
            shadow:cs.boxShadow, padding:cs.padding, fontFamily:cs.fontFamily,
            fontSize:cs.fontSize, lineHeight:cs.lineHeight,
            kids, labels, btns,
            text:(dlg.textContent||'').replace(/\s+/g,' ').trim().slice(0,120)};
  });
  return all;
}"""

# ★ 「添加角色」面板（源站的左侧面板是模式互斥的 ⟹ 切过去就没有场景树了）
READ_PANEL = r"""()=>{
  const vis=(e)=>{ if(!e) return false; const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0; };
  const rect=(e)=>{ if(!e) return null; const r=e.getBoundingClientRect();
    return {x:Math.round(r.x), y:Math.round(r.y), w:Math.round(r.width),
            h:Math.round(r.height), right:Math.round(r.right), bottom:Math.round(r.bottom)}; };
  // ★ 左侧 232 宽那个面板（源站 aside 内 `flex w-[232px] min-w-0 flex-col`）
  const panels=[...document.querySelectorAll('div')].filter(e=>{
    const c=(e.className||'').toString();
    return c.indexOf('w-[232px]')>=0 && c.indexOf('flex-col')>=0;
  });
  const panel=panels.find(vis)||null;
  const info={panel: rect(panel), panelCls: panel?(panel.className||'').toString().slice(0,200):null};
  if(panel){
    // 标题条：面板里第一个 h-12 的子元素
    const title=[...panel.querySelectorAll('div')].find(e=>{
      const c=(e.className||'').toString();
      return c.indexOf('h-12')>=0 && c.indexOf('shrink-0')>=0 && vis(e);
    });
    info.title=rect(title);
    info.titleCls=title?(title.className||'').toString().slice(0,160):null;
    info.titleFont=title?getComputedStyle(title).fontSize:null;
    info.titleText=title?title.innerText.trim():null;
    // 行：面板里 h-8 的按钮（逐行量）
    info.rows=[...panel.querySelectorAll('button')].filter(e=>{
      const c=(e.className||'').toString();
      return c.indexOf('h-8')>=0 && vis(e);
    }).map(e=>{
      const r=e.getBoundingClientRect();
      const cs=getComputedStyle(e);
      const sp=e.querySelector('span');
      const spc=sp?getComputedStyle(sp):null;
      return {text:(e.textContent||'').replace(/\s+/g,' ').trim().slice(0,18),
              x:Math.round(r.x), y:Math.round(r.y), w:Math.round(r.width), h:Math.round(r.height),
              fontSize:cs.fontSize, lineHeight:cs.lineHeight, fontFamily:cs.fontFamily,
              spanFont: spc?spc.fontSize:null,
              ariaExpanded:e.getAttribute('aria-expanded'),
              ariaHasPopup:e.getAttribute('aria-haspopup')};
    });
    // 几何就地展开：`ml-3 border-l pl-1` 那个容器
    const geo=[...panel.querySelectorAll('div')].find(e=>{
      const c=(e.className||'').toString();
      return c.indexOf('ml-3')>=0 && c.indexOf('border-l')>=0 && vis(e);
    });
    info.geometry=rect(geo);
    info.geometryCls=geo?(geo.className||'').toString().slice(0,160):null;
    if(geo){
      info.geometryItems=[...geo.querySelectorAll('button')].map(e=>{
        const r=e.getBoundingClientRect();
        return {text:(e.textContent||'').replace(/\s+/g,' ').trim().slice(0,14),
                x:Math.round(r.x), y:Math.round(r.y), w:Math.round(r.width), h:Math.round(r.height)};
      });
    }
    // ★ 场景树还在不在？（源站逐字：互斥 ⟹ 切到 character 后没有树）
    info.sceneTreePresent=Boolean(document.querySelector('aside')?.textContent?.includes('场景'));
  }
  return info;
}"""


def open_desk(page):
    card = page.locator(".react-flow__node-director-console-3d").first
    card.hover()
    page.wait_for_timeout(600)
    page.locator(
        ".react-flow__node-director-console-3d button:has-text('打开导演台')"
    ).first.click()
    page.wait_for_timeout(8_000)


def main() -> int:
    out = {}
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

            # ★ 关练习浮层（只能用 Escape；点 ✕ 会关掉整个导演台）
            if pg.query_selector("[data-director-practice-escape]"):
                out["②有练习浮层"] = True
                pg.keyboard.press("Escape")
                pg.wait_for_timeout(900)

            # ── ③ 逐个点 rail，找「添加角色」面板
            base_pop = pg.evaluate(READ_POPUP_BTN)
            panel_on = False
            for item in pg.evaluate(READ_RAIL):
                try:
                    pg.mouse.click(item["x"] + item["w"] / 2, item["y"] + item["h"] / 2)
                    pg.wait_for_timeout(700)
                    now = pg.evaluate(READ_POPUP_BTN)
                    new = [b for b in now if b not in base_pop]
                    if new:
                        out["③点开的rail按钮"] = item
                        out["③新出现的入口"] = new
                        panel_on = True
                        break
                    pg.keyboard.press("Escape")
                    pg.wait_for_timeout(300)
                except Exception:  # noqa: BLE001
                    continue
            if not panel_on:
                out["★没找到 crowd 入口"] = True
                return _save(out)

            pg.wait_for_timeout(500)
            out["④添加角色面板"] = pg.evaluate(READ_PANEL)
            pg.screenshot(path=str(SHOTS / "858src_character-panel.png"))

            # ── ⑤ 打开 crowd 对话框（★ 只打开、不点「添加」⟹ ⟹ 无副作用）
            # ★ 按**位置**点（③ 实测到的那枚在 (56,388)）⟹ ⟹ 不用
            #   `document.querySelector('button[aria-haspopup="dialog"]')`
            #   ——页面上可能还有**别的**同属性按钮，第一个未必是它。
            crowd_entry = out["③新出现的入口"][0]
            pg.mouse.click(crowd_entry["x"] + crowd_entry["w"] / 2,
                           crowd_entry["y"] + crowd_entry["h"] / 2)
            pg.wait_for_timeout(900)
            dlg_all = pg.evaluate(READ_DIALOG)
            out["⑤全部dialog摘要"] = [
                {"aria": d["aria"], "n": d["n"], "visible": d["visible"],
                 "box": d["box"], "text": d["text"]} for d in dlg_all
            ]
            crowd = None
            for d in dlg_all:
                if d["n"] >= 2:
                    crowd = d
                    break
            out["⑤群众对话框"] = crowd
            out["⑤页面上全部dialog数"] = len(dlg_all)
            pg.screenshot(path=str(SHOTS / "858src_crowd-dialog.png"))

            # ── ⑥ ★ crowd / geometry 共用一个状态 ⟹ ⟹ 开 crowd 时几何是关的
            out["⑥开crowd时几何展开"] = pg.evaluate(READ_PANEL).get("geometry")
            pg.evaluate("""()=>{ const gs=[...document.querySelectorAll('div')]
                .filter(e=>{const c=(e.className||'').toString();
                  return c.indexOf('ml-3')>=0 && c.indexOf('border-l')>=0;});
                if(gs.length) { const b=gs[0].previousElementSibling; } }""")
            # 点「几何模型」⟹ 逐字：`O(e=>"geometry"===e?null:"geometry")`
            pg.evaluate("""()=>{
              const rows=[...document.querySelectorAll('button')].filter(e=>{
                const c=(e.className||'').toString();
                return c.indexOf('h-8')>=0 && c.indexOf('w-full')>=0;});
              for(const r of rows){ if((r.textContent||'').includes('几何模型')){ r.click(); return; } }
            }""")
            pg.wait_for_timeout(800)
            geo_state = pg.evaluate(READ_PANEL)
            out["⑦开几何后"] = {
                "几何展开": geo_state.get("geometry"),
                "几何项": geo_state.get("geometryItems"),
                "对话框还在吗": any(d["n"] >= 2 and d["visible"]
                                    for d in pg.evaluate(READ_DIALOG)),
            }
            pg.screenshot(path=str(SHOTS / "858src_geometry-inline.png"))
            pg.close()
    except Exception:
        out["★异常"] = traceback.format_exc()[-2500:]
    return _save(out)


def _save(out: dict) -> int:
    RAW.mkdir(parents=True, exist_ok=True)
    SHOTS.mkdir(parents=True, exist_ok=True)
    (RAW / "source-858-panel.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2)[:7000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

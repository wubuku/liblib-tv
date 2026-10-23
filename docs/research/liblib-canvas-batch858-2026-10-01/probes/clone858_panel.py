#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 858 clone 探针：「添加角色」**面板化**后的几何与行为。

## ★ 本批的靶子（batch 857 登记的 D1）

clone 此前把「添加角色」做成 rail 上的 **portal 浮层** ⟹ ⟹ 它与场景树
**完全重叠**（浮层 x=48..280 ＝ 场景树 x=48..280）⟹ ⟹ 场景树看着能点、
其实点不动。源站逐字却是**左侧面板模式**（互斥）：

    `e?null:(0,i.jsxs)("div",{className:"flex w-[232px] min-w-0 flex-col
       bg-[#171717]",children:["scene"===z?n:null,"character"===z?(…)]})`

⟹ ⟹ 本探针要证明的事：
  ① 切到「添加角色」时**场景树不渲染**（互斥，源站逐字）；
  ② 面板宽度 232、标题条 h-12/12px、行 h-8/13px（源站逐字）；
  ③ 「群众 (3x3)」落在 **(56,388) 216×32** ⟹ ⟹ 对话框落在 **(280,388)
     220×204** ⟹ ⟹ 与源站实测**逐字一致**（batch 857 source-857-crowd.json）；
  ④ 「几何模型」**就地展开**在 (68,452) 204×256、每项 199×32
     ⟹ ⟹ 与源站实测**逐字一致**（batch 590 README 的源站读数）；
  ⑤ 源站的 crowd / geometry **共用一个状态** ⟹ ⟹ 开一个关另一个；
  ⑥ rail 按钮 `aria-pressed` 跟着面板模式走（源站逐字 `z===r.id`）。

## ★ 期望值的出处（不是 clone 自己算的）

| 期望 | 出处 |
| --- | --- |
| 对话框 220×204 @(280,388) | batch 857 `raw/source-857-crowd.json`（源站实测） |
| 几何就地展开 204×256 @(68,452)、项 199×32 | batch 590 README（源站实测） |
| 面板宽 232、标题 12px/h-12、行 h-8/13px | 源站 chunk 逐字（`aO` / `eu`） |
| 输入量程 rows/cols 1..10 step1、spacing .1..10 step.1 | 源站 chunk 逐字 |

## 输出
  raw/clone-858-panel.json
  images/858clone_*.png
"""
import json
import pathlib
import traceback

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch858-2026-10-01"
RAW = BATCH / "raw"
SHOTS = BATCH / "images"
BASE = "http://localhost:4317"

# ★ 源站实测的期望值（出处见上表）
SOURCE = {
    "panel_width": 232,
    "title_height": 48,
    "title_font_px": 12,
    "row_height": 32,
    "row_font_px": 13,
    "crowd_btn": {"x": 56, "y": 388, "w": 216, "h": 32},
    "crowd_dialog": {"x": 280, "y": 388, "w": 220, "h": 204},
    "geometry_box": {"x": 68, "y": 452, "w": 204, "h": 256},
    "geometry_item_w": 199,
    "dialog_z": 1800,
}

READ = r"""()=>{
  const vis=(e)=>{ if(!e) return false; const r=e.getBoundingClientRect();
    const cs=getComputedStyle(e);
    return r.width>0 && r.height>0 && cs.display!=='none' && cs.visibility!=='hidden'; };
  const rect=(e)=>{ if(!e) return null; const r=e.getBoundingClientRect();
    return {x:Math.round(r.x), y:Math.round(r.y), w:Math.round(r.width), h:Math.round(r.height),
            right:Math.round(r.right), bottom:Math.round(r.bottom)}; };
  const q=(s)=>document.querySelector(s);
  const panel=q('[data-director-character-panel]');
  const title=q('[data-director-panel-title="add-character"]');
  const dlg=q('[data-director-crowd-dialog]');
  const geo=q('[data-director-geometry-submenu]');
  const crowdBtn=q("[data-director-character-option='crowd-3x3']");
  const rows=[...document.querySelectorAll('[data-director-character-option]')].map(el=>{
    const labelSpan=[...el.querySelectorAll('span')].find(s=>s.getAttribute('aria-hidden')!=='true');
    return {id:el.getAttribute('data-director-character-option'),
            label:(labelSpan?.innerText||'').trim(),
            y:Math.round(el.getBoundingClientRect().y),
            w:Math.round(el.getBoundingClientRect().width),
            h:Math.round(el.getBoundingClientRect().height),
            font: getComputedStyle(el).fontSize,
            ariaExpanded: el.getAttribute('aria-expanded'),
            ariaHasPopup: el.getAttribute('aria-haspopup'),
            chevron: Boolean(el.querySelector('span[aria-hidden="true"]'))};
  });
  const geoItems=[...document.querySelectorAll('[data-director-geometry-option]')].map(el=>{
    const r=el.getBoundingClientRect();
    return {id:el.getAttribute('data-director-geometry-option'),
            x:Math.round(r.x), y:Math.round(r.y), w:Math.round(r.width), h:Math.round(r.height)};
  });
  const inp=(k)=>{ const e=q("[data-director-crowd-input='"+k+"']"); if(!e) return null;
    return {value:e.value, min:e.getAttribute('min'), max:e.getAttribute('max'),
            step:e.getAttribute('step'), aria:e.getAttribute('aria-label'),
            cls:e.className}; };
  const railBtn=(id)=>{ const e=q("[data-director-rail-entry='"+id+"']"); if(!e) return null;
    return {pressed:e.getAttribute('aria-pressed'), cls:e.className}; };
  return {
    面板: rect(panel),
    面板可见: vis(panel),
    面板标签: panel ? panel.getAttribute('aria-label') : null,
    标题条: rect(title),
    标题字号: title ? getComputedStyle(title).fontSize : null,
    标题文本: title ? title.innerText.trim() : null,
    左侧面板模式: (q('[data-director-left-panel-view]')||{}).dataset
        ? q('[data-director-left-panel-view]').getAttribute('data-director-left-panel-view') : null,
    场景树存在: Boolean(q('[data-director-tree]')),
    场景树按钮数: document.querySelectorAll('[data-director-tree] button').length,
    选项行: rows,
    几何展开: rect(geo),
    几何项: geoItems,
    crowd按钮: rect(crowdBtn),
    crowd按钮背景: crowdBtn ? getComputedStyle(crowdBtn).backgroundColor : null,
    对话框: rect(dlg),
    对话框可见: vis(dlg),
    对话框z: dlg ? getComputedStyle(dlg).zIndex : null,
    对话框背景: dlg ? getComputedStyle(dlg).backgroundColor : null,
    对话框阴影: dlg ? getComputedStyle(dlg).boxShadow : null,
    对话框标题字号: (()=>{ const t=dlg && dlg.querySelector('span.text-\\[13px\\]');
      return t ? getComputedStyle(t).fontSize : null; })(),
    计数文案: (q('[data-director-crowd-count]')||{}).textContent||'',
    行数: inp('rows'), 列数: inp('columns'), 间距: inp('spacing'),
    rail场景: railBtn('scene'),
    rail添加角色: railBtn('add-character'),
    rail添加机位: railBtn('add-camera'),
    移动端入口: rect(q('[data-director-crowd-mobile-trigger]')),
  };
}"""


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


def open_desk(pg):
    pg.goto(BASE + "/", wait_until="domcontentloaded")
    pg.wait_for_timeout(3000)
    pg.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")
    pg.wait_for_function("() => Boolean(window.__director_store)", timeout=90_000)
    pg.wait_for_timeout(1500)
    node = pg.locator(".react-flow__node-script-execution").first
    try:
        node.scroll_into_view_if_needed(timeout=8000)
    except Exception:
        pass
    pg.wait_for_timeout(400)
    try:
        node.hover(timeout=8000)
        pg.wait_for_timeout(600)
    except Exception:
        pass
    pg.locator("[data-open-director]").first.click(timeout=15000)
    pg.wait_for_timeout(6500)
    pg.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")


def main() -> int:
    out = {"批次": "batch 858", "探针": "clone858_panel", "源站期望": SOURCE}
    RAW.mkdir(parents=True, exist_ok=True)
    SHOTS.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        try:
            # ══════════════════ 桌面 1440×900 ══════════════════
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            open_desk(page)
            out["①打开导演台"] = "OK"

            # 初始态：场景树在，添加角色不在
            out["②初始态"] = page.evaluate(READ)

            # 点「添加角色」
            page.locator("[data-director-rail-entry='add-character']").click(timeout=15000)
            page.wait_for_timeout(500)
            state = page.evaluate(READ)
            out["③切到添加角色面板"] = state
            page.screenshot(path=str(SHOTS / "858clone_character-panel.png"))

            # ★ 判定：crowd 按钮是否落在源站实测的 (56,388,216,32)
            cb = state.get("crowd按钮") or {}
            out["③crowd按钮是否命中源站"] = {
                "期望": SOURCE["crowd_btn"], "实测": cb,
                "命中": all(cb.get(k) == v for k, v in SOURCE["crowd_btn"].items()),
            }

            # ★ 判定：几何就地展开是否落在源站实测的 (68,452,204,256)
            page.locator("[data-director-character-option='geometry']").click(timeout=15000)
            page.wait_for_timeout(500)
            geo_state = page.evaluate(READ)
            out["④几何就地展开"] = geo_state
            page.screenshot(path=str(SHOTS / "858clone_geometry-inline.png"))
            gb = geo_state.get("几何展开") or {}
            out["④几何展开是否命中源站"] = {
                "期望": SOURCE["geometry_box"], "实测": gb,
                "命中": all(gb.get(k) == v for k, v in SOURCE["geometry_box"].items()),
                "首项": (geo_state.get("几何项") or [{}])[0],
            }

            # ★ 源站的 crowd / geometry 共用一个状态 ⟹ ⟹ 开一个关另一个
            page.locator("[data-director-character-option='crowd-3x3']").click(timeout=15000)
            page.wait_for_timeout(500)
            both = page.evaluate(READ)
            out["⑤开crowd后几何是否关闭"] = {
                "几何展开存在": both.get("几何展开") is not None,
                "对话框存在": both.get("对话框") is not None,
            }
            dl = both.get("对话框") or {}
            # ★ 同口径：挑 aria-label 为「添加群众阵列」的那一枚
            #   （clone 页面里还有别的 dialog，且有的含 ≥2 个 number 输入）
            out["⑤clone对话框逐段"] = [
                d for d in page.evaluate(READ_DIALOG)
                if d["aria"] == "添加群众阵列"
            ]
            out["⑤对话框是否命中源站"] = {
                "期望": SOURCE["crowd_dialog"], "实测": dl,
                "命中": all(dl.get(k) == v for k, v in SOURCE["crowd_dialog"].items()),
                "z": both.get("对话框z"),
                "z期望": SOURCE["dialog_z"],
                "背景": both.get("对话框背景"),
                "阴影": both.get("对话框阴影"),
                "标题字号": both.get("对话框标题字号"),
            }
            page.screenshot(path=str(SHOTS / "858clone_crowd-dialog.png"))

            # ★ 间距：填 1.55 ⟹ 读回 1.6（源站实测行为）
            page.locator("[data-director-crowd-input='spacing']").fill("1.55")
            page.wait_for_timeout(300)
            out["⑥间距填1.55后"] = page.evaluate(READ)["间距"]

            # ★ 再点一次「群众 (3x3)」⟹ 对话框关闭（源站 `if("crowd"===L)O(null)`）
            page.locator("[data-director-character-option='crowd-3x3']").click(timeout=15000)
            page.wait_for_timeout(400)
            out["⑦再点一次"] = page.evaluate(READ)["对话框"]

            # ★ 点外面 ⟹ 关闭
            page.locator("[data-director-character-option='crowd-3x3']").click(timeout=15000)
            page.wait_for_timeout(400)
            page.locator("[data-director-character-option='standard-male']").click(timeout=15000)
            page.wait_for_timeout(400)
            out["⑧点外面之后"] = page.evaluate(READ)["对话框"]

            # ★ 切回「场景」⟹ ⟹ 面板关闭、场景树回来
            page.locator("[data-director-rail-entry='scene']").click(timeout=15000)
            page.wait_for_timeout(600)
            back = page.evaluate(READ)
            out["⑨切回场景"] = {
                "面板可见": back.get("面板可见"),
                "场景树存在": back.get("场景树存在"),
                "模式": back.get("左侧面板模式"),
                "rail场景": back.get("rail场景"),
                "rail添加角色": back.get("rail添加角色"),
            }
            page.screenshot(path=str(SHOTS / "858clone_back-to-tree.png"))

            # ★ 再切一次 ⟹ ⟹ 场景树必须消失（D1 的核心判定）
            page.locator("[data-director-rail-entry='add-character']").click(timeout=15000)
            page.wait_for_timeout(500)
            again = page.evaluate(READ)
            out["⑩再切到添加角色"] = {
                "场景树存在": again.get("场景树存在"),
                "场景树按钮数": again.get("场景树按钮数"),
                "面板可见": again.get("面板可见"),
                "模式": again.get("左侧面板模式"),
                "rail添加角色": again.get("rail添加角色"),
                "rail场景": again.get("rail场景"),
            }
            page.close()

            # ══════════════════ 移动端 390×844 ══════════════════
            mpage = browser.new_page(viewport={"width": 390, "height": 844})
            open_desk(mpage)
            out["⑪移动端导演台"] = "OK"
            mpage.locator("[data-director-crowd-mobile-trigger]").click(timeout=15000)
            mpage.wait_for_timeout(700)
            mstate = mpage.evaluate(READ)
            out["⑫移动端点开对话框"] = {
                "对话框": mstate.get("对话框"),
                "对话框可见": mstate.get("对话框可见"),
                "移动端入口": mstate.get("移动端入口"),
                "面板可见": mstate.get("面板可见"),
            }
            mpage.screenshot(path=str(SHOTS / "858clone_mobile-crowd.png"))
            mpage.close()
        except Exception:
            out["★异常"] = traceback.format_exc()[-2500:]
        finally:
            browser.close()

    (RAW / "clone-858-panel.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(out, ensure_ascii=False, indent=2)[:6000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

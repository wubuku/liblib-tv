#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 846 源站**只读补测②**：脸部精修段六枚页签的**同口径**文字 span。

## 为什么还要再跑一趟

`source846_tabfont.py` 证明：源站「服装造型」段的**子页签行**里，每一枚按钮都有
**两个**带文字的 span（外层 grid wrapper ＋ 内层文字），且未选中的那两枚
**内层文字盒宽 0**（`grid-template-columns:0px`）⟹ ⟹
源站是「**每枚**都渲染 label，未选中时宽度为 0」⟹ ⟹ 视觉上只有图标。

★ 而 clone 的 `renderOutfitTabs` 是「**只有选中**的那枚渲染 label」⟹ ⟹
虽然**视觉**一致（未选中时宽度 0 ⟹ ⟹ 看不见），但**结构**不同 ⟹ ⟹
「label span 存在性」这一条在 clone 侧读不到 ⟹ ⟹ 若门禁要断言它 ⟹ ⟹ clone 得改。

★ 更要紧的：脸部精修段的六枚页签**不在 `nav` 里**（846 的探针只找到
  「服装造型」段的 nav）⟹ ⟹ 那六枚的 label span 到底是「每枚都渲染」还是
  「只有选中才渲染」⟹ ⟹ **还没测过** ⟹ ⟹ 这直接决定 clone 该怎么写。

★ 本趟专测：
  ① 脸部精修段（默认态）那六枚页签的**内层**文字 span 盒 + 计算样式
  ② 它们的 label span **存在性**（未选中的那五枚到底有没有 0 宽 label）
  ③ 与「服装造型」段子页签**逐字段**对照 ⟹ ⟹ 判断是不是同一个组件

★ **只读**：不点任何分段 ⟹ ⟹ 默认态就是脸部精修段 ⟹ ⟹ 顺便核对 ⚡44 积分不变。

★ 输出：`/tmp/liblib_source_846_facetabs.json`
"""
import json
import pathlib
import sys
import traceback

from playwright.sync_api import sync_playwright

URL = ("https://www.liblib.tv/canvas"
       "?spaceId=7709759&projectId=a860e1da8e9e4504bececda022386429")
COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_846_facetabs.json")

# ★ 脸部精修段的六枚页签：**用 aria-label 找**（★ 不靠 nav ⟹ ⟹ 因为它不在 nav 里）
MEASURE = """()=>{
  const box=(e)=>{const r=e.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)};};
  const txt=(e)=>(e.textContent||'').trim().replace(/\\s+/g,' ');
  const st=(e)=>{if(!e)return null;const cs=getComputedStyle(e);
    return {fontSize:cs.fontSize,fontWeight:cs.fontWeight,lineHeight:cs.lineHeight,
      color:cs.color,display:cs.display,gridTemplateColumns:cs.gridTemplateColumns,
      paddingLeft:cs.paddingLeft,width:cs.width,height:cs.height,
      borderBottomColor:cs.borderBottomColor,borderBottomWidth:cs.borderBottomWidth,
      backgroundColor:cs.backgroundColor,fontFamily:cs.fontFamily};};

  const out={};
  // ★ 脸部精修段的六枚页签：aria-label ∈ {皮肤,眉眼,鼻子,嘴唇,脸部,妆造}
  const NAMES=['皮肤','眉眼','鼻子','嘴唇','脸部','妆造'];
  const btns=[...document.querySelectorAll('button')].filter(b=>{
    const a=b.getAttribute('aria-label')||'';
    if(!NAMES.includes(a))return false;
    const r=b.getBoundingClientRect();
    return r.y>200&&r.y<300&&r.x>1200;});
  out['★命中数']=btns.length;
  out['★按钮']=btns.map(b=>{
    const spans=[...b.querySelectorAll('span')].filter(x=>txt(x));
    const inner=spans.length?spans[spans.length-1]:null;
    const outer=spans.length?spans[0]:null;
    // ★ 父容器（⟹ ⟹ 看它是 `justify-between` 还是 `gap-3` ⟹ ⟹ 判断是不是同一个组件）
    const par=b.parentElement;
    return {aria:b.getAttribute('aria-label')||'',text:txt(b),box:box(b),
      cls:String(b.getAttribute('class')||''),
      style:st(b),
      span数:spans.length,
      内层文字盒:inner?box(inner):null,内层文字样式:inner?st(inner):null,
      外层文字盒:outer?box(outer):null,外层文字样式:outer?st(outer):null,
      图标盒:(()=>{const s=b.querySelector('svg');return s?box(s):null;})(),
      父盒:par?box(par):null,
      父cls:par?String(par.getAttribute('class')||''):null,
      父样式:par?st(par):null};});
  return out;}"""


def read_credit(pg):
    return pg.evaluate("""()=>{
      const t=document.body.innerText||'';
      const m=t.match(/⚡\\s*(\\d+)/);
      return m?Number(m[1]):null;}""")


def main():
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
            pg.set_default_timeout(25_000)
            pg.goto(URL, wait_until="domcontentloaded", timeout=90_000)
            pg.wait_for_timeout(12_000)
            el = pg.query_selector("text=下次再说")
            if el:
                el.click()
                pg.wait_for_timeout(900)
            el = pg.query_selector('[data-sidebar-btn="character-library"]')
            if el:
                bb = el.bounding_box()
                if bb:
                    pg.mouse.click(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2)
            pg.wait_for_timeout(5000)
            tab = pg.query_selector("button:text-is('官方角色库')")
            if tab:
                bb = tab.bounding_box()
                if bb:
                    pg.mouse.click(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2)
                pg.wait_for_timeout(4000)

            ok_edit = False
            for e in pg.query_selector_all("span,div,button,a,p"):
                if (e.text_content() or "").strip() != "编辑角色":
                    continue
                bb = e.bounding_box()
                if not bb:
                    continue
                pg.mouse.click(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2)
                ok_edit = True
                break
            out["★是否点到编辑角色"] = ok_edit
            pg.wait_for_timeout(5000)

            before = read_credit(pg)
            reading = pg.evaluate(MEASURE)
            after = read_credit(pg)
            out["★读数"] = reading
            out["★积分前"] = before
            out["★积分后"] = after
            out["★积分是否变化"] = (before != after)
            if before != after:
                out["★★ 积分变了 ⟹ 立刻停"] = True
                raise SystemExit("积分变了")
    except SystemExit:
        pass
    except Exception:
        out["异常"] = traceback.format_exc()
    finally:
        OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", OUT)
        if out.get("异常"):
            print("异常：", out["异常"])
        r = out.get("★读数") or {}
        print("命中数 =", r.get("★命中数"))
        for b in (r.get("★按钮") or []):
            print("== %-6s box=%s span数=%s" % (b.get("aria"), b.get("box"), b.get("span数")))
            print("   内层文字盒=%s fs=%s lh=%s color=%s" %
                  (b.get("内层文字盒"),
                   (b.get("内层文字样式") or {}).get("fontSize"),
                   (b.get("内层文字样式") or {}).get("lineHeight"),
                   (b.get("内层文字样式") or {}).get("color")))
            print("   父盒=%s 父cls=%r 父jc=%s" %
                  (b.get("父盒"), (b.get("父cls") or "")[:70],
                   (b.get("父样式") or {}).get("justifyContent")))
            print("   borderBottom=%s" % (b.get("style") or {}).get("borderBottomColor"))


if __name__ == "__main__":
    sys.exit(main())

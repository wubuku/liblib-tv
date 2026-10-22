#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 846 源站**只读补测**：把「页签文字 span」的字号/网格口径一次钉死。

## 为什么必须补测（★ 846 实施中发现的口径问题）

846 的源站 raw 里，`子页签行.按钮[*].文字盒` 记的是**外层 grid span**
（`display:grid; grid-template-columns:28px; padding-left:4px` ⟹ 盒宽 32），
而 846 的 clone 探针记的是**最内层**那个带文字的 span（盒宽 28）⟹ ⟹
**两边记的不是同一层** ⟹ ⟹ 直接对拍必然报差异 ⟹ ⟹ 且**分不清是真差异还是口径差异**。

★ 所以本趟专测三件事：
  ① **最内层**文字 span 的盒 + 计算样式（fontSize / lineHeight / color / grid 列宽）
  ② 脸部精修段的六枚页签**同样**的最内层文字 span（⟹ ⟹ 确认「子页签」与
     「脸部页签」在源站**是不是同一个组件** ⟹ ⟹ 若是 ⟹ ⟹ clone 的 `.ce-tab`
     字号必须是**一个值** ⟹ ⟹ 若要改 ⟹ ⟹ 两段**一起**改）
  ③ 源站**未选中**页签的 label span：盒宽 0（`grid-template-columns:0px`）⟹ ⟹
     即源站**每一枚**页签都有 label span ⟹ ⟹ 未选中时宽度为 0 ⟹ ⟹ 视觉上只有图标

★ **只读**：只点左列的**分段** ⟹ ⟹ **不消耗** ⚡44 ⟹ ⟹ 点击前后都核对那一颗积分。

★ 输出：`/tmp/liblib_source_846_tabfont.json`
"""
import json
import pathlib
import sys
import traceback

from playwright.sync_api import sync_playwright

URL = ("https://www.liblib.tv/canvas"
       "?spaceId=7709759&projectId=a860e1da8e9e4504bececda022386429")
COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_846_tabfont.json")

# ★ 「服装造型」段在左列里的**前缀**（★ 源站按钮可能带角标 ⟹ ⟹ 不能精确匹配）
SEGMENT = "服装造型"

MEASURE = """()=>{
  const box=(e)=>{const r=e.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)};};
  const txt=(e)=>(e.textContent||'').trim().replace(/\\s+/g,' ');
  const st=(e)=>{if(!e)return null;const cs=getComputedStyle(e);
    return {fontSize:cs.fontSize,fontWeight:cs.fontWeight,lineHeight:cs.lineHeight,
      color:cs.color,display:cs.display,gridTemplateColumns:cs.gridTemplateColumns,
      paddingLeft:cs.paddingLeft,columnGap:cs.columnGap,rowGap:cs.rowGap,
      width:cs.width,height:cs.height,fontFamily:cs.fontFamily,
      borderBottomColor:cs.borderBottomColor,borderBottomWidth:cs.borderBottomWidth,
      borderBottomStyle:cs.borderBottomStyle,backgroundColor:cs.backgroundColor,
      borderTopWidth:cs.borderTopWidth,borderTopColor:cs.borderTopColor};};

  const aside=[...document.querySelectorAll('aside')].find(a=>{
    const r=a.getBoundingClientRect();return r.x>=1273&&Math.round(r.width)===288;});
  if(!aside)return {err:'右栏没找到'};
  const out={};

  // ★ nav（这一段的**子页签行**）
  const nav=aside.querySelector('nav');
  if(nav){
    out['子页签行']={box:box(nav),style:st(nav),
      按钮:[...nav.querySelectorAll('button')].map(b=>{
        const spans=[...b.querySelectorAll('span')].filter(x=>txt(x));
        const inner=spans.length?spans[spans.length-1]:null;
        const outer=spans.length?spans[0]:null;
        return {aria:b.getAttribute('aria-label')||'',text:txt(b),box:box(b),
          style:st(b),
          // ★★ **最内层**（⟹ ⟹ 与 846 clone 探针**同口径**）
          内层文字盒:inner?box(inner):null,内层文字样式:inner?st(inner):null,
          // ★ 外层（⟹ ⟹ 与 846 raw 里记的那层**同口径** ⟹ ⟹ 可交叉验算）
          外层文字盒:outer?box(outer):null,外层文字样式:outer?st(outer):null,
          span数:spans.length,
          图标盒:(()=>{const s=b.querySelector('svg');return s?box(s):null;})()};})};
  }

  // ★ 脸部精修段的六枚页签（⟹ ⟹ 藏在**别的** DOM 里 ⟹ ⟹ 全文找 nav）
  const navs=[...document.querySelectorAll('nav')].map(n=>({
    box:box(n),cls:String(n.getAttribute('class')||''),
    按钮:[...n.querySelectorAll('button')].map(b=>({
      aria:b.getAttribute('aria-label')||'',text:txt(b),box:box(b),
      style:st(b),
      内层文字盒:(()=>{const ss=[...b.querySelectorAll('span')].filter(x=>txt(x));
        const s=ss.length?ss[ss.length-1]:null;return s?box(s):null;})(),
      内层文字样式:(()=>{const ss=[...b.querySelectorAll('span')].filter(x=>txt(x));
        const s=ss.length?ss[ss.length-1]:null;return s?st(s):null;})(),
      span数:[...b.querySelectorAll('span')].filter(x=>txt(x)).length,
      图标盒:(()=>{const s=b.querySelector('svg');return s?box(s):null;})()}))}));
  out['全部nav']=navs;
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

            # ── 先读**脸部精修段**（默认态）⟹ ⟹ 它的六枚页签在哪个 nav 里 ──
            before = read_credit(pg)
            reading0 = pg.evaluate(MEASURE)
            out["★默认态_全部nav"] = reading0.get("全部nav")
            out["★默认态_子页签行"] = reading0.get("子页签行")
            after0 = read_credit(pg)
            out["★默认态_积分是否变化"] = (before != after0)
            if before != after0:
                out["★★ 积分变了 ⟹ 立刻停"] = True
                raise SystemExit("积分变了")

            # ── 再点「服装造型」分段 ⟹ ⟹ 读它的子页签 ──
            ok_seg = pg.evaluate("""(label)=>{
              const bs=[...document.querySelectorAll('button')].filter(e=>{
                const r=e.getBoundingClientRect();
                return r.x<700&&r.width>100;});
              const b=bs.find(e=>(e.textContent||'').trim().startsWith(label));
              if(!b)return false; b.click(); return true;}""", SEGMENT)
            pg.wait_for_timeout(3500)
            after = read_credit(pg)
            out["★分段_是否点到"] = ok_seg
            out["★分段_积分是否变化"] = (before != after)
            if before != after:
                out["★★ 积分变了 ⟹ 立刻停"] = True
                raise SystemExit("积分变了")

            reading = pg.evaluate(MEASURE)
            nav_btns = [b.get("aria") for b in
                        ((reading.get("子页签行") or {}).get("按钮") or [])]
            out["★读数_子页签"] = nav_btns
            out["★读数_是目标段"] = ("造型" in nav_btns)
            if "造型" not in nav_btns:
                out["★★ 读到的不是目标段 ⟹ 这份读数不可信 ⟹ 立刻停"] = True
                raise SystemExit("读到的不是目标段")
            out["★子页签行"] = reading.get("子页签行")
            out["★全部nav_服装段"] = reading.get("全部nav")
            out["★读完_积分是否变化"] = (read_credit(pg) != after)
    except SystemExit:
        pass
    except Exception:
        out["异常"] = traceback.format_exc()
    finally:
        OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", OUT)
        if out.get("异常"):
            print("异常：", out["异常"])
        for tag in ("★默认态_子页签行", "★子页签行"):
            t = out.get(tag) or {}
            print("── %s 按钮数=%d" % (tag, len(t.get("按钮") or [])))
            for b in (t.get("按钮") or []):
                print("   %-8s box=%s 内层文字盒=%s span数=%s" %
                      (b.get("aria"), b.get("box"), b.get("内层文字盒"), b.get("span数")))
                print("      内层文字样式: fs=%s lh=%s color=%s display=%s grid=%s" %
                      ((b.get("内层文字样式") or {}).get("fontSize"),
                       (b.get("内层文字样式") or {}).get("lineHeight"),
                       (b.get("内层文字样式") or {}).get("color"),
                       (b.get("内层文字样式") or {}).get("display"),
                       (b.get("内层文字样式") or {}).get("gridTemplateColumns")))
        for tag in ("★默认态_全部nav", "★全部nav_服装段"):
            for n in (out.get(tag) or []):
                print("── %s nav box=%s cls=%r 按钮=%s" %
                      (tag, n.get("box"), (n.get("cls") or "")[:60],
                       [(b.get("aria"), b.get("box")) for b in (n.get("按钮") or [])]))


if __name__ == "__main__":
    sys.exit(main())

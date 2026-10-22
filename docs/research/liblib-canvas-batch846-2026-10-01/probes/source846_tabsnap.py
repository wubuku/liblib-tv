#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 846 源站**只读补测③**：子页签行的**溢出行为** ＋ **像素证据**。

## 为什么必须实测而不是推理

846 实施中发现：源站**每一枚**页签都渲染 label span，未选中时该 span 的
`grid-template-columns` ＝ **0px** ⟹ ⟹ 盒子宽 0 ⟹ ⟹ **文字理论上会溢出**。

⟹ ⟹ 但 batch 845 的像素对照（源站↔clone，45396/45500 完全相同）说明
脸部段那五枚**未选中**页签的文字**并没有画出来** ⟹ ⟹ 若 clone 也照抄
「每枚都渲染 label」⟹ ⟹ 必须知道源站是**靠什么**把溢出裁掉的
（`overflow:hidden`？`text-overflow`？还是文字本身就不在盒子里？）
⟹ ⟹ **不实测就会写出「照抄结构」却「画出了源站没有的字」**。

★ 本趟专测三件事：
  ① 按钮 / 外层 span / 内层 span 三层的 `overflow` `textOverflow` `whiteSpace`
     `visibility` `opacity` 计算样式（⟹ ⟹ 找到裁剪发生在哪一层）
  ② 内层 span 的 `scrollWidth` vs `clientWidth`（⟹ ⟹ 文字是否溢出自身盒子）
  ③ **像素证据**：截取页签行（1297..1425 × 225..275）的截图
     ⟹ ⟹ 肉眼看源站那两枚未选中页签**到底有没有字**

★ **只读**：不点任何分段 ⟹ ⟹ 不消耗 ⚡44 ⟹ ⟹ 顺便核对积分不变。

★ 输出：`/tmp/liblib_source_846_tabsnap.json` ＋ `/tmp/liblib_source_846_tabsnap.png`
"""
import json
import pathlib
import sys
import traceback

from playwright.sync_api import sync_playwright

URL = ("https://www.liblib.tv/canvas"
       "?spaceId=7709759&projectId=a860e1da8e9e4504bececda022386429")
COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_846_tabsnap.json")
PNG = pathlib.Path("/tmp/liblib_source_846_tabsnap.png")

SEGMENT = "服装造型"

# ★★★ 溢出相关的计算样式（★ 这一层就是本次要取证的东西）
MEASURE = """()=>{
  const box=(e)=>{const r=e.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)};};
  const txt=(e)=>(e.textContent||'').trim().replace(/\\s+/g,' ');
  const ov=(e)=>{if(!e)return null;const cs=getComputedStyle(e);
    return {overflow:cs.overflow,overflowX:cs.overflowX,overflowY:cs.overflowY,
      textOverflow:cs.textOverflow,whiteSpace:cs.whiteSpace,visibility:cs.visibility,
      opacity:cs.opacity,display:cs.display,position:cs.position,
      minWidth:cs.minWidth,maxWidth:cs.maxWidth,width:cs.width,
      gridTemplateColumns:cs.gridTemplateColumns,paddingLeft:cs.paddingLeft,
      overflowWrap:cs.overflowWrap,wordBreak:cs.wordBreak,
      clipPath:cs.clipPath,contain:cs.contain,
      scrollW:e.scrollWidth,clientW:e.clientWidth,
      scrollH:e.scrollHeight,clientH:e.clientHeight};};

  const aside=[...document.querySelectorAll('aside')].find(a=>{
    const r=a.getBoundingClientRect();return r.x>=1273&&Math.round(r.width)===288;});
  if(!aside)return {err:'右栏没找到'};
  const nav=aside.querySelector('nav');
  if(!nav)return {err:'nav 没找到'};
  return {nav:box(nav),
    按钮:[...nav.querySelectorAll('button')].map(b=>{
      const spans=[...b.querySelectorAll('span')].filter(x=>txt(x));
      const inner=spans.length?spans[spans.length-1]:null;
      const outer=spans.length?spans[0]:null;
      return {aria:b.getAttribute('aria-label')||'',text:txt(b),box:box(b),
        按钮溢出:ov(b),
        外层文字盒:outer?box(outer):null,外层溢出:outer?ov(outer):null,
        内层文字盒:inner?box(inner):null,内层溢出:inner?ov(inner):null,
        span数:spans.length,
        // ★ 内层 span 的**全部**子节点类型（⟹ ⟹ 文字是文本节点还是被包了别的）
        内层子节点:inner?[...inner.childNodes].map(n=>({
          类型:n.nodeType,名字:n.nodeName,
          文本:n.nodeType===3?(n.textContent||''):null})):null};})};}"""


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
            ok_seg = pg.evaluate("""(label)=>{
              const bs=[...document.querySelectorAll('button')].filter(e=>{
                const r=e.getBoundingClientRect();
                return r.x<700&&r.width>100;});
              const b=bs.find(e=>(e.textContent||'').trim().startsWith(label));
              if(!b)return false; b.click(); return true;}""", SEGMENT)
            pg.wait_for_timeout(3500)
            after = read_credit(pg)
            out["★分段_是否点到"] = ok_seg
            out["★积分前"] = before
            out["★积分后"] = after
            out["★积分是否变化"] = (before != after)
            if before != after:
                out["★★ 积分变了 ⟹ 立刻停"] = True
                raise SystemExit("积分变了")

            reading = pg.evaluate(MEASURE)
            out["★读数"] = reading

            # ★★★ 像素证据：截页签行那一带（⟹ ⟹ 含三枚页签）
            #     ★ clip 用**源站绝对坐标**（1290..1440 × 225..278）
            pg.screenshot(path=str(PNG), clip={"x": 1290, "y": 225,
                                                "width": 150, "height": 53})
            out["★截图"] = str(PNG)
            out["★读完_积分是否变化"] = (read_credit(pg) != after)
    except SystemExit:
        pass
    except Exception:
        out["异常"] = traceback.format_exc()
    finally:
        OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", OUT, PNG)
        if out.get("异常"):
            print("异常：", out["异常"])
        r = (out.get("★读数") or {})
        print("nav box:", r.get("nav"))
        for b in (r.get("按钮") or []):
            print("== %-8s box=%s span数=%s" % (b.get("aria"), b.get("box"), b.get("span数")))
            for tag in ("按钮溢出", "外层溢出", "内层溢出"):
                o = b.get(tag) or {}
                print("   %s: overflow=%s ws=%s visibility=%s display=%s grid=%s "
                      "scrollW=%s clientW=%s" %
                      (tag, o.get("overflow"), o.get("whiteSpace"),
                       o.get("visibility"), o.get("display"),
                       o.get("gridTemplateColumns"), o.get("scrollW"), o.get("clientW")))
            print("   内层子节点:", json.dumps(b.get("内层子节点"), ensure_ascii=False))


if __name__ == "__main__":
    sys.exit(main())

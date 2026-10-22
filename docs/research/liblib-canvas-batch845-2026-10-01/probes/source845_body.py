#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 845 源站探针（**只读**）：左列第三段「身材塑形」的 18 条滑杆。

## 为什么必须再跑一趟

batch 841 的 raw 里，右栏子树**被探针的 `y<=833` 截断**了 ⟹ ⟹
只留下**前 8 条**滑杆的盒 ⟹ ⟹ 后面 10 条**只**在 `inputs` 列表里有 aria 与 y
⟹ ⟹ 「**哪几条带「i」标记**」在视口外那段**完全没测过**。

★ 本趟**不按 y 过滤** ⟹ ⟹ 直接从 DOM 里读**全部** range input
  ⟹ ⟹ 18 条的名字／初值／min-max-step／「i」标记全部拿到。

## ★ 这一段的结构（841 raw 已机器提取）

    这一段**没有标题行** ⟹ ⟹ 右栏**第一层就是滚动区**（`pt-3`）
    ⟹ ⟹ 内容起点比「脸部精修」段**高 48px**
    每条滑杆＝ LABEL 240×55
      ├ 标签行 240×22（名字 ＋ 可选的「i」＋ 右端数值 7×16）
      └ 轨道 240×12（= 标签 +36）
    标签行 top = 82 + 74.8·i（★ 与页签滑杆**同一个步进**）

★ **只读**：只点左列的**分段** ⟹ ⟹ **不消耗** ⚡44
  ⟹ ⟹ 每次点击前后都核对那一颗积分（x 540..575、y 855..885）。

★ 输出：`/tmp/liblib_source_845_body.json`
"""
import json
import pathlib
import sys
import traceback

from playwright.sync_api import sync_playwright

URL = ("https://www.liblib.tv/canvas"
       "?spaceId=7709759&projectId=a860e1da8e9e4504bececda022386429")
COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_845_body.json")

SEGMENT = "身材塑形"

MEASURE = """()=>{
  const box=(e)=>{const r=e.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)};};
  const txt=(e)=>(e.textContent||'').trim().replace(/\\s+/g,' ');
  const cls=(e)=>String((e&&e.getAttribute)?(e.getAttribute('class')||''):'').slice(0,150);
  const st=(e)=>{if(!e)return null;const cs=getComputedStyle(e);
    return {fontSize:cs.fontSize,fontWeight:cs.fontWeight,lineHeight:cs.lineHeight,
      color:cs.color,backgroundColor:cs.backgroundColor,borderRadius:cs.borderRadius,
      borderTopWidth:cs.borderTopWidth,borderTopColor:cs.borderTopColor,
      paddingLeft:cs.paddingLeft,paddingTop:cs.paddingTop,gap:cs.gap,
      display:cs.display,alignItems:cs.alignItems,justifyContent:cs.justifyContent,
      fontFamily:cs.fontFamily,appearance:cs.appearance};};

  const aside=[...document.querySelectorAll('aside')].find(a=>{
    const r=a.getBoundingClientRect();return r.x>=1273&&Math.round(r.width)===288;});
  if(!aside)return {err:'右栏没找到'};
  const out={};
  out['右栏盒']=box(aside);

  // ★ 右栏**第一层**（★ 这一段没有标题行 ⟹ ⟹ 第一层就是滚动区）
  const kid=aside.firstElementChild;
  out['右栏第一层']=kid?{tag:kid.tagName,cls:cls(kid),box:box(kid),style:st(kid),
    子节点数:kid.children.length,
    滚动高:kid.scrollHeight, 客户端高:kid.clientHeight,
    内容盒:(()=>{const c=kid.firstElementChild;
      return c?{tag:c.tagName,cls:cls(c),box:box(c)}:null;})(),
    头行:(kid.firstElementChild&&kid.firstElementChild.tagName==='DIV'
      &&Math.round(kid.firstElementChild.getBoundingClientRect().height)===40)
      ?{box:box(kid.firstElementChild)}:null}:null;

  // ★ **全部** range input（★ 不按 y 过滤 ⟹ ⟹ 视口外的那 10 条也读得到）
  const ranges=[...aside.querySelectorAll('input[type="range"]')];
  out['滑杆']=ranges.map(r=>{
    const wrap=r.parentElement;                 // 轨道容器（240×25）
    const label=wrap?wrap.parentElement:null;  // LABEL（240×55）
    const row=label?label.firstElementChild:null;// 标签行（240×22）
    const nameEl=row&&row.firstElementChild?row.firstElementChild.querySelector('span'):null;
    const info=row?row.querySelector('[role="img"]'):null;
    const val=row?row.lastElementChild:null;
    const dot=wrap?wrap.querySelector('span'):null;
    return {aria:r.getAttribute('aria-label')||'',
      value:r.value, min:r.getAttribute('min'), max:r.getAttribute('max'),
      step:r.getAttribute('step'),
      标签盒:label?box(label):null,
      标签行盒:row?box(row):null,
      名字盒:nameEl?box(nameEl):null,
      名字文字:nameEl?txt(nameEl):null,
      有i:!!info, i盒:info?box(info):null,
      i样式:info?st(info):null,
      数值盒:val?box(val):null,
      数值文字:val?txt(val):null,
      轨道盒:wrap?box(wrap):null,
      输入盒:box(r),
      缩略点盒:dot?box(dot):null,
      名字样式:nameEl?st(nameEl):null,
      数值样式:val?st(val):null,
      输入样式:st(r),
      标签行样式:row?st(row):null};});

  // ★ 右栏可见子树（兜底：结构上还有什么没被上面读到）
  out['右栏可见子树']=[...aside.querySelectorAll('*')].filter(e=>{
    const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0&&r.height<200;}).slice(0,80).map(e=>({
    tag:e.tagName,role:e.getAttribute('role')||'',text:txt(e).slice(0,26),
    aria:e.getAttribute('aria-label')||'',box:box(e),cls:cls(e)}));

  // ★ 积分（底栏那颗）
  const hits=[];
  for(const e of document.querySelectorAll('span,div,b')){
    const t=txt(e); if(!/^\\d+$/.test(t)||e.children.length!==0)continue;
    const r=e.getBoundingClientRect(); if(r.width<=0||r.height<=0)continue;
    const x=Math.round(r.x), y=Math.round(r.y);
    if(x>=540&&x<=575&&y>=855&&y<=885)hits.push({t,x,y});}
  out['积分']=hits;
  return out;}"""


def read_credit(page):
    """★ 只读**那一颗**积分（x 540..575、y 855..885）。"""
    return page.evaluate("""()=>{
      const hits=[];
      for(const e of document.querySelectorAll('span,div,b')){
        const t=(e.textContent||'').trim();
        if(!/^\\d+$/.test(t)||e.children.length!==0)continue;
        const r=e.getBoundingClientRect();
        if(r.width<=0||r.height<=0)continue;
        const x=Math.round(r.x), y=Math.round(r.y);
        if(x>=540&&x<=575&&y>=855&&y<=885)hits.push({t,x,y});}
      return hits;}""")


def main():
    log = {}
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
            log["★是否点到编辑角色"] = ok_edit
            pg.wait_for_timeout(5000)

            before = read_credit(pg)
            # ★★ **定位器不能用「精确文本」**：源站的分段按钮**带角标**
            #   （「身材塑形**限免**」）⟹ ⟹ `textContent === "身材塑形"` **匹配不到**
            #   ⟹ ⟹ 上一趟就**点空了** ⟹ ⟹ 读到的是**皮肤页**的 6 条滑杆
            #   ⟹ ⟹ 改用**前缀匹配**（且限定在**左列**的按钮里）。
            ok_seg = pg.evaluate("""(label)=>{
              const bs=[...document.querySelectorAll('button')].filter(e=>{
                const r=e.getBoundingClientRect();
                return r.x<700&&r.width>100;});
              const b=bs.find(e=>(e.textContent||'').trim().startsWith(label));
              if(!b)return false; b.click(); return true;}""", SEGMENT)
            pg.wait_for_timeout(3000)
            after = read_credit(pg)
            log["★分段_是否点到"] = ok_seg
            log["★分段_积分是否变化"] = (before != after)
            if before != after:
                log["★★ 积分变了 ⟹ 立刻停"] = True
                raise SystemExit("积分变了")

            reading = pg.evaluate(MEASURE)
            # ★★ **自证**：读到的必须是**目标段**（第一条滑杆是「丰胸」）
            #   ⟹ ⟹ 若是别的段 ⟹ ⟹ 这份读数**不能**当源站 raw 入库
            first_aria = ((reading.get("滑杆") or [{}])[0] or {}).get("aria")
            log["★读数_第一条滑杆"] = first_aria
            log["★读数_是目标段"] = (first_aria == "丰胸")
            if first_aria != "丰胸":
                log["★★ 读到的**不是**目标段 ⟹ 这份读数不可信 ⟹ 立刻停"] = True
                raise SystemExit("读到的不是目标段")
            log["★读数"] = reading
            log["★读完_积分是否变化"] = (read_credit(pg) != after)
    except SystemExit:
        pass
    except Exception:
        log["异常"] = traceback.format_exc()
    finally:
        OUT.write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", OUT)
        for k, v in log.items():
            if k.startswith("★") and k != "★读数":
                print("  %-24s %s" % (k, json.dumps(v, ensure_ascii=False)[:90]))
        r = log.get("★读数") or {}
        sl = r.get("滑杆") or []
        print("  滑杆数:", len(sl))
        for c in sl:
            print("   - %-12s 值=%-4s min=%-4s max=%-4s step=%-4s 有i=%-5s 标签y=%s"
                  % (c.get("aria"), c.get("value"), c.get("min"), c.get("max"),
                     c.get("step"), c.get("有i"),
                     (c.get("标签行盒") or {}).get("y")))
        if log.get("异常"):
            print("异常：", log["异常"])


if __name__ == "__main__":
    sys.exit(main())

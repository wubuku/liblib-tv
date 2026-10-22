#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 847 源站探针（**只读**）：左列第五段「音色音调」的完整结构。

## 为什么必须再跑一趟

batch 841 的 raw 里，右栏子树**被探针的 `y<=833` 截断**了 ⟹ ⟹
这一段的**下半截**（第 10 条音色之后）**根本没进 raw** ⟹ ⟹
841 里看到的「20 条音色」**是当时读到的、不是完整清单** ⟹ ⟹ 不能直接照抄。

★ 本趟**不按 y 过滤** ⟹ ⟹ 直接从 DOM 里读**全部**元素 ⟹ ⟹ 清单与几何一次拿全。

## 这一段的结构（★ 与前四段**都不同**）

    右栏（ASIDE 288 宽）
      └ 内层 DIV `flex min-h-0 flex-1 flex-col px-6`（288 宽 @1273）
        ├ 标题行 DIV `... items-center gap-5 border-b`（240 宽 @1297）
        │   ├ SPAN `inline-flex h-full`（70 宽）→ BUTTON（70 宽）＋ icon 18 ＋ 文字 span
        │   ├ SPAN `inline-flex h-full`（24 宽）→ BUTTON（24 宽）＋ icon
        │   └ SPAN `inline-flex h-full`（24 宽）→ BUTTON（24 宽）＋ icon
        ├ 工具行 DIV `my-2 flex h-8 w-full shrink-0 items-center gap-[2px]`（240×32 @279）
        │   └ 两枚 BUTTON（32×32：第一个带 icon，第二个是 relative 容器）
        └ 滚动区 DIV `min-h-0 flex-1 space-y-2 overflow-y-auto pb-20`（240×514 @319）
            └ N 条音色卡 DIV `flex h-12 w-full items-center rounded-xl border p-1`（240×48）
                ├ BUTTON `flex min-w-0 flex-1 items-center text-left`（198×40）
                │   ├ SPAN `flex size-10 ... rounded-lg`（40×40，图标区）
                │   └ SPAN `min-w-0 flex-1 px-2`（158×36）
                │       ├ SPAN `block truncate text-xs leading-5`（名字，20 高）
                │       └ SPAN `text-fg-muted block truncate text-[10px] leading-4`（副标，16 高）
                └ BUTTON `hover:bg-canvas-controls-hover flex size-8`（32×32，播放按钮）

★ **只读**：只点左列的**分段** ⟹ ⟹ **不消耗** ⚡44 ⟹ ⟹ 点击前后都核对那一颗积分。

★ 输出：`/tmp/liblib_source_847_voice.json`
"""
import json
import pathlib
import sys
import traceback

from playwright.sync_api import sync_playwright

URL = ("https://www.liblib.tv/canvas"
       "?spaceId=7709759&projectId=a860e1da8e9e4504bececda022386429")
COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_847_voice.json")

SEGMENT = "音色音调"

MEASURE = """()=>{
  const box=(e)=>{const r=e.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)};};
  const txt=(e)=>(e.textContent||'').trim().replace(/\\s+/g,' ');
  const cls=(e)=>String((e&&e.getAttribute)?(e.getAttribute('class')||''):'');
  const st=(e)=>{if(!e)return null;const cs=getComputedStyle(e);
    return {fontSize:cs.fontSize,fontWeight:cs.fontWeight,lineHeight:cs.lineHeight,
      color:cs.color,backgroundColor:cs.backgroundColor,borderRadius:cs.borderRadius,
      borderTopWidth:cs.borderTopWidth,borderTopColor:cs.borderTopColor,
      borderBottomWidth:cs.borderBottomWidth,borderBottomColor:cs.borderBottomColor,
      paddingLeft:cs.paddingLeft,paddingTop:cs.paddingTop,paddingRight:cs.paddingRight,
      paddingBottom:cs.paddingBottom,gap:cs.gap,rowGap:cs.rowGap,columnGap:cs.columnGap,
      display:cs.display,alignItems:cs.alignItems,justifyContent:cs.justifyContent,
      gridTemplateColumns:cs.gridTemplateColumns,fontFamily:cs.fontFamily,
      appearance:cs.appearance,objectFit:cs.objectFit,overflow:cs.overflow,
      boxShadow:cs.boxShadow,outlineWidth:cs.outlineWidth,outlineColor:cs.outlineColor,
      outlineStyle:cs.outlineStyle,filter:cs.filter,opacity:cs.opacity};};

  const aside=[...document.querySelectorAll('aside')].find(a=>{
    const r=a.getBoundingClientRect();return r.x>=1273&&Math.round(r.width)===288;});
  if(!aside)return {err:'右栏没找到'};
  const out={};
  out['右栏盒']=box(aside);

  // ★ 内层（★ 这一段的内层带 `px-6` ⟹ ⟹ 与前几段不同）
  const inner=aside.firstElementChild;
  out['右栏内层']=inner?{tag:inner.tagName,cls:cls(inner),box:box(inner),
    子节点数:inner.children.length,
    子节点:[...inner.children].map(e=>({tag:e.tagName,cls:cls(e),box:box(e),
      子节点数:e.children.length,滚动高:e.scrollHeight,客户端高:e.clientHeight}))}:null;

  // ── 标题行（★ 这一段**有**，且是 `gap-5`） ───────────────────────────
  const head=[...aside.querySelectorAll('*')].find(e=>{
    const c=cls(e);
    return /h-10/.test(c)&&/border-b/.test(c)&&e.getBoundingClientRect().height<=40
      &&e.getBoundingClientRect().x>1273;});
  if(head){
    out['标题行']={box:box(head),cls:cls(head),style:st(head),
      子节点:[...head.children].map(e=>({tag:e.tagName,cls:cls(e),box:box(e),
        子节点数:e.children.length,
        孙节点:[...e.children].map(x=>({tag:x.tagName,cls:cls(x),box:box(x),
          text:txt(x),style:st(x),
          内层文字盒:(()=>{const ss=[...x.querySelectorAll('span')].filter(q=>txt(q));
            const s=ss.length?ss[ss.length-1]:null;return s?box(s):null;})(),
          内层文字样式:(()=>{const ss=[...x.querySelectorAll('span')].filter(q=>txt(q));
            const s=ss.length?ss[ss.length-1]:null;return s?st(s):null;})()}))}))};
  }

  // ── 工具行（32 高 ＋ 两枚 32×32 的按钮） ─────────────────────────────
  const toolRow=[...aside.querySelectorAll('*')].find(e=>{
    const r=e.getBoundingClientRect();
    return cls(e).includes('my-2')&&r.width>200&&r.height<=40&&r.x>1273;});
  if(toolRow){
    out['工具行']={box:box(toolRow),cls:cls(toolRow),style:st(toolRow),
      按钮:[...toolRow.querySelectorAll('button')].map(b=>({
        cls:cls(b),box:box(b),style:st(b),
        图标盒:(()=>{const s=b.querySelector('svg');return s?box(s):null;})()}))};
  }

  // ── 滚动区 ─────────────────────────────────────────────────────────
  const scroll=[...aside.querySelectorAll('*')].find(e=>{
    const c=cls(e);
    return /overflow-y-auto/.test(c)&&e.getBoundingClientRect().width<=260
      &&e.getBoundingClientRect().x>1273;});
  if(scroll){
    out['滚动区']={box:box(scroll),cls:cls(scroll),style:st(scroll),
      滚动高:scroll.scrollHeight,客户端高:scroll.clientHeight,子节点数:scroll.children.length};

    // ★★ 音色卡（★ 按**盒高 48** 认 ⟹ ⟹ 不靠猜类名）
    const cards=[...scroll.children].filter(e=>{
      const r=e.getBoundingClientRect();return Math.round(r.height)===48;});
    out['音色卡数']=cards.length;
    out['音色卡']=cards.map(card=>{
      const btn=card.querySelector('button');
      // ★ 名字 ＝ 那个 20 高的 span；副标 ＝ 那个 16 高的 span
      const spans=[...card.querySelectorAll('span')].filter(s=>txt(s));
      const nameSpan=spans.find(s=>Math.round(s.getBoundingClientRect().height)===20)||null;
      const subSpan=spans.find(s=>Math.round(s.getBoundingClientRect().height)===16)||null;
      const iconWrap=card.querySelector('span.rounded-lg, span[class*="rounded-lg"]');
      const playBtn=[...card.querySelectorAll('button')].find(b=>{
        const r=b.getBoundingClientRect();return Math.round(r.width)===32;});
      return {名字: nameSpan?txt(nameSpan):null,
        名字盒: nameSpan?box(nameSpan):null, 名字样式: nameSpan?st(nameSpan):null,
        副标: subSpan?txt(subSpan):null,
        副标盒: subSpan?box(subSpan):null, 副标样式: subSpan?st(subSpan):null,
        卡盒: box(card), 卡样式: st(card), 卡cls: cls(card),
        图标区盒: iconWrap?box(iconWrap):null, 图标区样式: iconWrap?st(iconWrap):null,
        图标盒: (()=>{const s=iconWrap?iconWrap.querySelector('svg'):null;return s?box(s):null;})(),
        主按钮盒: btn?box(btn):null,
        播放按钮盒: playBtn?box(playBtn):null, 播放按钮样式: playBtn?st(playBtn):null,
        播放图标盒: (()=>{const s=playBtn?playBtn.querySelector('svg'):null;return s?box(s):null;})()};
    });
  }

  // ★ 整页里**带文字**的叶子（⟹ ⟹ 用来核对「音色库」那个标题与全部文案）
  out['右栏所有带文字的叶子']=[...aside.querySelectorAll('*')]
    .filter(e=>e.children.length===0&&txt(e))
    .map(e=>({tag:e.tagName,text:txt(e),box:box(e),style:st(e)}));
  return out;}"""


def read_credit(pg):
    return pg.evaluate("""()=>{
      const t=document.body.innerText||'';
      const m=t.match(/⚡\\s*(\\d+)/);
      return m?Number(m[1]):null;}""")


def txt_nonempty(s) -> bool:
    return bool(s and str(s).strip())


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
            # ★★ **前缀匹配**（★ 源站的按钮可能带角标 ⟹ ⟹ 精确文本会**点空气**）
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
            # ★★ **自证**：读到的必须是**目标段**（标题行里有「音色库」）
            #   ⟹ ⟹ 标题行那层的结构是「子节点 → 孙节点 → text」⟹ ⟹ 取最里层的 text
            head_txt = " ".join(
                str(sn.get("text") or "")
                for c in ((reading.get("标题行") or {}).get("子节点") or [])
                for sn in (c.get("孙节点") or [])
                if txt_nonempty(sn.get("text")))
            out["★读数_标题行文本"] = head_txt
            out["★读数_是目标段"] = ("音色库" in head_txt)
            if "音色库" not in head_txt:
                out["★★ 读到的不是目标段 ⟹ 这份读数不可信 ⟹ 立刻停"] = True
                raise SystemExit("读到的不是目标段")
            out["★读数"] = reading
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
        r = out.get("★读数") or {}
        print("★是目标段 =", out.get("★读数_是目标段"),
              "｜积分变化 =", out.get("★分段_积分是否变化"))
        print("右栏盒:", r.get("右栏盒"))
        print("标题行:", (r.get("标题行") or {}).get("box"),
              (r.get("标题行") or {}).get("cls"))
        print("工具行:", (r.get("工具行") or {}).get("box"))
        print("滚动区:", (r.get("滚动区") or {}).get("box"),
              "滚动高 =", (r.get("滚动区") or {}).get("滚动高"))
        print("音色卡数:", r.get("音色卡数"))
        for c in (r.get("音色卡") or [])[:8]:
            print("   %-16s %-22s 卡=%s 名字盒=%s 副标盒=%s"
                  % (c.get("名字"), c.get("副标"), c.get("卡盒"),
                     c.get("名字盒"), c.get("副标盒")))


if __name__ == "__main__":
    sys.exit(main())

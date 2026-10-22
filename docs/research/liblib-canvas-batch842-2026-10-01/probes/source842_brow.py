#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 842 源站探针（**只读**）：补齐「眉眼」页与「妆造」页的**计算样式**。

## 为什么还要再跑一趟

batch 841 的 raw 够用，但**不够**做像素级复刻：

- 眉眼页的 `right` 子树被探针的 `y<=833` 过滤**截断**（只留首屏 7 条滑杆），
  ⟹ 卡片/H3 的**计算样式**（颜色、圆角、背景、字号）**根本没采到**；
- `leaves`／`inputs` 不限 y ⟹ ⟹ **30 条滑杆的四件套几何**已经够了
  （上一批 README 写的「32 条」是把「角色名称」输入框和 1×1 复选框也算进去了
  ⟹ ⟹ **实际是 30 条** ⟹ ⟹ 本批更正）。

⟹ 本趟**只**补「计算样式 + DOM 片段 + 妆造页的 chip 与卡片」。

★ **只读**：只点右栏页签（眉眼／妆造）⟹ **不点**「确认生成／保存／智能调整」
  ⟹ ⟹ **不消耗** ⚡44 ⟹ ⟹ 每次点击前后都核对那一颗积分（x 540..575、y 855..885）。

★ 输出：`/tmp/liblib_source_842_brow.json`
"""
import json
import pathlib
import sys
import traceback

from playwright.sync_api import sync_playwright

URL = ("https://www.liblib.tv/canvas"
       "?spaceId=7709759&projectId=a860e1da8e9e4504bececda022386429")
COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_842_brow.json")

# ★ 计算样式：只取**排版与外观**相关的属性（不取颜色以外的花哨属性）
#   ★ 这份列表要**内联进 JS** —— `page.evaluate` 在**页面上下文**里跑，
#   Python 的变量在里面**看不见**（第一版就栽在这：STYLE_KEYS is not defined）。
STYLE_KEYS = [
    "display", "position", "width", "height", "fontSize", "fontWeight",
    "lineHeight", "letterSpacing", "color", "backgroundColor", "borderRadius",
    "borderTopWidth", "borderTopColor", "paddingTop", "paddingLeft", "gap",
    "overflow", "objectFit", "textAlign", "whiteSpace", "justifyContent",
    "alignItems", "flexDirection", "marginBottom", "marginTop", "boxSizing",
]

MEASURE = """()=>{
  const STYLE_KEYS = __STYLE_KEYS__;
  const box=(e)=>{const r=e.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)};};
  const txt=(e)=>(e.textContent||'').trim().replace(/\\s+/g,' ');
  const st=(e)=>{const cs=getComputedStyle(e);const o={};
    for(const k of STYLE_KEYS)o[k]=cs[k];return o;};
  const html=(e,n)=>(e.outerHTML||'').slice(0,n);
  const vis=(e)=>{const r=e.getBoundingClientRect();
    if(r.width<=0||r.height<=0)return false;
    const cs=getComputedStyle(e);
    return cs.display!=='none'&&cs.visibility!=='hidden';};

  // ★ 找模态：沿用 841 那套锚点链（保存 ↔ 脸部精修）
  const leafByText=(t)=>{for(const e of document.querySelectorAll('span,div,button,a,p,label')){
    if(e.children.length===0&&txt(e)===t)return e;}return null;};
  const save=leafByText('保存'), seg=leafByText('脸部精修');
  if(!save||!seg)return {err:'锚点没找到'};
  const chain=(e)=>{const s=new Set();for(let n=e;n;n=n.parentElement)s.add(n);return s;};
  const cs_=chain(seg);let modal=null;
  for(let n=save;n;n=n.parentElement){if(cs_.has(n)){modal=n;break;}}
  if(!modal)return {err:'模态容器没找到'};

  const out={};
  out['★模态盒']=box(modal);

  // ★ 右栏：x>=1273 的那个 288 宽的 ASIDE
  const aside=[...modal.querySelectorAll('aside')].find(a=>a.getBoundingClientRect().x>=1273);
  if(!aside)return {err:'右栏没找到'};
  out['★右栏盒']=box(aside);
  // ★ 滚动容器：aside 里那个 overflow-y:auto 的盒子
  const scroller=[...aside.querySelectorAll('*')].find(e=>{
    const cs=getComputedStyle(e);
    return cs.overflowY==='auto'||cs.overflowY==='scroll';});
  out['★滚动容器']=scroller?{box:box(scroller),scrollTop:scroller.scrollTop,
    scrollHeight:scroller.scrollHeight,cls:(scroller.className||'').slice(0,90)}:null;

  // ★ 标题（H3/H4）：文字 ＋ 计算样式 ＋ DOM 片段
  out['★标题']=[...aside.querySelectorAll('h3,h4')].filter(vis).map(e=>({
    tag:e.tagName,text:txt(e),box:box(e),style:st(e),
    cls:(e.className||'').slice(0,110),html:html(e,400)}));

  // ★ 预设卡：76×96 的按钮 ⟹ 取**前两张**（第一张无图 ⟹ 第二张有图）
  const cards=[...aside.querySelectorAll('button')].filter(e=>{
    const r=e.getBoundingClientRect();return Math.round(r.width)===76&&Math.round(r.height)===96;});
  out['★卡片数']=cards.length;
  out['★卡片']=cards.slice(0,3).map(b=>{
    const kids=[...b.children];
    const img=b.querySelector('img');
    const name=[...b.querySelectorAll('span')].find(s=>
      s.children.length===0&&txt(s)&&s.getBoundingClientRect().height===16);
    return {aria:b.getAttribute('aria-label')||'',box:box(b),style:st(b),
      cls:(b.className||'').slice(0,110),html:html(b,700),
      子元素数:kids.length,
      首个子:kids[0]?{tag:kids[0].tagName,box:box(kids[0]),style:st(kids[0]),
        cls:(kids[0].className||'').slice(0,110),html:html(kids[0],400)}:null,
      图:img?{src:(img.currentSrc||img.src||'').slice(0,160),box:box(img),
        natural:[img.naturalWidth,img.naturalHeight],cls:(img.className||'').slice(0,80)}:null,
      名字: name?{text:txt(name),box:box(name),style:st(name),
        cls:(name.className||'').slice(0,90)}:null};});

  // ★ 「眼神光」那类**没有轨道**的标签（有 i、无 input）
  const ghost=[...aside.querySelectorAll('span,div')].filter(e=>{
    if(e.children.length!==0)return false;
    const t=txt(e); if(!t||t.length>6)return false;
    const r=e.getBoundingClientRect();
    return r.height===22&&r.width>0;}).filter(e=>{
    // ★ 同排右侧 6px 处有个 14×14 的 i ⟹ 就是这种标签
    const r=e.getBoundingClientRect();
    const sib=[...e.parentElement.children].some(o=>o!==e&&
      Math.round(o.getBoundingClientRect().width)===14&&
      Math.abs(o.getBoundingClientRect().x-(r.x+r.width+6))<=2&&
      Math.abs(o.getBoundingClientRect().y-(r.y+4))<=2);
    return sib;});
  out['★无轨道标签']=ghost.slice(0,6).map(e=>({text:txt(e),box:box(e),style:st(e),
    cls:(e.className||'').slice(0,90),父cls:(e.parentElement.className||'').slice(0,90),
    父html:html(e.parentElement,500)}));

  // ★ 一条**带轨道**的滑杆行（LABEL）：标签/i/轨道/数值 的 DOM 与样式
  const range=aside.querySelector('input[type="range"]');
  if(range){
    const lab=range.closest('label')||range.parentElement;
    const info=(lab&&lab.querySelector('[role="img"]'))||null;
    out['★滑杆行']={label:{box:box(lab),style:st(lab),
        cls:(lab.className||'').slice(0,110),html:html(lab,700)},
      轨道:{box:box(range),style:st(range),cls:(range.className||'').slice(0,110)},
      i标记:info?{box:box(info),style:st(info),html:html(info,240)}:null};
  }

  // ★ 妆造页的分类 chip（role=tab 且 50×26）
  const chips=[...aside.querySelectorAll('[role="tab"]')].filter(e=>{
    const r=e.getBoundingClientRect();return Math.round(r.width)===50&&Math.round(r.height)===26;});
  out['★chip数']=chips.length;
  out['★chip']=chips.slice(0,3).map(e=>({text:txt(e),box:box(e),style:st(e),
    cls:(e.className||'').slice(0,110),html:html(e,400)}));
  const tl=aside.querySelector('[role="tablist"]');
  out['★chip容器']=tl?{box:box(tl),style:st(tl),cls:(tl.className||'').slice(0,110),
    html:html(tl,300)}:null;
  const panel=aside.querySelector('[role="tabpanel"]');
  out['★tabpanel']=panel?{box:box(panel),style:st(panel),
    cls:(panel.className||'').slice(0,110),html:html(panel,400)}:null;

  // ★ 积分（底栏那颗）
  const hits=[];
  for(const e of document.querySelectorAll('span,div,b')){
    const t=txt(e); if(!/^\\d+$/.test(t)||e.children.length!==0)continue;
    const r=e.getBoundingClientRect(); if(r.width<=0||r.height<=0)continue;
    const x=Math.round(r.x), y=Math.round(r.y);
    if(x>=540&&x<=575&&y>=855&&y<=885)hits.push({t,x,y});}
  out['★积分']=hits;
  return out;}"""


# ★ 把键列表**内联**进 JS（`page.evaluate` 在页面上下文里跑，Python 变量看不见）
MEASURE = MEASURE.replace("__STYLE_KEYS__", json.dumps(STYLE_KEYS, ensure_ascii=False))


def click_text(page, label):
    for e in page.query_selector_all("span,div,button,a,p"):
        if (e.text_content() or "").strip() != label:
            continue
        bb = e.bounding_box()
        if not bb:
            continue
        page.mouse.click(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2)
        return True
    return False


def read_credit(page):
    """★ 只读**那一颗**积分（x 540..575、y 855..885）—— 不能读「页面上所有数字」。"""
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
            log["★是否点到编辑角色"] = click_text(pg, "编辑角色")
            pg.wait_for_timeout(5000)

            states = {}
            for label in ["眉眼", "妆造"]:
                before = read_credit(pg)
                ok = pg.evaluate(
                    """(label)=>{
                      const b=[...document.querySelectorAll('button')]
                        .find(e=>(e.getAttribute('aria-label')||'')===label);
                      if(!b)return false; b.click(); return true;}""", label)
                pg.wait_for_timeout(3000)
                after = read_credit(pg)
                states[label] = pg.evaluate(MEASURE)
                log["★%s_积分前" % label] = before
                log["★%s_积分后" % label] = after
                log["★%s_积分是否变化" % label] = (before != after)
                log["★%s_是否点到" % label] = ok
                if before != after:
                    log["★★ 积分变了 ⟹ 立刻停"] = True
                    break
            log["★各状态读数"] = states
    except Exception:
        log["异常"] = traceback.format_exc()
    finally:
        OUT.write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", OUT)
        for k, v in log.items():
            if k.startswith("★") and k != "★各状态读数":
                print("  %-24s %s" % (k, json.dumps(v, ensure_ascii=False)[:110]))
        if log.get("异常"):
            print("异常：", log["异常"])


if __name__ == "__main__":
    sys.exit(main())

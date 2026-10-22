#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 840 源站探针⑤：把**图标（svg）**的盒归档。

## 为什么还要再跑一趟

前四趟（`source840_editor{,2,3,4}.py`）归档的是 `leaves`（有文字的叶子）／`inputs`／`ctrls`
（按钮、输入）／`rowAcne`（祛斑祛痘那一行）／`preview`（中间预览区）四个**子集**。

⟹ 结果：**图标（`<svg>`）一个都没进去**
（`leaves` 只要有文字、`ctrls` 只要按钮/输入、`preview` 的 y 范围是 270..790）。

⟹ 而 clone 侧的几何**依赖**这些图标：
  - 五段按钮的**前置图标**（文案落在 rel 48 ⟹ 12 + icon + 6 = 36 ⟹ icon = 18）
  - 首枚页签「皮肤」的**前置图标**（文案落在 rel 961 ⟹ 3 + icon + 4 = 25 ⟹ icon = 18）
  - 「确认生成」文案左侧的图标（文案盒 64 @rel 1012 ⟹ 按钮内容 84 ⟹ icon = 16）
  - 半身/全身两枚按钮的图标

⟹ 这些尺寸**目前只是靠算术推出来的**（用源站自己测到的「文案 x 位置」反推），
⟹ 算术能定「图标 + 间隙」之和，**定不了**「图标本身多宽、间隙多宽」。

⟹ 所以本趟**只**把模态子树里**所有 svg** 连同其父盒一起归档 ⟹ 让图标宽度**有据**。

★★ **仍然只读**：绝不点「确认生成／保存／保存并添加到画布」。
"""
import json
import pathlib
import traceback

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_840_editor5.json")
SHOT = pathlib.Path("/tmp/liblib_source_840_editor5.png")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

MEASURE = r"""()=>{
  const box=(e)=>{const r=e.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)};};
  const txt=(e)=>(e.textContent||'').trim().replace(/\s+/g,' ');
  const leafByText=(t)=>{for(const e of document.querySelectorAll('span,div,button,a,p,label')){
    if(e.children.length===0&&txt(e)===t)return e;}return null;};
  const save=leafByText('保存'), seg=leafByText('脸部精修');
  if(!save||!seg)return {err:'锚点没找到'};
  const chain=(e)=>{const s=new Set();for(let n=e;n;n=n.parentElement)s.add(n);return s;};
  const cs_=chain(seg);let modal=null;
  for(let n=save;n;n=n.parentElement){if(cs_.has(n)){modal=n;break;}}
  if(!modal)return {err:'模态容器没找到'};

  // ★ 模态子树里**所有** svg（含 iconify 的 <svg> 与它内部的 <path>）
  const svgs=[];
  for(const e of modal.querySelectorAll('svg')){
    const p=e.parentElement;
    svgs.push({box:box(e), cls:(e.getAttribute('class')||'').slice(0,90),
      role:e.getAttribute('role')||'',
      parent:{tag:p?p.tagName:'', box:p?box(p):null,
        cls:p?(p.getAttribute('class')||'').slice(0,90):'',
        text:p?txt(p).slice(0,30):''}});
  }

  // ★ 几个**已知锚点**按钮的**直接子元素**（用来定「图标 + 间隙」的分配）
  const kids=(el)=>el?el.children.length?[...el.children].map(c=>({
      tag:c.tagName, box:box(c), text:txt(c).slice(0,24),
      cls:(c.getAttribute('class')||'').slice(0,80)})):null:null;
  const segBtns=[...modal.querySelectorAll('button')].filter(b=>{
    const t=txt(b); return t.startsWith('脸部精修')||t.startsWith('脸部 & 身体特征')
      ||t.startsWith('身材塑形')||t.startsWith('服装造型')||t.startsWith('音色音调');});
  const tabBtns=[...modal.querySelectorAll('button')].filter(b=>{
    const a=b.getAttribute('aria-label')||'';
    return ['皮肤','眉眼','鼻子','嘴唇','脸部','妆造'].includes(a);});
  const genBtn=[...modal.querySelectorAll('button')].find(b=>{
    const r=b.getBoundingClientRect();
    return Math.round(r.x)===1297&&Math.round(r.y)===783;});
  const halfBtns=[...modal.querySelectorAll('button')].filter(b=>{
    const a=b.getAttribute('aria-label')||'';
    return a==='半身'||a==='全身';});
  const swRoot=[...modal.querySelectorAll('*')].find(e=>
    (e.getAttribute('class')||'').includes('mantine-Switch-root'));

  return {
    modal:box(modal),
    svgs,
    segBtns:segBtns.map(b=>({text:txt(b).slice(0,20),box:box(b),kids:kids(b)})),
    tabBtns:tabBtns.map(b=>({aria:b.getAttribute('aria-label'),box:box(b),kids:kids(b)})),
    genBtn:genBtn?{box:box(genBtn),kids:kids(genBtn)}:null,
    halfBtns:halfBtns.map(b=>({aria:b.getAttribute('aria-label'),box:box(b),kids:kids(b)})),
    swRoot:swRoot?{box:box(swRoot),
      cls:(swRoot.getAttribute('class')||'').slice(0,90),
      role:swRoot.getAttribute('role')||'',
      ariaChecked:swRoot.getAttribute('aria-checked')}:null,
    url:location.href};
}"""


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
                pg.mouse.click(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2)
                pg.wait_for_timeout(4000)
            log["★是否点到编辑角色"] = click_text(pg, "编辑角色")
            pg.wait_for_timeout(5000)
            log["★读数"] = pg.evaluate(MEASURE)
            pg.screenshot(path=str(SHOT))
            br.close()
    except Exception:
        log["异常"] = traceback.format_exc()
    finally:
        OUT.write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", OUT)
        r = log.get("★读数") or {}
        if r.get("err"):
            print("★ 读数失败：", r)
        if r.get("modal"):
            print("模态：", r["modal"])
            print("svg 数：", len(r.get("svgs") or []))
            for s in (r.get("svgs") or []):
                b = s["box"]
                print("  svg box=(%d,%d,%d,%d) parent=%s %s" % (
                    b["x"], b["y"], b["w"], b["h"], s["parent"]["tag"],
                    (s["parent"]["cls"] or "")[:50]))
        if log.get("异常"):
            print("异常：", log["异常"])


if __name__ == "__main__":
    main()

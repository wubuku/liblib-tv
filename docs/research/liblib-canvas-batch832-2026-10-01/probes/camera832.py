#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 832 源站探针：**「添加机位」打开的机位预设面板**。

★ 为什么是它：batch 832 的盘点（`diag832b.py` 的 DOM 差分）显示——
  源站点「添加机位」会展开一整块 **232 宽的预设面板**（2 列网格、每格 104×72），
  内容是「当前视角 / 正面中景 / 正面特写 / 正面全景 / 侧面跟拍 / 侧面近景 /
  背面中景 / 俯拍全景 / 45° 俯拍 / 低角 …」；
  而 **clone 的「添加机位」是 `kind: "action"` ⟹ 点击直接加一个机位、没有面板**。
  ⟹ 这是一处**明确的产品缺口**（clone 少了「选预设」这一步）。

★ 本探针要抓的：
  ① 面板本体：盒、类名、网格规格（列数、格宽格高、gap）
  ② 每一格：文字、盒、图标（★ 20×20 的 SVG）、选中态
  ③ 面板的标题条（源站有一行 48 高的标题）
  ④ 面板打开时**左栏对象树**是否被替换（源站源码里是 `e?null:<div class="flex w-[232px] …">`）

★ 纪律：只读 + 只点 rail 入口；**不点任何预设格子**（点了会真的加机位、改源站数据）。
"""
import json
import pathlib
import traceback

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_desk832_camera.json")
SHOTS = pathlib.Path("/tmp/liblib_source_desk832")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

# ★ 机位预设面板读数（clone 侧会用**同一段 JS** ⟹ 两边字段可比）
DUMP_PANEL = """()=>{
  const box=(e)=>{const r=e.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)};};
  const cs=(e)=>{const c=getComputedStyle(e);
    return {bg:c.backgroundColor,color:c.color,fontSize:c.fontSize,
            fontWeight:c.fontWeight,borderRadius:c.borderRadius,border:c.border,
            padding:c.padding,gap:c.gap,width:c.width,height:c.height,
            display:c.display,gridTemplateColumns:c.gridTemplateColumns,
            gridAutoRows:c.gridAutoRows,position:c.position,
            boxShadow:c.boxShadow,overflow:c.overflow};};
  const vis=(e)=>{const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0&&getComputedStyle(e).visibility!=='hidden'
      &&getComputedStyle(e).display!=='none'&&getComputedStyle(e).opacity!=='0';};
  // ★ 面板容器：源站源码 `flex w-[232px] min-w-0 flex-col bg-[#171717]`
  const cands=Array.from(document.querySelectorAll('div,section')).filter(e=>{
    const c=getComputedStyle(e); const r=e.getBoundingClientRect();
    if(!vis(e)) return false;
    if(Math.abs(r.width-232)>1) return false;
    if(r.height<120) return false;
    // ★ 用「最外层」挑法：不含另一个候选的面板
    return true;});
  const outer=cands.filter(p=>!cands.some(q=>q!==p&&q.contains(p)));
  const panel=outer[outer.length-1];
  if(!panel) return {found:false, candCount:cands.length};
  const grid=panel.querySelector('div.grid');
  const cells=grid?Array.from(grid.children):[];
  const title=panel.firstElementChild;
  return {
    found:true,
    panelBox:box(panel), panelCls:String(panel.className||'').slice(0,220),
    panelStyle:cs(panel),
    title:title?{tag:title.tagName,t:(title.textContent||'').trim().slice(0,30),
                 box:box(title),cls:String(title.className||'').slice(0,140),
                 style:cs(title)}:null,
    gridBox:grid?box(grid):null,
    gridCls:grid?String(grid.className||'').slice(0,220):null,
    gridStyle:grid?cs(grid):null,
    gridTemplateColumns:grid?getComputedStyle(grid).gridTemplateColumns:null,
    cellCount:cells.length,
    cells:cells.map((c,i)=>({
      idx:i, tag:c.tagName, t:(c.textContent||'').trim().slice(0,20),
      box:box(c), cls:String(c.className||'').slice(0,160), style:cs(c),
      svgBox:c.querySelector('svg')?box(c.querySelector('svg')):null,
      svgHtml:c.querySelector('svg')?c.querySelector('svg').outerHTML.slice(0,220):null,
      spans:Array.from(c.querySelectorAll('span')).map(s=>({
        t:(s.textContent||'').trim().slice(0,20), box:box(s),
        cls:String(s.className||'').slice(0,90)})),
    })),
  };
}"""


def open_desk(page):
    card = page.locator(".react-flow__node-director-console-3d").first
    card.hover()
    page.wait_for_timeout(800)
    page.locator(
        ".react-flow__node-director-console-3d button:has-text('打开导演台')").first.click()
    page.wait_for_timeout(8_000)


def main():
    cookies = json.loads(COOKIE.read_text(encoding="utf-8"))
    out = {}
    try:
        run(out, cookies)
    finally:
        OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", OUT)


def run(out, cookies):
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        ctx = br.new_context(viewport={"width": 1920, "height": 1080},
                             locale="zh-CN")
        ctx.add_cookies([{"name": c["name"], "value": c["value"],
                          "domain": c["domain"], "path": c.get("path", "/"),
                          "expires": c.get("expires", -1),
                          "httpOnly": c.get("httpOnly", False),
                          "secure": c.get("secure", False),
                          "sameSite": c.get("sameSite", "Lax")} for c in cookies])
        page = ctx.new_page()
        page.goto(URL, wait_until="domcontentloaded", timeout=90_000)
        page.wait_for_timeout(12_000)
        open_desk(page)
        SHOTS.mkdir(exist_ok=True)
        try:
            nav = page.locator("nav").filter(
                has=page.locator("button[aria-label='场景']")).first
            out["①开台后"] = page.evaluate(DUMP_PANEL)
            nav.locator("button[aria-label='添加机位']").first.click()
            page.wait_for_timeout(2_200)
            out["②点添加机位后"] = page.evaluate(DUMP_PANEL)
            page.screenshot(path=str(SHOTS / "832_camera_panel.png"))
        except Exception:
            out["异常"] = traceback.format_exc()[-1500:]
        try:
            page.locator("[aria-label='关闭']:visible").first.click()
            page.wait_for_timeout(2_500)
        except Exception:
            pass
        ctx.close()
        br.close()


if __name__ == "__main__":
    main()

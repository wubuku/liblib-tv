#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 832 源站探针：**「添加机位」机位预设面板**（含每格图标的 SVG path 原文）。

★ 为什么上一版不够：batch 832 的第一版探针只量了盒与文字 ⟹ 缺了**图标**。
  而源站每格图标是 **iconify `libtv` 图标集**里的一枚（`viewBox="0 0 16 16"`），
  15 格各有一枚**不同的 path** ⟹ 要复现就得拿到 path 原文。

★ ★ 为什么 path 原文**不在静态 chunk 里**：
  - 预设清单（15 项）**不在** `0fmehki05gkzw.js.js` 里（源码里是 `eo.map(...)`，
    `eo` 来自别处）；
  - 也**不在** i18n 字典 chunk（`3sqc5lvxsgmdw.js.js`，153KB）里
    —— 搜「过肩镜头」「荷兰角」「鸟瞰」等 12 个中文名**全部 -1**；
  ⟹ ★ 结论：预设清单**走服务端下发**（与 batch 827 的「官方角色库筛选配置」
    同一形态）⟹ ★ **唯一可靠的来源是活体 DOM**。
  ⟹ 所以本探针直接从活体 DOM 抽 `path` 的 `d` 原文。

★ 纪律：只读；**绝不点任何预设格子**（点了会真的加机位、改源站数据）。
"""
import json
import pathlib
import traceback

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_desk832_camera2.json")
SHOTS = pathlib.Path("/tmp/liblib_source_desk832")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

DUMP_CELLS = """()=>{
  const box=(e)=>{const r=e.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)};};
  const cs=(e)=>{const c=getComputedStyle(e);
    return {bg:c.backgroundColor,color:c.color,fontSize:c.fontSize,
            fontWeight:c.fontWeight,borderRadius:c.borderRadius,border:c.border,
            padding:c.padding,gap:c.gap,width:c.width,height:c.height,
            display:c.display,position:c.position,lineHeight:c.lineHeight};};
  const vis=(e)=>{const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0&&getComputedStyle(e).visibility!=='hidden'
      &&getComputedStyle(e).display!=='none'&&getComputedStyle(e).opacity!=='0';};
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
    // ★★ 判别字段：**这是机位预设面板还是场景树**？
    //   两者**都是 232 宽** ⟹ 只看「有没有 232 宽的面板」分不出来
    //   ⟹ 必须另设一个判别依据（标题文案 / data 属性）。
    view: panel.getAttribute('data-director-camera-preset-panel')!==null
      ? 'camera-presets'
      : (panel.getAttribute('data-director-tree')!==null ? 'tree' : 'unknown'),
    panelBox:box(panel), panelCls:String(panel.className||'').slice(0,240),
    panelStyle:cs(panel),
    title:title?{tag:title.tagName,t:(title.textContent||'').trim().slice(0,30),
                 box:box(title),cls:String(title.className||'').slice(0,160),
                 style:cs(title)}:null,
    gridBox:grid?box(grid):null,
    gridCls:grid?String(grid.className||'').slice(0,240):null,
    gridStyle:grid?cs(grid):null,
    gridTemplateColumns:grid?getComputedStyle(grid).gridTemplateColumns:null,
    cellCount:cells.length,
    cells:cells.map((c,i)=>{
      const svg=c.querySelector('svg');
      const path=svg?svg.querySelector('path'):null;
      const span=c.querySelector('span');
      return {
        idx:i, tag:c.tagName, t:(c.textContent||'').trim().slice(0,24),
        box:box(c), cls:String(c.className||'').slice(0,200), style:cs(c),
        svgBox:svg?box(svg):null,
        svgCls:svg?String(svg.getAttribute('class')||''):null,
        svgViewBox:svg?svg.getAttribute('viewBox'):null,
        svgWidth:svg?svg.getAttribute('width'):null,
        pathD:path?path.getAttribute('d'):null,
        pathStroke:path?path.getAttribute('stroke'):null,
        pathStrokeWidth:path?path.getAttribute('stroke-width'):null,
        pathFill:path?path.getAttribute('fill'):null,
        spanBox:span?box(span):null,
        spanCls:span?String(span.className||'').slice(0,110):null,
        spanText:span?(span.textContent||'').trim():null,
      };
    }),
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
            nav.locator("button[aria-label='添加机位']").first.click()
            page.wait_for_timeout(2_500)
            out["①机位预设面板"] = page.evaluate(DUMP_CELLS)
            page.screenshot(path=str(SHOTS / "832_camera_panel2.png"))
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

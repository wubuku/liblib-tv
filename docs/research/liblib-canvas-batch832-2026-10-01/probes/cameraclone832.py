#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 832 clone 侧探针：量「添加机位」机位预设面板的几何。

★ 与源站探针（probes/camera832b.py）用**同一段读数 JS** ⟹ 两边字段可比。

★ 读数口径（两边一致）：
  - 面板容器：`flex` + `column` + 宽 232
  - 标题条：面板的第一个子元素
  - 网格：`div.grid`
  - 每格：网格的子元素（按钮），量盒、类名、图标盒、SVG path 原文、文字 span

★ ★ 一个前置事实（batch 832 实测）：**clone 的时间轴默认展开**，会盖住
  左侧栏底部 ⟹ 但**不影响**本面板（它在左栏**顶部**）⟹ 无需先关时间轴。
"""
import json
import pathlib

from playwright.sync_api import sync_playwright

OUT = pathlib.Path("/tmp/liblib_clone_desk832_camera.json")
SHOTS = pathlib.Path("/tmp/liblib_clone_desk832")

# ★ 与源站**逐字相同**的读数 JS
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
    return true;
  });
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


def main():
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        page = br.new_page(viewport={"width": 1920, "height": 1080})
        page.goto("http://localhost:4317/?batch832=1",
                  wait_until="networkidle", timeout=90_000)
        page.wait_for_function(
            "() => Boolean(window.__libtv_store && window.__libtv_ui_store "
            "&& window.__director_store)", timeout=60_000)
        page.wait_for_timeout(800)
        nid = page.evaluate("""() => {
          const nodes = window.__libtv_store.getState().getActiveCanvas().nodes
            .filter((n) => n.type === 'script-execution');
          return nodes.length === 1 ? nodes[0].id : null;
        }""")
        page.locator('.react-flow__node[data-id="%s"] [data-open-director]' % nid).first.click()
        page.locator("[data-director-workspace]").wait_for(state="visible", timeout=30_000)
        page.wait_for_timeout(2_000)
        page.evaluate(
            "() => { for (const el of document.querySelectorAll('nextjs-portal')) el.remove(); }")

        out = {}
        out["①开台后"] = page.evaluate(DUMP_CELLS)
        # 点「添加机位」⟹ 左侧栏切成机位预设面板
        page.locator("[data-director-rail-entry='add-camera']").click()
        page.wait_for_timeout(1_500)
        out["②点添加机位后"] = page.evaluate(DUMP_CELLS)
        SHOTS.mkdir(exist_ok=True)
        page.screenshot(path=str(SHOTS / "832_camera_panel.png"))

        # ★ 点「场景」应切回场景树
        page.locator("[data-director-rail-entry='scene']").click()
        page.wait_for_timeout(1_500)
        out["③点场景后"] = page.evaluate(DUMP_CELLS)
        out["③b场景树还在"] = page.evaluate(
            "()=>!!document.querySelector('[data-director-tree]')")
        page.screenshot(path=str(SHOTS / "832_back_to_tree.png"))
        br.close()
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("已落盘：", OUT)


if __name__ == "__main__":
    main()

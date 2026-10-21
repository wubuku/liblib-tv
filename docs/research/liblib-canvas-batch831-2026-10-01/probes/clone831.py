#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 831 clone 侧探针（4317）：量「帮助 → 菜单 → 快捷键对话框」的几何。

★ 与源站探针（probes/help831.py）**用同一段读数 JS** ⟹ 两边字段逐字可比。
★ 开台步骤沿用 batch 828 已验证的那套（唯一 script-execution 节点 ⟹ 按 node id
  定位按钮，**绝不 `.first`**）。视图 1920×1080（与源站实测同尺寸）。
★ ⚠ 关键前提：clone 的时间轴**默认展开**，会盖住 rail 底部的「帮助」按钮
  （源站默认时间轴是关的 ⟹ 帮助按钮平时可达）。本探针先把时间轴关掉
  （真实点底部胶囊里那枚「动画时间轴」开关），再走帮助路径。
"""
import json
import pathlib

from playwright.sync_api import sync_playwright

BASE = "http://localhost:4317"
OUT = pathlib.Path("/tmp/liblib_clone_desk831_help.json")
SHOTS = pathlib.Path("/tmp/liblib_clone_desk831")

DUMP_MENU = """()=>{
  const box=(e)=>{const r=e.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)};};
  const cs=(e)=>{const c=getComputedStyle(e);
    return {bg:c.backgroundColor,color:c.color,fontSize:c.fontSize,
            fontWeight:c.fontWeight,borderRadius:c.borderRadius,
            padding:c.padding,gap:c.gap,width:c.width,height:c.height,
            border:c.border,boxShadow:c.boxShadow,lineHeight:c.lineHeight,
            backdropFilter:c.backdropFilter,opacity:c.opacity,
            display:c.display,position:c.position,zIndex:c.zIndex};};
  const menu=document.querySelector('[role="menu"]');
  const btn=document.querySelector('[aria-label="帮助"]');
  const items=menu?Array.from(menu.querySelectorAll('[role="menuitem"]')):[];
  const svgs=menu?Array.from(menu.querySelectorAll('svg')).map(e=>({box:box(e)})):[];
  return {
    helpButton: btn?{box:box(btn),style:cs(btn),
                     ariaExpanded:btn.getAttribute('aria-expanded'),
                     ariaHasPopup:btn.getAttribute('aria-haspopup'),
                     cls:String(btn.className||'')}:null,
    menu: menu?{box:box(menu),style:cs(menu),
                cls:String(menu.className||''),
                items:items.map(e=>({t:(e.textContent||'').trim(),box:box(e),
                                     style:cs(e),cls:String(e.className||'')})),
                svgs:svgs}:null,
  };
}"""

DUMP_DIALOG = """()=>{
  const box=(e)=>{const r=e.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)};};
  const cs=(e)=>{const c=getComputedStyle(e);
    return {bg:c.backgroundColor,color:c.color,fontSize:c.fontSize,
            fontWeight:c.fontWeight,borderRadius:c.borderRadius,
            padding:c.padding,gap:c.gap,width:c.width,height:c.height,
            border:c.border,lineHeight:c.lineHeight,
            backdropFilter:c.backdropFilter};};
  const dlg=Array.from(document.querySelectorAll('[role="dialog"]'))
    .filter(e=>{const r=e.getBoundingClientRect();
      return r.width>0&&r.height>0;});
  const d=dlg[dlg.length-1];
  if(!d) return {found:false, dialogs:dlg.length};
  const h2=d.querySelector('h2');
  const cols=Array.from(d.querySelectorAll('div')).filter(e=>{
    const c=getComputedStyle(e);
    return c.display==='flex'&&e.children.length>=5
      &&e.getBoundingClientRect().width>150&&e.getBoundingClientRect().width<260;});
  const rows=[];
  for(const col of cols){
    for(const row of Array.from(col.children)){
      const kids=Array.from(row.children).map(k=>({
        tag:k.tagName,t:(k.textContent||'').trim().slice(0,20),
        box:box(k),cls:String(k.className||'').slice(0,70),
        style:cs(k),
        svgs:Array.from(k.querySelectorAll('svg')).map(s=>{
          const r=s.getBoundingClientRect();
          return {x:Math.round(r.x),y:Math.round(r.y),
                  w:Math.round(r.width),h:Math.round(r.height)};}),
        badges:Array.from(k.querySelectorAll('span')).map(s=>({
          t:(s.textContent||'').trim().slice(0,8),
          box:box(s),cls:String(s.className||'').slice(0,80)}))}));
      rows.push({colX:Math.round(col.getBoundingClientRect().x),
                 colBox:box(col),kids:kids});
    }
  }
  return {found:true,
          box:box(d),style:cs(d),
          aria:d.getAttribute('aria-label'),
          ariaModal:d.getAttribute('aria-modal'),
          cls:String(d.className||''),
          title:h2?{t:(h2.textContent||'').trim(),box:box(h2),
                    style:cs(h2)}:null,
          cols:cols.map(c=>({box:box(c),style:cs(c),
                              cls:String(c.className||'')})),
          rows:rows,
          allSvgs:Array.from(d.querySelectorAll('svg')).map(s=>{
            const r=s.getBoundingClientRect();
            return {x:Math.round(r.x),y:Math.round(r.y),
                    w:Math.round(r.width),h:Math.round(r.height),
                    html:s.outerHTML.slice(0,120)};})};
}"""

DUMP_COVER = """()=>{
  const b=document.querySelector('[data-director-rail-entry="help"]');
  const r=b.getBoundingClientRect();
  const cx=Math.round(r.x+r.width/2), cy=Math.round(r.y+r.height/2);
  const top=document.elementFromPoint(cx,cy);
  return {
    helpBox:{x:Math.round(r.x),y:Math.round(r.y),
             w:Math.round(r.width),h:Math.round(r.height)},
    hitTag:top?top.tagName:null,
    hitAria:top?(top.getAttribute('aria-label')||''):'',
    hitCls:top?String(top.className||'').slice(0,70):'',
    timelineOpen:!!document.querySelector('[data-director-timeline]'),
    timelinePressed:(function(){
      const t=document.querySelector("[aria-label='动画时间轴']");
      return t?t.getAttribute('aria-pressed'):null;})(),
  };
}"""

DUMP_COACH = """()=>{
  const c=document.querySelector('[data-director-timeline-coachmark]');
  if(!c) return {coach:false};
  const r=c.getBoundingClientRect();
  const bx=(e)=>{if(!e)return null;const q=e.getBoundingClientRect();
    return {x:Math.round(q.x),y:Math.round(q.y),
            w:Math.round(q.width),h:Math.round(q.height)};};
  return {coach:true,
          box:{x:Math.round(r.x),y:Math.round(r.y),
               w:Math.round(r.width),h:Math.round(r.height)},
          text:(c.textContent||'').trim(),
          skip:bx(c.querySelector('[data-director-coachmark-skip]')),
          next:bx(c.querySelector('[data-director-coachmark-next]'))};
}"""


def main():
    out = {}
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        page = br.new_page(viewport={"width": 1920, "height": 1080},
                           device_scale_factor=1)
        page.goto(f"{BASE}/?batch831=1", wait_until="networkidle", timeout=90_000)
        page.wait_for_function(
            "() => Boolean(window.__libtv_store && window.__libtv_ui_store "
            "&& window.__director_store)", timeout=60_000)
        page.wait_for_timeout(800)
        nid = page.evaluate("""() => {
          const nodes = window.__libtv_store.getState().getActiveCanvas().nodes
            .filter((n) => n.type === 'script-execution');
          return nodes.length === 1 ? nodes[0].id : null;
        }""")
        out["节点id"] = nid
        page.locator('.react-flow__node[data-id="%s"] [data-open-director]' % nid).first.click()
        page.locator("[data-director-workspace]").wait_for(state="visible", timeout=30_000)
        page.wait_for_timeout(1_800)
        SHOTS.mkdir(exist_ok=True)

        def clean_portals():
            # ★ Next.js 的 dev overlay portal（`nextjs-portal`）在 dev 上会盖住
            #   视口左下角并**拦截点击** ⟹ 这是 dev 专属产物、不是产品问题
            #   （batch 828 的探针用过同一手法）。生产构建里没有它。
            page.evaluate(
                "() => { for (const el of document.querySelectorAll('nextjs-portal')) el.remove(); }")

        clean_portals()

        # ⓪ 时间轴展开时「帮助」被谁盖住（源站同款）
        out["⓪时间轴展开时"] = page.evaluate(DUMP_COVER)

        # ⓪b 关掉时间轴（真实点底部胶囊里那枚「动画时间轴」开关）
        if out["⓪时间轴展开时"].get("timelineOpen"):
            clean_portals()
            page.locator("[aria-label='动画时间轴']").first.click()
            page.wait_for_timeout(1_500)
        out["⓪b关掉时间轴后"] = page.evaluate(DUMP_COVER)

        # ① 帮助按钮
        out["①帮助按钮"] = page.evaluate(DUMP_MENU)
        clean_portals()
        page.locator("[data-director-rail-entry='help']").click()
        page.wait_for_timeout(900)
        out["②菜单打开"] = page.evaluate(DUMP_MENU)
        page.screenshot(path=str(SHOTS / "831_menu.png"))

        # ③ 快捷键对话框
        clean_portals()
        page.locator("[data-director-help-menu-item='shortcuts']").click()
        page.wait_for_timeout(900)
        out["③快捷键对话框"] = page.evaluate(DUMP_DIALOG)
        page.screenshot(path=str(SHOTS / "831_shortcuts.png"))

        # ④ 点外面关闭
        page.mouse.click(1400, 700)
        page.wait_for_timeout(700)
        out["④点外面后"] = page.evaluate(
            "() => ({dialogs: document.querySelectorAll("
            "'[data-director-shortcuts-dialog]').length,"
            "overlay: document.querySelectorAll('[data-director-shortcuts-overlay]').length})")

        # ⑤ Esc 关闭
        clean_portals()
        page.locator("[data-director-rail-entry='help']").click()
        page.wait_for_timeout(500)
        page.locator("[data-director-help-menu-item='shortcuts']").click()
        page.wait_for_timeout(600)
        page.keyboard.press("Escape")
        page.wait_for_timeout(700)
        out["⑤Esc后"] = page.evaluate(
            "() => ({dialogs: document.querySelectorAll("
            "'[data-director-shortcuts-dialog]').length})")

        # ⑥ 「使用教程」⟹ 引导气泡重新出现（不是死按钮）
        clean_portals()
        page.locator("[data-director-rail-entry='help']").click()
        page.wait_for_timeout(500)
        page.locator("[data-director-help-menu-item='tutorial']").click()
        page.wait_for_timeout(1_200)
        out["⑥使用教程后"] = page.evaluate(DUMP_COACH)
        page.screenshot(path=str(SHOTS / "831_tutorial.png"))
        br.close()
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("已落盘：", OUT)


if __name__ == "__main__":
    main()

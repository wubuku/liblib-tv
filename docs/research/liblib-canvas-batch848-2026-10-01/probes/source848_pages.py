#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 848 源站探针（**只读**）：角色造型室右栏里**四枚尚未实测的页面**。

## 为什么要这四枚

★ batch 847 之后，clone 里还剩**四枚**「点开是整页内容、但内容**没测过**」的入口
（★ 它们被 840／841／842／843 四道门禁当作「页面级未实测入口」的靶子）：

  | 编号 | 位置 | 入口文案 |
  | --- | --- | --- |
  | P1 | 左列第四段「服装造型」的子页签 | 「服装」 |
  | P2 | 左列第四段「服装造型」的子页签 | 「AI 生成」 |
  | P3 | 左列第五段「音色音调」的页签 | 「我的音色」 |
  | P4 | 左列第五段「音色音调」的页签 | 「AI 生成」 |

★ **这四页长什么样，此前**完全**不知道** ⟹ ⟹ 所以本探针
  ★ **不预设任何结构** ⟹ ⟹ 直接把**整棵子树** dump 出来（tag／class／盒／文字／样式）
  ⟹ ⟹ 后面无论要实现哪一层，都有原文可依。

## 只读保证

★ 全程只点**分段**与**页签** ⟹ ⟹ **不点**任何「生成」「确认生成」按钮
⟹ ⟹ **不消耗** ⚡44 ⟹ ⟹ ★ 每一次点击**前后**都读那一颗积分 ⟹ ⟹ 变了就**立刻停**。

## 输出

  raw/source-848-p1-outfit-clothes.json   （P1 的整棵子树）
  raw/source-848-p2-outfit-ai.json        （P2）
  raw/source-848-p3-voice-mine.json       （P3）
  raw/source-848-p4-voice-ai.json         （P4）
  raw/source-848-voice.json               （四页合订 ＋ 积分自证 ＋ 截图路径）
  raw/source-848-p1.png … p4.png          （每页一张**视口**截图 ⟹ ⟹ 肉眼可核）
"""
import json
import pathlib
import sys
import traceback

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch848-2026-10-01"
RAW = BATCH / "raw"

URL = ("https://www.liblib.tv/canvas"
       "?spaceId=7709759&projectId=a860e1da8e9e4504bececda022386429")
COOKIE = pathlib.Path("/tmp/liblib-cookie.json")

# ★ 四枚入口：(键, 左列分段, 右栏页签文案, 期望在这页里看到的字样)
PAGES = [
    ("p1", "服装造型", "服装", None),
    ("p2", "服装造型", "AI 生成", None),
    ("p3", "音色音调", "我的音色", None),
    ("p4", "音色音调", "AI 生成", None),
]


# ── 整棵子树 dump（★ 不预设结构） ──────────────────────────────────────────
DUMP = r"""()=>{
  const box=(e)=>{const r=e.getBoundingClientRect();
    return [Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)];};
  const txt=(e)=>(e.textContent||'').trim().replace(/\s+/g,' ');
  const own=(e)=>txt(e).slice(0,70);
  const cls=(e)=>String((e&&e.getAttribute)?(e.getAttribute('class')||''):'');
  const st=(e)=>{const cs=getComputedStyle(e);
    return {fs:cs.fontSize,fw:cs.fontWeight,lh:cs.lineHeight,col:cs.color,
      bg:cs.backgroundColor,br:cs.borderRadius,
      bt:cs.borderTopWidth,btc:cs.borderTopColor,
      bb:cs.borderBottomWidth,bbc:cs.borderBottomColor,
      bl:cs.borderLeftWidth,blr:cs.borderLeftColor,
      brr:cs.borderRightWidth,brrc:cs.borderRightColor,
      pl:cs.paddingLeft,pt:cs.paddingTop,pr:cs.paddingRight,pb:cs.paddingBottom,
      gap:cs.gap,d:cs.display,ai:cs.alignItems,ji:cs.justifyContent,
      gtc:cs.gridTemplateColumns,ov:cs.overflow,op:cs.opacity,
      ff:cs.fontFamily.slice(0,90),sh:cs.boxShadow.slice(0,60)};};

  // ★ 模态根：视口 (361,161) 起的那个大盒子（★ 与 clone 同位 ⟹ 后面可相减）
  let modal=null;
  for(const e of document.querySelectorAll('div,section,form')){
    const r=e.getBoundingClientRect();
    if(Math.abs(r.x-361)<=4&&Math.abs(r.y-161)<=4&&r.width>1000&&r.height>600){
      if(!modal||e.getBoundingClientRect().height>modal.getBoundingClientRect().height)
        modal=e;}
  }
  const root=modal||document.body;

  const walk=(e,d)=>{
    const o={t:e.tagName,c:cls(e).slice(0,140),b:box(e),n:e.children.length};
    const t=own(e); if(t)o.x=t;
    if(e.tagName==='IMG')o.src=(e.getAttribute('src')||'').slice(0,160);
    if(e.tagName==='INPUT'||e.tagName==='TEXTAREA'){o.ph=e.getAttribute('placeholder')||'';
      o.ty=e.getAttribute('type')||'';}
    if(e.tagName==='SVG')o.svg=1;
    if(e.tagName==='BUTTON'||e.tagName==='A'||e.tagName==='INPUT'||e.tagName==='TEXTAREA'
       ||e.tagName==='SELECT'||e.tagName==='LABEL'){
      o.ar=e.getAttribute('aria-label')||'';o.ap=e.getAttribute('aria-pressed')||'';
      o.ac=e.getAttribute('aria-current')||'';o.tp=e.getAttribute('type')||'';}
    o.s=st(e);
    if(d<14&&e.children.length){
      o.c2=[...e.children].map(k=>walk(k,d+1));}
    return o;};

  const out={};
  out['★模态根']={b:box(root),c:cls(root).slice(0,160)};
  out['★整棵子树']=walk(root,0);
  // ★ 模态**之外**可能弹出的浮层（★ 「AI 生成」很可能开一个 dialog ⟹ ⟹ 必须一起抓）
  out['★浮层']=[...document.querySelectorAll('[role="dialog"],[aria-modal="true"],'
      +'[class*="popover"],[class*="Popover"],[class*="dropdown"],[class*="Dropdown"],'
      +'[class*="tooltip"],[class*="Tooltip"],[class*="portal"],[class*="Portal"]')]
    .map(e=>({t:e.tagName,c:cls(e).slice(0,140),b:box(e),x:own(e)}))
    .filter(e=>e['b'][2]>0&&e['b'][3]>0);
  // ★ 整页里带文字的叶子（★ 抓「弹到别处」的文案）
  out['★带文字的叶子']=[...document.querySelectorAll('*')]
    .filter(e=>e.children.length===0&&txt(e))
    .map(e=>({t:e.tagName,x:txt(e).slice(0,90),b:box(e)}));
  out['★整页文本']=(document.body.innerText||'').slice(0,4000);
  return out;}"""


def read_credit(pg):
    return pg.evaluate("""()=>{
      const t=document.body.innerText||'';
      const m=t.match(/⚡\s*(\d+)/);
      return m?Number(m[1]):null;}""")


def click_segment(pg, label):
    return pg.evaluate("""(label)=>{
      const bs=[...document.querySelectorAll('button')].filter(e=>{
        const r=e.getBoundingClientRect();
        return r.x<700&&r.width>100;});
      const b=bs.find(e=>(e.textContent||'').trim().startsWith(label));
      if(!b)return false; b.click(); return true;}""", label)


def click_tab(pg, label):
    """★ 点右栏里的页签（★ 只在**右栏**里找 ⟹ ⟹ 不会点到别处的同名按钮）。"""
    return pg.evaluate("""(label)=>{
      const aside=[...document.querySelectorAll('aside')].find(a=>{
        const r=a.getBoundingClientRect();
        return r.x>=1273&&Math.round(r.width)===288;});
      if(!aside)return 'no-aside';
      const bs=[...aside.querySelectorAll('button')].filter(e=>{
        const t=(e.textContent||'').trim();
        return t===label||t.startsWith(label);});
      if(!bs.length)return 'no-tab';
      bs[0].click(); return 'clicked';}""", label)


def main():
    out = {"★入口清单": []}
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

            for key, seg, tablabel, _exp in PAGES:
                rec = {"★分段": seg, "★页签": tablabel}
                try:
                    c0 = read_credit(pg)
                    rec["★点到分段"] = click_segment(pg, seg)
                    pg.wait_for_timeout(2500)
                    rec["★点到页签"] = click_tab(pg, tablabel)
                    pg.wait_for_timeout(3000)
                    c1 = read_credit(pg)
                    rec["★积分_点前"] = c0
                    rec["★积分_点后"] = c1
                    rec["★积分是否变化"] = (c0 != c1)
                    if c0 != c1:
                        rec["★★ 积分变了 ⟹ 立刻停"] = True
                        raise SystemExit("积分变了")
                    reading = pg.evaluate(DUMP)
                    shot = RAW / ("source-848-%s.png" % key)
                    pg.screenshot(path=str(shot))
                    rec["★截图"] = "raw/" + shot.name
                    (RAW / ("source-848-%s.json" % key)).write_text(
                        json.dumps(reading, ensure_ascii=False, indent=1), encoding="utf-8")
                    rec["★右栏文本头"] = (reading.get("★整页文本") or "")[:300]
                    rec["★浮层数"] = len(reading.get("★浮层") or [])
                    rec["★叶子数"] = len(reading.get("★带文字的叶子") or [])
                except SystemExit:
                    raise
                except Exception:
                    rec["★异常"] = traceback.format_exc()
                out["★入口清单"].append(rec)
                (RAW / "source-848-voice.json").write_text(
                    json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    except SystemExit:
        pass
    except Exception:
        out["异常"] = traceback.format_exc()
    finally:
        RAW.mkdir(parents=True, exist_ok=True)
        (RAW / "source-848-voice.json").write_text(
            json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", RAW / "source-848-voice.json")
        if out.get("异常"):
            print("异常：", out["异常"])
        for rec in out.get("★入口清单", []):
            print("%-28s 点分段=%s 点页签=%s 积分变化=%s 浮层=%s 叶子=%s"
                  % (rec.get("★分段") + "/" + rec.get("★页签"),
                     rec.get("★点到分段"), rec.get("★点到页签"),
                     rec.get("★积分是否变化"), rec.get("★浮层数"), rec.get("★叶子数")))
            if rec.get("★右栏文本头"):
                print("    文本头：", rec["★右栏文本头"][:160].replace("\n", " | "))


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 850 源站探针（**只读**）：角色大编辑器**预览区（中列）**的三次读数。

## 为什么是预览区

★ batch 847／848／849 把左列五段 ＋ 右栏六枚页签都做完并逐项对照了 ⟹ ⟹
**中列（预览区）成了最后一个「只做了壳、从未逐项对照」的地方**。

★ batch 840 说过中列是「624×602：角色图 467×550 ＋ 半身/全身（32×32）」 ⟹ ⟹
但那只是**一句概括** ⟹ ⟹ 从没读过它的**层级**、**渐变**、**transform**。

★ 而 batch 848 的 raw（整棵模态子树）里**已经躺着**中列的结构 ⟹ ⟹
本批先从那份 raw 里**挖**出差异清单（见 README）⟹ ⟹ 再用本探针补齐
**raw 里没有的那几样**：

  ① `backgroundImage`（渐变遮罩的确切定义）—— 848 的 DUMP 只记了 `backgroundColor`；
  ② `transform` / `transformOrigin` / `transition`（那层 `origin-[50%_8%] transition-transform`）；
  ③ **点「半身」「全身」之后**的样子 —— raw 是**静态**的 ⟹ ⟹ 必须点。

## ★ 只读纪律

★ 全程**只点**中列右下角那两枚取景按钮（半身／全身）⟹ ⟹
**绝不点**「确认生成」「保存」「保存并添加到画布」（⟹ ⟹ 后两者会**真扣 ⚡44**）。
★ 每一次点击**前后**都读那一颗积分 ⟹ ⟹ 变了就**立刻停**并如实记录。
★ 点取景按钮**不产生**任何付费副作用（它是纯前端取景切换）⟹ ⟹ 由积分读数自证。

## 输出

  raw/source-850-preview.json   （三次读数合订 ＋ 积分自证 ＋ 截图路径）
  raw/source-850-default.png    （默认态视口截图）
  raw/source-850-half.png       （点「半身」之后）
  raw/source-850-full.png       （点「全身」之后）
"""
import json
import pathlib
import sys
import traceback

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch850-2026-10-01"
RAW = BATCH / "raw"

URL = ("https://www.liblib.tv/canvas"
       "?spaceId=7709759&projectId=a860e1da8e9e4504bececda022386429")
COOKIE = pathlib.Path("/tmp/liblib-cookie.json")

# ── 中列（MAIN）整棵子树 dump ───────────────────────────────────────────────
# ★ 比 848 的 DUMP 多记四样：backgroundImage／transform／transformOrigin／visibility
DUMP = r"""()=>{
  const box=(e)=>{const r=e.getBoundingClientRect();
    return [Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)];};
  const txt=(e)=>(e.textContent||'').trim().replace(/\s+/g,' ');
  const st=(e)=>{const cs=getComputedStyle(e);
    return {fs:cs.fontSize,fw:cs.fontWeight,lh:cs.lineHeight,col:cs.color,
      bg:cs.backgroundColor,bi:cs.backgroundImage.slice(0,900),
      br:cs.borderRadius,bl:cs.borderLeftWidth,blr:cs.borderLeftColor,
      d:cs.display,ai:cs.alignItems,ji:cs.justifyContent,ov:cs.overflow,
      op:cs.opacity,vis:cs.visibility,
      tr:cs.transform,to:cs.transformOrigin,ts:cs.transition.slice(0,400),
      pos:cs.position,z:cs.zIndex,top:cs.top,left:cs.left,
      w:cs.width,h:cs.height,mw:cs.maxWidth,mh:cs.maxHeight,
      of:cs.objectFit,fl:cs.filter.slice(0,80),bt:cs.backdropFilter.slice(0,80)};};

  // ★ 模态根：视口 (361,161) 起的大盒子
  let modal=null;
  for(const e of document.querySelectorAll('div,section,form')){
    const r=e.getBoundingClientRect();
    if(Math.abs(r.x-361)<=4&&Math.abs(r.y-161)<=4&&r.width>1000&&r.height>600){
      if(!modal||e.getBoundingClientRect().height>modal.getBoundingClientRect().height)
        modal=e;}
  }
  const root=modal||document.body;

  // ★ 中列：模态根里那个 MAIN（★ 源站用 <main>）
  let main=null;
  for(const e of root.querySelectorAll('main')){
    const r=e.getBoundingClientRect();
    if(r.width>0&&r.height>0){main=e;break;}
  }
  if(!main) return {err:'找不到 MAIN'};

  const walk=(e,d)=>{
    const o={t:e.tagName,c:String(e.getAttribute('class')||'').slice(0,400),
             b:box(e),n:e.children.length};
    const t=txt(e); if(t&&t.length<=60)o.x=t.slice(0,60);
    if(e.tagName==='IMG')o.src=e.getAttribute('src')||'';
    if(e.tagName==='CANVAS'){o.cw=e.width;o.ch=e.height;}
    if(e.tagName==='BUTTON'||e.getAttribute('role')){
      o.ar=e.getAttribute('aria-label')||'';
      o.ap=e.getAttribute('aria-pressed')||'';
      o.ac=e.getAttribute('aria-current')||'';
      o.ds=e.getAttribute('data-state')||'';}
    o.s=st(e);
    if(d<12&&e.children.length)o.c2=[...e.children].map(k=>walk(k,d+1));
    return o;};

  const out={};
  out['★模态根']={b:box(root),c:String(root.getAttribute('class')||'').slice(0,300),
                  s:st(root)};
  // ★★ 模态根的**直接子元素**（★ 用来机器提取「内容框」的盒 ⟹ ⟹ 不靠手打原点）
  out['★模态根的子']=[...root.children].slice(0,6).map(e=>({
    t:e.tagName,c:String(e.getAttribute('class')||'').slice(0,160),
    b:box(e),s:st(e)}));
  out['★中列']=walk(main,0);
  // ★ 两枚取景按钮的**同级兄弟**（★ 用来找那枚分隔线）
  out['★取景按钮父级']=[...document.querySelectorAll('button[aria-label="半身"],button[aria-label="全身"]')]
    .map(b=>({ar:b.getAttribute('aria-label'),b:box(b),
              c:String(b.getAttribute('class')||'').slice(0,300),
              parent:{t:b.parentElement?b.parentElement.tagName:'',
                      c:b.parentElement?String(b.parentElement.getAttribute('class')||'').slice(0,300):'',
                      b:b.parentElement?box(b.parentElement):null,
                      kids:[...b.parentElement.children].map(k=>({
                        t:k.tagName,c:String(k.getAttribute('class')||'').slice(0,120),
                        b:box(k),vis:getComputedStyle(k).visibility,
                        op:getComputedStyle(k).opacity,
                        bg:getComputedStyle(k).backgroundColor,
                        bgi:getComputedStyle(k).backgroundImage.slice(0,160)}))}}));
  return out;}"""


def read_credit(pg):
    return pg.evaluate("""()=>{
      const t=document.body.innerText||'';
      const m=t.match(/⚡\s*(\\d+)/);
      return m?Number(m[1]):null;}""")


def click_framing(pg, label):
    """★ 点中列右下角那枚取景按钮（★ 按 aria-label 精确点 ⟹ 不靠坐标猜）。"""
    return pg.evaluate("""(label)=>{
      const b=[...document.querySelectorAll('button[aria-label]')]
        .find(e=>e.getAttribute('aria-label')===label);
      if(!b)return 'no-btn';
      const r=b.getBoundingClientRect();
      if(r.width<=0||r.height<=0)return 'no-box';
      b.click(); return 'clicked';}""", label)


def main():
    out = {"★阶段": []}
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
                    pg.mouse.click(bb["x"] + bb["width"] / 2,
                                   bb["y"] + bb["height"] / 2)
            pg.wait_for_timeout(5000)
            tab = pg.query_selector("button:text-is('官方角色库')")
            if tab:
                bb = tab.bounding_box()
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
            pg.wait_for_timeout(6000)

            for stage, action, shot in (
                ("default", None, "default"),
                ("half", "半身", "half"),
                ("full", "全身", "full"),
            ):
                rec = {"★阶段": stage}
                try:
                    c0 = read_credit(pg)
                    if action:
                        rec["★点击"] = click_framing(pg, action)
                        pg.wait_for_timeout(2500)
                    c1 = read_credit(pg)
                    rec["★积分_点前"] = c0
                    rec["★积分_点后"] = c1
                    rec["★积分是否变化"] = (c0 != c1)
                    if c0 != c1:
                        rec["★★ 积分变了 ⟹ 立刻停"] = True
                        raise SystemExit("积分变了")
                    reading = pg.evaluate(DUMP)
                    (RAW / ("source-850-%s.json" % stage)).write_text(
                        json.dumps(reading, ensure_ascii=False, indent=1),
                        encoding="utf-8")
                    p = RAW / ("source-850-%s.png" % shot)
                    pg.screenshot(path=str(p))
                    rec["★截图"] = "raw/" + p.name
                    rec["★是否找到中列"] = bool(reading.get("★中列"))
                    if reading.get("★中列"):
                        m = reading["★中列"]
                        rec["★中列盒"] = m.get("b")
                        rec["★中列class"] = m.get("c")
                    rec["★取景按钮数"] = len(reading.get("★取景按钮父级") or [])
                except SystemExit:
                    raise
                except Exception:
                    rec["★异常"] = traceback.format_exc()
                out["★阶段"].append(rec)
                (RAW / "source-850-preview.json").write_text(
                    json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    except SystemExit:
        pass
    except Exception:
        out["异常"] = traceback.format_exc()
    finally:
        RAW.mkdir(parents=True, exist_ok=True)
        (RAW / "source-850-preview.json").write_text(
            json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", RAW / "source-850-preview.json")
        if out.get("异常"):
            print("异常：", out["异常"])
        for rec in out.get("★阶段", []):
            print("%-8s 点击=%-8s 积分变化=%s 中列盒=%s 按钮数=%s"
                  % (rec.get("★阶段"), rec.get("★点击", "-"),
                     rec.get("★积分是否变化"), rec.get("★中列盒"),
                     rec.get("★取景按钮数")))
            if rec.get("★异常"):
                print("   异常：", rec["★异常"][-300:])


if __name__ == "__main__":
    sys.exit(main())

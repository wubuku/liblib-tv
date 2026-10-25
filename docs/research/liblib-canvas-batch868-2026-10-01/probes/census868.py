#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 868 普查探针：★ 找「**看着可点、点了没反应**」的控件。

## ★ 靶子（★ 为什么这是本批的靶子）

★ 目标里有一条硬要求：★ 「**检查之前已有的复刻成果**，如发现『糊弄』之处，
★ 如有检出必须整改到位」⟹ ⟹ 而「糊弄」在界面上的**典型形状**是：

★ ★★ **一个控件长得像按钮 ⟹ ⟹ 鼠标有 hover 反馈 ⟹ ⟹ 指针变成 pointer
   ⟹ ⟹ 点下去 ⟹ ⟹ ★ **什么也没发生** ⟹ ⟹ ★ 而它**又没有**任何「我这里是惰性的」标记。**

★ 而本仓**已经有**一套自证惰性的约定（`data-inert` ＋ `title` 说明）⟹ ⟹
★ 所以「**没标 `data-inert` ＋ 点了没反应**」⟹ ⟹ 就是**真糊弄**。

## ★ ★★ 判据一：★ 「点了没反应」必须**排除**四种**假死**

★ 第一版只拿「body 的 innerHTML 长度 ＋ innerText 长度」当签名 ⟹ ⟹ 抓到 3 个「死」⟹ ⟹
★ ★★ 逐条查下去 ⟹ ⟹ ★ **三个全是判据自己的问题** ⟹ ⟹ ⟹ ⟹ ⇒ 判据**必须**升级：

| 假死形状 | 现象 | 修法 |
| --- | --- | --- |
| ★ **换页后长度相同** | 点导航链接去了另一个页 ⟹ ⟹ 但两页 `innerHTML` 长度**恰好一样** ⟹ ⟹ 签名没变 ⟹ ⟹ 判成「死」 | ★ 签名里加 **`location.href`** ＋ 改成**内容哈希**（不再用长度） |
| ★ **「聚焦」不算变化** | 点文本输入框 ⟹ ⟹ 只是获得焦点 ⟹ ⟹ `innerText` 没变 ⟹ ⟹ 判成「死」 | ★ 签名里加 **`document.activeElement`** |
| ★ **点了打开了新标签** | 点站点导航 ⟹ ⟹ 新标签打开 ⟹ ⟹ 当前页**没动** | ★ 监听**新 page** 数量 |
| ★ **重复点当前选中项** | 「工作流／故事板」是二选一 ⟹ ⟹ 点**已经选中**的那个 ⟹ ⟹ 状态**本来就不该变** | ★ 见判据二（**同组兄弟对照**） |

## ★ ★★ 判据二：★ 「死」要靠**同组兄弟**做阳性对照才能定性

★ 一个控件点了没反应 ⟹ ⟹ 有**三种**可能 ⟹ ⟹ 必须分开：
  ① **它本来就该没反应**（幂等：重复点当前选中项）⟹ ⟹ **不是糊弄**
  ② **同组的兄弟有反应、它没有** ⟹ ⟹ **它坏了**（真糊弄）★ 这就是**阳性对照**
  ③ **它是一个「展示当前值」的输入框** ⟹ ⟹ 点击＝聚焦 ⟹ ⟹ **不是糊弄**

★ ⇒ 所以判据必须**成对**跑：★ 死控件 ⟹ ⟹ 找**同组兄弟**（相同 `data-*` 属性名
★ 或相同父容器）⟹ ⟹ **也点一遍** ⟹ ⟹ 兄弟有反应 ⟹ ⟹ ⇒ 它就是**坏了**。

## ★ ★★ 判据三：★ 页面自己会动 ⟹ ⟹ 一律判「不可判」

★ 页面有动画／定时器 ⟹ ⟹ 任何两次快照都不同 ⟹ ⟹ 「点了没反应」**恒假**。
★ ⇒ 所以每个控件要**点四次**：`pre1` / `pre2`（点前 1.5s）⟹ ⟹ 要求相等（页面静）
★ ⇒ ⟹ ⟹ `after1`（点后 600ms）⟹ ⟹ `after2`（点后 2.4s）⟹ ⟹ 要求相等（点击没引入变化）
★ ⇒ ⟹ ⟹ **三者全等**才叫「点了没反应」。

## ★ ★★ 两个必须处理的技术坑

★ ① **引导蒙层会吞掉点击** ⟹ ⟹ 导演台默认带一层 coachmark（`跳过`／`下一步`）
   ⟹ ⟹ 它盖住的地方 ⟹ ⟹ 点击全被它吃掉 ⟹ ⟹ ⟹ ⟹ ⇒ 那些控件会被**误判成死的**。
   ★ ⇒ 枚举**之前**先把蒙层关掉 ⟹ ⟹ 蒙层那两枚按钮**单独**测。
★ ② **重载后要能重新定位到同一个控件** ⟹ ⟹ 索引会漂 ⟹ ⟹
   ★ ⇒ 每个控件**带一个稳定定位器**（`data-*` 属性 > `aria-label` > 可见文本 > 序号）。

## ★ 输出
  raw/census-868.json
"""
from __future__ import annotations

import json
import pathlib
import sys

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch868-2026-10-01"
RAW = BATCH / "raw"
BASE = "http://localhost:4317"

SELECTORS = [
    "button",
    "[role='button']",
    "a[href]",
    "[role='switch']",
    "[role='tab']",
    "[role='menuitem']",
    "[role='option']",
    "input:not([type='hidden'])",
    "select",
    "textarea",
]

# ★ ★★ 两个签名：★ 「强」与「强＋焦点」
#   ⟹ ⟹ ★ strong ＝ href ＋ innerText 哈希 ＋ innerHTML 长度（**不含**焦点）
#   ⟹ ⟹ ★ focus ＝ strong ＋ activeElement 签名
#   ⟹ ⟹ ★ ★★ 为什么必须拆成两个：★ 点**任何**按钮都会让它**获得焦点**
#   ⟹ ⟹ ⟹ ⟹ ⇒ 若把焦点算进「变化」⟹ ⟹ ⟹ ⟹ ⇒ 「有反应」这个判据**恒真**
#   ⟹ ⟹ ⟹ ⟹ ⟹ ⇒ ⇒ 那样**任何糊弄都测不出来**（★ 这正是第一版的第二个教训）
#   ⟹ ⟹ ⟹ ⟹ ⟹ ⇒ ★ 所以：**只有焦点变了** ⟹ ⟹ 记成「只变焦点」⟹ ⟹ **不判死**
#   ⟹ ⟹ ⟹ ⟹ ⟹ ⇒ ★ 但它要**单独记下来** ⟹ ⟹ ⟹ ⟹ ⟹ ⇒ 因为「点它只是聚焦」
#   ⟹ ⟹ ⟹ ⟹ ⟹ ⇒ ⟹ ⟹ 对**按钮**是**正常**的 ⟹ ⟹ 对**输入框**也是**正常**的
SIGNATURE = r"""()=>{
  const h = (s)=>{let x=0x811c9dc5;for(let i=0;i<s.length;i++){x^=s.charCodeAt(i);x=(x*0x01000193)>>>0;}return x.toString(16);};
  const b=document.body;
  if(!b) return {strong:'NOBODY', focus:'NOBODY'};
  const strong = [location.href, h(b.innerText), b.innerHTML.length].join('~');
  const ae=document.activeElement;
  const aeSig = ae
    ? (ae.tagName+'|'+String(ae.getAttribute('aria-label')||'')
       +'|'+String(ae.getAttribute('data-workspace-name')||'')
       +'|'+String(ae.getAttribute('data-director-object-name')||'')
       +'|'+String(ae.getAttribute('name')||''))
    : 'NONE';
  return {strong: strong, focus: strong+'~'+aeSig};
}"""

ENUMERATE = r"""(sels)=>{
  const out = [];
  const seen = new Set();
  const q = (s)=>'\"'+String(s).replace(/\"/g,'\\\"')+'\"';
  for(const sel of sels){
    let list;
    try{ list = document.querySelectorAll(sel); }catch(e){ continue; }
    for(const e of list){
      if(seen.has(e)) continue;
      seen.add(e);
      const r = e.getBoundingClientRect();
      if(r.width <= 0 || r.height <= 0) continue;
      if(e.hasAttribute('data-inert')) continue;
      if(e.hasAttribute('disabled')) continue;
      if(e.getAttribute('aria-disabled') === 'true') continue;
      if(e.closest('[data-inert]')) continue;
      const cs = getComputedStyle(e);
      if(cs.visibility === 'hidden' || cs.display === 'none') continue;
      if(cs.pointerEvents === 'none') continue;
      const ds = {};
      for(const a of e.attributes){
        if(a.name.startsWith('data-')) ds[a.name] = a.value;
      }
      const tag = e.tagName.toLowerCase();
      const aria = e.getAttribute('aria-label') || '';
      const text = (e.textContent||'').trim().slice(0,30);
      let loc = null, how = '';
      const dkeys = Object.keys(ds).filter(k=>ds[k]!=='');
      if(dkeys.length){
        const k = dkeys[0];
        loc = tag+'['+k+'='+q(ds[k])+']';
        how = 'data:'+k;
      } else if(aria){
        loc = tag+'[aria-label='+q(aria)+']';
        how = 'aria';
      } else if(text){
        loc = tag+':has-text('+q(text)+')';
        how = 'text';
      }
      // ★ 分组键：★ 同组 = 相同「data-* 属性名」或相同「父容器 + 标签」
      const parent = e.parentElement;
      const pds = parent ? Array.from(parent.attributes).filter(a=>a.name.startsWith('data-')).map(a=>a.name) : [];
      const group = dkeys.length
        ? (tag+'#'+dkeys.slice().sort().join('+'))
        : (tag+'@'+(pds.length?pds.sort().join('+'):(parent?parent.tagName.toLowerCase():'root')));
      out.push({
        idx: out.length, tag, role: e.getAttribute('role')||'',
        text, aria, title: e.getAttribute('title')||'',
        type: e.getAttribute('type')||'', data: ds, how, loc, group,
        ariaPressed: e.getAttribute('aria-pressed'),
        ariaSelected: e.getAttribute('aria-selected'),
        ariaCurrent: e.getAttribute('aria-current'),
        cls: (e.getAttribute('class')||'').slice(0,140),
        x: Math.round(r.x), y: Math.round(r.y),
        w: Math.round(r.width), h: Math.round(r.height),
        cursor: cs.cursor, opacity: cs.opacity,
      });
    }
  }
  return out;
}"""

OPEN_DIRECTOR = r"""()=>{
  const card = document.querySelector('.react-flow__node-script-execution');
  if(!card) return {ok:false, why:'没有导演台卡片'};
  const r = card.getBoundingClientRect();
  return {ok:true, x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2)};
}"""

FIND_OPEN_BTN = r"""()=>{
  const card = document.querySelector('.react-flow__node-script-execution');
  if(!card) return null;
  const b = card.querySelector('[data-open-director]')
        || Array.from(card.querySelectorAll('button')).find(x=>(x.textContent||'').includes('打开导演台'));
  if(!b) return null;
  const r = b.getBoundingClientRect();
  return {x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2)};
}"""

DISMISS_COACHMARK = r"""()=>{
  const b = document.querySelector('[data-director-coachmark-skip]');
  if(!b) return {found:false};
  b.click();
  return {found:true};
}"""


def sig(pg) -> dict:
    return pg.evaluate(SIGNATURE)


def cleanup(pg) -> None:
    pg.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")


def open_root(pg) -> None:
    pg.goto(BASE + "/", wait_until="domcontentloaded")
    pg.wait_for_timeout(2200)
    cleanup(pg)
    try:
        pg.wait_for_function("() => Boolean(window.__libtv_store)", timeout=45_000)
    except Exception:  # noqa: BLE001
        pass
    pg.wait_for_timeout(1200)


def open_director(pg, dismiss=True) -> None:
    open_root(pg)
    info = pg.evaluate(OPEN_DIRECTOR)
    if not info.get("ok"):
        raise RuntimeError("打不开导演台：%s" % info.get("why"))
    pg.mouse.move(info["x"], info["y"])
    pg.wait_for_timeout(400)
    btn = pg.evaluate(FIND_OPEN_BTN)
    if not btn:
        raise RuntimeError("导演台卡片上找不到「打开导演台」按钮")
    pg.mouse.move(btn["x"], btn["y"])
    pg.wait_for_timeout(300)
    pg.mouse.click(btn["x"], btn["y"])
    pg.wait_for_timeout(1500)
    cleanup(pg)
    if dismiss:
        pg.evaluate(DISMISS_COACHMARK)
        pg.wait_for_timeout(700)
    pg.wait_for_timeout(500)


def locate(pg, c):
    if c.get("loc"):
        try:
            el = pg.locator(c["loc"]).first
            if el.count() and el.is_visible():
                return el
        except Exception:  # noqa: BLE001
            pass
    return None


def click_test(pg, ctx, c) -> dict:
    """★ 点四次法 ⟹ ⟹ 返回一条判定记录。"""
    n_pages_before = len(ctx.pages)
    pre1 = sig(pg)
    pg.wait_for_timeout(1500)
    pre2 = sig(pg)
    if pre1["strong"] != pre2["strong"] or pre1["focus"] != pre2["focus"]:
        return {"控件": c, "判定": "不可判", "原因": "页面自己在动（pre1≠pre2）"}
    el = locate(pg, c)
    try:
        if el is not None:
            el.click(timeout=5000, force=True)
        else:
            pg.mouse.click(c["x"], c["y"])
    except Exception as e:  # noqa: BLE001
        return {"控件": c, "判定": "不可判", "原因": "点不到：%s" % str(e)[:140]}
    pg.wait_for_timeout(600)
    a1 = sig(pg)
    pg.wait_for_timeout(1800)
    a2 = sig(pg)
    if len(ctx.pages) > n_pages_before:
        return {"控件": c, "判定": "有反应", "原因": "打开了新标签页"}
    if a1["strong"] != a2["strong"] or a1["focus"] != a2["focus"]:
        return {"控件": c, "判定": "有反应", "原因": "点后页面在动"}
    if a1["strong"] != pre1["strong"]:
        return {"控件": c, "判定": "有反应", "原因": "点后状态变了（href/文本/DOM 长度）"}
    if a1["focus"] != pre1["focus"]:
        return {"控件": c, "判定": "只变焦点",
                "原因": "★ 只有 activeElement 变了 ⟹ ⟹ 点它只是**获得焦点** ⟹ ⟹ 不是糊弄"}
    return {"控件": c, "判定": "死", "原因": "点了什么也没发生（页面静 ＋ 前后无差异 ＋ 连焦点都没拿到）"}


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "enumerate"
    only = sys.argv[2] if len(sys.argv) > 2 else ""
    out: dict = {"mode": mode, "base": BASE}
    RAW.mkdir(parents=True, exist_ok=True)
    try:
        with sync_playwright() as pw:
            br = pw.chromium.launch(headless=True)
            ctx = br.new_context(viewport={"width": 1920, "height": 1080},
                                 locale="zh-CN")
            pg = ctx.new_page()
            pg.set_default_timeout(30_000)
            pg.on("dialog", lambda d: d.dismiss())

            # ── 引导蒙层：**单独**测（★ 它会吞点击 ⟹ ⟹ 不能混在普查里）
            coach = {}
            open_director(pg, dismiss=False)
            coach["枚举时存在"] = pg.evaluate(
                "()=>Boolean(document.querySelector('[data-director-coachmark-skip]'))")
            pre = sig(pg)["strong"]
            pg.locator("[data-director-coachmark-skip]").first.click(force=True)
            pg.wait_for_timeout(800)
            coach["点「跳过」后蒙层还在"] = pg.evaluate(
                "()=>Boolean(document.querySelector('[data-director-coachmark-skip]'))")
            coach["点「跳过」有反应"] = sig(pg)["strong"] != pre
            out["引导蒙层"] = coach

            for scope in ("root", "director"):
                if only and scope != only:
                    continue
                out[scope] = {}
                if scope == "root":
                    open_root(pg)
                else:
                    open_director(pg)
                out[scope]["URL"] = pg.url
                controls = pg.evaluate(ENUMERATE, SELECTORS)
                out[scope]["控件数"] = len(controls)
                out[scope]["控件"] = controls
                if mode == "enumerate":
                    continue

                # ★ ★★ 按**组**跑：★ 每组测一个代表 ⟹ ⟹ 死了再测第二个成员做**阳性对照**
                groups: dict = {}
                for c in controls:
                    groups.setdefault(c["group"], []).append(c)
                out[scope]["组数"] = len(groups)
                results = []
                for gname, members in groups.items():
                    rep = members[0]
                    if scope == "root":
                        open_root(pg)
                    else:
                        open_director(pg)
                    r = click_test(pg, ctx, rep)
                    r["组"] = gname
                    r["组员数"] = len(members)
                    if r["判定"] == "死" and len(members) > 1:
                        # ★ 阳性对照：★ 再点一个同组的兄弟 ⟹ ⟹ 兄弟有反应 ⟹ ⟹ 它坏了
                        sib = members[1]
                        if scope == "root":
                            open_root(pg)
                        else:
                            open_director(pg)
                        r2 = click_test(pg, ctx, sib)
                        r["同组兄弟"] = {"兄弟": sib["aria"] or sib["text"] or sib["idx"],
                                        "兄弟判定": r2["判定"], "兄弟原因": r2["原因"]}
                    results.append(r)
                out[scope]["逐组"] = results
                dead = [r for r in results if r["判定"] == "死"]
                out[scope]["死控件"] = [r["控件"] for r in dead]
                out[scope]["不可判"] = [r for r in results if r["判定"] == "不可判"]
                out[scope]["有反应"] = [r for r in results if r["判定"] == "有反应"]
                out[scope]["只变焦点"] = [r for r in results if r["判定"] == "只变焦点"]
    except Exception as e:  # noqa: BLE001
        import traceback
        out["异常"] = traceback.format_exc()[-2500:]
        out["异常摘要"] = str(e)[:400]
    (RAW / ("census-868-%s.json" % (only or "all"))).write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    for scope in ("root", "director"):
        if scope in out and isinstance(out[scope], dict):
            print("== %s == 控件 %s ／ 组 %s" % (
                scope, out[scope].get("控件数"), out[scope].get("组数")))
            if mode != "enumerate":
                print("   ★ 死 %s ／ 不可判 %s ／ 有反应 %s ／ 只变焦点 %s" % (
                    len(out[scope].get("死控件", [])),
                    len(out[scope].get("不可判", [])),
                    len(out[scope].get("有反应", [])),
                    len(out[scope].get("只变焦点", []))))
    if "引导蒙层" in out:
        print("== 引导蒙层 ==", out["引导蒙层"])
    print("读数已落盘：%s" % (RAW / ("census-868-%s.json" % (only or "all"))))
    return 0


if __name__ == "__main__":
    sys.exit(main())

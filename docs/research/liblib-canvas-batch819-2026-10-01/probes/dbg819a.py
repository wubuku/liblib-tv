#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 819 探针 —— ★ **用户知不知道自己撤不掉**？

## 起点（818 自开的「本批最该接着做的一条」）

818 量到：连点 60 次 ⟹ 历史封顶在 50 ⟹ **前 10 份永远撤不掉**。
818 的「不声称」里明写：

> 静态读数：`page.tsx:496` 的 `canUndo = (historyStack?.past.length ?? 0) > 0`
> 传给 `page.tsx:1659` 的 `CanvasContextMenu` ⟹ **pane 右键菜单**里的
> 「撤销」项（`CanvasContextMenu.tsx:128`）会随 `past` 空而 **disabled**。
> ★ 推论（**没量**）：撤到底之后 UI 会说「撤销用完了」，而画布上还有 10 份
> **永远撤不掉**的产物 ⟹ 用户**看不到**这件事。

⟹ 本批就是量这条推论。

## ★ 「扫不到提示」这类读数，**必须先证明扫描器没坏**

「全页没有任何提示」是一个**否定性读数**，而否定性读数最容易是
**探针自己坏了**（选择器太窄、扫的不是可见元素……）。

⟹ 所以本批的扫描器**每次都先自检**：往页面里注入一个带 `role=alert`
的探针节点 ⟹ **必须扫得到它** ⟹ 然后删掉探针、再扫真实 DOM。
★ 这是 809「注入坏链接探针验证扫描器本身没坏」的同款做法，
  只是对象从 Markdown 链接换成了 DOM 选择器。
"""
import json
import os
import pathlib
import sys
import time
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent /
                       "liblib-canvas-batch774-2026-10-01" / "probes"))
import dbg774a as A  # noqa: E402
sys.path.insert(0, str(HERE.parent.parent /
                       "liblib-canvas-batch811-2026-10-01" / "probes"))
import dbg811a as P811  # noqa: E402

OUT = pathlib.Path(os.environ.get("VB819_OUT") or
                   (HERE.parent / "raw" / "vb819a.json"))
IMG = "i-1FQ9tErTcC"
LABEL = "旋转"
HOWMANY = 60

SEL = """()=>Array.from(window.__libtv_store.getState().selectedNodeIds||[]);"""

GRAPH = """()=>{const S=window.__libtv_store.getState();
  const c=S.canvases.find(x=>x.id===S.activeCanvasId);
  const h=S.historyByCanvas[S.activeCanvasId]||{past:[],future:[]};
  return {nodeIds:c.nodes.map(n=>n.id).sort(),edges:c.edges.length,
          past:h.past.length,future:h.future.length};}"""

#: ★ 找一个**确实落在 `.react-flow__pane` 上**的点
#: （816 的教训：写死坐标可能在画布外 ⟹ 夹具失败会伪装成读数）
PANE = """()=>{const W=window.innerWidth,H=window.innerHeight;
  for(let y=120;y<H-140;y+=40)for(let x=120;x<W-120;x+=40){
    const e=document.elementFromPoint(x,y);
    if(e&&e.classList&&e.classList.contains('react-flow__pane'))
      return {x,y,命中类名:e.className};}
  return null;}"""

MENU = """()=>{const m=document.querySelector('[data-canvas-context-menu]');
  if(!m)return null;
  return {变体:m.getAttribute('data-canvas-context-variant'),
          菜单项:Array.from(m.querySelectorAll('[data-canvas-context-item]'))
            .map(e=>({名称:(e.getAttribute('data-canvas-context-item')||'').trim(),
                      disabled:e.disabled===true})),
          可见文本:(m.textContent||'').trim().replace(/\\s+/g,' ')};}"""

#: ★★ 提示扫描 ＋ **扫描器自检**
HINT = """()=>{
  const SELS=['[role=status]','[role=alert]','[role=log]','[aria-live]',
              '[data-toast]','[data-sonner-toast]','[class*=toast]','[class*=Toast]',
              '[class*=snack]','[class*=banner]','[class*=warning]','[class*=alert]'];
  const scan=()=>{const out=[];const seen=new Set();
    for(const s of SELS)for(const e of Array.from(document.querySelectorAll(s))){
      if(seen.has(e))continue;seen.add(e);
      const r=e.getBoundingClientRect();
      if(r.width===0&&r.height===0)continue;
      out.push({选择器:s,文本:(e.textContent||'').trim().replace(/\\s+/g,' ').slice(0,60)});}
    return out;};
  // ★ 扫描器自检：注入探针，必须能扫到
  const probe=document.createElement('div');
  probe.setAttribute('role','alert');
  probe.setAttribute('data-probe','819');
  probe.style.cssText='position:fixed;left:0;top:0;width:10px;height:10px';
  probe.textContent='扫描器探针819';
  document.body.appendChild(probe);
  const selfTest=scan().filter(x=>x.文本==='扫描器探针819').length;
  probe.remove();
  // ★ 另外把所有**叶子节点**里提到「撤销/历史/还原/回退」的文案捞出来
  //   —— 防止「提示」长得不像提示（选择器扫不到但文字里说了）
  const said=Array.from(document.querySelectorAll('body *')).filter(e=>{
      if(e.children.length)return false;
      const t=(e.textContent||'').trim();
      return t&&t.length<=40&&/撤销|历史|还原|回退/.test(t);})
    .map(e=>({文本:(e.textContent||'').trim(),
              tag:e.tagName,
              禁用:e.disabled===true||e.getAttribute('aria-disabled')==='true'}));
  return {扫到:scan(),'★ 扫描器自检：注入探针能被扫到':selfTest>0,
          '★ 探针被扫到几次':selfTest,'提到撤销的叶子节点':said};}"""


def g(pg):
    return pg.evaluate(GRAPH)


def click_label(pg, label):
    for b in pg.query_selector_all("[data-image-toolbar] button"):
        for via, v in (("文字", (b.text_content() or "").strip()),
                       ("aria", b.get_attribute("aria-label") or ""),
                       ("title", b.get_attribute("title") or "")):
            if v == label:
                if b.is_disabled():
                    return "disabled", via
                b.click()
                return "clicked", via
    return "not-found", None


def open_pane_menu(pg):
    """打开 **pane** 右键菜单并把读数取回来（关掉）"""
    pane = pg.evaluate(PANE)
    if not pane:
        return {"FAILED": "找不到落在 pane 上的点"}
    pg.mouse.click(pane["x"], pane["y"], button="right")
    pg.wait_for_timeout(500)
    menu = pg.evaluate(MENU)
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(300)
    return {"拖拽点": pane, "菜单": menu}


def open_node_menu(pg, node_id):
    e = pg.query_selector('.react-flow__node[data-id="%s"]' % node_id)
    if not e:
        return {"FAILED": "拿不到节点"}
    bb = e.bounding_box()
    pg.mouse.click(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2,
                   button="right")
    pg.wait_for_timeout(500)
    menu = pg.evaluate(MENU)
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(300)
    return {"菜单": menu}


def run(b, label, how_many):
    pg = b.new_page()
    pg.set_default_timeout(25000)
    try:
        P811.boot(pg)
        pg.evaluate(P811.SELECT, [IMG])
        pg.wait_for_timeout(800)
        if not P811.ensure_visible(pg, IMG).get("★ 在视口内"):
            return {"FAILED": "图片节点不在视口"}

        g0 = g(pg)
        base = {"节点数": len(g0["nodeIds"]), "历史": g0["past"]}

        # ── 时刻 T1：起点（past 应该是空的）
        t1_pane = open_pane_menu(pg)
        t1_hint = pg.evaluate(HINT)

        # ── 连点 N 次
        made, prev = [], list(g0["nodeIds"])
        for k in range(1, how_many + 1):
            if k > 1:
                pg.evaluate(P811.SELECT, [IMG])
                pg.wait_for_timeout(600)
                P811.ensure_visible(pg, IMG)
            r, _ = click_label(pg, label)
            if r != "clicked":
                return {"FAILED": "第%d 下没点上：%s" % (k, r)}
            pg.wait_for_timeout(800)
            cur = g(pg)
            made.extend(sorted(set(cur["nodeIds"]) - set(prev)))
            prev = list(cur["nodeIds"])
        made_set = set(made)

        # ── 时刻 T2：连点之后（past 应该是满的）
        # ★ 探针返工（第二次）：第一版写 `g(prev)["past"]` —— `prev` 是
        #   **id 列表**、不是 page ⟹ `AttributeError: 'list' object has no
        #   attribute 'evaluate'` ⟹ 而且它抛在**构造返回值**那一刻，
        #   ⟹ 前 150 秒算出来的读数**全丢**。★ **探针要把「读数全部拿到
        #     之后再组装」当纪律**：中途抛异常等于整条臂白跑。
        t2_pane = open_pane_menu(pg)
        t2_hint = pg.evaluate(HINT)

        # ── 撤到底
        for _ in range(how_many + 5):
            pg.keyboard.press("Meta+z")
            pg.wait_for_timeout(650)
        g_end = g(pg)
        remain = [v for v in g_end["nodeIds"] if v in made_set]

        # ── 时刻 T3：撤到底之后（past 空，但画布上还有东西撤不掉）
        t3_pane = open_pane_menu(pg)
        t3_hint = pg.evaluate(HINT)
        # ★ 探针返工（**跑之前就预判到的夹具 bug**）：第一版在 T3 去右键
        #   `made[-1]`（最后建的那份）—— ★ 但撤到底之后它**已经被撤掉了**、
        #   DOM 里根本没有这个节点 ⟹ 这条臂会记成「拿不到节点」。
        #   ⟹ 修法：右键**幸存**的那一份（`remain` 里最后一个）。
        #   ★ 这正是 816 那条「拖拽点必须在 pane 上」的同款纪律：
        #   **夹具指向一个此刻不存在的元素**，读数会变成「功能没有」。
        t3_node = (open_node_menu(pg, remain[-1]) if remain
                   else {"FAILED": "一份都没剩下"})

        # ── T3 时再按一次 Cmd+Z：有没有**任何**反应
        before = {"节点数": len(g_end["nodeIds"]), "历史": g_end["past"],
                  "选区": list(pg.evaluate(SEL) or [])}
        pg.evaluate(P811.SELECT, [IMG])
        pg.wait_for_timeout(600)
        pg.keyboard.press("Meta+z")
        pg.wait_for_timeout(800)
        g_a = g(pg)
        after = {"节点数": len(g_a["nodeIds"]), "历史": g_a["past"],
                 "选区": list(pg.evaluate(SEL) or [])}
        after_hint = pg.evaluate(HINT)

        # ── 时刻 T4：T3 之后还有没有**自救窄路**？
        # ★ `redo()`（`canvasStore.ts:3965`）会把当前快照**推回 `past`**：
        #   `past: [...history.past, cloneGraphSnapshot(...)].slice(-MAX_HISTORY)`
        #   ⟹ 在 T3（past 空、future 50 条）按一次重做，**撤销又变回可按**。
        #   ★ 所以结论不是「完全无解」，而是「有一条**只能横跳、
        #     永远回不到起点**的窄路」—— 而 UI 里**没有任何文案**说这条窄路存在。
        def rd():
            c = g(pg)
            return {"节点数": len(c["nodeIds"]), "历史": c["past"],
                    "future": c["future"],
                    "还剩几份": len([v for v in c["nodeIds"] if v in made_set]),
                    "★ 回到起点": len(c["nodeIds"]) == base["节点数"]
                    and c["past"] == base["历史"]}

        t4 = {"T3 之后": rd()}
        pg.keyboard.press("Meta+Shift+z")
        pg.wait_for_timeout(800)
        t4["重做一次之后"] = rd()
        pg.evaluate(P811.SELECT, [IMG])
        pg.wait_for_timeout(500)
        pg.keyboard.press("Meta+z")
        pg.wait_for_timeout(800)
        t4["再撤销一次之后"] = rd()
        # 连按 12 次重做，看 future 会不会被吃光
        for _ in range(12):
            pg.keyboard.press("Meta+Shift+z")
            pg.wait_for_timeout(450)
        t4["连按 12 次重做之后"] = rd()
        t4_pane = open_pane_menu(pg)
        t4["pane菜单"] = t4_pane
        t4_hint = pg.evaluate(HINT)
        t4["提示"] = t4_hint

        return {
            "label": label, "howmany": how_many,
            "起点": base,
            "★ T4·横跳": t4,
            "★ 建出来的 id 数": len(made),
            "★ T1·起点": {"图": base, "pane菜单": t1_pane, "提示": t1_hint},
            "★ T2·连点之后": {"历史": g(pg)["past"], "pane菜单": t2_pane,
                             "提示": t2_hint},
            "★ T3·撤到底": {"图": {"节点数": len(g_end["nodeIds"]),
                                  "历史": g_end["past"],
                                  "★ 还剩几份撤不掉": len(remain)},
                             "pane菜单": t3_pane, "提示": t3_hint,
                             "节点右键菜单": t3_node},
            "★ T3·再按一次 Cmd+Z": {"之前": before, "之后": after,
                                 "节点数变了": before["节点数"] != after["节点数"],
                                 "历史变了": before["历史"] != after["历史"],
                                 "★ 之后有没有出现任何提示":
                                     after_hint["扫到"],
                                 "★ 扫描器自检": after_hint["★ 扫描器自检：注入探针能被扫到"]},
        }
    except Exception as e:  # noqa: BLE001
        return {"FAILED": "%s: %s" % (type(e).__name__, e)}
    finally:
        try:
            pg.close()
        except Exception:  # noqa: BLE001
            pass


def main():
    out = {"base": A.BASE, "img": IMG, "label": LABEL, "howmany": HOWMANY,
           "cells": []}
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        t0 = time.time()
        c = run(br, LABEL, HOWMANY)
        c["round"] = 0
        c["secs"] = round(time.time() - t0, 1)
        out["cells"].append(c)
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                       encoding="utf-8")
        t3 = (c.get("★ T3·撤到底") or {})
        t4 = c.get("★ T4·横跳") or {}
        print("T4: 重做后=%s 撤后=%s 连重做12次后=%s 回到起点=%s | %ss" % (
            json.dumps(t4.get("重做一次之后"), ensure_ascii=False),
            json.dumps(t4.get("再撤销一次之后"), ensure_ascii=False),
            json.dumps(t4.get("连按 12 次重做之后"), ensure_ascii=False),
            (t4.get("连按 12 次重做之后") or {}).get("★ 回到起点"),
            c.get("secs")), flush=True)
        print("%s | T3 剩%s份 历史%s | T3 pane撤销disabled=%s | T3 扫到提示%s | 再按无反应=%s | %ss" % (
            c.get("FAILED") or "ok", (t3.get("图") or {}).get("★ 还剩几份撤不掉"),
            (t3.get("图") or {}).get("历史"),
            [i["disabled"] for i in ((t3.get("pane菜单") or {}).get("菜单") or {})
             .get("菜单项", []) if i["名称"] == "撤销"],
            (t3.get("提示") or {}).get("扫到"),
            not (c.get("★ T3·再按一次 Cmd+Z") or {}).get("节点数变了"),
            c.get("secs")), flush=True)
        br.close()
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("written", OUT)


if __name__ == "__main__":
    main()
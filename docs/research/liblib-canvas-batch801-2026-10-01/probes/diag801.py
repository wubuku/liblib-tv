#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 801 诊断：`Cmd+D`（复制快捷键）到底有没有生效？

801 的 `copyFlatGroup` 臂读数显示：造组后 14 个节点，按 `Meta+d` 之后**还是 14 个**，
只有随后直接调 store 的 `duplicateSelectedNodes()` 才涨到 17 ⟹ 快捷键那次**没起作用**。

`:1381` 的分支读起来是对的，所以要么是事件没送到页面，要么是事件送到了但被挡掉。
本诊断只采集，不下结论：把 `keydown` 逐条记下来（key / code / metaKey / ctrlKey），
并同时记下每次按键之后的节点数与选区。
"""
import json
import pathlib
import sys
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent /
                       "liblib-canvas-batch774-2026-10-01" / "probes"))
import dbg774a as A  # noqa: E402

OUT = pathlib.Path("/tmp/d801.json")

TAP = """()=>{
  window.__k801 = [];
  window.addEventListener('keydown', (e)=>{
    window.__k801.push({key:e.key, code:e.code, metaKey:e.metaKey,
      ctrlKey:e.ctrlKey, shiftKey:e.shiftKey, altKey:e.altKey,
      defaultPrevented:e.defaultPrevented,
      tag:(e.target&&e.target.tagName)||null});
  }, true);
  window.addEventListener('keyup', (e)=>{
    window.__k801.push({__up:true, key:e.key, metaKey:e.metaKey});
  }, true);
  return {ok:true};}"""

STATE = """()=>{
  const S=window.__libtv_store.getState();
  const cv=S.canvases.find(c=>c.id===S.activeCanvasId)||S.canvases[0];
  return {total:cv.nodes.length, selected:[...S.selectedNodeIds],
    events:window.__k801 ? window.__k801.splice(0) : []};}"""


def snap(pg, label):
    s = pg.evaluate(STATE)
    print("  %-14s total=%-3s sel=%s" % (label, s["total"], s["selected"][:3]),
          flush=True)
    for e in s["events"]:
        print("        事件 %s" % json.dumps(e, ensure_ascii=False), flush=True)
    return s


def main():
    res = []
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True)
        pg = b.new_page()
        pg.set_default_timeout(60000)
        pg.goto(A.BASE, wait_until="domcontentloaded", timeout=90000)
        pg.evaluate(A.CLEAR_LS, A.LS_KEY)
        pg.set_viewport_size({"width": 1440, "height": 1000})
        pg.goto(A.BASE, wait_until="networkidle", timeout=90000)
        pg.wait_for_selector(".react-flow__node", timeout=60000)
        pg.wait_for_timeout(1300)
        pg.evaluate(TAP)
        snap(pg, "初始")

        # 造一个组
        ids = pg.evaluate("""()=>{
          const S=window.__libtv_store.getState();
          const cv=S.canvases.find(c=>c.id===S.activeCanvasId)||S.canvases[0];
          return cv.nodes.filter(n=>n.type!=='storyboard-group'&&!n.parentId)
            .slice(0,2).map(n=>n.id);}""")
        pg.evaluate("(ids)=>window.__libtv_store.getState().selectNodes(ids);", ids)
        snap(pg, "选中2个")
        pg.keyboard.press("g")
        pg.wait_for_timeout(800)
        snap(pg, "按G造组")

        print("  --- 试 Meta+d ---", flush=True)
        pg.keyboard.press("Meta+d")
        pg.wait_for_timeout(900)
        res.append(snap(pg, "Meta+d之后"))

        print("  --- 试 Control+d ---", flush=True)
        pg.keyboard.press("Control+d")
        pg.wait_for_timeout(900)
        res.append(snap(pg, "Ctrl+d之后"))

        print("  --- 试 Meta+Shift+D ---", flush=True)
        pg.keyboard.press("Meta+Shift+d")
        pg.wait_for_timeout(900)
        res.append(snap(pg, "Meta+Shift+d后"))

        print("  --- 试 Meta+z（撤销，对照：同类快捷键能不能通）---", flush=True)
        pg.keyboard.press("Meta+z")
        pg.wait_for_timeout(900)
        res.append(snap(pg, "Meta+z之后"))

        pg.close()
        b.close()
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()

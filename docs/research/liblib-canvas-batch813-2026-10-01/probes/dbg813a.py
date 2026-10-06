#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 813 探针 —— 「**重新选中源节点**再点一次」会怎样

## ★ 813 要补的是 812 的一个**推理漏洞**

812 测「连点两下」时，第二下是在**第一次触发之后立刻**点的 ——
而第一次触发会把**选区迁到新建的节点上**，于是工具栏与芯片「消失」了。
812 据此写下「store 层『又建了一遍』那条路径**用户走不到**」。

★ **但那条推理漏了一条路**：用户只要**重新选中原来那个源节点**，
工具栏就回来了 ⟹ 第二下**完全可达**。

全树调用点普查（本批先做的第一件事）：三个动作**各只有一个调用点**
（`VideoNode.tsx:201` / `:219` / `:257`）⟹ 没有第二条入口，
但**同一条入口可以被走第二次**。

⟹ 本批把 812 的三态读数在**「重新选中」这条真正可达的路径**上重做一遍。
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
sys.path.insert(0, str(HERE.parent.parent /
                       "liblib-canvas-batch812-2026-10-01" / "probes"))
import dbg812a as P12  # noqa: E402

OUT = pathlib.Path(os.environ.get("VB813_OUT") or
                   (HERE.parent / "raw" / "vb813a.json"))
VID = P811.VID


def snap(pg):
    g = P811.active(pg)
    return {"n": len(g["nodeIds"]), "e": g["edges"], "past": g["past"],
            "ids": g["nodeIds"], "fb": pg.evaluate(P12.FEEDBACK)}


#: 入口普查：把**所有**可能触发这三个动作的钩子一次性记下来
ENTRY_ALL = """()=>{
  const q=(s)=>Array.from(document.querySelectorAll(s));
  const txt=(e)=>(e.textContent||'').trim().replace(/\\s+/g,' ').slice(0,30);
  const btns=q('button').filter(b=>(b.textContent||'').trim());
  const byText=(t)=>btns.filter(b=>(b.textContent||'').trim()===t)
                       .map(b=>({txt:t,disabled:b.disabled,
                                 pressed:b.getAttribute('aria-pressed')}));
  return {
    attemptChips:q('[data-video-attempt]').map(e=>({label:txt(e),
        pressed:e.getAttribute('aria-pressed')})),
    breakdown:byText('逐帧拉片'),
    continuation:byText('智能续写'),
    audioTriggers:q('[data-video-audio-menu-trigger]').map(txt),
    audioModes:q('[data-video-audio-mode]').map(txt),
    subtitleTriggers:q('[data-video-subtitle-menu-trigger]').map(txt),
    shotStart:q('[data-shot-breakdown-start]').map(e=>({
        disabled:e.disabled, text:txt(e)})),
    contextMenu:q('[data-canvas-context-item]').map(e=>({
        item:e.getAttribute('data-canvas-context-item'), text:txt(e)})),
    shotNodes:q('[data-shot-breakdown-node]').length,
    nodeCount:q('.react-flow__node').length,
  };}"""


def run_reselect(b, key, name, trig, need_ready, need_sb, drop_ref):
    pg = b.new_page()
    pg.set_default_timeout(25000)
    try:
        P811.boot(pg)
        if need_sb:
            pg.evaluate(P811.SELECT, [VID])
            pg.wait_for_timeout(700)
            P811.ensure_visible(pg, VID)
            pg.evaluate(P811.PREP_READY, VID)
            pg.wait_for_timeout(800)
            P811.t_breakdown(pg)
            nodes_now = pg.evaluate(
                "()=>{const S=window.__libtv_store.getState();"
                "const cv=S.canvases.find(c=>c.id===S.activeCanvasId);"
                "return cv.nodes.map(n=>({id:n.id,type:n.type}));}")
            sbn = [n for n in nodes_now if n["type"] == "shot-breakdown"]
            if not sbn:
                return {"key": key, "FAILED": "没造出 shot-breakdown 节点"}
            src_id = sbn[0]["id"]
        else:
            src_id = VID

        pg.evaluate(P811.SELECT, [src_id])
        pg.wait_for_timeout(700)
        P811.ensure_visible(pg, src_id)
        if need_ready:
            pg.evaluate(P811.PREP_READY, src_id)
            pg.wait_for_timeout(800)
        if drop_ref:
            pg.evaluate(P811.DROP_IMG_REF, src_id)
            pg.wait_for_timeout(600)

        s0 = snap(pg)
        e0 = pg.evaluate(ENTRY_ALL)
        trig(pg)
        s1 = snap(pg)

        # ★★ 重新选中**原来那个源节点**
        pg.evaluate(P811.SELECT, [src_id])
        pg.wait_for_timeout(900)
        v = P811.ensure_visible(pg, src_id)
        s_sel = snap(pg)
        e_sel = pg.evaluate(ENTRY_ALL)

        # ★ 第二下（此时入口应该回来了）
        ui2 = {"outcome": None, "error": None}
        try:
            trig(pg)
            ui2["outcome"] = "clicked"
        except Exception as e:  # noqa: BLE001
            ui2["outcome"] = "★ 点不动"
            ui2["error"] = ("%s: %s" % (type(e).__name__, e))[:200]
        s2 = snap(pg)
        e2 = pg.evaluate(ENTRY_ALL)

        return {"key": key, "name": name, "srcId": src_id,
                "第一次之前（节点/边/历史）": [s0["n"], s0["e"], s0["past"]],
                "第一次之后（节点/边/历史）": [s1["n"], s1["e"], s1["past"]],
                "重新选中之后（节点/边/历史）": [s_sel["n"], s_sel["e"],
                                              s_sel["past"]],
                "第二下之后（节点/边/历史）": [s2["n"], s2["e"], s2["past"]],
                "★ 第一下建了东西": (s1["n"] != s0["n"] or s1["e"] != s0["e"]),
                "★ 重新选中**没改**任何东西":
                    s_sel["ids"] == s1["ids"] and s_sel["e"] == s1["e"]
                    and s_sel["past"] == s1["past"],
                "入口（第一次之前）": e0,
                "入口（重新选中之后）": e_sel,
                "入口（第二下之后）": e2,
                "UI 第二下": ui2,
                "★ UI 第二下点不动": ui2["outcome"] == "★ 点不动",
                "★ 第二下建了东西": (s2["n"] != s1["n"] or s2["e"] != s1["e"]),
                "★ 第二下历史 +1": s2["past"] == s1["past"] + 1,
                "★ 第二下的可见反馈变化": P12.fb_diff(s1["fb"], s2["fb"])}
    except Exception as e:  # noqa: BLE001
        return {"key": key, "FAILED": "%s: %s" % (type(e).__name__, e)}
    finally:
        try:
            pg.close()
        except Exception:  # noqa: BLE001
            pass


ACTIONS = P12.ACTIONS


def main():
    out = {"base": A.BASE, "cells": [], "census": {}}
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True)
        for rd in range(2):
            for key, name, trig, nr, ns, dr in ACTIONS:
                t0 = time.time()
                c = run_reselect(b, key, name, trig, nr, ns, dr)
                c["round"] = rd
                c["secs"] = round(time.time() - t0, 1)
                out["cells"].append(c)
                # ★ **每条臂增量落盘** —— 第一版只在全部跑完后写一次，
                #   于是中途被终止时**整批读数全丢**（rd1 只跑了一半）。
                #   ★ 这条纪律值得推广：长跑探针的 raw 必须能增量重建。
                OUT.parent.mkdir(parents=True, exist_ok=True)
                OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                               encoding="utf-8")
                es = c.get("入口（重新选中之后）") or {}
                print("rd%d %-15s %s  节点 %s→%s→%s  UI2=%s 建=%s 史+1=%s | 逐帧拉片%s 智能续写%s 音视频%s" % (
                    rd, key, c.get("FAILED") or "ok",
                    (c.get("第一次之后（节点/边/历史）") or [None])[0],
                    (c.get("重新选中之后（节点/边/历史）") or [None])[0],
                    (c.get("第二下之后（节点/边/历史）") or [None])[0],
                    (c.get("UI 第二下") or {}).get("outcome"),
                    c.get("★ 第二下建了东西"), c.get("★ 第二下历史 +1"),
                    bool(es.get("breakdown")), bool(es.get("continuation")),
                    bool(es.get("audioTriggers"))), flush=True)
        b.close()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("written", OUT)


if __name__ == "__main__":
    main()

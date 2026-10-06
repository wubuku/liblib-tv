#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 812 探针 —— **重复触发**同一个已生效的操作，用户得到什么？

## 起点

811 在验撤销时顺带发现：7 个派生动作里**有两个带防重守卫**、**五个没有** ——
`createSubtitleErase` 有**指纹去重**（`canvasStore.ts:1970`，同一请求返回
`no-op` 与既有 targetId）、`completeShotBreakdown` 有「已有结果就 return」
（`:3188`）。809 / 811 都只把它们当作「为什么要设阳性对照」的引用，
**它们本身的用户可见行为从来没量过**。

★ 用户会真的连点两下。所以要回答三件事：

1. ★ **入口在第一次触发之后还在不在**？（条件渲染 —— 806 立过一条纪律：
   **普查必须记两个状态**，只在动作后普查会漏算/多算入口。）
2. 第二下**建不建东西**、历史**加不加 1**。
3. ★ 第二下用户得到什么**可见反馈**（芯片 `aria-pressed`／状态文本／DOM 变化）。
   —— 这是判「静默」的唯一依据，807 立过：**光看节点数不够**。

## ★ 阳性对照

第一下**必须**真的建了东西且历史 **+1**，否则「第二下什么都没发生」是废话。
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
#: 复用 811 的触发器与准备动作（811 的探针目录在**隔壁批次目录**）
sys.path.insert(0, str(HERE.parent.parent /
                       "liblib-canvas-batch811-2026-10-01" / "probes"))
import dbg811a as P811  # noqa: E402

OUT = pathlib.Path(os.environ.get("VB812_OUT") or
                   (HERE.parent / "raw" / "vb812a.json"))
VID = P811.VID

#: 「用户看得见的反馈」普查：条件渲染的入口 + 状态文本 + 结果卡
FEEDBACK = """()=>{
  const txt=(e)=>(e.textContent||'').trim().replace(/\\s+/g,' ').slice(0,40);
  const q=(s)=>Array.from(document.querySelectorAll(s));
  return {
    attemptChips:q('[data-video-attempt]').map(e=>({label:txt(e),
        pressed:e.getAttribute('aria-pressed')})),
    audioTriggers:q('[data-video-audio-menu-trigger]').length,
    subtitleTriggers:q('[data-video-subtitle-menu-trigger]').length,
    subtitleTarget:q('[data-subtitle-erase-target]').map(e=>({
        mode:e.getAttribute('data-subtitle-erase-target-mode')})),
    subtitlePending:q('[data-subtitle-erase-pending-copy]').map(txt),
    audioOutputs:q('[data-audio-split-output]').map(e=>({
        mode:e.getAttribute('data-audio-split-mode'),
        kind:e.getAttribute('data-audio-split-output-kind')})),
    shotNodes:q('[data-shot-breakdown-node]').length,
    shotStart:q('[data-shot-breakdown-start]').length,
    shotMedia:q('[data-shot-breakdown-media]').map(txt),
    nodeCount:document.querySelectorAll('.react-flow__node').length,
    edgeCount:document.querySelectorAll('.react-flow__edge').length,
  };}"""


#: ★ store 层的第二下：直接调动作，绕开 UI。
#:   ⟹ 809/811 问的是「用户点第二下会怎样」；
#:      本条问的是「**即使直接调动作**会怎样」——
#:      UI 层可能已经把入口禁掉了（`data-shot-breakdown-start` 变 `disabled`
#:      且文案变成「拉片完成」），那样 store 层的守卫**永远观察不到**。
STORE_SECOND = """(cfg)=>{const S=window.__libtv_store.getState();
  const before=S.canvases.find(c=>c.id===S.activeCanvasId);
  const b={n:before.nodes.length,e:before.edges.length,
           past:(S.historyByCanvas[before.id]||{past:[]}).past.length};
  try{
    switch(cfg.action){
      case 'createFirstFrameReference':
        S.createFirstFrameReference(cfg.vid); break;
      case 'createFirstLastFrameReference':
        S.createFirstLastFrameReference(cfg.vid); break;
      case 'addDerivedNode':
        S.addDerivedNode(cfg.vid,'shot-breakdown',{}); break;
      case 'createVideoContinuation':
        S.createVideoContinuation(cfg.vid,0,6); break;
      case 'createSubtitleErase':
        S.createSubtitleErase(cfg.vid,'smart',[]); break;
      case 'createAudioSplit':
        S.createAudioSplit(cfg.vid,'av'); break;
      case 'completeShotBreakdown':
        S.completeShotBreakdown(cfg.vid,['storyboard','motion','music']); break;
      default: return {FAILED:'未知动作 %r'.replace('%r','')+cfg.action};
    }
  }catch(err){ return {FAILED:'抛异常: '+String(err)}; }
  const A2=window.__libtv_store.getState();
  const after=A2.canvases.find(c=>c.id===A2.activeCanvasId);
  const a={n:after.nodes.length,e:after.edges.length,
           past:(A2.historyByCanvas[after.id]||{past:[]}).past.length};
  return {before:b, after:a, 建了东西:(a.n!==b.n||a.e!==b.e),
          历史加1:(a.past===b.past+1)};}"""

#: 键 → store 动作名（只有那些「第一下确实建了东西」的动作才有意义）
STORE_ACT = {"u_firstFrame": "createFirstFrameReference",
             "u_firstLast": "createFirstLastFrameReference",
             "u_breakdown": "addDerivedNode",
             "u_continuation": "createVideoContinuation",
             "u_subtitle": "createSubtitleErase",
             "u_audio": "createAudioSplit",
             "u_shotComplete": "completeShotBreakdown"}


def snap(pg):
    g = P811.active(pg)
    return {"n": len(g["nodeIds"]), "e": g["edges"], "past": g["past"],
            "ids": g["nodeIds"], "fb": pg.evaluate(FEEDBACK)}


def fb_diff(a, b):
    """★ 只列**变了**的字段 —— 反馈普查的读数必须能一眼看出「变没变」"""
    out = {}
    for k in set(a) | set(b):
        if a.get(k) != b.get(k):
            out[k] = {"之前": a.get(k), "之后": b.get(k)}
    return out


#: (键, 动作名, 触发器, 要 ready, 要先造 shot-breakdown, 要删 image 入边)
ACTIONS = P811.UNDO_ACTIONS


def run_twice(b, key, name, trig, need_ready, need_sb, drop_ref):
    pg = b.new_page()
    pg.set_default_timeout(30000)
    try:
        P811.boot(pg)
        if need_sb:
            pg.evaluate(P811.SELECT, [VID])
            pg.wait_for_timeout(700)
            v = P811.ensure_visible(pg, VID)
            if not v.get("★ 在视口内"):
                return {"key": key, "FAILED": "视频节点不在视口"}
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
        v = P811.ensure_visible(pg, src_id)
        if not v.get("★ 在视口内"):
            return {"key": key, "FAILED": "源节点不在视口"}
        if need_ready:
            pg.evaluate(P811.PREP_READY, src_id)
            pg.wait_for_timeout(800)
        if drop_ref:
            pg.evaluate(P811.DROP_IMG_REF, src_id)
            pg.wait_for_timeout(600)

        s0 = snap(pg)                     # ★ 第一次触发**前**
        trig(pg)
        s1 = snap(pg)                     # ★ 第一次触发**后**（入口还在不在）
        entry_after_first = {
            "entryStillThere": bool(s1["fb"]["attemptChips"]
                                    or s1["fb"]["audioTriggers"] > 0
                                    or s1["fb"]["subtitleTriggers"] > 0
                                    or s1["fb"]["shotNodes"] > 0),
            "★ attempt 芯片还在": bool(s1["fb"]["attemptChips"]),
            "★ 工具栏触发器还在": (s1["fb"]["audioTriggers"] > 0
                                 or s1["fb"]["subtitleTriggers"] > 0),
            "★ 拉片节点还在": s1["fb"]["shotNodes"] > 0,
            "★ 拉片按钮还在": s1["fb"]["shotStart"] > 0,
            "★ 拉片按钮的文案": [b for b in
                               ["拉片完成"] if True] and
                              s1["fb"].get("shotMedia"),
        }
        # ★★ 第二下的 UI 触发：**点不动不是失败，是读数**
        ui2 = {"outcome": None, "error": None}
        try:
            trig(pg)
            ui2["outcome"] = "clicked"
        except Exception as e:  # noqa: BLE001
            ui2["outcome"] = "★ 点不动"
            ui2["error"] = ("%s: %s" % (type(e).__name__, e))[:220]
        s2 = snap(pg)
        # ★ store 层的第二下（绕开 UI）
        st2 = pg.evaluate(STORE_SECOND, {"action": STORE_ACT[key],
                                         "vid": src_id})
        return {"key": key, "name": name, "srcId": src_id,
                "s0": s0, "s1": s1, "s2": s2,
                "入口还在吗（第一次之后）": entry_after_first,
                "★ 第一下真的建了东西": (s1["n"] != s0["n"] or s1["e"] != s0["e"]),
                "★ 第一下历史 +1": s1["past"] == s0["past"] + 1,
                "第一下之后（节点/边/历史）": [s0["n"], s1["n"], s0["e"], s1["e"],
                                              s0["past"], s1["past"]],
                "第二下之后（节点/边/历史）": [s1["n"], s2["n"], s1["e"], s2["e"],
                                              s1["past"], s2["past"]],
                "★ 第二下建了东西": (s2["n"] != s1["n"] or s2["e"] != s1["e"]),
                "★ 第二下历史 +1": s2["past"] == s1["past"] + 1,
                "★ 第二下的可见反馈变化": fb_diff(s1["fb"], s2["fb"]),
                "★ 第二下**零**可见反馈": fb_diff(s1["fb"], s2["fb"]) == {},
                "UI 第二下": ui2,
                "★ UI 第二下点不动": ui2["outcome"] == "★ 点不动",
                "store 第二下": st2}
    except Exception as e:  # noqa: BLE001
        return {"key": key, "FAILED": "%s: %s" % (type(e).__name__, e)}
    finally:
        try:
            pg.close()
        except Exception:  # noqa: BLE001
            pass


def main():
    out = {"base": A.BASE, "cells": []}
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True)
        for rd in range(2):
            for key, name, trig, nr, ns, dr in ACTIONS:
                t0 = time.time()
                c = run_twice(b, key, name, trig, nr, ns, dr)
                c["round"] = rd
                c["secs"] = round(time.time() - t0, 1)
                out["cells"].append(c)
                st = c.get("store 第二下") or {}
                print("rd%d %-15s %s  UI下2=%s | store下2 建=%s 史+1=%s" % (
                    rd, key, c.get("FAILED") or "ok",
                    (c.get("UI 第二下") or {}).get("outcome"),
                    st.get("建了东西"), st.get("历史加1")), flush=True)
        b.close()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("written", OUT)


if __name__ == "__main__":
    main()

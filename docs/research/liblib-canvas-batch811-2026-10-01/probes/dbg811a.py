#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 811 探针 —— 两件事：7 个派生动作的**撤销**，与 `createAudioSplit` 的**跳画布语义**

## 甲：撤销（809 留下的最大一条）

809 验了 7 个动作的**几何**，但**没有验撤销**。它们全都走 `pushHistory`，
所以「一次 `Cmd+Z` 能不能完全还原」是一条**独立**的问题。

★ 809 撞出的一条相关事实：`createSubtitleErase` 有**指纹去重**（`:1970`）、
`completeShotBreakdown` 有「已有结果就 return」（`:3188`）⟹ 这两条**再点一次
不会产生第二次历史** ⟹ 如果只按一次 `Cmd+Z` 就回到「动作之前」，那是巧合；
如果需要按两次，说明第一次按掉的是**上一次别的操作**。所以本批**记「按了几次
才回到动作前」**（上限 3 次），而不是只记「一次之后对不对」。

## 乙：`createAudioSplit` 的跳画布语义

`canvasStore.ts:2062`（batch 437）明确写：它提交到**拥有源节点的那张画布**，
而不是**当前画布** —— 因为它是个**有 600ms 延迟的定时器**
（`VideoNode.tsx:248`）。而 `undo()`（`:3923`）作用在 **`activeCanvasId`** 上。

⟹ 用户在 600ms 内切走画布，会同时踩到三件事：
结果落在哪张画布、切过去之后**选区**是什么、那边按 `Cmd+Z` 会不会**误伤**。

★ 这三条都是**用户看得见**的，判据优先用 DOM 读数。

## ★ 判据

- **甲**：按 `Cmd+Z` 之后的**节点 id 集合**与**边数**必须与动作前**完全相同**。
  ★ 判「id 集合」而不是「节点数」—— 数量相同但换了内容是另一种坏。
- **乙**：新节点必须落在**拥有源节点的那张画布**（不是当前画布），
  且当前画布的节点数**不受影响**。
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

OUT = pathlib.Path(os.environ.get("VB811_OUT") or
                   (HERE.parent / "raw" / "vb811a.json"))
VID = "v-UGQZzZOpbv"
GRP = "g-EFbbHpwq5w"

GRAPH = """()=>{const S=window.__libtv_store.getState();
  return S.canvases.map(c=>({id:c.id, active:c.id===S.activeCanvasId,
    nodeIds:c.nodes.map(n=>n.id).sort(),
    edges:c.edges.length,
    types:c.nodes.map(n=>n.type).sort(),
    sel:S.activeCanvasId===c.id?S.selectedNodeIds:null,
    past:(S.historyByCanvas[c.id]||{past:[]}).past.length,
  }));}"""

#: ★ 探针返工：`GRAPH` 返回的是**画布列表**，而我到处写
#:   `pg.evaluate(GRAPH)[0]` —— 那是**第一张**画布（`canvas-1`，0 个节点），
#:   不是当前画布 ⟹ before/after 永远是同一张空画布，
#:   「动作真的建了东西」14 条臂**全部**读成 False。
#:   ★ 这正是 807／808／809／810 反复出现的那一类：**读数恒定无信息**，
#:     而恒定无信息看起来像「功能没生效」。
def active(pg):
    """★ 取**当前**画布的读数（不是列表第 0 项）"""
    return next(c for c in pg.evaluate(GRAPH) if c["active"])


PREP_READY = """(vid)=>{const S=window.__libtv_store.getState();
  window.__libtv_store.setState({canvases:S.canvases.map(c=>({...c,
    nodes:c.nodes.map(m=>m.id===vid?{...m,data:{...m.data,status:'ready'}}:m)}))});
  return {ok:true};}"""

DROP_IMG_REF = """(vid)=>{const S=window.__libtv_store.getState();
  const cv=S.canvases.find(c=>c.id===S.activeCanvasId); if(!cv) return {FAILED:'no canvas'};
  const imgIds=new Set(cv.nodes.filter(n=>n.type==='image').map(n=>n.id));
  const dropped=cv.edges.filter(e=>e.target===vid&&imgIds.has(e.source));
  S.setEdges(cv.edges.filter(e=>!dropped.includes(e)));
  return {ok:true,dropped:dropped.map(e=>e.id)};}"""

SELECT = """(ids)=>{window.__libtv_store.getState()
  .selectElements({nodeIds:ids,edgeIds:[]}); return {ok:true};}"""

IN_VIEW = """(id)=>{const e=document.querySelector('.react-flow__node[data-id="'+id+'"]');
  if(!e) return {present:false}; const r=e.getBoundingClientRect();
  return {present:true,x:r.left,y:r.top,w:r.width,h:r.height};}"""
VIEWPORT = """()=>({w:window.innerWidth,h:window.innerHeight})"""


def boot(pg):
    pg.goto(A.BASE, wait_until="domcontentloaded", timeout=90000)
    pg.evaluate(A.CLEAR_LS, A.LS_KEY)
    pg.set_viewport_size({"width": 1440, "height": 1000})
    pg.goto(A.BASE, wait_until="networkidle", timeout=90000)
    pg.wait_for_selector(".react-flow__node", timeout=60000)
    pg.wait_for_timeout(1500)


def ensure_visible(pg, node_id, tries=4):
    last = {}
    for _ in range(tries):
        last = pg.evaluate(IN_VIEW, node_id)
        if not last.get("present"):
            pg.wait_for_timeout(400)
            continue
        vp = pg.evaluate(VIEWPORT)
        if (last["x"] >= -2 and last["y"] >= -2
                and last["x"] + last["w"] <= vp["w"] + 2
                and last["y"] + last["h"] <= vp["h"] + 2):
            return {**last, "★ 在视口内": True}
        pg.keyboard.press("Meta+0")
        pg.wait_for_timeout(900)
    return {**last, "★ 在视口内": False}


def click_text(pg, text):
    for t in pg.query_selector_all("button"):
        if (t.text_content() or "").strip() == text:
            t.click()
            return True
    return False


# ---------------------------------------------------------------- 触发器
def t_first_frame(pg):
    pg.click('[data-video-attempt="首帧生成视频"]')
    pg.wait_for_timeout(900)


def t_first_last(pg):
    pg.click('[data-video-attempt="首尾帧生成视频"]')
    pg.wait_for_timeout(900)


def t_breakdown(pg):
    if not click_text(pg, "逐帧拉片"):
        raise RuntimeError("找不到「逐帧拉片」")
    pg.wait_for_timeout(1100)


def t_continuation(pg):
    if not click_text(pg, "智能续写"):
        raise RuntimeError("找不到「智能续写」")
    pg.wait_for_selector("[data-video-continuation-confirm]", timeout=20000)
    pg.click("[data-video-continuation-confirm]")
    pg.wait_for_timeout(900)


def t_subtitle(pg):
    pg.click("[data-video-subtitle-menu-trigger]")
    pg.wait_for_selector("[data-video-subtitle-mode]", timeout=20000)
    pg.click('[data-video-subtitle-mode="smart"]')
    pg.wait_for_selector("[data-subtitle-erase-submit]", timeout=20000)
    pg.click("[data-subtitle-erase-submit]")
    pg.wait_for_timeout(900)


def t_audio(pg):
    pg.click("[data-video-audio-menu-trigger]")
    pg.wait_for_selector("[data-video-audio-mode]", timeout=20000)
    pg.click('[data-video-audio-mode="av"]')
    # ★ createAudioSplit 走 acceptLibTVOperation，**有 600ms 延迟**
    pg.wait_for_timeout(2600)


def t_shot_complete(pg):
    pg.click("[data-shot-breakdown-start]")
    pg.wait_for_timeout(1200)


#: (键, 动作名, 触发器, 要 ready, 要先造 shot-breakdown, 要删 image 入边)
UNDO_ACTIONS = [
    ("u_firstFrame", "createFirstFrameReference", t_first_frame, False, False, True),
    ("u_firstLast", "createFirstLastFrameReference", t_first_last, False, False, True),
    ("u_breakdown", "addDerivedNode(shot-breakdown)", t_breakdown, True, False, False),
    ("u_continuation", "createVideoContinuation", t_continuation, True, False, False),
    ("u_subtitle", "createSubtitleErase", t_subtitle, True, False, False),
    ("u_audio", "createAudioSplit", t_audio, True, False, False),
    ("u_shotComplete", "completeShotBreakdown", t_shot_complete, False, True, False),
]


def run_undo(b, key, name, trig, need_ready, need_sb, drop_ref):
    pg = b.new_page()
    pg.set_default_timeout(30000)
    try:
        boot(pg)
        if need_sb:
            pg.evaluate(SELECT, [VID])
            pg.wait_for_timeout(700)
            v = ensure_visible(pg, VID)
            if not v.get("★ 在视口内"):
                return {"key": key, "FAILED": "视频节点不在视口"}
            pg.evaluate(PREP_READY, VID)
            pg.wait_for_timeout(800)
            t_breakdown(pg)
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

        pg.evaluate(SELECT, [src_id])
        pg.wait_for_timeout(700)
        v = ensure_visible(pg, src_id)
        if not v.get("★ 在视口内"):
            return {"key": key, "FAILED": "源节点不在视口"}
        if need_ready:
            pg.evaluate(PREP_READY, src_id)
            pg.wait_for_timeout(800)
        if drop_ref:
            pg.evaluate(DROP_IMG_REF, src_id)
            pg.wait_for_timeout(600)

        before = active(pg)
        trig(pg)
        after = active(pg)

        # ★ 记「按了几次 Cmd+Z 才回到动作前」——上限 3 次
        presses, undone = [], None
        for i in range(3):
            pg.keyboard.press("Meta+z")
            pg.wait_for_timeout(800)
            g = active(pg)
            presses.append({"第几次": i + 1, "节点 id 集合": g["nodeIds"],
                            "边数": g["edges"]})
            if g["nodeIds"] == before["nodeIds"] and g["edges"] == before["edges"]:
                undone = i + 1
                break
        final = active(pg)
        return {"key": key, "name": name, "srcId": src_id,
                "before": {"nodeIds": before["nodeIds"], "edges": before["edges"],
                           "types": before["types"], "past": before["past"]},
                "after": {"nodeIds": after["nodeIds"], "edges": after["edges"],
                          "types": after["types"], "past": after["past"]},
                "★ 动作真的建了东西":
                    after["nodeIds"] != before["nodeIds"]
                    or after["edges"] != before["edges"],
                "★ 历史真的多了一条": after["past"] == before["past"] + 1,
                "undoPresses": presses,
                "★ 按了几次才回到动作前": undone,
                "final": {"nodeIds": final["nodeIds"], "edges": final["edges"],
                          "types": final["types"], "past": final["past"]}}
    except Exception as e:  # noqa: BLE001
        return {"key": key, "FAILED": "%s: %s" % (type(e).__name__, e)}
    finally:
        try:
            pg.close()
        except Exception:  # noqa: BLE001
            pass


# ---------------------------------------------------------------- 乙：跳画布
def t_audio_then_switch(pg, other_canvas):
    """点「音视频分离」之后**立刻**切到另一张画布（600ms 延迟之内）。"""
    pg.click("[data-video-audio-menu-trigger]")
    pg.wait_for_selector("[data-video-audio-mode]", timeout=20000)
    pg.click('[data-video-audio-mode="av"]')
    pg.wait_for_timeout(120)          # ★ 120ms：远小于 600ms 的延迟
    pg.click("[data-canvas-trigger]")
    pg.wait_for_selector('[data-canvas-row="%s"]' % other_canvas, timeout=20000)
    pg.click('[data-canvas-row="%s"]' % other_canvas)
    pg.wait_for_timeout(3200)         # ★ 等延迟到期 + 提交
    return True


DOMCANVAS = """()=>{const sel=document.querySelectorAll('[data-canvas-row]');
  return Array.from(sel).map(e=>({id:e.getAttribute('data-canvas-row'),
    active:e.getAttribute('data-canvas-active')}));}"""
DOMNODES = """()=>Array.from(document.querySelectorAll('.react-flow__node'))
  .map(e=>e.getAttribute('data-id')).filter(Boolean).sort()"""


def run_cross(b, key, do_switch):
    pg = b.new_page()
    pg.set_default_timeout(30000)
    try:
        boot(pg)
        g0 = pg.evaluate(GRAPH)
        owner = next(c for c in g0 if c["active"])
        other = next(c for c in g0 if not c["active"])
        pg.evaluate(SELECT, [VID])
        pg.wait_for_timeout(700)
        v = ensure_visible(pg, VID)
        if not v.get("★ 在视口内"):
            return {"key": key, "FAILED": "视频节点不在视口"}
        pg.evaluate(PREP_READY, VID)
        pg.wait_for_timeout(800)
        before = pg.evaluate(GRAPH)
        t_audio_then_switch(pg, other["id"] if do_switch else owner["id"])
        after = pg.evaluate(GRAPH)
        dom = {"画布下拉": pg.evaluate(DOMCANVAS), "DOM 节点": pg.evaluate(DOMNODES)}
        # 在**当前画布**上按一次 Cmd+Z，看有没有误伤
        pg.keyboard.press("Meta+z")
        pg.wait_for_timeout(900)
        undone = pg.evaluate(GRAPH)
        return {"key": key, "源画布": owner["id"], "切过去的画布":
                other["id"] if do_switch else owner["id"],
                "before": {c["id"]: {"n": len(c["nodeIds"]), "e": c["edges"],
                                     "past": c["past"]} for c in before},
                "after": {c["id"]: {"n": len(c["nodeIds"]), "e": c["edges"],
                                    "past": c["past"]} for c in after},
                "activeAfter": next((c["id"] for c in after if c["active"]), None),
                "selAfter": next((c["sel"] for c in after if c["active"]), None),
                "dom": dom,
                "在当前画布按 Cmd+Z 之后":
                    {c["id"]: {"n": len(c["nodeIds"]), "e": c["edges"],
                               "past": c["past"]} for c in undone}}
    except Exception as e:  # noqa: BLE001
        return {"key": key, "FAILED": "%s: %s" % (type(e).__name__, e)}
    finally:
        try:
            pg.close()
        except Exception:  # noqa: BLE001
            pass


CROSS = [("crossSwitch", "延迟内切到另一张画布", True),
         ("crossStay", "对照组：不切画布", False)]


def main():
    out = {"base": A.BASE, "undo": [], "cross": []}
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True)
        for rd in range(2):
            for key, name, trig, nr, ns, dr in UNDO_ACTIONS:
                t0 = time.time()
                c = run_undo(b, key, name, trig, nr, ns, dr)
                c["round"] = rd
                c["secs"] = round(time.time() - t0, 1)
                out["undo"].append(c)
                print("rd%d %-15s %s  建了东西=%s  按了%s次" % (
                    rd, key, c.get("FAILED") or "ok",
                    c.get("★ 动作真的建了东西"),
                    c.get("★ 按了几次才回到动作前")), flush=True)
            for key, name, sw in CROSS:
                t0 = time.time()
                c = run_cross(b, key, sw)
                c["round"] = rd
                c["secs"] = round(time.time() - t0, 1)
                out["cross"].append(c)
                print("rd%d %-15s %s  active=%s" % (
                    rd, key, c.get("FAILED") or "ok", c.get("activeAfter")),
                    flush=True)
        b.close()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("written", OUT)


if __name__ == "__main__":
    main()

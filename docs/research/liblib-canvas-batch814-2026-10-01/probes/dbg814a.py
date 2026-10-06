#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 814 探针 —— 重复产物的三个问题

813 量到：**逐帧拉片／智能续写／音视频分离**在「重新选中源节点再点一次」这条
**完全可达**的路径上会**再建出一份**。813 留了三条没测，本批测前两条 + 累积量：

1. ★ **能不能被干净撤销** —— 连建两份之后按一次 `Cmd+Z`，
   是不是回到「只有一份」的精确状态（节点 id 集合 + 边数逐位）？
   ★ 811 量的是**单次**触发后的撤销；重复场景**没量过**。
2. ★ **能不能被看出来** —— 两份产物在 DOM 上**长得一样吗**？
   ⟹ 用户能不能分辨自己点了几次？（判据用 **DOM 可见读数**：标题／文件名）
3. ★ **能累积几份** —— 重新选中再点，第三次、第四次会怎样？
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

OUT = pathlib.Path(os.environ.get("VB814_OUT") or
                   (HERE.parent / "raw" / "vb814a.json"))
VID = P811.VID

#: ★ 「能不能被看出来」：取**所有**新建节点的**可见文本**（DOM）
#:   ⟹ 能读 DOM 就不只读 store（808 的 S4 同款纪律）
#: ★★ 探针返工：第一版只记 `textContent`，于是判据给出一个**假红** ⟹
#:   ① `audio` 一次建**两个 kind**（音轨 + 无声），它们文本**本来就该不同** ⟹
#:      「整条臂只应有一种文本」这个判据把**不同 kind** 当成了重复；
#:   ② `continuation` 的**第 3 份**文本多出一大截 —— 真因是**它正被选中**、
#:      编辑器面板展开、`textContent` 把面板文字也吃进去了 ⟹
#:      **那不是节点身份的差异**。
#:   ⟹ 修法：同一次读数里**同时**记下每个节点的 `type` 与 `selected`，
#:      让判据能「按 kind 分组 + 排除选中态」地比较。
VISIBLE = """(ids)=>{const o={};
  const S=window.__libtv_store.getState();
  const cv=S.canvases.find(c=>c.id===S.activeCanvasId);
  const byId=new Map(cv.nodes.map(n=>[n.id,n]));
  for(const id of ids){
    const e=document.querySelector('.react-flow__node[data-id="'+id+'"]');
    const st=byId.get(id)||{};
    if(!e){o[id]={text:null,type:st.type||null,
                 selected:(S.selectedNodeIds||[]).indexOf(id)>=0};continue;}
    o[id]={text:(e.textContent||'').trim().replace(/\\s+/g,' ').slice(0,80),
           type:st.type||null,
           selected:(S.selectedNodeIds||[]).indexOf(id)>=0};}
  return o;}"""


def graph(pg):
    return P811.active(pg)


def snap(pg):
    g = graph(pg)
    return {"n": len(g["nodeIds"]), "e": g["edges"], "past": g["past"],
            "ids": g["nodeIds"]}


def new_ids(before, after):
    return sorted(set(after["ids"]) - set(before["ids"]))


def run(b, key, trig, need_ready, how_many, do_undo):
    pg = b.new_page()
    pg.set_default_timeout(25000)
    try:
        P811.boot(pg)
        pg.evaluate(P811.SELECT, [VID])
        pg.wait_for_timeout(700)
        P811.ensure_visible(pg, VID)
        if need_ready:
            pg.evaluate(P811.PREP_READY, VID)
            pg.wait_for_timeout(800)

        marks = []
        prev = snap(pg)
        made = []
        for k in range(1, how_many + 1):
            if k > 1:
                # ★ 重新选回源节点（813 证明这是让入口回来的那条路）
                pg.evaluate(P811.SELECT, [VID])
                pg.wait_for_timeout(800)
                P811.ensure_visible(pg, VID)
            trig(pg)
            cur = snap(pg)
            made.extend(new_ids(prev, cur))
            marks.append({"第几次": k, "节点": [prev["n"], cur["n"]],
                          "边": [prev["e"], cur["e"]],
                          "历史": [prev["past"], cur["past"]],
                          "这次新建了": new_ids(prev, cur)})
            prev = cur

        # ★ 用户能不能分辨？取每一份的可见文本
        vis = pg.evaluate(VISIBLE, made) if made else {}

        # ★ 按 **kind** 分组、且**排除选中态**后再比 —— 见 VISIBLE 的注释
        groups = {}
        for i in made:
            g = (vis.get(i) or {})
            if not g.get("text"):
                continue
            if g.get("selected"):
                continue
            groups.setdefault(g.get("type"), []).append(g["text"])
        out = {"key": key, "marks": marks, "一共建了几份": len(made),
               "建出来的 id": made, "可见文本": vis,
               "按 kind 分组（已排除选中）": {k: len(set(v)) for k, v in groups.items()},
               "★ 每个 kind 只有一种文本":
                   bool(groups) and all(len(set(v)) == 1 for v in groups.values()),
               "★ 至少有一个 kind 出现过**两次以上**":
                   any(len(v) >= 2 for v in groups.values()),
               "★ 样本": {k: v[0] for k, v in groups.items()}}

        if do_undo:
            # ★ 撤销：一次 Cmd+Z 是不是回到「少一份」的精确状态
            target = marks[-2] if len(marks) >= 2 else None
            after_all = snap(pg)
            pg.keyboard.press("Meta+z")
            pg.wait_for_timeout(1000)
            undone = snap(pg)
            expect_n = marks[-2]["节点"][1] if target else None
            expect_e = marks[-2]["边"][1] if target else None
            out["撤销"] = {
                "全部建完（节点/边/历史）": [after_all["n"], after_all["e"],
                                           after_all["past"]],
                "★ 期望回到（少一份）": [expect_n, expect_e],
                "按一次 Cmd+Z 之后（节点/边/历史）": [undone["n"], undone["e"],
                                                    undone["past"]],
                "★ 节点数回到少一份": undone["n"] == expect_n,
                "★ 边数回到少一份": undone["e"] == expect_e,
                "★ 历史少一条": undone["past"] == after_all["past"] - 1,
                "★ 三件同时": undone["n"] == expect_n
                               and undone["e"] == expect_e
                               and undone["past"] == after_all["past"] - 1}
        return out
    except Exception as e:  # noqa: BLE001
        return {"key": key, "FAILED": "%s: %s" % (type(e).__name__, e)}
    finally:
        try:
            pg.close()
        except Exception:  # noqa: BLE001
            pass


#: (键, 动作, 触发器, 要 ready, 连点几次, 要测撤销)
CASES = [
    ("breakdown_x4", "addDerivedNode(shot-breakdown)", P811.t_breakdown, True, 4, True),
    ("continuation_x3", "createVideoContinuation", P811.t_continuation, True, 3, True),
    ("audio_x3", "createAudioSplit", P811.t_audio, True, 3, True),
    # 对照组：813 证明这两个会被守卫拦住 ⟹ 累积量应当**停在 1**
    ("subtitle_x3", "createSubtitleErase", P811.t_subtitle, True, 3, False),
]


def main():
    out = {"base": A.BASE, "cells": []}
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True)
        for rd in range(2):
            for key, name, trig, nr, how, du in CASES:
                t0 = time.time()
                c = run(b, key, trig, nr, how, du)
                c["name"] = name
                c["round"] = rd
                c["secs"] = round(time.time() - t0, 1)
                out["cells"].append(c)
                OUT.parent.mkdir(parents=True, exist_ok=True)
                OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                               encoding="utf-8")
                u = c.get("撤销") or {}
                print("rd%d %-15s %s  建了%s份 %s | 每kind一种文本=%s | 撤一次回到少一份=%s" % (
                    rd, key, c.get("FAILED") or "ok", c.get("一共建了几份"),
                    json.dumps(c.get("按 kind 分组（已排除选中）"), ensure_ascii=False),
                    c.get("★ 每个 kind 只有一种文本"),
                    u.get("★ 三件同时")), flush=True)
        b.close()
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("written", OUT)


if __name__ == "__main__":
    main()

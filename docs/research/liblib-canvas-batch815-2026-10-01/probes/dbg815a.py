#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 815 探针 —— ImageNode 那七个动作的**累积行为**（防不防重完全未知）

## 起点

813 的静态普查发现：`addDerivedNode` 有 **4 个**调用点 ——
`VideoNode.tsx:201`（逐帧拉片，813/814 已量）+ **`ImageNode.tsx:142/162/187`
三个**。814 明写「**ImageNode 那三个共用 `addDerivedNode` 的动作，本批完全没测**、
防不防重**未知**」。

★ 813/814 建立的方法论直接搬过来：
**第一次触发 → 重新选中源节点 → 第二次触发** ⟹ 这才是完全可达的第二条路径。

## ★ 三个动作其实不止三个

`ImageNode.tsx:185` 还有一条 `derivedImageActions[action]` 分支，
覆盖 **5 个**标签（多角度／打光／九宫格／高清／宫格切分）⟹ 合计 **7 个** UI 动作
共用同一个 store 动作 `addDerivedNode`。

★ 每个动作**独立测**（各自的 `offset`／`dimensions` 不同），
不能抽样代替 —— 抽样会让「某个动作有守卫」被平均掉。
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
                       "liblib-canvas-batch814-2026-10-01" / "probes"))
import dbg814a as P14  # noqa: E402

OUT = pathlib.Path(os.environ.get("VB815_OUT") or
                   (HERE.parent / "raw" / "vb815a.json"))
#: 种子图片节点（本来就在画布上、不是注入的）
IMG = "i-1FQ9tErTcC"

#: 工具栏普查 + 可见文本（判据优先读 DOM）
#:
#: ★★ 探针返工（第二版）：第一版只记 `label`（= `textContent`），
#:   而「旋转」是 **iconOnly** 动作（`ImageToolbar.tsx:91/100/108/116` 共 4 个），
#:   `:171` 的 `!iconOnly && <span>` 让它**没有可见文字** ⟹ `label` 是空串。
#:   判据（815 的 S1）要判「按钮存在」，却只能匹配到空串 ⟹ **假红**。
#:   ⟹ 修法在**探针侧**补 `aria-label` / `title`（`ImageToolbar.tsx:164-165`），
#:     **不放宽判据** —— 缺字段的是 raw，不是判据。
TOOLBAR = """()=>{const q=(s)=>Array.from(document.querySelectorAll(s));
  const txt=(e)=>(e.textContent||'').trim().replace(/\\s+/g,' ');
  const btns=q('[data-image-toolbar] button');
  return {
    toolbarPresent:q('[data-image-toolbar]').length,
    buttons:btns.map(b=>({label:txt(b),aria:b.getAttribute('aria-label')||'',
                          title:b.getAttribute('title')||'',
                          disabled:b.disabled,
                          pressed:b.getAttribute('aria-pressed'),
                          testid:b.getAttribute('data-testid')})),
  };}"""

#: ★ 新增读数：每一份产物的**可见文本 + 绝对几何**
#:   —— 814 在 VideoNode 那边量到「重复产物**长得一模一样**」；
#:   本批把它搬到 ImageNode 七个动作上，并**再加一条几何读数**：
#:   连点三次建出来的三份，是**叠在一起**（同一个 x）还是**扇形排开**？
#:   （`canvasStore.ts:1767` 的 `offset ?? {x:120,y:0}` 是相对**源节点**还是
#:   相对**上一份产物**，只有几何读数能分辨，而这是**用户看得见**的。）
GEOM = """(ids)=>{const o={};
  for(const id of ids){
    const e=document.querySelector('.react-flow__node[data-id="'+id+'"]');
    if(!e){o[id]=null;continue;}
    const r=e.getBoundingClientRect();
    o[id]={x:Math.round(r.left),y:Math.round(r.top),
           w:Math.round(r.width),h:Math.round(r.height)};
  } return o;}"""


def snap(pg):
    g = P811.active(pg)
    return {"n": len(g["nodeIds"]), "e": g["edges"], "past": g["past"],
            "ids": g["nodeIds"]}


def click_label(pg, label):
    """★ 三条匹配路径：可见文字 / `aria-label` / `title`
    —— icon-only 的动作只有后两者（`ImageToolbar.tsx:164-165`）
    ★ 返回**命中路径**，让 raw 能回答「它到底是被哪条路径点到的」
      （「旋转」必须走 `aria`/`title`，走 `label` 只会拿到空串）"""
    for b in pg.query_selector_all("[data-image-toolbar] button"):
        names = [("文字", (b.text_content() or "").strip().replace("\n", "")),
                 ("aria", b.get_attribute("aria-label") or ""),
                 ("title", b.get_attribute("title") or "")]
        for via, v in names:
            if v == label:
                if b.is_disabled():
                    return "disabled", via
                b.click()
                return "clicked", via
    return "not-found", None


def run(b, label, how_many):
    pg = b.new_page()
    pg.set_default_timeout(20000)
    try:
        P811.boot(pg)
        pg.evaluate(P811.SELECT, [IMG])
        pg.wait_for_timeout(800)
        v = P811.ensure_visible(pg, IMG)
        if not v.get("★ 在视口内"):
            return {"label": label, "FAILED": "图片节点不在视口"}
        tb0 = pg.evaluate(TOOLBAR)
        if not tb0["toolbarPresent"]:
            return {"label": label, "FAILED": "图片工具栏没渲染"}

        marks = []
        vias = []
        made = []
        prev = snap(pg)
        outcomes = []
        for k in range(1, how_many + 1):
            if k > 1:
                pg.evaluate(P811.SELECT, [IMG])
                pg.wait_for_timeout(800)
                P811.ensure_visible(pg, IMG)
            r, via = click_label(pg, label)
            vias.append({"第几次": k, "结果": r, "★ 命中路径": via})
            if r != "clicked":
                outcomes.append("★ 点不动（%s）" % r)
                break
            pg.wait_for_timeout(1000)
            cur = snap(pg)
            new = sorted(set(cur["ids"]) - set(prev["ids"]))
            made.extend(new)
            marks.append({"第几次": k, "节点": [prev["n"], cur["n"]],
                          "边": [prev["e"], cur["e"]],
                          "历史": [prev["past"], cur["past"]],
                          "这次新建了": new,
                          "这次新建了几个": len(new)})
            prev = cur
        # ★ 用户能不能分辨 + 三份叠没叠：可见文本 + 绝对几何（DOM）
        vis = pg.evaluate(P14.VISIBLE, made) if made else {}
        geom = pg.evaluate(GEOM, made) if made else {}
        # 按 kind 分组、排除选中态（814 的坑：选中会吃进编辑面板文字）
        groups = {}
        for i in made:
            g = (vis.get(i) or {})
            if not g.get("text") or g.get("selected"):
                continue
            groups.setdefault(g.get("type"), []).append(g["text"])
        xs = [(geom[i] or {}).get("x") for i in made]
        xs = [v for v in xs if v is not None]
        return {"label": label, "工具栏按钮": tb0["buttons"],
                "marks": marks, "UI 结局": outcomes, "命中路径": vias,
                "建出来的 id": made, "可见文本": vis, "绝对几何": geom,
                "★ 第一下建了东西": bool(marks)
                                     and marks[0]["这次新建了几个"] >= 1,
                "★ 逐次递增": all(y > x for m in marks for x, y in
                                  [(m["节点"][0], m["节点"][1])])
                             and all(marks[i + 1]["节点"][0] > marks[i]["节点"][1]
                                     for i in range(len(marks) - 1)),
                "★ 每个 kind 只有一种文本":
                    bool(groups) and all(len(set(v)) == 1 for v in groups.values()),
                "★ 同一 kind 出现过两次以上":
                    any(len(v) >= 2 for v in groups.values()),
                "★ 三份的 x 全同（叠在一起）":
                    bool(xs) and len(xs) >= 2 and len(set(xs)) == 1,
                "x 序列": xs,
                "一共建了几份": len(made),
                "★ 每一份都建成了 1 个节点": all(
                    m["这次新建了几个"] == 1 for m in marks)}
    except Exception as e:  # noqa: BLE001
        return {"label": label, "FAILED": "%s: %s" % (type(e).__name__, e)}
    finally:
        try:
            pg.close()
        except Exception:  # noqa: BLE001
            pass


#: 工具栏上的七个动作标签（`ImageNode.tsx:52-58` 与 `:141/:161`）
LABELS = ["旋转", "全景", "多角度", "打光", "九宫格", "高清", "宫格切分"]


def main():
    out = {"base": A.BASE, "img": IMG, "cells": []}
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        for rd in range(2):
            for label in LABELS:
                t0 = time.time()
                c = run(br, label, 3)
                c["round"] = rd
                c["secs"] = round(time.time() - t0, 1)
                out["cells"].append(c)
                OUT.parent.mkdir(parents=True, exist_ok=True)
                OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                               encoding="utf-8")
                print("rd%d %-8s %s  建了%s份 %s  结局=%s" % (
                    rd, label, c.get("FAILED") or "ok", c.get("一共建了几份"),
                    [(m["第几次"], m["节点"], m["这次新建了几个"])
                     for m in c.get("marks", [])],
                    c.get("UI 结局")), flush=True)
        br.close()
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("written", OUT)


if __name__ == "__main__":
    main()

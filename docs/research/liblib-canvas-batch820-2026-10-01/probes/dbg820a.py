#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 820 探针 —— ★ 撤销撤不掉，那**手动删**清得掉吗？

## 起点（819 自开的最重一条）

819 量到：连点 60 次 ⟹ 封顶 50 ⟹ **前 10 份永远撤不掉**；撤到底时
**全页没有任何提示**，而 UI 只把「撤销」灰掉。
819 的「不声称」里明写：

> **没测有没有别的自救路径**（手动拖走／逐个删）。
> ★ 但 816／817 已经证明叠在一起的那些份**连选都选不中**，
> ⟹ 「逐个删」**大概率也走不通**，★ **但那是从 816／817 的读数推的、
> 不是本批量的**。

⟹ 本批就去量那条推论。**它有可能把 819 的结论推翻**，这正是要量的理由。

## ★ 关键推论：Delete **每删一份，下一份就顶上来**

816 量到「点中心只选中最上面那一份」。于是：

> 点中心 → Delete ⟹ 删掉最上面那份 ⟹ **下一份自动顶上来**
> ⟹ 循环 N 次 ⟹ **N 份全清掉**

⟹ 若成立，「**撤不掉**」≠「**清不掉**」⟹ 819 的悲观结论要**大幅弱化**。

## ★ 两条臂：各测各的，但**都发生在同一个 T3 状态**上

★ 探针返工（**顺序错误**）：第一版把「创建副本」放在 Delete 循环**之后**
⟹ 而循环已经把 10 份**全清掉了** ⟹ 实测 `有活着的份可复制: false`
⟹ **那条臂前提不满足、作废**（807 纪律）。

★ 修法不是「就这样算作废」，而是**拆成两条臂**：

| 臂 | 测什么 | 前提 |
| --- | --- | --- |
| `A_delete_loop` | Delete 循环能不能清空 | T3 状态还剩 10 份 |
| `B_duplicate` | 「创建副本」把副本放哪 | T3 状态还剩 10 份 |

⟹ 两条臂都**独立地**先走到 T3（60 次点击 → 撤到底 → 还剩 10 份），
再各做各的事 ⟹ ★ **「对照」的前提是「对照的是同一件事」**。
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

OUT = pathlib.Path(os.environ.get("VB820_OUT") or
                   (HERE.parent / "raw" / "vb820a.json"))
IMG = "i-1FQ9tErTcC"
LABEL = "旋转"
HOWMANY = 60
MAXLOOP = 14          # 多按几次，用来确认**真的清空了**而不是「刚好按完」

SEL = """()=>Array.from(window.__libtv_store.getState().selectedNodeIds||[]);"""

GRAPH = """()=>{const S=window.__libtv_store.getState();
  const c=S.canvases.find(x=>x.id===S.activeCanvasId);
  const h=S.historyByCanvas[S.activeCanvasId]||{past:[],future:[]};
  return {nodeIds:c.nodes.map(n=>n.id).sort(),edges:c.edges.length,
          past:h.past.length,future:h.future.length};}"""

RECT = """(ids)=>{const o={};
  for(const id of ids){
    const e=document.querySelector('.react-flow__node[data-id="'+id+'"]');
    if(!e){o[id]=null;continue;}
    const r=e.getBoundingClientRect();
    o[id]={x:Math.round(r.left),y:Math.round(r.top),
           w:Math.round(r.width),h:Math.round(r.height),
           z:getComputedStyle(e).zIndex};}
  return o;}"""


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


def reach_T3(pg, label, how_many):
    """走到 819／818 的那个状态：连点 N 次 → 撤到底 → 还剩 M 份、`past` 空"""
    P811.boot(pg)
    pg.evaluate(P811.SELECT, [IMG])
    pg.wait_for_timeout(800)
    if not P811.ensure_visible(pg, IMG).get("★ 在视口内"):
        return None
    g0 = g(pg)
    base = {"节点数": len(g0["nodeIds"]), "历史": g0["past"]}
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
    for _ in range(how_many + 5):
        pg.keyboard.press("Meta+z")
        pg.wait_for_timeout(600)
    g_end = g(pg)
    made_set = set(made)
    return {"base": base, "made": made, "made_set": made_set,
            "还剩几份": len([v for v in g_end["nodeIds"] if v in made_set]),
            "节点数": len(g_end["nodeIds"]), "历史": g_end["past"]}


def arm_delete_loop(pg, t3, max_loop):
    """★ 核心：点中心 + Delete 循环"""
    made, made_set, base = t3["made"], t3["made_set"], t3["base"]
    loop = []
    for i in range(1, max_loop + 1):
        alive = [v for v in g(pg)["nodeIds"] if v in made_set]
        if not alive:
            loop.append({"第几次": i, "★ 点不动": True, "★ 还剩几份": 0,
                         "节点数": len(g(pg)["nodeIds"]), "★ 中断": True})
            break
        rects = pg.evaluate(RECT, alive)
        top = max(alive, key=lambda v: (rects.get(v) or {}).get("z") or "0")
        bb = pg.query_selector('.react-flow__node[data-id="%s"]' % top)
        box = bb.bounding_box()
        pg.mouse.click(box["x"] + box["width"] / 2,
                       box["y"] + box["height"] / 2)
        pg.wait_for_timeout(450)
        sel = set(pg.evaluate(SEL) or [])
        hit = [i + 1 for i, v in enumerate(made) if v in sel]
        before_n = len(g(pg)["nodeIds"])
        pg.keyboard.press("Delete")
        pg.wait_for_timeout(650)
        after = g(pg)
        loop.append({"第几次": i,
                     "★ 点之前活着的份数": len(alive),
                     "★ 选中的第几份": hit,
                     "★ 删掉的份数": before_n - len(after["nodeIds"]),
                     "★ 还剩几份": len([v for v in after["nodeIds"]
                                     if v in made_set]),
                     "节点数": len(after["nodeIds"]),
                     "历史": after["past"],
                     "★ 中断": not hit or before_n == len(after["nodeIds"])})
    g_after = g(pg)
    return {"Delete 循环": loop,
            "★ 循环之后还剩几份": len([v for v in g_after["nodeIds"]
                                   if v in made_set]),
            "★ 循环之后节点数": len(g_after["nodeIds"]),
            "★ 循环之后历史": g_after["past"],
            "★ 清空了所有产物": len([v for v in g_after["nodeIds"]
                                 if v in made_set]) == 0,
            "★ 回到起点": [len(g_after["nodeIds"]), g_after["past"]]
                          == [base["节点数"], base["历史"]]}


def arm_duplicate(pg, t3):
    """★ 「创建副本」把副本放哪（`duplicateGraphSelection` 会 +40,+40）"""
    made_set = t3["made_set"]
    pg.evaluate(P811.SELECT, [IMG])
    pg.wait_for_timeout(600)
    alive = [v for v in g(pg)["nodeIds"] if v in made_set]
    dup = {"有活着的份可复制": bool(alive), "★ 前提不满足": not bool(alive)}
    if not alive:
        return dup
    rects = pg.evaluate(RECT, alive)
    top = max(alive, key=lambda v: (rects.get(v) or {}).get("z") or "0")
    src_rect = rects.get(top) or {}
    box = pg.query_selector('.react-flow__node[data-id="%s"]' % top).bounding_box()
    pg.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2,
                   button="right")
    pg.wait_for_timeout(500)
    item = pg.query_selector('[data-canvas-context-item="创建副本"]')
    if not item:
        dup["FAILED"] = "菜单里没有「创建副本」项"
        pg.keyboard.press("Escape")
        return dup
    before_ids = set(g(pg)["nodeIds"])
    item.click()
    pg.wait_for_timeout(900)
    new_ids = sorted(set(g(pg)["nodeIds"]) - before_ids)
    rr = pg.evaluate(RECT, new_ids) if new_ids else {}
    moved = [(k, v.get("x"), v.get("y"), src_rect.get("x"), src_rect.get("y"))
             for k, v in rr.items()
             if v and (v.get("x") != src_rect.get("x")
                       or v.get("y") != src_rect.get("y"))]
    dup.update({"建出了几个": len(new_ids), "新节点矩形": rr,
                "原节点矩形": src_rect, "★ 副本有没有挪开": moved,
                "★ 副本的 z": [(k, (rr.get(k) or {}).get("z")) for k in rr],
                "★ 副本与原节点的屏幕位移": [
                    (v.get("x") - src_rect.get("x"),
                     v.get("y") - src_rect.get("y"))
                    for v in rr.values() if v]})
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(300)
    return dup


def run(b, key, label, how_many, max_loop):
    pg = b.new_page()
    pg.set_default_timeout(25000)
    try:
        t3 = reach_T3(pg, label, how_many)
        if not t3 or t3.get("FAILED"):
            return {"FAILED": (t3 or {}).get("FAILED", "没走到 T3")}
        out = {"label": label, "key": key, "howmany": how_many,
               "max_loop": max_loop,
               "起点": t3["base"], "★ 建出来的 id 数": len(t3["made"]),
               "★ 撤完之后还剩几份": t3["还剩几份"],
               "★ 撤完之后节点数": t3["节点数"],
               "★ 撤完之后历史": t3["历史"]}
        if key == "A_delete_loop":
            out.update(arm_delete_loop(pg, t3, max_loop))
            out["★ 创建副本"] = {"★ 本臂不测这一步": "见 B_duplicate 臂"}
        else:
            out["Delete 循环"] = []
            out["★ 循环之后还剩几份"] = t3["还剩几份"]
            out["★ 循环之后节点数"] = t3["节点数"]
            out["★ 循环之后历史"] = t3["历史"]
            out["★ 清空了所有产物"] = t3["还剩几份"] == 0
            out["★ 回到起点"] = [t3["节点数"], t3["历史"]] == [
                t3["base"]["节点数"], t3["base"]["历史"]]
            out["★ 创建副本"] = arm_duplicate(pg, t3)
        return out
    except Exception as e:  # noqa: BLE001
        return {"FAILED": "%s: %s" % (type(e).__name__, e)}
    finally:
        try:
            pg.close()
        except Exception:  # noqa: BLE001
            pass


ARMS = [("A_delete_loop", "★ Delete 循环能不能清空"),
        ("B_duplicate", "★「创建副本」把副本放哪")]


def main():
    out = {"base": A.BASE, "img": IMG, "label": LABEL, "howmany": HOWMANY,
           "max_loop": MAXLOOP, "arms": [{"key": k, "why": w} for k, w in ARMS],
           "cells": []}
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        for key, _why in ARMS:
            t0 = time.time()
            c = run(br, key, LABEL, HOWMANY, MAXLOOP)
            c["round"] = 0
            c["secs"] = round(time.time() - t0, 1)
            out["cells"].append(c)
            OUT.parent.mkdir(parents=True, exist_ok=True)
            OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                           encoding="utf-8")
            print("%-15s %s | 撤完剩%s份 | 循环=%s | 清空=%s | 副本挪开=%s | %ss" % (
                key, c.get("FAILED") or "ok", c.get("★ 撤完之后还剩几份"),
                [(s.get("第几次"), s.get("★ 选中的第几份"),
                  s.get("★ 还剩几份")) for s in (c.get("Delete 循环") or [])],
                c.get("★ 清空了所有产物"),
                (c.get("★ 创建副本") or {}).get("★ 副本有没有挪开"),
                c.get("secs")), flush=True)
        br.close()
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("written", OUT)


if __name__ == "__main__":
    main()
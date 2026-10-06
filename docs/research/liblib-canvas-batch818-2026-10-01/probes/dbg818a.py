#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 818 探针 —— 历史栈的**边界**：连点 N 次，撤 N 次能不能撤干净？

## 起点（817 自开的洞）

817 量到「叠 5 份之后连撤 6 次精确回到起点」，但它的「不声称」里明写两条：

- ★ **「只叠 5 份、一次都不删、连撤 5 次能不能回到起点」这条更简单的序列没测**
  （817 的撤销前提是「先按右键删除过一次」，要按 6 次才回到起点）；
- ★ **「能不能叠到几十份、会不会撞上 `MAX_HISTORY`」未测**。

## ★ 这批的**因果读数**（不是「撤不干净」，而是「撤不掉几份」）

`canvasStore.ts:464` `const MAX_HISTORY = 50;`
`pushHistory`（`:507`）每次把**当前整张图**深拷贝一份推进 `past`，然后
`.slice(-MAX_HISTORY)`。

⟹ 于是有一条**可以反推的因果**：连点 N 次（N > 封顶值）之后，
最老的 N−封顶 份快照**已经被丢掉** ⟹ 连撤到底**撤不掉那几份**，
而**撤不掉的份数应当恰好等于 N − 封顶值**。

★ 这就是本批的主读数：**不是**「撤销坏了」，而是「**撤销够不着**」。

## ★ 必须有对照臂（807 起立的纪律）

只有一条「跨过封顶」的臂 ⟹ 「撤不干净」分不清是**历史封顶**
还是**撤销本身坏了** ⟹ 另加一条**远在封顶之前**的臂（「撤得干净」）作对照。

## ★ 封顶点从**数据反推**，不写死

探针只逐次记录**历史长度**；判据去找「历史长度不再增长」的那一步，
再拿它跟源码里读出来的 `MAX_HISTORY` 对账 ⟹ **不预设常量**。
"""
import json
import os
import pathlib
import re
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

OUT = pathlib.Path(os.environ.get("VB818_OUT") or
                   (HERE.parent / "raw" / "vb818a.json"))
IMG = "i-1FQ9tErTcC"
LABEL = "旋转"          # ★ 抽一个动作：811/812/813 已确立「动作之间只有 offset
                        # 与 dimensions 不同」，而本批判的是**历史栈**这个
                        # **与动作无关**的量 ⟹ 七个动作全跑是浪费
#: (键, 连点次数, 这条臂要证明什么)
CASES = [
    ("A_far_below_cap", 12, "★ 对照臂：远在封顶之前 ⟹ 撤得干净"),
    ("B_past_cap", 60, "★ 跨过封顶 ⟹ 撤不干净，且撤不掉的份数有公式"),
]


#: ★ 本地读数：**`P811.active()` 只给 `past`，不给 `future`**
#: —— 若直接 `g0.get("future")` 会静默读成 **0**，那正是 807～810 反复踩的
#: 「**恒定无信息的读数比没有读数更危险**」。所以自己读一次。
GRAPH = """()=>{const S=window.__libtv_store.getState();
  const c=S.canvases.find(x=>x.id===S.activeCanvasId);
  const h=S.historyByCanvas[S.activeCanvasId]||{past:[],future:[]};
  return {nodeIds:c.nodes.map(n=>n.id).sort(),edges:c.edges.length,
          past:h.past.length,future:h.future.length};}"""


def g(pg):
    return pg.evaluate(GRAPH)


def click_label(pg, label):
    """三条匹配路径（`ImageToolbar.tsx:171` 的 `!iconOnly && <span>` ⟹
    「旋转」没有可见文字，只有 aria-label／title）"""
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
        base = {"节点数": len(g0["nodeIds"]), "历史": g0["past"],
                "future": g0["future"], "id": list(g0["nodeIds"])}

        # ── 连点 N 次，**逐次**记历史长度与节点数（封顶点要从这里反推）
        # ★ 探针返工：这一版把 `new` 算成「相对**初始**快照的新增」，
        #   于是 `这次新建了几个` 记的是**累计值** 1,2,…,N（arm A 的
        #   `建出来的 id 数` 变成 1+2+…+12 = **78**）⟹ S1「每一下都建了
        #   **1** 个」直接判红。★ 判红的是**前提**检查 —— 这正是
        #   「前提不满足的臂显式作废」那条纪律在**抓夹具 bug**，
        #   而不是在报应用缺陷。修法：拿**上一步**的 id 集合做差。
        click_steps, made = [], []
        prev_ids = list(g0["nodeIds"])
        for k in range(1, how_many + 1):
            if k > 1:
                pg.evaluate(P811.SELECT, [IMG])
                pg.wait_for_timeout(600)
                P811.ensure_visible(pg, IMG)
            r, via = click_label(pg, label)
            if r != "clicked":
                return {"FAILED": "第%d 下没点上：%s" % (k, r)}
            pg.wait_for_timeout(800)
            cur = g(pg)
            new = sorted(set(cur["nodeIds"]) - set(prev_ids))
            made.extend(new)
            click_steps.append({"第几次": k, "历史": cur["past"],
                                "节点数": len(cur["nodeIds"]),
                                "future": cur["future"],
                                "这次新建了几个": len(new),
                                "这次新建的 id": new,
                                "★ 命中路径": via})
            prev_ids = list(cur["nodeIds"])

        made_set = set(made)
        # ── 连撤 N 次，**逐次**记（撤到底之后再多按几次，看有没有变化）
        undo_steps = []
        for k in range(1, how_many + 5):
            pg.keyboard.press("Meta+z")
            pg.wait_for_timeout(700)
            cur = g(pg)
            undo_steps.append({
                "第几次撤销": k,
                "还活着的份数": len([v for v in cur["nodeIds"] if v in made_set]),
                "节点数": len(cur["nodeIds"]),
                "历史": cur["past"],
                "future": cur["future"],
                "选区": len(pg.evaluate(
                    "()=>Array.from("
                    "(window.__libtv_store.getState().selectedNodeIds||[]))"))})

        # ── 撤到底之后**还能不能继续新建**（封顶不该挡住新建）
        pg.evaluate(P811.SELECT, [IMG])
        pg.wait_for_timeout(700)
        r2, _ = click_label(pg, label)
        pg.wait_for_timeout(900)
        after_cap = g(pg)
        again = sorted(set(after_cap["nodeIds"]) - set(made_set)
                       - set(base["id"]))

        return {
            "label": label, "howmany": how_many,
            "起点": base, "建出来的 id": made,
            "★ 连点次数": len(click_steps),
            "★ 每一下都建了东西": all(
                c["这次新建了几个"] == 1 for c in click_steps),
            "点选逐次": click_steps,
            "撤销逐次": undo_steps,
            "★ 撤完之后还活着的份数": undo_steps[-1]["还活着的份数"],
            "★ 撤完之后节点数": undo_steps[-1]["节点数"],
            "★ 撤完之后历史": undo_steps[-1]["历史"],
            "★ 撤完之后 future": undo_steps[-1]["future"],
            "★ 回到起点": [undo_steps[-1]["节点数"], undo_steps[-1]["历史"]]
                          == [base["节点数"], base["历史"]],
            "★ 封顶后还能不能新建": r2,
            "★ 封顶后再建出了几个": len(again),
            "★ 封顶后再建后的节点数": len(after_cap["nodeIds"]),
        }
    except Exception as e:  # noqa: BLE001
        return {"FAILED": "%s: %s" % (type(e).__name__, e)}
    finally:
        try:
            pg.close()
        except Exception:  # noqa: BLE001
            pass


def main():
    src = (HERE.parent.parent.parent.parent / "src/store/canvasStore.ts").read_text(
        encoding="utf-8")
    cap = re.search(r"const MAX_HISTORY = (\d+)", src)
    out = {"base": A.BASE, "img": IMG, "label": LABEL,
           "cases": [{"key": k, "howmany": n, "why": w} for k, n, w in CASES],
           "源码里的 MAX_HISTORY": int(cap.group(1)) if cap else None,
           "cells": []}
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        for rd in range(2):
            for key, n, _w in CASES:
                t0 = time.time()
                c = run(br, LABEL, n)
                c["key"] = key
                c["round"] = rd
                c["secs"] = round(time.time() - t0, 1)
                out["cells"].append(c)
                OUT.parent.mkdir(parents=True, exist_ok=True)
                OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                               encoding="utf-8")
                print("rd%d %-16s %s | 封顶后还剩%s份 回到起点=%s 封顶后可新建=%s(%s个) %ss" % (
                    rd, key, c.get("FAILED") or "ok",
                    c.get("★ 撤完之后还活着的份数"), c.get("★ 回到起点"),
                    c.get("★ 封顶后还能不能新建"),
                    c.get("★ 封顶后再建出了几个"), c.get("secs")), flush=True)
        br.close()
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("written", OUT)


if __name__ == "__main__":
    main()
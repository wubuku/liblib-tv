#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 816 探针 —— 三份完全重叠的产物，用户**够得着**底下那两份吗

## 起点（815 直接留下的洞）

815 量到：`ImageNode` 七个动作连点三次，三份产物 **x／y／宽高逐像素相同**
（`canvasStore.ts:1784-1792` 的位置是「**源节点**绝对位置 + 源宽 + offset」，
三次 `sourceId` 是同一个 ⟹ 必然算出同一个坐标）。

815 的「不声称」里明写：★ **三份压在一起之后用户还能不能选中底下那两份，
本批没测**。本批就测这一条。

## ★ 为什么不能只点一下就下结论（807 起立的纪律）

「点不中底下那一份」有两种完全不同的成因：
① 命中测试天然只命中**最上层**那一份（**Z 序**问题）；
② 底下那两份**根本没被选中逻辑排除**，只是**没有别的路径**能把它们选出来。

所以本批**不只点一次**，而是把**所有可能的选中路径各走一遍**，
逐条记录选区变成什么：

| 路径 | 静态依据 |
| --- | --- |
| 点中心 | `page.tsx:1545` `onNodeClick` → `selectNode(node.id)` |
| Ctrl／Cmd + 点 | 同上，条件是 `!event.metaKey && !event.ctrlKey` ⟹ **带修饰键反而不选** |
| 框选（空白处左键拖） | `page.tsx:1624` `selectionOnDrag={false}` + `selectNodesOnDrag={false}` |
| `Cmd+A` 全选 | 全仓**没有** `selectAllNodes`（只有 FrameOS／即梦那两个画布有） |
| `Delete` 删选区 | `page.tsx:1376` 自己处理 Delete／Backspace |

⟹ 静态只说明**路径存不存在**，读数才说明**走一遍会发生什么**。

## ★ 探针返工的纪律

点击之前**必须先把选区挪走**（点一下源图片），否则第三次点击后新节点本来就是
选中态（`addDerivedNode` 里有 `selectedNodeIds: [nodeId]`），
「点中心之后选区没变」会被我误读成「点不中」。
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

OUT = pathlib.Path(os.environ.get("VB816_OUT") or
                   (HERE.parent / "raw" / "vb816a.json"))
IMG = "i-1FQ9tErTcC"
LABELS = ["旋转", "全景", "多角度", "打光", "九宫格", "高清", "宫格切分"]

#: 三个 id 在 DOM 里的先后 + z-index（React Flow 按数组顺序渲染，
#:   选中态可能把它挪到末尾 ⟹ 所以**两个都记**，让读数自己说话）
ZORDER = """(ids)=>{const all=Array.from(
    document.querySelectorAll('.react-flow__node'));
  const idx=new Map(all.map((e,i)=>[e.getAttribute('data-id'),i]));
  const o={};
  for(const id of ids){
    const e=document.querySelector('.react-flow__node[data-id="'+id+'"]');
    o[id]=e?{dom序号:all.indexOf(e),
             zIndex:getComputedStyle(e).zIndex,
             rect:(()=>{const r=e.getBoundingClientRect();
               return {x:Math.round(r.left),y:Math.round(r.top),
                       w:Math.round(r.width),h:Math.round(r.height)};})()}
           :null;
  } return {每份:o, 总节点数:all.length};}"""

#: 视口变换（用来判「空白处左键拖」到底是框选还是平移）
VIEW = """()=>{const e=document.querySelector('.react-flow__viewport');
  return e?e.style.transform:null;}"""

SEL = """()=>Array.from(window.__libtv_store.getState().selectedNodeIds||[]);"""

#: ★★ 探针返工（第一版踩的夹具坑）：第一版在**写死**的 `(40,400)` 上做
#:   空白处拖拽，结果「视口没变、选区也没多选」—— 可那**不能**说明
#:   「框选这条路不存在」：**那个点可能在画布之外**（侧栏／工具条），
#:   于是这条臂什么都没发生。809/810 的老坑：**夹具失败会伪装成读数**。
#:   ⟹ 修法：先扫出一个**确实落在 `.react-flow__pane` 上**的点再拖，
#:     并把该点上 `elementFromPoint` 的 className **一并记下来**当证据。
PANE_PROBE = """()=>{const W=window.innerWidth,H=window.innerHeight;
  for(let y=120;y<H-140;y+=40){
    for(let x=120;x<W-120;x+=40){
      const e=document.elementFromPoint(x,y);
      if(e&&e.classList&&e.classList.contains('react-flow__pane'))
        return {x,y,命中类名:e.className};
    }}
  return null;}"""


def active_ids(pg):
    g = P811.active(pg)
    return g["nodeIds"]


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


def box_of(pg, node_id):
    e = pg.query_selector('.react-flow__node[data-id="%s"]' % node_id)
    return e.bounding_box() if e else None


def run(b, label, how_many):
    pg = b.new_page()
    pg.set_default_timeout(20000)
    try:
        P811.boot(pg)
        pg.evaluate(P811.SELECT, [IMG])
        pg.wait_for_timeout(800)
        if not P811.ensure_visible(pg, IMG).get("★ 在视口内"):
            return {"label": label, "FAILED": "图片节点不在视口"}

        # ── 连点若干次，建出若干份
        vias, made, prev = [], [], list(active_ids(pg))
        for k in range(1, how_many + 1):
            if k > 1:
                pg.evaluate(P811.SELECT, [IMG])
                pg.wait_for_timeout(700)
                P811.ensure_visible(pg, IMG)
            r, via = click_label(pg, label)
            vias.append({"第几次": k, "结果": r, "★ 命中路径": via})
            if r != "clicked":
                return {"label": label, "FAILED": "第%d 下没点上：%s" % (k, r)}
            pg.wait_for_timeout(900)
            cur = list(active_ids(pg))
            made.extend(sorted(set(cur) - set(prev)))
            prev = cur
        if len(made) < 2:
            return {"label": label, "FAILED": "只建出 %d 份" % len(made)}

        zo = pg.evaluate(ZORDER, made)
        ids = list(made)

        def rel(sel):
            """把选区换算成「这几份里的第几份」，0 = 都不是
            ★ `选区原文` 是**原始 `selectedNodeIds`** —— 验收器要从它**重算**
              （815 的教训：判据读探针换算过的字段，阴性对照就打不中真正的读数）"""
            raw_sel = list(pg.evaluate(SEL) or [])
            s = set(raw_sel)
            hit = [i + 1 for i, v in enumerate(ids) if v in s]
            return {"选区原文": raw_sel, "★ 选中的第几份": hit,
                    "选中份数": len(hit),
                    "选区里还有别的": sorted(s - set(ids))}

        # ★ 点击之前**先把选区挪走**，否则「点中心后没变」会被误读
        pg.evaluate(P811.SELECT, [IMG])
        pg.wait_for_timeout(600)
        before = rel(None)

        # ── 路径一：点中心
        box = box_of(pg, ids[-1])
        if not box:
            return {"label": label, "FAILED": "拿不到叠在一起那份的包围盒"}
        cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
        pg.mouse.click(cx, cy)
        pg.wait_for_timeout(700)
        click1 = rel(None)

        # ── 路径二：Cmd／Ctrl + 点中心
        pg.evaluate(P811.SELECT, [IMG])
        pg.wait_for_timeout(600)
        pg.keyboard.down("Meta")
        pg.mouse.click(cx, cy)
        pg.keyboard.up("Meta")
        pg.wait_for_timeout(700)
        click2 = rel(None)

        # ── 路径三：Cmd+A 全选
        pg.evaluate(P811.SELECT, [IMG])
        pg.wait_for_timeout(600)
        pg.keyboard.press("Meta+a")
        pg.wait_for_timeout(700)
        selall = rel(None)

        # ── 路径四：Delete 删掉当前选区（先点中心选一个）
        pg.mouse.click(cx, cy)
        pg.wait_for_timeout(600)
        pre_del = rel(None)
        n_before = len(active_ids(pg))
        pg.keyboard.press("Delete")
        pg.wait_for_timeout(900)
        alive_after_del = list(active_ids(pg))
        n_after = len(alive_after_del)
        # ── 撤销能不能救回来
        pg.keyboard.press("Meta+z")
        pg.wait_for_timeout(900)
        alive_back = list(active_ids(pg))
        back = sorted(set(alive_back) & set(ids))
        gone = [i + 1 for i, v in enumerate(ids) if v not in alive_after_del]

        # ── 路径五：空白处左键拖（框选？平移？）
        # ★ 拖拽点必须**先证明落在 pane 上**，否则这条臂的读数不作数
        pane = pg.evaluate(PANE_PROBE)
        if not pane:
            return {"label": label, "FAILED": "找不到落在 pane 上的点"}
        pg.evaluate(P811.SELECT, [IMG])
        pg.wait_for_timeout(500)
        v0 = pg.evaluate(VIEW)
        pg.mouse.move(pane["x"], pane["y"])
        pg.mouse.down()
        pg.mouse.move(pane["x"] + 160, pane["y"] + 60, steps=8)
        pg.mouse.up()
        pg.wait_for_timeout(600)
        v1 = pg.evaluate(VIEW)
        after_drag = rel(None)

        return {
            "label": label, "命中路径": vias, "建出来的 id": ids,
            "Z 序": zo,
            "★ 三份坐标全同": len({(d["rect"]["x"], d["rect"]["y"],
                                   d["rect"]["w"], d["rect"]["h"])
                                 for d in zo["每份"].values() if d}) == 1,
            "★ DOM 最靠后的一份": (sorted(
                (v["dom序号"], k) for k, v in zo["每份"].items() if v)[-1][1]
                if zo["每份"] else None),
            "★ 点之前": before,
            "★ 路径一·点中心": click1,
            "★ 路径二·Cmd+点中心": click2,
            "★ 路径三·Cmd+A": selall,
            "★ 路径四·Delete 前": pre_del,
            "★ 路径四·删掉的是第几份": gone,
            "★ 路径四·删完还活着的 id": [i for i in alive_after_del if i in set(ids)],
            "★ 路径四·删掉的份数": n_before - n_after,
            "★ 撤销后活着的 id": [i for i in alive_back if i in set(ids)],
            "★ 撤销后还在的份数": len(back),
            "★ 路径五·拖拽点": pane,
            "★ 路径五·拖之前视口": v0,
            "★ 路径五·拖之后视口": v1,
            "★ 路径五·视口变了": v0 != v1,
            "★ 路径五·拖完选区": after_drag,
        }
    except Exception as e:  # noqa: BLE001
        return {"label": label, "FAILED": "%s: %s" % (type(e).__name__, e)}
    finally:
        try:
            pg.close()
        except Exception:  # noqa: BLE001
            pass


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
                print("rd%d %-6s %s | 顶层=%s 点中=%s Cmd点=%s 全选=%s 删掉=%s 撤回到=%s 平移=%s" % (
                    rd, label, c.get("FAILED") or "ok",
                    c.get("★ DOM 最靠后的一份"),
                    (c.get("★ 路径一·点中心") or {}).get("★ 选中的第几份"),
                    (c.get("★ 路径二·Cmd+点中心") or {}).get("★ 选中的第几份"),
                    (c.get("★ 路径三·Cmd+A") or {}).get("选中份数"),
                    c.get("★ 路径四·删掉的是第几份"),
                    c.get("★ 撤销后还在的份数"),
                    c.get("★ 路径五·视口变了")), flush=True)
        br.close()
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("written", OUT)


if __name__ == "__main__":
    main()
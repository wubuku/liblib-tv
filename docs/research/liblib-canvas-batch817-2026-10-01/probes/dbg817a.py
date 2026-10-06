#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 817 探针 —— 叠到五份之后：还点得中底下那四份吗？连续撤得干净吗？

## 起点（815／816 各自留下的洞）

- 815 只测到**三份**，「不声称」里明写「**只测了连点三次**」。
- 816 只测了**点中心／Cmd+点／Cmd+A／pane 拖／Delete／撤一次**，
  「不声称」里明写三处：
  ① 「**第四份、第五份叠上去之后是否仍只有最上面那份可点未测**」
     （按 `z-index` 机理应当仍是，但 ★ **没量就不说**）；
  ② 「**连按 `Cmd+Z` 能不能把多份全撤掉未测**」
     —— 811／814 只量过「**单次**撤销」；
  ③ 「**右键菜单路径没测**」（807／808 两批留的同一条遗留）。

⟹ 本批把三条一次测掉。

## ★ 为什么一定要连按而不是只按一次

单次撤销成立（811／814）**不蕴含**连按成立：`undo()` 里有可能在中途撞上
`MAX_HISTORY` 截断、或某一步 `currentCanvas` 与画布对不上而**静默 return**。
⟹ 必须**逐次**记录节点数／存活份数，**不能**只看最后一步。

## ★ 右键菜单：菜单本身也是一条路径

`page.tsx:1656` 的 `onNodeContextMenu` 会 `selectNode(node.id)` **再**打开
`CanvasContextMenu`，而菜单里有 `data-canvas-context-item="删除"`。
⟹ 右键是**独立于左键**的另一条入口，得单独量它选中的是哪一份、删掉的是哪一份。
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

OUT = pathlib.Path(os.environ.get("VB817_OUT") or
                   (HERE.parent / "raw" / "vb817a.json"))
IMG = "i-1FQ9tErTcC"
LABELS = ["旋转", "全景", "多角度", "打光", "九宫格", "高清", "宫格切分"]
HOWMANY = 5

SEL = """()=>Array.from(window.__libtv_store.getState().selectedNodeIds||[]);"""

ZO = """(ids)=>{const all=Array.from(
    document.querySelectorAll('.react-flow__node'));
  const o={};
  for(const id of ids){
    const e=document.querySelector('.react-flow__node[data-id="'+id+'"]');
    if(!e){o[id]=null;continue;}
    const r=e.getBoundingClientRect();
    o[id]={dom序号:all.indexOf(e),
           zIndex:getComputedStyle(e).zIndex,
           rect:{x:Math.round(r.left),y:Math.round(r.top),
                 w:Math.round(r.width),h:Math.round(r.height)}};
  } return o;}"""

#: 右键菜单的**可见读数**（808 的纪律：能读 DOM 就不只读 store）
MENU = """()=>{const m=document.querySelector('[data-canvas-context-menu]');
  if(!m)return null;
  return {可见文本:(m.textContent||'').trim().replace(/\\s+/g,' ').slice(0,200),
          菜单项:Array.from(m.querySelectorAll('[data-canvas-context-item]'))
                 .map(e=>(e.getAttribute('data-canvas-context-item')||'')
                          .trim())};}"""


def active(pg):
    return P811.active(pg)


def ids_of(pg):
    return list(active(pg)["nodeIds"])


def click_label(pg, label):
    """三条匹配路径（`ImageToolbar.tsx:171` 的 `!iconOnly && <span>` ⟹
    「旋转」没有可见文字）"""
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


def run(b, label):
    pg = b.new_page()
    pg.set_default_timeout(20000)
    try:
        P811.boot(pg)
        pg.evaluate(P811.SELECT, [IMG])
        pg.wait_for_timeout(800)
        if not P811.ensure_visible(pg, IMG).get("★ 在视口内"):
            return {"label": label, "FAILED": "图片节点不在视口"}

        g0 = active(pg)
        base_n, base_past = len(g0["nodeIds"]), g0["past"]

        # ── 连点五次
        vias, made, prev = [], [], list(ids_of(pg))
        for k in range(1, HOWMANY + 1):
            if k > 1:
                pg.evaluate(P811.SELECT, [IMG])
                pg.wait_for_timeout(700)
                P811.ensure_visible(pg, IMG)
            r, via = click_label(pg, label)
            vias.append({"第几次": k, "结果": r, "★ 命中路径": via})
            if r != "clicked":
                return {"label": label, "FAILED": "第%d 下没点上：%s" % (k, r)}
            pg.wait_for_timeout(900)
            cur = list(ids_of(pg))
            made.extend(sorted(set(cur) - set(prev)))
            prev = cur
        if len(made) < HOWMANY:
            return {"label": label, "FAILED": "只建出 %d 份" % len(made)}
        ids = list(made)

        zo = pg.evaluate(ZO, ids)

        def rel():
            sel = set(pg.evaluate(SEL) or [])
            return {"选区原文": list(pg.evaluate(SEL) or []),
                    "★ 选中的第几份": [i + 1 for i, v in enumerate(ids)
                                       if v in sel]}

        # ── 路径一：点中心
        pg.evaluate(P811.SELECT, [IMG])
        pg.wait_for_timeout(600)
        box = pg.query_selector('.react-flow__node[data-id="%s"]' % ids[-1])
        bb = box.bounding_box()
        cx, cy = bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2
        pg.mouse.click(cx, cy)
        pg.wait_for_timeout(700)
        p1 = rel()

        # ── 路径二：右键中心 → 菜单 → 「删除」
        pg.evaluate(P811.SELECT, [IMG])
        pg.wait_for_timeout(600)
        pg.mouse.click(cx, cy, button="right")
        pg.wait_for_timeout(700)
        p2 = rel()
        menu = pg.evaluate(MENU)
        before_del = list(ids_of(pg))
        item = pg.query_selector('[data-canvas-context-item="删除"]')
        if not item:
            return {"label": label, "FAILED": "右键菜单里没有「删除」项",
                    "菜单": menu}
        item.click()
        pg.wait_for_timeout(900)
        after_del = list(ids_of(pg))
        gone = [i + 1 for i, v in enumerate(ids) if v not in after_del]

        # ── 连续撤销：先撤掉那次删除，再一路撤掉五次创建
        undo_steps = []
        for step in range(HOWMANY + 1):
            pg.keyboard.press("Meta+z")
            pg.wait_for_timeout(850)
            alive = list(ids_of(pg))
            g = active(pg)
            undo_steps.append({
                "第几次撤销": step + 1,
                "还活着的份数": len([v for v in alive if v in set(ids)]),
                "总节点数": len(alive),
                "历史": g["past"],
                "选区": list(pg.evaluate(SEL) or [])})

        g_end = active(pg)
        return {
            "label": label, "命中路径": vias, "建出来的 id": ids,
            "★ 叠了几份": len(ids),
            "★ 起点节点数/历史": [base_n, base_past],
            "★ 五份坐标全同": len({(v["rect"]["x"], v["rect"]["y"],
                                 v["rect"]["w"], v["rect"]["h"])
                              for v in zo.values() if v}) == 1,
            "Z 序": zo,
            "★ z-index 大于 0 的有几份": len([v for v in zo.values()
                                       if v and v["zIndex"] != "0"]),
            "★ 路径一·点中心": p1,
            "★ 路径二·右键中心": p2,
            "★ 右键菜单": menu,
            "★ 路径三·右键删除前节点数": len(before_del),
            "★ 路径三·右键删掉的是第几份": gone,
            "★ 路径三·删掉的份数": len(before_del) - len(after_del),
            "★ 连续撤销逐次": undo_steps,
            "★ 撤完之后这几份还剩": len([v for v in ids_of(pg)
                                     if v in set(ids)]),
            "★ 撤完之后总节点数": len(g_end["nodeIds"]),
            "★ 撤完之后历史": g_end["past"],
            "★ 回到起点": [len(g_end["nodeIds"]), g_end["past"]] == [base_n, base_past],
        }
    except Exception as e:  # noqa: BLE001
        return {"label": label, "FAILED": "%s: %s" % (type(e).__name__, e)}
    finally:
        try:
            pg.close()
        except Exception:  # noqa: BLE001
            pass


def main():
    out = {"base": A.BASE, "img": IMG, "howmany": HOWMANY, "cells": []}
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        for label in LABELS:
            t0 = time.time()
            c = run(br, label)
            c["round"] = 0
            c["secs"] = round(time.time() - t0, 1)
            out["cells"].append(c)
            OUT.parent.mkdir(parents=True, exist_ok=True)
            OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                           encoding="utf-8")
            print("%-6s %s | 叠%s份 点中=%s 右键中=%s 右键删掉=%s 撤销序列=%s 回到起点=%s" % (
                label, c.get("FAILED") or "ok", c.get("★ 叠了几份"),
                (c.get("★ 路径一·点中心") or {}).get("★ 选中的第几份"),
                (c.get("★ 路径二·右键中心") or {}).get("★ 选中的第几份"),
                c.get("★ 路径三·右键删掉的是第几份"),
                [s["还活着的份数"] for s in (c.get("★ 连续撤销逐次") or [])],
                c.get("★ 回到起点")), flush=True)
        br.close()
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("written", OUT)


if __name__ == "__main__":
    main()
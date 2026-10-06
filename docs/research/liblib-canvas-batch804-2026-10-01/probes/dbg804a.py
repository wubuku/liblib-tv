#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 804 探针 a：点项目卡打开的新标签页，是不是你点的那张画布

## 缺陷（759 ①，至今未修）

`src/app/project/page.tsx:28-31`：

    const openCanvas = (canvasId: string) => {
      setActiveCanvas(canvasId);          // ← 只改**当前标签页**的内存
      window.open("/", "_blank");         // ← 新标签页有**自己的** store 实例
    };

`activeCanvasId` 只活在内存里（`canvasStore.ts` 全文**没有** persist / localStorage），
所以新标签页永远从 `createInitialState` 的初始值起步（`:1175` `activeCanvasId: "canvas-2"`）。

★ 759 实测：点 `canvas-1`（0 个节点）的卡 ⟹ 本标签页 active 变成 `canvas-1`，
新标签页 active 是 `canvas-2`、节点数 10 ⟹ 内容肉眼可辨地不是同一个。
本批**独立复现**一遍，而不是引用 759 的读数。

## 两条 DOM 读数，都不用 store

★ 判据只认**用户看得见**的东西，不读 `window.__libtv_store`：

  ① `[data-canvas-active="true"]` 所在的 `[data-canvas-row]` ⟹ 画布下拉里
     被标成当前的那一行，它的 `data-canvas-row` 值**就是画布 id**。
  ② `.react-flow__node` 的**数量** ⟹ 这张画布上画了几个东西。
     种子数据里两张画布节点数不同（0 与 10），所以数量能区分二者。

`src/app/project/page.tsx:238` 的 `data-project-card={canvas.id}` ⟹
卡片的 `data-*` **自带目标 id**，探针不必去问 store「我要点的是哪张」。

## 为什么方向要**两个都跑**

只跑一个方向会漏掉「恰好蒙对」。默认 active 是 `canvas-2`，所以点 `canvas-1` 一定错；
再点 `canvas-2` 一定「对」——但那是**默认蒙对的**，不是功能对。两个方向都记，
才看得出这是「完全不生效」还是「只在非默认时生效」。
"""
import json
import pathlib
import sys

from playwright.sync_api import sync_playwright

BASE = "http://localhost:4317"
OUT = pathlib.Path(
    "/Users/yangjiefeng/Documents/wubuku/liblib-tv"
    "/docs/research/liblib-canvas-batch803-2026-10-01/raw/../"
    "raw/vb804a-PLACEHOLDER.json")

# 页面里能看到的「当前是哪张画布」——两条独立读数
READ_ACTIVE = r"""()=>{
  const trigger = document.querySelector('[data-canvas-trigger]');
  if (trigger) trigger.click();          // 打开画布下拉，行才在 DOM 里
  return new Promise(res=>setTimeout(()=>{
    const active = document.querySelector('[data-canvas-active="true"]');
    const row = active ? active.closest('[data-canvas-row]') : null;
    const rows = Array.from(document.querySelectorAll('[data-canvas-row]'));
    res({
      dropdownOpened: !!trigger,
      activeCanvasId: row ? row.getAttribute('data-canvas-row') : null,
      visibleRows: rows.length,
      allRowIds: rows.map(r=>r.getAttribute('data-canvas-row')),
      reactFlowNodes: document.querySelectorAll('.react-flow__node').length,
    });
  }, 500));
}"""

CARDS = r"""()=>Array.from(document.querySelectorAll('[data-project-card]'))
        .map(c=>({id:c.getAttribute('data-project-card'),
                  text:(c.textContent||'').trim().slice(0,24)}))"""


def same_tab_active(pg):
    """★ 本标签页的 `activeCanvasId` 有没有跟着点的那张走。

    ## 为什么这条读数要**读 store** 而不是读 DOM

    缺陷本体（新标签页开错画布）全部用 DOM 读数判定，那条是用户看得见的。
    但「本标签页**跟着**走」这条是**无回归**声明 —— `/project` 页面上根本没有
    `[data-canvas-trigger]`（那是画布页的钩子），所以 DOM 上读不到。
    ⟹ 这里改读 `window.__libtv_store`，并且**只用于这条**。

    ★ 第一版的 `sameTabAfterClick` 是在 `/project` 上找 `[data-canvas-trigger]`，
      找不到 ⟹ 恒为 `{activeCanvasId: null}` ⟹ 一条**恒定无信息**的读数，
      差点被我当成「本标签页没跟着走」写进结论。无效读数比没有读数更危险。
    """
    return pg.evaluate(
        "()=>{const s=window.__libtv_store;"
        "if(!s) return {storeFound:false};"
        "const st=s.getState();"
        "return {storeFound:true, activeCanvasId: st.activeCanvasId,"
        " canvasCount: st.canvases.length};}")


def click_card_and_read(pg, canvas_id):
    """点指定卡片，等新标签页，在新标签页里读两条 DOM 读数。"""
    pg.goto(BASE + "/project", wait_until="networkidle")
    pg.wait_for_selector("[data-project-card]", timeout=25000)
    pg.wait_for_timeout(600)
    sel = '[data-project-card="%s"]' % canvas_id
    pg.wait_for_selector(sel, timeout=10000)
    with pg.expect_popup(timeout=20000) as pop:
        pg.click(sel)
    pg.wait_for_timeout(500)
    same_tab = same_tab_active(pg)      # ★ 点击**之后**才读
    newpg = pop.value
    newpg.wait_for_load_state("networkidle")
    newpg.wait_for_selector(".react-flow", timeout=25000)
    newpg.wait_for_timeout(1800)          # 等画布与下拉面板落定
    new_read = newpg.evaluate(READ_ACTIVE)
    new_url = newpg.url
    newpg.close()
    pg.wait_for_timeout(400)
    return {"target": canvas_id, "sameTabAfterClick": same_tab,
            "newTab": new_read, "newTabUrl": new_url,
            "showsTarget": new_read["activeCanvasId"] == canvas_id,
            "sameTabFollowed": same_tab.get("activeCanvasId") == canvas_id}


def invalid_param_arm(ctx):
    """★ 直接访问 `/?canvas=<不存在的 id>`：必须**回落到默认画布**，而不是白屏/崩。

    这条不是凑数。修复引入了「从 URL 读一个 id 并切画布」这条新路径 ⟹ 它自带
    一个新失败模式：**参数坏了会怎样**。不测它，就等于把一个新风险放进代码里
    却不看它。

    还要顺带记一条读数：默认 active 到底是哪个 id —— 「回落」要有个可核对的
    目标，不能写成「回落到某个正常画布」这种没法判的话。
    """
    pg = ctx.new_page()
    try:
        pg.goto(BASE + "/?canvas=canvas-does-not-exist",
                wait_until="networkidle")
        pg.wait_for_selector(".react-flow", timeout=25000)
        pg.wait_for_timeout(1500)
        read = pg.evaluate(READ_ACTIVE)
        return {"target": "canvas-does-not-exist", "newTab": read,
                "rendered": bool(read.get("reactFlowNodes") is not None
                                 and read.get("visibleRows") is not None),
                "fellBackToSomeCanvas": read["activeCanvasId"] is not None}
    finally:
        pg.close()


def run_round(ctx, R):
    rec = {"round": R}
    pg = ctx.new_page()
    try:
        pg.goto(BASE + "/project", wait_until="networkidle")
        pg.wait_for_selector("[data-project-card]", timeout=25000)
        pg.wait_for_timeout(500)
        rec["cards"] = pg.evaluate(CARDS)

        # ★ 两个方向都跑：默认 active 是 canvas-2，所以「点 canvas-2」是
        #   **默认蒙对**，只有「点 canvas-1」才真的检验功能。
        rec["arms"] = []
        for cid in ("canvas-1", "canvas-2"):
            try:
                rec["arms"].append(click_card_and_read(pg, cid))
            except Exception as exc:
                rec["arms"].append({"target": cid,
                                    "FAILED": type(exc).__name__ + ": " + str(exc)[:200]})
        pg.close()

        try:
            rec["invalidParam"] = invalid_param_arm(ctx)
        except Exception as exc:
            rec["invalidParam"] = {
                "FAILED": type(exc).__name__ + ": " + str(exc)[:200]}
    finally:
        pass
    return rec


def main():
    out_path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    phase = sys.argv[2] if len(sys.argv) > 2 else "pre"
    rounds = []
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)          # ★ 一律 headless
        try:
            for R in range(2):
                ctx = br.new_context(viewport={"width": 1440, "height": 1000})
                try:
                    rounds.append(run_round(ctx, R))
                finally:
                    ctx.close()
        finally:
            br.close()
    out = {"batch": 804, "phase": phase, "base": BASE, "rounds": rounds}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                        encoding="utf-8")
    for r in rounds:
        for a in r["arms"]:
            if a.get("FAILED"):
                print("round %s ｜ %s ｜ FAILED %s" % (r["round"], a["target"],
                                                      a["FAILED"][:60]))
            else:
                print("round %s ｜ 点 %-9s ⟹ 新标签页显示 %-9s ｜ 节点 %d ｜ %s"
                      % (r["round"], a["target"],
                         a["newTab"]["activeCanvasId"],
                         a["newTab"]["reactFlowNodes"],
                         "★ 是你点的" if a["showsTarget"] else "★ 不是你点的"))
    print("wrote %s" % out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
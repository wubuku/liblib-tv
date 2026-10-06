#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 805 探针 a：回收站那句「30 天」，是不是真的

## 修的是什么

759 ②：回收站面板写「仅显示最近 30 天内删除的内容」、每项写「· 剩余 30 天」，
**两处都是字面量** —— 周边 160 字符内没有任何 Date/diff/减法，`removedCanvases`
只有 `.map` **没有 `.filter`**。老化实验（把 `removedAt` 改成 20 个月前）后，
「剩余 **30** 天」**一字未变**，条目照样列在面板里。

## 判据里最重要的一条：**N 不写死**

★ 「剩余 30 天」里的 30 是**界面自己写着的字**，不是我的期望值。所以判据是
**「标题里的 N」与「各项算出来的剩余」必须一致**，以及
**「把某条挪早 k 天，它显示的剩余必须恰好少 k 天」** ⟹
N 是从数据里**反推**出来的，不是预设再对一遍。

## 三格读数

  格 1 `realDelete` —— 走**真实用户路径**删一张画布（画布页下拉 → 删除画布 →
        确认框 → 确认），再经 `TopNavBar → 全部项目` **客户端**路由到 /project
        打开回收站。★ 必须走客户端路由：759 ⑤ 实测过 `removedCanvases`
        **整页加载后会丢**（客户端路由才保留），`page.goto` 造不出条目。
        这一格是**阳性对照** —— 没有它，「面板是空的」什么也证明不了。
  格 2 `aging` —— 用 `store.setState` **程序化造数**：把条目按不同天数往前挪，
        然后只读**渲染出来的文字**。造数是 fixture，判据在产物上（759 同款做法）。
  格 3 `boundary` —— 剩余 1 天 / 0 天各一条，检查边界两侧行为是否不同。
"""
import json
import pathlib
import sys

from playwright.sync_api import sync_playwright

BASE = "http://localhost:4317"
OUTDIR = pathlib.Path(
    "/Users/yangjiefeng/Documents/wubuku/liblib-tv"
    "/docs/research/liblib-canvas-batch805-2026-10-01/raw")


def ev(pg, js, arg=None):
    """跑一段 JS，失败时记下来而不是把整轮带走。

    ★ 第一版写了个 `_safe(JS_STRING)` 装饰器，把 JS **字符串**包成 Python 闭包
      再传给 `page.evaluate` ⟹ Playwright 拿到的是 Python 源码、不是合法表达式，
      报 `Object of type function is not JSON serializable`。**无效读数比没有
      读数更危险** —— 这条坑和 804 的 `sameTabAfterClick` 是同一类。
    """
    try:
        return pg.evaluate(js) if arg is None else pg.evaluate(js, arg)
    except Exception as exc:
        return {"FAILED": type(exc).__name__ + ": " + str(exc)[:220]}


# ── 读回收站面板：标题里的天数 + 每项的「剩余 N 天」+ 有没有过期项 ──────────
READ_RECYCLE = r"""()=>{
  const panel = document.querySelector('[data-recycle-panel]');
  if (!panel) return {open:false};
  const head = panel.querySelector('p');
  const headText = head ? (head.textContent||'').trim() : '';
  // ★ 标题里的天数**从文字里解析**，不写死 30
  const m = headText.match(/(\d+)\s*天/);
  const items = Array.from(panel.querySelectorAll('[data-recycle-item]')).map(li=>{
    const t = (li.textContent||'');
    const r = t.match(/剩余\s*(\d+)\s*天/);
    const d = t.match(/(\d{4}-\d{2}-\d{2})/);
    return {id: li.getAttribute('data-recycle-item'),
            shownName:(li.textContent||'').trim().slice(0,20),
            shownRemaining: r ? Number(r[1]) : null,
            shownDate: d ? d[1] : null};
  });
  return {open:true, headText,
          titleDays: m ? Number(m[1]) : null,
          empty: !!panel.querySelector('[data-recycle-empty]'),
          items};
}"""

# ★ 幂等：面板已经开着就**别点**。原来是无脑 click ⟹ 第二次调用把开着的面板
#   toggle 关了 ⟹ 后续读数拿到 `{open:false}`、连 headText 都没有。
#   ★ 教训和 804/805 前两次一样：**读数失败先怀疑自己的动作**，别急着判功能坏。
OPEN_RECYCLE = """()=>{
  if(document.querySelector('[data-recycle-panel]')) return {ok:true, alreadyOpen:true};
  const b=document.querySelector('[data-sidebar-recycle]')
  || Array.from(document.querySelectorAll('button')).find(x=>/回收站/.test(x.textContent||''));
  if(!b) return {ok:false};
  b.click(); return {ok:true, alreadyOpen:false};}"""

# ★ 第一版点完触发器**立刻**去查行，拿到 `rows: 0` —— React 是异步渲染的。
#   诊断（/tmp/diag805.py）逐步打印才发现：点开下拉后行确实存在（第二步读到 2），
#   导航其实也成功了（URL 已到 /project）⟹ 两处都是**等得不够久**，不是功能坏。
#   所以下面每一步之后都由 Python `wait_for_selector` 等元素真的出现。
DELETE_VIA_UI = r"""()=>{
  const trig = document.querySelector('[data-canvas-trigger]');
  if(!trig) return {ok:false, why:'no canvas trigger'};
  trig.click();
  return {ok:true, stage:'trigger clicked'};
}"""
PICK_ROW = r"""()=>{
  const row = document.querySelector('[data-canvas-row]');
  if(!row) return {ok:false, why:'no canvas row'};
  const id = row.getAttribute('data-canvas-row');
  const more = row.querySelector('[data-canvas-row-more]');
  if(!more) return {ok:false, why:'no more button', id};
  more.click();
  return {ok:true, deletedCandidate:id};
}"""
PICK_REMOVE_ITEM = r"""()=>{
  const el = document.querySelector('[data-canvas-row-menu-item="delete"]');
  if(!el) return {ok:false, why:'no delete item'};
  el.click();
  return {ok:true};
}"""
# ★★ 确认框的两个按钮文案是「取消」/「确认」（759 记过 取消 50×30 / 确认 48×30）。
#   第一版按 `/删除/` 去找 —— 一个都没��中 ⟹ 「确认」从没被点过 ⟹ 画布根本没被删
#   ⟹ 回收站当然是空的。★ 我差点把「回收站是空的」当成「功能坏」的证据，
#   实际是**我自己的手没按下去**。按文案找之前，先把实际文案打出来。
CONFIRM_DELETE = r"""()=>{
  const box = document.querySelector('[data-canvas-delete-confirm]');
  if(!box) return {ok:false, why:'no confirm box'};
  const btns = Array.from(box.querySelectorAll('button'));
  const labels = btns.map(b=>(b.textContent||'').trim());
  const del = btns.find(b=>/^确认$/.test((b.textContent||'').trim()))
            || btns.find(b=>!/取消/.test(b.textContent||''));
  if(!del) return {ok:false, why:'no confirm button', labels};
  del.click();
  return {ok:true, clicked:(del.textContent||'').trim(), labels};
}"""
# ★ 「全部项目」在 **logo 下拉**里（TopNavBar 的 `items`，batch 106），
#   不先开下拉就找不到它 —— 第一版直接找那个文字，25 秒超时。
OPEN_PROJECT_MENU = """()=>{
  const trig = document.querySelector('[data-project-menu-trigger]');
  if(!trig) return {ok:false, why:'no project menu trigger'};
  trig.click();
  return {ok:true};
}"""
GOTO_PROJECT = """()=>{
  const a = document.querySelector('[data-project-menu-item="全部项目"]');
  if(!a) return {ok:false, why:'no 全部项目 item'};
  a.click();
  return {ok:true};
}"""

# 用 store.setState 造「不同删除天数」的条目。★ 造数是 fixture，判据在渲染产物上。
SEED_AGES = r"""(spec)=>{
  const s = window.__libtv_store;
  if(!s) return {ok:false, why:'no store'};
  const st = s.getState();
  const base = st.canvases[0] || {id:'x', name:'x', nodes:[], edges:[]};
  const today = new Date().toISOString().slice(0,10);
  const shift = (iso, days) =>
    new Date(Date.parse(iso + 'T00:00:00Z') + days*86400000)
      .toISOString().slice(0,10);
  const made = spec.map((age,i)=>({...base,
      id:'aged-'+i, name:'老化样本'+i+'(提前'+age+'天)',
      nodes:[], edges:[], removedAt: shift(today, -age)}));
  s.setState({removedCanvases: made});
  return {ok:true, made: made.map(m=>({id:m.id, removedAt:m.removedAt})),
          today};
}"""


def run_round(ctx, R):
    rec = {"round": R}
    pg = ctx.new_page()
    try:
        # ── 格 1：真实用户路径删一张 ⟹ 客户端路由到 /project ⟹ 打开回收站
        pg.goto(BASE, wait_until="networkidle")
        pg.wait_for_selector("[data-canvas-trigger]", timeout=25000)
        pg.wait_for_timeout(1200)
        opened = ev(pg, DELETE_VIA_UI)
        # ★ 每一步都等元素真的出现，而不是 sleep 一个拍脑袋的毫秒数
        pg.wait_for_selector("[data-canvas-row]", timeout=10000)
        opened["pickRow"] = ev(pg, PICK_ROW)
        pg.wait_for_selector('[data-canvas-row-menu-item="delete"]',
                             timeout=10000)
        opened["pickRemoveItem"] = ev(pg, PICK_REMOVE_ITEM)
        pg.wait_for_selector("[data-canvas-delete-confirm]", timeout=10000)
        pg.wait_for_timeout(400)
        confirmed = ev(pg, CONFIRM_DELETE)
        pg.wait_for_timeout(900)
        opened["openProjectMenu"] = ev(pg, OPEN_PROJECT_MENU)
        pg.wait_for_selector("[data-project-menu-item]", timeout=10000)
        goto = ev(pg, GOTO_PROJECT)
        pg.wait_for_selector("[data-project-list-page]", timeout=25000)
        pg.wait_for_timeout(900)
        ev(pg, OPEN_RECYCLE)
        pg.wait_for_timeout(700)
        rec["realDelete"] = {"deleteFlow": opened, "confirm": confirmed,
                             "gotoProject": goto,
                             "recycle": pg.evaluate(READ_RECYCLE)}

        # ── 格 2：造 0 / 1 / 7 / 29 天的样本，只读渲染文字
        ages = [0, 1, 7, 29]
        ev(pg, OPEN_RECYCLE)          # 确保面板已开
        pg.wait_for_timeout(300)
        seeded = pg.evaluate(SEED_AGES, ages)
        pg.wait_for_timeout(700)
        rec["aging"] = {"ages": ages, "seed": seeded,
                        "recycle": pg.evaluate(READ_RECYCLE)}

        # ── 格 3：边界 —— 提前 30 天（应过期）与 29 天（应在）分开放
        seed_b = ev(pg, SEED_AGES, [29, 30])
        pg.wait_for_timeout(700)
        rec["boundary"] = {"ages": [29, 30], "seed": seed_b,
                           "recycle": pg.evaluate(READ_RECYCLE)}
    finally:
        pg.close()
    return rec


def main():
    out_path = pathlib.Path(sys.argv[1])
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
    out = {"batch": 805, "phase": phase, "base": BASE, "rounds": rounds}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                        encoding="utf-8")
    for r in rounds:
        for cell in ("realDelete", "aging", "boundary"):
            c = r.get(cell, {})
            rc = c.get("recycle") or {}
            if rc.get("FAILED"):
                print("round %s ｜ %-10s FAILED %s" % (r["round"], cell,
                                                       rc["FAILED"][:50]))
                continue
            items = [(i["shownDate"], i["shownRemaining"])
                     for i in rc.get("items", [])]
            print("round %s ｜ %-10s ｜ 标题「%s」｜ 空=%s ｜ 项=%s"
                  % (r["round"], cell, rc.get("headText"),
                     rc.get("empty"), items))
    print("wrote %s" % out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
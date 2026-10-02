#!/usr/bin/env python3
"""batch 895 复刻探针：量**复刻侧**同一张 `tabindex` 条件矩阵（判据逐字复用 894）。

## 为什么要这张表

894（源站）查明：**中性状态下源站所有类型的节点都 `tabIndexProp=-1`**
（不可 Tab 到达）；而 894 同时指出，复刻用 `@xyflow/react`、节点 wrapper
**默认** `tabindex=0`（`nodesFocusable` 默认 true）⇒ 复刻节点**任何时候**可
Tab 到达。

⚠️ 但那句「复刻节点任何时候 `tabindex=0`」**本身还没测过** —— 它是从库默认
值**推**出来的，不是量出来的。**从库默认值推出产品行为，和从读数归纳成机制
是同一类错。**这批去量。

## 判据必须**逐字复用** 894

否则量出「不同」可能只是**两边各量各的**（890c 栽过一次，已记在基线里）。
条件、顺序、摘要口径（按 `kind|selected` 压成可机读摘要、**不钉节点数**）
全部照搬。

## 差异

- 复刻 demo 画布**自带**若干节点，不需要插入
- 仍要跑 `after_insert`（复刻的「音频」入口会插一个音频节点），
  才能与 894 的对应条件逐项对齐
- `after_blank` 的空白点：优先用 894 同一组候选坐标，**落空时**回落到
  pane 矩形角（**记录用的是哪一种** —— 坐标不同是**次要变量**，
  但必须**可追溯**，不许悄悄换）

## 纪律

- 每种条件**2 次**；每轮**从刚载完**开始
- 每个条件**先验前置态**
- **只读 DOM，不劫持任何东西**
- 落点**量出来**再点

跑法：`/opt/miniconda3/bin/python3 scripts/jimeng_probe895_node_tabindex_matrix_ck.py`
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://localhost:4317/jimeng/canvas/demo"
OUT = Path("/tmp/b895-ck-tabindex-matrix.json")
REPS = 2

# ⚠️⚠️ 以下四段 JS **逐字来自 894 源站探针**，不许在这里「顺手优化」——
# 判据不同就量出了「不同」，而那只是判据不同（890c 的教训）。
TOOLBAR_JS = """() => !!document.querySelector('button[aria-label^="音色"]')"""
BLANK_JS = """() => {
  for (const [x, y] of [[1300, 1000], [1360, 920], [1220, 1080],
                        [1400, 840], [400, 1080]]) {
    const t = document.elementFromPoint(x, y);
    if (t && t.closest('.react-flow__pane')
        && !t.closest('.react-flow__node')) return [x, y];
  }
  return null;
}"""
NODES_JS = """() => [...document.querySelectorAll('.react-flow__node')].map(n => ({
  testid: n.getAttribute('data-testid') || '',
  kind: [...n.classList].find(c => c.startsWith('react-flow__node-')
        && c !== 'react-flow__node') || '?',
  selected: n.classList.contains('selected'),
  tabindex: n.getAttribute('tabindex'),
  tabIndexProp: n.tabIndex,
  aria: n.getAttribute('aria-label') || '',
}))"""
FOCUS_JS = """() => { const a = document.activeElement;
  if (!a || a === document.body) return {tag: 'BODY', aria: '(body)'};
  const n = a.closest && a.closest('.react-flow__node');
  return {tag: a.tagName,
          aria: a.getAttribute('aria-label') || '',
          in_node: !!n,
          node_testid: n ? (n.getAttribute('data-testid') || '') : null,
          node_tabindex: n ? n.getAttribute('tabindex') : null,
          node_tabIndexProp: n ? n.tabIndex : null}; }"""


def summarize(nodes: list[dict]) -> dict:
    """与 894 **同款**摘要：不钉节点数（逐轮会变），只钉「哪类节点、各自
    tabindex 是什么」。"""
    by_kind: dict = {}
    for n in nodes:
        k = (n["kind"], n["selected"])
        by_kind.setdefault(k, {"n": 0, "tabindex": set(), "prop": set()})
        by_kind[k]["n"] += 1
        by_kind[k]["tabindex"].add(n["tabindex"])
        by_kind[k]["prop"].add(n["tabIndexProp"])
    return {f"{k[0]}|selected={k[1]}": {
        "n": v["n"],
        "tabindex": sorted(str(x) for x in v["tabindex"]),
        "tabIndexProp": sorted(v["prop"]),
    } for k, v in sorted(by_kind.items())}


def main() -> int:
    url = os.environ.get("SNAP_URL", URL)
    res: dict = {"url": url, "runs": []}
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_context(viewport={"width": 1680, "height": 1050}).new_page()
        for rep in range(1, REPS + 1):
            pg.goto(url, wait_until="domcontentloaded", timeout=60000)
            time.sleep(4.0)
            rec: dict = {"rep": rep, "conds": {}}

            def ev(js, arg=None):
                return pg.evaluate(js) if arg is None else pg.evaluate(js, arg)

            def snap(name, note=""):
                nodes = ev(NODES_JS)
                rec["conds"][name] = {"note": note, "summary": summarize(nodes),
                                      "focus": ev(FOCUS_JS),
                                      "toolbar": ev(TOOLBAR_JS)}
                print(f"\n  [{name}]{(' ' + note) if note else ''}")
                for k, v in rec["conds"][name]["summary"].items():
                    print(f"     {k:42s} n={v['n']:<3d} "
                          f"tabindex={v['tabindex']} prop={v['tabIndexProp']}")
                return rec["conds"][name]

            snap("fresh_load", "刚载完，什么都不做")

            spot = ev(BLANK_JS)
            spot_from = "list"
            if not spot:
                # 894 同一组候选坐标落空 ⇒ 回落到 pane 矩形角，**并记录**
                fb = ev("""() => {
                  const p = document.querySelector('.react-flow__pane');
                  if (!p) return null;
                  const r = p.getBoundingClientRect();
                  const x = Math.round(r.x + r.width - 30);
                  const y = Math.round(r.y + r.height - 30);
                  const t = document.elementFromPoint(x, y);
                  if (t && t.closest('.react-flow__pane')
                      && !t.closest('.react-flow__node')) return [x, y];
                  return null; }""")
                spot, spot_from = fb, "pane_rect"
            if spot:
                pg.mouse.click(spot[0], spot[1])
                time.sleep(1.2)
            c = snap("after_blank", f"点了空白 {spot}（{spot_from}）；"
                                    f"工具条在={ev(TOOLBAR_JS)}")
            c["blank_spot"] = spot
            c["blank_from"] = spot_from

            tabwalk = []
            for _ in range(16):
                pg.keyboard.press("Tab")
                # ⚠️⚠️ **单位**：Playwright 的 `wait_for_timeout` 收**毫秒**，
                # Python 的 `time.sleep` 收**秒**。第一版这里照搬 894 的
                # `wait_for_timeout(140)` 写成 `time.sleep(140)`
                # ⇒ 一次循环睡 **140 秒**、16 次 ≈ **37 分钟**，
                # 看起来像「页面按 Tab 卡死」（进程 0% CPU 一直睡）。
                # ⇒ **判据平移必须连单位一起平移。**
                time.sleep(0.14)
                tabwalk.append(ev(FOCUS_JS))
            rec["conds"]["after_tab"] = {
                "note": "点空白后连按 Tab 16 次（逐次记落点与那一刻的 tabindex）",
                "walk": tabwalk}
            print("\n  [after_tab] 逐次落点：")
            for i, f in enumerate(tabwalk, 1):
                print(f"     Tab{i:<2d} {f['aria']!r:26s} 在节点内={f['in_node']} "
                      f"该节点 tabindex={f['node_tabindex']!r} "
                      f"prop={f['node_tabIndexProp']}")
            snap("after_tab_final", "Tab 走完之后再看一眼全画布")

            before = set(ev("() => [...document.querySelectorAll('.react-flow__node')]"
                            ".map(n => n.getAttribute('data-testid')||'')"))
            loc = pg.locator('button[aria-label="音频"]')
            rec["insert_ok"] = bool(loc.count())
            if rec["insert_ok"]:
                loc.first.click(timeout=8000)
                time.sleep(2.0)
            after = ev("() => [...document.querySelectorAll('.react-flow__node')]"
                       ".map(n => n.getAttribute('data-testid')||'')")
            new = [t for t in after if t and t not in before]
            rec["new_node_testid"] = new[0] if new else None
            snap("after_insert", f"插入了 {rec['new_node_testid']}")

            spot2 = ev(BLANK_JS)
            if not spot2:
                fb = ev("""() => {
                  const p = document.querySelector('.react-flow__pane');
                  if (!p) return null;
                  const r = p.getBoundingClientRect();
                  const x = Math.round(r.x + r.width - 30);
                  const y = Math.round(r.y + r.height - 30);
                  const t = document.elementFromPoint(x, y);
                  if (t && t.closest('.react-flow__pane')
                      && !t.closest('.react-flow__node')) return [x, y];
                  return null; }""")
                spot2 = fb
            if spot2:
                pg.mouse.click(spot2[0], spot2[1])
                time.sleep(1.2)
            c = snap("after_insert_blank", f"插入后点空白 {spot2}")
            if rec["new_node_testid"]:
                one = ev("""(tid) => { const n = document.querySelector(
                    `.react-flow__node[data-testid="${tid}"]`);
                  if (!n) return {gone: true};
                  return {selected: n.classList.contains('selected'),
                          tabindex: n.getAttribute('tabindex'),
                          tabIndexProp: n.tabIndex}; }""",
                        rec["new_node_testid"])
                c["new_node_only"] = one
                print(f"     ⭐ 只看新节点：{one}")

            if rec["new_node_testid"]:
                xy = ev("""(tid) => { const n = document.querySelector(
                    `.react-flow__node[data-testid="${tid}"]`);
                  if (!n) return null; const r = n.getBoundingClientRect();
                  return [Math.round(r.x + r.width/2), Math.round(r.y + r.height/2)]; }""",
                        rec["new_node_testid"])
                if xy:
                    pg.mouse.click(xy[0], xy[1])
                    time.sleep(1.5)
                    one = ev("""(tid) => { const n = document.querySelector(
                        `.react-flow__node[data-testid="${tid}"]`);
                      if (!n) return {gone: true};
                      return {selected: n.classList.contains('selected'),
                              tabindex: n.getAttribute('tabindex'),
                              tabIndexProp: n.tabIndex}; }""",
                            rec["new_node_testid"])
                    rec["conds"]["after_select"] = {
                        "note": "点新节点把它选中之后",
                        "new_node_only": one, "focus": ev(FOCUS_JS),
                        "toolbar": ev(TOOLBAR_JS)}
                    print(f"\n  [after_select] ⭐ 新节点：{one}  "
                          f"工具条={ev(TOOLBAR_JS)}")
            else:
                rec["conds"]["after_select"] = {
                    "verdict": "前置态没成立：这一轮插不进新节点 ⇒ 本条件不测"}
                print("\n  [after_select] !! 前置态没成立（插不进新节点）")
            res["runs"].append(rec)

        summ = {}
        for name in ("after_insert_blank", "after_select"):
            vals = []
            for r in res["runs"]:
                o = (r["conds"].get(name) or {}).get("new_node_only")
                if o:
                    vals.append({"tabindex": o.get("tabindex"),
                                 "prop": o.get("tabIndexProp"),
                                 "selected": o.get("selected")})
            summ[name] = vals
        for name in ("fresh_load", "after_blank", "after_tab_final"):
            summ[name] = [(r["conds"].get(name) or {}).get("summary")
                          for r in res["runs"]]
        res["summary"] = summ
        print("\n== 汇总（复刻侧）==")
        print("  新节点自己的 tabindex：")
        for name in ("after_insert_blank", "after_select"):
            print(f"    {name:20s} {summ[name]}")
        print("\n  全画布摘要（`kind|selected` → tabindex）：")
        for name in ("fresh_load", "after_blank", "after_tab_final"):
            print(f"    {name}:")
            for s in summ[name]:
                if not s:
                    print("       (无)")
                    continue
                for k, v in s.items():
                    print(f"       {k:42s} n={v['n']:<3d} "
                          f"tabindex={v['tabindex']} prop={v['tabIndexProp']}")
        b.close()

    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print(f"\n== 已写 {OUT} ==")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""batch 897 复刻探针：补齐**复刻侧**的类型覆盖（896/895 留下的最后一个缺口）。

## 为什么还有这一批

895 的结论只能说到「**在 demo 画布实测到的类型上**恒为 `'0'`」——复刻 demo
画布**只有** video（n=2）**加**探针插入的 1 个 audio。而源站矩阵里还有
text / timeline / image / external。⇒ 「要不要改复刻 `nodesFocusable`」这个
决定，**还差**复刻侧其余类型的读数。

## 判据必须**逐字复用 896**

896 已经在源站把策略测完了，896 的 `STATE_JS` 里有 894 漏掉的那个关键量
——**直方图**（`tabindex` 值 → **各有几个**）。搬过来，不许在这里「顺手优化」：
判据不同就量出了「不同」，而那只是判据不同（890c 的教训，基线里记着）。

## 这一批量什么

对**每一种能插的类型**取三个读数：

| 读数 | 怎么建立 | 问的是什么 |
|---|---|---|
| `after_insert` | 点左栏那个类型的入口 | 插进去、**自带选中**时，它是不是 `'0'` |
| `after_blank` | 插完点画布空白 | 落选/失焦之后呢 |
| `after_focus` | **点它本体**（= 893 的 B 序列） | 焦点落在它身上那一刻呢 |

外加一整轮 **Tab 走查**，看复刻侧有没有任何 roving 迹象
（`n_zero` 是不是恒等于节点总数）。

## 插哪些类型

复刻左栏（`JimengToolRail.tsx`）的按钮 `aria-label` 就是类型名：
`文本` / `图片` / `视频` / `音频` / `时间线` / `主体` / `导演台`。
**视频/音频不重插**——demo 画布自带 video，895 也插过 audio。

⚠️ 记一笔**两侧类型集不对称**（不是 bug，是记账）：
- 复刻有 `subject`（主体），**源站 894 矩阵里没有**这一类
- 复刻的 `director`（导演台）对应源站的 `external`（894 的
  `react-flow__node-external` / aria `外部 node: 导演台`）

## 纪律

- 每轮**重复 2 次**（一次成功不叫可靠）；每轮**从刚载完**开始
- **只读 DOM，不挂任何监听器、不劫持任何东西**（896 的仪器这批**不需要**：
  复刻侧没有 MutationObserver 要查，896 已经证明源站那边是 keydown 驱动的）
- 钉**关系**（`n_zero`、某个节点自己的 `tabindex`），
  **不钉**节点总数、不钉节点序号
- 落点**量出来**再点

## 计费边界

只点左栏**插入**入口、点画布空白、点节点本体、按 Tab。
**绝不**点生成/发送/购买/充值，**也绝不**点音色 chip 本身。

跑法：
  /opt/miniconda3/bin/python3 -u scripts/jimeng_probe897_ck_type_coverage.py
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://localhost:4317/jimeng/canvas/demo"
OUT = Path("/tmp/b897-ck-type-coverage.json")
REPS = 2

# 要插的类型（左栏 aria-label → 复刻内部 kind）。
# ⚠️ 视频/音频**不插**：demo 自带 video，895 已插过 audio。
KINDS = [
    ("文本", "text"),
    ("图片", "image"),
    ("时间线", "timeline"),
    ("主体", "subject"),
    ("导演台", "director"),
]

# ⚠️⚠️ 下面这段 **逐字来自 896 源站探针** 的 STATE_JS，不许「顺手优化」——
# 896 的判据里有 894 漏掉的**直方图**（`tabindex` 值 → 各有几个），
# 那个量恰恰是区分 roving 的唯一判据。
STATE_JS = """() => {
  const nodes = [...document.querySelectorAll('.react-flow__node')];
  const hist = {};            // tabindex 值 → **有几个**
  const zeros = [];           // 所有 tabindex='0' 的节点身份
  for (const n of nodes) {
    const ti = n.getAttribute('tabindex');
    const k = ti === null ? 'None' : ti;
    hist[k] = (hist[k] || 0) + 1;
    if (ti === '0') zeros.push(n.getAttribute('data-testid') || '(no-testid)');
  }
  // 焦点链：**每一层**的 tabindex（0 到底挂在哪一层上？）
  const chain = [];
  let a = document.activeElement;
  for (let i = 0; a && i < 12; i++) {
    chain.push({tag: a.tagName,
                ti: a.getAttribute ? a.getAttribute('tabindex') : null,
                prop: a.tabIndex,
                aria: (a.getAttribute && a.getAttribute('aria-label')) || '',
                tid: (a.getAttribute && a.getAttribute('data-testid')) || null,
                is_node: !!(a.closest && a.closest('.react-flow__node'))});
    a = a.parentElement;
  }
  const an = document.activeElement
    && document.activeElement.closest
    && document.activeElement.closest('.react-flow__node');
  return {
    n_nodes: nodes.length,
    hist,                                   // ← **这就是 894 丢掉的计数**
    zeros,                                  // ← 谁身上有 0
    n_zero: zeros.length,
    active: {
      aria: (document.activeElement
             && document.activeElement.getAttribute
             && document.activeElement.getAttribute('aria-label')) || '',
      tid: an ? an.getAttribute('data-testid') : null,
      node_ti: an ? an.getAttribute('tabindex') : null,
      self_ti: (document.activeElement
                && document.activeElement.getAttribute)
               ? document.activeElement.getAttribute('tabindex') : null,
    },
    chain,
  };
}"""

# 某个节点自己的读数（按 testid 钉身份，**不钉序号**）
ONE_JS = """(tid) => {
  const n = document.querySelector(`.react-flow__node[data-testid="${tid}"]`);
  if (!n) return {gone: true};
  const ti = n.getAttribute('tabindex');
  return {kind: [...n.classList].find(c => c.startsWith('react-flow__node-')
          && c !== 'react-flow__node') || '?',
          selected: n.classList.contains('selected'),
          tabindex: ti,
          tabIndexProp: n.tabIndex,
          aria: n.getAttribute('aria-label') || '',
          is_active: document.activeElement
            && !!document.activeElement.closest
            && document.activeElement.closest('.react-flow__node') === n};
}"""

BLANK_JS = """() => {
  for (const [x, y] of [[1300, 1000], [1360, 920], [1220, 1080],
                        [1400, 840], [400, 1080]]) {
    const t = document.elementFromPoint(x, y);
    if (t && t.closest('.react-flow__pane')
        && !t.closest('.react-flow__node')) return [x, y];
  }
  const p = document.querySelector('.react-flow__pane');
  if (!p) return null;
  const r = p.getBoundingClientRect();
  const x = Math.round(r.x + r.width - 30), y = Math.round(r.y + r.height - 30);
  const t = document.elementFromPoint(x, y);
  if (t && t.closest('.react-flow__pane') && !t.closest('.react-flow__node'))
    return [x, y];
  return null;
}"""

TIDS_JS = """() => [...document.querySelectorAll('.react-flow__node')]
  .map(n => n.getAttribute('data-testid') || '')"""

CENTER_JS = """(tid) => {
  const n = document.querySelector(`.react-flow__node[data-testid="${tid}"]`);
  if (!n) return null;
  const r = n.getBoundingClientRect();
  return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
}"""


def derive(s: dict) -> dict:
    """把读数压成**关系**（不钉节点数/序号）。"""
    act = s.get("active") or {}
    return {
        "n_nodes": s.get("n_nodes"),
        "hist": s.get("hist"),
        "n_zero": s.get("n_zero"),
        # 复刻若是「每个节点都 0」，则 n_zero **恒等于** n_nodes
        "all_nodes_zero": s.get("n_zero") == s.get("n_nodes"),
        "zeros": s.get("zeros"),
        "active_aria": act.get("aria"),
        "active_tid": act.get("tid"),
        "active_node_ti": act.get("node_ti"),
        "chain_ti": [c["ti"] for c in (s.get("chain") or [])][:6],
    }


def main() -> int:
    url = os.environ.get("SNAP_URL", URL)
    res: dict = {"url": url, "runs": []}
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_context(viewport={"width": 1680, "height": 1050}).new_page()
        for rep in range(1, REPS + 1):
            pg.goto(url, wait_until="domcontentloaded", timeout=60000)
            time.sleep(4.0)
            rec: dict = {"rep": rep, "steps": [], "kinds": {}}

            def ev(js, arg=None):
                return pg.evaluate(js) if arg is None else pg.evaluate(js, arg)

            def read(cond, note=""):
                s = ev(STATE_JS)
                d = {"cond": cond, "note": note, "derive": derive(s)}
                rec["steps"].append(d)
                print(f"  [{cond}] {' ' + note if note else ''}")
                print(f"     n_nodes={d['derive']['n_nodes']} "
                      f"hist={d['derive']['hist']} n_zero={d['derive']['n_zero']} "
                      f"全节点都是0？{d['derive']['all_nodes_zero']}")
                return d

            print(f"\n===== rep {rep} =====")
            read("fresh_load", "刚载完，什么都不做")

            # 逐类型插入
            for label, kind in KINDS:
                before = set(ev(TIDS_JS))
                loc = pg.locator(f'button[aria-label="{label}"]')
                ok = bool(loc.count())
                if ok:
                    loc.first.click(timeout=8000)
                    time.sleep(1.6)
                after = set(ev(TIDS_JS))
                new = [t for t in after if t and t not in before]
                tid = new[0] if new else None
                one = ev(ONE_JS, tid) if tid else None
                d = read(f"after_insert_{kind}",
                         f"点了左栏「{label}」⇒ 新节点 {tid}")
                rec["kinds"][kind] = {
                    "label": label, "insert_ok": ok, "tid": tid,
                    "after_insert": one,
                    "hist": d["derive"]["hist"],
                    "n_zero": d["derive"]["n_zero"],
                    "all_nodes_zero": d["derive"]["all_nodes_zero"],
                }
                print(f"     ⭐ {kind}: {one}")

            # 插完点空白：落选/失焦之后
            spot = ev(BLANK_JS)
            if spot:
                pg.mouse.click(spot[0], spot[1])
                time.sleep(1.2)
            read("after_all_blank", f"全部插完后点空白 {spot}")
            rec["blank_spot"] = spot
            for kind, k in rec["kinds"].items():
                if k["tid"]:
                    k["after_blank"] = ev(ONE_JS, k["tid"])
                    print(f"     ⭐ {kind} 点空白后: {k['after_blank']}")

            # 点每个新节点本体（= 893 的 B 序列）：焦点落在它身上那一刻
            for kind, k in rec["kinds"].items():
                if not k["tid"]:
                    continue
                xy = ev(CENTER_JS, k["tid"])
                if not xy:
                    k["after_focus"] = {"gone": True}
                    continue
                # ⚠️ 落点**量出来**再点；点之前先确认那个点上确实是这个节点
                hit = ev("""([x, y, tid]) => {
                  const t = document.elementFromPoint(x, y);
                  const n = t && t.closest && t.closest('.react-flow__node');
                  return n ? (n.getAttribute('data-testid') || '') : null;
                }""", [xy[0], xy[1], k["tid"]])
                if hit != k["tid"]:
                    k["after_focus"] = {"skip": "落点不是本节点",
                                        "hit": hit, "want": k["tid"]}
                    print(f"     ⭐ {kind} 跳过：落点不是本节点 {hit} != {k['tid']}")
                    continue
                pg.mouse.click(xy[0], xy[1])
                time.sleep(1.2)
                k["after_focus"] = ev(ONE_JS, k["tid"])
                print(f"     ⭐ {kind} 点本体后: {k['after_focus']}")
            read("after_focus_all", "逐个点完本体之后")

            # 整轮 Tab 走查：复刻侧有没有任何 roving 迹象
            walk = []
            for i in range(1, 17):
                pg.keyboard.press("Tab")
                time.sleep(0.25)          # ← **秒**（895 踩过毫秒/秒的坑）
                s = ev(STATE_JS)
                d = derive(s)
                walk.append({"i": i, "active_aria": d["active_aria"],
                             "active_tid": d["active_tid"],
                             "active_node_ti": d["active_node_ti"],
                             "n_zero": d["n_zero"],
                             "all_nodes_zero": d["all_nodes_zero"],
                             "hist": d["hist"]})
                print(f"     Tab{i:<2d} {str(d['active_aria'])[:26]:26s} "
                      f"node_ti={d['active_node_ti']!r} n_zero={d['n_zero']} "
                      f"全节点都是0？{d['all_nodes_zero']}")
            rec["tab_walk"] = walk

            res["runs"].append(rec)

        b.close()

    # ── 汇总：按类型收口（钉「这个类型的节点自己是什么」，
    #    **不钉**节点总数/序号）──
    summ: dict = {}
    for kind in (k for _, k in KINDS):
        rows = []
        for r in res["runs"]:
            kk = r["kinds"].get(kind) or {}
            rows.append({
                "insert_ok": kk.get("insert_ok"),
                "after_insert": (kk.get("after_insert") or {}).get("tabindex"),
                "after_blank": (kk.get("after_blank") or {}).get("tabindex"),
                "after_focus": (kk.get("after_focus") or {}).get("tabindex"),
                "is_active_after_focus":
                    (kk.get("after_focus") or {}).get("is_active"),
                "all_nodes_zero": kk.get("all_nodes_zero"),
            })
        summ[kind] = rows
    res["summary"] = summ
    res["all_nodes_zero_everywhere"] = [
        all(r["all_nodes_zero"] for r in v) for v in summ.values()]
    res["tab_walk_all_zero"] = [
        all(w["all_nodes_zero"] for w in r["tab_walk"]) for r in res["runs"]]

    print("\n== 汇总（按类型；**不钉**节点总数/序号）==")
    for kind, rows in summ.items():
        print(f"  {kind}:")
        for row in rows:
            print(f"     插入后={row['after_insert']!r} 点空白后={row['after_blank']!r} "
                  f"点本体后={row['after_focus']!r} "
                  f"点完是带焦点那个？{row['is_active_after_focus']} "
                  f"全节点都是0？{row['all_nodes_zero']}")
    print(f"\n  每个类型两轮都「全节点都是 0」：{res['all_nodes_zero_everywhere']}")
    print(f"  整轮 Tab 走查全程「全节点都是 0」：{res['tab_walk_all_zero']}")
    res["verdict"] = "sampled"

    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print(f"\n== 已写 {OUT} ==")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

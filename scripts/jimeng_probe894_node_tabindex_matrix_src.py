#!/usr/bin/env python3
"""batch 894 源站探针：源站节点的 `tabindex` 到底**在什么条件下**是 `0`？

## 893 撞出来的那个不一致（本批要查的就是它）

| 读数 | 值 |
|---|---|
| 893 A 序列：点空白之后，那个**刚创建的音频**节点 | `tabindex=None` / `tabIndexProp=-1` |
| 889d 的 Tab 走查：**点空白之后**，页面自带节点（视频/文本/时间线/音频…） | **全都是** `tabindex='0'`，且**能被 Tab 到** |

⇒ 两者不一致。候选原因（**都还没测**）：
① **节点类型**（音频 vs 别的）
② **是否刚被创建**（刚插入 vs 页面自带）
③ **那套 Tab 走查里节点其实被选中了**（Tab 到某个节点常常会选中它）
④ 「不可聚焦」只发生在**某个特定状态组合**（例如：未选中 **且** 面板刚被收掉）

## 这批量一张矩阵

**条件**（每种都单独建立、单独读）：

| 代号 | 条件 | 怎么建立 |
|---|---|---|
| `fresh_load` | 刚载完，**什么都不做** | 页面加载后直接读 |
| `after_blank` | 点画布空白（全不选中） | 点一个 `elementFromPoint` 验过的空白点 |
| `after_tab` | 点空白后**连按 Tab** 若干次 | 记录每次落点与**那一刻**的 tabindex |
| `after_insert` | **新插入一个音频节点**后 | 点「音频」入口（不点节点） |
| `after_insert_blank` | 插入后**再点空白** | |
| `after_select` | 点某个节点**选中**它 | 记录选中前后该节点的 tabindex |

**每个条件都读全画布所有节点**的：`data-testid` / 有没有 `selected` class /
`tabindex` 属性 / `tabIndexProp` / `aria-label`。

## 纪律

- 每种条件**2 次**（一次成功不叫可靠）
- 每个条件都**先验证前置态**（如 `after_blank` 要验「工具条不在」）
- 落点**量出来**再点；点空白那个点必须 `elementFromPoint` 验过是 pane
- **只读 DOM，不劫持任何东西**（这一批不需要诊断动作，也就不该有留痕风险）
- ⚠️ 钉**条件与身份**，不许钉节点序号（逐轮插节点，序号是易变量）

## 计费边界

只点「音频」入口、点画布空白、点节点本体、按 Tab。
**绝不**点生成/发送/购买/充值，**也绝不**点音色 chip 本身。

跑法：
  ~/.venvs/liblib-harness/bin/python scripts/jimeng_headless.py run \
      scripts/jimeng_probe894_node_tabindex_matrix_src.py
"""

import json

OUT = "/tmp/b894-src-tabindex-matrix.json"
REPS = 2

TOOLBAR_JS = """() => !!document.querySelector('button[aria-label^="音色"]')"""
VOICES_JS = """() => [...document.querySelectorAll('*')].some(e =>
  (e.innerText||'').trim() === '全音色' && !e.querySelector('*'))"""

BLANK_JS = """() => {
  for (const [x, y] of [[1300, 1000], [1360, 920], [1220, 1080],
                        [1400, 840], [400, 1080]]) {
    const t = document.elementFromPoint(x, y);
    if (t && t.closest('.react-flow__pane')
        && !t.closest('.react-flow__node')) return [x, y];
  }
  return null;
}"""

# 全画布节点的可聚焦性快照
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


def ev(js, arg=None):
    return page.evaluate(js) if arg is None else page.evaluate(js, arg)


def summarize(nodes):
    """把一张快照压成**可机读**的摘要：不钉节点数（逐轮会变），
    只钉「有几类节点、各自的 tabindex 是什么」。"""
    by_kind = {}
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


URL = ("https://jimeng.jianying.com/ai-tool/ai-canvas/"
       "64b58cd5-7b04-4312-890a-09f2d1d3399f"
       "?enter_from=project_list&from_page=create")

out = {}
page.goto(URL, wait_until="domcontentloaded", timeout=90000)
page.wait_for_timeout(10000)
page.set_viewport_size({"width": 1512, "height": 1200})
page.wait_for_timeout(3000)
out["logged_in"] = page.locator('button[aria-label="音频"]').count() > 0
print(f"== 登录态 {out['logged_in']} ==")

if not out["logged_in"]:
    out["verdict"] = "BLOCKED_BY_FIXTURE（登录态没了）"
else:
    runs = []
    for rep in range(1, REPS + 1):
        # 每轮**从刚载完**开始（每种条件的起点必须一致）
        page.goto(URL, wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(9000)
        page.set_viewport_size({"width": 1512, "height": 1200})
        page.wait_for_timeout(2500)
        rec = {"rep": rep, "conds": {}}

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

        # after_blank：点画布空白，**验前置态**（工具条应该不在）
        spot = ev(BLANK_JS)
        if spot:
            page.mouse.click(spot[0], spot[1])
            page.wait_for_timeout(1200)
        c = snap("after_blank", f"点了空白 {spot}；工具条在={ev(TOOLBAR_JS)}")
        c["blank_spot"] = spot

        # after_tab：从**当前焦点**开始连按 Tab，逐次记落点 + 那一刻的 tabindex
        tabwalk = []
        for _ in range(16):
            page.keyboard.press("Tab")
            page.wait_for_timeout(140)
            tabwalk.append(ev(FOCUS_JS))
        rec["conds"]["after_tab"] = {
            "note": "点空白后连按 Tab 16 次（逐次记落点与那一刻的 tabindex）",
            "walk": tabwalk,
        }
        print("\n  [after_tab] 逐次落点：")
        for i, f in enumerate(tabwalk, 1):
            print(f"     Tab{i:<2d} {f['aria']!r:28s} 在节点内={f['in_node']} "
                  f"该节点 tabindex={f['node_tabindex']!r} "
                  f"prop={f['node_tabIndexProp']}")
        snap("after_tab_final", "Tab 走完之后再看一眼全画布")

        # after_insert：插入一个音频节点（**不点节点**）
        before = set(ev("() => [...document.querySelectorAll('.react-flow__node')]"
                        ".map(n => n.getAttribute('data-testid')||'')"))
        loc = page.locator('button[aria-label="音频"]')
        rec["insert_ok"] = bool(loc.count())
        if rec["insert_ok"]:
            loc.first.click(timeout=10000)
            page.wait_for_timeout(2500)
        after = ev("() => [...document.querySelectorAll('.react-flow__node')]"
                   ".map(n => n.getAttribute('data-testid')||'')")
        new = [t for t in after if t and t not in before]
        rec["new_node_testid"] = new[0] if new else None
        snap("after_insert", f"插入了 {rec['new_node_testid']}")

        # after_insert_blank：插入后**再点空白**
        spot2 = ev(BLANK_JS)
        if spot2:
            page.mouse.click(spot2[0], spot2[1])
            page.wait_for_timeout(1200)
        c = snap("after_insert_blank", f"插入后点空白 {spot2}")
        c["blank_spot"] = spot2
        # 只看**那个新节点**自己
        if rec["new_node_testid"]:
            one = ev("""(tid) => { const n = document.querySelector(
                `.react-flow__node[data-testid="${tid}"]`);
              if (!n) return {gone: true};
              return {selected: n.classList.contains('selected'),
                      tabindex: n.getAttribute('tabindex'),
                      tabIndexProp: n.tabIndex}; }""",
                    rec["new_node_testid"])
            rec["conds"]["after_insert_blank"]["new_node_only"] = one
            print(f"     ⭐ 只看新节点：{one}")

        # after_select：点那个新节点把它选中，看 tabindex 变不变
        if rec["new_node_testid"]:
            xy = ev("""(tid) => { const n = document.querySelector(
                `.react-flow__node[data-testid="${tid}"]`);
              if (!n) return null; const r = n.getBoundingClientRect();
              return [Math.round(r.x + r.width/2), Math.round(r.y + r.height/2)]; }""",
                rec["new_node_testid"])
            if xy:
                page.mouse.click(xy[0], xy[1])
                page.wait_for_timeout(1500)
                one = ev("""(tid) => { const n = document.querySelector(
                    `.react-flow__node[data-testid="${tid}"]`);
                  if (!n) return {gone: true};
                  return {selected: n.classList.contains('selected'),
                          tabindex: n.getAttribute('tabindex'),
                          tabIndexProp: n.tabIndex}; }""",
                        rec["new_node_testid"])
                rec["conds"]["after_select"] = {
                    "note": "点新节点把它选中之后",
                    "new_node_only": one,
                    "focus": ev(FOCUS_JS),
                    "toolbar": ev(TOOLBAR_JS),
                }
                print(f"\n  [after_select] ⭐ 新节点：{one}  "
                      f"工具条={ev(TOOLBAR_JS)}  焦点={ev(FOCUS_JS)['aria']!r}")
        else:
            rec["conds"]["after_select"] = {
                "verdict": "前置态没成立：这一轮插不进新节点 ⇒ 本条件不测"}
            print("\n  [after_select] !! 前置态没成立（插不进新节点）")

        runs.append(rec)

    out["runs"] = runs
    # 汇总：每个条件下「新节点自己」的 tabindex
    summ = {}
    for name in ("after_insert", "after_insert_blank", "after_select"):
        vals = []
        for r in runs:
            c = r["conds"].get(name) or {}
            o = c.get("new_node_only")
            if o:
                vals.append({"tabindex": o.get("tabindex"),
                             "prop": o.get("tabIndexProp"),
                             "selected": o.get("selected")})
        summ[name] = vals
    # `after_blank` 下**全画布**各类节点的 tabindex（这是 889d 的对照）
    for name in ("fresh_load", "after_blank", "after_tab_final"):
        summ[name] = [(r["conds"].get(name) or {}).get("summary")
                      for r in runs]
    out["summary"] = summ
    print("\n== 汇总 ==")
    print("  新节点自己的 tabindex：")
    for name in ("after_insert", "after_insert_blank", "after_select"):
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
    out["verdict"] = "sampled"

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(f"\n== 已写 {OUT} ==")

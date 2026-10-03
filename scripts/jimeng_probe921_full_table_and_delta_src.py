#!/usr/bin/env python3
r"""batch 921 源站探针（**纯诊断**）：**整张表**存下来，查清「为什么 `n_wrapper_any_ti` 从 76 变成 75」

## 920 留下的确切缺口

920 实测（2 轮 × 每次 14 连按，两轮逐条一致）：

- **归零那一刻** `n_wrapper_any_ti = 0`（一个 `tabindex` 属性都没有）
- **按第 1 次之后立刻变成 76**（1 个 `'0'` + 75 个 `'-1'`）
- **按第 2 次之后变成 75** ⇒ **有且仅有一个本体的 `tabindex` 属性消失了**

⚠️ 920 从**前 12 个的切片**里看，像是「焦点在**两次之前**那个本体的
`tabindex` 属性被移除」⇒ 但**样本只有约 8 个、而且只看得到前 12 个**
⇒ **那个规律不成立、只是观察** ⇒ **不许**拿它编规则。

## 这一批只做一件事：**别再切片，把整张表存下来，并且逐次记 delta**

- `zero_idx` / `idl_idx`：**完整**列表（不再 `slice(0, 12)`）
- 每次普查记 **`added` / `removed` / `changed`**（相对上一次普查）
  ⇒ 于是能**直接**问：「消失的那个下标，和「被布的下标」「焦点所在的下标」
  是什么关系？」而不是从 12 个切片里去猜。

⚠️ 三个候选解释都要**被读数分开**，本批**不预设**哪一个对：
① 与「被布的下标」差一个固定值；② 与「焦点下标」差一个固定值；
③ 别的规律（比如跟**视口内/外**有关 —— React Flow 会做节点虚拟化）。

## 判据纪律

- **纯诊断**：普查**纯读**、**不劫持 prototype、不装 MutationObserver**
- **每轮之间 reload**；**重复 2 轮**
- ⚠️ **`moved` 是必需字段**（904 记过、909 又踩一次）
- 节点总数是易变量 ⇒ **只记不钉**；按**身份**记 DOM 序
- **落盘排在打印之前**；**被挡时也要落盘**；登录判据**未命中就重试**
- ⚠️ **重定向到文件时一律加 `-u`**（914 踩过）
- ⚠️ 探针**只输出读数**，判读留给基线

## 计费边界

只按 `Tab`、点画布空白。**绝不**点生成/发送/购买/充值，
**也绝不**点音色 chip 本身。**不点任何节点。**

跑法：
  ~/.venvs/liblib-harness/bin/python -u scripts/jimeng_headless.py run \
      scripts/jimeng_probe921_full_table_and_delta_src.py
"""

import json

OUT = "/tmp/b921-src-full-table-and-delta.json"
REPS = 2
SETTLE = 400
N_PRESS = 16            # 比 920 多按 2 次，**多攒几个样本**

BLANK_JS = """() => {
  for (const [x, y] of [[1300, 1000], [1360, 920], [1220, 1080],
                        [1400, 840], [400, 1080]]) {
    const t = document.elementFromPoint(x, y);
    if (t && t.closest('.react-flow__pane')
        && !t.closest('.react-flow__node')) return [x, y];
  }
  return null;
}"""

# ⚠️⚠️ **921 的核心读数**：**整张表** + **逐次 delta**。
# ⚠️ 920 最大的问题就是 `slice(0, 12)` ⇒ 这里**一个字都不切**。
# ⚠️ `prev` 传进来是为了算 `added` / `removed` / `changed`
#    ⇒ 于是能**直接**问「消失的那个下标和被布/焦点的下标是什么关系」。
CENSUS_JS = """(prev) => {
  const nodes = [...document.querySelectorAll('.react-flow__node')];
  const zeroIdx = [], idlIdx = [];
  const cur = {};                       // idx -> tabindex 值（null 表示没这个属性）
  for (let i = 0; i < nodes.length; i++) {
    const n = nodes[i];
    const ti = n.getAttribute('tabindex');
    cur[i] = ti;
    if (ti === '0') zeroIdx.push(i);
    if (n.tabIndex >= 0) idlIdx.push(i);
  }
  const added = [], removed = [], changed = [];
  const anyTiIdx = [];
  for (let i = 0; i < nodes.length; i++) if (cur[i] !== null) anyTiIdx.push(i);
  if (prev) {
    for (let i = 0; i < nodes.length; i++) {
      const was = (i in prev) ? prev[i] : null;
      if (was === null && cur[i] !== null) added.push(i);
      else if (was !== null && cur[i] === null) removed.push(i);
      else if (was !== cur[i]) changed.push([i, was, cur[i]]);
    }
  }
  const a = document.activeElement;
  const aIsWrapper = !!(a && a.classList
                    && a.classList.contains('react-flow__node'));
  // ⚠️ 顺带：本体**在视口内吗**（候选解释③要用）
  let inViewport = null;
  if (aIsWrapper) {
    const r = a.getBoundingClientRect();
    inViewport = {w: Math.round(r.width), h: Math.round(r.height),
                  top: Math.round(r.top), left: Math.round(r.left)};
  }
  return {
    n_nodes: nodes.length,
    n_wrapper_ti0: zeroIdx.length,
    n_wrapper_any_ti: anyTiIdx.length,
    n_wrapper_idl_focusable: idlIdx.length,
    // ⚠️⚠️ **完整**列表（920 的教训：一个都不切）
    zero_idx: zeroIdx,
    idl_idx: idlIdx,
    any_ti_idx: anyTiIdx,
    removed, added, changed,
    active: {
      tag: a ? a.tagName : null,
      aria: a ? (a.getAttribute('aria-label') || '').slice(0, 22) : null,
      is_wrapper: aIsWrapper,
      wrapper_idx: aIsWrapper ? nodes.indexOf(a) : null,
      ti_attr: a ? a.getAttribute('tabindex') : null,
      ti_idl: a ? a.tabIndex : null,
      box: inViewport,
    },
  };
}"""


def ev(js, arg=None):
    return page.evaluate(js) if arg is None else page.evaluate(js, arg)


URL = ("https://jimeng.jianying.com/ai-tool/ai-canvas/"
       "64b58cd5-7b04-4312-890a-09f2d1d3399f"
       "?enter_from=project_list&from_page=create")

out = {}
page.goto(URL, wait_until="domcontentloaded", timeout=90000)
page.wait_for_timeout(10000)
page.set_viewport_size({"width": 1512, "height": 1200})
page.wait_for_timeout(3000)
# ⚠️ 906 的教训：**一次没命中不等于没登录** ⇒ 未命中就再等 8s 复判一次
out["login_check_attempts"] = []
for attempt in (1, 2):
    n = page.locator('button[aria-label="音频"]').count()
    out["login_check_attempts"].append(
        {"attempt": attempt, "n_audio_rail_button": n,
         "n_nodes": page.locator(".react-flow__node").count()})
    if n > 0:
        break
    if attempt == 1:
        page.wait_for_timeout(8000)
        n2 = page.locator('button[aria-label="音频"]').count()
        out["login_check_attempts"].append(
            {"attempt": "1b-再等8s", "n_audio_rail_button": n2,
             "n_nodes": page.locator(".react-flow__node").count()})
        if n2 > 0:
            break

out["logged_in"] = any(a["n_audio_rail_button"] > 0
                       for a in out["login_check_attempts"])
print(f"== 登录态 {out['logged_in']} ==")

if not out["logged_in"]:
    out["verdict"] = "BLOCKED_BY_FIXTURE（登录态没了；**已重试过**）"
    # ⚠️ **被挡时也要落盘**（906 的教训）
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"== 已写 {OUT}（被挡时也要落盘）==")
else:
    runs = []
    for rep in range(1, REPS + 1):
        # ⚠️ **每轮之间 reload**（906 已证明这是必须的）
        page.goto(URL, wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(9000)
        page.set_viewport_size({"width": 1512, "height": 1200})
        page.wait_for_timeout(2500)
        rec = {"rep": rep, "n_press": N_PRESS}

        sp = ev(BLANK_JS)
        if sp:
            page.mouse.click(sp[0], sp[1])
            page.wait_for_timeout(900)
        rec["blank_hit"] = sp
        c0 = ev(CENSUS_JS, None)
        rec["census_at_blank"] = c0
        # ⚠️ **用「完整的 tabindex 值表」当 prev**（不是切片、不是下标集合）
        prev_map = ev("() => { const o = {};"
                      " [...document.querySelectorAll('.react-flow__node')]"
                      ".forEach((n, i) => { o[i] = n.getAttribute('tabindex'); });"
                      " return o; }")
        rec["tabindex_map_at_blank"] = prev_map

        presses = []
        for k in range(N_PRESS):
            before = ev(CENSUS_JS, prev_map)     # ⚠️ 按之前普查（带 delta）
            page.keyboard.press("Tab")
            page.wait_for_timeout(SETTLE)
            after = ev(CENSUS_JS, prev_map)      # ⚠️ 按之后普查（带 delta）
            presses.append({
                "k": k + 1,
                "before": {kk: before[kk] for kk in
                           ("n_nodes", "n_wrapper_ti0", "n_wrapper_any_ti",
                            "n_wrapper_idl_focusable", "zero_idx", "idl_idx",
                            "added", "removed", "changed", "active")},
                "after": {kk: after[kk] for kk in
                          ("n_nodes", "n_wrapper_ti0", "n_wrapper_any_ti",
                           "n_wrapper_idl_focusable", "zero_idx", "idl_idx",
                           "added", "removed", "changed", "active")},
                "moved": before["zero_idx"] != after["zero_idx"],
            })
            prev_map = ev("() => { const o = {};"
                          " [...document.querySelectorAll('.react-flow__node')]"
                          ".forEach((n, i) => { o[i] = n.getAttribute('tabindex'); });"
                          " return o; }")
            a = after["active"]
            print(f"  第{k + 1:>2d}次：ti0={after['zero_idx']} "
                  f"any_ti={after['n_wrapper_any_ti']} "
                  f"IDL可聚焦={after['idl_idx']} "
                  f"| removed={after['removed']} added={after['added']} "
                  f"changed={after['changed']} "
                  f"| 焦点idx={a['wrapper_idx']} {a['aria']!r}")
        rec["presses"] = presses
        runs.append(rec)
        print("  （纯读普查，没有装任何监听器）")

    out["runs"] = runs
    out["verdict"] = "sampled"
    # ⚠️ 落盘**必须**排在打印之前（900 的教训）
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print("\n== 汇总（只输出读数，**不判机制**）==")
    for r in runs:
        print(f"  rep{r['rep']}：")
        for p in r["presses"]:
            a, b = p["after"], p["before"]
            print(f"    第{p['k']:>2d}次 any_ti {b['n_wrapper_any_ti']}→"
                  f"{a['n_wrapper_any_ti']} | removed={a['removed']} "
                  f"added={a['added']} | ti0 {b['zero_idx']}→{a['zero_idx']} "
                  f"| 焦点idx={a['active']['wrapper_idx']}")
    print(f"\n== 已写 {OUT} ==")

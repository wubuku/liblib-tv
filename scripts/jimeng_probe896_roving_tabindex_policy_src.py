#!/usr/bin/env python3
"""batch 896 源站探针：源站那个 roving tabindex 的**策略**是什么？

## 这一批要回答的问题（§106 留下的最后一块拼图）

894 测出：**中性态**下源站**所有类型**节点全是 `tabindex=None`/`-1`。
889d 测出：**焦点落在节点那一刻**该节点 wrapper 是 `tabindex='0'`。

⇒ 有人在那中间把 `0` 设上、又（大概）收回去。但**规则完全没测**：
**谁**在**何时**设、设**多久**、**谁**收回。**不许**在测清之前改复刻的
`nodesFocusable`（那会把整个画布 Tab 顺序改掉，§77）。

## ⚠️ 先说 894 自己踩的洞（本批第一个产物）

894 的 `summarize()` 把 tabindex 收成**值的集合**：

```python
v["tabindex"].add(n["tabindex"])   # ← 只收 set，**丢掉计数**
```

所以 894 的 `after_tab_final` 打出 `audio ... tabindex=['-1','0','None']`
——**三个值混在一起**，而「**各有几个** 0」恰好就是区分 roving 的**唯一**判据：

- roving ⇒ 任一时刻**恰好 1 个**节点是 `0`，且就是**带焦点那个**
- 非 roving ⇒ 可能同时有**多个** `0`

⇒ 894 明明**读到了**这个信息，却被 summarize **抹平**了。这跟 893 的
「跨时刻读数混比」是同一族的错：**量到了但没留下能判读的形状**。

## 这批量的三件事

1. **补直方图**：每个条件都记「各 tabindex 值**各有几个**」，外加
   **所有 `0` 的节点身份**（`data-testid`）
2. **挂 MutationObserver**（`attributes` + `attributeOldValue` +
   `attributeFilter:['tabindex']` + `subtree`）—— 从**任何交互之前**就挂上，
   拿到**有序**的变更流：`oldValue` / 变更时的值 / 目标身份 / 相对时间。
   MutationObserver 回调是微任务 ⇒ 报告时间**晚于**实际发生时间，所以
   **时间戳只能定「谁先谁后」的大方向**，不能当精确时刻。
3. **分辨「keydown 时就设好」还是「focusin 之后才设」**：在 `focusin`
   **捕获阶段**读一次落点的 tabindex。
   - 捕获阶段已经是 `0` ⇒ **先设 0、再移焦点**（keydown 时的 roving）
   - 捕获阶段还是 `-1`、步后变 `0` ⇒ 焦点移动**之后**才设（focusin 响应式）

## 收尾问题：「设多久」

- Tab 到下一个节点 ⇒ 上一个的 `0` 收回去吗？
- Shift+Tab **走回去** ⇒ 之前那个会不会**重新**拿到 `0`？
- 点空白（焦点整个离开画布）⇒ 所有 `0` 会清掉吗？

## 纪律

- 每轮**重复 2 次**（一次成功不叫可靠）
- 钉**关系**（「有几个 0」「0 在谁身上」「是不是带焦点那个」），
  **不钉**节点序号、不钉节点总数、不钉绝对坐标
- `defaultPrevented` 用 **892 的取法**：**捕获阶段只存事件对象的引用**
  （`ref: e`），等**派发结束**后（冒泡阶段那个 handler）再读值 ——
  只在捕获阶段读会**恒真为假**（890 的教训）
- **诊断动作必须还原**：`finally` 里 `mo.disconnect()` + 摘三类监听；
  探针**不劫持 prototype**（劫持放下一批单独做，且必须可 revert）
- 每轮**从刚载完**开始

## 计费边界

只按 Tab / Shift+Tab、点画布空白。**绝不**点生成/发送/购买/充值，
**也绝不**点音色 chip 本身。

跑法：
  ~/.venvs/liblib-harness/bin/python scripts/jimeng_headless.py run \
      scripts/jimeng_probe896_roving_tabindex_policy_src.py
"""

import json

OUT = "/tmp/b896-src-roving-policy.json"
REPS = 2
FWD_TABS = 12
BACK_TABS = 4
SETTLE_MS = 900          # Playwright 收**毫秒**
SETTLE_AFTER_MS = 1500   # 「设多久」：静置这么久再读一次

# 空白点：与 894 同一组候选（**必须记下实际用的是哪一个**）
BLANK_JS = """() => {
  for (const [x, y] of [[1300, 1000], [1360, 920], [1220, 1080],
                        [1400, 840], [400, 1080]]) {
    const t = document.elementFromPoint(x, y);
    if (t && t.closest('.react-flow__pane')
        && !t.closest('.react-flow__node')) return [x, y];
  }
  return null;
}"""

# ══ 仪器：一个有序日志，MutationObserver 与事件监听往同一处记 ══
# ⚠️ 不劫持 prototype：这一批只做**观测**，不做拦截。
INSTALL_JS = """() => {
  const root = document.querySelector('.react-flow');
  if (!root) return {ok: false, why: 'no .react-flow root'};
  if (window.__b896) { window.__b896.cleanup(); }
  const log = [];
  let seq = 0;
  const t0 = performance.now();

  // 元素身份：节点用 data-testid（稳定），别的用「tag+class+在 root 里的序号」
  const ident = (el) => {
    if (!el || el.nodeType !== 1) return String(el);
    const tid = el.getAttribute && el.getAttribute('data-testid');
    if (tid) return 'tid:' + tid;
    const tag = el.tagName;
    const cls = (el.className && el.className.baseVal !== undefined)
      ? el.className.baseVal : (el.className || '');
    const c = String(cls).split(/\\s+/).filter(Boolean).slice(0, 2).join('.');
    let i = 0, p = el;
    while ((p = p.previousElementSibling)) i++;
    return 'el:' + tag + (c ? '.' + c : '') + '#' + i;
  };

  const onFocusInCap = (e) => {
    // 捕获阶段：此刻**还没人**处理过这个 focusin
    log.push({seq: seq++, t: +(performance.now() - t0).toFixed(1),
              kind: 'focusin@capture',
              target: ident(e.target),
              target_tabindex: e.target.getAttribute
                ? e.target.getAttribute('tabindex') : null,
              is_active: document.activeElement === e.target,
              active_ident: ident(document.activeElement)});
  };
  const onFocusOut = (e) => {
    log.push({seq: seq++, t: +(performance.now() - t0).toFixed(1),
              kind: 'focusout',
              target: ident(e.target),
              target_tabindex: e.target.getAttribute
                ? e.target.getAttribute('tabindex') : null,
              active_ident: ident(document.activeElement)});
  };
  const onKey = (e) => {
    log.push({seq: seq++, t: +(performance.now() - t0).toFixed(1),
              kind: 'keydown@capture', key: e.key,
              target: ident(e.target), ref: e});
  };
  // 派发**结束**后才读 defaultPrevented（890/892 的教训：只读捕获阶段恒为假）
  const onKeyEnd = (e) => {
    const rec = log.find(r => r.ref === e);
    if (rec) { rec.default_prevented = e.defaultPrevented;
               rec.key = e.key; delete rec.ref; }
  };
  document.addEventListener('focusin', onFocusInCap, true);
  document.addEventListener('focusout', onFocusOut, true);
  document.addEventListener('keydown', onKey, true);
  document.addEventListener('keydown', onKeyEnd, false);

  const mo = new MutationObserver((recs) => {
    for (const r of recs) {
      log.push({seq: seq++, t: +(performance.now() - t0).toFixed(1),
                kind: 'attr:' + r.attributeName,
                target: ident(r.target),
                oldValue: r.oldValue,
                value_at_flush: r.target.getAttribute(r.attributeName),
                node_kind: (r.target.className
                  && String(r.target.className).includes('react-flow__node-'))
                  ? String(r.target.className).match(
                      /react-flow__node-[a-z]+/)?.[0] : null});
    }
  });
  mo.observe(root, {attributes: true, attributeOldValue: true,
                    attributeFilter: ['tabindex'], subtree: true});

  window.__b896 = {
    log,
    dump: () => log.slice(),
    cleanup: () => {
      mo.disconnect();
      document.removeEventListener('focusin', onFocusInCap, true);
      document.removeEventListener('focusout', onFocusOut, true);
      document.removeEventListener('keydown', onKey, true);
      document.removeEventListener('keydown', onKeyEnd, false);
      delete window.__b896;
    },
  };
  return {ok: true, n_nodes: document.querySelectorAll('.react-flow__node').length};
}"""

# ══ 读数：把 894 丢掉的**直方图**补回来 ══
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


def ev(js, arg=None):
    return page.evaluate(js) if arg is None else page.evaluate(js, arg)


def derive(s):
    """把读数压成**关系**（钉关系，不钉序号/总数）。"""
    active_tid = (s.get("active") or {}).get("tid")
    zeros = s.get("zeros") or []
    return {
        "n_zero": s.get("n_zero"),
        "zeros": zeros,
        "active_tid": active_tid,
        # 恰好 1 个 0，且就是带焦点那个 ⇒ roving 的**必要**条件
        "zero_is_active_only": (
            s.get("n_zero") == 1 and active_tid is not None
            and zeros == [active_tid]),
        "zero_count_matches_active": (
            s.get("n_zero") == (1 if active_tid else 0)),
        "hist": s.get("hist"),
        "active_node_ti": (s.get("active") or {}).get("node_ti"),
        "active_self_ti": (s.get("active") or {}).get("self_ti"),
        # 0 挂在哪一层：wrapper 自身 vs 更外层
        "chain_ti": [c["ti"] for c in (s.get("chain") or [])][:6],
    }


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
        # 每轮**从刚载完**开始（各条件起点必须一致）
        page.goto(URL, wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(9000)
        page.set_viewport_size({"width": 1512, "height": 1200})
        page.wait_for_timeout(2500)
        rec = {"rep": rep, "steps": []}
        cur = {"cond": "fresh_load", "note": "刚载完，什么都不做"}
        print(f"\n===== rep {rep} =====")

        def read(cond, note=""):
            """读一次当前状态 + 推关系 + 打印。"""
            s = ev(STATE_JS)
            d = {"cond": cond, "note": note, "raw": s, "derive": derive(s)}
            rec["steps"].append(d)
            print(f"  [{cond}] {' ' + note if note else ''}")
            print(f"     hist={d['derive']['hist']} n_zero={d['derive']['n_zero']} "
                  f"zeros={d['derive']['zeros']}")
            print(f"     active tid={d['derive']['active_tid']} "
                  f"node_ti={d['derive']['active_node_ti']} "
                  f"self_ti={d['derive']['active_self_ti']} "
                  f"chain={d['derive']['chain_ti']}")
            print(f"     ⇒ 恰好一个0且是带焦点那个？"
                  f"{d['derive']['zero_is_active_only']}")
            return d

        # 仪器在**任何交互之前**挂上（否则读不到 blank 之前发生了什么）
        inst = ev(INSTALL_JS)
        rec["instrument"] = inst
        print(f"  仪器：{inst}")

        try:
            read("fresh_load", "刚载完，什么都不做")

            # after_blank：点画布空白
            spot = ev(BLANK_JS)
            if spot:
                page.mouse.click(spot[0], spot[1])
                page.wait_for_timeout(SETTLE_MS)
            read("after_blank", f"点了空白 {spot}")

            # 往前 Tab：每一步都读
            fwd = []
            for i in range(1, FWD_TABS + 1):
                page.keyboard.press("Tab")
                page.wait_for_timeout(SETTLE_MS)
                d = read(f"tab_fwd_{i}", f"第 {i} 次 Tab")
                fwd.append(d["derive"])
            rec["fwd"] = fwd

            # 「设多久」：静置一段再读同一个状态
            page.wait_for_timeout(SETTLE_AFTER_MS)
            read("after_settle", f"Tab 完静置 {SETTLE_AFTER_MS}ms 之后")

            # 往回 Shift+Tab：之前那个会不会**重新**拿到 0
            back = []
            for i in range(1, BACK_TABS + 1):
                page.keyboard.press("Shift+Tab")
                page.wait_for_timeout(SETTLE_MS)
                d = read(f"tab_back_{i}", f"第 {i} 次 Shift+Tab")
                back.append(d["derive"])
            rec["back"] = back

            # 点空白：焦点整个离开画布 ⇒ 所有 0 会清掉吗？
            spot2 = ev(BLANK_JS)
            if spot2:
                page.mouse.click(spot2[0], spot2[1])
                page.wait_for_timeout(SETTLE_MS)
            read("after_blank_2", f"回走完之后再点空白 {spot2}")
            page.wait_for_timeout(SETTLE_AFTER_MS)
            read("after_blank_2_settle", "点空白后静置再看")

            # 有序变更流
            log = ev("() => window.__b896 ? window.__b896.dump() : null")
            rec["log"] = log
            attrs = [r for r in (log or []) if r["kind"].startswith("attr:")]
            rec["n_attr_mutations"] = len(attrs)
            print(f"\n  变更流：{len(log or [])} 条，其中 tabindex 属性变更 "
                  f"{len(attrs)} 条")
            for r in (log or []):
                if r["kind"].startswith("attr:"):
                    print(f"     #{r['seq']:<4d} t={r['t']:<9} "
                          f"{r['target'][:34]:34s} "
                          f"{r['oldValue']!r} → {r['value_at_flush']!r}")
                elif r["kind"] == "keydown@capture":
                    print(f"     #{r['seq']:<4d} t={r['t']:<9} "
                          f"keydown {r.get('key')!r} "
                          f"prevented={r.get('default_prevented')} "
                          f"@{r['target'][:28]}")
                else:
                    print(f"     #{r['seq']:<4d} t={r['t']:<9} {r['kind']} "
                          f"{r['target'][:30]} ti={r.get('target_tabindex')!r} "
                          f"active={r.get('active_ident', '')[:28]}")
        finally:
            # 诊断动作必须还原
            try:
                ev("() => { if (window.__b896) { window.__b896.cleanup(); "
                   "return 'cleaned'; } return 'none'; }")
            except Exception as e:      # noqa: BLE001
                print(f"  !! cleanup 失败（页面可能已经走了）：{e}")
            print("  仪器已还原（disconnect + 摘监听）")

        runs.append(rec)

    out["runs"] = runs

    # ── 汇总：只汇总**关系**，不钉节点数/序号 ──
    def agg(path_fn):
        vals = []
        for r in runs:
            vals.append(path_fn(r))
        return vals

    n_zeros_fwd = agg(lambda r: [d["n_zero"] for d in r["fwd"]])
    only_active = agg(lambda r: [d["zero_is_active_only"] for d in r["fwd"]])
    back_zeros = agg(lambda r: [d["n_zero"] for d in r["back"]])
    back_only = agg(lambda r: [d["zero_is_active_only"] for d in r["back"]])
    settle = agg(lambda r: next(
        (d["derive"] for d in r["steps"] if d["cond"] == "after_settle"), None))
    blank2 = agg(lambda r: next(
        (d["derive"] for d in r["steps"] if d["cond"] == "after_blank_2"), None))
    blank2_settle = agg(lambda r: next(
        (d["derive"] for d in r["steps"] if d["cond"] == "after_blank_2_settle"),
        None))
    n_attr = agg(lambda r: r.get("n_attr_mutations"))
    prevented = agg(lambda r: sorted({
        r.get("default_prevented") for r in (r.get("log") or [])
        if r["kind"] == "keydown@capture"}))

    out["summary"] = {
        "n_zero_per_fwd_tab": n_zeros_fwd,
        "zero_is_active_only_fwd": only_active,
        "n_zero_per_back_tab": back_zeros,
        "zero_is_active_only_back": back_only,
        "after_settle": settle,
        "after_blank_2": blank2,
        "after_blank_2_settle": blank2_settle,
        "n_tabindex_attr_mutations": n_attr,
        "keydown_defaultPrevented_seen": prevented,
    }
    print("\n== 汇总（**关系**，不钉序号/总数）==")
    print(f"  每次 Tab 后「有几个 0」        : {n_zeros_fwd}")
    print(f"  「恰好一个 0 且是带焦点那个」 : {only_active}")
    print(f"  每次 Shift+Tab 后「有几个 0」 : {back_zeros}")
    print(f"  回走时「恰好一个且是焦点那个」: {back_only}")
    print(f"  静置后 n_zero                 : "
          f"{[s and s.get('n_zero') for s in settle]}")
    print(f"  点空白后 n_zero               : "
          f"{[s and s.get('n_zero') for s in blank2]}")
    print(f"  点空白+静置后 n_zero          : "
          f"{[s and s.get('n_zero') for s in blank2_settle]}")
    print(f"  tabindex 属性变更条数         : {n_attr}")
    print(f"  读到的 keydown defaultPrevented 集合: {prevented}")
    out["verdict"] = "sampled"

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(f"\n== 已写 {OUT} ==")

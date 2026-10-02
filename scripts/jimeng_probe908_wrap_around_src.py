#!/usr/bin/env python3
"""batch 908 源站探针：**到底会不会绕回？** —— 899 那条「绝不绕回」可能是取样假象

## 907 顺带撞出来的东西（**一次诊断，必须重验**）

907 本来是去扫「终点 → 起点」那个映射的，结果**没扫成**（下面说）。
但 907 的读数逼着我做了一个补充诊断，那个诊断撞出这一条：

正向走查 `'0'` 的位置（78 个节点、107 次按压）：

```
0,1,…,11, [12 跳过], 13,…,67, [68 跳过], 69,…,75      ← 第 1–83 次按压
第 84 次：焦点落到 `替换媒体`（节点 75 的**内层控件**）⇒ 不布
第 84–102 次：焦点**一路走出画布**（替换媒体 → 文本 → 选择工具 → 小地图 →
             显示连线 → Zoom options → 与 AI 对话 → 返回首页 → 项目 →
             搜索 → 生成历史 → 分享 → 更多 → Credits → 用户菜单 → `Canvas`）
             ⇒ **`'0'` 一直停在 75，一次都没动**（896⑤ 再获一次证实）
第 103 次：焦点在**画布根** `Canvas`、按 **`Tab`** ⇒ **`'0'` 布到 0 —— 绕回了！**
第 104–107 次：0→1→2→3
```

⚠️⚠️ **这与 899 的「到末尾撒手、绝不绕回」相反**，而 901 的实现正是按
899 写的（越界直接 `return`、**没有** `% len`）⇒ **901 可能是错的。**

## 899 为什么会读成「不绕回」？（**这才是要验的**）

899 按了 `节点数 + 20` 次。而从诊断看：**走完末尾之后，还要再按约 19 次**
焦点才走回画布根 ⇒ **899 那点按压预算在焦点回来之前就用完了**
⇒ **「不绕回」是取样假象，它其实没问到绕回。**

⇒ **必须验的命题**：`绕回 ⟺ 指针在末尾 且 焦点回到画布根 且 方向为 Tab`
（906 已经证了后半句：画布根 + `Shift+Tab` **一次都不布**）

## 两条臂

| 臂 | 序列 | 问什么 |
|---|---|---|
| `W1` | 点空白 → 一路按 `Tab`（**按到焦点自己走回画布根之后**） | **到底会不会绕回？** 绕回发生在第几次？ |
| `W2` | 点空白 → 按 `Tab` 到**刚过末尾** → **立刻再点一次空白**（焦点直接回画布根，**不走出去**）→ 按 `Tab` ×3 | **绕回是因为「焦点回到画布根」，还是因为「走出画布」？** |

⇒ `W2` 是**专为证伪 `W1` 的机制假设**设计的：若 `W2` **也**绕回到 0 ⇒
「走出画布」不是必要条件；`W2` 若停在末尾 ⇒ 「必须先走出画布」。

## 判据纪律

- 仪器**逐字复用** 906（`__b908`）
- **每臂之间 reload**；**每轮重复 2 次**（一次成功不叫可靠）
- 节点总数是**易变量** ⇒ 按**身份**记 DOM 序，**不钉序号**、**不钉总数**
- **落盘排在打印之前**；**被挡时也要落盘**；登录判据**未命中就重试**
- ⚠️ 探针**只输出读数**，判读留给基线

## 计费边界

只按 Tab / Shift+Tab、点画布空白。**绝不**点生成/发送/购买/充值，
**也绝不**点音色 chip 本身。

跑法：
  ~/.venvs/liblib-harness/bin/python scripts/jimeng_headless.py run \
      scripts/jimeng_probe908_wrap_around_src.py
"""

import json

OUT = "/tmp/b908-src-wrap-around.json"
REPS = 2
SETTLE = 300           # 毫秒（901 教训：次数要多，别指望每次都推进指针）

BLANK_JS = """() => {
  for (const [x, y] of [[1300, 1000], [1360, 920], [1220, 1080],
                        [1400, 840], [400, 1080]]) {
    const t = document.elementFromPoint(x, y);
    if (t && t.closest('.react-flow__pane')
        && !t.closest('.react-flow__node')) return [x, y];
  }
  return null;
}"""

NAMES_JS = """() => {
  const out = {};
  [...document.querySelectorAll('.react-flow__node')].forEach((n, i) => {
    out[n.getAttribute('data-testid') || ''] = {
      idx: i, aria: n.getAttribute('aria-label') || ''};
  });
  return out;
}"""

# ⚠️ 仪器逐字来自 906
INSTALL_JS = """() => {
  const root = document.querySelector('.react-flow');
  if (!root) return {ok: false, why: 'no .react-flow root'};
  if (window.__b908) { window.__b908.cleanup(); }
  const log = [];
  let seq = 0;
  const t0 = performance.now();
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
    log.push({seq: seq++, t: +(performance.now() - t0).toFixed(1),
              kind: 'focusin@capture', target: ident(e.target),
              target_is_node_wrapper: !!(e.target.classList
                && e.target.classList.contains('react-flow__node')),
              target_aria: (e.target.getAttribute
                && e.target.getAttribute('aria-label')) || ''});
  };
  const onKey = (e) => {
    log.push({seq: seq++, t: +(performance.now() - t0).toFixed(1),
              kind: 'keydown@capture', key: e.key, shift: e.shiftKey,
              target: ident(e.target), ref: e});
  };
  const onKeyEnd = (e) => {
    const rec = log.find(r => r.ref === e);
    if (rec) { rec.default_prevented = e.defaultPrevented;
               rec.key = e.key; rec.shift = e.shiftKey; delete rec.ref; }
  };
  document.addEventListener('focusin', onFocusInCap, true);
  document.addEventListener('keydown', onKey, true);
  document.addEventListener('keydown', onKeyEnd, false);
  const mo = new MutationObserver((recs) => {
    for (const r of recs) {
      log.push({seq: seq++, t: +(performance.now() - t0).toFixed(1),
                kind: 'attr:' + r.attributeName,
                target: ident(r.target), oldValue: r.oldValue,
                value_at_flush: r.target.getAttribute(r.attributeName)});
    }
  });
  mo.observe(root, {attributes: true, attributeOldValue: true,
                    attributeFilter: ['tabindex'], subtree: true});
  window.__b908 = {
    log, dump: () => log.slice(),
    since: (f) => log.filter(r => r.seq >= f),
    cursor: () => log.length ? log[log.length - 1].seq + 1 : 0,
    cleanup: () => {
      mo.disconnect();
      document.removeEventListener('focusin', onFocusInCap, true);
      document.removeEventListener('keydown', onKey, true);
      document.removeEventListener('keydown', onKeyEnd, false);
      delete window.__b908;
    },
  };
  return {ok: true, n_nodes: document.querySelectorAll('.react-flow__node').length};
}"""

# ⚠️ 仪器逐字来自 906
STATE_JS = """() => {
  const nodes = [...document.querySelectorAll('.react-flow__node')];
  const hist = {}; const zeros = [];
  for (const n of nodes) {
    const ti = n.getAttribute('tabindex');
    const k = ti === null ? 'None' : ti;
    hist[k] = (hist[k] || 0) + 1;
    if (ti === '0') zeros.push(n.getAttribute('data-testid') || '(no-testid)');
  }
  const a = document.activeElement;
  return {n_nodes: nodes.length, hist, zeros, n_zero: zeros.length,
    active: {tag: a ? a.tagName : null,
      aria: (a && a.getAttribute && a.getAttribute('aria-label')) || '',
      tid: (a && a.getAttribute && a.getAttribute('data-testid')) || '',
      in_node: !!(a && a.classList
                  && a.classList.contains('react-flow__node'))}};
}"""


def ev(js, arg=None):
    return page.evaluate(js) if arg is None else page.evaluate(js, arg)


def snap(names):
    st = ev(STATE_JS)
    zs = [names.get(t, {}).get("idx") for t in st["zeros"]]
    return {"zeros": zs,
            "zero_one": (zs[0] if len(zs) == 1 else zs),
            "active_aria": st["active"]["aria"][:22],
            "active_is_wrapper": st["active"]["in_node"]}


def tap(pg, names, mod=False):
    """一次按压：按前焦点 + 布了什么 + 按后落点 + 按后 `'0'`。"""
    before = snap(names)
    cur = ev("() => window.__b908.cursor()")
    pg.keyboard.press("Shift+Tab" if mod else "Tab")
    pg.wait_for_timeout(SETTLE)
    seg = ev("(f) => window.__b908.since(f)", cur)
    armed = [r["target"] for r in seg
             if r["kind"].startswith("attr:")
             and r["value_at_flush"] == '0' and r["oldValue"] != '0']
    fi = [r for r in seg if r["kind"] == "focusin@capture"]
    kd = [r for r in seg if r["kind"] == "keydown@capture"]
    after = snap(names)
    return {"armed": armed,
            "armed_idx": [names.get(a[4:], {}).get("idx")
                          for a in armed if a.startswith("tid:")],
            "pre_aria": before["active_aria"],
            "pre_is_wrapper": before["active_is_wrapper"],
            "zero_before": before["zeros"],
            "zero_after": after["zeros"],
            "moved": before["zeros"] != after["zeros"],
            "land_aria": [f["target_aria"] for f in fi],
            "prevented": (kd[-1].get("default_prevented") if kd else None)}


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
         "n_react_flow": page.locator(".react-flow").count(),
         "n_nodes": page.locator(".react-flow__node").count()})
    if n > 0:
        break
    if attempt == 1:
        page.wait_for_timeout(8000)
        n2 = page.locator('button[aria-label="音频"]').count()
        out["login_check_attempts"].append(
            {"attempt": "1b-再等8s", "n_audio_rail_button": n2,
             "n_react_flow": page.locator(".react-flow").count(),
             "n_nodes": page.locator(".react-flow__node").count()})
        if n2 > 0:
            break

out["logged_in"] = any(a["n_audio_rail_button"] > 0
                       for a in out["login_check_attempts"])
print(f"== 登录态 {out['logged_in']} ==")

if not out["logged_in"]:
    out["verdict"] = "BLOCKED_BY_FIXTURE（登录态没了；**已重试过**）"
    # ⚠️ **被挡时也要落盘** —— 被挡恰恰是最该留痕的一次（906 的教训）
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"== 已写 {OUT}（被挡时也要落盘）==")
else:
    runs = []
    for rep in range(1, REPS + 1):
        rec = {"rep": rep, "arms": []}

        for arm_name in ("W1", "W2"):
            # ⚠️ **每臂之间 reload**（906 已证明这是必须的）
            page.goto(URL, wait_until="domcontentloaded", timeout=90000)
            page.wait_for_timeout(9000)
            page.set_viewport_size({"width": 1512, "height": 1200})
            page.wait_for_timeout(2500)
            names = ev(NAMES_JS)
            n = len(names)
            inst = ev(INSTALL_JS)
            print(f"\n--- rep{rep} {arm_name}（{n} 个节点，"
                  f"instrument={inst.get('ok')}）---")

            def blank():
                sp = ev(BLANK_JS)
                if sp:
                    page.mouse.click(sp[0], sp[1])
                    page.wait_for_timeout(900)
                return sp

            trace = []
            try:
                blank()
                if arm_name == "W1":
                    # 一路按到**焦点自己走回画布根之后**为止
                    # （诊断里：从末尾到画布根约 19 次 ⇒ 留足 n+45 的预算）
                    for _ in range(n + 45):
                        trace.append(tap(page, names))
                        if trace[-1]["zero_after"] == [0] and len(trace) > n:
                            break            # 一旦**第二次**布到 0 就收
                else:
                    # W2：按到刚过末尾，**立刻再点一次空白**（不走出去）
                    for _ in range(n + 6):
                        trace.append(tap(page, names))
                    blank()
                    for _ in range(3):
                        trace.append(tap(page, names))
            finally:
                try:
                    ev("() => { if (window.__b908) { window.__b908.cleanup(); "
                       "return 'cleaned'; } return 'none'; }")
                except Exception as e:          # noqa: BLE001
                    print(f"  !! cleanup 失败：{e}")

            moved = [(i + 1, t["zero_after"]) for i, t in enumerate(trace)
                     if t["moved"]]
            seq = [z[0] for _, z in moved if len(z) == 1]
            first_pass = [x for x in seq if x not in seq[:seq.index(x) + 1][:-1]]
            arm_rec = {
                "arm": arm_name, "n_nodes": n,
                "n_press": len(trace), "n_moved": len(moved),
                "moved_seq": seq,
                "moved_at_press": [p for p, _ in moved],
                # **第二次**布到 0 的按压序号（第一次是起走，不算）
                "wrap_press": next((p for p, z in moved
                                    if z == [0] and p > 1), None),
                "max_zero": max((x for x in seq if isinstance(x, int)),
                                default=None),
                "trace_tail": [
                    {"press": i + 1, "armed_idx": t["armed_idx"],
                     "pre_aria": t["pre_aria"],
                     "pre_is_wrapper": t["pre_is_wrapper"],
                     "zero_after": t["zero_after"],
                     "land_aria": t["land_aria"][:1]}
                    for i, t in list(enumerate(trace))[-26:]],
                "prevented_all_false": all(t["prevented"] is False
                                           for t in trace),
            }
            rec["arms"].append(arm_rec)
            print(f"  按了 {arm_rec['n_press']} 次，"
                  f"`'0'` 变化 {arm_rec['n_moved']} 次，"
                  f"最大下标 {arm_rec['max_zero']}，"
                  f"**第二次布到 0 发生在第 {arm_rec['wrap_press']} 次**"
                  f"（None = 没绕回）")
            if arm_name == "W1":
                print(f"  走查序列: {seq}")
        runs.append(rec)
        print("  仪器已还原")

    out["runs"] = runs
    out["summary"] = [{
        "rep": r["rep"],
        "arms": [{"arm": a["arm"], "n_nodes": a["n_nodes"],
                  "n_press": a["n_press"], "n_moved": a["n_moved"],
                  "max_zero": a["max_zero"], "wrap_press": a["wrap_press"],
                  "prevented_all_false": a["prevented_all_false"]}
                 for a in r["arms"]],
    } for r in runs]
    out["verdict"] = "sampled"

    # ⚠️ 落盘**必须**排在打印之前
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print("\n== 汇总（只输出读数，**不判机制**）==")
    for row in out["summary"]:
        print(f"  rep{row['rep']}")
        for a in row["arms"]:
            print(f"    {a['arm']}: 按 {a['n_press']} 次 / 变化 {a['n_moved']} 次 / "
                  f"最大 {a['max_zero']} / **绕回于第 {a['wrap_press']} 次**"
                  f" / prevented 全 False={a['prevented_all_false']}")
    print(f"\n== 已写 {OUT} ==")

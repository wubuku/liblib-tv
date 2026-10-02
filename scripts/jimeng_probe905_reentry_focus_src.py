#!/usr/bin/env python3
"""batch 905 源站探针（草稿，放 /tmp，等 904 门禁过了再落进仓库）

## 904 留下的取样缺口（**明确点名**的那一条）

904 测出：回来后**第一次**布 `'0'` 的下标是 **0 / 1 / 2 / 12**（4 臂各 2/2），
且**与终点无关**。但 904 的 `press()` **只抽了 `armed` 与 `prevented`**，
**没有逐次记「焦点落到哪个元素」** ⇒ 成因**未查明**（取样缺口，不是「测出来没有」）。

## 这一批只做两件事

### A. 把取样缺口补上：逐次记焦点落点
每次按压都记三样：**布了什么下标** / **焦点落到了哪个 `aria`** / **有没有被内层控件吃掉**。

### B. 单变量阶梯（每级只加一件事）
| 臂 | 走到末尾 | 回走 `k` 次 | 变量 |
|---|---|---|---|
| `L0` | ✗（从未 Tab 过） | ✗ | 基线 |
| `L1` | ✓ | ✗ | 只加「走到末尾」 |
| `L2` | ✓ | ✓ | 再加「回走 k 次」 |

**每臂之间 reload**（904 最大的缺陷：臂间不 reload ⇒ 「入场状态」其实是上一臂的尾巴）。
`k` 固定 30（904 已证终点 `= 88 − k`，不用再扫）。

## 判据纪律

- 仪器**逐字复用** 900（`__b905`）
- **每臂之间 reload** ⇒ 入场状态干净
- 节点总数是易变量 ⇒ 按**身份**记 DOM 序，不钉序号
- 每轮**重复 2 次**；臂序固定
- **落盘排在打印之前**
- ⚠️ 探针**只输出读数**，判读留给基线

## 计费边界

只按 Tab / Shift+Tab、点画布空白。**绝不**点生成/发送/购买/充值，
**也绝不**点音色 chip 本身。
"""

import json

OUT = "/tmp/b905-src-reentry-focus.json"
REPS = 2
K_BACK = 30
SETTLE = 300           # 毫秒（901 教训：次数要多，别指望每次都推进指针）

ARMS = [
    {"label": "L0-never-tabbed", "walk_end": False, "back": 0},
    {"label": "L1-to-end",        "walk_end": True,  "back": 0},
    {"label": "L2-to-end-back30", "walk_end": True,  "back": K_BACK},
]

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

# ⚠️ 仪器逐字来自 900
INSTALL_JS = """() => {
  const root = document.querySelector('.react-flow');
  if (!root) return {ok: false, why: 'no .react-flow root'};
  if (window.__b905) { window.__b905.cleanup(); }
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
  window.__b905 = {
    log, dump: () => log.slice(),
    since: (f) => log.filter(r => r.seq >= f),
    cursor: () => log.length ? log[log.length - 1].seq + 1 : 0,
    cleanup: () => {
      mo.disconnect();
      document.removeEventListener('focusin', onFocusInCap, true);
      document.removeEventListener('keydown', onKey, true);
      document.removeEventListener('keydown', onKeyEnd, false);
      delete window.__b905;
    },
  };
  return {ok: true, n_nodes: document.querySelectorAll('.react-flow__node').length};
}"""

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
  const an = a && a.closest && a.closest('.react-flow__node');
  return {n_nodes: nodes.length, hist, zeros, n_zero: zeros.length,
    active: {tag: a ? a.tagName : null,
      aria: (a && a.getAttribute && a.getAttribute('aria-label')) || '',
      tid: (a && a.getAttribute && a.getAttribute('data-testid')) || '',
      in_node: !!an,
      node_tid: an ? an.getAttribute('data-testid') : null}};
}"""


def ev(js, arg=None):
    return page.evaluate(js) if arg is None else page.evaluate(js, arg)


def press(pg, mod=False):
    """一次按压：布了什么下标 / 焦点落到哪个 aria / 有没有被内层控件吃掉。"""
    cur = ev("() => window.__b905.cursor()")
    pg.keyboard.press("Shift+Tab" if mod else "Tab")
    pg.wait_for_timeout(SETTLE)
    seg = ev("(f) => window.__b905.since(f)", cur)
    armed = [r["target"] for r in seg
             if r["kind"].startswith("attr:")
             and r["value_at_flush"] == '0' and r["oldValue"] != '0']
    fi = [r for r in seg if r["kind"] == "focusin@capture"]
    kd = [r for r in seg if r["kind"] == "keydown@capture"]
    return {"armed": armed,
            "focus_aria": [f["target_aria"] for f in fi],
            "focus_is_node": [f["target_is_node_wrapper"] for f in fi],
            "focus_tid": [f["target"] for f in fi],
            "prevented": (kd[-1].get("default_prevented") if kd else None)}


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
        rec = {"rep": rep, "arms": []}
        for spec in ARMS:
            # ⚠️ **每臂之间 reload**（904 的最大缺陷：入场状态是上一臂的尾巴）
            page.goto(URL, wait_until="domcontentloaded", timeout=90000)
            page.wait_for_timeout(9000)
            page.set_viewport_size({"width": 1512, "height": 1200})
            page.wait_for_timeout(2500)
            names = ev(NAMES_JS)
            n = len(names)
            rec.setdefault("n_nodes", n)
            inst = ev(INSTALL_JS)
            print(f"\n--- rep{rep} {spec['label']}（{n} 个节点，"
                  f"instrument={inst.get('ok')}）---")

            def blank():
                sp = ev(BLANK_JS)
                if sp:
                    page.mouse.click(sp[0], sp[1])
                    page.wait_for_timeout(900)
                return sp

            def snap():
                st = ev(STATE_JS)
                return {"zeros": [names.get(t, {}).get("idx") for t in st["zeros"]],
                        "n_zero": st["n_zero"],
                        "active_in_node": st["active"]["in_node"],
                        "active_aria": st["active"]["aria"][:20]}

            try:
                blank()
                entry = snap()
                fwd = []
                if spec["walk_end"]:
                    for _ in range(n + 25):        # 与 902/903/904 同
                        fwd.append(press(page))
                at_end = snap()
                back = [press(page, mod=True) for _ in range(spec["back"])]
                endpoint = snap()
                blank()
                # ⭐ 逐次记：布了什么 + 焦点落到哪个 aria
                after = [press(page) for _ in range(8)]
            finally:
                try:
                    ev("() => { if (window.__b905) { window.__b905.cleanup(); "
                       "return 'cleaned'; } return 'none'; }")
                except Exception as e:          # noqa: BLE001
                    print(f"  !! cleanup 失败：{e}")

            def idx_of(a):
                return names.get(a[4:], {}).get("idx") if a.startswith("tid:") else None

            rec["arms"].append({
                "label": spec["label"], "walk_end": spec["walk_end"],
                "back": spec["back"],
                "entry": entry, "at_end": at_end, "endpoint": endpoint,
                "fwd_armed_count": sum(1 for s in fwd if s["armed"]),
                "back_armed_count": sum(1 for s in back if s["armed"]),
                # ⭐ 逐次轨迹
                "after_per_press": [
                    {"armed_idx": [idx_of(a) for a in s["armed"]],
                     "focus_aria": s["focus_aria"],
                     "focus_is_node": s["focus_is_node"],
                     "focus_idx": [idx_of(t) for t in s["focus_tid"]],
                     "prevented": s["prevented"]}
                    for s in after],
                "after_armed_idx": [idx_of(a) for s in after for a in s["armed"]],
                "prevented_all_false": all(
                    s["prevented"] is False for s in fwd + back + after),
            })
            a = rec["arms"][-1]
            print(f"  入场{a['entry']['zeros']} → 末尾{a['at_end']['zeros']} "
                  f"→ 终点{a['endpoint']['zeros']}")
            for i, s in enumerate(a["after_per_press"]):
                print(f"    press{i+1}: 布{s['armed_idx']} "
                      f"焦点落点={s['focus_aria']} 在节点本体={s['focus_is_node']}")
        runs.append(rec)
        print("  仪器已还原")

    out["runs"] = runs
    out["summary"] = [{
        "rep": r["rep"],
        "arms": [{"label": a["label"],
                  "entry_zeros": a["entry"]["zeros"],
                  "at_end_zeros": a["at_end"]["zeros"],
                  "endpoint_zeros": a["endpoint"]["zeros"],
                  "after_armed_idx": a["after_armed_idx"],
                  "after_per_press": a["after_per_press"],
                  "prevented_all_false": a["prevented_all_false"]}
                 for a in r["arms"]],
    } for r in runs]
    out["verdict"] = "sampled"

    # ⚠️ 落盘**必须**排在打印之前
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print("\n== 汇总（只输出读数）==")
    for row in out["summary"]:
        print(f"  rep{row['rep']}")
        for a in row["arms"]:
            print(f"    {a['label']:<18s} 终点{a['endpoint_zeros']} "
                  f"⇒ Tab×8 布 {a['after_armed_idx']}")
    print(f"\n== 已写 {OUT} ==")

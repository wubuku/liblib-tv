#!/usr/bin/env python3
"""batch 906 源站探针：那个**方向不对称**到底是怎么回事？

## 905 留下的两条未验读数

① **首次 `Tab` 从画布根会布 `'0'`**（press1 布 0、落点 `视频 1`），
   而 **902 测到 `Shift+Tab` 从画布根一次都不布** ⇒ **方向不对称**。
   ⚠️ 905 明确标了「这是**读数**、不是机制」——两条测的**不是同一件事**：
   902 测的是「**已经走了一趟之后**从画布根往回」，905 测的是
   「**从未 Tab 过**从画布根往前」⇒ **这本身可能只是入场态不同，不是方向不对称**。

② **布与落点错开一位**：布的决定发生在 **keydown**，落点在**之后**。
   ⇒ 于是「这一次有没有布」到底该跟**按压前**的焦点比，还是跟**按压后**的
   落点比，**两批都没直接量过** ⇒ 905 只能用「上一次按压后的落点」近似。

## 这一批就问这两件事，各给一条能证伪的臂

### A. 把「按压**前**的焦点」直接量出来
`press()` 改成：按之前先读一次 `activeElement`（`aria` + 带不带
`react-flow__node` 类）⇒ 消掉错开一位的近似。

### B. 方向对照臂（`F8` / `B8` / `F8-fresh`）
| 臂 | 入场 | 方向 | 按压 |
|---|---|---|---|
| `F8-fresh` | **从未 Tab 过** | `Tab` | 8 |
| `F8` | 走到末尾＋回走 30 | `Tab` | 8 |
| `B8` | 走到末尾＋回走 30 | **`Shift+Tab`** | 8 |

⇒ `F8` vs `B8` **只差方向**（其余逐字相同）⇒ 方向不对称**成立/不成立**当场可判。
⇒ `F8-fresh` 是 905 `L0` 的复刻，用来确认 6/6 从 0 那条能不能重出。

## 判据纪律

- 仪器**逐字复用** 905（`__b906`）
- **每臂之间 reload**（905 已证明这是必须的）
- 节点总数是易变量 ⇒ 按**身份**记 DOM 序，不钉序号
- 每轮**重复 2 次**；臂序固定
- **落盘排在打印之前**
- ⚠️ 探针**只输出读数**，判读留给基线

## 计费边界

只按 Tab / Shift+Tab、点画布空白。**绝不**点生成/发送/购买/充值，
**也绝不**点音色 chip 本身。

跑法：
  ~/.venvs/liblib-harness/bin/python scripts/jimeng_headless.py run \
      scripts/jimeng_probe906_direction_asymmetry_src.py
"""

import json

OUT = "/tmp/b906-src-direction-asymmetry.json"
REPS = 2
K_BACK = 30
N_PRESS = 8
SETTLE = 300           # 毫秒（901 教训：次数要多，别指望每次都推进指针）

ARMS = [
    {"label": "F8-fresh", "walk_end": False, "back": 0,  "mod": False},
    {"label": "F8",       "walk_end": True,  "back": K_BACK, "mod": False},
    {"label": "B8",       "walk_end": True,  "back": K_BACK, "mod": True},
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

# ⚠️ 仪器逐字来自 905
INSTALL_JS = """() => {
  const root = document.querySelector('.react-flow');
  if (!root) return {ok: false, why: 'no .react-flow root'};
  if (window.__b906) { window.__b906.cleanup(); }
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
  window.__b906 = {
    log, dump: () => log.slice(),
    since: (f) => log.filter(r => r.seq >= f),
    cursor: () => log.length ? log[log.length - 1].seq + 1 : 0,
    cleanup: () => {
      mo.disconnect();
      document.removeEventListener('focusin', onFocusInCap, true);
      document.removeEventListener('keydown', onKey, true);
      document.removeEventListener('keydown', onKeyEnd, false);
      delete window.__b906;
    },
  };
  return {ok: true, n_nodes: document.querySelectorAll('.react-flow__node').length};
}"""

# ⚠️ 仪器逐字来自 905；906 额外用它来读「**按压前**的 activeElement」
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
    """一次按压：**按压前**的焦点 + 布了什么 + 按压后的落点（906 三样齐）。"""
    pre = ev(STATE_JS)["active"]          # ⭐ 906 新增：按压**前**的 activeElement
    cur = ev("() => window.__b906.cursor()")
    pg.keyboard.press("Shift+Tab" if mod else "Tab")
    pg.wait_for_timeout(SETTLE)
    seg = ev("(f) => window.__b906.since(f)", cur)
    armed = [r["target"] for r in seg
             if r["kind"].startswith("attr:")
             and r["value_at_flush"] == '0' and r["oldValue"] != '0']
    fi = [r for r in seg if r["kind"] == "focusin@capture"]
    kd = [r for r in seg if r["kind"] == "keydown@capture"]
    return {"armed": armed,
            # ⭐ 按压**前**的焦点（应用在 keydown 时看到的那一个）
            "pre_aria": pre["aria"][:20], "pre_in_node": pre["in_node"],
            "pre_tid": pre["tid"],
            # 按压**后**的落点
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
# ⚠️ 906 第一版只判一次就报 BLOCKED —— 而实测那次是**偶发加载失败**
#（隔离复跑同一判据在 t+13s 是命中的：button[aria-label="音频"] == 1）⇒
# **一次没命中不等于没登录**。这里**重试一次**再下结论。
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
print(f"== 登录态 {out['logged_in']}（尝试 {out['login_check_attempts']}）==")

if not out["logged_in"]:
    out["verdict"] = "BLOCKED_BY_FIXTURE（登录态没了；**已重试过**）"
    # ⚠️ 906 第一版把落盘写在 else 分支里 ⇒ **被挡的那次连文件都没有**。
    #    **被挡时也要落盘** —— 被挡恰恰是最该留痕的一次 ⇒ 落盘必须在 if/else **之外**。
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"== 已写 {OUT}（BLOCKED 也要落盘）==")
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
                    for _ in range(n + 25):        # 与 902–905 同
                        fwd.append(press(page))
                at_end = snap()
                back = [press(page, mod=True) for _ in range(spec["back"])]
                endpoint = snap()
                blank()
                # ⭐ 方向由 spec["mod"] 决定：F8 用 Tab、B8 用 Shift+Tab
                after = [press(page, mod=spec["mod"]) for _ in range(N_PRESS)]
            finally:
                try:
                    ev("() => { if (window.__b906) { window.__b906.cleanup(); "
                       "return 'cleaned'; } return 'none'; }")
                except Exception as e:          # noqa: BLE001
                    print(f"  !! cleanup 失败：{e}")

            def idx_of(a):
                return names.get(a[4:], {}).get("idx") if a.startswith("tid:") else None

            rec["arms"].append({
                "label": spec["label"], "mod": spec["mod"],
                "entry": entry, "at_end": at_end, "endpoint": endpoint,
                "fwd_armed_count": sum(1 for s in fwd if s["armed"]),
                "back_armed_count": sum(1 for s in back if s["armed"]),
                "after_per_press": [
                    {"armed_idx": [idx_of(a) for a in s["armed"]],
                     "pre_aria": s["pre_aria"], "pre_in_node": s["pre_in_node"],
                     "pre_idx": idx_of(s["pre_tid"]) if s["pre_tid"] else None,
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
                  f"→ 终点{a['endpoint']['zeros']}"
                  f"（fwd布了{a['fwd_armed_count']} back布了{a['back_armed_count']}）")
            for i, s in enumerate(a["after_per_press"]):
                print(f"    press{i+1}: 按前焦点={s['pre_aria']!r}"
                      f" 在节点本体={s['pre_in_node']}"
                      f" ⇒ 布{s['armed_idx']}"
                      f" ⇒ 落点={s['focus_aria']}")
        runs.append(rec)
        print("  仪器已还原")

    out["runs"] = runs
    out["summary"] = [{
        "rep": r["rep"],
        "arms": [{"label": a["label"], "mod": a["mod"],
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
            print(f"    {a['label']:<10s} mod={a['mod']} "
                  f"终点{a['endpoint_zeros']} ⇒ 按 {N_PRESS} 次布 {a['after_armed_idx']}")
    print(f"\n== 已写 {OUT} ==")

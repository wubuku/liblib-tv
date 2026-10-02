#!/usr/bin/env python3
"""batch 902 源站探针：两个 901 **明确拒绝猜**的格子。

## 为什么要专门测这两个

901 把 roving 实现进复刻时，有两处**按 §77 拒绝猜**：

① **`Shift+Tab` 且焦点不在任何节点上**时，源站到底做什么？
   901 的实现是「**什么都不做**」—— 因为**源站这个组合没测过**。

② **指针走到末尾之后**，如果焦点离开画布再回来，它**会不会重置**？
   899 只测到「走到末尾就撒手」；**没测**过「撒手之后回来」。

⇒ 这两个格子不填上，复刻那两处就永远是「猜」。

## 怎么量

复用 900 的仪器（**逐字**），仪器在任何交互**之前**挂上。

### 格 A：点空白（焦点落到画布根，**不在任何节点上**）后连按 `Shift+Tab`

- 源站会不会布 `'0'`？布给**谁**（第一个 / 最后一个 / 干脆不布）？
- 焦点往哪走？
- ⚠️ 关键：**连按几次**都要看 —— 有可能第 1 次不布、第 2 次才布

### 格 B：指针走到末尾 → 走出画布 → 再回到画布根 → 按 `Tab`

- 回来之后按 Tab，布 `'0'` 的是**从头**（下标 0）还是**接着上次**？
  ⇒ 这直接判「指针是**有状态**还是**每次从焦点现算**」

## 判据纪律

- 仪器**逐字复用** 900
- 节点总数是**易变量** ⇒ 按**身份**（`data-testid`）记 DOM 序
- 每轮**重复 2 次**
- **落盘必须排在打印之前**（900 的教训），长输出别进管道
- **诊断动作必须还原**（`finally`）

## 计费边界

只按 Tab / Shift+Tab、点画布空白。
**绝不**点生成/发送/购买/充值，**也绝不**点音色 chip 本身。

跑法：
  ~/.venvs/liblib-harness/bin/python scripts/jimeng_headless.py run \
      scripts/jimeng_probe902_unmeasured_cells_src.py
"""

import json

OUT = "/tmp/b902-src-unmeasured-cells.json"
REPS = 2
BLANK_STEP = 5        # 格 A：连按几次 Shift+Tab
OVERRUN = 25          # 走到末尾用
BACK_OUT = 30         # 往回走出画布

# ⚠️ 逐字来自 900 源站探针
BLANK_JS = """() => {
  for (const [x, y] of [[1300, 1000], [1360, 920], [1220, 1080],
                        [1400, 840], [400, 1080]]) {
    const t = document.elementFromPoint(x, y);
    if (t && t.closest('.react-flow__pane')
        && !t.closest('.react-flow__node')) return [x, y];
  }
  return null;
}"""

DOM_ORDER_JS = """() => [...document.querySelectorAll('.react-flow__node')]
  .map(n => n.getAttribute('data-testid') || '')"""

INSTALL_JS = """() => {
  const root = document.querySelector('.react-flow');
  if (!root) return {ok: false, why: 'no .react-flow root'};
  if (window.__b902) { window.__b902.cleanup(); }
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
                && e.target.getAttribute('aria-label')) || '',
              target_tabindex: e.target.getAttribute
                ? e.target.getAttribute('tabindex') : null});
  };
  const onKey = (e) => {
    log.push({seq: seq++, t: +(performance.now() - t0).toFixed(1),
              kind: 'keydown@capture', key: e.key,
              shift: e.shiftKey, target: ident(e.target), ref: e});
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
  window.__b902 = {
    log, dump: () => log.slice(),
    since: (f) => log.filter(r => r.seq >= f),
    cursor: () => log.length ? log[log.length - 1].seq + 1 : 0,
    cleanup: () => {
      mo.disconnect();
      document.removeEventListener('focusin', onFocusInCap, true);
      document.removeEventListener('keydown', onKey, true);
      document.removeEventListener('keydown', onKeyEnd, false);
      delete window.__b902;
    },
  };
  return {ok: true, n_nodes: document.querySelectorAll('.react-flow__node').length};
}"""

STATE_JS = """() => {
  const nodes = [...document.querySelectorAll('.react-flow__node')];
  const hist = {};
  const zeros = [];
  for (const n of nodes) {
    const ti = n.getAttribute('tabindex');
    const k = ti === null ? 'None' : ti;
    hist[k] = (hist[k] || 0) + 1;
    if (ti === '0') zeros.push(n.getAttribute('data-testid') || '(no-testid)');
  }
  const a = document.activeElement;
  const an = a && a.closest && a.closest('.react-flow__node');
  return {
    n_nodes: nodes.length, hist, zeros, n_zero: zeros.length,
    active: {
      tag: a ? a.tagName : null,
      aria: (a && a.getAttribute && a.getAttribute('aria-label')) || '',
      tid: (a && a.getAttribute && a.getAttribute('data-testid')) || '',
      self_ti: (a && a.getAttribute) ? a.getAttribute('tabindex') : null,
      in_node: !!an,
      node_tid: an ? an.getAttribute('data-testid') : null,
    },
  };
}"""


def ev(js, arg=None):
    return page.evaluate(js) if arg is None else page.evaluate(js, arg)


def step(pg, key, mod=False):
    """按一次键，返回这一步的读数 + 被布 `'0'` 的目标。"""
    cur = ev("() => window.__b902.cursor()")
    pg.keyboard.press("Shift+Tab" if mod else "Tab")
    pg.wait_for_timeout(400)
    seg = ev("(f) => window.__b902.since(f)", cur)
    st = ev(STATE_JS)
    armed = [r["target"] for r in seg
             if r["kind"].startswith("attr:")
             and r["value_at_flush"] == '0' and r["oldValue"] != '0']
    kd = [r for r in seg if r["kind"] == "keydown@capture"]
    fi = [r for r in seg if r["kind"] == "focusin@capture"]
    return {"armed": armed, "n_zero": st["n_zero"], "hist": st["hist"],
            "zeros": st["zeros"], "active": st["active"],
            "prevented": (kd[-1].get("default_prevented") if kd else None),
            "focus_aria_at_focusin": (fi[-1]["target_aria"] if fi else None),
            "focus_is_wrapper_at_focusin": (fi[-1]["target_is_node_wrapper"]
                                            if fi else None)}


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
        page.goto(URL, wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(9000)
        page.set_viewport_size({"width": 1512, "height": 1200})
        page.wait_for_timeout(2500)
        dom = ev(DOM_ORDER_JS)
        n = len(dom)
        rec = {"rep": rep, "n_nodes": n}
        print(f"\n===== rep {rep}（{n} 个节点）=====")
        inst = ev(INSTALL_JS)
        rec["instrument"] = inst
        try:
            # ────────── 格 A：点空白（焦点不在任何节点上）后连按 Shift+Tab ──────────
            spot = ev(BLANK_JS)
            if spot:
                page.mouse.click(spot[0], spot[1])
                page.wait_for_timeout(1200)
            st0 = ev(STATE_JS)
            rec["A_start"] = st0["active"]
            print(f"  [A 起手] 点空白 {spot} ⇒ active tag={st0['active']['tag']} "
                  f"aria={st0['active']['aria']!r} 在节点内={st0['active']['in_node']} "
                  f"n_zero={st0['n_zero']} hist={st0['hist']}")
            a_steps = []
            for i in range(1, BLANK_STEP + 1):
                s = step(page, "Tab", mod=True)
                a_steps.append(s)
                print(f"   A Shift+Tab{i:<2d} 布0={s['armed']} "
                      f"落点={s['active']['aria'][:20]!r} "
                      f"tag={s['active']['tag']} 在节点内={s['active']['in_node']} "
                      f"n_zero={s['n_zero']} prevented={s['prevented']}")
            rec["A"] = a_steps
            rec["A_armed_any"] = any(s["armed"] for s in a_steps)
            rec["A_armed_targets"] = [a for s in a_steps for a in s["armed"]]
            rec["A_armed_idx"] = [dom.index(a[4:]) if a.startswith("tid:")
                                  and a[4:] in dom else None
                                  for a in rec["A_armed_targets"]]

            # ────────── 格 B：Tab 走到末尾 → 走出画布 → 回来再按 Tab ──────────
            # 先回到干净起点：点空白
            spot_b = ev(BLANK_JS)
            if spot_b:
                page.mouse.click(spot_b[0], spot_b[1])
                page.wait_for_timeout(1000)
            rec["B_blank"] = spot_b
            fwd = []
            for _ in range(n + OVERRUN):
                fwd.append(step(page, "Tab"))
            rec["B_fwd_armed_idx"] = [dom.index(a[4:]) if a.startswith("tid:")
                                       and a[4:] in dom else None
                                       for s in fwd for a in s["armed"]]
            last = [x for x in rec["B_fwd_armed_idx"] if x is not None]
            rec["B_last_armed_idx"] = max(last) if last else None
            print(f"  [B 正向] 走到最远下标 {rec['B_last_armed_idx']} / "
                  f"DOM {n - 1}")

            # 往回走出画布：连按足够多次 Shift+Tab
            back = []
            for _ in range(BACK_OUT):
                back.append(step(page, "Tab", mod=True))
            rec["B_back_armed_idx"] = [dom.index(a[4:]) if a.startswith("tid:")
                                       and a[4:] in dom else None
                                       for s in back for a in s["armed"]]
            rec["B_back_final_active"] = back[-1]["active"] if back else None
            print(f"  [B 往回 {BACK_OUT} 次] 布0下标={rec['B_back_armed_idx']}；"
                  f"末步落点={rec['B_back_final_active']}")

            # 再点空白回到画布根（**不在任何节点上**），然后按 Tab —— 判「重置吗」
            spot_c = ev(BLANK_JS)
            if spot_c:
                page.mouse.click(spot_c[0], spot_c[1])
                page.wait_for_timeout(1000)
            rec["B_reblank"] = spot_c
            stc = ev(STATE_JS)
            rec["B_before_reentry"] = {"active": stc["active"],
                                       "n_zero": stc["n_zero"],
                                       "zeros": stc["zeros"]}
            print(f"  [B 回来] 再点空白 {spot_c} ⇒ active tag="
                  f"{stc['active']['tag']} 在节点内={stc['active']['in_node']} "
                  f"n_zero={stc['n_zero']} 0 在 {stc['zeros']}")
            re_tab = [step(page, "Tab") for _ in range(3)]
            rec["B_reentry_tab"] = re_tab
            rec["B_reentry_armed_idx"] = [
                dom.index(a[4:]) if a.startswith("tid:") and a[4:] in dom
                else None for s in re_tab for a in s["armed"]]
            print(f"  [B 回来后按 Tab ×3] 布0下标={rec['B_reentry_armed_idx']}"
                  f"（若是**重置**⇒ 第一次应是 0）")
        finally:
            try:
                ev("() => { if (window.__b902) { window.__b902.cleanup(); "
                   "return 'cleaned'; } return 'none'; }")
            except Exception as e:      # noqa: BLE001
                print(f"  !! cleanup 失败：{e}")
            print("  仪器已还原")
        runs.append(rec)

    out["runs"] = runs
    out["summary"] = [{
        "rep": r["rep"],
        "n_nodes": r["n_nodes"],
        "A_start_in_node": r["A_start"]["in_node"],
        "A_armed_any": r["A_armed_any"],
        "A_armed_idx": r["A_armed_idx"],
        "A_n_zero_each": [s["n_zero"] for s in r["A"]],
        "A_prevented": [s["prevented"] for s in r["A"]],
        "B_last_armed_idx": r["B_last_armed_idx"],
        "B_back_armed_idx": r["B_back_armed_idx"],
        "B_reblank_in_node": r["B_before_reentry"]["active"]["in_node"],
        "B_reentry_armed_idx": r["B_reentry_armed_idx"],
    } for r in runs]
    out["verdict"] = "sampled"

    # ⚠️ 落盘**必须**排在打印之前（900 的教训）
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print("\n== 汇总（两个格子）==")
    for s in out["summary"]:
        print(f"  rep{s['rep']}（{s['n_nodes']} 个节点）")
        print(f"    格A 起手时焦点在节点内？{s['A_start_in_node']}；"
              f"连按 Shift+Tab 有没有布 0？**{s['A_armed_any']}** "
              f"（布给 {s['A_armed_idx']}）；"
              f"n_zero 逐次={s['A_n_zero_each']}；"
              f"prevented={s['A_prevented']}")
        print(f"    格B 正向走到 {s['B_last_armed_idx']}；"
              f"往回 {len(s['B_back_armed_idx'])} 次布0下标="
              f"{s['B_back_armed_idx']}；再点空白后按 Tab×3 布0下标="
              f"**{s['B_reentry_armed_idx']}**")
    print(f"\n== 已写 {OUT} ==")

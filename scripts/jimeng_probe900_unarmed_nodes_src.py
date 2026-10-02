#!/usr/bin/env python3
"""batch 900 源站探针：那 2 个**整轮没被布上 `'0'`** 的节点，为什么？

## 要解释的现象（899 实测，各 2/2，两轮完全一致）

DOM 序共 76 个节点，连按 Tab **节点数 + 25** 次：

- 被布上 `'0'` 的下标：`[0,1,…,11, 13,14,…,75]` ⇒ **下标 12 与 68 从没被布过**
- 下标 12 = `图片 node: b22-upload`（`react-flow__node-image`）——
  **焦点第 17 步走到过它**，但它**从没被布上 `'0'`**
- 下标 68 = `音频 node: 音频 61`（`react-flow__node-audio`）——
  焦点**也没**到过它
- 两轮**完全一致** ⇒ **不是随机**

## 这一批要分清的三件事

① **它们在不在应用的「节点表」里？**
   896 实测**第一次** Tab 时，应用给**其余每个**节点都写了 `tabindex='-1'`
   ⇒ 如果这 2 个也在那次里被写了 `-1`，说明它们**在表里、只是不被选中**；
   如果**连 `-1` 都没写**，那它们压根不在表里（是 DOM 里多出来的）。

② **它们和别的节点有什么结构上的不同？**
   把 76 个节点的**完整指纹**读出来（属性集 / 类 / 父链 / 所在容器 /
   `data-id` 形态 / 有没有 `parentId` / 尺寸），标出**离群**的那些。
   ⇒ 找**它们独有的**属性，而不是猜原因。

③ **往回走（Shift+Tab）也跳过它们吗？**
   若是 ⇒ 排除「只是某一侧算错」；若不是 ⇒ 说明正反两套逻辑不一样。

## ⚠️ 纪律

- **不许编机制**：这一批只负责「把差异钉到某个具体属性上」，
  **钉不到就写「仍未查明」**，**不许**拿「读数能这么解释」当结论（891 的教训）
- 仪器 `INSTALL_JS` **逐字复用** 896
- 节点总数是**易变量**（同 URL 逐轮 74→75→76→77）⇒ 按**身份**
  （`data-testid` / `aria-label`）记录，**不钉**个数
- 每轮**重复 2 次**；诊断动作**必须还原**
- **只读 DOM + 按 Tab/Shift+Tab + 点空白**。
  **绝不**点生成/发送/购买/充值，**也绝不**点音色 chip 本身

跑法：
  ~/.venvs/liblib-harness/bin/python scripts/jimeng_headless.py run \
      scripts/jimeng_probe900_unarmed_nodes_src.py
"""

import json

OUT = "/tmp/b900-src-unarmed-nodes.json"
REPS = 2
FWD_STEPS = 30         # 走过头一点，确保覆盖到下标 12 与 68
BACK_STEPS = 30

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

# ══ ① 指纹：把每个节点的**结构特征**读全，用来找「离群」 ══
FINGERPRINT_JS = """() => [...document.querySelectorAll('.react-flow__node')].map((n, i) => {
  const attrs = {};
  for (const a of n.attributes) attrs[a.name] = a.value;
  // 父链（到 .react-flow 为止），看有没有**套在别的节点里**
  const parents = [];
  let p = n.parentElement;
  while (p && !p.classList.contains('react-flow')) {
    parents.push(p.tagName + (p.className
      ? '.' + String(p.className).split(/\\s+/).filter(Boolean).slice(0,2).join('.')
      : ''));
    p = p.parentElement;
  }
  const r = n.getBoundingClientRect();
  return {
    dom_idx: i,
    tid: n.getAttribute('data-testid') || '',
    data_id: n.getAttribute('data-id') || '',
    kind: [...n.classList].find(c => c.startsWith('react-flow__node-')
          && c !== 'react-flow__node') || '?',
    aria: n.getAttribute('aria-label') || '',
    tabindex: n.getAttribute('tabindex'),
    classes: [...n.classList],
    attr_names: Object.keys(attrs).sort(),
    parent_chain: parents,
    // 有没有「父节点」语义（react-flow 的子节点会被套在父节点 DOM 里）
    in_another_node: !!n.parentElement
      && !!n.parentElement.closest('.react-flow__node'),
    rect: {w: Math.round(r.width), h: Math.round(r.height),
           x: Math.round(r.x), y: Math.round(r.y)},
    n_descendants: n.querySelectorAll('*').length,
    n_buttons: n.querySelectorAll('button').length,
    n_focusable: n.querySelectorAll(
      'a[href],button,input,select,textarea,[tabindex]').length,
    hidden: n.offsetParent === null,
  };
})"""

# ══ 仪器：**逐字复用 896** ══
INSTALL_JS = """() => {
  const root = document.querySelector('.react-flow');
  if (!root) return {ok: false, why: 'no .react-flow root'};
  if (window.__b900) { window.__b900.cleanup(); }
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
              kind: 'keydown@capture', key: e.key,
              target: ident(e.target), ref: e});
  };
  const onKeyEnd = (e) => {
    const rec = log.find(r => r.ref === e);
    if (rec) { rec.default_prevented = e.defaultPrevented;
               rec.key = e.key; delete rec.ref; }
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
  window.__b900 = {
    log, dump: () => log.slice(),
    since: (f) => log.filter(r => r.seq >= f),
    cursor: () => log.length ? log[log.length - 1].seq + 1 : 0,
    cleanup: () => {
      mo.disconnect();
      document.removeEventListener('focusin', onFocusInCap, true);
      document.removeEventListener('keydown', onKey, true);
      document.removeEventListener('keydown', onKeyEnd, false);
      delete window.__b900;
    },
  };
  return {ok: true, n_nodes: document.querySelectorAll('.react-flow__node').length};
}"""


def ev(js, arg=None):
    return page.evaluate(js) if arg is None else page.evaluate(js, arg)


def armed_of(seg):
    return [r for r in seg
            if r["kind"].startswith("attr:")
            and r["value_at_flush"] == '0' and r["oldValue"] != '0']


def written_of(seg):
    """这一步里**所有**被写过 tabindex 的目标（不管写成什么值）。"""
    return [r["target"] for r in seg if r["kind"].startswith("attr:")]


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
        fp = ev(FINGERPRINT_JS)
        rec = {"rep": rep, "n_nodes": len(dom), "fingerprints": fp}
        print(f"\n===== rep {rep}：{len(dom)} 个节点 =====")

        # ── 指纹里先找「离群」：和大多数节点不一样的结构特征 ──
        from collections import Counter
        attr_sets = Counter(tuple(f["attr_names"]) for f in fp)
        common = attr_sets.most_common(1)[0][0] if attr_sets else ()
        outliers = [f for f in fp if tuple(f["attr_names"]) != common]
        rec["most_common_attr_set"] = list(common)
        rec["attr_set_histogram"] = {"|".join(k): v for k, v in attr_sets.items()}
        rec["attr_set_outliers"] = [
            {k: f[k] for k in ("dom_idx", "tid", "kind", "aria",
                               "attr_names", "parent_chain",
                               "in_another_node", "n_focusable",
                               "n_buttons", "rect", "hidden")}
            for f in outliers]
        print(f"  最常见的属性集（{attr_sets.most_common(1)[0][1]} 个节点）："
              f"{list(common)}")
        print(f"  **属性集离群的 {len(outliers)} 个**：")
        for f in outliers:
            print(f"     下标{f['dom_idx']:<3d} {f['kind']:<26s} "
                  f"aria={f['aria'][:24]!r:<26s} 独有属性="
                  f"{sorted(set(f['attr_names']) - set(common))} "
                  f"父链={f['parent_chain']}")

        # ── ① 它们在不在应用的节点表里？看**第一次** Tab 写了谁 ──
        inst = ev(INSTALL_JS)
        rec["instrument"] = inst
        try:
            spot = ev(BLANK_JS)
            if spot:
                page.mouse.click(spot[0], spot[1])
                page.wait_for_timeout(1200)
            rec["blank_spot"] = spot

            cur = ev("() => window.__b900.cursor()")
            page.keyboard.press("Tab")
            page.wait_for_timeout(500)
            seg1 = ev("(f) => window.__b900.since(f)", cur)
            w1 = written_of(seg1)
            a1 = armed_of(seg1)
            rec["first_tab"] = {
                "n_written": len(w1),
                "armed": [r["target"] for r in a1],
                "written_targets": w1,
            }
            print(f"\n  [第一次 Tab] 写了 tabindex 的目标 {len(w1)} 个 / "
                  f"共 {len(dom)} 个节点；布 0 的是 {rec['first_tab']['armed']}")
            miss = [t for t in dom
                    if ("tid:" + t) not in w1]
            rec["first_tab"]["not_written"] = miss
            print(f"     **没被写到**的：{miss if miss else '（无 —— 全部都被写了）'}")

            # ── ② 正向走到 30 步，看谁被布 0 ──
            fwd = []
            for _ in range(FWD_STEPS - 1):
                cur = ev("() => window.__b900.cursor()")
                page.keyboard.press("Tab")
                page.wait_for_timeout(350)
                seg = ev("(f) => window.__b900.since(f)", cur)
                fi = [r for r in seg if r["kind"] == "focusin@capture"]
                fwd.append({
                    "armed": [r["target"] for r in armed_of(seg)],
                    "focus_aria": (fi[-1]["target_aria"] if fi else None),
                    "focus_is_wrapper": (fi[-1]["target_is_node_wrapper"]
                                         if fi else None),
                })
            rec["fwd"] = fwd
            armed_fwd = [a[4:] if a.startswith("tid:") else a
                         for s in fwd for a in s["armed"]]
            rec["armed_fwd"] = armed_fwd
            rec["armed_fwd_idx"] = [dom.index(t) if t in dom else None
                                    for t in armed_fwd]
            print(f"\n  [正向 {FWD_STEPS} 步] 布 0 的 DOM 下标："
                  f"{rec['armed_fwd_idx']}")

            # ── ③ 往回走：Shift+Tab 也跳过它们吗 ──
            back = []
            for _ in range(BACK_STEPS):
                cur = ev("() => window.__b900.cursor()")
                page.keyboard.press("Shift+Tab")
                page.wait_for_timeout(350)
                seg = ev("(f) => window.__b900.since(f)", cur)
                fi = [r for r in seg if r["kind"] == "focusin@capture"]
                back.append({
                    "armed": [r["target"] for r in armed_of(seg)],
                    "focus_aria": (fi[-1]["target_aria"] if fi else None),
                })
            rec["back"] = back
            armed_back = [a[4:] if a.startswith("tid:") else a
                          for s in back for a in s["armed"]]
            rec["armed_back_idx"] = [dom.index(t) if t in dom else None
                                     for t in armed_back]
            print(f"  [往回 {BACK_STEPS} 步] 布 0 的 DOM 下标："
                  f"{rec['armed_back_idx']}")

            # ── 汇总：正向/反向都从没被布过的 ──
            never_f = [i for i in range(len(dom))
                       if i not in set(x for x in rec["armed_fwd_idx"]
                                       if x is not None)]
            never_b = [i for i in range(len(dom))
                       if i not in set(x for x in rec["armed_back_idx"]
                                       if x is not None)]
            rec["never_armed_fwd_idx"] = never_f
            rec["never_armed_back_idx"] = never_b
            rec["never_armed_both_idx"] = sorted(set(never_f) & set(never_b))
            rec["never_armed_both_nodes"] = [fp[i] for i in
                                             rec["never_armed_both_idx"]]
            print(f"\n  正向从没被布 0 的下标：{never_f}")
            print(f"  反向从没被布 0 的下标：{never_b}")
            print(f"  **正反都从没被布 0 的**：{rec['never_armed_both_idx']}")
            for f in rec["never_armed_both_nodes"]:
                print(f"     下标{f['dom_idx']} {f['kind']} aria={f['aria']!r}")
        finally:
            try:
                ev("() => { if (window.__b900) { window.__b900.cleanup(); "
                   "return 'cleaned'; } return 'none'; }")
            except Exception as e:      # noqa: BLE001
                print(f"  !! cleanup 失败：{e}")
            print("  仪器已还原")

        runs.append(rec)

    out["runs"] = runs
    out["summary"] = [{
        "rep": r["rep"],
        "n_nodes": r["n_nodes"],
        "n_attr_set_outliers": len(r["attr_set_outliers"]),
        "first_tab_n_written": r["first_tab"]["n_written"],
        "first_tab_not_written": r["first_tab"]["not_written"],
        "never_armed_both_idx": r["never_armed_both_idx"],
        "never_armed_both_nodes": [
            {k: f[k] for k in ("dom_idx", "tid", "kind", "aria",
                               "attr_names", "parent_chain",
                               "in_another_node", "n_focusable",
                               "n_buttons", "rect")}
            for f in r["never_armed_both_nodes"]],
    } for r in runs]

    # ⚠️⚠️ **先落盘、再打印**。第一版把 `print(json.dumps(summary))` 放在写文件
    # **之前**，而这批的输出是**管道给 `tail`** 的 ⇒ 打印一大坨 JSON 时
    # `tail` 早就退出、管道写不进去 ⇒ `BlockingIOError` ⇒ **探针在最后一步炸掉、
    # 连文件都没写**。⇒ 教训：**长输出要么落盘、要么别进管道**；
    # 任何情况下**落盘必须排在打印之前**，否则一次 stdout 事故就带走整轮数据。
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print("\n== 汇总（紧凑版；完整数据看文件）==")
    for s in out["summary"]:
        print(f"  rep{s['rep']}: n={s['n_nodes']} "
              f"属性集离群={s['n_attr_set_outliers']} "
              f"第一次Tab写了={s['first_tab_n_written']} 个、"
              f"没写到={s['first_tab_not_written']}")
        print(f"          正反都从没被布 0 的下标："
              f"{s['never_armed_both_idx']}")
        for f2 in s["never_armed_both_nodes"]:
            print(f"            下标{f2['dom_idx']} {f2['kind']} "
                  f"aria={f2['aria']!r} "
                  f"独有属性={sorted(set(f2['attr_names']))} "
                  f"父链={f2['parent_chain'][:2]} "
                  f"可聚焦子孙={f2['n_focusable']} "
                  f"尺寸={f2['rect']['w']}x{f2['rect']['h']}")
    print(f"\n== 已写 {OUT} ==")
    out["verdict"] = "sampled"

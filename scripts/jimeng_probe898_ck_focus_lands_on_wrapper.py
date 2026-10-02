#!/usr/bin/env python3
"""batch 898 复刻探针：焦点落点**是不是节点 wrapper 自身**？

## 这一批要分清的一件事

897 留下的坑：那 16 步 Tab 走查里，**没有**一步的落点写成节点 wrapper 的
aria，但 `node_ti='0'` 只说明「焦点所在的那个**最近节点祖先**是 `'0'`」——
**分不出**焦点在 wrapper **自身**、还是在它**内层**的某个控件上。

源站那一侧 **896 的日志已经答了**：`document.activeElement` **就是**节点
wrapper 本身（18/18 条 `focusin@capture` 的落点与 `activeElement` 是同一个
元素，且那些 `tid:rf__node-node_*` 就是 wrapper）。

⇒ 这一批量**复刻**侧，回答同一个问题。

## 为什么这个必须先分清

要按源站实现 roving（下一批），得知道「Tab 落点」是**节点本体**还是
**节点内层控件**——两者的 roving 写法完全不同（布 `0` 给谁、算「下一个」时
跳过什么）。**分不清就动手 = 照着猜的机制写实现。**

## 顺手修掉 897 的取点问题

897 失败在：左栏 `insertAtCenter` 把新节点**全插在画布中心**，五个叠在一起，
算出来的中心点落在**最上层那个**身上 ⇒ 四种类型点不到本体。

⇒ 这一批**插一个、量一个、再插下一个**（新节点必然在最上层）⇒ 每个类型
都能拿到自己的本体读数。**不是**去 hack 坐标。

## 纪律

- 每轮**重复 2 次**（一次成功不叫可靠）；每轮**从刚载完**开始
- 点之前先 `elementFromPoint` **验落点确实是本节点**，对不上就**跳过并记录**
  （**不许**硬点、不许改坐标硬凑）
- **只读 DOM，不挂监听器、不劫持任何东西**
- 钉**关系**（落点是不是 wrapper 本身 / 直方图），**不钉**节点总数/序号
- ⚠️ 判据 `STATE_JS` **逐字复用** 896（那个直方图是区分 roving 的唯一判据）

## 计费边界

只点左栏**插入**入口、点画布空白、点节点本体、按 Tab。
**绝不**点生成/发送/购买/充值，**也绝不**点音色 chip 本身。

跑法：
  /opt/miniconda3/bin/python3 -u scripts/jimeng_probe898_ck_focus_lands_on_wrapper.py
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://localhost:4317/jimeng/canvas/demo"
OUT = Path("/tmp/b898-ck-focus-on-wrapper.json")
REPS = 2
KINDS = [
    ("文本", "text"),
    ("图片", "image"),
    ("时间线", "timeline"),
    ("主体", "subject"),
    ("导演台", "director"),
]

# ⚠️⚠️ 以下 JS **逐字来自 896 源站探针**，不许「顺手优化」——
# 判据不同就量出了「不同」，而那只是判据不同（890c 的教训）。
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

# ★ 本批新增：直接量「activeElement **是不是等于**那个 wrapper」
IDENT_JS = """() => {
  const a = document.activeElement;
  const wrap = a && a.closest && a.closest('.react-flow__node');
  const tid = (e) => (e && e.getAttribute
    ? e.getAttribute('data-testid') : null) || '';
  return {
    active_tag: a ? a.tagName : null,
    active_tid: tid(a),
    active_aria: (a && a.getAttribute && a.getAttribute('aria-label')) || '',
    active_testid: tid(a),
    active_is_wrapper: !!(wrap && a === wrap),   // ★ 就是这一行在回答问题
    nearest_node_tid: tid(wrap),
    nearest_node_ti: wrap ? wrap.getAttribute('tabindex') : null,
  };
}"""

TIDS_JS = """() => [...document.querySelectorAll('.react-flow__node')]
  .map(n => n.getAttribute('data-testid') || '')"""

CENTER_JS = """(tid) => {
  const n = document.querySelector(`.react-flow__node[data-testid="${tid}"]`);
  if (!n) return null;
  const r = n.getBoundingClientRect();
  return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
}"""

HIT_JS = """([x, y]) => {
  const t = document.elementFromPoint(x, y);
  const n = t && t.closest && t.closest('.react-flow__node');
  return n ? (n.getAttribute('data-testid') || '') : null;
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

# ★★ 直接读「Tab 序列」本身，而不是靠走查去撞。
# 898 第一版的教训：12 步走查 24/24 都没落在 wrapper 上，看着像「wrapper Tab
# 不到」—— 其实**是起走点在最后一个节点内部**，往前走出去就再也回不来了。
# 「走查没走到」**不等于**「走不到」；要证「走不到」得直接读序列。
SEQ_JS = """() => {
  const SEL = 'a[href],button,input,select,textarea,'
             + '[tabindex]:not([tabindex="-1"])';
  const all = [...document.querySelectorAll(SEL)];
  const rows = all.map((e, i) => {
    const wrap = e.closest && e.closest('.react-flow__node');
    return {i,
      is_wrapper: !!(wrap && e === wrap),
      in_node: !!wrap,
      tag: e.tagName,
      tid: (e.getAttribute && e.getAttribute('data-testid')) || '',
      aria: ((e.getAttribute && e.getAttribute('aria-label')) || '').slice(0, 18),
      ti: e.getAttribute ? e.getAttribute('tabindex') : null};
  });
  return {total: all.length, rows,
          wrapper_indices: rows.filter(r => r.is_wrapper).map(r => r.i)};
}"""


def main() -> int:
    url = os.environ.get("SNAP_URL", URL)
    res: dict = {"url": url, "runs": []}
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_context(viewport={"width": 1680, "height": 1050}).new_page()
        for rep in range(1, REPS + 1):
            pg.goto(url, wait_until="domcontentloaded", timeout=60000)
            time.sleep(4.0)
            rec: dict = {"rep": rep, "kinds": {}, "tab_walk": []}

            def ev(js, arg=None):
                return pg.evaluate(js) if arg is None else pg.evaluate(js, arg)

            print(f"\n===== rep {rep} =====")

            # ── 先直接读 Tab 序列本身（中性态，别等插完节点）──
            seq0 = ev(SEQ_JS)
            rec["seq_neutral"] = {"total": seq0["total"],
                                  "wrapper_indices": seq0["wrapper_indices"]}
            print(f"  [seq_neutral] 可聚焦序列共 {seq0['total']} 项；"
                  f"其中**就是 wrapper 本身**的下标 = {seq0['wrapper_indices']}")
            for r in seq0["rows"][:10]:
                print(f"     #{r['i']:<3d} wrap={r['is_wrapper']!s:<5s} "
                      f"{r['tag']:<8s} ti={r['ti']!r:<5} "
                      f"{r['tid'][:26]:26s} {r['aria']}")

            # ── 逐类型：插一个、量一个（897 之所以点不到，就是因为全叠着）──
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
                entry: dict = {"label": label, "insert_ok": ok, "tid": tid}
                if not tid:
                    entry["verdict"] = "前置态没成立：这一轮插不进 ⇒ 不测"
                    rec["kinds"][kind] = entry
                    print(f"  [{kind}] !! 插不进，本条件不测")
                    continue

                xy = ev(CENTER_JS, tid)
                hit = ev(HIT_JS, xy) if xy else None
                entry["center"] = xy
                entry["hit_at_center"] = hit
                if hit != tid:
                    entry["verdict"] = f"落点不是本节点（{hit}）⇒ 跳过"
                    rec["kinds"][kind] = entry
                    print(f"  [{kind}] !! 跳过：落点 {hit} != {tid}")
                    continue

                # 点本体，看焦点落点是不是 wrapper **自身**
                pg.mouse.click(xy[0], xy[1])
                time.sleep(1.2)
                ident = ev(IDENT_JS)
                st = ev(STATE_JS)
                entry["ident"] = ident
                entry["hist"] = st["hist"]
                entry["n_zero"] = st["n_zero"]
                entry["all_nodes_zero"] = st["n_zero"] == st["n_nodes"]
                rec["kinds"][kind] = entry
                print(f"  [{kind}] 点本体后：active_tag={ident['active_tag']} "
                      f"active_tid={ident['active_tid']} "
                      f"**落点==wrapper 本身？{ident['active_is_wrapper']}** "
                      f"hist={entry['hist']}")
        # 继续跑后半段（缩进保持在 rep 循环内）
            # ── 插完之后再读一次序列：新节点的 wrapper 有没有进去？──
            seq1 = ev(SEQ_JS)
            rec["seq_after_insert"] = {
                "total": seq1["total"],
                "wrapper_indices": seq1["wrapper_indices"]}
            print(f"  [seq_after_insert] 共 {seq1['total']} 项；"
                  f"wrapper 下标 = {seq1['wrapper_indices']}")

            # ── 走查①：从**刚点过的节点内部**起走（复现 897/898 第一版的起点）──
            for i in range(1, 13):
                pg.keyboard.press("Tab")
                time.sleep(0.25)          # ← **秒**（895 踩过毫秒/秒的坑）
                ident = ev(IDENT_JS)
                st = ev(STATE_JS)
                rec["tab_walk"].append({
                    "i": i,
                    "active_tag": ident["active_tag"],
                    "active_aria": ident["active_aria"],
                    "active_tid": ident["active_tid"],
                    "active_is_wrapper": ident["active_is_wrapper"],
                    "nearest_node_tid": ident["nearest_node_tid"],
                    "nearest_node_ti": ident["nearest_node_ti"],
                    "n_zero": st["n_zero"],
                    "n_nodes": st["n_nodes"],
                    "all_nodes_zero": st["n_zero"] == st["n_nodes"],
                })
                w = rec["tab_walk"][-1]
                print(f"     Tab{i:<2d} {str(ident['active_aria'])[:24]:24s} "
                      f"tid={ident['active_tid']} "
                      f"落点==wrapper？{ident['active_is_wrapper']} "
                      f"n_zero={st['n_zero']}/{st['n_nodes']} "
                      f"全0？{st['n_zero'] == st['n_nodes']}")

            # ── 走查②：先点空白、**从画布外**起走 ——
            #    这才是和源站 896 **同一起点**的对比（896 也是点空白后起走）。
            spot = ev(BLANK_JS)
            if spot:
                pg.mouse.click(spot[0], spot[1])
                time.sleep(1.2)
            rec["blank_spot"] = spot
            after_blank = ev(IDENT_JS)
            rec["after_blank_ident"] = after_blank
            print(f"  [after_blank] 落点 {spot} ⇒ active_tag="
                  f"{after_blank['active_tag']} "
                  f"tid={after_blank['active_tid']} "
                  f"落点==wrapper？{after_blank['active_is_wrapper']}")
            walk2 = []
            for i in range(1, 13):
                pg.keyboard.press("Tab")
                time.sleep(0.25)          # ← **秒**（895 踩过毫秒/秒的坑）
                ident = ev(IDENT_JS)
                st = ev(STATE_JS)
                walk2.append({
                    "i": i,
                    "active_aria": ident["active_aria"],
                    "active_tid": ident["active_tid"],
                    "active_is_wrapper": ident["active_is_wrapper"],
                    "nearest_node_tid": ident["nearest_node_tid"],
                    "nearest_node_ti": ident["nearest_node_ti"],
                    "n_zero": st["n_zero"], "n_nodes": st["n_nodes"],
                    "all_nodes_zero": st["n_zero"] == st["n_nodes"],
                })
                w = walk2[-1]
                print(f"     (空白起)Tab{i:<2d} {str(ident['active_aria'])[:22]:22s} "
                      f"tid={ident['active_tid']} "
                      f"落点==wrapper？{ident['active_is_wrapper']} "
                      f"全0？{st['n_zero'] == st['n_nodes']}")
            rec["tab_walk_from_blank"] = walk2

            res["runs"].append(rec)

        b.close()

    # ── 汇总：钉关系，不钉序号/总数 ──
    summ: dict = {}
    for _, kind in KINDS:
        rows = []
        for r in res["runs"]:
            e = r["kinds"].get(kind) or {}
            rows.append({
                "insert_ok": e.get("insert_ok"),
                "skipped": bool(e.get("verdict")),
                "active_is_wrapper": (e.get("ident") or {}).get(
                    "active_is_wrapper"),
                "all_nodes_zero": e.get("all_nodes_zero"),
            })
        summ[kind] = rows
    res["summary"] = summ
    res["tab_walk_on_wrapper"] = [
        [w["active_is_wrapper"] for w in r["tab_walk"]] for r in res["runs"]]
    res["tab_walk_all_zero"] = [
        all(w["all_nodes_zero"] for w in r["tab_walk"]) for r in res["runs"]]
    res["tab_walk_from_blank_on_wrapper"] = [
        [w["active_is_wrapper"] for w in r.get("tab_walk_from_blank", [])]
        for r in res["runs"]]
    res["wrapper_indices_neutral"] = [
        r.get("seq_neutral", {}).get("wrapper_indices") for r in res["runs"]]
    res["wrapper_indices_after_insert"] = [
        r.get("seq_after_insert", {}).get("wrapper_indices") for r in res["runs"]]

    print("\n== 汇总 ==")
    for kind, rows in summ.items():
        print(f"  {kind}: " + " | ".join(
            f"插入后点本体→落点==wrapper?{r['active_is_wrapper']}"
            f"{'(跳过)' if r['skipped'] else ''}" for r in rows))
    print(f"\n  中性态 Tab 序列里 wrapper 的下标  ：{res['wrapper_indices_neutral']}")
    print(f"  插完节点后 wrapper 的下标        ：{res['wrapper_indices_after_insert']}")
    print(f"  走查①（节点内部起走）落点==wrapper：{res['tab_walk_on_wrapper']}")
    print(f"  走查②（**空白起走**）落点==wrapper：{res['tab_walk_from_blank_on_wrapper']}")
    print(f"  走查①全程「所有节点都是 0」      ：{res['tab_walk_all_zero']}")
    res["verdict"] = "sampled"

    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print(f"\n== 已写 {OUT} ==")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

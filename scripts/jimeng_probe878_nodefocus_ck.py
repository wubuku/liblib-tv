#!/usr/bin/env python3
"""batch 878（复刻侧）：Clear 上按 Esc，焦点落点 `body` —— 缺陷还是夹具？

## 这条差异是哪来的

§93 范围限制第 2 条：

> 源站 Clear 上 Esc 之后焦点落在 **音频节点本体**
> （`BUTTON/'音频 node: 音频 37'`）；复刻落在 **body**。
> **未修**。要判它是缺陷还是夹具，得先量一件事：
> **复刻画布上的节点到底能不能被聚焦。**

这不是猜的，是判定的**必要前提**：

- 若节点**不可聚焦** ⇒ 面板卸载后焦点除了 body **无处可去**，
  `body` 是**必然**结果而不是实现疏忽 ⇒ 记「夹具差异」
- 若节点**可聚焦** ⇒ 焦点掉 body 就是**真缺陷**
  （873 修 Y.4 用的就是这个理由：「面板一卸焦点掉到 body 是最坏落点，
  键盘用户完全不知道自己在哪」）

⚠️ **先量再判**（§77 机制未验死之前不许改判据）。本探针只量复刻侧，
不碰源站、不改产品。

## 量三件事

① 画布上每个节点的 `tabIndex`（属性与 DOM 属性两种读法）
② 每个节点**程序化** `focus()` 之后，`activeElement` 是不是它
③ Tab 走 40 步，轨迹里**有没有落到节点上**（Tab 序列里有没有节点）

第 ③ 项是关键：能被 `focus()` 不等于在 Tab 序列里。
源站的节点是 `BUTTON`（aria `音频 node: 音频 37`）——**按钮**，
按钮天生在 Tab 序列里。复刻的节点是什么，得量。

跑法：`/opt/miniconda3/bin/python3 scripts/jimeng_probe878_nodefocus_ck.py`
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://localhost:4317/jimeng/canvas/demo"
OUT = Path("/tmp/b878-ck-nodefocus.json")

# 一个节点的全部身份信息
NODE_JS = """() => {
  const out = [];
  for (const n of document.querySelectorAll('.react-flow__node')) {
    const r = n.getBoundingClientRect();
    out.push({
      tid: n.getAttribute('data-testid') || '',
      tag: n.tagName,
      attr_tabindex: n.getAttribute('tabindex'),
      prop_tabIndex: n.tabIndex,
      aria: n.getAttribute('aria-label') || '',
      role: n.getAttribute('role') || '',
      rect: [Math.round(r.x), Math.round(r.y),
             Math.round(r.width), Math.round(r.height)],
      /* 节点里**可聚焦的后代**有几个 —— 有的话 Tab 可能从那儿过 */
      n_focusable: n.querySelectorAll(
        'button,[href],input,select,textarea,[tabindex]').length});
  }
  return out;
}"""

# 程序化聚焦某个节点，读 activeElement（**不发 click**）
FOCUS_NODE_JS = """(tid) => {
  const n = document.querySelector(`.react-flow__node[data-testid="${tid}"]`);
  if (!n) return {no_node: true};
  const before = document.activeElement;
  const before_aria = before && before.getAttribute
    ? (before.getAttribute('aria-label') || before.tagName) : '?';
  n.focus();
  const a = document.activeElement;
  return {before_aria,
          focused_ok: a === n,
          focus_aria: a.getAttribute
            ? (a.getAttribute('aria-label') || a.tagName) : '?',
          fell_to_body: a === document.body};
}"""

FOCUS_JS = """() => { const a = document.activeElement;
  if (a === document.body) return {tag: 'BODY', aria: '(body)'};
  return {tag: a.tagName,
          aria: a.getAttribute('aria-label') || '',
          in_node: !!a.closest('.react-flow__node'),
          in_toolbar: !!a.closest('.react-flow__node-toolbar')}; }"""


def main() -> int:
    url = os.environ.get("SNAP_URL", URL)
    res: dict = {"url": url}
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_context(viewport={"width": 1680, "height": 1050}).new_page()
        pg.goto(url, wait_until="domcontentloaded", timeout=60000)
        time.sleep(4)

        # 插几个节点，量**不止一种**节点（别拿一个代表全部）
        for label in ("音频", "文本", "图片"):
            t = pg.locator(f'button[aria-label="{label}"]')
            if t.count():
                try:
                    t.first.click(timeout=6000)
                    time.sleep(1.6)
                except Exception:
                    pass
        time.sleep(1.0)

        nodes = pg.evaluate(NODE_JS)
        res["n_nodes"] = len(nodes)
        res["nodes"] = nodes
        print(f"== 画布节点 {len(nodes)} 个 ==")
        for n in nodes:
            print(f"   {n['tag']:8s} tabindex={n['attr_tabindex']!r}/"
                  f"{n['prop_tabIndex']} role={n['role']!r} "
                  f"aria={n['aria'][:22]!r} 可聚焦后代={n['n_focusable']}")

        # ② 程序化聚焦
        foc = []
        for n in nodes:
            if not n["tid"]:
                continue
            r = pg.evaluate(FOCUS_NODE_JS, n["tid"])
            foc.append({"tid": n["tid"], **r})
            print(f"\n   focus {n['tid'][:26]!r}："
                  f"成功={r.get('focused_ok')} "
                  f"焦点={r.get('focus_aria')!r} "
                  f"掉body={r.get('fell_to_body')}")
        res["focus"] = foc
        res["n_focusable"] = sum(1 for f in foc if f.get("focused_ok"))
        print(f"\n== 节点程序化可聚焦：{res['n_focusable']}/{len(foc)} ==")

        # ③ Tab 40 步：轨迹里有没有落到节点上
        pg.evaluate("() => { if (document.activeElement) document.activeElement.blur(); }")
        traj = []
        for _ in range(40):
            pg.keyboard.press("Tab")
            time.sleep(0.06)
            traj.append(pg.evaluate(FOCUS_JS))
        res["tab_traj_len"] = len(traj)
        res["n_tab_into_node"] = sum(1 for t in traj if t.get("in_node"))
        res["n_tab_into_toolbar"] = sum(
            1 for t in traj if t.get("in_toolbar"))
        res["n_tab_body"] = sum(1 for t in traj if t["tag"] == "BODY")
        res["tab_saw_node_aria"] = sorted({
            t["aria"] for t in traj
            if t["aria"] and t["aria"] != "(body)"
            and ("node" in t["aria"] or "node" in t["aria"].lower())})[:10]
        print(f"== Tab 40 步：进节点 {res['n_tab_into_node']} 次，"
              f"进工具条 {res['n_tab_into_toolbar']} 次，"
              f"落 body {res['n_tab_body']} 次 ==")
        print(f"   轨迹里见过的 node 类 aria：{res['tab_saw_node_aria']}")

        # ── 判定 ────────────────────────────────────────────
        # 「面板卸载后焦点除了 body 无处可去」只在**节点确实不可聚焦**时成立
        n_node_tab = res["n_tab_into_node"]
        n_node_focus = res["n_focusable"]
        if n_node_tab == 0 and n_node_focus == 0:
            res["verdict"] = (
                "夹具差异：复刻画布节点**既不可程序化聚焦、也不在 Tab 序列里**"
                " ⇒ 面板卸载后焦点除了 body 无处可去，body 是必然结果。"
                "源站的节点是 BUTTON（aria `音频 node: 音频 NN`）天生可聚焦，"
                "所以两边落点不同。**不是产品缺陷**，但也不是「已对齐」。")
        elif n_node_focus == 0 and n_node_tab > 0:
            res["verdict"] = (
                "**矛盾**：Tab 能进节点，但程序化 focus 进不去。"
                "得先查清这个矛盾（哪个读数错了），不许下结论。")
        else:
            res["verdict"] = (
                "**真缺陷候选**：节点**可以**被聚焦 ⇒ 焦点掉 body 是实现疏忽，"
                "与 873 修 Y.4 的理由同一条（「面板一卸焦点掉 body 是最坏落点」）。"
                "需要定「Esc 之后焦点该去哪」。")
        print(f"\n== 判定：{res['verdict']}")
        b.close()

    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print(f"\n== 已写 {OUT} ==")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

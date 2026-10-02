#!/usr/bin/env python3
"""batch 891 复刻探针：**最小复现**验死那条浏览器规则（不跑源站、不需登录）。

## 要验死的是什么

§101 把机制描述到了「一层」，但那条描述是**对读数的归纳**，**不是**因果证明：

> 「`mousedown` 落点若在当前焦点元素的**子树内**，浏览器不移动焦点」

源站那边 A 序列 `focusin` **0** 次、B 序列 **2** 次；复刻两边都把焦点移到了
节点。**但到底是不是这条规则在起作用，从来没被单独验过。**

§77：机制未验死之前不许改判据、下判断。所以这批**只做一件事** ——
在一个**空白页**上把这几个变量**逐个控制**，看焦点到底动不动。

## 真值表（每个格子 2 次）

| 编号 | 焦点起点 | 落点 | 页面上的额外设置 | 想验的 |
|---|---|---|---|---|
| C1 | 容器（可聚焦） | 容器里的**可聚焦子元素**里那个**不可聚焦后代** | 无 | **基线**：焦点在祖先 ⇒ 动不动？ |
| C2 | 容器**外面**的可聚焦元素 | 同上 | 无 | 焦点不在祖先 ⇒ 应该动 |
| C3 | 容器 | 同上 | mousedown **preventDefault** | 阻止默认动作会怎样 |
| C4 | 容器 | 同上 | mousedown **stopPropagation** | 只停冒泡（**不**阻止默认）会怎样 |
| C5 | 容器**外面** | 同一个落点，但**容器不可聚焦**（去掉 tabindex） | 无 | 「祖先可聚焦」是不是前提 |
| C6 | 容器 | 落点**自己可聚焦**（给它 tabindex=0） | 无 | 「落点不可聚焦」是不是前提 |

⇒ C1 与 C2 的差 = 「焦点在不在落点的祖先内」这一个变量；
C1 vs C5 = 祖先可聚焦性；C1 vs C6 = 落点可聚焦性；
C3/C4 用来分清「阻止默认」与「只停冒泡」。

## 纪律

- 每个格子**重新 `set_content`** 一次 ⇒ 互不污染
- 用**真鼠标事件**（`page.mouse`）⇒ 浏览器的默认行为才会发生；
  `dispatchEvent` 出来的合成事件**不会**触发焦点默认行为
- 落点**必须量出来**再点（`elementFromPoint`），不许照抄坐标
- 每个格子**2 次**（一次成功不叫可靠）

跑法：`/opt/miniconda3/bin/python3 scripts/jimeng_probe891_mousedown_rule_ck.py`
"""

from __future__ import annotations

import json
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path("/tmp/b891-ck-mousedown-rule.json")
REPS = 2

# 容器 = 焦点起点之一（tabindex 由 case 决定）；child = 节点（tabindex=0）；
# deep = 落点（tabindex 由 case 决定，**故意**默认不可聚焦）
HTML = """<!doctype html><html><body style="margin:0">
<div id="outside" tabindex="0"
     style="position:absolute;left:20px;top:20px;width:120px;height:40px;
            background:#eee">outside</div>
<div id="container" {container_attr}
     style="position:absolute;left:20px;top:120px;width:400px;height:300px;
            background:#dde">
  <div id="child" tabindex="0"
       style="position:absolute;left:40px;top:40px;width:200px;height:120px;
              background:#cc">
    <span id="deep"
          style="position:absolute;left:20px;top:20px;width:120px;height:60px;
                 background:#aaa">deep</span>
  </div>
</div>
</body></html>"""

FOCUS_JS = """() => { const a = document.activeElement;
  if (!a || a === document.body) return {id: '(body)'};
  return {id: a.id || a.tagName,
          in_container: !!(a.closest && a.closest('#container')),
          in_child: !!(a.closest && a.closest('#child'))}; }"""

# 装监听：**同时**在捕获与冒泡两个阶段读 defaultPrevented（890 的教训：
# 只在捕获阶段读**恒真为假**）
LISTEN_JS = """(mode) => {
  // ⚠️ 数组名与 handler 名**必须分开**（第一版把数组 `cap` 又赋成了 handler
  // 函数 ⇒ READ 回来是函数、序列化后是 None ⇒ `for m in None` 直接炸）。
  // 教训与 890 同族：**读数取不到时要认得出是「变量写重了」**，别当成
  // 「浏览器没触发」。
  const w = window.__w = {cap: [], bub: [], focusins: []};
  w.onCap = (e) => { w.cap.push({id: e.target.id,
      defaultPrevented: e.defaultPrevented}); };
  w.onBub = (e) => { w.bub.push({id: e.target.id,
      defaultPrevented: e.defaultPrevented}); };
  w.onFi = (e) => { w.focusins.push(e.target.id || e.target.tagName); };
  document.addEventListener('mousedown', w.onCap, true);
  document.addEventListener('focusin', w.onFi, true);
  if (mode === 'preventDefault' || mode === 'stopPropagation') {
    w.onH = (e) => {
      if (e.target.id === 'deep') {
        if (mode === 'preventDefault') e.preventDefault();
        else e.stopPropagation();
      }
    };
    // 挂在**容器**上：冒泡到 document 之前，节点自己的 handler 之后
    document.getElementById('container').addEventListener('mousedown', w.onH);
  }
  if (mode !== 'none') {
    document.addEventListener('mousedown', w.onBub, false);
  }
  return true;
}"""

READ_JS = """() => { const w = window.__w;
  if (!w) return null;
  return {focusins: w.focusins, cap: w.cap, bub: w.bub}; }"""

HIT_JS = """() => {
  const e = document.elementFromPoint(120, 200);
  return e ? {id: e.id, tabIndexProp: e.tabIndex} : {none: true}; }"""

# 每个 case：(容器可聚焦?, 落点可聚焦?, 页面模式, 焦点起点 id, 预期问题)
CASES = [
    ("C1_baseline_focus_in_ancestor",
     'tabindex="0"', "", "none", "container",
     "焦点在落点的**可聚焦祖先**上 ⇒ 浏览器动不动焦点？"),
    ("C2_focus_outside",
     'tabindex="0"', "", "none", "outside",
     "焦点在祖先**外面** ⇒ 应该动（对照组）"),
    ("C3_prevent_default",
     'tabindex="0"', "", "preventDefault", "container",
     "mousedown 被 **preventDefault** ⇒ 默认的焦点移动被阻止吗？"),
    ("C4_stop_propagation",
     'tabindex="0"', "", "stopPropagation", "container",
     "mousedown 被 **stopPropagation**（**不**阻止默认）⇒ 会怎样？"),
    ("C5_ancestor_not_focusable",
     "", "", "none", "outside",
     "祖先**不可聚焦** ⇒ 「祖先可聚焦」是不是前提？"),
    ("C6_target_itself_focusable",
     'tabindex="0"', 'tabindex="0"', "none", "container",
     "落点**自己可聚焦** ⇒ 「落点不可聚焦」是不是前提？"),
]


def main() -> int:
    res: dict = {"cases": {}}
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_context(viewport={"width": 900, "height": 600}).new_page()
        for name, container_attr, deep_attr, mode, focus_start, _why in CASES:
            deep = HTML.replace("{container_attr}", container_attr)
            deep = deep.replace('<span id="deep"',
                                f'<span id="deep" {deep_attr}'.strip() + " ")
            runs = []
            for rep in range(1, REPS + 1):
                # ⚠️ 每个格子**重新 set_content** ⇒ 互不污染
                pg.set_content(deep, wait_until="load")
                pg.evaluate(LISTEN_JS, mode)
                pg.evaluate("(id) => document.getElementById(id).focus()",
                            focus_start)
                before = pg.evaluate(FOCUS_JS)
                # 落点**量出来**再点，不许照抄坐标
                hit = pg.evaluate(HIT_JS)
                box = pg.evaluate(
                    "() => { const r = document.getElementById('deep')"
                    ".getBoundingClientRect();"
                    " return [Math.round(r.x + r.width/2),"
                    "         Math.round(r.y + r.height/2)]; }")
                if hit.get("id") != "deep":
                    runs.append({"rep": rep,
                                 "verdict": f"前置态没成立：坐标落点是 "
                                            f"{hit.get('id')!r} 不是 deep"})
                    print(f"  !! [{name} #{rep}] 落点={hit}")
                    continue
                pg.mouse.click(box[0], box[1])
                pg.wait_for_timeout(250)
                after = pg.evaluate(FOCUS_JS)
                ev = pg.evaluate(READ_JS) or {}
                rec = {
                    "rep": rep, "focus_start": focus_start, "mode": mode,
                    "hit": hit,
                    "focus_before": before, "focus_after": after,
                    "focusin": ev.get("focusins", []),
                    "md_capture_prevented": [m["defaultPrevented"]
                                              for m in ev.get("cap", [])],
                    "md_bubble_prevented": ([m["defaultPrevented"]
                                             for m in ev.get("bub", [])]
                                            if ev.get("bub") else "(没挂冒泡监听)"),
                    "moved": after.get("id") != before.get("id"),
                    "verdict": "sampled",
                }
                runs.append(rec)
                print(f"\n[{name} #{rep}] mode={mode}  起点={focus_start}")
                print(f"   落点={hit.get('id')!r} tabIndexProp="
                      f"{hit.get('tabIndexProp')!r}")
                print(f"   焦点 {before.get('id')!r} → {after.get('id')!r}"
                      f"   移动={rec['moved']}")
                print(f"   focusin={rec['focusin']}")
                print(f"   mousedown 捕获阶段 defaultPrevented="
                      f"{rec['md_capture_prevented']}"
                      f"  冒泡阶段={rec['md_bubble_prevented']}")
            res["cases"][name] = {
                "runs": runs,
                "moved": [r.get("moved") for r in runs],
                "why": _why,
                "stable": len([r for r in runs if "moved" in r]) == REPS
                and len({r["moved"] for r in runs if "moved" in r}) == 1,
            }
        b.close()

    print("\n== 真值表：焦点到底动不动 ==")
    print(f"  {'格子':34s} {'焦点是否移动':16s} 结论")
    for name, _v in res["cases"].items():
        s = res["cases"][name]
        mark = "OK " if s["stable"] else ("?? " if s["moved"] else "—  ")
        mv = s["moved"]
        txt = ("不动" if mv == [False, False] else
               "会动" if mv == [True, True] else str(mv))
        print(f"  {mark}{name:31s} {txt:16s} {s['why']}")

    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print(f"\n== 已写 {OUT} ==")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

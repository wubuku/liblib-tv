#!/usr/bin/env python3
r"""batch 920 源站探针（**纯诊断**）：走查过程中**逐次**普查「有几个本体带 `tabindex`」

## 919 留下的确切缺口

919 实测（两轮逐条一致）：

- **中性态**普查：画布内**没有任何节点本体是可聚焦的**
  （`n_wrappers_with_ti0 = 0`、IDL 列表里 0 个本体）；
- 布上**一个**之后：那个本体 `tabindex` 属性 = `0`、IDL = `0`、
  落在 IDL 序第 11 位（**紧跟 `Canvas` 之后、在它自己的第一个内层控件之前**）。

⚠️ **但 917/918 的焦点轨迹里，按前焦点多次落在「别的节点的本体」上**
（`pre_is_wrapper = True`，例如 `文本 node: 文本 2`）
⇒ **焦点怎么会落到一个（普查时）没有 `tabindex` 的元素上？**

## 这一批只做一件事：**每按一次就普查一次**

对走查的**每一次按压**，在**按之前**与**按之后**各普查一次：

1. **带 `tabindex="0"` 的本体有几个、分别是哪些下标**
   （⚠️ 关键：919 只在「按完 1 次之后」普查过一次，**没看过走查过程中会变几个**）
2. **带任意 `tabindex`（含 `-1`）的本体有几个**
3. **IDL `tabIndex >= 0` 的本体有几个**（真正在顺序焦点导航里的）
4. **按前焦点那个元素自己**的 `tabindex` 属性 / IDL `tabIndex` / 是不是本体
   ⇒ 于是能直接回答：「焦点停着的那个本体，**那一刻**到底可不可聚焦？」

⇒ 若走查过程中**同时有多个本体带 `tabindex="0"`** ⇒ 焦点能落到别的本体上
**就有了解释**（roving 留下了「轨迹」而不是只留一个）。
⇒ 若**始终只有一个**、而按前焦点却是别的本体 ⇒ **那这个本体一定不是靠
`tabindex` 可聚焦的** ⇒ 就是**程序化 `.focus()`** ⇒ 机制指向哪边由读数说话。

## 判据纪律

- **纯诊断**：普查**纯读**、**不劫持 prototype、不装 MutationObserver**
  ⇒ **诊断不许破坏被诊断状态**
- **每轮之间 reload**；**重复 2 轮**
- ⚠️ **`moved` 是必需字段**（`armed` 会被 `oldValue != '0'` 过滤吞读数 ——
  **904 记过、909 又踩一次**）
- 节点总数是易变量 ⇒ **只记不钉**；按**身份**记 DOM 序
- **落盘排在打印之前**；**被挡时也要落盘**；登录判据**未命中就重试**
- ⚠️ **重定向到文件时一律加 `-u`**（914 踩过）
- ⚠️ 探针**只输出读数**，判读留给基线

## 计费边界

只按 `Tab`、点画布空白。**绝不**点生成/发送/购买/充值，
**也绝不**点音色 chip 本身。**不点任何节点。**

跑法：
  ~/.venvs/liblib-harness/bin/python -u scripts/jimeng_headless.py run \
      scripts/jimeng_probe920_per_press_wrapper_census_src.py
"""

import json

OUT = "/tmp/b920-src-per-press-wrapper-census.json"
REPS = 2
SETTLE = 400
N_PRESS = 14            # 走 14 次：足够看到好几次「布」与中间那串「死按压」

BLANK_JS = """() => {
  for (const [x, y] of [[1300, 1000], [1360, 920], [1220, 1080],
                        [1400, 840], [400, 1080]]) {
    const t = document.elementFromPoint(x, y);
    if (t && t.closest('.react-flow__pane')
        && !t.closest('.react-flow__node')) return [x, y];
  }
  return null;
}"""

# ⚠️⚠️ **920 的核心读数**：本体「可聚焦性」的**逐次**普查。
# ⚠️ 三个口径**必须同时**记 —— 919 已经吃过一次「只用一个口径」的亏：
#   ① `tabindex="0"` 的本体有几个（**属性**口径，roving 指针的落点）
#   ② 带**任意** `tabindex`（含 `-1`）的本体有几个
#   ③ **IDL `tabIndex >= 0`** 的本体有几个（**真正在顺序焦点导航里**的）
#   ④ 按前焦点那个元素**自己**的三个口径
CENSUS_JS = """() => {
  const nodes = [...document.querySelectorAll('.react-flow__node')];
  const zeroIdx = [], anyTiIdx = [], idlIdx = [];
  for (let i = 0; i < nodes.length; i++) {
    const n = nodes[i];
    const ti = n.getAttribute('tabindex');
    if (ti === '0') zeroIdx.push(i);
    if (ti !== null) anyTiIdx.push(i);
    if (n.tabIndex >= 0) idlIdx.push(i);
  }
  const a = document.activeElement;
  const aIsWrapper = !!(a && a.classList
                    && a.classList.contains('react-flow__node'));
  return {
    n_nodes: nodes.length,
    // ① 属性口径：roving 指针落在哪几个本体上
    n_wrapper_ti0: zeroIdx.length,
    ti0_idx: zeroIdx,
    // ② 属性口径：带任意 tabindex 的本体
    n_wrapper_any_ti: anyTiIdx.length,
    any_ti_idx: anyTiIdx.slice(0, 12),
    // ③ IDL 口径：真正在顺序焦点导航里的本体
    n_wrapper_idl_focusable: idlIdx.length,
    idl_idx: idlIdx.slice(0, 12),
    // ④ 按前焦点那个元素**自己**的三个口径 ← 直接回答那个缺口
    active: {
      tag: a ? a.tagName : null,
      aria: a ? (a.getAttribute('aria-label') || '').slice(0, 22) : null,
      is_wrapper: aIsWrapper,
      wrapper_idx: aIsWrapper ? nodes.indexOf(a) : null,
      ti_attr: a ? a.getAttribute('tabindex') : null,
      ti_idl: a ? a.tabIndex : null,
    },
    // 顺带：本体的 tabindex 到底是「被应用设上去的」还是「本来就有」
    // ⇒ 只取**第一个**本体的当前值当样本（不钉具体下标）
    sample_wrapper_ti: nodes.length
      ? {idx: 0, ti_attr: nodes[0].getAttribute('tabindex'),
         ti_idl: nodes[0].tabIndex} : null,
  };
}"""


def ev(js, arg=None):
    return page.evaluate(js) if arg is None else page.evaluate(js, arg)


def zero_idx():
    """`'0'` 在哪些本体上（**按身份换算成下标**，不钉 testid、不钉总数）。"""
    return ev("() => [...document.querySelectorAll('.react-flow__node')]"
              ".map((n, i) => (n.getAttribute('tabindex') === '0' ? i : -1))"
              ".filter((i) => i >= 0)")


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
        rec["census_at_blank"] = ev(CENSUS_JS)   # 归零那一刻的普查

        presses = []
        for k in range(N_PRESS):
            before = ev(CENSUS_JS)               # ⚠️ **按之前**就普查
            zb = zero_idx()
            page.keyboard.press("Tab")
            page.wait_for_timeout(SETTLE)
            after = ev(CENSUS_JS)                # ⚠️ **按之后**再普查一次
            za = zero_idx()
            presses.append({
                "k": k + 1,
                "before": before,
                "after": after,
                "zero_before": zb, "zero_after": za,
                # ⚠️ **`moved` 是必需字段**（`armed` 会被 `oldValue != '0'` 过滤吞读数）
                "moved": zb != za,
            })
            print(f"  按第{k + 1:>2d}次：按前 本体ti0={before['n_wrapper_ti0']}个"
                  f"{before['ti0_idx']}／本体IDL可聚焦={before['n_wrapper_idl_focusable']}个"
                  f"　按前焦点={before['active']['aria']!r}"
                  f"（本体={before['active']['is_wrapper']}"
                  f"、ti_attr={before['active']['ti_attr']}"
                  f"、ti_idl={before['active']['ti_idl']}）")
            print(f"          按后 本体ti0={after['n_wrapper_ti0']}个{after['ti0_idx']}"
                  f"／本体IDL可聚焦={after['n_wrapper_idl_focusable']}个"
                  f"　'0' {zb}→{za}　moved={zb != za}")
        rec["presses"] = presses
        rec["sample_wrapper_ti_at_end"] = presses[-1]["after"]["sample_wrapper_ti"]
        runs.append(rec)
        print("  （纯读普查，没有装任何监听器）")

    out["runs"] = runs
    out["verdict"] = "sampled"
    # ⚠️ 落盘**必须**排在打印之前（900 的教训）
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print("\n== 汇总（只输出读数，**不判机制**）==")
    for r in runs:
        print(f"  rep{r['rep']}（{r['n_press']} 次按压）：")
        for p in r["presses"]:
            a = p["after"]["active"]
            print(f"    第{p['k']:>2d}次 moved={str(p['moved']):<5s} "
                  f"'0' {p['zero_before']}→{p['zero_after']} | "
                  f"按后本体ti0={p['after']['n_wrapper_ti0']}"
                  f"{p['after']['ti0_idx']} "
                  f"本体IDL可聚焦={p['after']['n_wrapper_idl_focusable']}"
                  f"{p['after']['idl_idx']} | "
                  f"焦点={a['aria']!r} 本体={a['is_wrapper']} "
                  f"ti_attr={a['ti_attr']} ti_idl={a['ti_idl']}")
    print(f"\n== 已写 {OUT} ==")

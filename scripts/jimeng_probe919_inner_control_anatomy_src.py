#!/usr/bin/env python3
r"""batch 919 源站探针（**纯诊断**）：那 5 个内层控件**能被 Tab 走到、却不被选择器匹配**，为什么？

## 918 留下的确切口

918 的 `TABORDER_JS` 用标准可聚焦选择器在画布根内**只找到 10 个元素、
`n_wrappers = 0`**，而同一批 918/917 的**焦点轨迹**里明明白白出现过这 5 个
**画布内**的内层控件：

| 控件 | 焦点轨迹里的出现次数（918，6 条臂合计） |
|---|---|
| `导出时间线` | 54 |
| `全屏编辑` | 54 |
| `静音` | 48 |
| `添加素材到时间线` | 42 |
| `替换媒体` | 24 |

⇒ **要么是选择器漏了、要么它们根本不在 `.react-flow` 子树里** ⇒ **未查明**。

## 这一批只做诊断，**不改任何扰动臂**

两条读数：

### 一、**逐个控件解剖**（决定性读数）

对每个已知 `aria-label`，直接把那个元素挖出来，记：
`tag` / 全部属性 / `matches(标准选择器)` / **IDL `tabIndex`** /
在不在 `.react-flow` 子树里 / 在不在任何 **shadow root** 里 /
它与所属 `.react-flow__node` 本体在 **document 序**上的相对位置。

⚠️ **为什么一定要看 IDL `tabIndex`**：浏览器的顺序焦点导航走的是
**IDL `tabIndex`**，它**不只**反映 `tabindex` 属性 ⇒
918 那个「属性选择器」视角可能整个问错了地方。
`el.tabIndex >= 0` 才是「**这个元素在顺序焦点导航里**」的权威判据。

### 二、**动态** tab 序：布上之后本体被注入到哪一位

918 已测到**中性态下节点本体没有 `tabindex`、不在 tab 序里**（它是布的那一刻
被临时注入的）。⇒ 这一批按一次 `Tab`（把某个节点布上）**立刻**重新普查
document 序 ⇒ 看**本体被插在哪一位**、以及它是不是成了 `activeElement`。

⇒ 这才是「**反向为什么绕整页**」该问的地方
（918 那个「静态 DOM 位置」的问法已被它自己否掉）。

## 判据纪律

- **每轮之间 reload**；**重复 2 轮**
- ⚠️ 诊断动作**不许破坏被诊断状态**：只按 `Tab` 与点画布空白；
  普查是**纯读**、不改 DOM、不劫持 prototype、不装 MutationObserver
- **落盘排在打印之前**；**被挡时也要落盘**；登录判据**未命中就重试**
- ⚠️ **重定向到文件时一律加 `-u`**（914 踩过）
- 节点总数是易变量 ⇒ **只记不钉**
- ⚠️ 探针**只输出读数**，判读留给基线

## 计费边界

只按 `Tab`、点画布空白。**绝不**点生成/发送/购买/充值，
**也绝不**点音色 chip 本身。**不点任何节点。**

跑法：
  ~/.venvs/liblib-harness/bin/python -u scripts/jimeng_headless.py run \
      scripts/jimeng_probe919_inner_control_anatomy_src.py
"""

import json

OUT = "/tmp/b919-src-inner-control-anatomy.json"
REPS = 2
SETTLE = 400
TAB_AFTER_BLANK = 1        # 布一次就够（这一批不是扰动批）

TARGETS = ["导出时间线", "全屏编辑", "静音", "添加素材到时间线", "替换媒体"]

STD_SEL = "a[href],button,input,select,textarea,[tabindex],[contenteditable=\"true\"]"

BLANK_JS = """() => {
  for (const [x, y] of [[1300, 1000], [1360, 920], [1220, 1080],
                        [1400, 840], [400, 1080]]) {
    const t = document.elementFromPoint(x, y);
    if (t && t.closest('.react-flow__pane')
        && !t.closest('.react-flow__node')) return [x, y];
  }
  return null;
}"""

# ⚠️⚠️ **919 的核心读数**：逐个控件解剖。
# 关键点：**同时**看「属性选择器口径」与「**IDL `tabIndex` 口径**」——
# 918 只看了前者，918 的失败有可能**整个是问错了口径**。
ANATOMY_JS = """(cfg) => {
  const SEL = cfg.sel;
  const canvas = document.querySelector('.react-flow');
  const out = {targets: [], canvas_found: !!canvas,
               n_nodes_in_canvas: canvas
                 ? canvas.querySelectorAll('.react-flow__node').length : 0};
  const deepest = (el) => {
    // ⚠️ 逐层往上找**带 shadowRoot 的宿主**：`querySelectorAll` **不穿透 shadow DOM**
    let d = 0, p = el;
    while (p) { if (p.shadowRoot) d++; p = p.parentNode || p.host; }
    return d;
  };
  for (const label of cfg.targets) {
    const els = [...document.querySelectorAll('[aria-label]')]
      .filter((e) => (e.getAttribute('aria-label') || '') === label);
    const rec = {aria: label, n_found: els.length, found: []};
    for (const el of els) {
      const owner = el.closest('.react-flow__node');
      const nodes = [...document.querySelectorAll('.react-flow__node')];
      const ownerIdx = owner ? nodes.indexOf(owner) : null;
      const allFocusable = [...document.querySelectorAll('*')]
        .filter((e) => e.tabIndex >= 0);
      const myPos = allFocusable.indexOf(el);
      const ownerPos = owner ? allFocusable.indexOf(owner) : null;
      rec.found.push({
        tag: el.tagName,
        // ⚠️ **属性选择器口径**（918 用的就是这个）
        matches_std_sel: el.matches(SEL),
        // ⚠️⚠️ **IDL `tabIndex` 口径**（顺序焦点导航的权威判据）
        idl_tabindex: el.tabIndex,
        attr_tabindex: el.getAttribute('tabindex'),
        attrs: el.getAttributeNames()
                 .filter((n) => n !== 'class' && n !== 'style')
                 .slice(0, 10),
        in_canvas: !!(canvas && canvas.contains(el)),
        in_react_flow_node: !!owner,
        owner_idx: ownerIdx,
        shadow_depth: deepest(el),
        // ⚠️ **在「顺序焦点导航的 document 序」里排第几**
        pos_in_idl_order: myPos,
        owner_pos_in_idl_order: ownerPos,
        doc_pos: (() => {   // 在整个 document 里的序号
          let i = 0, p = el;
          while ((p = p.previousElementSibling)) i++;
          return i;
        })(),
      });
    }
    out.targets.push(rec);
  }
  return out;
}"""

# ⚠️ **普查口径对照**：同时用「属性选择器」和「IDL `tabIndex`」数一遍
CENSUS_JS = """(cfg) => {
  const canvas = document.querySelector('.react-flow');
  const scope = canvas || document.body;
  const std = [...scope.querySelectorAll(cfg.sel)];
  const idl = [...scope.querySelectorAll('*')].filter((e) => e.tabIndex >= 0);
  const docIdl = [...document.querySelectorAll('*')].filter((e) => e.tabIndex >= 0);
  const brief = (els) => els.slice(0, 24).map((e) => ({
    tag: e.tagName,
    aria: (e.getAttribute('aria-label') || '').slice(0, 20),
    ti_attr: e.getAttribute('tabindex'),
    ti_idl: e.tabIndex,
    node_wrapper: !!(e.classList
      && e.classList.contains('react-flow__node')),
  }));
  return {
    n_nodes: document.querySelectorAll('.react-flow__node').length,
    n_wrappers_with_ti0: document.querySelectorAll(
      '.react-flow__node[tabindex="0"]').length,
    in_canvas_std: std.length,
    in_canvas_idl: idl.length,
    whole_doc_idl: docIdl.length,
    // ⚠️ 两份**样本**（918 忘了存这两份，导致「那 10 个是谁」查不了）
    sample_std: brief(std),
    sample_idl: brief(idl),
  };
}"""

# ⚠️ **动态**读法：布上之后再看一次本体被注入到哪一位
DYNAMIC_JS = """() => {
  const nodes = [...document.querySelectorAll('.react-flow__node')];
  const allIdl = [...document.querySelectorAll('*')].filter((e) => e.tabIndex >= 0);
  const w = nodes.find((n) => n.getAttribute('tabindex') === '0') || null;
  const a = document.activeElement;
  const around = [];
  if (w) {
    const i = allIdl.indexOf(w);
    for (let k = Math.max(0, i - 4); k <= Math.min(allIdl.length - 1, i + 4); k++) {
      const e = allIdl[k];
      around.push({k, is_wrapper: e === w,
        tag: e.tagName,
        aria: (e.getAttribute('aria-label') || '').slice(0, 20),
        ti_idl: e.tabIndex});
    }
  }
  return {
    n_wrappers_with_ti0: nodes.filter((n) => n.getAttribute('tabindex') === '0')
                               .length,
    wrapper_idx: w ? nodes.indexOf(w) : null,
    wrapper_ti_attr: w ? w.getAttribute('tabindex') : null,
    wrapper_ti_idl: w ? w.tabIndex : null,
    wrapper_pos_in_idl_order: w ? allIdl.indexOf(w) : null,
    n_idl: allIdl.length,
    active_is_wrapper: !!(a && a.classList
                        && a.classList.contains('react-flow__node')),
    active_aria: a ? (a.getAttribute('aria-label') || '').slice(0, 20) : null,
    active_ti_idl: a ? a.tabIndex : null,
    around,
  };
}"""


def ev(js, arg=None):
    return page.evaluate(js) if arg is None else page.evaluate(js, arg)


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
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"== 已写 {OUT}（被挡时也要落盘）==")
else:
    runs = []
    for rep in range(1, REPS + 1):
        rec = {"rep": rep}
        page.goto(URL, wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(9000)
        page.set_viewport_size({"width": 1512, "height": 1200})
        page.wait_for_timeout(2500)

        # ① 中性态普查（**纯读**，不改 DOM）
        rec["census_neutral"] = ev(CENSUS_JS, {"sel": STD_SEL})
        # ② 逐个控件解剖
        rec["anatomy"] = ev(ANATOMY_JS, {"sel": STD_SEL, "targets": TARGETS})

        # ③ **动态**：点空白把焦点归零到画布根 ⇒ 按一次 `Tab` ⇒ 立刻重测
        sp = ev(BLANK_JS)
        if sp:
            page.mouse.click(sp[0], sp[1])
            page.wait_for_timeout(900)
        rec["blank_hit"] = sp
        for _ in range(TAB_AFTER_BLANK):
            page.keyboard.press("Tab")
            page.wait_for_timeout(SETTLE)
        rec["after_tab"] = ev(DYNAMIC_JS)
        rec["census_after_tab"] = ev(CENSUS_JS, {"sel": STD_SEL})

        c = rec["census_neutral"]
        ca = rec["census_after_tab"]
        a = rec["anatomy"]
        at = rec["after_tab"]
        print(f"\n--- rep{rep} ---")
        print(f"  中性态：节点={c['n_nodes']}、有 tabindex=0 的本体="
              f"{c['n_wrappers_with_ti0']}")
        print(f"  画布内普查：属性选择器口径 **{c['in_canvas_std']}** 个"
              f"　IDL tabIndex 口径 **{c['in_canvas_idl']}** 个"
              f"　整篇 document 的 IDL 口径 **{c['whole_doc_idl']}** 个")
        print(f"  ⇒ 918 问的「属性选择器」口径在这一轮给出 {c['in_canvas_std']}，"
              f"IDL 口径给出 {c['in_canvas_idl']}")
        for t in a["targets"]:
            if not t["found"]:
                print(f"    {t['aria']:<18s} **没找到**")
                continue
            for f in t["found"][:1]:
                print(f"    {t['aria']:<18s} tag={f['tag']:<7s} "
                      f"属性口径={str(f['matches_std_sel']):<5s} "
                      f"IDL tabIndex={f['idl_tabindex']:<4} "
                      f"attr={str(f['attr_tabindex']):<5s} "
                      f"在画布内={str(f['in_canvas']):<5s} "
                      f"属于节点{f['owner_idx']} shadow层={f['shadow_depth']} "
                      f"IDL序位={f['pos_in_idl_order']} "
                      f"本体IDL序位={f['owner_pos_in_idl_order']}")
        print(f"  布上后：本体 tabindex=0 的个数={at['n_wrappers_with_ti0']}、"
              f"本体下标={at['wrapper_idx']}、"
              f"本体 attr tabindex={at['wrapper_ti_attr']}、"
              f"本体 **IDL tabIndex={at['wrapper_ti_idl']}**、"
              f"本体在 IDL 序里第 {at['wrapper_pos_in_idl_order']} 位"
              f"（共 {at['n_idl']} 个）")
        print(f"  布上后 activeElement 是本体？{at['active_is_wrapper']}、"
              f"aria={at['active_aria']!r}、IDL tabIndex={at['active_ti_idl']}")
        print(f"  布上后画布内普查：属性口径 {ca['in_canvas_std']}、"
              f"IDL 口径 {ca['in_canvas_idl']}")
        runs.append(rec)
        print("  （诊断是纯读，没有装任何监听器）")

    out["runs"] = runs
    out["verdict"] = "sampled"
    # ⚠️ 落盘**必须**排在打印之前（900 的教训）
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print("\n== 汇总（只输出读数，**不判机制**）==")
    for r in runs:
        c, a, at = r["census_neutral"], r["anatomy"], r["after_tab"]
        print(f"  rep{r['rep']}: 画布内 属性口径={c['in_canvas_std']}、"
              f"IDL 口径={c['in_canvas_idl']}、整篇 IDL={c['whole_doc_idl']}；"
              f"布上后本体 IDL tabIndex={at['wrapper_ti_idl']}、"
              f"序位={at['wrapper_pos_in_idl_order']}")
    print(f"\n== 已写 {OUT} ==")

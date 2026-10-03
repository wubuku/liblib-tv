#!/usr/bin/env python3
r"""batch 915 源站探针：**第二条历史扰动轴** —— 最终那一段走**之前**的历史有没有影响？

## 914 排除了哪一条、没排除哪一条

914（3 对 × 2 轮）证明的是：起点对「**同一段走查之内**越过终点再往回走回来」
这段历史**不敏感** ⇒ 910–912 那个「终点与历史共变」的顾虑被排除。

⚠️ 但 914 的 `B` 臂与 `A` 臂**最终那一段走查是同一条**（都是 `j` 次 `Tab`），
只在**同一段之内**多了「越过 + 回走」⇒ **只排除了「一种」历史扰动**。
⚠️ **别的历史轴一个都没测** —— 特别是：
**「最终那一段走查之前，还走查过别的地方」有没有影响？**

## 这一批的设计：前置走查 + 归零 + 再走**同一条**

| 臂 | 步骤 | 目标终点 |
|---|---|---|
| `A-fwd49` | `fwd 49` | 40（914 已测 ⇒ 起点 **11**） |
| `D1-pre30-fwd49` | `fwd 30` ⇒ **点空白** ⇒ `fwd 49` | 40 |
| `D2-pre30-back5-fwd49` | `fwd 30` ⇒ **回走 5** ⇒ **点空白** ⇒ `fwd 49` | 40 |
| `B-fwd44` | `fwd 44` | 35（914 已测 ⇒ 起点 **0**） |
| `H-pre30-back5-fwd44` | `fwd 30` ⇒ **回走 5** ⇒ **点空白** ⇒ `fwd 44` | 35 |
| `E-fwd60` | `fwd 60` | 51（914 已测 ⇒ 起点 **12**） |
| `F-pre30-fwd60` | `fwd 30` ⇒ **点空白** ⇒ `fwd 60` | 51 |
| `G-pre30-back5-fwd60` | `fwd 30` ⇒ **回走 5** ⇒ **点空白** ⇒ `fwd 60` | 51 |

⚠️ **关键点**：每个扰动臂的「**最后一段走查**」都与某条基线臂**逐字相同**
（`fwd 49` / `fwd 44` / `fwd 60`，同样从画布根起步），
**只有前面多了别的走查 + 一次点空白**。
⚠️ 这条前提由**静态 `assert`** 挡住（见下方「自检之二」——
`H-pre30-back5-fwd44` 一开始就没有基线臂可比，**靠它才当场发现**）。
⇒ 若起点仍与基线臂相同 ⇒ **前史无关**（起点只由最后那一段决定 ⇒ 也就是由终点决定）。
⇒ 若不同 ⇒ **历史确实有影响**，914 的结论要收窄。

## ⚠️ 探针**自己**拒绝再犯 913 那个错（沿用 914 的防线并加一条）

914 的教训：**证伪臂的参数必须越过对照组**，否则两条臂是同一条。
915 的对应风险是「前置走查白加了、最终那段其实没变」⇒ 所以：

- **静态侧**（开跑前 `assert`）：每个扰动臂**必须**含至少一个 `blank` 步骤
  ⇒ 否则「前置走查」根本没把焦点归零，那条臂就不是扰动臂。
- **运行侧**（每臂记 `design_ok`）：**同时**要求
  ① 实测终点 **==** 目标；② **确实存在前置步骤**（`n_pre_steps >= 1`）；
  ③ **前置走查真的走过**（`pre_forward_presses >= 1`）
  ⇒ 三条任一不成立就打「**设计违规**」，基线**不许**把那一条当对照读。

## 判据纪律

- 仪器**逐字复用** 914/913/912（`__b915`）
- **每臂之间 reload**；每轮**重复 2 次**；终点**实测**
- ⚠️ **`moved` 是必需字段**（`armed` 会被 `oldValue != '0'` 过滤吞读数 ——
  **904 记过、909 又踩一次**）
- **全程不碰末尾** ⇒ 撞不上绕回（`j ≤ 60` < 实测末尾 75）
- 节点总数是易变量 ⇒ 按**身份**记 DOM 序，**不钉序号**、**不钉总数**
- **落盘排在打印之前**；**被挡时也要落盘**；登录判据**未命中就重试**
- ⚠️ **重定向到文件时一律加 `-u`**（914 踩过：块缓冲把日志压在内存、10 分钟 0 行）
- ⚠️ 探针**只输出读数**，判读留给基线

## ⚠️ 本批自己踩到的坑（第一版整个作废、已修）

915 是从 914 改造来的（把「按 `j` 次」改成「按**步骤表**」走）。
**改造时把 913/914 每臂开头那句 `blank()` 顺手删掉了** —— 在新结构里
「每臂开头点一次空白」看着像多余的 setup，于是没保留。

⇒ **第一版第一批读数就撞出来了**：`A-fwd49` 终点 `[29]`（914 同一条臂是 `[40]`）、
首次布的下标 `0`（914 是 `11`）⇒ **走查根本没从画布根起步**。

⚠️ **教训（与 913/914 那条同源，甚至更基础）**：
**改造既有探针时，不要把原探针里那些「看起来多余」的前置动作删掉** ——
它们常常是**承重**的。913/914 每一条臂的有效性都建立在
「**先点空白把焦点归零到画布根、再开始走查**」这个前提上，
而这个前提在代码里只是**一行看起来像 setup 的 `blank()`**。

⇒ 修法不只是补回那句，还要**让探针自己看得见**：
`design_ok` 现在**对基线臂也设门槛**（第一版基线臂写死 `True`，
结果这条臂照样报 ok —— 门槛漏在基线上就等于没有），
并且要求 `init_blank` 真的点到空白。

### 二、⚠️ 「回走 5」那一档**实测是空操作** ⇒ 本批只测到**一种**扰动形状

读数出来后发现：`D2 / G / H` 的「回走 5」这一步
**一次都没布（`armed_idx` 空）、`moved` 全 `False`、终点也没动**
⇒ **那三条臂的前史其实只等于「`fwd 30` + 点空白」**
⇒ **与 `D1 / F` 不是两种扰动，是同一种**。
⚠️ 我**以为**测了两种形状（带回走 / 不带回走），**实际上只测了一种**。

**为什么会空操作**：`fwd 30` 的**最后两次**按压也**一次都没布** ⇒
那一刻焦点落在**某个节点的内层控件**上 ⇒ 随后的 `Shift+Tab`
自然也一次都不布。⇒ 这**第三次**证实了
`source_roving_direction_asymmetry_906` 那条规则
（**按压前焦点在内层控件 ⇒ 一次都不布**，906/909 之后第三次）。

⇒ **教训（与 913/914 同源）**：**扰动步骤自己可能是空操作** ——
「我按了 5 次」**不等于**「前史被扰动了」。
⚠️ 探针现在**每一步都记 `step_effective` / `n_armed` / `n_moved`**
（本批第一版**没有**记，是**读数之后人工看出来**的）
⇒ 下一个人一眼能看出哪一步其实没起作用。

## 计费边界

只按 Tab / Shift+Tab、点画布空白。**绝不**点生成/发送/购买/充值，
**也绝不**点音色 chip 本身。**不点任何节点**（本批的扰动全部由键盘 + 点空白构成）。

跑法：
  ~/.venvs/liblib-harness/bin/python -u scripts/jimeng_headless.py run \
      scripts/jimeng_probe915_prehistory_irrelevance_src.py
"""

import json

OUT = "/tmp/b915-src-prehistory-irrelevance.json"
REPS = 2
N_PRESS = 8            # 回到画布根之后按几次（与 906/908/909/910/913/914 逐字相同）
SETTLE = 300           # 毫秒

# ⚠️ 步骤表：每个元素是 `("fwd"|"back"|"blank", n)`
#    —— `fwd` 连按 `n` 次 `Tab`；`back` 连按 `n` 次 `Shift+Tab`；
#    —— `blank` 点一次画布空白（**把焦点归零到画布根**，这是扰动生效的前提）
ARMS = [
    {"label": "A-fwd49",              "target": 40, "base": True,
     "steps": [("fwd", 49)]},
    {"label": "D1-pre30-fwd49",       "target": 40, "base": False,
     "steps": [("fwd", 30), ("blank", 1), ("fwd", 49)]},
    {"label": "D2-pre30-back5-fwd49", "target": 40, "base": False,
     "steps": [("fwd", 30), ("back", 5), ("blank", 1), ("fwd", 49)]},
    {"label": "B-fwd44",              "target": 35, "base": True,
     "steps": [("fwd", 44)]},
    {"label": "H-pre30-back5-fwd44",  "target": 35, "base": False,
     "steps": [("fwd", 30), ("back", 5), ("blank", 1), ("fwd", 44)]},
    {"label": "E-fwd60",              "target": 51, "base": True,
     "steps": [("fwd", 60)]},
    {"label": "F-pre30-fwd60",        "target": 51, "base": False,
     "steps": [("fwd", 30), ("blank", 1), ("fwd", 60)]},
    {"label": "G-pre30-back5-fwd60",  "target": 51, "base": False,
     "steps": [("fwd", 30), ("back", 5), ("blank", 1), ("fwd", 60)]},
]

# ⚠️⚠️ **静态自检**：扰动臂**必须**含至少一个 `blank` —— 没有它，
# 「前置走查」就没把焦点归零，那条臂根本不是扰动臂（915 版的 913 错）
for _s in ARMS:
    if _s["base"]:
        assert len(_s["steps"]) == 1, "基线臂必须只有一段走查"
        continue
    assert any(k == "blank" for k, _ in _s["steps"]), (
        f"{_s['label']}：**扰动臂必须含至少一个 blank**"
        f"（否则前置走查没把焦点归零、这条臂不是扰动臂）")
    assert len(_s["steps"]) >= 2, f"{_s['label']}：扰动臂必须有多段步骤"

# ⚠️⚠️ **静态自检之二（本批自己撞出来的）**：每个扰动臂的**最后一段走查**
# 必须与**某条基线臂**逐字相同 —— 否则「最终那一段没变」这个前提不成立，
# 那条臂就没有可比对象（`H-pre30-back5-fwd44` 一开始就没有基线臂可比，
# ⚠️ **靠这条 assert 才当场发现**，否则会静默产出一份没对照的读数）
_BASE_LAST = {tuple(_s["steps"][-1:]) for _s in ARMS if _s["base"]}
for _s in ARMS:
    if _s["base"]:
        continue
    assert tuple(_s["steps"][-1:]) in _BASE_LAST, (
        f"{_s['label']}：**最后一段必须与某条基线臂逐字相同**"
        f"（否则这条扰动臂没有可比对象）—— 现有基线末段：{_BASE_LAST}")
print(f"== 静态自检过：{len(ARMS)} 臂，"
      f"{sum(1 for s in ARMS if not s['base'])} 个扰动臂都含 blank、"
      f"且最后一段都能对上基线 ==")

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

# ⚠️ 仪器逐字来自 914 / 913 / 912
INSTALL_JS = """() => {
  const root = document.querySelector('.react-flow');
  if (!root) return {ok: false, why: 'no .react-flow root'};
  if (window.__b915) { window.__b915.cleanup(); }
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
  window.__b915 = {
    log, dump: () => log.slice(),
    since: (f) => log.filter(r => r.seq >= f),
    cursor: () => log.length ? log[log.length - 1].seq + 1 : 0,
    cleanup: () => {
      mo.disconnect();
      document.removeEventListener('focusin', onFocusInCap, true);
      document.removeEventListener('keydown', onKey, true);
      document.removeEventListener('keydown', onKeyEnd, false);
      delete window.__b915;
    },
  };
  return {ok: true, n_nodes: document.querySelectorAll('.react-flow__node').length};
}"""

# ⚠️ 仪器逐字来自 914 / 913 / 912
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
      is_wrapper: !!(a && a.classList
                  && a.classList.contains('react-flow__node'))}};
}"""


def ev(js, arg=None):
    return page.evaluate(js) if arg is None else page.evaluate(js, arg)


def snap(names):
    st = ev(STATE_JS)
    zs = [names.get(t, {}).get("idx") for t in st["zeros"]]
    return {"zeros": zs, "zero_one": (zs[0] if len(zs) == 1 else zs),
            "active_aria": st["active"]["aria"][:22],
            "active_is_wrapper": st["active"]["is_wrapper"]}


def tap(names, mod=False):
    """一次按压：按前焦点 + 布了什么 + 按后落点 + 按后 `'0'`（**带 moved**）。"""
    before = snap(names)
    cur = ev("() => window.__b915.cursor()")
    if mod:
        page.keyboard.down("Shift")
    page.keyboard.press("Tab")
    if mod:
        page.keyboard.up("Shift")
    page.wait_for_timeout(SETTLE)
    seg = ev("(f) => window.__b915.since(f)", cur)
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
            "zero_before": before["zeros"], "zero_after": after["zeros"],
            "moved": before["zeros"] != after["zeros"],
            "land_aria": [f["target_aria"] for f in fi],
            "prevented": (kd[-1].get("default_prevented") if kd else None)}


def blank():
    sp = ev(BLANK_JS)
    if sp:
        page.mouse.click(sp[0], sp[1])
        page.wait_for_timeout(900)
    return sp


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
        for spec in ARMS:
            # ⚠️ **每臂之间 reload**（906 已证明这是必须的）
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
            all_presses = []          # 全部按压（含前置），供 prevented 汇总
            step_recs = []            # 每一步的读数
            design = {}
            blank_hits = []
            try:
                # ⚠️⚠️⚠️ **这句开头的 `blank()` 是承重的**（本批第一版把它删了、
                # 结果第一臂读数直接不可比 —— 详见文末「本批踩到的坑」）
                # 913/914 每一臂都是「先点空白把焦点归零到画布根、再开始走查」
                # ⇒ 少了它，走查就不是从画布根起步、终点会整体偏掉。
                init_blank = blank()
                for si, (kind, cnt) in enumerate(spec["steps"]):
                    if kind == "blank":
                        sp = blank()
                        blank_hits.append(sp)
                        step_recs.append({"step": si, "kind": "blank",
                                          "hit": sp,
                                          "after": snap(names)})
                        continue
                    mod = (kind == "back")
                    presses = [tap(names, mod=mod) for _ in range(cnt)]
                    all_presses.extend(presses)
                    # ⚠️⚠️ **记「这一步到底有没有真的改变状态」** ——
                    # 本批第一版**没有**记， 结果 `D2/G/H` 的「回走 5」是**空操作**
                    # （一次都没布、终点没动）而我以为测了两种扰动。
                    # ⇒ 扰动步骤**自己可能是空操作** ⇒ 必须把它记出来，
                    # 否则「测了两种形状」会变成「其实只测了一种」。
                    step_recs.append({
                        "step": si, "kind": kind, "n": cnt,
                        "armed_idx": [i for p in presses for i in p["armed_idx"]],
                        "moved": [p["moved"] for p in presses],
                        "n_armed": sum(1 for p in presses if p["armed"]),
                        "n_moved": sum(1 for p in presses if p["moved"]),
                        "step_effective": any(p["moved"] or p["armed"]
                                              for p in presses),
                        "after": snap(names)})
                endpoint = snap(names)           # ← **实测终点**
                # ⚠️⚠️ **设计自检**：三条全中才算「只多了前史」的扰动成立
                n_pre_steps = max(0, len(spec["steps"]) - 1)
                pre_fwd = sum(c for k, c in spec["steps"][:-1] if k == "fwd")
                design = {
                    "target": spec["target"],
                    "init_blank_hit": init_blank,
                    "n_pre_steps": n_pre_steps,
                    "pre_forward_presses": pre_fwd,
                    "n_blank_hits": sum(1 for b in blank_hits if b),
                    # ⚠️ **前置的按键步骤里有几个真的改变了状态** ——
                    # `D2/G/H` 的「回走 5」实测是 **0 个**（空操作）⇒ 本批
                    # **只测到一种扰动形状**，详见文末「本批踩到的坑」之二
                    "n_pre_keysteps_effective": sum(
                        1 for st in step_recs[:-1]
                        if st["kind"] != "blank" and st.get("step_effective")),
                    "n_pre_keysteps": sum(
                        1 for st in step_recs[:-1] if st["kind"] != "blank"),
                    "endpoint_zeros": endpoint["zeros"],
                    "reached_target": (endpoint["zero_one"]
                                       == spec["target"]),
                    "design_ok": None,
                }
                # ⚠️⚠️ **基线臂也要设门槛** —— 第一版这里写死 `True`，
                # 结果「开头那句 `blank()` 丢了」这条臂照样报 ok（真踩到了）
                design["design_ok"] = bool(
                    init_blank                       # ① 开头点到了空白（起手焦点在画布根）
                    and design["reached_target"])    # ② 实测终点 == 目标
                if not spec["base"]:
                    design["design_ok"] = bool(
                        design["design_ok"]
                        and n_pre_steps >= 1          # ③ 确实有前置步骤
                        and pre_fwd >= 1              # ④ 前置走查真的走过
                        and design["n_blank_hits"] >= 1)   # ⑤ 前置的 blank 真的点到了
                blank()
                after = [tap(names) for _ in range(N_PRESS)]
            finally:
                try:
                    ev("() => { if (window.__b915) { window.__b915.cleanup(); "
                       "return 'cleaned'; } return 'none'; }")
                except Exception as e:          # noqa: BLE001
                    print(f"  !! cleanup 失败：{e}")

            armed_idx = [i for s in after for i in s["armed_idx"]]
            first = next((s["armed_idx"][0] for s in after
                          if s["armed_idx"]), None)
            rec["arms"].append({
                "label": spec["label"], "base": spec["base"],
                "target": spec["target"],
                "steps": [[k, c] for k, c in spec["steps"]],
                "design": design,
                "step_recs": step_recs,
                "endpoint": endpoint,
                "after_per_press": [
                    {"armed_idx": s["armed_idx"],
                     "pre_aria": s["pre_aria"],
                     "pre_is_wrapper": s["pre_is_wrapper"],
                     "zero_before": s["zero_before"],
                     "zero_after": s["zero_after"],
                     "moved": s["moved"],
                     "land_aria": s["land_aria"][:1],
                     "prevented": s["prevented"]}
                    for s in after],
                "after_armed_idx": armed_idx,
                "after_moved": [s["moved"] for s in after],
                "first_armed_idx": first,
                "prevented_all_false": all(
                    s["prevented"] is False for s in all_presses + after),
            })
            a = rec["arms"][-1]
            flag = "" if a["design"]["design_ok"] is not False else "　**!! 设计违规**"
            print(f"  步骤 {a['steps']} ⇒ 终点 {a['endpoint']['zeros']}"
                  f" ⇒ 回来后 Tab×{N_PRESS} 布 {armed_idx}"
                  f"　**第一次布的下标 = {a['first_armed_idx']}**{flag}")
        runs.append(rec)
        print("  仪器已还原")

    out["runs"] = runs
    out["summary"] = [{
        "rep": r["rep"],
        "arms": [{"label": a["label"], "base": a["base"],
                  "target": a["target"],
                  "design_ok": a["design"].get("design_ok"),
                  "reached_target": a["design"].get("reached_target"),
                  "init_blank_hit": a["design"].get("init_blank_hit"),
                  "n_pre_steps": a["design"].get("n_pre_steps"),
                  "n_blank_hits": a["design"].get("n_blank_hits"),
                  "endpoint_zeros": a["endpoint"]["zeros"],
                  "first_armed_idx": a["first_armed_idx"],
                  "after_armed_idx": a["after_armed_idx"],
                  "prevented_all_false": a["prevented_all_false"]}
                 for a in r["arms"]],
    } for r in runs]
    out["verdict"] = "sampled"

    # ⚠️ 落盘**必须**排在打印之前（900 的教训）
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print("\n== 汇总（只输出读数，**不判机制**）==")
    for row in out["summary"]:
        print(f"  rep{row['rep']}")
        for a in row["arms"]:
            ep = (a["endpoint_zeros"][0]
                  if len(a["endpoint_zeros"]) == 1 else (a["endpoint_zeros"] or "∅"))
            ok = {True: "ok", False: "**设计违规**", None: "-"}[a["design_ok"]]
            print(f"    {a['label']:<24s} 设计{ok:<12s} 目标={a['target']:<4d}"
                  f" 起手blank={'命中' if a['init_blank_hit'] else '**没中**'}"
                  f" 前史步={a['n_pre_steps']} 点空白命中={a['n_blank_hits']}"
                  f" ⇒ 终点={str(ep):<5s} ⇒ 第一次布的下标 = "
                  f"{str(a['first_armed_idx']):<5s} 全程布 {a['after_armed_idx']}")
    print(f"\n== 已写 {OUT} ==")

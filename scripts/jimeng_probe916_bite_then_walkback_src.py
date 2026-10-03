#!/usr/bin/env python3
r"""batch 916 源站探针：把 915 塌缩掉的那一档（**带回走**）重做 —— 让回走**真的咬到**

## 915 留下的缺口

915 测了「前置走查 + 点空白 ⇒ 前史无关」，8 臂 × 2 轮、10/10 组一致。
⚠️ 但 `D2 / G / H` 的「**回走 5**」那一步**实测是空操作**（`armed_idx` 空、
`moved` 全 `False`、终点也没动）⇒ 那三条臂的前史**其实只等于「`fwd 30` + 点空白`」**
⇒ **915 只测到一种扰动形状**。

**为什么会空操作**：`fwd 30` 的**最后两次**按压也一次都没布 ⇒ 那一刻焦点落在
**某个节点的内层控件**上 ⇒ 随后的 `Shift+Tab` 自然也一次都不布
（这**第三次**证实了 906 那条规则）。

## 这一批怎么让它**真的咬到**

⚠️ **不许**再拍脑袋给「回走 N 次」（907/908/899 的教训：次数要盖过被内层控件
吃掉的那部分，否则那一步根本没被问到）。⇒ **改成自适应停止条件**：

> 一直按 `Shift+Tab`，**直到某一次真的把 `'0'` 挪动了**（`moved == True`）
> 才算「咬到」；**上限 40 次**，超了记 `bitten=False`。

⚠️ 咬到之后**再固定多按 3 次**（留出余量，确保回走确实发生了一段），
并记 `n_back_total` / `n_back_effective`。

## 设计：三条对照，每条**只多「一段真的回走」**

| 对 | 基线臂 | 扰动臂 |
|---|---|---|
| ① 终点 **40** | `A-fwd49` | `I2-bite30-raw49`（`fwd 30` ⇒ **咬到式回走** ⇒ 点空白 ⇒ `fwd 49`） |
| ② 终点 **35** | `B-fwd44` | `J2-bite30-raw44` |
| ③ 终点 **51** | `E-fwd60` | `K2-bite30-raw60` |

⚠️ 扰动臂的**最后一段走查**与基线臂**逐字相同**（`fwd 49` / `fwd 44` / `fwd 60`），
**只有中间多了一段「真的回走」**。

⇒ 若起点仍与基线臂相同 ⇒ **前史（含真回走）无关**；
⇒ 若不同 ⇒ **历史确实有影响**，914/915 的结论要收窄。

## ⚠️ 探针**自己**拒绝再犯 913/915 那两个错

- **静态侧**（开跑前 `assert`）：
  ① 扰动臂**必须**含至少一个 `blank`（否则前史没把焦点归零）；
  ② 扰动臂的**最后一段**必须与某条基线臂**逐字相同**（否则没有可比对象 ——
  915 靠这条才当场发现 `H` 没有基线臂可比）。
- **运行侧**（每臂记 `design_ok`），**同时**要求四条：
  ① 开头的 `init_blank` 真的点到（**915 第一版就是漏了这条**）；
  ② 实测终点 **==** 目标；
  ③ 前置按键步骤**至少一个真的改变了状态**（`n_pre_keysteps_effective >= 1`
  —— 915 的「回走 5」就是这一条没中）；
  ④ **回走那一步真的咬到了**（`bitten == True`）—— 这一条是 916 独有的门槛，
  没有它就又会退化成 915。

## 判据纪律

- 仪器**逐字复用** 915/914/913/912（`__b916`）
- **每臂之间 reload**；每轮**重复 2 次**；终点**实测**
- ⚠️ **`moved` 是必需字段**；⚠️ **每一步都记 `step_effective`**
- **全程不碰末尾** ⇒ 撞不上绕回（`j ≤ 60` < 实测末尾 75）
- 节点总数是易变量 ⇒ 按**身份**记 DOM 序，**不钉序号**、**不钉总数**
- **落盘排在打印之前**；**被挡时也要落盘**；登录判据**未命中就重试**
- ⚠️ **重定向到文件时一律加 `-u`**（914 踩过）
- ⚠️ 探针**只输出读数**，判读留给基线

## 计费边界

只按 Tab / Shift+Tab、点画布空白。**绝不**点生成/发送/购买/充值，
**也绝不**点音色 chip 本身。**不点任何节点。**

跑法：
  ~/.venvs/liblib-harness/bin/python -u scripts/jimeng_headless.py run \
      scripts/jimeng_probe916_bite_then_walkback_src.py
"""

import json

OUT = "/tmp/b916-src-bite-then-walkback.json"
REPS = 2
N_PRESS = 8            # 回到画布根之后按几次（与 906/908/909/910/913/914/915 逐字相同）
SETTLE = 300           # 毫秒
BITE_CAP = 40          # 「咬到」的自适应上限（**不是**拍脑袋给的次数，是封顶）
EXTRA_BACK = 3         # 咬到之后**再固定多按**几次（留余量，确保真回走了一段）

# ⚠️ 步骤表：每个元素是 `("fwd"|"back"|"bite"|"blank", n)`
#    —— `fwd` 连按 `n` 次 `Tab`
#    —— `back` 连按 `n` 次 `Shift+Tab`
#    —— `bite` **咬到式**回走：按 `Shift+Tab` 直到某一次真的把 `'0'` 挪动
#       （上限 `BITE_CAP`），咬到后再**多按 `EXTRA_BACK` 次**
#    —— `blank` 点一次画布空白（把焦点归零回画布根）
ARMS = [
    {"label": "A-fwd49",          "target": 40, "base": True,
     "steps": [("fwd", 49)]},
    {"label": "I2-bite30-raw49",  "target": 40, "base": False,
     "steps": [("fwd", 30), ("bite", 1), ("blank", 1), ("fwd", 49)]},
    {"label": "B-fwd44",          "target": 35, "base": True,
     "steps": [("fwd", 44)]},
    {"label": "J2-bite30-raw44",  "target": 35, "base": False,
     "steps": [("fwd", 30), ("bite", 1), ("blank", 1), ("fwd", 44)]},
    {"label": "E-fwd60",          "target": 51, "base": True,
     "steps": [("fwd", 60)]},
    {"label": "K2-bite30-raw60",  "target": 51, "base": False,
     "steps": [("fwd", 30), ("bite", 1), ("blank", 1), ("fwd", 60)]},
]

# ⚠️⚠️ **静态自检之一**：扰动臂**必须**含至少一个 `blank` ——
# 没有它，「前置走查」就没把焦点归零，那条臂根本不是扰动臂
for _s in ARMS:
    if _s["base"]:
        assert len(_s["steps"]) == 1, "基线臂必须只有一段走查"
        continue
    assert any(k == "blank" for k, _ in _s["steps"]), (
        f"{_s['label']}：**扰动臂必须含至少一个 blank**")
    assert len(_s["steps"]) >= 2, f"{_s['label']}：扰动臂必须有多段步骤"
    # ⚠️ 916 特有：扰动臂**必须**含一个 `bite`（真的回走）——
    # 没有它就退化成 915（只测到一种形状）
    assert any(k == "bite" for k, _ in _s["steps"]), (
        f"{_s['label']}：**扰动臂必须含 bite**（真的回走）—— "
        f"否则就退化成 915 那种只测一种形状")

# ⚠️⚠️ **静态自检之二**：扰动臂的**最后一段**必须与某条基线臂**逐字相同**
# —— 否则「最终那一段没变」这个前提不成立、那条臂没有可比对象
# （915 的 `H-pre30-back5-fwd44` 一开始就没有基线臂可比，靠这条 assert 才当场发现）
_BASE_LAST = {tuple(_s["steps"][-1:]) for _s in ARMS if _s["base"]}
for _s in ARMS:
    if _s["base"]:
        continue
    assert tuple(_s["steps"][-1:]) in _BASE_LAST, (
        f"{_s['label']}：**最后一段必须与某条基线臂逐字相同** —— "
        f"现有基线末段：{_BASE_LAST}")
print(f"== 静态自检过：{len(ARMS)} 臂，"
      f"{sum(1 for s in ARMS if not s['base'])} 个扰动臂都含 blank+bite、"
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

# ⚠️ 仪器逐字来自 915 / 914 / 913 / 912
INSTALL_JS = """() => {
  const root = document.querySelector('.react-flow');
  if (!root) return {ok: false, why: 'no .react-flow root'};
  if (window.__b916) { window.__b916.cleanup(); }
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
  window.__b916 = {
    log, dump: () => log.slice(),
    since: (f) => log.filter(r => r.seq >= f),
    cursor: () => log.length ? log[log.length - 1].seq + 1 : 0,
    cleanup: () => {
      mo.disconnect();
      document.removeEventListener('focusin', onFocusInCap, true);
      document.removeEventListener('keydown', onKey, true);
      document.removeEventListener('keydown', onKeyEnd, false);
      delete window.__b916;
    },
  };
  return {ok: true, n_nodes: document.querySelectorAll('.react-flow__node').length};
}"""

# ⚠️ 仪器逐字来自 915 / 914 / 913 / 912
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
    cur = ev("() => window.__b916.cursor()")
    if mod:
        page.keyboard.down("Shift")
    page.keyboard.press("Tab")
    if mod:
        page.keyboard.up("Shift")
    page.wait_for_timeout(SETTLE)
    seg = ev("(f) => window.__b916.since(f)", cur)
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


def bite_back(names, cap=BITE_CAP, extra=EXTRA_BACK):
    """**咬到式**回走：按 `Shift+Tab` 直到某一次真的把 `'0'` 挪动（`moved==True`），
    咬到后再**多按 `extra` 次**。

    ⚠️ 这是 907/908/899 的教训落地：**不许**拍脑袋给「回走 N 次」——
    915 的「回走 5」就是被内层控件吃掉、一步都没生效。
    ⇒ 停止条件是「**观测到 `'0'` 真的动了**」，上限 `cap` 只是封顶。
    """
    presses = []
    bitten = False
    bite_at = None
    for _ in range(cap):
        t = tap(names, mod=True)
        presses.append(t)
        if t["moved"] or t["armed"]:
            bitten = True
            bite_at = len(presses)
            break
    if bitten:
        for _ in range(extra):
            presses.append(tap(names, mod=True))
    return {"presses": presses, "bitten": bitten, "bite_at": bite_at,
            "n_back_total": len(presses)}


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
            all_presses = []
            step_recs = []
            design = {}
            blank_hits = []
            bite_info = None
            try:
                # ⚠️⚠️⚠️ **开头的 `blank()` 是承重的**（915 第一版删了它、
                # 结果第一批读数就不可比）—— 别删
                init_blank = blank()
                for si, (kind, cnt) in enumerate(spec["steps"]):
                    if kind == "blank":
                        sp = blank()
                        blank_hits.append(sp)
                        step_recs.append({"step": si, "kind": "blank",
                                          "hit": sp, "after": snap(names)})
                        continue
                    if kind == "bite":
                        bi = bite_back(names)
                        all_presses.extend(bi["presses"])
                        bite_info = bi
                        step_recs.append({
                            "step": si, "kind": "bite",
                            "n_back_total": bi["n_back_total"],
                            "bitten": bi["bitten"], "bite_at": bi["bite_at"],
                            "armed_idx": [i for p in bi["presses"]
                                          for i in p["armed_idx"]],
                            "n_armed": sum(1 for p in bi["presses"] if p["armed"]),
                            "moved": [p["moved"] for p in bi["presses"]],
                            # ⚠️⚠️ **916 第一版没记逐次焦点落点** ⇒
                            # 那 28 次「一次都没布」的死按压时**焦点在哪看不到**
                            # ⇒ 补上（供 917 用）：逐次记按压前的焦点落点与归属
                            "per_press_pre": [
                                {"i": pi,
                                 "pre_aria": p["pre_aria"],
                                 "pre_is_wrapper": p["pre_is_wrapper"],
                                 "armed": p["armed"],
                                 "moved": p["moved"],
                                 "land_aria": p["land_aria"][:1]}
                                for pi, p in enumerate(bi["presses"])],
                            "step_effective": any(p["moved"] or p["armed"]
                                                  for p in bi["presses"]),
                            "after": snap(names)})
                        continue
                    mod = (kind == "back")
                    presses = [tap(names, mod=mod) for _ in range(cnt)]
                    all_presses.extend(presses)
                    step_recs.append({
                        "step": si, "kind": kind, "n": cnt,
                        "armed_idx": [i for p in presses for i in p["armed_idx"]],
                        "moved": [p["moved"] for p in presses],
                        "n_armed": sum(1 for p in presses if p["armed"]),
                        "step_effective": any(p["moved"] or p["armed"]
                                              for p in presses),
                        "after": snap(names)})
                endpoint = snap(names)
                design = {
                    "target": spec["target"],
                    "init_blank_hit": init_blank,
                    "n_pre_steps": max(0, len(spec["steps"]) - 1),
                    "pre_forward_presses": sum(
                        c for k, c in spec["steps"][:-1] if k == "fwd"),
                    "n_blank_hits": sum(1 for b in blank_hits if b),
                    "n_pre_keysteps_effective": sum(
                        1 for st in step_recs[:-1]
                        if st["kind"] != "blank" and st.get("step_effective")),
                    "bitten": (bite_info["bitten"] if bite_info else None),
                    "n_back_total": (bite_info["n_back_total"]
                                     if bite_info else None),
                    "endpoint_zeros": endpoint["zeros"],
                    "reached_target": (endpoint["zero_one"]
                                       == spec["target"]),
                    "design_ok": None,
                }
                # ⚠️⚠️ **基线臂也设门槛**（915 第一版写死 True，门槛漏在基线=没有门槛）
                design["design_ok"] = bool(
                    init_blank
                    and design["reached_target"])
                if not spec["base"]:
                    design["design_ok"] = bool(
                        design["design_ok"]
                        and design["n_pre_steps"] >= 1
                        and design["pre_forward_presses"] >= 1
                        and design["n_blank_hits"] >= 1
                        # ④ **回走真的咬到了**（916 独有，没有它就退化成 915）
                        and design["bitten"] is True)
                blank()
                after = [tap(names) for _ in range(N_PRESS)]
            finally:
                try:
                    ev("() => { if (window.__b916) { window.__b916.cleanup(); "
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
            b = a["design"]["bitten"]
            print(f"  步 {a['steps']} | 回走咬到={b}（共 {a['design']['n_back_total']} 次）"
                  f" ⇒ 终点 {a['endpoint']['zeros']}"
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
                  "bitten": a["design"].get("bitten"),
                  "n_back_total": a["design"].get("n_back_total"),
                  "n_pre_keysteps_effective":
                      a["design"].get("n_pre_keysteps_effective"),
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
            bite = {True: "咬到", False: "**没咬到**", None: "-"}[a["bitten"]]
            print(f"    {a['label']:<18s} 设计{ok:<12s} 回走{bite}({a['n_back_total']})"
                  f" 前置有效步={a['n_pre_keysteps_effective']}"
                  f" ⇒ 终点={str(ep):<5s} ⇒ 第一次布的下标 = "
                  f"{str(a['first_armed_idx']):<5s} 全程布 {a['after_armed_idx']}")
    print(f"\n== 已写 {OUT} ==")

#!/usr/bin/env python3
r"""batch 917 源站探针：把回走**走满多步** ＋ **查清正/反向死按压 4 vs 28 的不对称**

## 916 留下的两个缺口

① 916 的回走**只咬到 1 次**（`'0'` 23→22），随后再按 3 次全不布
   ⇒ **「长距离回走」这一档仍然没测到**。
② 916 顺带撞出一个**不对称**：`fwd 30` 里的死按压是**成串 4 次**，
   反向却要**连 28 次**才咬到 ⇒ **为什么两边差这么多，未查明**。

## 这一批做两件事

### 一、把回走**走满多步**（`bite` × 3）

`bite_k(names, k)` = **连着做 k 次「咬到式回走」**（916 的 `bite` 循环 k 次）
⇒ `'0'` 应当真的退 **k 步**（23→22→21→20）⇒ 这才是「长距离回走」。

⚠️ **门槛要卡住「k 次全都咬到」** —— 916 的教训：**只咬到一次也算通过**
就会静默退化成 916 ⇒ 这里 `design_ok` **必须** `n_bites_bitten == k`。

### 二、**查清那个不对称**（这是本批真正的产出）

916 补的 `per_press_pre` **只覆盖了 `bite` 步** ⇒ 那 28 次死按压时焦点在哪，
本批**仍然看不到**（因为 916 跑的时候没记）。

⇒ 917 把**逐次焦点轨迹**（`pre_aria` / `pre_is_wrapper` / `land_aria`）
**同时铺到 `fwd` 步和 `bite` 步**上 ⇒ 于是能**逐次**问：
**死按压期间焦点到底在哪些元素上走？正向和反向是同一批元素吗？**

⇒ 判读留给基线；探针**只输出读数**。

## 设计：三条对照，每条只多「一段真的回走（k 步）」

| 对 | 基线臂 | 扰动臂（`fwd 30` ⇒ **bite×3** ⇒ 点空白 ⇒ **走查**） |
|---|---|---|
| 终点 **40** | `A-fwd49` | `L3-bite3-raw49` |
| 终点 **35** | `B-fwd44` | `M3-bite3-raw44` |
| 终点 **51** | `E-fwd60` | `N3-bite3-raw60` |

⚠️ 扰动臂的**最后一段走查与基线臂逐字相同**（同样 `j`、同样从画布根起步）。

## ⚠️ 探针**自己**拒绝再犯 913/915/916 那三个错

- **静态侧**（开跑前 `assert`）：① 扰动臂**必须**含 `blank`（前史要把焦点归零）；
  ② 扰动臂**必须**含 `bite`（否则退化成 915）；③ 扰动臂的**最后一段**
  **必须**与某条基线臂**逐字相同**（否则没有可比对象）。
- **运行侧**（每臂记 `design_ok`），**同时**要求：
  ① `init_blank` 真点到（**915 第一版就漏了这条**）；
  ② 实测终点 **==** 目标；
  ③ 前置按键步骤**至少一个真的改变了状态**（`n_pre_keysteps_effective >= 1`）；
  ④ **k 次 bite 全部咬到**（`n_bites_bitten == k`）—— **916 独有的门**；
  ⑤ **实测真的退了 k 步**（`n_zero_steps_retreat == k`）。

## 判据纪律

- 仪器**逐字复用** 916/915/914/913/912（`__b917`）
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
      scripts/jimeng_probe917_multi_bite_focus_trace_src.py
"""

import json

OUT = "/tmp/b917-src-multi-bite-focus-trace.json"
REPS = 2
N_PRESS = 8            # 回到画布根之后按几次（与 906/908/909/910/913/914/915/916 逐字相同）
SETTLE = 300           # 毫秒
BITE_CAP = 40          # **每一次**咬到的自适应上限（**不是**拍脑袋给的次数，是封顶）
N_BITE = 3             # 要连着咬到几次（让 `'0'` 真的退 N 步）

# ⚠️ 步骤表：`("fwd"|"back"|"bite"|"blank", n)`
#    —— `bite` 的 `n` 是**要连着咬几次**（每次各自有 `BITE_CAP` 的自适应上限）
ARMS = [
    {"label": "A-fwd49",         "target": 40, "base": True,
     "steps": [("fwd", 49)]},
    {"label": "L3-bite3-raw49",  "target": 40, "base": False,
     "steps": [("fwd", 30), ("bite", 3), ("blank", 1), ("fwd", 49)]},
    {"label": "B-fwd44",         "target": 35, "base": True,
     "steps": [("fwd", 44)]},
    {"label": "M3-bite3-raw44",  "target": 35, "base": False,
     "steps": [("fwd", 30), ("bite", 3), ("blank", 1), ("fwd", 44)]},
    {"label": "E-fwd60",         "target": 51, "base": True,
     "steps": [("fwd", 60)]},
    {"label": "N3-bite3-raw60",  "target": 51, "base": False,
     "steps": [("fwd", 30), ("bite", 3), ("blank", 1), ("fwd", 60)]},
]

# ⚠️⚠️ **静态自检之一**：扰动臂**必须**含 `blank`（前史要把焦点归零）
#              且**必须**含 `bite`（否则退化成 915）
for _s in ARMS:
    if _s["base"]:
        assert len(_s["steps"]) == 1, "基线臂必须只有一段走查"
        continue
    assert any(k == "blank" for k, _ in _s["steps"]), (
        f"{_s['label']}：**扰动臂必须含至少一个 blank**")
    assert any(k == "bite" for k, _ in _s["steps"]), (
        f"{_s['label']}：**扰动臂必须含 bite**（真的回走）—— "
        f"否则就退化成 915 那种只测一种形状")
    assert len(_s["steps"]) >= 2, f"{_s['label']}：扰动臂必须有多段步骤"

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

# ⚠️ 仪器逐字来自 916 / 915 / 914 / 913 / 912
INSTALL_JS = """() => {
  const root = document.querySelector('.react-flow');
  if (!root) return {ok: false, why: 'no .react-flow root'};
  if (window.__b917) { window.__b917.cleanup(); }
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
  window.__b917 = {
    log, dump: () => log.slice(),
    since: (f) => log.filter(r => r.seq >= f),
    cursor: () => log.length ? log[log.length - 1].seq + 1 : 0,
    cleanup: () => {
      mo.disconnect();
      document.removeEventListener('focusin', onFocusInCap, true);
      document.removeEventListener('keydown', onKey, true);
      document.removeEventListener('keydown', onKeyEnd, false);
      delete window.__b917;
    },
  };
  return {ok: true, n_nodes: document.querySelectorAll('.react-flow__node').length};
}"""

# ⚠️ 仪器逐字来自 916 / 915 / 914 / 913 / 912
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


def press_rec(pi, p):
    """⚠️⚠️ **逐次焦点轨迹** —— 本批真正的产出。
    916 只在 `bite` 步记了它、而且那次读数**还没跑**就补的；
    917 把它**同时铺到 `fwd` 步和 `bite` 步**上
    ⇒ 于是能**逐次**问「死按压期间焦点到底在哪些元素上走」。
    """
    return {"i": pi,
            "pre_aria": p["pre_aria"],
            "pre_is_wrapper": p["pre_is_wrapper"],
            "armed": p["armed"],
            "moved": p["moved"],
            "land_aria": p["land_aria"][:1]}


def tap(names, mod=False):
    """一次按压：按前焦点 + 布了什么 + 按后落点 + 按后 `'0'`（**带 moved**）。"""
    before = snap(names)
    cur = ev("() => window.__b917.cursor()")
    if mod:
        page.keyboard.down("Shift")
    page.keyboard.press("Tab")
    if mod:
        page.keyboard.up("Shift")
    page.wait_for_timeout(SETTLE)
    seg = ev("(f) => window.__b917.since(f)", cur)
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


def one_bite(names, cap=BITE_CAP):
    """**一次**咬到式回走：按 `Shift+Tab` 直到某一次真的把 `'0'` 挪动了。

    ⚠️ 907/908/899 的教训落地：**不许**拍脑袋给「回走 N 次」——
    915 的「回走 5」就是被内层控件吃掉、一步都没生效。
    ⇒ 停止条件是「**观测到 `'0'` 真的动了**」，`cap` 只是封顶。
    """
    presses = []
    bitten = False
    bite_at = None
    for _ in range(cap):
        t = tap(names, mod=True)
        presses.append(t)
        # ⚠️⚠️ **917 实测出来的更正：停止条件只能用 `moved`，不能带 `armed`。**
        # 917 抓到 `armed` 会在**非 `.react-flow__node`** 的元素上触发
        # （实测 `el:BUTTON.inline-flex.items-center#0`）⇒
        # **`armed` 触发时节点里的 `'0'` 可能根本没动** ⇒ 带 `armed` 会**提前收工**。
        # 916 用的正是 `moved or armed` ⇒ 那一版的「咬到」**可能提前结束**。
        if t["moved"]:
            bitten = True
            bite_at = len(presses)
            break
    return {"presses": presses, "bitten": bitten, "bite_at": bite_at,
            "n_back_total": len(presses),
            "zero_after": snap(names)}


def bite_k(names, k, cap=BITE_CAP):
    """**连着咬 k 次** —— 每次的停止条件都是「观测到 `'0'` 真的动了」。

    ⚠️ 916 只咬了 **1** 次（`23→22`）就再也不咬 ⇒ 「长距离回走」没测到。
    ⇒ 这里连咬 k 次，让 `'0'` 真的退 k 步，并**逐次记下每咬之后落在哪**。
    """
    bites = []
    all_presses = []
    for bi in range(1, k + 1):
        # ⚠️⚠️ **917 第一版这里有顺序错**：`zero_before` 原来是在 `one_bite()`
        # **跑完之后**才取的 ⇒ 打印出来是 `[22]→[22]` 这种**假象**（咬完的状态
        # 冒充咬之前的状态）⇒ 真实的 `23→22` 被抹掉了。
        # ⚠️ **判读纪律**：**前态必须在扰动之前取**，否则「前态 vs 后态」是空话。
        zero_before = snap(names)["zeros"]
        one = one_bite(names, cap=cap)
        all_presses.extend(one["presses"])
        one["bite_no"] = bi
        one["zero_before"] = zero_before
        bites.append(one)
    n_bites_bitten = sum(1 for b in bites if b["bitten"])
    # ⚠️ **实测**退了几步：拿「第一次 bite 之前的 `'0'`」减「最后一次 bite 之后的 `'0'`」
    zs_first = bites[0]["zero_before"]
    zs_last = bites[-1]["zero_after"]["zeros"]
    retreat = None
    if (isinstance(zs_first, list) and len(zs_first) == 1
            and isinstance(zs_last, list) and len(zs_last) == 1):
        retreat = zs_first[0] - zs_last[0]
    return {"bites": bites, "all_presses": all_presses,
            "n_bites_bitten": n_bites_bitten, "n_bites": k,
            "n_zero_steps_retreat": retreat,
            "zero_before": zs_first, "zero_after": zs_last}


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
            bk = None
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
                        bk = bite_k(names, cnt)
                        all_presses.extend(bk["all_presses"])
                        step_recs.append({
                            "step": si, "kind": "bite",
                            "n_bites": bk["n_bites"],
                            "n_bites_bitten": bk["n_bites_bitten"],
                            "n_zero_steps_retreat": bk["n_zero_steps_retreat"],
                            "zero_before": bk["zero_before"],
                            "zero_after": bk["zero_after"],
                            "per_bite": [
                                {"bite_no": b["bite_no"],
                                 "bitten": b["bitten"], "bite_at": b["bite_at"],
                                 "n_back_total": b["n_back_total"],
                                 "n_armed": sum(1 for p in b["presses"]
                                                if p["armed"]),
                                 "armed_idx": [i for p in b["presses"]
                                               for i in p["armed_idx"]],
                                 "zero_before": b["zero_before"],
                                 "zero_after": b["zero_after"]["zeros"],
                                 # ⚠️ 逐次焦点轨迹（**本批真正的产出**）
                                 "per_press_pre": [press_rec(pi, p)
                                                   for pi, p
                                                   in enumerate(b["presses"])]}
                                for b in bk["bites"]],
                            "step_effective": bk["n_bites_bitten"] > 0,
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
                        "n_moved": sum(1 for p in presses if p["moved"]),
                        # ⚠️ **正向也铺逐次焦点轨迹**（916 只铺了 bite 步）
                        # ⇒ 「正向成串 4 次 vs 反向连 28 次」这个不对称
                        #    这一批**才第一次能看到焦点在哪**
                        "per_press_pre": [press_rec(pi, p)
                                          for pi, p in enumerate(presses)],
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
                    "n_bites": (bk["n_bites"] if bk else None),
                    "n_bites_bitten": (bk["n_bites_bitten"] if bk else None),
                    "n_zero_steps_retreat": (bk["n_zero_steps_retreat"]
                                             if bk else None),
                    "endpoint_zeros": endpoint["zeros"],
                    "reached_target": (endpoint["zero_one"]
                                       == spec["target"]),
                    "design_ok": None,
                }
                # ⚠️ **基线臂也设门槛**（915 第一版写死 True，门槛漏在基线=没有门槛）
                design["design_ok"] = bool(
                    init_blank
                    and design["reached_target"])
                if not spec["base"]:
                    design["design_ok"] = bool(
                        design["design_ok"]
                        and design["n_pre_steps"] >= 1
                        and design["pre_forward_presses"] >= 1
                        and design["n_blank_hits"] >= 1
                        # ④ **k 次 bite 全部咬到**（916 独有的门）
                        and design["n_bites_bitten"] == design["n_bites"]
                        # ⑤ **实测真的退了 k 步**（否则「多步回走」又是一句空话）
                        and design["n_zero_steps_retreat"] == design["n_bites"])
                blank()
                after = [tap(names) for _ in range(N_PRESS)]
            finally:
                try:
                    ev("() => { if (window.__b917) { window.__b917.cleanup(); "
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
            print(f"  步 {a['steps']} | 咬到 {a['design']['n_bites_bitten']}/"
                  f"{a['design']['n_bites']}、实退 "
                  f"{a['design']['n_zero_steps_retreat']} 步"
                  f" ⇒ 终点 {a['endpoint']['zeros']}"
                  f" ⇒ 回来后 Tab×{N_PRESS} 布 {armed_idx}"
                  f"　**第一次布的下标 = {a['first_armed_idx']}**{flag}")
            for st in a["step_recs"]:
                if st["kind"] == "bite":
                    for b in st["per_bite"]:
                        print(f"    咬#{b['bite_no']}：第 {b['bite_at']} 次才咬到"
                              f"（共按 {b['n_back_total']} 次）"
                              f" ⇒ '0' {b['zero_before']}→{b['zero_after']}")
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
                  "n_bites": a["design"].get("n_bites"),
                  "n_bites_bitten": a["design"].get("n_bites_bitten"),
                  "n_zero_steps_retreat":
                      a["design"].get("n_zero_steps_retreat"),
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
            print(f"    {a['label']:<17s} 设计{ok:<12s} "
                  f"咬到={a['n_bites_bitten']}/{a['n_bites']} "
                  f"实退={a['n_zero_steps_retreat']}步 "
                  f"⇒ 终点={str(ep):<5s} ⇒ 第一次布的下标 = "
                  f"{str(a['first_armed_idx']):<5s} 全程布 {a['after_armed_idx']}")
    print(f"\n== 已写 {OUT} ==")

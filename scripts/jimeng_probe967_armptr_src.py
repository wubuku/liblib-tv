#!/usr/bin/env python3
"""batch 967 源站探针：900 的「从没被布上 `'0'`」与 963 的「从没被 `Tab` 落到」
   **是不是两个不同的可观测量**？那枚「被落上、却从没被布」的节点是**哪条路**进来的？

## 要解释的现象（两处读数并排，⚠️ 它们**从来没有被放在同一张表里对过账**）

| 量 | 批次 | 读到的集合（76 个节点里漏掉的） |
|---|---|---|
| 「**被布上 `'0'`**」 | 900 | **漏 2 个**：下标 12 `图片 node: b22-upload`、下标 68 `音频 node: 音频 61` |
| 「**被 `Tab` 落到**」 | 963 | **漏 1 个**：下标 68 |

⇒ 两个集合**不相等**（963/966 已证下标 12 **被落到了 2 次**：seq 17 / seq 118）
⇒ ⇒ **它们量的不是同一件事**（这正是本批的来由），但**「布 `'0'`」在什么时刻
   才存在**从来没被单独量过 —— 966 的 `FOCUSMOVE_JS` 只记了 `{armed: true}`
   这个**闩锁**，**没记是哪一枚** ⇒ **900 那个数至今无法复核**。

## 这一批只做三件事（**全部纯读 + 只发 `Tab`**）

1. **每一按在 4 个取样点各读一次**「带 `tabindex='0'` 的节点**全量**集合」：
   `c0`（`window` 捕获 = 派发**最前**）、`b2`（`window` 冒泡 = 派发**末尾**）、
   `task`（`window` 捕获里排的 `setTimeout(0)` = 浏览器默认动作之后）、
   `after`（按完 `SETTLE` 之后的纯读）。
   ⚠️ **不预设哪个取样点能抓到 `'0'`** —— 965 已经证明按后属性已被摘掉，
   所以这里把四个点**都**记下来，由读数说话（**不猜机制**，891 的教训）。
2. **每一按记 `focusin` 落在哪个元素上**，并分三类：
   `self`（**节点本体**）/ `inner`（**节点的内层控件**）/ `out`（节点之外）。
   ⚠️ 963 那套「落到没有」把 `self` 与 `inner` **合在一起**算 ⇒ 这里拆开。
3. **对账三个集合**（全部按 **`data-testid` 身份**，⚠️ **不按绝对下标** ——
   绝对下标逐轮会漂，961 已量过）：`ever_armed` / `ever_landed_self` /
   `ever_landed_inner`，再看两两之差。

## ⚠️ 本批的纪律（承 942–966 的教训，逐条对应）

1. ⭐ **一个错的判据比没有判据更坏** ⇒ 「布 `'0'` 的时刻」**不预设**，
   由四个取样点自己说话
2. ⭐ **恒真/恒假判据比没有判据更坏** ⇒ 每道门都挂在**独立分母**上：
   `n_fired`（监听器真的响了几次）/ `n_install`（装了几次）/
   `n_nodes_hist` 的**取值个数**（普查期间节点数变没变）
3. ⭐ **诊断动作必须还原** ⇒ 装/摘**成对**（`__ap_off`），且 `INSTALL_JS`
   **幂等**（装之前先摘干净 ⇒ 连按两次也不会叠监听器）；摘完再复查 `__ap_off` 是 null
4. ⭐ **表首格不写裸数字**、派生键不许与原始键重叠/重名/漏登记
5. ⭐ **逐字复用 + 断言**：尺子（`BLANK_JS`/`CENSUS_JS`/`FOCUS_JS`/`WHOAMI_JS`/
   `NODECENSUS_JS`/`boot_fn`）**逐字来自 966**，`assert _js in _p966src` 证明；
   **新件**反过来断言**不在** 966 里
6. ⭐ **切片守卫**：任何 `.slice(` 都必须紧挨着 `|| '').slice(0, `
7. ⭐ **两轮比较必须在 `for rep` 循环之外**，且**按身份**比不按下标
8. ⭐ **落盘排在所有后处理之前**
9. ⭐ **不许编机制**：对不上就写「仍未查明」
10. ⚠️⚠️ **复制/插入时必须核「名字」和「函数体」是不是同一对**（966 栽过：
    `READ_FT_JS` 名 + `READ_FM_JS` 体 ⇒ 同名覆盖 ⇒ `NameError`）

## 计费边界

**本批零计费动作。** 每轮只在开头点**一次画布空白**去焦点，⛔ 守卫拦在
`mouse.click` **之前**；其余**只发 `Tab`**、不点任何东西。

跑法：
  ~/.venvs/liblib-harness/bin/python -u scripts/jimeng_headless.py run \
      scripts/jimeng_probe967_armptr_src.py
"""

import json
import pathlib
import textwrap

OUT = "/tmp/b967-armptr.json"
REPS = 2
SETTLE = 350        # ms（照 952–966 的同一常量）
BLANK_WAIT = 900    # ms（照 952–966 的同一常量）
RAIL_TID = "canvas-fixed-toolbar"      # ⭐ 两边共用的锚点（复刻侧逐字相同）
N_LEAD_CAP = 140    # ⭐ 硬上限，不是目标（照 966）

FORBIDDEN_TIDS = ("canvas-commerce-entry", "canvas-pay-trigger",
                  "canvas-recharge")
BILLED_EXACT = ("生成", "发送", "购买", "充值", "立即支付", "开通", "订阅", "兑换")
BILLED_PREFIX = ("立即", "购买", "充值")

NODE_SEL = ".react-flow__node"

P966 = pathlib.Path(__file__).with_name("jimeng_probe966_clicksel_src.py")
P952 = pathlib.Path(__file__).with_name("jimeng_probe952_freeze_who_src.py")

# ── 原始读数键 ─────────────────────────────────────────────────────────
RAW_KEYS = frozenset({
    # 承 966 的 `RAW_KEYS`（本批确实用到的那些）
    "n_nodes", "n_with_ti", "n_without_ti", "ti", "ids", "cls",
    "active_tag", "active_tid", "focus_in_node",
    "aria", "disabled", "type_attr", "node_index", "in_node_list",
    "rect", "who", "tag", "tid", "cls_raw", "blank",
    "dom_index", "id", "tabindex",
    # ⭐ 本批新增的**原始**读数（`APREC_JS` 的整段返回，逐字带回来）
    "fired", "armed", "n_minus1", "n_nodes_snap", "cap_kind",
    "landed", "host_tid", "node_tid", "kind", "trusted",
    "installed", "off_after_read",
})
# ── 派生键 ─────────────────────────────────────────────────────────────
DERIVED_KEYS = frozenset({
    "target", "url", "reps", "rail_tid", "n_lead_cap", "node_sel",
    "question", "ruler", "baseline", "runs", "gate_notes",
    # 本批的派生量
    "ci", "mode", "rows", "n_ready", "n_lead", "n_lead_cap_hit",
    "n_rail_stops", "rail_seqs", "n_install", "n_read",
    "n_nodes_census", "nodes_dom_order", "n_nodes_hist",
    "n_nodes_hist_distinct", "census_stable_in_rep",
    "point_kind_hist", "armed_point_hist", "n_fired_total", "n_post_rows",
    "ever_armed", "ever_armed_by_aria", "ever_landed_self",
    "ever_landed_inner", "ever_landed_out", "landed_all",
    "never_armed", "never_armed_by_aria", "never_landed",
    "never_landed_by_aria", "landed_never_armed", "landed_never_armed_by_aria",
    "armed_never_landed", "n_never_armed", "n_never_landed",
    "n_landed_never_armed", "n_armed_never_landed",
    "b22_index", "b22_tid", "b22_aria", "a61_index", "a61_tid", "a61_aria",
    "b22_armed", "b22_landed", "a61_armed", "a61_landed",
    "b22_land_kinds", "n_landed_self", "n_landed_inner", "n_landed_out",
    "n_armed_presses", "armed_distinct_tids", "off_null_at_end",
    "listener_balanced", "fired_eq_rows", "reps_agree_never_armed",
    "reps_agree_landed_never_armed", "reps_agree_point_kind",
    "keys_disjoint", "design_gates", "skip_note",
    "what_967_measures", "discipline_967",
})
assert not (RAW_KEYS & DERIVED_KEYS), "派生键与原始读数键重叠了（935 的 KeyError 免疫针）"


# ── 逐字来自 966 的尺子（纯读、不调 `focus()`）─────────────────────────
BLANK_JS = """() => {
  for (const [x, y] of [[1300, 1000], [1360, 920], [1220, 1080],
                        [1400, 840], [400, 1080]]) {
    const t = document.elementFromPoint(x, y);
    if (t && t.closest('.react-flow__pane')
        && !t.closest('.react-flow__node')) return [x, y];
  }
  return null;
}"""
CENSUS_JS = """([nodeSel]) => {
  const nodes = Array.from(document.querySelectorAll(nodeSel));
  const ti = {}, ids = {}, cls = {};
  let n_with_ti = 0;
  nodes.forEach((el, i) => {
    const has = el.hasAttribute('tabindex');
    if (has) n_with_ti += 1;
    ti[i] = has ? el.getAttribute('tabindex') : null;
    ids[i] = (el.getAttribute('data-testid') || '')
      + '|' + (el.getAttribute('aria-label') || '')
      + '|' + (el.innerText || '').slice(0, 24);
    cls[i] = el.className;
  });
  return {n_nodes: nodes.length, n_with_ti: n_with_ti,
          n_without_ti: nodes.length - n_with_ti,
          ti: ti, ids: ids, cls: cls};
}"""
FOCUS_JS = """([nodeSel]) => {
  const a = document.activeElement;
  if (!a) return {active_tag: null, active_tid: null, focus_in_node: false};
  const host = a.closest('[data-testid]');
  const node = a.closest(nodeSel);
  return {active_tag: (a.tagName || '').toUpperCase(),
          active_tid: host ? host.getAttribute('data-testid') : null,
          focus_in_node: !!node};
}"""
WHOAMI_JS = """([nodeSel]) => {
  const a = document.activeElement;
  if (!a) return {who: null, tag: null, tid: null, aria: null, cls: null,
                  node_index: null, in_node_list: false, disabled: null,
                  type_attr: null, rect: null};
  const all = Array.from(document.querySelectorAll(nodeSel));
  const node = a.closest(nodeSel);
  const host = a.closest('[data-testid]');
  const r = a.getBoundingClientRect();
  return {who: 1, tag: (a.tagName || '').toUpperCase(),
          tid: host ? host.getAttribute('data-testid') : null,
          aria: a.getAttribute('aria-label') || a.getAttribute('title')
                || (a.innerText || '').slice(0, 30) || null,
          cls: (a.className && a.className.baseVal !== undefined)
                 ? a.className.baseVal : String(a.className || ''),
          node_index: node ? all.indexOf(node) : null,
          in_node_list: !!node,
          disabled: a.disabled === true,
          type_attr: a.getAttribute('type'),
          rect: [Math.round(r.left), Math.round(r.top),
                 Math.round(r.width), Math.round(r.height)]};
}"""
NODECENSUS_JS = """([nodeSel]) => {
  const all = Array.from(document.querySelectorAll('*'));
  const out = [];
  all.forEach((el, i) => {
    if (!el.matches(nodeSel)) return;
    const host = el.closest('[data-testid]');
    out.push({dom_index: i, tid: el.getAttribute('data-testid'),
              id: el.getAttribute('data-id'),
              tag: el.tagName,
              aria: el.getAttribute('aria-label')
                    || (el.innerText || '').slice(0, 20) || null,
              ti: el.hasAttribute('tabindex') ? el.getAttribute('tabindex') : null});
  });
  return {n_nodes: out.length, nodes: out};
}"""

SLICE_STR = "|| '').slice(0, "
# ⭐ 守卫常量自己必须能匹配上东西（946 第一版漏一个逗号 ⇒ 这道门恒绿）
assert any(SLICE_STR in _js for _js in (CENSUS_JS, WHOAMI_JS, NODECENSUS_JS)), (
    "SLICE_STR 自己就匹配不上任何一段 JS —— 这道门恒绿，等于没有门")
for _name, _js in (("CENSUS_JS", CENSUS_JS), ("WHOAMI_JS", WHOAMI_JS),
                   ("NODECENSUS_JS", NODECENSUS_JS)):
    assert _js.count("slice(") == _js.count(SLICE_STR), (
        f"{_name} 里有**非字符串**切片（§131：切片会把规律读反）")

_p966src = P966.read_text(encoding="utf-8") if P966.exists() else ""
assert _p966src, "读不到 966 的源码 —— 尺子没得比，这道门恒绿"
for _name, _js in (("BLANK_JS", BLANK_JS), ("CENSUS_JS", CENSUS_JS),
                   ("FOCUS_JS", FOCUS_JS), ("WHOAMI_JS", WHOAMI_JS),
                   ("NODECENSUS_JS", NODECENSUS_JS)):
    assert _js in _p966src, (     # noqa: S307 — 本文件自己定义的常量
        f"{_name} 与 966 那份**不一致** —— 两份尺子开始分家了")
del _name, _js


def ev(js, arg=None):
    return page.evaluate(js, arg) if arg is not None else page.evaluate(js)


def dump(out):
    """⚠️ 落盘必须排在**所有**后处理之前（935）。"""
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)


def guard(al, tid):
    """⛔ 计费守卫：契约是「**我正要点的这个元素**是什么」（逐字承 966）。"""
    if tid in FORBIDDEN_TIDS:
        raise AssertionError(f"拒绝点击计费入口 testid={tid!r}")
    t = (al or "").strip()
    if t in BILLED_EXACT or t.split(":")[0].strip() in BILLED_EXACT:
        raise AssertionError(f"拒绝点击计费文案 {t!r}")
    for b in BILLED_PREFIX:
        if t.startswith(b):
            raise AssertionError(f"拒绝点击计费文案 {t!r}")


def guard_point(x, y):
    at = ev("""([x, y]) => {
      const el = document.elementFromPoint(x, y);
      if (!el) return null;
      const host = el.closest('[data-testid]');
      return {tid: host ? host.getAttribute('data-testid') : null,
              al: (el.innerText || el.textContent || '').slice(0, 40)};
    }""", [x, y])
    guard((at or {}).get("al"), (at or {}).get("tid"))
    return at


def boot_fn():
    """重新 goto 并等登录态（940：AI 侧栏 Esc 关不掉 ⇒ 每格都得重开）。"""
    page.goto(URL, wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(10000)
    page.set_viewport_size({"width": 1512, "height": 1200})
    page.wait_for_timeout(3000)
    n = page.locator('button[aria-label="音频"]').count()
    if n == 0:
        page.wait_for_timeout(8000)
        n = page.locator('button[aria-label="音频"]').count()
    return n


_p952src = P952.read_text(encoding="utf-8") if P952.exists() else ""
assert _p952src, "读不到 952 的源码 —— boot 的尺子没得比，这道门恒绿"
_bs = textwrap.dedent(__import__("inspect").getsource(boot_fn)).strip()
assert _bs in _p952src, "boot_fn 与 952 那份**不一致** —— 就绪判据换了就读数不可比"
del _bs

URL = ("https://jimeng.jianying.com/ai-tool/ai-canvas/"
       "64b58cd5-7b04-4312-890a-09f2d1d3399f"
       "?enter_from=project_list&from_page=create")

# ── 新件 ①：`INSTALL_JS`（**本批唯一的仪器**）──────────────────────────
# ⭐ **不预设「布 `'0'` 发生在哪一刻」**：4 个取样点全记，由读数说话。
#   `c0`   = `window` 捕获（派发**最前**，应用还没动手）
#   `b2`   = `window` 冒泡（派发**末尾**，目标的 handler 都跑完了）
#   `task` = `c0` 里排的 `setTimeout(0)`（浏览器默认动作之后的那一 task）
#   ⚠️ `b2` **有可能被 `stopPropagation` 掐掉** ⇒ 所以 `task` 不排在 `b2` 上、
#     而排在 `c0`（捕获段永远第一个跑）⇒ `fired` 与 `pre`/`task` 三者必然配平。
INSTALL_JS = """([nodeSel]) => {
  if (window.__ap_off) window.__ap_off();
  window.__ap_rec = {fired: 0, pre: [], post: [], task: [], landed: []};
  const snapshot = () => {
    const list = Array.from(document.querySelectorAll(nodeSel));
    const armed = [];
    let n_minus1 = 0;
    list.forEach((el, i) => {
      const v = el.hasAttribute('tabindex') ? el.getAttribute('tabindex') : null;
      if (v === '0') {
        armed.push({index: i, tid: el.getAttribute('data-testid'),
                    aria: el.getAttribute('aria-label')});
      } else if (v === '-1') {
        n_minus1 += 1;
      }
    });
    return {n_nodes_snap: list.length, armed: armed, n_minus1: n_minus1};
  };
  const onCap = (e) => {
    if (e.key !== 'Tab') return;
    const r = window.__ap_rec;
    r.fired += 1;
    r.pre.push(snapshot());
    setTimeout(() => {
      const q = window.__ap_rec;
      if (q) q.task.push(snapshot());
    }, 0);
  };
  const onEnd = (e) => {
    if (e.key !== 'Tab') return;
    const r = window.__ap_rec;
    if (r) r.post.push(snapshot());
  };
  const onFocus = (e) => {
    const t = e.target;
    const r = window.__ap_rec;
    if (!r || !t || !t.closest) return;
    const list = Array.from(document.querySelectorAll(nodeSel));
    const node = t.closest(nodeSel);
    const idx = node ? list.indexOf(node) : -1;
    r.landed.push({
      tag: (t.tagName || '').toUpperCase(),
      host_tid: (t.closest('[data-testid]')
                 ? t.closest('[data-testid]').getAttribute('data-testid') : null),
      node_tid: node ? node.getAttribute('data-testid') : null,
      node_index: idx,
      aria: t.getAttribute('aria-label') || t.getAttribute('title') || null,
      kind: idx < 0 ? 'out' : (t === node ? 'self' : 'inner'),
      trusted: !!e.isTrusted});
  };
  window.addEventListener('keydown', onCap, true);
  window.addEventListener('keydown', onEnd, false);
  document.addEventListener('focusin', onFocus, true);
  window.__ap_off = () => {
    window.removeEventListener('keydown', onCap, true);
    window.removeEventListener('keydown', onEnd, false);
    document.removeEventListener('focusin', onFocus, true);
    window.__ap_off = null;
  };
  return {installed: true};
}"""
# ── 新件 ②：`READ_JS`（**读走即摘** ⇒ 装/摘成对）────────────────────────
READ_JS = """() => {
  const rec = window.__ap_rec || null;
  if (rec && window.__ap_off) window.__ap_off();
  window.__ap_rec = null; window.__ap_off = null;
  return rec;
}"""
# ── 新件 ③：`ARMED_ONLY_JS`（**纯读**：按后单独再读一次布防集合）────────
ARMED_ONLY_JS = """([nodeSel]) => {
  const list = Array.from(document.querySelectorAll(nodeSel));
  const armed = [];
  list.forEach((el, i) => {
    if (el.getAttribute('tabindex') === '0') {
      armed.push({index: i, tid: el.getAttribute('data-testid'),
                  aria: el.getAttribute('aria-label')});
    }
  });
  return {n_nodes_snap: list.length, armed: armed};
}"""
# ── 新件 ④：`OFF_NULL_JS`（**纯读**：复查监听器确实摘干净了）──────────────
OFF_NULL_JS = """() => ({off_after_read: (window.__ap_off === null),
                            rec_cleared: (window.__ap_rec === null)})"""

assert "INSTALL_JS" not in _p966src, "967 的新件别混进「逐字相同」那组"
assert "ARMED_ONLY_JS" not in _p966src, "967 的新件别混进「逐字相同」那组"
for _n, _s in (("INSTALL_JS", INSTALL_JS), ("READ_JS", READ_JS),
               ("ARMED_ONLY_JS", ARMED_ONLY_JS), ("OFF_NULL_JS", OFF_NULL_JS)):
    assert _s.count("slice(") == 0, f"{_n} 不该有切片（切片守卫 §131）"
del _n, _s
# ⭐ 仪器必须**自己就匹配得上它要验的东西**，否则这几道门恒绿
assert INSTALL_JS.count("__ap_off = () => {") == 1, (
    "`INSTALL_JS` 里没有可摘的句柄 ⇒ 「装/摘配平」这道门恒绿")
assert (INSTALL_JS.count("addEventListener") == 3
        and INSTALL_JS.count("removeEventListener") == 3), (
    "装 3 个就必须摘 3 个（配平门自己数一遍）")
assert INSTALL_JS.count("kind: idx < 0 ? 'out' : (t === node ? 'self' : 'inner')") == 1, (
    "`INSTALL_JS` 里 `self`/`inner` 的判据被改写了 ⇒ 这道门恒绿")
assert ARMED_ONLY_JS.count("getAttribute('tabindex') === '0'") == 1, (
    "`ARMED_ONLY_JS` 里没有「带 `'0'` 的节点」这一判据 ⇒ 这道门恒绿")

POINTS = ("pre", "post", "task", "after")

out = {
    "target": "source", "url": URL, "reps": REPS,
    "rail_tid": RAIL_TID, "n_lead_cap": N_LEAD_CAP, "node_sel": NODE_SEL,
    "question": "⭐⭐⭐⭐ 900 的「从没被布上 `'0'`」（漏 2 个）与 963 的"
                "「从没被 `Tab` 落到」（漏 1 个）**量的是不是同一件事**？"
                "⇒ 本批在**同一轮**里同时量这两个可观测量，并按**身份**对账",
    "ruler": {
        "js_verbatim_from_966": ["BLANK_JS", "CENSUS_JS", "FOCUS_JS",
                                 "WHOAMI_JS", "NODECENSUS_JS"],
        "py_verbatim_from_966": ["ev", "dump", "guard", "guard_point"],
        "verbatim_from_952": ["boot_fn"],
        "new_pieces": ["INSTALL_JS", "READ_JS", "ARMED_ONLY_JS", "OFF_NULL_JS"],
        "why_not_instrument": "966 的 `FOCUSMOVE_JS` 只记 `{armed: true}` 这个"
                              "**闩锁**、**不记是哪一枚** ⇒ 900 那个数"
                              "**至今无法复核**；`NODECENSUS_JS`/`CENSUS_JS`/"
                              "`WHOAMI_JS` 只读属性 ⇒ 不污染「焦点在哪」",
        "instrument_is_read_only": "⭐ `INSTALL_JS` 只**加监听器 + 读属性**，"
                                   "**从不调 `focus()`**、不写 `prototype`、"
                                   "不装 `MutationObserver`、不 `reload` ⇒ 纯诊断",
    },
    "baseline": {
        "b900_never_armed": ["图片 node: b22-upload", "音频 node: 音频 61"],
        "b900_never_armed_note": "900 原文：被布上 `'0'` 的下标 `[0..11, 13..75]`"
                                 " ⇒ 76 个里**漏 2 个**（下标 12 / 68）",
        "b963_never_landed": ["音频 node: 音频 61"],
        "b963_never_landed_note": "963 原文：落点 106 个、覆盖 75/76 ⇒ "
                                  "**漏 1 个**（下标 68）",
        "b966_b22_landed": "966：下标 12（`rf__node-node_gref4sw056`）"
                           "**被落到了 2 次**（seq 17 / seq 118，两轮一致）",
        "reconcile_hypothesis": "⚠️ **待验的假设（不是结论）**：两个集合"
                                "**不相等** ⇒ 「布 `'0'`」与「被落上」"
                                "**是两个不同的可观测量** ⇒ 若成立，900 与 963 "
                                "**都没错**，错的是把它们当同一件事",
    },
    "runs": [],
}

for rep in range(1, REPS + 1):
    print(f"===== rep {rep} =====", flush=True)
    rec = {"rep": rep, "cells": []}
    out["runs"].append(rec)
    dump(out)

    n = boot_fn()
    c = {"ci": 0, "mode": "walk", "n_ready": n, "rows": [], "n_install": 0,
         "n_read": 0, "n_rail_stops": 0, "n_lead_cap_hit": False}
    rec["cells"].append(c)
    dump(out)
    if n == 0:
        c["skip_note"] = "左栏入口没出来（`button[aria-label=音频]` 为 0）⇒ 本格什么也没测"
        continue

    # ⭐⭐⭐⭐ 走查**之前**先普查**全量节点的 DOM 序**（对账的基准）
    _nc = ev(NODECENSUS_JS, [NODE_SEL])
    c["n_nodes_census"] = _nc.get("n_nodes")
    c["nodes_dom_order"] = [{"dom_index": n2.get("dom_index"),
                             "tid": n2.get("tid"), "aria": n2.get("aria"),
                             "ti": n2.get("ti")}
                            for n2 in (_nc.get("nodes") or [])]
    print(f"      全量节点普查：{c['n_nodes_census']} 个（DOM 序）", flush=True)

    sp = ev(BLANK_JS)
    c["blank"] = sp
    if sp:
        guard_point(sp[0], sp[1])       # ⭐ 只点**画布空白**去焦点
        page.mouse.click(sp[0], sp[1])
        page.wait_for_timeout(BLANK_WAIT)

    c["n_lead"] = 0
    while c["n_lead"] < N_LEAD_CAP:
        c["n_lead"] += 1
        inst = ev(INSTALL_JS, [NODE_SEL])
        if inst.get("installed"):
            c["n_install"] += 1
        try:
            page.keyboard.press("Tab")
            page.wait_for_timeout(SETTLE)
            ap = ev(READ_JS)             # ⭐ 读走**并摘监听**（诊断动作必须还原）
            c["n_read"] += 1
            _after = ev(ARMED_ONLY_JS, [NODE_SEL])     # ⭐ 纯读的第四个取样点
            d = ev(WHOAMI_JS, [NODE_SEL])
        finally:
            ev(OFF_NULL_JS)               # ⭐ 复查摘干净（不依赖上面走到哪）
        row = {"k": c["n_lead"], "key": "Tab",
               "fired": (ap or {}).get("fired"),
               "pre": (ap or {}).get("pre"),
               "post": (ap or {}).get("post"),
               "task": (ap or {}).get("task"),
               "after": {"n_nodes_snap": _after.get("n_nodes_snap"),
                         "armed": _after.get("armed")},
               "landed": (ap or {}).get("landed"),
               "active_after": ev(FOCUS_JS, [NODE_SEL]),
               "who_after": d}
        c["rows"].append(row)
        if d.get("tid") == RAIL_TID:
            c["n_rail_stops"] += 1
            if c["n_rail_stops"] >= 2:
                break        # ⭐ 数到第 2 次命中左栏 = 走满一圈
        dump(out)
    else:
        c["n_lead_cap_hit"] = True
    # ⚠️ 复查：走完之后 `__ap_off` 必须是 null（最后一按的 finally 里已经查过，
    #   这里再查一次是为了**捕捉「循环被 break 掉时漏摘」**那种形状）
    c["off_null_at_end"] = ev(OFF_NULL_JS)
    dump(out)

    # ── 本格的后处理（全部在 `dump` 之后）────────────────────────────
    rows = c["rows"]
    census = c["nodes_dom_order"]
    tid2aria = {n2["tid"]: n2.get("aria") for n2 in census if n2.get("tid")}
    c["n_nodes_hist"] = sorted({
        (r["pre"][0]["n_nodes_snap"] if (r.get("pre") or []) else None)
        for r in rows} - {None})
    c["n_nodes_hist_distinct"] = len(c["n_nodes_hist"])
    c["census_stable_in_rep"] = (c["n_nodes_hist_distinct"] == 1
                                 and c["n_nodes_hist"]
                                 and c["n_nodes_hist"][0] == c["n_nodes_census"])
    # ── 取样点分布：`armed` 在**哪个点**第一次非空 ────────────────────
    pk, armed_point_hist = {}, {}
    ever_armed = set()
    n_armed_presses = 0
    for r in rows:
        _seen = None
        for pt in POINTS:
            v = r.get(pt)
            armed_here = (v[0]["armed"] if isinstance(v, list) and v
                          else (v.get("armed") if isinstance(v, dict) else None))
            if armed_here:
                _seen = pt
                for a in armed_here:
                    ever_armed.add(a.get("tid"))
                break
        pk[r["k"]] = _seen
        if _seen:
            n_armed_presses += 1
            armed_point_hist[_seen] = armed_point_hist.get(_seen, 0) + 1
    c["point_kind_hist"] = {k: v for k, v in pk.items() if v}
    c["armed_point_hist"] = armed_point_hist
    c["n_armed_presses"] = n_armed_presses
    c["armed_distinct_tids"] = len(ever_armed)
    c["ever_armed"] = sorted(x for x in ever_armed if x)
    c["ever_armed_by_aria"] = sorted(tid2aria.get(x, x) for x in c["ever_armed"])
    # ── 落点分三类 ────────────────────────────────────────────────────
    ls, li, lo = set(), set(), set()
    for r in rows:
        for L in (r.get("landed") or []):
            if L.get("kind") == "self":
                ls.add(L.get("node_tid"))
            elif L.get("kind") == "inner":
                li.add(L.get("node_tid"))
            else:
                lo.add(L.get("host_tid"))
    c["n_landed_self"] = len([x for x in ls if x])
    c["n_landed_inner"] = len([x for x in li if x])
    c["n_landed_out"] = len([x for x in lo if x])
    c["ever_landed_self"] = sorted(x for x in ls if x)
    c["ever_landed_inner"] = sorted(x for x in li if x)
    c["ever_landed_out"] = sorted(x for x in lo if x)
    c["landed_all"] = sorted(x for x in (ls | li) if x)
    # ── ⭐⭐⭐ 本批的正题：三个集合的两两之差 ─────────────────────────
    ctids = {n2["tid"] for n2 in census if n2.get("tid")}
    c["never_armed"] = sorted(ctids - set(c["ever_armed"]))
    c["never_landed"] = sorted(ctids - set(c["landed_all"]))
    c["landed_never_armed"] = sorted(set(c["landed_all"]) - set(c["ever_armed"]))
    c["armed_never_landed"] = sorted(set(c["ever_armed"]) - set(c["landed_all"]))
    for _k in ("never_armed", "never_landed", "landed_never_armed",
               "armed_never_landed"):
        c[_k + "_by_aria"] = sorted(tid2aria.get(x, x) for x in c[_k])
        c["n_" + _k] = len(c[_k])
    # ── 900/963 点名的那两枚，单列出来（免得埋在集合里）───────────────
    for _lbl, _frag in (("b22", "b22-upload"), ("a61", "音频 61")):
        c[_lbl + "_tid"] = next((t for t in ctids
                                 if _frag in (tid2aria.get(t) or "")), None)
        c[_lbl + "_index"] = next((i for i, n2 in enumerate(census)
                                   if n2.get("tid") == c[_lbl + "_tid"]), None)
        c[_lbl + "_aria"] = tid2aria.get(c[_lbl + "_tid"])
        c[_lbl + "_armed"] = c[_lbl + "_tid"] in set(c["ever_armed"])
        c[_lbl + "_landed"] = c[_lbl + "_tid"] in set(c["landed_all"])
    c["b22_land_kinds"] = sorted({
        L.get("kind") for r in rows for L in (r.get("landed") or [])
        if L.get("node_tid") == c["b22_tid"]})
    # ── 门：每道都挂在**独立分母**上 ──────────────────────────────────
    c["n_fired_total"] = sum(int(r.get("fired") or 0) for r in rows)
    c["n_post_rows"] = sum(len(r.get("post") or []) for r in rows)
    c["fired_eq_rows"] = (c["n_fired_total"] == len(rows))
    c["listener_balanced"] = (c["n_install"] == c["n_read"]
                              and c["off_null_at_end"].get("off_after_read") is True
                              and c["off_null_at_end"].get("rec_cleared") is True)
    dump(out)

# ── ⭐⭐ 两轮比较**必须在 `for rep` 循环之外**（955 第一版栽在这上面）───
_c0 = out["runs"][0]["cells"][0]
_c1 = out["runs"][1]["cells"][0] if len(out["runs"]) > 1 else {}
out["reps_agree_never_armed"] = (
    _c0.get("never_armed_by_aria") == _c1.get("never_armed_by_aria"))
out["reps_agree_landed_never_armed"] = (
    _c0.get("landed_never_armed_by_aria") == _c1.get("landed_never_armed_by_aria"))
out["reps_agree_point_kind"] = (_c0.get("armed_point_hist")
                                == _c1.get("armed_point_hist"))
out["keys_disjoint"] = bool(not (RAW_KEYS & DERIVED_KEYS))
# ── ⭐ 设计门：每道都挂在**独立分母**上，且**不许恒真/恒假**（942 的教训）──
out["design_gates"] = {
    # ① 普查期间节点数**不能变**，否则下标不可比（分母 = 取值个数）
    "census_stable_both_reps": bool(
        _c0.get("census_stable_in_rep") and _c1.get("census_stable_in_rep")),
    # ② 监听器**真的响了每按一次**（分母 = `fired` 与 `rows` 的条数）
    "fired_eq_rows_both_reps": bool(
        _c0.get("fired_eq_rows") and _c1.get("fired_eq_rows")),
    # ③ 装/摘**配平**（分母 = `n_install`/`n_read`，外加 `off_null_at_end`）
    "listener_balanced_both_reps": bool(
        _c0.get("listener_balanced") and _c1.get("listener_balanced")),
    # ④ ⭐ **armed 那一路读数会动**：既有非空的按、又有多个不同的身份
    #    （若 `n_armed_presses` 恒 0 ⇒ 仪器根本没抓到 `'0'`；若
    #    `armed_distinct_tids` 恒 1 ⇒ 它读到的可能是常量）
    "armed_read_is_live": bool(
        min(_c0.get("n_armed_presses") or 0, _c1.get("n_armed_presses") or 0) > 0
        and min(_c0.get("armed_distinct_tids") or 0,
                _c1.get("armed_distinct_tids") or 0) >= 10),
    # ⑤ ⭐ **落点的两条通道都存在**（`self` 与 `inner` 都要有）
    #    —— 963 把两者合在一起算，本批拆开 ⇒ 拆开之后至少一边不能是空
    "landing_channels_both_present": bool(
        min(_c0.get("n_landed_self") or 0, _c1.get("n_landed_self") or 0) > 0
        and min(_c0.get("n_landed_inner") or 0, _c1.get("n_landed_inner") or 0) > 0),
    # ⑥ 两轮**对账结果一致**（按身份比，不按下标）
    "reps_agree_on_recon": bool(out["reps_agree_never_armed"]
                                and out["reps_agree_landed_never_armed"]),
}
# ⭐ **只搬数字、不写判词**：判词必须在**读过这些原始读数之后**再写
#   （「判词与原始读数矛盾时先怀疑判词」—— 960/966 各栽过一次）
out["recon"] = {
    "rep%d" % i: {
        "n_lead": c.get("n_lead"),
        "n_nodes_census": c.get("n_nodes_census"),
        "armed_point_hist": c.get("armed_point_hist"),
        "n_armed_presses": c.get("n_armed_presses"),
        "armed_distinct_tids": c.get("armed_distinct_tids"),
        "n_landed_self": c.get("n_landed_self"),
        "n_landed_inner": c.get("n_landed_inner"),
        "n_landed_out": c.get("n_landed_out"),
        "n_never_armed": c.get("n_never_armed"),
        "never_armed_by_aria": c.get("never_armed_by_aria"),
        "n_never_landed": c.get("n_never_landed"),
        "never_landed_by_aria": c.get("never_landed_by_aria"),
        "n_landed_never_armed": c.get("n_landed_never_armed"),
        "landed_never_armed_by_aria": c.get("landed_never_armed_by_aria"),
        "n_armed_never_landed": c.get("n_armed_never_landed"),
        "b22": {"index": c.get("b22_index"), "aria": c.get("b22_aria"),
                "armed": c.get("b22_armed"), "landed": c.get("b22_landed"),
                "land_kinds": c.get("b22_land_kinds")},
        "a61": {"index": c.get("a61_index"), "aria": c.get("a61_aria"),
                "armed": c.get("a61_armed"), "landed": c.get("a61_landed")},
    }
    for i, c in enumerate(r["cells"][0] for r in out["runs"])
}
out["gate_notes"] = (
    "⭐ 967 的每道门都挂在**独立分母**上（940 的教训）："
    "`census_stable_in_rep` 挂在 `n_nodes_hist` 的**取值个数**上；"
    "`fired_eq_rows` 挂在 `fired` 与 `rows` 的**条数**上；"
    "`listener_balanced` 挂在 `n_install`/`n_read` 与 `off_null_at_end` 上；"
    "`n_armed_presses`/`armed_distinct_tids` 证明**armed 那一路读数会动**"
    "（若恒定就说明仪器没在读真东西）")
out["what_967_measures"] = (
    "**同一轮**里同时量两个**不同的可观测量**："
    "①「被布上 `'0'`」= 4 个取样点里第一次读到非空 `armed` 的那一按（900 的量）；"
    "②「被 `Tab` 落到」= `focusin` 的目标，并**拆成 `self`/`inner`/`out`**"
    "（963 的量，但它把 self 与 inner **合在一起**）"
    "⇒ 对账靠 `data-testid` 身份，**不靠绝对下标**（逐轮会漂）")
out["discipline_967"] = (
    "① **不预设「布 `'0'` 的时刻」** ⇒ 4 个取样点全记、由读数说话；"
    "② `b2`（`window` 冒泡）**可能被 `stopPropagation` 掐掉** ⇒ "
    "`task` 排在 `c0`（捕获段永远第一个跑）上 ⇒ `fired`/`pre`/`task` 必然配平；"
    "③ `INSTALL_JS` **幂等**（装之前先摘干净）⇒ 连按两次不叠监听器；"
    "④ `finally` 里**无条件**复查 `__ap_off` ⇒ `break` 掉循环也不漏摘；"
    "⑤ 两轮比较**按身份**、**不按下标**；"
    "⑥ **查不到就写「仍未查明」**，不许编机制（891）")
dump(out)
print("WROTE", OUT, flush=True)

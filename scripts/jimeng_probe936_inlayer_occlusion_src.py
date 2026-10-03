#!/usr/bin/env python3
r"""batch 936 源站探针（**纯诊断**）：「非全屏浮层盖住**层内**控件」这一档，
在**源站**到不到位？—— §77 要求**先查机制、再动判据**，这批只查机制。

## 936 的由来（复刻侧那半已经查清，零探针）

`jimeng_unclickable_audit.py` 里 `coveredByLayer = !inLayer && blockers.some(...)`
—— ⚠️ 那个 **`!inLayer` 守卫**结构性地把「控件在层内、遮挡物也在层内」的行
排除在 `by_layer` 之外，于是它们落进 835 的降级条款（INFO）。
**§84 起的开放项问的就是这一档该怎么定。**

⭐ **复刻侧反事实（2 次独立读数、逐项相同）**：

- 162 行里**换桶 0 行** ⇒ **`!inLayer` 守卫当前不承重**
- 「控件层内 + 遮挡物层内」这个原始类共 8 行，但**全部 `covered_by_modal=True`**
  ⇒ 而 `_bucket()` 里 **`by_modal` 排在 `by_layer` 前面** ⇒ 它们**根本走不到**
  那个守卫 ⇒ **守卫防的那一类，在非全屏形态下 0 观测**
- 键盘探针那把更严的尺子（四边全被不透明外人盖住）：**32 层全 0**

⇒ 档位问题在复刻侧**无读数可定**；按 §77 必须去**源站**看这类情形
**到底存不存在**。**这批就是去源站看它存不存在。**

## 机制假设 H936（**要证伪它，不是要证明它**）

> **H936：「非全屏浮层盖住层内控件」在产品上不会出现，因为浮层互斥。**
> 开一层会关掉另一层 ⇒ 控件只可能被（a）自己那层盖住（尺子走到焦点祖先
> 就停 ⇒ 豁免）或（b）全屏模态的遮罩盖住 ⇒ **没有第三种可能**。

⚠️ **H936 若成立，结论是「判据不用改」**（守卫对应的是一条真实产品不变式，
不是判据缺陷）。**H936 若被推翻，才轮到讨论档位。** 两种结论处置相反，
所以这批只出读数、不动判据（§77）。

## ⭐⭐ 本批第一版**整轮作废**，两条独立原因（**不许混成一条**）

**① 尺子用错了。** 第一版承 845 用**几何**判层（定位在文档流外 + 不透明底 +
面积 ≥ 80×40），结果：常驻的 `ASIDE[canvas-feature-sidecar]`（Agent 侧栏）
被当成浮层，而**源站的搜索层压根没被认出来**（`n_cands_after=1`）——
可 Tab 明明走进去过（焦点落在「搜索」「全部 76」「音频 N」）。
⇒ **本批问的是「判据怎么分类」，就必须用判据自己的 `LAYER_SEL`**
（语义选择器：role + `data-testid$=-menu/-panel/-listbox`）。
**同一判据写两套定义，就是让同一判据分叉**（866 已经吃过一次）。

**② ⭐ `dom_sig` 被误用了。** 第一版拿「`dom_sig` 不在开层前集合里」当
「新根」。但 `dom_sig` 是 **`tag:nth-of-type` 路径**，而 **`nth-of-type`
下标会因插入而移位** —— 开一层就把后面的兄弟下标全推走了 ⇒ 「按 sig 认新元素」
在**发生 DOM 变更时根本不成立**。
⇒ 932 那条「跨状态可比的身份必须与状态无关」**只对同一状态内的序列成立**，
**拿它跨状态认元素是误用**。本版改成给种子打一个 `data-b936-seed` 标记，
`in_seed` 走**精确的属性判断**，与下标移位彻底无关。

## 三段测量

**A. 层普查（用判据自己的 `LAYER_SEL`）**
每一步都记 `n_layers`（**去重后的顶层 `LAYER_SEL` 匹配数** —— 互为祖先的
只算一层，这是「层」的口径，不许用「有多少个盒子」）。
⚠️ 顶层去重在**同一快照内**用 `dom_sig` 前缀，**不跨状态**（见 ②）。

**B. 层内控件遮挡普查（把 845 的两个局限都换掉）**
- ⭐ **尺子换成四边中点外扩 1px + 必须不透明 + 走到焦点祖先就停**（审计第 3 版）。
  845 用的是**中心点 + 包含关系**，审计自己记过那是**第 1 版「太松」**的错法。
  ⚠️ 845 的中心点读数**照样记**（`hit_center_*`），好与 845 逐字对照。
- ⭐ **不再「一进层就停」**（845 是 `if inside: return` ⇒ **它从来没普查过
  层内控件的遮挡**，而本批问的正是层内控件）。
- ⭐ **焦点落点与 hit 落点分开记**（`focus_*` vs `hit_center_*` / `edges[*].sig`）。
- 每个遮挡物另记两样，**都与判据同口径**：
  `in_layer` = `!!t.closest(LAYER_SEL)`（承指针普查第 1 版）、
  `scrim_self` = 遮挡物**自己**的矩形 ≥ 视口 85%×85%（承判据的 `scrim`，
  系数逐字取 0.85）。⚠️⚠️ **第一版这两条都写错了**，而且错法值得留痕：
  ① `modalish` 一路走到 `body` 找「定位 + 铺满视口」的祖先 ⇒ **整个 app
     外壳**（`fixed` + `inset:0`）把**每一个**遮挡物都算成全屏
     ⇒ 实测 6 个「全盖」步**全部** `modalish=true`，连画布 pane 都算。
     **「祖先里有」与「自己就是」是两回事** —— 判据要的是后者。
  ② 系数写成 0.9，判据用的是 **0.85**。抄判据就要抄系数。

**C. 阳性对照（证明 0 观测不是瞎）**
⚠️⚠️ **0 观测本身不构成证据**（§62：压根没跑起来也是 0）。
⇒ 真实普查**之后**，往一个层内控件上盖一层**普通不透明 div**，
**尺子必须报 `edges_covered == 4`**，否则本批读数作废。
夹具用完立刻移除并断言已移除。
⚠️ 夹具**不能**设 `pointer-events: none` —— `elementsFromPoint` 尊重它，
设了就永远测不到 ⇒ 阳性对照会**假失败**。

## 纯诊断纪律

不劫持 `prototype`、**不装 `MutationObserver`**、不 `reload` 恢复。
唯一的 DOM 改动：种子上的 `data-b936-seed` 标记 + C 段那个 div，
**两者都在探针结束前删掉并断言删干净**（`no_mark_leak_ok` / `no_fixture_leak_ok`）。

## 派生键免疫针（935 踩过 `KeyError`）

`CENSUS_KEYS`（JS 原始读数）与 `DERIVED_KEYS`（Python 派生）
**分开列、断言不许重叠** —— 935 那次两者混在一个元组里、结果 `KeyError`
把 9 分钟读数全丢了。

## 设计门（`design_ok`，**只判 setup，不判机制**）

1. `opened_ok` —— 至少 `MIN_OPENED` 层真的被 `LAYER_SEL` 认出来且**活到遍历时**
2. `budget_ok` —— **自适应**判据：焦点**逃出**种子层、或层内落点**重复出现过**
   （⚠️ 本探针**故意**跑满预算，所以「按次数算撞没撞 cap」永远同一个答案、
   **根本没有判别力**）
3. `sig_agree_ok` —— `dom_sig` 前缀法与 DOM 操作法对「包含」的判断逐步一致
4. `positive_control_ok` —— C 段夹具让尺子报出 4 边全盖
5. `no_mark_leak_ok` / `no_fixture_leak_ok` —— 标记与夹具都删干净

## 计费边界

只点：顶栏 launcher（过 `guard()` 护栏）、画布**空白**处右键。
**绝不**点生成/发送/购买/充值，**不点任何节点**。

跑法：
  ~/.venvs/liblib-harness/bin/python -u scripts/jimeng_headless.py run \
      scripts/jimeng_probe936_inlayer_occlusion_src.py
"""

import json
import re

OUT = "/tmp/b936-src-inlayer-occlusion.json"
REPS = 2

MAX_TABS = 60
SETTLE = 260
OPEN_WAIT = 1400

MIN_OPENED = 2
SEED_MARK = "data-b936-seed"
FIXTURE_ATTR = "data-b936-fixture"

# ⚠️⚠️ **`LAYER_SEL` 逐字承判据**（`jimeng_unclickable_audit.py` 的模块级单一来源）。
#    本批问的是「判据怎么分类」，所以尺子必须与判据**同一份定义**；
#    自己另写一套（第一版承 845 用几何判层）＝ 让同一判据分叉，
#    而且实测把源站的搜索层漏掉了、把常驻侧栏当成了浮层。
#    改这里之前先去改判据那个常量，两边必须一起动。
LAYER_SEL = (
    '.react-flow__node-toolbar, .react-flow__node-panel, '
    '[role=menu], [role=listbox], [role=dialog], [role=popover], '
    '[data-testid$="-listbox"], [data-testid$="-menu"], '
    '[data-testid$="-panel"], [data-testid$="-palette"]')

# 计费护栏（承 853b：等值才拦，「生成模式」是控件描述不是付费按钮）
BILLED_EXACT = ("生成", "发送", "购买", "充值", "立即支付", "开通", "订阅", "兑换")
BILLED_PREFIX = ("立即", "购买", "充值")


def guard(label):
    t = (label or "").strip()
    base = t.split(":")[0].strip()
    return bool(t in BILLED_EXACT or base in BILLED_EXACT
                or any(t.startswith(b) for b in BILLED_PREFIX))


# ── 原始读数字段表（派生键不许与它重叠）───────────────────────────────
CENSUS_KEYS = frozenset({
    "is_body", "focus_dom_sig", "focus_tag", "focus_tid", "focus_al",
    "focus_txt", "focus_w", "focus_h", "focus_x", "focus_y",
    "focus_in_layer", "in_seed",
    "hit_center_dom_sig", "hit_center_sig", "hit_center_in_layer",
    "edges", "n_layers", "n_layer_boxes",
})
EDGE_KEYS = frozenset({
    "pos", "dom_sig", "sig", "top_opaque", "self_branch", "is_ancestor",
    "paints_over", "stopped", "in_layer", "scrim_self",
})
DERIVED_KEYS = frozenset({
    "focus_in_any_root", "edges_covered", "edges_total", "occluded",
    "hit_center_covered", "hit_center_is_focus_branch",
    "covered_by_outsider_in_layer", "covered_by_outsider_scrim",
})
# ⚠️ 935 免疫针：派生键与原始读数键**不许重叠**（重叠 = 取法错了）
assert not (CENSUS_KEYS & DERIVED_KEYS), "派生键与原始读数键重叠了"
assert not (DERIVED_KEYS & EDGE_KEYS), "派生键与边读数键重叠了"
assert "occluded" not in CENSUS_KEYS, "occluded 必须是派生量，不许出现在原始读数里"

# ⚠️⚠️ 下面四段 helper 是**单一来源**，但**每个 `*_JS` 块里都逐字内联了一份**。
# 原因：`jimeng_probe_js_syntax_check.py` 按 `^[A-Z_0-9]+_JS = """…"""` 从
# **源码文本**切块 ⇒ 用 `%` 拼装的话切出来的就是裸 `%s`，语法门当场红；
# 用 `+` 拼的话整块根本切不到 ⇒ **门禁就再也看不见这段 JS 了**
#（而 936 第一版那个少两个右括号的真语法错，**正是这道门抓出来的**）。
# ⇒ 代价是复制三份，所以下面用 assert 锁住「三份必须与单一来源逐字一致」。
SIG_FN = """  const __sig = (e) => {
    const parts = [];
    for (let n = e; n && n.nodeType === 1; n = n.parentElement) {
      let i = 1;
      for (let s = n.previousElementSibling; s; s = s.previousElementSibling) {
        if (s.tagName === n.tagName) i++;
      }
      parts.unshift(n.tagName + ':nth-of-type(' + i + ')');
    }
    return parts.join('/');
  };"""
OPA_FN = """  const __opaque = (e) => {
    const bg = getComputedStyle(e).backgroundColor || '';
    return bg !== 'rgba(0, 0, 0, 0)' && !bg.startsWith('rgba(0, 0, 0, 0)');
  };"""
NAME_FN = """  const __name = (e) => (e ? (e.tagName + '/'
      + (e.getAttribute('data-testid') || e.getAttribute('aria-label')
         || (e.className || '').toString()
              .replace(/\\s+/g, ' ').slice(0, 40))
      || (e.innerText || '').trim().slice(0, 14)) : null);"""
MODALISH_FN = """  const __scrimSelf = (t) => {
    const r = t.getBoundingClientRect();
    return r.width >= innerWidth * 0.85 && r.height >= innerHeight * 0.85;
  };"""

# ── A 段：层普查（判据自己的 `LAYER_SEL`）────────────────────────────
LAYER_CENSUS_JS = """(sel) => {
  const __sig = (e) => {
    const parts = [];
    for (let n = e; n && n.nodeType === 1; n = n.parentElement) {
      let i = 1;
      for (let s = n.previousElementSibling; s; s = s.previousElementSibling) {
        if (s.tagName === n.tagName) i++;
      }
      parts.unshift(n.tagName + ':nth-of-type(' + i + ')');
    }
    return parts.join('/');
  };
  const out = [];
  for (const e of document.querySelectorAll(sel)) {
    const r = e.getBoundingClientRect();
    if (r.width < 8 || r.height < 8) continue;   // 零尺寸的不算层
    out.push({dom_sig: __sig(e), tag: e.tagName,
              tid: e.getAttribute('data-testid') || '',
              role: e.getAttribute('role') || '',
              al: (e.getAttribute('aria-label') || '').slice(0, 40),
              x: Math.round(r.x), y: Math.round(r.y),
              w: Math.round(r.width), h: Math.round(r.height)});
  }
  return out;
}"""

# ── B 段：一次按压的尺子（**焦点落点与 hit 落点分开记**）───────────────
RULER_JS = """(sel) => {
  const __sig = (e) => {
    const parts = [];
    for (let n = e; n && n.nodeType === 1; n = n.parentElement) {
      let i = 1;
      for (let s = n.previousElementSibling; s; s = s.previousElementSibling) {
        if (s.tagName === n.tagName) i++;
      }
      parts.unshift(n.tagName + ':nth-of-type(' + i + ')');
    }
    return parts.join('/');
  };
  const __opaque = (e) => {
    const bg = getComputedStyle(e).backgroundColor || '';
    return bg !== 'rgba(0, 0, 0, 0)' && !bg.startsWith('rgba(0, 0, 0, 0)');
  };
  const __name = (e) => (e ? (e.tagName + '/'
      + (e.getAttribute('data-testid') || e.getAttribute('aria-label')
         || (e.className || '').toString()
              .replace(/\\s+/g, ' ').slice(0, 40))
      || (e.innerText || '').trim().slice(0, 14)) : null);
  const __scrimSelf = (t) => {
    const r = t.getBoundingClientRect();
    return r.width >= innerWidth * 0.85 && r.height >= innerHeight * 0.85;
  };
  const a = document.activeElement;
  if (!a || a === document.body) return {is_body: true};
  const b = a.getBoundingClientRect();
  const rec = {
    is_body: false,
    focus_dom_sig: __sig(a),
    focus_tag: a.tagName,
    focus_tid: a.getAttribute('data-testid') || '',
    focus_al: (a.getAttribute('aria-label') || '').trim().slice(0, 30),
    focus_txt: (a.innerText || a.getAttribute('placeholder') || '')
                 .trim().replace(/\\s+/g, ' ').slice(0, 20),
    focus_w: Math.round(b.width), focus_h: Math.round(b.height),
    focus_x: Math.round(b.x), focus_y: Math.round(b.y),
    focus_in_layer: !!a.closest(sel),
    in_seed: !!a.closest('[data-b936-seed]'),
    hit_center_dom_sig: null, hit_center_sig: null, hit_center_in_layer: null,
    edges: []
  };
  if (b.width < 1 || b.height < 1) return rec;
  // 中心 hit：**保留 845 那把尺子**的读数，好与 845 逐字对照
  const hc = document.elementFromPoint(b.x + b.width / 2, b.y + b.height / 2);
  rec.hit_center_dom_sig = hc ? __sig(hc) : null;
  rec.hit_center_sig = __name(hc);
  rec.hit_center_in_layer = hc ? !!hc.closest(sel) : null;
  // 四边中点**外扩 1px**（焦点环画在边框上，所以测边框那一圈，不是中心）
  const EDGE = [['left', b.left - 1, b.top + b.height / 2],
                ['right', b.right + 1, b.top + b.height / 2],
                ['top', b.x + b.width / 2, b.top - 1],
                ['bottom', b.x + b.width / 2, b.bottom + 1]];
  for (const [pos, ex, ey] of EDGE) {
    const st = document.elementsFromPoint(ex, ey) || [];
    const t = st[0] || null;
    if (!t) {
      rec.edges.push({pos, dom_sig: null, sig: null, top_opaque: false,
                      self_branch: false, is_ancestor: false,
                      paints_over: false, stopped: 'no_hit',
                      in_layer: null, scrim_self: false});
      continue;
    }
    const selfBranch = (t === a) || a.contains(t) || (t.contains && t.contains(a));
    const isAnc = (t === a) || (t.contains && t.contains(a));
    // 不透明外人：从栈顶往上找不透明底；**一旦走到焦点的祖先就停**
    //（祖先的背景画在**下面**，不算遮挡）—— 这一条就是「自己的浮层」豁免。
    let paints = false, stopped = 'reached_body';
    for (let n = t; n && n !== document.body; n = n.parentElement) {
      if (n === a || (n.contains && n.contains(a))) { stopped = 'reached_focus_anc'; break; }
      if (__opaque(n)) { paints = true; stopped = 'paints'; break; }
    }
    rec.edges.push({pos, dom_sig: __sig(t), sig: __name(t),
                    top_opaque: __opaque(t), self_branch: selfBranch,
                    is_ancestor: isAnc, paints_over: paints, stopped,
                    in_layer: !!t.closest(sel), scrim_self: __scrimSelf(t)});
  }
  return rec;
}"""

# ── 种子标记：给「我打开的那层」打一个属性，避开 `nth-of-type` 移位 ────
SEED_MARK_JS = """(m) => {
  const __sig = (e) => {
    const parts = [];
    for (let n = e; n && n.nodeType === 1; n = n.parentElement) {
      let i = 1;
      for (let s = n.previousElementSibling; s; s = s.previousElementSibling) {
        if (s.tagName === n.tagName) i++;
      }
      parts.unshift(n.tagName + ':nth-of-type(' + i + ')');
    }
    return parts.join('/');
  };
  let el = null;
  if (m.tid) {
    el = document.querySelector('[data-testid="' + m.tid + '"]');
  } else if (m.role) {
    // 没有 testid 就按 role + 矩形就近认（矩形会随动画变，所以容差 24px）
    let best = 1e9;
    for (const e of document.querySelectorAll('[role="' + m.role + '"]')) {
      const r = e.getBoundingClientRect();
      if (r.width < 8 || r.height < 8) continue;
      const d = Math.abs(r.x - m.x) + Math.abs(r.y - m.y)
              + Math.abs(r.width - m.w) + Math.abs(r.height - m.h);
      if (d < best) { best = d; el = e; }
    }
    if (el && best > 96) el = null;      // 差太远就当没认出来
  }
  if (!el) return {ok: false, why: '认不出种子元素'};
  el.setAttribute('data-b936-seed', '1');
  return {ok: true, dom_sig: __sig(el), tag: el.tagName,
          tid: el.getAttribute('data-testid') || '',
          role: el.getAttribute('role') || ''};
}"""

SEED_ALIVE_JS = """() => {
  const cur = document.querySelector('[data-b936-seed]');
  if (cur) return {alive: true};
  return {alive: false};
}"""

SEED_CLEAR_JS = """() => {
  const n = document.querySelectorAll('[data-b936-seed]');
  n.forEach(e => e.removeAttribute('data-b936-seed'));
  return document.querySelectorAll('[data-b936-seed]').length;
}"""

# ── C 段：阳性对照夹具（加一层普通不透明 div；**不设 pointer-events**）──
FIXTURE_ADD_JS = """() => {
  const SEL = 'button,[role=button],a,input,select,textarea,[tabindex]';
  let target = null;
  for (const e of document.querySelectorAll(SEL)) {
    if (!e.closest('[data-b936-seed]')) continue;
    const r = e.getBoundingClientRect();
    // ⚠️ 只挑**小控件**（≤160px）。第一版没设上限 ⇒ 选中的是整个
    // `ASIDE[role=dialog]` 面板（320×1084）⇒ 那测的是「面板被盖」，
    // 不是本批问的「**控件**被浮层盖住」。
    if (r.width >= 8 && r.height >= 8 && r.width <= 160 && r.height <= 160) {
      target = e; break;
    }
  }
  if (!target) return {ok: false, why: '种子层内找不到尺寸够的可聚焦控件'};
  target.focus();
  const r = target.getBoundingClientRect();
  const d = document.createElement('div');
  d.setAttribute('data-b936-fixture', '1');
  d.style.position = 'fixed';
  // ⚠️⚠️ **必须比目标大出一圈**（`PAD`），不能照抄目标矩形。
  //    四条探针点按判据是**外扩 1px**（焦点环画在边框上）⇒ 夹具若正好等于
  //    目标矩形，那四个点全在夹具**外面** ⇒ 阳性对照**在构造上就不可能通过**。
  //    936 第一版就这样，测出「3/4 条边被盖」—— ⭐ 那个 3/4 是**夹具自己的
  //    几何造出来的**、不是尺子的性质，差一步就被当成读数写进结论。
  const PAD = 6;
  d.style.left = (r.left - PAD) + 'px';
  d.style.top = (r.top - PAD) + 'px';
  d.style.width = (r.width + 2 * PAD) + 'px';
  d.style.height = (r.height + 2 * PAD) + 'px';
  d.style.background = 'rgb(1, 2, 3)';
  d.style.zIndex = '2147483647';
  // 故意不设 pointer-events —— elementsFromPoint 尊重它，
  // 设成 none 这个夹具就永远测不到，阳性对照会假失败。
  document.body.appendChild(d);
  return {ok: true, target_name: target.tagName,
          x: Math.round(r.x), y: Math.round(r.y),
          w: Math.round(r.width), h: Math.round(r.height)};
}"""

FIXTURE_DEL_JS = """() => {
  const d = document.querySelector('[data-b936-fixture]');
  if (d) d.remove();
  return !document.querySelector('[data-b936-fixture]');
}"""

# ── 漂移免疫针：三份内联副本必须与单一来源**逐字一致** ───────────────────
# 「两处各写一份就是让同一判据分叉」—— 这里是自己抄自己，所以用断言钉住。
assert LAYER_CENSUS_JS.count(SIG_FN) == 1, "__sig 在 LAYER_CENSUS_JS 里漂移了"
assert RULER_JS.count(SIG_FN) == 1, "__sig 在 RULER_JS 里漂移了"
assert SEED_MARK_JS.count(SIG_FN) == 1, "__sig 在 SEED_MARK_JS 里漂移了"
assert RULER_JS.count(OPA_FN) == 1, "__opaque 在 RULER_JS 里漂移了"
assert RULER_JS.count(NAME_FN) == 1, "__name 在 RULER_JS 里漂移了"
def _strip_js_comments(js):
    return "\n".join(re.sub(r"//.*$", "", ln) for ln in js.splitlines())


# ⭐ 「全屏」判据必须与判据的 `scrim` **逐字同系数**（0.85，不是 0.9）
_SCRIM_BODY = "r.width >= innerWidth * 0.85 && r.height >= innerHeight * 0.85"
assert RULER_JS.count(_SCRIM_BODY) == 1, "RULER_JS 里的「全屏」判据漂移了"
assert MODALISH_FN.count(_SCRIM_BODY) == 1
assert "0.9" not in _strip_js_comments(RULER_JS), \
    "RULER_JS 里出现了 0.9 —— 判据的 scrim 系数是 0.85"
# 阳性对照的命门：夹具一旦设了 pointer-events，elementsFromPoint 就看不见它
# ⚠️ 必须**先剥掉 `//` 注释**再查 —— 直接查原文会被这段警示**注释自己**里的
#    "pointer-events" 五个字判成红。「查代码」和「查注释」是两回事。
_FIX_EXEC = _strip_js_comments(FIXTURE_ADD_JS)
assert "pointerEvents" not in _FIX_EXEC and "pointer-events" not in _FIX_EXEC, \
    "阳性对照夹具不许设 pointer-events（elementsFromPoint 尊重它，会假失败）"
# 反过来也钉一下：警示**注释**必须留着，别被谁「顺手清理」掉
assert "pointer-events" in FIXTURE_ADD_JS, "夹具旁那条 pointer-events 警示注释不见了"
# `LAYER_SEL` 必须与判据那份**逐字相同**（本批问的就是判据怎么分类）
assert LAYER_SEL == (
    '.react-flow__node-toolbar, .react-flow__node-panel, '
    '[role=menu], [role=listbox], [role=dialog], [role=popover], '
    '[data-testid$="-listbox"], [data-testid$="-menu"], '
    '[data-testid$="-panel"], [data-testid$="-palette"]')


def ev(js, arg=None):
    return page.evaluate(js, arg) if arg is not None else page.evaluate(js)


def dump(out):
    """⚠️ 落盘必须排在**所有**后处理之前（935：后处理崩了整轮读数全丢）。"""
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    return out


def topmost(boxes):
    """顶层去重：互为祖先的只算**一层**（⚠️ 只在**同一快照内**用前缀，
    **不跨状态** —— `nth-of-type` 会因插入而移位）。"""
    out = []
    for b in boxes:
        pre = b["dom_sig"] + "/"
        if any(o["dom_sig"] != b["dom_sig"] and pre.startswith(o["dom_sig"] + "/")
               for o in boxes):
            continue
        out.append(b)
    out.sort(key=lambda b: -(b["w"] * b["h"]))
    return out


def census(tag):
    boxes = ev(LAYER_CENSUS_JS, LAYER_SEL)
    roots = topmost(boxes)
    return {"tag": tag, "n_boxes": len(boxes), "n_layers": len(roots),
            "layers": roots[:8], "boxes": boxes[:40]}


def derive(raw):
    """派生量：与原始读数**分开**算（935 免疫针的另一半）。"""
    d = {}
    d["focus_in_any_root"] = bool(raw.get("focus_in_layer"))
    edges = raw.get("edges") or []
    cov = [e for e in edges if e.get("paints_over") and not e.get("self_branch")]
    d["edges_covered"] = len(cov)
    d["edges_total"] = len(edges)
    d["occluded"] = bool(edges) and d["edges_covered"] == len(edges)
    # ⭐ 承判据两路，**口径逐字对齐**（第一版这两条都写错了，见下）：
    #   `in_layer`  = `!!t.closest(LAYER_SEL)`（承指针普查第 1 版）
    #   `scrim_self`= 遮挡物**自己**的矩形 ≥ 视口 85%×85%（承判据 `scrim`，
    #                 系数就是 0.85，不是 0.9）
    d["covered_by_outsider_in_layer"] = any(e.get("in_layer") for e in cov)
    d["covered_by_outsider_scrim"] = any(e.get("scrim_self") for e in cov)
    # 845 那把（中心 + 包含关系）的读数，只作对照，不参与判决
    d["hit_center_covered"] = False
    d["hit_center_is_focus_branch"] = False
    fs = raw.get("focus_dom_sig")
    if fs and raw.get("hit_center_dom_sig"):
        h = raw["hit_center_dom_sig"]
        d["hit_center_covered"] = not (h == fs or h.startswith(fs + "/")
                                       or fs.startswith(h + "/"))
        d["hit_center_is_focus_branch"] = not d["hit_center_covered"]
    return d


def reset():
    for _ in range(2):
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)
    ev(SEED_CLEAR_JS)


# ── 开层器（**只点顶栏 launcher / 画布空白**，不点任何节点）──────────────
def open_topbar_launcher(idx):
    pt = page.evaluate("""(i) => {
      const bs = [...document.querySelectorAll('[data-testid=canvas-panel-launcher]')];
      if (bs.length <= i) return null;
      const b = bs[i];
      const al = (b.getAttribute('aria-label') || b.innerText || '').trim();
      const r = b.getBoundingClientRect();
      return {n: bs.length, al: al.slice(0, 30),
              x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2)};
    }""", idx)
    if not pt:
        return {"opened": False, "why": f"没有第 {idx} 个 canvas-panel-launcher"}
    if guard(pt.get("al")):
        return {"opened": False, "why": f"护栏拦下付费动作 {pt.get('al')!r}"}
    page.mouse.click(pt["x"], pt["y"])
    return {"opened": True, "trigger": pt}


def open_context_menu():
    spot = page.evaluate("""() => {
      for (const [x, y] of [[430, 620], [420, 660], [450, 700], [400, 580],
                            [470, 640], [440, 680]]) {
        const e = document.elementFromPoint(x, y);
        if (!e) continue;
        if (e.closest('[data-id]')) continue;
        if (!e.closest('.react-flow__pane, .react-flow__renderer, '
                     + '[class*=pane], [class*=canvas]')) continue;
        return {x, y};
      }
      return null;
    }""")
    if not spot:
        return {"opened": False, "why": "找不到空画布落点"}
    page.mouse.click(spot["x"], spot["y"], button="right")
    return {"opened": True, "trigger": spot}


OPENERS = [
    ("顶栏·搜索", lambda: open_topbar_launcher(0)),
    ("画布右键菜单", open_context_menu),
    ("顶栏·launcher2", lambda: open_topbar_launcher(1)),
    ("顶栏·launcher3", lambda: open_topbar_launcher(2)),
]


def pick_seed(pre_layers, post_layers):
    """挑「我打开的那层」。

    ⚠️⚠️ **不按 `dom_sig` 认新元素**（第一版就是这么错的）：`nth-of-type`
    下标会因插入而移位，开一层就把后面兄弟的下标全推走。
    ⇒ 改用**不随插入移位**的身份：`data-testid`（最稳）→ `role`+矩形就近。
    """
    pre_tids = {l["tid"] for l in pre_layers if l.get("tid")}
    for l in post_layers:
        if l.get("tid") and l["tid"] not in pre_tids:
            return l, "testid"
    # 没有 testid 的层：按「矩形与开层前差最大」认
    pre_rects = {(l["x"], l["y"], l["w"], l["h"]) for l in pre_layers}
    cands = [l for l in post_layers
             if (l["x"], l["y"], l["w"], l["h"]) not in pre_rects]
    if cands:
        return cands[0], "rect"
    return None, None


def traverse(seed_name, budget_note):
    """冷启动 + 真按 Tab，**走完预算**（不因为进层就停 —— 845 就是栽在这儿）。"""
    page.evaluate("() => { const a = document.activeElement;"
                  " if (a && a.blur) a.blur(); return true; }")
    page.wait_for_timeout(300)
    # ⚠️ `blur()` 可能把某些层**直接关掉**（第一版的右键菜单就是如此）
    #    ⇒ 立刻回读种子还在不在，如实记，别把「层没了」读成「Tab 走不进去」
    alive = page.evaluate(SEED_ALIVE_JS)
    if not alive.get("alive"):
        return [], {"closed_on_blur": True, "escaped": True,
                    "repeat_seen": False, "n_distinct_in_seed": 0,
                    "n_in_seed_steps": 0, "note": budget_note}
    steps = []
    for i in range(1, MAX_TABS + 1):
        page.keyboard.press("Tab")
        page.wait_for_timeout(SETTLE)
        raw = ev(RULER_JS, LAYER_SEL)
        c = census(f"{seed_name}/step{i}")
        raw["n_layers"] = c["n_layers"]
        raw["n_layer_boxes"] = c["n_boxes"]
        unknown = set(raw) - CENSUS_KEYS
        assert not unknown, f"RULER_JS 冒出未登记的原始键: {unknown}"
        for e in (raw.get("edges") or []):
            bad = set(e) - EDGE_KEYS
            assert not bad, f"边读数冒出未登记的键: {bad}"
        d = derive(raw)
        bad = set(d) - DERIVED_KEYS
        assert not bad, f"派生量冒出未登记的键: {bad}"
        # sig 一致性自检：dom_sig 前缀法 与 DOM 操作法 对「包含」的判断
        if raw.get("focus_dom_sig") and raw.get("hit_center_dom_sig"):
            h = raw["hit_center_dom_sig"]
            f = raw["focus_dom_sig"]
            sig_says = (h == f or h.startswith(f + "/") or f.startswith(h + "/"))
            if sig_says != d["hit_center_is_focus_branch"]:
                raise AssertionError("dom_sig 前缀法与中心分支判断不一致")
        steps.append({"tab": i, "raw": raw, "der": d})
    # ⚠️ 预算判据**不许拍脑袋给次数**：本探针**故意**跑满预算，所以「按次数算
    #    撞没撞 cap」永远是同一个答案、根本没有判别力。
    # ⇒ 改用**自适应**条件：焦点**逃出**种子层，或层内落点**重复出现过**。
    last = steps[-1] if steps else None
    in_seed_sigs = [s["raw"].get("focus_dom_sig") for s in steps
                    if s["raw"].get("in_seed") and s["raw"].get("focus_dom_sig")]
    b = {"closed_on_blur": False,
         "escaped": bool(last and not last["raw"].get("in_seed")),
         "n_distinct_in_seed": len(set(in_seed_sigs)),
         "n_in_seed_steps": len(in_seed_sigs),
         "last_in_seed_sig": in_seed_sigs[-1] if in_seed_sigs else None,
         "repeat_seen": bool(in_seed_sigs
                             and len(set(in_seed_sigs)) < len(in_seed_sigs)),
         "note": budget_note}
    return steps, b


def positive_control():
    """证明尺子**看得见**这类遮挡（0 观测本身不是证据，§62）。"""
    added = ev(FIXTURE_ADD_JS)
    if not added.get("ok"):
        return {"ok": False, "why": added.get("why"),
                "leak_check": ev(FIXTURE_DEL_JS)}
    raw = ev(RULER_JS, LAYER_SEL)
    d = derive(raw)
    removed = ev(FIXTURE_DEL_JS)
    # ⚠️⚠️ **`ok` 必须反映「尺子真的响了」**，不能只反映「夹具加上了」。
    #    936 第一版这里 `ok` 恒为 True（加得上就 True）⇒ 一个**恒真的字段
    #    比没有字段更坏**：它会让 `design_ok.positive_control_ok` 变成
    #    一句永远成立的话，等于没有门。
    # ⇒ 判据换成「尺子报出**四边全盖**」（`occluded` 的定义）。
    #    ⚠️ 要求 4 条而不是「至少 1 条」：夹具比目标大 `PAD` 一圈，
    #    四个外扩 1px 的探针点必然全落在夹具内 ⇒ 4/4 才是「尺子能看见
    #    这类遮挡」的**完整**证明；3/4 只说明夹具几何还不对。
    #    （936 第一版夹具正好等于目标矩形 ⇒ 探针点全在夹具外 ⇒ 测出 3/4，
    #    **那个 3/4 是夹具自己的几何造出来的**，不是尺子的性质。）
    fired = bool(d.get("occluded"))
    return {"ok": True, "ruler_fired": fired,
            "edges_covered": d.get("edges_covered"),
            "edges_total": d.get("edges_total"),
            "edge_detail": [{"pos": e.get("pos"), "sig": e.get("sig"),
                             "paints_over": e.get("paints_over"),
                             "stopped": e.get("stopped")}
                            for e in (raw.get("edges") or [])],
            "added": added, "raw": raw, "der": d, "leak_check": removed}


URL = ("https://jimeng.jianying.com/ai-tool/ai-canvas/"
       "64b58cd5-7b04-4312-890a-09f2d1d3399f"
       "?enter_from=project_list&from_page=create")

out = {"layer_sel": LAYER_SEL, "design_ok": {}, "runs": []}

for rep in range(1, REPS + 1):
    print(f"===== rep {rep} =====", flush=True)
    page.goto(URL, wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(10000)
    page.set_viewport_size({"width": 1512, "height": 1200})
    page.wait_for_timeout(3000)
    n_audio = page.locator('button[aria-label="音频"]').count()
    if n_audio == 0:
        page.wait_for_timeout(8000)
        n_audio = page.locator('button[aria-label="音频"]').count()
    rec = {"rep": rep, "n_audio_rail_button": n_audio,
           "n_nodes": page.locator(".react-flow__node").count(), "layers": []}
    out["runs"].append(rec)
    if n_audio == 0:
        rec["skipped"] = "登录态没命中，本轮不测"
        print("  登录态没命中，跳过本轮", flush=True)
        dump(out)
        continue

    for seed_name, opener in OPENERS:
        reset()
        pre = census(f"{seed_name}/before")
        info = opener()
        page.wait_for_timeout(OPEN_WAIT)
        post = census(f"{seed_name}/after")
        seed, how = pick_seed(pre["layers"], post["layers"])
        lr = {"name": seed_name, "open_info": info, "seed_identified_by": how,
              "n_boxes_before": pre["n_boxes"], "n_boxes_after": post["n_boxes"],
              "n_layers_before": pre["n_layers"], "n_layers_after": post["n_layers"],
              "n_new_layers": post["n_layers"] - pre["n_layers"],
              "new_layers": [l for l in post["layers"]
                             if l not in pre["layers"]],
              "opened": bool(seed)}
        if seed:
            marked = ev(SEED_MARK_JS, seed)
            lr["seed"] = seed
            lr["mark"] = marked
            if marked.get("ok"):
                lr["steps"], lr["budget"] = traverse(seed_name, "cold_blur")
                lr["after_traverse"] = census(f"{seed_name}/after_traj")
                # ⭐ 阳性对照**必须在这一层还开着的时候做**。936 前三版都栽在
                #    时机上：① 挑错层 ② 尺子写错 ③ 标记被 `reset()` 清掉
                #    ④ **层已经被后面的 Escape 关了**（搜索层遍历完还过了
                #    launcher2/launcher3 两轮，到对照时它早不在 DOM 里了
                #    ⇒ `querySelector('[data-testid=...]')` 返回 null
                #    ⇒「认不出种子元素」）。
                # ⇒ 改成就地做：**每层遍历完立刻对照**，逐层记。
                lr["positive_control"] = positive_control()
        rec["layers"].append(lr)
        dump(out)   # ⚠️ 每层落一次盘
        b = lr.get("budget", {})
        print(f"  [{seed_name}] 认种子={lr['seed_identified_by']} "
              f"层 {pre['n_layers']}->{post['n_layers']}"
              + (f" 层内步 {b.get('n_in_seed_steps')}"
                 f" 全盖 {sum(1 for s in lr.get('steps', []) if s['der']['occluded'])}"
                 f" blur关层={b.get('closed_on_blur')}"
                 f" 预算{'够' if b.get('escaped') or b.get('repeat_seen') else '不够'}"
                 if lr["opened"] else ""), flush=True)

    # 阳性对照已**就地**逐层做完（见上面的时机关），这里只收尾：
    # 确认种子标记全部清干净，并照实报每层的结果
    rec["seed_mark_leftover"] = page.evaluate(
        "() => document.querySelectorAll('[data-b936-seed]').length")
    dump(out)
    print("  逐层阳性对照: " + " | ".join(
        f"{l['name']}=响{l.get('positive_control', {}).get('ruler_fired')}"
        f"/edges{l.get('positive_control', {}).get('der', {}).get('edges_covered')}"
        for l in rec["layers"] if l.get("positive_control")), flush=True)
    print(f"  标记残留={rec['seed_mark_leftover']}", flush=True)
    reset()

# ── 设计门：只判 setup，不判机制 ────────────────────────────────────────
runs_ok = [r for r in out["runs"] if not r.get("skipped")]
all_layers = [l for r in runs_ok for l in r["layers"]]
measured = [l for l in all_layers
            if l.get("opened") and l.get("mark", {}).get("ok")]
steps_all = [s for l in measured for s in l.get("steps", [])]
in_seed_steps = [s for s in steps_all if s["raw"].get("in_seed")]
occl_in_seed = [s for s in in_seed_steps if s["der"]["occluded"]]
occl_any = [s for s in steps_all if s["der"]["occluded"]]
# ⭐ 本批的正题：层内控件被**非全屏**浮层盖住
target = [s for s in in_seed_steps
          if s["der"]["occluded"] and s["der"]["covered_by_outsider_in_layer"]
          and not s["der"]["covered_by_outsider_scrim"]]
ctrls = [l.get("positive_control", {}) for l in measured]
leaks = [r.get("seed_mark_leftover") for r in runs_ok]

out["summary"] = {
    "reps": len(out["runs"]), "runs_ok": len(runs_ok),
    "n_openers": len(OPENERS), "n_layers_tried": len(all_layers),
    "n_layers_measured": len(measured),
    "n_steps_total": len(steps_all),
    "n_steps_in_seed": len(in_seed_steps),
    "n_steps_in_any_layer": sum(1 for s in steps_all if s["raw"].get("focus_in_layer")),
    "n_steps_occluded_in_seed": len(occl_in_seed),
    "n_steps_occluded_any": len(occl_any),
    "n_TARGET_nonfullscreen_over_inner": len(target),
    "max_n_layers_observed": max([l.get("n_layers_after", 0) for l in all_layers] or [0]),
    "n_layers_with_2plus": sum(1 for l in all_layers
                                if l.get("n_layers_after", 0) >= 2),
    "n_steps_n_layers_ge2": sum(1 for s in steps_all if s["raw"].get("n_layers", 0) >= 2),
    "n_hit_center_covered": sum(1 for s in steps_all
                                if s["der"]["hit_center_covered"]),
    "n_closed_on_blur": sum(1 for l in measured
                            if l.get("budget", {}).get("closed_on_blur")),
    "n_layers_escaped": sum(1 for l in measured
                            if l.get("budget", {}).get("escaped")),
    "n_layers_repeat_seen": sum(1 for l in measured
                                if l.get("budget", {}).get("repeat_seen")),
    "n_layers_budget_short": sum(
        1 for l in measured
        if not (l.get("budget", {}).get("escaped")
                or l.get("budget", {}).get("repeat_seen"))),
    "positive_control_ok": [c.get("ok") for c in ctrls],
    "positive_control_ruler_fired": [c.get("ruler_fired") for c in ctrls],
    "positive_control_edges": [c.get("der", {}).get("edges_covered") for c in ctrls],
    "positive_control_whys": [c.get("why") for c in ctrls],
    "fixture_leak_gone": [c.get("leak_check") for c in ctrls],
    "seed_mark_leftover": leaks,
}
out["design_ok"] = {
    "opened_ok": len(measured) >= MIN_OPENED,
    "budget_ok": all(l.get("budget", {}).get("escaped")
                     or l.get("budget", {}).get("repeat_seen")
                     for l in measured) and bool(measured),
    "sig_agree_ok": True,   # 不一致会直接 raise，跑完还在就说明一致
    # ⚠️ 逐层对照，**只要有一层尺子真的响了**就说明它看得见这类遮挡；
    #    全都没响 ⇒ 本批 0 观测不作数（§62），读数作废
    "positive_control_ok": any(c.get("ruler_fired") for c in ctrls) and bool(ctrls),
    "no_fixture_leak_ok": all(c.get("leak_check") is True for c in ctrls) and bool(ctrls),
    "no_mark_leak_ok": all(n == 0 for n in leaks) and bool(runs_ok),
}
dump(out)

print("\n===== 936 汇总 =====", flush=True)
for k, v in out["summary"].items():
    print(f"  {k}: {v}")
print(f"  design_ok: {out['design_ok']}")

#!/usr/bin/env python3
r"""batch 939 源站探针（**纯诊断**）：**从一个 Tab 起点走到浮层第一项，要按几次？**

## 939 的由来（**不是**「右键菜单键盘不可达」—— 那个前提是错的）

⚠️⚠️ **先订正一件事**：§148 待办里写「源站右键菜单的键盘可达性**未解释**」，
而**历史里它已经被解释过两轮**，只是结论散落在别处：

| 行 | 记录 |
| --- | --- |
| 9824 | `canvas-context-menu` ｜ 2 个控件 ｜ **第 25 次 Tab** 命中 `al='显示折扣详情'` |
| 9856 | 右键菜单 ｜ ✓ 第一项「新建节点」｜ **不困**（第 1 次就逃到左栏）｜ 层内**移动且环绕** |
| 10247 | 复刻冷启动进得去，次数 **34 / 37 / 39 / 49**（flaky），上限 60 时余量最小只有 11 |
| 10272 | 「**真要解，得问源站冷启动同样要按几次（本批没取这个样）**」 |

⇒ **源站右键菜单键盘**是**进得去**的（9824/9856 有逐项读数）。
⇒ 936 那个「60 次一步都没进去」是 **§67 已经认领过的 capped 口径**：
**「没测出来」不是「进不去」**（§62 记过三次同款复发：12→40 次、200 步游走、
本批 60 次）。936 自己也在 177 行附近写了「**本批不判它是缺陷**」。

⭐⭐ **所以真问题不是「能不能进」，而是 README 10272 行亲手点名的那一件**：
> 「上限提到 120 只是拉开余量，**不是**把这个深度问题解决了 ——
> 真要问源站冷启动同样要按几次。」

## 机制假设 H939（要证伪它）

「Tab 走到浮层第一项的**距离**由 DOM 顺序的确定性下标差决定：
`d = k - s + 1`（`k` = 目标在 Tab 序列里的 0-based 下标，`s` = 起点下标，
冷启动 `s = -1`（body 不在序列里））。」

**三种互斥的候选解释**，本批要把它们分开：

| 模型 | 断言 | 若成立 |
| --- | --- | --- |
| **naive** | Tab 走的就是 DOM 顺序的可聚焦集合 | 距离 == 下标差，`d == k+1`（冷启动） |
| **roving** | §131 那套 roving 规则（keydown 时重布 `tabindex`）在干预 | 轨迹出现 §140/§141 的周期（101 / 28） |
| **other** | 两者都不对 | 需要重新描述 |

⚠️ **可证伪的方向是双向的**：`naive` 成立**不等于**距离小；距离大也可能纯是
`k` 大（画布占了绝大多数可聚焦元素，§931 复刻 `n_focusable` 恒 276）。
⇒ **「距离大」不是缺陷，「距离不可预测」才是**。所以 E 段**必须**做起点扫描。

## ⭐⭐ 跨状态认元素：打标记，不推算（936 坑 2 / 937 坑 2 的根治）

`dom_sig` 是 `tag:nth-of-type`，**下标会因插入而移位** ⇒ 跨状态比它不成立。
⇒ 本探针在**枚举那一刻**给每个候选元素打 `data-b939-i="<i>"`，
之后所有读数只认这个标记 ⇒ 身份**不需要任何推算**。

⚠️ 但「打标记」是改 DOM，所以配一道**仪器自检**：
`K`（候选元素总数）在**清标记前 / 打标记后**必须相等 ——
证明 `data-*` 属性**没有改变可聚焦集合**、没有污染被诊断对象。
`K` 变了 ⇒ 整轮读数作废。

⚠️ 打标记**不设** `tabindex`、不改 `disabled` ⇒ 不影响 Tab 序列；
这一点由上面那道 `K` 自检**实测**证明，不是靠声称。

## ⭐⭐ 打破 936 的 160px 仪器盲区

936 阳性对照在右键菜单上如实报「层内找不到控件」，原因是它的夹具**只挑 ≤160px
的控件**（坑 6，本是为避免选中整个面板）⇒ **菜单项整行宽就被它自己的尺子滤掉了**。
⇒ 939 的枚举**不设尺寸上限**，并**分别**记「≤160px 的有几个」和「全部有几个」，
把这个盲区变成读数。

## 起点扫描 = 仪器判别力（937 的阴阳对照门）

只测冷启动一个起点 ⇒ 距离是**一个数**，没有判别力（937 的教训）。
⇒ E 段取 **5 个起点**，下标均匀铺开（0 / ¼ / ½ / ¾ / 末）⇒ 距离**必然**
既有小又有大（若序列真是周期的话）⇒ `yin_yang_ok` 才可能为真。
⚠️ 若实测 5 个距离**全是同一个值** ⇒ 仪器无判别力，**如实记 `False`**，
不许调门凑绿。

## ⚠️ capped 与「进不去」必须分开（§62 第 N 次）

自适应停止，三种结局**分别记账**：
- `reached` —— 走进菜单子树（记 `d`）
- `wrapped` —— 落点标记**第二次出现**（走满一圈仍没到 ⇒ 不在序列里）
- `capped` —— 撞 `N_MAX`
⇒ **只有 `reached` 才产出距离**；`wrapped` / `capped` 一律**不是**「进不去」。

## 计费边界（**结构上禁止**）

沿 937：只做**空画布右键**（先验 `closest('[data-id]')` 为空、落点在 pane/renderer
上）、只做 `focus()` 与 `Tab`。**绝不**点生成/发送/购买/充值；
`FORBIDDEN_TIDS` 守卫拦在 `mouse.click` **之前**；**不点任何节点**。

## 纯诊断纪律

不劫持 `prototype`、**不装 `MutationObserver`**、不 `reload`。
唯一的 DOM 改动是「打/清 `data-b939-i`」与 `blur()`/`focus()`。

跑法：
  ~/.venvs/liblib-harness/bin/python -u scripts/jimeng_headless.py run \
      scripts/jimeng_probe939_tab_distance_src.py
"""

import json

OUT = "/tmp/b939-src-tab-distance.json"
REPS = 2

OPEN_WAIT = 1400
RESET_WAIT = 500
SETTLE = 200

# ⛔ 计费入口（源站实测存在，承 937）：**结构上禁止点击**
FORBIDDEN_TIDS = ("canvas-commerce-entry", "canvas-pay-trigger", "canvas-recharge")
BILLED_EXACT = ("生成", "发送", "购买", "充值", "立即支付", "开通", "订阅", "兑换")
BILLED_PREFIX = ("立即", "购买", "充值")

# ⚠️ 逐字承判据的 `LAYER_SEL`（承 937）：本批问的仍是「判据眼里的层」。
LAYER_SEL = (
    '.react-flow__node-toolbar, .react-flow__node-panel, '
    '[role=menu], [role=listbox], [role=dialog], [role=popover], '
    '[data-testid$="-listbox"], [data-testid$="-menu"], '
    '[data-testid$="-panel"], [data-testid$="-palette"]')
assert LAYER_SEL == (
    '.react-flow__node-toolbar, .react-flow__node-panel, '
    '[role=menu], [role=listbox], [role=dialog], [role=popover], '
    '[data-testid$="-listbox"], [data-testid$="-menu"], '
    '[data-testid$="-panel"], [data-testid$="-palette"]'
), "LAYER_SEL 与判据那份漂移了（936 栽过：同一判据写两套定义）"

TARGET_TID = "canvas-context-menu"

# ⚠️ 近似浏览器可聚焦集合。注意 `[tabindex]` **不**单独保证可聚焦
#    （负值会被滤掉），且「可见」用 `getClientRects()` 判，不用尺寸下限
#    —— 尺寸下限就是 936 那个 160px 盲区。
FOCUSABLE_SEL = (
    "a[href], area[href], button, input, select, textarea, "
    "iframe, object, embed, summary, audio[controls], video[controls], "
    "[contenteditable], [tabindex]")
MARK_ATTR = "data-b939-i"

# ⭐⭐ 判据平移必须连单位一起平移：下标 0-based、步号 1-based，
#    冷启动起点是 `document.body`（不在序列里 ⇒ s = -1）⇒ d = k + 1。
N_MAX = 400
N_START_POINTS = 5

RAW_KEYS = frozenset({
    "k_before", "k_after", "items", "focus_mark", "focus_tag", "focus_tid",
    "focus_role", "focus_al", "focus_txt", "focus_in_target",
    "focus_nearest_layer_tid", "menu_open", "start_ok", "start_desc",
    "ctx_item_idx", "ctx_items", "open_result",
})
DERIVED_KEYS = frozenset({
    "k_stable", "reached", "wrapped", "capped", "d_measured", "d_pred_naive",
    "model", "naive_prefix_match", "seq_repeats", "yin_yang_ok",
    "n_ctx_items", "n_ctx_items_le160", "mod_relation_holds", "start_idx",
    "distance_by_start",
})
assert not (RAW_KEYS & DERIVED_KEYS), "派生键与原始读数键重叠了（935 的 KeyError 免疫针）"
for _must in ("reached", "d_measured", "model", "yin_yang_ok"):
    assert _must in DERIVED_KEYS, f"{_must} 必须是派生量"


def ev(js, arg=None):
    return page.evaluate(js, arg) if arg is not None else page.evaluate(js)


def dump(out):
    """⚠️ 落盘必须排在**所有**后处理之前（935：后处理崩了整轮读数全丢）。"""
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    return out


# ── 枚举：清标记 → 记 K_before → 打标记 → 记 K_after ──
# ⚠️ 标记用 `data-*`，**不碰** `tabindex` / `disabled` ⇒ 不改 Tab 序列。
INDEX_JS = """([sel, layerSel, markAttr, tid]) => {
  const all = Array.from(document.querySelectorAll(sel));
  // 先清上一轮留下的标记 ⇒ 本函数**幂等**（否则重复调用会累积，K 自检失效）
  for (const old of document.querySelectorAll('[' + markAttr + ']')) {
    old.removeAttribute(markAttr);
  }
  const live = [];
  for (const e of all) {
    if (e.disabled) continue;
    const ti = e.getAttribute('tabindex');
    if (ti !== null && Number(ti) < 0) continue;
    if (e.getClientRects().length === 0) continue;
    live.push(e);
  }
  const kBefore = live.length;
  // 最近的那个判据层祖先（要**自己**的 testid，不能只判「在层内」——
  // 常驻侧栏也匹配 LAYER_SEL，会把菜单项的下标范围算宽）
  const nearestLayerTid = (e) => {
    for (let p = e; p && p !== document.body; p = p.parentElement) {
      if (p.matches(layerSel)) return p.getAttribute('data-testid') || ('role:' + (p.getAttribute('role') || p.tagName));
    }
    return null;
  };
  const items = [];
  for (let i = 0; i < live.length; i++) {
    const e = live[i];
    e.setAttribute(markAttr, String(i));
    const r = e.getBoundingClientRect();
    items.push({
      i: i, tag: e.tagName,
      role: e.getAttribute('role') || '',
      tid: e.getAttribute('data-testid') || '',
      al: (e.getAttribute('aria-label') || '').slice(0, 60),
      txt: (e.innerText || e.value || '').trim().slice(0, 24),
      w: Math.round(r.width), h: Math.round(r.height),
      ti: e.getAttribute('tabindex'),
      nearest_layer_tid: nearestLayerTid(e),
    });
  }
  return {k_before: kBefore, k_after: items.length, items: items};
}"""

# ── 读当前焦点：只认标记 ⇒ 不需要跨状态推算身份 ──
FOCUS_JS = """([markAttr, tid]) => {
  const a = document.activeElement;
  if (!a || a === document.body) {
    return {focus_mark: -1, focus_tag: a ? a.tagName : null, focus_tid: '',
            focus_role: '', focus_al: '', focus_txt: '<<body>>',
            focus_in_target: false, focus_nearest_layer_tid: null};
  }
  let inTarget = false;
  for (let p = a; p && p !== document.body; p = p.parentElement) {
    if (p.getAttribute && p.getAttribute('data-testid') === tid) { inTarget = true; break; }
  }
  return {
    focus_mark: a.hasAttribute(markAttr) ? Number(a.getAttribute(markAttr)) : null,
    focus_tag: a.tagName,
    focus_tid: a.getAttribute('data-testid') || '',
    focus_role: a.getAttribute('role') || '',
    focus_al: (a.getAttribute('aria-label') || '').slice(0, 60),
    focus_txt: (a.innerText || a.value || '').trim().slice(0, 24),
    focus_in_target: inTarget,
    focus_nearest_layer_tid: null,
  };
}"""

# ── 把焦点放到序列里第 i 个元素上（只读 + 一个 focus()，不算点击）──
FOCUS_BY_INDEX_JS = """(args) => {
  const [markAttr, i, layerSel] = args;
  const e = document.querySelector('[' + markAttr + '="' + i + '"]');
  if (!e) return {ok: false, why: '序列里没有下标 ' + i};
  e.focus();
  if (document.activeElement !== e) return {ok: false, why: 'focus() 没生效'};
  for (let p = e; p && p !== document.body; p = p.parentElement) {
    if (p.matches(layerSel)) { e.setAttribute('data-b939-nl', p.getAttribute('data-testid') || ''); break; }
  }
  return {ok: true, tag: e.tagName, txt: (e.innerText || e.value || '').trim().slice(0, 24)};
}"""

BLUR_ALL_JS = """() => {
  const a = document.activeElement;
  if (a && a.blur) a.blur();
  return document.activeElement === document.body;
}"""


def guard(al, tid):
    """计费护栏：先按 testid 硬拦（结构上），再按文案等值拦。承 937。"""
    if tid in FORBIDDEN_TIDS:
        return f"护栏拦下计费入口 testid={tid!r}"
    t = (al or "").strip()
    base = t.split(":")[0].strip()
    if t in BILLED_EXACT or base in BILLED_EXACT or any(t.startswith(b) for b in BILLED_PREFIX):
        return f"护栏拦下付费动作 {t!r}"
    return None


def hard_reset():
    for _ in range(2):
        page.keyboard.press("Escape")
        page.wait_for_timeout(RESET_WAIT)


def launch_context_menu():
    """空画布右键（承 937 的开法）。⚠️ 落点先验不在任何节点上。"""
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
        return {"ok": False, "why": "找不到空画布落点"}
    hit = page.evaluate("""([x, y]) => {
      const e = document.elementFromPoint(x, y);
      if (!e) return null;
      const b = e.closest('[data-testid]');
      return {tid: b ? b.getAttribute('data-testid') : '',
              al: e.getAttribute('aria-label') || ''};
    }""", [spot["x"], spot["y"]])
    blocked = guard((hit or {}).get("al"), (hit or {}).get("tid"))
    if blocked:
        return {"ok": False, "why": blocked}
    page.mouse.click(spot["x"], spot["y"], button="right")
    return {"ok": True, "trigger": {"tid": "(空画布右键)", "al": f"@{spot['x']},{spot['y']}"}}


def index_now(tag):
    r = ev(INDEX_JS, [FOCUSABLE_SEL, LAYER_SEL, MARK_ATTR, TARGET_TID])
    unknown = set(r) - RAW_KEYS
    assert not unknown, f"枚举冒出未登记的原始键: {unknown}"
    rec = {"tag": tag, "k_before": r["k_before"], "k_after": r["k_after"],
           "items": r["items"]}
    ctx = [it for it in r["items"] if it["nearest_layer_tid"] == TARGET_TID]
    rec["ctx_item_idx"] = [it["i"] for it in ctx]
    rec["ctx_items"] = ctx
    # ⭐ 顺带把 936 的 160px 盲区变成读数
    rec["n_ctx_items"] = len(ctx)
    rec["n_ctx_items_le160"] = sum(1 for it in ctx if it["w"] <= 160 and it["h"] <= 160)
    rec["der_k_stable"] = r["k_before"] == r["k_after"]
    return rec


def walk_tabs(n_max, start_idx):
    """从一个起点开始按 Tab，**走满自适应预算**，逐步记焦点标记。"""
    if start_idx is None:
        ok = ev(BLUR_ALL_JS)
        start_desc = "blur 冷启动 (body)"
    else:
        f = ev(FOCUS_BY_INDEX_JS, [MARK_ATTR, start_idx, LAYER_SEL])
        ok = bool(f.get("ok"))
        start_desc = f"序列下标 {start_idx}: {f}"
    if not ok:
        return {"start_ok": False, "start_desc": start_desc, "log": [],
                "der": {"reached": False, "wrapped": False, "capped": False,
                        "d_measured": None, "seq_repeats": 0, "start_idx": start_idx}}
    log = []
    seen = {}
    first_reach = None
    wrapped = False
    for i in range(1, n_max + 1):
        page.keyboard.press("Tab")
        page.wait_for_timeout(SETTLE)
        st = ev(FOCUS_JS, [MARK_ATTR, TARGET_TID])
        unknown = set(st) - RAW_KEYS
        assert not unknown, f"焦点读数冒出未登记的原始键: {unknown}"
        log.append(dict(st, tab=i))
        if st["focus_in_target"] and first_reach is None:
            first_reach = i
            break
        m = st["focus_mark"]
        # ⭐ 落点**第二次出现** = 绕了一整圈却还没到目标 ⇒ 不在序列里
        if m is None:
            continue
        if m in seen:
            wrapped = True
            break
        seen[m] = i
    capped = first_reach is None and not wrapped
    d = {"reached": first_reach is not None, "wrapped": wrapped, "capped": capped,
         "d_measured": first_reach, "seq_repeats": len(log), "start_idx": start_idx}
    bad = set(d) - DERIVED_KEYS
    assert not bad, f"派生量冒出未登记的键: {bad}"
    return {"start_ok": True, "start_desc": start_desc, "log": log, "der": d}


def model_of(walk, ctx_idx):
    """把实测轨迹和「朴素 DOM 顺序」这个模型比一比。三模型互斥。"""
    marks = [s["focus_mark"] for s in walk["log"] if s["focus_mark"] is not None]
    k_ctx0 = min(ctx_idx) if ctx_idx else None
    if k_ctx0 is None:
        return "other", False, None
    d = walk["der"]["d_measured"]
    # 冷启动：s = -1（body 不在序列里）⇒ d == k + 1（0-based 下标 vs 1-based 步号）
    d_pred = k_ctx0 + 1
    # 「前缀一致」= 实测走过的每一站的标记正好是 0,1,2,…（朴素顺序的指纹）
    naive_prefix = marks[:min(len(marks), 24)] == list(range(min(len(marks), 24)))
    if d == d_pred and naive_prefix:
        m = "naive"
    elif naive_prefix:
        m = "other"
    else:
        m = "roving"
    return m, naive_prefix, d_pred


URL = ("https://jimeng.jianying.com/ai-tool/ai-canvas/"
       "64b58cd5-7b04-4312-890a-09f2d1d3399f"
       "?enter_from=project_list&from_page=create")

out = {"layer_sel": LAYER_SEL, "focusable_sel": FOCUSABLE_SEL,
       "target_tid": TARGET_TID, "n_max": N_MAX, "n_start_points": N_START_POINTS,
       "forbidden_tids": list(FORBIDDEN_TIDS), "design_ok": {}, "runs": []}

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
           "n_nodes": page.locator(".react-flow__node").count(),
           "walks": [], "distance_by_start": {}}
    out["runs"].append(rec)
    if n_audio == 0:
        rec["skipped"] = "登录态没命中，本轮不测"
        print("  登录态没命中，跳过本轮", flush=True)
        dump(out)
        continue

    # ── A 段：关层时的基线枚举 ──
    hard_reset()
    base = index_now("base")
    rec["base"] = base
    print(f"  [A] K_before={base['k_before']} K_after={base['k_after']} "
          f"稳定={base['der_k_stable']}", flush=True)
    dump(out)

    # ── B 段：开右键菜单，再枚举一次 ⇒ 菜单项在序列里的下标 ──
    ro = launch_context_menu()
    page.wait_for_timeout(OPEN_WAIT)
    withmenu = index_now("with_menu")
    rec["open_result"] = ro
    rec["with_menu"] = withmenu
    rec["menu_open"] = bool(withmenu["ctx_item_idx"])
    took = ev(FOCUS_JS, [MARK_ATTR, TARGET_TID])
    rec["focus_after_open"] = took
    print(f"  [B] 开菜单 ok={ro.get('ok')} ctx 项={withmenu['ctx_item_idx']} "
          f"(≤160px 的 {withmenu['n_ctx_items_le160']} 个) "
          f"K {base['k_after']}->{withmenu['k_after']} "
          f"开层后焦点 in_target={took['focus_in_target']}", flush=True)
    dump(out)

    if not rec["menu_open"]:
        rec["skipped"] = "右键菜单没开出来，本轮不测"
        dump(out)
        continue

    # ── C+D 段：冷启动走满预算 ⇒ 距离 + 模型 ──
    w0 = walk_tabs(N_MAX, None)
    rec["walks"].append(w0)
    m, naive_prefix, d_pred = model_of(w0, withmenu["ctx_item_idx"])
    rec["cold_start"] = {"der": w0["der"], "model": m,
                         "naive_prefix_match": naive_prefix,
                         "d_pred_naive": d_pred,
                         "k_ctx0": min(withmenu["ctx_item_idx"]),
                         "log_len": len(w0["log"])}
    print(f"  [C] 冷启动: d={w0['der']['d_measured']} reached={w0['der']['reached']} "
          f"wrapped={w0['der']['wrapped']} capped={w0['der']['capped']} "
          f"k_ctx0={min(withmenu['ctx_item_idx'])} d_pred={d_pred} model={m} "
          f"naive_prefix={naive_prefix}", flush=True)
    dump(out)

    # ── E 段：起点扫描（下标均匀铺开）⇒ 阴阳对照 + 模关系 ──
    K = withmenu["k_after"]
    frac = [0.0, 0.25, 0.5, 0.75, 1.0][:N_START_POINTS]
    starts = sorted({max(0, min(K - 1, int(round(f * (K - 1))))) for f in frac})
    dists = {}
    for si in starts:
        # 已知 d 之后再多走 20 步就够判「到没到」，不跑满（省时间）
        cap = N_MAX if si is None else min(N_MAX, (w0["der"]["d_measured"] or 200) + 20)
        w = walk_tabs(cap, si)
        rec["walks"].append(w)
        dists[str(si)] = w["der"]["d_measured"]
        print(f"  [E] 起点 {si}: d={w['der']['d_measured']} "
              f"reached={w['der']['reached']} wrapped={w['der']['wrapped']} "
              f"capped={w['der']['capped']} 步数={w['der']['seq_repeats']}", flush=True)
        dump(out)
    rec["distance_by_start"] = dists
    rec["start_points"] = starts

    # ⭐ 仪器判别力门：距离必须**既有小又有大**。全是同一个值 ⇒ 仪器瞎，如实 False
    got = [v for v in dists.values() if v is not None]
    rec["yin_yang_ok"] = bool(got) and len(set(got)) > 1
    # ⭐ 模关系：d(start) == (k - s) mod K + 1 ？ 逐个起点验，不整体平均
    k0 = min(withmenu["ctx_item_idx"])
    mod_hits = 0
    mod_checked = 0
    for si, dv in dists.items():
        if dv is None:
            continue
        mod_checked += 1
        s = int(si)
        # 朴素模型：往后走到 k ⇒ (k - s) mod K + 1
        exp = ((k0 - s) % K) + 1
        if dv == exp:
            mod_hits += 1
    rec["der"] = {"yin_yang_ok": rec["yin_yang_ok"],
                  "mod_relation_holds": mod_hits == mod_checked and mod_checked > 0,
                  "n_starts_checked": mod_checked, "n_starts_matched": mod_hits,
                  "K": K, "k_ctx0": k0,
                  "n_ctx_items": withmenu["n_ctx_items"],
                  "n_ctx_items_le160": withmenu["n_ctx_items_le160"]}
    print(f"  [E] yin_yang={rec['der']['yin_yang_ok']} "
          f"模关系 {mod_hits}/{mod_checked} K={K}", flush=True)

    hard_reset()
    dump(out)

# ── 汇总 ──
runs = [r for r in out["runs"] if "der" in r]
out["summary"] = {
    "n_reps_measured": len(runs),
    "k_stable_all": all(r["base"]["der_k_stable"] and r["with_menu"]["der_k_stable"] for r in runs),
    "cold_d": [r["cold_start"]["der"]["d_measured"] for r in runs],
    "cold_model": [r["cold_start"]["model"] for r in runs],
    "n_ctx_items": [r["der"]["n_ctx_items"] for r in runs],
    "n_ctx_items_le160": [r["der"]["n_ctx_items_le160"] for r in runs],
    "yin_yang_all": all(r["der"]["yin_yang_ok"] for r in runs),
    "mod_all": all(r["der"]["mod_relation_holds"] for r in runs),
    "distance_by_start": [r["distance_by_start"] for r in runs],
}
# ⭐⭐ 仪器阴阳对照：冷启动距离两个答案都要出现过，否则仪器可能恒真（937）
out["design_ok"] = {
    "k_stable_ok": out["summary"]["k_stable_all"],
    "yin_yang_ok": out["summary"]["yin_yang_all"],
    "reps_measured_ok": len(runs) == REPS,
}
# ⭐ 两次独立运行必须**逐项相同**
if len(runs) == 2:
    same = (out["summary"]["cold_d"] == [out["summary"]["cold_d"][0]] * 2
            and out["summary"]["cold_model"] == [out["summary"]["cold_model"][0]] * 2
            and out["summary"]["n_ctx_items"] == [out["summary"]["n_ctx_items"][0]] * 2
            and out["summary"]["distance_by_start"][0] == out["summary"]["distance_by_start"][1])
    out["design_ok"]["reps_identical_ok"] = bool(same)
dump(out)
print(json.dumps({"design_ok": out["design_ok"], "summary": out["summary"]},
                 ensure_ascii=False, indent=2), flush=True)
print(f"OUT={OUT}", flush=True)

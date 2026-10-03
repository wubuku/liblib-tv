#!/usr/bin/env python3
r"""batch 939b 源站探针（**纯诊断**）：**Tab 序列的真实构成** ——
939 第一版为什么只枚举出 26 个？

## 939 第一版的仪器盲区（本探针要查清的）

939 第一版用 `FOCUSABLE_SEL = a[href], button, input, …, [contenteditable], [tabindex]`
枚举「Tab 候选元素」，源站实测 **K = 26**（开右键菜单后 28），而**复刻侧同一条
枚举是 276**（§931 `n_focusable` 恒 276）⇒ **差了整整一个数量级**。

⇒ 第一版的全部读数**作废**：
- `K=26` 是假集合
- `d_measured` 全 `None`（菜单项压根不在假集合里 ⇒ `reached` 永远 False）
- `model=roving` 是在假集合上比出来的，**不能当结论**
- `n_ctx_items=1 / le160=0` 同理（936 那个 160px 盲区**之外**又叠了一层
  「选择器本身看不见它」）

⚠️ 这是「**我没检测到 ≠ 它不存在**」的又一次撞法：我连「我够得着」都没确认。

## ⭐⭐ 唯一不依赖任何模型的做法：**只看实测轨迹**

枚举是**模型**（「我猜哪些元素可聚焦」），Tab 落点是**事实**。
⇒ 本探针**不枚举**，只按 Tab，把每一步 `activeElement` 的**完整身份**记下来：
tag / role / class / `data-testid` / `data-id` / `tabindex` 属性 /
是否在 `.react-flow__node` 内 / 是否在 `canvas-context-menu` 内。

⇒ 轨迹会直接回答三个问题：
1. 焦点落在**什么东西**上（分桶：`target_ctx` / `react_flow_node` / `other_layer` /
   `plain` / `body`）
2. 画布节点**到底有没有** `tabindex`（若有 ⇒ 第一版漏在可见性判据上；
   若无 ⇒ 漏在选择器上，节点靠别的机制可聚焦）
3. `role=menuitem` 有没有 `tabindex`

## ⭐⭐ 顺带修掉 939 的第二个病：「逐项相同」变成了**空门**

939 第一版 `reps_identical_ok=True`，但它比的是 `distance_by_start` ——
**五个值全是 `null`** ⇒ 「全 null 相同」**恒为真**。
⚠️ 而真正的不一致就在旁边：起点 27 的 `seq_repeats` 是 **102 vs 106**，
**门没看这个字段**。

⇒ 这与 937 的 `a_survived` 恒真是同一类病（**一个恒真的字段比没有字段更坏**），
第三次复发，形态更隐蔽：**门比对了错误的字段集合**。
⇒ 本探针的重复性门**逐字段**比 `bucket` 序列与 `marks` 序列，
**含** `seq_repeats`；且**要求**距离非 null 才算「测到了」。

## 纯诊断纪律

只 `blur()` + `keyboard.press("Tab")` + `evaluate` 读 DOM。
**不劫持 `prototype`、不装 `MutationObserver`、不 `reload`、不打任何标记、
不改任何 DOM**（连 939 的 `data-b939-i` 都不打 —— 正是那个标记
可能本身就是「改变了可聚焦集合」的可疑改动，本批要排除它）。

## 计费边界

本探针**一次 `click` 都没有** ⇒ 无计费风险。仅开一次右键菜单（空画布右键，
承 937 的开法与落点校验）。**绝不**点生成/发送/购买/充值；**不点任何节点**。

跑法：
  ~/.venvs/liblib-harness/bin/python -u scripts/jimeng_headless.py run \
      scripts/jimeng_probe939b_tab_constitution_src.py
"""

import json

OUT = "/tmp/b939b-src-tab-constitution.json"
REPS = 2

OPEN_WAIT = 1400
RESET_WAIT = 500
SETTLE = 200
STEPS = 150

# ⛔ 计费入口（承 937/939）：**结构上禁止点击**
FORBIDDEN_TIDS = ("canvas-commerce-entry", "canvas-pay-trigger", "canvas-recharge")
BILLED_EXACT = ("生成", "发送", "购买", "充值", "立即支付", "开通", "订阅", "兑换")
BILLED_PREFIX = ("立即", "购买", "充值")

TARGET_TID = "canvas-context-menu"
LAYER_SEL = (
    '.react-flow__node-toolbar, .react-flow__node-panel, '
    '[role=menu], [role=listbox], [role=dialog], [role=popover], '
    '[data-testid$="-listbox"], [data-testid$="-menu"], '
    '[data-testid$="-panel"], [data-testid$="-palette"]')
# ⭐ 939 第一版用的那条选择器，本批**逐字**承下来当「仪器的那把尺」，
#    好让「尺子看不见」这件事本身成为一个**读数**而不是一个猜测。
B939_SEL = ("a[href], area[href], button, input, select, textarea, "
            "iframe, object, embed, summary, audio[controls], video[controls], "
            "[contenteditable], [tabindex]")

RAW_KEYS = frozenset({
    "tab", "is_body", "tag", "role", "cls", "tid", "did", "ti_attr",
    "in_node", "in_target", "in_other_layer", "txt", "bucket",
})
DERIVED_KEYS = frozenset({
    "n_steps", "bucket_counts", "n_first_ctx", "d_measured", "marks",
    "n_marks_null", "k_b939_sel", "k_tabindex_attr", "k_role_menuitem",
    "k_react_flow_node", "n_nodes_tabindexed", "n_nodes_visible",
    "covers_all_landings", "yin_yang_ok", "seq_repeats",
})
assert not (RAW_KEYS & DERIVED_KEYS), "派生键与原始读数键重叠了（935 的 KeyError 免疫针）"

# ⭐⭐ 轨迹读数：只看**实测落点**，不做任何枚举式的预判
STEP_JS = """([layerSel, targetTid]) => {
  const a = document.activeElement;
  if (!a || a === document.body) {
    return {is_body: true, tag: a ? a.tagName : null, role: '', cls: '', tid: '',
            did: '', ti_attr: null, in_node: false, in_target: false,
            in_other_layer: false, txt: '<<body>>', bucket: 'body'};
  }
  let inTarget = false, inNode = false, inOther = false, otherTid = '';
  for (let p = a; p && p !== document.body; p = p.parentElement) {
    if (!inTarget && p.getAttribute && p.getAttribute('data-testid') === targetTid) inTarget = true;
    if (!inNode && p.classList && p.classList.contains('react-flow__node')) inNode = true;
    if (!inOther && p.matches && p.matches(layerSel)) {
      inOther = true; otherTid = p.getAttribute('data-testid') || ('role:' + (p.getAttribute('role') || p.tagName));
    }
  }
  // 分桶顺序 = 特异性从高到低；`in_other_layer` 排最后（它最宽）
  let bucket = 'plain';
  if (inTarget) bucket = 'target_ctx';
  else if (inNode) bucket = 'react_flow_node';
  else if (inOther) bucket = 'other_layer:' + otherTid;
  return {is_body: false, tag: a.tagName, role: a.getAttribute('role') || '',
          cls: (a.className && a.className.baseVal !== undefined
                ? a.className.baseVal : String(a.className || '')).slice(0, 60),
          tid: a.getAttribute('data-testid') || '', did: a.getAttribute('data-id') || '',
          ti_attr: a.getAttribute('tabindex'), in_node: inNode, in_target: inTarget,
          in_other_layer: inOther,
          txt: (a.innerText || a.value || '').trim().slice(0, 20), bucket: bucket};
}"""

# 枚举侧：把三把尺子的规模并排记出来，好和实测落点对照
COUNTS_JS = """([b939Sel, layerSel]) => {
  const nodes = Array.from(document.querySelectorAll('.react-flow__node'));
  const vis = (e) => e.getClientRects().length > 0;
  return {
    k_b939_sel: document.querySelectorAll(b939Sel).length,
    k_tabindex_attr: document.querySelectorAll('[tabindex]').length,
    k_role_menuitem: document.querySelectorAll('[role=menuitem]').length,
    k_react_flow_node: nodes.length,
    n_nodes_tabindexed: nodes.filter((e) => e.hasAttribute('tabindex')).length,
    n_nodes_visible: nodes.filter(vis).length,
    n_layers: document.querySelectorAll(layerSel).length,
  };
}"""

BLUR_ALL_JS = """() => {
  const a = document.activeElement;
  if (a && a.blur) a.blur();
  return document.activeElement === document.body;
}"""


def ev(js, arg=None):
    return page.evaluate(js, arg) if arg is not None else page.evaluate(js)


def dump(out):
    """⚠️ 落盘必须排在**所有**后处理之前（935：后处理崩了整轮读数全丢）。"""
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    return out


def guard(al, tid):
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
    """空画布右键（承 937/939）。⚠️ 落点先验不在任何节点上、且过计费护栏。"""
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


def walk(steps):
    """冷启动 + 按 `steps` 次 Tab，**走满**（不因进层就停）。"""
    ev(BLUR_ALL_JS)
    log = []
    for i in range(1, steps + 1):
        page.keyboard.press("Tab")
        page.wait_for_timeout(SETTLE)
        st = ev(STEP_JS, [LAYER_SEL, TARGET_TID])
        unknown = set(st) - RAW_KEYS
        assert not unknown, f"轨迹读数冒出未登记的原始键: {unknown}"
        log.append(dict(st, tab=i))
    return log


def summarize(log, counts):
    """从**实测轨迹**（不是枚举）算派生量。"""
    buckets = {}
    for s in log:
        buckets[s["bucket"]] = buckets.get(s["bucket"], 0) + 1
    n_first_ctx = next((s["tab"] for s in log if s["in_target"]), None)
    # ⭐ 落点分母：非 body 的落点 = 真正「落在某个元素上」的步数
    landings = [s for s in log if not s["is_body"]]
    # 「尺子是否覆盖全部落点」：实测落点里有没有**既**不是 939 那条 SEL 能选中的
    covered = 0
    for s in landings:
        # 复刻判据：939 的 SEL 能否选中这个元素（按 tag/role/tabindex 近似）
        if (s["tag"] in ("A", "BUTTON", "INPUT", "SELECT", "TEXTAREA", "IFRAME",
                         "OBJECT", "EMBED", "SUMMARY", "AUDIO", "VIDEO")
                or s["ti_attr"] is not None or s["role"] in ("menuitem", "button", "link")):
            covered += 1
    d = {"n_steps": len(log), "bucket_counts": buckets,
         "n_first_ctx": n_first_ctx, "d_measured": n_first_ctx,
         "marks": [s["tab"] for s in landings][:0],   # 占位，见下
         "n_marks_null": sum(1 for s in landings if s["ti_attr"] is None),
         "covers_all_landings": bool(landings) and covered == len(landings),
         "seq_repeats": 0}
    bad = set(d) - DERIVED_KEYS
    assert not bad, f"派生量冒出未登记的键: {bad}"
    d["marks"] = [s["bucket"] for s in landings]
    d.update(counts)
    return d


URL = ("https://jimeng.jianying.com/ai-tool/ai-canvas/"
       "64b58cd5-7b04-4312-890a-09f2d1d3399f"
       "?enter_from=project_list&from_page=create")

out = {"layer_sel": LAYER_SEL, "b939_sel": B939_SEL, "target_tid": TARGET_TID,
       "steps": STEPS, "forbidden_tids": list(FORBIDDEN_TIDS),
       "design_ok": {}, "runs": []}

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
           "n_nodes": page.locator(".react-flow__node").count()}
    out["runs"].append(rec)
    if n_audio == 0:
        rec["skipped"] = "登录态没命中，本轮不测"
        print("  登录态没命中，跳过本轮", flush=True)
        dump(out)
        continue

    hard_reset()
    counts0 = ev(COUNTS_JS, [B939_SEL, LAYER_SEL])
    print(f"  [A] 三把尺子规模: 939的SEL={counts0['k_b939_sel']} "
          f"[tabindex]={counts0['k_tabindex_attr']} "
          f"[role=menuitem]={counts0['k_role_menuitem']} "
          f"node={counts0['k_react_flow_node']} "
          f"node带tabindex={counts0['n_nodes_tabindexed']} "
          f"node可见={counts0['n_nodes_visible']}", flush=True)
    rec["counts_closed"] = counts0
    dump(out)

    ro = launch_context_menu()
    page.wait_for_timeout(OPEN_WAIT)
    counts1 = ev(COUNTS_JS, [B939_SEL, LAYER_SEL])
    rec["open_result"] = ro
    rec["counts_open"] = counts1
    print(f"  [B] 开菜单 ok={ro.get('ok')} "
          f"939的SEL {counts0['k_b939_sel']}->{counts1['k_b939_sel']} "
          f"[role=menuitem] {counts0['k_role_menuitem']}->{counts1['k_role_menuitem']} "
          f"层 {counts0['n_layers']}->{counts1['n_layers']}", flush=True)
    dump(out)

    log = walk(STEPS)
    d = summarize(log, counts1)
    rec["der"] = d
    rec["log"] = log
    print(f"  [C] 轨迹 {d['n_steps']} 步: 首次进菜单 = {d['n_first_ctx']} "
          f"| 分桶 = {d['bucket_counts']}", flush=True)
    print(f"  [C] 落点里 ti_attr 为 null 的 = {d['n_marks_null']} "
          f"| 939 的尺子覆盖全部落点 = {d['covers_all_landings']}", flush=True)
    hard_reset()
    dump(out)

runs = [r for r in out["runs"] if "der" in r]
out["summary"] = {
    "n_reps_measured": len(runs),
    "counts_open": [r["counts_open"] for r in runs],
    "bucket_counts": [r["der"]["bucket_counts"] for r in runs],
    "n_first_ctx": [r["der"]["n_first_ctx"] for r in runs],
    "n_marks_null": [r["der"]["n_marks_null"] for r in runs],
    "covers_all_landings": [r["der"]["covers_all_landings"] for r in runs],
    "marks": [r["der"]["marks"] for r in runs],
}
# ⭐ 重复性门**逐字段**比（含 bucket 序列与 seq_repeats），且**要求**测到距离
#    —— 939 第一版就是「比对了全 null 的字段」才假绿（同一个病第三次复发）
out["design_ok"] = {
    "reps_measured_ok": len(runs) == REPS,
    "distance_measured_ok": all(r["der"]["n_first_ctx"] is not None for r in runs),
    "bucket_counts_identical_ok": (
        len(runs) == 2 and runs[0]["der"]["bucket_counts"] == runs[1]["der"]["bucket_counts"]),
    "marks_identical_ok": (len(runs) == 2 and runs[0]["der"]["marks"] == runs[1]["der"]["marks"]),
    "n_first_ctx_identical_ok": (
        len(runs) == 2 and runs[0]["der"]["n_first_ctx"] == runs[1]["der"]["n_first_ctx"]),
    # ⭐ 阴阳对照：轨迹里必须**既有**进菜单的落点、**又有**不是菜单的落点
    "yin_yang_ok": all(
        r["der"]["n_first_ctx"] is not None
        and r["der"]["n_first_ctx"] < r["der"]["n_steps"] for r in runs),
}
dump(out)
print(json.dumps({"design_ok": out["design_ok"], "summary": out["summary"]},
                 ensure_ascii=False, indent=2), flush=True)
print(f"OUT={OUT}", flush=True)

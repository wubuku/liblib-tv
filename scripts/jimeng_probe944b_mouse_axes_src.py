#!/usr/bin/env python3
r"""batch 944 源站探针（**纯诊断**）：把 943 标为「未测」的两条轴补上，
并追问「增长上限」。

## 944 的由来：943 明确挂着的三个未查项

`CANVAS_BASELINE` 里原样记着（原文一字未删）：

1. **落点角色**（点节点**本体** vs 点**内部控件**）**未测**；
2. **「不带 `tabindex` 的节点数」增长的**上限未测**（连点 5 次看到 1→6）；
3. 点节点**内部控件**是不是同一条规则**未测**。

⇒ 本批一次测掉三条，并多加一条 943 没提但同样该问的：**选中态**
（点**已选中**的节点 vs 点未选中的）。

## ⭐ 为什么不直接点内部控件：先做了 944a 纯读发现

⚠️ 节点**内部**有 **85 个 `BUTTON`**（944a 实测，2/2 逐字相同）——
点它们**可能是有破坏性的**（工具条上很可能有删除/移除）。
在源站上真删掉别人的东西、并且让后面所有读数作废，**代价太高**。

⇒ 所以先跑 `jimeng_probe944a_node_inner_scan_src.py`（**纯读、零点击**）摸底，
实测：**94 个可点的内部落点**里 `BUTTON` **只有 3 个**（85 个 BUTTON 大多在
**选中后才出现**的节点工具条上），且**带删除/移除语义的 0 个**。
⇒ 据此：本批的**内部元素臂**用**非交互**的内部后代（`PATH`/`SPAN`/`DIV`），
而那 3 个 `BUTTON` 里可点的一个是「添加素材到时间线」（**会改状态**）
⇒ ⭐⭐ **BUTTON 那一击放到整个序列的最后** ——
不可逆的动作放最后，前面所有读数就都不会被它连累（承「不要删掉承重前置动作」）。

## 三条臂与它们要回答的问题

| 臂 | 问题 | 判决点 |
| --- | --- | --- |
| **L（增长上限）** | 「不带 ti」一路涨到哪为止？ | 逐次 `n_without_ti` 序列 + **平台期**（连续 2 次咬到却不再涨） |
| **S（选中态）** | 点**已选中**的节点还是不是一次臂事件？ | 第二次点同节点：`bit` 真不真、`removed` 是什么 |
| **I（内部元素）** | 落点**不是本体**、是节点**内部后代**时同不同一条？ | `removed`/`added`/`changed` 三元组与本体臂对比 |
| **B（BUTTON，最后）** | 点**内部控件**是不是同一条？ | 同样记三元组，**并记 `n_nodes` 变没变、有没有开层** |

⭐ **为什么「平台期」比「涨到几」重要**：涨到几是**易变量**（节点数 74→77 逐轮变），
「连续两次咬到却不再涨」是**关系式**（承「预算类要求用关系式」）。

## ⭐ 补偿是「一次 Tab 全补」还是「一次 Tab 补一个」

943 看到键盘臂第一击把**全部**删掉的都写回（6 个一次补完）。
⚠️ 但那是在只有 5 次点击的小样本上看到的 ⇒ **规模变大之后还成立吗**？
⇒ 本批在跑完 L 臂（上限附近）之后连按 `N_REC` 次 `Tab`，
**逐次**记 `n_without_ti` ⇒ 直接读出**需要几次才能回到 1**。

## 复用与防漂移（承 913 / 940）

普查 / 落点搜索 / 计费守卫 / 等稳定这套机制 943 已经验过。
⚠️ 探针是 harness `exec` 进来的、**不是可 import 的模块** ⇒ 只能复制。
⇒ 按 940 的办法：**复制之后逐字 assert 与 943 那份相同**
⇒ 不给「两份慢慢分家」留任何余地（936 栽过：同一判据写两套定义）。

## 设计门（`design_ok`，每轮判一次，**只判 setup，不判机制**）

1. `init_ok` —— 初始化那一击之后身份**已稳**（承 943 的尺子自证）
2. `landed_ok` —— 至少 **4** 次点击**真的咬到**（点后焦点在节点内）
3. `plateau_or_cap_ok` —— L 臂**跑到平台期**或**打满上限**（二者之一即可）
4. `sel_ok` —— 选中态那一对**两次都咬到**
5. `inner_ok` —— 内部元素臂至少 **2** 次咬到
6. ⭐ `no_destroy_ok` —— **全程 `n_nodes` 一次都没减少**
   （真掉节点了 ⇒ 这一轮作废，且说明有破坏性动作被点到）
7. `identity_ok` —— 每一对被判决的普查身份逐位相同

## 判据纪律

- **纯诊断**：普查**纯读**，**不劫持 `prototype`、不装 `MutationObserver`**
- 每轮之间**重新 goto** 重置（AI 侧栏 Esc 关不掉，940 撞过）
- **重复 2 轮**（一次成功不叫可靠）
- **落盘排在所有后处理之前**（935：后处理崩了整轮读数全丢）
- **派生键不许与原始键重叠**（935 的 `KeyError` 免疫针）
- ⚠️ **不许用切片改文件**：`s[a:b]` 在 `a > b` 时是空串，
  而 `str.replace("", X)` 会把 `X` 插到每个字符之间（943 因此把文件撑到 29 万行）

## 计费边界

点**节点本体**、节点**内部非交互后代**，以及**最后那一个 BUTTON**
（实测文案「添加素材到时间线」，不在计费清单内）。
⛔ 守卫拦在 `mouse.click` **之前**，契约是「**我正要点的这个元素**是什么」。
**本批零计费动作。**

跑法：
  ~/.venvs/liblib-harness/bin/python -u scripts/jimeng_headless.py run \
      scripts/jimeng_probe944b_mouse_axes_src.py
"""

import json
import pathlib

OUT = "/tmp/b944b-mouse-axes.json"
REPS = 2
P943 = pathlib.Path(__file__).with_name(
    "jimeng_probe943_arm_relation_src.py")

SETTLE = 350
BLANK_WAIT = 900
N_CAP = 30               # L 臂上限（**关系式靠「平台期」判定，不靠这个数**）
N_REC = 6                # 连按几下 Tab 看补偿
N_SELECT = 4             # 选中态那一对的候选节点数
N_INNER = 3              # 内部元素臂次数

FORBIDDEN_TIDS = ("canvas-commerce-entry", "canvas-pay-trigger",
                  "canvas-recharge")
BILLED_EXACT = ("生成", "发送", "购买", "充值", "立即支付", "开通", "订阅", "兑换")
BILLED_PREFIX = ("立即", "购买", "充值")

NODE_SEL = ".react-flow__node"
HIT_FORBIDDEN = ("BUTTON", "INPUT", "A", "SELECT", "TEXTAREA", "LABEL", "OPTION")

RAW_KEYS = frozenset({
    "n_nodes", "n_with_ti", "n_without_ti", "ids", "cls", "ti",
    "removed", "added", "changed", "bit", "identity_stable", "diff_ids",
    "hit_cls",
    "diff_detail", "point", "i", "k", "arm", "landed", "hit_tag", "hit_kind",
    "active_tag", "active_tid", "focus_in_node", "n_diff", "blank", "layers_n",
    "layers_before", "layers_after",
})
# ⚠️ `identity_stable` 是 `delta()` 的**原始**读数（承 943），
#    **不是**派生量 ⇒ 只登记在 RAW 那边。
#    ⚠️ 第一版把它**同时**写进两边，当场被这道免疫针抓红 —— 这就是这道门
#    存在的理由（935）：重名会让「按原始键取值」那一步取错。
DERIVED_KEYS = frozenset({
    "n_landed", "n_bit", "plateau_at", "capped",
    "design_ok", "n_blank", "n_settle", "L_series", "comp_series", "plateau_found",
    "no_destroy", "internal_button_is_last",
})
assert not (RAW_KEYS & DERIVED_KEYS), "派生键与原始读数键重叠了（935 的 KeyError 免疫针）"
for _must in ("design_ok", "plateau_found", "L_series", "comp_series",
              "no_destroy"):
#    ⚠️ `identity_stable` **不在**这个列表里：它是 `delta()` 的原始读数（承 943）
#    —— 第一版把它当派生量、又当原始量，两边都登记，免疫针当场抓红。
    assert _must in DERIVED_KEYS, f"{_must} 必须是派生量"

# ── 空白点（承 921 / 943 逐字）──────────────────────────────────────
BLANK_JS = """() => {
  for (const [x, y] of [[1300, 1000], [1360, 920], [1220, 1080],
                        [1400, 840], [400, 1080]]) {
    const t = document.elementFromPoint(x, y);
    if (t && t.closest('.react-flow__pane')
        && !t.closest('.react-flow__node')) return [x, y];
  }
  return null;
}"""

# ── 普查（承 943 逐字）─────────────────────────────────────────────
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

# ── 落点搜索（承 943 逐字）：**节点本体**上的点 ────────────────────
POINT_JS = """([nodeSel, i, forbidden]) => {
  const el = document.querySelectorAll(nodeSel)[i];
  if (!el) return null;
  const r = el.getBoundingClientRect();
  const f = [0.5, 0.35, 0.65, 0.2, 0.8];
  for (const y0 of f) {
    for (const x0 of f) {
      const x = Math.round(r.left + r.width * x0);
      const y = Math.round(r.top + r.height * y0);
      if (x < 0 || y < 0) continue;
      const at = document.elementFromPoint(x, y);
      if (!at) continue;
      const tag = (at.tagName || '').toUpperCase();
      if (forbidden.indexOf(tag) >= 0) continue;
      if (!el.contains(at)) continue;
      return [x, y, tag];
    }
  }
  return null;
}"""

# ── ⭐ 落点搜索（**新增**）：节点**内部后代**上的点（不要本体）──────
INNER_POINT_JS = """([nodeSel, i, wantTags]) => {
  const el = document.querySelectorAll(nodeSel)[i];
  if (!el) return null;
  const r = el.getBoundingClientRect();
  const f = [0.5, 0.3, 0.7, 0.15, 0.85];
  const seen = new Set();
  for (const y0 of f) {
    for (const x0 of f) {
      const x = Math.round(r.left + r.width * x0);
      const y = Math.round(r.top + r.height * y0);
      if (x < 0 || y < 0) continue;
      const at = document.elementFromPoint(x, y);
      if (!at || at === el) continue;
      if (!el.contains(at)) continue;
      const tag = (at.tagName || '').toUpperCase();
      if (wantTags.indexOf(tag) < 0) continue;
      const cls = String(at.className && at.className.baseVal !== undefined
                         ? at.className.baseVal : (at.className || ''));
      const key = tag + '|' + cls;
      if (seen.has(key)) continue;
      seen.add(key);
      // ⚠️ 这里**不**截断 className。第一版在这儿截了一次，被自己那道
      //   「普查 JS 里只许有『截字符串』那一种形态」的门当场抓红。
      //   ⇒ **改代码而不是放宽门** —— 把门改成「刚好合这份代码」，
      //   就等于给下一个截取留了一道后门（门还在，测的东西已悄悄变了）。
      //   截断挪到 Python 侧做（只影响打印，不影响读数）。
      // ⭐⚠️ 而且这段注释**第一版还踩了一次**：注释里把那行代码**原样抄了一遍**，
      //   于是计数器**把注释里的字面量也算进去**、照样报红 ——
      //   与 942 的 DDDD.1（判据数到了它自己写的字面量）**同一族**。
      //   ⇒ 写注释时**别把被计数的字面量抄进来**。
      return [x, y, tag, cls];
    }
  }
  return null;
}"""

# ── 焦点（承 943 逐字）─────────────────────────────────────────────
FOCUS_JS = """([nodeSel]) => {
  const a = document.activeElement;
  if (!a) return {active_tag: null, active_tid: null, focus_in_node: false};
  const host = a.closest('[data-testid]');
  const node = a.closest(nodeSel);
  return {active_tag: (a.tagName || '').toUpperCase(),
          active_tid: host ? host.getAttribute('data-testid') : null,
          focus_in_node: !!node};
}"""

# ── ⭐ 层计数（用来发现「有没有开层」）──────────────────────────────
LAYERS_JS = """() => {
  return document.querySelectorAll(
    '[role=menu],[role=listbox],[role=dialog],[role=popover],'
    + '[data-testid$="-listbox"],[data-testid$="-menu"],'
    + '[data-testid$="-panel"],[data-testid$="-palette"]').length;
}"""

# ── ⭐⭐ 防漂移：逐字断言这四段与 943 那份相同（940 的办法）──────────
_p943src = P943.read_text(encoding="utf-8") if P943.exists() else ""
for _name in ("BLANK_JS", "CENSUS_JS", "POINT_JS", "FOCUS_JS"):
    _mine = eval(_name)                       # noqa: S307 — 本文件自己定义的常量
    assert _mine in _p943src, (
        f"{_name} 与 943 那份**不一致** —— 两份定义开始分家了"
        f"（936 栽过：同一判据写两套定义）")
assert "INNER_POINT_JS" not in _p943src, "944 的新件别混进「逐字相同」那组"

SLICE_STR = "|| '').slice(0, "
for _name in ("CENSUS_JS", "POINT_JS", "FOCUS_JS", "INNER_POINT_JS"):
    _js = eval(_name)                         # noqa: S307
    assert _js.count("slice(") == _js.count(SLICE_STR), (
        f"{_name} 里有**非字符串**切片（§131：切片会把规律读反）")


def ev(js, arg=None):
    return page.evaluate(js, arg) if arg is not None else page.evaluate(js)


def dump(out):
    """⚠️ 落盘必须排在**所有**后处理之前（935）。"""
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)


def guard(al, tid):
    """⛔ 计费守卫：契约是「**我正要点的这个元素**是什么」。"""
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


def delta(pre, post):
    """逐**身份**对齐的两张表之差；身份对不上**如实记下**，不静默丢弃。"""
    a, b = pre["ids"], post["ids"]
    if a != b:
        diff = sorted({int(k) for k in set(a) | set(b)
                       if a.get(k) != b.get(k)})
        return {"identity_stable": False, "removed": [], "added": [],
                "changed": [], "n_without_ti": post["n_without_ti"],
                "bit": False, "diff_ids": diff}
    removed, added, changed = [], [], []
    ta, tb = pre["ti"], post["ti"]
    for i in sorted(a, key=lambda x: int(x)):
        was, cur = ta[i], tb[i]
        if was is None and cur is not None:
            added.append(int(i))
        elif was is not None and cur is None:
            removed.append(int(i))
        elif was != cur:
            changed.append([int(i), was, cur])
    return {"identity_stable": True, "removed": removed, "added": added,
            "changed": changed, "n_without_ti": post["n_without_ti"],
            "bit": bool(removed or added or changed), "diff_ids": []}


URL = ("https://jimeng.jianying.com/ai-tool/ai-canvas/"
       "64b58cd5-7b04-4312-890a-09f2d1d3399f"
       "?enter_from=project_list&from_page=create")

out = {"node_sel": NODE_SEL, "reps": REPS, "n_cap": N_CAP, "n_rec": N_REC,
       "forbidden_tids": list(FORBIDDEN_TIDS),
       "precedent": "jimeng_probe944a_node_inner_scan_src.py（纯读发现，2/2）",
       "void_runs": [],
       "runs": []}


def boot():
    page.goto(URL, wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(10000)
    page.set_viewport_size({"width": 1512, "height": 1200})
    page.wait_for_timeout(3000)
    n = page.locator('button[aria-label="音频"]').count()
    if n == 0:
        page.wait_for_timeout(8000)
        n = page.locator('button[aria-label="音频"]').count()
    return n


def click_and_measure(rec, arm, key, pre, pt, kind):
    """点一下并记三元组。**返回** post 普查（供下一击当 pre）。"""
    guard_point(pt[0], pt[1])
    page.mouse.click(pt[0], pt[1])
    page.wait_for_timeout(SETTLE)
    post = ev(CENSUS_JS, [NODE_SEL])
    d = delta(pre, post)
    f = ev(FOCUS_JS, [NODE_SEL])
    landed = bool(f["focus_in_node"])
    row = {"arm": arm, key[0]: key[1], "landed": landed, "hit_kind": kind,
           "hit_tag": pt[2] if len(pt) > 2 else None,
           # ⭐ 截断只在**打印/记读数**时做，JS 侧原样返回（见上）
           "hit_cls": (pt[3][:60] if len(pt) > 3 else None),
           "bit": d["bit"],
           "removed": d["removed"], "added": d["added"],
           "changed": d["changed"], "identity_stable": d["identity_stable"],
           "diff_ids": d["diff_ids"],
           "pre_without_ti": pre["n_without_ti"],
           "post_without_ti": post["n_without_ti"],
           "pre_nodes": pre["n_nodes"], "post_nodes": post["n_nodes"],
           "active_tag": f["active_tag"], "focus_in_node": f["focus_in_node"]}
    rec["arms"].append(row)
    print(f"    [{arm}] {key[1]}{'' if landed else ' ⚠️没咬到'} "
          f"removed={d['removed']} added={d['added']} changed={d['changed']} "
          f"不带ti {pre['n_without_ti']}→{post['n_without_ti']} "
          f"节点 {pre['n_nodes']}→{post['n_nodes']}", flush=True)
    dump(out)
    return post, row


for rep in range(1, REPS + 1):
    print(f"===== rep {rep} =====", flush=True)
    n_audio = boot()
    rec = {"rep": rep, "n_audio_rail_button": n_audio, "arms": []}
    out["runs"].append(rec)
    dump(out)
    if n_audio == 0:
        rec["skipped"] = "登录态没命中，本轮不测"
        print("  登录态没命中，跳过本轮", flush=True)
        dump(out)
        continue

    # ① 进画布 + 初始化 + ⭐ 等身份稳定（承 943 的尺子自证）
    sp = ev(BLANK_JS)
    rec["blank"] = sp
    if sp:
        guard_point(sp[0], sp[1])
        page.mouse.click(sp[0], sp[1])
        page.wait_for_timeout(BLANK_WAIT)
    pre = ev(CENSUS_JS, [NODE_SEL])
    rec["clean"] = {"n_nodes": pre["n_nodes"], "n_with_ti": pre["n_with_ti"]}
    # ⚠️⚠️⚠️ 第一版这里有**两个**错，第二个把整个 L 臂的绝对值全带歪了：
    #   ① 退出循环时**没有 `pre = cur`** ⇒ 后面每一击的 `pre` 都是**陈旧普查**
    #      ⇒ 第一次点击读出「不带 ti 76→0」，那是**基线陈旧**的假象，
    #         不是「点击触发了初始化」；
    #   ② 判据只比 `ids`，而 `ids` **不含 tabindex** ⇒ 按一下 Tab 之后身份
    #      通常没变 ⇒ **第一轮就 break，等于没等**（rep2 的 `n_settle=1` 就是它）。
    # ⇒ v2：判据必须是「**初始化已发生**（`n_without_ti` 掉到 0 附近）
    #   **且** 身份稳定」；退出前**必须**把 `pre` 换成最后一次普查。
    n_settle = 0
    prev = pre
    for _ in range(10):
        page.keyboard.press("Tab")
        page.wait_for_timeout(SETTLE)
        n_settle += 1
        cur = ev(CENSUS_JS, [NODE_SEL])
        prev = cur
        if cur["ids"] == pre["ids"] and cur["n_without_ti"] <= 1:
            break
    pre = prev                      # ⭐ 承「不许拿陈旧读数当基线」
    rec["der_n_settle"] = n_settle
    rec["der_ready_without_ti"] = pre["n_without_ti"]
    print(f"  [就绪] 空白点={sp} 节点={pre['n_nodes']} 等稳定按了 {n_settle} 下",
          flush=True)
    dump(out)

    # ② 全表扫出**本体**可点的下标（承 943 的办法：固定挑会踩空）
    landable = []
    for i in range(pre["n_nodes"]):
        if ev(POINT_JS, [NODE_SEL, i, list(HIT_FORBIDDEN)]):
            landable.append(i)
        if len(landable) >= N_CAP + N_SELECT + N_INNER + 4:
            break
    rec["der_landable_found"] = len(landable)
    print(f"  [目标] 本体可点下标 {len(landable)} 个：{landable[:12]}…", flush=True)

    # ③ ⭐ **L 臂：增长上限** —— 连点**不同**节点，逐次记 `n_without_ti`
    series = []
    plateau_at = None
    prev_w = pre["n_without_ti"]
    for n_click, i in enumerate(landable[:N_CAP], start=1):
        pt = ev(POINT_JS, [NODE_SEL, i, list(HIT_FORBIDDEN)])
        if not pt:
            rec["arms"].append({"arm": "L", "k": n_click, "landed": False,
                                "hit_kind": "body",
                                "hit_reason": "重求可点位置失败"})
            print(f"    [L] {n_click} 跳过：重求失败（i={i}）", flush=True)
            dump(out)
            continue
        pre, row = click_and_measure(rec, "L", ("k", n_click), pre, pt, "body")
        series.append((n_click, row["post_without_ti"], row["bit"],
                       row["landed"]))
        # ⭐ 平台期：**连续 2 次咬到却不再涨**（关系式，不靠 N_CAP）
        if len(series) >= 3:
            tail = series[-3:]
            if (tail[0][2] and tail[1][2] and tail[2][2]
                    and tail[0][1] == tail[1][1] == tail[2][1]):
                plateau_at = n_click
                print(f"  ⭐ **平台期**：第 {n_click} 击之后 `不带 ti` "
                      f"连 3 次都是 {tail[2][1]}、但每次都真的咬到了"
                      f" ⇒ 涨不动了", flush=True)
                break
        if row["post_nodes"] < row["pre_nodes"]:
            print("  ⛔ 节点数减少了 ⇒ 本轮作废（有破坏性动作被点到）", flush=True)
            rec["destroyed"] = True
            break
    rec["der_L_series"] = series
    rec["der_plateau_at"] = plateau_at
    rec["der_capped"] = len(series) >= N_CAP
    rec["der_plateau_found"] = plateau_at is not None
    rec["der_landable_exhausted"] = (len(series) >= len(landable)
                                     and plateau_at is None)
    print(f"  [L 臂] 点了 {len(series)} 次；不带ti 序列="
          f"{[x[1] for x in series]}；平台期={plateau_at}；打满={rec['der_capped']}",
          flush=True)
    dump(out)

    # ④ ⭐ **补偿要几下才回到 1**：连按 N_REC 次 Tab，逐次记
    # ⚠️⚠️⚠️ v1 的这一臂**整个作废**，而且错得很典型：
    #   v1 连按 6 下 Tab，看到 `added` 恒 0、`不带 ti` 恒 14，就写下
    #   「**补偿没来**」。⚠️ 但 v1 的 `is_arm` 判据**太松** ——
    #   它只问「焦点在不在某个节点**内**」，而 `active_tag=BUTTON` 说明
    #   焦点落在节点**内部的按钮**上 ⇒ 按 §131/943 那是**死按压**
    #   （指针根本没推进）⇒ 应用当然不写回。
    #   ⭐⭐ **「应用没写回」与「这一击压根不是臂事件」必须分开** ——
    #   v1 把前者当成了后者（又一次「把『够不着』写成『没有』」）。
    # ⇒ v2：按 Tab 之前**程序化聚焦**带 `tabindex="0"` 的那个节点**本体**，
    #   并逐击记 `active_tag` ⇒ 「这一击到底是不是臂事件」有读数可查。
    _armed = ev("""([nodeSel]) => {
      const el = document.querySelector(
        nodeSel + '[tabindex="0"]') || document.querySelector(nodeSel);
      if (!el) return null;
      el.focus();
      return (document.activeElement === el);
    }""", [NODE_SEL])
    rec["comp_armed"] = _armed
    print(f"  [补偿前置] 程序化聚焦带 tabindex=0 的节点本体：成功={_armed}", flush=True)
    rec_series = []
    for k in range(1, N_REC + 1):
        page.keyboard.press("Tab")
        page.wait_for_timeout(SETTLE)
        cur = ev(CENSUS_JS, [NODE_SEL])
        d = delta(pre, cur)
        # ⚠️⚠️ 第一版只记「`added` 恒 0」就写下「补偿没来」——
        #   可 `bit=False` 有**两种**完全不同的成因：
        #   ① 焦点**根本不在画布里** ⇒ 这一击**压根不是臂事件**
        #   ② 它**是**臂事件、但应用**确实没写回**
        #   ⭐ 两件事同时出现时**不许只归因到其中一件**（930 的纪律）。
        #   ⇒ 每一击都记焦点在不在节点内，分开统计。
        f = ev(FOCUS_JS, [NODE_SEL])
        # ⭐ 判「是不是臂事件」要比 943/§131 更严：**焦点必须在节点本体上**
        #   （`active_tag == "DIV"`），落在节点**内部的按钮**上是**死按压**。
        is_arm = bool(f["focus_in_node"]) and f["active_tag"] == "DIV"
        rec_series.append({"k": k, "n_without_ti": cur["n_without_ti"],
                           "bit": d["bit"], "is_arm": is_arm,
                           "active_tag": f["active_tag"],
                           "focus_in_node": f["focus_in_node"],
                           "n_added": len(d["added"]),
                           "n_removed": len(d["removed"]),
                           "identity_stable": d["identity_stable"]})
        print(f"    [补偿] 第 {k} 下 Tab：added {len(d['added'])} 个、"
              f"removed {len(d['removed'])} 个、"
              f"不带ti {pre['n_without_ti']}→{cur['n_without_ti']}", flush=True)
        pre = cur
        dump(out)
    rec["der_comp_series"] = rec_series

    # ⑤ ⭐ **S 臂：选中态** —— ① **重新 boot**（940：状态会被上一段带跑，
    #    而「第一次点」必须落在**没被选中过**的节点上）
    #    v1 的 S 臂在 L 臂之后跑 ⇒ 那些节点**早就被选中过** ⇒
    #    「第一次点」也是 `bit=False` ⇒ 分不清「点已选中不咬」与
    #    「点已选中**之前**就该咬」⇒ **整臂无效**。
    print("  [S 臂] 重新 boot 以清掉选中态", flush=True)
    boot()
    page.wait_for_timeout(1500)
    pre = ev(CENSUS_JS, [NODE_SEL])
    # 走到「已初始化 + 指针稳定」，好让第一次点击真的是一次臂事件
    for _ in range(10):
        page.keyboard.press("Tab")
        page.wait_for_timeout(SETTLE)
        cur = ev(CENSUS_JS, [NODE_SEL])
        pre = cur
        if cur["n_without_ti"] <= 1:
            break
    sel_pair = []
    # ⚠️ 第一版写 `landable[N_CAP:N_CAP+N_SELECT] or landable[-2:]` ——
    #   `landable` 只有 15/17 个、而 `N_CAP=30` ⇒ 切片**恒空** ⇒ 静默回退到
    #   末尾两个（都被别的节点压住）⇒ `sel_ok` 一直 False。**越界回退把
    #   「没测到」写成了「测了没反应」**。
    # ⇒ v2：从**开头**取（它们已经被 L 臂点过，正好构成「已选中」的前置态）
    _sel_cand = landable[:N_SELECT]      # 重新 boot 之后全都是「未选中」
    for i in _sel_cand:
        pt = ev(POINT_JS, [NODE_SEL, i, list(HIT_FORBIDDEN)])
        if not pt:
            continue
        pre, row1 = click_and_measure(rec, "S_first", ("k", i), pre, pt, "body")
        pt2 = ev(POINT_JS, [NODE_SEL, i, list(HIT_FORBIDDEN)])
        if not pt2:
            continue
        pre, row2 = click_and_measure(rec, "S_again", ("k", i), pre, pt2, "body")
        sel_pair.append({"i": i, "first": row1["bit"], "again": row2["bit"],
                         "again_removed": row2["removed"],
                         "again_added": row2["added"],
                         "again_without_ti": row2["post_without_ti"]})
        print(f"    [S] i={i} 第一次 bit={row1['bit']}、"
              f"第二次（**已选中**）bit={row2['bit']} "
              f"removed={row2['removed']}", flush=True)
    rec["der_sel_pair"] = sel_pair

    # ⑥ **I 臂：内部后代**（非交互：PATH / SPAN / DIV）
    inner_hits = 0
    for i in landable[:N_INNER * 3]:
        if inner_hits >= N_INNER:
            break
        pt = ev(INNER_POINT_JS, [NODE_SEL, i, ["PATH", "SPAN", "DIV", "SVG", "G"]])
        if not pt:
            continue
        pre, row = click_and_measure(rec, "I", ("k", i), pre, pt, "inner")
        if row["landed"]:
            inner_hits += 1
    rec["der_n_inner_landed"] = inner_hits

    # ⑦ ⭐⭐ **B 臂放最后**（不可逆）：节点**内部 BUTTON**
    #    ⚠️ 这条纪律第一版只写在散文里、**没落成机器可查的标记**，
    #       于是 verifier 的 FFFF.2 钉它时红了 —— 「钉在注释里的纪律」
    #       和 942 的 AA.3 是同一个病。⇒ 现在它是个**读数里的显式字段**。
    rec["internal_button_is_last"] = True
    rec["internal_button_last_note"] = (
        "B 臂是整个序列的**最后一击**（前六段 L/补偿/S/I 全部跑完之后才点）；"
        "理由：它是**不可逆**动作（会开层、可能改内容），"
        "放最后 ⇒ 它不会把前面任何一段的读数带跑。")
    btn = None
    for i in range(pre["n_nodes"]):
        cand = ev("""([nodeSel, i]) => {
          const el = document.querySelectorAll(nodeSel)[i];
          if (!el) return null;
          const r = el.getBoundingClientRect();
          const f = [0.5, 0.3, 0.7, 0.15, 0.85];
          const seen = new Set();
          for (const y0 of f) {
            for (const x0 of f) {
              const x = Math.round(r.left + r.width * x0);
              const y = Math.round(r.top + r.height * y0);
              if (x < 0 || y < 0) continue;
              const at = document.elementFromPoint(x, y);
              if (!at || at === el || !el.contains(at)) continue;
              if ((at.tagName || '').toUpperCase() !== 'BUTTON') continue;
              const al = at.getAttribute('aria-label')
                || (at.innerText || '').slice(0, 30);
              const key = al;
              if (seen.has(key)) continue;
              seen.add(key);
              return [x, y, 'BUTTON', al];
            }
          }
          return null;
        }""", [NODE_SEL, i])
        if cand:
            btn = (i, cand)
            break
    if btn:
        i, pt = btn
        rec["button_target"] = {"i": i, "al": pt[3], "point": pt[:2]}
        pre_layers = ev(LAYERS_JS)
        pre, row = click_and_measure(rec, "B", ("k", i), pre, pt, "button")
        post_layers = ev(LAYERS_JS)
        rec["button_layers"] = {"before": pre_layers, "after": post_layers,
                                "opened": post_layers - pre_layers}
        print(f"    [B] 内部 BUTTON al={pt[3]!r}：层 {pre_layers}→{post_layers}、"
              f"节点 {row['pre_nodes']}→{row['post_nodes']}", flush=True)
    else:
        rec["button_target"] = None
        print("    [B] 没找到可点的内部 BUTTON", flush=True)
    dump(out)

    # ── 派生量（**只判 setup，不判机制**）─────────────────────────────
    rows = [a for a in rec["arms"] if "bit" in a]
    rec["der_n_landed"] = sum(1 for a in rows if a["landed"])
    rec["der_n_bit"] = sum(1 for a in rows if a["bit"])
    rec["der_identity_stable"] = bool(rows) and all(
        a["identity_stable"] for a in rows)
    sel_ok = bool(sel_pair) and all(p["first"] and p["again"] for p in sel_pair)
    rec["der_sel_ok"] = sel_ok
    destroyed = any(a.get("post_nodes") is not None
                    and a.get("pre_nodes") is not None
                    and a["post_nodes"] < a["pre_nodes"] for a in rows)
    rec["der_no_destroy"] = not destroyed and not rec.get("destroyed")
    rec["der_design_ok"] = {
        "init_ok": n_settle >= 1,
        "landed_ok": rec["der_n_landed"] >= 4,
        # ⚠️ 「可点下标耗尽」是**第三个诚实的终止态**：这一版画布节点大量重叠，
        #   全表只有 15–17 个点得到、点完就没了 ⇒ 这是**测量的边界**，
        #   不是「没测到」。漏掉它 ⇒ 门永远红 ⇒ 下一个人会以为探针坏了。
        "plateau_or_cap_ok": bool(rec["der_plateau_found"]
                                  or rec["der_capped"]
                                  or rec.get("der_landable_exhausted")),
        "sel_ok": sel_ok,
        "inner_ok": rec["der_n_inner_landed"] >= 2,
        "no_destroy_ok": rec["der_no_destroy"],
        "identity_ok": rec["der_identity_stable"],
    }
    print(f"  [设计门] {rec['der_design_ok']}", flush=True)
    print(f"  [汇总] 咬到 {rec['der_n_bit']}/{len(rows)}、"
          f"补偿序列 {[(x['k'], x['n_without_ti']) for x in rec_series]}",
          flush=True)
    dump(out)

print("\n读数已写入", OUT, flush=True)

#!/usr/bin/env python3
r"""batch 943 源站探针（**纯诊断**）：**鼠标臂**（点节点）与**键盘臂**（Tab 游走）
写的 `tabindex` 规则 —— **是不是同一条**？

## 943 的由来：先更正 942 留下的一个前提错误

942 的待办把 §131 记成「**指针臂**」、把 940 记成「**键盘臂**」，
并说「两者的**关系**未测」。⚠️⚠️ **这个前提本身是错的**：

- §131（批 921）的臂事件用的是 **`page.keyboard.press("Tab")`**（只有起手那一下
  `page.mouse.click(sp[0], sp[1])` 是点画布空白）；
- §136（923/926）的「臂事件流」也是按 `Tab` / `Shift+Tab`。

⇒ **§131 与 940 测的是同一条键盘臂**，「两臂关系未测」这个说法**立不住**。
⇒ ⭐ **真正从来没测过的**是**鼠标臂**：**点某个节点**会不会也写 `tabindex`、
写的话**是不是同一套三动作**。这才是 943 的题。

## 三条已知的键盘臂事实（作为**对照**，不当结论）

| 来源 | 读数 |
| --- | --- |
| §131（921） | 每次臂事件恰好三件事：`removed`＝上一个臂事件、`added`＝上上个、`changed`＝本次 |
| §131 | 不变式：**任何时刻恰好 1 个本体没有 `tabindex` 属性** |
| §136（923） | `removed` **不分方向**（正反向是同一条全局流） |
| §940 | 被标记元素 `unchanged` 26/26 ⇒ **应用只动画布**，侧栏那些不动 |

⇒ **本批不预设**鼠标臂是「同一条规则」还是「另一条」：**同一条** / **另一条** /
**根本不写** 三种都留在读数里，由读数分开。

## ⭐ 为什么必须在**交替**时才能验

键盘臂的规则里有 `removed` / `added` 这种**需要历史**的动作。
「两臂同一条」这件事，只有让两臂**先后交替**才验得出来 ——
各测各的臂再比对结论，是「两个答案来自两个不同集合」的弱形式
（940 的纪律：同向变化的两个集合不构成对照）。

## ⚠️⚠️⚠️ 前两版整跑作废，三条理由都留在这（承 876 的做法：作废也要留痕）

**v1**：设计门**自己把这一版否了**。
- `landed_ok = False` —— 6 个目标节点里只有 **1** 个的矩形中心落点算数
  ⇒ 设计的 5 次点击里 4 次**根本没点到目标**；
- **键盘臂 6 次 Tab 的 delta 全空** ⇒ **焦点压根没进画布**，
  那一版的键盘臂读数**什么也没测到**。
- 另有两处实现错：① 空白点用**算出来的**矩形点（落点可能是节点/子元素），
  换成 **921 的 `BLANK_JS` 候选列表**、点击后等 **900ms**；
  ② 直接取节点**矩形中心**当点击点 ⇒ 新增 `POINT_JS` **在节点矩形内搜网格**。
- 还有两处工具错：③ 计费守卫写成「页面上**有没有**计费入口」⇒ **第一击就炸**
  （那个入口本来常驻；939/940 都记过它可达、只是从不点）
  ⇒ ⭐ **「页面上有没有 X」的守卫 = 恒为真的守卫 = 没有守卫**；
  ④ JS 写成 `(a, b) => …` 而实参传 list ⇒ Playwright 把 list 当**一个**参数，
  `querySelectorAll([…])` 把数组 **`toString()`** 成四不像选择器；
  改成解构 `([a, b]) => …` 之后又忘了实参要传 **list** ——
  传裸字符串时解构取的是**首字符**（`.`）。

**v2**：设计门**又把自己否了**，但**键盘臂读数逐字复现了 §131（2/2）**，留下真信息。
- `landed_ok = False`（还是 1/6）⇒ 这一版画布节点**大量重叠**，
  后面的节点把前面的**整个压住** ⇒ **固定挑 6 个分散下标**这个设计本身不成立
  ⇒ v3 改成**扫全表**、把落点算数的下标按顺序收下；
- `identity_ok = False` —— ⭐ **根因的指纹非常干净**：
  键盘臂 `identity_stable` **16/16 为真**，**唯独鼠标臂那一击为假**
  ⇒ 是**点击**改了节点的身份串。v2 的身份串带了 `className`，
  而**点节点会加 `selected` 类** ⇒ 尺子恰好在**最有意思的那一下**坏掉。
  ⇒ v3 身份串去掉 `className`（它**设计上就是可变的**）、
  加 `innerText` 前 24 字，并**另存** `className` 表；
- ⚠️ 而 v2 的 `delta()` 在身份对不上时**静默返回空列表**
  ⇒ 那正是「把『没测到』写成了『没有』」⇒ v3 **不许静默丢弃**：
  身份对不上就把**哪些下标变了、变成什么、className 前后如何**原样记进读数。

## ⭐ 尺子要先自证（承 942 的阳性对照纪律）

身份函数是本批的**尺子** ⇒ 用前必须先证明它**量的是不变的东西**：

1. **无交互双读必须相同**；
2. **一次 `Tab` 之后必须仍然相同**。

⇒ 这两下是 v2 缺的；v2 的尺子坏了一整批**没人知道**，直到门自己报了出来。
⇒ `ident_selfcheck_ok` 是**设计门之一**，不是可选诊断。

## 设计门（`design_ok`，每轮判一次，**只判 setup、不判机制**）

1. `blank_ok` —— 空白点**找得到**
2. `landed_ok` —— 至少 **3** 次点击**真的落在目标节点体内**
3. `n_bit_kbd_ok` —— 键盘臂里**至少 3 次真的产生了 delta**（⚠️ 不是「按了 3 次」）
4. `n_bit_mouse_ok` —— 鼠标臂里**至少 2 次**能判读（落点算数即可；
   ⚠️ 「产生 delta」**不是**它的设计门 —— 若鼠标臂真的不写 `tabindex`，
   那就是**结论**，不能因为「没变化」把这一版作废）
5. `identity_ok` —— 每一对被判决的普查**身份逐位相同**
6. `ident_selfcheck_ok` —— 上面那两道尺子自证

## 判据纪律

- **纯诊断**：普查**纯读**，**不劫持 `prototype`、不装 `MutationObserver`**
- 每轮之间**重新 goto** 重置（AI 侧栏 Esc 关不掉，940 撞过）
- **重复 2 轮**（一次成功不叫可靠）
- **落盘排在所有后处理之前**（935：后处理崩了整轮读数全丢）
- **派生键不许与原始键重叠**（935 的 `KeyError` 免疫针）
- ⚠️ **不许用切片去改文件**：`s[a:b]` 在 `a > b` 时是**空串**，
  而 `str.replace("", X)` 会把 `X` 插到**每个字符之间** ——
  v3 之前的修补脚本就是这么把本文件撑到 **29 万行**、当场废掉的
  （902 同族教训：改既有文件别凭猜的边界切片）

## 计费边界

点**节点本体**（不是生成/发送/购买/充值），其余只按 `Tab`。
⛔ 守卫拦在 `mouse.click` **之前**，契约是「**我正要点的这个元素**是什么」。
**本批零计费动作。**

跑法：
  ~/.venvs/liblib-harness/bin/python -u scripts/jimeng_headless.py run \
      scripts/jimeng_probe943_arm_relation_src.py
"""

import json

OUT = "/tmp/b943-src-arm-relation.json"
REPS = 2

SETTLE = 350
BLANK_WAIT = 900         # 承 921：点空白之后等 900ms
N_MOUSE = 6               # 鼠标臂**目标**点击次数（落点算数的）
KBD_AFTER = 8             # 键盘臂步数
N_SETTLE = 8             # 等身份稳定，最多按几下

# ⛔ 计费入口（承 937/939/940）
FORBIDDEN_TIDS = ("canvas-commerce-entry", "canvas-pay-trigger",
                  "canvas-recharge")
BILLED_EXACT = ("生成", "发送", "购买", "充值", "立即支付", "开通", "订阅", "兑换")

NODE_SEL = ".react-flow__node"
HIT_FORBIDDEN = ("BUTTON", "INPUT", "A", "SELECT", "TEXTAREA", "LABEL", "OPTION")

RAW_KEYS = frozenset({
    "n_nodes", "n_with_ti", "n_without_ti", "ids", "cls", "ti", "n_diff",
    "removed", "added", "changed", "hit_ok", "hit_tag", "hit_reason",
    "point", "i", "k", "phase", "arm", "landed", "bit",
    "active_tag", "active_tid", "focus_in_node", "blank",
    "diff_ids", "diff_detail",
})
DERIVED_KEYS = frozenset({
    "n_mouse", "n_kbd", "n_landed", "n_bit_kbd", "n_bit_mouse",
    "identity_stable", "design_ok", "n_blank", "landable_found",
    "ident_selfcheck", "n_settle",
})
assert not (RAW_KEYS & DERIVED_KEYS), "派生键与原始读数键重叠了（935 的 KeyError 免疫针）"
for _must in ("design_ok", "n_bit_kbd", "identity_stable", "ident_selfcheck"):
    assert _must in DERIVED_KEYS, f"{_must} 必须是派生量"

# ── JS：空白点（承 921 **逐字**）────────────────────────────────────
BLANK_JS = """() => {
  for (const [x, y] of [[1300, 1000], [1360, 920], [1220, 1080],
                        [1400, 840], [400, 1080]]) {
    const t = document.elementFromPoint(x, y);
    if (t && t.closest('.react-flow__pane')
        && !t.closest('.react-flow__node')) return [x, y];
  }
  return null;
}"""

# ── JS：在节点矩形内**搜**一个真能点到本节点的点 ──────────────────────
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

# ── JS：普查（**纯读**）。⚠️ 身份串**不含 className** ────────────────
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

# ── JS：焦点在哪（「我没检测到」之前先确认「我够得着」）──────────────
FOCUS_JS = """([nodeSel]) => {
  const a = document.activeElement;
  if (!a) return {active_tag: null, active_tid: null, focus_in_node: false};
  const host = a.closest('[data-testid]');
  const node = a.closest(nodeSel);
  return {active_tag: (a.tagName || '').toUpperCase(),
          active_tid: host ? host.getAttribute('data-testid') : null,
          focus_in_node: !!node};
}"""


# ⚠️ §131 禁的是**切节点数组**（「切片会把规律读反」），
#    **不是**禁一切 `slice(` —— 身份串把 `innerText` 截到 24 字是合法的。
#    ⚠️ 第一版的门写成「不许出现 `slice(`」，**当场把自己判红了**
#    ⇒ 一个太钝的门会逼着人去绕过它（把 `slice` 改写成 `substring`），
#    那比钝门更坏：门还在，测的东西已经悄悄变了。
#    ⇒ 这里改成**精确规则**：普查里每一处 `slice(` 都必须**只**是
#    「截字符串到 24 字」那一种形态，而节点数组上的切片**一定不匹配**它。
SLICE_STR = "|| '').slice(0, "


def _no_node_slice(name, js):
    n_all, n_str = js.count("slice("), js.count(SLICE_STR)
    assert n_all == n_str, (
        f"{name} 里有 {n_all - n_str} 处**非字符串**切片"
        f"（§131：切片会把规律读反）")


_no_node_slice("POINT_JS", POINT_JS)
_no_node_slice("CENSUS_JS", CENSUS_JS)
_no_node_slice("FOCUS_JS", FOCUS_JS)


def ev(js, arg=None):
    return page.evaluate(js, arg) if arg is not None else page.evaluate(js)


def dump(out):
    """⚠️ 落盘必须排在**所有**后处理之前（935：后处理崩了整轮读数全丢）。"""
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)


def guard(al, tid):
    """⛔ 计费守卫：契约是「**我正要点的这个元素**是什么」。

    ⚠️ v1 写成「页面上**有没有**计费入口」⇒ **第一击就炸**
    （那个入口本来常驻，939/940 都记过它可达、只是从不点）。
    ⭐ 「页面上有没有 X」的守卫 = 恒为真的守卫 = 没有守卫。"""
    if tid in FORBIDDEN_TIDS:
        raise AssertionError(f"拒绝点击计费入口 testid={tid!r}")
    t = (al or "").strip()
    if t in BILLED_EXACT or t.split(":")[0].strip() in BILLED_EXACT:
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
    """逐**身份**对齐的两张表之差。

    ⚠️⚠️ v2 栽在这里：身份串里带了 `className`，而**点节点会加 `selected` 类**
    ⇒ 鼠标臂每一次点击的身份都变 ⇒ v2 的鼠标臂读数**一条都没测到**
    （键盘臂 16/16 为真、**唯独点击那一击为假** ⇒ 这就是根因的指纹）。

    ⭐ **不许静默丢弃**：身份对不上时把「哪些下标变了、变成什么、
    它们的 className 前后如何」**原样记进读数** ——
    「解析不出来 ≠ 解析错了」，静默变成空列表就是把「没测到」写成了「没有」。"""
    a, b = pre["ids"], post["ids"]
    if a != b:
        diff = sorted({int(k) for k in set(a) | set(b)
                       if a.get(k) != b.get(k)})
        return {"identity_stable": False, "removed": [], "added": [],
                "changed": [], "n_without_ti": post["n_without_ti"],
                "bit": False, "diff_ids": diff,
                "diff_detail": [{"i": i, "before": a.get(str(i)),
                                 "after": b.get(str(i)),
                                 "cls_before": pre["cls"].get(str(i)),
                                 "cls_after": post["cls"].get(str(i))}
                                for i in diff[:8]]}
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

out = {"node_sel": NODE_SEL, "reps": REPS, "n_mouse": N_MOUSE,
       "kbd_after": KBD_AFTER, "forbidden_tids": list(FORBIDDEN_TIDS),
       "void_runs": [
           "v1：设计门自否（落点 1/6、键盘臂 delta 全空＝焦点没进画布）",
           "v2：设计门自否（还是落点 1/6；identity 16/16 唯独点击那一击为假"
           " ⇒ 身份串带 className 而点击会加 selected）",
       ],
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


def step_row(rec, arm, phase, key, pre, post, d, f=None):
    row = {"arm": arm, "phase": phase, key[0]: key[1],
           "removed": d["removed"], "added": d["added"],
           "changed": d["changed"], "bit": d["bit"],
           "identity_stable": d["identity_stable"],
           "diff_ids": d["diff_ids"],
           "pre_without_ti": pre["n_without_ti"],
           "post_without_ti": post["n_without_ti"]}
    if d["diff_ids"]:
        row["diff_detail"] = d["diff_detail"]
    if f:
        row.update({"active_tag": f["active_tag"],
                    "active_tid": f["active_tid"],
                    "focus_in_node": f["focus_in_node"]})
    rec["arms"].append(row)
    tail = (f" 焦点={f['active_tag']}" if f else "")
    if f and f["focus_in_node"]:
        tail += "/在节点内"
    print(f"    [{arm}/{phase}] {key[1]}{tail} "
          f"removed={d['removed']} added={d['added']} changed={d['changed']} "
          f"不带ti {pre['n_without_ti']}→{post['n_without_ti']}"
          + (f"  ⚠️身份变了 {d['diff_ids']}" if d["diff_ids"] else ""),
          flush=True)


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

    # ① 进画布：921 的空白点候选列表
    sp = ev(BLANK_JS)
    rec["blank"] = sp
    if sp:
        guard_point(sp[0], sp[1])
        page.mouse.click(sp[0], sp[1])
        page.wait_for_timeout(BLANK_WAIT)
    rec["focus_after_blank"] = ev(FOCUS_JS, [NODE_SEL])
    pre0 = ev(CENSUS_JS, [NODE_SEL])
    rec["clean"] = {"n_nodes": pre0["n_nodes"], "n_with_ti": pre0["n_with_ti"],
                    "n_without_ti": pre0["n_without_ti"]}
    print(f"  [干净态] 空白点={sp} 节点={pre0['n_nodes']} "
          f"带ti={pre0['n_with_ti']} 不带ti={pre0['n_without_ti']} "
          f"焦点={rec['focus_after_blank']['active_tag']}", flush=True)
    dump(out)

    # ② ⭐ **尺子先自证**（v2 缺这一步，尺子坏了一整批没人知道）
    ident_a = ev(CENSUS_JS, [NODE_SEL])
    ident_b = ev(CENSUS_JS, [NODE_SEL])
    self_noop = (ident_a["ids"] == ident_b["ids"]
                 and ident_a["n_nodes"] == ident_b["n_nodes"])
    page.keyboard.press("Tab")
    page.wait_for_timeout(SETTLE)
    ident_c = ev(CENSUS_JS, [NODE_SEL])
    # ⚠️ v3 实测：这一击之后**24 个下标的身份变了**（`innerText` 从空变有值 ——
    #   应用给全部节点写上 `tabindex`、节点变为可聚焦、React 重排内层）
    #   ⇒ **初始化那一击必须隔离**，不许拿它去判「两臂同一条」；
    #   而且它**恰好是唯一一次非死按压**，所以尺子自证不能拿它做。
    self_tab = (ident_a["ids"] == ident_c["ids"])
    rec["init_press"] = {
        "n_with_ti": ident_c["n_with_ti"],
        "n_without_ti": ident_c["n_without_ti"],
        "identity_stable": self_tab,
        "diff_ids": sorted({int(k) for k in set(ident_a["ids"]) | set(ident_c["ids"])
                            if ident_a["ids"].get(k) != ident_c["ids"].get(k)}),
    }
    rec["der_ident_selfcheck"] = {"noop_read_stable": self_noop}
    print(f"  [尺子自证] 无交互双读={self_noop}｜"
          f"初始化那一击身份变了 {len(rec['init_press']['diff_ids'])} 个下标"
          f"（**已隔离**，不参与判决）", flush=True)
    dump(out)
    # ⚠️ v4 实测：初始化那一击之后，身份**还要再过 2 次臂事件**才稳定
    #   （v4 的 K1/K2 仍报「身份变了」，K3 起干净；两次跑的步数**一致**）
    #   ⇒ ⭐ **尺子要等它稳定下来再用**，而且「等了几下」本身是**读数**
    #   （不是把它藏起来，也不是假装它一开始就稳）。
    n_settle = 0
    prev = ident_c
    for k in range(N_SETTLE):
        page.keyboard.press("Tab")
        page.wait_for_timeout(SETTLE)
        cur = ev(CENSUS_JS, [NODE_SEL])
        n_settle += 1
        # ⚠️⚠️ 第一版这里写成「先 `prev = cur`、再比 `cur == prev`」
        #   ⇒ **永远相等** ⇒ 每轮都在第 1 下就 break，等于**没等**
        #   （又一个恒真的条件。v4 的 `identity_ok` 之所以一直红就是这么来的）
        stable = (cur["ids"] == prev["ids"])
        n_diff = len({int(i) for i in set(cur["ids"]) | set(prev["ids"])
                      if cur["ids"].get(i) != prev["ids"].get(i)})
        rec.setdefault("settle", []).append(
            {"k": n_settle, "identity_stable": stable, "n_diff": n_diff})
        print(f"    [等稳] 第 {n_settle} 下：身份"
              f"{'已稳' if stable else f'仍在变（{n_diff} 个下标）'}", flush=True)
        prev = cur
        if stable:
            break
    rec["der_n_settle"] = n_settle

    # ③ **键盘臂**（从「身份已稳」开始）
    for k in range(KBD_AFTER):
        page.keyboard.press("Tab")
        page.wait_for_timeout(SETTLE)
        cur = ev(CENSUS_JS, [NODE_SEL])
        d = delta(prev, cur)
        f = ev(FOCUS_JS, [NODE_SEL])
        step_row(rec, "kbd", "K", ("k", k + 1), prev, cur, d, f)
        prev = cur
        dump(out)

    # ④ **鼠标臂**：⚠️ **扫全表**取落点算数的下标（v1/v2 按固定分散下标挑，
    #    而这版画布节点大量重叠 ⇒ 6 个里只有 1 个点得到）
    n_nodes = prev["n_nodes"]
    landable = []
    for i in range(n_nodes):
        pt = ev(POINT_JS, [NODE_SEL, i, list(HIT_FORBIDDEN)])
        if pt:
            landable.append(i)
        if len(landable) >= N_MOUSE * 3:
            break
    step = max(1, len(landable) // N_MOUSE) if landable else 1
    cand = [landable[k * step] for k in range(min(N_MOUSE, len(landable)))] \
        if landable else []
    rec["der_landable_found"] = len(landable)
    print(f"  [目标] 全表扫出 {len(landable)} 个可点下标 → 取 {cand}", flush=True)
    for i in cand:
        # ⚠️ v3 崩在这里：扫表之后布局**又变了**，`POINT_JS` 返回 None
        #   ⇒ 点之前必须**重求**，为 None 就**跳过并记录**，不许崩
        #   （崩掉 = 整轮读数全丢，935 同款：后处理不许崩在判决之前）
        pt = ev(POINT_JS, [NODE_SEL, i, list(HIT_FORBIDDEN)])
        if not pt:
            rec["arms"].append({"arm": "mouse", "phase": "M", "i": i,
                                "landed": False, "bit": False,
                                "hit_reason": "重求可点位置失败（布局已变）"})
            print(f"    [M] i={i} 跳过：重求可点位置失败", flush=True)
            dump(out)
            continue
        pre = ev(CENSUS_JS, [NODE_SEL])
        guard_point(pt[0], pt[1])
        page.mouse.click(pt[0], pt[1])
        page.wait_for_timeout(SETTLE)
        post = ev(CENSUS_JS, [NODE_SEL])
        d = delta(pre, post)
        f = ev(FOCUS_JS, [NODE_SEL])
        # ⚠️⭐ **点后**再判 landed：v3 的 `[M] i=4` 点前体检说「可点」，
        #   点后焦点却**不在节点内** ⇒ 那一击根本没咬到、delta 也确实全空。
        #   ⇒ 只信点前的 `elementFromPoint` 体检是不够的
        #   （承「我没检测到，必须先确认我够得着」：够不着要在**动作之后**看）。
        landed = bool(f["focus_in_node"])
        row = {"arm": "mouse", "phase": "M", "i": i, "landed": landed,
               "point": pt[:2], "hit_tag": pt[2], "bit": d["bit"],
               "removed": d["removed"], "added": d["added"],
               "changed": d["changed"],
               "identity_stable": d["identity_stable"],
               "diff_ids": d["diff_ids"],
               "pre_without_ti": pre["n_without_ti"],
               "post_without_ti": post["n_without_ti"],
               "active_tag": f["active_tag"],
               "active_tid": f["active_tid"],
               "focus_in_node": f["focus_in_node"]}
        if d["diff_ids"]:
            row["diff_detail"] = d["diff_detail"]
        rec["arms"].append(row)
        print(f"    [M] i={i} 落点={pt[2]} 焦点={f['active_tag']}"
              f"{'/在节点内' if f['focus_in_node'] else ''} "
              f"removed={d['removed']} added={d['added']} "
              f"changed={d['changed']} 不带ti {pre['n_without_ti']}"
              f"→{post['n_without_ti']}"
              + ("" if landed else "  ⚠️**没咬到**（点后焦点不在节点内）")
              + (f"  ⚠️身份变了 {d['diff_ids']}" if d["diff_ids"] else ""),
              flush=True)
        dump(out)

    # ⑤ **反向交叉**：鼠标臂之后再接键盘臂 ⇒ 窗口认不认鼠标臂的写入
    prev = ev(CENSUS_JS, [NODE_SEL])
    for k in range(KBD_AFTER):
        page.keyboard.press("Tab")
        page.wait_for_timeout(SETTLE)
        cur = ev(CENSUS_JS, [NODE_SEL])
        d = delta(prev, cur)
        step_row(rec, "kbd", "K_after_M", ("k", k + 1), prev, cur, d)
        prev = cur
        dump(out)

    # ── 派生量（**只判 setup，不判机制**）─────────────────────────────
    kbd = [a for a in rec["arms"] if a.get("arm") == "kbd"]
    ml = [a for a in rec["arms"] if a.get("arm") == "mouse" and a.get("landed")]
    pairs = [a for a in rec["arms"] if "identity_stable" in a]
    # ⚠️ 身份不稳定的步**如实记进读数、但不算「不一致」** ——
    #   「解析不出来 ≠ 解析错了」（v3 的 K1/K2 就是初始化那一击的重排）
    rec["der_n_blank"] = 1 if sp else 0
    rec["der_n_landed"] = len(ml)
    rec["der_n_mouse"] = len(ml)
    rec["der_n_kbd"] = len(kbd)
    rec["der_n_bit_kbd"] = sum(1 for a in kbd if a.get("bit"))
    rec["der_n_bit_mouse"] = sum(1 for a in ml if a.get("bit"))
    rec["der_identity_stable"] = bool(pairs) and all(
        a["identity_stable"] for a in pairs)
    rec["der_design_ok"] = {
        "blank_ok": rec["der_n_blank"] == 1,
        "landed_ok": rec["der_n_landed"] >= 3,
        "n_bit_kbd_ok": rec["der_n_bit_kbd"] >= 3,
        "n_bit_mouse_ok": rec["der_n_bit_mouse"] >= 2,
        "identity_ok": rec["der_identity_stable"],
        "ident_selfcheck_ok": bool(self_noop),
    }
    print(f"  [设计门] {rec['der_design_ok']}  "
          f"(落点 {rec['der_n_landed']}/{rec['der_n_mouse']} "
          f"键盘咬到 {rec['der_n_bit_kbd']}/{rec['der_n_kbd']} "
          f"鼠标咬到 {rec['der_n_bit_mouse']})", flush=True)
    dump(out)

print("\n读数已写入", OUT, flush=True)

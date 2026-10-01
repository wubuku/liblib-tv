#!/usr/bin/env python3
"""batch 850 源站探针：生成面板那 **4 个下拉**的键盘行为。

849 把复刻侧的键盘覆盖面从 12 层补到 21 层，新增的 9 层全部记进
`kb_not_sampled` —— **测了，但不下结论**，因为源站基线表里没有它们。
848 的范围限制写得更直接：「源站那 4 个生成面板下拉**从未被鼠标打开过**
（只 dump 了工具条按钮）」。

而 848 同时 dump 到了这四个触发器的**文案**：

    选择模型: 即梦 Seedance 2.0 VIP
    视频尺寸选项: 16:9 · 720P · 1
    生成模式: 全能参考
    选择视频生成时长: 4s

所以它们在源站**是能打开的**，848 只是没点。这一轮去点，并把三个维度一次问全
（口径与 846/847 一致：真按键盘，读 `activeElement`）：

  ① **开层是否接管焦点** —— blur 之前先读
  ② **Tab 是否困在层内** —— 焦点进层后连按 Tab，看第几次跑出去
  ③ **方向键是否在层内移动** —— ArrowDown / ArrowUp，焦点动不动
  ④ **Esc 关层后焦点回哪**

⚠️ 认层必须**兜底**：848 只 dump 了工具条，**没打开过**这些下拉，所以
**不知道它们有没有 testid**。按 847 定的办法：testid 认不出就用**矩形差分**
（点触发器前后各取一份「不在画布壳里、带可聚焦项」的元素集合，取新增）。

⚠️ 触发器匹配必须用 `^=`（前缀）而不是等值 —— 实际 aria-label 带后缀
（「选择模型: 即梦 Seedance 2.0 VIP」）。849 在复刻侧就是在这上面栽了一层。

⚠️ **每个测量都从重开的层起手**（846 教训：串着跑多个破坏性测量，
只有第一个是准的）。

⚠️ 计费边界：只点下拉触发器开菜单，**绝不点 `生成`**（消耗积分）。
BILLED 护栏在下方 `guard()` 里把付费文案显式排掉。
"""

import json

MAX_TABS = 12
MAX_KEYS = 4

# ⚠️⚠️ 视口从 1512×950 抬到 1512×1200，**这是本批唯一的取舍**，写在这里
#    免得后面看到 README 的人以为几何也是 1200 高量出来的。
#
# 原因：源站选中视频节点后，生成面板出现在节点**下方**约 340px。节点在
# y≈648，于是「选择模型」触发器落在 y≈987 —— 950 高的视口**装不下**，
# 按钮 visible=True 但 `in_view=False`，`click` 直接 10s 超时。另外三个
# 下拉触发器连 `count` 都是 0（压根没进渲染/命中范围）。
#
# 抬视口**只影响几何**，不影响这一批要取的东西：开层是否接管焦点、Tab 困不困、
# 方向键动不动、Esc 回哪 —— 这四条与视口无关，只要元素点得到。
# 几何取样仍以 848 的 1512×950 为准，**本批的数字不进几何结论**。
page.set_viewport_size({"width": 1512, "height": 1200})

page.goto(
    "https://jimeng.jianying.com/ai-tool/ai-canvas/"
    "64b58cd5-7b04-4312-890a-09f2d1d3399f?enter_from=project_list&from_page=create",
    wait_until="domcontentloaded", timeout=90000)
page.wait_for_timeout(10000)
print("== 视口 ==", page.evaluate("() => [innerWidth, innerHeight]"))

# 付费护栏分两档，**不能一档**：
#   EXACT   —— 文案**就是**这个词，源站那个按钮确实是付费动作
#   PREFIX  —— 以这个词开头，且**整条 aria-label 都很短**，基本就是它
#
# ⚠️ 第一版只有一个 `startswith` 列表（含「生成」），结果把
#    `生成模式: 全能参考`、`选择视频生成时长: 4s` 全拦了 ——
#    **护栏太宽也是缺陷**：它让「测不到」被印成「不许测」。
#    源站的付费按钮文案就是光秃秃两个字（「生成」「发送」），
#    真要拦就按**等值**拦；带 `: …` 后缀的一律是控件描述，不是付费按钮。
# 「层还活着吗」：用**几何**探（源站这四层都没有 testid，847 定的办法）。
# ⚠️ 这一条是本批最要紧的补充：源站这些 listbox/dialog **失焦就关** ——
#    ② 按 Tab 时层被关掉，于是「焦点不在层内」有两种完全不同的成因：
#      (a) 层还在，焦点跑出去了  ⇒ 真的不困 Tab
#      (b) 层**没了**              ⇒ 伪像，拿 (a) 的口径写基线表就是错的
#    不分开，第三轮就会把「层自己关了」写成「源站不困 Tab」。
ALIVE_JS = """(lay) => {
  const lx = lay[0], ly = lay[1], lw = lay[2], lh = lay[3];
  const st = document.elementsFromPoint(lx + lw / 2, ly + lh / 2) || [];
  for (const e of st) {
    const r = e.getBoundingClientRect();
    if (r.x <= lx + 2 && r.y <= ly + 2
        && r.right >= lx + lw - 2 && r.bottom >= ly + lh - 2)
      return {alive: true,
              who: e.tagName + '/' + ((e.getAttribute('data-testid')
                    || e.getAttribute('role')
                    || (e.className || '').toString()
                         .replace(/\\s+/g, ' ').slice(0, 30)) || '')};
  }
  return {alive: false};
}"""

BILLED_EXACT = ("生成", "发送", "购买", "充值", "立即支付", "开通", "订阅", "兑换")
BILLED_PREFIX = ("立即支付", "购买会员", "充值",)


def guard(label: str) -> bool:
    """付费文案护栏：这个按钮不许点。返回 True = 拦下了。"""
    t = (label or "").strip()
    base = t.split(":")[0].strip()          # 「生成模式: 全能参考」→「生成模式」
    if t in BILLED_EXACT or base in BILLED_EXACT:
        print(f"   🛑 拦下付费动作 {t!r}（不点）")
        return True
    if any(t.startswith(b) for b in BILLED_PREFIX):
        print(f"   🛑 拦下付费动作 {t!r}（不点）")
        return True
    return False


# 读焦点：身份 + **是否落在层矩形里**。
#
# ⚠️ 这里用**矩形**判「在不在层内」，不用 testid 包含关系 ——
#    源站这一层压根**没有 testid**（实测 `role=listbox`、tid 为空、class 是
#    `animate-none transition-none absolute z-…`）。847 已经定过这条：
#    无 testid 的层用**矩形**认。硬套 testid 只会得到「永远不在层内」，
#    而那个结论会被当成「源站不接管焦点」写进基线表 ——
#    **判据量错对象，结论就整个反了**。
#    参数是扁平数组 [x, y, w, h, tid]；tid 为空时 `in_layer` 只看矩形。
FOCUS_JS = """(args) => {
  const [lx, ly, lw, lh, tid] = args;
  const a = document.activeElement;
  const inLayer = (() => {
    if (!a || a === document.body) return false;
    // 打了标记就**优先**按标记判（标记跟着元素走，不怕坐标漂）
    const marked = document.querySelector('[data-probe850]');
    if (marked) return marked.contains(a) || marked === a;
    if (tid) {
      for (const e of document.querySelectorAll(`[data-testid="${tid}"]`))
        if (e.contains(a)) return true;
    }
    if (!(lw > 0 && lh > 0)) return false;
    const r = a.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) return false;
    return r.x >= lx - 1 && r.y >= ly - 1
        && r.right <= lx + lw + 1 && r.bottom <= ly + lh + 1;
  })();
  if (!a || a === document.body)
    return {who: 'body', in_layer: false};
  return {
    who: a.tagName + '/' + ((a.getAttribute('data-testid')
          || a.getAttribute('aria-label')
          || (a.className || '').toString().replace(/\\s+/g, ' ').slice(0, 34)
          || (a.innerText || '').trim().slice(0, 14))),
    al: (a.getAttribute('aria-label') || '').trim().slice(0, 30),
    tid: a.getAttribute('data-testid') || '',
    role: a.getAttribute('role') || '',
    tabindex: a.getAttribute('tabindex'),
    txt: (a.innerText || a.getAttribute('placeholder') || '')
           .trim().replace(/\\s+/g, ' ').slice(0, 20),
    in_layer: inLayer};
}"""

# 「候选浮层」快照：不在画布壳里、带可聚焦项、够大。用于**矩形差分认层**。
SNAP_JS = """() => {
  const SHELL = '.react-flow__renderer, .react-flow__pane, '
              + '.react-flow__viewport, .react-flow__nodes, '
              + '.react-flow__node, .react-flow__node-toolbar';
  const out = [];
  for (const e of document.querySelectorAll('body *')) {
    const s = getComputedStyle(e);
    if (s.display === 'none' || s.visibility === 'hidden') continue;
    const r = e.getBoundingClientRect();
    if (r.width < 40 || r.height < 20) continue;
    if (!e.querySelector('button,[href],input,select,textarea,'
                          + '[tabindex]:not([tabindex="-1"]),'
                          + '[role=menuitem],[role=option]')) continue;
    out.push({tid: e.getAttribute('data-testid') || '',
              role: e.getAttribute('role') || '',
              al: e.getAttribute('aria-label') || '',
              cls: (e.className || '').toString().replace(/\\s+/g, ' ').slice(0, 40),
              in_shell: !!e.closest(SHELL),
              x: Math.round(r.x), y: Math.round(r.y),
              w: Math.round(r.width), h: Math.round(r.height),
              z: s.zIndex});
  }
  return out;
}"""

results = {}


def diff_layers(before, after):
    """点开之后**新增**的候选层（按矩形位置配对，取 before 里没有的）。"""
    keys = {(b["x"], b["y"], b["w"], b["h"]) for b in before}
    return [a for a in after if (a["x"], a["y"], a["w"], a["h"]) not in keys]


# 按 `role=listbox/dialog` 给层打一个临时标记（源站这四层**没有 testid**）。
# ⚠️ 认层那一刻就要打，而且**层每被关掉重开一次就得重打** —— 新建的元素
#    没有标记。第一版只在开头打了一次，③ 之前的 toggle 重开把层换成了新
#    元素，于是 refocus 报「标记不见了」——**又一次把「夹具没了」当成了
#    「层测不到」**。
MARK_JS = """(info) => {
  const FOC = 'button:not([disabled]),[tabindex]:not([tabindex="-1"]),'
            + '[role=option],[role=menuitem],input:not([disabled])';
  let best = null, area = 0;
  for (const e of document.querySelectorAll(
        '[role=listbox],[role=dialog]')) {
    if (e.hasAttribute('data-probe850')) continue;
    const st = getComputedStyle(e);
    if (st.display === 'none' || st.visibility === 'hidden') continue;
    const r = e.getBoundingClientRect();
    if (r.width < 60 || r.height < 40) continue;
    if (!e.querySelector(FOC)) continue;
    const a = r.width * r.height;
    if (a > area) { area = a; best = e; }
  }
  if (!best) return {ok: false};
  best.setAttribute('data-probe850', info.role || '1');
  const r = best.getBoundingClientRect();
  return {ok: true, role: info.role,
          rect: [Math.round(r.x), Math.round(r.y),
                 Math.round(r.width), Math.round(r.height)]};
}"""

UNMARK_JS = """() => {
  const n = document.querySelectorAll('[data-probe850]').length;
  for (const e of document.querySelectorAll('[data-probe850]'))
    e.removeAttribute('data-probe850');
  return n;
}"""


def mark_layer(layer, note=""):
    """打标记并返回新矩形。层被关掉重开过就**必须**重打。"""
    out = page.evaluate(MARK_JS, {"role": layer["role"]})
    if out.get("ok"):
        print(f"   打标记{note}: role={out.get('role')} rect={out.get('rect')}")
    else:
        print(f"   ⚠ 打标记{note}失败: {out}")
    return out


def probe(name, trig_aria, note=""):
    print("=" * 72)
    print(f"【{name}】触发器 aria-label^={trig_aria!r}  {note}")
    rec = {"name": name, "trigger_aria": trig_aria}

    trig = page.locator(f'button[aria-label^="{trig_aria}"]')
    # ⚠️ **不许**在这里按 `trig.count()` 早退：那是 Playwright 的计数，
    #    它为 0 时我们连「到底存不存在、存在的话在哪」都没量过 —— 直接跳过
    #    就变成「没找到」，而事实可能是「存在但不可点」或「在另一处渲染」。
    #    第一版就是这么把另外三个下拉写成 `count=0 ⇒ 前置态没成立」的，
    #    而那句 `count=0` 是**没查过**的同义反复。dump 本身就是那个查询。
    # ⚠️⚠️ **存在 ≠ 点得到**，而且存在的方式还会骗人。
    # 第二版先 `trig.first.evaluate(...)` 量落点，结果 30s 超时 —— 而上一行的
    # `get_attribute` **读得到** `选择模型: 即梦 Seedance 2.0 VIP, …`。
    # 两个 API 的差别：前者只要 attached，后者要 Playwright 能交出 handle。
    # ⇒ 匹配到的很可能是页面上一份**隐藏副本**（源站常按断点/路由渲染多份）。
    #
    # 所以这里**不用 locator**，直接按 CSS 在 DOM 里 dump 全部匹配，逐个量
    # 可见性/位置/在不在画布壳里，**从 dump 里挑能点的**，再用坐标点 ——
    # 848 dump 工具条时就是这么干的，区别只是这里要连着点。
    cands = page.evaluate("""(aria) => {
      const out = [];
      for (const l of document.querySelectorAll(`button[aria-label^="${aria}"]`)) {
        const s = getComputedStyle(l);
        const r = l.getBoundingClientRect();
        const x = r.x + r.width / 2, y = r.y + r.height / 2;
        const st = document.elementsFromPoint(x, y) || [];
        const top = st[0] || null;
        out.push({
          al: l.getAttribute('aria-label') || '',
          visible: s.display !== 'none' && s.visibility !== 'hidden'
                   && parseFloat(s.opacity || '1') > 0,
          rect: [Math.round(r.x), Math.round(r.y),
                 Math.round(r.width), Math.round(r.height)],
          in_view: r.width > 0 && r.height > 0
                   && x >= 0 && y >= 0
                   && x <= innerWidth && y <= innerHeight,
          in_shell: !!(l.closest('.react-flow__node, .react-flow__node-toolbar')),
          self_is_top: !!(top && (top === l || l.contains(top))),
          top: top ? (top.tagName + '/'
                      + ((top.getAttribute('data-testid')
                          || top.getAttribute('aria-label')
                          || (top.className || '').toString()
                               .replace(/\\s+/g, ' ').slice(0, 30)) || '')) : null,
        });
      }
      return out;
    }""", trig_aria)
    rec["candidates"] = cands
    print(f"   同名触发器 {len(cands)} 个:")
    for i, c in enumerate(cands):
        print(f"     [{i}] visible={c['visible']} in_view={c['in_view']} "
              f"in_shell={c['in_shell']} self_is_top={c['self_is_top']} "
              f"rect={c['rect']} top={c['top']!r}")
        print(f"         al={c['al'][:60]!r}")
    usable = [c for c in cands
              if c["visible"] and c["in_view"] and c["self_is_top"]]
    if not usable:
        rec["why"] = f"没有可点的触发器（{len(cands)} 个同名，全部不可点）"
        print("   ⚠ 没有一个同名触发器是**可见且点得到的** ⇒ 前置态没成立，不硬点")
        return rec
    if len(usable) > 1:
        print(f"   ⚠ {len(usable)} 个都能点，取第一个（其余可能是另一套渲染）")
    pt = usable[0]["rect"]
    label = usable[0]["al"]
    print(f"   触发器: {label!r} @ {pt[0] + pt[2] // 2},{pt[1] + pt[3] // 2}")
    if guard(label):
        rec["why"] = "付费护栏拦下"
        return rec

    # ⚠️⚠️ 这里**不许**按 Escape 清场（第一版就写了那么一句）：
    #    Escape 会**取消节点选中** → 生成面板整个卸载 → 触发器随之消失 →
    #    接着那一下点击点的是空气，「没有新增层」。审计的 `close_open()`
    #    注释里早就写过这条，第二轮又犯 —— 同一个错误在两处脚本里各犯一次，
    #    说明它得写成**结构**而不是注释。
    #    源站这边连「点回触发器」都不保险（面板可能因为 Escape 已经没了），
    #    所以清场一律放在**量完之后**做，量之前只做快照。
    before = page.evaluate(SNAP_JS)

    page.mouse.click(pt[0] + pt[2] // 2, pt[1] + pt[3] // 2)
    page.wait_for_timeout(900)

    after = page.evaluate(SNAP_JS)
    new = diff_layers(before, after)
    if not new:
        rec["why"] = "点了但没有新增层"
        print("   ⚠ 点开之后**没有新增任何候选层** ⇒ 前置态没成立")
        return rec
    # 取面积最大的那个当层（多层嵌套时最外层才是「那个层」）
    layer = sorted(new, key=lambda x: -(x["w"] * x["h"]))[0]
    rec["layer"] = layer
    print(f"   层: {layer['w']}×{layer['h']} @[{layer['x']},{layer['y']}] "
          f"z={layer['z']} role={layer['role']!r} tid={layer['tid']!r}")
    print(f"      class={layer['cls']!r}")
    if layer["tid"]:
        rec["src_tid"] = layer["tid"]

    # ── 打一个临时标记，之后所有测量都靠它定位 ───────────────────────
    #
    # ③ 这一项在**同一层上栽了四次**，四次都是「靠几何找层」：
    #   ①「罩住层中心」太松 ⇒ host=<body>／常驻的「上传参考内容」浮层
    #   ②「矩形与层相同」太严 ⇒ 层挪了位就找不到
    #   ③「最小含可聚焦项」⇒ 取到层里的子项
    #   ④ 取到生成面板本体的 <form>（680×208）和「提示词」区（646×66）
    # 根子一样：**坐标是快照，会漂**。源站这个下拉在 ② 的 Tab 之后会
    # 自己挪位，而所有后续测量都还在用开层瞬间那张坐标。
    #
    # 所以改成**认层那一刻就按 role 打标记**（源站这四层都是
    # `role=listbox` / `role=dialog`，只是没有 testid），之后一律按标记找。
    # 改 DOM 属于测试夹具 —— 845 的「皮」夹具也是这么做的，会被如实记账。
    marked = mark_layer(layer)
    rec["marked"] = marked
    print(f"   打标记: {marked}")
    if not marked.get("ok"):
        rec["arrow_down"] = {"measured": False,
                             "why": "按 role=listbox/dialog 认不出层 ⇒ 本项没测到"}
        return rec
    # 标记后**用标记的矩形**当 lay（不是快照那张）
    lay = marked["rect"] + [layer["tid"]]
    print(f"   改用标记矩形作 lay: {lay[:4]}")

    # 传给 FOCUS_JS 的扁平参数：有 testid 就用 testid，没有就**只用矩形**
    lay = [layer["x"], layer["y"], layer["w"], layer["h"], layer["tid"]]

    # ① 开层是否接管焦点（blur 之前先读）
    at_open = page.evaluate(FOCUS_JS, lay)
    rec["focus_at_open"] = at_open
    print(f"   ① 开层焦点: {at_open.get('who')!r} al={at_open.get('al')!r} "
          f"in_layer={at_open.get('in_layer')}")

    # ── ② Tab 困不困：⚠️ 从**开层那一刻的焦点**起手，不是冷启动 ──────────
    #
    # 846/H.6 的教训：第一版先 blur 再冷启动 Tab，结果三个源站层**全部**
    # 「12 次 Tab 都进不去」—— 而 ① 已经证明**开层就接管了焦点**。
    # 那就是说**用户根本不需要 Tab 进去**：他点开，焦点已经在里面了。
    # 在这样的层上量冷启动 Tab，等于拿一条**不存在的用户路径**当判据，
    # 量出来的「进不去」会被当成缺陷写进基线表。**先看清 ① 再决定口径。**
    #
    # 冷启动值仍然记下来（作参考），但明确标成「参考，非判据」。
    page.evaluate("() => { const a = document.activeElement;"
                  " if (a && a.blur) a.blur(); return true; }")
    enter_at = None
    for i in range(1, MAX_TABS + 1):
        page.keyboard.press("Tab")
        s = page.evaluate(FOCUS_JS, lay)
        if s.get("in_layer"):
            enter_at = i
            break
    rec["cold_enter_at_reference_only"] = enter_at
    print(f"   ② 参考（非判据）冷启动 Tab 第 {enter_at} 次进层"
          f"{'' if at_open.get('in_layer') else '  ← ① 说这层开层**不**接管焦点'}")

    # 真实口径：重新开一次层，从开层焦点起手量层内 Tab
    page.mouse.click(pt[0] + pt[2] // 2, pt[1] + pt[3] // 2)   # toggle 关
    page.wait_for_timeout(500)
    page.mouse.click(pt[0] + pt[2] // 2, pt[1] + pt[3] // 2)   # 再开
    page.wait_for_timeout(900)
    re_open = page.evaluate(FOCUS_JS, lay)
    rec["focus_at_reopen"] = re_open
    print(f"   ② 重开后焦点: {re_open.get('who')!r} in_layer={re_open.get('in_layer')}")

    escaped_at, landed, closed_at = None, None, None
    for i in range(1, MAX_TABS + 1):
        page.keyboard.press("Tab")
        s = page.evaluate(FOCUS_JS, lay)
        if not page.evaluate(ALIVE_JS, lay)["alive"]:
            closed_at = i
            break
        if not s.get("in_layer"):
            escaped_at, landed = i, s.get("who")
            break
    # 三种结果各归各的账：**困住 / 焦点逃出但层还在 / 层自己关了**
    if closed_at is not None:
        rec["escape"] = {"trapped": False, "layer_closed_at": closed_at,
                         "ambiguous": True,
                         "why": f"第 {closed_at} 次 Tab 时**层自己关了** ⇒ "
                                f"「焦点不在层内」是伪像，Tab 困不困**测不了**"}
        print(f"   ② 层内连按 Tab: 第 {closed_at} 次时**层自己关了** "
              f"⇒ Tab 困不困**测不了**（不写成「不困」）")
    elif escaped_at is None:
        rec["escape"] = {"trapped": True}
        print("   ② 层内连按 Tab: **困住**（12 次全在层内，层也一直在）")
    else:
        rec["escape"] = {"trapped": False, "escaped_at": escaped_at,
                         "landed": landed}
        print(f"   ② 层内连按 Tab: 第 {escaped_at} 次逃出（层还在），"
              f"落在 {landed!r}")

    # ③ 方向键：重新把焦点塞回层内再量（846 教训：破坏性测量之间要 refocus）
    # ② 的 Tab 可能已经把层关掉了（失焦即关）⇒ ③ 之前**无条件重开**：
    # 连点两下（开→关 或 关→开），最后状态**必是开**。不这么做，③ 的
    # elementsFromPoint 是在一个**空位置**上找 host，必然失败 —— 而
    # 第一版正是这么失败的，却没检查就继续按方向键，量出一堆层外轨迹。
    page.mouse.click(pt[0] + pt[2] // 2, pt[1] + pt[3] // 2)
    page.wait_for_timeout(500)
    page.mouse.click(pt[0] + pt[2] // 2, pt[1] + pt[3] // 2)
    page.wait_for_timeout(900)
    rec["reopen_ok"] = page.evaluate(ALIVE_JS, lay)["alive"]
    print(f"   ③ 重新开层: alive={rec['reopen_ok']}")
    # ⚠️ toggle 把层换成了**新元素** ⇒ 标记必须重打，否则后面全部按
    #    「层测不到」记账（而层其实好好开着）。
    m2 = mark_layer(layer, "（重开后补打）")
    rec["remarked"] = m2
    if not m2.get("ok"):
        rec["arrow_down"] = {"measured": False,
                             "why": "重开后按 role 认不出层 ⇒ 本项没测到"}
        print("   ③ 重开后认不出层 ⇒ **本项没测到**，不下结论")
        return rec
    lay3_pre = m2["rect"] + [layer["tid"]]

    # ⚠️⚠️ 第一版的 refocus **失败了**（`elementsFromPoint(层中心)` 找不到
    #    满足矩形条件的 host），而我**没检查就继续按方向键** —— 于是四条
    #    轨迹的焦点全在 `生成` / `视频尺寸选项` 这些**层外**按钮上，
    #    `moved=False` 量的是「层外的按钮按方向键不动」。
    #    846 早就写过：破坏性测量必须在层内起手，**且 refocus 失败就不许测**。
    #    这里两条都做了：换更靠得住的找法（沿元素祖先链往上找「罩住层中心
    #    且尺寸与层相当」的那个），并且**失败就记未测**，绝不报方向键结论。
    ok_rf = page.evaluate("""() => {
      // 按**标记**找层，不再靠几何（几何在 ③ 上栽了四次）
      const L = document.querySelector('[data-probe850]');
      if (!L) return {ok: false, why: '标记不见了（层被关掉了？）'};
      const FOC = 'button:not([disabled]),[tabindex]:not([tabindex="-1"]),'
                + '[role=option],[role=menuitem],input:not([disabled])';
      const f = L.querySelector(FOC);
      if (!f) return {ok: false, why: '层里没有可聚焦项'};
      f.focus();
      const r = L.getBoundingClientRect();
      const lay3 = [Math.round(r.x), Math.round(r.y),
                    Math.round(r.width), Math.round(r.height)];
      const a = document.activeElement;
      const ar = a.getBoundingClientRect();
      const inside = !!L.contains(a);
      return {ok: inside, lay3: lay3,
              host: L.tagName + '/' + (L.getAttribute('role') || ''),
              focused: a.tagName + '/' + ((a.getAttribute('aria-label')
                    || (a.className || '').toString()
                         .replace(/\\s+/g, ' ').slice(0, 24)) || ''),
              rect_of_focus: [Math.round(ar.x), Math.round(ar.y),
                              Math.round(ar.width), Math.round(ar.height)],
              why: inside ? '' : 'focus() 之后 activeElement 仍不在标记元素内'};
    }""")
    page.wait_for_timeout(200)
    if not (isinstance(ok_rf, dict) and ok_rf.get("ok")):
        rec["arrow_down"] = {"measured": False,
                             "why": f"refocus 失败（{ok_rf}）⇒ 本项**没测到**，不下结论"}
        print(f"   ③ refocus 失败：{ok_rf.get('why') if isinstance(ok_rf, dict) else ok_rf}"
              f" ⇒ **本项没测到**，不下结论")
    else:
        lay3 = ok_rf["lay3"]
        print(f"   ③ host={ok_rf.get('host')} 落点={ok_rf.get('focused')}"
              f"（现读矩形 {lay3[:4]}）")
        seq = []
        for _ in range(MAX_KEYS):
            page.keyboard.press("ArrowDown")
            st2 = page.evaluate(FOCUS_JS, lay3)
            seq.append({"who": st2.get("who"), "in": st2.get("in_layer")})
        uniq = len({x["who"] for x in seq})
        rec["arrow_down"] = {"measured": True, "moved": uniq > 1, "seq": seq}
        print(f"   ③ ArrowDown ×{MAX_KEYS}（层内起手）: moved={uniq > 1} "
              f"轨迹={[x['who'] for x in seq]}")


    # ④ Esc 归位
    page.keyboard.press("Escape")
    page.wait_for_timeout(600)
    after_esc = page.evaluate(FOCUS_JS, lay)
    still_open = page.locator(f'[data-testid="{layer["tid"]}"]').count() if layer["tid"] else 0
    page.evaluate(UNMARK_JS)
    rec["esc"] = {"who": after_esc.get("who"), "al": after_esc.get("al"),
                  "in_layer": after_esc.get("in_layer"),
                  "layer_still_in_dom": still_open}
    print(f"   ④ Esc 后焦点: {after_esc.get('who')!r} al={after_esc.get('al')!r} "
          f"in_layer={after_esc.get('in_layer')} 层还在DOM={still_open}")

    return rec


# ── 选中源站的视频节点（848 记：node_236ctpehgg「视频 node: 视频 1」）────
picked = page.evaluate("""() => {
  const n = document.querySelector('.react-flow__node[data-testid="node_236ctpehgg"]')
         || document.querySelector('.react-flow__node');
  if (!n) return null;
  const r = n.getBoundingClientRect();
  const CTRL = 'button,[role=button],a,input,select,textarea';
  for (const [fx, fy] of [[0.5,0.5],[0.5,0.25],[0.25,0.5],[0.75,0.5],
                          [0.5,0.75],[0.2,0.2],[0.8,0.8]]) {
    const x = r.x + r.width * fx, y = r.y + r.height * fy;
    const top = document.elementFromPoint(x, y);
    if (top && n.contains(top) && !top.closest(CTRL))
      return [Math.round(x), Math.round(y), n.getAttribute('data-testid')];
  }
  return null;
}""")
print("== 选点落点 ==", picked)
if not picked:
    raise SystemExit("!! 画布上没有视频节点（前置态没成立）")
page.mouse.click(picked[0], picked[1])
page.wait_for_timeout(1500)
print("== 选中态 ==", page.evaluate(
    "() => [...document.querySelectorAll('.react-flow__node.selected')]"
    ".map(n => n.getAttribute('data-testid'))"))

# ⚠️⚠️ 这里原来按 Escape，**整份探针的三个下拉都是这么没的**：Escape 取消
#    节点选中 → 生成面板卸载 → 后面三个触发器在 DOM 里**一个都不剩**。
#    而 `count=0 ⇒ 前置态没成立` 这句在 dump 之前就已经写好了，于是
#    「我没查到」被印成了「源站没有这一项」—— **假零比报错更危险**。
#    同一个错在三个地方各犯一次（审计 close_open、849 探针、本探针），
#    所以它必须变成**结构**：清场只允许「点回触发器」，不许出现 Escape。
# 每次 probe 之前**重新选中节点**：④ 那一步量 Esc 归位，Esc 在源站会
# 取消选中 → 面板卸载。不重选的话第二个下拉一进来就没有触发器。
def reselect():
    pt = page.evaluate("""() => {
      const n = document.querySelector(
        '.react-flow__node[data-testid="rf__node-node_236ctpehgg"]')
        || document.querySelector('.react-flow__node');
      if (!n) return null;
      const r = n.getBoundingClientRect();
      const CTRL = 'button,[role=button],a,input,select,textarea';
      for (const [fx, fy] of [[0.5,0.5],[0.5,0.25],[0.25,0.5],[0.75,0.5],
                              [0.5,0.75],[0.2,0.2],[0.8,0.8]]) {
        const x = r.x + r.width * fx, y = r.y + r.height * fy;
        const top = document.elementFromPoint(x, y);
        if (top && n.contains(top) && !top.closest(CTRL))
          return [Math.round(x), Math.round(y)];
      }
      return null;
    }""")
    if not pt:
        print("   !! 重新选点失败 ⇒ 前置态没成立")
        return False
    page.mouse.click(pt[0], pt[1])
    page.wait_for_timeout(1200)
    ok = page.evaluate(
        "() => document.querySelectorAll('.react-flow__node.selected').length") == 1
    print(f"   （重新选中: {ok}）")
    return ok


for nm, aria in [("模型", "选择模型"),
                 ("尺寸", "视频尺寸选项"),
                 ("模式", "生成模式"),
                 ("时长", "选择视频生成时长")]:
    if not reselect():
        results[nm] = {"name": nm, "why": "重新选中失败（前置态没成立）"}
        continue
    results[nm] = probe(nm, aria)
    # 清场：点回**刚点过的那个**触发器（toggle 关），不动选中态
    back = page.evaluate("""(aria) => {
      for (const l of document.querySelectorAll(`button[aria-label^="${aria}"]`)) {
        const s = getComputedStyle(l);
        const r = l.getBoundingClientRect();
        if (s.display === 'none' || s.visibility === 'hidden') continue;
        if (r.width < 1 || r.height < 1) continue;
        return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
      }
      return null;
    }""", aria)
    if back:
        page.mouse.click(back[0], back[1])
        page.wait_for_timeout(500)
        print(f"   （清场：点回 {aria} 触发器 @ {back}）")
    else:
        print(f"   （清场：{aria} 触发器已不在 DOM，跳过 —— **保持选中态**，"
              f"不用 Escape）")

with open("/tmp/b850-source-genpanel.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print("\n明细 /tmp/b850-source-genpanel.json")

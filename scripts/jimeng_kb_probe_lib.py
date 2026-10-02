#!/usr/bin/env python3
"""生成/音频面板下拉的**键盘取样**共享库（batch 850 建，851 扩用）。

为什么抽出来：850 探针里为了量「开层是否接管焦点 / Tab 困不困 / 方向键动不动 /
Esc 回哪」，攒了五段互相依赖的 JS（读焦点、候选层快照、层还活着吗、按 role
打标记、清标记）。851 要量**音频面板**那 5 个下拉，判据必须与 850 **逐字同款**
—— 分档只按源站基线表走，而基线表里两批的取样口径不一致的话，表就没法比。
814 的教训：「同一套值散在多个文件里各写一份字面量」。

⚠️ 每一段都有它的**来历**，别随手简化（850 里每一条都是踩出来的）：
  · FOCUS_JS   源站这四层**没有 testid** ⇒ 「在不在层内」按**矩形**判。
               硬套 testid 包含关系只会得到「永远不在层内」，而那个结论会被
               当成「源站不接管焦点」写进基线表 —— 判据量错对象，结论整个反。
               打上标记之后**优先**按标记判（标记跟着元素走，不怕坐标漂）。
  · SNAP_JS    开前/开后**矩形差分**认层。**不滤**画布壳内的元素：源站那个
               「选择模型」按钮实测 in_shell=True，滤掉壳内元素会让渲染在
               节点里的下拉整个消失（849 在复刻侧栽过同一个形状）。
  · ALIVE_JS   「层还在吗」。源站这些下拉**失焦即关** —— 不查这一条，就会
               把「层自己关了」写成「焦点逃出 Tab 陷阱」。
  · MARK_JS    按 `role=listbox/dialog` 给层打 `data-probe850` 标记。层每被
               关掉重开一次就**必须重打**（新元素没有标记）。
  · UNMARK_JS  清标记。
"""

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


MARK_JS = """(info) => {
  // ⚠️⚠️ 每次都**先清掉旧标记**（batch 851 修）。原来这里是
  //    `if (e.hasAttribute('data-probe850')) continue;` —— 跳过已标记的。
  //    而源站这些下拉**点触发器关不掉**（失焦才关），于是第二次调用时
  //    层还是**同一个元素**、还带着旧标记，被自己跳过 ⇒ 返回 ok:false。
  //    表现就是「重开后打标记失败」⇒ ②③④ 整片记「前置态没成立」。
  //    **夹具还挂在层上，判据却说层不见了** —— 这是最坏的一种假零。
  for (const old of document.querySelectorAll('[data-probe850]'))
    old.removeAttribute('data-probe850');

  const FOC = 'button:not([disabled]),[tabindex]:not([tabindex="-1"]),'
            + '[role=option],[role=menuitem],input:not([disabled])';
  const usable = (e, wMin, wMax, hMin, hMax) => {
    const st = getComputedStyle(e);
    if (st.display === 'none' || st.visibility === 'hidden') return false;
    const r = e.getBoundingClientRect();
    if (r.width < wMin || r.width > wMax) return false;
    if (r.height < hMin || r.height > hMax) return false;
    return !!e.querySelector(FOC);
  };
  const take = (nodes) => {
    let best = null, area = 0;
    for (const e of nodes) {
      if (!usable(e, 60, 900, 40, 700)) continue;
      const r = e.getBoundingClientRect();
      const a = r.width * r.height;
      if (a > area) { area = a; best = e; }
    }
    return best;
  };
  // 第一路：role=listbox / dialog（源站绝大多数下拉是这两种）
  let best = take(document.querySelectorAll('[role=listbox],[role=dialog]'));
  let how = 'role';
  // 第二路：class 特征 `animate-none transition-none absolute z-…`
  //   —— 「音色库」那种层**既不是 listbox 也不是 dialog**，只有这条路认得出。
  //   面积上下限是为了排除 `<body>` / 整页容器。
  if (!best) {
    best = take(document.querySelectorAll('[class*="animate-none"]'));
    how = 'class';
  }
  if (!best) return {ok: false, why: 'role 与 class 两条路都认不出层'};
  best.setAttribute('data-probe850', info.role || how);
  const r = best.getBoundingClientRect();
  return {ok: true, role: info.role, how: how,
          rect: [Math.round(r.x), Math.round(r.y),
                 Math.round(r.width), Math.round(r.height)]};
}"""


UNMARK_JS = """() => {
  const n = document.querySelectorAll('[data-probe850]').length;
  for (const e of document.querySelectorAll('[data-probe850]'))
    e.removeAttribute('data-probe850');
  return n;
}"""


# ══ batch 853 加：按 **class 特征**认层（第三路）══════════════════════════
# 探针 853a 查明：「音色: 音色库」开出来的那一层，**既不是 listbox 也不是
# dialog**，class 也不含 `animate-none` ⇒ 851 的两条路都认不出它，于是 851b
# 用矩形差分去抓，抓到 648×1932 的**整页容器**，读出来的「不接管焦点」是伪像。
# 853a 把它真正的身份 dump 出来了：**音色条目**带一个稳定的语义 class
#   `min-w-canvas-audio-voice-shrinkable`（实测含 生动解说/精品有声书/
#   桃花庵主/灵动女声/厚实男声/磁性男主播 …）
# ⇒ 认法 = **取这些条目的最近公共祖先**。这不是「放宽判据」：判据从「猜一个
#   矩形」换成「按一个**实测出来的**稳定 class 定位真身」，量的是同一个对象。
MARK_BY_CLASS_JS = """(a) => {
  for (const old of document.querySelectorAll('[data-probe850]'))
    old.removeAttribute('data-probe850');
  const items = [...document.querySelectorAll(
    `[class*="${a.cls}"]`)].filter((e) => {
      const s = getComputedStyle(e);
      if (s.display === 'none' || s.visibility === 'hidden') return false;
      const r = e.getBoundingClientRect();
      return r.width > 4 && r.height > 4;
    });
  if (items.length < (a.min_items || 2))
    return {ok: false, why: `只找到 ${items.length} 个含 ${a.cls} 的可见元素`};
  // 最近公共祖先：从第 1 个往上走，直到它包含**所有**条目
  let anc = items[0].parentElement;
  while (anc && !items.every((i) => anc.contains(i)))
    anc = anc.parentElement;
  if (!anc) return {ok: false, why: '这些条目没有公共祖先'};
  // 公共祖先可能一路涨到 <body>（整页）—— 那就退到「装着 ≥半数条目、
  // 且不是 body/html」的最高一层
  let pick = anc;
  while (pick.parentElement && pick.parentElement !== document.body
         && pick.parentElement !== document.documentElement
         && items.filter((i) => pick.parentElement.contains(i)).length
             >= items.length * 0.5) {
    pick = pick.parentElement;
  }
  if (pick === document.body || pick === document.documentElement)
    return {ok: false, why: '公共祖先一路涨到整页容器，说明认法不对'};
  pick.setAttribute('data-probe850', a.role || 'class-' + a.cls);
  const r = pick.getBoundingClientRect();
  return {ok: true, role: a.role, how: 'class-common-ancestor',
          n_items: items.length,
          rect: [Math.round(r.x), Math.round(r.y),
                 Math.round(r.width), Math.round(r.height)]};
}"""


def mark_by_class(page, cls, role="", min_items=2, note=""):
    """按 class 特征取**最近公共祖先**当层（853a 实测出来的认法）。"""
    out = page.evaluate(
        MARK_BY_CLASS_JS,
        {"cls": cls, "role": role, "min_items": min_items})
    if out.get("ok"):
        print(f"   按 class 认层{note}: {cls} ×{out.get('n_items')} "
              f"⇒ {out.get('rect')}")
    else:
        print(f"   ⚠ 按 class 认层{note}失败: {out}")
    return out


# ══ 853c：音色库层的**专用**认法 ═══════════════════════════════════════════
# ⚠️⚠️ `mark_by_class`（取最近公共祖先）在音色库上**也失败了**：实测该 class
#    有 **63** 个 chip 散布在**整个画布节点区**上（不只是打开的面板里），
#    公共祖先一路涨到 1512×1200 的**整个视口** ⇒ 又是「量到整页」。
#    这跟 851b 犯的是**同一个错的两面**：851b 用矩形差分抓到整页，
#    853b 用公共祖先也抓到整页。**换判据不解决判据量错对象。**
#
#    正确认法（853c 实测）：音色库面板有个**标题**「全音色」。从它往上找
#    「**装着 ≥N 个可见 chip、且面积 < 半个视口**」的**最小**祖先 —— 这才是面板。
#    面积上限是必需的：没有它，「整页」天然满足「装着所有 chip」。
MARK_VOICE_JS = """(a) => {
  for (const old of document.querySelectorAll('[data-probe850]'))
    old.removeAttribute('data-probe850');
  const visible = (e) => {
    const s = getComputedStyle(e);
    if (s.display === 'none' || s.visibility === 'hidden') return false;
    const r = e.getBoundingClientRect();
    return r.width > 4 && r.height > 4;
  };
  const chips = [...document.querySelectorAll(`[class*="${a.cls}"]`)].filter(visible);
  // 找标题「全音色」
  let head = null;
  for (const e of document.querySelectorAll('h1,h2,h3,div,span,p')) {
    if ((e.innerText || '').trim() === a.header && !e.querySelector('h1,h2,h3,div,span,p'))
      { head = e; break; }
  }
  if (!head) return {ok: false, why: `找不到标题「${a.header}」`};
  const vw = innerWidth, vh = innerHeight;
  // 从标题往上找：装 >=N 个 chip、且面积 < 视口一半的最小祖先
  let cur = head.parentElement, best = null;
  while (cur && cur !== document.body && cur !== document.documentElement) {
    const r = cur.getBoundingClientRect();
    const n = chips.filter((c) => cur.contains(c)).length;
    if (n >= (a.min_chips || 8)
        && r.width * r.height < vw * vh * (a.max_frac || 0.5)) { best = cur; break; }
    cur = cur.parentElement;
  }
  if (!best)
    return {ok: false,
            why: `从「${a.header}」往上没有祖先同时满足：`
                 + `chip≥${a.min_chips} 且 面积<视口×${a.max_frac}`};
  best.setAttribute('data-probe850', 'voice-library');
  const r = best.getBoundingClientRect();
  return {ok: true, how: 'header+nearest-fitting-ancestor',
          n_chips: chips.filter((c) => best.contains(c)).length,
          rect: [Math.round(r.x), Math.round(r.y),
                 Math.round(r.width), Math.round(r.height)]};
}"""


def mark_voice_panel(page, note=""):
    """音色库层专用认法：标题「全音色」+ ≥8 可见 chip + 面积<半视口的最小祖先。"""
    out = page.evaluate(MARK_VOICE_JS,
                        {"cls": "min-w-canvas-audio-voice-shrinkable",
                         "header": "全音色", "min_chips": 8, "max_frac": 0.5})
    if out.get("ok"):
        print(f"   认音色库层{note}: chip×{out.get('n_chips')} ⇒ {out.get('rect')}")
    else:
        print(f"   ⚠ 认音色库层{note}失败: {out}")
    return out


def mark_layer(page, layer, note=""):
    """打标记并返回新矩形。层被关掉重开过就**必须**重打。"""
    out = page.evaluate(MARK_JS, {"role": layer["role"]})
    if out.get("ok"):
        print(f"   打标记{note}: role={out.get('role')} rect={out.get('rect')}")
    else:
        print(f"   ⚠ 打标记{note}失败: {out}")
    return out


def ensure_open(page, layer, click_xy, note="", tries=4):
    """**确保层开着**，返回打标记结果；实在开不了返回 `{"ok": False}`。

    ⚠️⚠️ batch 851 补的第三层教训。前两版都是「点两下触发器」当重开，
    三次全错，因为**破坏性测量会改变层的状态**：

      · 冷启动那 12 次 Tab —— 源站这些下拉**失焦即关**，按着按着层没了
      · 盲点两下 = 「开→关」或「关→开」，到底哪个取决于**此刻**的状态
      · 结果：层明明可以打开，判据却报「重开后认不出层 ⇒ 前置态没成立」

    假零比报错更危险：报错会停，假零会流进「这一层源站测不到」的结论里，
    而它其实测得到。所以这里**不用状态假设，改用「打标记」当探针** ——
    打不到就点一下触发器，直到打得到为止。
    """
    for i in range(tries):
        m = mark_layer(page, layer, f"{note}试{i + 1}")
        if m.get("ok"):
            return m
        page.mouse.click(click_xy[0], click_xy[1])
        page.wait_for_timeout(900)
    return mark_layer(page, layer, f"{note}（{tries} 次都没打开）")


# ══ batch 853 加：**852 修正版**的四项测量例程 ════════════════════════════
# ⚠️⚠️ 为什么把测量例程也搬进共享库，而不是让 853b 抄 851b：
#    851b 的 ③ 方向键判据**带着 852 刚查出的两个病** ——
#      ① `moved` 只对按完之后的 4 个点去重、**漏掉起点**（852 §70 病根①）；
#      ② 判断「层里哪些可聚焦」时**真的调 `focus()`**，把起点推到最后一个
#         能聚焦的项上（852 §70 病根②）。
#    853 若抄 851b，等于把**刚修好的 bug 又抄回来**。所以例程放共享库，
#    口径与 850/851/852 逐字同款。
FOCUSABLE_JS = """() => {
  // 纯**属性**推断「层里哪些可聚焦」——**不许真的 focus() 试探**
  // （852：那会把起点推到最后一个能聚焦项上，制造假阴）
  const L = document.querySelector('[data-probe850]');
  if (!L) return {ok: false, why: '标记不见了'};
  const SEL = 'button,[role=option],[role=menuitem],[tabindex],a[href],input,select,textarea';
  const out = [];
  for (const e of L.querySelectorAll(SEL)) {
    const s = getComputedStyle(e);
    if (s.display === 'none' || s.visibility === 'hidden') continue;
    if (e.hasAttribute('disabled') || e.getAttribute('aria-disabled') === 'true') continue;
    if (e.getAttribute('tabindex') === '-1') continue;   // 漫游 tabindex 的非当前项
    const r = e.getBoundingClientRect();
    if (r.width < 2 || r.height < 2) continue;
    out.push({who: (e.innerText || e.getAttribute('aria-label') || e.tagName)
              .trim().replace(/\\s+/g, ' ').slice(0, 14),
              ti: e.getAttribute('tabindex')});
  }
  return {ok: true, n: out.length, items: out.slice(0, 6)};
}"""


def measure_kb(page, marked, trigger_pt, max_tabs=12, max_keys=4,
               note="", remark=None):
    """在一个**已打开并打好标记**的层上量四项，返回可直接进基线表的 rec。

    口径（与 850/851/852/853 逐字同款）：
      ① 开层是否接管焦点
      ③ 方向键动不动（**排在 ② 之前**，853c；`moved` 含起点，852）
      ② 层内 Tab 会不会逃出（**并查层还在不在** —— 源站这些下拉失焦即关）
      ④ Esc 关层后焦点回哪

    ⚠️⚠️ `remark`（854 补的第三个参数）：③ 在「① 焦点不在层内」时要用
    `ensure_open` **重开并重新打标记**。而 `ensure_open` 默认走 `mark_layer`
    —— 那是个 **role/class 启发式**（取面积最大的 `role=listbox/dialog` 或
    `[class*="animate-none"]`）。**对「音色库」这种既非 listbox 也非 dialog
    的层，它会认到别的元素**：853b 量到 680×328，而真实面板是 **680×96**
    （探针 854 连续 8 次采样恒为 96，`scrollH==clientH` 无内部滚动 ⇒
    96 是稳定态，328 是**认错元素**量出来的）。
    ⇒ 调用方**必须把当初认出这一层用的那个认法传进来**（音色库传
    `mark_voice_panel`），这样「重开」与「首次识别」用的是**同一把尺**。
    """
    rec = {}
    lay = marked["rect"]
    # ① 开层焦点
    at_open = page.evaluate(FOCUS_JS, lay + [None])
    rec["focus_at_open"] = at_open
    print(f"   ① 开层焦点{note}: {at_open.get('who')!r} "
          f"in_layer={at_open.get('in_layer')}")

    # ── ③ 方向键**先于**② 测（853c 的方法论修正，理由很长，见下）──────────
    # ⚠️ 为什么必须排在 ② 前面：① 已经把「层刚打开、焦点**自然**落在层内」这个
    #    最好的起点建立好了。而 ② 那串 Tab 是**破坏性**测量 —— 源站这几层第 1 次
    #    Tab 就逃出，层也跟着进入「被走过一遍」的中间态。853b 把 ③ 排在 ② 之后，
    #    于是每一层都要 ensure_open 再尝试 `focus()` 重建起点，而源站**对
    #    `focus()` 的反应很不稳**（音乐模型层、音色库层连着两次都是
    #    「focus() 后焦点仍不在层内」）⇒ 交出「没测到」—— 可它其实在 ① 那个
    #    状态下**直接按方向键就测得到**。
    #    这与 852 病根②同源：**别为了「建立起点」去动它，用天然的那个。**
    #    `moved` 仍**把 ① 读到的起点算进去**（852 修正），所以起手必须是
    #    「① 那一刻的焦点」，而不是任何一次 refocus 之后的。
    start_who = at_open.get("who")
    if at_open.get("in_layer"):
        seq = []
        for _ in range(max_keys):
            page.keyboard.press("ArrowDown")
            s = page.evaluate(FOCUS_JS, lay + [None])
            seq.append(s.get("who"))
        uniq = len(set(seq) | {start_who})       # ★ 起点并进来（852）
        rec["arrow_down"] = {"measured": True, "moved": uniq > 1,
                             "start": start_who, "seq": seq,
                             "how": "在①的天然焦点态上直接按（853c）"}
        print(f"   ③ ArrowDown×{max_keys} 起点={start_who!r} "
              f"moved={uniq > 1} 轨迹={seq}")
    else:
        # ① 焦点**不在**层内（这一层开层不接管焦点）⇒ 起点得自己建立，
        # 而建立起点 = **重开层**（回到「刚打开」），不是 `focus()` 试探。
        print(f"   ③ ① 焦点不在层内（{start_who!r}）⇒ 重开层建立起点")
        # ⚠️ 用**调用方给的同一个认法**重开（854）：默认的 mark_layer 是
        #    role/class 启发式，对音色库这种层会认错元素（328 vs 96）。
        if remark is not None:
            def _re_mark(_page, _layer, _xy, note="", tries=4):
                for i in range(tries):
                    m = remark(page, note=f"{note}试{i + 1}")
                    if m.get("ok"):
                        return m
                    page.mouse.click(_xy[0], _xy[1])
                    page.wait_for_timeout(900)
                return remark(page, note=f"{note}（{tries} 次都没打开）")
            reopened = _re_mark(page, None, trigger_pt, note="测方向键前重开")
        else:
            reopened = ensure_open(page, {"role": "arrow-restart"},
                                   trigger_pt, note="测方向键前重开")
        if not reopened.get("ok"):
            rec["arrow_down"] = {"measured": False,
                                 "why": "测方向键前重开层失败 ⇒ 没测到（不硬测中间态）"}
            print("      重开层失败 ⇒ **本项没测到**（不在中间态上硬测）")
        else:
            lay = reopened["rect"]
            at2 = page.evaluate(FOCUS_JS, lay + [None])
            if at2.get("in_layer"):
                start_who = at2.get("who")
                seq = []
                for _ in range(max_keys):
                    page.keyboard.press("ArrowDown")
                    s = page.evaluate(FOCUS_JS, lay + [None])
                    seq.append(s.get("who"))
                uniq = len(set(seq) | {start_who})
                rec["arrow_down"] = {"measured": True, "moved": uniq > 1,
                                     "start": start_who, "seq": seq,
                                     "how": "重开后焦点落在层内（①不接管焦点）"}
                print(f"   ③ ArrowDown×{max_keys} 起点={start_who!r} "
                      f"moved={uniq > 1} 轨迹={seq}")
            else:
                rec["arrow_down"] = {
                    "measured": False,
                    "why": f"重开后焦点仍不在层内（落在 {at2.get('who')!r}）⇒ 没测到"}
                print(f"   ③ 重开后焦点仍不在层内（{at2.get('who')!r}）"
                      f"⇒ **本项没测到**")

    # ② Tab 逃出（层还在才谈得上「逃出」；源站这些下拉失焦即关 ⇒ 必查 ALIVE）
    escaped_at, landed, closed_at = None, None, None
    for i in range(1, max_tabs + 1):
        page.keyboard.press("Tab")
        s = page.evaluate(FOCUS_JS, lay + [None])
        if not page.evaluate(ALIVE_JS, lay)["alive"]:
            closed_at = i
            break
        if not s.get("in_layer"):
            escaped_at, landed = i, s.get("who")
            break
    if closed_at is not None:
        rec["escape"] = {"trapped": False, "layer_closed_at": closed_at,
                         "ambiguous": True,
                         "why": f"第 {closed_at} 次 Tab 时层自关 ⇒ 测不了"}
        print(f"   ② 第 {closed_at} 次 Tab 层自己关了 ⇒ 困不困**测不了**")
    elif escaped_at is None:
        rec["escape"] = {"trapped": True}
        print(f"   ② **困住**（{max_tabs} 次全在层内，层也一直在）")
    else:
        rec["escape"] = {"trapped": False, "escaped_at": escaped_at,
                         "landed": landed}
        print(f"   ② 第 {escaped_at} 次逃出（层还在），落在 {landed!r}")

    # ④ Esc
    page.keyboard.press("Escape")
    page.wait_for_timeout(700)
    after = page.evaluate(FOCUS_JS, lay + [None])
    rec["esc"] = {"who": after.get("who"), "al": after.get("al"),
                  "in_layer": after.get("in_layer")}
    print(f"   ④ Esc 后焦点: {after.get('who')!r} al={after.get('al')!r}")
    page.evaluate(UNMARK_JS)
    return rec

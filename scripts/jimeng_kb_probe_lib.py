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

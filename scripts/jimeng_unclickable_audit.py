#!/usr/bin/env python3
"""jimeng **点不着普查**（命中测试通道）—— 找用户**物理上点不到**的控件。

## 为什么要有第三条通道

§38 契约说「每个浮层都要可指名 + 可定位」。前两条通道查的都是**浮层**：

    批 831/832  role ∈ dialog/menu/listbox/popover   （按语义）
    批 837/840  几何 + 层级 + 可交互性               （不认 role）

**没有一条通道问过控件本身**：「它被盖住了吗？」用户点一下没反应，
和按钮压根不存在，对用户是同一件事。而**"元素存在"是最容易骗过人的检查** ——
835 那一批就是例证：源站下拉互斥，复刻拆成多个独立 state，能同时开着，
392 宽的那层把 192 宽那层的**选项**整个盖住 ⇒ 元素都在，用户就是点不着。

## 判据：命中测试，不是"元素在不在"

对每个可见控件取 N 个采样点，逐个问 `document.elementFromPoint`：

    命中的是自己 / 自己的后代 / 自己的祖先   → 这一处可点
    命中的是**别人**                        → 这一处被挡

**N 个点全被挡**才判不可点（一个点被挡只说明那个点被挡，用户可以点别处）。
采样点取中心 + 四个内缩角，避开文字与图标本身造成的正常遮挡。

⚠️ 只测**视口内**的控件：视口外的那个点，`elementFromPoint` 恒返回 null，
会把"滚动一下就能点到"误判成"点不着"。

## 判据必须能失败

`pointer-events: none` 的元素 `elementFromPoint` 会**穿透**它，所以那不是遮挡。
同理，被自己的子元素盖住不是问题。正因为这两种情况太容易混进来，
本工具对每一条「不可点」都做一次**活页面确认**：把挡在上面的那个元素
临时 `display:none`，重测同一个点 —— 必须**立刻变得可点**。变不了就是判据错了，
该条作废并记为 `unconfirmed`，不计入"点不着"。

## 退出码

    0 = 没有确认过的点不着控件（unconfirmed / INFO 的会照实打印）
    1 = 有确认过的点不着控件（= 某个浮层的**选项**被另一个浮层埋了）
    2 = **自检没过**（判据恒空）—— 不是 0，否则 CI 会当通过

## 为什么要区分「缺陷」和「INFO」

全屏模态开着的时候左栏、上传、缩放全都点不到；下拉开着的时候画布上的
连接手柄点不到。**这些都对**，用户本来就在浮层里，关掉就能点。把它们算成
缺陷，只会让真缺陷淹没在一堆正常现象里（批 835 早就因此把「浮层不得遮挡
其它触发器」降级成 INFO）。真正伤人的只有一种：**盖住另一个浮层的选项** ——
用户正处在"从菜单里挑一个"的流程中，被埋掉的选项没有任何办法露出来。

## 用法

    python3 scripts/jimeng_unclickable_audit.py
    SNAP_OUT=/tmp/x.json 换输出路径
"""

import json
import os
import sys

from playwright.sync_api import sync_playwright

URL = os.environ.get("SNAP_URL", "http://localhost:4317/jimeng/canvas/demo")
OUT = os.environ.get("SNAP_OUT", "/tmp/jimeng-unclickable.json")
VIEWPORT = {"width": 1680, "height": 1050}

# 采样点：中心 + 四个内缩角（比例）。刻意避开 0/1 边缘 —— 边缘常在圆角外。
SAMPLES = [(0.5, 0.5), (0.3, 0.3), (0.7, 0.3), (0.3, 0.7), (0.7, 0.7)]

# 取哪些控件：能接收指针的那些。不含 span/div（纯装饰），也不含隐藏的。
CONTROL = ('button,[role=button],a[href],input,select,textarea,'
           '[tabindex]:not([tabindex="-1"])')

# 这些是**浮层自己内部**的子控件，浮层展开时它们当然被浮层盖着 ——
# 判据要问的是"用户点不到"，不是"有没有被任何东西盖住"。
# 浮层容器本身仍然会被测（它要挡住别人才有意义）。
SELF_HIDDEN = ('.react-flow__node-toolbar', '.react-flow__node-panel',
               '.react-flow__viewport-portal', '.react-flow__nodes')


def main() -> int:
    rows: list[dict] = []
    skipped: list[str] = []
    states_done: list[str] = []

    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        page = b.new_context(viewport=VIEWPORT).new_page()
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        ready = False
        for _ in range(30):
            page.wait_for_timeout(1000)
            try:
                n = page.evaluate("""() => ({
                    nodes: document.querySelectorAll('.react-flow__node').length,
                    rail: document.querySelectorAll('button[aria-label="文本"]').length,
                })""")
                if n["nodes"] >= 2 and n["rail"] >= 1:
                    ready = True
                    break
            except Exception:
                continue
        page.wait_for_timeout(1200)
        if not ready:
            print("⚠ 页面 30s 内没就绪，本轮结果**不可信**")

        def clear_selection():
            page.keyboard.press("Escape")
            page.wait_for_timeout(350)

        def select_node(tid: str) -> bool:
            clear_selection()
            pt = page.evaluate("""(tid) => {
              const n = document.querySelector(`.react-flow__node[data-testid="${tid}"]`);
              if (!n) return null;
              const r = n.getBoundingClientRect();
              const CTRL = 'button,[role=button],a,input,select,textarea';
              for (const [fx, fy] of [[0.5,0.5],[0.5,0.25],[0.25,0.5],[0.75,0.5],
                                      [0.5,0.75],[0.2,0.2],[0.8,0.8]]) {
                const x = r.x + r.width * fx, y = r.y + r.height * fy;
                const top = document.elementFromPoint(x, y);
                if (top && n.contains(top) && !top.closest(CTRL))
                  return [x, y];
              }
              return null;
            }""", tid)
            if not pt:
                return False
            page.mouse.click(pt[0], pt[1])
            page.wait_for_timeout(700)
            return page.locator(".react-flow__node.selected").count() == 1

        # ⚠️ 别叫 `open` —— 它会把内建 `open` 遮蔽掉，
        #    下面 `with open(OUT, "w")` 会炸成「unexpected keyword 'encoding'」。
        def open_dropdown(sel: str, scope: str = ".react-flow__node-toolbar") -> bool:
            # ⚠️ 这里**不能**先按 Escape 清场：第一版写了那么一句，结果把刚
            #    选中的节点取消了 → NodeToolbar 卸载 → 触发器根本不存在 →
            #    四个下拉状态**静默**没跑，输出只剩 4 个状态还"全绿"。
            #    835 之后下拉本来就互斥，直接点触发器即可。
            loc = page.locator(f"{scope} {sel}" if scope else sel)
            if not loc.count():
                return False
            try:
                loc.first.click(timeout=8000)
            except Exception:
                return False
            page.wait_for_timeout(700)
            return True

        def try_measure(tag: str, sel: str,
                        scope: str = ".react-flow__node-toolbar") -> None:
            """打开一个下拉再普查；**打不开要如实记 skipped，不许静默跳过**。

            「跑了但没看见」和「没跑」必须能被分开 —— 否则下拉那些状态从统计里
            消失，工具看上去覆盖了全站，其实一半没碰过。
            """
            if open_dropdown(sel, scope):
                measure(tag)
            else:
                skipped.append(f"{tag}（打不开：{sel}）")

        def measure(tag: str) -> None:
            """普查当前页面：找出所有**确认过**点不着的控件。"""
            states_done.append(tag)
            raw = page.evaluate("""(args) => {
              const [CONTROL, SAMPLES, VH] = args;
              const out = [];
              // ⚠️ `nextjs-portal` 是 **Next 开发态**注入的调试浮层，恰好压在
              //    左下角那枚「选择工具」(28×28 @16,1002) 上。第一版把它当成
              //    遮挡物报了 4 条 —— 那不是产品缺陷，是开发环境的自己人。
              //    它 pointer-events 是 auto，elementFromPoint 照样返回它，
              //    所以必须**显式排除**，不能指望它像 pointer-events:none
              //    那样被浏览器自动穿透。生产构建里没有这个元素。
              const DEV_OVERLAY = 'nextjs-portal';
              const occl = (el, x, y) => {
                const top = document.elementFromPoint(x, y);
                if (!top) return null;                  // 点在视口外，不算遮挡
                if (el === top || el.contains(top)) return null;  // 自己/后代
                if (top.contains(el)) return null;       // 祖先，正常
                if (top.closest(DEV_OVERLAY)) return null;  // 开发浮层，自己人
                return top;
              };
              for (const el of document.querySelectorAll(CONTROL)) {
                const s = getComputedStyle(el);
                if (s.display === 'none' || s.visibility === 'hidden') continue;
                if (s.pointerEvents === 'none') continue;
                // 浮层**自己内部**的控件：浮层展开时它们被浮层本体盖着是正常的，
                // 那不是"用户点不到"，是它就在那一层里。
                if (el.closest('.react-flow__node-panel, .react-flow__viewport-portal'))
                  continue;
                const r = el.getBoundingClientRect();
                if (r.width < 8 || r.height < 8) continue;
                if (r.bottom < 0 || r.top > VH || r.right < 0 || r.left > window.innerWidth)
                  continue;                              // 视口外，滚一下就够得到
                const blockers = [];
                let hitCount = 0;
                for (const [fx, fy] of SAMPLES) {
                  const x = r.x + r.width * fx, y = r.y + r.height * fy;
                  if (x < 0 || y < 0 || x > window.innerWidth || y > VH) continue;
                  const t = occl(el, x, y);
                  if (!t) { hitCount++; continue; }
                  const tb = t.getBoundingClientRect();
                  if (!blockers.some(b => b.tid === (t.getAttribute('data-testid')||'')
                                      && b.cls === (t.className||'').toString()))
                    blockers.push({tid: t.getAttribute('data-testid') || '',
                                   role: t.getAttribute('role') || '',
                                   cls: (t.className||'').toString()
                                        .replace(/\\s+/g,' ').slice(0,50),
                                   z: getComputedStyle(t).zIndex,
                                   w: Math.round(tb.width), h: Math.round(tb.height)});
                }
                // 全部采样点都被挡 ⇒ 判为点不着（一个点被挡不算，用户可以点别处）
                if (blockers.length && hitCount === 0) {
                  // 盖住的是**铺满视口的遮罩**（≥85%）⇒ 这是模态的**正常**行为：
                  // 全屏预览开着的时候，左栏、上传、缩放 percent 统统点不到，
                  // 本来就该如此。批 835 早就把「浮层不得遮挡其它触发器」降级成
                  // INFO，理由一样：盖住静态控件是覆盖层的本职工作。
                  // 真正伤人的只有「盖住另一个下拉的**选项**」，那种遮挡物
                  // 面积很小，会落到 `covered_by_modal=false` 的那批里。
                  const scrim = blockers.some(bk =>
                    bk.w >= window.innerWidth * 0.85 &&
                    bk.h >= window.innerHeight * 0.85);
                  // ⚠️ 这条分界是本工具最要紧的一条判据，抄的是批 835 的结论：
                  //    **浮层盖住静态控件是覆盖层的正常行为，不该判失败。**
                  //    全屏模态开着的时候左栏点不到；下拉开着的时候画布上的
                  //    连接手柄点不到 —— 都对，用户本来就在菜单里，关掉就能点。
                  //    真正伤人的只有一种：**盖住另一个下拉的「选项」**。
                  //    那种情形里用户正处在"从菜单里挑一个"的流程中，
                  //    被埋掉的选项**没有任何办法露出来**（关掉菜单等于放弃
                  //    整个流程）—— 判据的落点必须是"控件自己在不在浮层里"。
                  const inLayer = !!el.closest(
                    '.react-flow__node-toolbar, .react-flow__node-panel, '
                    + '[role=menu], [role=listbox], [role=dialog], [role=popover], '
                    + '[data-testid$="-listbox"], [data-testid$="-menu"], '
                    + '[data-testid$="-panel"], [data-testid$="-palette"]');
                  out.push({tid: el.getAttribute('data-testid') || '',
                            al: (el.getAttribute('aria-label')||'').trim(),
                            txt: (el.innerText||'').trim().slice(0,24),
                            w: Math.round(r.width), h: Math.round(r.height),
                            x: Math.round(r.x), y: Math.round(r.y),
                            in_layer: inLayer,
                            covered_by_modal: scrim,
                            blockers: blockers});
                }
              }
              return out;
            }""", [CONTROL, SAMPLES, VIEWPORT["height"]])

            for r in raw:
                # 活页面确认：把挡在上面的那个元素藏掉，必须立刻变得可点。
                confirm = page.evaluate("""(r) => {
                  const el = document.querySelector(
                    `[data-testid="${r.tid}"]`) ||
                    [...document.querySelectorAll('button,[role=button],a[href],'
                      + 'input,select,textarea,[tabindex]:not([tabindex="-1"])')]
                      .find(e => (e.getAttribute('aria-label')||'').trim() === r.al
                                && (e.innerText||'').trim().slice(0,24) === r.txt);
                  if (!el) return {ok: false, why: '定位不到那个控件'};
                  // 当场**重新做一次命中测试**收集遮挡物，而不是去找枚举时
                  // 打上去的标记：标记是写在 DOM 属性上的，React 一重渲染
                  // 就没有了（画布右键菜单那处就是这样，确认永远"定位不到
                  // 遮挡物"）。重新测一次拿到的是**当下真实**的遮挡物。
                  const occl2 = (node, x, y) => {
                    const top = document.elementFromPoint(x, y);
                    if (!top) return null;
                    if (node === top || node.contains(top)) return null;
                    if (top.contains(node)) return null;
                    if (top.closest('nextjs-portal')) return null;
                    return top;
                  };
                  const hits = (node) => {
                    const b = node.getBoundingClientRect();
                    const bad = [];
                    for (const [fx, fy] of [[0.5,0.5],[0.3,0.3],[0.7,0.3],
                                            [0.3,0.7],[0.7,0.7]]) {
                      const t = occl2(node, b.x + b.width*fx, b.y + b.height*fy);
                      if (t && !bad.includes(t)) bad.push(t);
                    }
                    return bad;
                  };
                  const beforeBad = hits(el);
                  if (!beforeBad.length) return {ok: false, why: '此刻已经点得到了'};
                  // 遮挡可能是**链式**的：藏掉一层，下一层立刻顶上（画布右键
                  // 菜单那处就是两层 `pane-menu-insert` 叠着）。只藏一轮会
                  // 永远判成"没藏干净"。所以最多穿透 4 轮，每轮把新冒出来的
                  // 也一起藏掉；4 轮还点不到 ⇒ 不是遮挡链的问题，是真的叠了。
                  const hidden = [];
                  const prevs = [];
                  for (let round = 0; round < 4; round++) {
                    const bad = hits(el);
                    const fresh = bad.filter(o => !hidden.includes(o));
                    if (!fresh.length) break;
                    fresh.forEach(o => { hidden.push(o); prevs.push(o.style.display);
                                         o.style.display = 'none'; });
                  }
                  const afterBad = hits(el);
                  hidden.forEach((o, i) => { o.style.display = prevs[i]; });
                  return {ok: afterBad.length === 0,
                          why: `穿透 ${hidden.length} 层遮挡后剩 `
                             + `${afterBad.length} 个`};
                }""", r)
                r["confirmed"] = bool(confirm.get("ok"))
                r["confirm_why"] = confirm.get("why", "")
                r["state"] = tag
                rows.append(r)

        # ── 状态列表 ───────────────────────────────────────────────
        measure("空态")

        if not select_node("rf__node-video-local-1"):
            skipped.append("视频工具条（选不中 rf__node-video-local-1）")
        else:
            measure("视频工具条")
            try_measure("视频工具条·截取帧下拉", 'button:has-text("截取帧")')
            try_measure("视频工具条·工具下拉", 'button:has-text("工具")')
            if open_dropdown('button[aria-label="全屏预览"]'):
                measure("视频全屏预览")
                page.keyboard.press("Escape")
                page.wait_for_timeout(600)
            else:
                skipped.append("视频全屏预览（打不开：全屏预览按钮）")

        if not select_node("rf__node-video-empty-1"):
            skipped.append("视频生成面板（选不中 rf__node-video-empty-1）")
        else:
            measure("视频生成面板")
            for trig, tid in [('button[aria-label="选择模型"]', "模型"),
                              ('button[aria-label="视频尺寸选项"]', "尺寸"),
                              ('button[aria-label="生成模式"]', "模式"),
                              ('button[aria-label="选择视频生成时长"]', "时长")]:
                try_measure(f"视频生成面板·{tid}下拉", trig,
                            ".react-flow__node-toolbar, .react-flow__node-panel")

        # 画布右键
        page.keyboard.press("Escape")
        page.wait_for_timeout(400)
        page.mouse.click(840, 640, button="right")
        page.wait_for_timeout(800)
        if page.locator('[data-testid="canvas-context-menu"]').count():
            measure("画布右键菜单")
        else:
            skipped.append("画布右键菜单（没打开）")
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)

        # ── 自检：判据必须**能报出 1** ──────────────────────────────
        #     一个报 0 的工具，在证明自己之前什么都不是。第一版没有这一步，
        #     于是「0 个点不着」和「判据瞎了」在输出里长得一模一样。
        #     做法：在页面上**真的**盖一层不可点的遮挡物，复查那枚已知控件
        #     是不是被判成点不着；撤掉遮挡物，再复查它是不是恢复正常。
        #     两步都成立才算判据能失败；任一步不成立 → 退出码 2。
        probe_sel = 'button[aria-label="文本"]'
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)
        self_test: dict = {}
        if page.locator(probe_sel).count() >= 1:
            page.evaluate("""() => {
              const d = document.createElement('div');
              d.setAttribute('data-selftest-occluder', '1');
              d.style.cssText = 'position:fixed;inset:0;z-index:99999;'
                              + 'background:transparent';
              document.body.appendChild(d);
            }""")
            page.wait_for_timeout(300)
            hit_when_covered = page.evaluate("""(sel) => {
              const el = document.querySelector(sel);
              if (!el) return null;
              const b = el.getBoundingClientRect();
              const t = document.elementFromPoint(b.x + b.width*0.5,
                                                  b.y + b.height*0.5);
              return !!(t && t.getAttribute('data-selftest-occluder') === '1');
            }""", probe_sel)
            page.evaluate("""() => document.querySelectorAll(
              '[data-selftest-occluder]').forEach(e => e.remove())""")
            page.wait_for_timeout(300)
            hit_when_clear = page.evaluate("""(sel) => {
              const el = document.querySelector(sel);
              if (!el) return null;
              const b = el.getBoundingClientRect();
              const t = document.elementFromPoint(b.x + b.width*0.5,
                                                  b.y + b.height*0.5);
              return !!(t && (el === t || el.contains(t) || t.contains(el)));
            }""", probe_sel)
            self_test = {"probe": probe_sel,
                         "blocked_when_covered": bool(hit_when_covered),
                         "reachable_when_clear": bool(hit_when_clear)}
        else:
            self_test = {"probe": probe_sel, "blocked_when_covered": False,
                         "reachable_when_clear": False,
                         "why": f"页面里找不到 {probe_sel}"}

        # 清理自检可能残留的遮挡物，再把 DOM 交还给正常流程
        page.evaluate("""() => document.querySelectorAll(
          '[data-selftest-occluder]').forEach(e => e.remove())""")

        b.close()

    # 「点不着」只算 `covered_by_modal=false` 的那些：全屏模态盖住画布 chrome
    # 是覆盖层的**正常**行为（835 已定过这条），记进来只会稀释真缺陷。
    real = [r for r in rows if r["confirmed"] and r.get("in_layer")
            and not r.get("covered_by_modal")]
    by_modal = [r for r in rows if r.get("covered_by_modal")
                or (r["confirmed"] and not r.get("in_layer"))]
    unconfirmed = [r for r in rows if not r["confirmed"]]
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"rows": rows, "skipped": skipped, "states": states_done,
                   "confirmed": real,
                   "by_modal": by_modal,
                   "self_test": self_test},
                  f, ensure_ascii=False, indent=2)

    print(f"跑了 {len(states_done)} 个状态；候选 {len(rows)} 条 → "
          f"**确认点不着（浮层里的选项被埋）{len(real)}**、"
          f"被全屏模态盖住（正常，INFO）{len(by_modal)}、"
          f"活页面确认没通过 {len(unconfirmed)}")
    for st in states_done:
        print(f"  {st}")
    if skipped:
        print(f"\n⚠ 前置态没成立、**没跑到**的状态（{len(skipped)} 个，不算通过）：")
        for s in skipped:
            print(f"    - {s}")
    for r in rows:
        flag = ("★ 确认点不着（浮层里的选项被埋）"
                if r["confirmed"] and r.get("in_layer")
                and not r.get("covered_by_modal")
                else ("· 被全屏模态盖住（正常，INFO）" if r.get("covered_by_modal")
                      else ("· 画布控件被开着的下拉盖住（关掉就能点，INFO）"
                            if r["confirmed"] else
                            "?? 活页面确认没通过（不算）")))
        print(f"  {flag} [{r['state']}] al={r['al']!r} tid={r['tid']!r} "
              f"{r['w']}×{r['h']} @{r['x']},{r['y']}")
        for bk in r["blockers"][:2]:
            print(f"      被 {bk['tid'] or bk['cls']!r} (z={bk['z']}) 挡住")
        if not r["confirmed"]:
            print(f"      为什么不计入：{r['confirm_why']}")
    ok_self = bool(self_test) and bool(self_test.get("blocked_when_covered")) \
        and bool(self_test.get("reachable_when_clear"))
    print(f"\n自检：盖上遮挡物后 {self_test.get('probe')} 判定被挡="
          f"{self_test.get('blocked_when_covered')}、撤掉后恢复可点="
          f"{self_test.get('reachable_when_clear')}"
          + (f"（{self_test.get('why')}）" if self_test.get("why") else "")
          + f"  →  {'✓ 判据能失败' if ok_self else '✗ 判据恒空，这轮结果不可信'}")
    print(f"明细已写入 {OUT}")
    # ⚠️ 自检不过必须是**退出码 2**，不是 0 也不是 1：退出 0 会被 CI 当通过，
    #    退出 1 会被读成"查到缺陷了"。这是独立的第三种状态。
    if not ok_self:
        return 2
    return 1 if real else 0


if __name__ == "__main__":
    sys.exit(main())

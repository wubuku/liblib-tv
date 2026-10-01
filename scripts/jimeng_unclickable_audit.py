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
    kb_rows: list[dict] = []        # 键盘可达性（批 844 加）

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
        def open_dropdown(sel: str, want_tid: str | None = None,
                          scope: str = ".react-flow__node-toolbar") -> bool:
            # ⚠️ 这里**不能**先按 Escape 清场：第一版写了那么一句，结果把刚
            #    选中的节点取消了 → NodeToolbar 卸载 → 触发器根本不存在 →
            #    四个下拉状态**静默**没跑，输出只剩 4 个状态还"全绿"。
            #    835 之后下拉本来就互斥，直接点触发器即可。
            #
            # ⚠️ `want_tid` 的短路同样必需：层**已经开着**的时候再点一次触发器
            #    是把它**关掉**。截帧那步就栽在这 —— 下拉里找不到「首帧」，
            #    看着像"产品没有这一项"，其实是被自己刚点的那一下关掉了。
            if want_tid and page.locator(f'[data-testid="{want_tid}"]').count():
                return True
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
                        scope: str = ".react-flow__node-toolbar",
                        want_tid: str | None = None) -> None:
            """打开一个下拉再普查；**打不开要如实记 skipped，不许静默跳过**。

            「跑了但没看见」和「没跑」必须能被分开 —— 否则下拉那些状态从统计里
            消失，工具看上去覆盖了全站，其实一半没碰过。
            """
            if open_dropdown(sel, want_tid, scope):
                measure(tag)
            else:
                skipped.append(f"{tag}（打不开：{sel}）")

        # ── 下面三个 helper 是从浮层普查（§54 第二通道）搬过来的 ──
        #     批 840 在那边踩过的坑，这边不该再踩一遍。
        TID2TRIG = {
            # ⚠️ 前两条是批 840 补的：原来**缺**它们，于是 `close_open()` 从来
            #    关不掉视频节点那两个下拉 —— 开着的工具下拉会一路漏到后面某个
            #    状态，被当成那个状态的浮层记进去。**漏下去比漏报更坏**。
            "video-toolbar-capture-menu": "截取帧",
            "video-toolbar-tools-menu": "工具",
            "gen-model-listbox": "选择模型", "gen-video-size-listbox": "视频尺寸选项",
            "gen-mode-listbox": "生成模式", "gen-duration-listbox": "选择视频生成时长",
            "image-gen-model-listbox": "选择模型", "image-gen-size-listbox": "图片尺寸选项",
            "audio-gen-type-listbox": "创作类型", "audio-music-model-listbox": "选择模型",
            "audio-music-duration-listbox": "选择时长", "audio-voice-model-listbox": "选择模型",
            "audio-gen-mode-listbox": "音频生成", "audio-all-voices-listbox": "音色",
            "image-tools-menu": "工具", "text-bg-palette": "背景色",
        }

        def close_open() -> None:
            """把开着的下拉逐个点回它自己的触发器（toggle 关闭）。

            **不能用 Escape**：那会取消选中 → NodeToolbar 卸载 → 顺带把还没
            扫的浮层一起弄没了，判据会**假装**没查到。
            定位器要**同时**试 `aria-label` 和可见文案：视频工具条上那两枚
            （截取帧 / 工具）压根没有 aria-label，名字就在按钮文字里。
            """
            for tid, trig in TID2TRIG.items():
                if not page.locator(f'[data-testid="{tid}"]').count():
                    continue
                loc = page.locator(
                    f'.react-flow__node-toolbar button[aria-label^="{trig}"], '
                    f'.react-flow__node-toolbar button:text-is("{trig}")')
                if not loc.count():
                    continue
                try:
                    loc.first.click(timeout=4000)
                except Exception:
                    continue
                page.wait_for_timeout(300)

        def node_tids() -> list[str]:
            return page.evaluate(
                "() => [...document.querySelectorAll('.react-flow__node')]"
                ".map(n => n.getAttribute('data-testid'))")

        def insert(kind: str) -> str | None:
            """插入节点并返回新节点的 testid（按**集合差分**，不按序号）。

            ⚠️ 不能让异常冒出去：左栏按钮在开发期重编译时会短暂消失，
            一次 30s 超时会把**整份审计**带崩，前面所有状态的结果全丢。
            这里改成"等一小会儿，还不在就返回 None"，由调用方如实记账。
            """
            loc = page.locator(f'button[aria-label="{kind}"]')
            try:
                loc.first.wait_for(state="attached", timeout=8000)
            except Exception:
                return None
            before = set(node_tids())
            try:
                loc.first.click(timeout=8000)
            except Exception:
                return None
            page.wait_for_timeout(1800)
            new = [t for t in node_tids() if t not in before]
            return new[0] if new else None

        def open_layer() -> str:
            """当前是否有一个**浮层**开着？开着就返回它的 testid（没有就空串）。

            键盘判据只在这一步为真时才判：没有浮层的时候，"Tab 走不到里面"
            根本无从谈起（那不是浮层的责任）。
            判"开着"靠几何 + role 两路：既要脱离文档流，又要在 DOM 里靠后
            （后出现的盖住先出现的），并且**不是**画布自己的壳。
            """
            return page.evaluate("""() => {
              const SHELL = 'react-flow__renderer, react-flow__pane, '
                          + 'react-flow__viewport, react-flow__nodes, '
                          + 'react-flow__node, react-flow__node-toolbar';
              const LAYER = '.react-flow__node-panel, [role=menu], [role=listbox], '
                          + '[role=dialog], [role=popover], [data-testid$="-listbox"], '
                          + '[data-testid$="-menu"], [data-testid$="-panel"], '
                          + '[data-testid$="-palette"]';
              for (const e of document.querySelectorAll(LAYER)) {
                const s = getComputedStyle(e);
                if (s.display === 'none' || s.visibility === 'hidden') continue;
                const r = e.getBoundingClientRect();
                if (r.width < 40 || r.height < 20) continue;
                if (e.closest(SHELL)) continue;
                if (e.closest('nextjs-portal')) continue;
                const hasFocusable = e.querySelector(
                  'button,[href],input,select,textarea,[tabindex]:not([tabindex="-1"]),'
                  + '[role=menuitem],[role=option]');
                if (!hasFocusable) continue;
                return e.getAttribute('data-testid')
                    || e.getAttribute('aria-label') || e.getAttribute('role') || '?';
              }
              return '';
            }""")

        def keyboard_probe(layer_tid: str, max_tabs: int = 60) -> dict:
            """真按 Tab 键，最多 max_tabs 次，看焦点有没有落进当前那个浮层里。

            ⚠️ **必须用真键盘事件**（`page.keyboard.press("Tab")`），不能自己
               模拟焦点推进。第一版是模拟的：维护一份"可聚焦元素"表然后手动
               往后挪 —— 而那张表的 `button:not([disabled])` **不看
               `tabindex="-1"`**，于是把 `tabindex=-1` 的按钮也算成可 Tab 到。
               自检把层里的 tabindex 全摘成 -1，判据却仍然说"进得去"，
               **自检当场把工具判红了（退出码 2）**。这正是自检该干的事：
               自己把自己抓出来，好过让人拿着一份错结论去改产品。
            """
            if not layer_tid:
                return {"ok": None, "why": "没有打开的浮层"}
            if not page.locator(f'[data-testid="{layer_tid}"]').count():
                return {"ok": None, "why": "定位不到那个浮层"}
            page.evaluate("""() => { const a = document.activeElement;
                if (a && a.blur) a.blur(); return true; }""")
            covered = None
            covered_n = 0
            for i in range(1, max_tabs + 1):
                page.keyboard.press("Tab")
                step = page.evaluate("""(args) => {
                  const [tid] = args;
                  const layer = document.querySelector(`[data-testid="${tid}"]`);
                  const a = document.activeElement;
                  if (!a || a === document.body) return {state: 'body'};
                  const inside = !!(layer && layer.contains(a));
                  if (inside) return {state: 'inside'};
                  // ⚠️ 焦点停在**被这个浮层遮住**的控件上 —— 鼠标看不见无所谓，
                  //    可焦点环也看不见：用户不知道自己停在哪，继续 Tab 只是在
                  //    一片看不见的控件里走。这是"浮层开了却没接管焦点"，
                  //    和"浮层管好了自己的选项"是两回事。
                  const b = a.getBoundingClientRect();
                  if (b.width < 1 || b.height < 1) return {state: 'other'};
                  const hit = document.elementFromPoint(b.x + b.width/2,
                                                        b.y + b.height/2);
                  const occluded = !!(hit && !a.contains(hit) && !hit.contains(a)
                                      && !hit.closest('nextjs-portal'));
                  return {state: occluded ? 'covered' : 'other',
                          al: (a.getAttribute('aria-label')||'').trim().slice(0,30),
                          tid: a.getAttribute('data-testid') || '',
                          w: Math.round(b.width), h: Math.round(b.height)};
                }""", [layer_tid])
                if step.get("state") == "inside":
                    return {"ok": True, "tabs": i, "covered": covered,
                            "covered_n": covered_n}
                if step.get("state") == "covered":
                    covered_n += 1
                    if covered is None:
                        covered = {"at_tab": i, "al": step.get("al"),
                                   "tid": step.get("tid"),
                                   "size": f"{step.get('w')}x{step.get('h')}"}
            return {"ok": False, "tabs": max_tabs, "covered": covered,
                    "covered_n": covered_n,
                    "why": f"Tab {max_tabs} 次都没进到 {layer_tid} 里"}

        

        def measure(tag: str) -> None:
            """普查当前页面：找出所有**确认过**点不着的控件 + 键盘可达性。"""
            states_done.append(tag)
            # ── 键盘那一路先做：它要真的按 Tab，会改变焦点 ──────────
            #    放在指针普查**之后**会互相污染（Tab 之后 activeElement 变了，
            #    命中测试本身不受影响，但读起来容易误会），所以先跑键盘。
            ltid = open_layer()
            if ltid:
                kbd = keyboard_probe(ltid)
                kbd["layer"] = ltid
                kb_rows.append({"state": tag, **kbd})
                # ⚠️ 探完**必须把层收掉**。不收的话「截取帧下拉」会一路开着，
                #    后面三个状态的 `open_layer()` 认到的都是它 —— 键盘那一栏
                #    于是变成三个状态在报同一层。批 840 在浮层普查那边踩过同一个
                #    坑（TID2TRIG 缺两个条目），这边是同一个病的另一个发作点。
                close_open()
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
                  // ⚠️ 第三档（批 843 加）：**同一层里自己压自己**才是布局 bug。
                  //    跨层遮挡一律 INFO —— 一个菜单盖住画布右下角的会员浮窗，
                  //    用户关掉菜单就能点，那不是缺陷，是覆盖层的本职工作。
                  //    「控件的最近浮层祖先」与「遮挡物的最近浮层祖先」**相同**，
                  //    才是那种"这张菜单自己把自己盖住了"的毛病。
                  //    （批 835 那种**跨层**互斥问题由 835 自己的 verifier 判，
                  //    那条判据更重：它要求"两个下拉不该同时开着"。这里不重复。）
                  const layerEl = el.closest('[data-testid]');
                  const myLayer = layerEl
                    ? (layerEl.getAttribute('data-testid') || '') : '';
                  let sameLayer = false;
                  if (myLayer) {
                    for (const bk of blockers) {
                      const bo = [...document.querySelectorAll('[data-testid]')]
                        .find(e => e.getAttribute('data-testid') === myLayer);
                      if (!bo) continue;
                      // 遮挡物是否在**同一个** data-testid 层里
                      const probeEl = [...document.querySelectorAll('*')]
                        .find(e => e.getAttribute('role') === bk.role
                                  && (e.className || '').toString()
                                       === bk.cls);
                      if (probeEl && bo.contains(probeEl)) { sameLayer = true; break; }
                    }
                  }
                  out.push({tid: el.getAttribute('data-testid') || '',
                            al: (el.getAttribute('aria-label')||'').trim(),
                            txt: (el.innerText||'').trim().slice(0,24),
                            layer: myLayer,
                            same_layer: sameLayer,
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
            try_measure("视频工具条·截取帧下拉", 'button:has-text("截取帧")', ".react-flow__node-toolbar", "video-toolbar-capture-menu")
            try_measure("视频工具条·工具下拉", 'button:has-text("工具")', ".react-flow__node-toolbar", "video-toolbar-tools-menu")
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
                            ".react-flow__node-toolbar, .react-flow__node-panel",
                            {"模型": "gen-model-listbox", "尺寸": "gen-video-size-listbox",
                             "模式": "gen-mode-listbox", "时长": "gen-duration-listbox"}[tid])

        # ══ D. 文本节点：背景色调色板 ═════════════════════════════
        # 「背景色」只在**选中非编辑态**的工具条上（isVisible={selected && !editing}），
        # 所以先双进入编辑、再重新选中——顺序反了按钮压根不出现。
        txt = insert("文本")
        if not txt or not select_node(txt):
            skipped.append("文本·背景色调色板（插不出文本节点或选不中）")
        else:
            loc = page.locator(f'.react-flow__node[data-testid="{txt}"]')
            if loc.count():
                try:
                    loc.first.dblclick(timeout=8000)
                    page.wait_for_timeout(1100)
                except Exception:
                    pass
            sel2 = select_node(txt)
            if sel2 and open_dropdown('button[aria-label="背景色"]',
                                      "text-bg-palette"):
                measure("文本·背景色调色板")
            else:
                skipped.append("文本·背景色调色板（背景色按钮打不开）")

        # ══ E. 图片节点：截帧产出 → 它的工具菜单 ═════════════════
        # 带 poster 的图片节点**只能**靠「截取帧 → 首帧」产出：左栏新插的图片
        # 节点没有 poster，渲染的是生成面板而不是工具条（832 踩过）。
        sel_v = select_node("rf__node-video-local-1")
        if not sel_v or not open_dropdown('button:has-text("截取帧")',
                                          "video-toolbar-capture-menu"):
            skipped.append("图片工具条·工具菜单（截取帧下拉打不开）")
        else:
            it = page.locator('.react-flow__node-toolbar button:text-is("首帧")')
            if not it.count():
                skipped.append("图片工具条·工具菜单（截取帧下拉里没有「首帧」）")
            else:
                before = set(node_tids())
                it.first.click()
                page.wait_for_timeout(2200)
                new = [t for t in node_tids()
                       if t not in before and t and "image" in t]
                framed = new[0] if new else None
                if framed is None:
                    skipped.append("图片工具条·工具菜单（点了首帧没长出图片节点）")
                elif not select_node(framed):
                    skipped.append("图片工具条·工具菜单（选不中图片节点）")
                elif open_dropdown('button:has-text("工具")', "image-tools-menu"):
                    measure("图片工具条·工具菜单")
                else:
                    skipped.append("图片工具条·工具菜单（工具菜单打不开）")

        # ══ F. 音频生成面板（两个分支，共 5 个下拉）════════════════
        aud = insert("音频")
        if not aud:
            skipped.append("音频生成面板·（插不出音频节点）")
        else:
            for branch, expect in [
                ("音乐生成", [("选择模型", "audio-music-model-listbox", "音乐模型"),
                              ("选择时长", "audio-music-duration-listbox", "音乐时长")]),
                ("音频生成", [("选择模型", "audio-voice-model-listbox", "音色模型"),
                              ("音频生成", "audio-gen-mode-listbox", "音频生成模式"),
                              ("音色", "audio-all-voices-listbox", "全音色")]),
            ]:
                if select_node(aud) and open_dropdown(
                        'button[aria-label^="创作类型"]', "audio-gen-type-listbox"):
                    opt = page.locator(
                        '[data-testid="audio-gen-type-listbox"] [role=option]'
                        f':text-is("{branch}")')
                    if opt.count():
                        opt.first.click()
                        page.wait_for_timeout(900)
                for trig, tid, label in expect:
                    if select_node(aud):
                        try_measure(f"音频生成面板·{label}",
                                    f'button[aria-label^="{trig}"]',
                                    ".react-flow__node-toolbar, "
                                    ".react-flow__node-panel", tid)
                    else:
                        skipped.append(f"音频生成面板·{label}（选不中音频节点）")

        # 画布右键
        # ⚠️ 落点**必须先验证是空画布**。第一版硬点 (840,640)，而跑到这里时
        #    画布上已经插进了文本/音频节点，坐标落在**节点**上 ⇒ 开出来的是
        #    节点菜单，不是画布菜单。后果不是"少测一个状态"那么简单：那条
        #    finding 写的是「音色: 音色库」，而空画布菜单里**根本没有这一项**，
        #    看到的人会以为产品有个不存在的菜单项。**落点不成立就该记账，
        #    不该硬点。**
        close_open()
        page.keyboard.press("Escape")
        page.wait_for_timeout(400)
        spot = page.evaluate("""() => {
          for (const [x, y] of [[840,640],[700,700],[900,560],[600,800],[1000,760]]) {
            const t = document.elementFromPoint(x, y);
            if (t && t.closest('.react-flow__pane') && !t.closest('.react-flow__node'))
              return [x, y];
          }
          return null;
        }""")
        if spot:
            page.mouse.click(spot[0], spot[1], button="right")
            page.wait_for_timeout(800)
            if page.locator('[data-testid="canvas-context-menu"]').count():
                measure("画布右键菜单")
            else:
                skipped.append(f"画布右键菜单（@{spot[0]},{spot[1]} 点开了"
                               "但没出现 canvas-context-menu）")
        else:
            skipped.append("画布右键菜单（找不到确认是空画布的落点，"
                           "硬点会开成节点菜单）")
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)

        # 缩放菜单
        z = page.locator('[data-testid="canvas-zoom-percent"]')
        if z.count():
            z.first.click()
            page.wait_for_timeout(650)
        if page.locator('[data-testid="canvas-zoom-menu"]').count():
            measure("缩放菜单")
        else:
            skipped.append("缩放菜单（没出现）")
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)

        # ══ H. 顶栏 5 个浮层 ═════════════════════════════════════
        # testid 全部来自源码实测 —— 浮层普查第一版这四个是**凭印象猜的**，
        # 四个全错，四个状态白跑一轮。猜名字的代价是实打实的。
        for label, tid, name in [
            ("分享", "topbar-share-panel", "分享面板"),
            ("用户菜单", "canvas-user-menu", "账号菜单"),
            ("更多", "topbar-more-menu", "更多菜单"),
            ("搜索", "jimeng-search-overlay", "搜索"),
            ("生成历史", "topbar-history-menu", "生成历史"),
        ]:
            loc = page.locator(f'header[aria-label="Canvas top bar"] '
                               f'button[aria-label="{label}"]')
            if not loc.count():
                loc = page.locator(f'button[aria-label="{label}"]')
            if loc.count():
                try:
                    loc.first.click(timeout=6000)
                    page.wait_for_timeout(700)
                except Exception:
                    pass
            if page.locator(f'[data-testid="{tid}"]').count():
                measure(f"顶栏·{name}")
            else:
                skipped.append(f"顶栏·{name}（打开后没找到 {tid}）")
            page.keyboard.press("Escape")
            page.wait_for_timeout(450)

        # ── 自检：判据必须**能报出 1** ──────────────────────────────
        #     一个报 0 的工具，在证明自己之前什么都不是。第一版没有这一步，
        #     于是「0 个点不着」和「判据瞎了」在输出里长得一模一样。
        #     做法：在页面上**真的**盖一层不可点的遮挡物，复查那枚已知控件
        #     是不是被判成点不着；撤掉遮挡物，再复查它是不是恢复正常。
        #     两步都成立才算判据能失败；任一步不成立 → 退出码 2。
        probe_sel = 'button[aria-label="文本"]'
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)
        # ── 自检（批 844 加）：键盘判据也必须**能报出 1** ──────────
        #     做法和指针那条一模一样：在真页面上制造一个走不到的状态，
        #     复查工具确实判成"Tab 进不去"，撤掉后再复查恢复。
        #     没有这一步，"24 个状态键盘都进得去"和"判据根本不看键盘"
        #     在输出里长得一模一样。
        kb_self: dict = {}
        probe_layer = "video-toolbar-capture-menu"
        # ⚠️ 必须**先选中视频节点**：跑到自检这一步时画布上没有任何选中，
        #    NodeToolbar 整个没挂载，触发器压根不存在。第一版直接开，
        #    自检那一层打不开（skipped 记着），而因为自检只看 `kb_self` 里的
        #    `why` 字段，很容易被当成"工具坏了"而不是"前置态没成立"。
        if (select_node("rf__node-video-local-1")
                and open_dropdown('button:has-text("截取帧")', probe_layer,
                                  ".react-flow__node-toolbar")
                and page.locator(f'[data-testid="{probe_layer}"]').count()):
            before_kb = keyboard_probe(probe_layer)
            # 把层里所有可聚焦元素的 tabindex 摘成 -1 ⇒ 走不进去
            page.evaluate("""(tid) => {
              const el = document.querySelector(`[data-testid="${tid}"]`);
              if (!el) return;
              el.querySelectorAll('a[href],button,input,select,textarea,[tabindex]')
                .forEach(e => e.setAttribute('data-kb-prev',
                                            e.getAttribute('tabindex') || ''));
              el.querySelectorAll('button,input,select,textarea,[tabindex]')
                .forEach(e => e.setAttribute('tabindex', '-1'));
            }""", probe_layer)
            page.wait_for_timeout(300)
            after_kb = keyboard_probe(probe_layer)
            page.evaluate("""() => document.querySelectorAll('[data-kb-prev]')
                .forEach(e => { const v = e.getAttribute('data-kb-prev');
                  if (v) e.setAttribute('tabindex', v);
                  else e.removeAttribute('tabindex');
                  e.removeAttribute('data-kb-prev'); })""")
            page.wait_for_timeout(300)
            restored_kb = keyboard_probe(probe_layer)
            # 再验「Tab 走进被遮住的控件」这一条：盖一层**真遮挡物**，
            # 判据必须报出 covered；撤掉后必须不再报。
            # ⚠️ 这条**不能用上面那层**：截取帧下拉第 1 次 Tab 就进去了，
            #    探针当场返回，压根没机会走到被遮住的控件上 —— 自检于是恒假。
            #    换成一个**深**的层（顶栏搜索，实测 39 步），前面 38 个焦点位
            #    足够让探针看见遮挡。第一版就是栽在这儿，自检把自己判红了。
            deep_layer = "jimeng-search-overlay"
            page.keyboard.press("Escape")
            page.wait_for_timeout(400)
            srch = page.locator('header[aria-label="Canvas top bar"] '
                                'button[aria-label="搜索"]')
            if not srch.count():
                srch = page.locator('button[aria-label="搜索"]')
            if srch.count() and page.locator(
                    f'[data-testid="{deep_layer}"]').count() == 0:
                try:
                    srch.first.click(timeout=6000)
                    page.wait_for_timeout(700)
                except Exception:
                    pass
            if page.locator(f'[data-testid="{deep_layer}"]').count():
                page.evaluate("""() => {
                  const d = document.createElement('div');
                  d.setAttribute('data-kbcover-probe', '1');
                  d.style.cssText = 'position:fixed;inset:0;z-index:99998;'
                                  + 'background:transparent';
                  document.body.appendChild(d);
                }""")
                page.wait_for_timeout(300)
                covered_when_shut = keyboard_probe(deep_layer)
                page.evaluate("""() => document.querySelectorAll('[data-kbcover-probe]')
                    .forEach(e => e.remove())""")
                page.wait_for_timeout(300)
                covered_when_clear = keyboard_probe(deep_layer)
            else:
                covered_when_shut = {"covered": None}
                covered_when_clear = {"covered": None}
            page.keyboard.press("Escape")
            page.wait_for_timeout(400)
            kb_self = {"layer": probe_layer,
                       "reachable_before": before_kb.get("ok"),
                       "unreachable_when_stripped": after_kb.get("ok") is False,
                       "reachable_after_restore": restored_kb.get("ok"),
                       "covered_probe_layer": deep_layer,
                       "covered_n_when_shut": covered_when_shut.get("covered_n"),
                       "covered_n_when_clear": covered_when_clear.get("covered_n")}
        else:
            kb_self = {"layer": probe_layer, "why": "自检用的那层没打开"}
        close_open()
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
    real = [r for r in rows if r["confirmed"] and r.get("same_layer")
            and not r.get("covered_by_modal")]
    by_modal = [r for r in rows if r.get("covered_by_modal")
                or (r["confirmed"] and not r.get("same_layer"))]
    unconfirmed = [r for r in rows if not r["confirmed"]]
    # 键盘那一路：`ok is False` 才是缺陷；`ok is None` 是"那一刻没有打开的
    # 浮层"，**不计也不当通过** —— 与指针那条 skipped/empty 的分档同一个道理。
    kb_bad = [r for r in kb_rows if r.get("ok") is False]
    # 「Tab 走进了被这个浮层遮住的控件」—— 第三个键盘缺陷桶。
    # 与指针那条的**分档正好相反**：鼠标点不到被模态盖住的控件是**正常**
    # （关掉模态就能点）；但**焦点**停在那上面，焦点环是看不见的，用户既不知道
    # 自己在哪也不知道刚才那下 Tab 有没有生效 —— 那不是正常，是浮层没接管焦点。
    kb_covered = [r for r in kb_rows if r.get("covered")]
    # 「进得去但很深」单列。**上限本身就是判据的一部分**：探到上限还没进去，
    # 报「缺陷」是在说"产品坏了"，可那也可能只是这条浮层在 tab 序里太靠后。
    # 上限以内 + 偏深 = INFO（值得人看一眼的信号），上限以外才判缺陷。
    DEEP = 30
    kb_deep = [r for r in kb_rows if r.get("ok")
               and (r.get("tabs") or 0) > DEEP]
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"rows": rows, "skipped": skipped, "states": states_done,
                   "confirmed": real,
                   "by_modal": by_modal,
                   "keyboard": kb_rows,
                   "keyboard_bad": kb_bad,
                   "keyboard_covered": kb_covered,
                   "keyboard_deep": kb_deep,
                   "keyboard_deep_threshold": DEEP,
                   "self_test": self_test,
                   "kb_self_test": kb_self},
                  f, ensure_ascii=False, indent=2)

    print(f"跑了 {len(states_done)} 个状态；候选 {len(rows)} 条 → "
          f"**确认点不着（同一层自己压自己）{len(real)}**、"
          f"被全屏模态盖住（正常，INFO）{len(by_modal)}、"
          f"活页面确认没通过 {len(unconfirmed)}")
    for st in states_done:
        print(f"  {st}")
    if skipped:
        print(f"\n⚠ 前置态没成立、**没跑到**的状态（{len(skipped)} 个，不算通过）：")
        for s in skipped:
            print(f"    - {s}")
    for r in rows:
        flag = ("★ 确认点不着（**同一层**自己压自己）"
                if r["confirmed"] and r.get("same_layer")
                and not r.get("covered_by_modal")
                else ("· 被全屏模态盖住（正常，INFO）" if r.get("covered_by_modal")
                      else ("· 被**另一层**盖住（关掉那层就能点，INFO）"
                            if r["confirmed"] else
                            "?? 活页面确认没通过（不算）")))
        print(f"  {flag} [{r['state']}] al={r['al']!r} tid={r['tid']!r} "
              f"层={r.get('layer') or '(无)'} {r['w']}×{r['h']} "
              f"@{r['x']},{r['y']}")
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

    # ── 键盘可达性（批 844 加）────────────────────────────────────
    # `ok is None` 是"那一刻没有打开的浮层" —— **不计也不当通过**，与指针那条
    # skipped / empty 分档同一个道理。混进"通过"里就是又一次恒空判据。
    kb_probed = [k for k in kb_rows if k.get("ok") is not None]
    kb_none = [k for k in kb_rows if k.get("ok") is None]
    print(f"\n键盘可达性：探测 {len(kb_probed)} 个开着浮层的状态 → "
          f"**Tab 进不去 {len(kb_bad)}**、"
          f"**Tab 走进被遮住的控件 {len(kb_covered)}**、"
          f"偏深 {len(kb_deep)}（>{DEEP} 次，INFO）、没浮层可探 {len(kb_none)}")
    for k in kb_bad:
        print(f"  ★ Tab 进不去 [{k['state']}] 浮层={k['layer']!r} {k.get('why','')}")
    for k in kb_covered:
        c = k["covered"]
        print(f"  ★ Tab 走进了**被遮住**的控件 [{k['state']}] 浮层={k['layer']!r}："
              f"第 {c['at_tab']} 次 Tab 停在 al={c['al']!r} tid={c['tid']!r} "
              f"{c['size']} —— 焦点环在那儿是看不见的"
              f"（全程共 {k.get('covered_n')} 个这样的焦点位）")
    for k in kb_deep:
        print(f"  · 偏深（INFO）[{k['state']}] 浮层={k['layer']!r} "
              f"Tab {k['tabs']} 次才进得去 —— 不是缺陷，但是个该人看一眼的信号")
    for k in kb_probed:
        if k.get("ok") and (k.get("tabs") or 0) <= DEEP:
            print(f"  · [{k['state']}] 浮层={k['layer']!r} Tab {k['tabs']} 次进得去")
    ok_kb_self = (bool(kb_self) and kb_self.get("reachable_before") is True
                  and kb_self.get("unreachable_when_stripped") is True
                  and kb_self.get("reachable_after_restore") is True
                  # ⚠️ 这里比的是**计数**，不是"有没有"：基线里本来就真有几处
                  #    焦点落在被遮住的控件上（那正是本批查出来的缺陷），
                  #    所以"撤掉后不再报"是个**错前提** —— 第一版就栽在这儿，
                  #    自检把自己判红了。真正要证明的是判据**对遮挡敏感**：
                  #    盖上一层，被遮住的焦点位必须**变多**。
                  and (kb_self.get("covered_n_when_shut") or 0)
                      > (kb_self.get("covered_n_when_clear") or 0))
    print(f"自检（键盘）：把 {kb_self.get('layer')!r} 里的 tabindex 全摘成 -1 后"
          f"判为进不去={kb_self.get('unreachable_when_stripped')}、"
          f"还原后恢复={kb_self.get('reachable_after_restore')}"
          + f"；盖一层遮挡物后被遮住的焦点位 "
          f"{kb_self.get('covered_n_when_clear')} → {kb_self.get('covered_n_when_shut')}"
          + (f"（{kb_self.get('why')}）" if kb_self.get("why") else "")
          + f"  →  {'✓ 键盘判据能失败' if ok_kb_self else '✗ 键盘判据恒真，这轮结果不可信'}")

    print(f"明细已写入 {OUT}")
    # ⚠️ 自检不过必须是**退出码 2**，不是 0 也不是 1：退出 0 会被 CI 当通过，
    #    退出 1 会被读成"查到缺陷了"。这是独立的第三种状态。
    if not ok_self or not ok_kb_self:
        return 2
    return 1 if (real or kb_bad or kb_covered) else 0


if __name__ == "__main__":
    sys.exit(main())

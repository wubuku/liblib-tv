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
    # 「这个状态本来就没有浮层」的名单。名单外跑到 `open_layer()` 返回空
    # ⇒ 脚本没把层点开（批 849 那个逗号 bug 就是这么藏起来的）。
    NO_LAYER_EXPECTED = {"空态", "视频工具条", "视频生成面板"}
    kb_no_layer: list[dict] = []
    kb_leaks: list[dict] = []      # 探完**关不掉**的层（会漏到后面所有状态）

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
        def _scoped(scope: str, sel: str) -> str:
            """把 `sel` 挂到 `scope` 的**每一项**下面。

            ⚠️⚠️ 批 849 的根因就在这里。第一版是把 `scope` 和 `sel` 直接用
            一个空格接起来（`scope` 整体 + " " + `sel`，不展开），而调用方
            传进来的 scope 是逗号列表：

                scope = ".react-flow__node-toolbar, .react-flow__node-panel"
                接起来 == ".react-flow__node-toolbar, .react-flow__node-panel button[…]"

            CSS 选择器里逗号的优先级**高于**后代空格，整条被读成
            「**工具条 div 自己** 或 **面板里的按钮**」。`.first` 命中的是
            **那个 div** —— 点了个寂寞，层压根没开。

            后果比报错更坏：`open_dropdown` 只看 `loc.count()`，那个 div
            确实存在（非 0）⇒ 返回 True ⇒ `measure()` 照跑、指针普查照跑
            （那些是真数据），但**键盘那一栏因为没有层而整条空白**。
            24 个状态里于是有 9 个「跑了却没开层」，看上去是覆盖面够了，
            实际键盘只探到 12 层。**判据没坏，脚本自己把层点丢了。**
            """
            parts = [s.strip() for s in (scope or "").split(",") if s.strip()]
            if not parts:
                return sel
            return ", ".join(f"{p} {sel}" for p in parts)

        def open_dropdown(sel: str, want_tid: str | None = None,
                          scope: str = ".react-flow__node-toolbar") -> bool:
            # ⚠️ 这里**不能**先按 Escape 清场：第一版写了那么一句，结果把刚
            #    选中的节点取消了 → NodeToolbar 卸载 → 触发器根本不存在 →
            #    四个下拉状态**静默**没跑，输出只剩 4 个状态还"全绿"。
            #    835 之后下拉本来就互斥，直接点触发器即可。
            #
            # ⚠️ `want_tid` 的短路同样必需：层**已经开着**的时候再点一下触发器
            #    是把它**关掉**。截帧那步就栽在这 —— 下拉里找不到「首帧」，
            #    看着像"产品没有这一项"，其实是被自己刚点的那一下关掉了。
            if want_tid and page.locator(f'[data-testid="{want_tid}"]').count():
                return True
            loc = page.locator(_scoped(scope, sel))
            if not loc.count():
                return False
            try:
                loc.first.click(timeout=8000)
            except Exception:
                return False
            page.wait_for_timeout(700)
            # ⚠️ 批 849 加的：**点了不等于开了**。`loc.count()` 只能说
            #    「找得到元素」，说不了「那个元素是被点到的那个」。上面那个
            #    逗号 bug 正是靠这一条才暴露的 —— 只有点完再回查 `want_tid`，
            #    「点了 div 本身」才会被记成「打不开」（进 skipped，有账），
            #    而不是悄悄留下一个没有层的状态（没账）。
            if want_tid and not page.locator(f'[data-testid="{want_tid}"]').count():
                return False
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

        # 清场时用的 scope。⚠️⚠️ 批 849：**必须**和打开时用的一致。
        #    原来只写 `.react-flow__node-toolbar`，于是 4 个生成面板下拉
        #    （触发器在 `.react-flow__node.selected` 里）压根**关不掉** ——
        #    一路漏到后面所有状态：`open_layer()` 认层时按文档顺序返回第一个，
        #    漏下去的 listbox 跟真层抢；更毒的是 Tab 序列被它们的按钮占满，
        #    「画布右键菜单」于是从 0 缺陷变成「Tab 60 次都进不去」。
        #    840 记过一次「漏下去比漏报更坏」，这次是同一个病的另一个发作点
        #    —— 根子还是**打开和清场用了两套 scope**。
        CLOSE_SCOPE = (".react-flow__node-toolbar, .react-flow__node-panel, "
                       ".react-flow__node.selected")

        def close_open() -> list[str]:
            """把开着的下拉逐个点回它自己的触发器（toggle 关闭）。

            **不能用 Escape**：那会取消选中 → NodeToolbar 卸载 → 顺带把还没
            扫的浮层一起弄没了，判据会**假装**没查到。
            定位器要**同时**试 `aria-label` 和可见文案：视频工具条上那两枚
            （截取帧 / 工具）压根没有 aria-label，名字就在按钮文字里。

            返回**没关掉的** tid 列表 —— 漏下去的层会让后面每个状态都在报
            同一层，而不报「这里漏了」，所以必须显式交出去（批 849）。
            """
            stuck: list[str] = []
            for tid, trig in TID2TRIG.items():
                if not page.locator(f'[data-testid="{tid}"]').count():
                    continue
                loc = page.locator(
                    _scoped(CLOSE_SCOPE, f'button[aria-label^="{trig}"]')
                    + ", "
                    + _scoped(CLOSE_SCOPE, f'button:text-is("{trig}")'))
                if not loc.count():
                    stuck.append(tid)
                    continue
                try:
                    loc.first.click(timeout=4000)
                except Exception:
                    stuck.append(tid)
                    continue
                page.wait_for_timeout(300)
                if page.locator(f'[data-testid="{tid}"]').count():
                    stuck.append(tid)
            return stuck

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

        def escape_probe(layer_tid: str, max_n: int = 6) -> dict:
            """焦点**已经在层里**的时候，连按 Tab 看会不会跑出去。

            问的是**焦点陷阱**：模态/菜单这类浮层，键盘 Tab 本该在层内循环
            （ARIA dialog / menu 的标准做法）。跑出去意味着用户按了几下 Tab
            之后焦点到了层外 —— 轻则离开了这个浮层（Esc 都关不掉它了），
            重则落到被遮住的地方（§63 量的就是那个）。

            ⚠️ 这一条**不许**自己拿"跑出去=缺陷"下结论 —— 得先看源站是不是
            也跑出去。源站也那样就是源站的取舍，不是复刻的缺陷（不许擅自
            改进源站）。所以这里只**测量**，分档由源站对照结果决定。
            """
            esc_at = None
            landed = None
            steps = 0
            for i in range(1, max_n + 1):
                page.keyboard.press("Tab")
                steps = i
                s = page.evaluate("""(tid) => {
                  const layer = document.querySelector(`[data-testid="${tid}"]`);
                  const a = document.activeElement;
                  if (!a || a === document.body) return {state: 'body'};
                  if (layer && layer.contains(a)) return {state: 'inside'};
                  const b = a.getBoundingClientRect();
                  return {state: 'outside',
                          al: (a.getAttribute('aria-label')||'').trim().slice(0,30),
                          tid: a.getAttribute('data-testid') || '',
                          txt: (a.innerText || a.getAttribute('placeholder')||'')
                                .trim().replace(/\\s+/g,' ').slice(0,20),
                          size: Math.round(b.width) + 'x' + Math.round(b.height)};
                }""", layer_tid)
                if s.get("state") != "inside":
                    esc_at = i
                    landed = {k: s.get(k) for k in ("state", "al", "tid",
                                                    "txt", "size")}
                    break
            return {"pressed": steps, "escaped_at": esc_at,
                    "landed": landed,
                    "trapped": esc_at is None,
                    "why": None if esc_at is None
                           else f"焦点在层里时按 {esc_at} 次 Tab 跑出去了"}

        def refocus_inside(layer_tid: str) -> bool:
            """把焦点塞回层内（上一个测量是破坏性的，会把焦点赶出去）。"""
            ok = page.evaluate("""(tid) => {
              const layer = document.querySelector(`[data-testid="${tid}"]`);
              if (!layer) return false;
              if (layer.contains(document.activeElement)) return true;
              const it = layer.querySelector(
                'input,button,a[href],select,textarea,[tabindex]');
              if (it) { it.focus(); return true; }
              if (layer.focus) { layer.focus(); return true; }
              return false;
            }""", layer_tid)
            page.wait_for_timeout(200)
            return bool(ok)

        def arrow_probe(layer_tid: str, key: str = "ArrowDown",
                        max_n: int = 4) -> dict:
            """层内按方向键，焦点**在层内移动**吗？移出去过吗？

            源站实测（探针 846b）：右键菜单 ArrowDown/ArrowUp **在层内移动并
            环绕**（新建节点→粘贴→重做→撤销→回新建节点）—— 那是 ARIA menu
            的漫游 tabindex + 方向键标准做法，**方向键才是菜单的主路径**，Tab
            是旁路。搜索面板（不是菜单）方向键**不消费**。所以"方向键动不动"
            不是一条统一判据，得**按层型**看：菜单该动，dialog 不该动。
            这里只**测量**层型事实，分档由源站对照表决定。
            """
            if not refocus_inside(layer_tid):
                return {"why": "焦点塞不回层里（前置态没成立）"}
            seq = []
            for _ in range(max_n):
                page.keyboard.press(key)
                s = page.evaluate("""(tid) => {
                  const layer = document.querySelector(`[data-testid="${tid}"]`);
                  const a = document.activeElement;
                  if (!a || a === document.body) return {who: 'body'};
                  return {who: (a.getAttribute('aria-label')
                              || a.getAttribute('data-testid')
                              || (a.innerText || '')
                                  .trim().replace(/\\s+/g, ' ').slice(0, 14)
                              || a.tagName),
                          in: !!(layer && layer.contains(a))};
                }""", layer_tid)
                seq.append(s)
            uniq = len({s.get("who") for s in seq})
            return {"key": key, "seq": seq, "moved": uniq > 1,
                    "stayed_in_layer": all(s.get("in") for s in seq),
                    "first": (seq[0].get("who") if seq else None)}

        # ⚠️⚠️ 批 849：上限从 60 提到 120。实测 `canvas-context-menu` 冷启动
        #    要 **39 次** Tab 才进得去（轨迹见 keyboard[].trace）—— 846 已经
        #    让它开层即接管焦点了，但**冷启动口径**仍要从头走一遍全文档。
        #    上限 60 时余量只有 21 次：画布上多一个节点、多一个没关掉的层，
        #    就顶满 ⇒ 判据把「上限不够」报成「Tab 进不去」。
        #    849 为这一条查了四轮才定位：同名层混淆 ✗、层泄漏 ✗、上限本身 ✗
        #    （独立复现插了节点也只要 37 次）—— **它是 flaky**，而判据把
        #    偶发当确定报了出去。查不出来就先把上限拉开、把措辞改准，
        #    别把一个说不清的东西写成产品缺陷。
        def keyboard_probe(layer_tid: str, max_tabs: int = 120) -> dict:
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
            # ── 开层**那一瞬间**焦点在不在层里（blur 之前先读）──────────
            #    冷启动口径（blur + 按 Tab）量的是"从零开始要按几次才进得去"，
            #    而用户真正的路径是"点开 → 焦点本来就该在里面"。这是**两件事**：
            #    打开时没接管（初始焦点）vs 接管了又放出去（焦点陷阱），修法完全
            #    不同。只报 covered_n 不够 —— 那只说"焦点停在了看不见的地方"，
            #    说不清是哪一种。不读这一下，finding 就只有现象没有病因。
            at_open = page.evaluate("""(tid) => {
              const layer = document.querySelector(`[data-testid="${tid}"]`);
              const a = document.activeElement;
              if (!a || a === document.body)
                return {state: 'body', inside: false};
              return {state: (layer && layer.contains(a)) ? 'inside' : 'other',
                      inside: !!(layer && layer.contains(a)),
                      al: (a.getAttribute('aria-label') || '').trim().slice(0, 30),
                      tid: a.getAttribute('data-testid') || '',
                      txt: (a.innerText || a.getAttribute('placeholder') || '')
                            .trim().replace(/\\s+/g, ' ').slice(0, 24)};
            }""", layer_tid)
            page.evaluate("""() => { const a = document.activeElement;
                if (a && a.blur) a.blur(); return true; }""")
            covered = None
            covered_n = 0
            skin_top_n = 0
            # ⚠️⚠️ 批 849 加的：**失败时把 Tab 轨迹一起交出来**。
            #    只交一个 `ok: False` 等于交一张没有地址的病历 —— 「进不去」
            #    有太多种进不去（上限不够 / 焦点被别的东西吃了 / 层不可聚焦 /
            #    压根量错了对象），而判据把它们**压成同一个词**。
            #    849 为这一条查了四轮：① 怀疑同名层混淆（querySelector 只取
            #    第一个）② 怀疑下拉层泄漏污染 Tab 序列 ③ 怀疑 max_tabs=60
            #    不够 —— 三次都被独立复现证伪。**与其第四次猜，不如让判据
            #    自己说**。这也是「布尔判据要配一条看轨迹的断言」的又一次
            #    应验：轨迹是判据自己的责任，不是排查者的额外工作。
            trace: list[str] = []
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
                  // ⚠️⚠️⚠️ 这条判据被证伪过**三次**，三次错法都不同，而根因是
                  //    我一直在问错问题。留着全部记录，免得下一个人"简化"回去：
                  //
                  //    第 1 版 `elementFromPoint` + DOM 包含：**太松**。只返回
                  //      栈顶一个元素；它若是焦点自己的**后代**，`hit.contains(a)`
                  //      为假而 `a.contains(hit)` 为真 ⇒ 判成"被遮"。批 843 的
                  //      「音色: 音色库」假缺陷就是这么来的。
                  //    第 2 版 `elementsFromPoint` 栈顶非自己非后代：**太严**。
                  //      源站节点内容是 **portal 渲染**的（探针 845c 实测：栈顶
                  //      `text-flow-node-full` 与焦点所在的 `rf__node-xxx`
                  //      **不同支**却同框）—— 那层就是节点自己的皮。
                  //    第 3 版「栈顶是不是**另一个浮层**」（比浮层锚）：**两个
                  //      错**。① `nextjs-portal` 那个 div 自己是栈顶时，它只是
                  //      结构容器、**什么都不画**，却被判成盖住了（自检里第 1 个
                  //      被遮就是它）；② 比"最近的 testid 祖先"时，控件的锚是
                  //      它**自己**、皮的锚是它**所在的容器**，两个 testid 必然
                  //      不同 ⇒ 自己的皮被判成另一个浮层。
                  //    三次都在回答"栈顶是不是外人"，可真正的问题是**焦点环
                  //    还在不在**。焦点环画在控件的**边框**上，所以：
                  //      · 该测**边框那一圈**，不是中心（不透明子元素永远盖住
                  //        中心，拿中心测必然误报）；
                  //      · 盖住它的东西必须**不透明** —— 透明的东西什么也盖不住，
                  //        皮和 portal 容器都是这一类；
                  //      · 祖先的背景画在**下面**，不算遮挡。
                  //    四条边中点（外扩 1px）全被不透明的外人盖住 ⇒ 焦点环
                  //    等于没了，判缺陷；只盖住一部分 ⇒ 焦点环还看得见，记 INFO。
                  const ANCHOR = /(dialog|menu|listbox|popover|alertdialog)/i;
                  const nameOf = (e) => (e ? (e.tagName + '/'
                      + (e.getAttribute('data-testid') || e.getAttribute('aria-label')
                         || (e.className || '').toString()
                              .replace(/\\s+/g, ' ').slice(0, 40))
                      || (e.innerText || '').trim().slice(0, 14)) : null);
                  // 从 e 往上找有没有不透明底；一旦走到 a 的祖先就停（那画在下面）
                  const paintsOver = (e, a) => {
                    for (let n = e; n && n !== document.body;
                         n = n.parentElement) {
                      if (n === a || (n.contains && n.contains(a))) return false;
                      const bg = getComputedStyle(n).backgroundColor || '';
                      if (bg !== 'rgba(0, 0, 0, 0)'
                          && !bg.startsWith('rgba(0, 0, 0, 0)')) return true;
                    }
                    return false;
                  };
                  const EDGE = [[b.left - 1, b.top + b.height / 2],
                                [b.right + 1, b.top + b.height / 2],
                                [b.x + b.width / 2, b.top - 1],
                                [b.x + b.width / 2, b.bottom + 1]];
                  let edges = 0, firstTop = null, firstName = null;
                  let skinTop = false;
                  for (const [ex, ey] of EDGE) {
                    const st = document.elementsFromPoint(ex, ey) || [];
                    const t = st[0] || null;
                    if (!t) continue;
                    if (t.getAttribute && t.getAttribute('data-kbskin-probe'))
                      skinTop = true;   // 皮当过栈顶（自检要拿它自证夹具在局）
                    if (t === a || a.contains(t) || (t.contains && t.contains(a)))
                      continue;                      // 自己/后代/祖先 ⇒ 没被盖
                    if (!paintsOver(t, a)) continue;   // 透明 ⇒ 什么也盖不住
                    edges += 1;
                    if (firstTop === null) {
                      firstTop = t;
                      firstName = nameOf(t);
                    }
                  }
                  const ANCHOR_R = (e) => {
                    for (let n = e; n && n !== document.body;
                         n = n.parentElement) {
                      const tid = n.getAttribute && n.getAttribute('data-testid');
                      const role = n.getAttribute && n.getAttribute('role');
                      if (tid) return 'tid:' + tid;
                      if (role && ANCHOR.test(role)) return 'role:' + role;
                    }
                    return null;
                  };
                  const occluded = edges === EDGE.length;
                  return {state: occluded ? 'covered' : 'other',
                          edges_covered: edges, edges_total: EDGE.length,
                          skin_top: skinTop,
                          top: firstName,
                          top_anchor: firstTop ? ANCHOR_R(firstTop) : null,
                          focus_anchor: ANCHOR_R(a),
                          al: (a.getAttribute('aria-label')||'').trim().slice(0,30),
                          tid: a.getAttribute('data-testid') || '',
                          txt: (a.innerText || a.getAttribute('placeholder') || '')
                                .trim().replace(/\\s+/g,' ').slice(0,20),
                          w: Math.round(b.width), h: Math.round(b.height)};
                }""", [layer_tid])
                if len(trace) < 24:
                    _a = step
                    trace.append(
                        f"{i}:{step.get('state')}"
                        f":al={_a.get('al') or '-'}"
                        f":tid={_a.get('tid') or '-'}"
                        f":txt={(_a.get('txt') or '-')[:12]}")
                if step.get("state") == "inside":
                    # 焦点**已经在层里**了 —— 正好就是「用户刚 Tab 进来」那一刻。
                    # 就在这个状态上问「再按 Tab 会不会跑出去」，零准备，且测的
                    # 正是真实路径。§63 留下的范围限制就是这条：冷启动量的是
                    # 「找不找得到层」，量不到「进去之后出不出得来」。
                    esc = escape_probe(layer_tid)
                    # ⚠️ 上一个测量是**破坏性**的（焦点已经被赶出层），下一个
                    #    测量必须**重新把焦点塞回层里**再起手 —— 三个破坏性
                    #    测量串着跑，只有第一个是准的（源站探针 846 第一轮
                    #    就栽在这儿，方向键和 Esc 两栏全测在层外）。
                    arr = arrow_probe(layer_tid, "ArrowDown")
                    arr_up = arrow_probe(layer_tid, "ArrowUp")
                    refocus_inside(layer_tid)
                    return {"ok": True, "tabs": i, "covered": covered,
                            "covered_n": covered_n, "skin_top_n": skin_top_n,
                            "focus_at_open": at_open, "trace": trace,
                            "escape": esc, "arrow_down": arr,
                            "arrow_up": arr_up}
                if step.get("skin_top"):
                    # 「皮当过栈顶」几次 —— 反向自检的**自证**：皮要是从来没落到
                    # 栈顶上过，那条"盖了皮也不多报"就是恒真的空话。
                    skin_top_n += 1
                if step.get("state") == "covered":
                    covered_n += 1
                    if covered is None:
                        covered = {"at_tab": i, "al": step.get("al"),
                                   "tid": step.get("tid"),
                                   "top": step.get("top"),
                                   "top_anchor": step.get("top_anchor"),
                                   "focus_anchor": step.get("focus_anchor"),
                                   "edges": f"{step.get('edges_covered')}"
                                            f"/{step.get('edges_total')}",
                                   "size": f"{step.get('w')}x{step.get('h')}"}
            # ⚠️ 措辞要说准：「用了满 {max_tabs} 次上限还没走到」和
            #    「怎么按都进不去」是**两件事**，第一版都写成前者的语气
            #    却当成后者报缺陷，844-848 五轮 0 缺陷的层就这么被冤枉过一次。
            #    轨迹摆在 trace 里，看的人能自己判是哪一种。
            return {"ok": False, "tabs": max_tabs, "covered": covered,
                    "covered_n": covered_n, "skin_top_n": skin_top_n,
                    "focus_at_open": at_open, "trace": trace,
                    "capped": True,
                    "why": f"按满 {max_tabs} 次 Tab 上限仍未进到 {layer_tid} 里"
                           f"（是上限不够还是真进不去，看 trace）"}

        

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
                # ⚠️ 探完**必须把层收掉**。不收的话「截取帧下拉」会一路���着，
                #    后面三个状态的 `open_layer()` 认到的都是它 —— 键盘那一栏
                #    于是变成三个状态在报同一层。批 840 在浮层普查那边踩过同一个
                #    坑（TID2TRIG 缺两个条目），这边是同一个病的另一个发作点。
                #    批 849 又踩了一次：清场的 scope 和打开的不一致 ⇒ 4 个
                #    生成面板下拉关不掉 ⇒ 漏到「画布右键菜单」把它的 Tab
                #    序列占满，凭空造出一条「Tab 进不去」。收不掉的必须报出来。
                stuck = close_open()
                if stuck:
                    kb_leaks.append({"state": tag, "stuck": stuck})
            else:
                # ⚠️⚠️ 批 849 加的：**「没认到层」必须留痕**。第一版这里
                #    什么都不记，于是「跑了但层没开」和「这个状态本来就没有
                #    浮层」在结果里**长得一模一样** —— 都表现为「这个状态
                #    不在 keyboard 那一栏」。24 个状态里 9 个是这么消失的，
                #    而 `states` 数出来还是 24，看上去覆盖面一点没少。
                #
                #    `NO_LAYER_EXPECTED` 是「本来就没有浮层」的名单：空画布、
                #    工具条本体、面板本体。名单外的状态跑到这里 ⇒ 层该开
                #    没开 ⇒ 判据没问题，是**脚本没把层点开**（逗号拼接那个
                #    bug 就是这么藏了三个星期的）。三种状态从此各归各的账。
                kb_no_layer.append({
                    "state": tag,
                    "expected": tag in NO_LAYER_EXPECTED,
                    "why": ("这个状态本来就没有浮层（画布壳 / 工具条本体 / "
                            "面板本体）")
                           if tag in NO_LAYER_EXPECTED else
                           ("**本该有层却没认出来** —— 判据六条都过了（探针 849 "
                            "判决：缺口 4/4 全认得出来），所以是脚本没把层点开，"
                            "不是判据盲区"),
                })
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
            # ⚠️⚠️ 批 849：scope 里**必须**有 `.react-flow__node.selected`。
            #    `JimengGenPanel` 是 `JimengVideoNode` 的**直系子节点**
            #    （`JimengVideoNode.tsx:209`，既不在 NodeToolbar 也不在
            #    NodePanel 里），探针 849 逐层量出来的祖先链是
            #        form.flex > div.relative > div.flex > div.relative
            #        > [gen-model-listbox]
            #    所以只写 toolbar/panel 的 scope **一个都匹配不上**。
            #    修好逗号优先级之后，这 4 个状态从「跑了但键盘栏空白（没账）」
            #    变成「skipped（打不开：…）（有账）」—— 记账修对了，但**没测到**。
            #    「记了账」不等于「测到了」，这正是本批要分开的第三种状态。
            #    用 `.selected` 收窄而不是 `.react-flow__node`：画布上可能有多个
            #    节点，`.first` 必须落在**刚选中的那个**里，不是任意一个。
            #
            # ⚠️⚠️⚠️ 批 849 的**第三层**根因：触发器必须用 `^=`（前缀），不是
            #    等值。实际 aria-label 是带后缀的
            #        `选择模型: 即梦 Seedance 2.0 VIP, Standard-only model`
            #        `视频尺寸选项: 16:9 · 720P · 1, Standard-only model`
            #        `生成模式: 全能参考`
            #        `选择视频生成时长: 4s`
            #    而这里原来写的是 `aria-label="选择模型"`（**等值**）⇒ 匹配 0 个。
            #    音频那 5 个之所以一直能开，纯粹是因为它们的调用点碰巧用了
            #    `^=`。**同一个字段，两种匹配法，只有碰巧对的那一半在跑** ——
            #    这类不一致不会报错，只会让「没测到的」看起来像「没有的」。
            for trig, tid in [('button[aria-label^="选择模型"]', "模型"),
                              ('button[aria-label^="视频尺寸选项"]', "尺寸"),
                              ('button[aria-label^="生成模式"]', "模式"),
                              ('button[aria-label^="选择视频生成时长"]', "时长")]:
                try_measure(f"视频生成面板·{tid}下拉", trig,
                            ".react-flow__node-toolbar, .react-flow__node-panel, "
                            ".react-flow__node.selected",
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
            # 再验「Tab 走进被遮住的控件」这一条：盖一层**真浮层**，
            # 判据必须报出 covered；撤掉后必须**少报**。
            # ⚠️ 这条**不能用上面那层**：截取帧下拉第 1 次 Tab 就进去了，
            #    探针当场返回，压根没机会走到被遮住的控件上 —— 自检于是恒假。
            #    换成一个**深**的层（顶栏搜索，实测 39 步），前面 38 个焦点位
            #    足够让探针看见遮挡。第一版就是栽在这儿，自检把自己判红了。
            # ⚠️⚠️ 遮挡物**必须是带浮层锚的真浮层**（role=dialog + data-testid）。
            #    第三版判据只认「栈顶是不是**另一个浮层**」，一个光秃秃的
            #    `inset:0` div 没有浮层锚，判据对它天然免疫 —— 自检会照到自己
            #    判红的下场（第二次）。自检的夹具必须长得像被它要验的那个东西。
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
                # ── 夹具一：给每个可聚焦控件盖一层「**它自己的皮**」────────
                #    同框、挂在 body 下、**没有浮层锚**（无 data-testid / 无
                #    dialog|menu|listbox|popover role、不在 portal 里）。
                #    判据必须**不**把这些算成「被遮」——
                #    第 1 版判据（elementFromPoint + 包含）会说遮（皮不是控件的
                #    后代），第 2 版（栈顶非自己非后代）也会说遮（皮同样不是）。
                #    这一条专治那两版，源站的 `text-flow-node-full` 就是这么
                #    一种皮（探针 845c 实测它和焦点所在节点**不同支**却同框）。
                #    ⚠️ 皮**不能**用 `pointer-events:none` —— 那样
                #    `elementsFromPoint` 压根不返回它，这条自检就成了恒真的
                #    空话（自检恒真比没有自检更坏：它会盖着错误的判据说"✓"）。
                # ⚠️⚠️ 皮必须插成控件的**同层兄弟**（紧跟控件之后），不能挂在
                #    body 末尾。前三版各错一次，错法一次比一次微妙：
                #      ① `z-index:99997` 太大 → 皮盖住一切，连真遮挡一起盖；
                #      ② 抄控件自己的 z-index → 皮落在子树底下，压根不当栈顶；
                #      ③ 挂 body 末尾 + 抄最近层叠上下文的 z → 皮当上栈顶 33 次，
                #         可**同层**的盖子按树序画在控件之后，body 末尾比它还后
                #         —— 又盖住 3 个真遮挡，计数 4 → 1。
                #    三次都不是判据错，是**夹具站错了位置**。真·「自己的皮」
                #    必须和控件同层、紧贴着，谁也不是谁的后代 —— 源站那个
                #    `text-flow-node-full` 就是这个形状（探针 845c 实测：和节点
                #    外壳同框、不同支）。层叠上下文不是看元素自己的，是看它
                #    所在的那一层。
                skin_n = page.evaluate("""() => {
                  const SEL = 'a[href],button,input,select,textarea,[tabindex],'
                            + '[role=menuitem],[role=option]';
                  let n = 0;
                  for (const c of document.querySelectorAll(SEL)) {
                    const r = c.getBoundingClientRect();
                    if (r.width < 1 || r.height < 1) continue;
                    if (!c.parentNode) continue;
                    const cs = getComputedStyle(c);
                    // absolute 的坐标要换算到 offsetParent 的坐标系去
                    let ox = 0, oy = 0;
                    const op = c.offsetParent;
                    if (op) {
                      const orr = op.getBoundingClientRect();
                      ox = orr.x + (op.clientLeft || 0);
                      oy = orr.y + (op.clientTop || 0);
                    }
                    const d = document.createElement('div');
                    d.setAttribute('data-kbskin-probe', '1');
                    // 外扩 2px：判据采样的是**边框外 1px**（焦点环就画在那儿），
                    // 同框的皮够不到那儿，反向自检就成了空话。外扩 2px 让皮
                    // 真的压在焦点环上 —— 判据仍必须判「没遮住」，因为它透明。
                    // 此刻这条自检验证的是新判据的**核心主张**：透明的东西
                    // 什么也盖不住。前面三代判据全都会在这里栽（它们只问
                    // 「栈顶是不是外人」，压根不看透明不透明）。
                    d.style.cssText = 'position:absolute;'
                      + 'z-index:' + (cs.zIndex === 'auto' ? '0' : cs.zIndex) + ';'
                      + 'left:' + (r.x - ox - 2) + 'px;'
                      + 'top:' + (r.y - oy - 2) + 'px;'
                      + 'width:' + (r.width + 4) + 'px;'
                      + 'height:' + (r.height + 4) + 'px;'
                      + 'background:transparent;';
                    c.parentNode.insertBefore(d, c.nextSibling);
                    n += 1;
                  }
                  return n;
                }""")
                page.wait_for_timeout(300)
                skin_when_skin = keyboard_probe(deep_layer)
                skin_top_when_skin = skin_when_skin.get("skin_top_n")
                page.evaluate("""() => document.querySelectorAll('[data-kbskin-probe]')
                    .forEach(e => e.remove())""")
                # ── 夹具二：再来一层**真浮层**（role=dialog + data-testid）──
                #    ⚠️ 它必须是**不透明**的。第四版判据问的是"焦点环还在不在"，
                #    透明的东西什么也盖不住 —— 一个 `background:transparent` 的
                #    遮挡层在新判据下**理应**不多报，自检要是拿它当阳性夹具，
                #    就是在要求判据犯错。阳性夹具必须长得像真模态。
                page.wait_for_timeout(300)
                page.evaluate("""() => {
                  const d = document.createElement('div');
                  d.setAttribute('data-kbcover-probe', '1');
                  d.setAttribute('role', 'dialog');
                  d.setAttribute('data-testid', 'kb-self-test-cover');
                  d.setAttribute('aria-label', '自检遮挡层');
                  d.style.cssText = 'position:fixed;inset:0;z-index:99998;'
                                  + 'background:rgb(13,13,13)';
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
                skin_when_skin = {"covered": None}
                skin_n = 0
            page.keyboard.press("Escape")
            page.wait_for_timeout(400)
            kb_self = {"layer": probe_layer,
                       "reachable_before": before_kb.get("ok"),
                       "unreachable_when_stripped": after_kb.get("ok") is False,
                       "reachable_after_restore": restored_kb.get("ok"),
                       "covered_probe_layer": deep_layer,
                       "skin_n": skin_n,
                       "skin_top_n": skin_top_when_skin,
                       "clear_covered": covered_when_clear.get("covered"),
                       "skin_covered": skin_when_skin.get("covered"),
                       "covered_n_when_skin": skin_when_skin.get("covered_n"),
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
    #
    # ⚠️⚠️ 批 849 再切一刀：`ok is False` 里还要分「**真进不去**」和
    #    「**按满了上限还没走到**」（`capped`）。这两件事第一版压成同一个词，
    #    而 844-848 五轮都 0 缺陷的 `canvas-context-menu` 就在这里被**冤枉**
    #    报出去过一次（实测它冷启动要 39 次 Tab，上限 60 余量太小 ⇒ flaky）。
    #    **capped 的不是缺陷，是「这轮没测出来」** —— 与 skipped 同级：
    #    有账，但不下结论。混进 kb_bad 就是拿测不出来当产品坏了。
    kb_capped = [r for r in kb_rows if r.get("capped")]
    kb_bad = [r for r in kb_rows
              if r.get("ok") is False and not r.get("capped")]

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

    # ── 焦点陷阱 / 方向键：分档**只能**按源站基线表走 ──────────────────
    #   源站实测（探针 846b / 847c / 847d，登录态 1512×950，**每个测量从重开的
    #   层起手**，真按键盘读 activeElement）。表里的分档**散得很开** —— 不是一条
    #   统一判据，而是「按层型/按产品各取所需」：
    #     · 搜索面板   开层接管(面板自己) / Tab **不困**(第10次逃) / 方向键**不**消费
    #     · 右键菜单   开层接管(第一项)     / Tab **不困**(第1次逃)  / 方向键**动**且环绕
    #     · 更多菜单   开层接管(层自己)     / Tab **困**(12次全在内) / 方向键**动**
    #     · 账号菜单   开层接管(层自己)     / Tab **困**              / 方向键**动**
    #     · 缩放菜单   **不接管**(焦点给触发器旁的行内百分比输入) / Tab **困** / 方向键**动**
    #     · 分享面板   **不接管**(焦点留在触发器) / Tab **不困** / 方向键不动 /
    #                  Esc 落到**「更多」**而不是分享触发器 —— 这是源站自己的
    #                  a11y 失手，**照抄，不修**（不擅自改进源站）
    #     · 时间线全屏 开层接管(dialog 自己) / Tab **困** / Esc 关掉但焦点不回触发器
    #
    # ⚠️⚠️ 表里**没有**的层，源站行为未知 ⇒ 一律记进 `kb_not_sampled`，
    #    **不许**按推测判缺陷。「复刻这边测出来是 0」和「源站也是 0」是两回事 ——
    #    §63 已经吃过一次这个亏（右键菜单 45 次探不到被写成"源站也这样"）。
    # ⚠️ 源站有几层**压根没有 testid**（更多菜单 200×84、缩放菜单 200×292），
    #    探针改用**矩形**当层身份（开前/开后差分拿矩形，单次打开内稳定）。
    #    `src_identified_by` 把这件事写明，不假装有锚点。
    SOURCE_BASELINE = {
        # ══ 批 850：生成面板那 4 个下拉（源站**首次**取到样）══════════════
        # 848 的范围限制写着「源站这 4 个下拉从未被鼠标打开过（只 dump 了
        # 工具条按钮）」，849 把它们从 kb_not_sampled 里捞出来之后就必须来取样，
        # 否则那 9 层永远只能记「没取过样」。
        #
        # 取样（探针 850，登录态，**视口 1512×1200**——见下面的范围说明）：
        #   · 认层靠 `role`：这 4 层**都没有 testid**，`role` 是
        #     `listbox` ×2 / `dialog` ×2，class `animate-none transition-none
        #     absolute z-…`。847 定过「无 testid 用矩形认」，这里更进一步：
        #     role 更稳，所以给层打了 `data-probe850` 临时标记。
        #   · ① **四个全都开层即接管焦点**（焦点落在层内的 BUTTON 上；
        #     「时长」那个落在 SPAN 滑块 thumb 上——**非可聚焦元素**）。
        #   · ② **四个都不困 Tab**（第 1 / 3 / 1 / 2 次逃出，且**层都还在**）。
        #     ⚠️ 这里必须区分「焦点逃出」与「层自己关了」：源站这些下拉会
        #     **失焦即关**，不查层还在不在就会把后者写成前者。
        #   · ③ 方向键 **没测到** —— 见 `arrows_move: None` 下面的说明。
        #   · ④ **Esc 关闭层但焦点不回触发器**（落到节点本体 / `添加参考`），
        #     与分享面板同病（源站 a11y 失手），**照抄，不修**。
        #
        # ⚠️ 视口 1512×1200 而非惯例的 1512×950：源站生成面板挂在节点**下方**
        # 约 340px，950 高的视口里「选择模型」触发器落在 y≈987，**点不到**
        # （`click` 10s 超时），另外三个触发器连 `count` 都是 0。抬视口只影响
        # 几何，这四条键盘分档与视口无关；**本批的数字不进几何结论**。
        "gen-model-listbox": {
            "src_tid": "(无 testid)", "src_kind": "listbox",
            "src_identified_by": "role=listbox + 矩形 400×384 @[783,752]（探针 850）",
            "takes_focus_at_open": True, "traps_tab": False,
            "arrows_move": None, "esc_returns_to_trigger": False,
            "src": "jimeng_probe850_genpanel_kb.py（登录态，视口 1512×1200）"},
        "gen-video-size-listbox": {
            "src_tid": "(无 testid)", "src_kind": "dialog",
            "src_identified_by": "role=dialog + 矩形 334×292 @[867,844]（探针 850）",
            "takes_focus_at_open": True, "traps_tab": False,
            "arrows_move": None, "esc_returns_to_trigger": False,
            "src": "jimeng_probe850_genpanel_kb.py（登录态，视口 1512×1200）"},
        "gen-mode-listbox": {
            "src_tid": "(无 testid)", "src_kind": "listbox",
            "src_identified_by": "role=listbox + 矩形 200×84 @[1041,1052]（探针 850）",
            "takes_focus_at_open": True, "traps_tab": False,
            "arrows_move": None, "esc_returns_to_trigger": False,
            "src": "jimeng_probe850_genpanel_kb.py（登录态，视口 1512×1200）"},
        "gen-duration-listbox": {
            "src_tid": "(无 testid)", "src_kind": "dialog",
            "src_identified_by": "role=dialog + 矩形 400×100 @[1006,1036]（探针 850）",
            "takes_focus_at_open": True, "traps_tab": False,
            "arrows_move": None, "esc_returns_to_trigger": False,
            "src": "jimeng_probe850_genpanel_kb.py（登录态，视口 1512×1200）"},
        "jimeng-search-overlay": {
            "src_tid": "canvas-feature-panel", "src_kind": "dialog",
            "src_identified_by": "testid",
            "takes_focus_at_open": True, "traps_tab": False,
            "arrows_move": False, "esc_returns_to_trigger": True,
            "src": "jimeng_probe846_focustrap2.py（登录态 1512×950）"},
        "canvas-context-menu": {
            "src_tid": "canvas-context-menu", "src_kind": "menu",
            "src_identified_by": "testid",
            "takes_focus_at_open": True, "traps_tab": False,
            "arrows_move": True, "esc_returns_to_trigger": False,
            "src": "jimeng_probe846_focustrap2.py（登录态 1512×950）"},
        "topbar-more-menu": {
            "src_tid": "(无 testid)", "src_kind": "panel",
            "src_identified_by": "矩形 200×84 @[1211,56]（探针 847d 差分）",
            "takes_focus_at_open": True, "traps_tab": True,
            "arrows_move": True, "esc_returns_to_trigger": True,
            "src": "jimeng_probe847d_baseline2.py（登录态 1512×950）"},
        "canvas-user-menu": {
            "src_tid": "canvas-user-menu", "src_kind": "panel",
            "src_identified_by": "testid（外层无，内层有；开层焦点即它 tabindex=-1）",
            "takes_focus_at_open": True, "traps_tab": True,
            "arrows_move": True, "esc_returns_to_trigger": True,
            "src": "jimeng_probe847d_baseline2.py（登录态 1512×950）"},
        "canvas-zoom-menu": {
            "src_tid": "(外层无 testid；内层 canvas-zoom-percent-input)",
            "src_kind": "panel",
            "src_identified_by": "矩形 200×292 @[16,599]（探针 847d 差分）",
            # ⚠️ 源站开层时焦点给的是**触发器旁的行内百分比输入**，不在层矩形内 ——
            #    判据按「在不在层里」读就是 False，如实记，不修饰成"接管了"。
            "takes_focus_at_open": False, "traps_tab": True,
            "arrows_move": True, "esc_returns_to_trigger": True,
            "src": "jimeng_probe847d_baseline2.py（登录态 1512×950）"},
        "topbar-share-panel": {
            "src_tid": "canvas-share-panel-surface", "src_kind": "panel",
            "src_identified_by": "testid",
            "takes_focus_at_open": False, "traps_tab": False,
            "arrows_move": False,
            # 源站 Esc 之后焦点落到**「更多」**那枚钮上，不是分享触发器 ——
            # 它自己的 a11y 失手。**照抄，不修**。
            "esc_returns_to_trigger": False,
            "src": "jimeng_probe847d_baseline2.py（登录态 1512×950）"},
        "text-bg-palette": {
            # 源站那枚钮 **aria-label 是空的**，认它靠 innerText「背景色」
            # （75×32）。层 = `DIV` fixed z=120 **214×40 @[657,190]**，
            # 无 testid / 无 role / 无 aria-label，7 个可聚焦。
            "src_tid": "(无 testid；触发器文案「背景色」)",
            "src_kind": "palette",
            "src_identified_by": "矩形 214×40 @[657,190]（探针 848b 差分）",
            # ⚠️ 源站开层时把焦点丢给**画布根** `rf__wrapper`（tabindex=0），
            #    **不在层矩形里** —— 这一层压根不接管焦点。
            "takes_focus_at_open": False,
            # 第 1 次 Tab 就逃出（落到视频节点）。
            "traps_tab": False,
            # ⚠️ `None` = **测不了**，不是「不动」：源站从不把焦点放进这层，
            #    所以「层内方向键」这条路径压根不存在，无从观测。判据里
            #    `None` 是 falsy ⇒ 不产生 finding，也不当通过。
            "arrows_move": None,
            "esc_returns_to_trigger": None,
            "src": "jimeng_probe848b_textpalette.py（登录态 1512×950）"},
    }
    NOT_SAMPLED = {
        "video-fullscreen-preview":
            "**BLOCKED_BY_FIXTURE**：源站那个视频节点（`node_236ctpehgg`"
            "「视频 node: 视频 1」）选中后的工具条**只有 4 枚**按钮 —— "
            "`Create connected node before 视频 1` / `Rename 视频 1` / "
            "`Add tags` / `Create connected node after 视频 1` —— "
            "**压根没有全屏入口**；全页唯一的 `全屏编辑` 属于**时间线**节点"
            "（探针 847 实测逐节点 dump）。所以复刻这一层的源站行为"
            "**未知** ⇒ 不下结论，也不拿时间线全屏的行为替它判。",
        "topbar-history-menu":
            "**前置态没成立**：点第 2 个 `canvas-panel-launcher` 开出来的是"
            "「积分明细」（焦点落在 al='' 的 BUTTON 上），**0 个新的 fixed 层**"
            "（探针 847c/847d）。源站的生成历史入口这一版画布上取不到样。",
        "video-toolbar-capture-menu":
            "**BLOCKED_BY_FIXTURE**：源站这一版画布上的**视频节点是生成结果**，"
            "不是挂在时间线上的可编辑片段 —— 选中后浮出来的是**生成面板**"
            "（`选择模型: 即梦 Seedance 2.0 VIP` / `视频尺寸选项: 16:9·720P·1` / "
            "`生成模式: 全能参考` / `选择视频生成时长: 4s` + `添加参考` / "
            "`引用参考` / `展开视频生成器` / `生成`，探针 848 逐节点 dump），"
            "**没有「截取帧」下拉**。复刻这一层是 mock 出来的可编辑视频形态，"
            "源站对应物在这一版画布上不存在 ⇒ 不下结论。",
        "video-toolbar-tools-menu":
            "**BLOCKED_BY_FIXTURE**：同上 —— 源站视频节点选中后是生成面板，"
            "**没有「工具」下拉**。要取样得先有一份**可编辑**的视频片段"
            "（挂在时间线上、有帧序列），这一版画布不具备。",
        "image-tools-menu":
            "**BLOCKED_BY_FIXTURE**：这一版画布上**没有图片节点** —— 节点实测"
            "只有 视频 / 文本×3 / 时间线 / 导演台 六个（探针 848）。"
            "源站图片节点的工具条菜单无从取样。",
    }
    # ⚠️ 音频生成面板那 5 个下拉：850 给**视频**生成面板的 4 个下拉取到了样
    #    （接管焦点 / 不困 Tab / Esc 不归位），这 5 个是**同一类**层，但
    #    **本批没有实测**。按 847 定下的规矩，「同类」**不等于**「同行为」——
    #    拿视频那 4 个的分档去判音频这 5 个，就是 847 明令禁止的
    #    「按推测判缺陷」。所以它们仍记 not_sampled，只是把「同类已取样」
    #    这条**线索**写进 why，好让下一批知道从哪下手。
    for _t in ("audio-music-model-listbox", "audio-music-duration-listbox",
               "audio-voice-model-listbox", "audio-gen-mode-listbox",
               "audio-all-voices-listbox"):
        NOT_SAMPLED[_t] = (
            "**没取过样**：源站这一层在探针 850 里没被打开过。**线索**：同属"
            "生成面板的下拉，而视频那 4 个（探针 850）实测是「开层即接管焦点 / "
            "不困 Tab / Esc 不归位」—— 但同类**不等于**同行为，847 明令不许"
            "按推测判缺陷，所以本层仍不下结论。下一批直接照 850 的路子取。")
    kb_no_initial, kb_escaped, kb_arrow_dead = [], [], []
    kb_judged, kb_not_sampled = [], []
    for r in kb_rows:
        if r.get("ok") is not True:
            continue
        tid = r.get("layer")
        if tid in NOT_SAMPLED:
            kb_not_sampled.append({"state": r.get("state"), "layer": tid,
                                   "why": NOT_SAMPLED[tid]})
            continue
        base = SOURCE_BASELINE.get(tid)
        if not base:
            kb_not_sampled.append({
                "state": r.get("state"), "layer": tid,
                "why": "源站这一层**没取过样**（849 补覆盖面之后，探到的层里"
                       "只有这 7+4 层在源站取过键盘行为）⇒ 源站行为未知，"
                       "不许按推测判缺陷。"})
            continue
        kb_judged.append(tid)
        at_open = r.get("focus_at_open") or {}
        if base["takes_focus_at_open"] and not at_open.get("inside"):
            kb_no_initial.append({"state": r.get("state"), "layer": tid,
                                  "src_tid": base["src_tid"],
                                  "at_open": at_open.get("al") or at_open.get("state"),
                                  "why": "源站这一层开层即接管焦点，复刻没有"})
        esc = r.get("escape") or {}
        if base["traps_tab"] and esc.get("trapped") is False:
            kb_escaped.append({"state": r.get("state"), "layer": tid,
                               "src_tid": base["src_tid"],
                               "escaped_at": esc.get("escaped_at"),
                               "landed": esc.get("landed"),
                               "why": "源站这一层 Tab 会困在层内，复刻第 "
                                      f"{esc.get('escaped_at')} 次就跑了"})
        arr = r.get("arrow_down") or {}
        if base["arrows_move"] and arr.get("moved") is False:
            kb_arrow_dead.append({"state": r.get("state"), "layer": tid,
                                  "src_tid": base["src_tid"],
                                  "seq": [s.get("who") for s in arr.get("seq", [])],
                                  "why": "源站这一层方向键在层内移动（ARIA menu 主路径），"
                                         "复刻按了方向键焦点不动"})

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"rows": rows, "skipped": skipped, "states": states_done,
                   "confirmed": real,
                   "by_modal": by_modal,
                   "keyboard": kb_rows,
                   "keyboard_bad": kb_bad,
                   "keyboard_covered": kb_covered,
                   "keyboard_deep": kb_deep,
                   "keyboard_deep_threshold": DEEP,
                   "keyboard_no_initial_focus": kb_no_initial,
                   "keyboard_escaped": kb_escaped,
                   "keyboard_arrow_dead": kb_arrow_dead,
                   "keyboard_judged_layers": sorted(set(kb_judged)),
                   "keyboard_not_sampled": kb_not_sampled,
                   "keyboard_no_layer": kb_no_layer,
                   "keyboard_capped": kb_capped,
                   "keyboard_leaks": kb_leaks,
                   "source_baseline": SOURCE_BASELINE,
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
          f"偏深 {len(kb_deep)}（>{DEEP} 次，INFO）、"
          f"没浮层可探 {len(kb_none)}、"
          f"**按满上限没测到 {len(kb_capped)}**（不是缺陷，是没测出来）")
    # 「没认到层」的两类必须分开印（批 849）。第一版这里一个数都不打，
    # 「本该有层却没开」和「本来就没有层」都表现为「不在 keyboard 栏里」。
    _nl_unexpected = [k for k in kb_no_layer if not k.get("expected")]
    if kb_no_layer:
        print(f"  · 没认到浮层的状态 {len(kb_no_layer)} 个"
              f"（本来就没有 {len(kb_no_layer) - len(_nl_unexpected)}、"
              f"**本该有层却没开 {len(_nl_unexpected)}**）")
        for k in _nl_unexpected:
            print(f"      ⚠ [{k['state']}] {k['why']}")
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

    # ── 焦点陷阱 / 方向键（批 846 加）：分档只按**源站基线表**走 ──────
    print(f"\n焦点陷阱 / 方向键：源站基线表里能判的层 "
          f"{len(set(kb_judged))} 个（{', '.join(sorted(set(kb_judged))) or '—'}）"
          f" → **开层没接管焦点 {len(kb_no_initial)}**、"
          f"**Tab 逃出层 {len(kb_escaped)}**、"
          f"**方向键不动 {len(kb_arrow_dead)}**；"
          f"源站**没取过样**因而**不下结论**的 {len(kb_not_sampled)} 个")
    for k in kb_no_initial:
        print(f"  ★ 开层**没把焦点移进层里** [{k['state']}] 浮层={k['layer']!r}："
              f"焦点还停在 {k.get('at_open')!r} —— 源站 {k['src_tid']!r} "
              f"开层即接管（{k['why']}）")
    for k in kb_escaped:
        print(f"  ★ Tab 从层里逃出去了 [{k['state']}] 浮层={k['layer']!r}："
              f"第 {k.get('escaped_at')} 次 Tab 跑到 "
              f"al={(k.get('landed') or {}).get('al')!r} "
              f"tid={(k.get('landed') or {}).get('tid')!r} "
              f"—— 源站 {k['src_tid']!r} 会困在层内（{k['why']}）")
    for k in kb_arrow_dead:
        print(f"  ★ 方向键**焦点不动** [{k['state']}] 浮层={k['layer']!r}："
              f"ArrowDown 连按 4 次都是同一个 —— 源站 {k['src_tid']!r} "
              f"方向键在层内移动（{k['why']}）")
    if kb_not_sampled:
        print("  ⚠ 源站**没取过样**的层（**不下结论**，也不当通过）：")
        for k in kb_not_sampled:
            print(f"    · [{k['state']}] {k['layer']!r} —— {k['why']}")
    for k in kb_probed:
        if k.get("ok") and (k.get("tabs") or 0) <= DEEP:
            esc = k.get("escape") or {}
            arr = k.get("arrow_down") or {}
            print(f"  · [{k['state']}] 浮层={k['layer']!r} Tab {k['tabs']} 次进得去"
                  f"｜层内 Tab "
                  + (f"第 {esc.get('escaped_at')} 次逃出" if not esc.get("trapped", True)
                     and esc.get("escaped_at") else "没逃出")
                  + (f"｜方向键{'动' if arr.get('moved') else '不动'}"
                     if arr and "moved" in arr else ""))
    ok_kb_self = (bool(kb_self) and kb_self.get("reachable_before") is True
                  and kb_self.get("unreachable_when_stripped") is True
                  and kb_self.get("reachable_after_restore") is True
                  # ⚠️ 这里比的是**计数**，不是"有没有"：基线里本来就真有几处
                  #    焦点落在被遮住的控件上（那正是本批查出来的缺陷），
                  #    所以"撤掉后不再报"是个**错前提** —— 第一版就栽在这儿，
                  #    自检把自己判红了。真正要证明的是判据**对遮挡敏感**：
                  #    盖上一层，被遮住的焦点位必须**变多**。
                  and (kb_self.get("covered_n_when_shut") or 0)
                      > (kb_self.get("covered_n_when_clear") or 0)
                      # ⚠️ 反向那条同样要是判据：给每个控件盖一层「它自己的皮」
                  #    （同框、无浮层锚）后，被遮的焦点位必须**一个都不多**。
                  #    这一条把第 1 版（elementFromPoint + 包含）和第 2 版
                  #    （栈顶非自己非后代）**当场判红** —— 两者都会把皮当成外人。
                  #    只做正向不做反向，等于只验了判据「会响」，没验它「分得清」。
                  and (kb_self.get("covered_n_when_skin") or 0)
                      == (kb_self.get("covered_n_when_clear") or 0)
                  # 而且皮必须**真的当过栈顶**（>0），否则上面那条是恒真的空话：
                  # 皮压根没参与判定，"不多报"当然成立。
                  and (kb_self.get("skin_top_n") or 0) > 0)
    print(f"自检（键盘）：把 {kb_self.get('layer')!r} 里的 tabindex 全摘成 -1 后"
          f"判为进不去={kb_self.get('unreachable_when_stripped')}、"
          f"还原后恢复={kb_self.get('reachable_after_restore')}"
          + f"；盖一层遮挡物后被遮住的焦点位 "
          f"{kb_self.get('covered_n_when_clear')} → {kb_self.get('covered_n_when_shut')}"
          + f"，给 {kb_self.get('skin_n')} 个控件各盖一层「自己的皮」后 → "
          f"{kb_self.get('covered_n_when_skin')}"
          f"（皮当过栈顶 {kb_self.get('skin_top_n')} 次；"
          f"必须不多报、且皮必须真当过栈顶）"
          + (f"（{kb_self.get('why')}）" if kb_self.get("why") else "")
          + f"  →  {'✓ 键盘判据能失败' if ok_kb_self else '✗ 键盘判据恒真，这轮结果不可信'}")

    print(f"明细已写入 {OUT}")
    # ⚠️ 自检不过必须是**退出码 2**，不是 0 也不是 1：退出 0 会被 CI 当通过，
    #    退出 1 会被读成"查到缺陷了"。这是独立的第三种状态。
    if not ok_self or not ok_kb_self:
        return 2
    # ⚠️⚠️ 批 849 加的第三种「不可信」：**本该有层却没认出来**。
    #    这不是缺陷（判据没报任何东西），也不是通过（那 9 个状态等于没测），
    #    而是「这轮键盘那一栏是残缺的」—— 和自检红是同一类：结果不能用。
    #    没有这一条，逗号拼接那个 bug 可以一直藏着：退出码 0、CI 绿、
    #    覆盖面从 12 层缩到 12 层 nobody notices。
    if kb_capped:
        print(f"\n⚠ 有 {len(kb_capped)} 个状态**按满 Tab 上限**仍没测到"
              f"（{[k.get('state') for k in kb_capped]}）"
              f" ⇒ 这是「没测出来」不是「产品坏了」，本轮键盘那一栏**不完整**"
              f"（退出码 2）")
        for k in kb_capped:
            print(f"    ⚠ [{k.get('state')}] 前 6 步轨迹: "
                  f"{(k.get('trace') or [])[:6]}")
        return 2
    if kb_leaks:
        print(f"\n⚠ 有 {len(kb_leaks)} 个状态探完**没把层收掉**"
              f"（漏下去的层会污染后面每个状态的键盘结果）"
              f" ⇒ 本轮结果**不可信**（退出码 2）")
        for k in kb_leaks:
            print(f"    ⚠ [{k['state']}] 关不掉 {k['stuck']}")
        return 2
    _nl_unexpected = [k for k in kb_no_layer if not k.get("expected")]
    if _nl_unexpected:
        print(f"\n⚠ 有 {len(_nl_unexpected)} 个状态本该开着浮层却没认出来"
              f"（{[k['state'] for k in _nl_unexpected]}）"
              f" ⇒ 键盘那一栏不完整，本轮结果**不可信**（退出码 2）")
        return 2
    return 1 if (real or kb_bad or kb_covered
                 or kb_no_initial or kb_escaped or kb_arrow_dead) else 0


if __name__ == "__main__":
    sys.exit(main())

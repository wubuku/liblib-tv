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


LAYER_SEL = (
    '.react-flow__node-toolbar, .react-flow__node-panel, '
    '[role=menu], [role=listbox], [role=dialog], [role=popover], '
    '[data-testid$="-listbox"], [data-testid$="-menu"], '
    '[data-testid$="-panel"], [data-testid$="-palette"]')

MODALISH_JS = """(tid) => {
              const el = document.querySelector(`[data-testid="${tid}"]`);
              if (!el) return {modalish: false, why: '层不存在'};
              const vw = innerWidth, vh = innerHeight;
              const opaque = (n) => {
                const bg = getComputedStyle(n).backgroundColor || '';
                return bg !== 'rgba(0, 0, 0, 0)'
                    && !bg.startsWith('rgba(0, 0, 0, 0)');
              };
              const covers = (r) => r.width >= vw * 0.9 && r.height >= vh * 0.9;
              const positioned = (n) => {
                const p = getComputedStyle(n).position;
                return p === 'fixed' || p === 'absolute';
              };
              for (let n = el; n && n !== document.body; n = n.parentElement) {
                const r = n.getBoundingClientRect();
                if (!positioned(n) || !covers(r)) continue;
                if (opaque(n)) {
                  return {modalish: true, via: '自身不透明',
                          why: n.tagName + ' 定位且铺满视口、自身不透明'};
                }
                for (const c of n.children) {
                  const cr = c.getBoundingClientRect();
                  if (covers(cr) && opaque(c)) {
                    return {modalish: true, via: '不透明孩子',
                            why: n.tagName + ' 定位且铺满视口，其中一个孩子'
                                  + '（' + ((c.className || '').toString()
                                            .slice(0, 28)) + '）铺满且不透明'};
                  }
                }
              }
              return {modalish: false,
                      why: '没有「定位 + 铺满视口 + 不透明」的祖先'};
}"""


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

        def select_node_soft(tid: str) -> bool:
            """选中节点，但**不按 Escape**（探针 868 用的那套：给已选中的节点
            派发 mousedown 来清选择，再点目标）。

            ⚠️ 为什么必须有这一版：`select_node()` 靠 Escape 清选择，而文本
            节点在编辑态里把 Escape 当「取消编辑」⇒ 用它「重新选中」会顺手把
            刚进的编辑态 undo 掉（机制见 J 段注释）。凡是**要保住编辑态**的
            前置态准备，只能走这一版。
            """
            page.evaluate("""() => document.querySelectorAll(
                '.react-flow__node.selected').forEach(n => n.dispatchEvent(
                    new MouseEvent('mousedown', {bubbles: true})))""")
            pt = page.evaluate("""(tid) => {
              const n = document.querySelector(
                `.react-flow__node[data-testid="${tid}"]`);
              if (!n) return null;
              const r = n.getBoundingClientRect();
              const CTRL = 'button,[role=button],a,input,select,textarea';
              for (const [fx, fy] of [[0.5,0.5],[0.5,0.25],[0.25,0.5],[0.75,0.5]]) {
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

        def hard_reload(why: str) -> bool:
            """重载页面；dev server 掉了就**重试**，仍不行就**如实记账**返回
            False —— 绝不让异常冒出去。

            ⚠️ 868 栽过：dev server 掉线时 `page.reload()` 抛
            `ERR_CONNECTION_REFUSED`，**整份审计**带崩，前面二十几个状态
            的结果全丢。跟 `insert()` 是同一条原则（不让一次 30s 超时吃掉
            整份结果），只是当时只给 `insert()` 加了护栏、忘了 reload。
            ⚠️ 返回 False 之后**继续跑出来的结果不可信**（页面半死不活），
            调用方要据此退出码 2，而不是若无其事地继续报「通过」。
            """
            for i in range(3):
                try:
                    page.reload(wait_until="domcontentloaded", timeout=60000)
                    page.wait_for_timeout(2500)
                    return True
                except Exception as e:
                    print(f"    ⚠ 重载失败（{why}）第 {i + 1} 次："
                          f"{str(e).splitlines()[0][:70]}")
                    page.wait_for_timeout(4000)
            return False

        def page_alive() -> bool:
            """画布页**此刻**还是不是活的（不是 Next 的报错页/空壳）。

            ⚠️ 869 栽过：dev server 在跑到一半时掉线，页面变成报错页，
            后面 20 个状态于是**一个都没跑成**，可它们被逐条记成
            「前置态没成立」—— 读起来像 20 个各不相干的前置态问题，
            实际上只有**一个**原因：页面早就不在了。**一份 20 条 skip 的
            结果，比没有结果更坏**：它看着像结论。
            所以每段开始前验一次页面还活着，不活就**当场退出码 2**，
            把「跑不动了」和「前置态没成立」这两件事分开记账。
            """
            try:
                return bool(page.evaluate("""() => {
                  const shell = document.querySelector('.react-flow');
                  if (!shell) return false;
                  // Next 开发期的报错覆盖层：有它就说明这一页根本不是应用
                  const ov = [...document.querySelectorAll('nextjs-portal')]
                    .some(p => (p.innerText || '').includes('Error')
                               || p.querySelector('[data-nextjs-dialog]'));
                  return !ov;
                }"""))
            except Exception:
                return False

        def bail_if_dead(seg: str) -> bool:
            """页面死了就打印 + 返回 True（调用方据此 `return 2`）。"""
            if page_alive():
                return False
            print(f"    ✗ 放弃：进入「{seg}」前页面**已经不是画布页了**"
                  f"（dev server 掉线或编译报错）。此前量到的结果**不可信**"
                  f"（退出码 2）")
            return True

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

            ⚠️⚠️ 批 869 改了一处：取「栈顶」的实现从「第一个命中」改成
            「**最里层**的那个命中」。第一版那句「后出现的盖住先出现的」
            写的是意图，实现返回的却是 DOM 顺序第一个 —— 浮层套浮层时
            那是**外层**。探针 869 实测两次（AI 抽屉里的技能面板 / 引用参考
            面板），它都返回 `canvas-agent-drawer`。改完按 §80 逐态对比过
            29 个状态的 layer 归属（见 README §87）。
            """
            return page.evaluate("""() => {
              const SHELL = 'react-flow__renderer, react-flow__pane, '
                          + 'react-flow__viewport, react-flow__nodes, '
                          + 'react-flow__node, react-flow__node-toolbar';
              const LAYER = '.react-flow__node-panel, [role=menu], [role=listbox], '
                          + '[role=dialog], [role=popover], [data-testid$="-listbox"], '
                          + '[data-testid$="-menu"], [data-testid$="-panel"], '
                          + '[data-testid$="-palette"]';
              const hit = [];
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
                hit.push(e);
              }
              // ⚠️⚠️ 批 869：返回**最里层**那个，不是第一个。
              //   docstring 一直写着「后出现的盖住先出现的」= 取栈顶，可第一版
              //   实现是 `return` 第一个命中的 —— DOM 顺序上**祖先在子孙之前**，
              //   于是浮层**套浮层**时它返回的是**外层**。
              //   探针 869 实测（`scripts/jimeng_probe869_drawerpanels.py`）：
              //   AI 抽屉里的 `agent-skills-panel` / `agent-mention-panel`
              //   两个内层面板开着时，它两次都返回 `canvas-agent-drawer` ——
              //   量的是**抽屉**，不是刚打开的那块面板。840/849 记的
              //   「后面每个状态都在报同一层」就是这个。
              //   判据：命中集合里**没有别的命中元素是它的后代**的那些，才算栈顶。
              if (!hit.length) return '';
              const top = hit.filter(e => !hit.some(o => o !== e && e.contains(o)));
              const win = top.length ? top[top.length - 1] : hit[hit.length - 1];
              return win.getAttribute('data-testid')
                  || win.getAttribute('aria-label') || win.getAttribute('role') || '?';
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
            # ══ 批 865：这一层算不算**真模态**？════════════════════════
            #   谓词提到模块级 `MODALISH_JS`（单一来源：键盘探针和指针普查
            #   都用它，两处各写一份就是第四次让同一判据分叉）。
            #   ⚠️ 谓词**不是猜的**：探针 865 拿 4 个已知答案的层实测过
            #   （资产库 True / 项目信息 False / 更多菜单 False / 缩放菜单
            #   False，零判错）。`position: fixed|absolute` 这条约束是
            #   **必需**的 —— 项目信息的祖先里就有个 `pos=static 1680×1050
            #   自身不透明` 的页面根，少了它每个层都会被算成模态、判据恒真。
            modalish = page.evaluate(MODALISH_JS, layer_tid)
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
                  // ⚠️⚠️ 批 863 改这里（**四个自检条件一并逐个验过**才动的手）。
                  // 原来 `if (inside) return` —— 焦点一进层就返回，后面的采样全不做。
                  // §79 已查清后果：新版搜索面板**层内可聚焦控件 1 → 15**，第一次
                  // Tab 就落在输入框的下一个兄弟（分类 tab，**层内**）⇒ `tabs=1`
                  // ⇒ 层外步 0 ⇒ **两个自检同时塌**：
                  //   · `skin_top_n = 0`（反向自检判「恒真」）
                  //   · `covered_n = 0`（正向自检 0→0）
                  // 现在进层也往下走照常采样。
                  //
                  // ⚠️⚠️ 863 **推翻了 862 那句「covered_n 只统计层外，判据没被
                  // 放松」——那句话是错的。层内控件被**别的**浮层盖住时，焦点环
                  // 一样看不见，这跟它在不在本层内毫无关系。层内控件**只**对
                  // 「自己的浮层」免疫（那是 `paintsOver` 里 `n.contains(a)`
                  // 那条在管的事），不是对任何浮层都免疫。
                  // 「自己的浮层」这件事判据本来就已经正确处理了 —— 所以把层内
                  // 也纳入统计**不是**放松判据，是把漏掉的一半补回来。
                  // 补完实测：正向 `covered_n_when_shut` 0 → 1 活；反向
                  // `covered_n_when_skin` 仍为 0（53 个控件各盖一层「自己的皮」
                  // 不多报），`skin_top_n` 1 > 0（皮确实当过栈顶）⇒ 双向都活。
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
                  // 批 863：进层也照常采样，但 `state` 仍标 `inside` —— 这个字段
                  // 说的是「焦点在不在本层里」，跟「焦点环看不看得见」是**两件事**，
                  // 不该混用一个字段。`occluded`（4 条边全被不透明外人盖住）另算，
                  // Python 侧两个都收。
                  // ⚠️ 「自己的浮层」已经被 `paintsOver` 正确豁免了（走到 a 的祖先
                  //    就停 —— 祖先的背景画在下面，不算遮挡），所以层内控件被
                  //    **自己的**层盖住时 `edges` 仍然是 0。
                  return {state: inside ? 'inside'
                                       : (occluded ? 'covered' : 'other'),
                          inside: inside,
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
                    # 批 863：JS 现在进层也采样皮了，但这个分支下面**直接
                    # return**，会跳过后面 `if step.get('skin_top')` 的累加
                    # ⇒ 进层那一步的皮「采到了却被丢掉」（§62 版实测：
                    # 旧版皮当栈顶因此少 1 次）。这里补上。
                    if step.get("skin_top"):
                        skin_top_n += 1
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
                    # ⚠️⚠️ 批 863 补的最后一处：层内控件**也要**计入
                    # `covered_n`。它们被**别的**浮层盖住时同样该报 ——
                    # 「看不见的焦点环」这件事跟控件在不在层内无关。
                    # 之前这里直接 return，层内一步都没统计 ⇒ 新版搜索面板
                    # （第一次 Tab 就在层内）正向自检恒为 `0 → 0`。
                    # ⚠️ 上面 JS 把 state 标成了 `inside`，所以这里不能只判
                    #    `state == 'covered'`（那条永远进不来），得直接用
                    #    `edges` 判据：4 条边全被不透明外人盖住。
                    if (step.get("edges_covered") == step.get("edges_total")
                            and step.get("edges_total")):
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
                    return {"ok": True, "tabs": i, "covered": covered,
                            "covered_n": covered_n, "skin_top_n": skin_top_n,
                            "focus_at_open": at_open, "trace": trace,
                            "modalish": modalish,
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
                    "modalish": modalish,
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
                # ⚠️ 探完**必须把层收掉**。不收的话「截取帧下拉」会一路开着，
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
            # ⚠️ 普查跑在 `close_open()` **之后**。资产库是「点外面关掉」，
            #    Esc 关不掉，所以它会被普查撞见（865 实测：8 条画布控件因此
            #    掉进「活页面确认没通过」—— 采样到的栈顶元素是视频节点自己的
            #    wrapper，不是那层 `bg-black/55` 遮罩，`scrim` 判假）。
            #    所以 `modal_open` 必须**在普查这一刻**重新问，**不能**复用
            #    键盘探针里那个值 —— 那是 `close_open()` 之前的另一个瞬间。
            modal_open = False
            _ml_now = open_layer()
            if _ml_now:
                _mres = page.evaluate(MODALISH_JS, _ml_now) or {}
                modal_open = bool(_mres.get("modalish"))
            raw = page.evaluate("""(args) => {
              const [CONTROL, SAMPLES, VH, MODAL_OPEN, LAYER_SEL] = args;
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
                                   w: Math.round(tb.width), h: Math.round(tb.height),
                                   // ══ 批 866：记下这个遮挡物**自己是不是浮层的一部分** ══
                                   //   §83 记下的 4 条「未确认」根因查清了：项目信息浮层
                                   //   （800×546，**非全屏**）盖住画布控件，而采样到的
                                   //   栈顶元素是浮层内部的**文本 span**（`text-white/85`
                                   //   662×20）或**内容区**（`flex-1 overflow-y-auto
                                   //   px-6 py-4` 798×452）—— 它们**自己没背景**
                                   //   （底色来自浮层根），所以既不是「铺满视口的
                                   //   遮罩」，也认不出是浮层 ⇒ 掉进「未确认」。
                                   //   判据缺的是「**遮挡物属于某个浮层**」这一项。
                                   in_layer: !!t.closest(LAYER_SEL)});
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
                  // ══ 批 865 补：开着**真模态**时，层外控件按定义就被盖住 ══
                  //   上面那条 `scrim` 判的是「**遮挡物自己**的矩形够不够大」。
                  //   本批加了两个模态状态后实测：资产库开着时，画布上
                  //   9×9 的「取消静音」这类控件采样到的**栈顶元素**是
                  //   **视频节点自己的 wrapper**（752×428），不是那层
                  //   `bg-black/55` 遮罩 ⇒ `scrim=false` ⇒ 掉进
                  //   「活页面确认没通过」（实测 8 条，全是模态背后的
                  //   画布控件：取消静音 / 全屏预览 / 播放 / Add tags /
                  //   文本节点 / 音频节点）。
                  //   可审计**自己已经知道**此刻开着真模态（`args[2]` 传进来
                  //   的 `modalOpen`）：模态盖住页面是它的定义，不是需要
                  //   再量一遍的巧合。所以层外控件直接判「被模态盖住」。
                  //   ⚠️ 只在**真模态**时用这条 —— 下拉菜单不算，它小，
                  //      盖住画布控件是别的判据在管。
                  // （`scrimByModal` 的定义放在 `inLayer` 之后 —— 它要用到
                  //  `inLayer`，写在前面就只能去引用一个还不存在的名字。）
                  // ⚠️ 这条分界是本工具最要紧的一条判据，抄的是批 835 的结论：
                  //    **浮层盖住静态控件是覆盖层的正常行为，不该判失败。**
                  //    全屏模态开着的时候左栏点不到；下拉开着的时候画布上的
                  //    连接手柄点不到 —— 都对，用户本来就在菜单里，关掉就能点。
                  //    真正伤人的只有一种：**盖住另一个下拉的「选项」**。
                  //    那种情形里用户正处在"从菜单里挑一个"的流程中，
                  //    被埋掉的选项**没有任何办法露出来**（关掉菜单等于放弃
                  //    整个流程）—— 判据的落点必须是"控件自己在不在浮层里"。
                  // ⚠️ 选择器提到模块级 `LAYER_SEL`：批 866 要在**遮挡物**上
                  //    用同一个定义（`blocker.in_layer`），两处各写一份就是
                  //    第四次让同一判据分叉 —— 而分叉出来的分叉最难查。
                  const inLayer = !!el.closest(LAYER_SEL);
                  // ⚠️ `scrimByModal` 必须写在 `inLayer` **之后**（见上）。
                  const scrimByModal = !!MODAL_OPEN && !inLayer;
                  // ══ 批 866：遮挡物**自己属于某个浮层** ══════════════
                  //   §83 剩下那 4 条「未确认」的根因：项目信息浮层（800×546，
                  //   **非全屏**）盖住画布控件，栈顶是浮层内部的文本 span 或内容
                  //   区（它们**自己没背景**，底色来自浮层根）⇒ 既不是「铺满视口
                  //   的遮罩」，也认不出是浮层 ⇒ 掉进「未确认」。
                  //   判据缺的就是这一项。
                  //   ⚠️ 条件是「**控件不在任何浮层里**，而遮挡物**在**某个浮层
                  //   里」—— 两侧都要。不是「有遮挡物就算」：认不出归属的遮挡物
                  //   必须**继续留在未确认**，把它顺手算成 INFO 才是把真缺陷
                  //   藏起来。
                  //   ⚠️ 也不碰缺陷桶：缺陷桶要求 `same_layer`（同一层自己压
                  //   自己），本条只对 `same_layer=false` 的行生效，所以 835
                  //   「盖住另一个下拉的选项」那类**跨层**缺陷的判定路径不变。
                  const coveredByLayer = !inLayer
                    && blockers.some(bk => bk.in_layer);
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
                            covered_by_modal: scrim || scrimByModal,
                            covered_by_layer: coveredByLayer,
                            blockers: blockers});
                }
              }
              return out;
            }""", [CONTROL, SAMPLES, VIEWPORT["height"], modal_open,
                   LAYER_SEL])

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

            # ── 音色库的**筛选下拉**（批 870 加）────────────────────
            #   两步：先开音色库，再点里面的筛选钮。上面那个 `expect` 循环
            #   只能表达**一步**（`open_dropdown` 一次点一个触发器）。
            #   ⚠️ 870 之前这一层**根本测不了**：四个筛选面板无条件常驻
            #   （探针 870 实测），而审计的 `open_layer()` 又返回**外层**
            #   音色库 ⇒ 量到的永远是外层。修完判据 + 修完产品，才第一次
            #   有资格把它当一个独立状态来量。
            if select_node(aud):
                if open_dropdown('button[aria-label^="音色"]',
                                 "audio-all-voices-listbox"):
                    # ⚠️ 作用域必须是**两段**：实测音色库那层 `role=listbox`
                    #   渲染在 `.react-flow__node-toolbar` 里（祖先链实测：
                    #   BUTTON → DIV.relative → … → DIV.react-flow__node-toolbar），
                    #   **不在** `.react-flow__node-panel`。第一版只写 node-panel
                    #   ⇒ 计数 0 ⇒ 记成「打不开」—— 又是一次「够不着」被写成
                    #   「没有」。跟其余音频状态用同一个作用域最稳（触发器在
                    #   哪一栏，层就在哪一栏）。
                    try_measure("音频生成面板·音色筛选",
                                'button:has-text("性别")',
                                ".react-flow__node-toolbar, "
                                ".react-flow__node-panel",
                                "audio-voice-filter-listbox")
                else:
                    skipped.append("音频生成面板·音色筛选（音色库打不开）")
            else:
                skipped.append("音频生成面板·音色筛选（选不中音频节点）")

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

        # ══ I. 批 865：两个**视口级模态** ══════════════════════════════
        #   §82 把它们探出来了、也修好了，但那时它们的证据是**一次性测量**
        #   （探针 864 跑一次记一次）。这里把它们提升为**常驻状态** ——
        #   从此这两个层的焦点行为由审计**每次都量**，坏了会自己报出来。
        #   ⚠️ 它们在源站基线表外，所以**不参与**「源站怎么做」的对照，
        #      会落进 `keyboard_not_sampled`；真正盯着它们的是 865 新加的
        #      **源站无关**的模态语义桶（`modal_no_focus` / `modal_no_trap`）。
        if bail_if_dead("I（顶栏/工具条那一串）"):
            return 2
        for tag, path, tid, why in [
            ("资产库模态", [('button[aria-label="资产库"]', None)],
             "jimeng-assets-modal", "工具条「资产库」"),
            ("项目信息模态",
             [('[data-testid="canvas-more-trigger"]', None),
              ('[role="menuitem"]:text-is("项目信息")', None)],
             "project-info-modal", "顶栏「更多」→「项目信息」"),
            # ══ 批 867：探针 867 探到的另外 3 个浮层，一并进常驻状态 ══
            #   三个都**不是**真模态（实测 modalish=false），所以 865 的模态
            #   语义桶**不管**它们；它们受管的是源站无关的那几个键盘桶
            #   （Tab 进不去 / 走进被遮 / 偏深）。这正是「进状态表」的价值：
            #   不是每个层都要被判缺陷，而是每个层都要**被量**。
            ("顶栏·节点摘要",
             [('[data-testid="canvas-node-summary-trigger"]', None)],
             "topbar-node-summary", "顶栏「节点 2」药丸"),
            ("顶栏·项目面板",
             [('[data-testid="canvas-project-trigger"]', None)],
             "topbar-project-panel", "顶栏「项目」"),
            ("AI 侧栏",
             [('button[aria-label="与 AI 对话"]', None)],
             "canvas-agent-drawer", "右下角「与 AI 对话」"),
        ]:
            for sel, _ in path:
                el = page.locator(sel).first
                if el.count():
                    try:
                        el.click(timeout=6000)
                    except Exception:
                        pass
                page.wait_for_timeout(700)
            if page.locator(f'[data-testid="{tid}"]').count():
                measure(tag)
                page.keyboard.press("Escape")
                page.wait_for_timeout(600)
                # ⚠️ 资产库的遮罩是「点外面关掉」，Esc **不一定**管用；
                #    这里再点一下工具条把状态清干净，否则下一个状态的
                #    `open_layer()` 认到的还是它（840 栽过同一个坑：
                #    探完不收层，后面每个状态都在报同一层）。
                if page.locator(f'[data-testid="{tid}"]').count():
                    if not hard_reload(f"收 {tag} 的层"):
                        print(f"    ✗ 放弃：dev server 在收 {tag} 的层时"
                              f"连续 3 次拒连，本次结果**不可信**（退出码 2）")
                        return 2
            else:
                skipped.append(f"{tag}（走 {why} 但没找到 {tid}）")

        def j_ctx_dump(nid: str, trig: str) -> dict:
            """J 段某个状态 skipped 时，把**当时的上下文**原样倒出来。

            ⚠️ 纯读（全是 `querySelectorAll` / `getBoundingClientRect`），
               **不碰**被诊断的状态 —— 诊断动作不许破坏被诊断对象（§65）。
            ⚠️ 为什么需要它：868 第一次跑，「文本·全屏编辑」在**这里**跳过、
               在**冷启动探针**里却点得开，两边上下文不一样但没人知道差在哪。
               只写一句「入口不在 DOM」等于把「没测到」写成「没发生」——
               所以必须留下**能自己查**的现场，而不是让人猜。
            """
            return page.evaluate("""(a) => {
              const {nid, trig} = a;
              const q = (s) => document.querySelectorAll(s).length;
              const n = document.querySelector(
                `.react-flow__node[data-testid="${nid}"]`);
              const sel = [...document.querySelectorAll('.react-flow__node.selected')]
                .map(x => x.getAttribute('data-testid'));
              const full = [...document.querySelectorAll('button[aria-label="全屏"]')];
              const vis = (e) => { const r = e.getBoundingClientRect();
                return r.width > 1 && r.height > 1; };
              const at = (x, y) => { const e = document.elementFromPoint(x, y);
                if (!e) return null;
                const nn = e.closest('.react-flow__node');
                return e.tagName + '/' + (nn ? nn.getAttribute('data-testid') : '-'); };
              const d = {nodes: q('.react-flow__node'),
                         text_nodes: q('.react-flow__node[data-testid^="rf__node-text"]'),
                         selected_n: sel.length, selected: sel.slice(0, 6),
                         editing: q('.react-flow__node.selected [contenteditable]'),
                         textareas: q('.react-flow__node.selected textarea'),
                         toolbars: q('.react-flow__node-toolbar'),
                         trig_n: q(trig),
                         aria_fullscreen_n: full.length,
                         aria_fullscreen_vis: full.filter(vis).length,
                         aria_fullscreen_in_toolbar: full.filter(
                           b => !!b.closest('.react-flow__node-toolbar')).length};
              if (n) {
                const r = n.getBoundingClientRect();
                d.rect = [Math.round(r.x), Math.round(r.y),
                          Math.round(r.width), Math.round(r.height)];
                d.is_selected = n.classList.contains('selected');
                d.hit_center = at(r.x + r.width * 0.5, r.y + r.height * 0.5);
                d.hit_quarter = at(r.x + r.width * 0.25, r.y + r.height * 0.5);
              } else { d.node_gone = true; }
              return d;
            }""", {"nid": nid, "trig": trig})

        # ══ J. 批 868：三个**要先插节点**才存在的浮层 ═══════════════════
        #   867 的探针把这三个记成「候选没命中」，本批查清了：**不是**入口
        #   没有，是**冷启动画布上压根没有那几种节点**（`rf__node-timeline` /
        #   `rf__node-text` / `rf__node-subject` 计数都是 0）⇒ 复刻侧的
        #   `BLOCKED_BY_FIXTURE`。用 `insert()` 把节点插出来，前置态就成立。
        #
        #   ⚠️ 顺便**更正 §83 的一条待办**：那条写「源站文本工具条有『全屏』
        #   入口，复刻没有」。**前提就是错的** —— 复刻有，按钮是
        #   `aria-label="全屏"` / `data-testid="text-expand"`（源码批 817
        #   注释逐字写着「源站第 8 个按钮 aria-label 是『全屏』」）。867 的
        #   探针候选写的是 `aria-label="全屏编辑"`，**候选写错 ≠ 产品没有**。
        #   这正是 864 记的「静态/文本判断当证据」的又一次发作，只是这次
        #   连**待办清单**都被它带偏了。
        if bail_if_dead("J（要先插节点的那三个）"):
            return 2
        for tag, kind, tid, trig, why in [
            ("文本·全屏编辑", "文本", "text-fullscreen",
             '[data-testid="text-expand"]', "文本节点工具条第 8 枚（aria=全屏）"),
            ("时间线·全屏", "时间线", "timeline-fullscreen",
             'button[aria-label="全屏编辑"]', "时间线顶行右簇"),
            ("主体·元数据编辑器", "主体", "subject-metadata-editor",
             '[data-testid="subject-meta-trigger"]', "主体节点「编辑主体」"),
        ]:
            nid = insert(kind)
            if not nid:
                skipped.append(f"{tag}（插不出 {kind} 节点 —— 前置态没成立，"
                               f"**不是**「入口没有」）")
                continue
            if not select_node(nid):
                skipped.append(f"{tag}（{kind} 节点插出来了但选不中）")
                continue
            # ⚠️⚠️ 文本节点：入口按钮**只在编辑态里存在**。这一条是本批
            #    查出来的**机制**（不是推测，源码 + 探针 + 现场转储三方对齐）：
            #      · 源码 `JimengTextNode.tsx:390` 起是 `{editing ? (…格式
            #        工具条…含第 8 枚 `text-expand`…) : null}` ⇒ 编辑态一
            #        掉，入口跟着卸。
            #      · 探针 868 冷启动量到 `editing=True → text_expand=1`
            #        且 `在工具条内 0`（它挂在编辑面**上方那条格式工具条**里，
            #        不是 `.react-flow__node-toolbar`）。
            #      · 审计现场转储（`j_ctx_dump`）：节点选中=True、**编辑面 0**、
            #        工具条 1、aria=全屏 0 ⇒ 正是「编辑态已经掉了」。
            #    ⚠️⚠️ 而编辑态是被**本审计自己**按掉的：`select_node()` 第一
            #    件事是 `clear_selection()` = 按 Escape，而文本节点的
            #    `onEditorKeyDown` 把 Escape 当「取消编辑」。于是
            #    「dblclick 进编辑 → select_node 按 Escape → 入口消失」
            #    **结构上不可能成功**，重试几遍都没用 —— 868 第一版把它记成
            #    「冷启动与审计上下文有差异，⚠️ 未查清」，**那个结论是错的**：
            #    不是环境差异，是准备步骤自己把自己 undo 了。
            if kind == "文本":
                nl = page.locator(f'.react-flow__node[data-testid="{nid}"]')
                if nl.count():
                    try:
                        nl.first.dblclick(timeout=8000)
                        page.wait_for_timeout(1200)
                    except Exception:
                        pass
                # ⚠️ 这里**绝不能**调 `select_node()`（它按 Escape = 取消编辑）。
                #   真要重新选中，用不带 Escape 的那版。
                if not (page.locator(
                        f'.react-flow__node[data-testid="{nid}"].selected'
                ).count() or select_node_soft(nid)):
                    _d = j_ctx_dump(nid, trig)
                    skipped.append(
                        f"{tag}（进了编辑态但节点掉选中："
                        f"编辑面 {_d.get('editing')}）")
                    continue
            # ⚠️ 入口点之前**先问它在不在**：不在就**不点**（点了也没用，
            #    而且会把「前置态没成立」记成「入口坏了」）。
            t = page.locator(trig)
            if not t.count():
                _d = j_ctx_dump(nid, trig)
                skipped.append(f"{tag}（{why}：入口按钮**压根不在 DOM 里** —— "
                               f"前置态没成立，**不是**「入口没有」；现场="
                               f"节点 {_d.get('nodes')}/文本 "
                               f"{_d.get('text_nodes')}/选中 "
                               f"{_d.get('selected_n')} {_d.get('selected')}/"
                               f"编辑面 {_d.get('editing')}/工具条 "
                               f"{_d.get('toolbars')}/aria=全屏 "
                               f"{_d.get('aria_fullscreen_n')}"
                               f"（可见 {_d.get('aria_fullscreen_vis')}）"
                               f"/本节点选中={_d.get('is_selected')} 中心落点="
                               f"{_d.get('hit_center')}）")
                continue
            try:
                t.first.click(timeout=7000)
            except Exception:
                pass
            page.wait_for_timeout(1200)
            if page.locator(f'[data-testid="{tid}"]').count():
                measure(tag)
                page.keyboard.press("Escape")
                page.wait_for_timeout(700)
                if page.locator(f'[data-testid="{tid}"]').count():
                    # ⚠️ 没收干净就**重载**：下一个状态的 `open_layer()`
                    #    认到的还是它（840 栽过：探完不收层，后面每个状态
                    #    都在报同一层）。
                    if not hard_reload(f"收 {tag} 的层"):
                        print(f"    ✗ 放弃：dev server 在收 {tag} 的层时"
                              f"连续 3 次拒连，本次结果**不可信**（退出码 2）")
                        return 2
            else:
                skipped.append(f"{tag}（{why} 点不到或点了层没出现）")

        # ══ K. 批 869：AI 抽屉里的 3 个 `role="dialog"` ═══════════════
        #   867 把这三个记成「本批没逐个探」。本批探了，**三种结果各一个** ——
        #   这本身就是这批的收获：「没探到」至少有三种长得不一样的样子。
        #
        #   ① 会话列表 `canvas-agent-session-menu`：**入口 disabled，进不去**。
        #      源码 `disabled={!hasSession}`、`hasSession = sessions.length > 0`，
        #      而 store 初始 `aiSessions: []`（`jimengStore.ts:913`）⇒ 冷启动
        #      两条会话入口（列表 / 新建）**都** disabled。复刻侧**没有 UI 路径**
        #      建出第一条会话 —— 另一个建会话的入口是 `appendAiMessage`，也就是
        #      **发消息**，那是计费动作，探针/审计**绝不点**。
        #      ⚠️ 所以这是**第三种「没结果」**：入口在 DOM 里、可见、但此刻按不动。
        #      它既不是「入口没有」，也不是「前置态没成立」——
        #      分不开记账，就会有人把 disabled 读成「没接交互」。
        #      ⚠️ 那个 `sessions.length === 0` 的空态分支因此**走不到**
        #      （列表进不去 ⇒ 永远进不了那个 if）。**本批只记录，不删**：
        #      源站无会话时什么样没取样，删掉就是把「没量到」当「不存在」。
        if bail_if_dead("K（AI 抽屉里那三个）"):
            return 2
        for tag, trig, tid, why in [
            ("AI 侧栏·会话列表",
             '[data-testid="canvas-agent-session-menu-trigger"]',
             "canvas-agent-session-menu", "抽屉顶栏「会话列表」"),
            ("AI 侧栏·搜索技能",
             '[data-testid="canvas-agent-skill-trigger"]',
             "agent-skills-panel", "底行「使用技能」"),
            ("AI 侧栏·添加参考",
             '[data-testid="canvas-agent-composer-mention"]',
             "agent-mention-panel", "底行「引用参考」"),
        ]:
            # ⚠️⚠️ 顺序：**先开抽屉，再问入口在不在**。这三个入口都渲染在抽屉
            #   内部（`mx-3 mb-2`），抽屉没开时它们**压根不在 DOM 里**。
            #   869 第一版把这两步写反了，于是三个状态**全部**记成
            #   「入口不在 DOM」—— 看着像三条各自独立的前置态问题，
            #   实际上只是抽屉没开。
            #   这就是「我没检测到」必须先确认「我够得着」那条：
            #   够不着的时候，**不能**把「没够着」写成「它没有」。
            if not page.locator('[data-testid="canvas-agent-drawer"]').count():
                dr = page.locator('button[aria-label="与 AI 对话"]').first
                if dr.count():
                    try:
                        dr.click(timeout=7000)
                    except Exception:
                        pass
                    page.wait_for_timeout(1200)
            t = page.locator(trig)
            if not t.count():
                skipped.append(f"{tag}（{why}：**抽屉已开**而入口仍**不在 DOM "
                               f"里** —— 前置态没成立，**不是**「入口没有」）")
                continue
            if t.first.is_disabled():
                skipped.append(f"{tag}（{why}：入口**在 DOM 但 disabled** —— "
                               f"`hasSession=false`、冷启动无会话，复刻侧没有"
                               f"UI 路径建出第一条；**不是**「入口没有」，"
                               f"也**不是**「没接交互」）")
                continue
            try:
                t.first.click(timeout=7000)
            except Exception:
                pass
            page.wait_for_timeout(1200)
            if page.locator(f'[data-testid="{tid}"]').count():
                measure(tag)
                page.keyboard.press("Escape")
                page.wait_for_timeout(700)
                if page.locator(f'[data-testid="{tid}"]').count():
                    if not hard_reload(f"收 {tag} 的层"):
                        print(f"    ✗ 放弃：dev server 在收 {tag} 的层时"
                              f"连续 3 次拒连，本次结果**不可信**（退出码 2）")
                        return 2
            else:
                skipped.append(f"{tag}（{why} 点不到或点了层没出现）")
        # ⚠️ 抽屉自己**不吃 Escape**（批 839 接的 Escape 只关抽屉里开着的
        #    浮层，关抽屉得点外面/启动器）。留着不收，后面自检的
        #    `open_layer()` 认到的就是它 —— 探针 869 实测「最后抽屉还开着」。
        if page.locator('[data-testid="canvas-agent-drawer"]').count():
            if not hard_reload("收 AI 抽屉"):
                print("    ✗ 放弃：dev server 收 AI 抽屉时连续 3 次拒连，"
                      "本次结果**不可信**（退出码 2）")
                return 2

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
                covered_when_shut = {"covered": None, "tabs": None}
                covered_when_clear = {"covered": None, "tabs": None}
                skin_when_skin = {"covered": None}
                skin_n = 0
            page.keyboard.press("Escape")
            page.wait_for_timeout(400)
            # ⚠️ 批 865 踩过一次：把 `modal_self_test` 直接写进下面这个字典
            #    字面量里。第一版跑出来是 **null** —— 字面量在**建的时候**
            #    就把当时的 `None` 拷进去了，而自检是在这**之后**才跑的。
            #    看着接上了、值是空的，比没接更坏（它会让下一个人以为
            #    「自检跑过了」）。所以改成：先不写，自检跑完再**回填**。
            kb_self = {"layer": probe_layer,
                       "reachable_before": before_kb.get("ok"),
                       "unreachable_when_stripped": after_kb.get("ok") is False,
                       "reachable_after_restore": restored_kb.get("ok"),
                       "covered_probe_layer": deep_layer,
                       "skin_n": skin_n,
                       "skin_top_n": skin_top_when_skin,
                       "clear_covered": covered_when_clear.get("covered"),
                       # ⚠️ 批 863 补：`shut_covered` 之前**没记进结果**。于是
                       #    「每条 finding 指名了被谁盖住」这条契约（verifier G.3b）
                       #    只能拿**产品当下真有的缺陷**来验 —— 缺陷一修好，契约
                       #    自己就红了。阳性夹具明明保证这里一定有 finding，
                       #    却没把它记下来，白白让一条断言绑在产品状态上。
                       "shut_covered": covered_when_shut.get("covered"),
                       # ⚠️ 同批补：自检**灵敏度**要看得见。正向夹具实测
                       #    `covered_n_when_shut` 只有 1（旧版搜索面板同一夹具
                       #    是 32）—— 因为新面板第一次 Tab 就在层内（§79 的定论），
                       #    整趟只采了 1 个焦点位。这不是缺陷，但「自检从 32 个
                       #    焦点位缩到 1 个」是**判据覆盖面缩小**，必须记在案，
                       #    不许只写在结论段的散文里。
                       "walked_when_shut": covered_when_shut.get("tabs"),
                       "walked_when_clear": covered_when_clear.get("tabs"),
                       "skin_covered": skin_when_skin.get("covered"),
                       "covered_n_when_skin": skin_when_skin.get("covered_n"),
                       "covered_n_when_shut": covered_when_shut.get("covered_n"),
                       "covered_n_when_clear": covered_when_clear.get("covered_n")}
        else:
            kb_self = {"layer": probe_layer, "why": "自检用的那层没打开"}
        close_open()
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)

        # ══ 批 865 自检：模态语义判据**能红**吗？════════════════════════
        #   上面那套自检管的是 covered/skin。这一条新判据必须有**自己的**
        #   自检，否则「模态却没接管焦点」可能就是一句恒真的空话。
        #   做法与夹具一/二同款：**注入一个合成的阳性夹具** —— 一层
        #   `position:fixed; inset:0` + 不透明底 + 带一枚可聚焦按钮的
        #   `role=dialog`，**刻意不给它焦点**。判据若真的在干活，就必须
        #   同时认出「它是模态」且「开层焦点不在层内」—— 这正是它报缺陷
        #   的那组输入。
        #   ⚠️ 只验判据的**输入**成立；「它会不会被列进 kb_modal_no_focus」
        #     由退出码那一行的桶名保证（verifier R 组钉住桶名接进退出码）。
        page.evaluate("""() => {
          const d = document.createElement('div');
          d.setAttribute('data-testid', 'kb-self-test-modal');
          d.setAttribute('role', 'dialog');
          d.setAttribute('aria-label', '自检合成模态');
          d.style.cssText = 'position:fixed;inset:0;z-index:99997;'
                          + 'background:rgb(20,20,20);display:flex;'
                          + 'align-items:center;justify-content:center';
          const b = document.createElement('button');
          b.type = 'button';
          b.textContent = '自检按钮';
          d.appendChild(b);
          document.body.appendChild(d);
        }""")
        page.wait_for_timeout(400)
        # 刻意**不** focus：焦点此刻还在页面上别处
        modal_self = page.evaluate("""(tid) => {
          const el = document.querySelector(`[data-testid="${tid}"]`);
          if (!el) return {ok: false, why: '合成模态没插进去'};
          const vw = innerWidth, vh = innerHeight;
          const opaque = (n) => {
            const bg = getComputedStyle(n).backgroundColor || '';
            return bg !== 'rgba(0, 0, 0, 0)'
                && !bg.startsWith('rgba(0, 0, 0, 0)');
          };
          const r = el.getBoundingClientRect();
          const pos = getComputedStyle(el).position;
          const is_modal = (pos === 'fixed' || pos === 'absolute')
                           && r.width >= vw * 0.9 && r.height >= vh * 0.9
                           && opaque(el);
          const a = document.activeElement;
          return {ok: true, is_modal: is_modal,
                  pos: pos, opaque: opaque(el),
                  covers: r.width >= vw * 0.9 && r.height >= vh * 0.9,
                  focus_inside: !!(a && el.contains(a)),
                  al: a ? (a.getAttribute('aria-label') || a.tagName) : 'body'};
        }""", "kb-self-test-modal")
        page.evaluate("""() => document.querySelectorAll(
            '[data-testid="kb-self-test-modal"]').forEach(e => e.remove())""")
        page.wait_for_timeout(300)
        kb_self["modal_self_test"] = modal_self

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

    # ══ 批 866：分桶改成**一次性互斥划分** ═══════════════════════════
    #   原来四个桶是四个独立的列表推导，**没有任何机制保证它们不重叠** ——
    #   于是 865 发现 `by_modal` 里的行也被 `unconfirmed` 数了一遍
    #   （124 ≠ 0+116+8），866 加 `by_layer` 之后又重叠一次
    #   （124 ≠ 0+120+9+0）。两次都是同一根病：**各算各的，没人管总和**。
    #   改成一行分派：每行**有且只有一个**桶，「各桶之和 == 候选数」从此是
    #   **结构保证**，不是希望。verifier S 组钉住这条恒等式。
    #
    #   判定顺序就是严重程度顺序，且**逐条保留旧语义**：
    #     1) 缺陷：已确认 + **同一层自己压自己**（`same_layer`）—— 835 定的
    #     2) 被**全屏模态遮罩**盖住（INFO）—— 关掉模态就能点
    #     3) 被**非全屏浮层的内容**盖住（INFO，866 新增）—— 画布其余部分
    #        还看得见、还点得着
    #     4) 已确认的**跨层**遮挡（INFO）—— **835 的降级条款**，原封不动
    #     5) 剩下的：既没确认、也没被任何浮层解释掉 ⇒ 认不出归属，**不瞎分**
    def _bucket(r: dict) -> str:
        if r["confirmed"] and r.get("same_layer") \
                and not r.get("covered_by_modal"):
            return "defect"
        if r.get("covered_by_modal"):
            return "by_modal"
        if r.get("covered_by_layer"):
            return "by_layer"
        if r["confirmed"]:          # 835 降级条款：确认过的跨层遮挡是 INFO
            return "by_modal"
        return "unconfirmed"

    real = [r for r in rows if _bucket(r) == "defect"]
    by_modal = [r for r in rows if _bucket(r) == "by_modal"]
    # 批 866：与 `by_modal` **分开**记，不塞进去 —— 前者是「被**全屏模态的
    # 遮罩**盖住」/「已确认的**跨层**遮挡」（835 的降级条款），后者是「被某个
    # **非全屏浮层的内容**盖住、而且还没被活页面确认」。三者严重程度不同，
    # 混成一栏就看不出是哪一种。
    #
    # ⚠️ 866 自己在这行翻过一次车：补丁只匹配到 `by_modal = [...]` 的**第一
    #    行**，把续行 `or (r["confirmed"] and not r.get("same_layer"))` 落下
    #    了 —— 那是 835 的**降级条款**，掉了就等于「确认过的跨层遮挡」重新
    #    变成未确认。**只匹配到一半的多行模式，比不匹配更危险**：它不报错，
    #    只是悄悄改了判据。py_compile 也没抓到（孤立的续行恰好合法）。
    by_layer = [r for r in rows if _bucket(r) == "by_layer"]
    unconfirmed = [r for r in rows if _bucket(r) == "unconfirmed"]
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
    # ⚠️⚠️ 批 852 更正：`arrows_move` 从 None 改成实测值。
    #    850/851 都记成「没测到」，而探针 852 查明**测到了** ——
    #    两个判据缺陷把它盖住了：
    #      ① `moved` 只对「按完之后」的 4 个点去重，**漏掉了按之前的起点**。
    #         源站这六层都是「**走一步就停**」：`16:9` → `1` → `1` → `1` → `1`
    #         去重后 1 个 ⇒ moved=False。**第一次移动恰恰发生在起点→第一次之间**。
    #      ② 判断「层里哪些可聚焦」时**真的调了 `focus()`**，把起点推到了最后
    #         一个能聚焦的项上（846 早写过：判断可聚焦性不能真的去 focus）。
    #
    #    源站实测（探针 852，登录态，视口 1512×1200）：
    #      模型 9 项 / 尺寸 14 项 / 模式 2 项 / 音色模型 2 项 ⇒ 动 ⇒ True
    #      时长层焦点在 `SPAN/slider` ⇒ **slider 自己吃方向键**，焦点不动
    #      音频·生成模式**只有 1 个选项** ⇒ 无处可动
    #    ⚠️ 源站是**漫游 tabindex**（一个 ti=0、其余 ti=-1）却**不更新 tabindex**
    #    ⇒ 走一步就再也走不动。这是源站自己的取舍，**照抄不修**。
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
            "arrows_move": True, "esc_returns_to_trigger": False,
            "src": "jimeng_probe850_genpanel_kb.py（登录态，视口 1512×1200）"},
        "gen-video-size-listbox": {
            "src_tid": "(无 testid)", "src_kind": "dialog",
            "src_identified_by": "role=dialog + 矩形 334×292 @[867,844]（探针 850）",
            "takes_focus_at_open": True, "traps_tab": False,
            "arrows_move": True, "esc_returns_to_trigger": False,
            "src": "jimeng_probe850_genpanel_kb.py（登录态，视口 1512×1200）"},
        "gen-mode-listbox": {
            "src_tid": "(无 testid)", "src_kind": "listbox",
            "src_identified_by": "role=listbox + 矩形 200×84 @[1041,1052]（探针 850）",
            "takes_focus_at_open": True, "traps_tab": False,
            "arrows_move": True, "esc_returns_to_trigger": False,
            "src": "jimeng_probe850_genpanel_kb.py（登录态，视口 1512×1200）"},
        "gen-duration-listbox": {
            "src_tid": "(无 testid)", "src_kind": "dialog",
            "src_identified_by": "role=dialog + 矩形 400×100 @[1006,1036]（探针 850）",
            "takes_focus_at_open": True, "traps_tab": False,
            "arrows_move": False, "esc_returns_to_trigger": False,
            "src": "jimeng_probe850_genpanel_kb.py（登录态，视口 1512×1200）"},
        # ══ 批 851：音频生成面板 2 层（源站取到样）══════════════════════
        # 850 结尾写「音频那 5 个下拉仍记 kb_not_sampled」，但那句话里藏着一个
        # **没验证过的前提**：为什么取不到？851a 侦察的答案是 —— 源站这一版
        # 画布**能插音频节点**（点左栏 `音频` → 新增 `音频 1`），选中后**真的有**
        # 下拉触发器。所以这 5 层**不是 BLOCKED_BY_FIXTURE**，是能取样的。
        #
        # 851b 实取到的**只有 2 层**（登录态，视口 1512×1200，与 850 同口径）：
        #   · 接管焦点（焦点落在层内 option 的 BUTTON 上）
        #   · **不困 Tab**（第 1 次就逃出，且层还在）
        #   · Esc 后焦点**不回触发器**（落到节点 / 顶栏控件）
        #   · 方向键 **没测到**（见 `arrows_move: None`）
        # 另外 3 层**没取到**，原因各不相同，逐条写在 NOT_SAMPLED 里 ——
        # 笼统写一句「没取过样」会把「前置态没成立」和「判据量错对象」
        # 混成同一种，而这两者的下一步动作完全相反。
        "audio-voice-model-listbox": {
            "src_tid": "(无 testid)", "src_kind": "listbox",
            "src_identified_by": "role=listbox + 矩形 400×180（探针 851b）",
            "takes_focus_at_open": True, "traps_tab": False,
            "arrows_move": True, "esc_returns_to_trigger": False,
            "src": "jimeng_probe851b_audiopanel_kb.py（登录态，视口 1512×1200）"},
        "audio-gen-mode-listbox": {
            "src_tid": "(无 testid)", "src_kind": "listbox",
            "src_identified_by": "role=listbox + 矩形 200×44（探针 851b）",
            "takes_focus_at_open": True, "traps_tab": False,
            "arrows_move": False, "esc_returns_to_trigger": False,
            "src": "jimeng_probe851b_audiopanel_kb.py（登录态，视口 1512×1200）"},
        # ══ 批 853：又把 2 层从 kb_not_sampled 升进基线表 ═════════════════
        # 851/§70 记的 3 层「测不到」，853 拆开之后**两层真取到样、一层是
        # 源站事实**。过程见 README §71，两条方法论值得单列：
        #  · **③ 方向键必须排在 ② Tab 之前测**（853c）。① 已经把「层刚打开、
        #    焦点自然落在层内」这个最好的起点建好了；② 那串 Tab 是**破坏性**的
        #    （源站这几层第 1 次就逃出）。853b 把 ③ 排在 ② 之后，就得 ensure_open
        #    再 `focus()` 重建起点 —— 而源站**对 `focus()` 反应不稳**（音乐模型层、
        #    音色库层连着两次「focus() 后焦点仍不在层内」），于是白交两份「没测到」。
        #    这与 852 病根②同源：**别为了「建立起点」去动它，用天然的那个。**
        #  · 认层**换判据不解决判据量错对象**：851b 用矩形差分抓到整页容器，
        #    853b 改用「取最近公共祖先」**又**抓到整页（该 class 实测 63 个 chip
        #    散布整个画布节点区）—— 同一个错的两面。真正管用的是
        #    `mark_voice_panel()`：**从标题「全音色」往上找「装 ≥8 个可见 chip
        #    且面积 < 半个视口」的最小祖先**，才落到真正的 680×96 面板。
        "audio-music-model-listbox": {
            "src_tid": "(无 testid)", "src_kind": "listbox",
            "src_identified_by": "role=listbox + 矩形 400×112（探针 853b）",
            "takes_focus_at_open": True, "traps_tab": False,
            # ⚠️ False 的原因是**内容只有 1 项**（SeedMusic 1.0 Preview），
            #    轨迹实测 4 次全停在同一项 ⇒ 无处可去。**不是**「源站方向键坏了」。
            "arrows_move": False, "esc_returns_to_trigger": False,
            "src": "jimeng_probe853b_audiostruct_kb.py（登录态，视口 1512×1200）"},
        "audio-all-voices-listbox": {
            "src_tid": "(无 testid)", "src_kind": "面板（既非 listbox 也非 dialog）",
            "src_identified_by": (
                "标题「全音色」+ ≥8 个 `min-w-canvas-audio-voice-shrinkable` "
                "chip + 面积<半视口的最小祖先 ⇒ **680×96**（探针 853b/c，"
                "探针 854 连续 8 次采样恒为 96、scrollH==clientH 无内部滚动 "
                "⇒ 96 是**稳定态**）"),
            # ⚠️ 854 更正：853b 曾在 `ensure_open` 重开时量到 **680×328**，
            #    一度以为这一层会变形。**不是** —— 328 是 `mark_layer` 的
            #    role/class 启发式**认错了元素**（音色库既非 listbox 也非
            #    dialog，被它匹配到别的块去了）。修法：`measure_kb()` 新增
            #    `remark=` 参数，**用当初认出这一层的同一个认法**重开。
            #    记在这里，免得半年后有人量到 328 以为判据坏了。
            # ⚠️ **这是 15 层里唯一开层不接管焦点的**：焦点自始至终停在
            #    触发器 `BUTTON/音色: 音色库` 上，**从没进过面板**。
            "takes_focus_at_open": False, "traps_tab": False,
            # 没测到，而且**是测到了「测不到」这件事本身**：焦点不在层内 ⇒
            # 没有层内起点可按方向键。与「判据没测到」要分清。
            # ⚠️ 理由写成**字段**而不是只写在注释里：判据要能机读，否则半年后
            #    分不清它是「测到了测不到」还是「忘了测」。
            "arrows_move": None,
            "arrows_move_why": (
                "焦点自始至终停在触发器上、**从没进过面板** ⇒ 层内没有起点，"
                "按方向键无从谈起。**这不是「判据没测到」**，"
                "是测到了「源站这一层开层不接管焦点」这个事实本身。"),
            "esc_returns_to_trigger": True,
            "src": "jimeng_probe853b_audiostruct_kb.py（登录态，视口 1512×1200）"},
        # ══ 批 871：音色库的**筛选下拉**（`性别 options`）══════════════
        #   870 把版式按源站实测对齐了，**键盘行为**当时一概没取 ⇒ 复刻那一层
        #   一直挂在 `kb_not_sampled` 里，不受任何判据管。871 取完样入表。
        #   ⚠️ 每一项都**单独验过前置态**才记（探针 871 头两版栽在这儿：
        #   ② 连按 40 次 Tab 途中层**已经被关掉**，导致 ③④ 的读数全是
        #   「层不存在」——长得跟真结论一模一样。修法是 `reopen_filter()`
        #   + 每项先验证前置态成立）。
        #
        #   ══ 批 872：把另外三个钮**逐个**也取了一遍 ══════════════════
        #   871 只取了「性别」，当时明写「不许拿同一个组件推测」。872 照做：
        #   四个钮**逐个**开、逐个量，五项行为**完全一致** ——
        #     性别 161×124/3 项、年龄 161×244/6 项、语言 161×164/4 项、
        #     声音特点 161×244/6 项；
        #     ①开层接管焦点到第一项 ②40 次 Tab 不经过（capped）
        #     ③层内第 1 次 Tab 就逃出（不困） ④方向键 0→1→2 ⑤Esc 收层回钮。
        #   ⇒ 下面这些字段现在是**四个实测**的共同结论，不是从「性别」外推的。
        #   高度实测公式 `h = n×36 + (n−1)×4 + 8`（124/164/244 三点全中），
        #   复刻侧内容驱动（`gap-1` + `p-1`）⇒ 天然一致，本批**没改版式**。
        "audio-voice-filter-listbox": {
            "src_tid": "(无 testid)", "src_kind": "listbox",
            "src_identified_by": (
                "role=listbox + aria-label=`{label} options`（如 `性别 options`）"
                "+ 宽 **161**、高 `n×36+(n−1)×4+8`（3/4/6 项 ⇒ 124/164/244，"
                "三点全中）+ `role=option` 若干"
                "（探针 870 版式 / 871+872 键盘，登录态，视口 1512×1200；"
                "**四个筛选钮逐个实测**）"),
            # 871 ①：开层**那一刻**焦点就落在**第一项** option
            #（`全部 性别`，idx=0）。复刻原先开层完全不接管焦点。
            "takes_focus_at_open": True,
            # 871 ③：从层内**第 1 次** Tab 就逃到下一个筛选 chip（`年龄`）
            # ⇒ 源站**不困** Tab。所以复刻**刻意不接** `useModalFocusTrap`。
            "traps_tab": False,
            # 871 ④：方向键在层内**逐格移动**（idx 0 → 1 → 2，共 3 项）。
            "arrows_move": True,
            # 871 ⑤：Esc **收层**，焦点回到那个筛选钮（实测落点
            # `BUTTON/性别`）。
            "esc_returns_to_trigger": True,
            # 871 ②：Tab **压根不经过**这一层（40 次上限内没走到，轨迹全程
            # 在音色库 chip 上）。⚠️ 这**不是**「Tab 进不去」——是「Tab 序列
            # 里没有它」：开层即把焦点放进来，用不着 Tab 进来。
            # 记成字段而不是注释：否则半年后有人读到 `walk=None` 会当成缺陷。
            "walk_note": (
                "源站这一层**不靠 Tab 进出**（40 次 Tab 全程在音色库 chip 上，"
                "capped=True）。与 `traps_tab=False` 是同一件事的两面。"),
            # 874：选完值按 Esc，**选中值保留**（复开层读 `aria-selected`，
            # 仍是 `男: true`）—— 收层 ≠ 取消选择。这条把 873 留下的
            # **唯一一个自选行为**（源站未取样）变成了实测。
            # ⚠️⚠️⚠️ 887 **限定了适用范围**（第一版这里写得太宽，是错的）：
            #   874 那一跑**层是开着的**（为了读 `aria-selected` 特意重开过层）。
            #   887 在**层收着**时测同样条件 ⇒ **值被清**（重开音色库读芯片
            #   文案 `'男' → '性别'`、Clear 重开后不在）。
            #   ⇒ **层开着 ⇒ 保留；层收着 ⇒ 被清**。两条并存。
            #     Esc 的行为由**两个**变量决定：**焦点在哪**（§95/§96）
            #     **和层开没开**。只测其中一条就会测反 —— 874 就测反了。
            "esc_keeps_value": True,
            "esc_keeps_value_仅在层开着": True,
            "esc_keeps_value_when_layer_closed": False,
            "esc_depends_on_layer_open_too": True,
            # 875：「没设值」在源站**不是**「什么都不选中」，而是
            # **`全部 {筛选名}` 那一项 aria-selected=true**（4/4 实测：
            # 刚开层时、以及点完 Clear 之后都是）。
            # ⚠️ 873 抄 `aria-label` 时**只抄了一半**：注释里记着未选中时
            # 读作 `BUTTON/性别: 全部 性别`，代码却写成 `?? label` ⇒ 读出
            # `性别: 性别`。875 复测 4/4 并改正。
            "no_value_means_all_selected": True,
            "trigger_aria_when_unset": "{label}: 全部 {label}",
            "trigger_aria_when_set": "{label}: {值}",
            "trigger_text_when_unset": "{label}",
            # 875：选中之后芯片右边冒出一个 16×16 的清除钮，
            # `aria-label="Clear {筛选名} filter"`（**英文**，逐字照抄）。
            # 四个筛选钮**逐个**量，4/4 一致。未选中时不存在。
            "has_clear_button": True,
            "clear_aria": "Clear {筛选名} filter",
            "clear_rect_when_shown": "16×16，垂直居中，横向在芯片右侧 8",
            "clear_behavior": (
                "点它 ⇒ 值回落到「全部 {筛选名}」→ 它自己消失 → "
                "焦点回到芯片（aria 变回 `{label}: 全部 {label}`）"),
            # 876：清除钮的**键盘**行为（探针 876/876b/876c，876c **三次复现**一致）
            # 877：把这四条**四个筛选钮逐个**重测（6/6 项全中），从
            # 「只测过性别」升格为「四钮的共同结论」。§69：按同类推测
            # 不许当结论 —— 不补测就得把基线降级，这批选了补测。
            # 探针里**一次只让一个钮有值**：都选中时 Tab 序列是
            # 芯片→Clear→年龄→年龄的Clear→…，分不清哪个 Clear 是谁的。
            # 逐钮实测的 Tab 轨迹（4/4 一致的规律）：
            #   **Clear 紧跟本钮芯片** → **后面**的筛选钮（无值态）→ 音色网格
            "clear_in_tab_order": True,
            "clear_sampled_on": "**四个筛选钮逐个**（877，6/6 项全中）",
            "clear_tab_after_chip": True,
            "clear_enter_fires": True,
            "clear_space_fires": True,
            "clear_arrows_dead": True,
            # ⚠️ Esc 的行为**由焦点位置决定** —— 这是本批最容易记错的一条：
            #   焦点在**芯片**上按 Esc  → 只收层，**值保留**（874 实测）
            #   焦点在 **Clear** 上按 Esc → **清除**，而且**同时**关掉
            #                                     整个音色库面板、焦点落到
            #                                     **音频节点本体**
            "clear_esc_fires": True,
            "clear_esc_also_closes_voices": True,
            "esc_depends_on_focus": True,
            # 877/878：Clear 上 Esc 之后焦点落在**该音频节点本体**
            # （源站 `BUTTON/音频 node: 音频 NN`）。
            # ⚠️ 这里**不能**照抄 `38` / `NN` —— 那是**节点序号**，
            # 逐轮插节点就变，是**易变量**（§70）。只记「落在该节点本体」。
            "clear_esc_focus": "该音频节点本体（BUTTON/音频 node: 音频 {序号}）",
            "clear_esc_focus_note": (
                "序号是易变量，不许钉。复刻侧节点**可以**被聚焦"
                "（878 实测 tabindex=0、5/5 程序化 focus 成功、Tab 能进）"
                "⇒ 焦点掉 body 不是必然，是实现疏忽。"),
            # 880/881 复刻侧的机制链（**记在基线里**，免得半年后重查一遍）：
            #   878 `closest('.react-flow__node')` → 无效（NodeToolbar 是 portal）
            #   879 改走 `data-id`               → 仍无效
            #   880 手工 replay 全可行          ⇒ 排除「focus 不可行」
            #   881 焦点**事件流**：+3~6ms focusin 节点（**同步 focus 成功**）
            #       → +46~56ms blur（**被某个延迟动作抢走**）
            #       → 节点 DOM **没被替换**（标记还在、isConnected、同一个元素）
            #   ⇒ 同步落焦点**不够**，必须在那个动作**之后**补落。
            # ⚠️⚠️ 882：**根因查到了**，881 那条「未查明」作废。
            #   抓 vendor chunk 定位到 `@xyflow/react` 的 `useNodesSelection`：
            #     } else if (unselect || node.selected && multiSelectionActive) {
            #        unselectNodesAndEdges({nodes:[node], edges:[]});
            #        requestAnimationFrame(() => nodeRef?.current?.blur());
            #     }
            #   Esc ⇒ 面板关 ⇒ 节点**失去选中态** ⇒ 该分支触发 ⇒ 它在自己的
            #   rAF 里 `blur()`。而组件里那个 rAF 是**同步注册**的（事件处理里），
            #   它是**状态更新后那次渲染里**注册 ⇒ **同一个 rAF 队列里它排后面**
            #   ⇒ blur 赢。这才是「同步 focus 成功、~50ms 后被抢走」的**全部原因**。
            #   根修 = **双层 rAF**（第二层排在 React Flow 之后）：
            #   实测 blur +355ms → 补落 +356ms，间隔 **1ms**（原 120ms 兜底方案
            #   的时间窗是 ~120ms）。120ms 保留为兜底。
            # ⚠️ **仍未验证**：双 rAF 能否保证排在 React Flow 之后 —— 那是
            #   **注册顺序**的性质，不是契约。
            # （885 已把这条疑点**查清并作废**，见下面的字段）
            # ⚠️ 885 **作废**了「更根本的疑点」那条。答案：
            #   **源站 Esc 之后节点也取消了选中**（实测：音频生成工具条
            #   `True → False`），但**焦点仍落在该节点本体**上。
            #   ⇒ 「取消选中」**不是**差异，两边都取消。
            #   ⇒ 差异**只**在「blur 之后有没有人把焦点抢回来」——
            #     源站有，复刻 882 的**双层 rAF 补的正是这一件**，
            #     所以 882 **治对了，不是治症状**。
            # ⚠️⚠️ 885 只试了 `center` 一个策略就命中（备胎没派上用场），
            #   「五种策略都可靠」这个结论**只由 884 支撑**（那里每个 2/2）。
            #   885 的「策略备胎」机制**没被检验过**。
            "clear_esc_node_unselected_too": True,
            # 886：**芯片**上按 Esc 是**另一条路径、同一个落点**。
            #   源站实测：焦点落**该音频节点本体**（`音频 node: 音频 44`），
            #   节点**也**取消选中（工具条 True→False）。
            #   ⇒ 复刻原先落 `body` 是**真差异**，已修（芯片也接同一个
            #     模块级 `refocusToNodeFromToolbar`）。
            # ⚠️⚠️ 887 **证伪了**第一版写的「芯片那条**不**清值」：在**层收着**
            #   时（芯片能拿到焦点的唯一情形）Esc **清值**。
            #   ⇒ 两条路径现在**完全一致**：都清值、都关层、焦点都落该节点本体。
            #   「不碰 filterSel」那句只对**层开着**成立，而那时芯片这个
            #   handler **压根不会触发**（焦点在层内）。
            "chip_esc_focus": "该音频节点本体（同 Clear 那条落点，886 实测）",
            "chip_esc_node_unselected_too": True,
            "chip_esc_clears_value_when_layer_closed": True,
            "clear_esc_focus_mechanism": (
                "源站也取消选中、也会 blur，但**blur 之后焦点仍落在节点本体**"
                "（工具条 True→False + 焦点 `音频 node: 音频 NN`，885 实测）。"
                "⇒ 差异只在「blur 之后有没有人把焦点抢回来」；"
                "复刻 882 的**双层 rAF** 补的正是这一件，**治对了**。"
                "复刻侧根因是 `@xyflow/react` 的 `useNodesSelection` —— "
                "节点失去选中时它在 `requestAnimationFrame` 里 "
                "`nodeRef.blur()`，而我们的 rAF 注册得**更晚/更早**导致排队输了。"),
            # ══════ 889：把「Esc 落点」从**两次互不相干的读数**变成**一条规则** ══════
            # 888 读到落点 `Canvas`，885/887 读到「节点本体」。889 第一版把
            # 前者写成「第四条 Esc 路径」—— **没量就下的结论**，已收回。
            # 889/889b/889c 逐个前置态各 2/2 之后，规则是：
            #   **落点 = 按 Esc 之前焦点在哪**（唯一的自变量）。
            "esc_landing_rule": (
                "**落点由「按 Esc 之前焦点在哪」决定**（889/889b/889c 各 2/2）："
                "焦点在芯片/Clear/节点本体 ⇒ 落**该音频节点本体**（工具条 True→False）；"
                "焦点在**筛选层内**的选项 ⇒ **回到筛选芯片**、工具条**仍 True**、"
                "**只关层不收面板**；焦点在**画布**上 ⇒ **原地不动**。"
                "⇒ 888 那个 `Canvas` 不是「第四条路径」，是它那跑按 Esc 前"
                "**焦点本来就在画布上**（889c 隔离出变量 = 那次 `blank()`，2/2）。"),
            "esc_landing_by_precondition": {
                "芯片": "节点本体", "Clear": "节点本体", "节点本体": "节点本体",
                "筛选层内": "回到筛选芯片（工具条 True、只关层）",
                "画布": "原地不动（仍在画布）",
            },
            "esc_landing_n": "每档 2/2（889 源站 4 档 + 889b 2 档 + 889c 1 档）",
            "layer_open_esc_keeps_value": (
                "889b 实测（2/2，**同一次运行**里读落点和值）：层开着、焦点在层内 "
                "按 Esc ⇒ 落点=芯片、工具条 True、层关、**值 `'男' → '男'` 保留**。"
                "⇒ **874 那条「值保留」在它自己的前置态里复核通过**，§98/§99 记的"
                "「没有同一次运行的证据」这条缺口**闭合**；"
                "而 887 的「层收着时被清」是**另一档**，两条**并存不冲突**。"),
            "canvas_root_is_focusable": (
                "889d 实测：源站画布**根容器** `.react-flow` 带 "
                "`role='application'` + `aria-label='Canvas'` + **`tabindex='0'`**，"
                "class 里有 `focus:outline-none`（作者明确为「它会获得焦点」写的）。"
                "⇒ 点画布空白时焦点落在**这个根容器**上（实测），"
                "**不是** `.react-flow__pane`（它 `tabindex=None`、点了没焦点）。"),
            "replica_canvas_root_tabindex_FIXED_889": (
                "复刻 801 抄了 `role`/`aria` 却**漏了 `tabindex`** ⇒ 复刻画布根"
                "**不可聚焦**，点空白时焦点掉到 `body`。889 已补 "
                "`if (!hasAttribute('tabindex')) setAttribute('tabindex','0')`，"
                "补后复刻点空白 ⇒ 焦点 `'Canvas'`（2/2）、"
                "「焦点在画布上按 Esc ⇒ 落 `Canvas` 原地不动」2/2，**与源站一致**；"
                "verifier 251/251 未被打破。"),
            "open_diff_node_click_takes_focus": (
                "⚠️ **仍然存在的差异，机制已定位到一层、但未钉死**：源站「点空白 → "
                "再点节点中心」之后焦点**留在画布**（889c 2/2），复刻**被节点抢走**"
                "（889b_ck `click_focus` 2/2 `node_took_focus=True`）。"
                "890b/890c（同一套判据，两边各 2/2）把机制查到这一层："
                "· 源站有一次**应用主动 `focus()`，目标是画布根**：序列 A 里"
                "「当时已是焦点=True」⇒ **空操作**；序列 B 里「当时已是焦点=False」"
                "⇒ 真的把焦点搬到画布根（= focusin #1），随后 focusin #2 才是"
                "**浏览器原生**把焦点移到节点。"
                "· **复刻侧 JS 调 `focus()` 的次数是 0**（890c，两序列各 2/2）"
                "⇒ 焦点移动是**纯浏览器原生**的。"
                "⇒ 也就是说：源站是「应用把焦点钉在画布根 + 浏览器随后不移动」，"
                "复刻是「浏览器直接原生移动到节点」。"
                "⚠️⚠️ **仍未验证、不许当结论**："
                "① 源站节点那次 `mousedown` "
                "**有没有被 `preventDefault()`** —— ⚠️⚠️ **892 已测掉："
                "没有**（见 `src_site_preventdefault_False_892`）。"
                "890b 当初读不到（挂在 `document` 冒泡阶段、事件**没冒泡到** "
                "document、读数是**空数组**），892 改成「捕获阶段存事件引用、"
                "**派发结束后**再读」才读到 ⇒ **读不到不代表没有**，"
                "但这一格**如今有答案了**；"
                "② ⚠️⚠️ **891 已把这条「浏览器规则」假设证伪**（见 "
                "`mousedown_focus_rule_refuted_891`）—— 上面那句"
                "「焦点在画布根 ⇒ 落点在其子树内 ⇒ 浏览器不移动」**是错的**，"
                "最小复现里 C1 格子就是直接反例。所以源站 A 序列 `focusin=0`"
                "**不是**浏览器规则造成的，**只可能**是源站自己 "
                "`preventDefault()` 了（891 的 C3 证明只有 `preventDefault` "
                "能挡住，`stopPropagation` 挡不住）。"),
            "mousedown_focus_rule_refuted_891": (
                "⚠️⚠️ **891 用最小复现把一条「看起来很合理」的规则证伪了。**"
                "被证伪的假设：「mousedown 落点在当前焦点元素的子树内 ⇒ "
                "浏览器不移动焦点」。"
                "最小复现（空白页、不跑源站；每格 2/2，六格全稳定）："
                "· C1 焦点在落点的**可聚焦祖先**上 ⇒ **会动**（移到可聚焦子元素）"
                "  ← **这就是那条假设的直接反例**"
                "· C2 焦点在祖先外面 ⇒ 会动"
                "· C3 mousedown 被 **`preventDefault()`** ⇒ **不动**"
                "· C4 mousedown 被 **`stopPropagation()`**（**不**阻止默认）⇒ **会动**"
                "· C5 祖先**不可聚焦** ⇒ 会动（所以「祖先可聚焦」不是前提）"
                "· C6 落点**自己可聚焦** ⇒ 会动（所以「落点不可聚焦」不是前提）"
                "⇒ **只有 `preventDefault()` 能阻止浏览器移动焦点**。"
                "⇒ 方法论教训：**「读数能这么解释」不等于「这条规则成立」**。"
                "一条假设必须能被**单独控制变量**的最小复现**证伪**，"
                "否则它只是对读数的归纳（§77）。"),
            "mechanism_hypothesis_must_survive_minimal_repro": (
                "⚠️ 方法论（891 证伪那条假设之后写下的）："
                "**「读数能这么解释」不等于「这条规则成立」。**"
                "一条机制假设要能被采信，得**同时**满足两条："
                "① 它能解释**全部**相关读数；"
                "② 它**扛得住**一个专门为证伪它设计的**最小复现**。"
                "第 ② 条是新的 —— 891 之前一直只做第 ① 条，"
                "于是把「焦点在可聚焦祖先内 ⇒ 浏览器不移动」当成了机制；"
                "而它**在空白页上就被证伪**了。"
                "⇒ **验机制不必每次回源站**：能在空白页/最小夹具上做的，"
                "就做在那儿（快、无需登录、且变量能逐个控制）。"
                "⚠️ 反过来说：空白页**证不了**源站自己的行为 —— "
                "它只否掉「这是浏览器规则」这类**通用**假设。"),
            "verifier_does_not_read_readme": (
                "⚠️ 刻意的：verifier **不读** `docs/research/jimeng-canvas/"
                "README.md`。所以改文档**不必**重跑 verifier，"
                "也不会因为别人改文档而把门禁搞红。"
                "⇒ 代价：凡是**要钉住**的东西，必须同时落在**基线**（本文件）"
                "或**源码/探针**里，钉在 README 上是钉不住的。"),
            "src_site_preventdefault_still_unmeasured": (
                "⚠️⚠️ **892 已经把这一格测掉了（结论：源站**没** preventDefault）**，"
                "所以本条**已被 892 取代**，保留是为了记录取法的演进。"
                "891 当时的取法（已跑）：**捕获阶段**先保存事件对象的**引用**，"
                "等派发**结束**后再读那个对象的 `defaultPrevented` —— "
                "事件对象在派发结束后仍保留**最终**值，"
                "这样就绕开了「读的时候 handler 还没跑完」。"
                "⇒ 见 `src_site_preventdefault_False_892`。"),
            "src_site_preventdefault_False_892": (
                "892 实测（A/B 两序列各 2/2，**事后读** `defaultPrevented` 这个"
                "读法是可靠的 —— 事件对象派发结束后仍保留**最终**值）："
                "**False / False**。⇒ **源站那次 `mousedown` 没有被 "
                "`preventDefault()`**。"
                "⇒ 891 收窄出的「唯一候选」**被否掉了**。"),
            "click_moment_node_not_focusable_893": (
                "✅ **893 把 §103 那个矛盾解开了**（A/B 各 2/2，两序列读数"
                "**内部一致**：同一个节点、同一状态，**只差点过空白**）："
                "· A（先点空白再点节点）：落点 target 的 **`isConnected=False`**"
                "（那个 `path` 元素已被 React 重渲染**摘掉**）、"
                "节点 **`tabindex=None` / `tabIndexProp=-1`**（**那一刻不可聚焦**）、"
                "MutationObserver 记到 **22 条**变化（class 加 `selected`、"
                "`data-node-selected-visible`、childList 增删）、**`focusin` 0 次**；"
                "派发**之后**节点 `tabindex` 变成 `'0'`。"
                "· B（直接点节点）：target `isConnected=True`、节点在 mousedown 时"
                "**已经是** `tabindex='0'`、MutationObserver **0 条**、"
                "**`focusin` 2 次**。"
                "⇒ **机制**：浏览器的默认动作是「把焦点移到 **mousedown 目标**的"
                "最近可聚焦祖先」；A 里它面对的是一个**已脱离文档的 target**"
                "**加一个**那一刻还没有 `tabindex` 的节点 ⇒ **无处可移**。"
                "⇒ 这**同时**满足 891 的 C1（那里节点**一直** `tabindex=0`）、"
                "892 的「没有 preventDefault」、和源站的 `focusin=0` —— "
                "三者不再冲突。⚠️ 注意 `tabindex` 是**事后**才变成 `'0'` 的，"
                "所以别写成「源站节点没有 tabindex」。"),
            "source_node_tabindex_is_conditional_893": (
                "⚠️⚠️ **894 推翻了本条的第一版，也推翻了我自己写下的那句话。**"
                "第一版写的是：「893 里 A 序列（点空白之后）那个音频节点 "
                "`tabindex=None`，而 889d 的 Tab 走查里**点空白之后**页面自带"
                "节点**全都是** `tabindex='0'` 且能被 Tab 到」。"
                "**894 实测（矩阵，每种条件 2 轮）否掉了后半句**："
                "· `fresh_load`（刚载完、什么都不做）：**所有**节点"
                "（audio 66 / text 3 / timeline 2 / video / image / external）"
                "**全都是 `tabindex=None` / `tabIndexProp=-1`**；"
                "· `after_blank`（点空白）：**同样全是** `None`/`-1`；"
                "· `after_tab_final`（连按 Tab 16 次**之后**）：音频节点变成"
                "**混合** `['-1','0','None']`、其余各类变成 `-1`；"
                "· 那个新节点：插入后点空白 ⇒ `None`；**再点它选中** ⇒ "
                "**仍是 `None`**（`selected=True` 但 `tabIndexProp=-1`）。"
                "⇒ **889d 那句「`tabindex='0'`」是假象**：它是**焦点落在节点上的"
                "那一刻**读的读数，**与中性状态不是同一个时刻** ⇒ 两次读数"
                "**本来就不该放在一起比**。这是「跨时刻读数混比」的第 N 次。"
                "⇒ 源站节点的 `tabindex` 是**动态**的（看着像 **roving tabindex**："
                "中性态 `-1`、被 Tab 命中时 `0`）。"
                "✅ **896 已把策略测出来**（原文见 "
                "`source_roving_tabindex_policy_896`：中性态**无属性**、"
                "Tab keydown 时布「目标 0 / 其余 -1」、**不** preventDefault、"
                "**此后不回撤**）⇒ 本条那句「**具体策略未测**」**已作废**。"
                "⚠️ 但**别顺手把 894 推翻了 889d 这件事删掉** —— "
                "「`tabindex='0'` 是**跨时刻**读数」这个判断才是本条的核心。"),
            "source_nodes_not_tabreachable_in_neutral_state_894": (
                "✅ **894 的一条硬事实（每种条件 2 轮）**：源站在**中性状态**"
                "（刚载完、或点空白之后）下，**所有类型**的节点 "
                "**`tabIndexProp=-1`/`tabindex=None`**，即**不可 Tab 到达**。"
                "⇒ 与复刻（`@xyflow/react` 默认 `nodesFocusable=true` ⇒ 节点"
                "**任何时候** `tabindex=0`）是**方向明确的产品差异**。"
                "⚠️ 但**先别改**：`@xyflow/react` 有 `nodesFocusable` / "
                "`nodeFocusable` 这类开关（**895 已量**：复刻侧现状是**恒定 "
                "`tabindex='0'`**）。"
                "✅ **896 把那个策略测出来了**（见 "
                "`source_roving_tabindex_policy_896`）—— 一句话："
                "**「按 Tab 才把画布装进 Tab 序列：目标 0、其余全 -1；"
                "装完交还浏览器原生 Tab；此后不再回撤。」**"
                "⚠️⚠️ **896 当时写「`nodesFocusable` 是错的杠杆」—— "
                "896 自己那版说法**过头了**，898 已更正**：单翻 "
                "`nodesFocusable={false}` 确实会让画布**再也 Tab 不到**，"
                "**但那只是「半个方案」**。源站的机制**恰恰就是**"
                "「**库不接管 `tabindex`、应用自己在 keydown 时布**」"
                "（896 实测：中性态**无属性**、按 Tab 现场全画布重写）⇒ "
                "所以 `{false}` **＋** 自己实现「布 `0`/`-1` 且**不** "
                "preventDefault」才是**成对的**忠实实现 —— "
                "**`{false}` 正是它的前半段**。"
                "⚠️ 真正的坑是：**`{false}` 绝不许单独上线** —— "
                "那会交付一个**画布 Tab 不到**的产品，比不改更糟。"
                "⚠️ 也就是说：896 那句「错的杠杆」**该读作「错的**单方**方案**」，"
                "**不是**「这个开关不许碰」** —— 后者会把正确的前半段也一起否掉。\n"
                "⚠️ 但「**先别改**」**曾经**成立过，而且理由是**具体**的"
                "（898 把 896 那句过头的话收窄过）。"
                "✅ **901 已经改了**（`nodesFocusable={false}` ＋ 自己的 "
                "`armRovingTabindex`）⇒ 改的**前提**（两侧测量都齐）当时"
                "**确实**已满足，且**改动本身**带自己的验证"
                "（复刻侧各 2/2、逐条对上源站七条，见 "
                "`replica_roving_implemented_901`）。"
                "⇒ 本条的「**不许**据此改」那句**只作历史记录**，"
                "⚠️ **不许**拿它去阻止后续按**已测规则**做的改动 —— "
                "901 就是按「先测清规则、再动手」这条纪律做的。\n"
                "⇒ **不许**写成「源站未选中节点一律不可聚焦」这种**过度概括**"
                "（894 已经证明：那不只对未选中成立，**选中的新节点也是 "
                "`None`/`-1`**）；"
                "⇒ 更**不许**据此改复刻的 `nodesFocusable` —— "
                "那是**整个画布 Tab 顺序**的改动，必须单独一批、"
                "带自己的验证做。"),

            "replica_node_always_focusable": (
                "⚠️⚠️ **本条已被 901 作废 —— 它描述的是「改之前」的复刻。**"
                "留在这里**不是**因为它还对，而是因为它是 895 当时的**真实测量**、"
                "**不许**回头抹掉。\n"
                "**895 的原测量**（各 2/2）：复刻侧**所有**条件、**所有**状态的"
                "节点 **`tabindex='0'` 恒定**（`fresh_load` / `after_blank` / "
                "连按 Tab 之后 / 插入后 / 插入后点空白 / 选中）；机制方向是"
                "`@xyflow/react` 的 `nodesFocusable` 默认 true ⇒ wrapper 静态带 "
                "`tabindex=0`。**不是**从库默认值**推**的，是量出来的。\n"
                "⚠️ 当年写下的「类型覆盖不全」缺口**已由 897 补齐**。\n"
                "**⇒ 901 把这个状态改掉了**（`nodesFocusable={false}` ＋ 自己的 "
                "`armRovingTabindex`）⇒ 现在复刻侧中性态是**无 `tabindex` 属性**，"
                "见 `replica_roving_implemented_901`。**本条只作历史记录。**"),
            "replica_roving_implemented_901": (
                "✅ **901 把源站那套 roving 实现了**（复刻侧，**各 2/2、两轮完全"
                "一致**；判据**逐字复用** 896/899/900 的**源站**探针，"
                "**不许**改写成「复刻版」）。改了两处：\n"
                "① `JimengWorkspace.tsx` 的 `<ReactFlow nodesFocusable={false}>` "
                "—— 中性态**无 `tabindex` 属性**（896 ①）。"
                "⚠️ 这是**配对方案的前半段**（另一半是下面那个 "
                "`armRovingTabindex`）—— "
                "⚠️⚠️ **只上前半段绝不许单独上线**（898 已证明：单上它画布"
                "**再也 Tab 不到**）。⚠️ **不许**把 `nodesFocusable={false}` "
                "**单独**当成「已对齐源站」。\n"
                "② 模块级 `armRovingTabindex(flow, dir)` ＋ window **捕获阶段**"
                "的 keydown 监听（906 式的理由：捕获阶段改完 tabindex，"
                "浏览器**默认动作**才算得出新顺序）。**不** `preventDefault()`。\n"
                "**逐条对上了源站的七条**（复刻侧各 2/2）：\n"
                "· 896① 中性态 / 插完 / 点空白后，**全都** `hist` 只含 `'None'`"
                "（**一个节点都不在 Tab 序列里**）\n"
                "· 896② `n_zero` **恒为 1**、直方图**恒**是 "
                "`{'0': 1, '-1': n-1}`（**全画布重写**）\n"
                "· 896③ `defaultPrevented` **全 `False`**（焦点移动是浏览器原生的）\n"
                "· 896④ **先布 `'0'`、再移焦点**（`focusin` 捕获阶段读到 `'0'`）\n"
                "· 899① 布 `'0'` 的下标 = **`[0,1,2,…,n-1]`** ⇒ **纯 DOM 序**\n"
                "· 899② 走到**最后一个**之后**再也没有任何布 `'0'` 的动作** ⇒ "
                "**撒手**、**不绕回**（实现里就是 `next` 越界就 `return`，"
                "**没有** `% len` 那套循环）\n"
                "· 896⑤ **此后不回撤**（900 的修正也照做了：**焦点不在节点上就不布**）"
                "⇒ 点空白之后那个 `'0'` **仍然**留在最后 rove 过的节点上\n"
                "⚠️ **两条如实记账的差异/缺口**：\n"
                "· **900 那个「源站有 2 个节点整轮没被布 `'0'`」的例外，复刻**没有**"
                "**（复刻按**纯 DOM 序**走）⇒ 这一处**刻意保留**为与源站的"
                "不一致（原因在应用内部、从 DOM 不可查明，"
                "**不许编 DOM 层判据去抹平**、"
                "**更不许**编判据去凑）。\n"
                "· **`Shift+Tab` 且焦点不在任何节点上**时，本实现**什么都不做**。"
                "⚠️ **源站这个组合没测过** ⇒ 按 §77"
                "「源站没测到的行为不实现、不伪称可用」⇒ 这里**不猜**。\n"                "✅ **902 已把这一格测掉了**（各 2/2）：源站在这个组合下"
                "**一次 `'0'` 都不布**（`n_zero` 逐次 `[0,0,0,0,0]`、"
                "`defaultPrevented` 全 `False`），焦点**按浏览器原生顺序"
                "往回走出画布** ⇒ **与本实现那个「什么都不做」的分支一致**。"
                "⚠️ 要说清：这是**测出来**的、**不是**「猜对了」—— 901 当时"
                "按 §77 选了「不猜」，902 证明这个选择与源站相符。"
                "（另一格「回来之后按 Tab」902 曾读到 `[2, 3]`、**903 的四条对照"
                "全部读到 `[0,1,2]`** ⇒ **8/8 与本实现相符**，那条分支"
                "**不再是「已知差异」**；但 902 那个落点的成因**仍未查明** ⇒ "
                "**仍然不许**据此改实现。详见 "
                "`source_roving_pointer_carries_state_902`。）\n"
                "⚠️ **901 第一版自己踩的坑**：走查第一版 `OVERRUN=6` **不够**"
                " —— 复刻 video 节点有 5 个**内层控件**，"
                "那些按压被它们吃掉了，指针只推到下标 5（DOM 共 7 个）⇒ "
                "**根本没走到末尾** ⇒ 「到末尾撒手」那一问**本轮不成立**，"
                "**差点**拿没测到的数据下结论。加到 `OVERRUN=20` 才真的走完一圈。"
                "⇒ 教训与 899 第一版**同一条**：**按压次数要盖过「被内层控件吃掉」"
                "的那部分**，否则「末尾行为」根本没被问到。"),
            "source_shift_tab_from_non_node_902": (
                "✅ **902 把 901 明确拒绝猜的那一格测掉了**（源站，各 2/2，"
                "两轮完全一致）：**点空白**（焦点落到画布根 `aria='Canvas'`、"
                "**不在任何节点上**）之后**连按 5 次 `Shift+Tab`** ⇒\n"
                "· `n_zero` 逐次 = **`[0, 0, 0, 0, 0]`**、布 `'0'` 的次数 "
                "**0** ⇒ **一次都没布**\n"
                "· `defaultPrevented` **全 `False`**\n"
                "· 焦点**按浏览器原生顺序往回走出画布**"
                "（用户菜单 → Credits → 更多 → 分享 → 生成历史）\n"
                "⇒ **源站的行为就是「完全不布 `'0'`」**。"
                "⚠️ 但要说清：这是**测出来**的，**不是**「猜对了」。"),
            "source_roving_pointer_carries_state_902": (
                "⚠️⚠️⚠️ **903 做了四条对照、把本条的一半结论推翻了；"
                "另一半仍然成立。**（源站，各 2/2）\n"
                "**902 的原读数**：往回走停在**下标 58** 时，离开画布再回来按 "
                "`Tab` ×3 ⇒ 布 `'0'` 的是 **`[2, 3]`**、**不是 0**（2/2 一致）。\n"
                "**902 答上来、903 复核仍成立的那一半**：① 往回走布 `'0'` 的"
                "下标**递减** ⇒ **反向也是 DOM 序**（⚠️ 同样**跳过 67–64**，"
                "与 900 正向跳过的是**同一类现象**）；② 离开画布再回来，"
                "那个 `'0'` **没**被清掉 ⇒ **896⑤「此后不回撤」连往返都成立**。\n"
                "**903 的四条对照**（每条只动一个变量，各 2/2）："
                "`A` 干净基线 / `B` 中途点空白（指针**没**到末尾）/ "
                "`C` 指针**到末尾**（**没**走出画布）/ "
                "`D` 到末尾**＋**走出画布（**就是 902 那条序列**）"
                "⇒ **8/8 全部 `[0,1,2]`**。\n"
                "⇒ ⚠️ 但这**不能宣布「902 是错的」**："
                "两次跑的往回走**停在 58 vs 59**"
                "（都 2/2 一致）⇒ **两个都是真实读数**。⇒ 真正的结论是："
                "**「回来后从 0 开始」不是无条件的**；"
                "**触发条件仍未查明**（那一位本身由**前面消耗了多少次按压**决定，"
                "而按压次数又被**内层控件吃掉多少**影响）。\n"
                "⇒ 📌 **904 接着查了这件事**：它把 902 的 `[2,3]` **复现出来了**"
                "（`pre=0` 的干净臂、终点 58），**排除了**「开头 5 次 `Shift+Tab` "
                "是触发条件」那条假设，并证明**落点条件不在终点上**、"
                "回来后第一次布的下标是 **0/1/2/12**（4 个值都 2/2）"
                "⇒ 详见 `source_roving_reentry_start_unstable_904`。\n"
                "⇒ ⚠️ **不许**把 `[2,3]` 当常态规则，"
                "**也不许宣布它是作废/随机的**。\n"
                "⇒ ⚠️ **对复刻的实践结论**：901 的 `cur === -1 && dir === 1` "
                "「**从头**布」那个分支，在 903 的 **8/8** 对照里**与源站相符** ⇒ "
                "**不再是「已知差异」**。⚠️ 但**仍然不许**据此去改实现 —— "
                "902 那个不符的落点**成因未查明**，改了就是在**没查清的规则**上动手。"),
            "source_roving_reentry_start_unstable_904": (
                "⚠️ **904 排除掉一条候选假设、并把变量挪到了别处；"
                "机制本身**仍未查明**。**（源站，4 臂 × 2 轮 = 8 条，"
                "**两轮逐条完全一致**）\n"
                "**扫的两个变量**：进场前先按几次 `Shift+Tab`（`pre` ∈ {0,5}）、"
                "往回按几次（`k` ∈ {28,30,32}）。仪器**逐字复用** 900。\n"
                "**① 902 的 `[2,3]` 复现了，而且是在 `pre=0` 的干净臂里**"
                "（终点 58 = `音频 node: 音频 51`、回来后 `Tab`×3 布 `[2,3]`、"
                "末态 `'0'` 在 [3]，2/2）⇒ **「902 开头那 5 次 `Shift+Tab` "
                "才是触发条件」这个假设被排除**。\n"
                "**② 终点是 `k` 的严格线性函数**：`endpoint = 88 − k`"
                "（k=28→60、30→58、32→56，各 2/2）⇒ 这一段**每多按一次退一格**、"
                "**终点只由 `k` 决定**。\n"
                "**③ 回来后布的下标与终点无关**（各 2/2）："
                "58→`[2,3]`、60→`[0,1,2]`、56→`[12]`、0→`[1,2]` "
                "⇒ **落点条件不在终点上** ⇒ 902 与 903 的差别**不是**"
                "「回走停在哪一格」。\n"
                "⚠️⚠️ **906 把本条 ③ 判为无效**：906 的终点 **58** 给出 "
                "`[2,3,4,5]`（**前 3 次与本条的 58→`[2,3]` 逐条相同**）、"
                "而终点 **59** 给出 `[0,1,2,3]` ⇒ **落点恰恰是跟着终点走的**，"
                "本条只是**没取到能区分的那几个终点**。\n"
                "**④ 回来后第一次布的下标不稳定**：0 / 1 / 2 / 12，"
                "**四个值都 2/2** ⇒ **「从 0 开始」确实不是无条件成立**"
                "（903 那 8/8 里的 `[0,1,2]` **只是其中一种**）；"
                "**4 臂里只有 1 臂从 0 开始**。\n"
                "**⑤ 5 次 `Shift+Tab` 那条臂的 `at_end` 只有 [4]**、**不是 75** ⇒ "
                "焦点被带出画布后 101 次 `Tab` **只走到第 4 格** ⇒ "
                "**那条序列不是「走到末尾再往回」**。\n"
                "⚠️ **本轮仍未查明的（不许猜）**：\n"
                "· **④ 里那个起点（0/1/2/12）由什么决定** —— 本轮**没逐次记"
                "**按压时的焦点落点**（`press()` 只抽了 `armed` 与 `prevented`）"
                "⇒ 这是**取样缺口**，不是「测出来没有」。\n"
                "· **903 的 59 vs 902/904 的 58**：本轮两轮都读到 **58**，"
                "⇒ ⚠️ **仍然不许**宣布 903 的 59 是错的 —— 903 那条序列里"
                "**有本轮没复现的差别**，只是还没找出来是哪一处。\n"
                "⚠️ **两条探针侧缺陷如实记账（不藏）**：\n"
                "· **4 条臂在同一页面里按固定顺序连跑、臂间不 reload** ⇒ "
                "我记的「入场状态」其实**是上一臂的尾巴**（已逐臂核对："
                "每臂 `entry` 都等于上一臂 `after_state`）⇒ "
                "**「入场状态」不是独立变量**；真正被扫到的是**臂的顺序**。\n"
                "· `back_armed_count` **不能当步数用**：`oldValue != '0'` 这个"
                "过滤会把「本来就是 `'0'`、又被重写一次」的那次算漏。\n"
                "⇒ **对复刻**：901 的 `cur === -1 && dir === 1`「从头布」分支"
                "**不是忠实实现**（源站 4 臂里 3 臂不是从 0 开始）—— "
                "⚠️ 但**触发条件未查明 ⇒ 仍然不许改实现**。"
                "⇒ **下一步**：逐次记**按压时的焦点落点**（每按一次记 "
                "「布了什么 + 焦点到了哪个 `aria`」）。"),
            "source_reentry_arm_pattern_confirmed_905": (
                "✅ **905 把 904 点名的那个取样缺口补上了**，并用**臂间 reload** 的"
                "干净对照把结论坐实（源站，3 臂 × 2 轮 = 6 次，"
                "**6 次的 8 步逐次轨迹完全一致**）。\n"
                "**设计**：`L0` 从未 Tab 过 / `L1` 只走到末尾 / `L2` 末尾＋回走 30；"
                "**每臂之间 reload**（这是 904 没有的、也是 904 最大的缺陷）；"
                "`k` 固定 30（904 已证终点 `= 88 − k`，不用再扫）。\n"
                "**① 回来后 8 次按压的轨迹完全确定**："
                "布的下标 = **`[0,1,2,3]` 然后连续 4 次不布**；"
                "落点依次是 `视频 1` / `文本 1` / `时间线 1` / `导出时间线` / "
                "`全屏编辑` / `静音` / `添加素材到时间线` / `文本 2`。\n"
                "**② 那 4 次「不布」逐次对得上「按压时焦点停在内层控件上」**"
                "（`导出时间线`→`全屏编辑`→`静音`→`添加素材到时间线`，"
                "**都不带 `react-flow__node` 类**）⇒ **900 的"
                "「焦点不在节点本体上就不布」在回来后这一段得到逐次证实**。\n"
                "**③ 布与落点严格错开一位**：第 8 次按压时焦点在"
                "「添加素材到时间线」（内层）⇒ **不布**；按压后焦点才落到 "
                "`文本 2`（节点本体）⇒ **正是 896④「先布 `'0'`、再移焦点」**。"
                "⚠️ 由此**不许**把「这一次布了什么」和「这一次焦点落在哪」"
                "当成同一件事读。\n"
                "**④ 单变量阶梯（臂间 reload ⇒ 入场状态干净）**：`L0` / `L1` / `L2` "
                "**三条臂的回来后轨迹完全相同** ⇒ 观察事实是"
                "**「走到末尾」和「回走 k 次」都没改变这三条臂的落点**。\n"
                "⚠️⚠️ **但 906 已把本条**后面那半句推论**判为无效** ——"
                "三条臂的终点是 `∅` / `75` / `59`，**恰好全都落在「从 0 开始」"
                "那一类**，而 906 的终点 **58** 就给出 `[2, …]` "
                "⇒ **「三条臂相同」推不出「与终点无关」**，那是**取样没覆盖到的巧合**。"
                "⇒ 正确说法是：**落点跟着终点走**，映射**仍未刻画**。"
                "详见 `source_roving_direction_asymmetry_906`。\n"
                "**⑤** 48 次按压的 `defaultPrevented` **全 `False`**。\n"
                "⚠️⚠️ **本批新发现的矛盾（必须记着，不许抹平）**："
                "**905 与 904 在名义上相同的序列上给出了不同的回来后轨迹** —— "
                "905 的 `L2`（终点 **59**）⇒ `[0,1,2,3]`；"
                "904 的 `base-k30`（终点 **58**）⇒ `[2,3]`。"
                "⇒ 存在一个**两批都没控住的变量**，**未查明**。\n"
                "⚠️ **由此钉死三条不许**：① **不许**宣布 904 作废；"
                "② **不许**宣布 905 是「干净的那次」；"
                "③ 那个 58 vs 59 本身也**仍未查清**（904 已记过一次）。\n"
                "⚠️ **另外两条读数，机制同样未验**：\n"
                "· **首次 `Tab` 从画布根会布 `'0'`**（press1 布 0、落点 `视频 1`），"
                "而 **902 测到 `Shift+Tab` 从画布根一次都不布** ⇒ "
                "**方向不对称**（902 测的是**往回**、905 测的是**往前**）。\n"
                "· ⚠️ **「第 9 次按压会布 4」是预测、探针只按了 8 次 ⇒ 没测** ⇒ "
                "**不许**当结论用。\n"
                "⇒ **对复刻**：900 规则**有逐次证据**了 ⇒ 901 那个分支站得住；"
                "但 901 的「从头布」分支在 905 是 **6/6 从 0**、在 904 是 "
                "0/1/2/12 ⇒ **仍然不许**当普适规则、**仍然不许改实现**。") ,
            "source_roving_direction_asymmetry_906": (
                "✅✅ **906 把 905 那条「方向不对称」从读数钉成了规则，"
                "并推翻了我自己 905 的一条推论。**（源站，3 臂 × 2 轮 = 6 次，"
                "两轮逐条一致）\n"
                "**设计**：`F8-fresh`（从未 Tab 过）/ `F8`（走到末尾＋回走 30、"
                "按 `Tab`）/ `B8`（**与 `F8` 逐字相同、只把方向换成 `Shift+Tab`**）"
                "⇒ **`F8` vs `B8` 只差方向**。每臂之间 reload。"
                "906 第一次跑就把按压**前**的 `activeElement` 直接量了出来，"
                "**消掉了 905 那个「错开一位」的近似**。\n"
                "**① 方向不对称成立，而且被定位到唯一一个位置**："
                "同一终点 **58**、同样 `back` 布了 **13** 次 ⇒ "
                "`F8` 布了 `[2,3,4,5]`、而 `B8` **8 次一次都没布**（2/2）。"
                "⇒ 但**不对称只发生在「焦点在画布根」这个位置上**："
                "焦点在**节点本体**上时，`Tab` 与 `Shift+Tab` **都布**"
                "（900 那次「中途连按 30 次 `Shift+Tab`、只有第 1 次布了」"
                "就是这一类）。\n"
                "**② 布与不布的真判据是 `contains`、不是 `closest`** —— "
                "906 **一条记录里同时有这两种口径**（`STATE_JS` 的 `pre_in_node` "
                "用 `closest`、仪器用 `classList.contains`）⇒ **自带对照**："
                "`导出时间线` / `全屏编辑` / `静音` / `添加素材到时间线` "
                "这四个**内层控件**，`closest` 全给 `True`、"
                "`contains` 全给 `False`，而**「没布」的那几次按压前焦点正是它们**"
                "⇒ **规则跟的是「焦点元素本身就是节点本体」**，"
                "**不是「焦点在某个节点里」**。\n"
                "**③ 能解释全部读数的最小规则**（**逐条对得上，仍是描述、"
                "不是机制**）：`布 ⟺ 按压前焦点是节点本体 ∨ "
                "(按压前焦点是画布根 且 方向为 Tab)`。"
                "⇒ 它同时解释了 902 的格 A（`Shift+Tab` 从画布根 ⇒ 一次都不布）"
                "与 905/906 的 press1（`Tab` 从画布根 ⇒ 布 0/布 2）。\n"
                "**④ 904 那个 `[2,3]` 被干净臂精确复现**（2/2）："
                "906 `F8` 终点 **58**、`back` 布了 **13** 次 ⇒ 布 `[2,3,4,5]`，"
                "**前 3 次与 904 `base-k30` 逐条相同** ⇒ "
                "**904 不是异常值**。\n"
                "⚠️⚠️ **906 顺手推翻了 905 的一条推论**："
                "905 ④ 说「三条臂轨迹完全相同 ⇒ **「走到末尾」「回走」都不影响"
                "回来后从哪开始**」⇒ **这个推论无效** —— "
                "那三条臂的终点是 `∅` / `75` / `59`，**恰好全都落在"
                "「从 0 开始」那一类**；906 的终点 **58** 就给出 `[2, …]`。"
                "⇒ **落点确实跟着入场状态（终点）走**，"
                "⚠️ 但**终点 → 起点**的映射**仍未刻画出来**"
                "（已知：58→2、56→12、0→1；而 59 / 60 / 75 / ∅ → 0）。\n"
                "⚠️ **两条如实记账**：\n"
                "· `F8-fresh` **两轮不完全一致**：rep1 布 `[0,None,1,2,3]`"
                "（多布了一次、且有一次目标不在本轮 DOM 序表里 ⇒ `None`，"
                "与 899/MM.4 同一类）、rep2 布 `[0,1,2,3]`。\n"
                "· 906 **第一版把一次偶发加载失败报成了 `BLOCKED_BY_FIXTURE`**"
                "（隔离复跑证明登录态是好的：`sessionid` 还有 363 天、"
                "同一判据在 t+13s 命中 `button[aria-label=\"音频\"] == 1`）"
                "⇒ **一次没命中不等于没登录**；已改成**判据未命中就重试**，"
                "且**被挡时也要落盘**（第一版把落盘写在 `else` 分支里，"
                "**被挡那次连文件都没有** —— 而被挡恰恰最该留痕）。\n"
                "⇒ **对复刻**：901 的实现是「keydown 时若焦点在节点本体就布 "
                "`cur+dir`」⇒ **节点本体位置上与源站相符**；"
                "⚠️ **「焦点在画布根时 `Tab` 也要布、`Shift+Tab` 不布」这一格"
                "复刻侧没实现也没测过** ⇒ 按 §77 **不猜**，"
                "**先记为未取样**。") ,
            "source_roving_wraps_at_canvas_root_908": (
                "⚠️⚠️⚠️ **908 推翻了 899 的「绝不绕回」** —— "
                "**源站会绕回**，但**只在「焦点回到画布根」的那一按**。"
                "（源站，2 臂 × 2 轮 = 4 条，**4/4 逐条一致**）\n"
                "**两条臂**：`W1` 一路按 `Tab` 直到焦点自己走回画布根；"
                "`W2` 按到刚过末尾就**立刻再点一次空白**（焦点直接回画布根、"
                "**不走出去**）⇒ `W2` 是**专为证伪「必须先走出画布」"
                "这条机制假设**设计的。\n"
                "**① 绕回是真的**：两条臂都布到了 **`0`**（走查序列末尾是 "
                "`… 74, 75, 0`），`W1` 在**第 103 次**按压、`W2` 在第 85/84 次，"
                "**2/2 各臂一致**。\n"
                "**② 4 次绕回那一按的「按前焦点」全是画布根 `Canvas`、"
                "四次都布 `0`** ⇒ **绕回的触发条件是「按前焦点在画布根」**，"
                "**不是**「走出过画布」—— `W2` 根本没走出去也绕回了，"
                "**这条机制假设被自己的证伪臂推翻**。\n"
                "**③ 但 899 的「撒手」那一半仍然成立**：`W1` 第 84 次按压，"
                "**按前焦点是节点本体**（`音频 node: 音频 68`）、指针已在末尾 ⇒ "
                "**一次都不布、不绕回**。⇒ **两条并存、互不矛盾**：\n"
                "· 指针在末尾 ＋ **按前焦点是节点本体** ＋ `Tab` ⇒ **撒手**（899 对）\n"
                "· 指针在末尾 ＋ **按前焦点是画布根** ＋ `Tab` ⇒ **布 `'0'`、绕回**"
                "（899 错）\n"
                "· **画布根 ＋ `Shift+Tab` ⇒ 一次都不布**（902/906）\n"
                "**④ 899 为什么会读成「不绕回」（取样假象的成因已找到）**："
                "899 按的是 `节点数 + 20` 次，而**从末尾走到画布根还要约 19 次**"
                "⇒ **按压预算在焦点回来之前就用完了** ⇒ "
                "**它其实根本没问到绕回**。⚠️ 与 899/901 自己记下的"
                "「按压次数要盖过被内层控件吃掉的那部分」是**同一条教训的另一半**："
                "**要盖的不只是内层控件，还有「走出去再走回来」这一段**。\n"
                "**⑤ 顺带复现了 900**：正序走查 `'0'` 的序列是 "
                "`0…11, [12 跳过], 13…67, [68 跳过], 69…75` ⇒ "
                "**整轮跳过的正好是 2 个、DOM 下标 12 与 68**"
                "（2/2）⇒ **900 那条「2 个节点整轮没被布 `'0'`」再次复现**。\n"
                "**⑥ 末尾之后焦点走出画布那一段（约 19 次按压）`'0'` 一次都没动** ⇒ "
                "**896⑤「此后不回撤」再获一次证实**。\n"
                "**⑦ 4 次按压的 `defaultPrevented` 全 `False`**。\n"
                "⇒ **对复刻（这是 901 的一个实打实的缺口）**：901 写的是"
                "「越界直接 `return`、**没有** `% len`」⇒ **缺了"
                "「画布根 ＋ `Tab` ⇒ 绕回布 `'0'`」这一格**。"
                "⚠️ 但这一格与 906 记下的「画布根 ＋ `Tab` 要布、`Shift+Tab` 不布」"
                "**是同一格** ⇒ 复刻侧**两格都没实现、也没测过** ⇒ "
                "**下一批按 §77 先取源样再动手**。") ,
            "source_endpoint_start_sweep_void_907": (
                "❌ **907 这一批作废，不许拿它下任何结论**"
                "（源站，6 臂 × 2 轮）。\n"
                "**它本来要做什么**：臂间 reload 连续扫 `k ∈ {0,3,8,15,25,40}`，"
                "刻画 906 留下的「**终点 → 起点**」映射。\n"
                "**为什么作废**：**正向走查每一条臂都绕回了**，"
                "所以 **6 条臂的终点全都是下标 `0`** ⇒ "
                "**一个能区分的终点都没扫到** ⇒ "
                "「`k` 变了而终点没变」这件事本身就说明**走查预算**有问题，"
                "**不是**映射的读数。\n"
                "**成因（908 查清了）**：907 的走查按的是 `节点数 + 25` 次，"
                "而 908 实测**绕回恰好发生在第 103 次按压**（78 个节点、"
                "2/2）⇒ **`节点数 + 25` 正好落在绕回点上**"
                "（904/905/906 那几批是 76 个节点、101 次 ⇒ **差一点没绕回**，"
                "所以它们读到的是「末尾」）。\n"
                "⚠️ **教训**：**按压预算不能拍脑袋给「+25」** —— "
                "它既可能**不够**（899/901 记过：被内层控件吃掉），"
                "也可能**刚好撞上绕回**（本条）⇒ "
                "**必须把走查的停止条件写成「观测到第二次布到 0」**，"
                "而不是「按够次数」。\n"
                "⚠️ **连带作废**：907 那批读数（`第一次布的下标 = 1`、"
                "`全程布 [1,2,3]`）**不能**用来支持或反驳任何映射结论。"
                "**⇒ 终点 → 起点的映射仍然未刻画**，"
                "要重扫就按 908 的停止条件重扫。"),
            "replica_roving_strict_wrapper_909": (
                "✅✅ **909 是 901 之后第一个真代码改动**，依据是 906 的"
                "**自带对照**（源站读数见 `source_roving_direction_asymmetry_906`；"
                "复刻侧验收 5 臂 × 2 轮 = 10 条，**两轮逐条一致**）。\n"
                "**改了三处，全在模块级 `armRovingTabindex` 里**：\n"
                "① 找指针的判据：`**n === active || n.contains(active)**` ⇒ "
                "**`n === active`**（**严格**）。依据 906：那四个内层控件 "
                "`closest` 全 True / `contains` 全 False，而**「没布」的按压前"
                "焦点正是它们** ⇒ 宽松口径会把它们当成「在节点上」而**多布一次**。\n"
                "② `cur === -1` 那一支：**先**判「焦点是否落在某个节点的"
                "**内层控件**里」，是就 **`return`（一次都不布）**；"
                "不是才按原来的 `dir !== 1` 判据走。\n"
                "③ 注释里的规则表从 5 条改成 **7 条**：④ 拆成「撒手（仍成立）」"
                "＋「**899 的『绝不绕回』已撤回**」；⑤ 新增**画布根**那一格；"
                "⑥ 新增**内层控件**那一格；⑦ 补记 908 对「此后不回撤」的复核。\n"
                "**逐条对照（复刻读数 2/2）**：\n"
                "· **画布根 ＋ `Tab` ⇒ 要布 `'0'`**：三条臂**可见地**对上 —— "
                "`F8-fresh` `'0'` 由 `[]→[0]`、`W1` 与 `W2` 由 `[1]→[0]`。\n"
                "· **画布根 ＋ `Shift+Tab` ⇒ 8 次一次都不布**（`B8`，`'0'` 一直 `[0]`）"
                "⇒ 与源站 906/902 逐条相同。\n"
                "· **内层控件 ⇒ 一次都不布**：`Add tags` / `播放` / `底部播放` / "
                "`取消静音` / `全屏预览` 五次，按压前 `closest=True` 而"
                "**本体=False**、`'0'` 一次没动 ⇒ **906② 逐条对上**，"
                "**而这五次正是 901 改前会多布的那五次**。\n"
                "· **布与落点错开一位**：最后一次按压按前焦点是内层控件 ⇒ 不布，"
                "尽管落点是节点本体 ⇒ 与 905/906 一致。\n"
                "⚠️ **两格必须标成「没验到 / 不可判定」，不许含糊过去**：\n"
                "· **`F8` 臂的 press1 不可判定**：要布的下标**恰好就是当前 `'0'` "
                "所在的下标** ⇒ 「`oldValue != '0'` 把这次过滤掉」与「位置本来"
                "就没变」**两个现象同时出现** ⇒ 本轮数据**分不出**"
                "「调了 `armAll` 且结果相同」与「什么都没做」。"
                "（同一格在另外三条臂上**可见地**成立。）\n"
                "· **源站 `F8` 与复刻 `F8` 终点不同、不可比**：源站终点 **58**、"
                "press1 布 `[2]`；复刻 demo 画布只有 **2 个节点**、回走 30 次之后"
                "终点是 `[0]` ⇒ **取不到同一个终点值** ⇒ "
                "**不许拿复刻的 `F8` 说「对上了 906 的 `F8`」**。\n"
                "⚠️ **探针缺陷（909 第一版自己踩的）**：第一版 `press()` **没记** "
                "`'0'` 动没动，只看 `armed` ⇒ 被 `oldValue != '0'` 过滤吞掉的读数"
                "**根本看不见**（**904 已经记过这个坑，909 又踩了一次**）⇒ "
                "第二版补上 `zero_before` / `zero_after` / `moved`，"
                "**两条序列一起看才不漏读**。\n"
                "⇒ **未变的已知差异（如实记着）**：源站 `F8` 的 press1 布的是"
                "**落点所在的那个节点**（复刻固定布 `0`）—— "
                "**这一格源站的成因仍未查明**，**不许**据此改复刻。"),
            "source_endpoint_to_start_threshold_910": (
                "✅ **910 把 907 作废之后重扫的那件事测出来了：存在一个分界。**"
                "（源站，8 臂 × 2 轮 = 16 条，**两轮逐条一致**；"
                "每臂之间 reload，终点**实测**）\n"
                "**设计（907 的毛病在于终点被走查预算绑架，这里换掉了）**："
                "907 是「先走到末尾、再往回按 `k` 次」⇒ 预算 `节点数 + 25` "
                "**正好撞上绕回点**；910 改成**直接扫「从画布根按 `j` 次」**"
                "（`j ∈ {0,3,8,15,25,40,55,65}`）⇒ **全程不碰末尾**、"
                "**结构上撞不上绕回**，且 `j` 最大 65 **小于**实测末尾 75。\n"
                "**读数（实测终点 → 回来后第一次布的下标）**：\n"
                "· `∅ / 2 / 3 / 10 / 20 / 31` ⇒ **0**（六个值，2/2 全是 0）\n"
                "· **`46 / 56` ⇒ 12**（两个值，2/2 全是 12）\n"
                "⇒ **存在分界，落在 `(31, 46]` 之间**。⚠️⚠️ **但分界点没夹逼**"
                "（31 与 46 之间一个点都没取）⇒ **不许**把「≤31→0、≥46→12」"
                "当规则、**不许**据此改实现。\n"
                "**落点也跟着变（这是新信息）**：\n"
                "· 「0」那一组：press1 布 `0`、落点 **`视频 node: 视频 1`**"
                "（节点 0 的**本体**）\n"
                "· 「12」那一组：press1 布 `12`、落点 **`导出时间线`**\n"
                "⚠️ **12 正是 900 查出的两个「整轮从没被布 `'0'`」之一**"
                "（`图片 node: b22-upload`，DOM 下标 **12**；另一个是 68）"
                "⇒ **这是相关，不是机制** —— ⚠️ **不许**把「12 是特殊节点」"
                "当成「分界的成因」去编规则。\n"
                "**「12」那一组 8 步的完整轨迹**：`[12, 16, 17]`、"
                "`moved = [T,F,F,F,F,T,F,T]` ⇒ 布完 12 之后**连按 4 次都不布**"
                "（焦点停在 `导出时间线`/`全屏编辑`/`静音`/`添加素材到时间线` "
                "这四个**内层控件**上）⇒ **又是 906② 那条规则**；"
                "⚠️ 且 **12 之后跳过了 13/14/15**（press6 直接布 **16**）。\n"
                "**两条设计纪律（907 的教训已落进探针）**：\n"
                "· ⚠️ **`moved` 是必需字段、不是可选** —— `armed` 会被 "
                "`oldValue != '0'` 过滤吞读数（**904 记过、909 又踩一次**）⇒ "
                "`zero_before`/`zero_after`/`moved` **三条一起记**才不漏读。\n"
                "· ⚠️ **走查停止条件不能拍脑袋给次数** —— 要写成"
                "「**观测到第二次布到 0**」（908 的做法）。") ,
            "source_endpoint_to_start_three_bands_911": (
                "✅ **911 把 910 那个「宽 15 个下标」的区间夹窄了，"
                "同时修正了 910 的「二档」描述 —— 中间还有一档 `11`。**"
                "（源站，5 臂 × 2 轮 = 10 条，**两轮逐条一致**；"
                "设计**逐字沿用** 910，只换 `j`；终点**实测**）\n"
                "**读数（实测终点 → 回来后第一次布的下标）**：\n"
                "· **`∅ … 33` ⇒ 0**（910 的 `∅/2/3/10/20/31` ＋ 911 的 **33**）\n"
                "· **`36 / 39` ⇒ 11** ← **这一档 910 没采到**\n"
                "· **`42 … 56` ⇒ 12**（911 的 **42/45** ＋ 910 的 **46/56**）\n"
                "⇒ **三档**（不是 910 说的两档）；⚠️ **两个边界仍未夹逼**："
                "**`(33, 36]` 与 `(39, 42]` 各还差 3 个下标** ⇒ "
                "**不许**把「≤33→0、36–39→11、≥42→12」当规则。\n"
                "**⚠️ 911 顺带收窄了 900 那条**：900 说「有 2 个节点整轮没被布 "
                "`'0'`」（下标 **12 / 68**），908 也复现过一次 ⇒ 但 **911 里 "
                "下标 12 **被布上了**（`42` 与 `45` 两档的 press1 都布 `12`）**"
                "⇒ ⚠️ **「整轮没被布」是「正序走查那一轮」的属性，"
                "不是该节点的固有属性** ⇒ **900 那条要按这个口径读**，"
                "**不许**拿它去解释「为什么起点是 11 或 12」。\n"
                "**三档的逐次轨迹（同一个落点序列，分岔在 press5）**：\n"
                "· `0` 档：press1 布 `0`、落点 `视频 node: 视频 1`（**节点 0 的本体**）\n"
                "· `11` 档：press1 布 `11`、落点 `导出时间线`；press5 落点 "
                "`音频 node: 音频 6`；press6 布 **`13`** ⇒ **跳过了 12**\n"
                "· `12` 档：press1 布 `12`、落点 `导出时间线`；press5 落点 "
                "`图片 node: b22-upload`；press6 布 **`16`** ⇒ **跳过了 13/14/15**\n"
                "⇒ **`11` 与 `12` 两档的 press1–press5 落点完全相同**"
                "（`导出时间线`→`全屏编辑`→`静音`→`添加素材到时间线`）"
                "⇒ 分岔**只体现在 press5 的落点**上。"
                "⚠️ **成因仍未查明**（这是描述、不是机制）。\n"
                "⚠️ **再次提醒**：910 已经钉过「**12 是 900 那两个特殊节点之一**」"
                "**只是相关、不是机制**；911 的读数**又把它削弱了一层**"
                "（12 在 911 里**能被布上**）⇒ **更不许**拿它编规则。") ,
            "source_endpoint_to_start_bands_1wide_912": (
                "✅✅ **912 把 911 剩下的两个边界都收成了 1 宽。**"
                "（源站，4 臂 × 2 轮 = 8 条，**两轮逐条一致**；"
                "设计**逐字沿用** 911、只换 `j`；终点**实测**）\n"
                "**912 自己的读数**（实测终点 → 回来后第一次布的下标）：\n"
                "· **`34` ⇒ 0**、**`35` ⇒ 0**\n"
                "· **`40` ⇒ 11**\n"
                "· **`41` ⇒ 12**\n"
                "**⇒ 三批（910/911/912）合起来，完整的经验映射是**：\n"
                "· **终点 `≤ 35` ⇒ 起点 `0`**"
                "（实测过 `∅ / 2 / 3 / 10 / 20 / 31 / 33 / 34 / 35`）\n"
                "· **终点 `36 … 40` ⇒ 起点 `11`**（实测过 `36 / 39 / 40`）\n"
                "· **终点 `≥ 41` ⇒ 起点 `12`**（实测过 `41 / 42 / 45 / 46 / 56`）\n"
                "⇒ **两个边界都收成 1 宽**：**`35 | 36`** 与 **`40 | 41`**。\n"
                "⚠️⚠️ **但这仍然只是「终点 → 起点」的经验映射，不是机制** —— "
                "**为什么是 0 / 11 / 12、为什么分界落在 35|36 与 40|41，"
                "全部未查明**。⚠️ **不许**把它写成规则、**不许**据此改实现"
                "（复刻侧目前固定布 `0`，见 `replica_roving_strict_wrapper_909`）。\n"
                "⚠️ 值得记的一条**巧合级别的观察（不是解释）**："
                "三个起点 **`0 / 11 / 12` 里后两个是相邻的**。"
                "⚠️ **这只是数字对得上，机制一个字都没测到** ⇒ "
                "**不许**拿它当解释、**不许**拿它去推规则。\n"
                "⇒ **进度**：910 把区间从 **15 宽**收到 3+3 宽；"
                "911 收到 **3 + 3**；912 收到 **1 + 1**。"
                "⚠️ **收窄的是「经验边界」，不是「理解」** —— "
                "**成因仍然未查明**，这条不许就此结案。") ,
            "source_endpoint_start_not_a_pure_function_913": (
                "⚠️❌ **913 的证伪没做成 —— 这一批只能当「复现」用，"
                "不许拿它说「起点是终点的纯函数」。**（源站，4 臂 × 2 轮 = 8 条，"
                "两轮逐条一致）\n"
                "**这一批本来要问什么**：910–912 每条臂的路线都是**同一条**"
                "（从画布根连按 `j` 次 ⇒ 点空白 ⇒ 回来按 `Tab`）⇒ "
                "**「终点」与「历史」是共变的** ⇒ 那张映射表**分不清**"
                "起点到底跟着**终点**走、还是跟着**某段别的历史**走。"
                "⇒ 设计是「**同一个终点、两条不同路线**」"
                "（`A` 只往前走 ／ `B` 往前走**再往回走回来**）。\n"
                "**✅ 真的测到的（复现）**：`A-fwd49` 终点 **40** ⇒ 起点 **11**、"
                "`A-fwd60` 终点 **51** ⇒ 起点 **12** ⇒ "
                "**与 `source_endpoint_to_start_bands_1wide_912` 逐条相同**（2/2）"
                "⇒ 912 那张表**又稳了一次**。\n"
                "❌ **没测到的（这一批的证伪落空）**：**两条 `B` 臂的"
                "「往回按了 0 次」** —— 因为 `ARMS` 里 `B` 臂的 `j` 填的是 "
                "**`49` / `60`**，而那正是**直接落在目标终点 `40` / `51` 上的**"
                "那个 `j` ⇒ **自适应停止条件一进去就满足、一次都没往回按** ⇒ "
                "**`A` 与 `B` 实际是同一条路线** ⇒ "
                "**「同一终点、两条不同路线」这个对照根本没成立**。\n"
                "⚠️ **这是我自己设计上的错，钉住当教训**："
                "**证伪臂的 `j` 必须「越过」目标终点**，再往回走回来 —— "
                "否则**两条臂是同一条**，那一问**根本没被问到**"
                "（与 899/901「按压次数要盖过被吃掉的那部分，否则末尾行为根本没被问到」"
                "**同一条教训**：**参数取在对照组自己的取值上，对照就作废了**）。\n"
                "⇒ **因此**：⚠️ **不许**据 913 说「起点是终点的纯函数」；"
                "⚠️ 也**不许**据 913 说「起点跟历史走」—— "
                "**两个方向这一批都没测到**。**要改成 `j` 越过目标**"
                "（`55→40`、`65→51`）再重做。\n"
                "⇒ ✅ **914 已经用正确设计重做了，见 "
                "`source_endpoint_start_invariant_to_history_914`**；"
                "**本条保留为历史**（记着「这一批问了个空的」这件事）。") ,
            "source_endpoint_start_invariant_to_history_914": (
                "✅ **914 第一次把 913 落空的那个证伪真正做成了** —— "
                "**同一个终点、两条真的不同的路线 ⇒ 起点与全程布序列逐条相同**。"
                "**（源站，3 对 × 2 轮 = 6 组比较，两轮逐条一致；"
                "`jimeng_probe914_two_routes_real_backwalk_src.py`）\n"
                "**三条对照**（每对两条臂**只差「有没有越过去再走回来」**）：\n"
                "① 终点 **35**：`A-fwd44`（纯正走）／"
                "`B-fwd45-back35`（正走到 **36** 再往回 **1** 次）"
                "⇒ 两条都 ⇒ 起点 **0**、全程布 `[0,1,2,3]`；\n"
                "② 终点 **40**：`A-fwd49`／`B-fwd55-back40`"
                "（正走到 **46** 再往回 **6** 次）"
                "⇒ 两条都 ⇒ 起点 **11**、全程布 `[11,13,14]`；\n"
                "③ 终点 **51**：`A-fwd60`／`B-fwd65-back51`"
                "（正走到 **56** 再往回 **5** 次）"
                "⇒ 两条都 ⇒ 起点 **12**、全程布 `[12,16,17]`。\n"
                "⇒ **910–912 那个「终点与历史共变」的顾虑被排除了**："
                "起点对**「越过终点再往回走回来」这段历史不敏感** "
                "⇒ 那张表**不只是共变假象**。\n"
                "⚠️⚠️ **但这只排除了「一种」历史扰动** ⇒ "
                "⚠️ **不许**把「起点是终点的纯函数」写成全称规则 —— "
                "别的历史轴（先往回走进画布、点某个节点再走开、…）**一个都没测**。\n"
                "⇒ ✅ **915 已经测了第二条轴**（「最终那一段走查之前的前史」），"
                "见 `source_prehistory_irrelevance_915`；"
                "⚠️ **914+915 合起来只排除了两种历史扰动**，"
                "**仍然不是全称规则**。\n"
                "⚠️ **仍然未查明**：**为什么是 `0 / 11 / 12`**、"
                "**为什么分界在 `35|36` 与 `40|41`** —— 本批**一条新机制都没测到**，"
                "**不许**据此结案、**不许**据此改实现。\n"
                "✅ **顺带测到一条新读数（`36→35`、"
                "`46→45→44→43→42→41→40`、`56→55→54→53→52→51`，"
                "两轮逐条一致）**：**反向走是严格 `−1`** —— "
                "每按一次 `Shift+Tab`、`'0'` 退**恰好一个**下标。"
                "⚠️ 但这段区间**不含**下标 `12 / 68` 那两个特殊节点 "
                "⇒ **「反向走会不会也跳过特殊节点」仍然没测到**，不许外推。\n"
                "✅ **探针这一批自己长了一道防线（本批最值钱的改动）**："
                "每条 `B` 臂都记 `design_ok`，它**同时**要求"
                "① 正走终点 **≠** 目标、② `n_back_presses >= 1`、"
                "③ 实测终点 **==** 目标 —— 三条里任何一条不成立就"
                "**打「设计违规」标记**，基线**不许**把那一条当对照读。"
                "⇒ 913 那种「两条臂其实是同一条」的错，"
                "**现在会让探针自己叫出来**，而不是静默产出一份"
                "看起来没问题的同路线对比。"
                "（⚠️ 静态侧还有一道：`B` 的 `j` 不严格大于同对 `A` 的 `j` "
                "就**开跑前 assert 挂掉**。）\n"
                "⚠️ **本批踩到的流程坑（同样钉住）**：探针 stdout "
                "**重定向到文件时忘加 `-u`** ⇒ 块缓冲把日志全压在内存里，"
                "**跑了 10 分钟日志 0 行**，"
                "**分不清「在跑」还是「挂住」**（只能靠 `ps` 看 Chrome GPU 进程的 CPU）"
                "⇒ ⚠️ **重定向到文件的探针一律要加 `-u`**。") ,
            "source_prehistory_irrelevance_915": (
                "✅ **915 测了第二条历史扰动轴 —— 「最终那一段走查之前的历史」"
                "无关**（源站，8 臂 × 2 轮 = 16 条，两轮逐条一致；"
                "`jimeng_probe915_prehistory_irrelevance_src.py`）\n"
                "**设计**：每个扰动臂的「**最后一段走查**」与某条**基线臂**逐字相同"
                "（同样 `j`、同样从画布根起步），**只有前面多了别的走查 + 一次点空白**。"
                "**读数（16 条全中）**：\n"
                "· 终点 **40**：`A-fwd49`（基线）／`D1-pre30-fwd49`"
                "（`fwd 30`⇒点空白⇒`fwd 49`）／`D2-pre30-back5-fwd49`"
                " ⇒ 三条都 ⇒ 起点 **11**、全程布 `[11,13,14]`；\n"
                "· 终点 **35**：`B-fwd44`（基线）／`H-pre30-back5-fwd44` "
                "⇒ 两条都 ⇒ 起点 **0**、全程布 `[0,1,2,3]`；\n"
                "· 终点 **51**：`E-fwd60`（基线）／`F-pre30-fwd60`／"
                "`G-pre30-back5-fwd60` ⇒ 三条都 ⇒ 起点 **12**、全程布 `[12,16,17]`。\n"
                "⇒ **10 组「扰动臂 vs 同目标基线臂」比较，同终点、同布序列、"
                "同首次布下标，10/10** ⇒ **前史无关**。\n"
                "⚠️❌ **但本批只测到「一种」扰动形状**：`D2 / G / H` 的"
                "「**回走 5**」那一步**实测是空操作** —— `armed_idx` 空、"
                "`moved` 全 `False`、**终点也没动** ⇒ 那三条臂的前史"
                "**其实只等于「`fwd 30` + 点空白」** ⇒ **与 `D1 / F` 不是两种扰动**。"
                "⚠️ 我**以为**测了两种形状（带/不带回走），**实际上只测了一种** ⇒ "
                "**不许**拿 915 说「两种扰动都无关」。\n"
                "✅ **顺带第三次证实 `source_roving_direction_asymmetry_906` 那条规则**"
                "（906/909 之后第三次）：`fwd 30` 的**最后两次**按压也**一次都没布**"
                "⇒ 那一刻焦点落在**某个节点的内层控件**上 ⇒ 随后的 `Shift+Tab` "
                "自然也一次都不布 ⇒ **「按压前焦点在内层控件 ⇒ 一次都不布」。**\n"
                "⚠️⚠️ **第一版整个作废过一次（钉住）**：915 是从 914 改造来的"
                "（把「按 `j` 次」改成「按**步骤表**」走），"
                "**改造时把 913/914 每臂开头那句 `blank()` 顺手删掉了** —— "
                "在新结构里它看着像多余的 setup。"
                "⇒ **第一批读数就撞出来**：`A-fwd49` 终点 `[29]`（914 同一条臂是 "
                "`[40]`）、首次布 `0`（914 是 `11`）⇒ **走查根本没从画布根起步**。\n"
                "⇒ **教训（比 913/914 那条更基础）**：**改造既有探针时，"
                "不要把原探针里那些「看起来多余」的前置动作删掉** —— "
                "它们常常是**承重**的；在这里，那句 `blank()` 就是"
                "**全部走查臂的有效性前提**，而它在代码里只是**一行像 setup 的调用**。\n"
                "⇒ **两处修法（都已落地）**：① 补回那句 `blank()`；"
                "② **让探针自己看得见** —— `design_ok` 现在**对基线臂也设门槛**"
                "（第一版基线臂写死 `True`，结果这条臂照样报 ok —— "
                "**门槛漏在基线上就等于没有**），并要求 `init_blank` 真的点到空白。\n"
                "⇒ **第三处（下一步要做）**：**扰动步骤自己可能是空操作** —— "
                "「我按了 5 次」**不等于**「前史被扰动了」⇒ "
                "探针现在**每一步都记 `step_effective` / `n_armed` / `n_moved`**。"
                "⚠️ **本批这一版的读数是在补这个探针之前跑的** ⇒ "
                "「回走 5 是空操作」这件事是**读数之后人工看出来的**，"
                "不是探针自己报出来的 —— **这一点要如实记着**。\n"
                "⇒ ✅ **916 已经把「带回走」那一档真正做成了**（回走"
                "**真的咬到**、前史**仍然无关**），见 "
                "`source_bite_walkback_prehistory_916`；⚠️ 但 916 的回走"
                "**实际只走了 1 步** ⇒ **「长距离回走」仍然没测到**。\n"
                "⚠️ **仍然未查明**：**为什么是 `0 / 11 / 12`**、"
                "**为什么分界在 `35|36` 与 `40|41`** —— 914 与 915 **合起来"
                "只排除了两种历史扰动**，**一条新机制都没测到** ⇒ "
                "**不许**把「起点是终点的纯函数」写成全称规则、"
                "**不许**据此结案、**不许**据此改实现。") ,
            "source_bite_walkback_prehistory_916": (
                "✅ **916 把 915 塌缩掉的那一档（带回走）真正做成了** —— "
                "回走**真的咬到**了，前史**仍然无关**。"
                "**（源站，6 臂 × 2 轮 = 12 条，两轮逐条一致；"
                "`jimeng_probe916_bite_then_walkback_src.py`）\n"
                "**怎么让它咬到**：⚠️ **不许**再拍脑袋给「回走 N 次」"
                "（907/908/899 的教训）⇒ 改成**自适应停止条件**："
                "一直按 `Shift+Tab`，**直到某一次真的把 `'0'` 挪动了**"
                "（`moved == True`）才算咬到，**上限 40 次只是封顶**；"
                "咬到后再**多按 3 次**留余量。\n"
                "**读数（6 条扰动臂 `bitten` 全 True）**：\n"
                "· 终点 **40**：`I2-bite30-raw49` vs 基线 `A-fwd49` "
                "⇒ 同终点、同布序列 `[11,13,14]`、同首布 **11**；\n"
                "· 终点 **35**：`J2-bite30-raw44` vs 基线 `B-fwd44` "
                "⇒ 同终点、同布序列 `[0,1,2,3]`、同首布 **0**；\n"
                "· 终点 **51**：`K2-bite30-raw60` vs 基线 `E-fwd60` "
                "⇒ 同终点、同布序列 `[12,16,17]`、同首布 **12**。\n"
                "⇒ **6/6 组一致（两轮逐条相同）** ⇒ "
                "**前史里含一次「真的」回走，起点仍然不变。**\n"
                "✅ **顺带一条重要的新读数（把 899/901 那条规则量化了）**："
                "`fwd 30` 之后，**一连 28 次 `Shift+Tab` 一次都没布**"
                "（逐次 `moved` 全 `False`），**第 29 次才咬到**"
                "（`armed 22`、`'0'` **23→22**）；⚠️ 6 条里有 1 条咬在**第 33 次**。"
                "⇒ **915 给的「回走 5」差了一个数量级** —— "
                "它不是「少按了几次」，而是**根本没问到回走**。\n"
                "⚠️ **但「回走」实际只走了 1 步**（`'0'` 23→22；"
                "咬到之后再按 3 次**又都不布**）⇒ "
                "⚠️ **「长距离回走」这一档仍然没测到** ⇒ "
                "**不许**拿 916 说「回走多远都无关」。\n"
                "⚠️ **为什么咬到之后就又不咬了，与 906 一致**："
                "每次布完 `'0'`，焦点又落在**内层控件**上 ⇒ "
                "下一次 `Shift+Tab` 自然又不布 ⇒ 要再走一步得**再等约 28 次**。"
                "⚠️ **但一个不对称没查明**：**正向**走查里的死按压是**成串 4 次**，"
                "**反向**却要**连 28 次** ⇒ **为什么两边差这么多，未查明** ⇒ "
                "**不许**拿「焦点在内层控件上」这句话去编解释。\n"
                "✅ **探针这一批又长了一道防线**：916 独有的门槛是 "
                "`design_ok` **必须** `bitten == True` —— "
                "**没有它就会静默退化成 915**（空操作也算通过）。"
                "⚠️ 另外**基线臂也设了门槛**（915 第一版写死 `True`，"
                "**门槛漏在基线上就等于没有**）并要求 `init_blank` 真点到。\n"
                "⚠️ **916 自己的记录缺口（已补、供 917 用）**：`bite` 步"
                "**没有逐次记按压前的焦点落点** ⇒ 那 28 次死按压时"
                "**焦点在哪看不到** ⇒ 已补 `per_press_pre`"
                "（逐次记 `pre_aria` / `pre_is_wrapper` / `land_aria`）。\n"
                "⚠️ **仍然未查明**：**为什么是 `0 / 11 / 12`**、"
                "**为什么分界在 `35|36` 与 `40|41`** —— 914/915/916 **合起来"
                "只排除了三种历史扰动**（同段内越过+回走 ／ 前置走查+归零 ／ "
                "前置走查+真回走+归零），**一条新机制都没测到** ⇒ "
                "**不许**把「起点是终点的纯函数」写成全称规则、"
                "**不许**据此结案、**不许**据此改实现。\n"
                "⇒ ✅⭐ **917 把「死按压期间焦点在哪些元素上走」完整记录下来了**"
                "（916 记过、但**没跑**的那个缺口），见 "
                "`source_focus_trace_dead_presses_917`；"
                "⚠️ 且 917 **更正了 916 的停止条件**（`armed` 会越界触发）"
                "⇒ 916 的「咬到」**可能提前结束过**。") ,
            "source_focus_trace_dead_presses_917": (
                "✅⭐ **917 第一次把「死按压期间焦点到底在哪些元素上走」"
                "完整记录下来了** —— 这是 916 记过、但**没跑**的那个缺口。"
                "**（源站，6 臂 × 2 轮 = 12 条，两轮逐条一致；"
                "`jimeng_probe917_multi_bite_focus_trace_src.py`；"
                "逐次焦点记录 996 条，每条都带 `pre_aria` / `pre_is_wrapper` / "
                "`land_aria` / `moved`）\n"
                "**为什么问这个**：916 撞出一个**不对称** —— "
                "**正向**走查里的死按压是**成串 4 次**（本批还看到 **1 次**的），"
                "**反向**却要**连 28 次**才动 ⇒ **为什么两边差这么多，没查明**。\n"
                "✅ **⭐ 正向：死按压数 = 刚被布的那个节点自己的内层控件个数**"
                "（本批轨迹里两次都数上了）：布完 node 3 焦点落到它的 "
                "`导出时间线` ⇒ 于是**恰好 4 次**死按压"
                "（`导出时间线`→`全屏编辑`→`静音`→`添加素材到时间线`）"
                "才回到下一个节点的本体；另一处布完落到 `替换媒体` ⇒ "
                "**恰好 1 次**死按压。⇒ **正向那侧「被吃掉多少」= "
                "那个节点有几个内层控件**，这条**已被读数完整解释**。\n"
                "✅ **⭐ 反向：死按压把焦点「带出画布」，把整页反向走一遍**"
                "（916 记的 28 次，**逐次路径**）：`静音`→`全屏编辑`→`导出时间线`→"
                "`替换媒体`→`添加素材到时间线`→（在节点内**转了一轮**）→"
                "`Canvas`→`用户菜单`→`Credits`→`更多`→`分享`→`生成历史`→`搜索`→"
                "`Canvas node summary…`→`项目`→`Canvas title`→`返回首页`→…→"
                "`Zoom options`→`显示连线`→`小地图`→`选择工具`→`文本`→`全部清空`→"
                "`Add tags`→**节点本体** ⇒ **第 29 次按压**按前焦点才落在节点本体上、"
                "这时才布（`'0'` **23→22**）。\n"
                "⇒ **一句话**：**正向下一格的「死按压」只有那个节点的内层控件那么多；"
                "反向却要跨出画布、把整页走一遍。** "
                "⚠️ 但**为什么反向的 tab 序会绕整页**（而不是回到上一个节点的本体）"
                "**仍然未查明** —— 路径是**实测**的，**成因不是** ⇒ "
                "**不许**拿上面那句话当机制、不许据此改实现。\n"
                "✅ **前史仍无关（6/6，与同目标基线臂逐条相同）**：终点 40 ⇒ 首布 "
                "**11**、35 ⇒ **0**、51 ⇒ **12** ⇒ "
                "**914/915/916/917 合起来只排除了四种历史扰动**，"
                "**仍然不是全称规则**。\n"
                "✅⚠️ **本批新加的门当场抓到了东西**：`design_ok` 的"
                "「**实测真的退了 `k` 步**」这一条把 **6/6 扰动臂全标成设计违规** —— "
                "「咬到 3/3」但**实退只有 1 步** ⇒ **「咬到几次 ≠ 退了几步」**。"
                "**没有这道门，917 会静默地声称测了「三步回走」** —— "
                "**这正是 915/916 同一个错误的第三次出现，第三次被门挡住。**\n"
                "⚠️⚠️ **一条方法论更正（比结论更重要）**：**`armed` 这个信号"
                "会在非 `.react-flow__node` 的元素上触发** —— "
                "917 实测到 `el:BUTTON.inline-flex.items-center#0` 上 `armed` 响了、"
                "而**节点里的 `'0'` 根本没动**（`armed_idx` 为空、`moved=False`）"
                "⇒ **`armed` 触发 ≠ `'0'` 移动**。⚠️ **916 用的停止条件正是 "
                "`moved or armed` ⇒ 那一版的「咬到」可能提前结束** "
                "⇒ 917 已把停止条件**收紧成只用 `moved`**。\n"
                "⚠️ **917 自己的探针缺陷（已修）**：`bite_k` 里 `zero_before` "
                "原来是在 `one_bite()` **跑完之后**才取的 ⇒ 打印出来是 "
                "`[22]→[22]` 这种**假象**（咬完的状态冒充咬之前的状态）"
                "⇒ 真实的 `23→22` 被抹掉。⚠️ **判读纪律：前态必须在扰动之前取**，"
                "否则「前态 vs 后态」是空话。\n"
                "⇒ ✅ **918 已经用收紧后的「只用 `moved`」重做了这一批**，见 "
                "`source_movedonly_retreat3_918`：**实退真到了 3 步**"
                "（917 只到 1 步）⇒ 917 那道「实退 `k` 步」的门**在收紧之后才过**。") ,
            "source_movedonly_retreat3_918": (
                "✅ **918 用收紧后的「只用 `moved`」停止条件重跑多步回走 ⇒ "
                "实退真到了 `k` 步**（917 只到 1 步）。"
                "**（源站，6 臂 × 2 轮 = 12 条，两轮逐条一致；"
                "`jimeng_probe918_movedonly_and_taborder_src.py`）\n"
                "**读数**：6 条扰动臂**全部** `n_bites_bitten = 3/3` 且 "
                "`n_zero_steps_retreat = 3`（`design_ok` 全 True）—— "
                "`'0'` 真的退了 **3 步**（`23→22→21→20`）⇒ "
                "**917 那道「实退 `k` 步」的门，在收紧停止条件之后终于过了。**\n"
                "**咬到次数高度可复现**：三次咬分别是 **第 29 / 5 / 1 次**才咬到，"
                "**6 条逐条一致**（两轮 × 三条扰动臂）⇒ "
                "⚠️ 这个序列**不是**「越往后越难」，而是"
                "**第一次要把焦点从整页走回画布、后面就只差一个节点内层控件的个数**。\n"
                "✅ **前史仍无关（6/6，与同目标基线臂逐条相同）**：终点 40 ⇒ 首布 "
                "**11**、35 ⇒ **0**、51 ⇒ **12** ⇒ "
                "**914/915/916/917/918 合起来只排除了五种历史扰动**，"
                "**仍然不是全称规则**。\n"
                "⚠️❌ **DOM tab 序直读这一半「落空」了 —— 但落空本身就是结果**："
                "`TABORDER_JS` 在画布根内**只找到 10 个可聚焦元素、"
                "`n_wrappers = 0`（76 个节点里一个都没匹配上）** ⇒ "
                "✅ **中性态下节点本体根本没有 `tabindex`、根本不在 tab 序里** ⇒ "
                "它是**被应用在 keydown 布的那一刻临时注入进去的**"
                "（这正是 roving tabindex 的定义）。\n"
                "⇒ ⚠️ **这反过来否掉了 917 那个候选解释的方向**："
                "917 想查「节点本体相对它自己内层控件的 **DOM 位置**」—— "
                "**在静态 DOM 里压根就没有「本体」这个可聚焦元素可查** ⇒ "
                "**那个提法方向就是错的**（不是结论错，是**问错了地方**）。\n"
                "⚠️ **但「为什么反向仍要 29 次才回到一个本体」仍然没查明** —— "
                "「本体是动态注入的」**解释得了**「它不在静态 tab 序里」，"
                "**解释不了**「反向要跨出画布把整页走一遍」。⇒ "
                "**不许**把「动态注入」当这个不对称的答案。\n"
                "⚠️ **918 自己的探针缺口（如实记着）**：① 只把 tab 序的 "
                "`summary` 存进了记录、**没存那 10 个元素分别是谁**；"
                "② 更要紧的是 —— **内层控件一个都没被选择器匹配上**"
                "（917 的焦点轨迹明明能走到 `导出时间线`/`全屏编辑`/`静音` 这些），"
                "⇒ **要么选择器漏了、要么那些控件不在 `.react-flow` 子树里** ⇒ "
                "**未查明**，**不许**猜。\n"
                "⚠️ **918 第一版自己撞了变量名**：算 tab 序直方图那两个累加器"
                "本来叫 `before` / `after` ⇒ **`after` 把上面那个"
                "「回来后 8 次按压的记录列表」覆盖成了整数** ⇒ 紧接着 "
                "`\"after_per_press\": [...]` 报 "
                "`TypeError: 'int' object is not iterable`、**整轮跑废**。"
                "⚠️ **教训：别给新变量起「这一层里已经用过的名字」** —— "
                "`before` / `after` 在走查代码里是**承载读数的列表**，不是布尔量。") ,
            "source_inner_control_anatomy_919": (
                "✅⭐ **919（纯诊断）把 918 的「选择器漏了 / 不在子树里」"
                "那个二选一直接排掉了**（源站，2 轮逐条一致；"
                "`jimeng_probe919_inner_control_anatomy_src.py`）。"
                "⚠️ **先纠正我自己一个误判**：918 报「画布内可聚焦 **10** 个」、"
                "919 报「**163** 个」—— 我一度以为是**两个探针报数矛盾**。"
                "❌ **作废**：918 的 `TABORDER_JS` **多了一道过滤器**"
                "（「`tabindex` 属性 `< 0` 就跳过」），919 那道**没加** ⇒ "
                "**两个数各自都对、只是口径不同**。"
                "⇒ ⚠️ **这条本身就是「一次异常读数不足以立机制」的又一次应用**："
                "**两个数不同 ≠ 有矛盾**，得先查**口径**。\n"
                "✅ **那 5 个内层控件的真实身份**（两轮逐条相同）："
                "`导出时间线` / `全屏编辑` / `静音` / `添加素材到时间线` / `替换媒体` "
                "**全都是 `<BUTTON>`**、**都在 `.react-flow` 里**、"
                "**`shadow_depth = 0`**（`querySelectorAll` 不穿透 shadow DOM，"
                "而它们**本来就不在 shadow 里**）⇒ "
                "⚠️ **918 那句「要么选择器漏了、要么不在子树里」两个都不是**。\n"
                "⭐ **它们最要紧的一个性质**：`tabindex` **属性是 `None`"
                "（压根没这个属性）**，而 **IDL `tabIndex = 0`** ⇒ "
                "**它们靠的是「原生 `<button>` 默认可聚焦」，不是靠 `tabindex` 属性。**\n"
                "✅ **IDL 口径的普查（这才是顺序焦点导航真正走的口径）**："
                "**中性态画布内只有 10 个可聚焦元素、整篇 document 只有 27 个** "
                "⇒ **整页能被 Tab 到的元素极少**；"
                "而**属性口径**（含 `tabindex=\"-1\"` 的）画布内有 163 个 "
                "⇒ 两者差 16 倍，**口径必须写清楚、不许混用**。\n"
                "⭐ **布上之后本体被注入到哪一位（两轮逐条一致）**："
                "按一次 `Tab` 之后，被布的那个本体"
                "（`视频 node: 视频 1`）**`tabindex` 属性 = `0`、IDL `tabIndex = 0`**，"
                "**落在 IDL 序的第 11 位**：**紧跟在 `Canvas`（画布根）之后、"
                "在它自己的第一个内层控件 `导出时间线` 之前** ⇒ "
                "**本体排在自己的内层控件「之前」**，而且它**就是 `activeElement`**。\n"
                "⚠️❌ **但这一批撞出一个真缺口、而且本批没有解释**："
                "中性态普查说**画布内没有任何节点本体是可聚焦的**"
                "（`n_wrappers_with_ti0 = 0`、IDL 列表里 0 个本体），"
                "可是 917/918 的**焦点轨迹里按前焦点多次落在「别的节点的本体」上**"
                "（`pre_is_wrapper = True`，例如 `文本 node: 文本 2`）⇒ "
                "**焦点怎么会落到一个没有 `tabindex` 的元素上？** "
                "⇒ **要么「本体可聚焦」这件事在普查那一刻和走查过程中不是同一回事**，"
                "**要么焦点是程序化 `.focus()` 上去的** ⇒ "
                "⚠️ **本批没有测到、没有解释 ⇒ 不许**拿「动态注入」一句话糊过去。\n"
                "✅ **顺带钉一条纪律：919 是「纯诊断」** —— 普查是**纯读**、"
                "**不劫持 prototype、不装 MutationObserver** "
                "⇒ **诊断不许破坏被诊断状态**（这条与 882 那次同源）。\n"
                "⇒ ✅ **920 已经把这个问题问倒了、而且把结论钉下来**："
                "见 `source_focus_always_on_armed_920`。") ,
            "source_focus_always_on_armed_920": (
                "✅⭐ **920 用「每按一次就普查一次」把 919 那个缺口结掉了** —— "
                "**而且结论是「那个问题的前提是错的」。**"
                "**（源站，纯诊断，2 轮 × 每次 14 连按，两轮逐条一致；"
                "`jimeng_probe920_per_press_wrapper_census_src.py`）\n"
                "**919 问的是**：「焦点怎么落到一个（普查时）没有 `tabindex` "
                "的元素上？」\n"
                "**✅ 920 的读数**：走查的每一次按压**按前、按后**各普查一次，"
                "**焦点是本体的时刻共 38 次，其中「焦点所在的下标 == "
                "唯一那个带 `tabindex=\"0\"` 的本体下标」= 38/38** "
                "⇒ **焦点从来不会停在一个没有 `tabindex` 的本体上** "
                "⇒ ⚠️ **919 那个问题本身不成立**（「不存在那一刻」）。\n"
                "**⇒ 顺带钉死一条**：整个走查过程中 "
                "`n_wrapper_ti0` 与 `n_wrapper_idl_focusable` "
                "**取值集合都只有 `{0, 1}`** ⇒ "
                "**任何时刻至多只有一个本体可聚焦**（两轮各 28 次普查全中）"
                "⇒ **roving 是「单指针」、不是「留轨迹」**。\n"
                "⭐ **另有一条重要读数（919 没看到）**："
                "**归零那一刻 `n_wrapper_any_ti = 0`（一个 `tabindex` 属性都没有）**，"
                "而**按第 1 次之后立刻变成 76**（**1 个 `'0'` + 75 个 `'-1'`**）"
                "⇒ **应用不是只给一个节点打 `tabindex`，而是第一次就把"
                "**所有**节点都管起来**（其余显式 `'-1'`）。\n"
                "⚠️ **但「为什么按第 2 次之后变成 75」我没查明**："
                "从样本看像是「焦点在**两次之前**那个本体的 `tabindex` 属性被移除」，"
                "但⚠️ **样本只有约 8 个、而且只看的是**前 12 个**的切片** "
                "⇒ **这个规律不成立、只是观察** ⇒ "
                "**不许**拿它编规则，**要重测就得把整张表存下来**。\n"
                "✅ **一条纪律**：920 也是**纯诊断** —— 普查**纯读**、"
                "**不劫持 prototype、不装 MutationObserver** ⇒ "
                "**诊断不许破坏被诊断状态**。\n"
                "⚠️ **919 那句「焦点可能落在别的节点本体上」的表述要收窄**："
                "它**本身没错**（焦点确实多次落在本体上），"
                "但**它总是「当前被布的那个」本体** ⇒ "
                "**不是「别的本体」** ⇒ 921 起按这个收窄后的说法记。") ,
            "source_tabindex_rolling_window_921": (
                "✅⭐ **921 用「整张表 + 逐次 delta」把 920 那个「76 → 75」查清了**。"
                "**（源站，纯诊断，2 轮 × 每次 16 连按，两轮逐条一致；"
                "`jimeng_probe921_full_table_and_delta_src.py`）\n"
                "**920 的缺口**：第一次布之后 `n_wrapper_any_ti = 76`，"
                "第二次布之后变成 75 ⇒ **有且仅有一个本体的 `tabindex` 属性消失了**；"
                "920 从 `slice(0, 12)` 里猜「是两次之前那个被移除」⇒ **只是观察**。\n"
                "**✅ 查清的结果：应用做的两类事件必须分开看** ——\n"
                "**① 初始化（第一次布，只有一次）**：**给所有节点都写上 `tabindex`**"
                "（`added = [0…75]`、1 个 `'0'` + 75 个 `'-1'`、"
                "`removed = []`、`changed = []`）⇒ 920 读到的那个 **76 就是这个初始化态**。\n"
                "**② 之后每一次「臂事件」（指针真的移动）**：应用**恰好做三件事** —— "
                "`removed` = **上一个臂事件**的下标（**`tabindex` 属性被整个移除**，"
                "**不是**被设成 `'-1'`）；`added` = **上上个臂事件**的下标"
                "（属性被**写回**、值是 `'-1'`）；`changed` = **本次**被布的那个下标"
                "（`'-1'` → `'0'`）⇒ **24/24 逐条成立**（两轮各 12 次臂事件）。\n"
                "**⇒ 由此得到一条不变式（两轮各 11 次臂事件后逐条成立）**："
                "**任何时刻恰好有 1 个本体没有 `tabindex` 属性**（就是「上一个臂事件」"
                "那个）⇒ **`n_wrapper_any_ti` 从第二次布起恒为 75**。\n"
                "**✅ 顺带钉死一条**：指针**没有**移动的那些按压（死按压）—— "
                "`removed` / `added` / `changed` **全空** ⇒ "
                "**应用完全没碰 `tabindex` 属性**，**8/8 成立**。"
                "⚠️⚠️ **【926 收窄，2026 追加 —— 原文一个字不许删】** "
                "926 实测到**一条反例**：在「退到下界 → 冻结整页循环 → 翻回正向」"
                "这个序列里，**冻结之后的第 2 次正向按压**虽然 `'0'` **没动**"
                "（`moved = False`），却做了 **`added = [1]`**"
                "（给下标 `1` **写回**了 `tabindex`）⇒ "
                "**这条必须收窄成「绝大多数死按压应用不碰 `tabindex`」**，"
                "**不是无条件的**。⚠️ **成因未查明**（1 次异常读数不足以立机制）。"
                "⚠️❌ **920 那个猜法正好把两者对调了**（作废、但**不许删** 920 那段）："
                "920 说「**两次之前**那个被移除」，实际是"
                "「**上一次**那个被移除、被写回的才是**上上个**」⇒ "
                "**两条正好对调**。\n"
                "⚠️ **一条方法论教训（本批最值钱的一条）**："
                "**切片会把规律读反。** 920 用 `slice(0, 12)` 只看**前 12 个**，"
                "而那 12 个里恰好**看不到**「被移除」的那个（它在更靠后的位置）、"
                "**只看到**「被写回」的那个 ⇒ 于是把两者**对调**了。"
                "⇒ ⚠️ **要看全貌就别切片**；"
                "**切片适合「有没有」，不适合「是哪一个」。**") ,
            "source_reverse_cannot_enter_canvas_922": (
                "✅⭐ **922 反向臂被自己的设计门挡住（`design_ok=False`、"
                "`n_armed=0`）⇒ rev 臂读数作废**（**不是**「反向不布」！），"
                "**但顺手查清一条真事实：**"
                "**反向从画布根出发、永远进不了画布。**"
                "**（源站，纯诊断，2 轮 × 每臂 14 次被测按压，两轮逐条一致；"
                "`jimeng_probe922_reverse_arm_window_src.py`）\n"
                "**设计**：想测「921 那条滚动窗口规则在**反向**是不是同一条」⇒ "
                "A 段先连按 `Shift+Tab` 直到**焦点真的落到某个节点本体上**，"
                "B 段才开始记**整张表 + 逐次 delta**。\n"
                "**✅ 测出来的（2 轮逐条一致，60 次按压的完整焦点序列）：**"
                "**60 次 `Shift+Tab` 构成一个周期恰为 27 的「闭环」** —— "
                "`Canvas` 出现在第 27 次和第 54 次（`用户菜单` 在第 1/55 次）"
                "⇒ 整页被反复走；**`moved` 60/60 全 False**（应用一次都没布）、"
                "**`is_wrapper` 60/60 全 False**（焦点**从未**落在本体上）"
                "⇒ **反向从画布根本身出发、永远进不了画布。**\n"
                "**✅ 顺带钉死两条（都把 919/920 的口径往前推了一步）**：\n"
                "**① 闭环里唯一与节点有关的元素是 `Canvas node summary: 节`**，"
                "但它 `is_wrapper = False` ⇒ 它是**汇总元素、不是 `.react-flow__node` "
                "本体** ⇒ **别把它当成本体**。\n"
                "**② 闭环里有节点的「内层控件」**（`添加素材到时间线`/`静音`/"
                "`全屏编辑`/`导出时间线`/`替换媒体`，各出现 2 次）"
                "⇒ ✅ **内层控件在中性态就已经在 tab 序里**（919 已查清它们是原生 "
                "`<BUTTON>`、靠默认可聚焦），**而本体不在**。\n"
                "⚠️⚠️⚠️ **【932 订正 —— 上面「**各出现 2 次**」是错的，"
                "原文一个字不许删】**：逐条数下来是 "
                "**`添加素材到时间线`/`静音`/`全屏编辑`/`导出时间线` 各 2 次、"
                "而 `替换媒体` 只有 1 次**（每个 27 步闭环 9 个内层控件停靠）。\n"
                "**三方确认**（不是单次读数）：**922 自己的落盘** 60 站 `entry` 序列逐条可查、"
                "**932 臂 A 两段 27 窗口 2/2**、**932 臂 B 四圈 2/2** 全都数出同一个 4+1。\n"
                "⇒ 顺带记一条 **owner 归属**（932 新加的 `owner_node_idx`）："
                "**那 9 个槽位分属三个节点 —— `22` 贡献 4 个、"
                "`12` 只贡献 `替换媒体` 那 1 个、`2` 贡献 4 个**\n"
                "⚠️⚠️ **但不许据此说「节点 12 特殊」**：NN.1 已查清 12/68 在 DOM 层"
                "毫无特殊之处（属性集相同、离群 0 个、可聚焦子孙数相同）"
                "⇒ **最简读法是位置性的**（闭环的入口恰好挨着哪几个节点），"
                "**不是内在属性** ⇒ **§122 那条硬约束继续有效：不许编 DOM 层判据去对齐。**\n"
                "⚠️ **成因是推断、不是读数**：读数只证明了「闭环 + 从不布」。"
                "推断链（每一环都是此前已查清的）：中性态 `n_wrapper_any_ti = 0` ⇒ "
                "**没有任何本体有 `tabindex`** ⇒ `<div>` 本体不可聚焦；"
                "而应用**只在臂事件里**写 `tabindex`（921）；"
                "焦点在画布根时反向按压**不布** ⇒ 于是"
                "「没有本体可进」与「不布」**互为因果** ⇒ 永远进不去。"
                "⇒ 这也**解释**了 917/918 为什么必须先 `fwd` 若干次才谈得上回走。\n"
                "✅ **同 run 的正向对照臂（`fwd`）2/2 逐条复现了 921 的规则**："
                "初始化 1 次（`added = [0…75]`）；普通臂事件 9 次 —— "
                "`removed` = 上一个 **9/9**、`added` = 上上个 **9/9**、"
                "`changed` = 本次 **9/9**；死按压 4 次、`removed`/`added`/`changed` "
                "**全空 4/4**；不变式「`n_wrapper_any_ti` 第 2 次起恒 75」"
                "**全程成立** ⇒ **921 的结论在全新运行里站住了**（不只是同一次跑出来的）。\n"
                "⚠️❌ **rev 臂作废**（`design_ok = False`、`n_armed = 0`）："
                "**我的 A 段设计就错了** —— 我以为反向能从画布根走进画布。"
                "⇒ 反向臂**必须先正向布一个**才有本体可退（923 重做）。\n"
                "⚠️ **这一批最值钱的是设计门又救了一次场**："
                "若没有「A 段必须真的落在本体上」这道门，"
                "这份读数会被当成「**反向不布**」的证据写进基线 —— "
                "**一个看起来很正常、实际上什么都没测到的结论。**"
                "⇒ 这是 912 起「探针自己长防线」那条纪律第二次直接挡住一个错误结论。") ,
            "source_rolling_window_direction_symmetric_923": (
                "✅⭐ **923 查清了 §131 那条滚动窗口规则是「不分方向」的** —— "
                "窗口是**一条全局的臂事件流**，不是分方向的。⇒ **方向对称。**"
                "**（源站，纯诊断，2 轮 × 24 次正向 + 16 次反向，"
                "两轮 `arm_stream` 与逐次 delta 完全一致；"
                "`jimeng_probe923_continuous_arm_stream_src.py`）\n"
                "**设计**：**不是**分两段各测一遍，而是**一条连续的臂事件流、中途翻向**"
                "—— `Tab` 连按到下标 19（给反向留退路）→ **不停顿、直接翻成 "
                "`Shift+Tab`** 继续按 ⇒ 每次按压都记**整张表 + 逐次 delta**。"
                "**这样「翻向的那一次」就是最锋利的判别点。**\n"
                "**✅ 判别结果（2/2 逐条一致）**：翻向后**第 1 次**反向臂事件 —— "
                "`pre` 的 `zero_idx = [19]`、焦点在本体 19 上；"
                "`post` 的 `zero_idx = [18]`、焦点在本体 18 上；"
                "**`removed = [19]`、`added = [18]`** ⇒ **正是正向最后那两个臂事件**。"
                "⇒ 若窗口是**分方向**的，第一次反向按压的 `removed`/`added` 应当是**空的**"
                "⇒ 实测**不是** ⇒ **窗口不分方向。**\n"
                "**✅ 全程 34 次臂事件**（正向 19 + 反向 15）："
                "**`removed` = 上一个臂事件（不分方向）34/34 全中**；"
                "死按压 **6 次**、`removed`/`added`/`changed` **全空 6/6**；"
                "不变式「`n_wrapper_any_ti` 恒 75」**跨方向全程成立**。\n"
                "**✅ 两处「偏离三动作」的地方都有确定解释（不许当例外糊过去）**：\n"
                "**① 正向第 1 次按压是「初始化」**（`added` 是 76 项、不是单项）"
                "⇒ §131 已单独记过这个特例。\n"
                "**② 翻向那一次 `changed` 是空的** ⇒ ⭐ 因为反向这一步"
                "**恰好落在正向刚腾空的那个节点上**（`19 → 18`，而 18 正是「上上个」、"
                "并且**没有 `tabindex` 属性**）⇒ 于是 `null → '0'` 被记成 **`added`** "
                "（而不是 `changed`）⇒ **不是规则被破坏，是读数分类撞上了巧合。**\n"
                "**✅ 顺带一条新的一致性证据**：**下标 12 在正反两向都被跳过**"
                "（正向 `11 → 13`、反向 `13 → 11`）⇒ 此前**只观察到正向**跳过它。"
                "⚠️ **成因仍未查明**（§122 已钉：原理上不可从 DOM 查明；"
                "复刻**只能**按纯 DOM 序实现、并把差异**如实记为已知差异**，"
                "**不许**编一个 DOM 层判据去「对齐」它）。\n"
                "⚠️ **一条方法论教训（本批第二条）**："
                "**`post` 那一侧的焦点是这次按压的「结果」、不是 keydown 那刻的「原因」。**"
                "实测有 **3 次**按压的 `post` 焦点**确实在本体上、却一次都没布**"
                "（`delta` 全空）⇒ 因为按压前焦点还在刚被布那个节点的**内层控件**里。"
                "⇒ ⚠️ **不许**拿 `post` 焦点当「这一次 keydown 的落点」"
                "（§130 那条「内层控件 ⇒ 不布」说的才是 **keydown 那一刻**）。") ,
            "source_both_boundaries_stop_no_wrap_924": (
                "✅⭐ **924 在同一次运行里把两个边界都穿过去了**："
                "**正向到末尾、反向到下界，两向都是「到头停手、绝不绕回」。**"
                "**（源站，纯诊断，2 轮 × 24+16 改成「走到边界再各多按 10 次」，"
                "两轮逐次读数与 `arm_stream` **完全一致**；"
                "`jimeng_probe924_both_boundaries_src.py`）\n"
                "**为什么必须同一次运行**：896（MM.1）早已测到**正向**走到末尾"
                "（`max_dom_idx_armed = 75`）**就停手、绝不绕回**；"
                "⚠️ **反向那条下界 0 从来没被测过** ⇒ 只测一向就是"
                "「正向有证据、反向靠推测」。"
                "⇒ 本批正向一路按到布上下标 75、反向一路退到布上下标 0，"
                "**各自越界之后再各按 10 次**（不然「没绕回」这个结论就没有样本）"
                "⇒ **两向互为对照**。\n"
                "**✅ 越界读数（2/2 逐条一致）**："
                "**正向**：布到 `n_nodes - 1 = 75` 之后又按 **10 次**、"
                "**一次都没布**（`after_fwd_arm_idx = []`）；"
                "**反向**：退到 **0** 之后又按 **10 次**、**一次都没布**"
                "（`after_rev_arm_idx = []`）⇒ **两向都是「到头停手、绝不绕回」**。\n"
                "**✅ 顺带把 §133 那条规则放到最大样本上再验一遍**："
                "**全程 144 次臂事件**（正向 74 + 反向 70）—— "
                "**`removed` = 上一个臂事件（不分方向）、零偏差**；"
                "`added` = 上上个只有 **1 次**偏差（就是那次**初始化**、"
                "`added` 是 76 项）；死按压 **47 次**、`removed`/`added`/`changed` "
                "**全空 47/47**；不变式「`n_wrapper_any_ti` 恒 75」**全程成立** "
                "⇒ **那条规则跨两个边界都站得住。**\n"
                "**✅ 顺带查清一条关于「反向怎么起手」的事实**："
                "**反向臂事件不是从「正向阶段最后一次按压」起手的** —— "
                "正向那 **10 次越界按压已把焦点带出画布、绕了半圈页面**；"
                "**反向第 1–9 次全是死按压**，**第 9 次**焦点才回到"
                "**正向布到的最后一个下标那个本体**上、**第 10 次**才真的布 "
                "⇒ **反向是从「正向布到的最后一个下标」那个本体起手的。**\n"
                "**✅ 本轮 76 个节点里 75 个被布过**，只有**下标 12 整轮没被布**"
                "（与 §133 一致：正反两向都跳过它）。"
                "⚠️⚠️ **不许**据此说 §121「2 个节点整轮没被布」被推翻 —— "
                "**节点总数在同 URL 逐轮会变**（74→77 都出现过）"
                "⇒ **跨 run 的下标未必可比** ⇒ 本轮只能记「**这一轮** 76 个里 "
                "75 个被布过」。"
                "⚠️⚠️⚠️ **【930 订正 —— 上面「只有 12 没布」是少报了一个，"
                "原文一个字不许删】**\n"
                "**930 走完了「正向 1 趟 + 绕回 3 圈」** ⇒ "
                "**整轮里从没被布上 `'0'` 的下标 = `[12, 68]`** "
                "（**每一圈都一样**、2/2 逐条一致）⇒ "
                "**§121 当年记的「2 个」才是完整的**，"
                "**本节那次只看到 1 个，是因为反向只退了 70 次臂事件、没走完一整圈**。"
                "详见 `source_wrap_cycle_is_constant_930`。\n"
                "⚠️ **924 第一版自己踩的坑（读数没错、门放错了）**："
                "第一版拿「**正向阶段最后一次**按压之后焦点在不在本体上」当门，"
                "而正向阶段**故意**在越界之后又按了 10 次 ⇒ 那道门**必然 FAIL**，"
                "**可它并不是「反向臂事件起手时焦点在不在本体上」**。"
                "⇒ 改成问它本来该问的那个问题（**第一个反向臂事件的 `pre` 焦点**，"
                "2/2 实测 `True`、本体下标 75）—— "
                "**不是把门删掉、也不是放宽**；"
                "**第一版的读数没错**（两轮逐次读数与第二版**完全一致**）。") ,
            "source_past_zero_boundary_focus_returns_but_no_arm_925": (
                "✅⭐ **925 消掉了 §134 留下的一处歧义**："
                "**过了下界 0 之后，焦点每 28 步真的会落回下标 0 的本体上**，"
                "**而且那个本体还带着 `tabindex=\"0\"`** —— "
                "**可应用一次都不布。**"
                "**（源站，纯诊断，2 轮；`jimeng_probe925_past_zero_boundary_src.py`）\n"
                "**§134 只在 0 之后又按了 10 次就停** ⇒ 那 10 次里"
                "「没布」有**两种**可能：(a) 焦点**不在**本体上；(b) 焦点**在**本体上、"
                "但 `cur + dir` **越界** ⇒ **分不出来**。925 把尾巴拉长到 **80 次**"
                "（**盖过 §132 那个 27 步整页闭环**）⇒ **歧义被消掉。**\n"
                "**✅ 消歧义的那个读数**：尾巴里焦点**每 28 步**落回一次"
                "**下标 0 的本体**（`aria = 视频 node: 视频 1`、`ti_attr = '0'`）"
                "⇒ **焦点确实在本体上、那个本体确实是被布着的那个**，"
                "**而应用仍然不布**（`moved = False`、"
                "`removed`/`added`/`changed` **全空 80/80**）\n"
                "⇒ ⭐ **所以「到边界停手」不是「因为焦点不在本体上」"
                "，而是「焦点在本体上、但 `cur + dir` 越界 ⇒ 不布」。**\n"
                "⚠️⚠️⚠️ **【928 订正 —— 上面那个「不绕回」的一半是回归，"
                "原文一个字不许删】**\n"
                "⚠️ **反向那半个结论仍然成立**（退到 0 之后 10 次、"
                "以及 §135 的 80 次尾巴都实测零臂事件）。\n"
                "⚠️ **但「正向到末尾也不绕回」那半个是错的** —— "
                "§134 越界之后**只按了 `10` 次**，"
                "**而绕回要等焦点走完约 28 步的整页循环、回到画布根才发生** "
                "（§134 自己也实测过那个循环是 28 步）"
                "⇒ **10 次预算根本不够** ⇒ **这正是 899 踩过的同一个「取样假象」**。\n"
                "⇒ **正确规则早已由 §130/908 判死**（4/4，两条并存）："
                "· 指针在末尾 ＋ **按前焦点是节点本体** ＋ `Tab` ⇒ **撒手**"
                "（899 对、§134 的「按前焦点在本体」那一格也对）\n"
                "· 指针在末尾 ＋ **按前焦点是画布根** ＋ `Tab` ⇒ **布 `'0'`、绕回**\n"
                "⇒ **§134 把这两条并存的两分支一刀切成「绝不绕回」，是回归。**"
                "**✅ 顺带两条**：\n"
                "**① 状态完全冻结**：80 次按压 `n_wrapper_any_ti` **全程恒为 75** "
                "⇒ 应用**一次都没碰 `tabindex` 属性**。\n"
                "**② 闭环周期是 28**（`Canvas` 出现在第 1/29/57 次，**2/2 一致**）"
                "⇒ 比 §132 那个周期 **27** 恰好多 **1** 个停靠点 —— "
                "**就是「当前被布的那个本体」** ⇒ "
                "**闭环长度 = 中性态时的 27 + 当前被布的那个本体 1**（自洽）。\n"
                "⚠️⚠️ **925 原本要问的那个问题，本批仍然没有被问到**："
                "「**滚动窗口跨整页循环还成立吗**」—— 因为整页循环里"
                "**应用一次都没布**、压根**没有新的臂事件** ⇒ "
                "⇒ **不许**把它记成「窗口跨循环成立」；"
                "**它仍然是一个未回答的问题。**\n"
                "⚠️ **两轮不是逐条一致，如实记账**："
                "**臂事件读数 144 次两轮完全一致**、`arm_stream` **完全一致**；"
                "但**死按压总数差 1**（117 vs 118；反向退到 0 的次数 **88 vs 89**）"
                "⇒ 焦点在**非本体元素**上多走/少走了一步。"
                "⇒ **臂事件机制 2/2 可复现；不稳定性只出现在「与机制无关」的那部分。**"
                "⚠️ 这也**印证**了一条老纪律：**`moved` 才是必需字段** —— "
                "死按压路径会抖，**拿死按压的次数当判据就会假绿/假红**。") ,
            "source_window_survives_boundary_freeze_926": (
                "✅⭐⭐ **926 把 §135 那个「未回答的问题」真问掉了："
                "越界冻结不结束窗口。**"
                "**（源站，纯诊断，2 轮；`jimeng_probe926_window_survives_freeze_src.py`）\n"
                "**做法**：正向走到末尾 → 反向退到下界 `0` → "
                "⭐ **冻结**：继续按 `30` 次 `Shift+Tab`"
                "（**必须 > §135 实测的 28 步闭环**，静态 assert 钉住）→ "
                "⭐⭐ **翻回正向再布一次**。\n"
                "**✅ 判别结果（2/2 逐条一致）**：冻结阶段 **零臂事件**、"
                "`n_wrapper_any_ti` **全程 75**、`removed`/`added`/`changed` "
                "**全空 30/30**；而**冻结之后的第一次正向臂事件** —— "
                "**`removed = [0]`** ⇒ **`0` 正是冻结前最后一个臂事件那个下标** "
                "⇒ **窗口确实跨过了那 30 次整页循环** ⇒ "
                "**「越界 ⇒ 不布」只是不更新窗口、不是把窗口清掉。**\n"
                "**✅ 顺带**：**全程 147 次臂事件**，"
                "**`removed` = 上一个臂事件（不分方向）、零偏差** "
                "⇒ 那条规则在「**两个边界 + 一次整页循环冻结**」之后**仍然成立**。\n"
                "⚠️⭐ **但撞出一条反例，必须如实记账、并且要收窄 §131**："
                "**死按压里出现了 `delta` 不空的一次** —— "
                "**冻结之后第 2 次正向按压**（`'0'` **停在 `[0]` 没动**、"
                "`moved = False`）却做了 **`added = [1]`**"
                "（给下标 `1` **写回**了 `tabindex`）"
                "⇒ **2/2 两次运行都恰好是这同一次**（死按压 1/73 与 1/75）。"
                "⇒ ⚠️ **§131 那条「死按压 ⇒ 应用完全没碰 `tabindex` 属性」"
                "必须收窄成「绝大多数」** —— 它在 921/922/924"
                "（**8/8、4/4、47/47**）都成立，但 **926 实测到 1 次例外**。"
                "⚠️ **成因未查明**（**1 次异常读数不足以立机制**）。"
                "⭐ 而**正是这个 `added = [1]` 解释了**下一个臂事件的 `changed` "
                "为什么是「`-1` → `'0'`」而不是「`null` → `'0'`」。\n"
                "⚠️ **925→926 的一条自我纠错（诚实留痕）**：926 **事先写下**的预期是"
                "「冻结后第一次正向臂事件 `removed = [0]`、**`added = [1]`、"
                "`changed = []`**」⇒ **判别用的那一格预测对了**，"
                "**机制细节那一格预测错了**（实测 `added = []`、"
                "`changed = [[1, '-1', '0']]`）"
                "⇒ **错因正是上面那条「写回早了一步」的现象。**\n"
                "⚠️⚠️ **【927 收窄 —— 上面「早了一步」这个说法要改，原文一个字不许删】** "
                "927 用**分档冻结**复现后查明：那**不是**多了一个「提前的额外动作」—— "
                "**是同一个「写回」动作可以落在一次「不布」的按压上**"
                "（落点取决于**第一次正向按压时焦点在不在画布内**）。"
                "**详见 `source_early_writeback_not_per_loop_927`。**\n"
                "⇒ 教训：**「先写下预期」这个做法有效**"
                "（它当场把我没料到的那条新现象顶了出来），"
                "**但预测本身也会错** ⇒ **预测只配当假设、不配当证据**；"
                "**判据必须钉在读数上，不能钉在预测上。**") ,
            "source_early_writeback_not_per_loop_927": (
                "✅⭐ **927 用「分档冻结」把 §136 那条异常钉住了："
                "它**不是每个整页循环一次**。**"
                "**（源站，纯诊断，2 轮 × 4 档，两轮逐档读数与 `arm_stream` "
                "**完全一致**；`jimeng_probe927_early_writeback_repro_src.py`）\n"
                "**要问的**：那条「死按压却做了 `added = [1]`」"
                "是 ① **只发生一次**、② **每个整页循环一次**、"
                "③ **与「焦点什么时候回到画布内」有关**？"
                "⇒ **专为证伪它设计的最小复现**：把冻结长度分档成 "
                "**`L ∈ {1, 5, 29, 57}`**（`1`/`5` **不足一个 28 步循环**、"
                "`29`/`57` 是**一到两个**）⇒ **静态 assert 钉住「必须同时有不足一个"
                "循环和超过一个循环的档」**（不然 ① 和 ② **分不开**）。\n"
                "**✅ 候选②被排除（2/2）**：冻结段的**死按压**里 "
                "`delta` **不空**的次数 —— `L=1`：**1 次死按压、0 次不空**；"
                "`L=5`：**4 次、0 次**；`L=29`：**28 次、0 次**；"
                "`L=57`：**56 次、0 次** "
                "⇒ **跨越 1–2 个整页循环、84 次死按压，`delta` 一次都没不空** "
                "⇒ **不是「每个循环一次」。**\n"
                "**✅ 那次写回「恰好 1 次」，且落点可钉**："
                "**`L=1`** 落在翻回正向后的**第 1 次**（`moved = False`、"
                "`pre` **焦点不在**本体）、臂事件在第 2 次；"
                "**`L=5`** 落在**第 4 次**（同样不布、`pre` 不在本体）、"
                "臂事件在第 5 次；**`L=29` / `L=57`** 则**落在第 1 次、"
                "而且就是臂事件那一次**（`pre` **焦点在**本体）\n"
                "⇒ ⭐ **落点取决于「第一次正向按压时焦点在不在画布内」** "
                "⇒ ⇒ **§136 那个「写回早了一步」的说法要收窄**："
                "**不是多了一个提前的额外动作，而是同一个「写回」动作"
                "可以落在一次「不布」的按压上。**\n"
                "**✅ 顺带独立复现 §926（4/4）**：四档「冻结之后的第一次臂事件」的 "
                "`removed` **全部是 `[0]`** ⇒ 窗口在 **0–2 个整页循环**之后"
                "**仍然指着上一个臂事件**。\n"
                "⚠️⚠️ **927 第一版的分档设计有 flaw，如实记账**："
                "**`L ≥ 5` 的那几档「冻结」根本不是冻结** —— "
                "上一档结束时 `'0'` 停在**下标 1**，下一档的第一次 `Shift+Tab` "
                "于是**合法地退到 0、真的布了一次**"
                "（`removed = [1]`、`added = [0]`）"
                "⇒ 那些档的「冻结」只包含**其后**的那些死按压。"
                "⇒ **门 `frz_clean_ok` 2/2 正确地把它判成 FAIL** "
                "⇒ **又一次避免了把不同起点的读数当成可比的分档结果**（"
                "§122、§925 之后第三次）。\n"
                "⇒ ⚠️ **不许**把四档当成「同一实验的不同档」"
                "（`L ≥ 5` 的起点与 `L = 1` 不同）；"
                "✅ **但上面那三条结论仍然成立** —— 它们只依赖"
                "**「冻结段的死按压」**和**「每档都恰好 1 次写回」**这两件事，"
                "**而每档都恰好各有一次「回到画布内」事件** ⇒ **跨档可比。**\n"
                "⚠️ **成因仍未查明**：为什么焦点回来得早/晚，"
                "**本批没有回答**（不预设、不编机制）。") ,
            "source_replica_same_ruler_928": (
                "✅ **928 第一次用**同一把尺子**（919–927 那套 census + 逐次 delta，"
                "**口径逐字未改**）量了**复刻侧**。"
                "**（复刻侧，纯读，2 轮逐次完全一致；"
                "`jimeng_probe928_replica_same_ruler.py`）\n"
                "**为什么换到复刻侧**：919–927 **九个 batch 全是源站纯诊断**，"
                "而复刻实现自 909 之后**一个字没动过** "
                "⇒ 「那些新查到的事实复刻对不对得上」**从没被问过**。\n"
                "**✅ 那个实现差异，实测确认存在**："
                "**「没有 `tabindex` 属性」的本体个数** —— "
                "**源站 §131 实测 = 恒 1**（任何时刻恰好一个）；"
                "**复刻 = 恒 0**（`armAll` 天然把每个节点都写了）"
                "⇒ 相应地 **`n_wrapper_any_ti`**：源站 = 节点总数 **− 1**、"
                "复刻 = **等于**节点总数。"
                "**`removed` 累计**：源站每次臂事件至少 1 条、复刻 **0 条**。"
                "⭐ 而 **`n_wrapper_idl_focusable` 两侧都是 1**（只有被布那个 "
                "`'0'` 的 `IDL tabIndex ≥ 0`）⇒ **顺序焦点位个数是对齐的**。\n"
                "⚠️ **928 自己的一处硬限制（如实记账）**：**复刻 demo 画布只有 "
                "2 个节点**（源站同 URL 是 76）⇒ **边界那几读数偏弱、"
                "不足以判定「复刻的边界行为对不对」** ⇒ 本批**只**用复刻侧回答了"
                "「`missing_ti` 差 0 还是差 1」和「三动作形态」这两个问题。\n"
                "⚠️⚠️ **但 928 撞出一件必须马上处理的事：它和 §134 的结论矛盾。**"
                "复刻侧正向臂事件实测是 **`[0, 1, 0, 1]`** —— **它绕回了 `0`**；"
                "焦点轨迹显示：布到下标 1 之后**焦点走出了画布、绕了整页**、"
                "**回到画布根**，下一按 `Tab` 才布 `0`。"
                "⇒ 而 §134 记的是「**到末尾停手、绝不绕回**」—— "
                "⚠️⚠️ **但 §134 越界之后只按了 `10` 次**，"
                "**而绕回要等焦点走完约 28 步的整页循环才发生** "
                "⇒ **§134 那条「绝不绕回」是在预算不够的情况下读到的** "
                "⇒ **这正是 899 踩过的同一个「取样假象」**。"
                "⇒ **不许**把 §134 那条当已验证；929 去判死。\n"
                "⚠️ **源站侧本来就有一对互相矛盾的记录**，本批**没有**解决、"
                "**也不假装解决**：§124/896 记「到末尾停手、**绝不绕回**」"
                "（`revisited = {}`），而 §130/908 记「**源站确实会布 `'0'`**、"
                "这一按就是绕回」"
                "⇒ ⚠️ **两条都是源站实测、方向相反** ⇒ **成因未查明**，"
                "**不许**在没有更长预算的读数之前采信任何一条。"
                "⚠️⚠️ **【929 已判死，见下一条 —— 结论是 §908 对】**") ,
            "source_wrap_after_end_confirmed_929": (
                "✅⭐⭐ **929 用足够长的尾巴把这一对矛盾判死了："
                "§908 对、§134（我自己在 924 记的）「绝不绕回」是错的。**"
                "**（源站，纯诊断，2 轮 × 越界后 90 次按压，"
                "两轮尾巴**逐次完全一致**；"
                "`jimeng_probe929_long_tail_wrap_or_not_src.py`）\n"
                "**要判死的那一对**：§124/896 记「到末尾**绝不绕回**」"
                "（`revisited = {}`），§130/908 记「**源站确实会布 `'0'`**、"
                "**只在「按前焦点是画布根」的那一按**」（4/4）。\n"
                "**本批就是那一跑**：正向走到**最后一个下标**之后，"
                "⭐ **继续按 `90` 次**（**≥ 3 个整页循环**；"
                "**静态 assert 钉住 `TAIL >= 3 × 28`**，"
                "**不然就又是一次「预算不够就下结论」的取样假象**）。\n"
                "**✅ 判别结果（2/2 逐条一致）**："
                "**到末尾 = 第 83 次**（布在下标 `75`）⇒ "
                "越界之后**第 84–101 次共 18 次全是死按压**（`'0'` 停在 `[75]`），"
                "焦点一路走**页面前半圈**"
                "（`音频 node: 音频 68` → `文本` → `选择工具` → `小地图` → "
                "`显示连线` → `Zoom options` → `与 AI 对话` → `''` → `返回首页` → "
                "`Canvas title` → `项目` → `Canvas node summary` → `搜索` → "
                "`生成历史` → `分享` → `更多` → `Credits` → `用户菜单`）\n"
                "⇒ ⭐⭐ **第 102 次：按前焦点 = `Canvas`（画布根）⇒ 布 `0`、"
                "**绕回**（`pre_on_canvas_root = True`）** —— "
                "**§908 那条触发条件 2/2 复现**；之后一路正常布 "
                "`0,1,2,…,63`（**跳过 12**，与 §133 一致）；"
                "不变式「`n_wrapper_any_ti` = 节点总数 − 1」全程成立（尾巴最小 75）。\n"
                "⚠️⭐ **顺带把 §908 当年那个「约 19 次」量准、并钉死了「差一按」**："
                "**到末尾 83、绕回 102 ⇒ 恰好 19 次**；"
                "而 **896 的预算是 `节点数 + 25 = 101` 次** "
                "⇒ **`revisited = {}` 真的只差 1 按** ⇒ "
                "**它不是机制、是一按之差。**\n"
                "⇒ **由此得到一条硬纪律（本批最值钱的一条）**："
                "**「到边界之后的行为」这类问题，预算必须 > 「从边界走回触发点」"
                "所需的那一圈** —— **而那一圈的长度本身就是要先测出来的东西**，"
                "**不许拿「按了 N 次没看到」当机制**。\n"
                "⚠️ **929 第一版自己踩的坑（门禁用错了解释器）**："
                "把一个**跨行的 f-string 表达式**写进了打印语句 —— "
                "**f-string 表达式里不许换行**（那是 **PEP 701 / Python 3.12** "
                "才放宽的）⇒ **`/opt/miniconda3` 的 3.12 语法门全绿放行**，"
                "**而 harness 跑的是 3.11** ⇒ **一跑就 SyntaxError、整轮读数全丢**。"
                "⇒ ✅ **已把第二道语法门加进 `jimeng_probe_js_syntax_check.py`**："
                "**用 harness 那个解释器把每个探针 `parse` 一遍**"
                "（122 个探针全过）⇒ **教训：语法门必须用「真跑那个」解释器** —— "
                "**门跑在另一个版本上，它就可能放行真跑时崩的代码。**") ,
            "source_wrap_cycle_is_constant_930": (
                "✅⭐⭐⭐ **930 把 §139 那条硬纪律量化了，而且挖出一条很重的东西：**"
                "\n"
                "**（源站，纯诊断，2 轮 × 越界后 228 次按压（= 3 个节点数），"
                "两轮 `arms` 逐条完全一致；"
                "`jimeng_probe930_second_wrap_src.py`）\n"
                "**① 「那一圈」是常数**：绕回发生在按压 **102 / 203 / 304**，"
                "**两次绕回之间的按压间隔 = 101、101**。"
                "**② 每一圈逐条完全相同**（2 圈各：按压 **101**、臂事件 **73**、"
                "死按压 **28**、下标 `1…75`）⇒ **绕回不是一次性的，"
                "每一圈都完整重走。**\n"
                "**③ §908 的触发条件反复成立**：**三次绕回的按前焦点全在画布根**；"
                "而**每一次「末尾 → 画布根」都恰好 19 次**（三次全 19）"
                "⇒ **§908 当年那个「约 19」精确成立。**\n"
                "**④ ⭐⭐⭐ 最重的一条：整轮（正向 1 趟 + 绕回 3 圈）里"
                "从没被布上 `'0'` 的下标 = `[12, 68]`** —— "
                "**正是 §121 当年记的那两个**（2/2 逐条一致、**每一圈都一样**）"
                "⇒ **那不是「随机没赶上」，而是一个稳定可重复的跳过。**\n"
                "⚠️⇒ **由此订正 §134/924 那次「76 个里 75 个被布过、只有 12 没布」** —— "
                "**那是走查不够深造成的**（反向只退了 70 次臂事件、**没走完一整圈**）"
                "⇒ **§121 的「2 个」才是完整的**，§924 那次**少报了一个**。"
                "（⚠️ §122 已钉的「成因原理上不可从 DOM 查明、复刻只能按纯 DOM 序、"
                "**不许编 DOM 层判据去对齐**」**继续有效** —— 本条**只**把它"
                "**从「某一趟没赶上」升级成「每一趟都稳定跳过」**。）\n"
                "**⑤ 自洽核对**：周期 **101 = 73 臂事件 + 28 死按压**，"
                "而 `1…75` 去掉 `{12, 68}` 恰好 **73**；"
                "那 **28 次死按压 = §132 那个 27 步整页闭环 + 1** ⇒ **完全对上。**\n"
                "⚠️⚠️⚠️ **【931 订正 —— 上面那个「28 死按压」是**我按模式填进去的**、"
                "不是数出来的；「完全对上」因此**不成立**。原文一个字不许删。】**\n"
                "**931 把 930 自己的落盘读数重新枚举了一遍**（`/tmp/b930-src-second-wrap.json`，"
                "2 轮 × 四个窗口口径 `(w1,w2] / (w1,w2) / [w1,w2) / [w1,w2]`，"
                "绕回在 k=102/203）：\n"
                "**① 死按压数在四个口径下全是 `27`、两轮一致** ⇒ **28 是错的**；\n"
                "**② 臂事件数随口径变（73 / 74 / 74 / 75），但死按压恒为 27** "
                "⇒ 错的是死按压那一项，不是口径问题；\n"
                "**③ 正确分解：101 = 74 臂事件（`{0} ∪ (1…75 去 {12,68})`）+ 27 死按压**。\n"
                "⭐ **但订正之后自洽反而更紧**：**那个 27 正是 §132 那个整页闭环的 27**"
                " ⇒ **正向那一圈 = 73 个节点推进 + 1 次绕回布 `0` + §132 那个 27 步整页闭环**；"
                "而**反向那一圈 = 27 步整页闭环 + 1 个被布本体 = 28**（§135 当年就是这么说的）"
                "⇒ **两侧用的是同一个 27。**\n"
                "⚠️ **为什么会错**：那个 `28` 恰好等于 §135 记的**反向**周期 "
                "⇒ **这是模式匹配填出来的数**\n"
                "⇒ **又一次执行「预测只配当假设、不配当证据」那条（926）**："
                "**「自洽核对」这种话，只有把两边的数"
                "各自数出来才成立；凭印象凑一个能对上的数，等于没核对。**\n"
                "⚠️ **代价也要记账**：QQQ.3 曾把这个「自洽核对」钉成判据 ⇒ "
                "**判据跟着一起收窄**（原文留在判据文本里、收窄批注加在旁边）。\n"
                "⚠️⭐ **把 §139 的硬纪律量化成一句可执行的**："
                "**「到边界之后」的预算必须 > 一个完整周期（本画布 = 101 次按压）** "
                "⇒ ⇒ **§896 那个 `节点数 + 25 = 101` 次的预算，"
                "在结构上就永远抓不到绕回** —— "
                "**它不是「差一按的运气」，而是「预算恰好等于周期」。**\n"
                "⚠️ **930 的方法论收获**：**「那一圈」的长度必须先测出来、"
                "再拿它当预算的下限** —— 而 930 正是**用「尾巴 = 3 个节点数」"
                "这个关系式**（**不是钉一个常量**）来保证预算够的。"
                "⇒ 这条关系式已**静态 assert 钉住**。"
                "⚠️ **不许**把「尾巴长度」钉成某个实测常量 —— "
                "**节点总数是易变量**（同 URL 逐轮 74→77 都出现过）⇒ "
                "**只能用关系式**（「几个节点数」），**不能钉一个数字**。") ,
            "source_reverse_lap_cycle_is_constant_931": (
                "✅⭐⭐⭐ **931 把 §140 六(1) 那个问题问掉了："
                "反向那一侧**也有**常数周期 —— 恰好 28。**\n"
                "**（源站，纯诊断，2 轮；尾巴**自适应按到第 4 次落回**为止 = 112 次，"
                "`design_ok=True`、`cap_hit=False`；"
                "`jimeng_probe931_reverse_lap_cycle_src.py`）\n"
                "**① 落回被布本体在按压 **28 / 56 / 84 / 112**，"
                "**间隔 = `[28, 28, 28]`，2/2 逐条一致**；"
                "**画布根停靠 = `[1, 29, 57, 85]`、间隔同为 `[28, 28, 28]`** "
                "⇒ **两者逐个恰好错开 27**（画布根是每圈第 1 站、被布本体是最后一站）。\n"
                "**② 每一圈逐条完全相同** —— 这是 931 新加的读数："
                "每圈 28 个停靠点，**以「焦点在可聚焦元素序列里的序号」(`fpos`) 逐条比**，"
                "**4 圈序列全等、2/2 一致**。\n"
                "**③ 应用在尾巴里零参与**（**再次复现 §135**）："
                "**尾巴 112 次按压零臂事件**、`removed/added/changed` **全空 112/112**、"
                "`any_ti` **75 → 75 全程冻结**、"
                "且 **`n_focusable` 全程恒为 276**（可聚焦集合一次都没变）。\n"
                "**④ 单圈 28 站已逐条列全**（`fpos` 11→0 一路降到 265 再回到 12，"
                "其中**第 12 站是 `BODY`、不在可聚焦集合里（`fpos = -1`）** —— "
                "与 §929 正向走线里那个空 `aria` 的那一站是同一个；"
                "**第 18 站 `文本` 这个 BUTTON 自带 `tabindex='0'`**）。\n"
                "⭐ **§132 留下的一处「同名成对」**：931 顺带解开了 —— "
                "§132 记过闭环里有 `添加素材到时间线`/`静音`/`全屏编辑`/`导出时间线` "
                "**各出现 2 次**、当时分不清是同一元素的两次出现还是两个元素；"
                "**931 用 `fpos` 分开了：89/88/87/86 与 23/22/21/20 "
                "⇒ 是两个不同节点各自的 4 个控件**，**不是同一个元素出现两次。**\n"
                "⭐⭐ **931 顺带把 §135 那处「两轮不是逐条一致」定位了**（"
                "**这是 931 那个对照臂的产出、不需要额外的臂**）："
                "**接近段在动、尾巴不动** —— 反向退到 `0` 的次数 **88 → 89（变了）**，"
                "而**尾巴间隔两轮完全相同 `[28, 28, 28]`**、画布根停靠与落回位置也完全相同\n"
                "⇒ ⇒ **§925 记的那处抖动在「接近段」、不在尾巴** "
                "⇒ **它不影响任何机制读数**（**又一次印证 `moved` 才是必需字段**）。\n"
                "⚠️⚠️⚠️ **931 探针自己踩的坑（**分析层**的切片，**不是采集层**）："
                "逐圈比较那段**首尾用了不一致的边界** —— "
                "第 0 圈从「尾巴第 1 次按压」起、第 1..3 圈从「上一次的落回本体」起\n"
                "⇒ 打出 `lap_lens = [28, 29, 29, 29]`、`laps_identical = False`\n"
                "⚠️ **那不是源站事实、是我自己的切片把规律读反**："
                "改用**统一边界**重算同一份落盘读数 —— "
                "**以画布根停靠点为每圈起点**\n"
                "⇒ **各圈长度全为 28、`fpos` 序列逐条全等**。\n"
                "⇒ **教训：连「以什么为界切分一整圈」都得先钉死，"
                "否则「每圈相同」这个判断会被切片约定污染** —— "
                "这是「切片会把规律读反」那条纪律的**第四次执行**，"
                "但这次犯在**分析层**（§131 那次犯在采集层）。"
                "**好在这批的原始读数（`fpos_seq` + `root_at`）全在落盘里 "
                "⇒ 离线重算即可、不必重跑浏览器。**\n"
                "**⑤ 两侧的对照（观测，**机制不宣称**）**："
                "把 930 的正向那一圈那 **27** 次死按压**倒着读**，与 931 反向那一圈的"
                "**中间 17 站**（`用户菜单`→…→`与 AI 对话`→…→`选择工具`→`文本`）"
                "**是同一批停靠点、同一相对顺序、方向相反**；"
                "**而两端那 9 站身份不同**（正向那 9 站里含两个别的节点本体，"
                "反向那 9 站是当前节点自己的 4+4 个内层控件）\n"
                "⇒ ⇒ **对称的是「常数 + 每圈可重复」这个性质**"
                "（正向 **101**、反向 **28**，都是常数、都逐圈全等），"
                "**不是周期长度、也不是每一站的身份**。") ,
            "source_reverse_lap_cycle_is_constant_931": (
                "✅⭐⭐⭐ **931 实测：反向那一侧**也有**常数周期 —— 恰好 28**"
                "（`source_reverse_lap_cycle_is_constant_931` 的正文）\n"
                "⚠️⚠️⚠️ **【932 收窄 —— 上面「间隔 `[28, 28, 28]`」与「每一圈逐条完全相同」"
                "两条都只覆盖了 8 圈里的 8 圈、而其中有 1 圈不是 28；"
                "原文保留在这里当历史记录、不许删。详见 `source_27_cycle_is_one_loop_932`。】**\n"
                "**932 的读数**：8 圈（2 轮 × 4 圈）里 **7 圈是 28、1 圈是 27**"
                "（rep2 的第 3 圈），且那 1 圈**缺的恰好是 `document.body` 那一站**、"
                "其余 27 站**逐条全等**\n"
                "⇒ **「28」不是常数**；真正的结构是"
                "**「27 步整页闭环 + 1 个被布本体」，而 27 步闭环本身偶发少停一站**\n"
                "⇒ 所以「间隔恒定」与「每圈逐条全等」这两句都要收窄成"
                "**「绝大多数（7/8）」** —— **又一次执行「一次成功不叫可靠」**："
                "931 那两轮恰好各 4/4 相同，**再多测一轮就撞出反例了。**") ,
            "source_27_cycle_is_one_loop_932": (
                "✅⭐⭐⭐ **932 把「那 27 步整页闭环」钉成**同一个**闭环，"
                "并顺手收窄了 931 的两条「恒定」**\n"
                "**（源站，纯诊断，2 轮；⭐ **同一次运行里跑两臂、共用同一把尺子**；"
                "`design_ok=True`、2/2；`jimeng_probe932_same_27_cycle_src.py`）\n"
                "**① ⭐⭐ 换了与状态无关的尺子**：`fpos`（焦点在「可聚焦序列」里的序号）"
                "的分母是**当前可聚焦集合的大小** ⇒ 中性态（`any_ti = 0`）与"
                "越界尾巴（`any_ti = 75`）**同一个元素的 `fpos` 数值不同** "
                "⇒ **拿它跨状态对齐是错的。** 932 新加两个与状态无关的身份："
                "`dom_sig`（纯 `tag:nth-of-type` 结构路径，**一个字都不掺 aria/class/"
                "tabindex**，静态 assert 钉住）与 `owner_node_idx`"
                "（最近那个 `.react-flow__node` 祖先的 DOM 下标）。\n"
                "**② ✅ 臂 A 独立复现 §132 的 27**（中性态、点空白后 `any_ti ≡ 0`、"
                "60 次 `Shift+Tab`、`moved` 全 False、`any_ti` 全程恒 0）："
                "画布根停靠在第 **27 / 54** 次 ⇒ 间隔 **27**；"
                "**按周期 27 切出的两段完整窗口 `dom_sig` 逐条 27/27 全等**（2/2）。\n"
                "⚠️⚠️ **【933 收窄 —— 上面那个「间隔 **27**」是**两轮各 2 个圈**的样本、"
                "**臂 A 同样会有 26 长的圈**（实测 1/16）；原文保留、不许删】**\n"
                "⇒ **「臂 A 的圈恒为 27」与「臂 B 的圈恒为 28」一样，都不是常数** —— "
                "**两边的短圈都恰好是「同臂参照整圈删掉 `BODY` 那一站」**。"
                "详见 `source_body_stop_absent_933`。\n"
                "**③ ⭐⭐⭐ 「那 27 步整页闭环」确实是同一个**："
                "**臂 B 那一圈 = 臂 A 那个 27 步闭环 `dom_sig` 逐条全等、"
                "同一位置（最佳 offset = 0、匹配 27/27）＋ 末尾多出被布本体那一站**"
                "（`owner_node_idx = 0`、`aria = 视频 node: 视频 1`），2/2 一致\n"
                "⇒ ⇒ **§135 当年那句「闭环长度 = 中性态时的 27 + 当前被布的那个本体 1」"
                "现在有了 `dom_sig` 口径的逐条证据**（当年只有个数、没有逐条对齐）。\n"
                "⚠️⚠️ **④ 收窄 931：「28」不是常数** —— 8 圈（2 轮 × 4 圈）里"
                "**7 圈是 28、1 圈是 27**（rep2 的第 3 圈）；"
                "**那一圈缺的恰好是 `document.body` 那一站**（正常圈的第 12 位）、"
                "**其余 27 站逐条全等**、owner 取值集合也不变（`{-1, 0, 2, 12, 22}`）\n"
                "⇒ ⇒ **真正的结构是「27 步整页闭环 + 1 个被布本体」，"
                "而那个 27 步闭环本身偶发少停一站** ⇒ "
                "**「间隔恒定」与「每圈逐条全等」都收窄成「绝大多数（7/8）」**\n"
                "⚠️ **机制只到这一步为止**：`document.body` 那一站为什么偶发不出现，"
                "**成因未查明、标「未验证」**（不许编）。\n"
                "**⑤ ⭐ 答掉 §141 九(1)**：那 9 个「节点邻近槽位」的 `owner` 全表 = "
                "**`22` 贡献 4 个、`12` 只贡献 `替换媒体` 那 1 个、`2` 贡献 4 个**；"
                "**下标 `68` 在两臂四圈里一次都没出现**（owners 全集 = `{0, 2, 12, 22}`）\n"
                "⇒ **在「被布本体 = 0」这个状态下，中性态与越界尾巴的 9 站完全相同** "
                "⇒ **越界、走过一圈、这些状态切换都不改它**\n"
                "⚠️⚠️ **但不许据此说「节点 12 特殊」**（`12` 恰好是 §121/§930 记的"
                "那两个「整轮从没被布上 `'0'`」之一）—— NN.1 已查清 12/68 在 DOM 层"
                "毫无特殊之处（属性集相同、离群 0 个、可聚焦子孙数相同）"
                "⇒ **最简读法是位置性的**（闭环入口恰好挨着哪几个节点），"
                "**不是内在属性** ⇒ **§122 继续有效：不许编 DOM 层判据去对齐。**\n"
                "⚠️⚠️⚠️ **932 自己踩的第二个坑（切片边界的第三次）**：臂 A 那一段"
                "**按「画布根」切圈**，而 60 次按压切出的是 **[27, 7]** —— "
                "**拿一个整圈去和一个 7 次的残尾比**，于是打出「圈间一致 = False」\n"
                "⚠️ **那不是读数**、是**切法**造成的：改按**周期 27** 切两段窗口 "
                "⇒ **`dom_sig` 逐条 27/27 全等**\n"
                "⇒ **「切片会把规律读反」第四次执行**（§131 采集层、931 分析层、"
                "932 这里）\n"
                "⇒ **教训升级：切分之前必须先钉死「以什么为界」，而且要比的那两个集合"
                "必须同质** —— **一个整圈和一个残尾不是同类东西。**") ,
            "source_body_stop_absent_933": (
                "✅⭐⭐ **933 量到了 `document.body` 那一站的缺席率，并一次排除了三个假设**\n"
                "**（源站，纯诊断，2 轮 × **两臂各 8 个完整圈** = 32 圈；"
                "`design_ok=True`、2/2；`jimeng_probe933_body_stop_rate_src.py`）\n"
                "**① 切分口径**：⚠️ **周期本身是读数 ⇒ 不许拿「27」去切** "
                "（那会把「这一圈是 26 还是 27」变成假设）"
                "⇒ **按「画布根停靠点」切**（932 已实测**缺 `BODY` 那一圈画布根照样命中**）"
                "⇒ 并用 `MIN_CYCLE_LEN` 剔掉残尾（**整圈与残尾不同质，932 的教训**）。\n"
                "**② 读数**：**32 圈里 3 圈缺 `document.body`（9.4%）** —— "
                "**臂 A（中性态）1/16、臂 B（越界尾巴）2/16**；"
                "落点分别是**第 4 圈、第 2 圈、第 7 圈**\n"
                "**③ ⭐⭐ 每一处短圈都精确等于「同臂参照整圈删掉 `BODY` 那一站」"
                "（3/3 逐条全等）** ⇒ **唯一的差异就是那一站**，"
                "没有别的站跟着动（`dom_sig` 口径）\n"
                "⚠️ **这个比较不是「在外面另算一遍」**：它是探针里**自己的**"
                "`short_cycle_vs_ref()` 做的，**参照圈必须带 `BODY` 且长度恰好多 1**，"
                "找不到合格参照就记 `None`、**不许拿长度不对的圈硬比** ⇒ "
                "**判据钉在代码里、可复现**。\n"
                "**④ ⭐⭐⭐ 一次排除三个假设**：\n"
                "**① 「越界状态才让它消失」——排除**："
                "**臂 A（中性态、`any_ti ≡ 0`）也缺了 1 次** "
                "（932 只在臂 B 看到，是因为它**臂 A 只测了 2 个圈**）\n"
                "**② 「可聚焦集合大小变了」——排除**："
                "`n_focusable` **全程恒定**（臂 A **201**、臂 B **276**，两轮 32 圈无一次变化）\n"
                "**③ 「短圈是少了被布本体」——排除**："
                "臂 B 每一圈**都恰好停被布本体 1 次（16/16）**\n"
                "⇒ 剩下唯一与之相关的事实是：**那一站是 `document.body` 本身**、"
                "而它**出现与否与可聚焦集合、与越界状态、与被布本体都无关**。\n"
                "⚠️⚠️⚠️ **但成因仍然未查明、标「未验证」**：**3/32 的样本不足以判定**"
                "它是「随机」「固定周期」还是「与某个未观测变量相关」—— "
                "**落点分散在第 2/4/7 圈、不支持「固定位置」，但也证不了「随机」**\n"
                "⇒ **不许**把「分散」读成「随机」（这是本轮最容易犯的推论跳跃）\n"
                "**⑤ 顺带记一条自检**：933 第一版的**预算算错了** —— "
                "按「保守下界 20」算 cap = 200，而 8 圈 × 27 = **216** ⇒ **必然撞 cap**\n"
                "⚠️ **这条要留痕**：它是「预算不足 ⇒ 读数作废」这条纪律的**第二次**现场踩坑"
                "（第一次是 §929 的 §896 差一按）\n"
                "⇒ **这正是 §139/§140 那条纪律的同一个坑（「预算必须 > 圈数 × 真实单圈长度」"
                "、而那个长度要先测出来）** ⇒ 已改成按 **30** 算（cap = 280），"
                "并加了静态 assert 钉住「预算系数必须高于实测单圈长度」。") ,
            "source_body_own_attrs_falsified_934": (
                "✅⭐⭐⭐ **934 把假设 H 整个证伪了，而且撞出「切片会把规律读反」"
                "那条纪律的**第四种形式****\n"
                "**（源站，纯诊断，2 轮 × **两臂各 15 圈 = 60 圈**；"
                "`design_ok=True`、2/2；`jimeng_probe934_body_own_attrs_src.py`）\n"
                "**① 934 为什么不去堆圈数** —— 堆更多圈**只能把频率估得更准、"
                "判不了性质**（§143 五已钉：落点分散**既不支持「固定位置」、"
                "也证不了「随机」**）⇒ 换成一个**具体、可测、可证伪**的假设：\n"
                "**H：「那一站的出没，取决于 `document.body` 自己那一下当时"
                "是否可被顺序聚焦」** ⇒ 逐次按压记四个**与焦点走线无关**的页面量："
                "`body_tabindex`（属性原文）、`body_tab_index`（IDL）、"
                "`body_n_children`、`body_scroll_top`。\n"
                "**② 读数**：**5/60 圈缺 `document.body`（8.3%）**，"
                "落点第 **10 / 6 / 1 / 12 / 8** 圈 ⇒ 与 933 的 **3/32（9.4%）**"
                "**同量级** ⇒ **频率落在 8–9%**；"
                "⭐ **短圈 == 同臂整圈删掉 `BODY` 那一站：5/5 逐条全等**"
                "（探针自己的 `short_cycle_vs_ref()`，**934 独立复核了 933 的结论**）。\n"
                "**③ ⭐⭐⭐ H 被证伪**：**`body_tabindex` ≡ `null`、"
                "`body_tab_index` ≡ `-1`、`body_scroll_top` ≡ `0` —— 全臂恒定**；"
                "`body_n_children` 在 **12 / 13** 之间跳、**完整圈之间逐次全同**\n"
                "⇒ 但**一旦按正确的时间对齐（把参照圈在 `BODY` 那一行切开再拼），"
                "缺席圈与完整圈的四个量逐次全同（5/5）**\n"
                "⇒ ⇒ **`document.body` 自己那一下的任何可测属性，"
                "与「那一站出不出现」无关。**\n"
                "⚠️⚠️⚠️ **④ 撞出「切片会把规律读反」的**第四种形式**："
                "**「缺席圈比参照圈少一行」⇒ 按行号对齐就是整体错位一格**\n"
                "**可复算的证据**：完整圈的 `body_n_children` 跳变行号是 "
                "`[…15, 17, 20, 24, 25]`，而缺席圈是 **`[…14, 16, 19, 23, 24]`** —— "
                "**每一个都恰好少 1**，而**前 13 行完全相同**\n"
                "⇒ 第一版读到的「`all_same = False` ⇒ 它变了」**全是错位**，"
                "**不是真相关** ⇒ ⇒ **这是本轮最容易上当的一处**："
                "**「找到了一个相关的量」这个结论本身，也可能是切片对齐造出来的**\n"
                "⇒ ✅ **处置：两种对齐都算、都记** —— `naive_row_align`（**保留当历史记录**："
                "它是那处错位的现场）与 `time_aligned`（**判决**）；"
                "**基线与判据都写明「判决看 `time_aligned`」**。\n"
                "⚠️⚠️ **第五点纪律（934 事先写下的，现在正好用上）**："
                "**「不许因为找到相关量就宣称它就是成因」** —— 本条本来就该说，"
                "而 H 连「相关」都不是、**它连错位都不是**。\n"
                "⚠️⚠️⚠️ **成因仍然未查明、标「未验证」**："
                "**5/60 仍不足以判定**「随机 / 固定周期 / 与某个未观测变量相关」；"
                "落点第 1/6/8/10/12 圈**分散** ⇒ **仍然不许把「分散」读成「随机」**。") ,
            "source_body_stop_not_in_dom_935": (
                "✅⭐⭐⭐ **935 把「原理上不可从 DOM 查明」从**假设**升级成**测出来的结论****\n"
                "**（源站，纯诊断，2 轮 × **两臂各 15 圈 = 60 圈**；"
                "`design_ok=True`、2/2；`jimeng_probe935_body_stop_sweep_src.py`）\n"
                "**① ⭐ 两个方法论要点都是被 934 的坑逼出来的**：\n"
                "**（a）对齐必须按落点、不许按行号** ⇒ 935 **不在整圈上比**，"
                "而是先在每一圈里**定位「从 BODY 之前那一站出发的那一次按压」**"
                "（参照圈那一 press 的 `pre.active.dom_sig`），**只比那一次** "
                "⇒ **单点比较、行号无关**。\n"
                "⚠️⚠️⚠️ **⚠️ 定位轴第一版选错了、而且错得「看起来能跑」**："
                "原本想找「`post.dom_sig` == 参照圈 `BODY` 那一站 `dom_sig`」的那次按压；"
                "**但 933/934 已经测出「缺席圈 == 整圈删掉 `BODY` 那一站」** "
                "⇒ **缺席圈的 `sig` 里压根没有 `BODY` 那个 `dom_sig`** "
                "⇒ 那样定位的话**缺席圈必然 `found=False`**，"
                "**而那恰恰是唯一要看的那些圈 ⇒ 整批会落空**。\n"
                "⇒ ⭐ 改用 **`pre` 落点**之后：**「那一 press」在缺席圈里也找得到、"
                "60/60 全找到、找不到 0 个** ⇒ **顺带独立复核了 933/934 那个"
                "「短圈 == 整圈删 `BODY`」的结论**\n"
                "⇒ ⭐ **这是「先读上一批的结论、再设计下一批」的一次正收益**："
                "**933/934 那条结论不只答了原问题，还直接救了 935 的设计。**\n"
                "**（b）目标不是找一个原因，而是把「查不出来」变成一条读数** —— "
                "⚠️ 934 已把 `document.body` 自己能测的全测了、全恒定 "
                "⇒ **不许**接着在它身上找 ⇒ 935 在**同一时刻**系统扫 "
                "**14 个互不相关的** DOM 可观测量（`documentElement` 滚动量三样、"
                "`window` 滚动量三样、**`document.hasFocus()`**、`visibilityState`、"
                "焦点元素视口坐标、`n_focusable`、承 934 的 body 四项），"
                "外加 **3 个 pre 落点字段**。\n"
                "**② ⭐⭐⭐ 判决**（**每臂 pre 比 17 个字段、post 比 14 个**）：\n"
                "**`pre` 侧：4/4 臂、60 个圈、逐点全部相同、零差别**\n"
                "**⇒ ⇒ 在「从 BODY 之前那一站出发」那一刻的 `pre` 状态里，"
                "这 17 个可观测量没有任何一个能区分「这一圈会不会出现 `BODY` 站」** "
                "⇒ ⇒ **「原理上不可从 DOM 查明」不再是假设、而是一条测出来的结论**"
                "（对这批量而言）⇒ **复刻侧由此拿到一条可以写进基线的边界**（§122 的精神）。\n"
                "⚠️⚠️ **`post` 侧那两处差别（`active_rect` / `has_focus`）"
                "是**必然的因果后果**、不是相关量** —— ⭐ 因为「焦点有没有落到 `BODY`」"
                "**本身就是那次按压的结果**（落在 `BODY` 与落在 `与 AI 对话` "
                "视口坐标当然不同）\n"
                "⇒ **这正是 §923 那条「`post` 是按压的**结果**、不是 keydown 那刻的"
                "**原因**」的直接体现** ⇒ **不许把那两处差别读成线索**。\n"
                "⇒ ⭐ **也正因如此，判决只认 `pre` 侧**（4/4 臂零差别）—— "
                "**`post` 侧那一律不作数**，因为它测的是**结果**。\n"
                "**③ 读数**：**5/60 圈缺 `document.body`（8.3%）**、落点第 "
                "**10 / 6 / 1 / 12 / 8** 圈 ⇒ 与 933 的 **3/32（9.4%）**、"
                "934 的 **5/60（8.3%）** 全部一致 ⇒ **频率稳定在 8–9%**。\n"
                "⚠️⚠️⚠️ **④ 935 探针自己踩的两个坑（都要留痕）**：\n"
                "**（a）`KeyError: 'pre_dom_sig'` ⇒ 整轮 9 分钟读数全丢** —— "
                "根因是**把「census 原始键」与「派生键」混在同一个元组里**、"
                "再按原始键去取；且**落盘排在后处理之后** ⇒ 后处理一崩、连原始读数都没了\n"
                "⇒ ✅ 两处都修：原始键与派生键**分开取**、**原始读数一采到就先落盘**；"
                "并加了**两条 assert 当免疫针**"
                "（「派生键与 census 原始键**不许重叠**」「pre/post 派生键**不许重名**」—— "
                "**重叠就说明取法错了**）\n"
                "**（b）汇总行把圈数与臂数虚高了 3 倍** —— 我为了「落盘提前」"
                "把 `rec` 在每轮里 `append` 了 **3 次**（三次都指向同一个 dict）"
                "⇒ 打出「**15/180** 圈」「**12/12** 臂」，真实是「**5/60** 圈」「**4/4** 臂」\n"
                "⇒ ⭐ **比值恰好没受影响**（8.3% 两边一样）⇒ **只错在绝对计数** "
                "⇒ ⇒ **教训：「落盘要早」与「每轮只记一次」是两件事**，"
                "**前者不能牺牲后者** ⇒ 已改成 `if len(runs) < rep` 才 append。\n"
                "⚠️⚠️ **⑤ 成因仍然未查明、标「未验证」**："
                "**935 只说「这 17 个量查不出来」**，**没说「任何量都查不出来」** —— "
                "**不许**把「这一批查不出来」读成「原理上必然查不出来」"
                "（那仍然是 §122 那种断言，只是换了个说法）。") ,
            "source_inlayer_occlusion_absent_936": (
                "✅⭐⭐⭐ **936：§84 起挂着的「非全屏浮层盖住**层内**控件该算什么档」，"
                "机制查清了 —— 两侧都测出**这一类 0 观测**，所以判据不用改**\n"
                "**（分两半：复刻侧零探针反事实 2 次读数；源站探针 "
                "`jimeng_probe936_inlayer_occlusion_src.py`，2 轮 × 各 3 层 = 6 层、"
                "360 步，`design_ok` 全 True、2/2 逐项相同）**\n"
                "**① 复刻侧：那个 `!inLayer` 守卫当前**不承重****\n"
                "`coveredByLayer = !inLayer && blockers.some(bk => bk.in_layer)` —— "
                "**`by_modal` 在 `_bucket()` 里排在 `by_layer` 前面** "
                "⇒「控件层内 + 遮挡物层内」那 8 行**全部** `covered_by_modal=true` "
                "⇒ **根本走不到那个守卫**。\n"
                "⭐ **反事实：把 `!inLayer` 拿掉重算分桶，162 行里换桶 0 行**"
                "（2 次独立读数逐项相同；离线复刻的分桶函数与审计自报的 151/11 逐字吻合，"
                "说明判据没读错）。\n"
                "⇒ **守卫防的那一类，在非全屏形态下 0 观测**；"
                "键盘探针那把更严的尺子（四边全被不透明外人盖住）**32 层全 0**。\n"
                "**② 源站：目标形态 0/360 步**\n"
                "层内步 **42**（搜索层 `ASIDE[canvas-feature-panel][role=dialog]` "
                "20 步/轮：输入框 + `全部 76` + 分类按钮 + 15 个结果按钮 + 翻页按钮）、"
                "**层内四边全被不透明外人盖住 0 步**、"
                "**「层内控件被**非全屏**浮层盖住」0 步**。\n"
                "⚠️ 任意位置全盖 **6** 步，**全部**是顶部 `返回首页` 那个链接、"
                "遮挡物是**铺满视口**的画布 pane（合判据的 `scrim`，系数 0.85）"
                "⇒ **落在 `by_modal` 那一路，与 §77 问的形态无关**。\n"
                "⭐⭐ **两侧独立指向同一结论**：这一类不是「判据分错了档」，"
                "而是**它到 936 为止没发生过** ⇒ **判据一个字都不动**（§77）。\n"
                "**③ 顺带测出 845 那把尺子到底有多松（**约 25 倍**）**\n"
                "同一批步上：845 的**中心点 + 包含关系**口径报「被遮」**154/360**，"
                "审计第 3 版的**四边 + 不透明**口径报**6/360** "
                "⇒ **936 第一次把两把尺子的差距量化出来**"
                "（845 的读数只当对照，不参与判决）。\n"
                "**④ 阳性对照：4/6 层尺子报出**四边全盖**，0 观测因此作数**\n"
                "⚠️⚠️ 夹具**必须比控件大出一圈**（`PAD=6`）—— 四条探针点按判据是"
                "**外扩 1px**，夹具若正好等于控件矩形，四个点全落在夹具**外面** "
                "⇒ **阳性对照在构造上就不可能通过**。\n"
                "⚠️⚠️ 另有一条更隐蔽的：夹具若照抄目标选择器、不设尺寸上限，"
                "选中的是**整个面板**（实测 `ASIDE` 320×1084）⇒ 那测的是「面板被盖」，"
                "不是本批问的「**控件**被盖」⇒ 已限定只挑 ≤160px 的控件。\n"
                "**⑤ ⚠️⚠️⚠️ 机制假设 H936「浮层互斥导致这一类不可能出现」"
                "**未验证、只是与两侧读数相容**** —— "
                "源站实测同时最多 **2 层**，而**那第 2 层是常驻的 `.react-flow__node-toolbar`**，"
                "**不是**第二个浮层 ⇒ **「2 层」不能读成「两个浮层并存」**，"
                "本批**没有**测到「开一层会不会关掉另一层」这件正事。\n"
                "⚠️ **所以不许**说 H936 已成立；只说「这一类 0 观测、判据不动」。\n"
                "**⑥ 顺带一条源站读数（**未解释**）**：画布右键菜单 "
                "`DIV[canvas-context-menu][role=menu]` 开出来后，**60 次 Tab 一步都没进去**"
                "（`n_steps_in_seed=0`），且层内**没有任何尺寸够的可聚焦控件** "
                "⇒ 阳性对照在它身上如实报「层内找不到控件」。"
                "**源站这个菜单的键盘可达性从未取样过**，本批**不判它是缺陷**。") ,
            "source_transient_layers_exclusive_agent_panel_not_937": (
                "✅⭐⭐⭐ **937：H936「浮层互斥」查清了 —— 一半被证实、一半被证伪**，"
                "**判据仍然一个字不动**\n"
                "**（源站，纯诊断，2 轮 × 5 个开层器的 20 个有向配对 = **40 配对**，"
                "其中「两段都开得出来」**28 个**；`design_ok` 全 True、**2/2 逐项完全相同**）**\n"
                "**① 判决：瞬时浮层**确实互斥**，24/28**\n"
                "开 A 再开 B，**B 把 A 关掉** 24 次，按 A 的身份分组**没有一个例外**：\n"
                "`canvas-feature-panel`（搜索/生成历史）**10/10 被关**、"
                "`canvas-zoom-menu`（缩放）**6/6 被关**、"
                "`canvas-context-menu`（右键）**8/8 被关**。\n"
                "**② ⭐⭐ 唯一的例外，也是唯一的反例：`canvas-agent-panel`（与 AI 对话侧栏）**\n"
                "它作为 A 时 **4/4 全部存活**，能与 `canvas-feature-panel`、`canvas-zoom-menu` "
                "**真的并存** ⇒ ⇒ **H936 不是全错**："
                "**「浮层互斥」对瞬时浮层成立、对常驻侧栏不成立。**\n"
                "⚠️⚠️ **而且是不对称的**：侧栏作为 **B** 时**照样收掉 A**"
                "（`生成历史→侧栏` A 没了、`右键菜单→侧栏` A 也没了）"
                "⇒ **它是「开关式常驻侧栏」：开它会收掉瞬时浮层，"
                "而它自己不被瞬时浮层收掉。**\n"
                "**③ ⭐ 这条反例为什么值得单独记：它是被判据当成「层」的**\n"
                "`canvas-agent-panel` 之所以落进 `LAYER_SEL`，**只因为它的 "
                "`data-testid` 以 `-panel` 结尾**（`[data-testid$=\"-panel\"]`）"
                "—— 它**其实是常驻侧栏，不是浮层**。\n"
                "⇒ ⇒ **判据的「层」定义里有一个未被记录的例外：常驻侧栏与浮层不是一回事，"
                "而 `LAYER_SEL` 把它们混在一起。**\n"
                "⚠️⚠️ **但这仍然不构成改判据的理由**（§77）：936 已测出 42 个层内步里"
                "**被非全屏浮层四边全盖 0 次** ⇒ **即使侧栏与浮层并存，它也没有盖住层内控件** "
                "⇒ **§77 问的那一档仍然不成立、判据不用动**。\n"
                "**④ ⭐⭐⭐ 937 探针自己打出的汇总与真相**正好相反**，"
                "靠「原始读数先落盘」才捞回来**\n"
                "第一版有一行 `if k and k != base_ids:` —— `k` 是**字符串**、"
                "`base_ids` 是**集合**，`!=` **恒为真** ⇒ 每个浮层都「通过」"
                "⇒ 循环把**最后一个**浮层当成 A，而实测那最后一个**正是常驻的 "
                "`canvas-editor-menu`**（左侧工具条，从加载起就开着）\n"
                "⇒ ⇒ `a_survived` 测的是「常驻层还在不在」⇒ **恒为 true**\n"
                "⇒ ⇒ 探针当时打出的汇总是「**32/32 全部并存 ⇒ H936 被证伪**」，"
                "**而从原始读数重算的真相是「24/28 里 B 关掉 A」—— 结论正好相反。**\n"
                "⚠️⚠️ **「一个恒真的字段比没有字段更坏」又应验了一次，而且这次它直接"
                "产出了一条完全相反的结论。**\n"
                "✅ 三处已修：① 身份改用**集合差**；② 「A 到底是谁」写进读数"
                "（`a_new_keys`），读的人无从再被蒙；③ ⭐⭐ **新增仪器自身的阴阳对照门** "
                "`instrument_discriminates_ok` —— `a_survived` **必须两个答案都出现过**"
                "（实测 8 True / 24 False）。\n"
                "⚠️ **这道门是冲着「结论看起来整齐」去的：越整齐越要验。**\n"
                "**⑤ 计费边界做成了**结构性禁令**（不是靠自觉）**\n"
                "`FORBIDDEN_TIDS` 含 `canvas-commerce-entry`（源站实测存在的"
                "积分/会员入口 `Credits: 805 · 基础会员`），守卫按 `data-testid` "
                "**拦在 `mouse.click` 之前** ⇒ 本批**没点过它**。\n"
                "**⑥ ⚠️⚠️ 仍未验证的**\n"
                "· **H936 没有被整体证实**：它只覆盖「瞬时浮层互相排斥」这一半；"
                "「被关掉的层里那些控件因此才没被盖住」这后半截靠的是 936 的 42 个层内步，"
                "**两批合起来才够，本批自己不够** ⇒ **不许**说 H936 成立。\n"
                "· 本批**没测**源站其余形态的浮层（资产库、项目信息、时间线全屏等）"
                "⇒ 「瞬时浮层互斥」这个结论**只在这 3 个已测的瞬时浮层上成立**。\n"
                "· 源站**右键菜单的键盘可达性仍未解释**（936 撞出、937 只量了它的开合行为）。") ,
            "replica_transient_layers_exclusive_938": (
                "✅⭐⭐⭐ **938：把 937 的源站读数**真正实现进复刻**，并用复刻侧探针"
                "逐条验过 —— 互斥从「各自为政」变成**结构保证**\n"
                "**（复刻侧纯诊断 `jimeng_probe938_replica_layer_exclusivity.py`，"
                "2 轮 × 14 个有向配对 = **28 配对**；`design_ok` 全 True、"
                "**28/28 全部可用、28/28 全部符合预期、2/2 逐项相同**）**\n"
                "**① 动手前复刻这边根本没有「互斥」这回事**\n"
                "每个层各自一个**本地 `useState`**：TopBar 的 search/history/more、"
                "BottomDock 的 zoomMenu、Workspace 的 contextMenu/paneMenu "
                "⇒ **没有任何一处能实现「开一个关掉另一个」**；"
                "只有 TopBar 内部手动关掉了 search↔history 一对，其余全各自为政。\n"
                "⇒ 938 在 `jimengStore` 里加了**单一来源**的 `transientLayer` 槽位"
                "（`openTransientLayer` / `closeTransientLayer`），"
                "把**已测到的 4 个**（search/history/more/zoom）接进去。\n"
                "⚠️ 源站其余形态（资产库/项目信息/时间线全屏/视频全屏）的互斥"
                "**本批没测** ⇒ 推广到那些层是**推断、未验证**，它们保持原样。\n"
                "**② 侧栏的**不对称**也实现了，而且只做了实测的那一半**\n"
                "**开侧栏会清空槽位**（`setAiDrawerOpen(true)` / `openAiDrawer`）"
                "⇒ 收掉所有瞬时浮层（实测 24 个配对里的 4 个方向都符合）；\n"
                "**反方向故意不做** —— 开搜索/缩放/右键**不关**侧栏"
                "（实测 `agent→search` / `agent→zoom` 侧栏仍在，4/4）。\n"
                "**③ 复刻侧读数：24 个「A 被关」+ 4 个「A 仍在」，与源站同构**\n"
                "14 个有向配对 × 2 轮 = 28，**全部可用、全部符合预期**，"
                "两轮逐项完全相同 ⇒ **不是「碰巧对」，是行为一致**。\n"
                "**④ ⭐⭐ 复刻探针当场抓到 938 自己写出来的一个真交互 bug**\n"
                "`more` 触发器是 `closeAll(); openTransientLayer(\"more\")`，"
                "而 `closeAll` 里若**无条件清空** `transientLayer` ⇒ "
                "再点一次时先被清成 `null`、紧接着 `openTransientLayer(\"more\")` "
                "看到 `null !== \"more\"` ⇒ **又把它打开** ⇒ **再点一次关不掉**，"
                "toggle 语义被自己破坏。\n"
                "⇒ 是探针的 `reset_all()` 断言（「复位没清干净仍在场上的层: ['more']」）"
                "当场抓到的 ⇒ ✅ 已修（槽位的开关**只**由 `openTransientLayer` 管，"
                "`closeAll` 只管那四个**不在**槽位里的层）。\n"
                "**⑤ ⚠️ 探针自己踩的两个坑（都留痕）**\n"
                "**（a）zoom 触发器有两个身份**：React 的 "
                "`id=\"jimeng-zoom-menu-trigger\"`（给 `aria-labelledby` 用）"
                "**和** `data-testid=\"canvas-zoom-percent\"`。"
                "第一版拿**前者**当 testid 去找 ⇒ **DOM 里压根没有** "
                "⇒ 8 个配对**静默不可用**，而门只数「可用的有几个」（阈值 8）**照样绿**。\n"
                "⇒ 已把门**收紧**成「**每个触发器都被点到过**」+「可用数 == 配对总数」。\n"
                "**（b）侧栏不能靠点自己的触发器关掉**：`JimengAiButton` 用 "
                "`setAiDrawerOpen(true)` 且代码里明写「**不**改成 toggle」，"
                "而 `JimengWorkspace` 是 `{aiDrawerOpen ? null : <JimengAiButton />}` "
                "⇒ **侧栏开着时触发器根本不在 DOM 里**。\n"
                "⇒ 复位必须走抽屉内部的「收起」键 `canvas-agent-session-collapse`；"
                "第一版用「点触发器」复位 ⇒ 侧栏永远关不掉 ⇒ "
                "`zoom→agent` **假报**「A 没被关」。\n"
                "**⑥ 仍未验证的**\n"
                "· **只接了 4 个层**；源站其余浮层的互斥**没测**（推广是推断）。\n"
                "· 复刻的 contextMenu / paneMenu **没有**接进槽位 —— "
                "它们在 `JimengWorkspace` 里、且 936 已测出**源站右键菜单 60 次 Tab "
                "一步都进不去**，键盘可达性未解释 ⇒ 本批**不碰**，等那个问题有答案。\n"
                "· 本批**没有**测「两个层共存时键盘焦点怎么走」—— "
                "槽位保证的是**至多一个瞬时层**，焦点行为是另一件事。") ,



            "replica_type_coverage_closed_897": (
                "✅ **897 把复刻侧的类型覆盖补齐了**（各 2/2，两轮完全一致；"
                "判据**逐字复用** 896 的 `STATE_JS`，含那个**直方图**）。"
                "复刻左栏（`JimengToolRail.tsx`）`aria-label` 就是类型名，"
                "逐个插入 `文本`/`图片`/`时间线`/`主体`/`导演台` "
                "（video/音频 不插：demo 自带 video、895 插过 audio）⇒ "
                "**7 种类型全部覆盖**。**901 之前的读数**：每种类型"
                "**插入后（自带选中）**、**点空白之后**都是 `tabindex='0'`，"
                "**整轮 16 步 Tab 走查全程** `n_zero == n_nodes` "
                "⇒ 当时据此判定「**复刻侧根本没有 roving**」。\n"
                "⚠️⚠️ **901 已把这个状态改掉**（`nodesFocusable={false}` ＋ "
                "自己的 roving）⇒ **本条描述的是 901 之前**。"
                "⇒ 顺带把**三代状态各自留痕**钉在这里："
                "**895** 恒 `'0'`、**类型覆盖不全** ⇒ **897** 恒 `'0'`、"
                "**7 种类型全测**（**在 895 当时没测全**的那个缺口"
                "**已由 897 补齐**）⇒ **901** **中性态无 `tabindex` 属性**、"
                "仍是 7 种全测（**又被 901 改掉**的是「恒 `'0'`」这一条）。"
                "**不许**回头删掉这一段 —— 它是当时**真实测出来的**结论，"
                "也是 901「为什么值得改」的依据（见 "
                "`replica_roving_implemented_901`）。\n"
                "⚠️ **诚实记账（当时就有、现在仍然成立）**："
                "**4 种类型的「点本体」读数没取到** —— 左栏 `insertAtCenter` "
                "把新节点**全叠在画布中心**，中心点**落在最上层那个身上** ⇒ "
                "探针按纪律**跳过**（落点 `elementFromPoint` 对不上就**不点**），"
                "**没有**把那 4 个读数**猜**出来。⇒ 901 的探针改成"
                "**插一个、量一个、再插下一个**，每个类型都拿到了自己的读数。\n"
                "⚠️ **两侧类型集不对称**（记账，不是 bug）：复刻有 `subject`（主体），"
                "**源站 894 矩阵里没有**这一类；复刻的 `director`（导演台）"
                "对应源站的 `external`。⇒ **源站侧**那一类仍未取样。"),
            "replica_wrapper_is_in_tab_sequence_898": (
                "⚠️⚠️ **本条的前提已被 901 改掉** —— 它量的是**901 之前**的"
                "复刻（那时节点 wrapper **恒** `tabindex='0'`、**一直**在 Tab "
                "序列里）。**901 之后**：中性态 wrapper **没有** `tabindex`、"
                "**不在**序列里；**第一次按 Tab 才被装进去**（见 "
                "`replica_roving_implemented_901`）。⚠️ **不许**拿本条去论证"
                "「901 之后 wrapper 还在序列里」—— **不成立了**。\n"
                "**898 的原测量**（各 2/2，两轮完全一致）：**复刻的节点 wrapper "
                "确实在 Tab 序列里**。三条独立读法：\n"
                "① **直接读序列**（不靠走查去撞）：中性态 "
                "`wrapper 下标 = [1, 7]`；再插 5 个节点后 "
                "`= [1, 7, 8, 12, 16, 27, 37]`（**7 个 wrapper 对 7 个节点**）。\n"
                "② **从空白起走**：Tab 第 **1/7/8/9/10** 步**就落在 wrapper 上**。\n"
                "③ **点节点本体**：`text`/`image`/`director` 落点**就是** wrapper "
                "本身（`activeElement === wrapper`）；⚠️ 但 `timeline`/`subject` "
                "的**几何中心正好是一个内层 BUTTON** ⇒ 点中心落点是那个按钮"
                "（**不是**「这两种节点不可聚焦」—— 它们照样在序列里、"
                "Tab 也照样能到）。\n"
                "⚠️⚠️ **898 第一版自己踩的坑，必须留痕**：第一版只做了"
                "「**从刚点过的那个节点内部**起走」的 12 步走查，读数是 "
                "**24/24 全 False**，看着**像**「wrapper Tab 不到」—— "
                "**那是取样假象**：起点在**最后一个节点内部**，往前走只会"
                "越过前面那些 wrapper。⇒ 教训：**「走查没走到」≠「走不到」**；"
                "要证「走不到」得**直接读序列**，或者**从画布外起走**。"
                "（897 当时写下的「**不许**据此下结论」**正好**挡住了这个坑。）\n"
                "⇒ 由此得到的那条结论**依然有用、但要换措辞**："
                "**源站和复刻都能用 Tab 走到节点 wrapper**（901 之后也一样："
                "按 Tab 就能走到）。⚠️ **不许**把差异概括成"
                "「**复刻的节点 Tab 不到**」（那是**错的**）。"),
            "source_roving_next_rule_899": (
                "✅ **899 把「算下一个」的规则也测出来了**（源站，各 2/2，"
                "两轮**完全一致**；仪器 `INSTALL_JS` / `STATE_JS` **逐字复用** 896，"
                "从**点空白**起走，同 896 的起点；按 Tab **节点数 + 25** 次，"
                "故意**走过一圈**）。\n"
                "① **顺序 ≈ DOM 序**：按**身份**（`data-testid`）记 DOM 序，"
                "把「每次**新**布上 `'0'` 的那个节点」的下标连起来 ⇒ "
                "`[0,1,…,11, 13,14,…,75]`，**和 DOM 序高度一致**。\n"
                "② **到末尾就停手、绝不绕回**（这一条最关键）："
                "`max_dom_idx_armed = 75`（**就是最后一个**），"
                "而整轮 101 次按压里 `revisited = {}` —— "
                "**没有任何一个下标被布过第二次** ⇒ **不循环**。"
                "指针走完之后，应用**完全不再布 `'0'`**，焦点就按**浏览器原生**"
                "顺序走出画布（选择工具 / 小地图 / 显示连线 / Zoom options / "
                "与 AI 对话 → 顶栏 → 绕回 `Canvas`）。\n"
                "⚠️⚠️ **908 撤回了本条的后半句：「绝不绕回」是错的。** "
                "**「撒手」那一半仍然成立**（按前焦点是**节点本体**时确实一次都不布）；"
                "但**按前焦点是**画布根**、方向为 `Tab` 时，应用会**布 `'0'` 绕回**"
                "（4/4）。⇒ 899 之所以读到 `revisited = {}`，是因为"
                "**它的按压预算（`节点数 + 20`）在焦点走回画布根之前就用完了** "
                "——**从末尾走到画布根还要约 19 次** ⇒ **它根本没问到绕回**。"
                "⚠️⚠️ **929 把这个「约 19」量准了、并钉死了「差一按」**："
                "**到末尾 = 第 83 次、绕回 = 第 102 次 ⇒ 恰好 19 次**；"
                "而 896 的预算是 `节点数 + 25 = 101` 次 ⇒ **恰好差 1 按** "
                "⇒ **`revisited = {}` 真的只差一按**。"
                "详见 `source_roving_wraps_at_canvas_root_908`。\n"
                "③ 途中 **27 次按压「原地没布」**：落点既有节点**内层控件**"
                "（全屏编辑 / 静音 / 添加素材到时间线 各 ×2），也有节点**本体**，"
                "还有画布**外围 chrome**。⇒ 指针走完之后就是**彻底撒手**。\n"
                "④ `n_zero` **恒为 1**、`defaultPrevented` **全 False**"
                "（复核 896 的结论，成立）。\n"
                "⚠️⚠️ **两条未解释，不许编机制**：\n"
                "· **76 个节点里有 2 个整轮从没被布上 `'0'`**："
                "下标 12 = `图片 node: b22-upload`（image 类型，**焦点第 17 步"
                "走到过它**，但它**从没被布上 `'0'`**）、"
                "下标 68 = `音频 node: 音频 61`（audio 类型，焦点**也没**到过）。"
                "**两轮完全一致 ⇒ 不是随机**，但**原因未查明**。\n"
                "· **有 1 个节点被布上 `'0'`、而焦点**从没到达**它。\n"
                "⇒ 所以复刻若按「**纯 DOM 序**」实现，**会**在那 2 个节点上"
                "**和源站不一致**。⚠️ **不许**把这个差异**当成 bug 顺手抹平**，"
                "⚠️ **更不许**反过来**猜**一个原因去「对齐」它 —— "
                "要么就这样**记着**，要么**先测清原因**。\n"
                "⚠️ **899 第一版自己踩的两个坑，必须留痕**：\n"
                "· `OVERRUN=5` **不够** —— 81 次按压里只有 72 次真正推进指针"
                "（其余是「原地重写同一个已有 `'0'` 的节点」），指针只走到下标 72、"
                "**根本没到末尾** ⇒ 「怎么绕」那一问**其实没测到**，"
                "**差点**把「不绕回」这个结论建立在没测到的数据上。\n"
                "· `focus_is_wrapper` 这个字段**写错了、而且恒为真**："
                "它比的是「focusin 的 target 是否等于 `activeElement`」—— "
                "而拿到焦点的元素**按定义**就成了 `activeElement`"
                "（896 那边 18/18 全 True 就是这个原因，看着像证据、"
                "其实**什么也没测**）。⇒ 899 改成真判据："
                "**落点自己带不带 `react-flow__node` 类**。"
                "教训：**一个恒真的字段比没有字段更坏** —— 它让人以为测过了。\n"
                "⚠️ **节点总数是易变量**（同一条 URL 逐轮 74→75→76→77）"
                "⇒ 本条**不许**钉节点总数。\n"
                "⚠️ 汇总代码第一版还会**崩**：`seq` 里可能有 `None`"
                "（布 0 的目标不在本轮记录的 DOM 序里 —— 走查途中节点被 React "
                "重建就会这样，本轮实测到 1 次）⇒ 排序/比较前**必须**先把 "
                "`None` 摘出去。"),
            "unarmed_nodes_have_no_dom_reason_900": (
                "✅ **900 把「那 2 个节点为什么整轮没被布上 `'0'`」推到了"
                "**能推的边界**，并**排除了一个方向**（各 2/2，两轮一致）：\n"
                "① **它们在应用的节点表里**：第一次 Tab 时，应用给**全部 "
                "76 个**节点都写了 `tabindex`（目标 `'0'`、其余 `'-1'`）"
                "⇒ `not_written` **为空**。⚠️ 所以**不是**「它们压根不在表里、"
                "是 DOM 里多出来的」。\n"
                "② **它们在 DOM 层毫无特殊之处**：76 个节点的**属性集完全相同**"
                "（`aria-describedby` / `aria-label` / `aria-roledescription` / "
                "`ccfmp-element` / `class` / `data-first-content-source` / "
                "`data-id` / `data-testid` / `role` / `style`）"
                "⇒ **离群节点 0 个**；父链也一样"
                "（`react-flow__nodes` → `viewport` → `pane` → `renderer`）、"
                "`in_another_node=false`、可聚焦子孙数与尺寸都相同。\n"
                "⇒ **「这两个节点在 DOM 上有某种特殊标记」这个方向被排除了。**"
                "剩下的原因在**应用的内部节点表顺序/指针**里，"
                "**从 DOM 侧看不到**。\n"
                "⚠️⚠️ **所以结论是：这一条「仍未查明」，而且是"
                "**原理上不可从 DOM 查明**的那一种**（要看应用自己的数组）。"
                "⇒ 由此得到一条**实现层的硬约束**：复刻**没法**复刻这个"
                "「跳过 2 个节点」的具体行为（手上没有能产生它的信息），"
                "所以实现时**只能按纯 DOM 序**、并把这条差异**如实记为已知差异**。"
                "⚠️ **不许**为了「看起来一致」去**编**一个 DOM 层的判据"
                "（例如「跳过 aria 含 upload 的节点」「跳过倒数第 N 个」之类）"
                "—— 那是**把未查明的东西伪装成已知**。\n"
                "📌 顺带一条**对 896 规则②的修正**（900 实测 2/2）："
                "「**每次 keydown 都布 `'0'`」**不是无条件的** —— "
                "从画布**中途**开始连按 30 次 `Shift+Tab`，**只有第 1 次**布了"
                " `'0'`（下标 22），其余 29 次**一次都没布** "
                "⇒ 焦点一旦不在节点本体上，应用就**不再布**。"
                "⇒ 896 那条「唯一触发是 Tab/Shift+Tab 的 keydown」**仍然成立**，"
                "但要补一句：**还要求那一刻焦点在某个节点上**。\n"
                "⚠️ **900 第一版自己踩的坑**：结尾把一大坨 `json.dumps(summary)` "
                "**打到 stdout**，而输出是**管道给 `tail`** 的 ⇒ `tail` 早退出、"
                "管道写不进去 ⇒ `BlockingIOError` ⇒ **探针在最后一步炸掉、"
                "连文件都没写**（写文件的语句排在打印**之后**）。"
                "⇒ 教训两条：**① 落盘必须排在打印之前**；",
                "**② 长输出要么落盘、要么别进管道**。"),
            "source_roving_tabindex_policy_896": (
                "✅ **896 把策略测出来了**（源站，各 2/2，两轮逐步一致；"
                "仪器 = `focusin`/`focusout`/`keydown` 监听 **＋** "
                "`MutationObserver(attributes, attributeOldValue, "
                "attributeFilter:['tabindex'], subtree)` 挂在 `.react-flow` 上、"
                "**任何交互之前**就挂）。规则原文：\n"
                "① **中性态：所有节点根本没有 `tabindex` 属性**"
                "（`getAttribute` → `None`；`el.tabIndex` **属性**读作 DOM 默认的 "
                "`-1`）⇒ **一个节点都不在 Tab 序列里**。\n"
                "   ⚠️ 「`tabindex=None` / `tabIndexProp=-1`」是**同一件事的两种"
                "读法**（属性不存在 vs 属性读到默认值），**不是矛盾**，"
                "894 存档里中性态记的也是 `tabindex=['None'] prop=[-1]`。\n"
                "② **布 `0` 的触发只有 Tab / Shift+Tab 的 `keydown`**：按下后"
                "~0.6ms 内**先**给目标节点写 `tabindex='0'`、**再**给**其余每个**"
                "节点写 `tabindex='-1'`（**全画布重写**）。\n"
                "③ **不 preventDefault**（`defaultPrevented=False`，2/2；"
                "用 892 的取法：捕获阶段存引用、派发结束后再读）"
                "⇒ 焦点移动是**浏览器原生的**，应用只负责「先把目标装进 Tab 序列」。\n"
                "④ **先布 `0`、再移焦点**：`focusin` **捕获阶段**读落点，"
                "`tabindex` **已经是 `'0'`** ⇒ **不是** focusin 之后的反应式回调。\n"
                "⑤ **「设多久」= 到下一次 Tab 为止；焦点离开画布也**不**回撤**："
                "点空白之后那个 `0` **仍然**留在最后一个被 rove 过的节点上"
                "（静置 1.5s 仍在）⇒ **不是「焦点在哪 0 在哪」**，"
                "是「**上次布的那个 0 一直留着**」。\n"
                "⑥ **选中不布 `0`**：直接点节点选中它（`selected=True`），"
                "它的 `tabindex` **仍是 `None`**（894 `after_select`，2/2）。\n"
                "⑦ **roving 指针会跑到真实焦点前面**：时间线节点的**内层按钮**"
                "（导出时间线/全屏编辑/静音/添加素材到时间线，**本来就天然可聚焦**）"
                "落进 Tab 序列时，应用已经把 `0` 布给了**下一个**节点，"
                "而浏览器原生 Tab 先落到内层按钮 ⇒ **连续 4 步**"
                "「带焦点的节点 ≠ 持有 `0` 的节点」。`n_zero` 仍是 1"
                "（roving 本身不乱），只是**指针跑在焦点前面**。\n"
                "⇒ 一句话：**「按 Tab 才把画布装进 Tab 序列：目标 0、其余全 -1；"
                "装完就交还给浏览器原生 Tab；此后不再回撤。」**\n"
                "⚠️⚠️ **896 当时在本条写下的「`nodesFocusable` 是错的杠杆」"
                "——898 更正为「错的**单方**方案」**：单翻 "
                "`nodesFocusable={false}` 会让节点**永远**不在 Tab 序列里 ⇒ "
                "画布**再也 Tab 不到**，**绝不许单独上线**（那比不改更糟）。"
                "但源站的机制**本身就是**「库不接管 + 应用自己布」⇒ "
                "**`{false}` 正是忠实实现的**前半段**，配后半段"
                "（keydown 布 0/-1 且**不** preventDefault）才成立。"
                "⚠️ **不许**把这条读成「这个开关不许碰」—— 那会否掉正确的前半段。\n"
                "⚠️ **896 也暴露了 894 判据里的一个洞**：`summarize()` 把 tabindex "
                "收成 `v[\"tabindex\"].add(...)`（**只收集合、丢掉计数**），"
                "而「**各有几个 0**」恰好就是区分 roving 的**唯一**判据 ⇒ "
                "894 读到了**却被 summarize **抹平**了，"
                "所以 894 明明看到 `audio ... ['-1','0','None']` 却答不出"
                "「到底几个是 0」。跟 893 的「跨时刻读数混比」同族："
                "**量到了但没留下能判读的形状**。\n"
                "⚠️ 894 里 `after_insert` / `after_insert_blank` / `after_select` "
                "三个条件**跑在 Tab 走查之后** ⇒ 那时画布**已经不是中性态**了，"
                "桶里出现混合值是**被布过 `0`** 的结果、**不是**中性读数；"
                "894 的中性读数只有 `fresh_load` / `after_blank` 两个。\n"
                "⚠️ **节点总数是易变量**（同一条 URL 逐轮 74→75→76→77），"
                "**不许**钉 `n_nodes` 或节点序号，只钉**关系**"
                "（`n_zero`、谁身上有 `0`、是不是带焦点那个）。"),
            "cancelbubble_unreliable_after_dispatch": (
                "⚠️ `cancelBubble` **派发结束后会被重置** ⇒ 它**不能**用来证明"
                "「有没有人调过 `stopPropagation()`」。892 实测到的是一组**互相"
                "拉扯**的读数：`bubbles=True` + 事后 `cancelBubble=False`，"
                "但 **`document` 冒泡阶段收到 0 次** ⇒ 事件本该冒泡却没到。"
                "⇒ 强烈指向**有人调了 `stopPropagation()`**，"
                "但**这一步仍未测到**，**不许**拿 `cancelBubble=False` 当证据。"),
            "contradiction_891_vs_source_RESOLVED_893": (
                "✅ **893 已把这个矛盾解开**（本条**第二版**：原来叫 "
                "`..._still_open`；事实推进后改名，免得基线里留一条"
                "「仍未解决」跟结论打架）。"
                "矛盾原样：891 的 C1（空白页 2/2）说浏览器**会**把焦点移到"
                "可聚焦子元素；源站结构与 C1 **完全一样**却 `focusin` **0** 次；"
                "892 又证明源站**没有** `preventDefault` ⇒ 三者不可能同时成立。"
                "**893 的答案（各 2/2）**：A 序列里 mousedown 那一刻，"
                "**落点 target 已 `isConnected=False`**（被 React 重渲染摘掉）、"
                "**节点 `tabindex=None` / `tabIndexProp=-1`**（**不可聚焦**），"
                "而 `tabindex` 是**事后**才变成 `'0'` 的 ⇒ 默认动作"
                "**无处可移** ⇒ `focusin` 0 次。"
                "⇒ 三者**同时**成立，矛盾消失。**排除法的净进展：排除了两个"
                "候选**（「浏览器规则」与「preventDefault`）。"
                "⚠️ 但「**为什么**点空白后那个节点 tabindex 是 None」"
                "**仍未查清**（与 889d 的 Tab 走查**不一致**，见 "
                "`source_node_tabindex_is_conditional_893`）—— "
                "**不许**简化成「源站未选中节点一律不可聚焦」。"),
            "preventdefault_judgement_defect_890": (
                "890 第一版把 `defaultPrevented` 挂在 `document` 的**捕获阶段**读，"
                "两条序列都读到 `False` —— 那个读法**恒真为假**（捕获阶段是最早跑的，"
                "此刻还没有任何 handler 执行过），**不是**「源站没 preventDefault」"
                "的证据。890b 改到**冒泡阶段**才算修对了判据，"
                "**但仍没读到**（事件没冒泡到 document）。"
                "⇒ 教训：判据坏了要**修判据并留痕**，不许把坏判据的读数当结论"
                "（与 876c「错判据不许悄悄改掉」同族）。"),
            "node_click_lands_on_nonfocusable_child": (
                "890b/890c 实测：点节点**中心**那个坐标，`elementFromPoint` 落到的"
                "**不是** `tabindex='0'` 的节点本身，而是它里面的一个"
                "**不可聚焦后代**（源站是 `svg`/tabIndex=-1，复刻是 `SPAN`/tabIndex=-1）。"
                "节点本身 `tabindex='0'`（两边都是）。"
                "⚠️ 这条**只说明落点是谁**，**不许**据此推出「所以焦点会/不会移动」"
                "—— 那一步**没测**。"),

            # 875：外层格子**恒定 153×28**，选中前后都不变；变的是格子里
            # 装什么：未选中 芯片 135（=153−左右 padding 9×2），
            # 选中 芯片 111 + gap 8 + Clear 16 = 135（正好填满）。
            "trigger_row_rect": "153×28，选中前后不变",
            "chip_rect_when_unset": "135×28",
            "chip_rect_when_set": "111×26（四个不同值文案量出来都一样 ⇒ 非内容驱动）",
            "src": ("jimeng_probe871_voicefilter_kb.py（性别）+ "
                    "jimeng_probe872_voicefilters_kb.py（**四个钮逐个**，"
                    "登录态，视口 1512×1200）+ "
                    "jimeng_probe873_voiceselect.py（选完之后）+ "
                    "jimeng_probe874_escvalue.py（焦点落点身份 / Esc 保留值）+ "
                    "jimeng_probe875_clearfilter.py（**清除钮**，四钮逐个）+ "
                    "jimeng_probe876c_clearfilter_kb2.py"
                    "（**清除钮的键盘**，三次复现）+ "
                    "jimeng_probe877_clearfilter_kb_all.py"
                    "（键盘行为**四钮逐个**重测，6/6 项全中）+ "
                    "jimeng_probe884_selectnode_src.py"
                    "（可靠选中节点，5 策略各 2/2）+ "
                    "jimeng_probe885_escselect2_src.py"
                    "（**Esc 之后节点也取消选中**、焦点仍在节点上）+ "
                    "jimeng_probe886_esconchip_src.py"
                    "（**芯片**上按 Esc 同一落点，源站首次取样）+ "
                    "jimeng_probe887_esconchip_val_src.py"
                    "（同一次运行读落点+值，**证伪**「芯片不清值」）+ "
                    "jimeng_probe888_reopen_src.py"
                    "（Esc 后**真卸载**、五种重开手段各 2/2）+ "
                    "jimeng_probe889_esclanding_src.py"
                    "（**逐个前置态**测落点，4 档各 2/2）+ "
                    "jimeng_probe889b_esclanding2_src.py"
                    "（`pure_mouse` 2/2 + **层开着时同一次运行读值** 2/2）+ "
                    "jimeng_probe889c_blankvar_src.py"
                    "（**只隔离** `blank()` 这一个变量 ⇒ 2/2 复现出 `Canvas`）+ "
                    "jimeng_probe889d_canvasfocus_src.py"
                    "（画布根容器的 **role/aria/tabindex** 身份 + Tab 轨迹）+ "
                    "jimeng_probe890_nodefocus_why_src.py"
                    "（点节点抢不抢焦点的**两个候选机制**；⚠️ 它的 "
                    "`defaultPrevented` 判据**恒真为假**）+ "
                    "jimeng_probe890b_nodefocus_why2_src.py"
                    "（**修判据**到冒泡阶段 + focus() 目标身份 + "
                    "mousedown 落点是谁，各 2/2）+ "
                    "jimeng_probe890c_nodefocus_why_ck.py"
                    "（**同一套判据**用在复刻侧对照，各 2/2）+ "
                    "jimeng_probe891_mousedown_rule_ck.py"
                    "（**最小复现**把「浏览器规则」那条假设**证伪**，"
                    "六格各 2/2）+ "
                    "jimeng_probe892_preventdefault_src.py"
                    "（**派发结束后**再读 `defaultPrevented` ⇒ 源站**没**"
                    "preventDefault，各 2/2）+ "
                    "jimeng_probe893_clickmoment_src.py"
                    "（**点击那一刻**节点发生了什么：target `isConnected=False` + "
                    "节点 `tabindex=None` ⇒ **机制钉死**，各 2/2）+ "
                    "jimeng_probe894_node_tabindex_matrix_src.py"
                    "（节点 `tabindex` 的**条件矩阵**（刚载完/点空白/连按 Tab 后/"
                    "插入/插入后点空白/选中），**推翻**了 889d 那句读数，"
                    "各 2 轮）+ "
                    "jimeng_probe895_node_tabindex_matrix_ck.py"
                    "（**同一张表**在复刻侧，判据**逐字复用** 894 ⇒ "
                    "复刻 `tabindex` **恒为 0**，各 2 轮）+ "
                    "jimeng_probe896_roving_tabindex_policy_src.py"
                    "（源站那个 roving 的**策略**：中性态**无 tabindex 属性**、"
                    "Tab keydown 时**全画布重写**「目标 `0` / 其余 `-1`」、"
                    "**不** preventDefault、**此后不回撤**；"
                    "含 894 判据漏掉的**计数**（各有几个 `0`），各 2 轮）+ "
                    "jimeng_probe897_ck_type_coverage.py"
                    "（**补齐复刻侧类型覆盖**（895 最后一个缺口）：判据**逐字"
                    "复用** 896 的 `STATE_JS`，左栏逐个插入 文本/图片/时间线/"
                    "主体/导演台 ⇒ **7 种类型全测**，各 2 轮）+ "
                    "jimeng_probe898_ck_focus_lands_on_wrapper.py"
                    "（「焦点落点**是不是 wrapper 自身**」+ **直接读 Tab 序列**："
                    "中性态 `wrapper 下标=[1,7]`、插 5 个后 "
                    "`=[1,7,8,12,16,27,37]` ⇒ wrapper **确实在序列里**；"
                    "**从空白起走**第 1/7/8/9/10 步落在 wrapper 上，各 2 轮）+ "
                    "jimeng_probe899_roving_next_rule_src.py"
                    "（「**算下一个**」的规则：顺序**≈DOM 序**、"
                    "**到末尾就停手、绝不绕回**（`max=75`＝最后一个、"
                    "`revisited={}`）、途中 **27 次**「原地没布」；"
                    "⚠️ 76 个里有 **2 个整轮没被布上 `0`**、原因**未查明**；"
                    "各 2 轮）+ "
                    "jimeng_probe900_unarmed_nodes_src.py"
                    "（「那 2 个节点为什么没被布 `0`」：**第一次 Tab 时全部 76 个"
                    "都被写了** ⇒ **在应用的节点表里**；**76 个属性集完全相同**、"
                    "**离群 0 个** ⇒ **DOM 层无特殊之处**；⇒ 原因在**应用内部**、"
                    "**从 DOM 侧不可查明** ⇒ 实现只能按纯 DOM 序并**记为已知差异**，"
                    "**不许编 DOM 层判据**去假装对齐；各 2 轮）+ "
                    "jimeng_probe901_roving_impl_ck.py"
                    "（**复刻侧实现后的验收**：判据**逐字复用** 896/899/900 的"
                    "**源站**探针 ⇒ 逐条对上源站**七条**"
                    "（中性态无属性 / n_zero 恒 1 / 不 preventDefault / "
                    "先布 0 再移焦点 / 纯 DOM 序 / 到末尾撒手不绕回 / "
                    "此后不回撤），各 2/2）+ "
                    "jimeng_probe902_unmeasured_cells_src.py"
                    "（把 901 **拒绝猜**的两格测掉：① 点空白后连按 `Shift+Tab` "
                    "⇒ 源站**一次 `\'0\'` 都不布**（与 901 那个「不猜」的"
                    "分支**一致**，但这是**测出来的**）；② 往回走**也是 DOM 序**、"
                    "往返后那个 `\'0\'` **不清**；⚠️ 但「回来后按 Tab 布的是 "
                    "`[2,3]`、**不是 0**」⇒ 指针**有被带过来的状态**、"
                    "具体规则**仍未查明** ⇒ 复刻那一格**记为已知差异**、"
                    "**不许**猜规则去凑；各 2/2））+ "
                    "jimeng_probe903_carried_state_src.py"
                    "（**四条对照**，每条只动一个变量，把 902 的 `[2,3]` "
                    "**大部分推翻**：`A` 干净基线 / `B` 中途点空白 / "
                    "`C` 指针到末尾 / `D` 两件都加（= 902 那条序列）"
                    "⇒ **8/8 全部 `[0,1,2]`**；⚠️ 但 902 与 903 的往回走"
                    "**停在 58 vs 59** ⇒ **两个读数都真实**、"
                    "触发条件**仍未查明**；各 2/2）+ "
                    "jimeng_probe904_endpoint_condition_src.py"
                    "（**扫两个变量**（进场前 `pre` 次 `Shift+Tab` ∈{0,5} / "
                    "往回 `k` ∈{28,30,32}）× 2 轮 = 8 条，**两轮逐条一致**："
                    "① **902 的 `[2,3]` 在 `pre=0` 干净臂里复现** ⇒ "
                    "**排除**「开头 5 次 `Shift+Tab` 是触发条件」；"
                    "② 终点是 `k` 的**严格线性函数** `endpoint = 88 − k`；"
                    "③ **回来后布的下标与终点无关**（58→`[2,3]`、"
                    "60→`[0,1,2]`、56→`[12]`、0→`[1,2]`）⇒ "
                    "**落点条件不在终点上**；④ 回来后第一次布的下标是 "
                    "**0/1/2/12**、**4 臂里只有 1 臂从 0 开始** ⇒ "
                    "**「从 0 开始」确实不是无条件成立**；"
                    "⚠️ **④ 的成因仍未查明**（本轮**没逐次记焦点落点** = 取样缺口）"
                    "⇒ **不许猜规则、不许改实现**）+ "
                    "jimeng_probe905_reentry_focus_src.py"
                    "（**补上 904 点名的取样缺口**：**逐次记按压时的焦点落点**；"
                    "并改用**臂间 reload 的单变量阶梯** "
                    "`L0` 从未 Tab / `L1` 只走到末尾 / `L2` 末尾＋回走 30。"
                    "3 臂 × 2 轮 = 6 次，**8 步逐次轨迹完全一致**："
                    "布的下标 = `[0,1,2,3]` 然后**连续 4 次不布**，"
                    "而那 4 次**逐次对得上「按压时焦点停在内层控件上」** ⇒ "
                    "**900 规则得到逐次证实**；且**布与落点严格错开一位** ⇒ "
                    "**896④ 再获证据**；**三条臂轨迹完全相同** ⇒ "
                    "**「走到末尾」「回走」都不影响回来后从哪开始**。"
                    "⚠️ **但 905 与 904 在名义相同的序列上给出了不同轨迹**"
                    "（终点 59⇒`[0,1,2,3]` vs 终点 58⇒`[2,3]`）⇒ "
                    "**有一个两批都没控住的变量，未查明** ⇒ "
                    "**不许宣布 904 作废、也不许宣布 905 是干净的那次**））＋ "
                    "jimeng_probe906_direction_asymmetry_src.py"
                    "（**把 905 的「方向不对称」钉成规则、并推翻 905 的一条推论**："
                    "① `F8` vs `B8` **只差方向**（同终点 58、同 back 布 13 次）"
                    "⇒ `F8` 布 `[2,3,4,5]`、`B8` **8 次一次都不布** ⇒ "
                    "**方向不对称成立，且只发生在「焦点在画布根」这个位置上**；"
                    "② 906 **一条记录里同时有 `closest` 与 `contains` 两种口径**"
                    "⇒ **自带对照**：那四个内层控件 `closest=True` / "
                    "`contains=False`，而**「没布」的按压前焦点正是它们** ⇒ "
                    "**真判据是「元素本身就是节点本体」**；"
                    "③ **904 的 `[2,3]` 被干净臂精确复现** ⇒ **不是异常值**；"
                    "⚠️ **⑤ 但 906 推翻了 904③ 与 905④**：终点 58→`[2,…]`、"
                    "59→`[0,…]` ⇒ **落点恰恰跟着终点走**，"
                    "那两条「与终点无关」是**取样没覆盖到的巧合**。"
                    "另记两条缺陷：① **第一版把偶发加载失败报成 `BLOCKED`** "
                    "（登录态其实是好的）⇒ 已加**重试**；"
                    "② **被挡时不落盘**（落盘写在 `else` 分支里）⇒ 已移到外面。"
                    "各 2/2）＋ "
                    "jimeng_probe907_endpoint_to_start_map_src.py"
                    "（❌ **这一批作废**：臂间 reload 连续扫 `k`，"
                    "**但 6 条臂的终点全都是 `0`** —— 正向走查**每条都绕回了**，"
                    "**一个能区分的终点都没扫到**；成因是**走查按了 `节点数 + 25` 次，"
                    "而 908 实测绕回恰好在第 103 次**（78 节点）⇒ **`+25` 正好撞上"
                    "绕回点**。⇒ 终点→起点的映射**仍未刻画**，"
                    "要重扫得按 908 的停止条件。详见 `source_endpoint_start_sweep_void_907`）＋ "
                    "jimeng_probe908_wrap_around_src.py"
                    "（⚠️⚠️ **推翻 899 的「绝不绕回」**：2 臂 × 2 轮 = **4/4**，"
                    "两条臂都布到了 `0`（序列末尾 `… 74, 75, 0`），"
                    "**4 次绕回那一按的按前焦点全是画布根 `Canvas`**；"
                    "`W2`（**点空白直接回画布根、不走出去**）**也绕回** ⇒ "
                    "**「必须先走出画布」这条机制假设被自己的证伪臂推翻**。"
                    "**但 899 的「撒手」仍然成立**（按前焦点是节点本体时一次都不布）"
                    "⇒ 两条并存。⚠️ 899 读成「不绕回」是因为**按压预算"
                    "在焦点走回画布根之前就用完了**。顺带复现 **900**（跳过 12 与 68）"
                    "与 **896⑤**（走出去那段 `'0'` 一次没动））＋ "
                    "jimeng_probe909_canvas_root_ck.py"
                    "（**909 的真代码改动 ＋ 复刻侧验收**，5 臂 × 2 轮 = 10 条、"
                    "**两轮逐条一致**，判据**逐字复用** 906/908 的 `STATE_JS`/"
                    "`INSTALL_JS`，臂**逐字对应** 906 的 `F8-fresh`/`F8`/`B8` 与 "
                    "908 的 `W1`/`W2`）：改了三处 —— ① 找指针的判据从 "
                    "**`n === active || n.contains(active)`** 改成 **严格的 "
                    "`n === active`**（906：宽松口径会把内层控件当成「在节点上」"
                    "而**多布一次**）；② `cur === -1` 那一支**先**判「焦点是否落在"
                    "某个节点的**内层控件**里」、是就 **`return`**；"
                    "③ 注释规则表 5 条 → 7 条（撤回 899 的「绝不绕回」＋补两格）。"
                    "⇒ 逐条对上：画布根＋`Tab` 要布 `'0'`（三条臂**可见**）、"
                    "画布根＋`Shift+Tab` **8 次一次都不布**、"
                    "**内层控件 5 次全不布**（正是 901 改前会多布的那五次）、"
                    "布与落点错开一位。"
                    "⚠️ **两格标成没验到**：`F8` 的 press1 **不可判定**（要布的下标"
                    "**恰好就是**当前 `'0'` 所在的下标 ⇒ 「被 `oldValue != '0'` "
                    "过滤掉」与「位置本来没变」**同时出现**）；源站 `F8` 终点 **58** "
                    "vs 复刻终点 `[0]`（demo 只有 2 个节点）⇒ **不可比**。"
                    "⚠️ **探针缺陷**：第一版没记 `'0'` 动没动 ⇒ 被过滤吞掉的读数"
                    "**看不见**（**904 记过这个坑、909 又踩一次**）⇒ 第二版补 "
                    "`moved`）＋ "
                    "jimeng_probe910_endpoint_to_start_rescan_src.py"
                    "（**907 作废之后的重扫**，8 臂 × 2 轮 = 16 条、"
                    "**两轮逐条一致**）：**换掉了 907 的设计** —— "
                    "907 靠「先走到末尾再往回」⇒ 终点被走查预算绑架；"
                    "910 **直接扫「从画布根按 `j` 次」**（`j ≤ 65` **小于**实测"
                    "末尾 75）⇒ **结构上撞不上绕回**。"
                    "⇒ **实测终点 → 第一次布的下标**：`∅/2/3/10/20/31` ⇒ **0**；"
                    "**`46/56` ⇒ 12** ⇒ **分界落在 `(31,46]`、但没夹逼** ⇒ "
                    "**不许**当规则。**落点也跟着变**（0 那组落在 `视频 1`、"
                    "12 那组落在 `导出时间线`）；⚠️ **12 正是 900 那两个"
                    "「整轮没被布」之一** ⇒ **相关、不是机制**。"
                    "另落两条纪律：**`moved` 是必需字段**、"
                    "**走查停止条件不能拍脑袋给次数**）＋ "
                    "jimeng_probe911_threshold_bisect_src.py"
                    "（**把 910 那个宽 15 个下标的区间夹窄，并修正 910 的"
                    "「二档」**——中间还有一档 `11`。5 臂 × 2 轮 = 10 条、"
                    "**两轮逐条一致**，设计**逐字沿用** 910 只换 `j`）："
                    "实测终点 **`33` ⇒ 0**、**`36`/`39` ⇒ 11**、**`42`/`45` ⇒ 12** "
                    "⇒ **三档**（910 说的两档不完整）；⚠️ **两个边界仍未夹逼**"
                    "（`(33,36]` 与 `(39,42]` 各还差 3 个下标）⇒ **不许**当规则。"
                    "⚠️ **顺带收窄了 900**：**911 里下标 12 被布上了** ⇒ "
                    "**「整轮没被布」是「正序走查那一轮」的属性、不是该节点的"
                    "固有属性** ⇒ **900 那条要按这个口径读**。"
                    "另记：`11` 与 `12` 两档的 press1–press5 落点**完全相同**，"
                    "分岔只体现在 press5 的落点上 ⇒ **成因仍未查明**）＋ "
                    "jimeng_probe912_threshold_bisect2_src.py"
                    "（**把 911 剩下的两个边界都收成 1 宽**，4 臂 × 2 轮 = 8 条、"
                    "**两轮逐条一致**，设计**逐字沿用** 911 只换 `j`）："
                    "终点 **`34`/`35` ⇒ 0**、**`40` ⇒ 11**、**`41` ⇒ 12** ⇒ "
                    "**三批合起来边界收成 `35|36` 与 `40|41`**。"
                    "⚠️ **但这仍只是经验映射、不是机制** ⇒ **不许**写成规则、"
                    "**不许**据此改实现；⚠️ **收窄的是「经验边界」、不是「理解」**，"
                    "**成因仍未查明**、**不许就此结案**）＋ "
                    "jimeng_probe913_same_endpoint_two_routes_src.py"
                    "（**换方法**：不再夹边界，改问「同一个终点、两条不同路线，"
                    "起点跟不跟终点走」—— 4 臂 × 2 轮 = 8 条、两轮逐条一致。"
                    "✅ **真的测到的**：`A-fwd49` 终点 40 ⇒ 起点 **11**、"
                    "`A-fwd60` 终点 51 ⇒ 起点 **12** ⇒ **与 912 逐条相同**。"
                    "❌ **证伪落空**：**两条 `B` 臂「往回按了 0 次」** —— "
                    "`ARMS` 里 `B` 的 `j` 填的 **就是直接落在目标上的那个 `j`** ⇒ "
                    "**`A` 与 `B` 实际是同一条路线** ⇒ 对照根本没成立。"
                    "⚠️ **钉住这条教训**：证伪臂的参数**必须越过对照组**、"
                    "否则两条臂同一条、**那一问根本没被问到**"
                    "（与 899/901「次数要盖过被吃掉的部分」同一条）。"
                    "⇒ **不许**据 913 说起点是纯函数、**也不许**说它跟历史走，"
                    "**两个方向都没测到**"
                    "＋ jimeng_probe914_two_routes_real_backwalk_src.py"
                    "（**把 913 落空的证伪重做成功**：**3 对 × 2 轮**，"
                    "每对两条臂**只差「有没有越过去再走回来」** —— "
                    "⚠️ `B` 的 `j` **都越过了**目标终点（`45→36`、`55→46`、`65→56`），"
                    "**都真的往回按了**（1 / 6 / 5 次）**并精确命中**目标"
                    "（35 / 40 / 51）⇒ **6 条 `B` 臂 `design_ok` 全 True**。"
                    "✅ **结果：每对里 A/B 同终点 ⇒ 首次布的下标与全程布序列"
                    "逐条相同**（`0/0`、`11/11`、`12/12`；两轮逐条一致）"
                    "⇒ **910–912 那个「终点与历史共变」的顾虑被排除**。"
                    "⚠️ **但只排除了这一种历史扰动** ⇒ "
                    "**不许**把「起点是终点的纯函数」写成全称规则。"
                    "⚠️ **为什么是 `0/11/12`、分界为什么在 `35|36` 与 `40|41`，"
                    "仍然未查明**。"
                    "✅ **顺带测到**：**反向走是严格 `−1`**"
                    "（`46→45→44→43→42→41→40`、`56→55→54→53→52→51`，"
                    "两轮逐条一致），"
                    "⚠️ 但该区间**不含** `12/68` ⇒ "
                    "**「反向会不会也跳过特殊节点」没测到**。"
                    "✅ **探针自己长了一道防线**：每条 `B` 臂的 `design_ok` "
                    "**同时**要求「正走终点≠目标」「往回次数≥1」「实测终点==目标」，"
                    "任何一条不成立就打**设计违规**标记 ⇒ "
                    "**913 那种错现在会被探针自己叫出来**；"
                    "静态侧还有 `j` 必须越过同对 `A` 的 `assert`")},
        # ══ 批 855：生成历史层（**按名字**找，不是按位置）════════════════
        # 这条 why 原来写「前置态没成立：点**第 2 个** `canvas-panel-launcher`
        # 开出的是『积分明细』」—— 那是**按位置猜名字**。855a 把顶栏 9 个按钮
        # 逐个点了一遍，证明**位置和功能没有对应关系**：
        #   [3] 搜索 28×28 → 320×1084 dialog canvas-feature-panel
        #   [4] **生成历史** 28×28 → 320×211 dialog canvas-feature-panel ← 就是它
        #   [5] 分享 → 400×251 canvas-share-panel-surface
        #   [6] 更多 → 200×84
        #   [7] Credits → 1512×2801
        # ⚠️ 「积分明细」其实是**生成历史层里的一个 tab**
        #   （层内文本实测 `生成历史\n积分明细` / `全部 图片 视频 音频 文本`），
        #   847 点「第 2 个」点进了同一层的另一个 tab，于是认不出层 ⇒ 记成
        #   「前置态没成立」。**不是夹具不具备，也不是源站没这个入口。**
        "topbar-history-menu": {
            "src_tid": "canvas-feature-panel", "src_kind": "dialog",
            "src_identified_by": (
                "testid + **按 aria-label=\\\"生成历史\\\" 找**（不是按位置）"
                " + 矩形 320×211 @[1029,56]（探针 855a/855b）"),
            "takes_focus_at_open": True, "traps_tab": False,
            # False 的原因：开层焦点落在**顶部 tab 按钮**（生成历史/积分明细/
            # 全部/图片/视频/音频/文本）上，实测 4 次 ArrowDown 轨迹**全是同一个
            # 按钮** ⇒ 这一层**没接方向键漫游**，不是「内容只有 1 项」。
            "arrows_move": False, "esc_returns_to_trigger": True,
            # ══ 批 940（源站纯诊断）：把 939 的判决性缺口填上，
            #    并取到第一张**跳层**焦点矩阵。
            #    ⚠️ 本条是**跨层**结论，宿主选 `topbar-history-menu` 只是因为
            #    它是矩阵里唯一一个「开层即接管 **且** 冷启动可达」的层
            #    ⇒ 判据按层 `get(tid)` 能取到本条；**矩阵本身覆盖 5 个层**。
            "src_roving_single_pointer_and_focus_matrix_940": (
                "⭐⭐⭐ **940：939 那个判决性缺口填上了 —— 机制是「单指针」**\n"
                "**（源站纯诊断 `jimeng_probe940_tabindex_rewrite_src.py`，2 轮；"
                "`transitions` / 焦点矩阵 / 计费步号**两轮逐项相同**）**\n"
                "**① ✅ 判决：Tab 游走给**节点本体**写 `tabindex`（939 缺的那一格）**\n"
                "| 量 | 游走前 | 游走后 |\n"
                "| --- | --- | --- |\n"
                "| **节点带 `tabindex`** | **0 / 77** | **76 / 77** |\n"
                "| `tabindex=\"0\"` 的个数 | 2 | **3（只 +1）** |\n"
                "| `tabindex=\"-1\"` 的个数 | 175 | 250 |\n"
                "| 被标记的 26 个的 `tabindex` | — | **`unchanged` 26/26** |\n"
                "⇒ ⭐⭐ **940 的方向是「从『**没有** tabindex』变成 -1」**"
                "（外加当前焦点那一个 0）——\n"
                "⚠️⚠️ **订正 939 的一处归因**（原文一字不删，批注见本条 ③）："
                "**不是**「从 `-1` 改写成 `0`」。\n"
                "⇒ ⭐ `0` **只 +1、不累积** ⇒ 这就是 §130「roving 是**单指针**、"
                "不是留轨迹」的**源站实证**（节点总数逐轮 77/81/80 变，"
                "**比例**稳定在「几乎全部拿到 `tabindex`」）。\n"
                "⇒ ⭐ `unchanged` 26/26 ⇒ **应用只动画布，不动顶栏/侧栏/dock 的元素**。\n"
                "**② ⭐⭐ 第一张**跳层**焦点矩阵**（5 个层，两轮逐项相同）**\n"
                "| 层 | 开层那一瞬间焦点 | 冷启动 Tab 进层 |\n"
                "| --- | --- | --- |\n"
                "| 顶栏·**搜索** `canvas-feature-panel` | **在层内**（ASIDE 本体） | ❌ **`wrapped`（绕一圈未进）** |\n"
                "| 顶栏·**生成历史** `generation-history-panel` | **在层内**（BUTTON） | ✅ **第 1 次** |\n"
                "| **缩放菜单** `canvas-zoom-menu` | **不在层内**（INPUT） | ❌ `wrapped` |\n"
                "| **与 AI 对话侧栏** `canvas-agent-panel` | **不在层内**（ASIDE） | ✅ **第 1 次** |\n"
                "| **画布右键菜单** `canvas-context-menu` | **在层内**（DIV） | ❌ `wrapped` |\n"
                "⇒ ⭐⭐ **「开层即接管焦点」与「冷启动可达」是两件完全独立的事**"
                "（搜索/右键**接管但不可达**、侧栏**不接管但可达**、缩放**两个都不是**）\n"
                "⇒ 与 847d/855b/9772 的既有字段**逐条吻合**"
                "（缩放 `takes_focus_at_open: False`、搜索「面板自己」、"
                "右键 `traps_tab: False`）⇒ **940 又是一次交叉验证**。\n"
                "⇒ ⭐ **侧栏冷启动第 1 次可达**是**新读数**（937 只量过它的开合）。\n"
                "⇒ ⭐⭐ **`wrapped` 比 `capped` 强**：它表示「**落点标记第二次出现**」"
                "＝ 序列走完一圈仍没到 ⇒ **目标不在 Tab 序列里**；"
                "`capped` 只说明「按满预算没到」（§62：那是**没测出来**）。\n"
                "⇒ ⚠️ **939b 那个「150 步 0 命中」其实分不出这两种**"
                "（它没打标记，步末全是 `mark=null` ⇒ 永远不会 `wrapped`）"
                "⇒ **940 把 939 的结论从「0 命中」升级成「`wrapped`（不可达）」**。\n"
                "**③ ⚠️⚠️ 【对 939 的订正批注 —— 939 原文一字未删】**\n"
                "939 的 ⑩ 写「『Tab 游走是否把节点的 `tabindex` 从 `-1` 改写成 `0`』"
                "嫌疑很大，**但 `[C]` 段后没重测那个数**」⇒ **940 测了：方向错了。**\n"
                "实测节点初始是「**根本没有** `tabindex` 属性**」"
                "（`k_nodes_ti: 0/77`），游走后是 -1（绝大多数）"
                "+ **一个** 0 ⇒ **从来不存在「-1 → 0」这个转换**。\n"
                "⚠️⚠️ **939 还有一个归因也要收窄**：「`K=26` 是假集合、造不出 95+ 个落点」"
                "—— **这句不准确**：26 是**真实的初始可聚焦数**"
                "（实测 `[tabindex]` 共 177，其中 175 个是 `-1`，被浏览器规则正确排除）；\n"
                "真正的原因是 **`.react-flow__node` 是 `<div>`、`B939_SEL` 不选 `div` "
                "⇒ 节点**从头到尾没进过那个集合**，"
                "而游走中它们**新获得**了 `tabindex` ⇒ **集合本身在变**。\n"
                "⇒ 这是 §129「918/919 两个数各自都对、只是口径不同」的**同款**，"
                "但**不是**同一个病（918 是「多了一道过滤」，"
                "939 是「**普查对象里根本没有后来才可聚焦的那批**」）。\n"
                "**④ ⚠️⚠️ 阴阳对照门**连改四版都错** —— 本批最值钱的一条纪律**\n"
                "| 版 | 门的形状 | 实测 |\n"
                "| --- | --- | --- |\n"
                "| v1 | 被标记的里「既有变过又有没变过」 | `unchanged` 26/26 ⇒ **必 False** |\n"
                "| v2 | 整体计数里「既有变过又有没变过」 | 4 个计数**全变** ⇒ **必 False** |\n"
                "| v3 | 「计数变了」×「`n_marked_in_node == 0`」 | 实测该数是 **9** ⇒ **必 False** |\n"
                "| v4 | 「计数变了」×「`n_marked_is_node == 0`」 | ✅ **True** |\n"
                "⇒ ⭐⭐⭐ **通用纪律：阴阳对照门的两个答案必须来自**两个不同的集合**。**\n"
                "同一个集合里的两种答案**不构成对照** —— 机制可以让它们**同向**变化，"
                "于是「全变」与「全不变」都会把门判成 False，**而门和读数都没错**。\n"
                "⇒ ⚠️ v3 还踩了一个更细的坑：「**在节点内**」（9 个，是节点里的 button/a）"
                "与「**就是节点本体**」（0 个）是**两件完全不同的事**，我混成了一个数。\n"
                "⇒ ✅ v4 的 `n_marked_is_node == 0` 是**结构保证**的 0"
                "（`B939_SEL` 不选 `div`，而节点本体就是 `div`），**不是碰巧**。\n"
                "**⑤ ⚠️ 探针自己踩的坑（都当场抓到）**\n"
                "· ⭐ **派生键免疫针连抓三次**：`STEP_JS` 7 个键、`REREAD_JS` 的 "
                "`sel_size_after`、`INDEX_JS` 的 `n_marked_in_node` 都被漏登记。"
                "⚠️ 第三次还因为**我只把它从 `DERIVED_KEYS` 删掉、忘了加进 `RAW_KEYS`**。\n"
                "⇒ 顺手发现**静态复核脚本自己也有一个盲区**（与「锚点自查对跨行不报错」同款）："
                "它只认**对象字面量** `key:`，**不认** `out.key = value` 这种**赋值**形式 "
                "⇒ 已补上，两种形式都抓。\n"
                "· ⚠️ **B 段用「新增层**唯一**」当判据是错的**：实测 **3/5 个层新增的是 2 个**"
                "（搜索 = `canvas-feature-panel` + `canvas-search-panel`；"
                "右键 = `canvas-context-menu` + `role:menu`）"
                "⇒ 那 3 个层的目标层全成 `None`、**进层检测整个失效**"
                "⇒ 改用「**开层焦点所在的那个层**」（实测 3/5 都能定出来）才修好。\n"
                "· ⚠️ `rec[\"der_rewrite\"]` **从不被任何键检查**（只有 `walk()` 的 `d` 被查）"
                "⇒ 已补上 `_dchk` 断言。\n"
                "**⑥ ⚠️ 计费入口的 Tab 步号**不是常数**（实测两轮各自稳定）**\n"
                "干净态（无浮层）第 **9** 站 / 右键菜单**开着**时第 **16** 站（939 的读数）\n"
                "⇒ **同一个元素的下标随 DOM 状态变** ⇒ **不许钉绝对步号**"
                "（预算类要求一律用关系式）。\n"
                "⇒ ✅ 本批**只按 `Tab`、零 `click`**（除各开层器那一次）⇒ **未产生计费**。\n"
                "**⑦ ⚠️⚠️ 一条**未解决**的矛盾（如实记，不许调和）**\n"
                "940 实测**搜索层冷启动 `wrapped`（绕一圈未进）**，"
                "而 §146（936）记「层内步 20/轮：输入框 + 全部 76 + 分类按钮 + "
                "15 个结果按钮 + 翻页」⇒ **两者口径可能不同**：\n"
                "936 的 `in_seed` 判据用的是 **`LAYER_SEL` 的 `closest` 形式**，"
                "而 `LAYER_SEL` 含 `[data-testid$=\"-panel\"]` "
                "⇒ **落进 `canvas-feature-panel` 这个宽泛容器的落点都会被算成「层内」**。\n"
                "⇒ **本批没有查清 936 那 20 步是从第几步开始的** ⇒ **不许说 936 错了**，"
                "也不许说 940 推翻了它 —— **留给下一批**。\n"
                "**⑦之二 ⭐⭐ 顺手撞出一个**更老的门禁盲区**（不是 940 引入的）**\n"
                "verifier 的 `strip_comments()` 在审计脚本**第 269 行**就把 "
                "`with open(OUT, \"w\")` 里的 **`\"w\"` 误判成三引号的开头**\n"
                "⇒ 从那儿起**整段被当成字符串吞掉** ⇒ verifier 里 9 处 `acode` 判据\n"
                "数的一直是「**文件里出现几次**」，而不是「**代码里出现几次**」。\n"
                "⇒ **S.6 一直绿只是因为没人往基线文本里写过那个字面量** —— 940 写了，\n"
                "它当场变红（467/468）⇒ **这条门一直在数错的东西**。\n"
                "⇒ 本批的处置：**改述措辞**（零风险、立刻绿）；\n"
                "⚠️ **修 `strip_comments` 的三引号识别留给下一批**（会同时影响那 9 处判据，"
                "**不能在诊断批里顺手改** —— 866 记过「改对一件事、顺手弄坏五件」）。\n"
                "**⑦之二·942 订正 —— 上面这段有**两处过头**，原文一字未删，只在这里订正**\n"
                "① 「9 处 `acode` 判据」是**说错了**：那是 **9 行提到 `acode`、"
                "**3 条**字面量判据**（P.3 那条按层内/层外各一处计数、"
                "S.6 那条要求控件侧与阻塞物侧共用同一个选择器常量、"
                "CCCC.5 那条数基线文本里那个选择器字面量），**不是 9 条判据**。\n"
                "② 「数的一直是「文件里出现几次」，而不是「代码里出现几次」」"
                "**对读数不成立**：这 3 条**数的就是真代码** —— 全文计数与剥后计数"
                "**完全相同**，**答案全对**。「碰巧对」只对**机制**成立："
                "一旦有人往基线文本里写那个字面量（940 / 941 各一次），"
                "同一道判据就变红。⇒ **准确的说法是「门在数一个会被污染的量，"
                "而眼下恰好没被污染」，不是「门一直在数错的东西」。**\n"
                "⚠️⚠️ **而 942 写这段订正时，当场又踩了一次 CCCC.5 那个坑**：\n"
                "第一版订正**原文照抄**了那三条的字面量，于是 P.3 / S.6 / CCCC.5 "
                "**三条一起变红**（472/478）⇒ ⭐ **这不是旧坑复发，是同一个坑"
                "换个身份再来**：上次是「往基线里写被计数的字面量」，"
                "这次是「**往基线里写订正旧坑的说明时，照抄了那个字面量**」。\n"
                "⇒ **纪律**：在本文件里**描述**任何按字面计数的判据时，"
                "**不许原样写出它数的那个字面量**，改用「那条判据」「那个选择器常量」"
                "这类**指代**说法。（这也是 CCCC.5 说的「不该只靠记性」的又一处证据："
                "光有门不够，**写字的人自己也会踩**。）\n"
                "⚠️ **连带订正 942 自己开头的两句过头说法**：\n"
                "· 「剥除器坏了 ⇒ 判据全都在读注释」**也是过头** —— 坏掉时判据读的"
                "是**没剥过的原文**，其中**多数锚文本来就只出现在代码里** ⇒ "
                "**它们一直是对的**（942 普查：56 条锚文里 52 条读代码）。\n"
                "· 「修好之后 9 处判据全部受影响」**也是过头** —— 修好之后**恰好 1 条**"
                "变红（AA.3），其余**逐字未变**。\n"
                "⇒ ⭐ 这也是本批最值钱的一条：**「一个恒真的判据比没有判据更坏」"
                "和「一个恒绿的仪器比没有仪器更坏」是同一件事** —— 两者都长成"
                "「看起来没问题」的样子。942 那道普查门第一版就把 19 条锚文"
                "**误判成合成用例**、让「读注释 0 条」对它们**根本没测**，"
                "是同一道工具自己的 G4 把它拒掉的（又一次当场复发）。\n"
                "**⑦之三 ⚠️⚠️⚠️ 【940 自己的结论正在被 941 证伪 —— 原文一字未删】**\n"
                "复查 940 探针源码，发现它的「进层」判据有个**真缺陷**：\n"
                "`layer_tid` 只取**最近**的那个 `LAYER_SEL` 祖先，而判定写成\n"
                "`st[\"layer_tid\"] === target_layer_tid`（**恰好等于**）。\n"
                "而 `target_layer_tid` 取自**开层焦点**的最近祖先；实测搜索层开层后\n"
                "新增**两个**层（`canvas-feature-panel` + `canvas-search-panel`），\n"
                "开层焦点（ASIDE 本体）的最近祖先是 `canvas-feature-panel` ⇒\n"
                "**而冷启动后落在 `canvas-search-panel` 内部**的输入框 / 分类钮 / 结果钮，\n"
                "它们**最近**的祖先是 `canvas-search-panel` ≠ target\n"
                "⇒ **被判成「没进」⇒ `wrapped=True` 是假阴性。**\n"
                "⇒ ⚠️ 所以 940 第二节矩阵里那三行 `wrapped`（搜索 / 缩放 / 右键）\n"
                "**在 941 出结果之前一律按「未验证」看**（§77）。\n"
                "⇒ ⭐ 顺带**订正 940 的一处措辞错误**（「936 的 `in_seed` 用的是 "
                "`LAYER_SEL` 的 `closest` 形式」**是错的**）：936 源码里 `focus_in_layer` "
                "才是 `LAYER_SEL` 那个，而 `in_seed` 是 `data-b936-seed` **打标记**；\n"
                "936 报的「层内步 20/轮」用的**正是** `in_seed`（精确那个）\n"
                "⇒ **936 与 940 的矛盾不能用「口径宽窄」解释** —— 两个口径都精确，\n"
                "**是 940 的 A 判据本身写错了**。\n"
                "⇒ 941 的正题：同一份游走，**A（最近祖先恰好等于）/ B（`closest` 祖先链**含**它）"
                "/ C（`data-b941-seed` 标记）三判据并排**，\n"
                "并把**完整的 `LAYER_SEL` 祖先链**逐步记下来（不只最近那个）。\n"
                "**⑧ 仍未验证的**\n"
                "· 上述 ⑦ 那条矛盾。\n"
                "· 「游走时 `tabindex` 到底按什么规则被写/被删」"
                "—— §131 量的是**指针臂**事件，本批是**键盘**；"
                "两者的**关系**本批**没有测**。\n"
                "· 源站其余形态的浮层（资产库/项目信息/时间线全屏/视频全屏）"
                "**本批仍未取样**。\n"
                "· **复刻侧与源站在「开层是否接管焦点」上不一致**（源站 3/5 接管、复刻不接管）"
                "⇒ 该不该对齐**没有结论**，是产品决策。") ,
            # ══ 批 941（源站纯诊断 / **自我证伪**）：**940 有一条结论被证伪了** ══
            "src_layer_identity_criterion_941": (
                "⭐⭐⭐ **941：940 矩阵里「搜索层冷启动不可达」是**假阴性** —— "
                "被 941 当场证伪**（探针 `jimeng_probe941_layer_identity_probe_src.py`，"
                "2 轮 × 4 个层，**三判据并排**，`design_ok` 全 True、**两轮逐项相同**）\n"
                "**① ⭐ 本批的正题：同一份游走，三个判据并排**\n"
                "| 判据 | 定义 |\n"
                "| --- | --- |\n"
                "| **A（940 用的）** | `最近 LAYER_SEL 祖先的 testid === target` |\n"
                "| **B（祖先包含）** | `!!el.closest(\'[data-testid=TARGET]\')` |\n"
                "| **C（936 的口径）** | `!!el.closest(\'[data-b941-seed]\')`（打标记） |\n"
                "**A 与 B 的差别就是本批要量的东西**：A 要求「最近祖先**恰好**是它」，"
                "B 只要求「祖先链里**有**它」。\n"
                "**② ✅ 判决（两轮逐项相同）**\n"
                "| 层 | target | A | B | C | A 是假阴性 |\n"
                "| 顶栏·**搜索** | `canvas-feature-panel` | **None** | **1** | **1** | ⭐ **True** |\n"
                "| 画布·**右键菜单** | `canvas-context-menu` | None | None | None | False |\n"
                "| 顶栏·**生成历史** | `generation-history-panel` | 1 | 1 | 1 | False |\n"
                "| **缩放菜单** | `canvas-zoom-menu` | 见本键 ⑥（第一版**漏测**，已补） |\n"
                "⇒ ⭐⭐ **搜索层**冷启动**第 1 次 Tab 就进层**（落点 `tag=INPUT`，"
                "就是那个搜索输入框）\n"
                "⇒ ⭐⭐ **与 §146（936）「层内步 20/轮：输入框 + `全部 76` + 分类按钮 "
                "+ 15 个结果按钮 + 翻页」**完全吻合**\n"
                "（第 1 次就进去、之后 20 步都在层内）\n"
                "⇒ ⇒ **936 与 940 的那条「未解决矛盾」就此消解**，"
                "**不是口径宽窄的问题，是 940 的 A 判据本身写错了**。\n"
                "**③ ⭐⭐ 假阴性的**确切形状**（祖先链读数把它摆得一清二楚）**\n"
                "搜索层第 1 步：`nearest = canvas-search-panel`、"
                "`chain = [canvas-search-panel, canvas-feature-panel]`\n"
                "⇒ 最近祖先是**子层** ⇒ A 不命中；祖先链里**有** target ⇒ B 命中。\n"
                "⇒ ⭐ **「把完整祖先链逐步落盘」是本批能一眼看出问题的原因**"
                "（承 937 的教训：「A 到底是谁」必须进读数，"
                "否则读的人无从发现它测错了对象）。\n"
                "**④ ⚠️⚠️ 根子上的错误在 940 的设计**\n"
                "`target_layer_tid` 取自**开层焦点**的最近祖先 ⇒ "
                "**它假设「一个层只有一个元素」**；\n"
                "而实测搜索层开层后**新增两个**层（`canvas-feature-panel` + "
                "`canvas-search-panel`）⇒ 这个假设**当场不成立**。\n"
                "⇒ ✅ 正确判据是 B（`closest` 祖先链**含** target）。\n"
                "**⑤ ⚠️ 顺带订正 940 的一处措辞错误**\n"
                "940 的基线写「936 的 `in_seed` 判据用的是 `LAYER_SEL` 的 `closest` 形式」"
                "⇒ **错**。936 源码里是**两个分开的**判据：\n"
                "· `focus_in_layer` = `LAYER_SEL` 那个（**宽泛**）\n"
                "· `in_seed` = `!!a.closest(\'[data-b936-seed]\')`（**打标记**）\n"
                "而 936 报的「层内步 20/轮」用的**正是** `in_seed`（精确那个）。\n"
                "⇒ ⚠️⚠️ 940 用「口径宽窄」解释那条矛盾，**方向就错了**。\n"
                "**⑥ ⚠️ 第一版**漏测了缩放菜单**（取样缺口，已补测）**\n"
                "940 报缩放菜单 `wrapped=True`，而第一版 941 的 `TARGETS` 里**没有它** "
                "⇒ 那是一条**没人证伪过**的结论，不许默认它「大概也一样」。\n"
                "⚠️ 缩放菜单与搜索层是**不同的两种结构**：它的开层焦点**不在层内**"
                "（行内百分比 `INPUT`）⇒ 940 的 target 取自「新增层唯一」"
                "（不是「开层焦点所在层」）⇒ **A 判据在这种情形下不一定失效**。\n"
                "⇒ 补测读数见本键末尾的追加批注。\n"
                "**⑦ ⭐ 仪器设计（承 940「门连错四版」的教训，这次先设计对）**\n"
                "· ⭐ `criteria_disagree_ok`：**至少一个层上 A 与 B 给出不同答案**"
                "（实测搜索层满足）—— 若三者处处相同 ⇒ 本批**测不出差别**"
                "⇒ **如实记 `False`，不许调门凑绿**。\n"
                "· ⭐ `positive_control_ok`：带一个 940 报「第 1 次可达」的层"
                "（`generation-history-panel`）当**阳性对照** "
                "⇒ 只有一个判别器时，三判据的读数**都可能是恒真的**。\n"
                "· 实测 `design_ok`：`reps_measured_ok` / `measured_ok` / "
                "`positive_control_ok` / `criteria_disagree_ok` / "
                "`reps_identical_ok` / `yin_yang_ok` **全 True**。\n"
                "**⑧ ⚠️ 仍未验证的**\n"
                "· 源站**其余**形态的浮层（资产库/项目信息/时间线全屏/视频全屏）"
                "**本批仍未取样**。\n"
                "· 940 矩阵里的**「缩放菜单」那行**在补测前**一直是未验证的**"
                "（见 ⑥）—— 这条**取样缺口本身就是本批撞出来的**。\n"
                "· 复刻侧与源站的「开层是否接管焦点」差异**仍未对齐**（产品决策）。\n"
                "· 本批**只证伪了 A 判据**，**没有**去查「层内元素为什么 `tabindex` "
                "那么写」—— 那是 §131（指针臂）那条线的后续。\n"
                "**⑨ ✅ 缩放菜单的补测读数（第二轮补上，2/2 逐项相同）**\n"
                "| 层 | target | A | B | C | 判决 |\n"
                "| **缩放菜单** | `canvas-zoom-menu` | None | **None** | **None** | "
                "**三判据一致为 None ⇒ 真不可达**（步数 106/轮） |\n"
                "⇒ ✅ **940 那条「缩放菜单冷启动不可达」经三判据复核后成立**"
                "（与搜索层不同：缩放**没有子层结构**，A 判据在它身上**没有失效**）。\n"
                "⇒ ⚠️ 但注意：缩放菜单的**开层焦点祖先链是空的** `chain=[]`"
                "（焦点在层**外**的行内百分比 `INPUT`）—— 与 847d 记的 "
                "`takes_focus_at_open: False` **一致**。\n"
                "**⑩ ⚠️⚠️ 三条「不可达」结论的最终账**（本批之后）**\n"
                "| 层 | 940 的说法 | 941 的判决 |\n"
                "| 顶栏·搜索 | `wrapped`（不可达） | ⭐ **证伪 —— 第 1 次可达**（假阴性） |\n"
                "| 画布右键菜单 | `wrapped`（不可达） | ✅ **成立**（三判据一致 None） |\n"
                "| 缩放菜单 | `wrapped`（不可达） | ✅ **成立**（三判据一致 None，补测） |\n"
                "| 顶栏·生成历史 | 第 1 次可达 | ✅ **成立**（A/B/C 全 1） |\n"
                "⇒ ⭐ **两条「不可达」是真的、一条是假的**；而区分它们的"
                "**不是**层本身，是「**该层有没有子层结构**」。\n"
                "**⑪ ⚠️ 本批撞到的一个纯技术坑（留痕）**\n"
                "写基线时把 `[data-testid=\"TARGET\"]` 直接放进 **Python 双引号字符串**里，"
                "那个**双引号**没转义 ⇒ **提前闭合了字符串** ⇒ 整段块语法崩。\n"
                "⇒ ⚠️ 靠**逐行二分删除**才定位到（`ast.parse` 报的行号在**块首**，"
                "离真正的错行很远）—— 又一次「报错位置离病因很远」。\n"
                "⇒ 记法纪律：**嵌在 Python 字符串里的 CSS 选择器，一律写成"

                "不带引号的形式**。") ,
            "src": "jimeng_probe855b_history_kb.py（登录态，视口 1512×1200）"},
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
            "src_context_menu_unreachable_by_tab_939": (
                "⭐⭐⭐ **939：源站右键菜单的键盘可达性**查清了 —— "
                "而 938 那句「等那个问题有答案」的答案是"
                "**「按多少次都到不了」**，不是「要按很多次」**\n"
                "**（源站纯诊断 `jimeng_probe939b_tab_constitution_src.py`，"
                "2 轮 × 150 次冷启动 Tab = **300 步**；"
                "`bucket_counts` **两轮逐字相同**）**\n"
                "**① ✅ 判决：源站右键菜单**不可 Tab 到达**（2/2）**\n"
                "开右键菜单后 150 步冷启动 Tab，**两轮都是 0 次进菜单**；"
                "分桶 `{plain 32, body 2, other_layer:canvas-editor-menu 2, "
                "react_flow_node 114}`，**没有 `target_ctx` 桶**。\n"
                "⇒ 936 那句「60 次一步都没进去」**方向是对的**，只是它"
                "**不知道历史早就取过样**（§四 9772 行：源站**探到 45 次仍未进**）。\n"
                "**② ⚠️⚠️ 订正 §148 待办第 4 条 —— 它的**前提**是错的**\n"
                "§148 写「源站右键菜单的键盘可达性**未解释**」⇒ "
                "**已被取样两轮**：9772（源站，45 次未进）＋ 939b（源站，300 步 0 进）。\n"
                "⚠️ 更要紧的是 10272 行那句「**真要解，得问源站冷启动同样要按几次**」"
                "**本身就问错了** —— 源站的答案不是「次数多」，是"
                "**「无论按几次都到不了」** ⇒ 那个开放项**不是一个待测的数**，"
                "是一个**已经测完的事实**。\n"
                "**③ ⭐ 机制：开菜单后 `role=menuitem` 从 0 → 13，"
                "而 300 步 0 命中**\n"
                "⇒ 那 13 个菜单项**压根不在 Tab 序列里**"
                "（`role=menuitem` 的 `<div>` 没有 `tabindex`）\n"
                "⇒ **源站的键盘可达性完全依赖「开层即接管焦点」**"
                "（939b 实测开层后 `in_target=True`，2/2；9772 记的是"
                "焦点给到**第一项「新建节点」**）\n"
                "⇒ **一旦焦点离开（`blur` 或冷启动），就再也回不去。**\n"
                "**④ ⭐⭐ 顺带把「源站 / 复刻」两侧一直混着的读数分清了**\n"
                "| | 开层那一瞬间焦点 | 冷启动 Tab 进层 |\n"
                "| --- | --- | --- |\n"
                "| **源站** `canvas-context-menu` | **第一项「新建节点」** | **进不去**（45 次 / 300 步） |\n"
                "| **复刻** `canvas-context-menu` | **body**（压根没接管） | **进得去**（27 步 / 25 步） |\n"
                "⚠️ §67 那句「34/37/39/49 次」是**复刻侧**的 ⇒ "
                "**四方读数（源站 45、源站 300 步、复刻 27、复刻 25）彼此不矛盾**；\n"
                "⚠️ **矛盾的是 936 / §148 把源站和复刻当成了同一侧。**\n"
                "**⑤ ⚠️ 实测撞到计费入口：它在 Tab 序列的第 16 站**\n"
                "第 16 站落点 `cls='justify-center gap-1 whitespace-no'`、"
                "`txt='805\\n基础会员'`（即 `canvas-commerce-entry`），**两轮逐字相同**。\n"
                "⚠️ 本批**只按 `Tab`、一次 `click` 都没有** ⇒ **未产生任何计费**；\n"
                "⚠️⚠️ 但这暴露一条边界：937/938 的 `FORBIDDEN_TIDS` 守卫"
                "**只拦 `mouse.click`、不拦焦点** ⇒ 「绝不点计费入口」这条纪律"
                "**拦不住键盘把焦点送上去** ⇒ 键盘可达性本身**就是**一条风险面。\n"
                "**⑥ ⚠️ 源站的 Tab 周期**不是常数**（而 §930 的 101 是复刻侧 2/2 稳定）**\n"
                "`canvas-editor-menu` 两次落点的间隔：**101 / 104**（两轮不同）\n"
                "⇒ 源站画布在游走过程中有动态增删（节点数也是 77 / 76 两轮不同）\n"
                "⇒ **「一圈 = 101」不能搬到源站**（它是复刻侧的读数）。\n"
                "**⑦ ⚠️⚠️ 939 第一版整个作废**"
                "（`jimeng_probe939_tab_distance_src.py`，留痕不删）\n"
                "· 它报源站 Tab 候选元素 **K = 26**，而 939b 实测**不过滤是 203/219**、\n"
                "  **从落盘轨迹重算的「不同落点元素数」是 95 / 100**\n"
                "  ⇒ **26 造不出 95+ 个落点** ⇒ 那个 K 是**假集合**。\n"
                "· 连带作废：`d_measured` 全 `null`（菜单项不在假集合里）、"
                "  `model=roving`（在假集合上比出来的）、`yin_yang_ok=false`。\n"
                "· ⭐ **病根与 §129 记的 918/919 是同一款**：「多了一道过滤器」"
                "  （918 报 10、919 报 163，**两个数各自都对、只是口径不同**）。\n"
                "  ⚠️ 但**这次不能照抄「各自都对」**：26 与轨迹**互相矛盾**，"
                "  ⇒ 这一侧**不成立**。\n"
                "· ⚠️⚠️ 而且它的 `reps_identical_ok=True` 是**空门** —— "
                "  比对的是 `distance_by_start`（五个值**全是 `null`**）"
                "  ⇒ 「全 null 相同」**恒为真**；而真正不一致的 `seq_repeats`"
                "  **102 vs 104 就在旁边，门没看这个字段**。\n"
                "  ⇒ 与 937 的 `a_survived` 恒真**同类**（**一个恒真的字段比没有字段更坏**），"
                "  **第四次**复发，形态更隐蔽：**门比对了错误的字段集合**。\n"
                "**⑧ ⚠️ 939b 自己也有一个恒真字段（第四次复发的另一个形态）**\n"
                "`covers_all_landings` 判据里我写了 "
                "`role in (\"menuitem\", \"button\", \"link\")` 就当「尺子能覆盖」"
                "⇒ 而 `B939_SEL` **根本不选 `[role=menuitem]`** ⇒ **自己给自己开了后门**，"
                "实测两轮都报 `true` 却**毫无信息量** ⇒ 已如实记为不可用字段。\n"
                "**⑨ ✅ 一条顺带钉死的**：`document.body` 那一站在**第 7 步**，2/2\n"
                "（与 §930/933/935 记的「`document.body` 那一站」是同一站）。\n"
                "**⑩ ⚠️⚠️ 判决性缺口（留给 940，本批**没有测**）**\n"
                "`[A]` 段（游走**前**）测到 `[tabindex]` 共 **178** 个，"
                "而**实测 100 步落点带 `tabindex=\"0\"`**、"
                "且 `n_nodes_tabindexed=0`（**节点本体** 0 个）\n"
                "⇒ 「**Tab 游走是否把节点的 `tabindex` 从 `-1` 改写成 `0`**」"
                "嫌疑很大，**但 `[C]` 段之后本批没有重测那个数**\n"
                "⇒ **两次读数不足以定机制**（§77）⇒ 940 第一件事就是补它。\n"
                "**⑪ ⚠️ §130/§131 的归属**未查明**（原文没写跑在源站还是复刻）**\n"
                "它们记的是「节点本体 1×`'0'` + 75×`'-1'`」，本批记的是"
                "「**节点本体 0 个**」⇒ **不能直接比较**；\n"
                "何况 §131 的触发条件是**指针臂事件**，而本批**全程没动过指针**\n"
                "⇒ 两者**不构成矛盾，也互不印证**（§77）。\n"
                "**⑫ 仍未验证的**\n"
                "· 「Tab 游走是否重写 `tabindex`」—— 见 ⑩。\n"
                "· **源站其余浮层的键盘可达性**本批**只测了右键菜单一个**。\n"
                "· **复刻与源站在「开层是否接管焦点」上不一致**"
                "（源站接管 / 复刻不接管）⇒ 该不该对齐**没有结论**，"
                "得先在源站上把各层**逐层**取样（940）。\n"
                "· 复刻的 `contextMenu` / `paneMenu` 仍未接进槽位 —— "
                "**939 给出了 938 当时等的那条答案**（见 ②），"
                "但「该不该接」是**产品决策**，不是读数能定的。\n"
                "**⑬ ⭐ 交叉验证：本条与 846/847d 的既有基线字段**完全自洽****\n"
                "`canvas-context-menu` 那条早就有 "
                "`takes_focus_at_open: True, traps_tab: False`\n"
                "⇒ 939 **没有推翻任何既有字段**，只是**补上了机制**。\n"
                "⚠️ 顺带指出既有字段的一个**分辨力缺口**：`traps_tab: False` "
                "**分不清「不困」与「压根进不去」**（两者都表现为「不困」）\n"
                "⇒ **939 补的正是这一刀**：源站右键菜单是后者。\n"
                "**⑭ ⚠️⚠️ 顺手撞出一个**结构缺陷**（不是 939 引入的）**\n"
                "`SOURCE_BASELINE` 顶层 17 键 = **层 testid**，而 "
                "**900–939 这 41 个批次结论键全部挂在 `audio-voice-filter-listbox` "
                "条目下面** —— 那是 900 批起的**既有挂载惯例**。\n"
                "⇒ 后果：`SOURCE_BASELINE.get(tid)`（审计按层查）"
                "**按层取不到这 41 条**；且它们**污染**了音色筛选下拉那个条目。\n"
                "⇒ 本条已**移进 `canvas-context-menu` 条目**（语义正确的宿主）；\n"
                "⚠️ **其余 40 条不动**（纯大改已提交内容、零语义收益），"
                "**整体错位留给下一批**处理。\n"
                "**⑭之二 ⚠️ 942 差点让上面「顶层 17 键 = 层 testid」"
                "**当场失效**（原文一字未删）**\n"
                "942 第一版把自己的工具侧读数当成了第 18 个**顶层键**放进来，"
                "而 H.1/H.2 逐条查「每个顶层键都有源站字段与取样出处」"
                "⇒ **两条当场变红**（472/478）。\n"
                "⇒ 处置：那个键**移出去了**，改放 `TOOLING_BASELINE`"
                "（**工具侧**读数，不是任何一层的源站读数）"
                "⇒ 顶层**仍然 17 键、仍然全是层 testid**，上面那句**继续成立**。\n"
                "⇒ ⭐ 但「顶层键都该是层」这个**性质本身**经不起一根非层键："
                "**下一批处理那 40 个错位键时，别拿它当前提**，"
                "也别再往这张表里塞**不同域**的数据。") ,
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
    # ⚠️⚠️ 942：**这一批的读数故意不放进 `SOURCE_BASELINE`** ——**这一条不是层的读数**，是关于我们自己门禁的读数 ══════
# ⚠️ 那张表是「**源站**基线表」，H.1/H.2 逐条查它每个顶层键都有
#   源站字段与取样出处；把**工具侧**读数塞进去，H.1/H.2 当场变红
#   （942 第一版真塞过 ⇒ 472/478）。⇒ ⭐ **别把不同域的数据塞进同一张表**：
#   「顶层键都该是层 testid」这个性质会悄悄失效，939 那条结构缺陷的
#   订正批注（§⑭之二）也正是这么写的。
#
# 内容：把 verifier 里**打在 `strip_comments()` 派生变量上的锚文**逐条
# 分类，看它读的是**代码**还是**注释**。
# 由来：942 修掉了 `strip_comments` 的一个**真 bug**（三引号识别的第一个
# 条件只查「第 1 个 == 第 3 个」、漏了第 2 个 ⇒ `with open(OUT, "w")` 的
# 双引号当场触发三引号模式、整段被吞）。修好之后全套判据里**恰好一条变红**：
# AA.3 —— 它钉的「不** `stopPropagation()`」这句话**只存在于源码注释里**，
# 而剥除器坏掉时 `.tsx` 的注释**根本没被剥** ⇒ 那句注释只要还在就绿，
# **就算有人真往 Clear 的 Esc 分支加上 `stopPropagation()` 也照样绿**。
#
# ⚠️ 下面的计数是**一次读数、会被正常演进改写**，而且有个**循环**：
#   **写一条打在派生变量上的判据，普查总数就会 +1** —— DDDD.3 自己
#   加了 `count(那个符号) == 1` 这条锚文，普查就从 56 变成 57。
#   （942 一开始把总数按「AA.3 修完是 56」写死，下一条判据就把它
#   推翻了 —— 又一次「钉实测常量」的现场教学。）
# ⇒ **一处只钉一件事**：这里**记录**这次读数（连同「读代码的必须是多数」
#   这条关系），**门**在 `scripts/jimeng_check_comment_anchors.py` 的
#   G2（占比 ≥ 85%）与 G3（读注释必须是 0），**不在**判据里钉死计数。
    TOOLING_BASELINE = {
    # ⚠️ 它**故意不叫任何 `data-testid`**：审计按层 `SOURCE_BASELINE.get(tid)`
    #   取数据，顶层多一个非层键不会污染任何一层（`LAYER_SEL` 只匹配真 testid）。
    #   放这里只因为一条纪律：**基线是唯一可机读来源**（verifier 不读 README）。
    #
    # 内容：把 verifier 里**打在 `strip_comments()` 派生变量上的锚文**逐条
    # 分类，看它读的是**代码**还是**注释**。
    # 由来：942 修掉了 `strip_comments` 的一个**真 bug**（三引号识别的第一个
    # 条件只查「第 1 个 == 第 3 个」、漏了第 2 个 ⇒ `with open(OUT, "w")` 的
    # 双引号当场触发三引号模式、整段被吞）。修好之后全套判据里**恰好一条变红**：
    # AA.3 —— 它钉的「不** `stopPropagation()`」这句话**只存在于源码注释里**，
    # 而剥除器坏掉时 `.tsx` 的注释**根本没被剥** ⇒ 那句注释只要还在就绿，
    # **就算有人真往 Clear 的 Esc 分支加上 `stopPropagation()` 也照样绿**。
    #
    # ⚠️ 下面的计数是**一次读数、会被正常演进改写**，而且有个**循环**：
    #   **写一条打在派生变量上的判据，普查总数就会 +1** —— DDDD.3 自己
    #   加了 `_agp2.count("stopPropagation") == 1` 这条锚文，普查就从
    #   56 变成 57。（942 一开始把总数按「AA.3 修完是 56」写死，
    #   下一条判据就把它推翻了 —— 又一次「钉实测常量」的现场教学。）
    # ⇒ **一处只钉一件事**：基线**记录**这次读数（连同「读代码的必须是多数」
    #   这条关系），**门**在 `scripts/jimeng_check_comment_anchors.py` 的
    #   G2（占比 ≥ 85%）与 G3（读注释必须是 0），**不在**判据里钉死计数。
    "jimeng_942_anchor_census": {
        "anchors": 57,
        "code": 53,
        "comment_only": 0,
        "synth": 4,
        "absent_both": 0,
        "census_nonempty": True,
        "code_is_majority": True,
        "strip_bug_fixed": True,
        "aa3_rewritten_to_code_form": True,
        "aa3_positive_control_mutants": 8,
        "aa3_positive_control_all_rejected": True,
        "census_gate_itself_falsified": True,
        "tool_path": "scripts/jimeng_check_comment_anchors.py",
        "note": (
            "57 = 53 读代码 + 4 合成用例（_sc_out，剥除器自测）；"
            "0 读注释 ⇒ 修好剥除器的爆炸半径恰好 1 条判据（AA.3）。"
            "⚠️ 不钉**「恰好 52/56」**这类计数：写一条打在派生变量上的判据"
            "总数就 +1（DDDD.3 就 +1 过），钉死必然假红。"
            "aa3_positive_control 的 8 个变异含**空洞写法**（"
            "全文件从不调 stopPropagation）—— 只看否定判据必被它白送。"
            "census_gate_itself_falsified：把旧版 AA.3 那条锚文塞回副本，"
            "comment_only 从 0 变 1 ⇒ 这道门**不是恒绿的**。"
        ),
    },
    }
    # ══ 批 943：**画布表面**的读数（不属于任何一层，也不属于工具侧）══════
    # ⚠️ 为什么**第三张表**：H.1/H.2 要求 `SOURCE_BASELINE` 的**每个顶层键**
    #   都带 `src` / `src_tid` + 三个焦点字段，而 943 测的是
    #   「**点节点 / 按 Tab` 时应用怎么写节点的 `tabindex`**」——
    #   **它不属于任何一个浮层**，塞进层表会让 H.1/H.2 当场变红（942 塞过，红了）。
    # ⭐ 而这**正是 939 撞出的那个结构缺陷的根因**：900–938 那 40 个批次键
    #   **没有画布级的家**，只好挂在 `audio-voice-filter-listbox` 下面
    #   ⇒ 「顶层键都该是层 testid」这个性质一旦被破，就再也塞不回去了。
    #   ⇒ **给画布表面一张正经的表**，下一批搬那 40 条时才有地方放。
    CANVAS_BASELINE = {
        "canvas_surface": {
            # ── ⭐⭐⭐ 本批的判决：**两条臂不是同一条规则** ──────────────
            # 取样：探针 943，源站，登录态，视口 1512×1200，
            # **2 轮 × 22 条判决步逐条逐字相同**、**六道设计门 2/2 全 True**。
            #
            # 先更正一个**前提错误**（942 的待办原文，一字未删）：
            # §131（批 921）的臂事件用的是 `keyboard.press("Tab")`，
            # §136（923/926）也是按 `Tab`/`Shift+Tab`
            # ⇒ **§131 与 940 测的是同一条键盘臂**，「两臂关系未测」立不住；
            #    真正**从来没测过**的是**鼠标臂**（点节点）。
            #
            # **键盘臂**（逐条复现 §131 921，2/2）：
            #   每次咬到 ⇒ removed＝上一个臂事件、added＝上上个、changed＝本次
            #   ⇒ **「不带 `tabindex` 的节点数」恒为 1**
            # **鼠标臂**（5/5 咬到，2/2）：
            #   removed＝上一个被布 `'0'` 的节点、**added 恒空**、changed＝本次
            #   ⇒ **「不带 `tabindex` 的节点数」每咬一次 +1**（1→2→3→4→5→6）
            # ⇒ ⚠️ **鼠标臂单独跑会破坏 §131 那条不变式**。
            "mouse_arm_added_always_empty": True,
            "mouse_arm_without_ti_grows_monotonic": True,
            "keyboard_arm_without_ti_always_one": True,
            "keyboard_arm_reproduces_131": True,
            # ── ⭐⭐ `removed` **不分臂**：窗口是**全局**的 ──────────────
            # 第一次鼠标点击的 `removed` 正是**键盘臂**最后布的那个下标
            # （键盘臂最后一步 `changed=[8,'-1','0']`，紧接着点 i=0 得
            # `removed=[8]`）⇒ 鼠标臂**接着键盘臂的历史走**，不是另起一套。
            "removed_is_cross_arm": True,
            # ── ⭐⭐⭐ **补偿只在键盘臂上** ────────────────────────────
            # 鼠标臂连点之后，键盘臂的**第一击**把**两臂删掉的全部**一次性写回：
            # `added` 里同时有鼠标臂删的与键盘臂自己早先删的
            # ⇒ 「不带 ti」**一次性**从 6 回到 1，**不变式被恢复**；
            # 之后键盘臂立刻回到 §131 的老样子。
            # ⇒ 复刻侧若用同一套逻辑处理点击，就会**漏掉这半边补偿**。
            # ⚠️ 两条合起来才是完整判决：它们是**同一条窗口、**不同**的补偿**
            # —— 只说其中一半都会读错（只说「不同」会以为各管各的，
            # 只说「同一条」会以为点击也会写回）。
            "keyboard_first_tab_after_mouse_recovers_all": True,
            "two_reps_identical": True,
            "design_gates_all_true": True,
            "src": "jimeng_probe943_arm_relation_src.py（登录态 1512×1200）",
            "src_tid": "canvas-surface（非浮层）",
            # ── ⚠️⚠️ 未查的一律标未查，不许补机制 ──────────────────────
            "removed_scope_unverified": (
                "只验到「`removed` 追上一个被布 `'0'` 的节点」；"
                "**方向**（反向臂是不是同一条）本批**没测**"
                "（§136 923 在键盘臂内部验过，鼠标臂方向**未测**）。"),
            "without_ti_growth_cap_unverified": (
                "连点 5 次看到 1→6 **单调增长**，**上限未测**"
                "（可能是「删满就不再删」，也可能一路涨到节点总数 —— **未测**）。"),
            "identity_settling_unexplained": (
                "初始化那一击之后，节点身份串还要 **4 下**臂事件才稳定"
                "（2/2 都是 4 下，但每下变几个下标**逐轮不同**）"
                "⇒ **成因未查明**（怀疑是 React Flow 视口虚拟化，"
                "**只是怀疑**）。⚠️ 这也是本批**唯一**必须靠「等稳定」"
                "才能取到判决读数的地方。"),
            # ── 批 944：把上面两条「未测」各推进一步（三版探针，详见 §154）──
            # ⚠️⚠️ **944 的三版设计门都有红项 ⇒ 本批不产出新的机制结论**，
            #    只产出下面这些**逐条可复现的局部读数**（都是「点前 pre、
            #    点后 post」的当场比较，2/2 逐条相同）。
            "inner_scan_944a": (
                "**纯读发现**（探针 944a，零点击，2/2 逐字相同）：节点 76 个，"
                "内部元素直方图 PATH 651 / SPAN 411 / DIV 410 / SVG 237 / G 156 / "
                "**BUTTON 85** / P 1 / IMG 1 / INPUT 1；"
                "**可点的内部落点 94 个**，其中 BUTTON **只有 3 个**"
                "（85 个 BUTTON 大多在**选中后才出现**的节点工具条上），"
                "**带删除/移除语义的 0 个**。⇒ ⭐ 这就是为什么 944 要先花一个"
                "纯读探针：在源站上真删掉别人的东西、并且让后面所有读数作废，"
                "代价太高。"),
            "node_ids_are_stable_944a": (
                "节点有**稳定 id**：`data-testid` 形如 `rf__node-node_236ctpehgg`，"
                "配 `aria-label` 形如「视频 node: 视频 1」⇒ "
                "**跨状态认元素有正经的锚**（比「按 className 认」可靠，943 栽过）。"),
            "body_click_monotone_944b": (
                "**点节点本体**：2 轮各 13 次成功点击，`added` **恒空**、"
                "`removed` = 上一个被布的下标、**「不带 ti」严格单调 +1**"
                "（1→14），**全程没有平台期**；节点数全程 76（**没删任何东西**）。"
                "⇒ 943 那条「鼠标臂只删不写回」在更大样本上**逐条复现**。"),
            "inner_button_not_an_arm_event_944b": (
                "⭐⭐ **点节点内部的 BUTTON 不是臂事件**：三元组**全空**"
                "（`bit=False`），**而且开了 1 个层**（层 1→2）、节点数不变"
                "（2/2；实测文案「添加素材到时间线」，在视频节点上）"
                "⇒ ⭐ **内部控件走它自己的 handler，完全不碰 `tabindex` 窗口** —— "
                "这是 943「内部控件未测」那条的确切答案。"),
            "already_selected_not_an_arm_event_944b": (
                "⭐⭐ **点「已经选中」的同一个节点不是臂事件**：第一次点 `bit=True`、"
                "**紧接着再点一次 `bit=False` 且三元组全空**（2/2，i=0）"
                "⇒ 鼠标臂**要求「这一下改变了选中态」**才咬。"
                "⚠️ 它的**反向**（点未选中的节点是不是每次都咬）"
                "**本批没测到**（S 臂第二对 `bit=False`，状态已被前一对比带跑）"
                "⇒ **不许拿这一条去推**「点未选中必然咬」。"),
            # ── ⚠️⚠️ 一条**必须撤回**的假读数 ──────────────────────────
            "retracted_v1_compensation_944b": (
                "⚠️⚠️ **944 v1 写下过「补偿没来」（连按 6 下 Tab、`added` 恒 0）"
                "—— 这条已撤回**：它的 `is_arm` 判据**太松**（只问「焦点在不在"
                "某个节点**内**」），而实测 `active_tag=BUTTON` 说明焦点落在"
                "节点**内部的按钮**上 ⇒ 那是**死按压**（指针根本没推进）"
                "⇒ ⭐ **「应用没写回」与「这一击压根不是臂事件」必须分开**，"
                "v1 把前者当成了后者（又一次「把『够不着』写成『没有』」）。"),
            # ── ⚠️⚠️ 一条**两轮不一致**、因此**不许下结论**的 ────────────
            # ⚠️⚠️ 948 改名：矛盾**已结案**（是个误读），但**成因仍未查明**的是
            #    「944 自己那次为什么不补」—— 两者**必须分开记**（承 HH.4：
            #    判据要跟上事实，但**不许**因为矛盾解开就把待查项一起删掉）。
            "compensation_scale_threshold_RESOLVED_944b_948": (
                "⚠️ **这条 944 当时下的「不许下结论」仍然成立**（一字未删）："
                "rep1 连点 **7** 次之后第 1 下 Tab `added=7`、`不带 ti 14→1`；"
                "rep2 连点 **13** 次之后**连按 6 下** `added` 恒 **0**、"
                "`不带 ti` 恒 **14**。\n"
                "⇒ **两轮不一致**，所以**不许**下结论 ⇒ "
                "**不许**写成「补偿有规模阈值」，**不许**说 943 的读数被推翻。\n"
                "✅⭐⭐⭐⭐⭐ **948 结案（受控，2/2）：那条矛盾是一个误读。**\n"
                "  · 945 已排除**规模**、**那一击是不是臂事件**；947 已排除"
                "**连点期间身份在不在动**\n"
                "  · 948 **受控**地让 settle 落在 **76 / 0 / 1** 三个点上"
                "（`n_settle ∈ {0,1,2}`、别的全固定、逐格 2/2 逐条相同）：\n"
                "    就绪 **1** 那一格（= 944 那个值）补偿**照常**"
                "（第 1 击 `added=5`、`5→1`）⇒ **分界是 76 vs {0,1}**\n"
                "  · 唯一异常的是就绪 **76** 那一格，而 946 的 **sham**（零点击）"
                "已经证明刚 boot 完第 1 击 `Tab` 就是 `76 → 0`\n"
                "⇒ ⇒ **944 把「冷启动铺窗口」读成了「补偿没来」——矛盾根本不存在。**\n"
                "⚠️⚠️ **但下面这一条在 948 当时仍未查明，别以为一起解开了**："
                "**944 自己那次**（就绪 1、13 连点、连按 6 下 `added` 恒 0）"
                "**948 没有解释** —— 按 948 的落点，按 2 下就停在 1 ⇒ "
                "**它的前置态与 948 的 `n_settle=2` 那一格是同一个值**，"
                "而那一格补偿照常 ⇒ **那次不补另有原因**"
                "（944 自己的 `cell_ok` 不满足；身份不稳那一段的读数按 946 "
                "**一律不作数**）⇒ 948 当时记的是**成因仍未查明**。\n"
                "✅⭐⭐⭐ **949 把这一条降级为「不可复现」**（见 `replay944_949`）："
                "用 **944 自己那组数字**（就绪 1、`scale=13`、连按 6 下）重跑，"
                "**2/2 逐条相同**地测到第 1 击 `added=10`、`10→1`、"
                "其余 5 击**每击 `added=1`** ⇒ **`reproduced_944 = False`**\n"
                "⇒ ⇒ **944 那次读数不是机制的性质**；"
                "结合「就绪 = 1 是瞬态」⇒ **944 测的是一段身份还在动的瞬态**。\n"
                "⚠️ **但「944 当时到底发生了什么」仍然不可知** —— "
                "本树**没有**在源站上复现出 944 那个不稳定的前置态 ⇒ "
                "**不许**写成「已查明」，只写「**不可复现**」+「**那一侧是瞬态**」"
                "两条并列。"),
            # ── 批 945：把 943/944 之间那个分歧**拆成两个自变量** ─────────
            # 2 轮 × 4 格（scale ∈ {2,6,12} × mode ∈ {body, asis}），
            # **每格独立 `boot()`**，逐格读数 **2/2 逐条相同**。
            "comp_scale_is_not_the_cause_945": (
                "✅⭐⭐ **规模不是主因**：连点 **12** 次（实际咬到 **8** 次）之后，"
                "键盘臂的**第一击** `added=8`、`不带 ti 8→1` —— **一次性补完**"
                "（`scale=6` 那一格是 `added=2`、`2→1`，同理）；"
                "第二击通常 `added=1`、`1→1`（补偿只在第一击发生）。"
                "⇒ **944 记的「13 次连点后连按 6 下 `added` 恒 0」不是规模阈值** —— "
                "本批在 12 次这一侧 2/2 补回。"),
            "not_an_arm_event_hypothesis_refuted_945": (
                "✅⭐⭐⭐ **944 的另一半假设被读数直接推翻**："
                "`mode=asis`（**不干预焦点**、就按点击留下的样子）那一格，"
                "**按 Tab 之前焦点仍然是 `DIV` 且在节点内**"
                "⇒ ⭐ **点击之后焦点本来就在节点本体上**。"
                "⇒ 所以 944 那次 `active_tag=BUTTON` **不是点击造成的**，"
                "而是**那 6 下 Tab 自己一路 Tab 进**了节点内部的按钮"
                "⇒ 「那一击压根不是臂事件」这个解释**不成立**。"),
            "comp_refuted_reading_third_variable_945": (
                "⚠️⚠️⚠️ **但 944 那次「不补」的成因仍然未查明**，而且本批"
                "**没有对照真正的可疑变量**：本批每格 settle 只按 **1** 下、"
                "`就绪不带 ti = 0`（初始化刚发生、指针还没推进）；"
                "而 944 settle 了 **10** 下、`就绪不带 ti = 1`（指针已经走过）。"
                "⇒ 剩下没被拆开的自变量是**前置态**（settle 多少下 / "
                "`不带 ti` 停在 0 还是 1）"
                "⇒ ⭐ **你以为只有两个，其实有三个** —— 拆自变量只拆了一层。"
                "⇒ **不许**把 944 那次读数记成「偶发」或「有别的条件」，"
                "**成因未查明**。"),
            "cell_ok_false_and_why_945": (
                "⚠️ `cell_ok` **2/2 全 False**：它的判据是"
                "「点击次数 == 咬到次数」，而实测 12 次那一格是"
                "**9 次点得到、8 次咬到**（`重求可点位置失败` 一次）"
                "⇒ 这一版画布节点**大量重叠**、全表只有 15–17 个点得到。"
                "⇒ ⚠️ 按纪律**这一批不产出机制结论**，上面三条是"
                "**逐格 2/2 相同的局部读数**，不是结案。"),
            "recovered_is_two_state_edge_945": (
                "⚠️ 探针的 `recovered` 是**两态**判据（「连点后 > 1 且连按后 == 1」），"
                "在 `scale=2` 那一格判成 `False`，**但那是定义边界不是现象**："
                "那一格连点后 `不带 ti` 本来就 **== 1**（只咬到 1 次、"
                "没破坏不变式）⇒ 正确读法是三态的 **「没破坏、无需补回」**。"
                "⇒ ⭐ **不许**把那格的 `False` 读成「没补回」。"),
            "unselected_node_always_bites_945": (
                "⭐ **944 的 S 臂反向由此答掉**（945 只是**引用**、没另设臂）："
                "944 的 L 臂连点 **13 个不同下标**、每次都是一次臂事件（`bit=True`）"
                "⇒ **「点未选中的节点必然咬」**在「本体落点、13 个不同下标」"
                "这个范围内 **2/2 成立**；与之成对的是 944 那条"
                "**「点已选中的同一节点不咬」** ⇒ ⭐ "
                "**鼠标臂要求「这一下改变了选中态」才咬**（两侧各 2/2）"
                "⇒ ⇒ 复刻侧判「这一击是不是臂事件」时，"
                "**先问「选中态变没变**，别只看落点在哪。"),
            "mouse_click_on_inner_control_unverified": (
                "本批 5 次咬到的落点都是节点**本体**（`DIV` 4 次 / `PATH` 1 次）；"
                "点节点**内部控件**（按钮/输入框）是不是同一条规则**未测**。"),
        },
        "prestate_946": {
            # ── 批 946：拆**第三个**自变量「前置态」—— ⚠️ 含**一道撤回** ──
            # 取样：探针 946，源站，登录态，视口 1512×1200，
            # 2 轮 × 5 格（`warm ∈ {0,1,2,6}` + 1 个 **sham** 格 `scale=0`），
            # **每格独立 `boot()`**；五段 JS 逐字 assert 与 945 相同。
            # ⚠️ **本批不产出机制结论**（`cell_ok` 4/5 为 False、
            # **有一格两轮不一致**）—— 下面是 2/2 局部读数 + 撤回。
            "warm_never_manipulated_946": (
                "⚠️⚠️⚠️ **本批的设计有一处真缺陷，如实记账**：`warm ∈ {0,1,2,6}` "
                "**全都 ≤ boot 之后的自然值 76** ⇒ 预热循环**一次都没进**"
                "（实测 `warm_presses = 0`、10 个格次全同）"
                "⇒ ⭐ **`warm` 这个自变量从头到尾没有被操控过**"
                "⇒ 相应地 **`warm_reached` 是恒真的**（自然值就 ≥ 任何目标）"
                "⇒ ⭐ **「一个恒真的判据比没有判据更坏」（942）**"
                "⇒ **撤回这道门**：`warm_reached=True` 不许算作「操纵成功」。"),
            "sham_refutes_first_tab_means_compensation_946": (
                "⭐⭐⭐⭐ **sham 格（`scale=0`、**零点击**）推翻了一个隐含前提**："
                "刚 `boot()` 完就按第 1 下 `Tab`，「不带 ti」**76 → 0**、"
                "第 2 下 `0 → 1`、第 3 下 `1 → 1`（2/2 逐条相同）"
                "⇒ ⭐⭐⭐ **「第一击 Tab 把「不带 ti」大幅压下去」根本不需要连点来解释**"
                "—— 那是**冷启动之后第一下 Tab 本身**的行为"
                "⇒ ⇒ **不许**把「第一击 `Tab` 之后 `不带 ti` 变小了」当成"
                "**补偿已经发生**的证据；sham 就是专为证伪这件事而设计的。"),
            "front_state_is_real_and_huge_946": (
                "⭐⭐⭐ **「前置态」这个变量是真的、而且落差极大**（虽然**不是**按设计"
                "操控出来的，是 boot 的自然状态替我们动了它）："
                "**刚 boot 完 = 76（76 个节点全都没有 `tabindex`）**；"
                "而 945 在预热里**按了 1 下 `Tab`** 之后 = **0**"
                "⇒ 同一段连点代码（`scale=8`）跑在 **76** 与 **0** 两种前置态上，"
                "读数**不可比** ⇒ ⚠️ 945 与 946 的读数**必须分开记**，"
                "**不许**当成同一个实验的两批数据。"),
            "944_contradiction_reproduced_946": (
                "⭐⭐⭐⭐⭐ **944 那个矛盾在 946 原样重现**：格 0 **两轮不一致** —— "
                "rep1 第 1 击 `Tab` 把「不带 ti」**75 → 1**（压回 1）、"
                "rep2 **75 → 8**（**停在 8、不补**），"
                "而**这两轮跑的是同一段代码**（`warm` 没起作用 ⇒ 唯一变量都没动）"
                "⇒ ⇒ **成因不在 `warm`、也不在 `scale`、也不在 `mode`**"
                "（945 已把后两个排除）⇒ ⚠️ **944 那个矛盾成因仍未查明**，"
                "且它**不是** 945 以为的「第三个自变量」那么简单。"),
            "added_zero_is_constructive_946": (
                "⚠️⚠️ **`added=0` 在这一批是 `delta()` 的**构造性产物**、不是现象**："
                "`delta()` 在 `identity_stable=False` 时**按构造**返回 "
                "`added=[] / removed=[] / changed=[]`"
                "⇒ 于是出现了「`不带 ti` **75 → 1** 而 `added=0`」这种读数"
                "⇒ ⭐ **不许**把它读成「没写回」"
                "⇒ ⚠️ 这是 944 那个「`is_arm` 判据太松」的**同族**病，"
                "但这次在 `delta()` 里 ⇒ **凡是身份不稳的那一段，"
                "三元组一律不许当读数用**。"),
            "identity_churn_on_this_canvas_946": (
                "⚠️ 946 这一版画布上，**连点过程里身份一直在动**："
                "8 次点击只落点成功 **5** 次、只咬到 **2** 次，"
                "且第 3 次起 `identity_stable` **恒为 False**"
                "（945 同一块是 9 成功 / 8 咬、`landable_found` 14；"
                "946 是 5 成功 / 2 咬、`landable_found` 10）"
                "⇒ ⇒ `w_after_clicks` 这个数**不可信地归属**于本批的点击"
                "⇒ ⚠️ 与 935「重求可点位置失败」同族：**节点大量重叠**。"),
            "anchor_tool_binding_gap_946": (
                "⭐⭐⭐ **锚点自查工具的绑定表停在 `_p941` 就是个真口子**："
                "943 / 944a / 944b / 945 / 946 这五个探针**一个都没登记** "
                "⇒ 它们身上的锚文**从来没被自查过**。"
                "⇒ 代价当场就付了：一条锚文写的是 `**这道门恒绿，等于没有门**`，"
                "而探针里其实是 `—— 这道门恒绿，等于没有门`（**没有加粗标记**）"
                "⇒ 而锚点自查当时报的是「**1645 条 / 0 个问题**」"
                "⇒ ⭐ **一道没登记的锚文，等于一道不存在的锚文**。"
                "⇒ 已补登记（自查读数 **1645 → 1691**）。"
                "⇒ ⚠️ 门禁的**覆盖面**和门禁的**严格性**是两件事："
                "后者再好也补不了前者的漏。"),
        },
        "stablewait_947": {
            # ── 批 947：944 矛盾**剩下的**那个可疑变量 —— 判为**排除** ──────
            # 取样：探针 947，源站，登录态，视口 1512×1200，
            # 2 轮 × 2 格（`wait_stable ∈ {False, True}`），**每格独立 `boot()`**，
            # 五段 JS 逐字 assert 与 946 相同；**逐格 2/2 逐条相同**、
            # **七道设计门 2/2 全 True**（含那道**反恒绿门**）。
            # 固定：settle **照抄 945**（按 `Tab` 到 `不带 ti <= 1` 为止）
            # ⇒ **前置态与 945 同侧**，读数可与 945 对照。
            "wait_stable_changes_nothing_947": (
                "✅⭐⭐⭐ **「连点期间身份在不在动」被排除**："
                "`wait_stable=False`（只等 350ms）与 `wait_stable=True`"
                "（轮询到**连续两次身份表相同**）两格的 `click_rows` 与 `tabs` "
                "**逐条相同** —— 咬到 **4**、第 1 击 `added=4`、`不带 ti 4→1`、"
                "第 2 击 `added=1`、第 3 击 `added=0` "
                "⇒ ⭐ **唯一变的是轮询计数**（0 次 vs **5** 次，5 次**全部等到稳定**）"
                "⇒ ⇒ **「等它稳定」这件事本身对结果没有任何影响**。"
                "⚠️ 结论**限定在「咬到 4 次」这个范围内**（`cell_ok=False`："
                "8 次里只落点 5 次、5≠4）。"),
            "settle_traj_76_to_0_947": (
                "⭐⭐⭐ **settle 轨迹本身成了读数**（946 只知道两个端点）："
                "**刚 `boot()` 完 `不带 ti` = 76，按 1 下 `Tab` 之后 = 0**"
                "（轨迹 `[76, 0]`，2/2 逐格相同）"
                "⇒ ⇒ **76 → 0 是「一下」的落差**，而 946 那批**一按都没按**"
                "⇒ ⭐ 这条轨迹正是 946 想测却**没测到**的那个「前置态」。"),
            "contradiction_only_when_ready_not_zero_947": (
                "⭐⭐⭐⭐⭐ **跨批对照表成形了**（`就绪不带 ti` vs 有没有矛盾）：\n"
                "  · **945**：settle 1 下 ⇒ 就绪 **0**、咬到 8、第 1 击 `added=8`、"
                "8→1 ⇒ **无矛盾**\n"
                "  · **947**：settle 1 下（轨迹 `[76,0]`）⇒ 就绪 **0**、咬到 4、"
                "第 1 击 `added=4`、4→1 ⇒ **无矛盾**\n"
                "  · **944**：settle 10 下 ⇒ 就绪 **1**、连按 6 下 `added` 恒 0 ⇒ **有矛盾**\n"
                "  · **946**：settle **0** 下 ⇒ 就绪 **76**、`75→1` 与 `75→8` "
                "两轮不一致 ⇒ **有矛盾**\n"
                "⇒ ⭐⭐⭐ **矛盾只在「就绪 `不带 ti` ≠ 0」的两侧出现**；"
                "在 **0** 那一侧两批（945、947）都干净。\n"
                "⇒ ⚠️ **但这仍然是关系式推断、不是受控对照** —— "
                "那三批的 `scale`、点击落点、咬到数**都不同** "
                "⇒ 按纪律**不结案**；⭐ 但**下一步该测什么已经唯一了**："
                "让 settle **显式停在 0 和停在 1**，其它一切固定。"),
            "first_click_never_bites_947": (
                "⭐ **§156 挂的那条「第一击不咬」在这里答掉了**："
                "每格的第 1 击都是 `i=0 / bit=False / identity_stable=False`，"
                "**12 个格次 2/2 逐条相同**（945 的 8 个 + 947 的 4 个）"
                "⇒ ⭐ 「`boot()`/预热之后**第一击不咬**、而且连身份都没稳」"
                "在这个范围内**成立**。⚠️ 946 那侧不计入：它的前置态是 76，不是这一侧。"
                "⇒ ⇒ 复刻侧做「连点 N 次」的臂事件实验时，"
                "**第一击必须单独记、不能混进平均值**。"),
            "manip_gate_worked_947": (
                "⭐⭐ **本批自己设计的「反恒绿门」生效了** "
                "（`manip_moved_something`）：`wait_stable=True` 那一格如果"
                "**测不出任何差别**，那道门就恒绿了（和 946 被撤回的 "
                "`warm_reached` 同一个病）⇒ 所以加了一道"
                "**「这个操纵到底动了没有」必须自己答**的门"
                "⇒ 实测 `poll` 从 **0 → 5** ⇒ 操纵**确实动了**、"
                "而结果**没变** ⇒ 这才敢下「排除」的结论。\n"
                "⇒ ⭐ **「操纵动了没有」必须自己答，不能默认它动了。**"
                "⇒ ⚠️ 同一个词「等稳定」的门，**同一种门，一个生效一个恒真**，"
                "差别就在有没有这一道自证：947 这道 `manip_moved_something` "
                "会自己算（0 → 5），946 那道 `warm_reached` 恒真、已撤回。"),
        },
        "settle_landing_948": {
            # ── 批 948：⭐⭐⭐⭐⭐ **944 那个矛盾结案了 —— 它是一个误读** ──────
            # 取样：探针 948，源站，登录态，视口 1512×1200，
            # 2 轮 × 3 格（**显式**按 `n_settle ∈ {0,1,2}` 下），**每格独立 `boot()`**，
            # 五段 JS 逐字 assert 与 947 相同；
            # **逐格 2/2 逐条相同**（`reps_identical = [True, True, True]`）、
            # **反恒绿门 `landed_differently=True`**（三个格真的落在三个不同的值上）。
            "controlled_landing_table_948": (
                "⭐⭐⭐⭐⭐ **受控落点对照表**（2/2，别的全固定，只改按压下数）：\n"
                "  · `n_settle=0` ⇒ 就绪 `不带 ti` = **76**\n"
                "  · `n_settle=1` ⇒ 就绪 = **0**（逐按落点 `[76, 0]`）\n"
                "  · `n_settle=2` ⇒ 就绪 = **1**（逐按落点 `[76, 0, 1]`）\n"
                "⇒ ⭐ 这**第一次**是**受控**的：947 那张表是**关系式**的"
                "（三批的 `scale`/落点/咬到数都不同，947 自己写明了"
                "「这仍然是关系式推断、不是受控对照」）。\n"
                "⚠️ 946 栽过的坑**不许再栽**：它用「按到 `>= warm` 为止」，"
                "而 boot 后的自然值就是 76 ⇒ 任何目标都 ≤ 76 ⇒ 循环一次都没进 "
                "⇒ 门恒真、已撤回。⇒ 本批**不用条件循环**，改成"
                "**显式按固定下数**，并**把每一按的落点与身份稳不稳都记下来**。"),
            "contradiction_resolved_it_was_a_misread_948": (
                "⭐⭐⭐⭐⭐ **944 那个挂了四批的矛盾结案了 —— 它是一个误读。**\n"
                "  · 947 的表说「矛盾只在就绪 **≠ 0** 那侧」⇒ **本批把它推翻了**：\n"
                "    `n_settle=2` 就绪 = **1**（正是 944 那一侧的值），\n"
                "    而第 1 击 **`added=5`、`不带 ti 5→1`、补回=True**，"
                "**补偿照常发生**（2/2）\n"
                "  ⇒ ⇒ 真正的分界是 **76 vs {0, 1}**，**不是** 0 vs 1。\n"
                "  · 唯一异常的是 `n_settle=0`（就绪 **76**）那一格：\n"
                "    连点 2 咬、连点后 `不带 ti` **76 → 75**（**降了 1、不是涨**），\n"
                "    且 `click_rows` 是 **`added=[0]` / `added=[2]`** —— "
                "点击在**给**没有 `tabindex` 的节点**加上** `tabindex`，\n"
                "    与另一侧的 `removed=[…]`（**拿掉**）**方向相反**\n"
                "  · 那一格第 1 击 `Tab` 是 `75 → 1`、`added=0`、`identity_stable=False`\n"
                "    ⇒ 而 946 的 **sham**（**零点击**）已经证明刚 boot 完第 1 击 `Tab` "
                "就是 `76 → 0` ⇒ **那一击在干的是「冷启动铺窗口」，不是补偿**\n"
                "⇒ ⇒ ⇒ **944 把「冷启动铺窗口」读成了「补偿没来」——矛盾根本不存在。**\n"
                "⚠️ **但 944 自己那次读数（就绪 1、13 连点、连按 6 下 `added` 恒 0）"
                "本批没有解释** —— 按 948 的落点，按 2 下就停在 1 ⇒ "
                "**944 的前置态与 `n_settle=2` 那一格是同一个值**，而那一格补偿照常\n"
                "⇒ ⇒ 那次不补**另有原因**（944 自己的 `cell_ok` 不满足、"
                "身份不稳那一段的读数按 946 **一律不作数**）。**成因仍未查明。**"),
            "settle_readings_are_transient_948": (
                "⭐⭐⭐ **`settle_stable_ok = False`** —— settle 那几按的 "
                "`identity_stable` **全为 `False`** ⇒ ⭐ "
                "**`76 → 0 → 1` 这条路径每一按身份都在动**\n"
                "⇒ 按 948 自己写下的那道门（「**一个数看起来像状态不够，"
                "得知道它稳不稳**」）⇒ **`不带 ti = 1` 不是一个稳定状态，"
                "它是铺窗口过程中的一个瞬态读数。**\n"
                "⇒ ⚠️ 这条**反过来削弱** 944 自己的前置态："
                "「settle 10 下、就绪 1」那个 **1** 也是瞬态 ⇒ "
                "**944 的连点是在一个瞬态上做的**。"),
            "first_click_regime_dependent_948": (
                "⭐ 「第一击咬不咬」**也分 regime**（2/2）：\n"
                "  · 就绪 **0** 与 **1** 两格：第 1 击都是 "
                "`i=0 / bit=False / identity_stable=False`（**不咬**）\n"
                "  · 就绪 **76** 那一格：第 1 击反而 **`bit=True` / `added=[0]`**"
                "（**咬了**）\n"
                "⇒ ⇒ 「boot/预热之后第一击不咬」那条（945 的 8 + 947 的 4，"
                "**12 个格次**）**只在这一侧成立**，**不许**外推"),
            "three_cells_not_all_ok_948": (
                "⚠️ 三格 `cell_ok` **全为 `False`**（8 次里只落点 5 次；"
                "咬到 2 / 4 / 4）⇒ **本批的结论限定在「咬到 2~4 次」这个范围内**。"
                "⚠️ 而「咬到 2 / 4 / 4」这个差别本身也是读数："
                "就绪 **76** 那格只咬到 **2**，另两格咬到 **4** ⇒ "
                "**落点与咬到的关系也分 regime**。"),
        },
        "replay944_949": {
            # ── 批 949：⭐⭐⭐ **944 那次读数不可复现** ──────────────────────
            # 取样：探针 949，源站，登录态，视口 1512×1200，
            # 2 轮 × 2 格、**每格独立 `boot()`**，五段 JS 逐字 assert 与 948 相同；
            # **逐格 2/2 逐条相同**（`reps_identical = [True, True]`）、
            # **对照格真的在**（`control_present = True`）。
            # ⭐ 设计关键：对照格**就在同一次跑里** ⇒ 不再犯 947 那个
            # 「拿不同批次的读数当对照」的错。
            "replay944_uses_its_own_numbers_949": (
                "⭐⭐⭐ **格 0 用的是 944 自己那组数字**："
                "`n_settle=2`（就绪 `不带 ti` = **1**，948 已 2/2 验过）、"
                "`scale=13`、连按 **6** 下 `Tab`；"
                "格 1 是**同一次跑里的对照**（`scale=8`、按 3 下），"
                "两格**只差 `scale` 与按压下数**，其余逐字相同"),
            "not_reproduced_949": (
                "⭐⭐⭐⭐ **944 那次读数不可复现**（2/2，逐条相同）：\n"
                "  · 格 0（944 的数字）：就绪 **1**、点 13 次**落点 10、咬到 9**、"
                "连点后 `不带 ti = 10`\n"
                "    → 第 1 击 `was_arm=True`、**`added=10`、`10 → 1`**（补回）\n"
                "    → 第 2~6 击**每击 `added=1`、`1 → 1`**、**`was_arm=True` 全程**\n"
                "    ⇒ `added` 全 0 = **False**、有 `added` 的按压数 = **6/6**\n"
                "  · 格 1（同跑对照）：就绪 **1**、落点 5、咬到 4、连点后 **5**\n"
                "    → 第 1 击 `added=5`、`5 → 1`；第 3 击 `added=0`（**死按压**）\n"
                "  ⇒ ⇒ **`reproduced_944 = False`**，而两格**都补回**\n"
                "⇒ ⇒ ⭐⭐⭐ **用同一组数字、2/2 逐条相同地测到了补偿** ⇒ "
                "**944 那次「连按 6 下 `added` 恒 0」不是机制的性质**"),
            "what_944_actually_recorded_949": (
                "⚠️⚠️ **944 自己就记下了它那一格不满足条件**，本批只是把这件事指出来："
                "它写的是「**两轮不一致**、所以**不许**下结论」"
                "⇒ 而 949 用**同一组数字**测到的是 **2/2 逐条相同**\n"
                "⇒ ⇒ 结合 948 那条（**就绪 = 1 是瞬态**、settle 那几按 "
                "`identity_stable` **全为 `False`**）⇒ "
                "**944 测的是一段身份还在动的瞬态** ⇒ 按 946 的纪律，"
                "**那一段的读数本来就不作数**。\n"
                "⇒ ⚠️ **但这是推断不是实测** —— 本批**没有**在源站上复现出"
                "944 那个不稳定的前置态 ⇒ **不许**写成「已查明 944 当时发生了什么」，"
                "只写「**不可复现**」+「**那一侧是瞬态**」两条并列。"),
            "control_matches_948_949": (
                "⭐⭐ **同一次跑里的对照格与 948 格 2 逐条相同**"
                "（就绪 1、落点 5、咬到 4、连点后 5、"
                "`added=5` 5→1、`added=1` 1→1、末击 `added=0`）\n"
                "⇒ ⇒ **跨批次可比的疑难第一次被消掉了**："
                "不是靠「不同批次碰巧一样」，而是**同一段代码在同一次会话里测了两遍**\n"
                "⇒ ⭐ **对照必须放在同一次跑里** —— 947 栽过一次，"
                "它那张表被自己判成「**关系式推断、不是受控对照**」。"),
            "replay949_cells_not_ok_949": (
                "⚠️ 两格 `cell_ok` **都为 `False`**（格 0：落点 **10** ≠ 咬到 **9**；"
                "格 1：落点 **5** ≠ 咬到 **4**）⇒ **「第一击不咬」仍然是常态**"
                "（格 0、格 1 的第 1 击都是 `i=0 / bit=False`）\n"
                "⚠️ 而格 0 的 `landable_found = 15`、格 1 是 **10** ⇒ "
                "**同一块画布上「本体可点的下标数」逐轮会变** ⇒ "
                "**规模类断言必须关系式**（935 的老教训，第三次应验）。"),
            "verifier_stale_read_949": (
                "⚠️⭐⭐ **本批的门禁第一次跑出 509/514，而**逐条手算那 5 条"
                "判据的条件**全部成立** ⇒ 二者矛盾 ⇒ 真相是"
                "**门禁读到了半旧的源码**（它在最后几次改动落定前就启动了）"
                "⇒ **重跑一遍 = 514/514**。\n"
                "⇒ ⭐⭐ **门禁红了、而把它的每条条件单独求值都成立时，"
                "第一动作是「重跑」，不是「改判据」** —— "
                "那个矛盾本身就是「读到旧文件」的指纹。\n"
                "⇒ ⚠️ **改判据会把一个时序问题变成一个永久的假红**，"
                "而门一旦被人当成「需要放宽的东西」，它就失去意义了"
                "（942：**一个恒真的判据比没有判据更坏**）。\n"
                "⇒ ⚠️ 这条是「**别等门禁跑完才发现**」的**反面**用例："
                "那次是门禁跑了才发现，而**正确动作是重跑**——"
                "**先怀疑自己的时序，再怀疑判据**。"),
        },
        "coldwindow_950": {
            # ── 批 950：⭐⭐⭐⭐⭐ 「铺窗口」从**现象**升级成**规则** ──────────
            # 取样：探针 950，源站，登录态，视口 1512×1200，
            # **零点击**（只点一次画布空白去焦点）、从刚 boot 完连按 **14** 下 `Tab`，
            # **2 轮**、每轮独立 `boot()`；**曲线 2/2 逐条相同**。
            # 五段 JS 逐字 assert 与 949 相同；`NO_TI_JS` 是本批**新件**、
            # 显式 assert **不许混进**「逐字相同」那组。
            "coldwindow_curve_950": (
                "⭐⭐⭐⭐⭐ **「冷启动铺窗口」的完整规则**（**零点击**、2/2 逐条相同）：\n"
                "  · `不带 ti` 曲线 = **[76, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]**\n"
                "  · ⇒ 第 1 按：**76 → 0**（**铺窗口**，所有节点都拿到 `tabindex`）\n"
                "  · ⇒ 第 2 按：**0 → 1**（**建立「当前」节点**）\n"
                "  · ⇒ 第 3 按之后：**恒 1**（§131 那条不变式**成立**，`steady_at_one`）\n"
                "  · 第 1 按落差 **76**、其后**最大落差 1** ⇒ `press1_is_the_big_drop`\n"
                "⇒ ⭐ 「铺窗口」是**一次性事件**（只有第 1 按），"
                "**不是**「每按一下都在铺」"),
            "pointer_freezes_on_inner_button_950": (
                "⚠️⚠️ **「冻住」这个说法已被 952 改写**（见 `freeze_who_952`）："
                "**不是指针被卡住，是 `Tab` 正常走完了节点工具条的全部 4 个按钮，"
                "而那 4 下指针一步都不动** ⇒ 下面 950 写的**现象**（`no_ti` 恒 `[2]`）"
                "**仍然成立**，**被改写的只是「冻住」这个心因模型**。\n"
                "⚠️ 另有一条 952 才查出来的陷阱：`active_before == active_after` "
                "**不代表焦点没动**（按钮之间切换时两者都是 `BUTTON`）⇒ "
                "950 读图得出的「被吞了 3 下」**只对 1 下为真**。\n"
                "——— 以下是 950 当时的原文，保留下来对照 ———\n"
                "⭐⭐⭐⭐⭐ **指针会冻住 —— 而且冻在「焦点落在节点内部按钮」的那几按**：\n"
                "  · 指针（「没有 `tabindex` 的下标」）序列 = "
                "`[] → [0] → [1] → [2] → [2] → [2] → [2] → [2] → [3] → [4] → … → [8]`\n"
                "  · ⇒ 第 2~4 按：指针 **+1 每按一次**（0→1→2）\n"
                "  · ⇒ ⚠️ **第 5~8 按：指针整整 5 下冻在 `[2]` 不动**\n"
                "    而那 5 下 `active_before = BUTTON`、`was_arm = False`、"
                "三元组**全空**、`不带 ti` **恒 1**\n"
                "  · ⇒ 第 9 按：`active_before` 回到 `DIV`、`was_arm = True`、"
                "`bit = True`、`added = 1` ⇒ 指针 **2 → 3** **立刻恢复游走**\n"
                "⇒ ⭐⭐⭐⭐⭐ **焦点一旦落在节点内部的 `BUTTON` 上，"
                "`Tab` 连按 5 下指针完全不动**"),
            "pointer_walks_gate_went_red_950": (
                "⚠️⭐⭐ **本批自己设计的可红门真的红了** —— 这正是它存在的意义：\n"
                "· 判据写的是「**「没有 tabindex 的那个下标每按一次就变」**」，"
                "而实测 `pointer_walks = **False**`（5 下重复 `[2]`）\n"
                "⇒ ⇒ **「每按一次就往前挪一格」这句话本身是错的** —— "
                "正确的是「**每按一次有可能挪一格；落在内部按钮上时连挪 5 下都不动**」\n"
                "⇒ ⭐ **一道可红的门比一道恒绿的门值钱**："
                "这道门**当场把一句错话拦下来了**，而 942 的教训是"
                "**一个恒真的判据比没有判据更坏**\n"
                "⇒ ⚠️ 对照：本批的 `steady_at_one` 与 "
                "`press1_is_the_big_drop` 都是**绿的**，说明它们没有在混日子"),
            "explains_944_added_all_zero_950": (
                "⚠️⚠️⚠️ **本条已于 951 撤回（见 `focus_gate_951`）—— 下面这段"
                "是 950 当时写的推断原文，保留下来只为对照** ⭐\n"
                "**当时的推断**：「只要按 Tab 之前焦点落在内部 `BUTTON` 上，"
                "连按 5 下指针都不动 ⇒ **不是「没补偿」，"
                "是那 6 下压根没在臂窗口上按**」。\n"
                "**951 的证伪**：在 **944 的数字**（就绪 1、13 连点、6 下 `Tab`）下，"
                "**2/2 逐条相同**地测到指针 **6/6 每按都动**、`added` 合计 **15**、"
                "补回 **True** ⇒ **那个「因此」不成立**。\n"
                "⇒ ⭐ **950 的冻结现象本身仍然成立**（零点击、2/2、"
                "第 5~8 按冻在 `[2]`）—— **被撤回的只是「拿它解释 944」这一步**。\n"
                "⇒ ⭐⭐ **冻结属于「冷启动直接 `Tab`」那条路径**，"
                "**在「13 连点之后」根本不成立** ⇒ "
                "⚠️⚠️ **我上一批把两条路径混成了一条** ⇒ "
                "**950 的机制不得再被引用来解释 944**。\n"
                "⚠️ 另一条更要紧的：**写这条推断之前我没有先查基线里有没有反例** —— "
                "而 945 早就把「**点击之后焦点本来就在节点本体上**」写进基线了，"
                "951 实测与它**逐字吻合** ⇒ ⭐ **一条推断如果与基线里已有的读数矛盾，"
                "那它一开始就不该被写下来**"),
            "zero_clicks_and_capped_reading_950": (
                "⭐ 本批**零节点点击**（只点一次画布空白去焦点，943 起的标准前置）"
                "⇒ 设计门 `zero_node_clicks` 在**每一轮**都为 True。\n"
                "⚠️ 且「无 ti 下标」那份读数**截断到 40 条并如实记 "
                "`no_ti_capped`**（冷启动那一档 76 条**超了**）⇒ "
                "**不许**让人以为那就是全部 —— 截断必须**自带标记**"),
        },
        "focus_gate_951": {
            # ── 批 951：⚠️⭐⭐⭐ **950 那条推断作废**（被自己的门红掉）────────
            # 取样：探针 951，源站，登录态，视口 1512×1200，
            # 2 轮 × 2 格，**每格独立 `boot()`**，六段 JS 逐字 assert 与 950 相同；
            # **逐格 2/2 逐条相同**。
            # 唯一自变量：按 Tab 之前**做不做**程序化聚焦
            # （格 0 照 **944** 不做、格 1 照 **949** 做）；其余全固定
            # （`n_settle=2` ⇒ 就绪 1、`scale=13`、`n_rec=6` —— **全是 944 的数字**）。
            "arm_focus_is_a_noop_here_951": (
                "⚠️⭐⭐⭐ **`arm_focus` 这个自变量在 944 的条件下是个 **no-op**：**\n"
                "  · 格 0（**不**程序化聚焦，照 944）实测读到 "
                "`focus_skipped = {'active_tag': 'DIV', 'focus_in_node': True}`\n"
                "  ⇒ ⇒ **点击之后焦点本来就在节点本体上** ⇒ "
                "「不聚焦」与「聚焦」**是同一件事**\n"
                "  · 两格**逐条相同**（2/2，四个格次全同）："
                "指针序列都是 **`[68] → [69] → [70] → [71] → [72] → [73]`**、"
                "`指针动 6/6`、`冻住 0 下`、`added` 合计 **15**、补回 **True**\n"
                "⇒ ⇒ **`focus_moved_the_pointer = False`** ⇒ "
                "**「这个操纵到底动了没有」的答案是：没动**"),
            "inference_950_retracted_951": (
                "⚠️⚠️⚠️ **撤回 950 那条推断**（承 §77 + 950 自己写下的"
                "「**这三条链接都是推断、不是实测**」）：\n"
                "  · 950 说：「焦点落在内部 `BUTTON` 上 ⇒ 指针冻住」⇒ "
                "**因此** 944 那次 6 下 `added` 恒 0 是「没在臂窗口上按」\n"
                "  · ⇒ ⭐⭐⭐ **本批证伪的是那个「因此」**：在 **944 的数字下**"
                "（就绪 1、13 连点、6 下 `Tab`）**不聚焦也照样 6/6 全咬、"
                "指针 6/6 全动**\n"
                "  · ⇒ **950 的冻结现象本身是真的**（零点击、2/2），"
                "**但它的触发条件属于「冷启动直接 `Tab`」那条路径**"
                "（第 5~8 按），**在「13 连点之后」根本不成立**\n"
                "⇒ ⇒ ⚠️⚠️ **我上一批把「冷启动路径」与「连点之后路径」混成了一条** "
                "⇒ **950 的机制不得再被引用来解释 944**"),
            "baseline_already_had_the_counterexample_951": (
                "⚠️⭐⭐⭐ **更要紧的一条：写 950 那条推断之前，我**没有先查基线里"
                "有没有反例** —— 而 945 早就把这条读数**写进基线**了：\n"
                "  · 945 的 `not_an_arm_event_hypothesis_refuted_945` 写着"
                "**「点击之后焦点本来就在节点本体上」**\n"
                "  · 951 实测 `focus_skipped` **与那句话逐字吻合**\n"
                "⇒ ⇒ ⭐⭐⭐ **一条推断如果与基线里已有的读数矛盾，"
                "那它一开始就不该被写下来** —— 不是「写完再被证伪」，"
                "是「写之前就该撞上」\n"
                "⇒ ⚠️ **门禁只查判据锚不锚得到，查不出「这句推断和已有读数打架」** "
                "⇒ ⇒ **这一条只能靠写的人自己先查**"),
            "944_still_unexplained_with_negative_evidence_951": (
                "⚠️⚠️⚠️ **「944 自己那次为何不补」仍然未查明**，而且本批**给它补了一条"
                "负面证据**：\n"
                "  · 在 **944 的数字**（就绪 1、13 连点、6 下 `Tab`）下，"
                "**2/2 逐条相同**地测到：指针 **6/6 每按都动**、"
                "`added` 合计 **15**、终值 **1**、补回 **True**\n"
                "  · ⇒ ⇒ **944 那次是一个至今无法复现的异常**，"
                "**不是**「焦点卡在内部按钮」\n"
                "⇒ ⇒ 与 949 那条**并列**（都指向「不可复现」）：\n"
                "  · 949：**同一组数字**重跑 ⇒ 补偿**照常**（2/2）\n"
                "  · 951：**同一组数字 + 两种聚焦**重跑 ⇒ 两边**逐条相同**、都补偿（2/2）\n"
                "⇒ ⭐ **两条独立的重跑都测到补偿** ⇒ "
                "**944 那次的成因在本树上已无从追查** ⇒ "
                "**不许**再往它身上加机制解释"),
        },
        "freeze_who_952": {
            # ── 批 952：⭐⭐⭐⭐⭐ 「冻住」其实是「`Tab` 走完了工具条」 ──────
            # 取样：探针 952，源站，登录态，视口 1512×1200，
            # **零节点点击**，2 轮 × 2 格、每格独立 `boot()`；
            # 六段 JS 逐字 assert 与 951 相同，`WHOAMI_JS` 是本批**新件**
            # （显式 assert **不许混进**「逐字相同」那组）；
            # **逐格 2/2 逐条相同**、`design_gates` 七门全 True。
            # 格 0 = 照 950 的基线（`Tab` × 14）；格 1 = 先按 4 下到冻结点、
            # 再跑判别组（`Shift+Tab` → `Tab` → `ArrowDown` → `Escape` → `Tab`×3）。
            "not_frozen_but_walking_the_toolbar_952": (
                "⭐⭐⭐⭐⭐ **那不是「卡住」，是 `Tab` **正常走完了节点工具条** ——**\n"
                "  · 冻结段的 4 个元素身份**逐一取到**（全是**时间线节点** "
                "`node_index=2`「时间线 node: 时间线 1」的工具条按钮）：\n"
                "    按 4 → `tid=timeline-toolbar` / aria **`导出时间线`**\n"
                "    按 5 → `tid=timeline-toolbar` / aria **`全屏编辑`**\n"
                "    按 6 → `tid=timeline-mute-button` / aria **`静音`**\n"
                "    按 7 → `tid=timeline-passive-source-picker-slot` / aria "
                "**`添加素材到时间线`**\n"
                "    按 8 → 离开工具条、落到 `node#3` 的 `DIV`（「文本 node: 文本 2」）\n"
                "  · ⇒ ⭐ **4 个按钮、4 下按压、指针一步都不动** ⇒ "
                "**不是「指针冻住」，是「指针在这段里根本不参与」**\n"
                "  · ⇒ 与 944b 那条 `inner_button_not_an_arm_event`"
                "（三元组全空 + 开 1 个层）**完全同形** —— "
                "只是这次是从**指针侧**、用**正面的身份读数**看到的"),
            "pointer_only_moves_on_div_press_952": (
                "⭐⭐⭐⭐⭐ **指针只在「从节点本体 `DIV` 出发的那一按」上 +1**：\n"
                "  · 格 0：按 1~4 指针 `[…]→[]→[0]→[1]→[2]`（**每按 +1**）\n"
                "  · 按 5/6/7（**在工具条的 3 个按钮之间**）指针**恒 `[2]`**\n"
                "  · 按 8（**离开**工具条、落到 `DIV`）指针**仍 `[2]`**\n"
                "  · 按 9（从 `DIV` 出发）指针**才 `[2]→[3]`**\n"
                "  · ⇒ ⇒ **「一按滞后」是真的**（`lag_is_one_press = True`，2/2），"
                "**但 950 当时的因果说错了**：不是「离开的那一按不算」，"
                "而是「**指针只认 `DIV` 出发的那一按**」\n"
                "⇒ ⭐ 这也**顺带解释了 §131 那条不变式为什么对得上**："
                "指针每次只 +1、而工具条那 4 下**一次都不 +** ⇒ `不带 ti` 恒 1"),
            "discrimination_952": (
                "⚠️⚠️⚠️ **本条已被 953 部分改写**（见 `escape_claim_retracted_953` "
                "与 `shift_tab_rule_is_position_dependent_953`）：**`Escape` 与 "
                "`ArrowDown` 那两按按下时焦点**已经在节点本体上、不在工具条里** ⇒ "
                "**「`Escape` 不能从工具条里弄出来」没有对应的那一按**；"
                "**`Shift+Tab` 立刻离开工具条**是**位置相关**的。原文如下，保留对照 ———\n"
                "⭐⭐ 判别组（格 1，2/2 逐条相同）：\n"
                "  · **`Shift+Tab`**：焦点**立刻**离开工具条（落到 `aria='Canvas'`），"
                "而指针**仍不动** ⇒ **反向臂有效、且同样不推指针**\n"
                "  · 紧接着的 `Tab`：指针 **`[2]→[3]`** **动了** ⇒ "
                "**再次印证「从 `DIV` 出发的那一按才推指针」**\n"
                "  · **`ArrowDown`**：焦点**没动**、指针**没动** ⇒ "
                "方向键在节点本体上**无反应**\n"
                "  · **`Escape`**：焦点**没动**、指针**没动** ⇒ ⭐ "
                "**`Escape` 不能把焦点从工具条里弄出来** —— "
                "**反向臂比 `Shift+Tab` 差一截**"),
            "tab_cycle_is_10_here_952": (
                "⚠️⚠️⚠️ **本条整条已被 953 撤回**（见 `cycle_10_retracted_953`）—— "
                "**952 自己的 14 按读数就否掉了它**（10 个节点停靠点、从未回卷），"
                "而它的算法把「4 个按钮 4 下」写成了「1 下」。原文如下，保留对照 ———\n"
                "⭐⭐⭐⭐ **Tab 周期 = 10**（2/2）：\n"
                "  · 节点 `0..8` 各 1 下（指针 `0→1→…→8`）= **9 下**\n"
                "  · + 时间线工具条 1 段（**4 个按钮、4 下、指针不动**）= **1 下**\n"
                "  · ⇒ **9 + 1 = 10**，且从节点 `3` 按一下 `Tab` 指针**直接 `[3]→[0]`**"
                "（**回卷**，不是 +1 到 4）⇒ **周期闭合**\n"
                "⇒ ⚠️ 而 943/944 记过「Tab 周期 101/104」⇒ **差 10 倍** "
                "⇒ 因为**这一版画布只有 1 个节点带工具条**（时间线节点），"
                "其余 8 个是纯节点 ⇒ ⭐ **周期长度 = 节点数 + 带工具条的节点数**，"
                "**逐轮会变**（节点数逐轮会变，935/949 记过）⇒ "
                "**周期类断言必须关系式**"),
            "active_tag_equal_does_not_mean_focus_stayed_952": (
                "⚠️⭐⭐⭐ **`active_before == active_after` 并不代表焦点没动** —— "
                "这是 950 那个「被 `Tab` 吞了」说法的**来源**，我上一批是**读图说话**：\n"
                "  · 按 5：前 `BUTTON` 后 `BUTTON`、aria 都是按钮 ⇒ **真的没动**"
                "（`focus_moved=False`）\n"
                "  · 按 6：前 `BUTTON` 后 `BUTTON`、**但 aria 从「全屏编辑」变成"
                "「静音」、`tid` 从 `timeline-toolbar` 变成 `timeline-mute-button`** "
                "⇒ **焦点动了**（`focus_moved=True`）\n"
                "  · 按 7：同理（「静音」→「添加素材到时间线」）\n"
                "⇒ ⇒ ⭐⭐⭐ **光看 `tag` 读不出焦点有没有动** —— "
                "这些按钮**不自带 `testid`、要靠 `closest('[data-testid]')` 才借到节点的** "
                "⇒ **必须比 `aria-label`（或 `type`）**\n"
                "⇒ ⭐ **「前标签 == 后标签」是个陷阱**：它让 `focus_moved=False` "
                "**只对 4 次里的 1 次为真**，而我据此写了「吞了 3 下」\n"
                "——— ⚠️⚠️⚠️ **以下三行已被 953 改写（原文保留，承 HH.4）** ———\n"
                "⚠️ ① **「按 5 真的没动」是错的**：953 拿**同一份 952 读数**换成"
                "**强判据**（比 `aria`/`node_index`）重算，按 5 是"
                "「`导出时间线` → `全屏编辑`」**aria 变了、焦点动了**\n"
                "⚠️ ② 那个比例**不是 1/4 而是 0/4** ⇒ 952 的 `swallowed_presses=1` "
                "**整条作废** ⇒ 源站那 4 个「指针不动」的按压**焦点 4/4 全动了**\n"
                "⇒ ⇒ ⭐⭐⭐ 正确的说法是：**「指针不动」≠「焦点不动」**，"
                "而 **952 把弱判据的结论当成了现象**\n"
                "⚠️ ③ 原理那一半**仍然成立**（必须比 `aria-label`/`type`）—— "
                "被推翻的只是**那句计数**，以及**据此写下的「吞了 3 下」**"),
        },
        # ══ 批 953：⭐⭐⭐⭐ 把 952 那把尺子搬到**复刻侧**量一遍 ══════════
        # 取样：探针 953，**本地复刻**（localhost:4317），2 轮 × 2 格、每格独立
        # 重开页面；**七段 JS + 七个 Python 助手全部与 952 逐字相同**
        # （用 `inspect.getsource` 对着 952 的**文件内容** assert）。
        # 唯一自变量 = **URL**。固定前置：照 901 插 5 个节点（两格一样）。
        # 设计门：`js/py_verbatim` ✅、`zero_node_clicks` ✅、
        # `pressed_exactly_n` ✅、`replica_actually_moved` ✅、
        # `reached_the_freeze` ✅、`keys_disjoint` ✅、
        # `curve_reproducible_norm` ✅；**逐字那道 `curve_reproducible` 红**
        # 与 **`ring_closed` 红**各有各的读数，见下。
        "replica_ring_953": {
            # 953 是**验收**批：七段 JS 与七个 Python 助手全部与 952 逐字相同，
            # 唯一自变量 = URL。取样：本地复刻 localhost:4317，2 轮 × 2 格。
            "same_ruler_verbatim_953": (
                "⭐⭐⭐ 本批**不是**再取一次样，是**拿 952 的尺子量复刻**：\n"
                "  · **七段 JS 全部与 952 逐字相同**"
                "（`BLANK_JS`/`CENSUS_JS`/`NO_TI_JS`/`POINT_JS`/`FOCUS_JS`/"
                "`ARM_FOCUS_JS`/`WHOAMI_JS`）⇒ 本批**零**新件 JS\n"
                "  · **七个 Python 助手也逐字相同**"
                "（`ev`/`dump`/`guard`/`guard_point`/`delta`/`press_row`/`curve_key`）"
                "—— 用 `inspect.getsource` 对着 952 的**文件内容** assert ⇒ 改一个字就红\n"
                "  · 唯一自变量 = **URL**（源站 → 本地复刻）\n"
                "  · 固定前置：照 901 插 5 个节点（两格完全一样）；"
                "插的是**左栏入口**、不是节点本体 ⇒ `zero_node_clicks` 仍成立\n"
                "⚠️⭐⭐ 这条纪律**当场救了本批**：第一版往 `press_row` 里塞了 2 行新字段 "
                "⇒ **自己把自己判红** ⇒ 才发现指针**根本不用新仪器** —— "
                "`CENSUS_JS` 已经把每个节点的 `ti` 带回来了"),
            "pointer_two_calibers_953": (
                "⚠️⭐⭐ **指针的定义两边不同，这件事必须写出来、不许糊过去**：\n"
                "  · 源站解除布防是**把 `tabindex` 属性摘掉** ⇒ 指针 = "
                "**第一个没有 `tabindex` 的下标**（`NO_TI_JS` 读得到）\n"
                "  · 复刻的 `armAll` 写的是 `'0'`/`'-1'`、**属性一直都在** ⇒ "
                "`no_ti` 在复刻上**恒为空**，源站那把尺子**读不出复刻的指针**\n"
                "  · ⇒ ⭐ **不需要另加仪器**：`CENSUS_JS` 已经把 `ti` 带回来了，"
                "两个口径**从同一份数据派生**\n"
                "  · ⇒ 「指针」统一定义成 `no_ti[0] if no_ti else armed[0]`："
                "**同一件事的两种口径，不是两个现象**；两个都为空记 `None`\n"
                "  · ⭐⭐ **但两个口径在序号上差一格**"
                "（源站那个是「**刚离开**的节点」、复刻那个是「**下一个要落脚**的节点」）\n"
                "  · ⇒ **不能拿「指针落在第几个」直接比两边**，"
                "**该比的是**形状**"
                "（几个节点停靠点、几个内层停靠点、哪一段指针不动）"),
            "ring_is_open_not_cyclic_953": (
                "⭐⭐⭐⭐ **复刻的 `Tab` 环是**开环**：走完画布内**全部 24 个停靠点**"
                "之后，焦点**离开画布**、进入全局 chrome ⇒ "
                "**「周期」这个量在复刻侧根本不存在**"
                "（`ring_closed = False`、实测从不回卷）。\n"
                "  · 28 按的停靠点序列（**2/2 逐条相同**）：\n"
                "    `node#0` + 5 个 video 内层（`Add tags`/`播放`/`底部播放`/"
                "`取消静音`/`全屏预览`）\n"
                "    → `node#1` → `node#2` → `node#3` → `node#4`\n"
                "    → 6 个时间线内层（`导入`/`删除时间线`/`导出时间线`/`全屏编辑`/"
                "`静音`/`添加素材到时间线`）\n"
                "    → `node#5` → 6 个主体内层（`编辑主体`/`主体描述`/`导入主体`/"
                "`从画布选择`/`从资产库选择`/`本地添加`）\n"
                "    → `node#6` → `inner:进入导演台`\n"
                "    → ⭐ **`out:返回首页` → `out:Canvas title: 测试项目` → `out:项目`**\n"
                "  · ⇒ 画布内 = 7 节点 + 17 内层 = **24 个停靠点**，之后**跑出画布**\n"
                "⇒ ⭐ **形状与源站同形**（进内层 → 指针冻住 → 离开那一按仍不动 → "
                "下一按才动），**但环的开闭两边不同**\n"
                "⚠️ **源站那一侧至今未测到环的尽头** ⇒ "
                "**不许**说源站会回卷"),
            "cycle_10_retracted_953": (
                "⚠️⚠️⚠️ **撤回 952 的 `tab_cycle_is_10_here_952` 整条**"
                "（原文保留，承 HH.4）。**两条互相独立的证据**：\n"
                "  · ⭐ **952 自己的数据就否掉了它**：14 按里出现 **10 个不同的节点"
                "停靠点**（下标 `0..9`）**且从未回卷** ⇒ 环 **> 10 个停靠点**\n"
                "  · ⭐ 而 952 的算法「9 个节点 + 工具条 1 段 = 1 下 ⇒ 10」"
                "**把「4 个按钮 4 下」写成了「1 下」** —— "
                "**它自己的前提和它自己的结论互相矛盾**\n"
                "  · ⭐ **复刻侧连「周期」都不成立**（开环、跑出画布）⇒ "
                "那条公式**在唯一能量到的地方直接对不上**\n"
                "⇒ ⇒ **`Tab 周期 = 10`」与**「周期 = 节点数 + 带工具条的节点数」**"
                "两条一并撤回**\n"
                "⇒ ⭐⭐ **仍然成立**的是它背后的纪律："
                "**周期/规模类断言必须关系式**\n"
                "⚠️⚠️⚠️ **更要紧的一条：101/104 基线就在 952 自己引用的那句话里** ——\n"
                "  · §930 早就记过：源站 `canvas-editor-menu` 两次落点的间隔是 "
                "**101 / 104**（两轮不同，因为节点数 77 / 76 也在变）\n"
                "  · §139 把它写成了纪律：「**到边界之后**」的预算必须 > "
                "**一个完整周期（本画布 = 101 次按压）**\n"
                "  · ⚠️ **952 把「101/104」**引用**了，却**没有拿它跟自己的「10」对账**，"
                "反而解释成「差 10 倍是因为只有 1 个节点带工具条」\n"
                "  · ⇒ ⇒ ⭐⭐⭐ **写推断之前先查基线里有没有反例**（951 栽过的那条，"
                "**953 又栽了一次，而且反例就在自己引用的下一句**）\n"
                "  · ⇒ ⇒ 顺带：**源站的周期是 ~101、复刻这一侧是 24 个停靠点然后跑出画布** "
                "⇒ 两者**结构上就差一个量级** ⇒ 这是**复刻与源站的一处结构差异**，"
                "**待查**（不许在没测之前说谁对）\n"
                "⚠️⭐⭐ **新增一条待查（953 没能测到）**：**源站的 `Tab` 到底会不会"
                "离开画布**？14 按只走到 `node#9`、**没走到环的尽头** ⇒ "
                "**源站那一侧必须加预算重测**，"
                "**不许**拿复刻的开环去替源站下结论"),
            "weak_instrument_caught_953": (
                "⚠️⭐⭐⭐⭐ **本批把 952 自己的仪器判红了 —— 而 952 已经把这个陷阱"
                "写进过基线**：\n"
                "  · 952 的 `press_row` 里 `focus_moved` 比的是 "
                "`(active_tag, active_tid)`，而 `FOCUS_JS` 的 `active_tid` 取的是 "
                "`closest('[data-testid]')` —— **内层按钮自己没有 `data-testid`**、"
                "借的是**所属节点**的 ⇒ 按钮之间切换时 `(BUTTON, 节点tid)` "
                "**一模一样**\n"
                "  · 复刻侧实测：28 按里**弱判据 8 次**说「焦点没动」，"
                "**强判据（比 `aria`/`node_index`）8 次全是「动了」** ⇒ "
                "**强判据下「焦点也没动」= 0 下**\n"
                "  · 拿**同一份 952 读数**重算也一样：源站那 4 个「指针不动」的按压，"
                "**强判据 4/4 全动了** ⇒ 952 的 `swallowed_presses=1` **整条作废**\n"
                "⇒ ⇒ ⭐⭐⭐ **正确说法是：「指针不动」不等于「焦点不动」**，"
                "而 **952 把弱判据的结论当成了现象**\n"
                "⇒ ⭐ 处置：**不改 952 那把尺子**（逐字复用是纪律），"
                "**另立一条强的并排记** ⇒ 两条都在读数里，不许只报好看的"),
            "swallowed_count_corrected_953": (
                "⚠️⚠️ 952 那句「**只对 4 次里的 1 次为真**」**也是错的**：\n"
                "  · 「按 5 真的没动」是错的 —— 按 5 是「`导出时间线` → `全屏编辑`」，"
                "**`aria` 变了、焦点动了**\n"
                "  · 那个比例**不是 1/4 而是 0/4** ⇒ `swallowed_presses=1` **整条作废**\n"
                "  · ⇒ **原理那一半仍然成立**（必须比 `aria-label`/`type`），"
                "被推翻的只是**那句计数**，以及**据此写下的「吞了 3 下」**"),
            "shift_tab_rule_is_position_dependent_953": (
                "⭐⭐ **「`Shift+Tab` 焦点**立刻**离开工具条」是**位置相关**的**，"
                "不是通用规则：\n"
                "  · 源站：从**第一个**按钮（`导出时间线`）按 `Shift+Tab` ⇒ "
                "**离开工具条**、落到 `aria='Canvas'`\n"
                "  · 复刻：从**第二个**按钮（`底部播放`）按 `Shift+Tab` ⇒ "
                "**退到第一个**（`播放`）—— 弱判据说「没动」，**强判据说动了**\n"
                "  · ⇒ 这是 ⭐ **又一次弱判据漏报**\n"
                "  · ⇒ ⇒ 两侧是**同一条规则**：**在工具条内反向逐个退，"
                "退到第一个再按就离开** ⇒ 952 那句**不许**当通用结论引用"),
            "escape_claim_retracted_953": (
                "⚠️⚠️⚠️ **撤回 952 的「`Escape` 不能把焦点从工具条里弄出来」**"
                "（原文保留，承 HH.4）—— "
                "**理由不是被证伪，是压根没在那个位置测过**：\n"
                "  · 952 判别组的按键顺序是 `Shift+Tab` → `Tab` → `ArrowDown` → "
                "`Escape` → `Tab`×3；**前两步已经把焦点带出工具条了**\n"
                "  · 逐键重查 952 自己的读数：`Shift+Tab` 从 `BUTTON/导出时间线` "
                "→ `DIV/Canvas`，下一按 `Tab` → `DIV/视频 node: 视频 1`，"
                "**`ArrowDown` 与 `Escape` 都按在节点本体 `DIV` 上**\n"
                "  · ⇒ ⇒ **按 `Escape` 时焦点压根不在工具条里** ⇒ "
                "**「不能从工具条里弄出来」这句话没有对应的那一按**\n"
                "  · ⭐ **仍然成立的那条**（弱、强判据都支持）："
                "**`Escape` 在节点本体 `DIV` 上不动焦点**\n"
                "  · ⭐ 953 **在复刻侧真的在工具条里按了 `Escape`**："
                "按前 `inner:底部播放`、按后**还是** `inner:底部播放` ⇒ "
                "**焦点真没动** ⇒ 「出不来」在**复刻**上成立 —— "
                "⚠️ 但**源站从未在那个位置测过**，所以**不许**说源站也这样"),
            "timestamped_ids_two_gates_953": (
                "⚠️⭐⭐ **逐字那道 `curve_reproducible` 在复刻上恒红** —— "
                "而那**不是**「读数不稳」，是**被测对象**不稳定：\n"
                "  · 复刻节点 `data-testid` **带时间戳**"
                "（形如 `rf__node-text-` + 13 位毫秒数），"
                "⇒ 逐条身份比较在复刻上**构造性不可复现**\n"
                "  · 源站的 id **稳定**（`rf__node-node_236ctpehgg`）⇒ "
                "**这是复刻与源站的一处真实差异**\n"
                "  · ⭐ 处置**不是**改产品让门变绿、**也不是**放宽门："
                "逐字那道**照旧如实记红**，另加一道"
                "**只把 `tid` 尾部数字归一化**的比较\n"
                "  · ⇒ **两道都进读数**（逐字红、归一化后 "
                "`curve_reproducible_norm = True`）\n"
                "⚠️ 与 949 那次对照：**门红了先怀疑仪器** —— 这次**仪器是对的**，"
                "是**被测对象**不稳定 ⇒ 正确处置是**并排记两道**\n"
                "⚠️ **待查**：这个时间戳 id 有没有被别处依赖（持久化/撤销/引用），"
                "**没查之前不许改**"),
            "budget_not_criterion_953": (
                "⭐⭐ **补预算而不是改判据**（901 的先例）：\n"
                "  · `N_PRESS_BASE`：14 → 24（环 24 个停靠点，14 **走不完一圈**）"
                "→ 28（第 24 按落在**最后一个**停靠点上、还没回卷）\n"
                "  · 判别组尾部 `Tab` 由 3 下改成 **4 下**：952 那组在**源站**上"
                "正好停在工具条里，而**复刻**的落点不同（第 3 下**已经离开**工具条）"
                "⇒ 组结束在「离开的那一按」上、**后面没有下一按 ⇒ 滞后根本测不到**\n"
                "  · ⇒ 第一版读成 `False`，那是**预算不够**、不是「没滞后」；"
                "补 1 下后 `lag_is_one_press_probe = True`\n"
                "⇒ ⭐⭐ **复刻与源站在这一条上同形**："
                "离开内层控件的那一按指针**仍不动**、**下一按才动**（滞后 1 下，2/2）\n"
                "⚠️ `seq` 是必需的：base 的 `k` 与 probe 的 `k` **会撞号**\n"
                "⚠️ 952 那两个派生量（`left_button_press`/`lag_is_one_press`）"
                "在**格 1 是**结构性不适用**（它们只算 `base`/`cold` 行）"
                "⇒ **不许**把格 1 的 `False` 当读数；"
                "953 另立了含判别组的 `left_button_press_probe` / "
                "`lag_is_one_press_probe` 两个名字，**不覆盖** 952 那两个"),
        },
        "source_ring_954": {
            # ── 批 954：⭐⭐⭐ 走到**源站**的环尽头 + 补 953 缺的那一格 ─────
            # 取样：探针 954，源站，登录态，视口 1512×1200，2 轮 × 2 格、
            # **每格独立 boot()**；**十六个助手 + 七段 JS 与 953 逐字相同**、
            # `boot_fn` 与 952 逐字相同 ⇒ 本批**唯一的新件是格子驱动器**，
            # **不是仪器**。逐格 2/2 逐条相同。
            # 格 0 = 一路 `Tab` 走到 `N_PRESS_CAP = 120`（§139：预算必须 >
            #   一个完整周期）；格 1 = 每遇一个内层停靠点就试
            #   `Shift+Tab` → `Escape` → `Tab`（上限 6 处）。
            "source_ring_is_102_and_open_954": (
                "⭐⭐⭐⭐ **源站的 `Tab` 环 = 102 下**（2/2 逐条相同、`curve_reproducible` "
                "绿、`ruler_actually_moved` 绿）：\n"
                "  · 120 按里：**节点停靠 88 个 + 内层停靠 14 个 + 出画布 18 个**\n"
                "  · ⇒ **回卷点 = 第 102 按**（`node#0` 第二次出现）⇒ "
                "**环长 101**（从第一次 `node#0` 到第二次）\n"
                "  · ⭐⭐ **与 §930 记的 101 / 104 吻合**（954 实测 **102**，"
                "两轮相同）⇒ **§930 那条独立成立**\n"
                "  · ⭐⭐⭐ **源站也是「开环」**：走完节点段之后焦点**进入顶栏** —— "
                "`out:搜索` → `out:生成历史` → `out:分享` → `out:更多` → "
                "`out:Credits: 725 · 基础会员` → `out:用户菜单` → `out:Canvas`\n"
                "  · ⇒ ⇒ **然后又回到 `node#0`** ⇒ ⭐ **它是开环，但**回得来**\n"
                "  · ⇒ 「周期」在这两边都**不是常数**：它含节点段 + 内层控件段 + "
                "**顶栏那一段** ⇒ **周期类断言必须关系式**（§139 那条纪律再次成立）"),
            "cycle_10_thoroughly_refuted_954": (
                "⚠️⚠️⚠️ **952 的「`Tab` 周期 = 10」被同一把尺子彻底推翻**：\n"
                "  · 954 用的就是 952/953 那把尺子（**逐字复用**），"
                "只把 URL 换回源站、预算补到 §139 要求的量级\n"
                "  · 实测 **102** ⇒ **10 是「节点停靠点数」那一小段**，"
                "**不是周期**（真实周期里还有 14 个内层停靠 + 18 个出画布停靠）\n"
                "  · ⭐⭐ **而 952 当时写下的「差 10 倍」这个直觉反而是对的** —— "
                "它只是把因果归错了（归成「只有 1 个节点带工具条」）\n"
                "  · ⇒ ⇒ 连同 953 的撤回（`cycle_10_retracted_953`），"
                "**这条现在有两条独立的证伪**：① 14 按里从未回卷；"
                "② 同一把尺子走到底 = **102**"),
            "replica_open_ring_is_not_a_deviation_954": (
                "⚠️⭐⭐⭐ **要更正 953 的一条措辞**：953 写「复刻的环是开环」时，"
                "把「源站是不是也开环」列成了**待查**。**现在查到了：源站也开环。**\n"
                "  · 源站：节点段 → **进顶栏 18 个停靠** → **回到 `node#0`**\n"
                "  · 复刻：画布内 24 个停靠 → **进顶栏**（`返回首页` / 项目标题 / `项目`）"
                "⇒ 953 那 28 按里**没看到回来**，但**预算不够**（953 的 28 < "
                "954 源站用的 102）⇒ **不许**拿 953 的 28 下断言复刻回不来\n"
                "  · ⇒ ⭐ **真正的差异是「回不回得来」，不是「开不开环」** —— "
                "而这一条**两边都还没测到**（复刻侧要加预算重测）⇒ **待查**\n"
                "  · ⚠️ 本条**同时更正** 953 里「**复刻与源站的结构差异**」那个说法："
                "**「开环」不是差异**（两边都开环）⇒ 该说的是"
                "**「环长差一个量级」（复刻 24 vs 源站 101）**"),
            "inner_probe_design_flaw_954": (
                "⚠️⚠️⚠️⚠️ **本批自己犯了和 952 一模一样的错，如实记账** —— "
                "而它正是本批要修的那个 bug：\n"
                "  · 格 1 的按键顺序是 `Shift+Tab` → `Escape` → `Tab`\n"
                "  · ⇒ **`Shift+Tab` 已经把焦点带出工具条了**（实测落到 `out:Canvas`）"
                "⇒ **轮到 `Escape` 时按前已经是 `out:Canvas`、不在工具条里**\n"
                "  · ⇒ ⇒ **954 仍然没有测到「焦点在工具条里按 `Escape`」**\n"
                "  · ⚠️⚠️ **这与 952 的原罪逐字同形**：952 判别组也是"
                "「`Shift+Tab` → `Tab` → `ArrowDown` → `Escape`」，"
                "**前两步就把焦点带出去了** ⇒ 953 撤回 952 的理由"
                "（「压根没在那个位置测过」）**完全适用于我这一批**\n"
                "  · ⚠️ **第二个缺陷**：6 次内层探测**全部落在同一个停靠点**"
                "（`inner:导出时间线`，工具条的**第一个**按钮）—— 因为每次探测的"
                "最后一步 `Tab` 落到 `node#0`，游标**被打回环的开头**，"
                "下一次又走到同一个按钮 ⇒ **第 2/3/4 个按钮上的行为至今没测到**\n"
                "  · ⇒ ⭐ **正确修法（下一批）**：**每个内层停靠点单独成格、"
                "每格独立 `boot()`、每格只发那一个键**（`L_i` 由格 0 的 `stop_seq` "
                "**关系式**给出）⇒ **结构上不可能**再犯「按键顺序把键落在错误位置」"
                "这个错\n"
                "  · ⇒ ⭐⭐ **纪律**：**判别组里每个键都必须在它**声称要测的那个位置**上按**"
                "—— 而**唯一能保证的办法是「一次只按一个键」**，不是「记得核对」"),
            "shift_tab_first_button_and_escape_on_canvas_954": (
                "⭐⭐ **两条仍然成立 / 仍然被独立复现的读数**（2/2 逐条相同）：\n"
                "  · ⭐ **`Shift+Tab` 从工具条**第一个**按钮按 ⇒ 立刻离开工具条**、"
                "落到 `out:Canvas`（弱判据与强判据**都说动了**）"
                "⇒ 与 953 在复刻侧测到的「**从第二个按钮按是退到第一个**」合起来，"
                "**「位置相关」这个判断在源站这一侧也成立**\n"
                "  · ⭐ **`Escape` 在 `out:Canvas`（画布根）上不动焦点**"
                "（弱=False 强=False）⇒ **独立复现** 952 那条"
                "「`Escape` 在节点本体 `DIV` 上不动焦点」的**同族结论** ⇒ "
                "**952 那条「仍然成立」的部分，954 再次支持**\n"
                "  · ⚠️ **这两条都只是部分支持**：它们**不能**替代"
                "「焦点在工具条里按 `Escape`」那一格 —— 那一格**至今空着**"),
        },
        "onekey_inner_955": {
            # ── 批 955：⭐⭐⭐ 补上 952/954 都缺的那一格（**只发一个键**）─────
            # 取样：探针 955，源站，登录态，视口 1512×1200，2 轮 × **8 格**
            # = 16 格，**每格独立 `boot()`**；**十七个助手 + 七段 JS 与 954
            # 逐字相同**（954 又与 953 逐字相同 ⇒ 链式）⇒ 本批**零新件仪器**。
            # 格 = `(第 i 个内层停靠点, 键)`，`i ∈ {1,2,3,4}` × 键 ∈
            # {`Escape`, `Shift+Tab`}；每格**只发那一个判别键**（引导键 `Tab` 不算）。
            "escape_in_toolbar_finally_measured_955": (
                "⭐⭐⭐⭐ **空着的那一格补上了：`Escape` 在**工具条里**按不动焦点**\n"
                "  · 4 个内层停靠点**逐个**测（2/2 逐格相同、`position_verified` 全绿、"
                "`one_key_only` 全绿）：\n"
                "    `导出时间线` → 按前按后**都是它**（弱=False 强=False）\n"
                "    `全屏编辑` → 同上　　`静音` → 同上　　`添加素材到时间线` → 同上\n"
                "  · ⇒ 指针 `[2]→[2]`、`left_toolbar = False`（**没有**离开内层）\n"
                "  · ⇒ ⇒ ⭐⭐⭐ **952 那条被 953 撤回的「`Escape` 不能把焦点从"
                "工具条里弄出来」，现在**重新成立** —— 而且证据等级**更高**：\n"
                "    ① **位置门**（按之前验到焦点真的在内层控件上，并记下身份）\n"
                "    ② **每格只发一个键** ⇒ **结构上**排除了「前一个键把焦点带走」\n"
                "    ③ **强判据**（比 `aria`/`node_index`，不是比 tag）\n"
                "    ④ 2/2 逐格相同\n"
                "  · ⚠️ **撤回的理由（953 记的）没有被推翻，是被满足了**："
                "953 撤回它是因为「压根没在那个位置测过」⇒ **现在测过了**\n"
                "  · ⚠️ 954 那一格是**同一个空缺**（它自己的判别组顺序也把焦点带走了）"
                "⇒ **954 的空缺与 952 的空缺是同一个**，本批一次补上"),
            "shift_tab_rule_mapped_on_all_four_955": (
                "⭐⭐⭐⭐ **`Shift+Tab` 在工具条里的规则，现在在源站侧**完整**成立**"
                "（2/2 逐格相同，4 个位置**各判各的**）：\n"
                "  · 第 1 个 `导出时间线` → **`out:Canvas`**（**离开内层** = True）\n"
                "  · 第 2 个 `全屏编辑` → **`导出时间线`**（留在内层）\n"
                "  · 第 3 个 `静音` → **`全屏编辑`**（留在内层）\n"
                "  · 第 4 个 `添加素材到时间线` → **`静音`**（留在内层）\n"
                "  · ⇒ ⇒ **在工具条内反向逐个退，退到第一个再按就离开工具条**\n"
                "  · ⇒ 与 953 在**复刻**侧测到的「从第 2 个按钮按是退到第 1 个」"
                "**同一条规则** ⇒ ⭐ 「位置相关」这个判断**两边都成立**\n"
                "  · ⚠️⭐⭐ **第 2 格又是一次弱判据漏报**：`全屏编辑` → `导出时间线` "
                "**焦点动了**，而弱判据（比 `(tag, tid)`）说**没动** ⇒ "
                "`弱=False 强=True` ⇒ **弱判据在这一格上又是错的**\n"
                "  · ⇒ 与 953 那条合起来：**弱判据在内层控件之间切换时**"
                "**逐字地不可信**，已两次、两次都是它错"),
            "identity_unstable_on_source_955": (
                "⚠️⭐⭐ **逐字那道 `curve_reproducible` 在**源站**上红**，"
                "而那**不是**「读数不稳」，是**被测对象**在动**：\n"
                "  · 差异字段逐条查出来**只有** `identity_stable` / `bit` / `n_added` / "
                "`n_removed`（行为字段**全部一致**）\n"
                "  · ⭐ `identity_stable=False` 意味着**按前按后的节点表对不上** ⇒ "
                "`added` / `removed` / `changed` / `bit` / `diff_ids` "
                "**全是构造性产物**（946 的原话：「身份对不上时三元组是空的"
                "是构造性产物，不是现象」）\n"
                "  · ⇒ **源站的节点集逐轮会变** —— §930 早记过 77 / 76 两轮不同\n"
                "  · ⚠️⚠️⚠️ **第一版我以为「加一道归一化就修好了」—— 错了**："
                "归一化是**按 `identity_stable` 这个标志分派**的，而**标志本身逐轮在动**"
                "（同一按 rep1 是 `True`、rep2 是 `False`）⇒ 归一化把其中一边标成 "
                "`UNSTABLE`、另一边保留原值 ⇒ **两边照样不同**、而且**不稳定的格次"
                "每一轮都换一批**\n"
                "  · ⇒ ⇒ ⭐⭐⭐ **946 那条原理的正确落点在这里**：「**哪些按的三元组"
                "不可用**」这件事本身也是**逐轮变**的 ⇒ **三元组在这张画布上根本不是"
                "一个可复现的读数面** ⇒ **任何按它分派的归一化都抓不住**\n"
                "  · ⇒ ⭐ **第三道比较：只比「行为字段」**（停靠点身份 + 焦点动不动 + "
                "指针 + 位置门 + 只按一键）—— 它**不依赖那个标志** ⇒ "
                "**8/8 格 2/2 逐条相同**\n"
                "  · ⚠️⭐ **三道门逐字进读数**：逐字（红）、归一化（红）、"
                "行为（绿）⇒ **不许只报好看的第三道**\n"
                "  · ⚠️ 与 953 那次对照：那边是**复刻 id 带时间戳**、这边是"
                "**源站节点集在变** ⇒ **两处的红都是被测对象不稳定，不是仪器不可靠**"),
            "one_key_cell_design_955": (
                "⭐⭐⭐ **本批的设计就是「让 954 那个错在结构上不可能发生」**：\n"
                "  · 格 = `(第 i 个内层停靠点, 键)`，每格**独立 `boot()`**、"
                "**只发那一个判别键**\n"
                "  · 引导是**关系式**的：一直按 `Tab`、数着「这是第几个内层停靠点」，"
                "数到目标就**停** ⇒ **不需要跨格共享的引导表**\n"
                "  · ⇒ ⭐⭐ **「前一个键把焦点带走、后一个键落在错误位置」"
                "这种错在结构上**不可能**再发生\n"
                "  · ⭐⭐⭐ 两道新门都**真的在算**：\n"
                "    · `position_verified_before_press` —— **按之前**验到焦点在内层"
                "控件上并记下身份（`aria` / `tid` / `node_index` / `type_attr`）\n"
                "    · `one_key_only` —— 每格**只发一个**判别键\n"
                "  · ⚠️⚠️ **两轮都真的跑了**：第一版我把两轮比较和设计门写在了 "
                "`for rep` 循环**里面**还跟了个 `break` ⇒ **第二轮根本不会跑** ⇒ "
                "`py_compile` 与逐字门都抓不到（语法合法、逻辑残废）⇒ "
                "**已提出循环**。⭐ 这是「**一次成功不叫可靠**」的另一种翻法："
                "**结构上压根没跑第二遍**\n"
                "  · ⚠️ 另：`assert not (RAW_KEYS & DERIVED_KEYS)` **又一次**真红"
                "（`n_nodes` 同时登记在两边）—— 953 与 955 **两次**栽在同一个键上 ⇒ "
                "**这道门有效，但它的存在不替代「登记前先看一眼」**"),
        },
        "replica_ring_956": {
            # ── 批 956：**复刻侧**加预算走到环尽头（验「回不回得来」）──────
            # 取样：探针 956，复刻（`localhost:4317/jimeng/canvas/demo`），
            # 视口 1512×1200，2 轮 × **2 格** = 4 格，**每格独立 `boot()`**；
            # **十七个助手 + 七段 JS 与 955 逐字相同**（955 又与 954/953 逐字相同
            # ⇒ 链式）⇒ 本批**零新件仪器**（新件只有 `READY_JS`/`boot_ck`/
            # `insert_kinds`/`norm_tid`，都**不是**仪器）。
            # ⚠️ **预算从 953 的 28 提到 120**（与 954 源站那一侧 102 同量级）：
            # 954 明确写了「**不许**拿 953 的 28 下断言复刻回不来」。
            "replica_ring_closes_956": (
                "⭐⭐⭐⭐⭐ **复刻的 `Tab` 环**闭合** —— 954 那条「复刻回不来」"
                "**被彻底推翻**。\n"
                "  · 走 **120 下**（预算与源站同量级），`wrap_k`（同一个节点下标"
                "第二次出现）= **53**（格 0）｜节点停靠 **7** + 内层 **18** + "
                "出画布 **27** = 52，回卷落在第 **53** 按\n"
                "  · ⇒ **`ring_closed = True`**，而 953 读的是 `False`\n"
                "  · ⇒ ⭐⭐⭐ **953 那个 `False` 是预算不够，不是现象**：28 < 53，"
                "28 下**连环的一半都走不到** ⇒ 与 901 `OVERRUN=6→20`、"
                "953 `14→24→28`、954 `14→120` 属**同一类**\n"
                "  · ⚠️⚠️⚠️ **这是本批推翻的第二条**（第一条见下）⇒ "
                "**954 亲手写的「不许拿 28 下断言」是对的，而 953 自己那 28 下"
                "的结论早该作废**"),
            "replica_comes_back_956": (
                "⭐⭐⭐⭐ **`Shift+Tab` 在复刻出画布段**逐个停靠点**都回得来**\n"
                "  · 按**停靠点**去重（不是按「第几个」—— 第一版按序号去重，"
                "结果 3 次探针**全落在 `out:返回首页` 这一个点上**，"
                "是 1 个点的 3 个样本、**不是** 3 个点 ⇒ 已修）\n"
                "  · `out:返回首页` → **`inner:进入导演台`**（**回进节点表 = True**，"
                "2/2 逐条相同）\n"
                "  · `out:Canvas title: 测试项目` → `out:返回首页`（out→out）\n"
                "  · `out:项目` → `out:Canvas title: 测试项目`（out→out）\n"
                "  · ⇒ ⇒ ⭐ **反向逐个退**（955 在源站侧测到的**同一条规则**）"
                "**在复刻侧也成立**\n"
                "  · ⇒ ⚠️⭐⭐ **`back_into_node_list` 只有第 1 个点是 True**："
                "在**顶栏**那两个点按 `Shift+Tab` 只是**在顶栏内部退**、"
                "**一步还回不到画布** ⇒ ⭐ **`came_back` 必须读成「整条出画布段"
                "**第一条** `Shift+Tab` 就回得来」，不是「随便哪个点都回得来」**\n"
                "  · ⇒ 与 954 源站侧对照：**两边都回得来** ⇒ 「回不回得来」"
                "**根本不是**两边的差异"),
            "what_is_the_real_difference_956": (
                "⭐⭐⭐⭐ **两边真正的差异不是「开环」也不是「回不回得来」，"
                "是环的**结构**与环长**量级**\n"
                "  · 源站（954）：环 = **102** 下，节点段 **88** + 内层 **14** + "
                "出画布 **18**\n"
                "  · 复刻（956）：环 = **53** 下，节点段 **25**（7 节点 + 18 内层）+ "
                "出画布 **27–30**\n"
                "  · ⇒ **两边都开环（都经过顶栏/左栏）、都回得来** ⇒ "
                "**953 的「开环」与 954 的「回不来」两条差异**"
                "**都不是**差异\n"
                "  · ⇒ ⭐⭐⭐ **差异在两段的相对权重**：源站**节点段占绝对主导**"
                "（88/102 ≈ 86%，因为它那一版画布有 ~77 个节点），"
                "复刻**出画布段占一半**（27/53 ≈ 51%，出画布段 27 个 vs 源站 18 个）\n"
                "  · ⇒ ⇒ ⭐ **952 那个「差 10 倍」的直觉，方向是对的、"
                "但**对象错了**：差的不是**环长**（53 vs 102 只差 ~2 倍），"
                "是**节点数**（复刻 7 个 vs 源站 ~77 个）⇒ "
                "**那条直觉该改写成「节点规模差一个量级」**\n"
                "  · ⇒ ⚠️ **复刻出画布段 27 个停靠点 vs 源站 18 个 —— 净多 9 个**，"
                "逐条两边**并排 diff** 查出来（⚠️ **第一版我把差异归错了**，见下）：\n"
                "    · **复刻多出 10 个**：**左栏 8 个**（`图片`/`视频`/`音频`/`时间线`/"
                "`主体`/`导演台`/`资产库`/`上传`）+ **2 个无名停靠点**"
                "（`out:`（`aria` 为空）与 `out:sb_518102884867410`）\n"
                "    · **源站多出 1 个**：`out:测试项目…已保存…分享`（**项目面板**）"
                "⇒ 10 − 1 = **净 +9**\n"
                "  · ⚠️⚠️ **第一版我写的是「多出左栏 9 个 + 画布控件 4 个 + `与 AI 对话`」"
                "—— 错了**：并排 diff 一查，**`选择工具`/`小地图`/`显示连线`/"
                "`Zoom options`/`与 AI 对话` 源站那 18 个里全都有** ⇒ "
                "**它们根本不是差异**；⭐ 且 `out:文本` **两边都有**，"
                "所以左栏的差是 **8 个不是 9 个**\n"
                "  · ⚠️ **顺序也不同**（同一批查出来的，一并记）："
                "源站 = `文本`/`选择工具`…画布控件 → 项目面板 → 顶栏 11 个；"
                "复刻 = 顶栏 10 个 → 左栏 9 个 → 画布控件 4 个 → 无名 2 个 ⇒ "
                "**复刻把顶栏排在左栏之前、源站相反**"),
            "leg_decomposition_956": (
                "⭐⭐⭐⭐ **环必须分段量，不能只报一个环长** —— 第四道门"
                "（只比「节点段」）**2/2 逐格相同**\n"
                "  · `leg_node_inner` = **25**（4 格全部一致，2/2 逐格相同）\n"
                "  · `node_inner_stops` 逐条：`node#0` → `Add tags`/`播放`/"
                "`底部播放`/`取消静音`/`全屏预览` → `node#1`…`node#4` → "
                "`导入`/`删除时间线`/`导出时间线`/`全屏编辑`/`静音`/"
                "`添加素材到时间线` → `node#5` → `编辑主体`/`主体描述`/`导入主体`/"
                "`从画布选择`/`从资产库选择`/`本地添加` → `node#6` → `进入导演台`\n"
                "  · ⇒ ⭐ **节点段是稳定的**（2/2 逐条相同）⇒ **它才是可复现的读数**\n"
                "  · ⚠️⭐⭐ **出画布段逐轮会变**：`leg_out` = **[30, 27]**（格 1）"
                "/ **[27, 27]**（格 0）⇒ 环长 53 与 56 都出现过 ⇒ "
                "**绝对环长不是稳定量，绝不能当「周期」断言**\n"
                "  · ⇒ 变的是 `out:`（无 aria）/`out:sb_518102884867410` 这类"
                "**没有可读名字的停靠点**逐轮**多寡不同**\n"
                "  · ⇒ ⭐ **与 955 的教训同构**：不稳定的东西只能**关系式**地记，"
                "**绝不能**当绝对值断言"),
            "three_gates_replica_956": (
                "⚠️⭐⭐⭐ **四道门逐字进读数**（不许只报绿的那道）：\n"
                "  · 逐字 `curve_reproducible` ❌（红）\n"
                "  · 归一化 `curve_reproducible_norm` ❌（红）\n"
                "  · 行为 `curve_reproducible_behavior` ✅（绿，**2 格全绿**）\n"
                "  · ⭐ **第四道：节点段** `node_inner_leg_reproducible` ✅（绿）\n"
                "  · ⚠️ 逐字红 = **复刻 `data-testid` 带时间戳**（953 记过），"
                "**不是**读数不稳 ⇒ 逐字那道**照旧如实记红**\n"
                "  · ⚠️⚠️ **`curve_key` 的覆盖面只有 4/13**：`curve_key` 是**逐字复用**"
                "955 的、**键表内联在函数体里** ⇒ `step_rows`/`frozen_presses`/"
                "`swallowed_presses`/`left_button_press`/`lag_is_one_press`/"
                "`reached_the_freeze`/`escape_releases`/`shift_tab_moves`/"
                "`arrow_moves` 这 **9 个键在 956 的格里不存在** ⇒ `cell.get(k)` 全 `None`\n"
                "  · ⇒ ⭐ **这个覆盖面已如实数出来记进读数**"
                "（`curve_key_coverage`），**不许**让读者以为 13 项都在比\n"
                "  · ⚠️⚠️ **第一版的行为门差点恒真**：照抄 955 的 `_BEHAVIOR` 会让"
                "956 的格**整片变 `None`** ⇒ 两轮**必然相同** ⇒ **假绿** ⇒ "
                "**改用 956 自己的字段表**，并加 `behavior_gate_non_vacuous` 门"
                "（至少一半键**真的存在**）⇒ 本批绿**是真的绿**"),
            "first_version_defects_956": (
                "⚠️⚠️ ⚠️ **写完自查抓到 6 个自身缺陷**（都不是运行时报错，"
                "是**读之前**看出来的）：\n"
                "① ⛔ **根本没有 `sync_playwright`/`launch`** ⇒ `page` 永远是 "
                "`None` ⇒ **一格都跑不了**（`py_compile` 抓不到）\n"
                "② ⛔ `norm_tid` 用了**没定义** ⇒ 归一化那段 `NameError`\n"
                "③ ⛔ `norm_row` 在**逐字 assert 的元组里**却**没定义** ⇒ "
                "文件级 assert 直接 `NameError`\n"
                "④ ⚠️ `if c[\"first_out_seq\"] if \"first_out_seq\" in c else None:` "
                "—— 嵌套条件表达式，**能跑但读不懂** ⇒ 改成 "
                "`if \"first_out_seq\" not in c:`\n"
                "⑤ ⚠️ `import time` 缺了 ⇒ `insert_kinds` `NameError`"
                "（**这是第一次真跑才暴露的**，前四条靠读代码抓到）\n"
                "⑥ ⚠️⭐ **`_BEHAVIOR` 照抄 955 会恒真**（见上）\n"
                "· ⇒ ⭐ 顺带又踩了一次 **954 的坑**：`pointer_of` 和 `strong_moved` "
                "**只有 docstring 被我改短了** ⇒ 文件级 assert 真红 ⇒ "
                "**docstring 也不许分家**（连注释都算）\n"
                "· ⇒ ⭐⭐ **`py_compile` 只保证语法，不保证「名字都用过」** —— "
                "① ② ③ ⑤ 四个都是**语法合法**的"),
        },
        "rail_roving_957": {
            # ── 批 957：**源站**左栏是不是 ARIA roving tabindex（**纯读 + 零点击**）────
            # 取样：探针 957，源站，登录态，视口 1512×1200，2 轮 × **3 格** = 6 格，
            # **每格独立 `boot()`**；**十七个助手 + 七段 JS 与 955 逐字相同**
            # （955 又与 954/953 逐字相同 ⇒ 链式）⇒ **零新件仪器**，
            # 新件只有 `RAIL_JS`（**普查用，只读属性、不调 `focus()`**）。
            # 格 0 `census` / 格 1 `arrow` / 格 2 `armcheck`。
            "source_rail_is_roving_tabindex_957": (
                "⭐⭐⭐⭐⭐ **源站左栏是标准的 ARIA roving tabindex** —— "
                "956/956b 那个「复刻左栏 9 个 / 源站只有 1 个」的差异，"
                "**机制查死了**。\n"
                "  · 格 0 普查（**零点击**，只读属性）：壳 `role=\"toolbar\"`、"
                "`aria-label=\"Canvas toolbar\"`、壳**无** `tabindex`；"
                "壳内 9 枚 `BUTTON` 的 `tabindex` 分布 = "
                "**`0`×1 + `-1`×9**（另有 43 个非按钮后代 `None`）\n"
                "  · ⇒ 唯一顺序入口是 **`文本`**（`tabindex=\"0\"`），"
                "其余 8 枚全被写成 **`tabindex=\"-1\"`** ⇒ "
                "**逐字复刻 WAI-ARIA toolbar 的 roving 模式**\n"
                "  · ⇒ 2/2 逐格**逐条相同**（`census_reproducible`）\n"
                "  · ⭐⭐⭐ **这解释了 956 那个「净多 9」里的 8 个**："
                "复刻左栏 **9 枚按钮全无 `tabIndex`** ⇒ 全部原生可聚焦 ⇒ "
                "**9 个 `Tab` 停靠点**；源站只给 1 个 ⇒ **8 个差额**\n"
                "  · ⇒ ⭐ **954 那个「源站左栏只贡献 1 个停靠点（seq=84、2/2）」"
                "仍然成立，但依据必须换成这一条普查**，"
                "**不能**再靠「数停靠点」（见 `arm_focus_taints_ruler_957`）"),
            "source_rail_arrow_navigates_957": (
                "⭐⭐⭐⭐ **方向键在左栏内移动焦点**（WAI-ARIA roving 的另一半，"
                "源站**有**）：\n"
                "  · 格 1：引导走到左栏那**一个**停靠点（`out:文本`、第 84 按）"
                "⇒ **只发一个** `ArrowDown`（`one_key_only` ✅）\n"
                "  · 读数：`BUTTON/文本/canvas-fixed-toolbar` → "
                "**`BUTTON/图片/canvas-fixed-toolbar`**（`仍停左栏 = True`）\n"
                "  · ⇒ **强判据 True**、2/2 逐格相同\n"
                "  · ⚠️⚠️⭐ **弱判据又说「没动」（`弱=False`）** —— "
                "因为它比的是 `(active_tag, active_tid)`，而左栏 9 枚按钮"
                "**同属一个 `canvas-fixed-toolbar`** ⇒ `(BUTTON, 同一 tid)` "
                "**一模一样** ⇒ **弱判据在内层控件之间切换时逐字不可信，"
                "这已经是第三次、第三次都是它错**（953/955 各一次）\n"
                "  · ⇒ ⭐ **复刻侧完全没有这一套**：`JimengToolRail.tsx` 里 "
                "`tabIndex` 出现 **0 次** ⇒ 既没有 roving、也没有方向键栏内导航"),
            "arm_focus_taints_ruler_957": (
                "⚠️⚠️⚠️⭐⭐ **这一格把 954/955/956 那把尺子的一个隐含前提查红了** —— "
                "而且**第一版自己踩中之后才发现**。\n"
                "  · 格 2（**不可逆动作放序列最后**，只调 `ARM_FOCUS_JS`、**不发键**）："
                "在左栏停靠点上，`ARM_FOCUS_JS` **会**把焦点从"
                "**左栏按钮**拽到**画布节点**"
                "（`BUTTON/图片/canvas-fixed-toolbar` → "
                "`DIV/音频 node: 音频 68/rf__node-node_tadm1nyykc`、"
                "`focus_ok=True`）2/2 相同\n"
                "  · ⚠️ **为什么这是个问题**：`press_row` 按完键之后会调 "
                "`ARM_FOCUS_JS`，而它**带 `el.focus()`**；`who_after` 是在"
                "**它之后**读的 ⇒ **只要那一刻画布里恰好有节点带 "
                "`tabindex=\"0\"`，`who_after` 读到的就根本不是「按完键的焦点」**\n"
                "  · ⚠️⚠️ **第一版就是这么坏的**：格 1 里先跑了一次"
                "「尺子自检」（恰好就是调 `ARM_FOCUS_JS`）⇒ **它自己把焦点"
                "拽到了 `node#75`** ⇒ 随后的 `ArrowDown` **是在 `node#75` 上按的** "
                "⇒ 读出来 `node#75 → node#75` ⇒ ⭐⭐ **那一格什么也没测到**"
                "（**不是**「`ArrowDown` 不动焦点」！）\n"
                "  · ⇒ 修法：判别键那一按**绕开 `press_row`**，"
                "**自己发键 + 逐字 `FOCUS_JS`/`WHOAMI_JS` 读**（`arrow_read_isolated` ✅）；"
                "尺子自检**另起一格**、排最后\n"
                "  · ⇒ ⭐⭐ **由此回头限定 954**：它读到的 18 个出画布停靠点"
                "**没有**被污染（它们逐个不同、不可能全是同一个节点）⇒ "
                "那些按上 `ARM_FOCUS_JS` 恰好**没**动焦点；"
                "**但**格 2 证明**「恰好没动」并不稳固** ⇒ "
                "⚠️ **954 在左栏那一个停靠点上的读数，可信度依赖一个它从没验过的前提**\n"
                "  · ⇒ ⭐⭐ **纪律**：「逐格读数可信」**不等于**「尺子可信」—— "
                "**尺子自己那一步会改被测对象**这件事，**必须自己查**，"
                "而且**要趁它还没污染读数的时候查**"),
            "first_version_defects_957": (
                "⚠️⚠️⚠️ **第一版自己踩了 4 个坑**（其中 2 个是**测完之后**才暴露的）：\n"
                "① ⛔ **手抄 955 的 `FOCUS_JS`/`ARM_FOCUS_JS`/`BLANK_JS` 时抄漏/抄错** "
                "⇒ `BLANK_JS` 只抄了前 3 行（箭头函数**没闭合**）⇒ "
                "**JS 语法门抓到**（`py_compile` 抓不到）\n"
                "② ⛔ `delta` 里 `changed.append([i, ...])` 少了 `int()` ⇒ "
                "文件级 assert 真红 ⇒ **和 956 那次一模一样的错**"
                "（954 也栽在同一个函数上）\n"
                "③ ⚠️⭐⭐ **「尺子自检」自己污染了它要检查的对象** ⇒ "
                "格 1 测到的是节点、不是左栏（详见 `arm_focus_taints_ruler_957`）\n"
                "④ ⚠️⭐ **`arrow_from` 标签指向错的按**：它取 "
                "`row[\"who_before\"]`（引导行走里**上一按之前**的焦点 = `node#75`），"
                "而「`ArrowDown` 之前」的焦点是 `row[\"who_after\"]`（= `out:文本`）⇒ "
                "**读数对、标签错** ⇒ 已把真值另存为 `arrow_from`、"
                "旧的另存为 `walk_who_before`\n"
                "· ⇒ ⭐⭐ **「读数对、标签错」和「读数错」一样危险**："
                "下一个人会把错标签当读数抄走\n"
                "· ⇒ ⭐ `py_compile` 只保语法、`verify` 的逐字门只保「字面相同」，"
                "**两者都抓不到「标签指向了错的按」**\n"
                "· ⚠️⚠️ **顺带记一条门禁之间的关系**：`jimeng_check_verifier_anchors.py` "
                "**只验「那串字面量在文件里存在吗」** ⇒ 它**分不清**"
                "「同一个包里那串字」与「判据真正引用的那处字」"
                "⇒ 本批 SSSS.1 的判据里把探针变量写成了 `cens`、探针里其实叫 "
                "`cen` ⇒ **锚点自查报「问题 0 个」、而门禁真红**"
                "⇒ ⭐⭐ **锚点自查是比门禁弱的门，「自查 0 问题」**不等于**判据会过**"),
        },
        "rail_roving_fix_958": {
            # ── 批 958：**复刻侧实施** 957 测死的机制（roving tabindex）──────
            # 取样：探针 958，复刻（`localhost:4317/jimeng/canvas/demo`），
            # 视口 1512×1200，2 轮 × **4 格** = 8 格，每格独立 `boot()`；
            # **十七个助手 + 七段 JS 与 956 逐字相同**（956 又与 955/954/953
            # 逐字相同 ⇒ 链式）⇒ **零新件仪器**；`RAIL_JS` **逐字来自 957**。
            # 格 0 `census` / 格 1 `arrow` / 格 2 `ring` / 格 3 `armcheck`。
            "replica_rail_roving_installed_958": (
                "⭐⭐⭐⭐⭐ **957→958：952 以来第一次产出**实际产品改动**，"
                "而且验收**两侧逐条相同**。\n"
                "  · 格 0 普查（**零点击**）：`tabindex` 分布 = "
                "**`0`×1 + `-1`×8**（另有 17 个非按钮后代 `None`）、"
                "顺序里可聚焦 **1** 枚（改前是 **9**）⇒ **与源站 957 同一形状**\n"
                "  · 唯一顺序入口仍是 **`文本`**，与源站一致\n"
                "  · ⚠️ 源站是 `0`×1 + `-1`×9 + `None`×43，复刻是 `0`×1 + "
                "`-1`×8 + `None`×17 ⇒ **`-1` 少 1、`None` 少 26** —— "
                "那是**后代数量不同**（源站左栏壳里有 52 个后代、复刻 26 个），"
                "**不是** roving 行为不同 ⇒ 关系式对上了\n"
                "  · ⇒ 改动的代码只有两处：`JimengToolRail.tsx` 加 `railRef` "
                "+ 两个 `useEffect`（初始化 `0`/`-1`、方向键栏内漫游）"),
            "replica_rail_arrow_matches_source_958": (
                "⭐⭐⭐⭐ **`ArrowDown` 在复刻左栏内移动焦点**，与源站 957 "
                "**逐条相同**（2/2 逐格相同）：\n"
                "  · 源站 957：`out:文本` → **`out:图片`**（`仍停左栏 = True`、"
                "**强判据 True**）\n"
                "  · 复刻 958：`out:文本` → **`out:图片`**（`仍停左栏 = True`、"
                "**强判据 True**）\n"
                "  · ⇒ ⭐⭐ **强弱判据两边都是同一个组合**（弱 False / 强 True）⇒ "
                "**弱判据第三次说错这件事，在复刻侧也照样发生**（左栏 9 枚按钮"
                "同属一个 `canvas-fixed-toolbar`）\n"
                "  · ⚠️⚠️ **端点撒手是「不臆造」的选择、不是实测**：957 **没有**"
                "测 `ArrowUp` 在第 1 枚上、也没有测 `ArrowDown` 在最后一枚上 ⇒ "
                "复刻按「端点撒手、让焦点按浏览器默认离开工具条」实现，"
                "并在代码里写明**源站那一格未测** ⇒ **不许**把它当已对齐"),
            "one_lap_now_1_and_19_958": (
                "⭐⭐⭐⭐ **一圈的结构**：左栏 **9 → 1**、出画布段 **27 → 19**\n"
                "  · 格 2 数到**第 2 次**命中左栏为止（= 走满一圈），"
                "**绕开 `press_row`**（格 3 实测它会动焦点）\n"
                "  · 改前 956：一圈 = 左栏 9 + 出画布 27（`wrap_k = 53`）\n"
                "  · 改后 958：一圈 = 左栏 **1** + 出画布 **19**\n"
                "  · 源站 954：一圈 = 左栏 1 + 出画布 **18**\n"
                "  · ⇒ ⭐⭐⭐ **复刻从「27 vs 18」变成「19 vs 18」** —— "
                "956b 记的那个「净多 9」**降到净多 1**\n"
                "  · ⚠️ **剩下的那 1 个是结构性的、不是随机**：并排 diff 一圈 ⇒ "
                "复刻**多 2 个无名停靠点**（`out:`（`aria` 为空）与 "
                "`out:sb_518102884867410`）、**少 1 个**源站有的**项目面板**"
                "（`out:测试项目…已保存…分享`）⇒ 2 − 1 = **+1**\n"
                "  · ⚠️⚠️ **顺序差异仍然存在**（956b 记的那条**没有被本批修掉**）："
                "复刻 = 顶栏 10 个 → 左栏 1 个 → 画布控件 4 个 → 无名 2 个；"
                "源站 = 左栏 1 个 → 画布控件 4 个 → 项目面板 → 顶栏 11 个 ⇒ "
                "**复刻把顶栏排在最前、源站把顶栏排在最后**"),
            "arm_focus_also_taints_replica_958": (
                "⚠️⚠️⚠️⭐⭐ **957 查红的那条，在**复刻**侧同样成立** —— 而我"
                "**第一版是拿推断当读数**的\n"
                "  · 格 3 实测：`ARM_FOCUS_JS` 在**复刻**左栏停靠点上"
                "**会**把焦点从 `out:文本` 拽到 **`node#6`**（`focus_ok=True`）\n"
                "  · ⚠️⚠️ **我第一版的推断是「复刻侧不会」**，理由是"
                "「复刻的 `armRovingTabindex` 只在焦点位于 `.react-flow` 内时"
                "才布 ⇒ 焦点在左栏时画布里没有节点带 `tabindex=0` ⇒ 早退」"
                "⇒ **推断错了**：复刻的 roving **离开画布时不清除**"
                "**上一个**布上去的 `'0'` ⇒ 节点上**仍留着** `tabindex=\"0\"`\n"
                "  · ⇒ ⭐⭐ **纪律**：「复刻的实现读起来是这样」**不是**读数；"
                "**两边都得实测** —— 同一段仪器在源站拽焦点、在复刻也拽，"
                "**不能因为「实现看着不同」就推断它不同**\n"
                "  · ⇒ 本批因此把**格 2 也改成绕开 `press_row`**（第一版的格 2 "
                "走的正是 `press_row` ⇒ 它的 `stop_seq` **不可信**，"
                "「出画布 60 个」是**被污染 + 走了三圈**两个错叠在一起）\n"
                "  · ⇒ ⭐⭐ **由此回头限定 956**：956 那些 `out:` 停靠点"
                "**逐个不同**（`返回首页`/`搜索`/`分享`…）⇒ 不可能是同一个节点 ⇒ "
                "**那些按上 `ARM_FOCUS_JS` 恰好没动**；但**「恰好」并不稳固** ⇒ "
                "956 的结论**方向仍成立**，只是**依据要换成 958 的普查 + 一圈计数**"),
            "probe_defects_958": (
                "⚠️⚠️⚠️ **958 探针自己踩了 4 个坑**（都是「跑之前看不出来」那一类）：\n"
                "① ⛔ **用 `re.search(r'RAIL_JS = \"\"\"\\(\\[\\[^\\]\\]\\*\\]\\)...') "
                "抽 957 的 `RAIL_JS` 抽不出来** ⇒ 改按行切\n"
                "② ⛔ 按行切时**函数签名在 `RAIL_JS = \"\"\"` 那一行**、"
                "**不在下面那些行里** ⇒ 抽出来**少一个签名** ⇒ "
                "自己那道 `count(\"[tid, nodeSel]\") == 1` 的免疫针当场真红"
                "（**这正是免疫针的用处**）\n"
                "③ ⛔⭐⭐ **收尾那行是 `}\"\"\"`**（一个 `}` 加终止符）⇒ "
                "不把那个 `}` 补回去，`page.evaluate` 当场 "
                "`SyntaxError: Unexpected end of input`\n"
                "④ ⚠️⭐ **`jimeng_probe_js_syntax_check.py` 抓不到它** —— "
                "那道门只认**字面量** `NAME = \"\"\"...\"\"\"`，"
                "而这里的 `RAIL_JS` 是**切片拼出来的** ⇒ "
                "**门看不见的东西就得自己配平** ⇒ 已加「大括号配平」免疫针\n"
                "· ⇒ ⭐⭐ **两道既有门（`py_compile` / JS 语法门）都只认"
                "**自己看得见的形状**；**用别的方式造出来的东西，它们都是瞎的** ⇒ "
                "自己造的东西**必须自己配平、自己 assert**"),
        },
        "domorder_959": {
            # ── 批 959：**源站** `Tab` 序 vs DOM 序（**纯读 + 零点击**）──────────
            # 取样：探针 959，源站，登录态，视口 1512×1200，2 轮 × 1 格；
            # 十七助手 + 七段 JS 与 957 逐字相同（957 又与 955/954/953 逐字相同
            # ⇒ 链式）⇒ **零新件仪器**；新件 `DOMIDX_JS`（**纯读、不是仪器**）。
            # ⚠️ 读法**绕开 `press_row`**（957 源站实测、958 复刻实测：
            #   它内部的 `ARM_FOCUS_JS` 带 `el.focus()`、会把焦点从 chrome
            #   停靠点**拽回画布节点** ⇒ 用它读 DOM 下标会**读到节点**）。
            "tab_order_is_not_dom_order_959": (
                "⭐⭐⭐⭐⭐ **本批推翻了我自己 958 结尾写下的那个猜想** —— "
                "「`Tab` 顺序 == DOM 顺序」在源站**是假的**（2/2 逐轮一致）。\n"
                "  · 量法：逐按发 `Tab`、逐字读焦点元素的 "
                "`document.querySelectorAll('*')` 下标与 `tabindex`\n"
                "  · 源站 out 段共 **18** 个停靠点，**与 954 逐条相同**，"
                "**DOM 下标却是**：\n"
                "    · 画布控件 6 个（左栏 `文本` / `选择工具` / `小地图` / "
                "`显示连线` / `Zoom options` / `与 AI 对话`）= "
                "**dom#2263、2357、2367、2377、2387、2396**\n"
                "    · 项目面板 + 顶栏 11 个 + 画布根 = **dom#60…177**\n"
                "  · ⇒ ⭐⭐⭐ **Tab 序把 DOM 靠后的 2263–2396 排在前面**，"
                "而 DOM 靠前的 60–177 排在后面 ⇒ "
                "`dom_index_monotonic = False`（2/2）\n"
                "  · ⇒ ⭐⭐⭐⭐ **958 结尾的「查源站 DOM 序」方向就错了**："
                "**源站 DOM 序本来就是「顶栏在前、画布控件在后」**，"
                "**和复刻的 DOM 序一致** ⇒ **真差异不是 DOM 序，"
                "是「应用怎么把 `Tab` 接到焦点上」**"),
            "rail_order_split_959": (
                "⭐⭐⭐⭐ **out 段被切成两段，源站把「画布控件」整体提前**\n"
                "  · 第 1 段（6 个）：`文本`（左栏）→ `选择工具` → `小地图` → "
                "`显示连线` → `Zoom options, 50%` → `与 AI 对话`"
                "（**dom#2263–2396**）\n"
                "  · 第 2 段（12 个）：项目面板 → `返回首页` → `Canvas title` → "
                "`项目` → `Canvas node summary` → `搜索` → `生成历史` → `分享` → "
                "`更多` → `Credits` → `用户菜单` → `Canvas`（`rf__wrapper`、"
                "**dom#60–177**）\n"
                "  · ⇒ ⭐ **第 2 段就是 DOM 序**（60→68→85→90→94→118→122→131"
                "→136→150→163→177，**严格单调**）⇒ **只有第 1 段被提前了**\n"
                "  · ⇒ ⭐⭐ 这是一条**可复现的**结构事实（2/2 逐条相同），"
                "**但机制未查明**"),
            "mechanism_unknown_959": (
                "⚠️⚠️⚠️ **机制未验死，标「未验证」—— 而最顺手那个解释**已被我的读数否掉**：\n"
                "  · 猜想：源站在 `keydown` 里给画布控件写**正 `tabindex`**，"
                "把 `Tab` 顺序顶到前面（896 早记过「应用在 keydown 里改 `tabindex`」）\n"
                "  · ⛔ **这个解释被 959 的读数否掉了**：那 6 个画布控件在**按下之后**"
                "读出来 `tabindex = None`（**没有**该属性）⇒ "
                "**它们不是靠正 `tabindex` 排到前面的**\n"
                "  · ⇒ HTML 规范说「无 `tabindex` 的原生可聚焦元素按 DOM 序」"
                "⇒ 实测与之相反 ⇒ **剩下的可能性（shadow DOM / 应用自己搬焦点 / "
                "别的什么）本批一条都没测到**\n"
                "  · ⇒ ⭐⭐ **不许**把「源站按正 `tabindex` 排序」写进任何结论 —— "
                "那是**已被否掉的猜想**，不是「待查的猜想」\n"
                "  · ⇒ ⭐ 「未查明」与「否掉了」是**两件不同的事**，"
                "**记错哪一件都会让下一个人白查一遍**"),
            "dom_index_not_stable_959": (
                "⚠️⚠️⭐ **DOM 绝对下标逐轮整体偏移 2** ⇒ **不能当断言**：\n"
                "  · rep1 画布控件首枚 `dom#2263`、rep2 `dom#2265`；"
                "顶栏 `dom#60` / `dom#62` ⇒ **两轮**逐条**差 2**\n"
                "  · 但 **`Tab` 序（`seq` + `data-testid` 序列）两轮逐条相同**\n"
                "  · ⇒ ⭐⭐ **源站的 DOM 逐轮在动**（§930 早记过 77/76 两轮不同）⇒ "
                "**DOM 绝对下标只能比「相对大小关系」**（谁大谁小），"
                "**绝不能**写成「`dom_index == 2263`」这种绝对断言\n"
                "  · ⇒ 这也是 956 那条「周期/规模类断言必须**关系式**」的**又一次**印证，"
                "而且这次**在 DOM 层面**、不是节点层面"),
            "budget_caveat_959": (
                "⚠️ **本批只量到「完整的 out 段」，不是完整一圈** —— 如实记账：\n"
                "  · `N_LEAD_CAP = 140`，而第 2 次命中左栏落在**第 141 下**"
                "⇒ `n_lead_cap_hit = True`（2/2）⇒ `rail_seqs` 只有 1 个\n"
                "  · ⇒ 窗口是「从第 1 个左栏停靠点到预算耗尽」；"
                "**好在 out 段是连续的**（第 84–101 按、共 18 个）⇒ "
                "**「out 段 18 个」这个结论成立**，但**「一圈」这个说法不成立**\n"
                "  · ⇒ ⚠️⚠️ **顺带测到一条更重要的**：第 2 次命中左栏在第 141 下 ⇒ "
                "**源站这一轮的环长 ≈ 57**，而 954 那轮是 **102** ⇒ "
                "⭐⭐ **源站的环长逐轮在变**（956 说过「绝对环长不是稳定量」，"
                "**现在在源站侧也证实了**）⇒ 任何「源站环长 = N」的断言都不许写"),
        },
        "taborder_960": {
            # ── 批 960：**源站** 逐个否掉 959 留下的两个可能性（**纯读**）────────
            # 取样：探针 960，源站，登录态，视口 1512×1200，2 轮 × 1 格；
            # 十七助手 + 八段 JS 与 959 逐字相同（959 又与 957/955/954/953
            # 逐字相同 ⇒ 链式）⇒ **零新件仪器**；新件 `ROOT_JS`（**纯读**）。
            # 读法仍**绕开 `press_row`**（957 源站、958 复刻，两侧都实测过）。
            "shadow_root_refuted_960": (
                "⭐⭐⭐⭐ **959 留下的可能性之一「shadow root」被否掉了**（2/2）\n"
                "  · 判据：`document.activeElement.getRootNode()` 是 "
                "`#document` 还是 `ShadowRoot`\n"
                "  · 读数：out 段 18 个停靠点，**在 shadow root 里的 = 0**，"
                "**root 种类只有 `['#document']`** ⇒ `all_out_in_document = True`\n"
                "  · ⇒ ⭐⭐⭐ **这条否掉得很关键**：959 用 "
                "`document.querySelectorAll('*')` 取 `dom_index` 一直有个隐患 ——"
                "**若元素在 shadow root 里，那个下标口径就不成立**"
                "⇒ 现在**口径被证实成立** ⇒ ⭐ **959 的 DOM 读数不需要重做**"
                "（**不是**「959 错了」，是**「959 用对了口径」**，而此前**没验过**）"),
            "ti_rewrite_refuted_960": (
                "⭐⭐⭐⭐ **可能性之二「应用在 keydown 里改它们的 `tabindex`」"
                "也被否掉了**（2/2）\n"
                "  · 判据：按**前**记住那一枚元素的**引用**，按**后**回来看"
                "**同一个引用**（不是当前焦点）的 `tabindex`\n"
                "  · 读数：**离开时 `tabindex` 变过的 = 0** ⇒ "
                "`no_ti_changed_by_tab = True`（逐按 `before == after`）\n"
                "  · ⇒ ⭐⭐⭐⭐ **这把 959 的那个否掉**补强成**更彻底**的否掉："
                "959 只读到「按**之后**是 `None`」（那还留着「按下时被写过、"
                "读完又被清掉」的口子）；960 证明**离开时也没被改**\n"
                "  · ⚠️ 与 957 那条**并存不矛盾**：左栏的 `0` 是**常驻** roving"
                "（普查 `0`×1 + `-1`×9，957），而**画布控件那 6 个**"
                "**既无常驻 roving、也未被逐次改写**"),
            "unresolved_contradiction_960": (
                "⚠️⚠️⚠️⭐⭐ **机制仍然未查明，而且三条事实凑成了一组矛盾** —— "
                "**原样记账，不许圆**：\n"
                "  · **A**（960 实测 2/2）：18 个 out 元素**全在 `#document`**、"
                "**离开时都没被改过 `tabindex`**\n"
                "  · **B**（959 实测 2/2）：它们的 `Tab` 序**不是** DOM 序"
                "（`dom_index` 非单调，2/2）\n"
                "  · **C**（896 早已记过）：源站 keydown 的 `defaultPrevented=False`"
                "（**没拦**浏览器默认动作）\n"
                "  · ⇒ ⭐⭐ **A + C 蕴含「浏览器应当按 DOM 序走」，而与 B 矛盾**\n"
                "  · ⇒ ⚠️⚠️ **两条出路，本批一条都没验到**：(a) **C 已经过时** —— "
                "应用后来加了 `preventDefault()` 或在 `focusin` 阶段**主动 "
                "`focus()`**（那样顺序就是**它自己的表**、与 DOM 无关）；"
                "(b) **B 的 `dom_index` 口径还有本批没发现的问题**\n"
                "  · ⇒ ⭐⭐ **不许**编一个机制把它圆上；"
                "**「A、C 都对而 B 也对」这件事本身就是待查的线索**\n"
                "  · ⇒ ⭐ **下一批的第一件事就是查 C 是否过时**"
                "（逐按读那一按的 `keydown` 的 `defaultPrevented`）"),
            "first_version_criterion_was_wrong_960": (
                "⚠️⚠️⚠️⭐⭐ **第一版的判据是错的，被自己抓住**（在**落交付物之前**）：\n"
                "  · 我把 `ti_before`（按**前当前焦点**的 ti）与 `ti_after`"
                "（按**后新焦点**的 ti）拿去比 ⇒ 那是**两个不同元素**的 ti，"
                "「变了」**只说明两者恰好不同，不说明任何元素被改过**\n"
                "  · ⇒ 第一版读出的 `n_ti_changed = 2` **是无意义的数字**\n"
                "  · ⇒ ⭐⭐ **改法不是放宽判据，是改「盯谁」**：按**前**把那个元素的"
                "**引用**存下来（`window.__preEl`）、按**后**回来看**这个引用**\n"
                "  · ⇒ 改完重跑，**`n_ti_changed` 变成 0**\n"
                "  · ⇒ ⭐⭐⭐ **「两个不同元素的属性被当成同一个元素的前后变化」**"
                "是一种**极容易写出来、极难自己看出来**的错 —— "
                "**一个错的判据比没有判据更坏**（942）\n"
                "  · ⭐ **它没被锚点自查抓到、也没被 `py_compile` 抓到**，"
                "是**读自己那 18 行输出、发现 `None→None` 和 `'0'→None` "
                "不可能是同一个元素**才抓到的"),
            "out_path_overwrote_959_960": (
                "⚠️⚠️⚠️ **操作事故：960 第一版把 `OUT` 照抄成了 959 的路径** ⇒ "
                "**960 跑完把 959 的读数文件覆盖了**\n"
                "  · 起因：`cp` 959 做基底时只改了 `out[\"out\"]`、"
                "**忘了改模块级的 `OUT = \"/tmp/b959-domorder.json\"`** ⇒ "
                "`dump()` 照 `OUT` 写 ⇒ **959 的读数被覆盖**\n"
                "  · ⚠️ `out[\"out\"]` 与 `OUT` 是**两个各自独立的字段**，"
                "**改一个不改另一个不会报错**、也不会被任何既有门抓到\n"
                "  · ⇒ ✅ 已把 `OUT` 改成 `/tmp/b960-taborder.json` 并**重跑**"
                "（交付的读数必须由**提交的那份探针**产出）\n"
                "  · ⇒ ⚠️ 959 的读数**本地已丢**；但它的**判决**完整保存在"
                "`fb165bd7` 的 commit message、`README` §169 与本基线里 ⇒ "
                "**结论没有丢**\n"
                "  · ⇒ ⭐⭐ **纪律**：`cp` 一个探针当新基底时，"
                "**输出路径、读数文件名、基线键名**这三样**必须逐个核**，"
                "**它们不在任何一道现有门里**\n"
                "  · ⚠️⚠️⚠️ **本批又撞见 957 记的那件事**"
                "（`jimeng_check_verifier_anchors.py` **只验「那串字面量在文件里"
                "存在吗」**）：VVVV.1 的两条锚点我**多写了一对 `**`**，"
                "而探针里那两句**根本没有那对 `**`** ⇒ "
                "**锚点自查报「问题 0 个」、而门禁真红** ⇒ "
                "**第三次**栽在同一个地方 ⇒ ⭐⭐ "
                "**「锚点自查 0 问题」既不等于判据会过、也不等于锚点写对了**"),
        },
        "ticensus_961": {
            # ── 批 961：**源站** 普查**全文档** `tabindex`（**纯读**）───────────
            # 取样：探针 961，源站，登录态，视口 1512×1200，2 轮 × 1 格；
            # 十七助手 + 九段 JS 与 960 逐字相同（960 又与 959/957/955/954/953
            # 逐字相同 ⇒ 链式）⇒ **零新件仪器**；新件 `TICENSUS_JS`（**纯读**）。
            "blind_spot_closed_961": (
                "⭐⭐⭐⭐ **959/960 的读法盲区被堵上了 —— 而盲区里是空的**：\n"
                "  · 盲区：959/960 读 `tabindex` **只读「焦点所在的那一枚」**"
                "⇒ 读出的是 `'0'`（左栏 roving 那枚）或 `None` "
                "⇒ **「它们没有正 `tabindex`」这个结论只覆盖了"
                "「它们各自获得焦点的那一刻」**，**其它候选**当时的 `tabindex` "
                "**根本没读过**\n"
                "  · 961 改成**逐按普查全文档**所有原生可聚焦元素的 `tabindex`"
                "（`BUTTON`/`A`/`INPUT`/`SELECT`/`TEXTAREA` 且未 `disabled`）\n"
                "  · ⭐⭐⭐⭐ 读数（2/2 逐条相同）：**全文档原生可聚焦 112 个**，"
                "分布 = **`0`×1 + `None`×25 + `-1`×86**，"
                "**带正 `tabindex` 的 = 0 个**\n"
                "  · ⇒ ⭐⭐⭐⭐ **「靠正 `tabindex` 排序」这个解释被**彻底**排除** —— "
                "不只是那 6 个画布控件没有，是**整个文档一个都没有**\n"
                "  · ⇒ ⇒ 960 留下的矛盾**没有被解开、反而更硬了**"),
            "contradiction_hardens_961": (
                "⚠️⚠️⚠️⭐⭐ **矛盾加强了，而且现在只剩一个方向**：\n"
                "  · **A′**（961，2/2）：全文档**没有任何正 `tabindex`**；"
                "全部原生可聚焦元素要么 `-1`（86）、要么**无属性**（25）、"
                "要么 `'0'`（1，左栏那枚）；且都不在 shadow root 里（960）、"
                "离开时都没被改过 ti（960）\n"
                "  · **C**（**892 首测** 2/2、**896 复核**全 `False`，两处**都**用"
                "「派发结束后再读」的**正确取法**）：源站**没** `preventDefault`\n"
                "  · **B**（959/961，2/2）：`Tab` 序**不是** DOM 序"
                "（画布控件 `dom#2263–2396` 排在顶栏 `dom#60–177` 之前）\n"
                "  · ⇒ ⭐⭐ **A′ + C 蕴含「浏览器应当**严格**按 DOM 序走」**"
                "⇒ **与 B 直接冲突**\n"
                "  · ⇒ ⭐⭐⭐ **剩下的方向只剩一个**：源站在 `keydown` **之后**"
                "（`focusin` / 宏任务 / `requestAnimationFrame`）**主动 `focus()` "
                "到下一枚** ⇒ 那样 `defaultPrevented` 仍是 `False`（**没拦**，与 C 不矛盾）、"
                "`tabindex` 也**不用改**（与 A′ 不矛盾），"
                "而顺序**来自它自己的表**\n"
                "  · ⇒ ⭐⭐⭐ **这才是复刻真正要对齐的东西** —— 不是 DOM 序、"
                "也不是 `tabindex` 序，而是**应用自己维护的那张焦点顺序表**"),
            "where_961_almost_made_the_same_mistake_961": (
                "⚠️⚠️⚠️ **更正一处出处 —— 而我第一版的「更正」本身就是错的**"
                "（961 **自己抓到**）：\n"
                "  · 960 §二 的表把 C（`defaultPrevented=False`）的出处写成 **896**\n"
                "  · ⚠️⚠️⚠️ **896 确实测过**：它第 55 行明写「`defaultPrevented` 用 "
                "**892 的取法**」、汇总里有 `keydown_defaultPrevented_seen`、"
                "结论**全 `False`** ⇒ **960 那处引用不算错**\n"
                "  · ⇒ ⭐ **准确的说法是「892 首测（2/2 `False`）＋ 896 复核（全 `False`）」**"
                "⇒ **C 有两个出处、都站得住**，矛盾**依然存在**\n"
                "  · ⚠️⚠️⚠️ 我 961 第一版写的是「**不是 896**」⇒ **那一句是错的**\n"
                "  · ⇒ ⭐⭐ **由此钉住一条新纪律**：**更正出处时，不许只查「被指的那一处」**"
                "—— 要查**「真正测过这一项的还有哪些探针」**，"
                "否则会把「指错了」误判成「没测过」，**再制造一个假更正**\n"
                "  · ⇒ ⚠️ 这是**同一天内第二次**栽在「引读数不看原出处」上"
                "（第一次是 960 那个 `OUT` 照抄）⇒ "
                "**引用纪律要查两遍：路径查一遍、来源也查一遍**"),
            "two_censuses_961": (
                "⚠️⚠️ **同一次跑里有两个普查，口径不同、数字不可比**：\n"
                "  · `census_ti_hist`（≈50 几）= `RAIL_JS`，范围**只有左栏那一个容器**"
                "内部全部 `*`（**不是**「原生可聚焦」口径）\n"
                "  · `ti_hist`（≈110 几）= `TICENSUS_JS`，范围是**整个 `document`** 的"
                "原生可聚焦元素 ⇒ 961 的判决**只认后一个**\n"
                "  · ⇒ ⚠️ **差点踩**：日志里那句 `普查：ti 分布` 两种都像 ⇒ "
                "已改成 `左栏普查（RAIL_JS，范围=左栏容器）`，并在读数里补 `census_scope`\n"
                "  · ⇒ ⭐ **口径必须写在产物里**，不能只存在于跑的人脑子里"),
            "own_gate_missing_961": (
                "⚠️⚠️⚠️ **961 自己抓到两个缺陷，都改了、都重跑了**：\n"
                "  · ① `out[\"domidx_note\"]` **原文是 960 照抄来的**、还在讲 960 的"
                "两个可能性 ⇒ **交付的读数文件里「本批问什么」被标错**了"
                "（`question` 才是对的）⇒ 与 960 那个 `OUT` 事故**同类、不同面**\n"
                "    —— 那回毁的是**读数文件**，这回毁的是**读数文件里的一个说明字段**\n"
                "  · ② ⭐ 探针的 `design_gates` 里**没有 961 判决自己的门**"
                "（960 有「两道**可红**判决门」的先例，961 漏了）⇒ 已补 "
                "`no_positive_tabindex` + `ti_hist_stable_across_stops`\n"
                "  · ⇒ ⭐ **「可红」的门必须和判决同时落进探针**：门写在别处、"
                "读数先跑完，才发现「没门」时已经不知道当时该不该红\n"
                "  · ⇒ ⚠️ 顺带把 961 的派生键补登记进 `DERIVED_KEYS`"
                "（`positive`/`ti_hist` 是**原始**读数，不能混）"),
            "anchor_hole_961": (
                "⚠️⚠️⚠️⭐⭐ **锚点自查里有一个「静默跳过」的洞，961 把它堵上了**：\n"
                "  · 收集器对**未登记**的变量是**裸 `continue`** ⇒ 判据引了一个没登记的"
                "变量时，那几条锚点**一条都不查、且连提示都没有**\n"
                "  · ⇒ **`_p957`–`_p960` 一直漏登记** ⇒ 957–960 **四批**的探针锚点"
                "**一次都没被自查过**（只有指向 `_ausrc` 的被查了）\n"
                "  · ⇒ 补登记后：锚点总数 **2411 → 2853**（**+442**），"
                "其中新增受检 235 条**实测 0 问题**\n"
                "  · ⚠️⚠️⚠️⭐⭐ **补登记当场抓出一条真问题**：M.6 的判据是 "
                "`\"只有 1 项\" in lsrc or … in <audit>`，而 `jimeng_kb_probe_lib.py` "
                "里「只有 1 项」**出现 0 次** ⇒ **第一个析取支恒假**，"
                "这条判据一直**只靠第二个析取**撑着\n"
                "  · ⇒ ⭐ **改法不是放宽门，是删掉那句从来不真的话**（判据强度不变）\n"
                "  · ⇒ ⭐⭐ **教训**：「0 问题」+「没报错」**可能只是没人查**；"
                "**覆盖率的洞必须显式报出来**，否则自查会一直假绿\n"
                "  · ⇒ ⚠️ 剩下 167 条锚点（30 个变量）**确实是字典/切片/循环变量**、"
                "不是文件源 ⇒ **不当门**（会误报），但**已改成逐条打印**"
                "（`SKIPPED-未登记`）⇒ **洞不再无声**"),
            },
            "clicksel_966": {
                # ── 批 966：**源站** 行为侧 —— 点选那枚 vs 点选两个邻居 ─────────
                # 取样：探针 966，源站，登录态，视口 1512×1200，2 轮 × 1 格；
                # 助手与 JS 与 965 逐字相同（链式）⇒ 新件 `CLICKPLAN_JS` + `STATE_JS`。
                "what_966_measures": (
                    "⭐⭐⭐⭐ 965 之后只剩**行为侧**可查：那枚节点被**点选**时"
                    "是否与邻居不同（**选中态 / 编辑态 / 是否开层**）\n"
                    "  · ⚠️⚠️ **每枚都重新 `boot()` 归零**（源站侧「层开过后 "
                    "Esc 关不掉」的老坑）\n"
                    "  · ⚠️⚠️ **不盲点**：节点 `offset_*` 是 320（`dpr=2`）而**视觉盒"
                    "只有 160**，且**节点内部有可聚焦控件**（963 见过「替换媒体」）"
                    "⇒ **点之前先纯读地确认「那个坐标上到底是什么」**\n"
                    "  · ⭐ 落在**按钮/输入框**上就**不点**、如实记「**因为点上不安全"
                    "而没点**」——这正是老教训「**我没做到**」要先确认「**我够不够得着**」\n"
                    "  · ⚠️ ⛔ 守卫照旧拦在 `page.mouse.click` **之前**；"
                    "**不碰生成/发送/购买/充值**"),
                "slice_guard_fired_twice_966": (
                    "⚠️⚠️ **切片守卫这一批响了两次，都是它对**：\n"
                    "  · ① `wrapper_cls` 写成 `(wrap.className || '').toString()"
                    ".slice(0, 120)` ⇒ 中间插了 `.toString()` ⇒ 与守卫要的"
                    "**紧挨着**的字面量对不上\n"
                    "  · ② `layers.sort().slice(0, 40)` ⇒ 那是**数组**切片 ⇒ "
                    "守卫直接判「**非字符串**切片（§131）」\n"
                    "  · ⇒ ⭐ 两处的改法**都不是放宽守卫**：① 改成逐字相邻的写法；"
                    "② **不截断**（层本来就不多）\n"
                    "  · ⇒ ⭐⭐ **数组切片会把「前 N 个」当成规律**（§131 的本意）"
                    "⇒ **这条守卫两次都替我挡住了一个会污染读数的写法**"),
                "all_four_paths_exhausted_966": (
                "⭐⭐⭐⭐ **四条路全部走完的总结**（963 `tabindex` / 964 解剖 / "
                "965 可聚焦性 / 966 行为）⇒ **那枚与邻居在所有可观察维度上无异** ⇒ "
                "**跳过是应用自己表里的一个选择**，**没有 DOM 表达式**\n"
                "  · ⇒ ⭐⭐ **对复刻不变**：**按纯 DOM 序实现 + 把这一枚记为"
                "已知差异**（NN.2 的处置依然成立）\n"
                "  · ⇒ ⚠️ **「未查明」到此为止是**有穷尽依据**的**："
                "不是「懒得查」，是**四个维度都查完了、结论是「没有差异」**"),
            "three_more_traps_966": (
                    "⚠️⚠️⚠️ 966 在**跑起来之前**又踩了三个坑，三个都**当场抓住**：\n"
                    "  · ① ⭐⭐ **`READ_FM_JS` 的名字被写成了 `READ_FT_JS`** —— 而"
                    "**函数体是 `READ_FM_JS` 的读走逻辑** ⇒ 与上面那个 `READ_FT_JS` "
                    "**同名覆盖** ⇒ 走查循环里的 `ev(READ_FM_JS)` 直接 **`NameError`**\n"
                    "    ⇒ ⭐ **教训**：**复制/插入时必须核「名字」和「函数体」是不是"
                    "同一对**（这一族已栽过 `OUT`、切片守卫、`__fm` 闩锁…）\n"
                    "  · ② ⭐⭐ **把 Python 的 `#` 注释留在了 JS 字符串里** ⇒ "
                    "`#` 不是合法 JS ⇒ **运行时才炸**，而⚠️ **静态 JS 语法门"
                    "**没抓到它** ⇒ **那也是一条要记的洞**（静态门有覆盖不全的问题）\n"
                    "    ⇒ 改法：`//` 注释；并**逐段扫一遍「JS 字符串里有没有 `#`」**\n"
                    "  · ③ ⚠️ 我给两道新门**少写了一个右括号**（`bool(all(` 需要 `))`）"
                    "⇒ `py_compile` 直接报「`}` 与 `(` 不匹配」⇒ "
                    "**这是最便宜的一类错**（语法门当场抓住，零成本）\n"
                    "  · ⇒ ⭐⭐ **三个坑的共同点**：**都在跑之前被抓住**、"
                    "而且**都是「复制/插入」这一动作带进来的** ⇒ "
                    "**改完必须 `py_compile` + JS 语法门 + 一次干跑**，"
                    "**三样都要过再谈读数**"),
            },
            "armptr_967": {
                # ── 批 967：**源站** 把 900 与 963 的两个数**放在同一张表里对账** ──
                # 取样：探针 967，源站，登录态，视口 1512×1200，2 轮 × 1 格；
                # 尺子（`BLANK_JS`/`CENSUS_JS`/`FOCUS_JS`/`WHOAMI_JS`/
                # `NODECENSUS_JS`/`boot_fn`）逐字来自 966/952（`assert _js in
                # `_p966src` 证明）⇒ 新件 `INSTALL_JS` + `READ_JS` +
                # `ARMED_ONLY_JS` + `OFF_NULL_JS`。读数 `/tmp/b967-armptr.json`。
                "what_967_measures": (
                    "⭐⭐⭐⭐ **900 与 963 的两个数从来没有被放在同一张表里对过账**\n"
                    "  · 900 说「**被布上 `'0'`**」漏 **2** 个（`b22-upload` / "
                    "`音频 61`）；963 说「**被 `Tab` 落到**」漏 **1** 个（`音频 61`）\n"
                    "  · ⇒ **两者不等** ⇒ 967 **不复述**任何一个数，而是**在同一轮里"
                    "同时量这两个可观测量**\n"
                    "  · ① **布防指针**：每一按在 **4 个取样点**各读一次"
                    "「带 `tabindex='0'` 的节点**全量**集合」—— `pre`(`window` 捕获)"
                    " / `post`(`window` 冒泡) / `task`(`setTimeout(0)`) / "
                    "`after`(按后 350ms)\n"
                    "    ⚠️ **不预设「布防发生在哪一刻」**（965 已证按后属性**不是**"
                    "被摘掉）⇒ 由读数说话，**不猜机制**\n"
                    "  · ② **落焦**：每一按记 `focusin` 的目标，并**拆成** "
                    "`self`（节点本体）/ `inner`（**节点的内层控件**）/ `out`\n"
                    "    ⚠️ 963 那套把 `self` 与 `inner` **合在一起**算 ⇒ 这里拆开\n"
                    "  · ③ 对账三个集合（`ever_armed` / `ever_landed_self` / "
                    "`ever_landed_inner`），**按 `data-testid` 身份**、"
                    "**不按绝对下标**（逐轮会漂，961 已量过）"),
                "recon_967_two_observables": (
                    "⭐⭐⭐⭐⭐ **900 与 963 都没错 —— 它们量的不是同一件事**"
                    "（源站 2/2 轮**逐项一致**）：\n"
                    "| 可观测量 | 谁量的 | 76 个里漏掉的 |\n"
                    "|---|---|---|\n"
                    "| **被布上 `'0'`** | 900 | **2**：`图片 node: b22-upload`、"
                    "`音频 node: 音频 61` |\n"
                    "| **被 `Tab` 落到**（本体**或**内层控件） | 963 | **1**："
                    "`音频 node: 音频 61` |\n"
                    "  · ⭐⭐⭐ **`n_never_armed` = 2、`n_never_landed` = 1** ⇒ "
                    "**900 那个数第一次被复核成功**（966 的 `FOCUSMOVE_JS` 只记了 "
                    "`{armed: true}` 这个**闩锁**、**不记是哪一枚** ⇒ 此前**无法复核**）\n"
                    "  · ⭐⭐⭐ **差集恰好 1 枚** = `n_landed_never_armed` = "
                    "`{图片 node: b22-upload}` ⇒ **它落上过，但从不是落焦「本体」**\n"
                    "    · 它唯一两次落焦（seq 17 / seq 118，**2/2**）都落在**它内层的 "
                    "`替换媒体` 按钮**上；那两按应用布的 `'0'` 都是 "
                    "`音频 node: 音频 7`，**与它无关**\n"
                    "    · ⇒ 它**不是「不被选中」，而是「压根没进过指针」**："
                    "焦点是**浏览器原生 `Tab` 走进它内层控件**的结果\n"
                    "  · ⭐⭐⭐ **反向差集 `n_armed_never_landed` = 0** ⇒ "
                    "**布防是落焦的充分条件**\n"
                    "  · ⭐⭐ **`音频 node: 音频 61` 才是唯一一枚既没被布、也没被落上的"
                    "节点** ⇒ 963/964/965/966 那四条维度的「跳过」**只对这一枚成立**"),
                "self_equals_armed_967": (
                    "⭐⭐⭐ **落焦落在「本体」的那 104 按（2/2 轮逐次一致）"
                    "**全部**等于「当按 `post` 取样点上被布上 `'0'` 的那一枚**、"
                    "**零例外** ⇒ **布防 ⇒ 落焦**\n"
                    "  · ⚠️ 与之相对，`focus==armed(pre)` 只占 6/104 ⇒ "
                    "指针确实**每一按都在前进**（`pre` 上留着的 `'0'` 是上一按那一枚，"
                    "正是 ⑦「此后不回撤」，896/907 已记）\n"
                    "  · ⇒ 这条是复刻 ③「本函数只负责**先把目标装进 `Tab` 序列**、"
                    "真正的焦点移动交给浏览器原生 `Tab`」所依赖的前提，**现在有直接读数**了"),
                "corrects_965_967": (
                    "⚠️⚠️⚠️⭐⭐⭐⭐ **更正 965 §二 的一句越界推论**（965 **主判决不动**）：\n"
                    "  · 965 原文：「被跳过的那枚 `el.tabIndex === -1`，**而** "
                    "`getAttribute('tabindex')` 是 `None` ⇒ 浏览器**原生 `Tab` 根本不会停在"
                    "这些 `div` 节点上** ⇒ **应用必须自己调 `focus()`** 才能让节点可达」\n"
                    "  · ⇒ ⭐⭐⭐⭐ **那个 `-1` 只说明「那一瞬间它身上没有 `tabindex` 属性」**\n"
                    "    · 它读自 **965 那个孤立的 `focus()` 测试**（脚本直接对节点调 "
                    "`focus()`，那时节点没被布过防）\n"
                    "  · ⇒ **走查里的落焦节点 106/140 读到的 `tabindex` 就是 `'0'`**"
                    "（另 34 读 `None`，是落焦到**内层 BUTTON** 的那些按）\n"
                    "  · ⇒ ⭐⭐⭐ 而且 **`'0'` 在按后 350ms 仍然布着**（`after` 取样点："
                    "140/140 按都能读到布防集合）⇒ **`tabindex='0'` 确实把这些 `div` "
                    "装进了 `Tab` 序列**，**不撤**正是 ⑦「此后不回撤」\n"
                    "  · ⇒ ⇒ ⭐⭐⭐ **「A ≠ B」不等于「A 能把 A 从 C 里挑出来」**"
                    "（老坑，第 N 次；同族还有 964 的「A ≠ B」门）\n"
                    "  · ⇒ ⚠️ **原样成立、不动**的部分：965 的**主判决**——"
                    "「`focus()` 同步落上、四个时点都没被拽走 ⇒ 既不是「不可聚焦」、"
                    "也不是「被 `focusin` 拽走」」——**与 967 无冲突**"),
                "discipline_967": (
                    "① ⭐ **不预设「布防的时刻」** ⇒ 4 个取样点全记、由读数说话；\n"
                    "  · ② ⚠️ `post`（`window` 冒泡）**可能被 `stopPropagation` 掐掉** ⇒ "
                    "`task` 排在 **`pre`（捕获段永远第一个跑）**上 ⇒ "
                    "`fired`/`pre`/`task` 三者**必然配平**（门 `fired_eq_rows`）\n"
                    "  · ③ `INSTALL_JS` **幂等**（装之前先摘干净）⇒ 连按两次不叠监听器；\n"
                    "  · ④ **`finally` 里无条件复查 `__ap_off`** ⇒ `break` 掉循环也不漏摘；\n"
                    "  · ⑤ **两轮比较按身份、不按下标**，且**在 `for rep` 之外**；\n"
                    "  · ⑥ ⭐ **每道门都挂在独立分母上**：`armed_read_is_live` 要求"
                    "`n_armed_presses>0` **且** `armed_distinct_tids>=10`"
                    "（**防「仪器读的是常量」**）、`census_stable_in_rep` 挂在"
                    "`n_nodes_hist` 的**取值个数**上\n"
                    "  · ⑦ ⭐⭐ **干跑当场抓到一处真错**：`RAW_KEYS` 与 `DERIVED_KEYS` "
                    "**重了 `blank`** ⇒ 键账免疫针**在跑之前就红**\n"
                    "    ⇒ ⇒ ⭐ **门有牙的证明**：干跑喂假数据时 "
                    "`armed_read_is_live` / `landing_channels_both_present` "
                    "**直接判红** ⇒ 它们**不是恒真门**\n"
                    "  · ⑧ ⭐ **判词不许预写**：探针只输出 `recon`（**纯数字**），"
                    "本段判词是**读过 `/tmp/b967-armptr.json` 的原始读数之后**才写的"),
            "replicarmptr_968": {
                # ── 批 968：**复刻侧** 用 **967 同一把尺子**复核那两条机制 + 步长 ──
                # 取样：探针 968，复刻 `http://localhost:4317/jimeng/canvas/demo`，
                # 视口 1512×1200，2 轮 × 1 格，**零节点点击**（插节点走左栏入口）。
                # ⭐ 四段仪器 + 四段尺子**逐字来自 967**（`_grab` + `assert _s in
                # `_p967src`）⇒ 两侧数字**才可比**。读数 `/tmp/b968-replica-armptr.json`。
                "what_968_measures": (
                    "⭐⭐⭐⭐ **967 在源站新钉的三条，全部拿到复刻侧各验一遍**\n"
                    "  · 判据是**关系式**的、**不是绝对值**（复刻节点数与源站不同、"
                    "也没有那一枚被跳过 ⇒ 数字本就不该相等）\n"
                    "  · ① **布防 ⇒ 落焦**：落焦落在「本体」的那些按里，"
                    "落点下标 **==** 当按 `post` 取样点上布上的下标\n"
                    "  · ② **`'0'` 不撤**：`after` 取样点（按后 350ms）仍读到布防集合\n"
                    "  · ③ **步长分布**：`+1` / `+2` / `gt2` / `wrap` 四类，"
                    "**回折单独记成一类**\n"
                    "  · ⇒ ⚠️ **分母要对**：步长门的分母是 `step_pairs`、"
                    "**不是** `n_lead`（`n_lead` 里混着 chrome 停靠点）"),
                "mechanism_two_rules_hold_968": (
                    "⭐⭐⭐⭐ **967 那两条机制规则在复刻侧同样成立**（2/2 轮逐项一致）：\n"
                    "| 规则 | 源站（967） | **复刻（968）** |\n"
                    "|---|---|---|\n"
                    "| **布防 ⇒ 落焦** | `self_eq_armed` = `n_self_rows` = **104/104** | "
                    "= **14/14** |\n"
                    "| **`'0'` 不撤** | `n_armed_after_rows` = `n_armed_presses` = "
                    "**140/140** | = **80/80** |\n\n"
                    "  · ⇒ ⭐⭐⭐ 复刻的 `armAll` **只写不撤** ⇒ 与源站 ⑦「此后不回撤」"
                    "**同一条规则**；「布了防就落焦」在复刻侧**零例外**\n"
                    "  · ⇒ ⭐⭐ `armed_point_hist` = `{\"pre\": 80}` ⇒ 布防在"
                    "**每一按开始时就已存在** ⇒ 与源站 `{\"pre\": 139, \"post\": 1}` "
                    "**同一形状** ⇒ arming 的**时机**也对上了"),
                "steps_dom_order_968": (
                    "⭐⭐⭐⭐ **步长：复刻严格按纯 DOM 序**（2/2 轮逐项一致）\n"
                    "  · 复刻 `step_hist` = `{\"+1\": 12, \"wrap\": 1}`（13 个步长对、"
                    "14 个「落焦本体」的落点）⇒ **`gt2` = 0、`+2` = 0**\n"
                    "  · ⇒ **算术自洽**：7 个节点走两圈 = 14 个落点；"
                    "首落点无前驱、其后 6 个 `+1`、回折 1 次、再 6 个 `+1` "
                    "= `+1`×12 + `wrap`×1 ✅\n"
                    "  · ⇒ ⭐ **与源站对照**：源站 963 是 `{+1: 103, +2: 1, 折返: 1}`"
                    "（106 个落点、**恰好漏一枚**）⇒ **复刻比源站「干净」**："
                    "**既没有 `+2`，也没有漏** ⇒ 这正是 **967 写进实现的处置**"
                    "（「按纯 DOM 序 + 把那一枚记为已知差异」）**确实落地了**\n"
                    "  · ⇒ ⚠️⚠️ **`wrap` 必须单独记成一类**：走查**绕一圈** ⇒ "
                    "相邻落点**必然**有一次回折 ⇒ ⭐ **「非单调」根本推不出「乱序」**"
                    "（962 栽过：下降**恰好 1 次**、方向 `high_to_low`）"),
                "three_sets_align_968": (
                    "⭐⭐⭐ **复刻三张集合两两对齐**（2/2）：`n_never_armed` = **0**、"
                    "`n_never_landed` = **0**、`n_landed_never_armed` = **0**\n"
                    "  · ⇒ 复刻**没有任何**「布了不落」或「落了没布」的节点 "
                    "（`armed_distinct_tids` = 7 = 节点总数）\n"
                    "  · ⇒ ⭐⭐ **这正是**与源站的**已知差异**：源站那两枚"
                    "（`b22-upload` 落了却没布 / `音频 61` 既没布也没落）"
                    "**复刻刻意不复刻** ⇒ NN.2 的处置成立"),
                "inner_stops_968": (
                    "⭐⭐ **复刻的内层落点 4 个节点、23 次**（2/2）：\n"
                    "  · 视频节点（下标 0）5 个：`Add tags` / `播放` / `底部播放` / "
                    "`取消静音` / `全屏预览`\n"
                    "  · 时间线（下标 4）6 个：`导入` / `删除时间线` / `导出时间线` / "
                    "`全屏编辑` / `静音` / 一个无 `aria` 的\n"
                    "  · 主体（下标 5）6 个：`编辑主体` / `主体描述`（**`INPUT`**）/ "
                    "`导入主体` / `从画布选择` / `从资产库选择` / `本地添加`\n"
                    "  · 导演台（下标 6）1 个：无 `aria`\n"
                    "  · ⇒ ⚠️ **与源站的形状不同**：源站每圈的 `inner` 落点只有"
                    "时间线 4 个 × 2 个节点 ＋ `b22-upload` 的 `替换媒体`\n"
                    "  · ⇒ ⇒ ⭐ **机制相同、数字不同**（两侧节点数与控件集都不同）⇒ "
                    "**只可对账机制、不可对账绝对个数**"),
                "weak_gate_fixed_968": (
                    "⚠️⚠️⚠️ **步长那道门第一版太弱，是干跑当场抓到的**：\n"
                    "  · 第一版只查 `n_step_gt2 == 0` ⇒ 在「**全部是 `wrap`、"
                    "`+1` 一次都没有**」的**退化数据**上**照样绿**\n"
                    "  · ⇒ 按 942 的纪律**改严**：再加「**`+1` 真的出现过**」"
                    "**且**「**回折真的出现过**」\n"
                    "  · ⇒ ⭐⭐ **改完之后双向可验**：退化数据 ⇒ 判红；"
                    "合理数据（`{\"+1\": 102, \"+2\": 10, \"wrap\": 15}`）⇒ 转绿\n"
                    "  · ⇒ ⭐ **一道门必须能红、能不红**；只会绿的门**比没有门更坏**"),
            "nextjsportal_968b": {
                # ── 批 968b：纯读 —— 复刻 out 段第 17 个停靠点 `NEXTJS-PORTAL` ──
                "count_equal_but_set_not_equal_968b": (
                    "⭐⭐⭐⭐⭐ **「数目相等」不等于「集合相等」** —— "
                    "而长期待办「复刻缺的项目面板停靠点」**差点被错关掉**：\n"
                    "  · 968 的 out 段实测 **18 个**停靠点，源站也 **18 个** "
                    "⇒ **数目一模一样**\n"
                    "  · ⚠️⚠️ **其中第 17 个是 `NEXTJS-PORTAL`** —— "
                    "`aria=None`、`data-testid=None`\n"
                    "  · ⇒ 纯读复查（探针 968b，**零点击零按键**）："
                    "`parent_tag` = **`SCRIPT`**、`n_children` = **0**、"
                    "`innerHTML` = **空**、`rect` = **`[0,0,0,0]`**、"
                    "`has_tabindex` = **`False`**、`is_focusable` = **`False`**\n"
                    "  · ⇒ ⭐⭐⭐ **它压根不是复刻的 UI 元素**，是 **Next.js 开发态"
                    "注入的 runtime 节点**（仓里搜不到任何 `nextjs-portal` / "
                    "`NEXTJS-PORTAL` 的自写实现）\n"
                    "  · ⇒ ⇒ 复刻**真正的** out 停靠点是 **17 个**，"
                    "源站 **18 个** ⇒ ⭐ **差的那一个仍然是「项目面板」**\n"
                    "  · ⇒ ⇒ ⭐⭐⭐ **待办不许关**：这个「巧合的 18」差一点就被"
                    "当成「已补齐」而结案\n"
                    "  · ⇒ ⇒ ⭐ **纪律**：**数目对齐只是线索、不是结论** —— "
                    "必须**逐个核身份**（`tag` / `aria` / 最近 `data-testid`）\n"
                    "  ·\n"
                    "  · ⚠️⚠️⚠️ **本条已被批 969 推翻**，原文保留、不删：\n"
                    "    「差的那一个仍然是项目面板」**是错的** ⇒ "
                    "**错因：拿 954 的历史基线当本轮对照，没有在同一轮重测源站**"
                    "⇒ 详见下一条 `projectpanel_969`"),
            "projectpanel_969": {
                # ── 批 969：**源站**同轮重新量 out 段 ⇒ ⭐⭐⭐⭐⭐ **推翻 968b
                #   自己刚下的结论**（错在「拿历史基线当本轮对照」）────────────
                # 取样：探针 969，源站，登录态，视口 1512×1200，2 轮 × 1 格；
                # ⭐ 四段仪器**逐字来自 967**（`_grab` + `assert`），
                # 新件 `FINGER_JS`（**只读属性、不调 `focus()`**）。
                # 读数 `/tmp/b969-projectpanel.json`。
                "panel_judgement_found_nothing_969": (
                    "⚠️⚠️⚠️⭐⭐⭐⭐⭐ **本批的判决是一条否定结果，"
                    "而且它推翻的是上一批自己刚下的结论**。\n"
                    "  · 判据是「out 停靠点里 **`host_tid is None`** 的那些」"
                    "（**不是**按 aria —— 「项目面板」只是我自己起的名字，"
                    "拿它匹配就等于把结论写进判据）\n"
                    "  · 读数（**2/2 轮逐项一致**）：`n_out_stops` = **17**、"
                    "**`null_tid_rows` = 0** ⇒ ⭐ **本轮 out 段 17 个停靠点"
                    "全都带真 `data-testid`，一个 `tid=None` 的都没有**\n"
                    "  · ⇒ ⭐⭐⭐ **判据门 `panel_judgement_is_live_both_reps` "
                    "如实判红** —— 这正是它该做的：判据恒 0 时**必须**报出来，"
                    "而不是让这一批安静地写下「0 个 ⇒ 没有这个东西」\n"
                    "  · ⇒ ⭐⭐⭐⭐ **历史条目本轮不在线**：954 记的那个 "
                    "`out:测试项目…已保存…分享`，其 `aria` 来自 **`WHOAMI_JS` 的 "
                    "innerText 回退**（**不是** `aria-label`；969 只读 "
                    "`getAttribute('aria-label')`、**不回退**）"
                    "⇒ 且内容含「**已保存**」这种**瞬时状态**\n"
                    "  · ⇒ ⇒ ⚠️ **未复现、成因未查明** ⇒ **待办不许直接关**，"
                    "但「**复刻缺一个**」这个说法必须改（见下条）"),
                "corrects_968b_969": (
                    "⚠️⚠️⚠️⭐⭐⭐⭐⭐ **968b 那句「复刻真正的 out 停靠点是 17 个、"
                    "源站 18 个、差的那一个仍然是项目面板」是错的** ——\n"
                    "  · **错因**：**拿 954 的历史基线当本轮对照**，"
                    "**没有在同一轮重新量源站**\n"
                    "  · ⇒ 本轮**同轮实测**：源站 **17**、复刻 **16 真 + 1 个"
                    "开发态产物** ⇒ **数目本来就相同**\n"
                    "  · ⇒ ⭐⭐⭐⭐⭐ **集合逐个对完，两侧是同一组**（16 个身份全对上）：\n"
                    "    · 三处 aria 文本不同 —— **全是数据/默认值，不是结构差异**：\n"
                    "      `Canvas node summary: 节点 76`（源站，76 个节点）"
                    "vs `节点 7`（复刻，7 个节点）；`Credits: 791`（源站）"
                    "vs `745`（复刻）；`Zoom options, 50%`（源站）vs `73%`（复刻）\n"
                    "    · ⇒ ⭐ **唯一真实的结构差异只有一处**："
                    "「更多」的 `data-testid` —— 源站 **`canvas-editor-menu`**、"
                    "复刻 **`canvas-more-trigger`**\n"
                    "    · 加上复刻侧的 `NEXTJS-PORTAL`（968b 已证是 "
                    "**Next.js 开发态产物**）\n"
                    "  · ⇒ ⇒ ⭐⭐⭐ **挂了几十批的待办「复刻缺的项目面板停靠点」"
                    "应当结案为「本轮两侧同组、结构相同」**；**剩下的未复现项是"
                    "「954 那个瞬时状态条目本轮不在线」，与复刻无关**\n"
                    "  · ⇒ ⇒ ⭐⭐⭐ **纪律（本批最值钱的一条）**：**同一件事要对比，"
                    "就得在同一轮量两侧** —— 拿**历史基线**当本轮一侧的对照，"
                    "会把「基线过期」误读成「实现有缺陷」\n"
                    "  · ⇒ ⇒ ⭐ **968b 自己也留了后手**（「数目对齐只是线索、"
                    "不是结论」）—— 它的**方法**对、**收尾那一句**跳过了"
                    "「先重新量源站」这一步 ⇒ ⭐ **判据对不等于结论对，"
                    "收尾那一步同样要查**"),
                "one_real_structural_diff_969": (
                    "⚠️⚠️⚠️⭐⭐⭐⭐⭐ **本条已被批 970 整条推翻，原文保留、不删。**\n"
                    "  它犯的是**「口径不同当同一件事比」**：读的是 `closest()`"
                    "（**最近祖先**）那个字段，却拿它当「**元素自己的** "
                    "`data-testid`」在讲 ⇒ **两处都错**：\n"
                    "  ① 「更多」：源站**元素自己**没有 testid（816 早就写过、"
                    "还列进了 `KNOWN_CLONE_ONLY`）⇒ 那是**有意偏离**、**不该改**；\n"
                    "  ② ⭐⭐⭐ **本条把 `生成历史` 误列成「对齐」** —— "
                    "源站 `canvas-panel-launcher`（与「搜索」**共用**）、"
                    "复刻 `canvas-history-launcher` ⇒ **那是第二处有意偏离**"
                    "（816 也记过：照抄会同时命中 2 个元素、打破 801 的断言）\n"
                    "  ⇒ 正确的同口径结论见下一条 `owntid_970`。\n"
                    "  · —— 以下是 969 的**原文**：\n"
                    "  ⭐⭐⭐ **唯一真实的结构差异：「更多」的 `data-testid` 不一致**\n"
                    "  · 源站 = **`canvas-editor-menu`**｜复刻 = **`canvas-more-trigger`**\n"
                    "  · ⇒ ⚠️ **下一批的产品候选**：改 `data-testid` 即可对齐，"
                    "**但**必须先核「这个 testid 在别处有没有被引用」"
                    "（**不许**为了对齐而打断别的读数）\n"
                    "  · ⇒ ⇒ ⭐ **其余全部对齐**：`返回首页`/`canvas-project-logo`、"
                    "`Canvas title: 测试项目`/`canvas-project-title-trigger`、"
                    "`项目`/`canvas-project-trigger`、"
                    "`Canvas node summary`/`canvas-node-summary-trigger`、"
                    "`搜索`+`生成历史`/`canvas-panel-launcher`、"
                    "`分享`/`canvas-share-trigger`、"
                    "`Credits`/`canvas-commerce-entry`、"
                    "`用户菜单`/`canvas-user-menu-trigger`、"
                    "`文本`/`canvas-fixed-toolbar`、"
                    "`选择工具`/`canvas-pointer-tool-toggle`、"
                    "`小地图`/`canvas-display-toggle-minimap`、"
                    "`显示连线`/`canvas-display-toggle-connections`、"
                    "`Zoom options`/`canvas-zoom-percent`、"
                    "`与 AI 对话`/`canvas-sidecar-launcher`、"
                    "`Canvas`/`rf__wrapper`"),
            "owntid_970": {
                # ── 批 970：**复刻侧**同口径重测（自身 tid + 祖先 tid 都读）──
                # 取样：探针 970，复刻，**零插入、零节点点击**，2 轮 × 1 格；
                # ⭐ 四段仪器**逐字来自 967**（与 968/969 同一把尺子），
                # 新件 `OWN_JS`（**只读属性、不调 `focus()`**）。
                # 读数 `/tmp/b970-replica-owntid.json`；
                # 源站一侧**复用 969 的读数**（969 的 `FINGER_JS` 本来就
                # **同时**记了 `tid` 与 `host_tid` ⇒ **两张表同口径**）。
                "same_caliber_970": (
                    "⭐⭐⭐⭐⭐ **同口径重做那张表之后，结论完全变了**：\n"
                    "  · 复刻 out 段实测 **19 类**（其中 `NEXTJS-PORTAL` 是 "
                    "**Next.js 开发态产物**、`BODY` 是焦点兜底落点，**都不算 UI 元素**）\n"
                    "  · ⭐⭐⭐ **`文本` 那枚两侧**完全一致**：源站**自身 `None`**、"
                    "祖先 `canvas-fixed-toolbar`；复刻**自身 `None`**、"
                    "祖先**也是 `canvas-fixed-toolbar`**\n"
                    "    ⇒ ⭐⭐⭐ **复刻连「testid 放在祖先容器上」这个做法都对上了**\n"
                    "  · ⇒ 逐个对齐后，**其余 15 枚的「自身 tid」与「祖先 tid」"
                    "两侧都相同**\n"
                    "  · ⇒ `n_self_eq_closest` = **28/30**（复刻只有 2 枚"
                    "「自身 ≠ 祖先」，就是两圈里的两个 `文本`）"),
                "two_deliberate_deviations_970": (
                    "⭐⭐⭐ **真正剩下的差异只有两处，而且两处 816 都明确记录过、"
                    "都有理由 ⇒ 都不该改**：\n"
                    "| 停靠点 | 源站（自身 / 祖先） | 复刻（自身 / 祖先） | 816 的理由 |\n"
                    "|---|---|---|---|\n"
                    "| **`更多`** | `None` / `canvas-editor-menu` | "
                    "`canvas-more-trigger` / 同 | 源站**没有** testid ⇒ "
                    "删掉复刻的自造锚点 = **主动削弱自己的验收锚点** |\n"
                    "| **`生成历史`** | `canvas-panel-launcher` / 同 | "
                    "`canvas-history-launcher` / 同 | 源站与「搜索」**共用**一个 "
                    "tid ⇒ 照抄会**同时命中 2 个元素**、直接打破 801 的"
                    "「右簇 6 控件各命中 1 次」 |\n\n"
                    "  · ⇒ ⭐⭐⭐ **969 漏掉了第二处**（把 `生成历史` 误列成「对齐」）\n"
                    "  · ⇒ ⇒ ⭐⭐ **969 那句「唯一真实的结构差异」也错了** —— "
                    "**真实的是两处、而且两处都是有意为之**\n"
                    "  · ⇒ ⇒ ⚠️ **原计划的产品改动（把复刻「更多」改成 "
                    "`canvas-editor-menu`）取消** —— 那会把一个**有理由的**"
                    "有意偏离改回去、**削弱复刻自己的验收锚点**"),
                "same_kind_of_error_twice_970": (
                    "⭐⭐⭐⭐⭐ **两次同一种错，必须归成一条纪律**：\n"
                    "- **批 968b**：拿 **954 的历史基线**当本轮源站一侧的对照 ⇒ "
                    "把「**基线过期**」误读成「**实现有缺陷**」\n"
                    "- **批 969**：拿复刻的**自身 tid** 去比源站读到的**祖先 tid** ⇒ "
                    "把「**口径不同**」误读成「**实现有缺陷**」\n\n"
                    "  · ⚠️⚠️ **这里原本是一张两行表格（首格写着批次号）**⇒ pre-commit 钩子的\n"
                    "    `added_batch_numbers` 用 `^\\+\\|\\s*(\\d+)[a-z]?\\s*\\|` 抓「新增的批次行」\n"
                    "    ⇒ 首格写批次号会被当成本仓的**新增批次**、而本地绿构建只走到 274\n"
                    "    ⇒ **提交被拦**。**这是钩子对、我错** ⇒ **改的是排版、不是绕过钩子**：\n"
                    "    表格换成列表，首格不再写裸数字（948 早就为此栽过一次，**这次栽在同一处**）\n"
                    "  · ⇒ ⇒ ⭐⭐⭐ **纪律**：**先核「我比的是不是同一个东西」** —— "
                    "这一步同时包含**是不是同一轮量的**、**是不是同一个字段的**、"
                    "**是不是同一个口径的**\n"
                    "  · ⇒ ⇒ ⭐ **两次都是「对照侧没对齐」** ⇒ "
                    "**结论方向都是同一个错**（把差异算到复刻头上）⇒ "
                    "⇒ **发现差异时，先怀疑对照、别先怀疑实现**\n"
                    "  · ⇒ ⇒ ⭐⭐⭐ **两次都是自己先写结论、下一批才发现**，"
                    "而**两次都是靠「原始读数里其实两个字段都有」翻回来的** ⇒ "
                    "⇒ ⭐ **判词必须回查原始读数**（965 立下的规矩，"
                    "这两批是它的**第二次与第三次**兑现）"),
                "own_ruler_970": (
                    "⭐⭐ **为什么这两批能翻回来**：969 的 `FINGER_JS` 与 970 的 "
                    "`OWN_JS` **都同时记了两个字段**（自身 + 最近祖先）"
                    "⇒ **原始读数里答案一直在**，只是**汇总层**只用了其中一个\n"
                    "  · ⇒ ⇒ ⭐⭐⭐ **又一次兑现 965 的教训**：「**取值层级/取法搞错 ⇒ "
                    "读数到了、但被解释成反的**」—— 这一族到现在已复发"
                    "**三次**（965 的 `_raw.get(_tid)`、969、970）⇒ "
                    "⇒ ⭐ **凡是自己写的对照表，都要确认「我引的那一列是哪个字段」**"),
                "fifth_skip_trap_970": (
                    "⚠️⚠️⚠️⚠️⚠️ **同一个「静默跳过」坑的第五次**，而且这次"
                    "**两个门给了相反的信号**：\n"
                    "  · `CCCCC.2` 有一条判据要**反证 816 那条决策真的在仓库里**"
                    "⇒ 我新读了 `scripts/verify-jimeng-batch816-anchors.py` 到 "
                    "`_p816`\n"
                    "  · ⚠️⚠️ **锚点自查报「问题 0 个」** —— 因为 **`_p816` "
                    "没登记进 `PROBE_VARS`** ⇒ 收集器对**未登记**的变量是 "
                    "`continue`（**静默跳过**）⇒ **它的锚点一条都没被查过**\n"
                    "  · ⇒ 而 **verifier 那条判据真的红了**（609/610）\n"
                    "  · ⇒ ⇒ ⭐⭐⭐ **两个门同时在跑、各自抓到了不同的东西**："
                    "**verifier 抓到「锚文写错」，锚点自查（本该抓同一件事）"
                    "却因为「变量没登记」而放过了它**\n"
                    "  · ⇒ ⇒ ⭐⭐⭐ **最重要的一条**："
                    "**锚点自查报「0 问题」≠ 全部被查过** —— "
                    "**它只查「已登记」的那些变量**\n"
                    "  · ⇒ ⇒ 修法两处：① 锚文原文（我多打了一个 `「`）；"
                    "② **`_p816` 补登记进 `PROBE_VARS`**\n"
                    "  · ⇒ ⇒ ⭐ 补登记后 `SKIPPED-未登记` 那一栏会**变少** —— "
                    "**那一栏的行数本身就是个仪表**（它变少 = 有变量被查上了）"),
                "discipline_970": (
                    "① ⭐⭐⭐ **同一个字段要对比，就得用同一个口径**（本批的来由）；\n"
                    "  · ② ⭐⭐ **两次同一种错**（历史基线 / 不同字段）⇒ "
                    "归成一条：**先核「比的是不是同一个东西」**；\n"
                    "  · ③ ⭐ **发现差异先怀疑对照、别先怀疑实现**；\n"
                    "  · ④ ⭐ `OWN_JS` **只读属性、不调 `focus()`**；\n"
                    "  · ⑤ ⭐ **零插入、零节点点击**（只量 out 段）；\n"
                    "  · ⑥ ⭐ **判词不许预写**：探针只输出 `recon`（纯数字）"),
            },
            # ── 批 971：**源站**取样 954 那个「未复现条目」——
            #   ⭐⭐⭐⭐⭐ 它是 **`document.body` 本身**，不是 UI 元素；
            #   ⇒ 「复刻缺项目面板停靠点」这条挂了几十批的待办**彻底结案**
            "savestate_971": {
                "body_is_document_body_971": (
                    "⭐⭐⭐⭐⭐ **954 记的 `out:测试项目…已保存…分享` 不是 UI 元素 —— "
                    "它就是 `document.body` 本身。**\n"
                    "  · 探针 971，**源站**，2 轮 × 1 格 × 140 次 `Tab`；"
                    "`boot_saved_n` = **9**（两轮一致）\n"
                    "  · ⭐⭐⭐⭐⭐ **三条独立读数同指一枚**（k=90，两轮逐字相同）：\n"
                    "    · ① 落焦元素 `tag = ` **`BODY`**\n"
                    "    · ② `self_tid = None` **且** `closest_tid = None` "
                    "⇒ 元素自己和**所有祖先**都没有 `data-testid`\n"
                    "    · ③ `tabindex = None`、`el.tabIndex = -1`、"
                    "`is_focusable = false`、`rect = [0, 0, 1512, 1200]`"
                    "（**整块视口**）、`inner_text_head` = "
                    "**页面顶部那一大片文本**、`n_children` = **12–13**\n"
                    "  · ⇒ ⭐⭐⭐ **成名的机制**：`WHOAMI_JS` 的 "
                    "`tid = a.closest('[data-testid]')` 对 `body` **必然是 `null`** ⇒ "
                    "`aria` 就**回退到 `innerText.slice(0, 30)`** ⇒ "
                    "**整页文本被当成这个元素的「名字」**\n"
                    "  · ⇒ ⇒ ⚠️⭐⭐⭐ **它是焦点掉出文档时的兜底落点，"
                    "不是「项目面板」** —— 「项目面板」这个词从头到尾是**我的叫法**\n"
                    "  · ⇒ ⇒ ⭐⭐⭐⭐ **挂了几十批的待办「复刻缺的项目面板停靠点」"
                    "可以彻底结案**，而结案依据是「**找到了那枚元素本身**」，"
                    "**不是**「重测没找到」"),
                "why_954_saw_one_extra_971": (
                    "⭐⭐⭐⭐⭐ **954 那句「源站多出 1」的成因，现在说得出机制了 —— "
                    "两侧的「名字」用了不同口径**（这是这一族错的**最早一次**，"
                    "954 就是它的源头）：\n"
                    "  · **源站侧**用 `WHOAMI_JS`（`aria-label || title || "
                    "innerText.slice(0,30)`）⇒ **`BODY` 拿到了一个假名字**"
                    "（`测试项目\\n节点\\n76\\n已保存\\n分享\\n791 · 基础会员\\n76 `）\n"
                    "  · **复刻侧**读的是**纯 `aria-label`**（**不带回退**）⇒ "
                    "`BODY` 读到 `null`、**根本不出现在名字表里**\n"
                    "  · ⇒ ⇒ ⭐⭐⭐ **同一枚元素、同一件事，两侧差一个回退规则 "
                    "⇒ 差恰好 1** —— 与「复刻少了一个 UI 元素」毫无关系\n"
                    "  · ⇒ ⇒ ⭐⭐⭐⭐ **同口径之后**：源站真 UI 停靠点 **17 枚**、"
                    "复刻真 UI 停靠点 **17 枚** ⇒ **相等**\n"
                    "  · ⇒ ⇒ ⭐⭐ **换成 `(tag, 自身 tid, 祖先 tid)` 作键**："
                    "源站 **16** / 复刻 **17** ⇒ 差的 3 个键**恰好**是那两处"
                    "816 有意偏离（源站 `更多` 自身无 tid；复刻 `更多` = "
                    "`canvas-more-trigger`、`生成历史` = `canvas-history-launcher`；"
                    "而源站 `搜索` 与 `生成历史` **共用**一个 tid ⇒ **折叠成 1 个键**，"
                    "这才是 16 与 17 的真正来由）⇒ ⇒ **两侧 UI 停靠点实质等价**"),
                "both_sides_have_fallback_971": (
                    "⭐⭐⭐⭐ **「18 = 18」这句话的真正解释不是「两侧同组」，"
                    "而是两侧各带一枚非 UI 兜底落点**：\n"
                    "  · **源站**：**1 枚** `BODY`，`rect = [0, 0, 1512, 1200]`"
                    "（`is_focusable = false`）\n"
                    "  · **复刻**（批 970 原始读数）：**2 枚** —— `NEXTJS-PORTAL` "
                    "`rect = [0, 0, 0, 0]`（968b 已证是 **Next.js 开发态产物**）"
                    "**＋** `BODY` `rect = [0, 0, 1512, 1200]`\n"
                    "  · ⇒ ⭐⭐⭐⭐ **`BODY` 那枚两侧 `rect` **完全相同** "
                    "⇒ 它是同一种兜底落点，不是某一侧特有的东西**\n"
                    "  · ⇒ ⇒ ⚠️ **改写 §180 的措辞**：那里写的是「**复刻**另有 "
                    "`NEXTJS-PORTAL` … `BODY` …」（读起来像只有复刻有）⇒ "
                    "**原文保留**，但准确说法是**两侧都有 `BODY`**、"
                    "**只有复刻多一枚 0×0 的 `NEXTJS-PORTAL`**"),
                "systemic_reading_rule_971": (
                    "⚠️⚠️⚠️⭐⭐⭐⭐⭐ **本批最系统的一条**：**任何用 `WHOAMI_JS` 的 "
                    "`aria` 做 out 段停靠点统计的批次，都必须先排除 "
                    "`tag == 'BODY'`** ——\n"
                    "  · ⇒ **954 / 959 / 961 / 966 都用过这个口径** ⇒ "
                    "它们的 out 段计数里**都可能混着一枚 `BODY`**\n"
                    "  · ⇒ ⇒ ⭐⭐⭐ **判据层面的修法**：凡是以「停靠点集合」为"
                    "分母的门，**分母里必须显式剔掉 `BODY`/`NEXTJS-PORTAL`** ⇒ "
                    "否则分母上挂着一枚**不是 UI 的东西**，"
                    "**「集合相等」这门判据就永远差 1 或差 2**\n"
                    "  · ⇒ ⇒ ⭐⭐ **这不是「再测一遍」能解决的** —— "
                    "**口径写在脚本里**，不写在某一次的读数里"),
                "why_body_sometimes_971": (
                    "⚠️ **未查明（本批只记，不下结论）**：为什么 `BODY` 那一格"
                    "**有时在线、有时不在线** ——\n"
                    "  · 批 969 那轮源站：17 个停靠点、**没有** `BODY`；"
                    "批 971 这轮源站：18 个停靠点、**有** `BODY`\n"
                    "  · ⇒ 而**两批各自 2/2 轮内完全一致** ⇒ "
                    "**它不是随机噪声**\n"
                    "  · ⇒ ⇒ ⭐⭐ **我有一个猜测**（`BODY` 是「走过了最后一个可聚焦"
                    "元素之后」的落点 ⇒ 在不在取决于走查长度与可聚焦元素数之比）"
                    "**但本批没有对照，不许把它当结论** ⇒ "
                    "属**规模量**，留给下一批用**加长走查**去测"
                    "\n\n  · ——— ⚠️⚠️⚠️⭐⭐⭐⭐⭐ **批 972 改写横幅"
                    "（上面原文保留、不删）** ———\n"
                    "  · ⭐⭐⭐⭐⭐ **上面这条「未查明」是个假问题，"
                    "本条整条作废**：回查 **969 的原始读数**发现 "
                    "`BODY` **那会儿就在 `k=90` 上**，两批 4 轮的 k=86..96 "
                    "**逐格完全相同** ⇒ ⇒ **它一直在、一直在同一个座位上**；\n"
                    "  · ⇒ ⭐⭐⭐⭐ **两个错**：① 「有时在线有时不在线」"
                    "**从来不是事实**；② 「规模量」那个猜测"
                    "**被本批自己的读数否掉**（`BODY` 之后**还有 11 枚**真 UI 停靠点）\n"
                    "  · ⇒ ⇒ ⭐⭐⭐ **真正的成因是 969 的一个代理条件把整行滤掉了** ⇒ "
                    "见下一条 `landed_caliber_drops_body_972`"),
                "falsy_zero_bug_971": (
                    "⚠️⭐⭐⭐ **对账脚本里踩到一个 `or` 的 falsy-zero 坑，"
                    "差点把 17 个 `BUTTON` 全判成非 UI**：\n"
                    "  · 写成 `(tab_index_prop or -1) < 0` ⇒ "
                    "**`0` 是假值** ⇒ 所有 `tabIndex = 0` 的按钮（= **所有可聚焦元素**）"
                    "全被判成「不可聚焦」\n"
                    "  · ⇒ ⇒ ⭐⭐⭐ **纪律：处理读数时不要用 `or` 兜底 —— "
                    "读数里的 `0`、`\"\"`、`[]`、`False` 都是合法值**，"
                    "必须写显式的 `is None` 判断\n"
                    "  · ⇒ ⇒ ⚠️ **同一个坑的另一个面**：门**必须挂在独立分母上** —— "
                    "若这道门当时是绿的，**它绿得毫无意义**"),
                "discipline_971": (
                    "① ⭐⭐⭐⭐⭐ **先认「那枚元素本身是谁」** —— "
                    "「没复现」有两种：**它不在**，或**它不是你以为的那个东西**；"
                    "本批是后者，**只有真读到元素本身才分得开**；\n"
                    "  · ② ⭐⭐⭐ **两侧的「名字」必须用同一条回退规则** —— "
                    "954 的「多出 1」**整条**是回退规则不对称造成的；\n"
                    "  · ③ ⭐⭐⭐ **集合类判据的分母要显式剔掉非 UI 落点**；\n"
                    "  · ④ ⭐⭐ **未查明就写未查明**，"
                    "猜测必须**标明是猜测**、不许混进结论；\n"
                    "  · ⑤ ⭐ **读数里的 `0` / `\"\"` / `[]` 都不是假值**，"
                    "别用 `or` 兜底；\n"
                    "  · ⑥ ⭐⭐ **「我重新对了一次账」不等于「对账对」** —— "
                    "本批我**第一次对账把 inner 段和 out 段混在一起**算，"
                    "重算后才得到 16/17 ⇒ ⭐ **对账脚本自己也要过一遍口径**；\n"
                    "  · ⑦ ⭐ **`TEXTHO_JS` / `SAVED_CENSUS_JS` 只读属性/文本、"
                    "从不调 `focus()`** ⇒ 不污染焦点读数；\n"
                    "  · ⑧ ⭐ **零计费**：按键只有 `Tab`，"
                    "⛔ 守卫拦在 `mouse.click` 之前"),
            },
            # ── 批 972：⭐⭐⭐⭐⭐ `BODY` 接缝的**座位**；并把 969 那套
            #   `landed` 口径**并排**算一遍 ⇒ 它吃掉的那枚就是 `BODY`
            "seam_972": {
                "body_seat_972": (
                    "⭐⭐⭐⭐⭐ **接缝的座位查实了，而且它**不是**末尾兜底**：\n"
                    "  · 探针 972，**源站**，2 轮 × 1 格 × 140 次 `Tab`；"
                    "**969 / 971 / 972 三批共 6 轮**读数**完全一致**\n"
                    "  · 环长 **18** 枚；`el === document.body` 的那一格落在"
                    "**下标 6**（**第 7 枚**），两轮相同 ⇒ "
                    "**它既不在环首也不在环尾**\n"
                    "  · ⭐⭐⭐⭐ **它前面那一枚是 `与 AI 对话`**"
                    "（`canvas-sidecar-launcher`）⇒ 接缝落在"
                    "**右簇最后一个控件之后、左簇第一个控件之前**\n"
                    "  · ⭐⭐⭐⭐ **它后面还有 11 枚真 UI 停靠点** ⇒ "
                    "⭐⭐⭐ **971 猜的「走过了最后一个可聚焦元素之后的落点」"
                    "（**规模量**）被否掉了**\n"
                    "  · ⭐⭐ **新加的一件仪器**：`SEAT_JS` 读的是 "
                    "`el === document.body`（**比引用**），"
                    "971 只从 `tag == 'BODY'` **推断** ⇒ "
                    "门 `is_body_eq_tag_body` 要求**两者同时**成立 ⇒ "
                    "「标签相同但**不是** body」的元素分得开"),
                "landed_caliber_drops_body_972": (
                    "⭐⭐⭐⭐⭐ **同一族错的第六次，而且这次把机制说死了 —— "
                    "969 不是「没量到」，是「量到了但被一个代理条件滤掉了」**：\n"
                    "  · 969 的 out 段是这么圈的（`jimeng_probe969_projectpanel_src.py` "
                    "第 305–310 行）：\n"
                    "    `for r in rows:` / `for L in (r.get(\"landed\") or []):` / "
                    "`if L.get(\"kind\") == \"out\":` …\n"
                    "  · ⚠️⚠️ **`BODY` 那一行的 `landed` 是空数组** ⇒ "
                    "**它在进 `out_stops` 之前就被整行过滤掉了**\n"
                    "  · ⇒ ⇒ ⭐⭐⭐⭐ 本批把两套口径**并排**算了出来，"
                    "**两轮都是同一个数**：\n"
                    "    · `own.kind == 'out'`（971 口径，读 `document.activeElement`）"
                    "⇒ **18**\n"
                    "    · `landed[].kind == 'out'`（**969 口径**）⇒ **17**\n"
                    "    · **差额 = 1**，被丢掉的那一行 `tag` = **`BODY`**、"
                    "`landed` 的长度 = **0**\n"
                    "  · ⇒ ⇒ ⭐⭐⭐⭐ **969 那个 `null_tid_rows = 0` 由此得解**："
                    "它不是「页面上没有」，而是「**统计口径没数到**」\n"
                    "  · ⇒ ⇒ ⭐⭐⭐⭐⭐ **这一族的全链**（每一环都能说清是哪个机制）：\n"
                    "    ① **954**：源站用 `WHOAMI_JS`（**带 innerText 回退**）⇒ "
                    "`BODY` 拿到一个**假名字** ⇒ 被当成「源站多出的 1 个 UI 停靠点」\n"
                    "    ② **969**：改用纯 `aria-label`（**不带回退**）"
                    "**且**用 `landed` 圈 out 段 ⇒ `BODY` 既没名字**又整行被滤**\n"
                    "    ③ **970**：换字段口径（自身 tid + 祖先 tid）⇒ "
                    "复刻侧读到 `BODY` 与 `NEXTJS-PORTAL` 两枚\n"
                    "    ④ **971**：三套口径并读 ⇒ **认出了 `BODY` 就是 `document.body`**\n"
                    "    ⑤ **972**：把两套口径**并排** ⇒ **差额恰好吃掉一枚 `BODY`**\n"
                    "  · ⇒ ⇒ ⭐⭐⭐ **纪律**："
                    "**凡是用「某个代理条件」圈出来的集合，"
                    "都要单独记「被代理条件吃掉了多少」** —— "
                    "否则那个代理条件就是**隐形的分母修正**"),
                "ring_is_same_cyclic_order_972": (
                    "⭐⭐⭐⭐⭐ **把两侧的环旋到同一起点逐格对齐之后："
                    "是同一条环**，复刻只差两处：\n"
                    "  · ① 多一枚 **0×0 的 `NEXTJS-PORTAL`**"
                    "（968b 已证是 **Next.js 开发态产物**）\n"
                    "  · ② ⭐⭐⭐ **`rf__wrapper`（Canvas）那枚的位置不一样**：\n"
                    "    · **源站**：在 `用户菜单` 与 `文本` **之间**\n"
                    "    · **复刻**：在**接缝之后、`返回首页` 之前**\n"
                    "  · ⇒ ⇒ ⭐⭐⭐ **其余 16 枚逐格顺序两侧完全相同** ⇒ "
                    "「两侧是同一条环」这件事**站得住**\n"
                    "  · ——— ⚠️⚠️⚠️⭐⭐⭐⭐⭐ **批 973 改写横幅"
                    "（上面原文保留、不删）** ———\n"
                    "  · ⭐⭐⭐⭐⭐ **上面「复刻只差两处」这句不准确，"
                    "真实差处是**三枚**：① `NEXTJS-PORTAL` ② "
                    "**`BODY`（它是 ① 的**连带效应**）** ③ `rf__wrapper` 位置**\n"
                    "  · ⇒ 973 实测：`BODY` 那一格的前一格就是 "
                    "`NEXTJS-PORTAL`，而它的 `focusable = false`"
                    "（**浏览器无法聚焦**）⇒ ⇒ **生产构建里那枚 "
                    "`BODY` 应当整个消失**\n"
                    "  · ⇒ ⇒ ⭐⭐ **「其余 16 枚逐格顺序两侧完全相同」"
                    "这句话仍成立**，但「差两处」要改成"
                    "「**差三枚，其中两枚是开发态产物**」"
                    "\n  · ⇒ ⇒ 详见下一条 "
                    "`body_is_portal_artifact_973`\n"
                    "  · ⚠️⚠️⚠️ **本批不提出产品改动**：复刻侧 `rf__wrapper` "
                    "的**成因还没量过**（它是 xyflow 的容器、挂外层 ref 取的）⇒ "
                    "⭐⭐ **「发现差异先怀疑对照」这条不许被跳过** ⇒ "
                    "留给下一批用**复刻侧专用探针**把环序**测出来**再判"),
                "tuple_shape_bug_972": (
                    "⚠️⭐⭐⭐ **「`(k, row)` 当成 `row` 用」这一族栽到第四次**，"
                    "而 **`py_compile` 抓不到**（它只抓语法、不抓运行期形状）：\n"
                    "  · `out_own` 是 **`(k, row)` 二元组列表**，"
                    "我却写了 `for i, r in enumerate(out_own)` ⇒ "
                    "`r[\"seat\"]` 直接 `TypeError`\n"
                    "  · ⇒ ⇒ ⭐⭐⭐ 修法两条：① 解包写成 "
                    "`for i, (_k, r) in enumerate(out_own)`；"
                    "② ⭐⭐⭐ **加一条形状自证**（`assert` 两套口径的每个元素"
                    "**都**是 `(k, row)`）⇒ **下次同一个错在原地就红**\n"
                    "  · ⇒ ⇒ ⭐⭐ **可推广**：凡是「列表里装元组」的地方，"
                    "**形状要在用之前自证一次**，因为**类型错误发生在解包那一刻**、"
                    "而**所有静态检查都已经跑完了**"),
                "discipline_972": (
                    "① ⭐⭐⭐⭐⭐ **回查上一批的原始读数，"
                    "可能直接把它自己的「未查明」变成一个假问题** —— "
                    "971 那条「`BODY` 时有时无」**回查 969 的 k=90 就没了**；\n"
                    "  · ② ⭐⭐⭐ **「没看见」与「不在」是两件事** —— "
                    "前者需要更多证据、后者需要反证 ⇒ "
                    "本族错的六次里有**三次**是「没看见」被写成了「不在」；\n"
                    "  · ③ ⭐⭐⭐ **门必须能判红**：恒 0 时「不存在」与"
                    "「判据写错了」**分不开** ⇒ 本批 `landed_caliber_drops_something` "
                    "（防恒 0）与 `caliber_gap_eq_dropped`（防漏网）**成对**；\n"
                    "  · ④ ⭐⭐ **`all()` 作用在空列表上是恒真** ⇒ "
                    "门 `dropped_rows_are_all_body` 的**分母先钉非空**；\n"
                    "  · ⑤ ⭐⭐ **钉关系不钉绝对值**：座位用「两轮相同」"
                    "与「既不在环首也不在环尾」，**不钉下标 6**；\n"
                    "  · ⑥ ⭐ `SEAT_JS` **只读属性、从不调 `focus()`**；\n"
                    "  · ⑦ ⭐ **零计费**：按键只有 `Tab`，"
                    "⛔ 守卫拦在 `mouse.click` 之前"),
            },
            # ── 批 973：**复刻侧**测「环序 = DOM 序」⇒ 972 悬的问题有答案了，
            #   而且**顺手发现复刻那枚 `BODY` 是开发态产物的连带效应**
            "ringorder_973": {
                "ring_is_dom_order_973": (
                    "⭐⭐⭐⭐⭐ **复刻的环序就是 DOM 序** —— 而这条是**第一次**"
                    "**直接**被证实（967 当时是**靠步长推**的，"
                    "步长对得上**不等于**顺序的来源被验过）：\n"
                    "  · 探针 973，**复刻侧**，2 轮 × 1 格 × 140 次 `Tab` 上限；"
                    "**零插入、零节点点击、零计费**\n"
                    "  · ⭐⭐⭐ **证据取的是 `document.querySelectorAll('*')` "
                    "里的全文档下标**（`dom_rank`）⇒ **不依赖任何 `data-testid`、"
                    "不依赖任何「簇」** ⇒ 最中立的「DOM 序」证据\n"
                    "  · ⇒ ⇒ ⭐⭐⭐ `arc_ranks` = "
                    "`[110, 120, 121, 125, 134, 139, 145, 154, 160, 166, 169, "
                    "237, 240, 245, 251, 255, 268, 37, 42]`："
                    "**单调递增、恰好一次回绕**（268 → 37），两轮**逐字相同**\n"
                    "  · ⇒ ⇒ ⭐⭐ **门钉的是「回绕次数 ≤ 1」这个关系式**，"
                    "**不是**任何绝对下标 ⇒ 复刻逐轮 DOM 在动也不影响"),
                "wrapper_is_first_in_dom_973": (
                    "⭐⭐⭐⭐⭐ **972 悬的那件事有答案了："
                    "`rf__wrapper` 的位置差异是 DOM 摆放差异"
                    "（**实现差异**），不是口径差异**：\n"
                    "  · 复刻侧 `rf__wrapper` 的 `dom_rank` = **42** ⇒ "
                    "**它是整个环里 `dom_rank` 最小的真 UI 停靠点**"
                    "（其余全在 **110–268**）⇒ ⇒ **它是复刻 DOM 序里的第一个可聚焦元素**\n"
                    "  · 而 972 实测源站那一枚在 `用户菜单` 与 `文本` **之间** ⇒ "
                    "**它在源站 DOM 序的中间**，不是第一个\n"
                    "  · ⇒ ⇒ ⭐⭐⭐⭐ **前提也钉住了**：复刻侧画布根 "
                    "`tabindex=0`、`data-testid=rf__wrapper`、"
                    "`aria-label=Canvas` ⇒ **与源站同名同义**\n"
                    "  · ⇒ ⇒ ⭐⭐ **而 `armRovingTabindex` 只布 `.react-flow__node`、"
                    "从不碰 `rf__wrapper`**（静态取证：`JimengWorkspace.tsx:141-180`）"
                    "⇒ **它的 `tabindex` 来自 xyflow 自己的静态属性、"
                    "位置完全由 DOM 摆放决定** ⇒ "
                    "⭐⭐⭐⭐⭐ **「实现差异」这个判断是从实现里查出来的，"
                    "不是从数字里猜的**\n"
                    "  · ⚠️⚠️ **但源站侧的 `dom_rank` 本批没量** ⇒ "
                    "「源站的环**也是** DOM 序」**不能**由本批下结论 ⇒ "
                    "**下一批把同一件仪器搬到源站跑一遍**"),
                "body_is_portal_artifact_973": (
                    "⭐⭐⭐⭐⭐ **顺手挖到一件更大的："
                    "复刻侧那枚 `BODY` 很可能整个是开发态产物的连带效应**：\n"
                    "  · ⭐⭐⭐⭐ `BODY` 那一格的前一格 = **`NEXTJS-PORTAL`**"
                    "（`dom_rank` = **268**，**环里最大**），"
                    "而它的 `focusable` = **`false`**\n"
                    "  · ⇒ ⇒ ⭐⭐⭐⭐⭐ **机制 therefore 说得通了**："
                    "从**浏览器无法聚焦**的元素按 `Tab` ⇒ 焦点掉到 "
                    "`document.body`（`dom_rank` = **37**）⇒ "
                    "下一按走到 DOM 序里的第一个可聚焦元素 = `rf__wrapper`（**42**）\n"
                    "  · ⇒ ⇒ ⭐⭐⭐⭐ **推论（可验，本批**只测了复刻侧**）**："
                    "生产构建里**没有** `nextjs-portal` ⇒ "
                    "⭐⭐⭐ **仓内交叉印证**：更早的批次在 "
                    "`scripts/jimeng_unclickable_audit.py` 里**已经写过** "
                    "`nextjs-portal` 是 **Next 开发态**注入的调试浮层、"
                    "**「生产构建里没有这个元素」**、且因为 "
                    "`pointer-events` 是 `auto` 所以**必须显式排除**"
                    "（那里是为「点击遮挡」检查设的 `DEV_OVERLAY`）"
                    "⇒ ⇒ ⭐⭐ **本批是同一件事的第二次独立印证**，"
                    "而**这次是在 Tab 环上** ⇒ "
                    "⚠️ **注意它当时被排除了、这次却仍在环里**："
                    "**「遮挡」与「Tab 序」是两条路，排掉一条不等于另一条**\n"
                    "**那枚 `BODY` 应当整个消失** ⇒ ⇒ "
                    "**复刻侧的环上有**两枚**开发态产物，"
                    "不是 §182 写的那一枚**\n"
                    "  · ⇒ ⇒ ⚠️⚠️ **改写 §182 的措辞**（原文保留）："
                    "那里写「复刻只差两处：① `NEXTJS-PORTAL` ② `rf__wrapper` 位置」"
                    "⇒ **不准确** —— ① **连带**产生了 `BODY` ⇒ 真实差处是**三枚**\n"
                    "  · ⇒ ⇒ ⭐⭐ **源站那一侧**：`BODY` 的前一格是 "
                    "`与 AI 对话`（一个**能聚焦**的按钮）⇒ "
                    "⚠️ **两侧的 `BODY` 很可能不是同一个机制** ⇒ "
                    "**不许把复刻的机制直接搬到源站头上**"
                    "\n  · ——— ⚠️⚠️⚠️⭐⭐⭐⭐ **批 974 改写横幅"
                    "（上面原文保留、不删）** ———\n"
                    "  · ⭐⭐⭐⭐⭐ **「很可能不是同一个机制」这句**说重了**，"
                    "本批实测把它改掉一半：\n"
                    "  · ⇒ **结构角色两侧相同** —— 两枚 `BODY` 的"
                    "**前一格 `dom_rank` 都是环里最大**、**后一格都是最小**"
                    "⇒ **它们都是序列焦点导航的回绕点**\n"
                    "  · ⇒ **不同的只是「回绕之前那一格是什么」**："
                    "源站是 `与 AI 对话`（可聚焦）、复刻是 "
                    "`NEXTJS-PORTAL`（**无法聚焦**）\n"
                    "  · ⇒ ⇒ ⭐⭐⭐ **纪律**：**「实测到一个差异」很容易被"
                    "写成「机制不同」** —— 本例差异只在**前驱元素**，"
                    "**角色完全一致** ⇒ ⭐⭐ **下结论前先问"
                    "「差异在哪个字段上」**\n"
                    "  · ⇒ ⇒ ⚠️ **仍然成立的那半句**："
                    "**不许把复刻的机制预写给源站** —— 本批正因为没预写，"
                    "**才测出了这半个修正**\n"
                    "\n  · ⇒ ⇒ 详见下一条 `seam_is_wrap_point_974`"),
                "tuple_family_fifth_973": (
                    "⚠️⚠️⚠️⭐⭐⭐ **「`(k, row)` 当成 `row` 用」这一族栽到第五次，"
                    "而且 972 加的那条「形状自证」**没抓到它**：\n"
                    "  · 错在**解包处**（`for i, r in enumerate(out_own)`），"
                    "**不在元组形状上** ⇒ "
                    "⭐⭐⭐ **形状自证只挡「形状错」，挡不住「解包错」**\n"
                    "  · ⇒ ⇒ ⭐⭐⭐⭐ **本批做的是结构性修法**："
                    "**不再存 `(k, row)` 元组**，改成 `out_ks` / `out_rows` "
                    "**两个平行列表** ⇒ **元组根本不再存在** ⇒ "
                    "**这一族的坑从根上被拆掉**（而不是再加一条断言）\n"
                    "  · ⇒ ⇒ ⭐⭐ **可推广**：**当一种错误重复到第三次，"
                    "就该改数据结构，而不是加断言** —— "
                    "断言只能挡住**它被写出来的那一种形状**"),
                "discipline_973": (
                    "① ⭐⭐⭐⭐⭐ **把上批的「假说」变成一条可证伪的关系式** —— "
                    "本批直接读**全文档下标**（**最中立**），"
                    "而不再靠「步长像不像」去推；\n"
                    "  ② ⭐⭐⭐ **证据的粒度要匹配断言的粒度** —— "
                    "「环序」是**顺序**命题 ⇒ 证据必须是**顺序**"
                    "（单调性 + 回绕次数），**不是**「集合相等」；\n"
                    "  ③ ⭐⭐⭐ **读数恒为一个哨兵值时要判红** —— `dom_rank` 恒 `-1` "
                    "会让整条链**安静空转** ⇒ 自证门（`dom_rank_is_live`）"
                    "与主门**成对**；\n"
                    "  ④ ⭐⭐ **`all([])` 是恒真** ⇒ 每道「全部都是……」的门"
                    "**分母都要先钉非空**；\n"
                    "  ⑤ ⭐⭐⭐ **一种错重复到第三次就改数据结构，别再加断言**；\n"
                    "  ⑥ ⭐⭐ **`DOMRANK_JS` 只读属性、从不调 `focus()`**；\n"
                    "  ⑦ ⭐ **零插入、零节点点击、零计费**"),
            },
            # ── 批 974：**源站侧**补上 973 留的对照缺口 ⇒ 两侧各测一轮、同一件仪器
            "srcdomrank_974": {
                "both_sides_are_dom_order_974": (
                    "⭐⭐⭐⭐⭐ **两侧的环都是 DOM 序** —— 而 973 只证了复刻侧，"
                    "**源站那一侧的 `dom_rank` 它自己写明了没量** ⇒ 本批补上：\n"
                    "  · 探针 974，**源站**，2 轮 × 1 格 × 140 次 `Tab`；"
                    "`DOMRANK_JS` 用 `_grab` 从 973 **逐字抠**、**不复制源码**\n"
                    "  · ⇒ ⇒ 源站 `arc_ranks` **单调递增、恰好一次回绕**"
                    "（2396 → 60），两轮**签名相同** ⇒ "
                    "**源站的环也是 DOM 序**\n"
                    "  · ⇒ ⇒ ⭐⭐⭐ **两侧各测一轮、同一件仪器** ⇒ "
                    "**973 的结论现在两侧都钉住了**\n"
                    "  · ⭐⭐⭐ **「同一件仪器」是可证的**：`_grab` 抠完再 "
                    "`assert _s in _p973` ⇒ **它是一条断言，不是文档里的一句保证**"),
                "wrapper_ends_are_swapped_974": (
                    "⭐⭐⭐⭐⭐ **`rf__wrapper` 的位置差异 = 实现差异，"
                    "两侧各测一轮钉住了；而且差别是「**两端对调**」**：\n"
                    "  · **源站**：`rf__wrapper` 在环的**最后一位**（下标 17），"
                    "`dom_rank` = 177/179 ⇒ **它是源站 DOM 序里最后一个可聚焦元素**"
                    "（环里最大的是 `与 AI 对话`，`dom_rank` = 2396/2398）\n"
                    "  · **复刻**：`rf__wrapper` 的 `dom_rank` = 42 ⇒ "
                    "**它是复刻 DOM 序里第一个可聚焦元素**\n"
                    "  · ⇒ ⇒ ⭐⭐⭐⭐⭐ **所以源站在弧的末端、复刻在弧的起点之前** —— "
                    "**不是「少了一个 / 多了一个」，是「同一枚在两端对调**」**\n"
                    "  · ⇒ ⇒ ⭐⭐ **972 记的「源站那枚在 `用户菜单` 与 `文本` 之间」"
                    "本批复核成立**：源站环序 `用户菜单`(16) → **`rf__wrapper`**(17) → "
                    "`文本`(0) ⇒ 旋转后正是「`用户菜单`、`Canvas`、`文本`」\n"
                    "  · ⚠️⚠️ **仍不提出产品改动** —— 「差异是实现差异」这一步测实了，"
                    "但「**该往哪边对齐**」是一个**产品决策**："
                    "把复刻的画布根挪到弧末，还是把源站的挪到弧首，"
                    "两边都不是「照抄一下」⇒ "
                    "⭐⭐⭐ **「差异成立」与「该怎么改」是两件事，"
                    "不许拿前者当后者的许可证**"),
                "seam_is_wrap_point_974": (
                    "⭐⭐⭐⭐⭐ **两侧那枚 `BODY` 都是「DOM 序的回绕点」"
                    "—— 而 973 说「很可能不是同一个机制」，本批把它改掉**：\n"
                    "  · **结构角色（已测实，两侧相同）**："
                    "它的**前一格 `dom_rank` 是环里最大**、**后一格是最小** ⇒ "
                    "**它落在序列焦点导航的绕回点上**\n"
                    "    · 源站：`与 AI 对话`(2396) → **`BODY`**(60) → `返回首页`(68)\n"
                    "    · 复刻：`NEXTJS-PORTAL`(268) → **`BODY`**(37) → "
                    "`rf__wrapper`(42)\n"
                    "  · **触发方式（两侧不同，这才是 973 测到的）**：\n"
                    "    · **源站**前一格是 `canvas-sidecar-launcher`（BUTTON）、"
                    "`prev_focusable = TRUE`（**可聚焦**）\n"
                    "    · **复刻**前一格是 `NEXTJS-PORTAL`、`prev_focusable = false`"
                    "（**浏览器无法聚焦**）\n"
                    "  · ⇒ ⇒ ⚠️⚠️⚠️ **改写 973 的说法**：973 写「两侧的 `BODY` "
                    "**很可能不是同一个机制**」⇒ **说重了** —— "
                    "**落点角色两侧相同**（都是回绕点），"
                    "**不同的是「回绕之前那一格是什么」**\n"
                    "  · ⇒ ⇒ ⭐⭐⭐ **纪律**："
                    "**「实测到一个差异」很容易被写成「机制不同」** —— "
                    "本例里差异只在**前驱元素**，**角色完全一致** ⇒ "
                    "⭐⭐ **下结论前先问「差异在哪个字段上」**\n"
                    "  · ⚠️ **未测实**：源站那一枚**为什么**也会落在 body 上"
                    "（它前面是可聚焦的按钮）⇒ 属**触发机制**，"
                    "本批**只有观测、没有机制** ⇒ **记未查明**"
                    "\n  · ——— ⚠️⚠️⚠️⭐⭐⭐⭐ **批 975 改写横幅"
                    "（上面原文保留、不删）** ———\n"
                    "  · ⭐⭐⭐⭐ **975 验过一个假设 H₁、并把它判否了**："
                    "`与 AI 对话` 的**祖先链带正 `tabindex`** ⇒ "
                    "**独立作用域** ⇒ 作用域那条**出局**\n"
                    "  · ⇒ ⚠️ **「未查明」仍然成立** —— "
                    "只是**候选空间缩小了**（见下一条 "
                    "`still_unexplained_975`）⇒ "
                    "⭐⭐⭐ **否掉一条假设 ≠ 查明机制**，这两件事不要混\n"
                    "  · ⇒ ⇒ ⭐⭐⭐ **否掉它的读数顺带给 967 补了"
                    "第二个独立证据**（祖先链 9 层 `ti_attr` 全是 `None`）"
                    "\n  · ⇒ ⇒ 详见下一条 `h1_falsified_975`"),
                "wrong_kind_gate_974": (
                    "⚠️⚠️⚠️⭐⭐⭐ **本批我自己写坏了一道门，"
                    "而且它是「错在种类」而不是「太严」**：\n"
                    "  · 第一版的跨轮门是 `arc_ranks` **直接比相等** ⇒ "
                    "**它必然红**：源站 DOM 逐轮在动（本批两轮**每项正好差 1**、"
                    "长度都是 18）⇒ **红的原因不是「环序变了」**\n"
                    "  · ⇒ ⇒ ⭐⭐⭐ **这正是我一直在治的那一族错，反过来咬了我自己**："
                    "**在会动的源站上钉绝对值** ⇒ "
                    "⭐⭐⭐⭐ **纪律：跨轮比顺序，必须比「顺序关系」而不是「绝对数值」**\n"
                    "  · ⇒ ⇒ 修法**不是放宽**：新增 `rank_order_signature`"
                    "（只记相邻两项**谁大**，**不记绝对值**）⇒ "
                    "**与 DOM 总大小无关**，而**环序真变了签名一定跟着变**\n"
                    "  · ⇒ ⇒ ⭐⭐ **验证**：用**已有读数**就验完了 —— "
                    "新签名两轮都是 `UUUUUDUUUUUUUUUUU`（绿）、"
                    "旧门是 `False`（红）⇒ **不必重跑源站就能确认改对了**"),
                "self_inflicted_omission_974": (
                    "⚠️⚠️⭐⭐⭐ **另一处自己犯的**：门 ⑥ 我第一版写成了 "
                    "`... if False else True` ⇒ **那是一道恒真门，"
                    "比没有门更坏** ⇒ 已删掉重写：判据落到**后处理真算的字段**"
                    "（`is_body_eq_tag_body`）上\n"
                    "  · ⇒ ⇒ ⭐⭐⭐ **纪律**：**写门的时候，"
                    "凡是写了 `if X` 的短路分支，都要问一句「X 恒定吗」** —— "
                    "**恒定的条件 + `else` 分支 = 一道永远绿的门**"),
                "discipline_974": (
                    "① ⭐⭐⭐⭐⭐ **先核「我比的是不是同一个东西」** —— "
                    "973 只证了复刻侧 ⇒ **跨侧结论必须两侧各量一次**"
                    "（与 968b/969/970 是**同一条纪律**）；\n"
                    "  ② ⭐⭐⭐ **不复制源码** —— `_grab` + `assert` "
                    "把「两侧真的是同一件仪器」变成**断言**；\n"
                    "  ③ ⭐⭐⭐ **不预写结论** —— "
                    "门只钉「**测到了**」与「**能判红**」，"
                    "**不钉**源站 `BODY` 的前驱**该是什么** ⇒ "
                    "**上一批的机制不许直接当成这一批的预期**"
                    "（而这条**当场就赚回来了**：973 的机制被本批改了一半）；\n"
                    "  ④ ⭐⭐⭐ **跨轮比顺序要比「顺序关系」、不是「绝对数值」**；\n"
                    "  ⑤ ⭐⭐⭐ **`if X` 的短路分支要问「X 恒定吗」** —— "
                    "恒定 + `else` = 一道永远绿的门；\n"
                    "  ⑥ ⭐⭐ **两个平行列表、不是元组**（973 那一族栽到第五次）；\n"
                    "  ⑦ ⭐ **零计费**：按键只有 `Tab`，"
                    "⛔ 守卫拦在 `mouse.click` 之前"),
            },
            # ── 批 975：源站那枚 `BODY` 的触发机制 ⇒ ⭐⭐⭐⭐⭐ **假设 H₁ 被判否**，
            #   而否掉它的读数顺带给了 967 一条**第二个独立证据**
            "scope_975": {
                "h1_falsified_975": (
                    "⭐⭐⭐⭐⭐ **H₁ 被判否** —— 而这是本批最大的收获：\n"
                    "  · H₁ 原话：**`与 AI 对话` 的某个祖先带正 `tabindex`** ⇒ "
                    "形成**独立的顺序焦点导航作用域** ⇒ 从该作用域最后一格按 `Tab` "
                    "**出作用域** ⇒ 焦点无处可落、暂留 `document.body`\n"
                    "  · ⭐⭐⭐⭐⭐ **实测**：`与 AI 对话` 的**整条祖先链 9 层**，"
                    "每一层的 `ti_attr`（`getAttribute('tabindex')`）"
                    "**全都是 `None`** —— ⭐⭐⭐ "
                    "**DOM 上根本没有写 `tabindex` 属性**\n"
                    "  · ⇒ ⇒ `ti_prop`（`.tabIndex`）读到的 `0` / `-1` "
                    "**只是浏览器默认行为**，不是任何人写上去的\n"
                    "  · ⇒ ⇒ ⭐⭐⭐ **H₁ 被否** ⇒ **不存在「独立作用域边界」**\n"
                    "  · ⇒ ⇒ ⭐⭐⭐⭐⭐ **这一否顺带给出了 967 的第二个独立证据**："
                    "967 当年写「源站 Tab 顺序 = 朴素环形 DOM 序、**无正 "
                    "`tabindex`**」时，证据是**步长观测**；"
                    "本批的证据是**属性逐层读出来是空的** ⇒ "
                    "⭐⭐⭐ **两条证据互相独立、方法完全不同** ⇒ "
                    "「源站侧没有任何对 Tab 序的显式干预」这条结论**更硬了**\n"
                    "  · ⭐⭐ 整段 out 环**零个**停靠点的祖先链带正 `tabindex`"
                    "（`n_positive_ti_rows = 0`），两轮一致"),
                "ti_attr_vs_prop_975": (
                    "⭐⭐⭐ **这一批的方法上有一处值得单独记**：\n"
                    "  · 新件 `SCOPE_JS` 把每一层**同时**读两个字段：\n"
                    "    · `ti_attr` = `getAttribute('tabindex')` ⇒ "
                    "**属性在不在 / 属性是什么**（没有就是 `None`）\n"
                    "    · `ti_prop` = `.tabIndex` ⇒ **归一化后的可聚焦性**\n"
                    "  · ⇒ ⇒ ⭐⭐⭐ **两件事因此分得开**："
                    "本批的全部结论来自「`ti_attr` 全是 `None`」—— "
                    "**只看 `ti_prop` 是看不出来的**（它会给出 `0` / `-1`）\n"
                    "  · ⇒ ⇒ ⭐⭐⭐ **这也让「不许用 `or` 兜底」这条纪律落成了**"
                    "**一条可执行的断言**：探针里有 "
                    "`assert 'ti_attr ||' not in SCOPE_JS` ⇒ "
                    "971 踩过的 `(tab_index_prop or -1) < 0` "
                    "（把 `0` 当假值）**在这一族里被物理禁止**\n"
                    "  · ⇒ ⇒ ⭐⭐ **正面自证门与主门成对**："
                    "`ti_reading_is_live` 先证明**确实逐层拿到了**"
                    "（`chain_depth >= 1` 且每层都有 `ti_attr` 字段）⇒ "
                    "**「没有作用域」与「读数是空的」分不开**这件事被挡住了"),
                "reversed_gate_975": (
                    "⚠️⚠️⚠️⭐⭐⭐ **本批我自己写反了一道门，"
                    "而处置过程本身就是一条纪律**：\n"
                    "  · 第一版写的是 `body_precedes_sidecar`（`BODY` 在 "
                    "`与 AI 对话` 之前）⇒ **它判红了**\n"
                    "  · ⇒ ⭐⭐⭐ **门红先判「门错还是数据错」**："
                    "974 的读数就已经是「`与 AI 对话`(seat 5) → **`BODY`**(seat 6)」"
                    "⇒ 与本批一致、2/2 相同 ⇒ ⇒ **是门写反了**\n"
                    "  · ⇒ ⇒ ⭐⭐⭐ **处置是「改门」（改精确）、不是放宽** —— "
                    "新门 `sidecar_precedes_body` 说的是同一件事的**正确方向**\n"
                    "  · ⇒ ⇒ ⭐⭐⭐⭐ **而且改门要成对**：只改正向的话，"
                    "「改精确」与「放宽」**分不开** ⇒ "
                    "本批**额外钉了一条反向门** `reversed_relation_stays_false` "
                    "⇒ **旧方向必须仍然是红的** ⇒ "
                    "这样才证明改的是**方向**、不是**门槛**\n"
                    "  · ⇒ ⇒ ⭐⭐ **可推广**：**任何一次「改门」，"
                    "都要问「我怎么证明我不是在放宽」**"),
                "grab_is_consumer_975": (
                    "⚠️⚠️⭐⭐⭐ **另一处：`_grab` 当场教了我一件事 —— "
                    "974 是 `_grab` 的「消费者」不是「生产者」**：\n"
                    "  · 975 第一版写 `_grab(\"DOMRANK_JS\", _p974)` ⇒ "
                    "**真跑当场报「抠不到」** —— 因为 974 **自己没定义**那份字面量，"
                    "它也是从 973 抠的\n"
                    "  · ⇒ ⇒ ⭐⭐⭐ **必须沿链回到源头 `_p973`** ⇒ "
                    "**974 / 975 都指向 973 的同一份字面量** ⇒ "
                    "⭐⭐⭐ **三支探针、一个源头**，而不是三份拷贝\n"
                    "  · ⇒ ⇒ ⭐⭐⭐ **这条链还给了第二道保险**：本批加了 "
                    "`assert 'DOMRANK_JS = \"\"\"' not in _p974` ⇒ "
                    "**974 自己一旦开始定义字面量，这条就红** ⇒ "
                    "⭐⭐ 「同一把尺子」这件事**从「靠自觉」变成「有断言」**"),
                "still_unexplained_975": (
                    "⚠️⚠️⚠️ **诚实记账：源站那一枚 `BODY` 的机制**"
                    "**本批仍然未查明**，只是候选空间被缩小了：\n"
                    "  · H₁ 被否 ⇒ **「作用域边界」这条出局**\n"
                    "  · ⇒ ⇒ 剩下的候选（**这是假说，不是结论**）："
                    "`与 AI 对话` 是**源站 DOM 里最后一个可聚焦元素**"
                    "（974 实测它的 `dom_rank` = 2396/2398、环里最大）⇒ "
                    "按 `Tab` **绕回文档开头**、而开头那一段**没有可聚焦元素** ⇒ "
                    "焦点**暂留 `document.body`**\n"
                    "  · ⇒ ⇒ ⭐⭐⭐ **要证成它，还差一个测量**："
                    "**「从回绕点到第一个可聚焦元素之间，还剩几个不可聚焦元素」**"
                    "⇒ ⚠️ **本批不测**（探针的 `skip_note` 已写明）\n"
                    "  · ⇒ ⇒ ⭐⭐⭐⭐ **最要紧的一句**："
                    "**不许把复刻那套「从无法聚焦元素掉下来」搬过来当预期** —— "
                    "974 已经因为没预写而赚回半个修正；"
                   "**继续不预写，是这一族唯一能少错一次的东西**"),
                "discipline_975": (
                    "① ⭐⭐⭐⭐⭐ **假设门必须能判红** —— 「假设门」这一族最容易滑成"
                    "叙述：写一句「可能是作用域造成的」、门却是恒绿的 ⇒ "
                    "**门要直接判「祖先链里有没有正 `tabindex`」** ⇒ "
                    "本批它**真的判红了**，而且**红的正是 H₁**；\n"
                    "  ② ⭐⭐⭐ **正向自证门与主门成对** —— "
                    "「读数是空的」和「读数里没有」**看起来一模一样**；\n"
                    "  ③ ⭐⭐⭐ **读数不许用 `or` 兜底** —— 用 "
                    "`getAttribute` 拿**原始属性值**、探针里落一条 "
                    "`assert` 把这件事**物理禁止**；\n"
                    "  ④ ⭐⭐⭐ **门红先判「门错还是数据错」**，"
                    "而且**改门要成对**：改完正向**必须钉住反向**，"
                    "否则「改精确」与「放宽」分不开；\n"
                    "  ⑤ ⭐⭐⭐ **`_grab` 链要认得谁是消费者、谁是生产者** —— "
                    "**消费者不是生产者**，得沿链回到源头；\n"
                    "  ⑥ ⭐⭐ **钉关系不钉绝对值**（只钉「`与 AI 对话` 在 `BODY` 之前」）；\n"
                    "  ⑦ ⭐ **零计费**：按键只有 `Tab`，"
                    "⛔ 守卫拦在 `mouse.click` 之前"),
            },
                "discipline_969": (
                    "① ⭐⭐⭐ **判据不许用自己起的名字**：「项目面板」是**我的叫法**，"
                    "用它匹配 = 把结论写进判据 ⇒ 判据是「`host_tid is None`」；\n"
                    "  · ② ⭐ **判据恒 0 必须报红**（`panel_judgement_is_live_both_reps` "
                    "本批**真的红了**）⇒ 不许把「没匹配上」写成「不存在」；\n"
                    "  · ③ ⭐⭐⭐ **对比要在同一轮量两侧**（本批最大的教训）；\n"
                    "  · ④ ⭐ `FINGER_JS` **只读属性、不调 `focus()`** ⇒ 不污染焦点读数；\n"
                    "  · ⑤ ⭐ **判词不许预写**：探针只输出 `recon`（纯数字）"),
            },
            },
            },
            },        # ← 闭合 `armptr_967`（968/968b 是它的**后续**两批）
            "unwrap_inverted_verdict_965": (
                "⚠️⚠️⚠️⭐⭐⭐ **第一版的汇总层把判决整个说反了** —— "
                "而**原始读数其实是对的**：\n"
                "  · `READ_FT_JS` 返回的是**整张以 tid 为键的表**，"
                "我却写成 `_ft[_tid] = ev(READ_FT_JS)` ⇒ 当成单条记录用\n"
                "  · ⇒ `v.get(\"sync\")` 取到的是 **`None`** ⇒ "
                "「同步落上没落上」三项**全打成「没落上」**\n"
                "  · ⇒ ⚠️⚠️ **真相正好相反**：原始记录里 "
                "`sync` / `micro` / `task` / `frame` **全是 `is_target = true`**"
                "⇒ **焦点同步就落上了、而且四个时点都没被拽走**\n"
                "  · ⇒ ⭐⭐⭐ **如果我信了那个打印出来的判决**，"
                "就会把一个**反向结论**写进基线 ⇒ "
                "**一个能把结论说反的汇总层，比没有汇总层更坏**\n"
                "  · ⇒ ⭐⭐⭐ **教训（与 962 的闩锁、965 的局部变量同一族，但更危险）**：\n"
                "    · 闩锁 / 局部变量 ⇒ **读数到不了**（恒空）\n"
                "    · **取值层级搞错 ⇒ 读数到了、但被解释成反的**（**恒有、但恒反**）\n"
                "  · ⇒ ⭐ **纪律**：凡是自己写的**汇总/判词字符串**，"
                "**必须回查原始读数至少一次**；而**判词与原始读数矛盾时，"
                "先怀疑判词**（本批就是这样查出来的）\n"
                "  · ⇒ 修法：`_raw.get(_tid)` **显式解包** ＋ "
                "新增门 `focus_test_unwrap_complete`（**解包漏一个就红**）"),
            "focustest_965": {
                # ── 批 965：**源站**「它到底能不能被脚本聚焦」——**机制层**的问题 ──
                # 取样：探针 965，源站，登录态，视口 1512×1200，2 轮 × 1 格；
                # 助手与 JS 与 964 逐字相同（链式）⇒ 新件 `FOCUSTEST_JS` + `READ_FT_JS`。
                "what_965_measures": (
                    "⭐⭐⭐⭐⭐ 963/964 已经把**两条路都走到头**了（`tabindex` 维度、"
                    "非 `tabindex` 解剖维度）⇒ **DOM 上查不到** ⇒ 只能问"
                    "**机制层面**的问题：**「它到底能不能被脚本聚焦？」**\n"
                    "  · 963 观察到的是「从 67 按 Tab 落到 69、**从不落 68**」⇒ "
                    "两种可能：\n"
                    "    (a) **它根本不可聚焦** ⇒ 被**跳过**\n"
                    "    (b) 它**可以**聚焦，但**应用的 `focusin` 处理器立刻把焦点"
                    "拽走** ⇒ 表现为「跳过」\n"
                    "  · ⇒ ⭐ **用「同步读一次、微任务后再读一次」就能分开**：\n"
                    "    · 同步就**没落上去** ⇒ (a)\n"
                    "    · 同步**落上了**、微任务后**被拽走** ⇒ (b)\n"
                    "  · ⇒ ⭐⭐⭐⭐ **本批判决：两个候选机制**全被否掉** —— "
                    "`focus()` **同步就落上**、**四个时点都没被拽走**"
                    "（`n_focusins = 1`、trusted）⇒ 既不是「不可聚焦」、"
                    "也不是「被 `focusin` 拽走」⇒ **跳过是应用自己的选择**\n"
                    "  · ⇒ ⭐⭐⭐⭐ **顺带钉住一条机制事实**：被跳过的那枚 "
                    "`el.tabIndex === -1`（**而** `getAttribute('tabindex')` "
                    "是 `None`）⇒ 浏览器**原生 `Tab` 根本不会停在这些 `div` 节点上**"
                    "⇒ **应用必须自己调 `focus()`** ⇒ 与 962「节点段 102/140 "
                    "在派发中搬」**吻合** ⇒ 整条链子闭合\n"
                    "  · ⚠️ **必须带对照组**：**左右两个邻居**跑**同一段**代码"
                    "（943/BB.3：两个答案必须来自**两个不同的集合**）\n"
                    "  · ⚠️ 只调 `el.focus()`、**不点任何东西** ⇒ 不碰计费入口"),
                "structural_bug_965": (
                    "⚠️⚠️⚠️ **第一版的 `FOCUSTEST_JS` 有个结构性错误**：\n"
                    "  · 它把 `micro` / `task` / `frame` 写成**函数内的局部变量**、"
                    "再 `return` ⇒ 那三个赋值发生在 **return 之后**\n"
                    "  · ⇒ ⭐⭐ **调用方永远看不到它们** ⇒ 三个时点里**只有 `sync` "
                    "是真的读数**，另外三个是**结构性不可达**\n"
                    "  · ⇒ 改成**挂在 `window.__ft` 上**、由第二步 `READ_FT_JS` 读走\n"
                    "  · ⇒ ⭐⭐ **教训**：**「赋值写在 return 之后」不会报错、只会"
                    "永远读不到** ⇒ 凡是「**先安排、后读**」的时序读数，"
                    "**必须把结果挂在跨调用的载体上**（`window`），并**给等的时间**"
                    "（本批 `120ms`，必须 > 一帧）\n"
                    "  · ⚠️ 与 962 那个**闩锁 bug** 同一族：**都是「读数根本到不了」**"
                    "⇒ **一个恒空的读数比没有读数更坏**"),
            },
            "diff_is_not_discriminative_964": (
                "⚠️⚠️⚠️ **第一版把「字典整体不等」当成了「有差异」** ⇒ "
                "**位置噪声被当成了原因**：\n"
                "  · 第一版读出 2 个差异字段：`computed` 与 `scroll_h`\n"
                "  · ⚠️ `computed` 差的只是 **`z_index`（68 / 67 / 69）与 "
                "`transform`（画布坐标）** —— 这两个**每枚节点按位置必然不同**"
                "⇒ **不是内在属性**\n"
                "  · ⚠️ `scroll_h` 是 **320 / 328 / 320** ⇒ 被跳过的那枚与"
                "**另一个邻居完全相同** ⇒ **不可区分**\n"
                "  · ⇒ ⭐⭐ 加**第二层判据**「**可区分**」：该字段**与左右邻居都不相等**"
                "才算数（与任一邻居相等 ⇒ 不可区分）\n"
                "  · ⇒ ⚠️⚠️ **通用纪律**：**「A ≠ B」不等于「A 能把 A 从 C 里挑出来」** ——"
                "**凡是比较，必须问「这个差异能不能把目标从对照里挑出来」**\n"
                "  · ⇒ ⭐ 本批的诚实结论：**可区分项全是「按位置必然不同」的量** ⇒ "
                "**没有一个是内在属性** ⇒ **DOM 上依然查不到 ⇒ 原因不在 DOM**"),
            "skipwhy_964": {
                # ── 批 964：**源站** 那枚被跳过的节点到底特殊在哪（**纯读**）─────
                # 取样：探针 964，源站，登录态，视口 1512×1200，2 轮 × 1 格；
                # 助手与 JS 与 963 逐字相同（链式）⇒ 新件只有 `SKIPANATOMY_JS`（**纯读**）。
                "what_964_measures": (
                    "⭐⭐⭐⭐ 963 已把「跳过」**精确成恰好一枚**，并证明**那枚与邻居在 "
                    "`tabindex` 上完全同构**（全量 76 个全是 `None`）\n"
                    "  · ⇒ **`tabindex` 这条维度已经穷尽** ⇒ 本批换**非 `tabindex`** "
                    "的维度去找：几何 / 可见性 / 计算样式 / 属性集 / 类名 / "
                    "子节点数 / 文本长度 / 内部可聚焦控件数 / 是否被选中 / 父链 / "
                    "是否在视口内\n"
                    "  · ⚠️ 口径：拿它与**左右两个邻居**逐字段比（三个都同型 ⇒ "
                    "比邻居最严）\n"
                    "  · ⭐⭐ **判据可证伪**：若差异字段**为空**，那也是**正当结论**"
                    "（=「DOM 上根本查不到」）⇒ **不许**因为空就编一个机制圆上"),
                "slice_guard_fired_964": (
                    "⚠️⚠️ **探针在跑之前就被自己的切片守卫拦下**（**这正是它该做的事**）：\n"
                    "  · 第一版写的是 `(p.className || '').toString().slice(0, 40)`\n"
                    "  · 而切片守卫要的是**紧挨着**的 `|| '').slice(0, ` "
                    "⇒ **中间插了个 `.toString()` 就对不上**\n"
                    "  · ⇒ 改成 `(p.className || '').slice(0, 40)`\n"
                    "  · ⇒ ⭐ 顺带记一条：**这类「字面量守卫」只认逐字相邻** ⇒ "
                    "**任何在两者之间插的调用都会让它假红**（§131 的老坑）\n"
                    "  · ⇒ ⭐⭐ **正面意义**：它证明了**守卫是活的**（不是恒绿）——"
                    "与 946 那次「守卫自己匹配不上它要验的东西」正好成对"),
            },
            "nodecensus_963": {
                # ── 批 963：**源站** 全量节点 DOM 序普查 + 落点**对账** ──────────
                # 取样：探针 963，源站，登录态，视口 1512×1200，2 轮 × 1 格；
                # 助手与 JS 与 962 逐字相同（链式）⇒ 新件只有 `NODECENSUS_JS`（**纯读**）。
                "what_963_measures": (
                    "⭐⭐⭐⭐ 962 读到「**画布节点段**里 102/140 压是**应用在派发中"
                    "自己搬焦点**」⇒ 它**搬到哪**？962 读数里相邻落点的 "
                    "`Δdom_index` **+25 占 84/98** ⇒ 像是「DOM 序的下一枚节点」\n"
                    "  · ⇒ ⚠️ 但**「像」不是判决**：⭐ **NN.2 早就记过「节点上会"
                    "跳过 2 个」**，而那条**至今未查明**\n"
                    "  · ⇒ 判「有没有跳过」必须有一份**全量节点的 DOM 序清单**来"
                    "**对账**：走查落到的节点序列 == 全量清单？\n"
                    "  · ⚠️ 对账只比**身份**（tid），**不比绝对下标**"
                    "（959 记过：DOM 逐轮会漂）"),
                "verdict_963": (
                    "⭐⭐⭐⭐⭐ **落点序列 = 全量 DOM 序，只少一枚** —— "
                    "**NN.2 的「跳过 2 个」被精确成「恰好 1 个」**：\n"
                    "  · 全量节点 **76** 个（DOM 序）；这一轮走查落到节点 **106** 个"
                    "⇒ 它**绕了一整圈**（76 + 30）\n"
                    "  · 把落点换算成 census 下标后看**步长**：**+1 出现 103 次、"
                    "**+2 出现 1 次**、折返（负）**1 次**\n"
                    "  · ⇒ ⭐⭐⭐⭐ **除那一枚之外，每一步都是 DOM 序的下一枚**"
                    "⇒ 源站节点上的 `Tab` **就是 DOM 序**\n"
                    "  · ⇒ ⭐⭐⭐⭐⭐ **唯独被跳过的那一枚在 DOM 上与邻居完全同构**："
                    "同类型节点、同样的 aria 模式、**全量 76 个 `tabindex` 全是 "
                    "`None`（无差异可解释）**、DOM 间距也一样\n"
                    "  · ⇒ ⭐⭐⭐⭐ 「跳过」**不是 DOM 属性决定得了的** ⇒ "
                    "原因**在应用自己的节点表里**（NN.2 的原话）\n"
                    "  · ⇒ ⭐⭐ **NN.2 那条处置依然正确**：复刻**没法**复刻这一枚，"
                    "**只能按纯 DOM 序实现并把差异如实记为已知差异**；"
                    "本批把那个差异从「跳过 2 个」**精确成「跳过 1 个」**"),
                "criterion_was_wrong_963": (
                    "⚠️⚠️⚠️ **第一版的对账判据（「连续前缀」）是错的，被读数否掉**：\n"
                    "  · 它假设落点序列是 census 的**前缀** ⇒ 读出 `False`\n"
                    "  · ⇒ ⚠️ **那个 `False` 并不代表有 bug**：走查落到 **106** 个、"
                    "全量只有 **76** 个 ⇒ 它**绕了一整圈** ⇒ 「前缀」这个说法"
                    "**根本不成立**\n"
                    "  · ⇒ ⭐ **正确的判据是「步长」**：换算成 census 下标后，"
                    "绝大多数应是 **+1**，外加 ① 恰好一次折返、② 若干次 **+2**"
                    "（= 被跳过的节点数）\n"
                    "  · ⇒ ⭐⭐ **门也一起换了**：原来那道门挂在「连续前缀」上"
                    "⇒ 同样不成立 ⇒ 改挂**独立分母**（`+1` 次数 > 0、`>2` 的 0 次、"
                    "折返 ≥ 1 次）\n"
                    "  · ⇒ ⚠️ 第一版的判据与其 `False` 读数**都留档**"
                    "（`landed_is_census_prefix` / `landed_first_mismatch`），"
                    "**不许悄悄删掉**（承 HH.4）\n"
                    "  · ⚠️⚠️ **同类的错我这一批犯了两次**：另一道门"
                    "（`landed_subset_of_census`）也是**看读数之前**写的 —— "
                    "它要求「落点数 ≤ 普查数」，而这一轮落点 **106** > 普查 **76**"
                    "（**绕了一整圈**）⇒ **假红** ⇒ 改成分母**乘上圈数**\n"
                    "  · ⇒ ⭐⭐ **纪律**：**判据/门必须先把「走查会绕圈」这个"
                    "结构性事实算进去** —— 忘了它，**前缀型**与**上界型**的判据"
                    "**都会假红**"),
            },
            "focusmove_962": {
                # ── 批 962：**源站** 验「应用在 `keydown` 之后主动 `focus()`」─────
                # 取样：探针 962，源站，登录态，视口 1512×1200，2 轮 × 1 格；
                # 助手与 JS 与 961 逐字相同（链式）⇒ 新件只有
                # `FOCUSMOVE_JS` + `READ_FM_JS`（**加监听 + 读属性 + 摘还原**）。
                "what_962_measures": (
                    "⭐⭐⭐⭐ **判据 = 「派发结束那一刻焦点在哪」**：\n"
                    "  · 浏览器的**默认动作**（`Tab` 的原生移焦）是在**派发彻底结束"
                    "之后**才做的 ⇒ 只要在派发末尾（`document` 与 `window` 冒泡里"
                    "**较晚**的那个）读 `document.activeElement`：\n"
                    "    · 焦点**已经变了** ⇒ 必然是**派发过程中**被脚本 `focus()` 搬的\n"
                    "    · 焦点**还没变** ⇒ 默认动作之后才搬 ⇒ **浏览器搬的**\n"
                    "  · ⚠️ 只比**身份四字段**（tag/tid/aria/is_body）—— DOM 绝对"
                    "下标逐轮会漂（959 记过）"),
                "verdict_962": (
                    "⭐⭐⭐⭐⭐ **959 的 B（`Tab` 序 ≠ DOM 序）被否掉 —— 而否它的"
                    "是**关系**，不是绝对值**：\n"
                    "  · 整条走查的 `dom_index` **下降恰好 1 次**，且那一次是"
                    "**「高索引跳回低索引」**（文档**尾部折返到头部**）\n"
                    "  · ⇒ ⚠️⚠️⚠️ **959 的判决是用「单调不降」下的**，而**环形**走查"
                    "本来**必然**有下降 ⇒ **「非单调」推不出「乱序」**\n"
                    "  · ⇒ 那 6 个画布控件排在顶栏之前，**不是乱序，是绕了一圈**："
                    "走完文档尾部就回到头部（顶栏在头部）\n"
                    "  · ⭐⭐⭐⭐ **两条独立证据互相印证**：\n"
                    "    ① 时序：out 段那 18 个 chrome 停靠点**全部**是"
                    "**派发结束后**才变的焦点 ⇒ **浏览器原生移焦**，应用**没插手**\n"
                    "    ② 形状：`dom_index` **只有折返那一次**下降\n"
                    "  · ⇒ ⭐⭐⭐⭐⭐ **959–962 四批的谜团整个解开了**：源站就是"
                    "**朴素的、原生的、环形 DOM 序**——无正 `tabindex`（961）、"
                    "无 shadow root（960）、未被改写 ti（960）、未 `preventDefault`"
                    "（892/896）、不由应用搬焦点（962）\n"
                    "  · ⇒ ⭐⭐ **对复刻的直接含义**：**不需要**去对齐什么"
                    "「应用自己的焦点顺序表」（961 那个猜想**被否掉了**）——"
                    "**按 DOM 序**实现即可（与 NN.2 一致）\n"
                    "  · ⚠️ **961 的猜想不算「错」**：它是当时证据下**唯一**剩下的"
                    "方向 ⇒ **被否 ≠ 当时不该猜**；错的是**我第一版把"
                    "`isTrusted` 当成能区分「脚本 vs 浏览器」的证据**"),
                "istrusted_misread_962": (
                    "⚠️⚠️ **我第一版把 `isTrusted` 的语义写错了，被自己抓住**：\n"
                    "  · 我写的是「`false` = 脚本调的 `focus()`；`true` = 浏览器/"
                    "用户动作产生的」⇒ **错**\n"
                    "  · ⇒ **脚本调 `element.focus()` 产生的 focus 事件同样是 "
                    "trusted**（`isTrusted` 只区分「由用户代理产生」vs"
                    "「由 `dispatchEvent` 合成」）⇒ `isTrusted=True` **不能**"
                    "用来否掉「应用主动 `focus()`」\n"
                    "  · ⇒ ⭐ 真正判决性的是**「派发末尾 `activeElement` 变没变」**\n"
                    "  · ⇒ ⭐⭐ **通用纪律**：用一个 DOM 标志下结论前，"
                    "**先确认这个标志的语义边界**；`isTrusted` 这类标志的"
                    "「直觉语义」和真实语义**经常不一样**\n"
                    "  · ⚠️ 另记一条读数口径：`which_bubble` 记的是**最后一个**"
                    "写它的监听器 ⇒ 恒为 `window` ⇒ 它只证明**「window 冒泡"
                    "确实跑了」**（即派发没被 `stopPropagation` 掐断），"
                    "**不能**证明「`document` 冒泡没跑」"),
                "fm_latch_bug_962": (
                    "⚠️⚠️⚠️⭐⭐ **第一版的仪器有致命 bug，而门却是绿的**：\n"
                    "  · `FOCUSMOVE_JS` 里第一版写的是 `if (window.__fm) return "
                    "{already:true}`，而 `READ_FM_JS` 读完把 `__fm` 置 `true` 且"
                    "**再也不清** ⇒ 那个闩锁是**粘的**\n"
                    "  · ⇒ 整圈 ~140 按里**只有第 1 按**真的装了监听 ⇒ "
                    "读数只剩 1 按（**而门照样绿**）\n"
                    "  · ⇒ 改成以 `__fm_rec`（读完被置 `null`）为判据 ⇒ **重跑**\n"
                    "  · ⚠️⚠️ **更该记的是那道门**：它写的是 "
                    "`n_fm_armed == n_fm_rows` ⇒ 在「装 1 按、测 1 按」时**也成立**"
                    " ⇒ **恒真**\n"
                    "  · ⇒ ⭐⭐ **改法不是加条件，是换成和「按压总数」比**"
                    "（`n_fm_rows == n_lead`）⇒ 漏一按就红\n"
                    "  · ⇒ ⭐⭐⭐ **教训**：「两个数相等」这种门，在**其中一个数"
                    "本身坏掉**时是恒真的 ⇒ **门必须挂在独立的分母上**"),
                "guard_was_wrong_962": (
                    "⚠️⚠️ **第一版的「摘干净」守卫写错了，被自己抓住**（还没跑就红）：\n"
                    "  · 我数的是 `__fm_off` 这个**名字**出现几次（= 1 次定义）"
                    "⇒ 数「名字」**量不到「监听有没有摘干净」**\n"
                    "  · ⇒ 改成量**真正要保的东西**：`addEventListener` 与 "
                    "`removeEventListener` **必须配平**（4 : 4）\n"
                    "  · ⇒ ⭐ 同上：**守卫要量「后果」，不要量「名字」**\n"
                    "  · ⚠️ 另有一个**死字段** `same_target`：比的是 `rec._el0`，"
                    "而 `_el0` **从未被赋值** ⇒ 恒为无意义 ⇒ **删掉**"
                    "（**交付物里每个字段都得是真读数**）"),
                "focusin_miss_962": (
                    "⚠️ **有一根红着的门，原因已查明，**如实记**：\n"
                    "  · `focusin_heard_every_press` = **False**，因为 **140 按里有 1 按**"
                    "没听到 `focusin`\n"
                    "  · ⭐ 那一按是**落在画布根**（无 `data-testid`、aria 是整块画布文本）"
                    "的那一按 ⇒ 它的焦点落到了 **`document.body`**\n"
                    "  · ⇒ **`body` 不是可聚焦元素** ⇒ 移焦到它**只发 `blur`/`focusout`、"
                    "**不发 `focusin`** ⇒ 这是**真实读数**，不是「没测到」\n"
                    "  · ⇒ ⭐⭐ **决定：不为了变绿去放宽这道门** —— 它红得有理由、"
                    "而且**这个理由一旦变了它就会提醒** ⇒ 保留原样\n"
                    "  · ⇒ ⚠️ 同理 `app_moves_focus_before_dispatch_end` = **False** "
                    "也是**预期红**：整体 140 压里确有 102 压是**应用在派发中搬的**"
                    "（集中在**画布节点段**）⇒ ⭐ **「961 的猜想被否掉」只对"
                    "**out 段（chrome 停靠点）**成立**，这个限定**必须一起记**"),
                "forgot_register_p962": (
                    "⚠️⚠️⚠️⭐⭐ **同一个坑，隔一层又踩了一次**：\n"
                    "  · 962 写完判据后跑锚点自查 ⇒ **0 问题** ⇒ 我差点直接收工\n"
                    "  · ⇒ 真正暴露它的是**verifier 跑出一条 FAIL**（`XXXX.5`）\n"
                    "  · ⇒ 查下去：**`_p962` 我忘了登记进 `PROBE_VARS`**"
                    "（只登记了 `_p961`/`_p892`）⇒ **整组 `XXXX.*` 的锚文"
                    "全被静默跳过** ⇒ 「0 问题」**又一次是假绿**\n"
                    "  · ⇒ 登记后自查**立刻报出那条真 MISSING**（`same_target` "
                    "那条锚文多写了两个 `**`）⇒ **门与自查互相补位、缺一不可**\n"
                    "  · ⇒ ⭐⭐⭐ **纪律（补上 961 那条）**：**新增 `_pXXX` 变量时，"
                    "登记必须和写判据**同一步**完成** —— 「自查 0 问题」在"
                    "**新变量**上**不构成任何证据**\n"
                    "  · ⇒ ⚠️ 顺带修掉一处**编号冲突**（我一度让两条判据都叫 "
                    "`XXXX.6`）"),
                "residue_chain_962": (
                    "⚠️⚠️ **照抄基底留下的两样「产物级」残留，962 一并清了**：\n"
                    "  · ① **docstring 头连错了三批**：959/960/961 的文件头"
                    "**都还写着「batch 957」**（`cp` 做基底时只改了 `OUT`、没改头）"
                    "⇒ 照抄基底的核对清单**要加一条：文件头也算产物**\n"
                    "  · ② ⭐⚠️ **4 处真坏字节**（U+FFFD）——每个 3 字节汉字变成了"
                    " 2–3 个 U+FFFD（**早年被有损解码过一次**）\n"
                    "  · ⇒ 四处都能**从上下文无歧义恢复**（「新增」「同一」"
                    "「留下的」「两个」）⇒ 已修，**不猜、不留坏字节**\n"
                    "  · ⇒ ⚠️ 仓里另有 56 处 U+FFFD **属别的项目**（liblib / frameos）"
                    "⇒ **不碰**（不是这批的路径，也不该动别人的东西）"),
            },
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
        # ⚠️⚠️ `topbar-history-menu` **不在** NOT_SAMPLED 里了 —— 855b 取到样了，
        #    已进 SOURCE_BASELINE。**必须删掉这条**：循环是「先查
        #    NOT_SAMPLED、再查 SOURCE_BASELINE」，只要它还留在这儿就会被
        #    打回 `kb_not_sampled`，**永远进不了基线表**。
        #    留着旧文案就是**假病历**：它说「前置态没成立 / 这一版画布取不到样」，
        #    而事实是「**按位置猜名字猜错了**，按名字一找一个准」。
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
    # ⚠️ 这 3 层的「没取到」**原因各不相同**，下一步动作也完全不同 ——
    #    笼统写一句「没取过样」会把三种病混成一种。
    # ⚠️ 853 更正：这 3 层里**两层已升进基线表**（`audio-music-model-listbox`
    #    与 `audio-all-voices-listbox`，见 SOURCE_BASELINE），**第三层是源站
    #    事实**。三条 why 逐条改写 —— 留着旧文案就是**假病历**。
    NOT_SAMPLED["audio-music-duration-listbox"] = (
        "**源站没有这个入口**（853 实测，登录态，视口 1512×1200）。这一层原先记"
        "「前置态没成立」，理由是「切不到音乐生成分支」—— 853b 用**文本**找到"
        "「音乐生成」那个 `<SPAN role=\"\">`（851 按 `[role=option]:text-is(…)` "
        "**永远数不到它，因为它根本不是 role=option**）并成功切了过去；"
        "切过去之后 `button[aria-label^=\"选择时长\"]` 计数**仍是 0**"
        "（重新选中节点、等到面板刷新完，仍是 0），而同一时刻"
        "`选择模型` 计数是 1（`SeedMusic 1.0 Preview`）⇒ **音乐分支有模型、"
        "没有时长下拉**。\n"
        "⚠️ 这跟「判据量错对象」是**两码事**：这里触发器压根不存在，"
        "任何认法都找不到它。**源站没做的，不许在复刻里假称可用**，"
        "也不许按「音频分支有时长 ⇒ 音乐分支也该有」推测实现（847 明令）。")
    # ⚠️⚠️ `audio-all-voices-listbox` **不在** NOT_SAMPLED 里了 —— 刻意删掉的。
    #    循环是「先查 NOT_SAMPLED、再查 SOURCE_BASELINE」，只要它还留在
    #    NOT_SAMPLED 就会被打回 `kb_not_sampled`，**永远进不了基线表**。
    #    留一条备忘在这儿（而不是留一条 NOT_SAMPLED 记录），是因为它讲的是
    #    **判据史**不是「没取到样」：
    #      851b 记的「判据量错对象」是真的（矩形差分抓到 648×1932 整页容器），
    #      当时读出的「开层不接管焦点」是**伪像**；853b 换对认法后重测，
    #      结论**仍然是**「不接管焦点」—— 伪像与真结论**碰巧同形**。
    #    这正是 851b「不许放宽判据、要重新认层」的理由：放宽只会把伪像洗成
    #    结论，而重新认层才知道这次的「不接管焦点」是真的。
    kb_no_initial, kb_escaped, kb_arrow_dead = [], [], []
    # ══ 批 865：源站**无关**的模态语义桶 ══════════════════════════════
    #   上面三个桶全部基线门控。865 给「铺满视口且不透明」的层单开两条：
    #     · 模态却**没接管焦点**（焦点停在被自己遮住的触发器上，或掉到 body）
    #     · 模态却**不困 Tab**（焦点从层内漏回被遮住的页面）
    #   依据是「模态盖住了页面，就不该把焦点漏给页面」—— 模态自身的定义，
    #   与源站怎么实现无关。**刻意不查源站**：源站没取过样的层照样受管。
    #   ⚠️ 这两条**必须能红**，否则就是恒真的空话 —— 自检见 G 组。
    kb_modal_no_focus, kb_modal_no_trap = [], []
    kb_judged, kb_not_sampled = [], []
    for r in kb_rows:
        if r.get("ok") is not True:
            continue
        tid = r.get("layer")
        mi = r.get("modalish") or {}
        if mi.get("modalish") is True:
            at = r.get("focus_at_open") or {}
            if not at.get("inside"):
                kb_modal_no_focus.append({
                    "state": r.get("state"), "layer": tid,
                    "at_open": at.get("al") or at.get("state"),
                    "modalish_why": mi.get("why"),
                    "why": "这一层铺满视口且不透明（真模态），开层却没把焦点"
                           "放进层内 —— 焦点停在被自己遮住的地方，或掉到 body"})
            esc = r.get("escape") or {}
            if esc.get("trapped") is False:
                kb_modal_no_trap.append({
                    "state": r.get("state"), "layer": tid,
                    "escaped_at": esc.get("escaped_at"),
                    "landed": esc.get("landed"),
                    "modalish_why": mi.get("why"),
                    "why": "真模态却没有焦点陷阱：第 "
                           f"{esc.get('escaped_at')} 次 Tab 就跑回被遮住的页面"})
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
                   "by_layer": by_layer,
                   "keyboard": kb_rows,
                   "keyboard_bad": kb_bad,
                   "keyboard_covered": kb_covered,
                   "keyboard_deep": kb_deep,
                   "keyboard_deep_threshold": DEEP,
                   "keyboard_no_initial_focus": kb_no_initial,
                   "keyboard_escaped": kb_escaped,
                   "keyboard_arrow_dead": kb_arrow_dead,
                   "keyboard_modal_no_focus": kb_modal_no_focus,
                   "keyboard_modal_no_trap": kb_modal_no_trap,
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
          f"被非全屏浮层盖住（正常，INFO）{len(by_layer)}、"
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
    # ══ 批 865：模态语义（**源站无关**）══════════════════════════════
    #   上面那三项是**基线门控**的 —— 源站没取过样的层不受管。§82 抓到的
    #   两个模态正好在基线表外，所以它们的焦点行为当时只是一次性测量。
    #   下面这条按**层自己的形状**判：铺满视口且不透明 = 真模态 ⇒ 必须
    #   接管焦点 + 困 Tab。依据是模态自身的定义，不依赖源站。
    #   ⚠️ 必须**打印**出来：定义了却不印，等于「写了但没人看」，
    #   下一批就会当死代码删掉（verifier R.5 钉住它在源码里）。
    _mod_layers = sorted({r.get("layer") for r in kb_rows
                          if (r.get("modalish") or {}).get("modalish") is True})
    print(f"模态语义（源站无关）：认出的真模态 {len(_mod_layers)} 个"
          f"（{', '.join(_mod_layers) or '—'}） → "
          f"**没接管焦点 {len(kb_modal_no_focus)}**、"
          f"**不困 Tab {len(kb_modal_no_trap)}**")
    for k in kb_modal_no_focus:
        print(f"  ★ 真模态却**没接管焦点** [{k['state']}] 浮层={k['layer']!r}："
              f"开层时焦点在 {k.get('at_open')!r} —— {k.get('modalish_why')}；"
              f"模态盖住了页面，就不该把焦点漏给页面（{k['why']}）")
    for k in kb_modal_no_trap:
        print(f"  ★ 真模态却**不困 Tab** [{k['state']}] 浮层={k['layer']!r}："
              f"第 {k.get('escaped_at')} 次 Tab 跑回 "
              f"al={(k.get('landed') or {}).get('al')!r} "
              f"tid={(k.get('landed') or {}).get('tid')!r} —— {k['why']}")
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
                 or kb_no_initial or kb_escaped or kb_arrow_dead
                 # 批 865：模态语义桶也参与判缺陷 —— 写了却不进退出码，
                 # 等于「定义了但没人看」，下一批就会把它当死代码删掉。
                 or kb_modal_no_focus or kb_modal_no_trap) else 0


if __name__ == "__main__":
    sys.exit(main())

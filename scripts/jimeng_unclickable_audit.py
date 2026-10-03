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
                "75 个被布过」。\n"
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

#!/usr/bin/env python3
"""jimeng **浮层普查（按几何，不按 role）** —— §38 契约的第二条通道。

## 为什么要有第二个通道

§38 立契约「每个浮层都要可指名 + 可定位」，历来的普查都靠
`role ∈ dialog/menu/listbox/popover` 去找浮层。**这个选法有结构性盲区**：

    div.react-flow__node-toolbar
      └ div[data-testid=video-toolbar-capture-menu]   ← 裸 div，**没有 role**
      └ div[data-testid=video-toolbar-tools-menu]     ← 同上

这两处（批 836 补的锚点）在 role 型普查里**永远枚举不到**。源站侧测不到它们
该有什么 role（BLOCKED_BY_FIXTURE），所以**不能靠加 role 来让普查看见它们** ——
那会拿改产品去迁就工具，掩盖问题。

正确的做法是**换一条通道**：不认 role，认**几何 + 可交互性** —— 一块
「浮在别的东西之上、深色圆角板、里面至少有两个可交互子元素」的容器，
就是候选浮层，有没有 role 都报出来。

## 判据（枚举脚本全程**不引用** role 属性 —— 引用了就等于没开这条通道）

  ① 几何：`position: absolute|fixed|sticky` 且面积 ≥ 阈值
  ② 层级：`z-index ≥ 100`，或挂在已知浮层宿主内
  ③ 可交互：内部 ≥ 2 个可交互子元素（button / [role=*] / input / a …）
  ④ 可见：非 display:none / visibility:hidden，尺寸 ≥ 阈值

排除（**按身份，不按尺寸** —— 批 840 实测把「≥1500×700 就跳过」那条改掉了：
它和画布壳尺寸一模一样，顺带吃掉了全屏模态）：`.react-flow__renderer` /
`.react-flow__pane` / `.react-flow__viewport` / `.react-flow__nodes`（画布自身）、
`.react-flow__node`（装着浮层的那一层）、`.react-flow__node-toolbar`
（xyflow 自己的宿主壳，复刻控制不了；工具条自己的锚点是内层 `node-toolbar`）、
顶栏容器 `canvas-top-bar`（装着那些浮层的架子）。

## 退出码

  0 = 每个候选浮层都有 data-testid
  1 = 有缺锚点的
  2 = **自检没过**（判据恒真，本轮结果不可信）—— 不是 0，否则 CI 会当通过

## 用法

    python3 scripts/jimeng_floating_layer_audit.py
    SNAP_OUT=/tmp/x.json 换输出路径
"""

import json
import os
import sys

from playwright.sync_api import sync_playwright

URL = os.environ.get("SNAP_URL", "http://localhost:4317/jimeng/canvas/demo")
OUT = os.environ.get("SNAP_OUT", "/tmp/jimeng-floating-layers.json")
VIEWPORT = {"width": 1680, "height": 1050}

# 豁免清单：没有 data-testid 是**已知**且有理由的，逐条自带取证结论。
# 与批 831/832 的白名单同一套规矩：不许写「同上」。
#
# ⚠️ 这里曾经放过一个 `"": "..."` 的条目 —— 空 tid 于是被**全部**豁免，
#    `缺锚点` 恒为 0，工具"永远通过"。**万能钥匙式的豁免比没有豁免更糟**：
#    它让工具看起来在干活。现在一条都不该有。
NO_TID_EXEMPT: dict[str, str] = {}

ENUM_JS = """() => {
  const vis = (e) => {
    const s = getComputedStyle(e);
    if (s.display === 'none' || s.visibility === 'hidden') return false;
    const r = e.getBoundingClientRect();
    return r.width >= 24 && r.height >= 16;
  };
  const INTERACTIVE = 'button,[role=option],[role=menuitem],[role=radio],'
                    + '[role=tab],a[href],input,select,textarea,[tabindex]';
  const nameOf = (e) => {
    const al = e.getAttribute('aria-label');
    if (al && al.trim()) return al.trim();
    const lb = e.getAttribute('aria-labelledby');
    if (lb) {
      const t = lb.split(/\\s+/).map(id => document.getElementById(id))
        .filter(Boolean).map(n => (n.getAttribute('aria-label')
             || n.innerText || '').trim()).join(' ').trim();
      if (t) return t;
    }
    return '';
  };
  const out = [];
  const seen = new Set();
  for (const e of document.querySelectorAll('body *')) {
    if (!vis(e)) continue;
    const s = getComputedStyle(e);
    if (!['absolute', 'fixed', 'sticky'].includes(s.position)) continue;
    // ③ 可交互：**≥1 个**就行。
    //    第一版写 ≥2，把「音乐模型」这种**只有一个选项**的下拉挡在外面 ——
    //    实测它 392×66、items=1，absolute、z=140、挂在 node-toolbar 里，
    //    四个条件里只差这一条。一个只有一项的下拉仍然是浮层。
    const kids = e.querySelectorAll(INTERACTIVE);
    if (kids.length < 1) continue;
    // ② 层级：z ≥ 100 / 挂在已知宿主内 / **顶栏内**。
    //    账号菜单（canvas-user-menu 240×312）、更多菜单、搜索、生成历史全是
    //    `absolute` 但**没有 z-index**，也不在节点宿主里 ⇒ 只看 z 的话这四层
    //    全被挡掉。顶栏浮层挂在 `header[aria-label="Canvas top bar"]` 内，
    //    那是它唯一的共同挂载点。
    const z = parseInt(s.zIndex || '0', 10);
    // 缩放菜单（canvas-zoom-menu）是 `absolute` + **无 z-index** + 不在节点宿主
    // 里，只看 z 就被挡掉；它的实测挂载点是底部 dock，所以 dock 也算宿主。
    const host = e.closest('.react-flow__node-toolbar, .react-flow__node-panel, '
                          + '[data-testid="canvas-node-insert-menu"], '
                          + '[data-testid="canvas-insert-submenu"], '
                          + '[data-testid="canvas-bottom-dock"], '
                          // 缩放菜单实测父链是 `div.jimeng-bottom-dock.relative`
                          // —— **类名**，不是那个 testid（testid 在它里面的
                          // 一层上）。只加 testid 会漏掉。
                          + '.jimeng-bottom-dock');
    const inTopbar = !!e.closest('header[aria-label="Canvas top bar"]');
    if (!(z >= 100 || host || inTopbar)) continue;
    const r = e.getBoundingClientRect();
    // ⚠️ 这里原先写的是「`w ≥ 1500 && h ≥ 700` 就跳过」（排除铺满全屏的巨型容器）。
    //    **那条规则是错的**，它把全屏模态一起吃掉了 —— 批 840 实测：
    //      · react-flow__renderer  1680×1050  z=4   透明底  21 个可交互子元素  ← 该排除
    //      · react-flow__pane      1680×1050  z=1   透明底  10 个可交互子元素  ← 该排除
    //      · fixed inset-0 z-[400] 1680×1050 z=400 黑/60 底 4 个可交互子元素  ← **真模态**
    //    三者尺寸完全一样，只有**身份**不同。视频全屏预览（`role="dialog"`）就
    //    这么整整一个状态没被枚举到，而它是货真价实的浮层。尺寸只是表象。
    //    源站侧同样中招：timeline-fullscreen-editor 1512×950，它的
    //    `fixed inset-0 bg-octo-overlay z-50` 遮罩也是同尺寸且**没有锚点**。
    //
    //    ⚠️ 第一版改错过一次：用 `closest('.react-flow__renderer, ...)` ——
    //    `closest` 走的是**祖先链**，于是画布里所有东西（节点工具条、生成面板、
    //    十来个下拉）全被干掉，一轮下来 14 个状态变成「打开了却枚举不到」。
    //    正确写法是两条分开：**自身**是流壳就排除，**包含**画布的祖先壳才排除。
    //    仍然**不引用 role**：判别靠挂载点，不靠语义。
    const FLOW_SHELL = ['react-flow__renderer', 'react-flow__pane',
                        'react-flow__viewport', 'react-flow__nodes',
                        'react-flow__viewport-portal',
                        'react-flow__edgelabel-renderer'];
    if (e.classList
        && FLOW_SHELL.some(c => e.classList.contains(c))) continue;
    if (e.querySelector('.react-flow__renderer')) continue;
    if (e.classList && e.classList.contains('react-flow__node')) continue;
    if (e.classList && e.classList.contains('react-flow__node-toolbar')) continue;
    // ⚠️ 同样排除**顶栏容器本身**：它 absolute + 在 header 内 + 10 个按钮，
    //    三个条件全中，但它是**装着**那些浮层的架子（还带 pointer-events-none）。
    //    浮层在它**里面**，各自有锚点。
    if (e.closest('header[aria-label="Canvas top bar"]') &&
        e.getAttribute('data-testid') === 'canvas-top-bar') continue;
    const key = s.position + '|' + Math.round(r.x) + '|' + Math.round(r.y)
              + '|' + Math.round(r.width) + 'x' + Math.round(r.height);
    if (seen.has(key)) continue;
    seen.add(key);
    out.push({
      tid: e.getAttribute('data-testid') || '',
      role: e.getAttribute('role') || '',      // 只作**记录**，不作筛选条件
      // 自检探针的标记：让自检能**在重扫结果里认出这一个元素**，
      // 而不必靠"元素还在不在"那种恒真判断（见下方自检段）。
      selfcheck: e.getAttribute('data-selfcheck') || '',
      name: nameOf(e),
      pos: s.position, z: z,
      w: Math.round(r.width), h: Math.round(r.height),
      x: Math.round(r.x), y: Math.round(r.y),
      items: kids.length,
      inHost: !!host,
      inTopbar: inTopbar,
      cls: (e.className || '').toString().replace(/\\s+/g, ' ').slice(0, 60),
    });
  }
  return out;
}"""


def main() -> int:
    rows: list[dict] = []
    skipped: list[str] = []          # 前置态没成立的状态 —— 如实记录，不静默跳过
    empty: list[str] = []            # 打开了但枚举到 0 个候选 —— 与 skipped 分开记账
    expected_empty: list[str] = []   # 这个状态本来就没有浮层（正常，不是盲区）
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        ctx = b.new_context(viewport=VIEWPORT)
        page = ctx.new_page()
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        # ⚠️ **不要用固定等待**。开发期并行会话一直在改文件 → Next dev 周期性
        #    重编译重载 → 有时 6 秒后画布还没就绪（节点数不足、左栏按钮没挂上）。
        #    实测这会让「选不中 rf__node-video-local-1」连着 8 个状态一起废掉，
        #    而输出里只写"前置态不成立"，**看不出是页面没加载好还是判据坏了**。
        #    改成轮询一个明确的就绪条件。
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
            print("⚠ 页面 30s 内没就绪（节点/左栏未出现），本轮结果**不可信**")

        # ── 以下四个 helper 是 832/835/836 三批踩坑换来的，别再简化 ──
        def census(tag: str) -> int:
            got = page.evaluate(ENUM_JS)
            for r in got:
                r["state"] = tag
                rows.append(r)
            return len(got)

        def clear_selection() -> None:
            """清空选中。

            必须清：工具条/生成面板的门控是 `selected === true && soloSelected`，
            `addNodeAt` 插出的新节点自带 selected ⇒ 计数 2 ⇒ 面板**永远不挂**。
            用点画布空白，不用 Escape（那会连浮层一起卸载）。
            """
            pt = page.evaluate("""() => {
              const pane = document.querySelector('.react-flow__pane');
              if (!pane) return null;
              const r = pane.getBoundingClientRect();
              for (const [fx, fy] of [[0.02,0.95],[0.98,0.95],[0.02,0.05],[0.98,0.05],
                                      [0.5,0.97],[0.5,0.03]]) {
                const x = r.left + r.width * fx, y = r.top + r.height * fy;
                const h = document.elementFromPoint(x, y);
                if (h && pane.contains(h)) return {x, y};
              }
              return null;
            }""")
            if pt:
                page.mouse.click(pt["x"], pt["y"])
                page.wait_for_timeout(450)
            else:
                page.keyboard.press("Escape")
                page.wait_for_timeout(400)

        def select_node(tid: str, retry: int = 1) -> bool:
            """选中一个节点（且**只**选中它）。

            两点都是踩出来的：
              ① 命中点**不能落在控件上** —— 带媒体的视频节点中心是 32px 的
                 播放/暂停键，它 onClick 有 stopPropagation ⇒ 点了不选中。
              ② 画布上节点互相叠压，坐标点击常被别的节点子树拦截，`force=True`
                 也没用（真实事件仍落到最上层）。所以先用 `elementFromPoint`
                 问**事实**：哪个采样点的最上层元素落在本节点内且不是控件。
            """
            for attempt in range(retry + 1):
                if attempt:
                    page.wait_for_timeout(1200)
                if _select_once(tid):
                    return True
            return False

        def _select_once(tid: str) -> bool:
            clear_selection()
            pt = page.evaluate(
                """(tid) => {
              const n = document.querySelector(`.react-flow__node[data-testid="${tid}"]`);
              if (!n) return null;
              const r = n.getBoundingClientRect();
              if (r.width < 8 || r.height < 8) return null;
              const CTRL = 'button,[role=button],a,input,select,textarea,'
                         + '[role=option],[role=menuitem],[role=tab]';
              for (const [fx, fy] of [[0.5,0.5],[0.5,0.25],[0.25,0.5],[0.75,0.5],
                                      [0.5,0.75],[0.2,0.2],[0.8,0.8],[0.3,0.3],
                                      [0.7,0.7],[0.15,0.5],[0.85,0.5],[0.5,0.15]]) {
                const x = r.left + r.width * fx, y = r.top + r.height * fy;
                const h = document.elementFromPoint(x, y);
                if (h && n.contains(h) && !h.closest(CTRL)) return {x, y};
              }
              return null;
            }""", tid)
            if pt is None:
                return False
            page.mouse.click(pt["x"], pt["y"])
            page.wait_for_timeout(900)
            return page.evaluate(
                "() => document.querySelectorAll('.react-flow__node.selected').length === 1")

        TID2TRIG = {
            # ⚠️ 这两条是批 840 补的：原来**缺**它们，于是 `close_open()` 从来
            #    关不掉视频节点那两个下拉 —— 开着的工具下拉会一路漏到后面某个
            #    状态，被当成那个状态的浮层记进去（839 那轮「截帧」状态报出的
            #    1 个候选就是它）。「漏下去」比「漏报」更坏：它让一个干净的
            #    状态看起来有浮层，还让真浮层张冠李戴。
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

            定位器要**同时**试 `aria-label` 和可见文案：视频节点工具条上那两枚
            （截取帧 / 工具）压根没有 aria-label，名字就在按钮文字里 —— 只按
            `aria-label^=` 找，一个都匹配不到。
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

        def open_trigger(sel: str, want_tid: str | None = None,
                         scope: str = ".react-flow__node-toolbar") -> bool:
            """打开一个下拉。幂等 + 先收起别的（批 835 的教训，见上）。"""
            close_open()
            if want_tid and page.locator(f'[data-testid="{want_tid}"]').count():
                return True
            loc = page.locator(f'{scope} {sel}' if scope else sel)
            if not loc.count():
                return False
            try:
                loc.first.click(timeout=8000)
            except Exception:
                return False
            page.wait_for_timeout(650)
            return True

        def node_tids() -> list[str]:
            return page.evaluate(
                "() => [...document.querySelectorAll('.react-flow__node')]"
                ".map(n => n.getAttribute('data-testid'))")

        def insert(kind: str) -> str | None:
            """插入节点并返回新节点的 testid（按集合差分，不按序号）。

            ⚠️ 不能让异常冒出去：左栏按钮在**开发期重编译**时会短暂消失
            （并行会话改文件 → Next dev 重载 → 那一瞬间 DOM 重建），
            一次 30s 超时会把**整份审计**带崩，前面 20 个状态的结果全丢。
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

        def step(tag: str, cond: bool, want: str = "",
                 expect_empty: str = "") -> None:
            """跑一个状态并普查。

            两种"没结果"必须**分开记账**，都不能沉默：
              · 前置态不成立（`cond` 为假）⇒ skipped
              · 浮层确实打开了，但几何判据枚举到 0 个候选 ⇒ empty
            第一版把第二种情况**静默吞掉**了：账号菜单/搜索/生成历史三个状态
            既不在统计里、也不在 skipped 里，看上去像"跑过了且没问题"。
            **"跑了但没看见"和"没跑"必须能被区分开**，否则漏报不可见。
            """
            if not cond:
                skipped.append(f"{tag}（{want or '前置态不成立'}）")
                return
            n = census(tag)
            # ⚠️ 普查完**必须把浮层收掉**。批 840 实测到这条是必要的：
            #    839 那轮「图片节点产出（截帧）」这个状态报出了 1 个候选
            #    `video-toolbar-tools-menu` —— 那是**两个状态之前**开的工具下拉
            #    一路漏到了这里，被当成本状态的浮层记了进去。
            #    漏出去的两面：真浮层被安到别的状态名下（张冠李戴），
            #    以及下一个状态明明干净却被算成「开着却看不见」（假盲区）。
            close_open()
            if n == 0:
                # 「这个状态本来就没有浮层」与「浮层开着但判据看不见」是两回事。
                # 前者是正常的（例如空态、工具条那层架子），后者是盲区 ——
                # 混在一起报，等于让正常项稀释真正的盲区。
                if expect_empty:
                    # ⚠️ 结构化存，**不要**再拼成 `f"{tag}（{reason}）"`。
                    #    批 840 踩过：verifier 那边按 `（` 切回状态名，
                    #    而状态名**本身就可能带括号**（`图片节点产出（截帧）`）
                    #    —— 一拼一拆就张冠李戴，白名单永远对不上，而且错得
                    #    很像"工具有 bug"。歧义要从**格式**上根除。
                    expected_empty.append({"state": tag, "reason": expect_empty})
                else:
                    empty.append(f"{tag}（浮层已打开，但几何判据枚举到 0 个候选）")

        # ══ A. 空态 ══════════════════════════════════════════════
        step("空态", True, expect_empty="画布上本来就没有任何浮层")

        # ══ B. 视频节点（带媒体）工具条 ══════════════════════════
        sel = select_node("rf__node-video-local-1")
        step("视频工具条", sel, "选不中 rf__node-video-local-1",
             expect_empty="工具条本身是 React Flow 的宿主架，判定为不是浮层；"
                          "它带出来的两个下拉由下面两个状态各自枚举")
        step("视频工具条·截取帧下拉",
             open_trigger('button:text-is("截取帧")', "video-toolbar-capture-menu"),
             "截取帧下拉打不开")
        step("视频工具条·工具下拉",
             open_trigger('button:text-is("工具")', "video-toolbar-tools-menu"),
             "工具下拉打不开")

        # ══ B·. 视频全屏预览（全屏模态，批 840 新增）══════════════
        #    这是**第一条按「不再被尺寸规则挡掉」而进来的状态**。
        #    旧规则「≥1500×700 的巨型容器跳过」会把它整个吃掉：实测它是
        #    fixed 1680×1050、z=400、黑/60 底、4 个可交互子元素的真模态。
        #    源站侧同样中招（timeline-fullscreen-editor 1512×950，
        #    连它的 `fixed inset-0 bg-octo-overlay z-50` 遮罩也是同尺寸且无锚点）。
        sel = select_node("rf__node-video-local-1")
        ok_fs = False
        if sel:
            close_open()
            # ⚠️ **不要**先去开「工具」下拉：`全屏预览` 这枚按钮本身就平铺在
            #    工具条上（`JimengNodeToolbar` 里它在工具下拉 div **之外**），
            #    多开一个下拉只会让普查把工具菜单也记进这个状态名下。
            #    顺带说明「点了之后工具下拉还开着」不是判据的毛病：那是真状态。
            #    源站这枚的实名是「全屏编辑」，复刻收口成「全屏预览」
            #    （见 JimengNodeToolbar 里那条注释）。这里认**复刻真值**。
            fs_btn = page.locator(
                '.react-flow__node-toolbar button[aria-label="全屏预览"]')
            if fs_btn.count():
                try:
                    fs_btn.first.click(timeout=8000)
                    page.wait_for_timeout(900)
                except Exception:
                    pass
                ok_fs = page.locator(
                    '[data-testid="video-fullscreen-preview"]').count() >= 1
            if ok_fs:
                step("视频全屏预览", True)
                page.keyboard.press("Escape")
                page.wait_for_timeout(700)
            else:
                step("视频全屏预览", False, "全屏预览浮层没打开")

        # ══ C. 视频生成面板（空视频节点）═══════════════════════════
        sel = select_node("rf__node-video-empty-1")
        step("视频生成面板", sel, "选不中 rf__node-video-empty-1",
             expect_empty="生成面板是工具条里的一块板，本身没有独立锚点；"
                          "它内部的 4 个下拉由下面 4 个状态各自枚举")
        for trig, tid, label in [
            ("选择模型", "gen-model-listbox", "模型"),
            ("视频尺寸选项", "gen-video-size-listbox", "尺寸"),
            ("生成模式", "gen-mode-listbox", "模式"),
            ("选择视频生成时长", "gen-duration-listbox", "时长"),
        ]:
            step(f"视频生成面板·{label}下拉",
                 open_trigger(f'button[aria-label^="{trig}"]', tid), f"{trig} 打不开")

        # ══ D. 文本节点 ═══════════════════════════════════════════
        txt = insert("文本")
        opened = False
        if txt and select_node(txt):
            loc = page.locator(f'.react-flow__node[data-testid="{txt}"]')
            if loc.count():
                try:
                    loc.first.dblclick(timeout=8000)
                    page.wait_for_timeout(1100)
                except Exception:
                    pass
            # 「背景色」只在**选中非编辑态**的工具条上（isVisible={selected && !editing}）
            sel2 = select_node(txt)
            opened = open_trigger('button[aria-label="背景色"]', "text-bg-palette")
        step("文本·背景色调色板", opened and sel2, "背景色调色板打不开")

        # ══ E. 图片节点（带 poster：走「截取帧 → 首帧」才有）════════
        # 带 poster 的图片节点**只能**靠视频「截取帧 → 首帧」产出：左栏新插的
        # 图片节点没有 poster，渲染的是生成面板而不是工具条（批 832 踩过）。
        # 每一步单独记账 —— 只报一句"没产出"等于什么都没说。
        before = set(node_tids())
        framed, why = None, ""
        sel_v = select_node("rf__node-video-local-1")
        if not sel_v:
            why = "选不中 rf__node-video-local-1（选中数≠1）"
        elif not open_trigger('button:has-text("截取帧")',
                              "video-toolbar-capture-menu"):
            why = "截取帧下拉打不开"
        else:
            it = page.locator('.react-flow__node-toolbar button:text-is("首帧")')
            if not it.count():
                # 只报"没有首帧项"等于什么都没说。把工具条上**此刻真实存在**的
                # 按钮文案全打出来：是下拉没开（只有工具条那几枚），还是开了但
                # 里面是别的字。这两者的修法完全不同。
                labels = page.evaluate("""() => [...document.querySelectorAll(
                    '.react-flow__node-toolbar button')]
                    .map(b => (b.innerText || b.getAttribute('aria-label') || '').trim())""")
                opened = page.locator(
                    '[data-testid="video-toolbar-capture-menu"]').count()
                why = (f"下拉里没有「首帧」项（截取帧下拉此刻{'开着' if opened else '**没开**'}）；"
                       f"工具条按钮={labels}")
            else:
                it.first.click()
                page.wait_for_timeout(2200)
                new = [t for t in node_tids() if t not in before and t and "image" in t]
                framed = new[0] if new else None
                if framed is None:
                    why = f"点了首帧但没长出图片节点（现有 {len(node_tids())} 个节点）"
        # 这个状态**本来就不该有浮层**：点「首帧」只是长出一个图片节点，
        # 它的工具菜单是**下一个状态**才打开的。标成 expected_empty 而不是留成
        # 盲区——839 那轮它报出的那 1 个候选是漏过来的工具下拉，0 才是真值。
        step("图片节点产出（截帧）", framed is not None, why,
             expect_empty="截帧只产出图片节点，本身不打开任何浮层；"
                          "它的工具菜单由下面那个状态各自枚举")
        img_ok, why2 = False, ""
        if framed is None:
            why2 = "没有带 poster 的图片节点"
        elif not select_node(framed):
            why2 = "选不中图片节点"
        else:
            img_ok = open_trigger('button:text-is("工具")', "image-tools-menu")
            if not img_ok:
                why2 = "工具菜单打不开"
        step("图片工具条·工具菜单", img_ok, why2)

        # ══ F. 音频生成面板 ═══════════════════════════════════════
        aud = insert("音频")
        for branch, expect in [
            ("音乐生成", [("选择模型", "audio-music-model-listbox", "音乐模型"),
                          ("选择时长", "audio-music-duration-listbox", "音乐时长")]),
            ("音频生成", [("选择模型", "audio-voice-model-listbox", "音色模型"),
                          ("音频生成", "audio-gen-mode-listbox", "音频生成模式"),
                          ("音色", "audio-all-voices-listbox", "全音色")]),
        ]:
            if aud and select_node(aud):
                if open_trigger('button[aria-label^="创作类型"]', "audio-gen-type-listbox"):
                    opt = page.locator('[data-testid="audio-gen-type-listbox"] [role=option]'
                                       f':text-is("{branch}")')
                    if opt.count():
                        opt.first.click()
                        page.wait_for_timeout(900)
            for trig, tid, label in expect:
                if aud:
                    select_node(aud)
                step(f"音频生成面板·{label}",
                     open_trigger(f'button[aria-label^="{trig}"]', tid), f"{trig} 打不开")

        # ══ G. 画布级浮层 ═════════════════════════════════════════
        clear_selection()
        page.mouse.click(840, 700, button="right")
        page.wait_for_timeout(700)
        step("画布右键菜单",
             page.locator('[data-testid="canvas-context-menu"]').count() >= 1,
             "右键菜单没出现")
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)

        z = page.locator('[data-testid="canvas-zoom-percent"]')
        if z.count():
            z.first.click()
            page.wait_for_timeout(650)
        step("缩放菜单",
             page.locator('[data-testid="canvas-zoom-menu"]').count() >= 1,
             "缩放菜单没出现")
        if page.locator('[data-testid="canvas-zoom-menu"]').count():
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)

        # ══ H. 顶栏浮层 ═══════════════════════════════════════════
        # testid 全部来自源码实测（第一版这四个是**凭印象猜的**，四个全错：
        # 真实值是 topbar-share-panel / topbar-more-menu / jimeng-search-overlay
        # / topbar-history-menu。猜名字的代价是四个状态白跑一轮。）
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
                    # 点不开就当这个状态没成立，由 step() 如实记账
                    page.locator('[data-testid="canvas-top-bar"]').first.click(
                        timeout=3000) if page.locator(
                        '[data-testid="canvas-top-bar"]').count() else None
                    page.wait_for_timeout(400)
            step(f"顶栏·{name}",
                 page.locator(f'[data-testid="{tid}"]').count() >= 1,
                 f"顶栏 {label} 打开后没找到 {tid}")
            page.keyboard.press("Escape")
            page.wait_for_timeout(450)

        # ── 自检：把一个锚点摘掉，普查**必须**报出来 ──────────────
        #     不做这一步，"缺锚点 0 个"就没有分量。
        selfcheck: dict = {}
        probe_tid = "video-toolbar-capture-menu"
        if select_node("rf__node-video-local-1") and \
                open_trigger('button:text-is("截取帧")', probe_tid):
            removed = page.evaluate(
                """(tid) => {
                  const e = document.querySelector(`[data-testid="${tid}"]`);
                  if (!e) return false;
                  e.removeAttribute('data-testid');
                  e.setAttribute('data-selfcheck', '1');
                  return true;
                }""", probe_tid)
            if removed:
                # ⚠️ 这里**必须重跑整段几何枚举**，不能只查 `[data-selfcheck]`
                #    还在不在 —— 那种写法 `still_candidate = bool(rows2)`
                #    恒为真（`removed` 为真 ⇒ 元素必然还在），等于没有自检：
                #    哪怕有人把枚举改成"只挑有 data-testid 的"，它照样报 ✓。
                #    真重扫才能证明几何判据**不依赖锚点**。
                rows2 = page.evaluate(ENUM_JS)
                probe = [r for r in rows2 if r.get("selfcheck") == "1"]
                selfcheck = {
                    "removed": probe_tid,
                    "still_candidate": bool(probe),
                    "now_reported_missing": any(not r.get("tid") for r in probe),
                }
                page.evaluate("""() => document.querySelectorAll('[data-selfcheck]')
                    .forEach(e => e.removeAttribute('data-selfcheck'))""")

        ctx.close()
        b.close()

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"rows": rows, "skipped": skipped, "empty": empty,
                   "expected_empty": expected_empty},
                  f, ensure_ascii=False, indent=2)

    missing = [r for r in rows if not r["tid"] and r["tid"] not in NO_TID_EXEMPT]
    by_state: dict[str, int] = {}
    for r in rows:
        by_state[r["state"]] = by_state.get(r["state"], 0) + 1

    print(f"候选浮层 {len(rows)} 次 / {len(by_state)} 个状态；无 data-testid {len(missing)} 个")
    for s, n in by_state.items():
        print(f"  {s:26} {n}")
    if skipped:
        print(f"\n⚠ 前置态没成立、**没跑到**的状态（{len(skipped)} 个，不算通过）：")
        for s in skipped:
            print(f"    - {s}")
    if expected_empty:
        print(f"\n· 本来就没有浮层的状态（{len(expected_empty)} 个，正常）：")
        for s_ in expected_empty:
            print(f"    - {s_['state']}（{s_['reason']}）")
    if empty:
        print(f"\n⚠ 打开了、但几何判据枚举到 **0 个候选**的状态（{len(empty)} 个）：")
        print("   —— 这不是「干净」，是**判据看不见它们**。要么补判据，要么记为盲区。")
        for s in empty:
            print(f"    - {s}")
    for r in missing:
        print(f"  ★ 缺锚点 [{r['state']}] role={r['role']!r} {r['w']}x{r['h']} "
              f"@{r['x']},{r['y']} items={r['items']} cls={r['cls'][:44]!r}")

    # 自检结果打在**最前面**：它决定上面那份"0 个缺锚点"值不值得信
    ok_self = (bool(selfcheck) and selfcheck.get("still_candidate")
               and selfcheck.get("now_reported_missing"))
    print(f"\n自检：摘掉 {selfcheck.get('removed')} 的 data-testid 后，"
          f"**重跑几何枚举**仍把它当候选={selfcheck.get('still_candidate')}、"
          f"并报成缺锚点={selfcheck.get('now_reported_missing')}"
          f"  →  {'✓ 判据能失败' if ok_self else '✗ 判据恒真，这轮结果不可信'}")
    if not ok_self:
        return 2
    print(f"明细已写入 {OUT}")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())

"""Jimeng canvas fixed-position census — `position: fixed` 有没有被 transform 祖先收编。

起因（batch 821）：全屏时间线编辑器写着 `class="fixed inset-0"`，实测只铺满
**1200×207 的节点**而不是视口。根因不是写错了关键字，是
**任何建立包含块的 transform 祖先都会成为 `position: fixed` 的包含块** ——
React Flow 给每个节点加 `transform`，于是 `inset-0` 相对那个节点解析。

修法是 `createPortal(…, document.body)`。但那只是**一个**浮层。
本工具把这条从「一处修复」升级成**一条常备契约**：

    契约：页面上任何 computed `position: fixed` 的元素，它到 <body> 之间的
          祖先链上不得存在任何非 `none` 的 transform。

为什么值得单独一个普查工具，而不是在某个 verifier 里加一条断言：

1. **触发路径太长**。单选框要 shift+click 多选才有；包围盒要编组才有；
   资产库要开模态框才有。一个只覆盖「打开全屏编辑器」状态的断言，
   盖不住其余八成路径。
2. **静默失败**。`fixed` 被收编时页面**不报错、元素照常渲染**、坐标只是悄悄不对。
   肉眼和普通断言都很难发现，只有普查能把「哪些浮层在错误的坐标系里」列全。
3. **回归成本不对称**。写一次，永久看门狗。

⚠️ **本工具必须报出每个状态扫到几个 `fixed` 元素**，不能只报违规数。
批 817 记过一次取证事故：工具静默降级（读到 SSR 骨架 / 没 hydrate），
输出「0 个违规」，看上去是干净，实际是根本没扫到东西 ——
**「零违规」和「扫了但没东西」长得一模一样**。所以每态都打印
`fixed 元素 N 个 / 违规 M 个`，并断言总扫描量不为 0。

用法：
    ~/.venvs/liblib-harness/bin/python scripts/jimeng_fixed_census.py
退出码 0 = 零违规；1 = 有收编点（打印全部细节）。
"""

import os
import sys

from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get("JIMENG_BASE_URL", "http://localhost:4317")
VIEWPORT = {"width": 1512, "height": 950}
HYDRATED = """() => { const el = document.getElementById('__next')
  || document.body.firstElementChild || document.body;
  return Object.keys(el).some(k => k.startsWith('__reactFiber$')); }"""

# 契约本体。逐个元素问两件事：你是 fixed 吗？你到 body 之间有人带 transform 吗？
SCAN = r"""() => {
  const out = [];
  const label = (e) => {
    const t = e.getAttribute('data-testid');
    if (t) return `[${t}]`;
    const a = e.getAttribute('aria-label');
    if (a) return `«${a}»`;
    const d = e.getAttribute('data-group-frame');
    if (d) return `<group-frame ${d}>`;
    const cls = (e.className || '').toString().trim().split(/\s+/).slice(0, 2).join('.');
    return e.tagName.toLowerCase() + (cls ? '.' + cls : '');
  };
  for (const el of document.querySelectorAll('*')) {
    const cs = getComputedStyle(el);
    if (cs.position !== 'fixed') continue;
    const chain = [];
    let p = el.parentElement;
    while (p && p !== document.documentElement) {
      const t = getComputedStyle(p).transform;
      if (t && t !== 'none') {
        chain.push({
          el: p.tagName.toLowerCase() + '.' + (p.className || '').toString().trim().split(/\s+/)[0],
          transform: t.slice(0, 40),
        });
      }
      p = p.parentElement;
    }
    const r = el.getBoundingClientRect();
    out.push({
      el: label(el),
      parent: el.parentElement ? el.parentElement.tagName : null,
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      captured: chain,
    });
  }
  return out;
}"""


def main() -> int:
    total_fixed = 0
    violations: list[tuple[str, dict]] = []
    rows: list[tuple[str, int, int, str]] = []

    def scan(pg, state: str) -> None:
        nonlocal total_fixed
        found = pg.evaluate(SCAN)
        bad = [f for f in found if f["captured"]]
        total_fixed += len(found)
        for f in bad:
            violations.append((state, f))
        note = ""
        if not found:
            # 零 fixed 可能是「这态真的没有浮层」，也可能是「浮层没被触发出来」。
            # 分不清就写明，让读数的人自己判断，而不是当成一条干净的结论。
            note = "⚠ 本态无 fixed 元素 —— 触发可能没生效，别当成结论"
        rows.append((state, len(found), len(bad), note))
        print(f"  {state:<22} fixed {len(found):>2} 个 / 被收编 {len(bad)} 个 {note}")
        for f in bad:
            print(f"      ✗ {f['el']}  rect={f['rect']}  parent={f['parent']}")
            for c in f["captured"]:
                print(f"          ↑ {c['el']}  transform: {c['transform']}")

    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        pg = b.new_context(viewport=VIEWPORT, locale="zh-CN").new_page()
        try:
            pg.goto(f"{BASE_URL}/jimeng/canvas/demo", wait_until="domcontentloaded")
            pg.wait_for_selector('[data-testid="canvas-fixed-toolbar"]', timeout=60000)
            for _ in range(12):
                if pg.evaluate(HYDRATED):
                    break
                pg.wait_for_timeout(1000)
            else:
                print("复刻未 hydrate —— 读到 SSR 骨架，普查无意义，直接退出")
                return 1
            for _ in range(8):
                pg.keyboard.press("Meta+1")
                pg.wait_for_timeout(400)
                if pg.locator('[data-testid="canvas-zoom-percent"]').first.inner_text().strip() == "100%":
                    break

            print("— 逐态普查（1512×950，缩放已归 100%）—")
            scan(pg, "base")

            # 两个节点：文本 + 时间线。编组/多选都需要至少两个。
            pg.get_by_label("文本", exact=True).first.click()
            pg.wait_for_timeout(900)
            pg.get_by_label("时间线", exact=True).first.click()
            pg.wait_for_selector('[data-testid="timeline-shell"]', timeout=30000)
            pg.wait_for_timeout(1200)
            scan(pg, "two-nodes")

            tl = pg.locator('[data-testid="timeline-shell"]').first
            tl.click()
            pg.wait_for_timeout(700)
            scan(pg, "node-selected")

            # shift+click 第二个 → 包围盒 + 多选工具条
            # ⚠️ 两个坑：
            #  1. 必须点**两个不同**的节点。先 plain 点再 shift 点同一个，等于
            #     在切换选中态，不会进多选。
            #  2. 关掉工具条里的下拉**不能按 Escape** —— JimengFlow 的全局
            #     Escape 监听会顺手把选中态也清掉，多选工具条整个消失。
            #  3. 批 54 记过 shift+click 有已知 flake ⇒ 压到真实信号上重试，
            #     不靠固定 sleep。
            def enter_multiselect() -> bool:
                ns = pg.locator('.react-flow__node')
                for _ in range(4):
                    ns.nth(0).click()
                    pg.wait_for_timeout(500)
                    ns.nth(1).click(modifiers=["Shift"])
                    try:
                        pg.wait_for_selector('[data-testid="jimeng-multi-toolbar"]', timeout=6000)
                        return True
                    except Exception:
                        pg.keyboard.press("Escape")
                        pg.wait_for_timeout(400)
                return False

            if not enter_multiselect():
                print("多选态触发不出来（shift+click flake）—— 后续多选/编组态无法普查，"
                      "本次结果不完整")
                print(f"\n合计扫到 fixed 元素 {total_fixed} 个（覆盖不全）。")
                return 1
            pg.wait_for_timeout(800)
            scan(pg, "multi-select")

            # 多选工具条的下拉（浮层套浮层）
            pg.locator('[data-testid="multi-layout"]').click()
            pg.wait_for_timeout(700)
            scan(pg, "multi-layout-menu")
            # 收下拉：先试 `multi-layout` 自己再点一次（切换收起，不动选中态）。
            # Escape 也能收，但 JimengFlow 的全局 Escape 会**顺手清掉选中态**，
            # 多选工具条整个消失，后面编组就没得点了。
            # ⚠️ 别改成「点工具条空白处收起」：工具条是自适应宽度，点它自己盒子
            #    以外的坐标会落到 .react-flow__pane 上，Playwright 报
            #    `intercepts pointer events` —— 那是探针打错地方，不是产品缺陷。
            pg.locator('[data-testid="multi-layout"]').click()
            pg.wait_for_timeout(600)
            if pg.locator('[data-testid="multi-layout-menu"]').count() > 0:
                pg.keyboard.press("Escape")
                pg.wait_for_timeout(500)

            # 编组 → 出现 group frame。多选若已丢失就重新进，且**必须验回来**：
            # 上一版 enter_multiselect() 的返回值被丢掉了，失败后紧接着点
            # multi-group，表现为一条 30s 的 locator 超时，看不出真正原因是
            # 上一步没进多选。
            if pg.locator('[data-testid="multi-group"]').count() == 0:
                for _ in range(4):
                    if enter_multiselect() and pg.locator(
                            '[data-testid="multi-group"]').count() > 0:
                        break
                pg.wait_for_timeout(600)
            if pg.locator('[data-testid="multi-group"]').count() == 0:
                print("编组态触发不出来 —— group 态无法普查，本次结果不完整")
                print(f"\n合计扫到 fixed 元素 {total_fixed} 个（覆盖不全）。")
                return 1
            pg.locator('[data-testid="multi-group"]').click()
            pg.wait_for_selector('[data-group-frame]', timeout=15000)
            pg.wait_for_timeout(900)
            scan(pg, "group")

            # 节点右键菜单
            tl.click(button="right")
            pg.wait_for_timeout(800)
            scan(pg, "node-ctx-menu")
            pg.keyboard.press("Escape")
            pg.wait_for_timeout(500)

            # 空白处右键（画布级菜单）
            pg.mouse.click(1400, 820)
            pg.wait_for_timeout(800)
            scan(pg, "pane-ctx-menu")
            pg.keyboard.press("Escape")
            pg.wait_for_timeout(500)

            # 资产库模态框
            pg.get_by_label("资产库", exact=True).first.click()
            pg.wait_for_timeout(1000)
            scan(pg, "assets-modal")
            pg.keyboard.press("Escape")
            pg.wait_for_timeout(600)

            # 全屏时间线编辑器（821 修好的那一处）
            pg.locator('[data-testid="timeline-fullscreen-trigger"]').first.click()
            pg.wait_for_selector('[data-testid="timeline-fullscreen-workspace"]', timeout=20000)
            pg.wait_for_timeout(900)
            scan(pg, "timeline-fullscreen")
            pg.keyboard.press("Escape")
            pg.wait_for_timeout(700)

            # ------------------------------------------------------------------
            # 第二段：顶栏 / AI 族的浮层
            #
            # 822 只覆盖了画布内的 9 个态，顶栏这一族一个都没扫到 ——
            # 而它们恰恰是最像 `fixed` 的一批（模态框、下拉、面板）。
            #
            # 到达信号用**「冒出了新的 testid」**而不是逐个硬编码选择器：
            #  1. 硬编码十几个 testid，改一次名就得同步改这里，漏一个就静默少扫一态；
            #  2. 更要紧的是，用「fixed 元素数变多」当信号是**错的** ——
            #     一个合法的 `absolute` 浮层不会让 fixed 计数增加，
            #     那样会把「浮层正常打开了」误判成「没打开」。
            # 冒新 testid 只证明「确实有东西打开了」，与它是不是 fixed 无关。
            # ------------------------------------------------------------------
            print("\n— 第二段：顶栏 / AI 族浮层 —")

            def signature() -> set:
                """「页面上有哪些可被自动化指认的东西」的指纹。

                ⚠️ 第一版只收 `data-testid`，结果 generation-history 与
                shortcuts-panel 两态死活到不了 —— 查下去发现这两块浮层
                **只有 `role="dialog"` + `aria-label`，没有 testid**。
                也就是说：信号依赖了它自己要审计的那个东西，一旦某块浮层
                缺锚点，普查就「看不见它打开」，于是把「摸不到」报成
                「没发现问题」—— 而这两者在报告里长得一模一样。

                所以指纹收两类：testid，以及浮层语义（role ∈ dialog/menu/
                listbox，带 aria-label 就一并带上）。这样**即使将来又出现
                缺锚点的浮层**，普查仍能确认它确实被打开过。"""
                return set(pg.evaluate("""() => {
                  const out = new Set();
                  for (const e of document.querySelectorAll('*')) {
                    const t = e.getAttribute('data-testid');
                    if (t) { out.add('#' + t); continue; }
                    const r = e.getAttribute('role');
                    if (r === 'dialog' || r === 'menu' || r === 'listbox') {
                      const a = e.getAttribute('aria-label');
                      out.add('@' + r + (a ? ':' + a : ''));
                    }
                  }
                  return [...out]; }"""))

            def open_and_scan(state: str, trigger) -> None:
                before = signature()
                trigger()
                fresh: set = set()
                for _ in range(20):          # 最多等 ~4s
                    pg.wait_for_timeout(200)
                    fresh = signature() - before
                    if fresh:
                        break
                if not fresh:
                    print(f"  {state:<22} ⚠ 没冒出任何新锚点 —— 触发可能没生效，"
                          f"本态**未普查**，别当成干净")
                    rows.append((state, -1, -1, "⚠ 未到达"))
                    return
                pg.wait_for_timeout(600)    # 让浮层把布局稳定下来再量
                scan(pg, state)
                show = ", ".join(sorted(fresh)[:3])
                print(f"      ↳ 到达信号：{show}"
                      + (f" 等 {len(fresh)} 个" if len(fresh) > 3 else ""))

            def close_top() -> None:
                pg.keyboard.press("Escape")
                pg.wait_for_timeout(600)

            open_and_scan("node-summary",
                          lambda: pg.locator(
                              '[data-testid="canvas-node-summary-trigger"]').click())
            close_top()
            open_and_scan("search-panel",
                          lambda: pg.locator(
                              '[data-testid="canvas-panel-launcher"]').click())
            close_top()
            open_and_scan("generation-history",
                          lambda: pg.locator(
                              '[data-testid="canvas-history-launcher"]').click())
            close_top()
            open_and_scan("share-panel",
                          lambda: pg.locator(
                              '[data-testid="canvas-share-trigger"]').click())
            close_top()
            open_and_scan("more-menu",
                          lambda: pg.locator(
                              '[data-testid="canvas-more-trigger"]').click())
            close_top()
            open_and_scan("ai-drawer",
                          lambda: pg.locator(
                              '[data-testid="ai-trigger-pill"]').click())
            close_top()

            # 用户菜单 → 它的三项各自开一个浮层（帮助中心 / 快捷键 / 水印）
            def from_user_menu(item: str):
                def go() -> None:
                    pg.locator('[data-testid="canvas-user-menu-trigger"]').click()
                    pg.wait_for_timeout(600)
                    pg.locator(f'[data-testid="account-menu-item-{item}"]').click()
                return go

            open_and_scan("help-center", from_user_menu("帮助中心"))
            close_top()
            open_and_scan("shortcuts-panel", from_user_menu("快捷键"))
            close_top()
            open_and_scan("watermark-dialog", from_user_menu("AI生成水印设置"))
            close_top()
        finally:
            b.close()

    print()
    print(f"合计扫到 fixed 元素 {total_fixed} 个。")
    unreached = [s for s, n, _, _ in rows if n < 0]
    if total_fixed == 0:
        # 绝不能把「一个都没扫到」当成「零违规」——那是 817 那次事故的形状。
        print("一个 fixed 元素都没扫到 ⇒ 工具本身降级了，不构成任何结论。")
        return 1
    if unreached:
        # 覆盖不全的普查**不能**报 PASS。没扫到的那几态里完全可能有收编点，
        # 而「没发现」和「不存在」在输出上长得一样。
        print(f"覆盖不全 —— 下列状态没到达，未被普查：{', '.join(unreached)}")
        print("（没扫到 ≠ 不存在；这些态必须先能打开，结论才成立）")
        return 1
    if violations:
        print(f"FAIL —— {len(violations)} 处 fixed 被 transform 祖先收编：")
        for state, f in violations:
            print(f"  [{state}] {f['el']} rect={f['rect']}")
            for c in f["captured"]:
                print(f"      ↑ {c['el']}  transform: {c['transform']}")
        return 1
    print("PASS —— 所有态零收编：每个 fixed 元素的祖先链上都没有 transform。")
    return 0


if __name__ == "__main__":
    sys.exit(main())

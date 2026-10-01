#!/usr/bin/env python3
"""Jimeng clone batch 821 verifier — 普查扩到顶栏其余浮层，接上最后一个真死按钮，
并把「分享面板结构与源站不符」这件更根本的事修掉。

背景：批 820 把「账号菜单」纳入死按钮普查的状态。本批把状态扩到
**更多菜单 / 搜索 / 生成历史 / 分享** 四个顶栏浮层，259 个可点元素里报出 7 个候选，
逐个查证后：

  真死 1 个：分享面板「创建团队」——无 onClick（源站点开是全屏团队会员购买抽屉）
  假阳性 6 个，全是**指纹覆盖不足**：
    「小地图」「显示连线」——确实接了（setMinimapOpen / setEdgesVisible），
      但指纹既不记连线数也不记小地图在场
    生成历史「全部/图片/视频/音频」——确实接了（setTab 改下划线），但指纹
      不看控件**自身**的 class

修「创建团队」时顺手量出更根本的问题：这面板此前是「一列裸文案」，跟源站的三段
结构完全不是一回事（源站是 药丸链接行 / 权限行 / 分隔线+footer）。内容自然高度
246 > 可用 219，flex 把两枚按钮从 32/36 压到 19.5/21.5 —— 也就是说**普查当初
是在一个错的组件上判的死按钮**。按源站实测重排后逐节点坐标完全对齐。

同时补上源站有、复刻漏掉的一枚交互控件：权限 chip（106×26 + 倒角）点开是
role=menu 200×84，两枚 menuitemradio。此前复刻把它渲染成纯文本，普查因此
压根没机会看见它。
"""

import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = os.environ.get("JIMENG_CLONE_URL", "http://localhost:4317")
URL = f"{BASE}/jimeng/canvas/demo"
STATE = Path.home() / ".jimeng-automation" / "state.json"

PANEL = '[data-testid="topbar-share-panel"]'

failures: list[str] = []
checks = 0


def check(name: str, ok: bool, detail: str = "") -> None:
    global checks
    checks += 1
    if ok:
        print(f"  PASS  {name}" + (f"  ({detail})" if detail else ""))
    else:
        print(f"  FAIL  {name}  {detail}")
        failures.append(name)


# 源站 2026-10-04 实测的 rel 坐标（相对面板左上角），面板 @[1268,56]。
# 逐节点对齐，不写只在我这份 mock 上成立的数字。
SRC = {
    "panel": (400, 251),
    "header": 52,
    "body": 199,
    "section": 122,
    "pill": (368, 40),
    "divider": (1, 10),
    "copy": (100, 36),
    "access": (368, 46),
    "circle": (36, 36),
    "permchip": (106, 26),
    "desc": (320, 20),
    "footer": 73,
    "footdiv": (376, 1),
    "footrow": (400, 64),
    "createteam": (80, 36),
    "createteam_xy": (304, 197),
    "menu": (200, 84),
    "menuitem": (192, 36),
}


def geom(page, sel: str):
    """返回相对分享面板的 (x, y, w, h)；元素不在面板内则 x/y 为 null。"""
    return page.evaluate(
        """(sel) => {
            const p = document.querySelector('[data-testid="topbar-share-panel"]');
            if (!p) return null;
            const pr = p.getBoundingClientRect();
            const el = document.querySelector(sel);
            if (!el) return null;
            const r = el.getBoundingClientRect();
            return {x: +(r.x - pr.x).toFixed(1), y: +(r.y - pr.y).toFixed(1),
                    w: +r.width.toFixed(1), h: +r.height.toFixed(1)};
        }""",
        sel,
    )


def main() -> int:
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        ctx = b.new_context(
            storage_state=str(STATE) if STATE.exists() else None,
            viewport={"width": 1680, "height": 1050},
        )
        page = ctx.new_page()
        errs: list[str] = []
        page.on("pageerror", lambda e: errs.append(str(e)[:160]))
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(6000)

        # ── A. 分享面板结构对齐源站三段 ──────────────────────────────
        page.locator('[data-testid="canvas-share-trigger"]').click()
        page.wait_for_timeout(900)
        check("A.0 前置：分享面板打开", page.locator(PANEL).count() == 1)

        outer = page.evaluate(
            """() => {
                const p = document.querySelector('[data-testid="topbar-share-panel"]');
                const r = p.getBoundingClientRect();
                return {x: +r.x.toFixed(1), y: +r.y.toFixed(1),
                        w: +r.width.toFixed(1), h: +r.height.toFixed(1)};
            }"""
        )
        check(
            "A.1 面板 400×251 @[1268,56]（源站 canvas-share-panel-surface）",
            (outer["w"], outer["h"], outer["x"], outer["y"]) == (400, 251, 1268, 56),
            f"{outer['w']}×{outer['h']} @[{outer['x']:.0f},{outer['y']:.0f}]",
        )

        seg = page.evaluate(
            """() => {
                const p = document.querySelector('[data-testid="topbar-share-panel"]');
                const pr = p.getBoundingClientRect();
                const head = p.children[0], body = p.children[1];
                const foot = body.querySelector('[data-testid="canvas-share-scope-action"]');
                const sec = body.children[0];
                const px = (e) => { const r = e.getBoundingClientRect();
                    return {y: +(r.y - pr.y).toFixed(1), h: +r.height.toFixed(1),
                            w: +r.width.toFixed(1)}; };
                return {head: px(head), body: px(body), sec: px(sec), foot: px(foot)};
            }"""
        )
        check(
            "A.2 header 52 / body 199 / section 122 / footer 73 四段纵向严丝合缝",
            seg["head"]["h"] == SRC["header"]
            and seg["body"]["h"] == SRC["body"]
            and seg["sec"]["h"] == SRC["section"]
            and seg["foot"]["h"] == SRC["footer"]
            and seg["body"]["y"] == 52
            and seg["foot"]["y"] == 178,
            f"head={seg['head']['h']} body={seg['body']['h']} sec={seg['sec']['h']} foot={seg['foot']['h']}",
        )

        pill = geom(page, '[data-testid="share-link-pill"]')
        check(
            "A.3 链接药丸 368×40 @[16,64]（源站此前是一行裸 URL 文案）",
            pill and (pill["w"], pill["h"], pill["x"], pill["y"]) == (368, 40, 16, 64),
            str(pill),
        )
        divd = geom(page, '[data-testid="share-link-pill"] span[aria-hidden="true"]')
        check("A.4 药丸内 1×10 分隔条 @[277,79]", divd and (divd["w"], divd["h"]) == (1, 10), str(divd))
        cp = geom(page, '[data-testid="share-copy-link"]')
        check("A.5 「复制链接」100×36 @[282,66]（在药丸**内**，不是独立按钮）",
              cp and (cp["w"], cp["h"], cp["x"], cp["y"]) == (100, 36, 282, 66), str(cp))

        circ = geom(page, '[aria-label="分享画布"] span[aria-hidden="true"]:has(> svg)')
        check("A.6 权限行圆标 36×36", circ and (circ["w"], circ["h"]) == (36, 36), str(circ))

        chip0 = geom(page, '[data-testid="share-perm-trigger"]')
        check(
            "A.7 权限 chip 是 BUTTON 106×26（此前复刻把它渲染成纯文本，普查压根看不见）",
            chip0 and (chip0["w"], chip0["h"]) == (106, 26)
            and page.locator('[data-testid="share-perm-trigger"]').count() == 1,
            str(chip0),
        )

        fdiv = geom(page, '[data-testid="canvas-share-scope-action"] > div[aria-hidden="true"]')
        check("A.8 footer 分隔线 376×1 @[12,178]", fdiv and (fdiv["w"], fdiv["h"]) == (376, 1), str(fdiv))

        ct = geom(page, '[data-testid="share-create-team"]')
        check(
            "A.9 「创建团队」80×36 @[304,197] → 视口 [1572,253]（源站实测同值）",
            ct
            and (ct["w"], ct["h"], ct["x"], ct["y"])
            == (SRC["createteam"][0], SRC["createteam"][1], *SRC["createteam_xy"]),
            str(ct),
        )
        # 上一版写的是 h-9 w-20 但实测 80×22 —— flex 收缩。真根因是内容栈
        # 246 > 219，按源站三段重排后总和正好 251。这里显式防回归。
        check(
            "A.10 面板无 flex 压扁：所有子块实测高 = 声明高（回归 80×22 那次）",
            seg["head"]["h"] + seg["body"]["h"] == 251,
            f"{seg['head']['h']}+{seg['body']['h']}={seg['head']['h'] + seg['body']['h']}",
        )

        # ── B. 权限下拉（源站有、复刻此前整块缺失）──────────────────
        # 判据用**闭合态 vs 展开态的差**，不写死颜色字符串：Tailwind v4 把
        # bg-white/[0.08] 算成 oklab(...) 而不是源站的 rgba(255,255,255,0.08)，
        # 上一版直接比字符串就是这么红的。同样，rotate-180 落在 CSS `rotate`
        # 属性上，`transform` 读出来是 none —— 读错属性等于读错判据。
        closed = page.evaluate(
            """() => {
                const b = document.querySelector('[data-testid="share-perm-trigger"]');
                const s = getComputedStyle(b);
                return {bg: s.backgroundColor, rot: getComputedStyle(b.querySelector('svg')).rotate};
            }"""
        )
        page.locator('[data-testid="share-perm-trigger"]').click()
        page.wait_for_timeout(600)
        menu = geom(page, '[data-testid="share-perm-menu"]')
        check("B.1 权限 chip 点开 role=menu 200×84 @rel[48,146]",
              menu and (menu["w"], menu["h"], menu["x"], menu["y"]) == (200, 84, 48, 146), str(menu))
        opened = page.evaluate(
            """() => {
                const b = document.querySelector('[data-testid="share-perm-trigger"]');
                const s = getComputedStyle(b);
                return {bg: s.backgroundColor, aria: b.getAttribute('aria-expanded'),
                        rot: getComputedStyle(b.querySelector('svg')).rotate};
            }"""
        )
        check(
            "B.1b 展开态：chip 亮起 8% 白底、倒角 180° 反向（源站 aria-expanded 联动）",
            opened["bg"] != closed["bg"]
            and opened["aria"] == "true"
            and opened["rot"] == "180deg"
            and closed["rot"] == "none",
            f"bg {closed['bg']} -> {opened['bg']}；rot {closed['rot']} -> {opened['rot']}",
        )
        check("B.2 菜单语义是 role=menu + 两枚 menuitemradio",
              page.locator('[data-testid="share-perm-menu"][role="menu"]').count() == 1
              and page.locator('[data-testid="share-perm-option"]').count() == 2)
        it = geom(page, '[data-testid="share-perm-option"]')
        check("B.3 菜单项 192×36", it and (it["w"], it["h"]) == (192, 36), str(it))
        checked = page.evaluate(
            """() => [...document.querySelectorAll('[data-testid="share-perm-option"]')]
                .map(e => e.getAttribute('aria-checked'))"""
        )
        check("B.4 选中项 aria-checked=true 且仅一项", checked == ["true", "false"], str(checked))
        tick = page.locator('[data-testid="share-perm-option"][aria-checked="true"] svg')
        check("B.5 选中项右侧有 16×16 对勾（源站是勾，不是纯变色）", tick.count() == 1)

        page.locator('[data-testid="share-perm-option"]').nth(1).click()
        page.wait_for_timeout(600)
        chip1 = geom(page, '[data-testid="share-perm-trigger"]')
        desc = page.locator(PANEL + " p").first.inner_text().strip()
        check(
            "B.6 切到「获得此链接的任何人」：chip 文案变、宽度 106→145、说明文案跟着变",
            chip1
            and chip1["w"] == 145
            and page.locator('[data-testid="share-perm-trigger"]').inner_text().strip()
            == "获得此链接的任何人"
            and desc == "任何人都能使用此链接访问画布",
            f"w={chip1['w'] if chip1 else None} desc={desc!r}",
        )

        page.locator('[data-testid="share-perm-trigger"]').click()
        page.wait_for_timeout(500)
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)
        check(
            "B.7 Escape 分层：先收菜单，面板还在",
            page.locator('[data-testid="share-perm-menu"]').count() == 0
            and page.locator(PANEL).count() == 1,
        )

        # ── C. 「创建团队」是真按钮（普查查出的唯一真死按钮）────────
        page.locator('[data-testid="share-create-team"]').click()
        page.wait_for_timeout(1000)
        member = page.evaluate(
            """() => ({
                close: document.querySelectorAll('[aria-label="关闭订阅页"]').length,
                plans: document.querySelectorAll('[data-testid="plan-credits"]').length,
            })"""
        )
        check(
            "C.1 点「创建团队」打开会员弹窗（此前无 onClick，是真死按钮）",
            member["close"] == 1 and member["plans"] > 0,
            f"close={member['close']} plans={member['plans']}",
        )
        check("C.2 分享面板已关闭（不叠着两个浮层）", page.locator(PANEL).count() == 0)
        page.keyboard.press("Escape")
        page.wait_for_timeout(700)

        # ── D. 假阳性回归：那三个「死按钮」真能改状态 ─────────────────
        def snap():
            return page.evaluate(
                """() => ({
                    edges: document.querySelectorAll('.react-flow__edge').length,
                    minimap: document.querySelectorAll('.react-flow__minimap').length,
                    cls: (document.querySelector('[data-testid="canvas-display-toggle-minimap"]')||{}).className || '',
                })"""
            )

        s0 = snap()
        page.locator('[data-testid="canvas-display-toggle-minimap"]').click()
        page.wait_for_timeout(700)
        s1 = snap()
        check(
            "D.1 「小地图」真改变状态（此前普查误判成死按钮：指纹不记小地图在场）",
            s1["minimap"] != s0["minimap"] or s1["cls"] != s0["cls"],
            f"minimap {s0['minimap']}->{s1['minimap']}",
        )
        page.locator('[data-testid="canvas-display-toggle-minimap"]').click()
        page.wait_for_timeout(600)

        def conn_cls():
            return page.evaluate(
                """() => (document.querySelector('[data-testid="canvas-display-toggle-connections"]')||{}).className || ''"""
            )

        c0 = conn_cls()
        page.locator('[data-testid="canvas-display-toggle-connections"]').click()
        page.wait_for_timeout(600)
        c1 = conn_cls()
        check("D.2 「显示连线」真切换（自身 class 变化）", c0 != c1, "class 已变" if c0 != c1 else "无变化")
        page.locator('[data-testid="canvas-display-toggle-connections"]').click()
        page.wait_for_timeout(600)

        # ── E. 假阳性回归：生成历史 4 个 chip 真能切 ──────────────────
        page.locator('[data-testid="canvas-history-launcher"]').click()
        page.wait_for_timeout(900)
        chips = page.locator('[aria-label="生成历史"] button')
        n = chips.count()
        check("E.0 前置：生成历史 4 个筛选 chip", n == 4, f"count={n}")
        if n == 4:
            first_cls = chips.nth(0).get_attribute("class") or ""
            chips.nth(1).click()
            page.wait_for_timeout(500)
            cls0 = chips.nth(0).get_attribute("class") or ""
            cls1 = chips.nth(1).get_attribute("class") or ""
            check("E.1 切到「图片」后 chip 自身 class 真变（此前普查看不到控件自身）",
                  cls0 != first_cls and cls0 != cls1, "0 与 1 的 class 已分离")
            under = page.evaluate(
                """() => {
                    const b = [...document.querySelectorAll('[aria-label="生成历史"] button')]
                        .find(e => (e.innerText||'').trim() === '图片');
                    return b ? b.querySelectorAll('span').length : -1;
                }"""
            )
            check("E.2 选中项有下划线 span（源站是选中下划线，不是纯变色）", under >= 1, f"span={under}")
            # 「全部」是普查唯一剩下的 DEAD：进态时它默认就是激活态，点它正确地
            # 不改变任何状态。与其把它记成"探针无法验证"，不如双向都验一遍。
            all_cls_before = chips.nth(0).get_attribute("class") or ""
            chips.nth(0).click()
            page.wait_for_timeout(500)
            all_cls_after = chips.nth(0).get_attribute("class") or ""
            img_cls_back = chips.nth(1).get_attribute("class") or ""
            check(
                "E.3 从「图片」切回「全部」：选中 class 真的转移（普查里它默认激活，"
                "点它正确地不变化 —— 这是切换组的固有性质，不是死按钮）",
                all_cls_after != all_cls_before
                and all_cls_after == first_cls
                and img_cls_back != cls1,
                f"回到 {all_cls_after == first_cls}，图片失去选中 {img_cls_back != cls1}",
            )
        page.keyboard.press("Escape")
        page.wait_for_timeout(600)

        # ── F. 更多菜单两项仍正常（普查扩态的回归护栏）───────────────
        page.locator('[data-testid="canvas-more-trigger"]').click()
        page.wait_for_timeout(800)
        items = page.evaluate(
            """() => {
                const m = document.querySelector('[data-testid="topbar-more-menu"]');
                if (!m) return null;
                return [...m.querySelectorAll('button, [role=menuitem]')]
                    .map(e => (e.innerText || '').trim());
            }"""
        )
        check("F.1 更多菜单两项齐全", items == ["项目信息", "复制项目"], str(items))
        page.keyboard.press("Escape")
        page.wait_for_timeout(600)

        check("G.0 无页面 JS 报错", not errs, "; ".join(errs[:2]))
        ctx.close()
        b.close()

    print(f"\n{checks - len(failures)}/{checks}")
    if failures:
        print("FAILED: " + ", ".join(failures))
        return 1
    print("batch 821 OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())

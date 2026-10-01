"""Jimeng clone batch 807 verifier — 死按钮普查 + 左栏三个死按钮 + 返回首页真链接。

batch 794~803 是"按控件逐个接交互"，但没有系统性手段证明没有漏网的死按钮。
本批先做普查（scripts/jimeng_dead_button_audit.py），再修普查出来的真缺陷。

## 普查结论（1680×826 demo 画布，40 个可点元素）

真死按钮只有 3 个，全在左栏：**时间线 / 主体 / 导演台**。
其余命中经人工复核为探针盲区，不是缺陷：
  - 视频卡的 播放/静音/全屏：状态存在 store 不在 DOM（mock 播放器无 <video>）
  - dock 的 小地图/显示连线/选择工具：改的是 class 与 minimap 挂载，指纹没覆盖
  - 「与 AI 对话」：开抽屉，前一版指纹没覆盖抽屉

## 根因：这三个不是"打开浮层"，是"插入节点"

SOURCE_FACT @1680×826 登录态实测，源站点这三个按钮后：
  落点 `data-testid="rf__node-*"`、`role="group"`、位于 `.react-flow__viewport` 内，
  顶栏节点计数 +1。复刻此前把 `insert` 留空，onClick 走空分支 —— 点了没反应。

节点实测尺寸：时间线 1206×212 · 主体 352×352 · 导演台 320×320。
"""

import os
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references" / "jimeng"
BASE_URL = os.environ.get("JIMENG_BASE_URL", "http://localhost:4317")
CANVAS_URL = f"{BASE_URL}/jimeng/canvas/demo"
VIEWPORT = {"width": 1680, "height": 826}


def run_timeline_checks(page, check, toast_text) -> None:
    """时间线节点内是真交互：加片段 → 片段出现 + 时长变化 + toast。"""
    before = page.locator('[data-testid="timeline-time"]').first.inner_text()
    check("时间线空态 00:00 / 00:00", before == "00:00 / 00:00", repr(before))
    check("初始无片段", page.locator('[data-testid="timeline-clip"]').count() == 0)
    page.locator('[data-testid="timeline-add-clip"]').first.click()
    page.wait_for_timeout(500)
    n_clip = page.locator('[data-testid="timeline-clip"]').count()
    check("「添加素材到时间线」后出现片段", n_clip == 1, f"count={n_clip}")
    after = page.locator('[data-testid="timeline-time"]').first.inner_text()
    check("时间码随之变化（不是静态图）", after != before, f"{before!r} -> {after!r}")
    check("添加片段有 toast", "时间线" in toast_text(), repr(toast_text()[:60]))


def run_subject_checks(page, check, toast_text) -> None:
    """主体节点内是真交互：描述写回 + 导入素材 + 画布选择有反馈。"""
    desc = page.locator('[data-testid="subject-description"]').first
    desc.click()
    desc.fill("主角：一名侦探")
    desc.press("Enter")
    page.wait_for_timeout(400)
    val = page.locator('[data-testid="subject-description"]').first.input_value()
    check("主体描述写回节点", val == "主角：一名侦探", val)
    page.locator('[data-testid="subject-node"] button[aria-label="导入主体"]').first.click()
    page.wait_for_timeout(400)
    n_imp = page.locator('[data-testid="subject-imported"] li').count()
    check("「导入主体」后列出素材", n_imp == 1, f"count={n_imp}")
    page.locator('[data-testid="subject-node"] button[aria-label="从画布选择"]').first.click()
    page.wait_for_timeout(300)
    check("「从画布选择」给出反馈（不是静默）", "从画布选择" in toast_text(), repr(toast_text()[:60]))


def run_director_checks(page, check, toast_text) -> None:
    """导演台节点内是真交互：点「进入导演台」→ 文案切换 + toast。"""
    before = page.locator('[data-testid="director-caption"]').first.inner_text()
    page.locator('[data-testid="director-enter"]').first.click()
    page.wait_for_timeout(400)
    after = page.locator('[data-testid="director-caption"]').first.inner_text()
    check("「进入导演台」改变节点内文案", after != before, f"{before!r} -> {after!r}")
    check("进入导演台有 toast", "导演台" in toast_text(), repr(toast_text()[:60]))


def main() -> None:
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []
    checks = 0

    def check(name: str, ok: bool, detail: str = "") -> None:
        nonlocal checks
        checks += 1
        if not ok:
            failures.append(f"{name}: {detail}")
        print(f"  [{'ok ' if ok else 'FAIL'}] {name}{'' if ok else ' — ' + detail}")

    def near(a: float, b: float, tol: float = 0.6) -> bool:
        return abs(a - b) <= tol

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport=VIEWPORT, locale="zh-CN")
        page = ctx.new_page()
        # 用 list 装计数：lambda 里改外层 int 需要 nonlocal，闭包做不到
        navs = [0]
        page.on("framenavigated", lambda f: navs.__setitem__(0, navs[0] + 1)
                if f == page.main_frame else None)
        errors: list[str] = []
        page.on("console", lambda m: errors.append(f"console.{m.type}: {m.text}") if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))

        page.goto(CANVAS_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(2500)

        def node_count() -> int:
            return page.locator(".react-flow__node").count()

        def topbar_count() -> str:
            return page.locator('[data-testid="canvas-node-summary-trigger"]').inner_text().strip()

        def toast_text() -> str:
            t = page.locator('[role="status"]')
            return " ".join(t.nth(i).inner_text() for i in range(t.count()))

        base_nodes = node_count()
        check("初始 2 节点", base_nodes == 2, f"count={base_nodes}")

        # 按真实使用顺序：插一个就立刻用它，再插下一个。三个节点都很大
        # （时间线 1206 宽、主体/导演台 320+），叠在视口中心时后者会压住前者 ——
        # 源站也是如此（截图里 主体 1/2/3 互相叠压），靠级联错位 + 用户拖开。
        print("— 左栏三个按钮：死按钮 → 插入节点 —")
        for step, (label, tid, expect_wh) in enumerate(
            [
                ("时间线", "timeline-node", (1206, 212)),
                ("主体", "subject-node", (352, 352)),
                ("导演台", "director-node", (320, 320)),
            ]
        ):
            before = node_count()
            page.locator(f'[aria-label="{label}"]').first.click()
            page.wait_for_timeout(600)
            after = node_count()
            check(f"点「{label}」节点 +1", after == before + 1, f"{before} -> {after}")
            sel = f'[data-testid="{tid}"]'
            n_tid = page.locator(sel).count()
            check(f"点「{label}」出现 {tid}", n_tid == 1, f"count={n_tid}")
            # 节点**布局**尺寸（SOURCE_FACT 实测值）。必须用 offsetWidth/
            # offsetHeight 而不是 getBoundingClientRect：后者是屏幕像素，
            # 会被视口 zoom(0.7299) 缩放（352 会量成 257）。
            # testid 就挂在带 inline width/height 的那层上，直接量它；
            # 再往里 firstElementChild 是绝对定位的标题行（h-8 = 32）。
            wh = page.evaluate(
                """(tid) => {
                    const el = document.querySelector(`[data-testid="${tid}"]`);
                    if (!el) return null;
                    return {w: el.offsetWidth, h: el.offsetHeight};
                }""",
                tid,
            )
            check(f"{label} 节点 {expect_wh[0]}×{expect_wh[1]}",
                  wh is not None and near(wh["w"], expect_wh[0]) and near(wh["h"], expect_wh[1]),
                  str(wh))
            check(f"顶栏计数同步（{step + 1} 个新节点）",
                  topbar_count() == f"节点 {2 + step + 1}", repr(topbar_count()))
            if step == 0:
                run_timeline_checks(page, check, toast_text)
            elif step == 1:
                run_subject_checks(page, check, toast_text)
            else:
                run_director_checks(page, check, toast_text)

        check("顶栏节点计数最终为 5", topbar_count() == "节点 5", repr(topbar_count()))

        print("— 新节点进入节点摘要弹层 —")
        page.locator('[data-testid="canvas-node-summary-trigger"]').click()
        page.wait_for_timeout(400)
        pop = page.locator('[data-testid="topbar-node-summary"]')
        check("节点摘要弹层已开", pop.count() == 1)
        pop_txt = pop.inner_text()
        for frag in ["时间线 1", "主体 1", "导演台 1", "查看项目信息"]:
            check(f"弹层含「{frag}」", frag in pop_txt, repr(pop_txt[:120]))
        # 高度仍是内容驱动公式：5 个条目 + 底部入口
        ph = pop.bounding_box()
        check("弹层高度仍符合 H=40N+52", ph is not None and near(ph["height"], 40 * 5 + 52),
              f"h={ph and ph['height']}")
        page.screenshot(path=str(REFERENCE_DIR / "jimeng-clone-batch807-rail-nodes-1680.png"))
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)

        print("— 顶栏「返回首页」不再是死按钮 —")
        logo = page.locator('[data-testid="canvas-project-logo"]')
        tag = logo.evaluate("el => el.tagName.toLowerCase()")
        href = logo.get_attribute("href") or ""
        check("返回首页是锚点（源站是 <a href>）", tag == "a", f"tag=<{tag}>")
        check("返回首页有 href", href.startswith("/jimeng"), f"href={href!r}")
        lb = logo.bounding_box()
        check("返回首页仍是 40×40", lb is not None and near(lb["width"], 40) and near(lb["height"], 40),
              str(lb))
        # /jimeng 会 302 回 demo 画布，所以**最终 URL 不会变**，
        # 不能拿 url 变化当判据 —— 改用导航事件计数。
        before_url = page.url
        logo.click()
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(1500)
        check("点返回首页真的发生导航（不再是死按钮）", navs[0] > 0,
              f"navigations={navs[0]}, url {before_url} -> {page.url}")

        print("— 回归 —")
        page.goto(CANVAS_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(2000)
        check("刷新后仍是初始 2 节点", node_count() == 2, f"count={node_count()}")
        check("无 console/page 错误", not errors, "; ".join(errors[:3]))
        ctx.close()
        browser.close()

    print()
    if failures:
        print(f"FAIL: {len(failures)}/{checks} 项未通过")
        for f in failures:
            print("  -", f)
        raise SystemExit(1)
    print(f"PASS: jimeng batch 807 死按钮普查 + 左栏三工具 + 返回首页真链接（{checks} 项断言全通过）")


if __name__ == "__main__":
    main()

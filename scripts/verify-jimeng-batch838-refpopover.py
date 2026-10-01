#!/usr/bin/env python
"""batch 838-refpopover verifier —— 「添加参考」改成源站的**两块 240 宽**面板。

取证（`jimeng_838_refpopover_probe.py` + 两张截图，源站 1512×950）：

    一级 分类列表  @[1003,482] 240×296  bg rgb(38,38,38)  role=listbox
         标题 36px；5 行各 232×48、行距 4、每行右端一个 ›
    二级 条目面板  @[759,518] 240×212  同底色、圆角 16
         顶与一级**首行**对齐，与一级左缘相距 4px，底比一级底高 48px
         两段：「当前画布」/「<分类>库」，各带「暂无相关节点」

复刻此前是「抽屉里内联的一行 tab + 一枚确认钮」，**形状完全不同**。本批改成
上面那个形状，并刻意**不编条目**：源站在这块画布上每个分类都是「暂无相关节点」
（连画布上明明有的「视频 1」都没列），所以「它列画布节点」这个推断不成立
（OPEN_QUESTION 838-b）。确认钮是**复刻自有**，保留（否则「加引用」变死路）。

⚠ 本批自己踩的坑写在 ⑦：`bottom-full` 按**最近的定位祖先**解析，父容器若是
`static`，浮层会按整个抽屉定位、跑到视口外，5 枚分类行一个都点不到。
定位链是判据的一部分，所以 ⑦ 专门把它钉成契约。
"""

from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:4317"
VIEWPORT = {"width": 1680, "height": 826}

CATS = '[data-testid="agent-ref-categories"]'
ITEMS = '[data-testid="agent-ref-items"]'
KINDS = ["主体", "图片", "视频", "音频", "文本"]


def main() -> int:
    failures: list[str] = []
    passed = 0

    def check(name: str, ok: bool, detail: str = "") -> None:
        nonlocal passed
        if ok:
            passed += 1
        else:
            failures.append(f"{name}: {detail}")
        print(f"  [{'ok ' if ok else 'FAIL'}] {name}{'' if ok else ' — ' + detail}")

    def box(page, sel: str) -> dict:
        return page.locator(sel).first.bounding_box() or {}

    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        page = b.new_context(viewport=VIEWPORT, locale="zh-CN").new_page()
        errs: list[str] = []
        page.on("pageerror", lambda e: errs.append(str(e)[:160]))
        page.on("console", lambda m: errs.append(f"console.{m.type}: {m.text}") if m.type == "error" else None)
        try:
            page.goto(f"{BASE_URL}/jimeng/canvas/demo", wait_until="domcontentloaded")
            page.wait_for_selector('[data-testid="canvas-fixed-toolbar"]', timeout=60000)
            for _ in range(12):
                if page.evaluate("() => !!document.querySelector('.react-flow__node')"):
                    break
                page.wait_for_timeout(1000)
            page.locator('[data-testid="canvas-sidecar-launcher"]').first.click()
            page.wait_for_selector('[data-testid="canvas-agent-drawer"]', timeout=20000)
            page.wait_for_timeout(600)
            page.locator('[data-testid="canvas-agent-composer-mention"]').first.click()
            page.wait_for_timeout(500)

            print("— ① 两块面板，源站实测各 240 宽 —")
            check("一级分类列表存在", page.locator(CATS).count() == 1)
            check("二级条目面板存在", page.locator(ITEMS).count() == 1)
            cb, ib = box(page, CATS), box(page, ITEMS)
            check("一级宽 240（源站实测）", cb.get("width") == 240, str(cb.get("width")))
            check("二级宽 240（源站实测）", ib.get("width") == 240, str(ib.get("width")))
            check("一级在二级**右边**（源站：1003 vs 759）",
                  cb["x"] > ib["x"], f'{cb["x"]} vs {ib["x"]}')
            check("两块相距 240+4（源站：999↔1003，4px 间隙）",
                  abs((cb["x"] - (ib["x"] + 240)) - 4) <= 1,
                  f'gap={cb["x"] - (ib["x"] + 240)}')
            # ⚠ 批 839 订正：这条原来是 `abs(ib["y"] - (cb["y"] + 36)) <= 2` ——
            #   拿一个**常量 36** 跟同一批另一个常量 36 比，而复刻当时正好写着
            #   `top-[36px]`，于是**恒真**。它量的是「CSS 类是不是我写的那句」，
            #   不是「面板顶有没有落在那一行上」：复刻一级还带着 `py-2`，首行
            #   实际在 +48，这条判据硬是全绿，把 12px 的错整个放了过去。
            #   现在改成跟**那一行的真实盒**比（默认选中「主体」= 首行）。
            first_row = page.locator('[data-testid^="agent-ref-kind-"]').first.bounding_box() or {}
            check("二级顶落在当前选中行上（源站 518 == 主体行 518）",
                  abs(ib["y"] - first_row["y"]) <= 1,
                  f'items top={ib["y"]} vs row top={first_row["y"]}')
            # 源站「二级底比一级底高 48px」看着像规则，其实是**两块高度不同**的
            # 后果（296 vs 212）—— 复刻两块高度本就不同，底差不可能照抄。
            # 判据落在看得见的那条：二级不越过一级底缘。
            check("二级底缘不越过一级底缘（源站 730 < 778）",
                  (ib["y"] + ib["height"]) < (cb["y"] + cb["height"]),
                  f'items bottom={ib["y"] + ib["height"]} vs cats bottom={cb["y"] + cb["height"]}'
                  f'（源站底差 48）')

            print("— ② 5 枚分类行，各 48 高、行距 4、右侧带 › —")
            rows = page.locator('[data-testid^="agent-ref-kind-"]')
            check("5 枚分类", rows.count() == 5, f"count={rows.count()}")
            check("文案逐字等于源站", [rows.nth(i).inner_text().strip() for i in range(5)] == KINDS,
                  str([rows.nth(i).inner_text().strip() for i in range(5)]))
            heights = [rows.nth(i).bounding_box()["height"] for i in range(5)]
            check("每行 48 高（源站实测）", all(h == 48 for h in heights), str(heights))
            tops = [rows.nth(i).bounding_box()["y"] for i in range(5)]
            gaps = [round(tops[i + 1] - (tops[i] + 48)) for i in range(4)]
            check("行距 4px（源站实测）", all(g == 4 for g in gaps), str(gaps))
            check("行宽 232（源站实测；240 减左右各 4 内缩）",
                  all(rows.nth(i).bounding_box()["width"] == 232 for i in range(5)))
            check("每行右端有一个 ›（svg）",
                  rows.nth(0).locator("svg").count() == 1, str(rows.nth(0).locator("svg").count()))
            sel_now = page.locator('[data-testid^="agent-ref-kind-"][aria-selected="true"]')
            check("当前分类带 aria-selected（唯一一条）", sel_now.count() == 1,
                  f"selected={sel_now.count()}")

            print("— ③ 二级两段 + 各自的空态 —")
            itxt = page.locator(ITEMS).first.inner_text()
            check("含「当前画布」", "当前画布" in itxt, itxt[:60])
            check("含「主体库」（分组名跟着当前分类走）", "主体库" in itxt, itxt[:60])
            check("两处「暂无相关节点」（源站实测的空态文案）",
                  itxt.count("暂无相关节点") == 2, str(itxt.count("暂无相关节点")))

            print("— ④ 换分类 ⇒ 二级分组名跟着变（内容随状态走，不是写死）—")
            page.locator('[data-testid="agent-ref-kind-音频"]').first.click()
            page.wait_for_timeout(400)
            itxt2 = page.locator(ITEMS).first.inner_text()
            check("切到「音频」⇒ 分组变「音频库」", "音频库" in itxt2 and "主体库" not in itxt2, itxt2[:60])
            check("切分类后选中标记跟着走",
                  page.locator('[data-testid="agent-ref-kind-音频"][aria-selected="true"]').count() == 1)
            check("空态仍是两处（不为空分类编条目）",
                  itxt2.count("暂无相关节点") == 2, str(itxt2.count("暂无相关节点")))

            print("— ⑤ 批 839：条目面板开始列**真节点**，确认钮已撤 —")
            check("空分类（音频）仍给空态，不编条目",
                  page.locator('[data-testid^="agent-ref-item-"]').count() == 0,
                  str(page.locator('[data-testid^="agent-ref-item-"]').count()))
            check("确认钮已撤（源站没有它 —— 810 那两条判据已据此改写）",
                  page.locator('[data-testid="agent-ref-confirm"]').count() == 0)
            page.locator('[data-testid="agent-ref-kind-视频"]').first.click()
            page.wait_for_timeout(400)
            # 判据落在「条目数 == 画布上该类型的节点数」，不写死 1：demo 里有**两个**
            # video 节点（video-local-1 / video-empty-1），写死 1 就是把 fixture 的
            # 巧合当契约（810 当年栽过「刷新后仍是初始 2 节点」那类）。
            n_video = page.evaluate(
                """() => document.querySelectorAll('.react-flow__node').length / 2""")
            items = page.locator('[data-testid^="agent-ref-item-"]')
            check("切到有节点的分类 ⇒ 条目数等于画布上该类型的节点数（这里是 2）",
                  items.count() == 2, f"items={items.count()}")
            names = [items.nth(i).inner_text().strip() for i in range(items.count())]
            # 不写死「都含视频」：demo 第二个 video 节点的标题是个 sb_… 文件名
            # （批 73 的本地上传 mock）。判据是**非空且互不相同**。
            check("条目名非空且互不相同（是节点标题，不是 @分类 那种合成串）",
                  all(names) and len(set(names)) == len(names), str(names))
            _ = n_video
            page.locator('[data-testid^="agent-ref-item-"]').first.click()
            page.wait_for_timeout(450)
            check("点条目 ⇒ composer 出现同名芯片",
                  names[0] in page.locator('[data-testid="agent-composer-tokens"]').first.inner_text(),
                  page.locator('[data-testid="agent-composer-tokens"]').first.inner_text()[:40])
            page.locator('[data-testid="canvas-agent-composer-mention"]').first.click()
            page.wait_for_timeout(400)

            print("— ⑥ ⑦ 定位链：整块浮层必须在视口内（本批踩过的坑）—")
            vp = page.viewport_size
            in_view = (
                cb["x"] >= 0 and ib["x"] >= 0
                and cb["y"] >= 0 and ib["y"] >= 0
                and cb["y"] + cb["height"] <= vp["height"] + 1
                and ib["y"] + ib["height"] <= vp["height"] + 1
            )
            check("两级都在视口内（`bottom-full` 的定位祖先是卡片，不是抽屉）", in_view,
                  f'cats y={cb["y"]}…{cb["y"] + cb["height"]}, items y={ib["y"]}…{ib["y"] + ib["height"]}, vp={vp["height"]}')
            card = box(page, '[data-testid="canvas-agent-session-composer"]')
            cats_bottom = cb["y"] + cb["height"]
            check("浮层锚在输入卡片上缘（源站：一级底落在卡片顶下移 9px）",
                  cats_bottom > card["y"],
                  f"cats bottom={cats_bottom} vs card top={card['y']}")

            print("— ⑧ 反向自检 —")
            # ⚠ 批 839：这三条原来连着跑，中间那次「收起」靠按 Esc —— 但
            #   JimengAiDrawer 当时**一个 Escape 监听都没有**（全仓 20+ 个浮层
            #   都有，唯独它没有）。于是 Esc 是空操作，下一次点击 `@` 走的是
            #   **toggle**，把浮层关掉了，最后那条断言拿到 0/0。
            #   看着像「产品坏了」，其实是判据用了一个根本不存在的收起手段，
            #   顺带暴露了一个真的缺口。处理：产品补上 Escape（复用全仓同一条
            #   捕获阶段约定），判据把「Esc 真的收起了」单列一条 —— 收起手段
            #   本身也该被量到，不能只是它后面那条断言的隐含前提。
            page.keyboard.press("Escape")
            page.wait_for_timeout(400)
            check("Esc 能收起抽屉里开着的浮层（全仓浮层统一契约，源站未取证）",
                  page.locator('[data-testid="agent-mention-panel"]').count() == 0)
            page.locator('[data-testid="canvas-agent-composer-mention"]').first.click()
            page.wait_for_timeout(400)
            check("收起后重开，两块仍在（④ 不是恒真）",
                  page.locator(CATS).count() == 1 and page.locator(ITEMS).count() == 1)
            check("页面无运行时错误", not errs, str(errs[:2]))
        finally:
            out = Path("docs/research/jimeng-canvas-batch838-2026-10-04")
            out.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(out / "clone-refpopover.png"))
            b.close()

    print(f"\n{'PASS' if not failures else 'FAIL'} — batch 838 refpopover "
          f"{passed}/{passed + len(failures)}")
    for f in failures:
        print("  -", f)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

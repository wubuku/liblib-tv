#!/usr/bin/env python
"""batch 839-refitems verifier —— 「添加参考」条目面板列**画布上该类型的节点**。

取证（`jimeng_839_refsource.py` + `docs/research/jimeng-canvas-batch839-*`，
源站 1512×950，逐个分类点开实测）：

    条目面板「当前画布」段列的就是**画布上该类型的节点，倒序**：
        文本 → 文本 3 / 文本 2 / 文本 1
        视频 → 视频 1
        主体 / 图片 / 音频 → 「暂无相关节点」（这张画布上真没有这三种节点）
    点条目 ⇒ composer 多出**同名**芯片、浮层收起。**没有确认钮。**

这一条**推翻了批 838 的前提**。838 我只试了「主体」一个分类，看到空态就
写下「源站每个分类都空、连画布上明明存在的『视频 1』都没列」，并据此断言
「它列画布节点这个推断不成立」—— 那是个**没验过的推论**：试了一个分类，
就外推到五个。逐个点开之后真相是「它列的就是画布节点」。据此 839：

  ① 删掉复刻自有的 `agent-ref-confirm` 确认钮（源站没有；它产出的
     `@分类` 是一种**合成串**，node 明明叫「视频 1」却插成「@视频」，
     那是另一条会说谎的路）。
  ② 条目接真节点：按类型过滤 → **倒序** → 取 `data.title`。
  ③ 浮层锚点从 bottom 改成 **top**（层高 312 = 一级实高）。bottom 锚在
     条目一多、面板变高时顶会跟着跑，判据当场变红。

判据怎么落：期望值**从画布自己算**，不写死 fixture 里的字符串 ——
量侧读每个 `.react-flow__node` 的类型（class 里的 `react-flow__node-<type>`）
与标题（`[data-testid="node-title-text"]` 的 **`title` 属性**，未选中态那个
span 带的是**完整未截断**的标题；节点正文里那行是截断的，还混着「0:02 / 0:06」
这类时长后缀，不能当标题读 —— 这是批 839 探针实测到的）。
"""

from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:4317"
VIEWPORT = {"width": 1680, "height": 826}

ITEMS = '[data-testid="agent-ref-items"]'
# 复刻的 REF_KIND_TO_NODE_TYPE（JimengAiDrawer.tsx）。判据把它逐项钉住 ——
# 五个分类各点一遍，条目数/条目名都必须等于该类型节点在画布上的倒序标题。
KIND_TO_TYPE = {
    "主体": "subject",
    "图片": "image",
    "视频": "video",
    "音频": "audio",
    "文本": "text",
}

# 读画布：[{type, title}]，顺序 = DOM 顺序（= store 顺序）
READ_CANVAS = """() => Array.from(document.querySelectorAll('.react-flow__node'))
  .map((n) => {
    const m = (n.className || '').match(/react-flow__node-([a-z]+)/);
    const t = n.querySelector('[data-testid="node-title-text"]');
    return { type: m ? m[1] : '', title: t ? (t.getAttribute('title') || '') : '' };
  })"""

# 读 composer 里的芯片：每枚一枚标签，**去掉**那颗移除钮的文字。
# ⚠ 量具（批 839 自己踩的）：直接取容器 inner_text 会把移除钮的 `×` 也读进来，
#   于是「芯片文字 == 节点标题」永远差一个字符。这不是产品坏了，是尺子把
#   按钮的字当成了标签的一部分 —— 标签与按钮本来就是两个东西。
READ_CHIPS = """() => {
  const c = document.querySelector('[data-testid="agent-composer-tokens"]');
  if (!c) return [];
  return Array.from(c.children).map((chip) => {
    const clone = chip.cloneNode(true);
    clone.querySelectorAll('button').forEach((b) => b.remove());
    return (clone.textContent || '').trim();
  });
}"""


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

    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        page = b.new_context(viewport=VIEWPORT, locale="zh-CN").new_page()
        errs: list[str] = []
        page.on("pageerror", lambda e: errs.append(str(e)[:160]))
        page.on(
            "console",
            lambda m: errs.append(f"console.{m.type}: {m.text}") if m.type == "error" else None,
        )

        def n(sel: str) -> int:
            return page.locator(sel).count()

        def item_names() -> list[str]:
            """条目可见文字 = testid 后缀（后缀就是节点标题，契约的一部分）。"""
            return page.evaluate(
                """() => Array.from(document.querySelectorAll('[data-testid^="agent-ref-item-"]'))
                     .map((e) => (e.getAttribute('data-testid') || '')
                                    .replace('agent-ref-item-', ''))"""
            )

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

            canvas = page.evaluate(READ_CANVAS)
            titled = [c for c in canvas if c["title"]]
            check(
                "画布上每个节点都能从 DOM 读到类型和完整标题",
                len(titled) == len(canvas) and all(c["type"] and c["title"] for c in canvas),
                f"canvas={canvas}",
            )

            def expected(kind: str) -> list[str]:
                t = KIND_TO_TYPE[kind]
                return [c["title"] for c in canvas if c["type"] == t][::-1]

            page.locator('[data-testid="canvas-agent-composer-mention"]').first.click()
            page.wait_for_timeout(500)

            print("— ① 五个分类逐个点开：条目 == 画布上该类型节点的标题（倒序）—")
            for kind, ntype in KIND_TO_TYPE.items():
                page.locator(f'[data-testid="agent-ref-kind-{kind}"]').click()
                page.wait_for_timeout(220)
                want = expected(kind)
                got = item_names()
                if want:
                    check(
                        f"「{kind}」⇒ 条目是画布上 {ntype} 节点标题、**倒序**",
                        got == want,
                        f"want={want} got={got}",
                    )
                else:
                    check(
                        f"「{kind}」（画布上无 {ntype} 节点）⇒ 空态「暂无相关节点」",
                        got == [] and n(f'{ITEMS} >> text=暂无相关节点') >= 1,
                        f"got={got}",
                    )
                # 两段标题随分类走：<分类>库
                check(
                    f"「{kind}」⇒ 第二段标题是「{kind}库」",
                    n(f'{ITEMS} >> text={kind}库') == 1,
                    f'count={n(f"{ITEMS} >> text={kind}库")}',
                )

            print("— ② 条目与画布同源：每个条目名都来自画布，非空互异 —")
            page.locator('[data-testid="agent-ref-kind-视频"]').click()
            page.wait_for_timeout(220)
            names = item_names()
            canvas_titles = [c["title"] for c in titled]
            check("条目名非空", all(x.strip() for x in names), str(names))
            check("条目名互异（两枚节点标题不同）", len(set(names)) == len(names), str(names))
            check(
                "每个条目名都真的是画布上某个节点的标题",
                all(x in canvas_titles for x in names),
                f"names={names} canvas={canvas_titles}",
            )
            check(
                "条目数 == 该类型画布节点数",
                len(names) == len(expected("视频")),
                f'items={len(names)} nodes={len(expected("视频"))}',
            )

            print("— ③ 点条目 ⇒ 芯片是**被点那个**的名字 + 浮层收起 —")
            # ⚠ 量具：先取名字再点。被点的条目点完就从 DOM 里没了（浮层收起），
            #   点完再去读它会 30s 超时 —— 810 就这么炸过一次。
            target = page.locator('[data-testid^="agent-ref-item-"]').first
            target_name = target.inner_text().strip()
            target.click()
            page.wait_for_timeout(400)
            chips = page.evaluate(READ_CHIPS)
            check("composer 出现芯片容器", n('[data-testid="agent-composer-tokens"]') == 1)
            check(
                "芯片文字 == 被点条目的名字（不是 @视频 这种合成串）",
                chips == [target_name],
                f"chips={chips} target={target_name!r}",
            )
            check("浮层自动收起（源站实测）", n('[data-testid="agent-mention-panel"]') == 0)

            print("— ④ 确认钮已撤：源站点条目即生效，没有二次确认 —")
            confirm = '[data-testid="agent-ref-confirm"]'
            check("`agent-ref-confirm` 不复存在", n(confirm) == 0, f"count={n(confirm)}")
            page.locator('[data-testid="canvas-agent-composer-mention"]').first.click()
            page.wait_for_timeout(400)
            check(
                "重开后浮层里也不再有确认钮",
                n('[data-testid="agent-mention-panel"]') == 1 and n(confirm) == 0,
            )
            check(
                "浮层里只有两段 + 条目，没有第三个动作按钮",
                page.locator(f'{ITEMS} button').count() == len(expected("视频")),
                f'buttons={page.locator(f"{ITEMS} button").count()}',
            )

            print("— ⑤ 同一个节点点两次只插一枚芯片（去重）—")
            page.locator('[data-testid^="agent-ref-item-"]').first.click()
            page.wait_for_timeout(350)
            page.locator('[data-testid="canvas-agent-composer-mention"]').first.click()
            page.wait_for_timeout(350)
            page.locator('[data-testid^="agent-ref-item-"]').first.click()
            page.wait_for_timeout(350)
            chips2 = page.evaluate(READ_CHIPS)
            check(
                "重复引用同一节点不产生第二枚芯片",
                chips2.count(target_name) == 1,
                f"chips={chips2}",
            )

            print("— ⑥ 芯片可单独移除（发消息后不残留脏引用）—")
            page.locator(f'[aria-label="移除 {target_name}"]').first.click()
            page.wait_for_timeout(300)
            left = page.locator('[data-testid="agent-composer-tokens"]')
            check(
                "移除后芯片容器退场",
                n('[data-testid="agent-composer-tokens"]') == 0,
                f"text={left.all_inner_texts() if left.count() else ''!r}",
            )

            print("— ⑦ Escape 收起（本批给抽屉补上的，全仓浮层统一契约）—")
            page.locator('[data-testid="canvas-agent-composer-mention"]').first.click()
            page.wait_for_timeout(400)
            check("先确认浮层是开着的", n('[data-testid="agent-mention-panel"]') == 1)
            page.keyboard.press("Escape")
            page.wait_for_timeout(400)
            check("Esc 收起浮层", n('[data-testid="agent-mention-panel"]') == 0)
            check("Esc 没顺手把抽屉也关了", n('[data-testid="canvas-agent-drawer"]') == 1)

            print("— ⑧ 二级面板的顶**跟着当前选中行走**（源站逐分类实测；批 839 订正 838）—")
            # 源站五组实测：主体 行 518→二级 518 / 图片 570→570 / 视频 622→622 /
            # 音频 674→674 / 文本 726→726。批 838 只在默认选中的「主体」上量过
            # 一次，把「对齐首行」当成了规则，复刻于是把 top 写死 36 也判绿。
            # 这里**逐个分类**各比一次，且比的是**那一行的真实盒**。
            page.locator('[data-testid="canvas-agent-composer-mention"]').first.click()
            page.wait_for_timeout(400)
            for i, kind in enumerate(KIND_TO_TYPE):
                page.locator(f'[data-testid="agent-ref-kind-{kind}"]').click()
                page.wait_for_timeout(200)
                row = page.locator(f'[data-testid="agent-ref-kind-{kind}"]').bounding_box() or {}
                it = page.locator(ITEMS).first.bounding_box() or {}
                check(
                    f"选中「{kind}」⇒ 二级顶落在**这一行**上（源站 {518 + i * 52}）",
                    abs(it["y"] - row["y"]) <= 1,
                    f"items top={it['y']} vs row top={row['y']}",
                )

            print("— ⑨ 浮层形状没被这批改坏（回归 838 的几何）—")
            page.locator('[data-testid="agent-ref-kind-视频"]').click()
            page.wait_for_timeout(250)
            cats = page.locator('[data-testid="agent-ref-categories"]').first.bounding_box() or {}
            ibox = page.locator(ITEMS).first.bounding_box() or {}
            rows = page.locator('[data-testid^="agent-ref-kind-"]')
            check("一级仍 240 宽", cats.get("width") == 240, str(cats.get("width")))
            check(
                "一级实高 296（源站实测；批 838 写 312 是因为多留了 py-2）",
                cats.get("height") == 296,
                str(cats.get("height")),
            )
            check("二级仍 240 宽", ibox.get("width") == 240, str(ibox.get("width")))
            check(
                "一级首行在顶下 36（源站 518-482；这条曾被恒真判据放过 12px 的错）",
                abs(rows.first.bounding_box()["y"] - (cats["y"] + 36)) <= 1,
                f'{rows.first.bounding_box()["y"]} vs {cats["y"] + 36}',
            )
            check("5 枚分类行仍各 48 高",
                  all(rows.nth(i).bounding_box()["height"] == 48 for i in range(rows.count())),
                  str([rows.nth(i).bounding_box()["height"] for i in range(rows.count())]))
            vp = page.viewport_size
            check(
                "两块都在视口内（定位链回归自检）",
                cats["y"] >= 0 and ibox["y"] >= 0
                and cats["y"] + cats["height"] <= vp["height"] + 1
                and ibox["y"] + ibox["height"] <= vp["height"] + 1,
                f'cats {cats["y"]}…{cats["y"] + cats["height"]}, '
                f'items {ibox["y"]}…{ibox["y"] + ibox["height"]}, vp={vp["height"]}',
            )
            check("页面无运行时错误", not errs, str(errs[:2]))
        finally:
            out = Path("docs/research/jimeng-canvas-batch839-2026-10-04")
            out.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(out / "clone-refitems.png"))
            b.close()

    print(
        f"\n{'PASS' if not failures else 'FAIL'} — batch 839 refitems "
        f"{passed}/{passed + len(failures)}"
    )
    for f in failures:
        print("  -", f)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

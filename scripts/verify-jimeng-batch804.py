"""Jimeng clone batch 804 verifier — 节点摘要弹层的高度是**内容驱动**的。

batch 795 当初只看到 1 个节点条目，把弹层高度记成写死的 92px；batch 794 照抄了这个
数值。batch 804 在源站画布节点变多后复测，发现 92 是 N=1 的特例：

    内部 padding 4px · 圆角 12px · 条目行高 36px · 条目间 4px
    分隔块 4px（内含 1px 线，上下各 4px）· 底部「查看项目信息」36px
    ⇒ H = 4 + (36N + 4(N-1)) + 4 + 4 + 4 + 36 + 4 = **40N + 52**

    实测吻合：N=1 → 92（batch 795 读数）· N=2 → 132 · N=4 → 212

写死高度在节点数一变时就假失败，所以本批断言的是**公式**和构成项，并且直接注入一条
多余行来证明高度确实随内容增长（而不是恰好等于某个常数）。
"""

import os
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "design-references" / "jimeng"
BASE_URL = os.environ.get("JIMENG_BASE_URL", "http://localhost:4317")
CANVAS_URL = f"{BASE_URL}/jimeng/canvas/demo"
VIEWPORT = {"width": 1680, "height": 826}
SUMMARY = '[data-testid="topbar-node-summary"]'
TRIGGER = '[data-testid="canvas-node-summary-trigger"]'

# 弹层内部几何快照：一次 evaluate 拿全，避免反复往返。
GEOMETRY_JS = """() => {
  const root = document.querySelector('[data-testid="topbar-node-summary"]');
  if (!root) return null;
  const cs = getComputedStyle(root);
  const kids = Array.from(root.children);
  const list = kids.find((k) => k.tagName === 'DIV');
  const rows = list ? Array.from(list.children) : [];
  const gap = list ? parseFloat(getComputedStyle(list).rowGap || '0') : 0;
  const sep = kids.find((k) => k.tagName === 'DIV' && k !== list);
  const tailBtn = kids.find((k) => k.tagName === 'BUTTON');
  const rect = root.getBoundingClientRect();
  return {
    width: rect.width, height: rect.height,
    paddingTop: parseFloat(cs.paddingTop), paddingBottom: parseFloat(cs.paddingBottom),
    borderRadius: parseFloat(cs.borderTopLeftRadius),
    rowCount: rows.length,
    rowHeights: rows.map((r) => r.getBoundingClientRect().height),
    gap,
    sepHeight: sep ? sep.getBoundingClientRect().height : null,
    tailHeight: tailBtn ? tailBtn.getBoundingClientRect().height : null,
  };
}"""


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
        errors: list[str] = []
        page.on("console", lambda m: errors.append(f"console.{m.type}: {m.text}") if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))

        page.goto(CANVAS_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(2500)

        print("— 打开节点摘要弹层 —")
        page.locator(TRIGGER).click()
        page.wait_for_timeout(400)
        g = page.evaluate(GEOMETRY_JS)
        check("弹层已开", g is not None, str(g))
        if g is None:
            ctx.close()
            browser.close()
            raise SystemExit(1)

        n = g["rowCount"]
        expect_h = 40 * n + 52

        print("— SOURCE_FACT：构成项 —")
        check("宽度 200", near(g["width"], 200), f"width={g['width']}")
        check("圆角 12", near(g["borderRadius"], 12), f"radius={g['borderRadius']}")
        check("上下 padding 各 4",
              near(g["paddingTop"], 4) and near(g["paddingBottom"], 4),
              f"{g['paddingTop']}/{g['paddingBottom']}")
        check(f"每行高 36（共 {n} 行）",
              len(g["rowHeights"]) == n and all(near(h, 36) for h in g["rowHeights"]),
              str(g["rowHeights"]))
        check("行间 gap 4", near(g["gap"], 4), f"gap={g['gap']}")
        check("分隔块高 4", g["sepHeight"] is not None and near(g["sepHeight"], 4), f"sep={g['sepHeight']}")
        check("底部「查看项目信息」高 36", g["tailHeight"] is not None and near(g["tailHeight"], 36),
              f"tail={g['tailHeight']}")

        print("— 公式 H = 40N + 52 —")
        check(f"实际高度 {round(g['height'])} == 40*{n}+52 = {expect_h}",
              near(g["height"], expect_h), f"h={g['height']} expect={expect_h}")
        # 分项求和 = 实际高度：证明公式是从构成项推出来的，不是凑数
        parts = (4 + sum(36 for _ in range(n)) + 4 * (n - 1) + 4 + 4 + 4 + 36 + 4)
        check("分项求和等于实际高度", parts == expect_h and near(g["height"], parts),
              f"sum={parts} actual={g['height']}")

        print("— 高度随内容增长，不是写死 —")
        # 注入一条多余行：高度必须跟着 +40。这是对「内容驱动」最直接的证伪测试。
        injected = page.evaluate(
            """() => {
              const root = document.querySelector('[data-testid="topbar-node-summary"]');
              const list = Array.from(root.children).find((k) => k.tagName === 'DIV');
              const before = root.getBoundingClientRect().height;
              const b = document.createElement('button');
              b.style.height = '36px';
              list.appendChild(b);
              return { before, after: root.getBoundingClientRect().height };
            }"""
        )
        check("加一行后高度 +40（证明内容驱动）",
              near(injected["after"] - injected["before"], 40),
              f"{injected['before']} -> {injected['after']}")

        page.screenshot(path=str(REFERENCE_DIR / "jimeng-clone-batch804-node-summary-1680.png"))

        # 刷新回去，别把注入的 DOM 留给后续断言
        page.reload(wait_until="domcontentloaded")
        page.wait_for_timeout(2000)
        page.locator(TRIGGER).click()
        page.wait_for_timeout(350)
        g2 = page.evaluate(GEOMETRY_JS)
        check("刷新后回到公式高度", g2 is not None and near(g2["height"], 40 * g2["rowCount"] + 52),
              str(g2 and g2["height"]))

        print("— 回归 —")
        check("无 console/page 错误", not errors, "; ".join(errors[:3]))
        ctx.close()
        browser.close()

    print()
    if failures:
        print(f"FAIL: {len(failures)}/{checks} 项未通过")
        for f in failures:
            print("  -", f)
        raise SystemExit(1)
    print(f"PASS: jimeng batch 804 节点摘要弹层内容驱动高度 H=40N+52（{checks} 项断言全通过）")


if __name__ == "__main__":
    main()

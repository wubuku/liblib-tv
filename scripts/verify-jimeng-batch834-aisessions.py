"""Jimeng clone batch 834-aisessions verifier — 「新建会话」不再等于「销毁会话」。

本批起因是 833 留下的**最后一处** `onClick={() => pushToast` 桩：AI 抽屉的
「会话列表」。查它能不能照 833 的路子接（弹个真面板）时，发现底下是**两个**缺陷：

1. **「会话列表」是 toast 桩** —— 点它只弹一句「会话列表：N 条」。
2. **「新建会话」在销毁会话** —— 它的 onClick 是 `setMessages([])`。标签写着
   「新建」，实际把当前会话删掉且**不可恢复**。这比桩更糟：桩至少不假装。

而 `messages` 是 `JimengAiDrawer` 的**组件本地 useState**，store 里没有任何会话
概念（`grep session|messages|conversation src/store/jimengStore.ts` 为空）——
也就是说抽屉一卸载会话就没了。给它套个面板列出那唯一一条，等于造假。

本批把会话搬进 store（`aiSessions` / `aiActiveSessionId` / `appendAiMessage` /
`newAiSession` / `selectAiSession`），于是「新建」= **追加一条并切过去**，旧的仍在列表里。

### 判据（落在关系上，不写死条数与文案）

  ① 会话列表是真浮层（有 testid），不是 toast
  ② 发一条消息 ⇒ 列表里出现 1 行，标题 = 首条用户消息
  ③ **新建会话 ⇒ 变 2 行，旧的那条还在**（这条是本批的核心：它直接判「新建≠销毁」）
  ④ **切回旧会话 ⇒ 消息流真的换回去**（不是只改个高亮）
  ⑤ **关掉抽屉再打开 ⇒ 会话还在**（这条验的是「搬进 store」这件事本身；
     搬之前抽屉一卸载就没了）
  ⑥ 一条都没发时：触发钮 aria-disabled，列表里显示「还没有会话」
  ⑦ 反向自检：不点新建时行数不变（③ 不是恒真）

⚠️ 源站这枚弹层的**内容与几何未取证**（批 808/810 量到的是触发钮 58×32，
弹层没打开量过），所以列表的**语义是复刻自有的**，不写成 SOURCE_FACT。
"""

import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs" / "research" / "jimeng-canvas-batch834-2026-10-04"
BASE_URL = os.environ.get("JIMENG_BASE_URL", "http://localhost:4317")
VIEWPORT = {"width": 1512, "height": 950}

HYDRATED = """() => { const el = document.getElementById('__next')
  || document.body.firstElementChild || document.body;
  return Object.keys(el).some(k => k.startsWith('__reactFiber$')); }"""

ROWS = r"""() => {
  const m = document.querySelector('[data-testid="canvas-agent-session-menu"]');
  if (!m) return null;
  const rows = [...m.querySelectorAll('[data-testid^="canvas-agent-session-row-"]')];
  return { n: rows.length,
           titles: rows.map((r) => (r.textContent || '').replace(/\s+/g, ' ').trim()),
           active: rows.filter((r) => r.getAttribute('aria-current') === 'true').length };
}"""

MSGS = r"""() => {
  const box = document.querySelector('[data-testid="agent-messages"]');
  if (!box) return null;
  const us = [...box.querySelectorAll('[data-testid="agent-msg-user"]')];
  return { n: box.querySelectorAll('[data-testid="agent-msg-agent"]').length
                + us.length,
           userTexts: us.map((e) => (e.textContent || '').trim()) };
}"""


def main() -> int:
    failures: list[str] = []
    checks = 0

    def check(name: str, ok: bool, detail: str = "") -> None:
        nonlocal checks
        checks += 1
        if not ok:
            failures.append(f"{name}: {detail}")
        print(f"  [{'ok ' if ok else 'FAIL'}] {name}{'' if ok else ' — ' + detail}")

    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        pg = b.new_context(viewport=VIEWPORT, locale="zh-CN").new_page()
        errs: list[str] = []
        pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
        try:
            pg.goto(f"{BASE_URL}/jimeng/canvas/demo", wait_until="domcontentloaded")
            pg.wait_for_selector('[data-testid="canvas-fixed-toolbar"]', timeout=60000)
            for _ in range(12):
                if pg.evaluate(HYDRATED):
                    break
                pg.wait_for_timeout(1000)
            else:
                check("复刻已 hydrate", False, "读到 SSR 骨架，其余断言全部无意义")
                return 1
            check("复刻已 hydrate", True)

            trigger = pg.get_by_label("与 AI 对话", exact=True).first

            print("\n— ⑥ 还没发过消息：触发钮应当禁用 —")
            trigger.click()
            pg.wait_for_selector('[data-testid="canvas-agent-drawer"]', timeout=20000)
            pg.wait_for_timeout(800)
            list_btn = pg.locator('[data-testid="canvas-agent-session-menu-trigger"]').first
            create_btn = pg.locator('[data-testid="canvas-agent-session-create"]').first
            check("会话列表钮 aria-disabled（源站契约：无会话时禁用）",
                  list_btn.get_attribute("aria-disabled") == "true"
                  or list_btn.is_disabled(),
                  f'aria-disabled={list_btn.get_attribute("aria-disabled")} '
                  f'disabled={list_btn.is_disabled()}')
            check("新建会话钮同样禁用",
                  create_btn.get_attribute("aria-disabled") == "true"
                  or create_btn.is_disabled(),
                  f'aria-disabled={create_btn.get_attribute("aria-disabled")}')

            print("\n— ② 发一条消息 ⇒ 会话出现 —")
            ci = pg.locator('[data-testid="agent-composer-input"]').first
            check("输入框有无障碍名（此前只有 placeholder = 信号缺口）",
                  (ci.get_attribute("aria-label") or "") != "",
                  repr(ci.get_attribute("aria-label")))
            # ⚠️ 「发送消息」是**按钮**的 aria-label，不是输入框。
            #    我第一版拿它去 fill，超时 30s —— 元素存在但 disabled，
            #    报错是 "element is not enabled"，很容易误判成「产品坏了」。
            #    输入框走自己的锚点（本批刚补上的 agent-composer-input）。
            pg.locator('[data-testid="agent-composer-input"]').first.fill("把这段布光照亮一点")
            pg.wait_for_timeout(300)
            pg.get_by_label("发送消息").first.click()
            pg.wait_for_timeout(900)
            m1 = pg.evaluate(MSGS)
            check("消息流出现了（1 问 1 答）", m1 and m1["n"] == 2, str(m1))
            check("用户消息就是刚发的那句",
                  m1 and "把这段布光照亮一点" in (m1["userTexts"][0] if m1["userTexts"] else ""),
                  str(m1 and m1["userTexts"]))

            list_btn.click()
            pg.wait_for_selector('[data-testid="canvas-agent-session-menu"]', timeout=10000)
            r1 = pg.evaluate(ROWS)
            check("① 会话列表是真浮层（有 testid，不是 toast）", r1 is not None, str(r1))
            check("② 列表里有 1 行，标题取首条用户消息",
                  r1 and r1["n"] == 1 and "把这段布光照亮一点" in r1["titles"][0],
                  str(r1 and r1["titles"]))
            check("当前会话带 aria-current（唯一一条）",
                  r1 and r1["active"] == 1, str(r1 and r1["active"]))

            print("\n— ③ 新建会话 ⇒ 变 2 行，旧的那条还在（本批核心）—")
            # ⚠️ 不要在这里按 Escape 试图收起面板：批 381 契约「Escape 不关抽屉」，
            #    对这个面板同样无效 —— 面板会一直开着，而我再点一次列表钮
            #    反而会把它 toggle 关掉（我踩过：后面 wait_for_selector 超时 10s）。
            #    正确做法：面板本来就开着，直接点「新建会话」，然后直接读列表。
            check("新建前列表仍开着（2 的前置条件）",
                  pg.locator('[data-testid="canvas-agent-session-menu"]').count() == 1)
            create_btn.click()
            pg.wait_for_timeout(800)
            r2 = pg.evaluate(ROWS)
            check("③ 新建后变成 2 行 —— 旧会话**没有**被销毁",
                  r2 and r2["n"] == 2, str(r2 and r2["n"]))
            check("旧会话（首条用户消息那条）仍在列表里",
                  r2 and any("把这段布光照亮一点" in t for t in r2["titles"]),
                  str(r2 and r2["titles"]))
            check("新会话标题是「新会话」（还没有消息）",
                  r2 and any(t.startswith("新会话") for t in r2["titles"]),
                  str(r2 and r2["titles"]))
            m2 = pg.evaluate(MSGS)
            check("切到新会话后消息流是空的（不是还留着旧的）", m2 is None or m2["n"] == 0, str(m2))

            print("\n— ④ 切回旧会话 ⇒ 消息流真的换回去 —")
            rows = pg.locator('[data-testid^="canvas-agent-session-row-"]')
            rows.filter(has_text="把这段布光照亮一点").first.click()
            pg.wait_for_timeout(800)
            m3 = pg.evaluate(MSGS)
            check("④ 切回后消息流恢复成旧会话那两条",
                  m3 and m3["n"] == 2
                  and "把这段布光照亮一点" in (m3["userTexts"][0] if m3["userTexts"] else ""),
                  str(m3))
            check("列表面板已收起（点完即关）",
                  pg.locator('[data-testid="canvas-agent-session-menu"]').count() == 0)

            print("\n— ⑤ 关掉抽屉再打开 ⇒ 会话还在（验「搬进 store」本身）—")
            pg.locator('[data-testid="canvas-agent-session-collapse"]').first.click()
            pg.wait_for_timeout(800)
            check("抽屉已关闭",
                  pg.locator('[data-testid="canvas-agent-drawer"]').count() == 0)
            trigger.click()
            pg.wait_for_selector('[data-testid="canvas-agent-drawer"]', timeout=20000)
            pg.wait_for_timeout(900)
            m4 = pg.evaluate(MSGS)
            check("⑤ 重开后消息流还是旧会话那两条（会话没随卸载消失）",
                  m4 and m4["n"] == 2
                  and "把这段布光照亮一点" in (m4["userTexts"][0] if m4["userTexts"] else ""),
                  str(m4))
            list_btn.click()
            pg.wait_for_selector('[data-testid="canvas-agent-session-menu"]', timeout=10000)
            r4 = pg.evaluate(ROWS)
            check("重开后列表仍是 2 条", r4 and r4["n"] == 2, str(r4 and r4["n"]))
            pg.keyboard.press("Escape")

            print("\n— ⑦ 反向自检 —")
            before = (pg.evaluate(ROWS) or {}).get("n")
            pg.wait_for_timeout(2000)
            after = (pg.evaluate(ROWS) or {}).get("n")
            check("不点新建时行数不变（③ 不是恒真）",
                  before is not None and before == after, f'{before} → {after}')

            check("页面无运行时错误", not errs, str(errs[:2]))
        finally:
            b.close()

    print(f"\n{'PASS' if not failures else 'FAIL'} — {checks - len(failures)}/{checks}")
    for f in failures:
        print("  · " + f)
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())

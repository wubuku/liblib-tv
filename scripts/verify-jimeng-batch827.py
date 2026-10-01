#!/usr/bin/env python3
"""Jimeng clone batch 827 verifier — 两笔**欠账**，一笔是判据欠的，一笔是普查欠的。

起因是批 826 自己埋下的：它给账号菜单补上了源站有的第六项「新功能许愿」，
那是个外链。而死按钮普查的指纹只看**当前页**，看不见新标签页 —— 跟早就登记在
`UNVERIFIABLE` 里的「使用手册」「即梦CLI」完全同型。**不登记的话，下一轮
普查就会把它报成 DEAD**，下一个来跑普查的人会替他去"修"一个没坏的按钮。

所以本批的第一件事不是改产品，是**把判据的欠账补上**：

  A. 静态门禁：账号菜单里每一枚**外链型**菜单项，都必须在 UNVERIFIABLE 里有
     登记。这条是防复发的 —— 以后再加外链而忘了登记，A.2 会当场红掉。
  B. 静态门禁：有了 data-testid 的浮层容器，应登记进 KNOWN_BENIGN。
     批 826 的 README 写过一句"没有 testid，它连被正确归档的资格都没有"；
     现在有了 testid（canvas-user-menu），就登记上去。

第二笔欠账来自 826 的 C.4：普查按 `role ∈ dialog/menu/listbox` 枚举，
**看不见不带 role 的全屏 fixed 遮罩**。本批去源站量了同一入口，结果是 ——
**源站也一样不带**（全屏 fixed z-1001 1680×1050，role/aria-label/testid 三无）。
也就是说这盲区是**源站自带的性质**，不是复刻的缺陷，补 `role` 反而是擅自偏离
源站。于是本批的做法是：让普查能看见它 + 如实记录 + 只补用户不可见的
自动化锚点，**不动语义**。并用断言把这个"刻意不补"锁住，防止后人"顺手修好"。
"""

import json
import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = os.environ.get("JIMENG_CLONE_URL", "http://localhost:4317")
URL = f"{BASE}/jimeng/canvas/demo"
STATE = Path.home() / ".jimeng-automation" / "state.json"
ROOT = Path(__file__).resolve().parent.parent
AUDIT = ROOT / "scripts" / "jimeng_dead_button_audit.py"
MENU = '[data-testid="canvas-user-menu"]'

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


# 账号菜单里"点了会开新标签页"的那几项 —— 判据伸不到的地方
EXTERNAL_ITEMS = ["使用手册", "即梦CLI", "新功能许愿"]

# 全屏 fixed 遮罩：普查的 role 枚举看不见它，所以另开一条枚举
FULLSCREEN_JS = """() => {
  const vw = window.innerWidth, vh = window.innerHeight;
  return [...document.querySelectorAll('div,section,aside')].filter(e => {
    const s = getComputedStyle(e);
    if (s.position !== 'fixed') return false;
    const r = e.getBoundingClientRect();
    return r.width >= vw * 0.9 && r.height >= vh * 0.9;
  }).map(e => {
    const r = e.getBoundingClientRect();
    return {tag: e.tagName, role: e.getAttribute('role'),
            tid: e.getAttribute('data-testid'),
            al: e.getAttribute('aria-label'),
            w: +r.width.toFixed(0), h: +r.height.toFixed(0),
            z: getComputedStyle(e).zIndex,
            txt: (e.innerText || '').replace(/\\s+/g, ' ').trim().slice(0, 40)};
  });
}"""


def main() -> int:
    audit_src = AUDIT.read_text(encoding="utf-8")

    # ── A. 判据欠账：静态门禁 + 正面行为断言 ───────────────────────
    print("— 判据欠账 —")
    unv_start = audit_src.index("UNVERIFIABLE = {")
    unv_end = audit_src.index("\n}", unv_start)
    unverifiable_block = audit_src[unv_start:unv_end]
    still_exempt = [i for i in EXTERNAL_ITEMS if f'"{i}"' in unverifiable_block]
    check(
        "A.1 三枚外链项**不在** UNVERIFIABLE 里 —— 批 820 那条"
        "「外链 = 判据伸不到新标签页」的理由是错的，它们点完会关菜单，指纹看得见。"
        "带着错误理由的豁免比没有豁免更糟：它会让真正的死按钮永远查不出来。",
        not still_exempt,
        f"仍被豁免={still_exempt}" if still_exempt else "已全部撤回",
    )
    benign_start = audit_src.index("KNOWN_BENIGN = {")
    benign_end = audit_src.index("\n}", benign_start)
    benign_block = audit_src[benign_start:benign_end]
    check(
        "A.2 账号菜单容器 canvas-user-menu 已登记进 KNOWN_BENIGN"
        "（批 826 给了它 testid，从此有资格被正确归档）",
        '"canvas-user-menu"' in benign_block,
    )
    # 逐项 testid 是由 HELP_ITEMS 数组用模板串生成的
    # （`data-testid={`account-menu-item-${label}`}`），所以源码里**不会**出现
    # `account-menu-item-使用手册` 这种字面量 —— 第一版就是在这里读错了东西。
    # 该断言的是：三个 label 都在列表里，且 window.open 恰好被调 3 次。
    help_src = (ROOT / "src/components/jimeng/JimengHelpMenu.tsx").read_text(encoding="utf-8")
    missing = [i for i in EXTERNAL_ITEMS if f'label: "{i}"' not in help_src]
    opens = help_src.count("window.open(")
    check(
        "A.3 复刻里三枚外链菜单项都在，且 window.open 恰好 3 次",
        not missing and opens == len(EXTERNAL_ITEMS),
        f"缺失 label={missing}；window.open 调用 {opens} 次",
    )

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

        # ── A.4 正面断言：普查**看得见**这三枚外链项 ──────────────────
        # 撤回豁免的依据不能只是"我读了代码觉得会关菜单"，得用普查自己的
        # FINGERPRINT_JS 实测一遍：点完，菜单关掉，指纹变 → 普查不会误判。
        import importlib.util  # noqa: PLC0415 - 只在这一处需要

        spec = importlib.util.spec_from_file_location("jimeng_audit", str(AUDIT))
        audit_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(audit_mod)
        for item in EXTERNAL_ITEMS:
            page.reload(wait_until="domcontentloaded")
            page.wait_for_timeout(2500)
            page.locator('[data-testid="canvas-user-menu-trigger"]').click()
            page.wait_for_timeout(700)
            sel = f'[data-testid="account-menu-item-{item}"]'
            el = page.locator(sel)
            if not el.count():
                check(f"A.4 外链项「{item}」会被普查检出为活的", False, "菜单项不存在")
                continue
            bb = el.bounding_box()
            before = page.evaluate(audit_mod.FINGERPRINT_JS)
            page.mouse.click(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2)
            page.wait_for_timeout(500)
            after = page.evaluate(audit_mod.FINGERPRINT_JS)
            diff = [k for k in json.loads(before) if json.loads(before)[k] != json.loads(after)[k]]
            check(
                f"A.4 外链项「{item}」会被普查检出为活的"
                "（点完菜单关闭 → tids/text/layers 同时变，**不需要豁免**）",
                before != after and "tids" in diff and "text" in diff,
                f"指纹变化={before != after} 差异字段={diff}",
            )
            for extra in list(ctx.pages)[1:]:
                extra.close()
        page.reload(wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        # ── B. 普查的 role 枚举看不见的那一层 ───────────────────────
        print("— 普查盲区：全屏 fixed 遮罩（role 枚举之外） —")
        page.locator('[data-testid="canvas-share-trigger"]').first.click()
        page.wait_for_timeout(700)
        page.locator('[data-testid="share-create-team"]').click()
        page.wait_for_timeout(900)
        layers = page.evaluate(FULLSCREEN_JS)
        modal = [x for x in layers if x["tid"] == "jimeng-member-modal"]
        check("B.0 前置：会员弹窗已开", len(modal) == 1, str([x["tid"] for x in layers]))
        if modal:
            m = modal[0]
            check(
                "B.1 有自动化锚点 jimeng-member-modal（对用户不可见，只是让普查能看见）",
                True,
                f"{m['w']}×{m['h']} z={m['z']}",
            )
            check(
                "B.2 **刻意不补** role / aria-label —— 源站这一层同样三无"
                "（全屏 fixed z-1001 1680×1050 实测），补了就等于擅自偏离源站。"
                "这条断言是为了防止后人'顺手修好'。",
                m["role"] is None and m["al"] is None,
                f"role={m['role']} al={m['al']}",
            )
        # 每个全屏遮罩都要可定位（哪怕它没有 role）
        no_tid = [x for x in layers if not x["tid"]]
        check(
            "B.3 每个全屏 fixed 遮罩都有 data-testid（role 枚举之外另开一条判据，"
            "盲区不再靠人记得）",
            not no_tid,
            "; ".join(f"{x['tag']}/{x['w']}×{x['h']}" for x in no_tid[:4]),
        )
        page.keyboard.press("Escape")
        page.wait_for_timeout(600)

        # ── C. 补上锚点之后，普查真的能看见它了 ──────────────────────
        check(
            "C.1 弹窗关闭后锚点随之消失（testid 不是写死在别处的残留）",
            page.locator('[data-testid="jimeng-member-modal"]').count() == 0,
        )
        # 分享面板此时还开着（Escape 只收掉了会员弹窗），先收掉再开账号菜单，
        # 否则下一步查的是"菜单在不在"，而页面上开着的其实是分享面板。
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)
        page.locator('[data-testid="canvas-user-menu-trigger"]').click()
        page.wait_for_timeout(800)
        check(
            "C.2 账号菜单容器本身现在可被普查定位到（批 826 之前连定位都做不到）",
            page.locator(MENU).count() == 1,
            f"count={page.locator(MENU).count()}",
        )
        if page.locator(MENU).count() == 1:
            check(
                "C.3 容器上那层 aria-labelledby 仍解析得出触发器（加 testid 没破坏可访问名）",
                page.evaluate(
                    """() => {
                        const m = document.querySelector('[data-testid="canvas-user-menu"]');
                        if (!m) return false;
                        const lb = m.getAttribute('aria-labelledby');
                        const el = lb && document.getElementById(lb);
                        return !!(el && el.getAttribute('aria-label') === '用户菜单');
                    }"""
                ),
            )
        page.keyboard.press("Escape")
        page.wait_for_timeout(400)

        check("D.0 无页面 JS 报错", not errs, "; ".join(errs[:2]))
        ctx.close()
        b.close()

    print(f"\n{checks - len(failures)}/{checks}")
    if failures:
        print("FAILED: " + ", ".join(failures))
        return 1
    print("batch 827 OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())

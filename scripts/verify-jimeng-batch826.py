#!/usr/bin/env python3
"""Jimeng clone batch 826 verifier — 账号菜单补上源站有的第 6 项与两样锚点，
并把「每个浮层都必须可指名、可定位」立成**常备契约**。

选题来自一次全量浮层盘点：复刻里 8 个浮层，7 个同时有 `data-testid` 与可访问名，
**只有账号菜单两样都没有**。后果不是"不好看"：

  1. 自动化只能靠 `[role=menu]` 猜。而批 821 刚给分享面板的权限下拉也加了
     `role=menu` —— 这个选择器**真的歧义了**。
  2. 死按钮普查的 STATES 里，account-menu 态只能靠触发器进态，菜单容器本身
     因为没有 testid，连被登记进 KNOWN_BENIGN 的机会都没有。

源站实测（@1680×826，登录态，`[data-testid="canvas-user-menu"]`）：
  240×312 @[1428,56] bg rgb(34,34,34) r12 p-1 gap-1 flex-col
  ├ 头行 232×56 @[4,4] p 8/12 gap-12：36×36 头像 @[16,14] + 昵称 14/22/500
  ├ 分隔条 232×4 @[4,64]，内含 208×1 @[16,65.5] white/4
  └ 6 枚 role=menuitem 232×36，y = 72/112/152/192/232/272，p 9/12，13/20/400
复刻此前是 240×268、五项、项高 44、头是一行 12px 灰字，且无 testid/无名字。
差的 44px 恰好是漏掉的那一项：36 + 4。
"""

import json
import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = os.environ.get("JIMENG_CLONE_URL", "http://localhost:4317")
URL = f"{BASE}/jimeng/canvas/demo"
STATE = Path.home() / ".jimeng-automation" / "state.json"

MENU = '[data-testid="canvas-user-menu"]'
WISH_URL = "https://bytedance.larkoffice.com/share/base/form/shrcnqQGbwjK0rSJpJiNMVWCecc"

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


# 盘点所有 role 浮层：可指名（有可访问名）+ 可定位（有 data-testid）
CENSUS_JS = """() => {
  const SEL = '[role=dialog],[role=menu],[role=listbox]';
  const nameOf = (e) => {
    const al = e.getAttribute('aria-label');
    if (al && al.trim()) return al.trim();
    const lb = e.getAttribute('aria-labelledby');
    if (lb) {
      const parts = lb.split(/\\s+/).map(id => document.getElementById(id));
      const t = parts.filter(Boolean).map(n => (n.innerText || n.textContent || '').trim())
                    .join(' ').trim();
      if (t) return t;
    }
    const t = (e.innerText || '').trim();
    return t ? '(fallback:' + t.slice(0, 12) + ')' : '';
  };
  return [...document.querySelectorAll(SEL)].filter(e => {
    const s = getComputedStyle(e);
    if (s.display === 'none' || s.visibility === 'hidden') return false;
    const r = e.getBoundingClientRect();
    return r.width >= 4 && r.height >= 4;
  }).map(e => {
    const r = e.getBoundingClientRect();
    return {role: e.getAttribute('role'), tid: e.getAttribute('data-testid'),
            name: nameOf(e), w: +r.width.toFixed(0), h: +r.height.toFixed(0)};
  });
}"""

# 每个态：怎么进去。None = 基础态
STATES = [
    ("分享", '[data-testid="canvas-share-trigger"]', None),
    ("更多", '[data-testid="canvas-more-trigger"]', None),
    ("搜索", '[aria-label="搜索"]', None),
    ("生成历史", '[data-testid="canvas-history-launcher"]', None),
    ("用户菜单", '[data-testid="canvas-user-menu-trigger"]', None),
    ("节点摘要", '[data-testid="canvas-node-summary-trigger"]', None),
    ("AI 对话", '[data-testid="canvas-sidecar-launcher"]', None),
    ("快捷键面板", '[data-testid="canvas-user-menu-trigger"]', '[data-testid="account-menu-item-快捷键"]'),
    ("帮助中心", '[data-testid="canvas-user-menu-trigger"]', '[data-testid="account-menu-item-帮助中心"]'),
    ("水印设置", '[data-testid="canvas-user-menu-trigger"]', '[data-testid="account-menu-item-AI生成水印设置"]'),
    ("分享权限下拉", '[data-testid="canvas-share-trigger"]', '[data-testid="share-perm-trigger"]'),
]

RESET_JS = """() => { document.activeElement && document.activeElement.blur(); }"""


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
        # 打桩 window.open：外链的真实后果是开新标签页，本地不该真开
        page.add_init_script(
            """window.__opened = [];
               window.open = function (u, t, f) {
                 window.__opened.push({url: String(u), target: String(t)}); return null;
               };"""
        )
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(6000)

        # ── A. 账号菜单结构对齐源站 ─────────────────────────────────
        page.locator('[data-testid="canvas-user-menu-trigger"]').click()
        page.wait_for_timeout(900)
        check("A.0 前置：账号菜单打开", page.locator(MENU).count() == 1)

        m = page.evaluate(
            """(sel) => {
                const e = document.querySelector(sel);
                const r = e.getBoundingClientRect(); const s = getComputedStyle(e);
                const px = v => (v||'').replace('px','');
                const rel = el => { const b = el.getBoundingClientRect();
                    return {x:+(b.x-r.x).toFixed(1), y:+(b.y-r.y).toFixed(1),
                            w:+b.width.toFixed(1), h:+b.height.toFixed(1)}; };
                const head = e.children[0], av = head.children[0], dv = e.children[1], ln = dv.children[0];
                return {
                  menu: {x:+r.x.toFixed(1), y:+r.y.toFixed(1),
                         w:+r.width.toFixed(1), h:+r.height.toFixed(1),
                         bg:s.backgroundColor, r:px(s.borderTopLeftRadius),
                         p:px(s.paddingTop), gap:px(s.gap)},
                  tid: e.getAttribute('data-testid'),
                  al: e.getAttribute('aria-label'),
                  labelledby: e.getAttribute('aria-labelledby'),
                  head: rel(head), avatar: rel(av), divBox: rel(dv), line: rel(ln),
                  items: [...e.querySelectorAll('[role=menuitem]')].map(it => {
                    const b = it.getBoundingClientRect(); const cs = getComputedStyle(it);
                    return {txt:(it.innerText||'').trim(), x:+(b.x-r.x).toFixed(1),
                            y:+(b.y-r.y).toFixed(1), w:+b.width.toFixed(1),
                            h:+b.height.toFixed(1), p:px(cs.paddingTop),
                            fs:px(cs.fontSize), lh:px(cs.lineHeight)};
                  }),
                };
            }""",
            MENU,
        )
        check(
            "A.1 容器 240×312 @[1428,56]（此前 240×268，差的 44px 正是漏掉的那一项）",
            (m["menu"]["w"], m["menu"]["h"], m["menu"]["x"], m["menu"]["y"]) == (240, 312, 1428, 56),
            f"{m['menu']['w']}×{m['menu']['h']} @[{m['menu']['x']:.0f},{m['menu']['y']:.0f}]",
        )
        check(
            "A.2 底色/圆角/内距/间距 rgb(34,34,34) r12 p4 gap4",
            (m["menu"]["bg"], m["menu"]["r"], m["menu"]["p"], m["menu"]["gap"])
            == ("rgb(34, 34, 34)", "12", "4", "4"),
            str(m["menu"]),
        )
        check("A.3 容器有 data-testid=canvas-user-menu（源站同名）",
              m["tid"] == "canvas-user-menu", str(m["tid"]))
        resolved = page.evaluate(
            """(lb) => {
                const el = document.getElementById(lb);
                return el ? {
                  text: (el.innerText || el.textContent || '').trim(),
                  al: el.getAttribute('aria-label'),
                } : null;
            }""",
            m["labelledby"] or "",
        )
        check(
            "A.4 容器有可访问名：aria-labelledby 指向触发器且能解析出「用户菜单」"
            "（此前**两样都没有**，全画布 8 个浮层里唯一的例外）",
            m["al"] is None
            and m["labelledby"] is not None
            and resolved is not None
            and (resolved["al"] or resolved["text"]) == "用户菜单",
            f"labelledby={m['labelledby']} → {resolved}",
        )
        check("A.5 头行 232×56 @[4,4]（此前是一行 12px 灰字）",
              (m["head"]["w"], m["head"]["h"], m["head"]["x"], m["head"]["y"]) == (232, 56, 4, 4),
              str(m["head"]))
        check("A.6 头像 36×36 @[16,14]",
              (m["avatar"]["w"], m["avatar"]["h"], m["avatar"]["x"], m["avatar"]["y"]) == (36, 36, 16, 14),
              str(m["avatar"]))
        check("A.7 分隔条盒 232×4 @[4,64] + 内线 208×1 @[16,65.5]（源站 y 精确到 65.5）",
              (m["divBox"]["w"], m["divBox"]["h"], m["divBox"]["x"], m["divBox"]["y"]) == (232, 4, 4, 64)
              and (m["line"]["w"], m["line"]["h"], m["line"]["x"], m["line"]["y"]) == (208, 1, 16, 65.5),
              f"{m['divBox']} / {m['line']}")
        labels = [i["txt"] for i in m["items"]]
        check(
            "A.8 六枚 menuitem 齐全且顺序与源站逐字一致（含此前**缺失**的「新功能许愿」）",
            labels == ["帮助中心", "使用手册", "快捷键", "AI生成水印设置", "即梦CLI", "新功能许愿"],
            str(labels),
        )
        ys = [i["y"] for i in m["items"]]
        check("A.9 六项 y = 72/112/152/192/232/272（步进 40）",
              ys == [72, 112, 152, 192, 232, 272], str(ys))
        check("A.10 每项 232×36、padding-top 9、13px/20px（此前项高 44）",
              all(i["w"] == 232 and i["h"] == 36 and i["p"] == "9" and i["fs"] == "13" and i["lh"] == "20"
                  for i in m["items"]),
              str([(i["w"], i["h"], i["p"], i["fs"], i["lh"]) for i in m["items"]][:2]))

        # ── B. 新增那项不是死按钮 ───────────────────────────────────
        page.locator('[data-testid="account-menu-item-新功能许愿"]').click()
        page.wait_for_timeout(700)
        opened = page.evaluate("() => window.__opened || []")
        check(
            "B.1 点「新功能许愿」真开外链（打桩 window.open 取 URL，非计费、没真开页）",
            len(opened) == 1 and opened[0]["url"] == WISH_URL and opened[0]["target"] == "_blank",
            json.dumps(opened, ensure_ascii=False),
        )
        check("B.2 菜单已关闭", page.locator(MENU).count() == 0)

        # ── C. 常备契约：每个 role 浮层都要可指名 + 可定位 ────────────
        print("— 浮层锚点/可访问名普查（8 个浮层，逐态开） —")
        page.reload(wait_until="domcontentloaded")
        page.wait_for_timeout(5000)
        seen: list[dict] = []
        for name, trig, sub in STATES:
            try:
                page.locator(trig).first.click()
                page.wait_for_timeout(700)
                if sub:
                    page.locator(sub).first.click()
                    page.wait_for_timeout(700)
            except Exception as exc:  # noqa: BLE001
                check(f"C.x 进入「{name}」态", False, str(exc)[:90])
                continue
            for o in page.evaluate(CENSUS_JS):
                o["state"] = name
                seen.append(o)
            page.keyboard.press("Escape")
            page.wait_for_timeout(350)
            page.evaluate(RESET_JS)
            page.mouse.click(30, 950)
            page.wait_for_timeout(350)

        uniq = {o["tid"] or f"{o['state']}#{id(o)}": o for o in seen}
        by_tid: dict[str, dict] = {}
        for o in seen:
            if o["tid"]:
                by_tid[o["tid"]] = o
        no_tid = [o for o in seen if not o["tid"]]
        no_name = [o for o in seen if not o["name"] or o["name"].startswith("(fallback")]
        check(
            f"C.1 每个浮层都有 data-testid（本次盘点 {len(by_tid)} 个具名浮层）",
            not no_tid,
            "; ".join(f"{o['state']}/{o['role']}" for o in no_tid[:4]),
        )
        check(
            "C.2 每个浮层都有可访问名（aria-label 或 aria-labelledby 解析成功，"
            "不接受「拿 innerText 兜底」当可访问名）",
            not no_name,
            "; ".join(f"{o['state']}/{o['tid']}:{o['name']!r}" for o in no_name[:4]),
        )
        check(
            "C.3 `[role=menu]` 不再歧义：账号菜单与分享权限下拉各有独立 testid",
            "canvas-user-menu" in by_tid and "share-perm-menu" in by_tid,
            ", ".join(sorted(t for t in by_tid if "menu" in t)),
        )
        # 普查的盲区要**实证**，不能靠一条恒真断言糊过去（恒真断言就是假绿）。
        # 会员弹窗正是那种东西：全屏 fixed 遮罩，但**不带 role**，于是任何按
        # role 枚举的普查都看不见它。这里真去打开它、把它量出来。
        page.locator('[data-testid="canvas-share-trigger"]').first.click()
        page.wait_for_timeout(700)
        page.locator('[data-testid="share-create-team"]').click()
        page.wait_for_timeout(900)
        blind = page.evaluate(
            """() => {
                const vw = window.innerWidth, vh = window.innerHeight;
                const found = [...document.querySelectorAll('div')].filter(e => {
                    const s = getComputedStyle(e);
                    if (s.position !== 'fixed') return false;
                    const r = e.getBoundingClientRect();
                    if (r.width < vw * 0.9 || r.height < vh * 0.9) return false;
                    // 普查只认 role ∈ dialog/menu/listbox；这种全屏遮罩不带 role，
                    // 所以它既不在普查的枚举里，也没有可访问名 —— 记成 OPEN_QUESTION
                    return !e.getAttribute('role') && !e.querySelector('[role]');
                });
                return {n: found.length, hasClose: !!document.querySelector('[aria-label="关闭订阅页"]')};
            }"""
        )
        check(
            "C.4 普查盲区**实证**：会员弹窗是全屏 fixed 遮罩却不带 role，"
            "因此不在 role 枚举里 —— 记为 OPEN_QUESTION，不装作已覆盖",
            blind["n"] >= 1 and blind["hasClose"],
            f"无 role 的全屏 fixed 浮层 {blind['n']} 个，关闭钮存在={blind['hasClose']}",
        )
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)

        check("D.0 无页面 JS 报错", not errs, "; ".join(errs[:2]))
        ctx.close()
        b.close()

    print(f"\n{checks - len(failures)}/{checks}")
    if failures:
        print("FAILED: " + ", ".join(failures))
        return 1
    print("batch 826 OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())

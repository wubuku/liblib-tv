#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 838 源站探针 v8：★★ **决定性实验** —— 点「添加角色」，看新角色叫什么。

★ v7 已确证：
  - 源站资源栏有 `aria-label='添加角色'`（@8,116）与 `aria-label='添加机位'`（@8,156）；
  - 源站场景树当前是「机位1 / 机位2 / **角色A**」。

★ 本实验要回答：**「角色A」是源站的默认命名规则，还是用户自拟的名？**
⟹ 做法：点「添加角色」⟹ 看新角色叫什么 ⟹ 然后**删掉它**复原。

★ ★ 三条纪律：
  1. **前提不满足就作废**：如果「添加角色」点开的是一个**预设面板**（像机位那样 15 枚），
     那就**不是**直接新建 ⟹ 判「本实验无效」并**不下结论**；
  2. **收尾必须复原**（删掉新建的），且**用无正则口径复验**；
  3. ★ **源站有并发活动**（batch 837 时基线已是两台机位）⟹
     **只删本批新建的那一个**，绝不删不属于本批的对象。

★ 记录**每一步的读数**（进站基线 → 点开面板 → 选中后 → 收尾）。
"""
import json
import pathlib
import traceback

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_charname838b.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

DUMP_TREE = """() => {
  const vis=(e)=>{const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0 && getComputedStyle(e).visibility!=='hidden';};
  const out=[];
  for (const el of Array.from(document.querySelectorAll('span,div,button,a,p,li'))) {
    if (!vis(el) || el.childElementCount>0) continue;
    const r=el.getBoundingClientRect();
    if (r.x > 300) continue;
    const t=(el.textContent||'').trim();
    if (!t || t.length>30) continue;
    out.push({text:t, x:Math.round(r.x), y:Math.round(r.y), tag:el.tagName});
  }
  return out.sort((a,b)=> (a.y-b.y) || (a.x-b.x));
}"""

# ★ 面板里所有可见文本（点开「添加角色」后，右栏会出现角色列表）
DUMP_PANEL = """() => {
  const vis=(e)=>{const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0 && getComputedStyle(e).visibility!=='hidden';};
  const out=[];
  for (const el of Array.from(document.querySelectorAll('span,div,button,a,p,li,img'))) {
    if (!vis(el) || el.childElementCount>0) continue;
    const r=el.getBoundingClientRect();
    if (r.x < 1300) continue;
    const t=(el.textContent||'').trim();
    if (!t || t.length>40) continue;
    out.push({text:t, x:Math.round(r.x), y:Math.round(r.y), tag:el.tagName,
              cls:(el.className||'').toString().slice(0,70)});
  }
  return out.sort((a,b)=> (a.y-b.y) || (a.x-b.x));
}"""

# ★ 场景树里**可点的角色行**（用于删除）
DUMP_ROWS = """() => {
  const out=[];
  for (const el of Array.from(document.querySelectorAll('button,[role="button"],[role="treeitem"],li'))) {
    const r=el.getBoundingClientRect();
    if (r.width<=0||r.height<=0) continue;
    if (r.x > 300 || r.x < 40) continue;
    const t=(el.textContent||'').trim();
    if (!t || t.length>30) continue;
    out.push({text:t, x:Math.round(r.x), y:Math.round(r.y),
              w:Math.round(r.width), h:Math.round(r.height),
              tag:el.tagName, aria:el.getAttribute('aria-label')||'',
              title:el.getAttribute('title')||'',
              dataKeys:Object.keys(el.dataset||{})});
  }
  return out.sort((a,b)=> (a.y-b.y) || (a.x-b.x));
}"""


def open_desk(page):
    card = page.locator(".react-flow__node-director-console-3d").first
    card.hover()
    page.wait_for_timeout(800)
    page.locator(
        ".react-flow__node-director-console-3d button:has-text('打开导演台')").first.click()
    page.wait_for_timeout(9_000)


def clean(page):
    page.evaluate("() => { for (const el of document.querySelectorAll('nextjs-portal')) el.remove(); }")


def tree(page):
    items = page.evaluate(DUMP_TREE)
    # ★ 无正则口径：取左栏 x∈[50,300] 的叶子文本
    names, seen = [], set()
    for it in items:
        if 50 <= it["x"] <= 300 and it["text"]:
            if it["text"] not in seen:
                seen.add(it["text"])
                names.append(it["text"])
    return names, items


def run(out, cookies):
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        ctx = br.new_context(viewport={"width": 1920, "height": 1080}, locale="zh-CN")
        ctx.add_cookies([{"name": c["name"], "value": c["value"],
                          "domain": c["domain"], "path": c.get("path", "/"),
                          "expires": c.get("expires", -1),
                          "httpOnly": c.get("httpOnly", False),
                          "secure": c.get("secure", False),
                          "sameSite": c.get("sameSite", "Lax")} for c in cookies])
        page = ctx.new_page()
        page.goto(URL, wait_until="domcontentloaded", timeout=90_000)
        page.wait_for_timeout(12_000)
        open_desk(page)
        clean(page)

        base, _ = tree(page)
        out["①进站基线_左栏"] = base
        out["①★进站基线_角色数"] = len([x for x in base if x.startswith("角色")])

        # ② 点「添加角色」
        page.locator("[aria-label='添加角色']").first.click()
        page.wait_for_timeout(2_000)
        clean(page)
        out["②点添加角色后_面板文本"] = page.evaluate(DUMP_PANEL)
        after_open, _ = tree(page)
        out["②点添加角色后_左栏"] = after_open
        out["②★是否直接新增了角色"] = len(after_open) != len(base)

        try:
            page.screenshot(path="/tmp/liblib_source_charname838b.png")
            out["截图"] = "/tmp/liblib_source_charname838b.png"
        except Exception:
            pass

        # ③ 场景树的可点行（用于后续复原）
        out["③场景树可点行"] = page.evaluate(DUMP_ROWS)
        br.close()


def main():
    cookies = json.loads(COOKIE.read_text(encoding="utf-8"))
    out = {}
    try:
        run(out, cookies)
    except Exception:
        out["异常"] = traceback.format_exc()
    finally:
        OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", OUT)
        print("\n=== 进站基线（左栏）===")
        for x in (out.get("①进站基线_左栏") or []):
            print("   ", repr(x))
        print("  角色数 =", out.get("①★进站基线_角色数"))
        print("\n=== 点「添加角色」后左栏 ===")
        for x in (out.get("②点添加角色后_左栏") or []):
            print("   ", repr(x))
        print("  是否直接新增了角色：", out.get("②★是否直接新增了角色"))
        print("\n=== 点开后面板文本（前 30）===")
        for d in (out.get("②点添加角色后_面板文本") or [])[:30]:
            print("  @(%s,%s) %r" % (d["x"], d["y"], d["text"]))
        print("\n=== 场景树可点行 ===")
        for r in (out.get("③场景树可点行") or []):
            print("  @(%s,%s) %r aria=%r data=%s" % (r["x"], r["y"], r["text"], r["aria"], r["dataKeys"]))
        if out.get("异常"):
            print("异常：", out["异常"])


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 838 源站探针 v10：★ **复原** —— 删掉 v9 新建的「角色B」。

★★ 为什么必须复原：v9 在源站**新建了一个角色**（「角色B」）⟹ 源站是**用户的真实项目** ⟹
   不复原就等于替用户改了他们的画布 ⟹ ★ **副作用必须复核**。

★ 做法（**只删本批新建的那一个**，不碰别的）：
  1. 进站 ⟹ 读**树区行**（**无正则口径**：按 y 落在树区、x∈[40,300] 的可点行）；
  2. 找到名字为「**角色B**」的那一行 ⟹ ★ 用**名字**定位，但**先验证它是唯一的一行**
     （若有多行「角色B」⟹ 判「不唯一，不删」⟹ 报告让人工处理）；
  3. 右键它 ⟹ 菜单里找「删除」⟹ 点 ⟹ 确认；
  4. ★ **收尾复验**：用**与名字形态无关**的口径（**树区行数**）复验 ⟹ 回到进站基线。

★ ★ 纪律：
  - **不猜**：菜单里找不到「删除」⟹ 就**报告**而不是乱点；
  - ★ **每一步都记录读数**（进站行 → 菜单项 → 删除后行）；
  - 若删不掉 ⟹ 如实报告「未复原」，**不谎称已复原**。
"""
import json
import pathlib
import time
import traceback

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_charname838d.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

# ★ 场景树对象行（**无正则口径**：靠几何 + 可点元素类型，**不**靠名字前缀）
DUMP_TREE_ROWS = """() => {
  const vis=(e)=>{const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0 && getComputedStyle(e).visibility!=='hidden';};
  const out=[];
  const seen=new Set();
  for (const el of Array.from(document.querySelectorAll('[role="treeitem"],button,li,[role="button"]'))) {
    if (!vis(el)) continue;
    const r=el.getBoundingClientRect();
    if (r.x < 40 || r.x > 300) continue;
    if (r.y < 130 || r.y > 460) continue;
    const t=(el.textContent||'').trim();
    if (!t || t.length>30) continue;
    const key=Math.round(r.y)+'|'+t;
    if (seen.has(key)) continue;
    seen.add(key);
    out.push({text:t, x:Math.round(r.x), y:Math.round(r.y),
              w:Math.round(r.width), h:Math.round(r.height),
              tag:el.tagName, aria:el.getAttribute('aria-label')||'',
              dataKeys:Object.keys(el.dataset||{})});
  }
  return out.sort((a,b)=> (a.y-b.y) || (a.x-b.x));
}"""

# ★ 右键菜单的所有可见条目
DUMP_MENU = """() => {
  const vis=(e)=>{const r=e.getBoundingClientRect(); return r.width>0&&r.height>0;};
  const out=[];
  for (const el of Array.from(document.querySelectorAll('[role="menuitem"],[role="menu"] *,button,li,span,div'))) {
    if (!vis(el) || el.childElementCount>0) continue;
    const r=el.getBoundingClientRect();
    const t=(el.textContent||'').trim();
    if (!t || t.length>20) continue;
    out.push({text:t, x:Math.round(r.x), y:Math.round(r.y), tag:el.tagName,
              role:el.getAttribute('role')||'', cls:(el.className||'').toString().slice(0,60)});
  }
  return out;
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


def tree_rows(page):
    rows = page.evaluate(DUMP_TREE_ROWS)
    names, seen = [], set()
    for r in rows:
        if r["text"] not in seen:
            seen.add(r["text"])
            names.append(r["text"])
    return names, rows


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

        base, base_rows = tree_rows(page)
        out["①进站_树区行名"] = base
        out["①★进站_行数_与名字形态无关"] = len(base_rows)
        out["①基线行详情"] = base_rows

        # ② 找「角色B」（**先验证唯一**）
        cand = [r for r in base_rows if r["text"] == "角色B"]
        out["②★角色B的行数"] = len(cand)
        if len(cand) != 1:
            out["②★不唯一或找不到"] = "⟹ 不自动删除 ⟹ 如实报告"
            br.close()
            return
        row = cand[0]
        out["②★待删的行"] = row

        # ③ 右键 → 菜单
        page.mouse.click(row["x"] + 20, row["y"] + row["h"] / 2, button="right")
        page.wait_for_timeout(1_200)
        clean(page)
        out["③右键后菜单项"] = page.evaluate(DUMP_MENU)
        try:
            page.screenshot(path="/tmp/liblib_source_charname838d.png")
            out["截图"] = "/tmp/liblib_source_charname838d.png"
        except Exception:
            pass

        # ④ 点「删除」
        deleted = False
        try:
            page.get_by_text("删除", exact=True).first.click()
            deleted = True
        except Exception as exc:
            out["④点删除_异常"] = str(exc)
        page.wait_for_timeout(1_500)
        clean(page)

        # ④b 可能有二次确认
        try:
            confirm = page.get_by_text("确定", exact=True).first
            if confirm.is_visible():
                out["④★有二次确认"] = True
                confirm.click()
                page.wait_for_timeout(1_500)
                clean(page)
        except Exception:
            out["④★有二次确认"] = False

        after, after_rows = tree_rows(page)
        out["⑤删除后_树区行名"] = after
        out["⑤★删除后_行数_与名字形态无关"] = len(after_rows)
        out["⑤★是否还剩角色B"] = any(r["text"] == "角色B" for r in after_rows)
        out["⑤★行数是否回到基线"] = len(after_rows) == len(base_rows)
        out["⑤★是否复原"] = (not any(r["text"] == "角色B" for r in after_rows)
                          and len(after_rows) == len(base_rows))
        try:
            page.screenshot(path="/tmp/liblib_source_charname838d_after.png")
        except Exception:
            pass
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
        print("\n=== 进站树区行 ===")
        print("  ", out.get("①进站_树区行名"))
        print("  行数 =", out.get("①★进站_行数_与名字形态无关"))
        print("  角色B 行数 =", out.get("②★角色B的行数"))
        print("\n=== 右键菜单项 ===")
        for d in (out.get("③右键后菜单项") or [])[:25]:
            print("  @(%s,%s) %r role=%s" % (d["x"], d["y"], d["text"], d["role"]))
        print("\n=== 删除后 ===")
        print("  行名 =", out.get("⑤删除后_树区行名"))
        print("  行数 =", out.get("⑤★删除后_行数_与名字形态无关"), "（基线", out.get("①★进站_行数_与名字形态无关"), "）")
        print("  还剩角色B？", out.get("⑤★是否还剩角色B"))
        print("  ★是否复原 =", out.get("⑤★是否复原"))
        if out.get("异常"):
            print("异常：", out["异常"])


if __name__ == "__main__":
    main()

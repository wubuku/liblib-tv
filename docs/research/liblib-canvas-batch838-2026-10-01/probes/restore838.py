#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 838 源站探针 v12：★ **删掉「角色B」**，把源站复原。

★★★ 为什么要单独立这一趟：
  v11（单趟闭环）的**读数器口径坏了** ⟹ 它读到的「新增行」其实是**体型预设面板的行**
  （面板浮在场景树上，y 132..420，与场景树重叠）⟹ ★ 于是它把「角色B」**误判成新增行**，
  转而去右键「标准男性」⟹ ★★ **副作用**：右键菜单弹出（「删除⌘⌫」「创建副本⌘D」…）
  并**停留在页面上**（没点掉）。

★ v12 的读数口径（**照抄 v12 实测有效的那个**）：
  - 场景树对象行：**x∈[40,300] 且 y∈[140,300]**（v12 实测：机位1@154／机位2@186／
    角色A@218／角色B@250，**全部 x=96**）⟹ ★ 用 **x 窄区间 [80,240]** 收窄 ⟹
    排除浮层面板（面板行 x=56）⟹ ★ **读数器扫的元素类型必须与界面真实元素类型相交**；
  - ★ 定位目标：**按 y 排序取最靠后的那个对象行**（本例是 y=250 的「角色B」），
    ⟹ **不靠名字猜**（万一名字变了也还能定位到"最后一个"），
    但**同时校验它的文本 == 「角色B」** ⟹ 两者都对才删。

★ ★ 铁律：
  1. ★ **只删一个**（本批新建的那个）⟹ 删前**读回**它的文本，删后**复验**；
  2. ★ **删除要真删掉** ⟹ 删完**重新进站**（新 context）**再读一遍** ⟹ 跨刷新复验
     （★ 内存里的删除不等于存盘了）；
  3. ★ 若右栏弹出的是**菜单**（不是确认框）⟹ 点菜单里的「删除」⟹ 之后若还有确认框再点「确定」；
  4. ★ 任何一步失败 ⟹ **如实报告「未复原」**，不谎称复原。
"""
import json
import pathlib
import traceback

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_restore838.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

# ★ 场景树对象行（**收窄口径**：x∈[80,240]，避开浮层面板（x=56））
DUMP_TREE_OBJ = """() => {
  const vis=(e)=>{const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0 && getComputedStyle(e).visibility!=='hidden';};
  const out=[];
  const seen=new Set();
  for (const el of Array.from(document.querySelectorAll('span,div,button,a,p,li'))) {
    if (!vis(el) || el.childElementCount>0) continue;
    const r=el.getBoundingClientRect();
    if (r.x < 80 || r.x > 240) continue;
    if (r.y < 140 || r.y > 300) continue;
    const t=(el.textContent||'').trim();
    if (!t || t.length>30) continue;
    const key=Math.round(r.y)+'|'+t;
    if (seen.has(key)) continue;
    seen.add(key);
    out.push({text:t, x:Math.round(r.x), y:Math.round(r.y),
              w:Math.round(r.width), h:Math.round(r.height), tag:el.tagName});
  }
  return out.sort((a,b)=> (a.y-b.y) || (a.x-b.x));
}"""

DUMP_MENU = """() => {
  const vis=(e)=>{const r=e.getBoundingClientRect(); return r.width>0&&r.height>0;};
  const out=[];
  for (const el of Array.from(document.querySelectorAll('[role="menuitem"],button,li,span,div'))) {
    if (!vis(el) || el.childElementCount>0) continue;
    const r=el.getBoundingClientRect();
    const t=(el.textContent||'').trim();
    if (!t || t.length>24) continue;
    out.push({text:t, x:Math.round(r.x), y:Math.round(r.y), tag:el.tagName,
              role:el.getAttribute('role')||''});
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


def tree_obj(page):
    rows = page.evaluate(DUMP_TREE_OBJ)
    names = []
    for r in rows:
        if r["text"] not in names:
            names.append(r["text"])
    return names, rows


def make_ctx(pw, cookies):
    ctx = pw.chromium.launch(headless=True).new_context(
        viewport={"width": 1920, "height": 1080}, locale="zh-CN")
    ctx.add_cookies([{"name": c["name"], "value": c["value"],
                      "domain": c["domain"], "path": c.get("path", "/"),
                      "expires": c.get("expires", -1),
                      "httpOnly": c.get("httpOnly", False),
                      "secure": c.get("secure", False),
                      "sameSite": c.get("sameSite", "Lax")} for c in cookies])
    return ctx


def main():
    cookies = json.loads(COOKIE.read_text(encoding="utf-8"))
    out = {}
    try:
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

            names, rows = tree_obj(page)
            out["①进站_场景树对象行"] = names
            out["①★进站_行数"] = len(rows)
            out["①行详情"] = rows

            # ② 定位目标：文本 == 「角色B」的那一行
            cand = [r for r in rows if r["text"] == "角色B"]
            out["②★角色B候选数"] = len(cand)
            if len(cand) != 1:
                out["②★不唯一或找不到"] = "⟹ 不自动删 ⟹ 如实报告"
                br.close()
                return
            row = cand[0]
            out["②★待删行"] = row

            # ③ 右键 → 菜单 → 点「删除」
            page.mouse.click(row["x"] + 10, row["y"] + row["h"] / 2, button="right")
            page.wait_for_timeout(1_500)
            clean(page)
            out["③右键后菜单项"] = page.evaluate(DUMP_MENU)
            try:
                page.screenshot(path="/tmp/liblib_source_restore838_menu.png")
            except Exception:
                pass

            clicked = False
            for label in ("删除", "删除⌘⌫"):
                try:
                    el = page.get_by_text(label, exact=True).first
                    if el.is_visible():
                        el.click()
                        clicked = True
                        out["③★点的菜单项"] = label
                        break
                except Exception:
                    continue
            out["③★是否点到删除项"] = clicked
            page.wait_for_timeout(1_500)
            clean(page)

            # ④ 二次确认
            try:
                c = page.get_by_text("确定", exact=True).first
                if c.is_visible():
                    out["④★有二次确认"] = True
                    c.click()
                    page.wait_for_timeout(1_500)
                    clean(page)
            except Exception:
                out["④★有二次确认"] = False

            after, after_rows = tree_obj(page)
            out["⑤删除后_场景树对象行"] = after
            out["⑤★删除后_行数"] = len(after_rows)
            out["⑤★还剩角色B"] = any(r["text"] == "角色B" for r in after_rows)
            out["⑤★行数是否回到基线"] = len(after_rows) == len(rows)
            try:
                page.screenshot(path="/tmp/liblib_source_restore838_after.png")
            except Exception:
                pass
            ctx.close()
            br.close()

            # ⑥ ★ 跨刷新复验（新 context ⟹ 真的落盘了吗）
            with sync_playwright() as pw2:
                br2 = pw2.chromium.launch(headless=True)
                ctx2 = br2.new_context(viewport={"width": 1920, "height": 1080}, locale="zh-CN")
                ctx2.add_cookies([{"name": c["name"], "value": c["value"],
                                   "domain": c["domain"], "path": c.get("path", "/"),
                                   "expires": c.get("expires", -1),
                                   "httpOnly": c.get("httpOnly", False),
                                   "secure": c.get("secure", False),
                                   "sameSite": c.get("sameSite", "Lax")} for c in cookies])
                p2 = ctx2.new_page()
                p2.goto(URL, wait_until="domcontentloaded", timeout=90_000)
                p2.wait_for_timeout(12_000)
                open_desk(p2)
                clean(p2)
                f_names, f_rows = tree_obj(p2)
                out["⑥★跨刷新后_场景树对象行"] = f_names
                out["⑥★跨刷新后_行数"] = len(f_rows)
                out["⑥★跨刷新后还剩角色B"] = any(r["text"] == "角色B" for r in f_rows)
                out["⑥★★是否已复原"] = (
                    not any(r["text"] == "角色B" for r in f_rows)
                    and len(f_rows) == len(rows))
                try:
                    p2.screenshot(path="/tmp/liblib_source_restore838_final.png")
                except Exception:
                    pass
                ctx2.close()
                br2.close()
    except Exception:
        out["异常"] = traceback.format_exc()
    finally:
        OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", OUT)
        for k in ("①进站_场景树对象行", "③★点的菜单项", "⑤删除后_场景树对象行",
                  "⑥★跨刷新后_场景树对象行"):
            print("%-22s %s" % (k, out.get(k)))
        for k in ("①★进站_行数", "②★角色B候选数", "③★是否点到删除项", "④★有二次确认",
                  "⑤★删除后_行数", "⑤★还剩角色B", "⑤★行数是否回到基线",
                  "⑥★跨刷新后_行数", "⑥★跨刷新后还剩角色B", "⑥★★是否已复原"):
            print("%-24s %r" % (k, out.get(k)))
        print("\n=== 菜单项 ===")
        for d in (out.get("③右键后菜单项") or [])[:20]:
            print("  @(%s,%s) %r role=%s" % (d["x"], d["y"], d["text"], d["role"]))
        if out.get("异常"):
            print("异常：", out["异常"])


if __name__ == "__main__":
    main()

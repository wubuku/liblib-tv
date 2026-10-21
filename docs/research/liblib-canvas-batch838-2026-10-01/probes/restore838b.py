#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 838 源站探针 v13：★ **把「角色B」真正删掉并落盘**。

★★ 背景：v12 在**内存里**删掉了「角色B」（行数 4→3、名字消失），
   但**跨刷新复验**（新 context 重新进站）⟹ 「角色B」**又出现了** ⟹
   ★★ **删除没有落盘**（或落盘被后续状态覆盖）⟹ ★ **不能算复原完成**。

★ 本趟做三件事：
  ① 读**保存机制**：导演台有没有「保存」按钮／关闭时是否自动保存／
     改动的提交走哪个 API（**抓网络**）；
  ② 再删一次 ⟹ ★ **抓删除请求的响应** ⟹ 看服务端返回什么（200 但没生效？）；
  ③ 关闭导演台 ⟹ 等一段时间 ⟹ 跨刷新复验 ⟹ 看是否落盘。

★ ★ 铁律：
  - **不谎称复原** ⟹ 每一步都如实记录；
  - 若 UI 删不掉 ⟹ ★ **不直接调 API 改用户数据**（那是越权）⟹
    如实报告「未能复原」，并给出**已尝试的动作**清单。
"""
import json
import pathlib
import time
import traceback

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_restore838b.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

DUMP_TREE_OBJ = """() => {
  const vis=(e)=>{const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0 && getComputedStyle(e).visibility!=='hidden';};
  const out=[]; const seen=new Set();
  for (const el of Array.from(document.querySelectorAll('span,div,button,a,p,li'))) {
    if (!vis(el) || el.childElementCount>0) continue;
    const r=el.getBoundingClientRect();
    if (r.x < 80 || r.x > 240) continue;
    if (r.y < 140 || r.y > 300) continue;
    const t=(el.textContent||'').trim();
    if (!t || t.length>30) continue;
    const key=Math.round(r.y)+'|'+t;
    if (seen.has(key)) continue; seen.add(key);
    out.push({text:t, x:Math.round(r.x), y:Math.round(r.y),
              w:Math.round(r.width), h:Math.round(r.height), tag:el.tagName});
  }
  return out.sort((a,b)=> (a.y-b.y) || (a.x-b.x));
}"""

# ★ 导演台顶栏的所有按钮（找「保存」）
DUMP_TOPBAR = """() => {
  const vis=(e)=>{const r=e.getBoundingClientRect(); return r.width>0&&r.height>0;};
  const out=[];
  for (const el of Array.from(document.querySelectorAll('button,[role="button"]'))) {
    if (!vis(el)) continue;
    const r=el.getBoundingClientRect();
    if (r.y > 60) continue;
    out.push({text:(el.textContent||'').trim().slice(0,24),
              aria:el.getAttribute('aria-label')||'', title:el.getAttribute('title')||'',
              x:Math.round(r.x), y:Math.round(r.y), w:Math.round(r.width), h:Math.round(r.height)});
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

        # ★ 抓网络：任何写请求（POST/PUT/PATCH/DELETE）
        writes = []

        def on_resp(resp):
            try:
                m = resp.request.method
                if m in ("POST", "PUT", "PATCH", "DELETE"):
                    body = ""
                    try:
                        body = (resp.request.post_data or "")[:600]
                    except Exception:
                        pass
                    writes.append({"method": m, "url": resp.url[:220],
                                   "status": resp.status, "reqBody": body})
            except Exception:
                pass

        page.on("response", on_resp)
        page.goto(URL, wait_until="domcontentloaded", timeout=90_000)
        page.wait_for_timeout(12_000)
        open_desk(page)
        clean(page)

        names, rows = tree_obj(page)
        out["①进站_场景树对象行"] = names
        out["①★进站_行数"] = len(rows)
        out["①★顶栏按钮"] = page.evaluate(DUMP_TOPBAR)

        # ② 再删一次（抓写请求）
        writes.clear()
        cand = [r for r in rows if r["text"] == "角色B"]
        out["②★角色B候选数"] = len(cand)
        if len(cand) == 1:
            row = cand[0]
            page.mouse.click(row["x"] + 10, row["y"] + row["h"] / 2, button="right")
            page.wait_for_timeout(1_500)
            clean(page)
            clicked = False
            for label in ("删除", "删除⌘⌫"):
                try:
                    el = page.get_by_text(label, exact=True).first
                    if el.is_visible():
                        el.click()
                        clicked = True
                        out["②★点的菜单项"] = label
                        break
                except Exception:
                    continue
            out["②★是否点到删除"] = clicked
            page.wait_for_timeout(2_000)
            clean(page)
            try:
                c = page.get_by_text("确定", exact=True).first
                if c.is_visible():
                    c.click()
                    page.wait_for_timeout(1_500)
                    clean(page)
            except Exception:
                pass
            page.wait_for_timeout(3_000)
            after, after_rows = tree_obj(page)
            out["②删除后_行名"] = after
            out["②★删除后_行数"] = len(after_rows)
            out["②★还剩角色B"] = any(r["text"] == "角色B" for r in after_rows)

        out["③★删除期间的写请求"] = writes[:30]

        # ④ 关掉导演台（可能触发自动保存）⟹ 等 ⟹ 复验
        closed = False
        try:
            cb = page.locator("[aria-label='关闭']").first
            if cb.is_visible():
                cb.click()
                closed = True
        except Exception as exc:
            out["④关闭_异常"] = str(exc)
        out["④★是否关了导演台"] = closed
        page.wait_for_timeout(6_000)
        out["④★关闭后的写请求"] = writes[:30]
        try:
            page.screenshot(path="/tmp/liblib_source_restore838b.png")
        except Exception:
            pass
        ctx.close()
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
        for k in ("①进站_场景树对象行", "②删除后_行名"):
            print("%-20s %s" % (k, out.get(k)))
        for k in ("①★进站_行数", "②★角色B候选数", "②★是否点到删除", "②★删除后_行数",
                  "②★还剩角色B", "④★是否关了导演台"):
            print("%-20s %r" % (k, out.get(k)))
        print("\n=== 顶栏按钮 ===")
        for b in (out.get("①★顶栏按钮") or [])[:20]:
            print("  @(%s,%s) text=%r aria=%r" % (b["x"], b["y"], b["text"], b["aria"]))
        print("\n=== 写请求 ===")
        for w in (out.get("③★删除期间的写请求") or [])[:20]:
            print("  %s %s -> %s" % (w["method"], w["status"], w["url"][:150]))
            if w["reqBody"]:
                print("      body:", w["reqBody"][:220])
        if out.get("异常"):
            print("异常：", out["异常"])


if __name__ == "__main__":
    main()

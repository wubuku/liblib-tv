#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 838 源站探针 v14：★ 找出导演台数据的**保存机制**，并把「角色B」真正删掉落盘。

★★ 已知：v13 删除后**内存**里「角色B」消失，但**跨刷新复验仍在** ⟹ 没落盘。
   v13 抓到的写请求**只有** `POST /api/canvas/project/heartbeat` ⟹
   ★ **删除没有触发任何数据保存**。

★ 本趟要查的：
  ① 删除期间**所有** `api.liblib.tv` 的请求（含 GET ⟹ 可能有「读时顺带写」的接口）；
  ② ★ **保存机制**是「关台时保存」还是「改动后自动保存」还是「有手动保存按钮」⟹
     实测：删完 ⟹ **等 30 秒** ⟹ 看有没有写请求；再 ⟹ **关台** ⟹ 看有没有写请求；
  ③ ★ 若 UI 路径删不掉 ⟹ ★ **不越权直接调 API 改用户数据** ⟹
     如实报告，并把「已尝试的动作」清单写清楚。

★ ★★ 但**有一条正当路径**：源站的导演台数据存在**画布节点**的 `compositionData` 里
   （v5 已实测：节点 `n-gYB1c2Peq9` 的 data.compositionData）⟹
   ⟹ 如果 UI 的保存最终是「更新这个节点」⟹ 那是**产品的正常路径** ⟹
   ⟹ ★ 应当**通过 UI 触发**它（而不是我手搓 API 请求）。
"""
import json
import pathlib
import time
import traceback

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_restore838c.json")
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

        api_calls = []

        def on_resp(resp):
            try:
                if "api.liblib.tv" not in resp.url:
                    return
                m = resp.request.method
                body = ""
                try:
                    body = (resp.request.post_data or "")[:800]
                except Exception:
                    pass
                api_calls.append({"m": m, "url": resp.url[:200], "st": resp.status,
                                  "body": body, "t": time.time()})
            except Exception:
                pass

        page.on("response", on_resp)
        page.goto(URL, wait_until="domcontentloaded", timeout=90_000)
        page.wait_for_timeout(12_000)
        open_desk(page)
        clean(page)

        names, rows = tree_obj(page)
        out["①进站_行名"] = names
        out["①★进站_行数"] = len(rows)

        # ② 删除
        api_calls.clear()
        cand = [r for r in rows if r["text"] == "角色B"]
        out["②★角色B候选数"] = len(cand)
        if len(cand) == 1:
            row = cand[0]
            page.mouse.click(row["x"] + 10, row["y"] + row["h"] / 2, button="right")
            page.wait_for_timeout(1_500)
            clean(page)
            for label in ("删除", "删除⌘⌫"):
                try:
                    el = page.get_by_text(label, exact=True).first
                    if el.is_visible():
                        el.click()
                        out["②★点的菜单项"] = label
                        break
                except Exception:
                    continue
            page.wait_for_timeout(1_500)
            clean(page)
            try:
                c = page.get_by_text("确定", exact=True).first
                if c.is_visible():
                    c.click()
                    page.wait_for_timeout(1_500)
                    clean(page)
            except Exception:
                pass
        after, after_rows = tree_obj(page)
        out["②删除后_行名"] = after
        out["②★删除后_行数"] = len(after_rows)
        out["②★删除期间api调用"] = list(api_calls)

        # ③ 等 25 秒看自动保存
        api_calls.clear()
        page.wait_for_timeout(25_000)
        out["③★等待25秒后的api调用"] = list(api_calls)

        # ④ 关台（**不删 nextjs-portal**，否则关不掉）
        api_calls.clear()
        closed = False
        try:
            cb = page.locator("button[aria-label='关闭']").first
            cb.click(timeout=8_000)
            closed = True
        except Exception as exc:
            out["④关闭_异常"] = str(exc)
        out["④★是否关台成功"] = closed
        page.wait_for_timeout(12_000)
        out["④★关台后的api调用"] = list(api_calls)
        try:
            page.screenshot(path="/tmp/liblib_source_restore838c.png")
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
        for k in ("①进站_行名", "②删除后_行名"):
            print("%-18s %s" % (k, out.get(k)))
        for k in ("①★进站_行数", "②★角色B候选数", "②★删除后_行数", "④★是否关台成功"):
            print("%-20s %r" % (k, out.get(k)))
        for phase in ("②★删除期间api调用", "③★等待25秒后的api调用", "④★关台后的api调用"):
            print("\n=== %s ===" % phase)
            for c in (out.get(phase) or []):
                print("  %s %s %s" % (c["m"], c["st"], c["url"][:140]))
                if c["body"]:
                    print("       body:", c["body"][:200])
        if out.get("异常"):
            print("异常：", out["异常"])


if __name__ == "__main__":
    main()
